# Crop – Flow

This document describes the control and data flow for the Crop feature: entering and
exiting Crop mode, editing the rectangle, accepting/cancelling, and applying crop to
display and saving.

---

## Legend

- **User action** — direct UI interaction (click, drag).
- **UI widget** — Qt widget (buttons, viewer, controls).
- **Handler** — function in `src/ui/handlers/`.
- **Viewer** — `ImageViewer` and its `CropHandler` / `GridOverlay`.
- **Service** — `ImageProcessorService` methods.

---

## Entering Crop Mode

### Flow

```text
User clicks "Crop" button
    │
    ▼
UI: Crop button in toolbar / menu
    │  connected to MainWindow.slot_toggle_crop_mode()
    ▼
MainWindow.slot_toggle_crop_mode()
    │
    ├── if not state.crop_mode:
    │       enter_crop_mode()
    │   else:
    │       exit_crop_mode(discard_current=False)
    │
    ▼
enter_crop_mode()
    │
    ├── if no image is loaded (svc.has_aligned_channels() is False):
    │       return  # nothing to crop
    │
    ├── state.crop_mode = True
    │
    ├── viewer.crop_handler.set_crop_mode(True, photo)
    │       if saved rect exists:
    │           current = copy(saved)
    │       else:
    │           current = 80% of image size, centred
    │       if crop_ratio is set:
    │           adjust current to respect ratio
    │       mark viewport for repaint
    │
    ├── show crop controls widget (ratio combo, Accept, Cancel)
    │
    └── status_bar.set_mode("Cropping")
```

When entering Crop mode, the **saved** crop rectangle is not yet applied to the
main display; the user is editing the **current** rectangle only.

---

## Editing the Crop Rectangle

Rectangle editing is handled entirely within `CropHandler`, attached to the
`ImageViewer`'s scene.

### Mouse interaction

```text
User presses mouse button inside viewer
    │
    ▼
ImageViewer.mousePressEvent(event)
    │
    └── if crop_handler.is_crop_mode_active():
            crop_handler.handle_mouse_press(event)

crop_handler.handle_mouse_press(event)
    │
    ├── if no current rect:
    │       start new rect at mouse position
    │       _drag_info["handle"] = "bottom-right"  # grow from initial point
    │
    ├── elif click near a corner handle:
    │       _drag_info["handle"] = "top-left" / "top-right" / ...
    │       _rectangles["original"] = copy(current)
    │       _drag_info["start"] = mouse_pos
    │
    ├── elif click near an edge handle:
    │       _drag_info["handle"] = "left" / "right" / "top" / "bottom"
    │       snapshot original rect and start position
    │
    ├── elif click inside rect:
    │       _drag_info["handle"] = "interior"  # move
    │       snapshot original rect and start position
    │
    └── _state["dragging"] = True
```

```text
User moves mouse with button held
    │
    ▼
ImageViewer.mouseMoveEvent(event)
    │
    └── if crop_handler.is_dragging():
            crop_handler.handle_mouse_move(event)

crop_handler.handle_mouse_move(event)
    │
    ├── if _drag_info["handle"] is a corner:
    │       compute new width/height from drag delta
    │       enforce aspect ratio if _crop_ratio is set
    │       clamp rect to image bounds
    │
    ├── elif edge handle:
    │       adjust one dimension only, clamp to bounds
    │
    ├── elif "interior":
    │       translate rect by drag delta, clamp to bounds
    │
    └── request viewport repaint
```

```text
User releases mouse button
    │
    ▼
ImageViewer.mouseReleaseEvent(event)
    │
    └── crop_handler.handle_mouse_release(event)

crop_handler.handle_mouse_release(event)
    │
    ├── _state["dragging"] = False
    ├── _drag_info.clear()
    └── (optional) normalise rect (ensure width/height > 0)
```

