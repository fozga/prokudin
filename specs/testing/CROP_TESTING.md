# Crop – Manual Testing

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
