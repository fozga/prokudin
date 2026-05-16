# Autosave

## Contract

The autosave feature persistently stores the current working session — channel file
paths, adjustment sliders, and crop rectangle — so that the application can restore
this state on the next launch. Autosave is:

- **Automatic:** triggered via a debounced timer after slider changes; the user does
  not manually request it.
- **Non-intrusive:** never shows dialogs; all failures are silent or reported via
  the status bar.
- **Idempotent:** overwriting the same `autosave.json` file repeatedly.

Autosave never writes image pixel data to disk, only small JSON metadata.

---

## Storage Location and Format

### File path

Autosave uses a single JSON file in the config directory determined by
`src.ui.config.get_config_dir()`:

```python
_AUTOSAVE_FILENAME = "autosave.json"

# Effective path:
path = os.path.join(main_window.config_dir, _AUTOSAVE_FILENAME)
```

Typical locations, in order of preference:

1. `/app/config` (container environment)
2. `<project_root>/config`
3. `~/.config/prokudin`

### JSON structure

```json
{
  "version": 1,
  "channels": {
    "red":   { "path": "/abs/path/to/red.arw",   "brightness": 0, "contrast": 0, "intensity": 100 },
    "green": { "path": "/abs/path/to/green.arw", "brightness": 0, "contrast": 0, "intensity": 100 },
    "blue":  { "path": "/abs/path/to/blue.arw",  "brightness": 0, "contrast": 0, "intensity": 100 }
  },
  "crop": {
    "x": 120,
    "y": 80,
    "width": 160,
    "height": 120
  }
}
```

Semantics:

- `version` — format version (currently `1`). Reserved for future migrations.
- `channels` — per-spectral-slot state keyed by `"red"`, `"green"`, `"blue"`.
  - `path` — absolute path to the ARW file originally loaded into that slot.
  - `brightness`, `contrast`, `intensity` — slider values at the time of autosave.
- `crop` — persisted crop rectangle in image coordinates.
  - If absent or invalid, no crop is restored.

---

## Save Path — `save_autosave(main_window)`
`src/ui/handlers/autosave.py`

`save_autosave()` serialises the current session state to `autosave.json`.

### Data collection

```python
channels = {}
for i, name in enumerate(["red", "green", "blue"]):
    ctrl = main_window.controllers[i]
    channels[name] = {
        "path": main_window.state.channel_paths[i],
        "brightness": ctrl.sliders["brightness"].value(),
        "contrast":   ctrl.sliders["contrast"].value(),
        "intensity":  ctrl.sliders["intensity"].value(),
    }
```

Crop rectangle:

```python
saved_crop = main_window.viewer.get_saved_crop_rect() if main_window.viewer else None
crop = None
if saved_crop and saved_crop.isValid():
    crop = {
        "x": saved_crop.x(),
        "y": saved_crop.y(),
        "width": saved_crop.width(),
        "height": saved_crop.height(),
    }
```

Final payload:

```python
data = {
    "version": 1,
    "channels": channels,
    "crop": crop,
}
```

### Writing to disk

```python
with open(_autosave_path(main_window), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
```

I/O errors (e.g. permission issues) are caught and logged via `logging.warning`;
no exception propagates to the GUI layer.

---

## Restore Path — `restore_autosave(main_window)`

`restore_autosave()` is called once from `MainWindow.__init__()` after the UI has
been constructed. If no autosave file exists, it returns immediately.

### File loading

```python
path = _autosave_path(main_window)
if not os.path.exists(path):
    return

with open(path, encoding="utf-8") as f:
    data = json.load(f)
```

Malformed JSON (e.g. truncated file) is caught via `json.JSONDecodeError` and
ignored — no state is restored, and no exception is raised.

### Channel restoration

For each spectral slot `name` in `{"red", "green", "blue"}`:

1. Read `filepath = ch_data.get("path")` from the JSON.
2. If `filepath` is a string and `os.path.exists(filepath)` is `True`, call
   `load_channel_from_path(main_window, i, filepath)`.
