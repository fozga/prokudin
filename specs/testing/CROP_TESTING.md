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

## Manual Tests — `CropHandler` (Qt-dependent)

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
