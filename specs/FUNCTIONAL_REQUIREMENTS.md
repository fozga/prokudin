# Functional Requirements — Prokudin

## Purpose

This document defines a consolidated, system-level set of functional requirements for the Prokudin desktop application. It synthesizes and deduplicates the content of three separate functional requirements drafts into a single, coherent reference for integration and system-level testing. Requirements are stated from the perspective of the user or the system as a whole and are grouped by feature area.

---

## Numbering Convention

- Requirements are numbered `FR-1`, `FR-2`, … and grouped by feature area.
- Requirements marked **(inferred)** are not explicitly documented in the repository but are consistent with the existing design and typical for this class of application.
- Each requirement is intended to be individually testable at integration or system level.

---

## 1. Channel Management

**FR-1 — Load three spectral channels.**  
The application shall allow the user to load exactly one Sony ARW RAW file into each of three spectral channel slots: IR (index 0 / Red), VIS (index 1 / Green), and UV (index 2 / Blue). Each channel may be loaded or reloaded independently at any time without affecting the other two channels.

**FR-2 — File dialog filtering and modality.**  
The file selection dialog for loading channels shall:
- filter selectable files to `*.arw` by default, and  
- be modal with respect to the main window (the main UI is blocked while the dialog is open). **(inferred)**

**FR-3 — Loading in any order and incomplete set indication.**  
Channels may be loaded in any order; if fewer than three channels are loaded, the UI shall clearly indicate missing channels (e.g. empty thumbnails, status information) and shall not present combined-view or export functionality as available for an incomplete set. **(partly inferred)**

**FR-4 — Successful channel load feedback.**  
On successful load of a channel, the system shall:
- update the corresponding per‑channel thumbnail preview, and  
- display a success message in the status bar identifying the loaded spectral slot.

**FR-5 — Handling unreadable or invalid files.**  
If a selected file:
- does not exist,  
- cannot be decoded as a valid ARW file, or  
- is unreadable due to permission or format issues,  

the system shall:
- display a descriptive, non‑blocking error message in the status bar,  
- leave the previously loaded channel content unchanged, and  
- remain responsive without raising an unhandled exception or showing a blocking modal dialog.

**FR-6 — Reloading a channel.**  
When the user reloads a channel with a new file:
- only that channel’s data shall be replaced,  
- alignment and downstream state shall be recomputed or marked stale as appropriate, and  
- existing per‑channel adjustment values (brightness, contrast, intensity) for that channel shall be preserved and re‑applied to the newly aligned result.

**FR-7 — Path-based loading for restore.**  
The session-restore path (`load_channel_from_path`) shall load channel files directly from stored paths without opening a file dialog; if a file is missing or unreadable, restore for that specific channel shall fail with a status-bar error, while other channels continue to load normally.

**FR-8 — Clearing an individual channel.**  
The system shall provide a way to clear (unload) an individual channel, returning it to the “not loaded” state without affecting the other channels. **(inferred)**

---

## 2. Alignment

**FR-9 — Automatic alignment on three loaded channels.**  
When all three channels (IR, VIS, UV) are successfully loaded, the application shall automatically trigger an alignment process without additional user action, using the IR (Red) channel as the fixed spatial reference and warping VIS (Green) and UV (Blue) to match it.

**FR-10 — Alignment algorithm.**  
Alignment shall use:
- ORB feature detection (around 1 000 features per channel),  
- brute-force Hamming matching with cross-check, and  
- partial affine transformation estimation (`estimateAffinePartial2D`)  

and shall apply the resulting transforms both to grayscale working arrays and full RGB arrays so that all downstream operations see geometrically consistent data.

**FR-11 — Alignment success behaviour.**  
On successful alignment, the system shall:
- populate aligned grayscale and aligned RGB arrays for all three channels with a common output resolution equal to that of the reference channel, and  
- update the combined-colour preview using these aligned results.

**FR-12 — Alignment failure conditions.**  
If alignment cannot be computed (e.g. too few feature matches, degenerate geometry, or missing descriptors), the system shall:
- treat this as an alignment error,  
- report a clear message in the status bar,  
- keep aligned arrays unset,  
- disable image export that depends on alignment, and  
- remain fully usable for further channel loading or replacement.

