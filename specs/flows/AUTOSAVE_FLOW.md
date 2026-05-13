# Autosave – Flow

This document describes the control and data flow for the Autosave feature:
when and how autosave is triggered, how state is written to disk, how it is
restored on startup, and how it is cleared on reset.

For the data model and JSON schema see `specs/features/AUTOSAVE.md`.

---

## Legend

- **User action** — slider moves, clicking "New" (reset), starting the app.
- **UI widget** — `ChannelController` sliders, main window, viewer.
- **Handler** — functions in `src/ui/handlers/autosave.py` and related modules.
- **Timer** — `QTimer` used for debouncing writes.

---

## Debounced Autosave Trigger

Autosave is triggered only by changes to adjustment sliders. It uses a single
`QTimer` owned by `MainWindow` to debounce frequent updates.

### Timer setup (MainWindow)

```text
MainWindow.__init__()
    │
    ├── self._autosave_timer = QTimer(self)
    │   self._autosave_timer.setSingleShot(True)
    │   self._autosave_timer.setInterval(500)  # 500 ms
    │   self._autosave_timer.timeout.connect(lambda: save_autosave(self))
    │
    └── connect ChannelController.value_changed → self._on_slider_changed()
```

### Slider change flow

```text
User moves any brightness/contrast/intensity slider
    │
    ▼
UI: ChannelController.sliders[*].valueChanged
    │
    └── ChannelController.value_changed emitted
            (from _update_text_from_slider or reset_all_sliders)

MainWindow._on_slider_changed()
    │
    ├── self._autosave_timer.stop()
    │
    ├── self._autosave_timer.start()  # restarts 500 ms countdown
    │
    └── (optionally) update preview / display
```

Result:

- As long as the user keeps moving sliders, the timer is restarted and no
  autosave is written.
- Once the user stops interacting for at least 500 ms, the timer fires exactly
  once and calls `save_autosave(self)`.

---

## Writing Autosave – `save_autosave(main_window)`

### High-level sequence

```text
Timer fires (500 ms after last slider change)
    │
    ▼
Handler: save_autosave(main_window)
    │
    ├── determine autosave.json path in config_dir
    │
    ├── collect channel paths and slider values
    │
    ├── collect saved crop rectangle
    │
    ├── build JSON payload
    │
    └── write JSON to disk (overwrite if exists)
```

### Detailed flow

```text
save_autosave(main_window)
    │
    ├── path = _autosave_path(main_window)  # config_dir/autosave.json
    │
    ├── channels = {}
    │   for i, (name, ctrl) in enumerate(zip(["red","green","blue"], controllers)):
    │       channels[name] = {
    │           "path":       state.channel_paths[i],
    │           "brightness": ctrl.sliders["brightness"].value(),
    │           "contrast":   ctrl.sliders["contrast"].value(),
    │           "intensity":  ctrl.sliders["intensity"].value(),
    │       }
    │
    ├── saved_crop = viewer.get_saved_crop_rect() if viewer else None
    │   if saved_crop and saved_crop.isValid():
    │       crop = {
    │           "x": saved_crop.x(),
    │           "y": saved_crop.y(),
    │           "width":  saved_crop.width(),
    │           "height": saved_crop.height(),
    │       }
    │   else:
    │       crop = None
    │
    ├── data = {"version": 1, "channels": channels, "crop": crop}
    │
    ├── try:
    │       os.makedirs(config_dir, exist_ok=True)
    │       with open(path, "w", encoding="utf-8") as f:
    │           json.dump(data, f, indent=2)
    │   except OSError as e:
    │       log warning (no GUI error); autosave is skipped
    │
    └── return
```

The handler does not update the UI directly; autosave is a background operation.

---

## Restoring Autosave – `restore_autosave(main_window)`

`restore_autosave()` is called once from `MainWindow.__init__()` after widgets
and handlers have been created but before the window is shown.

### High-level sequence

```text
MainWindow.__init__()
    │
    ├── setup UI and handlers
    │
    ├── restore_autosave(self)
    │
    └── show()  # normal event loop begins
```

### File loading and parsing

```text
restore_autosave(main_window)
    │
    ├── path = _autosave_path(main_window)
    │   if not os.path.exists(path):
    │       return  # nothing to restore
    │
    ├── try:
    │       with open(path, encoding="utf-8") as f:
    │           data = json.load(f)
    │   except (OSError, JSONDecodeError):
    │       return  # malformed or unreadable file is ignored
```

