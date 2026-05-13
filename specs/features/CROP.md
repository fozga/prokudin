# Crop

## Contract

The crop feature allows the user to define a rectangular region of interest on the
preview image and apply that region consistently across the main display, per-channel
previews, and image saving. Crop is:

- **Interactive:** controlled via a dedicated Crop mode with draggable handles.
- **Non-destructive:** the underlying image arrays are never modified; crop is
  applied as a view/window when reading or saving.
- **Persistent:** the last accepted crop rectangle is remembered across sessions
  via autosave.

The crop rectangle only affects the final display and exported images once it is
**accepted**. Cancelling a crop or leaving Crop mode discards the temporary rect
and leaves the previously saved crop (if any) untouched.

---

## Responsibilities and Ownership

| Component | Responsibility |
|---|---|
| `CropHandler` (`src/ui/widgets/crop_handler.py`) | Owns current and saved crop rectangles, handles mouse interaction and drawing. Qt-dependent. |
| `ImageViewer` (`src/ui/widgets/image_viewer.py`) | Hosts the `CropHandler` and shared `GridOverlay`. Exposes `get_saved_crop_rect()` / `set_saved_crop_rect()`. |
| `AppState` (`src/ui/app_state.py`) | Stores `crop_mode` flag and `crop_ratio` (aspect constraint) but not the rectangle itself. |
| `display` handlers (`src/ui/handlers/display.py`) | Apply the saved crop when fetching images from `ImageProcessorService` for display. |
| `image_saving` handlers (`src/ui/handlers/image_saving.py`) | Apply the saved crop when writing images to disk. |
| `autosave` handlers (`src/ui/handlers/autosave.py`) | Persist and restore the saved crop rectangle to/from JSON. |

---

## Modes and Lifecycle

### Crop mode flag

`AppState.crop_mode: bool` indicates whether the application is currently in Crop
mode. When `crop_mode` is `True`:

- The Crop controls widget (ratio selector, Accept, Cancel) is visible.
- The `CropHandler` shows its current rectangle and handles.
- The **saved** crop rectangle is **not** applied to the main display or saves;
  the user is still editing.

When `crop_mode` is `False`:

- If a saved crop rectangle exists, it is applied to the main display and image
  saving.
- The Crop controls widget is hidden.
- The `CropHandler` does not draw handles; only the grid (if enabled) is shown.

### Lifecycle

```
User clicks Crop button
    → enter_crop_mode()
        → CropHandler.set_crop_mode(True, photo)
            if saved rect exists: current = copy(saved)
            else: current = 80% of image, centred
            if ratio set: adjust current to ratio
        → AppState.crop_mode = True
        → show crop controls widget

User adjusts rectangle (drag/move/resize)
    → CropHandler updates current rect only
    → viewport is updated; no changes to saved rect yet

User clicks Accept Crop
    → CropHandler.confirm_crop(photo)
        saved rect = copy(current)
        set_crop_mode(False, photo)
    → AppState.crop_mode = False
    → hide crop controls widget
    → main display and image saving now use saved rect

User clicks Cancel Crop
    → CropHandler.cancel_crop()
        current rect = None
        set_crop_mode(False, None)
    → AppState.crop_mode = False
    → saved rect remains unchanged (may be None)
    → UI returns to non-crop view
```

---

## Aspect Ratio Constraints

The Crop controls widget exposes a ratio combo box with options:

- `Free` — no constraint
- `16:9`, `3:2`, `4:3`, `5:4`, `1:1`, `4:5`, `3:4`, `2:3`, `9:16`

The current selection is stored in `AppState.crop_ratio: Optional[Tuple[int,int]]`.
`CropHandler` enforces this ratio while the user is drawing or resizing the crop
rectangle:

- On entering Crop mode, if a ratio is active, the initial rectangle is immediately
  adjusted to match it.
- During drag operations, the rectangle is resized in such a way that
  `width / height ≈ ratio_w / ratio_h`.
- The rectangle is always clamped to the image bounds.

