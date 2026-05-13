# Presets – Flow

This document describes the control and data flow for the Presets feature: saving
presets from the current slider state, reloading them into the sidebar, and
applying them to the UI and processing pipeline.

For data model details see `specs/features/PRESETS.md`.

---

## Legend

- **User action** — button clicks, selecting preset items.
- **UI widget** — `PresetPanel`, `PresetItem`, dialogs.
- **Handler** — functions in `src/ui/handlers/presets.py`.
- **Service** — `ImageProcessorService` (via `adjust_channel`).

---

## Saving a Preset

### High-level sequence

```text
User clicks "Save Preset" button
    │
    ▼
UI: PresetPanel.save_btn.clicked
    │  (connected in MainWindow to save_preset(main_window))
    ▼
Handler: save_preset(main_window)
    │
    ├── prompt user for preset name
    │
    ├── validate and sanitise name → safe_name
    │
    ├── collect slider values from all ChannelControllers
    │
    ├── write JSON file to presets_dir/safe_name.json
    │
    ├── optionally write thumbnail PNG
    │
    ├── preset_panel.reload_presets()
    │
    └── status bar: "Preset '<name>' saved"
```

### Detailed flow

```text
save_preset(main_window)
    │
    ├── name, ok = QInputDialog.getText(
    │       main_window,
    │       "Save Preset",
    │       "Preset name:",
    │   )
    │
    ├── if not ok or not name.strip():
    │       return  # cancelled or empty
    │
    ├── safe_name = sanitise(name)
    │       # remove invalid chars, strip, replace spaces with underscores
    │
    ├── if not safe_name:
    │       QMessageBox.warning("Please enter a valid preset name.")
    │       return
    │
    ├── channels = {}
    │   for i, ctrl in enumerate(main_window.controllers):
    │       channels[_CHANNEL_NAMES[i]] = {
    │           "brightness": ctrl.sliders["brightness"].value(),
    │           "contrast":   ctrl.sliders["contrast"].value(),
    │           "intensity":  ctrl.sliders["intensity"].value(),
    │       }
    │
    ├── preset_data = {"name": name, "channels": channels}
    │
    ├── ensure presets_dir exists (os.makedirs(..., exist_ok=True))
    │
    ├── json_path = presets_dir / f"{safe_name}.json"
    │
    ├── with open(json_path, "w", encoding="utf-8") as f:
    │       json.dump(preset_data, f, indent=2)
    │
    ├── try to create thumbnail from current main image:
    │       pixmap = viewer.current_pixmap()
    │       if pixmap is valid:
    │           thumb = pixmap.scaled(120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    │           thumb.save(presets_dir / f"{safe_name}.png")
    │
    ├── main_window.preset_panel.reload_presets()
    │
    └── status_bar.set_message(f"Preset '{name}' saved", MEDIUM_TIMEOUT)
```

Error handling:

- JSON write fails (`OSError`) → `QMessageBox.critical` with error message,
  thumbnail is skipped, and no preset is added.
- Thumbnail write fails → silently ignored; preset remains functional.

---

## Loading Presets into the Sidebar

### Flow

```text
PresetPanel.__init__(presets_dir)
    │
    └── self.reload_presets()

User saves or modifies presets
    │
    └── save_preset() or external change calls reload_presets()
```

```text
PresetPanel.reload_presets()
    │
    ├── clear existing PresetItem widgets (keep trailing stretch)
    │
    ├── if not os.path.isdir(presets_dir):
    │       return
    │
    ├── for fname in sorted(os.listdir(presets_dir)):
    │       if not fname.endswith(".json"):
    │           continue
    │       json_path  = presets_dir / fname
    │       thumb_path = presets_dir / (basename(fname) + ".png")
    │
    │       try:
    │           with open(json_path, "r", encoding="utf-8") as f:
    │               data = json.load(f)
    │       except (JSONDecodeError, OSError):
    │           continue  # skip invalid file
    │
    │       item = PresetItem(data, thumb_path)
    │       item.clicked.connect(self.preset_selected)
    │       insert item above stretch in layout
    │
    └── done
```

Result:

- The sidebar is always built from the current contents of `presets_dir`.
- Invalid or corrupted JSON files are ignored and not shown.

---

## Applying a Preset

### High-level sequence

```text
User clicks a preset in the sidebar
    │
    ▼
UI: PresetItem.mousePressEvent
    │  emits clicked(preset_data)
    ▼
PresetPanel.preset_selected(preset_data)
    │  connected in MainWindow to apply_preset(main_window, preset_data)
    ▼
Handler: apply_preset(main_window, preset_data)
    │
    ├── validate preset_data["channels"] structure
    │
    ├── for each ChannelController:
    │       block signals
    │       set sliders + text fields from preset
    │       unblock signals
    │
    ├── for each channel index:
    │       adjust_channel(main_window, i)
    │
    └── status bar: "Applied preset '<name>'"
```