### Restoring channels

```text
channels_data = data.get("channels", {}) or {}

for i, name in enumerate(["red", "green", "blue"]):
    ch_data  = channels_data.get(name, {}) or {}
    filepath = ch_data.get("path")

    if isinstance(filepath, str) and os.path.exists(filepath):
        load_channel_from_path(main_window, i, filepath)
            # → load_raw_image_from_path()
            # → _process_channel_image()
    else:
        # optional: status bar message about missing file
        continue
```

`load_channel_from_path()` reuses the same `_process_channel_image()` as
interactive loads, so alignment, previews, and display updates follow the
standard channel-loading flow.

### Restoring sliders

```text
for i, ctrl in enumerate(main_window.controllers):
    ch_data = channels_data.get(_CHANNEL_NAMES[i], {}) or {}

    ctrl.blockSignals(True)
    for key in ["brightness", "contrast", "intensity"]:
        value = ch_data.get(key)
        if isinstance(value, int) and key in ctrl.sliders:
            slider = ctrl.sliders[key]
            slider.setValue(value)
            if key in ctrl.text_inputs:
                ctrl.text_inputs[key].setText(str(value))
    ctrl.blockSignals(False)

# Apply adjustments to newly aligned images
for i in range(3):
    if main_window.svc.aligned[i] is not None:
        adjust_channel(main_window, i)
    update_channel_preview(main_window, i)
```

Key points:

- `blockSignals(True/False)` prevents `value_changed` from firing while sliders
  are programmatically set.
- `adjust_channel()` is called only after channels have been loaded and aligned.

### Restoring crop

```text
crop_data = data.get("crop")

if isinstance(crop_data, dict):
    x = crop_data.get("x")
    y = crop_data.get("y")
    w = crop_data.get("width")
    h = crop_data.get("height")

    if all(isinstance(v, (int, float)) for v in [x, y, w, h]) and w > 0 and h > 0:
        rect = QRect(int(x), int(y), int(w), int(h))
        main_window.viewer.set_saved_crop_rect(rect)
        for i in range(3):
            update_channel_preview(main_window, i)
        update_main_display(main_window)
```

`state.crop_mode` remains `False` after restore; the crop rectangle is active
immediately for display and saving.

### Final UI updates

```text
main_window.update_save_button_state()
status_bar.set_message("Session restored", MEDIUM_TIMEOUT)
```

If no channels were successfully restored, the app starts in an empty state but
without errors.

---

## Clearing Autosave – `clear_autosave(main_window)`

Autosave is cleared when the user resets the application via the **New** action.

### Flow

```text
User clicks "New" toolbar/menu action
    │
    ▼
MainWindow.reset_to_defaults()
    │
    ├── svc.reset()                  # clear image arrays
    │
    ├── state.reset()                # reset AppState to defaults
    │
    ├── clear_autosave(main_window)  # remove autosave.json from disk
    │
    ├── for each ChannelController:
    │       reset_all_sliders()
    │
    ├── viewer.clear()               # clear crop + display
    │
    ├── update_main_display(main_window)
    │
    ├── update_save_button_state()
    │
    └── status_bar.set_message("Reset to defaults", SHORT_TIMEOUT)
```

```text
clear_autosave(main_window)
    │
    ├── path = _autosave_path(main_window)
    │
    ├── try:
    │       os.remove(path)
    │   except OSError:
    │       pass  # missing file is not an error
    │
    └── return
```

After clearing autosave, the next application start will not attempt to restore
any previous session.

---

## Cross-Feature Interactions in the Flow

- **Channel Loading:** autosave reads and writes only file paths; loading/
  alignment logic is shared with the regular channel-loading flow.
- **Adjustments:** autosave is driven exclusively by slider changes; restoring a
  session replays those adjustments on newly aligned images.
- **Crop:** only the saved crop rectangle is persisted; the temporary editing
  rect in Crop mode is never written to disk.
- **Presets:** presets are not referenced by name; autosave sees only the final
  slider values they produced.
- **Reset (New):** both in-memory state and autosave file are cleared together,
  ensuring that the next startup reflects a truly fresh session.