**FR-13 — No re-alignment on non-geometric changes.**  
Adjusting sliders, changing grid settings, toggling views, applying presets, or entering/exiting Crop mode shall not trigger re-alignment; re‑alignment occurs only when a channel is newly loaded or replaced.

**FR-14 — Out-of-bounds handling.**  
Regions of a warped channel that map outside the output image bounds after applying the affine transform shall be filled with black (zero-valued pixels).

---

## 3. Adjustments and Visualisation

**FR-15 — Per-channel adjustment controls.**  
For each spectral channel (IR, VIS, UV), the system shall provide independent, non‑destructive adjustment controls for at least:
- brightness,  
- contrast, and  
- intensity (gain).

**FR-16 — Adjustment ranges and defaults.**  
Each adjustment control shall have a defined numeric range and default value (e.g. brightness/contrast centred at 0, intensity around 100%), and resetting all controls for a channel shall produce output identical to the unmodified aligned image for that channel.

**FR-17 — Immediate visual feedback.**  
Changes to adjustment controls shall be reflected immediately (or near-real-time) in:
- the per‑channel thumbnail previews, and  
- the main viewer (combined or single‑channel view),  

without requiring an explicit “Apply” action.

**FR-18 — Non-destructive adjustments.**  
Adjustments shall be applied to dedicated working copies (`processed` arrays); original and aligned arrays shall remain unchanged so that adjustments can be reset or recalculated at any time without reloading the source files.

**FR-19 — Per-slider reset.**  
Each adjustment slider shall support a local reset (e.g. via double-click) that returns that specific parameter to its default value, without affecting other parameters for that channel.

**FR-20 — View modes.**  
The main viewer shall support:
- a combined RGB view that composites all three aligned channels, and  
- single‑channel views for IR, VIS, and UV individually,  

and shall allow the user to switch between these modes at any time; switching views shall not alter underlying data or adjustment values.

**FR-21 — Consistency between single-channel and combined views.**  
When viewing a single channel, the system shall render that channel with its current adjustments; changes made in single‑channel view shall remain in effect when returning to combined view.

---

## 4. Crop

**FR-22 — Crop mode and interaction.**  
The system shall provide a dedicated Crop mode in which the user can define and adjust a rectangular crop region over the image by dragging its corners and edges. Crop mode shall be visually indicated and shall temporarily focus interactions on crop-related operations.

**FR-23 — Non-destructive crop in image coordinates.**  
The crop rectangle shall:
- be defined in image pixel coordinates (independent of zoom/pan), and  
- be non-destructive (no modification of underlying image arrays; crop is applied as a view/window when displaying or saving).

**FR-24 — Aspect ratio constraints.**  
Crop mode shall support:
- a Free (unconstrained) mode, and  
- several fixed aspect ratios (including at least 16:9, 3:2, 4:3, 5:4, 1:1, 4:5, 3:4, 2:3, 9:16).  

When a ratio is active, resize operations shall preserve that ratio while keeping the crop within image bounds.

**FR-25 — Bounds and minimum size.**  
The crop rectangle shall always remain fully inside the image bounds and shall respect a minimum size to avoid degenerate rectangles (e.g. extremely thin or zero‑area). Attempts to drag beyond bounds shall clamp to valid coordinates.

**FR-26 — Accept vs Cancel behaviour.**  
While editing a crop:
- the in‑progress rectangle shall **not** affect display or export;  
- clicking **Accept** shall store the current rectangle as the saved crop and deactivate Crop mode;  
- clicking **Cancel** (or exiting Crop mode without accepting) shall discard in‑progress changes and keep the previously saved crop (if any) or “no crop” state.

**FR-27 — Crop application to display and saving.**  
A saved crop rectangle, when present and Crop mode is inactive, shall be consistently applied:
- to the main combined view,  
- to any views or previews that are defined to respect crop (as per design), and  
- to all exported images (combined and per-channel).  

If no crop is saved, exports and displays shall use the full aligned extent.

**FR-28 — Crop and session restore.**  
The accepted crop rectangle shall be persisted in the session state and restored on startup if autosave is available; after restore, the crop shall be active (affecting display and saving) while Crop mode remains inactive until explicitly entered.

**FR-29 — Crop availability.**  
Crop mode shall have no effect when no image is loaded; attempting to enter Crop mode in an empty state shall either be disabled or result in no visible change, without errors.

---

## 5. Grid Overlay

