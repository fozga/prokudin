# Architecture Overview

## Purpose

Prokudin is a desktop application for composing colour photographs from three
separate monochrome layers (Red, Green, Blue) captured on Sony ARW RAW film
plates — a technique inspired by Sergei Mikhailovich Prokudin-Gorsky's
early-20th-century colour photography method. The application aligns the three
channels using feature matching, applies per-channel brightness/contrast
adjustments, and exports the result as a colour image.

---

## Technology Stack

| Component | Library / Version |
|---|---|
| GUI framework | PyQt5 5.15.10 |
| Image processing | OpenCV (`opencv-python-headless`) 4.9.0.80 |
| Array operations | NumPy 1.26.4 |
| RAW file decoding | rawpy 0.26.1 |
| Image I/O (thumbnails) | Pillow 10.2.0 |
| Python | 3.10+ |

---

## Layer Architecture

The codebase is divided into three strictly separated layers. The dependency
rule is absolute: **a lower layer never imports from a higher layer.**

```
┌─────────────────────────────────────────────────────────────┐
│  src/ui/                                                    │
│  All Qt-dependent code. Requires a running QApplication.    │
│                                                             │
│  main_window.py      Root widget; wires all components      │
│  app_state.py        UI-only mutable state dataclass        │
│  default_state.py    Compile-time default values            │
│  qt_utils.py         numpy → QImage conversion utility      │
│                                                             │
│  handlers/           Thin functions (no class state):       │
│    autosave.py         Session persistence (JSON ↔ disk)    │
│    channels.py         Load / adjust / preview channels     │
│    display.py          Update main image viewer             │
│    image_loading.py    Open file dialog + rawpy decode      │
│    image_saving.py     Save dialog + write PNG/TIFF         │
│    keyboard.py         Global keyboard shortcut dispatch    │
│    presets.py          Save / apply adjustment presets      │
│                                                             │
│  widgets/            QWidget subclasses:                    │
│    image_viewer.py     Zoomable/pannable image display      │
│    channel_controller.py  Sliders + preview per channel     │
│    crop_handler.py     Crop rectangle interaction + draw    │
│    grid_overlay.py     Composition grid rendering           │
│    grid_settings_dialog.py  Grid config popup              │
│    grid_types.py       Grid type string constants           │
│    preset_panel.py     Preset list + save button            │
│    sliders.py          ResetSlider (double-click to reset)  │
│    status_bar.py       Status bar message helper            │
└────────────────────────────┬────────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────────┐
│  src/services/                                              │
│  Stateful orchestration. Zero Qt imports.                   │
│                                                             │
│  processor.py        ImageProcessorService                  │
│                        Owns all image arrays                │
│                        Coordinates calls into src/core/     │
│                        Exposes clean query methods          │
└────────────────────────────┬────────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────────┐
│  src/core/                                                  │
│  Pure Python + NumPy/OpenCV. Zero Qt imports.               │
│  Every function is independently unit-testable.             │
│                                                             │
│  align.py            ORB feature matching + affine warp     │
│  image_processing.py Brightness/contrast + channel merge    │
│  [crop_geometry.py]  Planned — issue #56                    │
│  [grid_geometry.py]  Planned — issue #57                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Reference

### `src/core/`

| Module | Responsibility |
|---|---|
| `align.py` | `align_images(grayscale_images, rgb_images)` — detects ORB keypoints, matches G and B channels to R using BFMatcher, estimates partial affine transform, and applies `warpAffine` to both grayscale and RGB copies. Raises `AlignmentError` if fewer than 50 matches are found or the transform cannot be estimated. |
| `image_processing.py` | `apply_adjustments(image, brightness, contrast)` — applies the formula `clip(image × (1 + contrast/100) + brightness, 0, 255)`. `combine_channels(channels, intensities)` — merges three grayscale arrays into a single HxWx3 RGB array, scaling each channel by its intensity percentage. Returns `None` if any channel is missing. |
| `crop_geometry.py` | *(Planned — issue #56)* Pure geometry functions for crop rectangle calculations: clamping, ratio enforcement, corner and edge resize arithmetic. No Qt types. |
| `grid_geometry.py` | *(Planned — issue #57)* Pure coordinate calculations for all 11 grid types. Each function takes `(left, top, width, height)` and returns a list of `(x1, y1, x2, y2)` line segments. No Qt types. |

### `src/services/`

| Module | Responsibility |
|---|---|
| `processor.py` | `ImageProcessorService` — owns all image arrays (`original_images`, `aligned`, `processed`, `original_rgb_images`, `aligned_rgb`) and the per-channel `ChannelAdjustments` list. Provides `load_channel_from_array()`, `adjust_channel()`, `get_channel()`, `get_combined()`, `get_channel_preview()`, `get_image_dimensions()`, `has_aligned_channels()`, `has_processed_channels()`, and `reset()`. |

### `src/ui/handlers/`

Handlers are stateless module-level functions. They receive `MainWindow` as their
first argument, read widget state, call service methods, and update the UI.
They are the only code that bridges the Qt layer and the service layer.

| Module | Responsibility |
|---|---|
| `image_loading.py` | Opens a file dialog (or accepts a path directly), calls `rawpy.imread()` + `postprocess()`, and returns the RGB array. |
| `channels.py` | Orchestrates the load-and-align sequence; calls `adjust_channel` and `update_channel_preview` after each channel load. |
| `display.py` | Calls `svc.get_combined()` or `svc.get_channel()`, converts to `QPixmap`, and pushes it to `ImageViewer`. |
| `image_saving.py` | Opens a save dialog, retrieves the combined image (with optional crop), converts BGR, and writes via `cv2.imwrite`. |
| `autosave.py` | Serialises `AppState` fields, slider values, and crop rect to `autosave.json`; deserialises and restores on startup. |
| `presets.py` | Writes/reads preset JSON files; applies slider values via `adjust_channel`. |
| `keyboard.py` | Maps `QKeyEvent` key codes to application actions. |

### `src/ui/widgets/`

| Widget | Responsibility |
|---|---|
| `ImageViewer` | Zoomable, pannable `QGraphicsView`. Owns the shared `GridOverlay` instance. Delegates crop interaction to `CropHandler`. |
| `ChannelController` | `QGroupBox` with brightness, contrast, and intensity sliders (`ResetSlider`), paired text inputs, and a channel preview label. Emits `value_changed`. |
| `CropHandler` | Manages crop rectangle state (current, saved, original), handle detection, mouse interaction, ratio enforcement, and drawing. Delegates geometry to `crop_geometry` *(planned)*. |
| `GridOverlay` | Stores grid settings (type, line width, colour, opacity) and draws the active grid type onto a `QPainter`. Owns no Qt widget state. |
| `GridSettingsDialog` | Frameless popup `QFrame` for selecting grid type and line width. Emits `grid_type_changed` and `line_width_changed` signals. |
| `PresetPanel` | Scrollable list of saved presets with thumbnails. Emits `preset_selected` and `save_requested`. |
| `ResetSlider` | `QSlider` subclass that emits `doubleClicked` to allow double-click-to-reset behaviour. |
| `StatusBarHandler` | Thin wrapper around `QStatusBar` providing named timeout constants (`SHORT_TIMEOUT`, `MEDIUM_TIMEOUT`, `LONG_TIMEOUT`, `NO_TIMEOUT`). |

### `src/ui/` (top-level)

| Module | Responsibility |
|---|---|
| `main_window.py` | Root `QMainWindow`. Creates and owns all widgets and the `ImageProcessorService`. Wires signals to handlers. Manages the 500 ms autosave debounce timer. |
| `app_state.py` | `AppState` dataclass — UI-only mutable state: channel file paths, display mode, current channel, crop mode flag, crop ratio, grid dialog reference. |
| `default_state.py` | `DefaultState` class — compile-time constants for all default values (slider defaults, display mode, crop mode). Used by both `AppState.reset()` and `ChannelController`. |
| `qt_utils.py` | `convert_to_qimage(ndarray)` — converts a NumPy HxW (grayscale) or HxWx3 (RGB) uint8 array to `QImage`. |

---

## Key Design Decisions

### Single `GridOverlay` instance
`ImageViewer` creates and owns one `GridOverlay`. `CropHandler` receives a
reference to the same instance in its constructor. This ensures grid settings
(type, line width) are always in sync between normal view mode and crop mode,
with no synchronisation logic required.

### Handlers are stateless functions
UI handlers in `src/ui/handlers/` are plain functions, not classes. All state
they need is passed in via the `MainWindow` argument. This makes them easy to
test with a mock or partial `MainWindow` object and avoids hidden instance state.

### `AppState` vs `ImageProcessorService`
All image array state lives exclusively in `ImageProcessorService`.
`AppState` holds only UI-display decisions (what to show, which channel,
whether crop mode is active). This separation means the service can be
tested with zero Qt dependency, and the UI can be reset by calling
`AppState.reset()` without touching image memory.

### Dependency rule enforcement
The `src/core/` and `src/services/` layers have no PyQt5 imports. This is
verified at test time: the unit test suite runs without a `QApplication` and
therefore fails loudly if a Qt import leaks into a lower layer.

---

## Planned Changes

| Issue | Module affected | Description |
|---|---|---|
| [#47](https://github.com/fozga/prokudin/issues/47) | `src/ui/widgets/preset_panel.py`, `src/ui/handlers/presets.py` | Add right-click context menu to preset list with Rename and Delete actions. |
| [#48](https://github.com/fozga/prokudin/issues/48) | `src/services/processor.py` | Fix `get_channel()` to always return an independent copy, not an internal reference. |
| [#56](https://github.com/fozga/prokudin/issues/56) | `src/core/crop_geometry.py` *(new)*, `src/ui/widgets/crop_handler.py` | Extract pure geometry logic from `CropHandler` into a Qt-free core module. |
| [#57](https://github.com/fozga/prokudin/issues/57) | `src/core/grid_geometry.py` *(new)*, `src/ui/widgets/grid_overlay.py` | Extract grid line coordinate calculations into a Qt-free core module. |
