# Channel Loading – Flow

This document describes the control and data flow for loading channel images into
Prokudin. It covers both the interactive file-dialog path and the autosave restore
path.

---

## Legend

- **User action** — direct UI interaction (click, keypress).
- **UI widget** — Qt widget that receives the action.
- **Handler** — function in `src/ui/handlers/`.
- **Service** — `ImageProcessorService` methods.
- **Core** — pure functions in `src/core/`.

---

## Interactive Load – Single Channel

### High-level flow

```
User clicks "Load" button on a ChannelController
    │
    ▼
UI widget: ChannelController.btn_load
    │  (connected in MainWindow.init_ui)
    ▼
Handler: load_channel(main_window, channel_idx)
    │
    ▼
Handler: load_raw_image(parent=main_window)         [image_loading.py]
    │  QFileDialog.getOpenFileName("*.arw")
    │  → (filename, filter) or ("", "")
    │
    ├── if filename == "":
    │       return (None, None, "No file selected")
    │
    ├── else:
    │       with rawpy.imread(filename) as raw:
    │           rgb = raw.postprocess(...)
    │       return (rgb, filename, None)
    │
    ▼
Back in load_channel()
    │
    ├── if rgb_image is not None and file_path is not None:
    │       main_window.state.channel_paths[channel_idx] = file_path
    │       _process_channel_image(main_window, channel_idx, rgb_image)
    │   else:
    │       if err_msg != "No file selected":
    │           status_bar.set_message(err_msg, LONG_TIMEOUT)
    │       return
    │
    ▼
Handler: _process_channel_image(main_window, channel_idx, rgb_image)
    │
    ├──► Service: svc.load_channel_from_array(channel_idx, rgb_image)
    │       original_rgb_images[idx] = rgb
    │       original_images[idx]     = cvtColor(rgb, GRAY)
    │       processed[idx]           = copy(grayscale)
    │       all 3 channels present?
    │           YES → _perform_alignment()      (see Alignment flow)
    │                  processed[0..2] updated via _update_processed_image()
    │           NO  → skip alignment for now
    │
    ├──► Status bar:
    │       "Successfully loaded image into <ChannelName> channel"
    │
    ├──► if svc.has_aligned_channels():
    │           for i in 0..2:
    │               adjust_channel(main_window, i)
    │               update_channel_preview(main_window, i)
    │           status: "All channels loaded successfully – Ready for editing!"
    │       else:
    │           update_channel_preview(main_window, channel_idx)
    │
    ├──► update_main_display(main_window)
    │
    └──► main_window.update_save_button_state()
            (enables Save button if any processed channels exist)
```

### Error paths

- **User cancels dialog**: `load_raw_image()` returns `("", ...)` →
  `rgb_image` is `None`, `err_msg` is "No file selected" → handler returns silently
  with no status bar message.
- **File cannot be read or decoded**: `rawpy` raises an exception → caught in
  `load_raw_image_from_path()` → `err_msg = "Error loading ARW file: …"` →
  status bar shows error with long timeout.
- **Alignment failure upon third load**: `_perform_alignment()` raises
  `AlignmentError` → caught elsewhere; `svc.has_aligned_channels()` stays `False`.
  Status bar shows an alignment-specific error; no combined view is available.

---

## Autosave Restore Path – Channels

On application startup, `restore_autosave(main_window)` attempts to reload
previously used channels without user interaction.

### Flow

```
MainWindow.__init__()
    │
    ▼
Handler: restore_autosave(main_window)             [autosave.py]
    │
    ├── path = _autosave_path(main_window)
    │   if not os.path.exists(path):
    │       return  # nothing to restore
    │
    ├── with open(path) as f:
    │       data = json.load(f)
    │
    ├── for i, name in enumerate(["red", "green", "blue"]):
    │       ch_data = data.get("channels", {}).get(name, {})
    │       filepath = ch_data.get("path")
    │       if isinstance(filepath, str) and os.path.exists(filepath):
    │           load_channel_from_path(main_window, i, filepath)
    │
    └── (slider and crop restoration handled separately — see AUTOSAVE spec)
```

### `load_channel_from_path` details

```python
load_channel_from_path(main_window, channel_idx, file_path)
    │
    ▼
rgb_image, err_msg = load_raw_image_from_path(file_path)
    │
    ├── if rgb_image is not None:
    │       main_window.state.channel_paths[channel_idx] = file_path
    │       _process_channel_image(main_window, channel_idx, rgb_image)
    │
    └── elif err_msg:
            status_bar.set_message(
                f"Failed to restore <ChannelName> channel: {err_msg}",
                LONG_TIMEOUT,
            )
```

The same `_process_channel_image()` function is used for both interactive and
path-based loading, ensuring identical behaviour (alignment, previews, display
update, Save button state).

### Error paths

- **Missing file:** `os.path.exists(filepath)` is `False` → channel is skipped,
  no exception raised, no call to `load_channel_from_path()`.
- **Unreadable or invalid ARW file:** `load_raw_image_from_path` returns
  `(None, err_msg)` → status bar shows
  "Failed to restore <ChannelName> channel: <err_msg>".
- Malformed autosave JSON is ignored; no restore is performed, and startup
  continues with empty state.

---

## Cross-Feature Interactions in the Flow

- **Alignment:** triggered by `_process_channel_image()` automatically once all
  three channels are loaded (either interactively or via autosave). See
  `specs/features/ALIGNMENT.md` and `specs/flows/ALIGNMENT_FLOW.md` for details.
- **Adjustments:** after alignment, `adjust_channel()` is called for each channel
  to apply restored or default brightness/contrast before updating the display.
- **Autosave:** channel paths written by `save_autosave()` are the source of truth
  for the restore path. Any changes made to the preset or slider state after
  loading are included in the next autosave write.
- **Save button state:** updated at the end of `_process_channel_image()` so that
  the availability of the Save action always reflects the presence of aligned
  and processed channels.
