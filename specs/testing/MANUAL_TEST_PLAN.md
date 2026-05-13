# Manual Test Plan

## Scope

This document defines the scope and structure of manual testing for Prokudin. It
covers feature-level and end-to-end testing for:

- Channel loading
- Alignment
- Adjustments
- Grid overlay
- Crop
- Presets
- Autosave
- Image saving
- Reset

Automated tests (unit/integration) are specified separately; this plan focuses
on interactive manual verification in a desktop environment.

---

## Test Environment

- **OS:** Linux, Windows, and macOS (at least one representative version each).
- **GPU:** No specific GPU requirements; tests assume CPU processing is sufficient.
- **Display:** Minimum 1920×1080 resolution recommended.
- **Input devices:** Mouse or trackpad, keyboard.
- **Test data:**
  - A small set of Sony ARW RAW files with clear structure and high contrast.
  - At least one "edge case" set with low-contrast / uniform regions.
  - Example output directory with write permission.

---

## Test Categories

### 1. Smoke Tests

Short sanity checks to run before any deeper testing:

- Application starts without errors.
- All toolbars and side panels are visible.
- "Load" buttons are clickable but show appropriate error if no file is chosen.
- Save button is disabled on fresh start.

### 2. Feature Tests

Feature-specific test sets are defined in dedicated documents:

- `GRID_TESTING.md`
- `RESET_TESTING.md`
- `CHANNEL_LOADING_TESTING.md`
- `ALIGNMENT_TESTING.md`
- `CROP_TESTING.md`
- `PRESETS_TESTING.md`
- `AUTOSAVE_TESTING.md`
- `IMAGE_SAVING_TESTING.md`

Each of these describes:

- Preconditions
- Step-by-step procedures
- Expected results
- Edge cases

### 3. Full Workflow Tests

End-to-end scenarios that chain multiple features together are defined in
`FULL_WORKFLOW_TESTING.md`.

---

## Test Execution Guidelines

- Log OS, build commit hash, and date for each run.
- Use fresh application state (no autosave) for baseline runs.
- Document any deviations from expected behaviour, including screenshots and
  sample inputs.
- When possible, re-run failing scenarios after fixes to confirm regression
  coverage.
