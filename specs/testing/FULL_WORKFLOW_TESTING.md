# Full Workflow – Manual Testing

## Objectives

- Validate that the complete user workflow behaves correctly from loading
  channels through final image export.
- Exercise interactions between features under realistic usage.

---

## Scenario FW1 – Typical editing session

1. Start the application.
2. Load IR, VIS, and UV channels from a Prokudin-style scene.
3. Verify that alignment completes successfully and Save becomes enabled.
4. Apply brightness/contrast adjustments to each channel until the preview looks
   satisfactory.
5. Save a preset named "FW1_Preset".
6. Enter Crop mode and choose a 4:3 aspect ratio.
7. Position the crop rectangle around the main subject and click **Accept**.
8. Wait for autosave to run.
9. Click **Save** and export images as `fw1_output.png`.
10. Quit the application.
11. Restart the application.

**Expected:**

- The previous session is restored (channels, sliders, crop) from autosave.
- Applying "FW1_Preset" reproduces the same look if sliders were changed.
- Saved images from step 9 are correctly cropped and aligned.

---

## Scenario FW2 – Recovery after missing file

1. Perform steps 1–9 of FW1.
2. Before restarting, delete the VIS channel file from disk.
3. Restart the application.

**Expected:**

- IR and UV channels are restored; VIS fails with a clear error message.
- Combined view is unavailable until VIS is reloaded.

4. Load a replacement VIS file.

**Expected:**

- Alignment re-runs.
- Combined view and Save become available.

---

## Scenario FW3 – Reset and clean start

1. Start with a restored session from FW1.
2. Click **New**.

**Expected:**

- Application returns to an empty state (no channels, default sliders, Save
  disabled).

3. Load a completely different set of channels.
4. Apply presets, crop, and save as desired.

**Expected:**

- Previous session does not leak into the new one.
- Autosave now reflects only the new session.

---

## Scenario FW4 – Stress test with multiple presets and crops

1. Load three compatible channels.
2. Create at least three presets with different looks.
3. For each preset:
   - Apply the preset.
   - Enter Crop mode, set a different aspect ratio, and Accept.
   - Save images with a filename that encodes the preset and ratio.

**Expected:**

- All presets can be applied in sequence without corruption.
- Crops and saved images match the expected aspect ratios.
- No crashes or severe slowdowns occur during repeated use.
