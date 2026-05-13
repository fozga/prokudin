# Presets – Manual Testing

## Objectives

- Verify that presets capture and restore slider values correctly.
- Validate rename/delete behaviour (planned context menu feature).
- Confirm that presets persist across sessions and resets.

---

## Preconditions

- Application with three aligned channels.
- Distinct slider configurations per channel (different brightness/contrast).

---

## Test Cases

### P1 – Saving a preset

1. Adjust sliders for each channel to a recognisable configuration.
2. Click **Save Preset**.
3. Enter a descriptive name (e.g. "High Contrast Warm").
4. Confirm.

**Expected:**

- The new preset appears in the sidebar with the given name.
- If a thumbnail is implemented, it shows the current viewer image.

---

### P2 – Applying a preset

1. Change sliders to a different configuration.
2. Click the preset created in P1.

**Expected:**

- All sliders snap back to the values stored in the preset.
- Channel previews and main viewer update accordingly.

---

### P3 – Presets and autosave

1. Apply a preset.
2. Wait for autosave.
3. Quit and restart the application.

**Expected:**

- Sliders reflect the last applied preset's values.
- The preset itself is not marked as "active" (no special selection state
  unless implemented), but the visual result matches.

---

### P4 – Presets and reset

1. Save at least one preset.
2. Click **New** (Reset).

**Expected:**

- The preset remains listed in the sidebar.
- Applying the preset after loading new channels works as before.

---

### P5 – Rename/delete (if implemented)

1. Right-click a preset in the sidebar.
2. Choose **Rename** and enter a new name.

**Expected:**

- The preset's displayed name changes.
- Applying the renamed preset still restores the same slider configuration.

3. Right-click the same preset.
4. Choose **Delete**.

**Expected:**

- The preset disappears from the sidebar.
- It does not reappear after restart.