> Planned (issue #56): all ratio and clamping logic will be extracted to
> `src/core/crop_geometry.py` so that it can be unit-tested without Qt.

---

## Geometry and Interaction

### Internal state (CropHandler)

`CropHandler` maintains three internal rectangles and several helper fields:

| Key | Description |
|---|---|
| `_rectangles["current"]` | The temporary rectangle being drawn/edited in the current Crop session. |
| `_rectangles["saved"]` | The last accepted crop rectangle. Used for display and saving; persisted by autosave. |
| `_rectangles["original"]` | Snapshot of the rectangle at the start of a drag, used as a base for resize calculations. |
| `_state["crop_mode"]` | Whether Crop mode is active. Mirrors `AppState.crop_mode`. |
| `_state["dragging"]` | Whether a drag operation is in progress. |
| `_drag_info["handle"]` | Which handle is being dragged (corner, edge, or interior). |
| `_drag_info["start"]` | Initial mouse position in scene coordinates at mouse press time. |
| `_crop_ratio` | Current aspect ratio constraint (`(w, h)` or `None`). |

### Mouse interaction

High-level behaviour:

- **Mouse press:**
  - If no current rect exists yet, start a new rect at the press position.
  - If the press is near a handle, set `_drag_info["handle"]` accordingly.
  - If the press is inside the rect, treat it as a move (interior drag).
- **Mouse move:**
  - If dragging a corner handle, resize both width and height while enforcing
    the aspect ratio (if any).
  - If dragging an edge, resize in one dimension while clamping to image bounds.
  - If dragging interior, translate the rect without changing size.
  - After each update, request a viewport repaint.
- **Mouse release:**
  - Clear `_state["dragging"]` and `_drag_info`.

> Planned (issue #56): the above arithmetic will be delegated to
> `crop_geometry` helper functions such as `resize_top_left`, `edge_resize_free_aspect`,
> `clamp_rect_to_bounds`, etc.

### Drawing

`CropHandler.draw_foreground()` is responsible for rendering the crop overlay:

1. Draws a semi-transparent dark overlay over the entire image.
2. Clears the area inside the current rectangle to highlight it.
3. Draws the crop rectangle border.
4. Draws handles at the corners and midpoints of edges.
5. Uses the shared `GridOverlay` to draw any active grid **inside** the current
   crop rectangle (clipped), so the grid respects the crop region.

When Crop mode is disabled, `CropHandler` does not draw; only `GridOverlay`
(through `ImageViewer`) may draw across the full visible image.

---

## Applying Crop to Data

Crop is never applied in-place to arrays. Instead, it is passed as a tuple of
integers `(x, y, width, height)` to functions that read from the service.

### Display — `src/ui/handlers/display.py`

#### Combined view

```python
saved_crop_rect = main_window.viewer.get_saved_crop_rect()
crop_tuple = None if main_window.state.crop_mode else _qrect_to_tuple(saved_crop_rect)

combined = main_window.svc.get_combined(crop=crop_tuple, intensities=intensities)
```

If `crop_tuple` is not `None`, `get_combined()` returns a cropped RGB array:

- Input: full-size combined array, shape `H × W × 3`.
- Output: cropped array, shape `h × w × 3`.

#### Single-channel view

```python
saved_crop_rect = main_window.viewer.get_saved_crop_rect()
crop_tuple = None if main_window.state.crop_mode else _qrect_to_tuple(saved_crop_rect)

img = main_window.svc.get_channel(main_window.state.current_channel, crop=crop_tuple)
```

For display, the grayscale channel is stacked into RGB before conversion to
`QImage`.

### Channel previews

`update_channel_preview()` uses `svc.get_channel_preview(idx)`, which does **not**
apply crop. The small thumbnails in `ChannelController` always show full-channel
content for easier comparison.

### Saving — `src/ui/handlers/image_saving.py`

Before saving, the handler computes `crop_rect` in the same way as the display
code (using `get_saved_crop_rect()` and `crop_mode`). It then calls
`apply_crop(image, crop_rect)` for each image to be written.

`apply_crop` clamps the rectangle to image dimensions and ensures minimum size of
1×1 pixel. If `crop_rect` is `None`, it returns the input image unchanged.

---

## Persistence via Autosave

`save_autosave()` stores the saved crop rectangle in JSON if it exists and is
valid:

```python
saved_crop = main_window.viewer.get_saved_crop_rect()
if saved_crop and saved_crop.isValid():
    crop = {
        "x": saved_crop.x(),
        "y": saved_crop.y(),
        "width": saved_crop.width(),
        "height": saved_crop.height(),
    }
else:
    crop = None
```

`restore_autosave()` reconstructs the saved rect:

```python
crop_data = data.get("crop")
if isinstance(crop_data, dict):
    x = crop_data.get("x", 0)
    y = crop_data.get("y", 0)
    w = crop_data.get("width", 0)
    h = crop_data.get("height", 0)
    if all(isinstance(v, (int, float)) for v in [x, y, w, h]) and w > 0 and h > 0:
        crop_rect = QRect(int(x), int(y), int(w), int(h))
        main_window.viewer.set_saved_crop_rect(crop_rect)
        for i in range(3):
            update_channel_preview(main_window, i)
```

After restore, the saved crop immediately affects both per-channel previews and
the combined display, unless the user enters Crop mode (in which case the crop
is temporarily suspended while editing).

---

## Planned Core Extraction — `crop_geometry.py` (Issue #56)

Crop geometry logic is currently embedded in `CropHandler` and depends on Qt
classes such as `QRect` and `QPointF`, making it hard to unit-test. Issue #56
proposes a refactor that splits responsibilities:

- `src/core/crop_geometry.py` — pure geometry helpers operating on plain
  dataclasses and tuples:
  - `clamp_point_to_bounds(point, bounds)`
  - `clamp_rect_to_bounds(rect, bounds)`
  - `adjust_dimensions_to_ratio(width, height, ratio)`
  - `resize_top_left`, `resize_top_right`, `resize_bottom_left`, `resize_bottom_right`
  - Horizontal/vertical constraint helpers
  - `edge_resize_free_aspect(context)`
  - `get_anchor_point(handle, rect)`
- `CropHandler` — remains responsible for Qt event handling and drawing only,
  delegating geometry decisions to `crop_geometry`.

This change will not alter the observable behaviour of the crop feature but will
make its geometry rules testable at the `src/core/` layer.

---

## Constraints and Edge Cases

- Crop operates in **image pixel coordinates**, not in display coordinates.
  The rectangle is defined relative to the underlying image, regardless of zoom
  or pan in `ImageViewer`.
- Minimum crop size is enforced (e.g. 50×50 pixels in the current implementation)
  to avoid degenerate rectangles that are hard to manipulate.
- If the image is smaller than the minimum crop size, the initial crop covers the
  entire image.
- Crop is disabled when no image is loaded. Entering Crop mode with no photo
  has no effect.
- If the saved crop rectangle lies partially outside the image (e.g. after
  loading a smaller image), `apply_crop` clamps it to the valid area.