> Planned (issue #56): all geometry calculations in `handle_mouse_move()` will be
> delegated to pure helpers in `src/core/crop_geometry.py`.

---

## Accepting Crop

### Flow

```text
User clicks "Accept" button in crop controls
    │
    ▼
UI: Accept button
    │  connected to MainWindow.slot_accept_crop()
    ▼
MainWindow.slot_accept_crop()
    │
    ├── if not state.crop_mode:
    │       return
    │
    ├── viewer.crop_handler.confirm_crop(photo)
    │       if current rect exists and is valid:
    │           _rectangles["saved"] = copy(current)
    │       _state["crop_mode"] = False
    │       hide handles, request repaint
    │
    ├── state.crop_mode = False
    │
    ├── hide crop controls widget
    │
    ├── update_channel_preview(main_window, i) for i in 0..2
    │       (previews now reflect saved crop)
    │
    ├── update_main_display(main_window)
    │       combined / single-channel view uses saved crop
    │
    ├── update_save_button_state()
    │       (cropped dimensions may change but Save remains available)
    │
    └── status_bar.set_mode("Editing")
```

After Accept, the saved crop rectangle is applied everywhere that uses
`get_saved_crop_rect()` — previews, combined view, and saving.

---

## Cancelling Crop

### Flow

```text
User clicks "Cancel" button in crop controls
    │
    ▼
UI: Cancel button
    │  connected to MainWindow.slot_cancel_crop()
    ▼
MainWindow.slot_cancel_crop()
    │
    ├── if not state.crop_mode:
    │       return
    │
    ├── viewer.crop_handler.cancel_crop()
    │       _rectangles["current"] = None
    │       _state["crop_mode"] = False
    │       request repaint (no handles, no overlay)
    │       # _rectangles["saved"] is NOT changed
    │
    ├── state.crop_mode = False
    │
    ├── hide crop controls widget
    │
    ├── update_main_display(main_window)
    │       uses existing saved crop (if any)
    │
    └── status_bar.set_mode("Editing")
```

Cancelling leaves the previously saved crop rectangle (if any) in effect. If no
crop was previously saved, the application returns to uncropped view.

---

## Applying Crop in Display Flow

The display handlers apply crop by reading the saved rectangle from the viewer
and passing it as a tuple to `ImageProcessorService` query methods.

### Combined view

```text
update_main_display(main_window)
    │
    ├── saved = main_window.viewer.get_saved_crop_rect()
    │
    ├── if state.crop_mode:
    │       crop_tuple = None  # editing, do not apply saved crop
    │   elif saved is not None:
    │       crop_tuple = (saved.left(), saved.top(), saved.width(), saved.height())
    │   else:
    │       crop_tuple = None
    │
    ├── intensities = [ctrl.sliders["intensity"].value() for ctrl in controllers]
    │
    ├── img = svc.get_combined(crop=crop_tuple, intensities=intensities)
    │
    └── if img is not None:
            show_combined_image(main_window, img)
        else:
            show_empty_placeholder()
```

### Single-channel view

```text
update_main_display(main_window)
    │
    ├── saved = main_window.viewer.get_saved_crop_rect()
    │
    ├── if state.crop_mode:
    │       crop_tuple = None
    │   elif saved is not None:
    │       crop_tuple = (saved.left(), saved.top(), saved.width(), saved.height())
    │   else:
    │       crop_tuple = None
    │
    ├── idx = state.current_channel
    │
    ├── img = svc.get_channel(idx, crop=crop_tuple)
    │
    └── if img is not None:
            show_single_channel_image(main_window, idx, img)
        else:
            show_empty_placeholder()
```

### Channel previews

`update_channel_preview(main_window, idx)` uses `svc.get_channel_preview(idx)` and
does **not** apply crop. Previews show full-channel content regardless of crop,
providing a consistent reference while editing the crop.

---

## Applying Crop in Save Flow

Saving uses the same saved crop rectangle as display, but resolved in
`image_saving.py`.

### Flow snippet

```text
save_image_with_dialog(main_window)
    │
    ├── saved_crop_rect = main_window.viewer.get_saved_crop_rect() if viewer else None
    │
    ├── if state.crop_mode:
    │       crop_rect = None  # do not apply incomplete crop
    │   elif saved_crop_rect is not None:
    │       crop_rect = (
    │           saved_crop_rect.left(),
    │           saved_crop_rect.top(),
    │           saved_crop_rect.width(),
    │           saved_crop_rect.height(),
    │       )
    │   else:
    │       crop_rect = None
    │
    ├── for each aligned_rgb[i]:
    │       img_to_save = apply_crop(aligned_rgb[i], crop_rect)
    │       save_image(img_to_save, "..._ir/vis/uv...", file_format, is_bgr=True)
    │
    └── combined = _create_combined_image(aligned, crop_rect)
            if combined is not None:
                save_image(combined, filepath, file_format, is_bgr=False)
```

`apply_crop` clamps the crop rectangle to valid bounds and ensures that width and
height are at least 1 pixel.

---

## Interaction with Autosave

Autosave persists only the **saved** crop rectangle (`_rectangles["saved"]`),
never the temporary current rect.

### Save

```text
save_autosave(main_window)
    │
    ├── saved = viewer.get_saved_crop_rect()
    │
    ├── if saved and saved.isValid():
    │       crop = {"x": saved.x(), "y": saved.y(),
    │               "width": saved.width(), "height": saved.height()}
    │   else:
    │       crop = None
    │
    └── write crop into autosave.json
```

### Restore

```text
restore_autosave(main_window)
    │
    ├── crop_data = data.get("crop")
    │
    ├── if crop_data has valid x, y, width, height:
    │       crop_rect = QRect(int(x), int(y), int(w), int(h))
    │       viewer.set_saved_crop_rect(crop_rect)
    │       for i in 0..2:
    │           update_channel_preview(main_window, i)
    │       update_main_display(main_window)
    │
    └── crop_mode remains False after restore
```

After restore, the saved crop is immediately active in both display and saving
until the user enters Crop mode again.
