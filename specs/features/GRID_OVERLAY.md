# Grid Overlay

## Contract

The grid overlay feature draws composition guides on top of the image in the
viewer. It supports multiple grid types (rule-of-thirds, golden ratio, and several
families of diagonal grids) and a configurable line width. The grid:

- Is purely visual and non-interactive.
- Does not affect image data, crop geometry, or saving.
- Can be toggled on or off and reconfigured on the fly without rebuilding the
  scene.

A single `GridOverlay` instance is shared between the normal view and Crop mode,
so grid settings are always consistent across both.

---

## Components

| Component | Responsibility |
|---|---|
| `GridOverlay` (`src/ui/widgets/grid_overlay.py`) | Stores grid settings and draws lines given a `QPainter` and `QRectF`. Qt-dependent but stateless between draws. |
| `GridSettingsDialog` (`src/ui/widgets/grid_settings_dialog.py`) | Popup panel for selecting grid type and line width. Emits signals when settings change. |
| `grid_types` (`src/ui/widgets/grid_types.py`) | String constants for all supported grid types, shared across widgets. |
| `ImageViewer` (`src/ui/widgets/image_viewer.py`) | Owns the single `GridOverlay` instance and calls `draw_grid()` from its paint routine. |
| `CropHandler` (`src/ui/widgets/crop_handler.py`) | Receives a reference to the same `GridOverlay` so that grids are drawn consistently in Crop mode. |

---

## Grid Types

Grid types are identified by string constants defined in `grid_types.py`.

| Constant | Value | Description |
|---|---|---|
| `GRID_TYPE_NONE` | `"none"` | Grid disabled. `GridSettingsDialog` emits this when the user selects "None". |
| `GRID_TYPE_3X3` | `"3x3"` | Rule-of-thirds grid: image divided into 3×3 equal rectangles by 2 vertical and 2 horizontal lines. |
| `GRID_TYPE_GOLDEN_RATIO` | `"golden_ratio"` | Golden-ratio grid: lines at approximately 0.382 and 0.618 of width and height. |
| `GRID_TYPE_DIAGONAL_1_1` | `"diagonal_1_1"` | Four 45° diagonals from each corner, matching a 1:1 slope. |
| `GRID_TYPE_DIAGONAL_2_3` | `"diagonal_2_3"` | Diagonals with slope 2:3 (≈33.69°). |
| `GRID_TYPE_DIAGONAL_3_2` | `"diagonal_3_2"` | Diagonals with slope 3:2 (≈56.31°). |
| `GRID_TYPE_DIAGONAL_3_4` | `"diagonal_3_4"` | Diagonals with slope 3:4 (≈36.87°). |
| `GRID_TYPE_DIAGONAL_4_3` | `"diagonal_4_3"` | Diagonals with slope 4:3 (≈53.13°). |
| `GRID_TYPE_DIAGONAL_THIRDS_V` | `"diagonal_thirds_v"` | Diagonals plus **vertical** lines to rule-of-thirds division points. |
| `GRID_TYPE_DIAGONAL_THIRDS_H` | `"diagonal_thirds_h"` | Diagonals plus **horizontal** lines to rule-of-thirds division points. |
| `GRID_TYPE_DIAGONAL_GOLDEN_V` | `"diagonal_golden_v"` | Diagonals plus **vertical** lines to golden-ratio division points. |
| `GRID_TYPE_DIAGONAL_GOLDEN_H` | `"diagonal_golden_h"` | Diagonals plus **horizontal** lines to golden-ratio division points. |

`GridOverlay` defaults to `GRID_TYPE_3X3` at startup.

---

## `GridOverlay` API

### Construction

```python
grid = GridOverlay()
```

Initial settings:

- `enabled = True`
- `color = QColor("white")`
- `line_width = 4` pixels
- `line_style = Qt.SolidLine`
- `opacity = 128` (semi-transparent)
- `grid_type = GRID_TYPE_3X3`

### Configuration methods

```python
grid.set_enabled(enabled: bool)
grid.is_enabled() -> bool

grid.set_color(color: QColor)

grid.set_line_width(width: int)
grid.get_line_width() -> int

grid.set_opacity(opacity: int)

grid.set_grid_type(grid_type: str)
grid.get_grid_type() -> str
```

- `set_enabled(False)` hides the grid without changing any other settings.
- `set_opacity(value)` clamps the value to `[0, 255]`.
- `set_grid_type()` raises `ValueError` if an unsupported grid type is passed.

### Drawing

```python
grid.draw_grid(painter: QPainter, rect: Union[QRect, QRectF]) -> None
```

Behaviour:

1. If `enabled` is `False`, returns immediately.
2. Converts `QRect` to `QRectF` if needed.
3. Returns early for zero-area rectangles (`width <= 0 or height <= 0`).
4. Saves the painter state.
5. Creates a `QPen` from `color` and `line_width`, sets alpha to `opacity`, and
   sets brush to `Qt.NoBrush`.
6. Looks up the drawing function in `_grid_drawing_methods` using `grid_type`.
   Defaults to `_draw_3x3_grid` if the key is missing.
7. Calls the drawing function with `(painter, rect)`.
8. Restores the painter state.

The grid is drawn **after** the base image but before any crop handles, so that
handles remain visible on top of the grid.

---

## GridSettingsDialog Flow

`GridSettingsDialog` is a frameless popup used to configure the grid. It is
usually created lazily by `MainWindow` and reused between openings.

