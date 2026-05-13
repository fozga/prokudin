# Grid Overlay – Manual Testing

## Objectives

- Verify that all grid types are rendered correctly on top of the image.
- Ensure grid settings can be changed at runtime without glitches.
- Confirm that grid behaviour in Crop mode matches the specification (clipped to
  the crop rectangle).

---

## Preconditions

- Application started with default settings.
- At least one aligned image loaded and visible in the viewer.
- Crop mode is **off**.

---

## Test Cases

### G1 – Toggle grid visibility

1. Ensure an image is visible in the main viewer.
2. Click the **Grid** toolbar button to enable the grid.
3. Observe that a 3×3 grid appears across the entire image area.
4. Click the **Grid** button again.
5. Observe that the grid disappears.

**Expected:**

- Default grid type is 3×3.
- Toggling the button hides/shows the grid without affecting the image.

---

### G2 – Change grid type

For each grid type in the settings dialog:

1. Open **Grid Settings**.
2. Select the target grid type (e.g. Golden Ratio, Diagonal 1:1, Diagonal Thirds V).
3. Close the dialog (optional).
4. Visually inspect the grid overlay.

**Expected:**

- The grid updates immediately after selection.
- Only one grid type is applied at a time.
- No stale lines from the previously selected grid remain.

---

### G3 – Line width adjustment

1. Enable the grid.
2. Open **Grid Settings**.
3. Decrease the line width to the minimum.
4. Observe the grid.
5. Increase the line width to the maximum.
6. Observe the grid.

**Expected:**

- Grid lines become visibly thinner/thicker according to the selected width.
- Lines remain crisp (no obvious aliasing issues) at all widths.

---

### G4 – Grid in Crop mode

1. Enable the grid.
2. Enter **Crop mode**.
3. Draw a crop rectangle smaller than the full image.
4. Observe the grid inside the crop rectangle.
5. Resize/move the crop rectangle.

**Expected:**

- Grid lines are drawn only inside the crop rectangle.
- The grid "moves" with the crop region; it is always aligned to the active crop.
- No grid is visible in the dimmed area outside the crop.

---

### G5 – Interaction with reset and autosave

1. Enable a non-default grid type and custom line width.
2. Quit and restart the application.
3. Load an image.

**Expected:**

- Grid settings revert to defaults (3×3, default line width) after restart.

4. Change grid settings again.
5. Click **New** to reset the application.

**Expected:**

- Reset does **not** change grid settings; the chosen grid type and width remain.
