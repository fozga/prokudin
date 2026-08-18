# Non-Functional Requirements — Prokudin

## Purpose

This document defines a consolidated and comprehensive set of non-functional requirements for the Prokudin desktop application. It synthesizes and deduplicates several drafts of non-functional requirements into a single reference covering performance, reliability, usability, maintainability, portability, security, logging, and recovery. Requirements are intended to guide implementation and to serve as a basis for integration and system-level testing.

Requirements with soft numeric targets are marked **TBD** for refinement once empirical performance and resource-usage data are available. Requirements marked **(inferred)** are not explicitly stated in the repository but are consistent with the existing design and common practice for desktop image-processing applications.

For release **v0.1.0**, the most critical performance requirements (NFR-1, NFR-2, NFR-3, NFR-4, NFR-7) are now defined with initial numeric targets based on baseline measurements on a reference development machine. These initial targets are intentionally conservative and may be tightened in later releases as more benchmark data is collected.

---

## Numbering Convention

- Requirements are numbered `NFR-1`, `NFR-2`, … and grouped by quality attribute.
- Each requirement addresses a single quality aspect that can be validated by test or inspection.
- Soft targets use phrases such as "within a few seconds" or "feels responsive" and may later be converted into concrete thresholds.

---

## 1. Performance

Reference baseline used for v0.1.0 targets (measured 2026-08-18):
- Machine: Linux 6.8, Intel Core i5-10210U, 31.2 GiB RAM, SSD-backed workspace.
- Input set: `input/_DSC4370.ARW`, `input/_DSC4371.ARW`, `input/_DSC4372.ARW`.
- Method: repeated timing runs of production code paths (raw decode/load, 3-channel alignment, adjustment/display refresh path, crop interaction display/geometry path, and export).

**NFR-1 — Channel loading time.**  
Channel loading (RAW decode via rawpy plus grayscale conversion) for a typical Sony ARW file shall complete in **<= 1.5 seconds per channel** on reference hardware, with observed baseline medians around **0.97 seconds**. This target is an initial v0.1.0 threshold and may be tightened in later releases.

**NFR-2 — Alignment time.**  
Automatic alignment of three loaded channels (ORB feature extraction, matching, affine estimation, and warping) shall complete in **<= 2.0 seconds** for full-resolution typical ARW images on reference hardware, with observed baseline medians around **0.73 seconds**. This target is an initial v0.1.0 threshold and may be tightened in later releases.

**NFR-3 — Adjustment responsiveness.**  
Per-channel adjustment changes (brightness, contrast, intensity) shall produce a visible main-view update in **<= 0.6 seconds** for typical image sizes on reference hardware, with observed baseline medians around **0.41 seconds** for the adjustment-plus-display path. This target is an initial v0.1.0 threshold and may be tightened in later releases.

**NFR-4 — Crop interaction responsiveness.**  
Crop interaction shall satisfy both of the following on reference hardware for typical image sizes:
- Enter/exit Crop mode display updates shall complete in **<= 1.0 second per transition cycle**, with observed baseline medians around **0.69 seconds** for crop/full display refresh.
- Dragging or resizing the crop rectangle shall keep interactive update latency **<= 50 ms per visual update** (targeting smooth interaction), with crop-geometry computations observed to be far below this threshold in baseline runs.
These targets are initial v0.1.0 thresholds and may be tightened in later releases.

**NFR-5 — Autosave overhead.**  
Autosave operations (serialising session state and writing `autosave.json`) shall complete within approximately 500 ms of the debounce timer firing and shall not cause noticeable pauses or stutters in the UI during normal interaction. **(TBD)**

**NFR-6 — Session restore time.**  
Session restoration on startup (including channel reload, re‑alignment, adjustment reapplication, and crop restoration) shall complete within a time comparable to a fresh three‑channel load and alignment cycle, such that the application is ready for interaction within a few seconds on reference hardware. **(TBD)**

