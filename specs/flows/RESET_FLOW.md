# Reset – Flow

This document describes the control and data flow for the Reset feature:
triggering a reset from the UI, coordinating state and widget resets, and
interactions with autosave.

For behaviour and responsibilities see `specs/features/RESET.md`.

---

## Legend

- **User action** — click or keyboard shortcut.
- **UI widget** — toolbar button, menu item, status bar.
- **Handler** — `MainWindow` slots and helper functions.
- **Service** — `ImageProcessorService` methods.
- **State** — `AppState` fields.

---

## Entry Points

Reset is exposed through a single `MainWindow.reset_to_defaults()` method that is
invoked from multiple UI entry points.

### Toolbar / menu

```text
User clicks "New" toolbar button or menu action
    │
    ▼
QAction.triggered(bool)
    │  connected in MainWindow.__init__
    ▼
MainWindow.reset_to_defaults()
```

### Keyboard shortcut

```text
User presses Ctrl+N (or platform-specific equivalent)
    │
    ▼
QShortcut activated
    │  connected to same slot
    ▼
MainWindow.reset_to_defaults()
```

All entry points share the exact same implementation; there is no special-case
logic per source.

---

## Reset Orchestration – `reset_to_defaults()`

`reset_to_defaults()` coordinates the reset across all layers. The order of
operations is important to avoid unnecessary work and inconsistent UI states.

### High-level sequence

```text
reset_to_defaults()
    │
    ├── stop timers (autosave, etc.)
    │
    ├── svc.reset()                     # clear image data + adjustments
    │
    ├── state.reset()                   # AppState ← DefaultState
    │
    ├── clear_autosave(self)            # delete autosave.json from disk
    │
    ├── reset_channel_controllers()     # sliders + thumbnails
    │
    ├── reset_viewer_and_crop()         # clear image + crop rectangles
    │
    ├── update_main_display(self)       # redraw empty viewer
    │
    ├── for i in 0..2:
    │       update_channel_preview(self, i)
    │
    ├── update_save_button_state()      # disable Save
    │
    └── status_bar_after_reset()
```

The following sections expand each step.

---

## Step 1 – Stop Timers

Before mutating state, reset stops background timers that might otherwise
schedule work based on outdated data (primarily the autosave timer).

```text
if self._autosave_timer.isActive():
    self._autosave_timer.stop()
```

Stopping the timer ensures that no `save_autosave()` call occurs after the
in-memory state has been cleared.

---

## Step 2 – Service Reset (`svc.reset()`)

`ImageProcessorService.reset()` clears all image-related state.

### Flow

```text
svc.reset()
    │
    ├── original_images      = [None, None, None]
    ├── original_rgb_images  = [None, None, None]
    ├── aligned              = [None, None, None]
    ├── aligned_rgb          = [None, None, None]
    ├── processed            = [None, None, None]
    ├── adjustments          = [ChannelAdjustments(0, 0), ...]
    └── cached dimensions / metadata cleared
```

After this call:

- `has_aligned_channels()` and `has_processed_channels()` both return `False`.
- Display and saving operations see no available images.

---

## Step 3 – UI State Reset (`state.reset()`)

`AppState.reset()` restores UI flags and paths to their compile-time defaults.

### Flow

```text
state.reset()
    │
    ├── channel_paths = [None, None, None]
    ├── show_combined = DefaultState.SHOW_COMBINED   # True
    ├── current_channel = DefaultState.CURRENT_CHANNEL  # 0
    ├── crop_mode = DefaultState.CROP_MODE           # False
    ├── crop_ratio = None
    ├── grid_settings_dialog = None (or left intact depending on implementation)
    └── other UI-only fields reset as needed
```

State reset does not touch widgets or image arrays directly; it only updates the
logical representation of UI state.

---

## Step 4 – Clear Autosave (`clear_autosave(self)`) 

Reset clears the persisted session so that the next application start does not
attempt to restore the pre-reset state.

### Flow

```text
clear_autosave(main_window)
    │
    ├── path = _autosave_path(main_window)
    │
    ├── try:
    │       os.remove(path)
    │   except OSError:
    │       pass  # missing file or permission issue is ignored
    │
    └── return
```

Autosave is the only on-disk state that Reset modifies.

---

## Step 5 – Reset Channel Controllers

Each `ChannelController` is reset to default slider values and cleared of any
preview image.

### Flow

```text
reset_channel_controllers()
    │
    └── for ctrl in main_window.controllers:
            ctrl.reset_all_sliders()
                # sets brightness, contrast, intensity → DefaultState
                # emits single value_changed after all sliders are set

            ctrl.clear_image()
                # sets processed_image = None
                # preview_label shows placeholder text or empty frame
```

Because timers are stopped and service arrays are already cleared, the
`value_changed` emission during `reset_all_sliders()` does not trigger any
meaningful processing.

---

## Step 6 – Reset Viewer and Crop

The viewer and crop components are reset so that no crop rectangle or image is
left in the scene.

### Flow

```text
reset_viewer_and_crop()
    │
    ├── if viewer has a crop handler:
    │       crop_handler.cancel_crop()
    │           _rectangles["current"] = None
    │           _rectangles["saved"]   = None
    │           _state["crop_mode"]    = False
    │           request repaint
    │
    ├── viewer.clear_image()
    │       # remove pixmap from the scene / viewport
    │
    └── ensure AppState.crop_mode = False, AppState.crop_ratio = None
```

Grid overlay configuration is left untouched; only crop and image content are
cleared.

---

## Step 7 – Display and Save Button Updates

After internal state and widgets have been reset, the UI is brought into a
consistent visible state.

### Main display

```text
update_main_display(main_window)
    │
    ├── detects that svc.has_processed_channels() is False
    │
    ├── shows empty placeholder image or background in viewer
    │
    └── ensures zoom/pan are reset or left unchanged depending on design
```

### Channel previews

```text
for i in 0..2:
    update_channel_preview(main_window, i)
        # sees that svc.get_channel_preview(i) is None
        # ChannelController preview labels show "No image" or are blank
```

### Save button state

```text
update_save_button_state()
    │
    ├── enabled = svc.has_aligned_channels() and svc.has_processed_channels()
    │
    └── save_button.setEnabled(False)  # after reset
```

---

## Step 8 – Status Bar Update

The final step is to inform the user that the reset has completed.

### Flow

```text
status_bar_after_reset()
    │
    ├── status_bar.set_mode("Load images")
    │
    └── status_bar.set_message("Reset to defaults", SHORT_TIMEOUT)
```

This makes it clear that the application is ready for a new set of channel
images.

---

## Interaction with Other Flows

- **Autosave Flow:** Reset stops the autosave timer and deletes `autosave.json`.
  Subsequent slider changes will start a new autosave cycle for the fresh
  session.
- **Channel Loading Flow:** After reset, the next call to `load_channel()` or
  `restore_autosave()` behaves as if the app was started for the first time.
- **Crop Flow:** Reset fully clears both saved and current crop rectangles;
  entering Crop mode after reset starts with a fresh default rect once new
  images are loaded.
- **Presets Flow:** Reset does not alter the preset files or sidebar contents.
  Users can immediately apply existing presets to newly loaded channels.
