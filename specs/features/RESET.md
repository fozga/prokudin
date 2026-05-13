# Reset

## Contract

The Reset feature returns the application to a clean, ready-to-use state. It:

- Clears all loaded images and intermediate processing results.
- Restores all UI state and sliders to their default values.
- Clears the saved crop rectangle and exits Crop mode.
- Deletes any autosaved session data so the next launch starts fresh.

Reset does **not** remove user presets or alter configuration files other than
`autosave.json`.

---

## User-Facing Behaviour

### Entry points

Users can trigger Reset via:

- The **New** toolbar button or menu action.
- A keyboard shortcut (e.g. `Ctrl+N` or platform-specific equivalent), wired to
  the same slot.

Both entry points call the same `MainWindow.reset_to_defaults()` method.

### What the user sees

After Reset:

- The three channel previews are empty; all sliders snap back to their defaults.
- The main viewer shows an empty placeholder (no image).
- Crop controls are hidden and grid remains in its current configuration.
- The Save button is disabled.
- The status bar shows a short message such as "Reset to defaults" and the mode
  indicator reverts to "Load images".

User presets in the left sidebar remain visible and can be applied to new
sessions.

---

## Responsibilities by Component

| Component | Responsibility |
|---|---|
| `MainWindow` | Coordinates the reset operation: calls service, state, autosave, widgets, and display updates in the correct order. |
| `ImageProcessorService` | Drops all image arrays and adjustment structures. After reset it behaves as if no channels were ever loaded. |
| `AppState` | Resets all UI state flags and stored paths to compile-time defaults from `DefaultState`. |
| `ChannelController` | Resets its sliders and preview image to defaults. |
| `CropHandler` / `ImageViewer` | Clears any saved crop rectangle and exits Crop mode. |
| `autosave` handlers | Remove `autosave.json` so the next run does not restore the old session. |
| `StatusBarHandler` | Shows a brief confirmation message and updates mode to match the empty state. |

---

## Reset Sequence – `MainWindow.reset_to_defaults()`

`reset_to_defaults()` performs a multi-step reset in a specific order to avoid
flicker and inconsistent intermediate states.

### High-level flow

```text
reset_to_defaults()
    │
    ├── stop background timers (autosave, etc.)
    │
    ├── svc.reset()                     # clear image data
    │
    ├── state.reset()                   # AppState ← DefaultState
    │
    ├── clear_autosave(self)            # remove autosave.json
    │
    ├── for each ChannelController:
    │       reset_all_sliders()         # restore brightness/contrast/intensity
    │       clear_image()               # clear preview thumbnail
    │
    ├── viewer.clear_all()             # clear main image and crop rectangles
    │
    ├── update_main_display(self)      # show empty placeholder
    │
    ├── update_channel_preview(self, i) for i in 0..2
    │
    ├── update_save_button_state()     # disable Save
    │
    └── status_bar.set_message("Reset to defaults", SHORT_TIMEOUT)
```

### Service reset – `ImageProcessorService.reset()`

`reset()` restores the service to its initial state:

- Sets `original_images`, `original_rgb_images`, `aligned`, `aligned_rgb`, and
  `processed` to `[None, None, None]`.
- Resets the per-channel `adjustments` list to default brightness/contrast
  values.
- Clears any cached dimensions or metadata used by the UI.

After `reset()`, all query methods such as `get_channel()`, `get_combined()`, and
`has_aligned_channels()` behave as if no images were ever loaded.

### UI state reset – `AppState.reset()`

`AppState.reset()` is responsible for restoring UI-related state to
compile-time constants defined in `DefaultState`:

- `channel_paths = [None, None, None]`
- `show_combined = DefaultState.SHOW_COMBINED` (True)
- `current_channel = DefaultState.CURRENT_CHANNEL` (0 → Red)
- `crop_mode = DefaultState.CROP_MODE` (False)
- `crop_ratio = None`
- References to transient widgets (e.g. grid settings dialog) are cleared or
  reinitialised as needed.

The reset of `AppState` does not touch any image arrays; those live exclusively
in `ImageProcessorService` and are reset separately.

### Widget reset – `ChannelController`

Each `ChannelController` exposes a `reset_all_sliders()` method that:

- Sets brightness, contrast, and intensity sliders to `DefaultState` values.
- Updates the paired text fields to match the new slider values.
- Emits a single `value_changed` signal after all sliders have been reset.

Immediately after resetting sliders, `clear_image()` is called to:

- Clear the internal `processed_image` reference.
- Replace the preview label with a placeholder (e.g. "No image").

### Viewer and crop reset

The viewer and crop-related components are reset as follows:

- `CropHandler.cancel_crop()` is called (directly or via a wrapper) to:
  - Clear the current and saved crop rectangles.
  - Exit Crop mode and hide handles.
- `ImageViewer` clears the currently displayed pixmap and any scene items
  related to the previous image.
- `AppState.crop_mode` is set to `False` and `crop_ratio` to `None`.

---

## Autosave Interaction

Reset and autosave interact in a controlled way:

- `reset_to_defaults()` calls `clear_autosave(self)` to remove `autosave.json`.
- The next application start finds no autosave file and therefore does **not**
  call `restore_autosave()`.
- Any existing in-memory state at the time of reset is discarded and not written
  again because the autosave timer is stopped before `save_autosave()` can run.

Autosave does not persist anything about Reset itself; it only stores session
state that existed before the reset.

---

## Presets and Configuration

Reset is intentionally conservative regarding user configuration:

- Preset JSON and thumbnails in `presets_dir` are untouched.
- Application configuration files (logging, paths, etc.) are untouched.
- Only the autosave file is removed.

This allows users to experiment freely and return to a clean state without
risking loss of custom presets.

---

## Constraints and Edge Cases

- Reset is safe to call even when no images have been loaded; in that case it
  effectively becomes a no-op beyond ensuring defaults.
- If `clear_autosave()` fails due to filesystem permissions or a missing file,
  the error is ignored; the application continues with all in-memory state reset.
- Reset does not reload any UI language or theme settings; those are assumed to
  be outside the scope of this feature.
