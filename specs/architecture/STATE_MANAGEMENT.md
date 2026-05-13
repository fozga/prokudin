# State Management

## Overview

Application state is distributed across three distinct owners: `ImageProcessorService`
(image data), `AppState` (UI display decisions), and individual widgets (transient
interaction state). Understanding which owner holds which piece of state is essential
for correctly reading, modifying, and resetting the application.

The core rule: **image arrays never leave `ImageProcessorService` by reference.**
All other layers receive copies through the service's query methods.

---

## State Ownership Map

### `ImageProcessorService` — `src/services/processor.py`

Owns all image data. Zero Qt imports. Can be instantiated and tested without a
`QApplication`.

| Field | Type | Description |
|---|---|---|
| `original_images` | `List[Optional[np.ndarray]]` | Grayscale versions of the three loaded channels, converted immediately on load via `cv2.cvtColor(RGB→GRAY)`. Index: 0=R, 1=G, 2=B. |
| `original_rgb_images` | `List[Optional[np.ndarray]]` | Full RGB arrays as returned by rawpy. Preserved for use during alignment. |
| `aligned` | `List[Optional[np.ndarray]]` | Grayscale images after `align_images()`. Green and Blue are warped to match Red. Populated only after all three channels are loaded. |
| `aligned_rgb` | `List[Optional[np.ndarray]]` | RGB images after applying the same warp transforms as `aligned`. |
| `processed` | `List[Optional[np.ndarray]]` | Result of applying brightness/contrast to `aligned`. This is the working image used for display and export. |
| `adjustments` | `List[ChannelAdjustments]` | Per-channel `brightness` and `contrast` integers, last set by `adjust_channel()`. |

**Lifecycle:**

```
load_channel_from_array(idx, rgb)
    → original_rgb_images[idx] = rgb
    → original_images[idx]     = grayscale(rgb)
    → processed[idx]           = grayscale copy
    → all 3 loaded?
        YES → _perform_alignment()
                  → aligned[0..2]     = aligned grayscale
                  → aligned_rgb[0..2] = aligned RGB
                  → processed[0..2]   = copies of aligned grayscale
              → _update_processed_image(i) for each i
                  → processed[i] = apply_adjustments(aligned[i], brightness, contrast)

adjust_channel(idx, brightness, contrast)
    → adjustments[idx] = ChannelAdjustments(brightness, contrast)
    → _update_processed_image(idx)
        → processed[idx] = apply_adjustments(aligned[idx], brightness, contrast)

reset()
    → all fields reset to [None, None, None]
```

**⚠ Known issue — #48:** `get_channel(idx)` without a crop argument returns
`self.processed[idx]` directly (internal reference). Callers must not modify the
returned array until this is fixed. `get_channel(idx, crop=...)` correctly returns
a copy.

---

### `AppState` — `src/ui/app_state.py`

Owns UI-display decisions only. No image arrays. Instantiated by `MainWindow` and
passed implicitly through the `main_window` argument to every handler.

| Field | Type | Default | Description |
|---|---|---|---|
| `channel_paths` | `List[Optional[str]]` | `[None, None, None]` | Absolute file paths of the three loaded ARW files. Used by `save_autosave()` and `restore_autosave()`. |
| `show_combined` | `bool` | `True` | Whether the main viewer shows the combined RGB image (`True`) or a single channel (`False`). |
| `current_channel` | `int` | `0` | Index of the channel shown when `show_combined` is `False`. 0=R, 1=G, 2=B. |
| `crop_mode` | `bool` | `False` | Whether the application is in interactive crop mode. Controls UI visibility (crop controls widget) and display logic (crop rect not applied while in crop mode). |
| `crop_ratio` | `Optional[Tuple[int, int]]` | `None` | Active aspect ratio constraint during crop, e.g. `(16, 9)`. `None` means free-form crop. |
| `grid_settings_dialog` | `Optional[GridSettingsDialog]` | `None` | Reference to the singleton grid settings popup. Created on first use; reused on subsequent opens. |

**Reset:** `AppState.reset()` restores all fields to their `DefaultState` defaults.
Called by `MainWindow.reset_to_defaults()` (the "New" button).

---

### `CropHandler` — `src/ui/widgets/crop_handler.py`

Owns crop rectangle state. Qt-dependent (uses `QRect`, `QRectF`, `QPointF`).

| Field | Type | Description |
|---|---|---|
| `_rectangles["current"]` | `QRect \| None` | The temporary crop rectangle being drawn or resized in crop mode. Discarded on cancel. |
| `_rectangles["saved"]` | `QRect \| None` | The confirmed crop rectangle. Applied to `get_channel()` and `get_combined()` calls. Persisted to autosave. |
| `_rectangles["original"]` | `QRect \| None` | Snapshot of the rectangle at the start of a drag, used to compute resize deltas. |
| `_state["crop_mode"]` | `bool` | Whether the handler is in active crop mode. Mirrors `AppState.crop_mode`. |
| `_state["dragging"]` | `bool` | Whether a mouse drag is in progress. |
| `_drag_info["handle"]` | `str \| None` | Name of the handle being dragged (`"top-left"`, `"bottom-right"`, `"interior"`, etc.). |
| `_drag_info["start"]` | `QPointF \| None` | Scene coordinate of the initial mouse press. |
| `_crop_ratio` | `tuple[int, int] \| None` | Active aspect ratio constraint. Set by `MainWindow` when the ratio combo box changes. |

