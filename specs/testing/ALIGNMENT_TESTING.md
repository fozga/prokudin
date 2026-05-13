# Alignment – Manual Testing

## Objectives

- Verify that alignment is triggered correctly and produces visually aligned
  channels under normal conditions.
- Validate behaviour when there are too few features or when alignment fails.

---

## Preconditions

- Application running with default settings.
- Test data:
  - A set of Prokudin-style plates with clear overlapping content.
  - At least one low-texture scene (e.g. sky, wall) to provoke alignment issues.

---

## Test Cases

### A1 – Successful alignment

1. Load three compatible channels (IR, VIS, UV) from the same scene.
2. Observe the combined image.

**Expected:**

- Features (buildings, edges, objects) line up across channels.
- No obvious colour ghosting at high-contrast edges.

---

### A2 – Alignment with small offsets

1. Load three images where channels are slightly shifted but otherwise similar.
2. Compare combined image before and after alignment (if reference is available).

**Expected:**

- Visible improvement in alignment after the third channel is loaded.
- Remaining misalignment is minimal and within expected tolerance.

---

### A3 – Insufficient features

1. Load three channels composed mostly of uniform regions (e.g. sky, blank wall).

**Expected:**

- Alignment fails with a clear status bar message (e.g. "Alignment failed:
  Insufficient matches (N/50)").
- Combined view is not updated; Save remains disabled.
- Single-channel views continue to work.

---

### A4 – Retry after failure

1. After an alignment failure as in A3, reload one or more channels with
   different images that contain more texture.

**Expected:**

- Alignment is attempted again.
- If the new images contain sufficient features, alignment succeeds.
- No stale error messages remain once alignment succeeds.

---

### A5 – Interaction with adjustments

1. Load and align three channels.
2. Apply noticeable brightness/contrast changes.
3. Inspect the combined view.

**Expected:**

- Geometric alignment remains correct; adjustments do not affect alignment.
- Changing sliders does not trigger re-alignment.
