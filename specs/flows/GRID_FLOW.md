# Grid Overlay – Flow

This document describes the control and data flow for the Grid Overlay feature:
opening the grid settings panel, changing grid type and line width, and how the
grid is drawn in both normal and Crop modes.

For behaviour and types see `specs/features/GRID_OVERLAY.md`.

---

## Legend

- **User action** — click, key press, or other direct interaction.
- **UI widget** — `ImageViewer`, `GridSettingsDialog`, toolbar buttons.
- **GridOverlay** — shared grid instance owned by `ImageViewer`.
- **CropHandler** — crop overlay, draws grid inside crop rectangle in Crop mode.

---

## Opening and Closing Grid Settings

The grid settings panel is a small frameless popup anchored to the viewer area.
It is created lazily and reused across openings.

### Open flow

```text
User clicks "Grid" button / menu item
    │
    ▼
MainWindow.slot_toggle_grid_settings()
    │
    ├── if self.grid_settings_dialog is None:
    │       self.grid_settings_dialog = GridSettingsDialog(
    │           current_width=self.grid_overlay.get_line_width(),
    │           current_grid_type=self.grid_overlay.get_grid_type(),
    │           parent=self,
    │       )
    │       wire dialog signals to grid overlay
    │
    ├── position dialog relative to viewer (top-right corner)
    │
    ├── if dialog.isVisible():
    │       dialog.hide()      # toggle off
    │   else:
    │       dialog.show()
    │       dialog.raise_()
    │       dialog.activateWindow()
    │
    └── return
```

The initial call to `GridSettingsDialog` synchronises the UI controls with the
current grid configuration (type and line width).

### Close flow

The dialog can be closed in three ways:

- Clicking the Grid button again (toggle behaviour).
- Clicking outside the dialog, if it is configured to close on focus out.
- Pressing the standard window close control (if enabled on the platform).

In all cases, closing the dialog does **not** modify grid settings; it only hides
the configuration UI.

---

## Wiring Between Dialog and GridOverlay

When the dialog is created, `MainWindow` connects its signals to the shared
`GridOverlay` instance and a repaint of the viewer.

```text
MainWindow._init_grid_settings_dialog()
    │
    ├── dialog.grid_type_changed.connect(on_grid_type_changed)
    ├── dialog.line_width_changed.connect(on_line_width_changed)
    │
    └── return

on_grid_type_changed(grid_type: str)
    │
    ├── if grid_type == GRID_TYPE_NONE:
    │       grid_overlay.set_enabled(False)
    │   else:
    │       grid_overlay.set_enabled(True)
    │       grid_overlay.set_grid_type(grid_type)
    │
    └── viewer.update()  # schedule repaint

on_line_width_changed(width: int)
    │
    ├── grid_overlay.set_line_width(width)
    │
    └── viewer.update()
```

The dialog itself owns no persistent state beyond its widgets. `GridOverlay` is
the single source of truth for grid settings.

---

## Grid Drawing Flow – Normal View

### Paint cycle in ImageViewer

`ImageViewer` is responsible for drawing the base image and the grid overlay when
not in Crop mode.

```text
ImageViewer.paintEvent(event)
    │
    ├── create QPainter(self.viewport())
    │
    ├── draw base image pixmap (if any) at current zoom and pan
    │
    ├── if grid_overlay.is_enabled():
    │       view_rect = visible image rect in scene coordinates
    │       grid_overlay.draw_grid(painter, view_rect)
    │
    └── if crop_mode is active:
            delegate drawing of crop handles to CropHandler
```

Key points:

- `GridOverlay` always draws **after** the base image.
- In normal (non-crop) mode, the grid covers the entire visible image rect.
- The `line_width` and `color` are independent of zoom; lines remain the same
  thickness in screen pixels, not image pixels.

---

## Grid Drawing Flow – Crop Mode

In Crop mode, the grid is drawn **inside** the crop rectangle rather than across
the full image.

### Crop drawing sequence

```text
ImageViewer.paintEvent(event)
    │
    ├── draw base image
    │
    ├── if grid_overlay.is_enabled() and crop_mode is False:
    │       grid_overlay.draw_grid(painter, full_view_rect)
    │
    ├── if crop_mode is True:
    │       CropHandler.draw_foreground(painter)
    │           ├── draw dark overlay outside current rect
    │           ├── clear interior of current rect
    │           ├── if grid_overlay.is_enabled():
    │           │      # Clip painter to current rect
    │           │      painter.save()
    │           │      painter.setClipRect(current_rect)
    │           │      grid_overlay.draw_grid(painter, current_rect)
    │           │      painter.restore()
    │           └── draw crop rectangle border + handles
    │
    └── return
```

This ensures that:

- The grid always aligns to the **crop region** while the user is editing it.
- Grid lines do not extend into the dimmed outside area during Crop mode.

---

## Changing Grid Type

### Flow

```text
User selects a different grid type in GridSettingsDialog
    │
    ▼
UI: list widget currentRowChanged → emit grid_type_changed(grid_type)
    │
    ▼
Slot: on_grid_type_changed(grid_type)
    │
    ├── if grid_type == GRID_TYPE_NONE:
    │       grid_overlay.set_enabled(False)
    │   else:
    │       grid_overlay.set_enabled(True)
    │       grid_overlay.set_grid_type(grid_type)
    │
    └── viewer.update()
```

`GridOverlay.set_grid_type()` selects the corresponding internal drawing method
(or the future `grid_geometry.calculate_*_lines()` function). The change takes
effect on the next repaint; no other state is modified.

---

## Changing Line Width

### Flow

```text
User clicks "+" / "-" buttons or edits width spinbox in GridSettingsDialog
    │
    ▼
UI: line width control valueChanged(int)
    │
    ▼
Signal: line_width_changed(width)
    │
    ▼
Slot: on_line_width_changed(width)
    │
    ├── grid_overlay.set_line_width(width)
    │   # clamps width to a valid range, e.g. [1, 10]
    │
    └── viewer.update()
```

Line width affects only the visual thickness of grid lines. It has no influence
on crop geometry, saving, or alignment.

---

## Toggling Grid On and Off

Grid visibility can be toggled either via a dedicated toolbar button or by
selecting the "None" entry in the grid type list.

### Toolbar toggle (example)

```text
User clicks "Toggle Grid" button
    │
    ▼
MainWindow.slot_toggle_grid()
    │
    ├── grid_overlay.set_enabled(not grid_overlay.is_enabled())
    │
    ├── if grid_overlay.is_enabled() and grid_overlay.get_grid_type() == GRID_TYPE_NONE:
    │       grid_overlay.set_grid_type(GRID_TYPE_3X3)  # default
    │
    └── viewer.update()
```

### Via GridSettingsDialog

```text
User selects "None" in grid type list
    │
    ▼
GridSettingsDialog emits grid_type_changed(GRID_TYPE_NONE)
    │
    ▼
on_grid_type_changed(GRID_TYPE_NONE)
    │
    ├── grid_overlay.set_enabled(False)
    │
    └── viewer.update()
```

When the grid is disabled, no geometry is computed and `draw_grid()` returns
immediately.

---

## Interaction with Other Flows

- **Crop Flow:** grid drawing in Crop mode is integrated with `CropHandler` so
  that it is always clipped to the current crop rectangle (see
  `specs/flows/CROP_FLOW.md`).
- **Autosave Flow:** grid settings are not persisted; autosave stores only
  channel paths, sliders, and crop rectangle. After restart the grid returns to
  default settings.
- **Reset Flow:** Reset clears image and UI state but does not change grid
  configuration; users can reset the session without losing their preferred grid
  type or line width.