3. If the file is missing or cannot be decoded, the corresponding handler reports
   an error via the status bar but does not abort the restore process.

### Slider restoration

For each channel index `i`:

1. Read the channel dict `ch_data` from JSON.
2. For each slider name in `{ "brightness", "contrast", "intensity" }`:
   - Check that the JSON value is an `int`.
   - Set `ctrl.sliders[slider_name].value` to that value.
   - If the controller has a text input for the slider, set its text to the same
     value.
3. All slider updates are wrapped in `ctrl.blockSignals(True/False)` so that
   no `value_changed` signals fire during restoration.

After sliders are restored and channels are loaded:

```python
for i in range(3):
    if main_window.svc.aligned[i] is not None:
        adjust_channel(main_window, i)       # apply adjustments
    update_channel_preview(main_window, i)   # refresh thumbnails
```

### Crop restoration

If `data.get("crop")` is a valid dict with numeric `x`, `y`, `width`, `height`
values and `width > 0`, `height > 0`, a `QRect` is constructed and applied:

```python
crop_rect = QRect(int(x), int(y), int(w), int(h))
main_window.viewer.set_saved_crop_rect(crop_rect)
for i in range(3):
    update_channel_preview(main_window, i)
```

### Final UI updates

At the end of restoration:

- `main_window.update_save_button_state()` is called to reflect the presence of
  processed channels.
- The status bar is updated to "Session restored" with a medium timeout.

---

## Clear Path — `clear_autosave(main_window)`

`clear_autosave()` removes the autosave file from disk when the user resets the
application via the **New** button.

```python
try:
    os.remove(_autosave_path(main_window))
except OSError:
    pass  # Absence of autosave file is not an error
```

After clearing autosave, `MainWindow.reset_to_defaults()` also resets in-memory
state (`AppState`, `ImageProcessorService`, widgets), ensuring that the next
startup begins from a fully clean state.

---

## Triggering and Debounce Logic

Autosave is not triggered on every state change; only slider movements schedule a
save via a debounced timer owned by `MainWindow`:

```python
self._autosave_timer = QTimer()
self._autosave_timer.setSingleShot(True)
self._autosave_timer.setInterval(500)  # 500 ms
self._autosave_timer.timeout.connect(lambda: save_autosave(self))
```

Every slider change in a `ChannelController` emits `value_changed`, and the
connected slot restarts the timer. As long as the user keeps adjusting sliders,
the timer is reset and no autosave occurs. Once the user pauses for at least
500 ms, the timer fires exactly once and writes the current state.

Key points:

- Autosave is **slider-driven only** — loading new channels or changing crop
  ratio does not immediately trigger a save. The next slider change will include
  any such state in the JSON.
- The timer is single-shot; there is never more than one pending autosave.

---

## Interactions with Other Features

| Feature | Relationship |
|---|---|
| **Channel Loading** | Saves `AppState.channel_paths` so that `restore_autosave()` can reload channels from their original paths. |
| **Adjustments** | Persists per-channel brightness, contrast, and intensity. After restore, `adjust_channel()` is called to reapply adjustments to newly aligned images. |
| **Crop** | Persists only the confirmed crop rectangle (`saved`), not the temporary rect in edit. Crop is applied to previews and combined display after restore. |
| **Image Saving** | Reads the crop rectangle that may have been restored earlier, but does not write anything back to autosave. |
| **Reset (New)** | Calls `clear_autosave()` and resets all in-memory state, ensuring the next launch starts with no restored session. |

---

## Constraints and Failure Modes

- Autosave does not detect or handle renamed/moved source files. If an ARW file
  path stored in `autosave.json` no longer exists, that channel is simply skipped
  on restore and a status bar error is shown.
- Permissions issues (read-only config directory, disk full) prevent autosave
  from writing. These are logged but do not interrupt the user's workflow.
- The autosave file is not encrypted or checksummed; a corrupted JSON file is
  ignored entirely.
- Only a single autosave slot exists. There is no multi-session or bookmark
  support.