### Initialisation

```python
dialog = GridSettingsDialog(current_width=grid.get_line_width(),
                            current_grid_type=grid.get_grid_type(),
                            parent=main_window)
```

The dialog:

- Shows a small toolbar for line width (`-  [width]  +`).
- Shows a list of grid types based on `GRID_TYPES` tuples:
  `[("None", GRID_TYPE_NONE), ("3x3 Grid", GRID_TYPE_3X3), …]`.
- Selects the current grid type row based on `current_grid_type`.

### Signals

`GridSettingsDialog` emits two signals:

- `grid_type_changed(str)` — emitted when the selection in the list changes.
- `line_width_changed(int)` — emitted when the user adjusts the width.

`MainWindow` wires these signals to the shared `GridOverlay`:

```python
dialog.grid_type_changed.connect(grid.set_grid_type)
dialog.line_width_changed.connect(grid.set_line_width)
viewer.update()  # requested by slots as needed
```

The "None" type from the dialog maps to `GRID_TYPE_NONE`. When this is selected,
`MainWindow` typically calls `grid.set_enabled(False)`; any other type enables the
grid.

---

## Internal Drawing Behaviour

### 3×3 grid

`_draw_3x3_grid(painter, rect)`:

- Computes `x1 = left + width/3`, `x2 = left + 2·width/3`.
- Computes `y1 = top + height/3`, `y2 = top + 2·height/3`.
- Draws 2 vertical and 2 horizontal lines at these positions.

### Golden-ratio grid

`_draw_golden_ratio_grid(painter, rect)`:

- Uses constants ≈0.382 and ≈0.618 of width and height.
- Draws vertical lines at `left + width*0.382` and `left + width*0.618`.
- Draws horizontal lines at `top + height*0.382` and `top + height*0.618`.

### Diagonal 1:1 grid

`_draw_diagonal_1_1_grid(painter, rect)`:

- Draws four diagonals (45°, 135°, 225°, 315°) from each corner.
- Each line extends until it hits either the opposite edge horizontally or
  vertically, depending on whether the rect is wider than tall.

### Parametric diagonal ratio grids

`_draw_diagonal_ratio_grid(painter, rect, vertical_ratio, horizontal_ratio)`:

- Computes an offset `(x_offset, y_offset)` such that the line from a corner with
  slope `vertical_ratio/horizontal_ratio` hits exactly one of the opposite edges.
- Draws four symmetric lines using this offset from each corner.

This helper is used by:

- `_draw_diagonal_2_3_grid` (2:3 slope)
- `_draw_diagonal_3_2_grid` (3:2 slope)
- `_draw_diagonal_3_4_grid` (3:4 slope)
- `_draw_diagonal_4_3_grid` (4:3 slope)

### Diagonal + thirds / golden grids

`_draw_diagonal_thirds_v_grid` / `_draw_diagonal_thirds_h_grid`:

- Draw the two main diagonals.
- Compute rule-of-thirds points on the relevant edges.
- From each corner, draw an extra line to a thirds point (vertical or horizontal
  depending on `_v` / `_h`).

`_draw_diagonal_golden_v_grid` / `_draw_diagonal_golden_h_grid`:

- Same pattern, but thirds points are replaced with golden-ratio points
  (0.382 and 0.618 of width/height).

---

## Planned Core Extraction – `grid_geometry.py` (Issue #57)

Grid line geometry is currently computed directly inside `GridOverlay` using
Qt types (`QRectF`, `QLineF`). Issue #57 proposes extracting this logic into a
Qt-free core module so that it can be unit-tested and reused.

### Target design

- New module: `src/core/grid_geometry.py`.
- All functions are pure and operate on plain tuples:

  ```python
  Rect = tuple[float, float, float, float]  # (left, top, width, height)
  Segment = tuple[float, float, float, float]  # (x1, y1, x2, y2)

  def calculate_3x3_lines(rect: Rect) -> list[Segment]:
      ...
  def calculate_golden_ratio_lines(rect: Rect) -> list[Segment]:
      ...
  def calculate_diagonal_1_1_lines(rect: Rect) -> list[Segment]:
      ...
  # etc. for all 11 grid types
  ```

- `GridOverlay` becomes a thin adapter:

  ```python
  segments = grid_geometry.calculate_3x3_lines((rect.left(), rect.top(), rect.width(), rect.height()))
  for x1, y1, x2, y2 in segments:
      painter.drawLine(QLineF(x1, y1, x2, y2))
  ```

### Behavioural invariants

- All functions return segments that lie within the input rect bounds.
- For diagonal families, there are always four symmetric lines from each corner.
- For combined diagonal+thirds/golden grids, each corner produces exactly two
  segments: one diagonal and one towards the division point.

This refactor does not change the visual outcome; it only relocates geometry
calculations to `src/core/` for better testability.

---

## Interactions with Crop and Viewer

- `ImageViewer` always uses the same `GridOverlay` instance for both the full
  image and the Crop overlay. This ensures that changing the grid type or line
  width is reflected immediately in both modes.
- In Crop mode, `CropHandler` clips the grid to the crop rect before drawing.
  The grid is therefore always drawn **inside** the active crop, not on the
  full image.
- Grid settings are **not** persisted via autosave. On application start, grid
  type reverts to `GRID_TYPE_3X3` and line width to 4, with `enabled=True`.
