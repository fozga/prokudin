# Autosave – Manual Testing

## Objectives

- Verify that autosave captures channel paths, slider values, and crop rectangle.
- Confirm that restore behaves correctly on startup.
- Ensure that reset clears autosave.

---

## Preconditions

- Application with autosave enabled (default).
- Known location of the autosave file (for inspection if needed).

---

## Test Cases

### AS1 – Basic autosave and restore

1. Start the application.
2. Load three channels.
3. Apply distinct adjustments to each channel.
4. Set a crop rectangle and click **Accept**.
5. Wait at least 1 second (longer than the autosave debounce interval).
6. Quit the application.
7. Restart the application.

**Expected:**

- All three channels are reloaded.
- Sliders reflect the previously set values.
- The crop rectangle is restored and applied to the viewer.

---

### AS2 – Autosave with missing files

1. Perform steps 1–5 from AS1.
2. Before restarting, delete one of the ARW files from disk.
3. Restart the application.

**Expected:**

- The remaining channels are restored successfully.
- The missing channel is skipped, with a clear status bar error.
- The application remains usable; user can load a replacement file.

---

### AS3 – Reset clears autosave

1. Perform AS1 to create a valid autosave.
2. Restart and confirm that the session is restored.
3. Click **New** (Reset).
4. Quit and restart the application.

**Expected:**

- No session is restored.
- Application starts in a clean state.

---

### AS4 – Autosave timing

1. Start the application.
2. Move a slider continuously for several seconds.

**Expected:**

- Autosave does **not** run while the slider is moving (no disk writes).

3. Release the slider and wait ~1 second.

**Expected:**

- Autosave runs exactly once shortly after you stop interacting.