**FR-30 — Visual composition grid.**  
The system shall provide an optional visual grid overlay drawn on top of the image in the viewer as a composition aid. The grid shall be purely cosmetic and shall never affect image data, crop geometry, or export results.

**FR-31 — Supported grid types.**  
The grid overlay shall support multiple layout types, including at least:
- None,  
- Rule-of-thirds (3×3),  
- Golden ratio, and  
- several diagonal families (1:1, 2:3, 3:2, 3:4, 4:3, and diagonal‑thirds/golden variants as defined in `grid_types`).

**FR-32 — Grid appearance configuration.**  
The user shall be able to configure at least:
- grid type, and  
- line width,  

via a grid settings panel or dialog, and changes shall be reflected immediately in the viewer.

**FR-33 — Consistency across modes.**  
A single shared grid configuration (type, line width, colour, opacity) shall apply consistently to both normal view and Crop mode.

**FR-34 — Grid in Crop mode.**  
When Crop mode is active and a crop rectangle is being edited, the grid overlay (if enabled) shall be drawn clipped to the interior of the current crop rectangle, not over the dimmed outside area.

---

## 6. Presets

**FR-35 — Saving presets.**  
The application shall allow the user to save the current per-channel adjustment state (brightness, contrast, intensity for each channel) as a named preset, stored as a JSON file in a presets directory. Saving a preset shall not store image pixels, channel paths, or crop geometry.

**FR-36 — Applying presets.**  
Selecting a preset in the preset panel shall:
- update the sliders for all channels to the stored values,  
- update associated text inputs if present, and  
- trigger re-application of adjustments so that previews and the main view reflect the preset immediately.

**FR-37 — Preset persistence and listing.**  
Presets shall persist across application restarts and shall be enumerated from the presets directory into the preset sidebar at startup; invalid preset files (e.g. malformed JSON) shall be ignored rather than causing crashes.

**FR-38 — Neutral / built-in preset.**  
The application shall ship with at least one built‑in “neutral” preset corresponding to default adjustment values, available on first launch.

**FR-39 — Presets and other features.**  
Applying a preset shall not change:
- which channel files are loaded, or  
- the current crop rectangle;  

it may influence autosave (through updated slider values) and will be reflected in subsequent session restores.

**FR-40 — Presets and reset.**  
Resetting the current session shall not delete or modify preset files; presets shall remain available and usable after a reset.

---

## 7. Autosave and Session Management

**FR-41 — Automatic session save.**  
The application shall automatically save the current session state — including channel file paths, per‑channel adjustment values, and the accepted crop rectangle — to a local JSON file (`autosave.json`) in a configuration directory, without explicit user action.

**FR-42 — Debounced autosave triggering.**  
Autosave shall be driven by a debounced timer tied to slider changes: the timer restarts on each change and fires only after a defined period of inactivity (e.g. 500 ms), resulting in a single write for a burst of interactions rather than one write per change.

**FR-43 — Session restore on startup.**  
On startup, if `autosave.json` exists and is valid, the application shall:
- restore each channel whose path is still accessible and readable,  
- restore slider values for all channels,  
- restore the saved crop rectangle (if any), and  
- update previews and the main display accordingly.

**FR-44 — Behaviour with missing or invalid autosave.**  
If:
- `autosave.json` does not exist, or  
- is unreadable or malformed,  

the application shall skip restoration and start in a clean default state without crashing or blocking the user.

**FR-45 — Partial restore on missing files.**  
During restore, if a channel file path recorded in `autosave.json` no longer exists or cannot be opened, the application shall:
- skip loading that channel,  
- report the failure in a non‑blocking status-bar message, and  
- continue restoring other channels and UI state.

**FR-46 — Autosave content constraints.**  
Autosave shall never write raw image pixel data; it shall store only:
- file paths,  
- numeric adjustments, and  
- crop rectangle coordinates (or `null`).

**FR-47 — Signal blocking during restore.**  
When restoring slider values from autosave, the implementation shall block adjustment signals while programmatically setting values, then re‑enable them to avoid spurious reprocessing or redundant autosave triggers.

**FR-48 — Single autosave slot.**  
Only one autosave slot (`autosave.json`) shall exist; the application shall not manage multiple named sessions or a history of autosaves. **(explicit constraint)**

---

## 8. Image Saving