**Persistence bridge:** `get_saved_crop_rect()` / `set_saved_crop_rect()` are the
only public accessors used by `autosave.py` to persist and restore the crop rect
across sessions.

---

### `ChannelController` widget — `src/ui/widgets/channel_controller.py`

Each of the three `ChannelController` instances holds its own slider values as
Qt widget state. These are **not** stored in `AppState` — they live in the sliders
themselves.

| Widget state | Type | Description |
|---|---|---|
| `sliders["brightness"].value()` | `int` | Current brightness adjustment, ∈ [−100, 100]. |
| `sliders["contrast"].value()` | `int` | Current contrast adjustment, ∈ [−100, 100]. |
| `sliders["intensity"].value()` | `int` | Current intensity multiplier, ∈ [0, 100]. |
| `processed_image` | `np.ndarray \| None` | The last grayscale image set by `update_channel_preview()`. Displayed as a 160×120 thumbnail. |

Slider values are read by handlers (`autosave.py`, `presets.py`, `channels.py`)
directly from the widget. They are written by `restore_autosave()` and
`apply_preset()` using `blockSignals(True)` to prevent cascading updates.

---

### `GridOverlay` — `src/ui/widgets/grid_overlay.py`

Holds grid rendering settings. Owned by `ImageViewer`; shared reference held by
`CropHandler`.

| Field | Type | Default | Description |
|---|---|---|---|
| `_enabled` | `bool` | `True` | Whether any grid is drawn. Set to `False` when grid type "none" is selected. |
| `_grid_type` | `str` | `GRID_TYPE_3X3` | Active grid type string constant from `grid_types.py`. |
| `_line_width` | `int` | `4` | Line width in pixels, ∈ [1, 10]. |
| `_color` | `QColor` | White | Grid line colour. |
| `_opacity` | `int` | `128` | Alpha value ∈ [0, 255]. Semi-transparent by default. |

Grid state is **not persisted** to autosave or presets. It resets to defaults on
application restart.

---

## State Reset on "New"

When the user clicks the **New** button, `MainWindow.reset_to_defaults()` performs
a full state reset in this order:

1. `svc.reset()` — clears all image arrays in `ImageProcessorService`
2. `AppState.reset()` — restores all UI state fields to `DefaultState` defaults
3. `clear_autosave()` — deletes `autosave.json` from disk
4. Each `ChannelController.reset_all_sliders()` — resets slider widgets to defaults
5. `CropHandler` — saved and current crop rects are cleared via `cancel_crop()`
6. `update_main_display()` — refreshes the viewer (shows empty state)
7. `update_save_button_state()` — disables the Save button

---

## Autosave Bridge

`autosave.py` is the only code that serialises in-memory state to disk and
deserialises it back. It reads from two sources that are not stored in one place:

| Serialised field | Read from | Written to |
|---|---|---|
| `channel_paths` | `AppState.channel_paths` | `AppState.channel_paths` via `load_channel_from_path()` |
| `brightness`, `contrast`, `intensity` (per channel) | `ChannelController.sliders[name].value()` | `ChannelController.sliders[name].setValue()` |
| `crop` (x, y, width, height) | `CropHandler.get_saved_crop_rect()` | `CropHandler.set_saved_crop_rect()` |

The autosave timer is a 500 ms single-shot `QTimer` owned by `MainWindow`. It is
started (or restarted) on every slider `value_changed` signal. It fires
`save_autosave(main_window)` once the user stops adjusting.

---

## State Flow Diagram

```
User action
    │
    ▼
Qt widget (ChannelController slider, Crop button, etc.)
    │  signal / direct call
    ▼
Handler function in src/ui/handlers/
    │  reads widget state, calls service methods
    ├──► ImageProcessorService  (image array mutations)
    │       processed[i] = apply_adjustments(aligned[i], b, c)
    │
    ├──► AppState               (display flag mutations)
    │       show_combined, current_channel, crop_mode, …
    │
    └──► UI update calls
             update_main_display()   → get_combined() / get_channel() → QPixmap → ImageViewer
             update_channel_preview() → get_channel_preview() → QPixmap → ChannelController
             update_save_button_state() → has_processed_channels() → save_btn.setEnabled()
```

---

## Default Values Reference

All defaults are defined in `DefaultState` (`src/ui/default_state.py`) and
`SliderDefaults`. No magic numbers appear elsewhere in the codebase.

| Setting | Default | Source |
|---|---|---|
| Brightness | `0` | `DefaultState.SLIDER_DEFAULTS.brightness` |
| Contrast | `0` | `DefaultState.SLIDER_DEFAULTS.contrast` |
| Intensity | `100` | `DefaultState.SLIDER_DEFAULTS.intensity` |
| Display mode | Combined (`True`) | `DefaultState.SHOW_COMBINED` |
| Current channel | Red (`0`) | `DefaultState.CURRENT_CHANNEL` |
| Crop mode | Off (`False`) | `DefaultState.CROP_MODE` |