### Detailed flow

```text
apply_preset(main_window, preset_data)
    │
    ├── channels = preset_data.get("channels", {})
    │   if not isinstance(channels, dict):
    │       channels = {}
    │
    ├── for i, ctrl in enumerate(main_window.controllers):
    │       ch_name = _CHANNEL_NAMES[i]  # "red", "green", "blue"
    │       ch_data = channels.get(ch_name, {}) or {}
    │
    │       ctrl.blockSignals(True)
    │       for slider_name in ["brightness", "contrast", "intensity"]:
    │           value = ch_data.get(slider_name)
    │           if isinstance(value, int) and slider_name in ctrl.sliders:
    │               slider = ctrl.sliders[slider_name]
    │               slider.setValue(value)
    │               if slider_name in ctrl.text_inputs:
    │                   ctrl.text_inputs[slider_name].setText(str(value))
    │       ctrl.blockSignals(False)
    │
    ├── for i in range(3):
    │       adjust_channel(main_window, i)
    │           # recomputes processed[i] from aligned[i]
    │           # updates channel preview and main display
    │
    └── status_bar.set_message(f"Applied preset '{name}'", MEDIUM_TIMEOUT)
```

Notes:

- If a channel or slider is missing from the preset JSON, the corresponding
  current UI value is left unchanged.
- Applying a preset on a channel without loaded/aligned data has no visible
  effect until that channel is loaded.

---

## Interaction with Autosave

Preset application changes only slider values (and thus `processed[]` state). The
**name** of the currently applied preset is not stored anywhere.

### After applying a preset

1. Sliders in all `ChannelController`s now reflect the preset.
2. `adjust_channel()` has recomputed `processed[]` from `aligned[]`.
3. The next autosave tick (`save_autosave()` after 500 ms of slider inactivity)
   writes the new slider values into `autosave.json`.

On application restart, `restore_autosave()` restores the slider values and calls
`adjust_channel()` again. The visual result matches the last applied preset, but
there is no concept of an "active preset" in the UI.

---

## Planned Context Menu Flow (Issue #47)

Issue #47 proposes adding Rename and Delete actions for presets via a context
menu on `PresetItem`.

### Rename preset (planned)

```text
User right-clicks a PresetItem
    │
    ▼
Context menu → "Rename"
    │
    ▼
Slot: rename_preset(preset_data)
    │
    ├── old_name = preset_data["name"]
    │   old_safe = derive_safe_name(old_name)
    │
    ├── new_name, ok = QInputDialog.getText(
    │       parent, "Rename Preset", "New name:", text=old_name)
    │
    ├── if not ok or not new_name.strip():
    │       return
    │
    ├── new_safe = sanitise(new_name)
    │       # same rules as save_preset
    │
    ├── rename files:
    │       presets_dir/old_safe.json → presets_dir/new_safe.json
    │       presets_dir/old_safe.png  → presets_dir/new_safe.png (if exists)
    │
    ├── update "name" field inside JSON
    │
    ├── preset_panel.reload_presets()
    │
    └── status_bar.set_message("Preset renamed", SHORT_TIMEOUT)
```

### Delete preset (planned)

```text
User right-clicks a PresetItem
    │
    ▼
Context menu → "Delete"
    │
    ▼
Slot: delete_preset(preset_data)
    │
    ├── if preset is protected (e.g. built-in neutral preset):
    │       return  # do nothing
    │
    ├── safe_name = derive_safe_name(preset_data["name"])
    │
    ├── delete files if they exist:
    │       os.remove(presets_dir/safe_name.json)
    │       os.remove(presets_dir/safe_name.png)
    │
    ├── preset_panel.reload_presets()
    │
    └── status_bar.set_message("Preset deleted", SHORT_TIMEOUT)
```

No confirmation dialog is shown; deletion is immediate to keep workflow fast.

---

## Cross-Feature Interactions in the Flow

- **Adjustments:** presets are a thin layer over slider values. All actual image
  changes happen via `adjust_channel()`.
- **Alignment:** presets are most useful once all channels are aligned; applying
  them before alignment only changes UI state until valid image data arrives.
- **Autosave:** the autosave flow sees only slider numbers and channel paths,
  not preset identities.
- **Reset (New):** resetting the app clears sliders and images but leaves preset
  files intact. The next autosave will record the reset slider state.