**NFR-7 — Export performance.**  
Export of combined output plus per-channel outputs shall meet the following initial v0.1.0 thresholds on reference hardware for typical full-resolution ARW-derived images:
- **JPEG:** <= 3 seconds total (baseline median approx. 1.88 seconds).
- **TIFF:** <= 6 seconds total (baseline median approx. 3.85 seconds).
- **PNG (compression level 9):** <= 75 seconds total (baseline median approx. 66.1 seconds).
The UI shall remain responsive where possible; if the operation is synchronous, the Save action shall be protected from re-entry and a status message shall indicate progress or completion. These thresholds are initial v0.1.0 targets and may be tightened in later releases.

**NFR-8 — Behaviour on large images.**  
When processing larger‑than‑typical images, alignment, cropping, and saving may take longer but the application shall remain responsive, providing status or progress feedback rather than appearing to hang. **(inferred)**

**NFR-9 — Memory usage.**  
The application shall not exhibit unbounded growth in memory usage when repeatedly loading, reloading, and processing channels. Memory consumption for typical workflows shall remain within reasonable limits for a mid‑range desktop, with no evidence of leaks across long sessions. **(TBD; inferred)**

---

## 2. Reliability & Robustness

**NFR-10 — No unhandled crashes.**  
The application shall not terminate with unhandled exceptions in response to any user‑reachable action (e.g. loading invalid files, saving to unwritable locations, starting with a corrupted autosave). All such errors shall be caught and handled gracefully.

**NFR-11 — Robustness to corrupted and unsupported files.**  
Opening corrupted, partially downloaded, or unsupported image files shall fail gracefully with an error message; previously loaded data shall remain intact, and the application shall stay usable.

**NFR-12 — Alignment failure robustness.**  
If alignment fails (e.g. insufficient features or degenerate geometry), the application shall remain in a consistent state, allow channels to be reloaded, and permit re‑attempting alignment without restart.

**NFR-13 — Autosave robustness.**  
Malformed, partially written, or otherwise invalid autosave files shall not prevent startup; they shall be detected and ignored, and the application shall fall back to a clean initial state.

**NFR-14 — Autosave filesystem errors.**  
Filesystem errors during autosave (read‑only config directory, disk full, missing directories) shall be logged and ignored without interrupting ongoing user interaction or leaving the application in an inconsistent state.

**NFR-15 — Reset robustness.**  
The Reset operation shall always leave the application in the same clean state as a fresh launch, regardless of prior state (no channels, partial session, full session, crop active). Any sub‑step failures (e.g. failure to delete the autosave file) shall not prevent completion of Reset.

**NFR-16 — Stability over prolonged use.**  
During extended sessions involving many cycles of load–align–adjust–crop–save, the application shall remain stable without crashes or major performance degradation; minor slowdowns may be acceptable and should be characterised during testing. **(inferred)**

**NFR-17 — Atomic or detectable autosave writes.**  
Autosave writes shall be performed in an atomic or equivalent fashion such that the resulting file is either fully valid or detectably invalid. Partially written autosave files shall not be silently interpreted as valid session data.

**NFR-18 — Preset corruption handling.**  
Corrupted or malformed preset files shall be reported or skipped without preventing the application from launching or listing other valid presets. **(inferred)**

---

## 3. Usability

**NFR-19 — Clear status and error messages.**  
Status bar and error messages shall use clear, concise, non‑technical language that indicates which operation was attempted (load, align, save, restore, etc.) and what went wrong, avoiding raw stack traces or internal jargon.

**NFR-20 — Feedback for key operations.**  
All major user-visible operations (load, alignment, adjustments, crop accept, preset apply, save, reset, session restore) shall provide visible feedback, typically via the status bar, indicating success, failure, or progress.

**NFR-21 — Appropriate message timeouts.**  
Status messages shall use appropriate lifetimes: short for transient confirmations, longer or sticky for errors and mode indicators, so that users have enough time to read them without cluttering the UI.

