# Channel Loading – Manual Testing

## Objectives

- Verify that channels can be loaded interactively and via autosave restore.
- Confirm that alignment triggers correctly after the third channel is loaded.
- Ensure error conditions (missing files, invalid ARW) are handled gracefully.

---

## Preconditions

- Application started with no session restored.
- Folder containing valid Sony ARW files and at least one invalid/unsupported
  file with `.arw` extension.

---

## Test Cases

### CL1 – Load single channel

1. Start the application.
2. Click **Load IR** and choose a valid ARW file.

**Expected:**

- IR channel preview shows a grayscale thumbnail.
- Status bar shows "Successfully loaded image into IR channel".
- Main viewer shows the IR channel in single-channel mode.
- Save button remains disabled.

---

### CL2 – Load all three channels (alignment trigger)

1. With IR loaded, click **Load VIS** and choose a valid ARW.
2. Click **Load UV** and choose a valid ARW.

**Expected:**

- After the third channel loads, alignment runs.
- All three channel previews show aligned content.
- Main viewer switches to combined view.
- Status bar shows "All channels loaded successfully – Ready for editing!".
- Save button becomes enabled.

---

### CL3 – Reload a channel

1. With all three channels loaded, click **Load VIS** again and choose a
   *different* file.

**Expected:**

- Green channel preview updates to the new content.
- Alignment re-runs for all channels.
- Combined image changes accordingly.

---

### CL4 – Invalid ARW file

1. Click **Load IR**.
2. Select an invalid or corrupted `.arw` file.

**Expected:**

- An error message appears in the status bar (e.g. "Error loading ARW file: …").
- IR channel preview remains empty.
- No crash or modal error dialog.

---

### CL5 – Missing file on autosave restore

1. Load all three channels.
2. Wait for autosave to run.
3. Quit the application.
4. Delete one of the previously loaded ARW files from disk.
5. Restart the application.

**Expected:**

- Restore attempts to load each channel.
- For the missing file, a status bar error appears:
  "Failed to restore <ChannelName> channel: …".
- Other channels load and align if their files exist.
