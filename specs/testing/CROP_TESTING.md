# Crop – Testing

## Unit Tests — `src/core/crop_geometry.py`

Pure geometry logic is covered by `tests/unit/test_core_crop_geometry.py` (no Qt
dependency). The test classes and their scope:

| Test class | Functions covered |
|---|---|
| `TestRect` | `Rect` properties (`right`, `bottom`, `center_x`, `center_y`) |
| `TestClampPointToBounds` | `clamp_point_to_bounds` — 8 cases (EP + BV) |
| `TestClampRectToBounds` | `clamp_rect_to_bounds` — 7 cases including zero-size |
| `TestAdjustDimensionsToRatio` | `adjust_dimensions_to_ratio` — ratio enforcement + corner mapping |
| `TestResizeTopLeft` | `resize_top_left` — normal drag, min-size, ratio, bounds clamp |
| `TestResizeTopRight` | `resize_top_right` |
| `TestResizeBottomLeft` | `resize_bottom_left` |
| `TestResizeBottomRight` | `resize_bottom_right` |
| `TestEdgeResizeFreeAspect` | `edge_resize_free_aspect` — all 4 handles, min-size, bounds clamp |
| `TestGetHorizontalConstraints` | `get_horizontal_constraints` — left/right, centering |
| `TestGetVerticalConstraints` | `get_vertical_constraints` — top/bottom, centering |
| `TestApplyHorizontalBoundsConstraints` | `apply_horizontal_bounds_constraints` — 4 violation cases |
| `TestApplyVerticalBoundsConstraints` | `apply_vertical_bounds_constraints` — 4 violation cases |
| `TestGetAnchorPoint` | `get_anchor_point` — all 8 named handles + unknown + None rect |

---

## Automated Qt Widget Tests — `tests/qt/test_widget_crop_handler.py`

Qt widget tests for the `CropHandler` class cover interactive behavior, state management, and rendering (code coverage: 85%, required 80%).

### Test Coverage by Feature

| Feature | Test Classes | Test Count |
|---------|---|---|
| Initialization & defaults | `TestCropHandlerInit` | 4 |
| State management (rect, mode, ratio) | `TestCropHandlerStateSetters` | 7 |
| Handle detection (9 handles) | `TestCropHandlerGetHandleAt` | 8 |
| Mouse interaction (press/move/release) | `TestCropHandlerMouseInteraction`, `TestCropHandlerMouseMove` | 10 |
| Rectangle operations (confirm, cancel, apply) | `TestCropHandlerRectangleOperations` | 3 |
| Aspect ratio enforcement | `TestCropHandlerAspectRatioEnforcement` | 2 |
| Cursor management (all 9 handle types) | `TestCropHandlerCursorManagement` | 12 |
| Rectangle constraints (clamping) | `TestCropHandlerConstraints` | 4 |
| Drawing/rendering | `TestCropHandlerDrawing` | 3 |
| Edge cases & error conditions | `TestCropHandlerEdgeCases` | 9 |
| Comprehensive workflows | `TestCropHandlerComprehensive` | 10 |
| **Total** | **11 classes** | **72 tests** |

### Test Design Pattern

All tests follow the **Test Design Specification (TDS) + Test Case Specification (TCS)** format:

- **TDS (class docstring)**: Contract, infrastructure dependencies, equivalence partitions, boundary values, mocking strategy, constraints
- **TCS (function docstring)**: Given/When/Then scenario with Arrange/Act/Assert implementation

Example:

```python
def test_set_crop_rect_stores_rect(self, qtbot: QtBot, crop_handler: CropHandler) -> None:
    """
    Given a CropHandler,
    When set_crop_rect(QRect(50, 50, 100, 100)) is called,
    Then get_crop_rect() returns QRect(50, 50, 100, 100).
    """
    # Arrange
    rect = QRect(50, 50, 100, 100)
    # Act
    crop_handler.set_crop_rect(rect)
    # Assert
    assert crop_handler.get_crop_rect() == rect
```

### Key Test Scenarios

1. **Initialization**: Default state, default geometry, default state dict
2. **State Transitions**: Crop mode enable/disable, rect persistence, ratio application
3. **Handle Detection**: All 9 handles (corners, edges, move), outside rect
4. **Mouse Interaction**: Press/move/release sequences, different handle types, ratio constraints, bounds checking
5. **Aspect Ratio**: Landscape (16:9), portrait (9:16), square (1:1), unconstrained
6. **Constraint Enforcement**: Minimum size, image bounds, ratio maintenance during clamping
7. **Rendering**: Overlay, grid, handles (8 squares at corners/edges)
8. **Integration**: Full workflows (enter→adjust→confirm/cancel), state restoration after cancel

### Coverage Gaps (By Design)

- **Helper functions** (`_qrect_to_rect`, etc.): Low-level converters; Qt/geometry semantics covered elsewhere
- **Complex resize algorithms** (edge resize with ratio): Delegated to `src.core.crop_geometry` (unit-tested separately)
- **Drawing compositing**: Qt painter internals; test verifies methods called, not pixel output
- **QApplication event processing**: Mocked to avoid GUI requirements



## Objectives

- Verify that Crop mode behaves as designed (enter/exit, Accept/Cancel).
- Confirm that the saved crop rectangle is applied consistently to display,
  previews, autosave, and image saving.

---

## Preconditions

- Application running with three aligned channels.
- Combined view visible.

---

## Test Cases

### C1 – Enter and exit Crop mode

1. Click **Crop**.

**Expected:**

- Crop controls (ratio selector, Accept, Cancel) appear.
- A default crop rectangle appears over the image.

2. Click **Cancel**.

**Expected:**

- Crop controls disappear.
- Any temporary rectangle is discarded.
- Viewer returns to uncropped view.

---

### C2 – Accepting a crop

1. Click **Crop**.
2. Draw or resize the crop rectangle to a clearly smaller region.
3. Click **Accept**.

**Expected:**

- Viewer shows the combined image cropped to the selected region.
- Channel previews update to reflect the crop (if designed to do so).
- Crop controls disappear; Crop mode turns off.

---

### C3 – Aspect ratio constraints

1. Enter Crop mode.
2. Select different aspect ratios from the ratio combo (e.g. 16:9, 4:3, 1:1).
3. Resize the crop rectangle for each ratio.

**Expected:**

- The rectangle maintains the selected aspect ratio while resizing.
- The rectangle never extends beyond image boundaries.

---

### C4 – Interaction with autosave

1. Enter Crop mode and set a non-trivial crop.
2. Click **Accept**.
3. Wait for autosave to run.
4. Quit and restart the application.

**Expected:**

- After restore, the same crop is applied to the viewer.
- Crop mode is **off**; the rectangle is active but not editable.

---

### C5 – Interaction with image saving

1. With a saved crop in effect, click **Save** and export images.
2. Inspect the saved combined and per-channel images in an external viewer.

**Expected:**

- All saved images are cropped exactly to the saved crop rectangle.
- No extra borders or unintended padding appear.