**NFR-22 — Predictable control availability.**  
Controls (buttons, menu items, sliders) shall be enabled or disabled consistently based on the current state, preventing users from invoking actions that cannot succeed (e.g. Save with no aligned channels, Crop with no image).

**NFR-23 — Minimal blocking dialogs.**  
Modal dialogs shall be used sparingly and only where necessary (e.g. destructive confirmations, file selection). Non‑critical warnings and errors should be displayed using non‑blocking mechanisms (status bar, notifications) where possible.

**NFR-24 — Visual indication of modes.**  
Important UI modes and states (Crop mode active vs inactive, grid enabled vs disabled, combined vs single‑channel view) shall be visually distinct so users can immediately understand the current context.

**NFR-25 — Slider ergonomics.**  
Sliders shall support efficient interaction, including fine‑grained control and double‑click to reset to default where defined, enabling quick experimentation and recovery from extreme settings.

**NFR-26 — Preset panel usability.**  
The preset panel shall present preset names (and thumbnails if available) in a scrollable list that remains usable even with many presets saved; applying a preset shall update controls and previews immediately without further confirmation.

**NFR-27 — Clear initial state.**  
When no channels are loaded (fresh start or after Reset), the UI shall present a clear, stable initial state (empty or placeholder previews, disabled Save, appropriate mode text) to guide the user toward loading images as the first step.

**NFR-28 — Keyboard and mouse efficiency.**  
Common operations (switching views, toggling grid, entering Crop mode, triggering Reset) should be accessible both via mouse and via well‑chosen keyboard shortcuts to support efficient workflows. **(inferred)**

---

## 4. Maintainability & Testability

**NFR-29 — Layered architecture.**  
The codebase shall maintain a strict layering discipline: core image-processing logic in `src/core/` shall not depend on `src/services/` or any UI modules; `src/services/` shall have no Qt dependencies; `src/ui/` may depend on both lower layers but not vice versa.

**NFR-30 — Core/UI separation for tests.**  
Core logic for alignment, crop geometry, grid geometry, autosave, and preset management shall be implemented in Qt‑free components so that they can be unit‑tested without starting a GUI or `QApplication`.

**NFR-31 — Modularity of features.**  
Channel loading, alignment, crop, presets, autosave, image saving, grid overlay, and reset behaviour shall be organised into cohesive modules or services, reducing coupling and simplifying future maintenance.

**NFR-32 — Spec–implementation–test traceability.**  
For each feature described under `specs/features/`, there shall be corresponding implementation and test artefacts such that behaviour can be traced from requirement through implementation to verification.

**NFR-33 — Static analysis and style.**  
The codebase shall conform to the project’s static-analysis standards (PEP 8/flake8, pylint), formatting rules (Black + isort), and type‑checking requirements (mypy); violations shall be caught in CI before changes are merged.

**NFR-34 — Documentation coverage.**  
Public modules, classes, and functions shall have docstrings that satisfy the configured documentation‑coverage checks; documentation updates shall be part of feature or refactor changes.

**NFR-35 — Configurability of key parameters.**  
Frequently tuned parameters such as alignment search ranges, autosave intervals, and default grid settings should be configurable without code changes (e.g. via configuration files or documented constants) to ease experimentation and deployment adjustments. **(inferred)**

**NFR-36 — Test coverage and automation.**  
Automated tests shall cover core algorithms (`src/core/`) and key flows, and shall be runnable locally and in CI via dedicated scripts (e.g. `run_tests.py`, `run_checks.py`). Manual test plans in `specs/testing/` shall complement automated tests for complex scenarios.

---

## 5. Portability & Platform Support

**NFR-37 — Supported platforms.**  
The application shall run on the explicitly supported desktop platforms documented in the project (at minimum Linux with Python 3.10+, PyQt5, and declared Python dependencies). Support for Windows and macOS is desirable but secondary.

