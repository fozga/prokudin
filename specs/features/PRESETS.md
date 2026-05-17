# Presets

## Contract

The presets feature allows users to save and reuse per-channel adjustment settings
(brightness, contrast, intensity) under named presets. A preset contains **only**
slider values; it does not store image pixels or crop rectangles. Presets are
persistent across sessions and displayed in a scrollable sidebar with optional
thumbnails.

Applying a preset updates all sliders in all channels and re-applies adjustments
via `adjust_channel()` exactly once per channel.

> Planned (issue #47): the preset list will expose a context menu for renaming and
> deleting presets directly from the UI.

---

## Data Model

### JSON schema

Each preset is a JSON file in the presets directory chosen by `MainWindow`:

```json
{
  "name": "Warm contrast boost",
  "channels": {
    "red":   { "brightness": 10, "contrast": 20, "intensity": 100 },
    "green": { "brightness":  0, "contrast": 10, "intensity": 100 },
    "blue":  { "brightness": -5, "contrast":  5, "intensity":  90 }
  }
}
```

Keys:

- `name` — user-facing name shown in the preset list.
- `channels` — per-channel slider state. Keys are fixed: `"red"`, `"green"`,
  `"blue"`. Missing channels or sliders are simply ignored when applying.

### File naming and location

- Directory: `main_window.presets_dir`, resolved by `src.ui.config.get_presets_dir()`.
- File name: `safe_name + ".json"`, where `safe_name` is derived from `name` by:
  1. Removing all characters not matching `[\w\s-]`.
  2. Trimming whitespace.
  3. Replacing remaining spaces with underscores.

Example:

- Input name: `"Warm contrast (sunset #1)"`
- Safe name: `"Warm_contrast_sunset_1"`
- JSON file: `Warm_contrast_sunset_1.json`
- Thumbnail (optional): `Warm_contrast_sunset_1.png`

---

## UI Components

### PresetPanel — `src/ui/widgets/preset_panel.py`

`PresetPanel` is the left-sidebar widget that displays preset thumbnails and
names and provides a **Save Preset** button.

- Emits `preset_selected(dict)` when the user clicks a preset item.
- Emits `save_requested()` when the user clicks **Save Preset**.
- Uses `reload_presets()` to repopulate its list from `presets_dir`.

Presets are shown as `PresetItem` widgets:

- Thumbnail: scaled to 120×80 with `Qt.KeepAspectRatio`, or "No image" if the
  PNG file does not exist.
- Name: `preset_data["name"]` or "Unnamed" if missing, word-wrapped under the
  thumbnail.
- Hover highlight: background changes on mouse enter/leave.

> Planned (issue #47): `PresetItem` will handle right-click events to open a
> context menu with Rename and Delete actions.

### Save Preset Button

- Always enabled while the application is running.
- Clicking the button emits `save_requested` to `MainWindow`, which forwards the
  call to `save_preset(main_window)`.

---

## Saving a Preset — `save_preset(main_window)`
`src/ui/handlers/presets.py`

The `save_preset` handler captures the current slider state and writes a JSON file
(and optional thumbnail) to `presets_dir`.

### Name input and validation

1. Shows a modal `QInputDialog.getText(main_window, "Save Preset", "Preset name:")`.
2. If the dialog is cancelled or the entered name is empty/whitespace only, the
   handler returns without saving.
3. Builds `safe_name` by:
   - Removing all characters that are not letters, digits, underscore, whitespace,
     or hyphen (`[^\w\s-]`).
   - Stripping leading/trailing whitespace.
   - Replacing remaining spaces with underscores.
4. If `safe_name` is empty after sanitisation, shows a `QMessageBox.warning`
   with "Please enter a valid preset name." and returns.

### Collecting slider values

```python
channels = {}
for i, ctrl in enumerate(main_window.controllers):
    channels[_CHANNEL_NAMES[i]] = {
        s: ctrl.sliders[s].value() for s in ["brightness", "contrast", "intensity"]
    }

preset_data = {"name": name, "channels": channels}
```

Where `_CHANNEL_NAMES = ["red", "green", "blue"]`.

### Writing JSON

```python
os.makedirs(main_window.presets_dir, exist_ok=True)
json_path = os.path.join(main_window.presets_dir, f"{safe_name}.json")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(preset_data, f, indent=2)
```

Errors (`OSError`) during file creation or writing are reported via
`QMessageBox.critical` and abort thumbnail saving.

### Writing thumbnail (optional)

If the main viewer currently has a valid pixmap:

1. `thumb = pixmap.scaled(120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)`
2. `thumb.save(os.path.join(presets_dir, f"{safe_name}.png"))`

Errors (e.g. file system permissions) are ignored — the preset remains functional
without a thumbnail.

### Finalisation

- `main_window.preset_panel.reload_presets()` is called to refresh the list.
- Status bar message: `Preset '<name>' saved` with a medium timeout.

---

## Applying a Preset — `apply_preset(main_window, preset_data)`

`apply_preset` takes the `preset_data` dict from a clicked `PresetItem` and
applies slider values to all channels.

### Data validation

1. Reads `channels = preset_data.get("channels", {})`.
2. If `channels` is not a dict, treats it as empty.
3. For each controller index `i` and corresponding channel name
   (`"red"`, "green", "blue"), reads `ch_data = channels.get(name, {})`.
4. Ignores any non-dict `ch_data` or non-int slider values.

### Slider update with signal blocking

```python
for i, ctrl in enumerate(main_window.controllers):
    ch_data = channels.get(_CHANNEL_NAMES[i], {}) or {}
    ctrl.blockSignals(True)
    for slider_name, value in ch_data.items():
        if slider_name in ctrl.sliders and isinstance(value, int):
            slider = ctrl.sliders[slider_name]
            slider.setValue(value)
            if slider_name in ctrl.text_inputs:
                ctrl.text_inputs[slider_name].setText(str(value))
    ctrl.blockSignals(False)
```

This ensures that `value_changed` is not emitted for each individual slider
change; instead, adjustments are applied in a controlled way afterwards.

### Applying adjustments

After all sliders have been updated, the handler calls:

```python
for i in range(3):
    adjust_channel(main_window, i)
```

This recomputes `processed[i]` from `aligned[i]` using the newly applied
brightness and contrast values and refreshes the channel previews and main
display.

Finally, the status bar shows `"Applied preset '<name>'"` with a medium timeout.

---

## Preset List Reload — `PresetPanel.reload_presets()`

`reload_presets()` repopulates the preset sidebar from the filesystem:

1. Clears existing `PresetItem` widgets from the internal layout.
2. If `presets_dir` is not a directory, returns immediately.
3. Iterates over `sorted(os.listdir(presets_dir))`.
4. For each `*.json` file:
   - Builds `json_path` and the corresponding `thumb_path` (same base name, `.png`).
   - Attempts to `json.load` the file; invalid JSON is skipped.
   - Creates a `PresetItem(data, thumb_path)` and connects its `clicked` signal
     to `preset_selected`.
   - Inserts the item above the layout's trailing stretch.

This means the preset list is always in sync with the contents of `presets_dir`
whenever a preset is saved or presets are modified externally.

---

## Planned Enhancements — Issue #47

Issue #47 proposes improving preset management UX by adding rename and delete
operations directly in the UI.

### Rename

- Trigger: right-click on a `PresetItem` → context menu → **Rename**.
- Behaviour:
  1. Show `QInputDialog.getText` with the current preset name pre-filled.
  2. Validate new name using the same rules as `save_preset` (non-empty,
     sanitised to `safe_name`, no duplicates, valid filename characters only).
  3. Rename both the JSON file and the thumbnail (if it exists) from the old
     `safe_name` to the new `safe_name`.
  4. Call `reload_presets()` to update the list.

### Delete

- Trigger: right-click on a `PresetItem` → context menu → **Delete**.
- Behaviour:
  1. If the preset is **protected** (e.g. built-in defaults such as
     `neutral.json`), the action is disabled or does nothing.
  2. For regular presets, delete the JSON file and thumbnail (if present).
  3. Call `reload_presets()` to update the list.
  4. No confirmation dialog is shown — deletion is immediate by design for fast
     workflow.

These changes affect only file management and UI. The JSON schema and
`apply_preset` behaviour remain unchanged.

---

## Interactions with Other Features

| Feature | Relationship |
|---|---|
| **Adjustments** | Presets store and restore slider values for brightness, contrast, and intensity. Applying a preset triggers `adjust_channel()` for each channel. |
| **Autosave** | Autosave records the last used slider values, not the selected preset name. After restart, the state matches the effect of the last applied preset, but there is no notion of an "active" preset. |
| **Channel Loading** | Presets can be applied only after alignment; otherwise adjustments are applied to whatever data is currently in `aligned[]`. Loading new channels and realigning retains the current slider state until a preset is applied. |
| **Reset (New)** | Resetting the application clears slider state and image data but does not delete preset files from `presets_dir`. |
| **Image Saving** | Saved images reflect current slider state (via `processed[]` for display) but the combined image written to disk currently ignores adjustments (built from `aligned[]`). Presets therefore affect what the user sees, not the saved combined file. |

---

## Constraints

- Preset names are not enforced to be unique at the JSON level; uniqueness is
  enforced only via file naming conventions. It is technically possible to
  create two presets with the same `name` but different `safe_name` variants.
- Presets are global to the application. There is no per-project preset
  isolation.
- Presets do not store crop rectangles or alignment state — they only store
  sliders. Crop and alignment must be managed independently.
- Presets are not versioned. Changes to slider semantics or ranges may require
  a migration step in a future format version.
