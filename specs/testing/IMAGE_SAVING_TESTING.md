# Image Saving – Manual Testing

## Objectives

- Verify that image saving writes the expected files for combined and per-channel
  outputs.
- Confirm that crop is applied correctly.
- Ensure that invalid paths or permission issues are handled gracefully.

---

## Preconditions

- Application with three aligned channels.
- Save button enabled.
- Writable output directory.

---

## Test Cases

### IS1 – Save combined and per-channel images

1. Load and align three channels.
2. Ensure no crop is active.
3. Click **Save**.
4. Choose a filename `test_output.png` in a writable directory.

**Expected:**

- Files exist:
  - `test_output.png` (combined image).
  - `test_output_ir.png`, `test_output_vis.png`, `test_output_uv.png`.
- Combined image reflects alignment (no obvious misalignment).
- Per-channel images show the original spectral channels in colour.

---

### IS2 – Crop interaction

1. Set and accept a crop rectangle.
2. Click **Save**.
3. Choose `cropped_output.png`.
4. Open all saved images.

**Expected:**

- All saved images are cropped to exactly the same rectangle.
- No extra borders or misaligned crops between combined and per-channel files.

---

### IS3 – Cancel save dialog

1. Click **Save**.
2. Cancel the file dialog without choosing a path.

**Expected:**

- No files are written.
- Status bar indicates that the save was cancelled or no message is shown.
- Application remains responsive.

---

### IS4 – Invalid output path / permissions

1. Attempt to save to a directory where the user does not have write permission
   (if possible on the test OS).

**Expected:**

- An error is reported (e.g. "Error saving image: …").
- Application does not crash.

---

### IS5 – Save with no aligned channels

1. Start the application.
2. Ensure no channels are loaded.
3. Attempt to click **Save**.

**Expected:**

- Save button is disabled, or a clear message indicates there are no images to
  save.