**NFR-38 — Dockerised execution.**  
The application shall be runnable inside a Docker container using the provided Dockerfile and helper scripts (e.g. `run.sh`), with configuration and presets directories mappable to host volumes.

**NFR-39 — Dependency and licence management.**  
All runtime dependencies (Qt, rawpy, OpenCV, NumPy, etc.) shall be explicitly versioned and tracked; licence compatibility shall be verified (e.g. via `pip-licenses`) to ensure the overall application remains open‑source‑compliant.

**NFR-40 — Portable configuration formats.**  
Configuration, autosave, and preset data shall be stored in portable, platform‑independent formats (UTF‑8 JSON), and configuration directory resolution (`/app/config` → `<project_root>/config` → `~/.config/prokudin`) shall work correctly in both bare‑metal and container environments.

**NFR-41 — Behaviour consistency across platforms.**  
Within the constraints of platform differences (file dialogs, fonts, window management), the application shall provide consistent functional behaviour and workflow across all supported platforms.

---

## 6. Security & Privacy

**NFR-42 — Local-only processing.**  
All image processing and session management operations shall occur locally on the user’s machine. The application shall not transmit image data, file paths, or session metadata over any network connection without explicit user consent. **(inferred)**

**NFR-43 — Limited file-system access.**  
The application shall access only those files and directories explicitly selected by the user (input images, output destinations) and its own configuration/presets directories; it shall not scan or modify unrelated areas of the filesystem. **(inferred)**

**NFR-44 — Safe handling of image files.**  
Input image files shall be treated purely as data and shall not be executed or interpreted as code; external tools shall not be invoked on user paths without appropriate validation. **(inferred)**

**NFR-45 — Privacy of session data.**  
Autosave and preset files shall contain only the information necessary to restore sessions and presets (paths, parameters) and shall be stored in user‑accessible locations; no hidden telemetry or personally sensitive data shall be collected or stored without explicit documentation and consent.

---

## 7. Error Handling & Logging

**NFR-46 — Structured logging.**  
The application shall use the standard Python `logging` module for internal diagnostics. Expected failure modes (file I/O, decode failures, save errors, autosave issues) shall log at `WARNING` or `ERROR` levels as appropriate.

**NFR-47 — Graceful degradation of logging.**  
If log files cannot be written (e.g. due to missing directories or permissions), logging failures shall not crash the application; logging may be degraded or disabled, and a warning may be shown where appropriate.

**NFR-48 — No raw tracebacks in UI.**  
End users shall not see raw stack traces or unformatted exception messages in the UI; these details may be logged for diagnostics but not exposed in status messages.

**NFR-49 — Partial-failure reporting.**  
Operations that can partially succeed (e.g. restoring some but not all channels, saving some but not all images) shall complete as far as possible and present a clear summary of which elements succeeded and which failed.

---

## 8. Recovery, Data Integrity & Resource Usage

**NFR-50 — Integrity of saved images.**  
Exported combined and per‑channel images shall either be written correctly and completely or not at all. The system should minimise the chance of partially written files; such files, if created, should be detectable by standard image tools. **(inferred)**

**NFR-51 — Behaviour after unexpected shutdown.**  
After unexpected termination (e.g. power loss, OS crash), previously saved output files and the last fully written autosave (if any) shall remain usable. On next start, the application shall offer or attempt to restore from any valid autosave found.

**NFR-52 — Consistent internal state transitions.**  
State transitions such as loading channels, running alignment, entering/exiting Crop mode, and resetting shall be designed so that partial updates do not leave the application in an unusable or inconsistent state; transitions shall either complete successfully or fail with a rollback to a safe previous state.

**NFR-53 — Resource-friendly CPU/GPU usage.**  
If multi‑core CPU or GPU acceleration is used, the application shall avoid saturating system resources to the point of making the machine unusable; long‑running computations should be interruptible where feasible. **(inferred)**