**FR-49 — Save availability conditions.**  
The Save action (e.g. button/menu item) shall be enabled only when a valid aligned combined image is available (i.e. alignment has succeeded for the required channels); otherwise it shall be disabled and not invocable.

**FR-50 — Save dialog and formats.**  
When Save is invoked, the application shall show a modal file dialog for selecting:
- destination path, and  
- output format (supporting at least JPEG, PNG, and TIFF).  

If the user cancels the dialog, no files shall be written and the status bar may indicate that the save was cancelled.

**FR-51 — Output files and naming.**  
A save operation shall produce:
- one combined-colour image at the chosen base path, and  
- up to three per‑channel colour images with distinguishable suffixes (e.g. `_ir`, `_vis`, `_uv`),  

depending on configuration and available channels.

**FR-52 — Export fidelity and adjustments.**  
Exported images shall be built from aligned channel data. Whether per‑channel adjustments are reflected in the exported combined/per‑channel images shall follow the explicit design in the project specs; currently the combined image is specified to be built from aligned grayscale channels without adjustments, so the export may differ from the on‑screen preview. **(take current spec as source of truth)**

**FR-53 — Crop interaction with saving.**  
If an accepted crop rectangle exists and Crop mode is inactive, all exported images (combined and per‑channel) shall be cropped to exactly that rectangle. If Crop mode is active and a crop is being edited, the previously accepted crop (if any) shall be applied; an in‑progress crop shall not affect exports.

**FR-54 — Save error handling.**  
If any output file cannot be written (e.g. due to permission errors, missing directories, insufficient disk space, or codec failure), the system shall:
- report the failure in the status bar with a clear message,  
- avoid crashing, and  
- leave the current session intact so the user can try again with different parameters.

**FR-55 — No overwriting of input files.**  
The application shall never overwrite original input channel files when saving; only new output files at user-specified locations shall be created or overwritten.

---

## 9. Reset (New)

**FR-56 — Reset entry points.**  
The application shall provide a Reset (New) action accessible at least via:
- a toolbar or menu action, and  
- a keyboard shortcut (e.g. Ctrl+N),  

both of which invoke the same reset logic.

**FR-57 — Reset effect on session state.**  
Reset shall:
- clear all loaded image data and intermediate processing results,  
- reset all sliders to their default values,  
- clear both current and saved crop rectangles and deactivate Crop mode,  
- reset UI state flags (e.g. view mode) to defaults,  
- delete the autosave file, and  
- disable Save (and other actions that require loaded data).

**FR-58 — Reset and autosave.**  
During reset, the autosave debounce timer shall be stopped and `autosave.json` shall be removed so that a subsequent application start does not restore the pre‑reset session. Any failure to delete `autosave.json` (e.g. file missing or permissions) shall be silently ignored.

**FR-59 — Reset and persistent data.**  
Reset shall not remove or modify persistent user data such as presets or global configuration files (other than the autosave file); presets shall remain available for subsequent sessions.

**FR-60 — Reset from empty state.**  
Invoking Reset when the application is already in its initial empty state shall have no effect other than possibly displaying a brief status message.

---

## 10. General UI & Workflow

**FR-61 — Combined workflow support.**  
Within a single run, the application shall support a complete workflow consisting of:
- loading channels,  
- alignment,  
- adjustments,  
- grid usage,  
- cropping,  
- autosaving / restoring,  
- preset usage, and  
- final image saving,  

without requiring application restart.

**FR-62 — Sequential projects in one session.**  
The user shall be able to complete one project (from load to save), reset or clear it, and start another project with different inputs in the same application session.

**FR-63 — Status bar feedback and control enabling.**  
The status bar shall provide concise feedback on major operations and errors (loading, alignment, autosave, saving, reset, restore). Controls such as Save, Crop, and Align shall be enabled or disabled context‑sensitively based on the current state so that unusable actions cannot be invoked.

**FR-64 — Non-blocking error reporting.**  
Where possible, errors (e.g. load/save failures, alignment issues, missing restore files) shall be reported using non‑blocking UI elements (e.g. status bar) rather than modal dialogs, except for clearly destructive actions that require confirmation. **(partly inferred)**

**FR-65 — Graceful shutdown.**  
On application exit, any in‑progress operations (e.g. autosave) shall either complete or be safely aborted, and the last consistent state shall be reflected in autosave where applicable. The application shall shut down without leaving corrupted config or autosave files. **(inferred)**

