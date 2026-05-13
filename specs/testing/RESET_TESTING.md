# Reset – Manual Testing

## Objectives

- Verify that Reset clears all in-memory state and returns the UI to defaults.
- Ensure autosave is cleared so that a future restart does not restore the
  pre-reset session.

---

## Preconditions

- Application started normally.
- At least one full session has been established:
  - Three channels loaded and aligned.
  - Adjustments applied.
  - Crop rectangle defined.
  - Preset saved.

---

## Test Cases

### R1 – Basic reset behaviour

1. Confirm that all three channel previews show images.
2. Confirm that the main viewer shows a combined image.
3. Confirm that the Save button is enabled.
4. Click **New** (Reset).

**Expected:**

- All channel previews are cleared.
- The main viewer shows an empty placeholder.
- The Save button is disabled.
- Crop controls (if visible) disappear.
- Status bar shows a short "Reset to defaults" message.

---

### R2 – Interaction with autosave

1. Build a non-trivial session:
   - Load three channels.
   - Apply visible adjustments.
   - Set a crop rectangle.
2. Wait long enough for autosave to run.
3. Quit and restart the application.

**Expected:**

- The session is restored automatically (channels, sliders, crop).

4. Click **New**.
5. Quit and restart the application again.

**Expected:**

- No session is restored.
- The application starts in an empty state.

---

### R3 – Presets persistence

1. Save a new preset (e.g. "ResetTestPreset").
2. Confirm that it appears in the preset sidebar.
3. Click **New**.
4. Confirm that the preset is still listed in the sidebar.
5. Load new channels and apply the preset.

**Expected:**

- Reset does not remove preset files.
- The preset remains usable after Reset.

---

### R4 – Reset with partial session

1. Load only one channel.
2. Apply some adjustments to that channel.
3. Do **not** load other channels.
4. Click **New**.

**Expected:**

- UI returns to the same post-reset default state as in R1.
- No errors or warnings are shown.
