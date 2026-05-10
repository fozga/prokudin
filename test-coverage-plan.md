# Test Coverage Plan

## How to use this file

```bash
# Run all unit tests with coverage (uses dedicated .venv-test):
python3 run_tests.py

# Run a specific test file:
python3 run_tests.py tests/unit/test_core_align.py

# Run tests matching a keyword:
python3 run_tests.py -k "test_combine_channels"

# Generate HTML coverage report:
python3 run_tests.py  # HTML report is generated at htmlcov/index.html by default
```

### Coverage Enforcement Workflow

**Coverage targets are managed via `COVERAGE_TARGETS` in `tests/coverage_config.py`.**

When you add test coverage for a new module:

1. Create test file: `tests/unit/test_module_name.py`
2. Write tests until module reaches ≥90% coverage
3. **Update exclusions in `tests/coverage_config.py` (remove your module from `EXCLUDED_MODULES` when ready):**
   ```python
   EXCLUDED_MODULES = {
      "src.ui.handlers.example_module",  # Remove this entry once coverage is >= 90%
   }
   ```
4. Run: `python3 run_tests.py`
   - If you discover a bug while writing tests, see the **Testing Philosophy & Bug Handling** section before proceeding.
5. Coverage is now enforced at 90% minimum on next run

**Note:** Coverage targets are auto-discovered from `src/`; modules in `EXCLUDED_MODULES` are skipped from enforcement.

---

## Testing Guidelines (from review findings)

**Precise Assertions**
- Use specific assertion methods: `np.testing.assert_array_equal()` for exact matches, `assert_array_almost_equal()` for numerical tolerance
- Avoid broad `try/except` blocks; use `pytest.raises()` with `exc_info` for exception testing
- Verify complete output, not partial (e.g., all channels, not just red channel)
- Never use generic exception handlers like `except Exception:` that mask regressions

**Meaningful Test Names**
- Test names must accurately describe what is being tested
- Avoid misleading names like `test_accepts_different_sizes` if inputs are normalized first
- If a test covers an edge case or unimplemented feature, document why in a comment

**Test Organization**
- Group related tests into classes (e.g., `TestAlignImages`, `TestAlignmentError`)
- One logical scenario per test method; avoid combining multiple assertions into a single test
- Use descriptive docstrings explaining what is being tested and why

---

## Testing Philosophy & Bug Handling

If, while writing tests for a module, you discover that the existing implementation contains a bug or incorrect behavior:

1. **Write the test to verify the correct behavior, not the current (broken) behavior.**
   The test should assert what the function *ought* to do, based on its documented contract (docstring, type hints, spec) — not what it currently does. The test will fail (red). That is intentional and correct.

2. **Do NOT adjust the assertion to make the test pass against the broken code.**
   A passing test that validates wrong behavior is worse than no test at all — it creates false confidence and hides real defects.

3. **Mark the test with `@pytest.mark.xfail` and add a short reason string** that describes the known bug, for example:

   ```python
   @pytest.mark.xfail(reason="Bug: apply_adjustments clips before adding brightness, should clip after. See issue #42.")
   def test_brightness_applied_before_clipping():
       ...
   ```

   This keeps CI green while making the defect explicit and trackable.

4. **Inform the user** that a bug report / GitHub issue needs to be created for this defect, and print a short suggested issue title and one-sentence description that the user can copy directly into their issue tracker. Do not create the issue yourself.

5. Update the module's **Notes** field in this plan with a short description of the discovered bug and the issue reference.

---

## Coverage Summary

| Module | Stmts | Miss | Branch | Cover | Status |
|--------|-------|------|--------|-------|--------|
| `src/core/align.py` | 27 | 1 | 10 | 95% | ✅ DONE |
| `src/core/image_processing.py` | 18 | 0 | 9 | 100% | ✅ DONE |
| `src/services/processor.py` | 84 | 1 | 29 | 97% | ✅ DONE |
| `src/ui/default_state.py` | 16 | 0 | 4 | 100% | ✅ DONE |
| `src/ui/widgets/grid_types.py` | 12 | 0 | — | 100% | ✅ DONE |
| `src/ui/app_state.py` | 25 | 2 | 6 | 90% | ✅ DONE |
| `src/ui/handlers/channels.py` | 51 | 1 | 16 | 96% | ✅ DONE |
| `src/ui/handlers/keyboard.py` | 36 | 1 | 10 | 96% | ✅ DONE |
| `src/ui/handlers/display.py` | 36 | 1 | 12 | 96% | ✅ DONE |
| `src/ui/handlers/autosave.py` | 77 | 77 | — | 0% | PLAN |
| `src/ui/handlers/image_loading.py` | 22 | 22 | — | 0% | PLAN |
| `src/ui/handlers/image_saving.py` | 118 | 118 | — | 0% | PLAN |
| `src/ui/handlers/presets.py` | 65 | 65 | — | 0% | PLAN |
| `src/ui/qt_utils.py` | 10 | 10 | — | 0% | SKIP |
| `src/ui/widgets/sliders.py` | 12 | 12 | — | 0% | SKIP |
| `src/ui/widgets/channel_controller.py` | 136 | 136 | — | 0% | SKIP |
| `src/ui/widgets/image_viewer.py` | 140 | 140 | — | 0% | SKIP |
| `src/ui/widgets/grid_overlay.py` | 193 | 193 | — | 0% | SKIP |
| `src/ui/widgets/grid_settings_dialog.py` | 86 | 86 | — | 0% | SKIP |
| `src/ui/widgets/crop_handler.py` | 480 | 480 | — | 0% | SKIP |
| `src/ui/widgets/preset_panel.py` | 98 | 98 | — | 0% | SKIP |
| `src/ui/widgets/status_bar.py` | 27 | 27 | — | 0% | SKIP |
| `src/ui/main_window.py` | 344 | 344 | — | 0% | SKIP |
| `src/main.py` | 11 | 11 | — | 0% | SKIP |
| `src/__init__.py` | — | — | — | — | SKIP |
| `src/core/__init__.py` | — | — | — | — | SKIP |
| `src/services/__init__.py` | — | — | — | — | SKIP |
| `src/ui/__init__.py` | — | — | — | — | SKIP |
| `src/ui/handlers/__init__.py` | — | — | — | — | SKIP |
| `src/ui/widgets/__init__.py` | — | — | — | — | SKIP |

---

## Module Plan

### `src/core/align.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure logic (numpy/cv2 computation, no Qt, no IO) |
| **Current coverage** | 95% (26/27 statements, only line 98 uncovered) |
| **Target coverage** | 90%+ |
| **Test file** | `tests/unit/test_core_align.py` |
| **Dependencies** | numpy, cv2 (OpenCV) |
| **Notes** | 13 comprehensive tests covering align_images() and AlignmentError with synthetic image arrays. |

**Key test cases:**
- Aligned identical images produce zero offset
- Known pixel-shifted images produce correct alignment
- Single-channel input raises `AlignmentError`
- Empty or mismatched array shapes raise appropriate errors

---

### `src/core/image_processing.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure logic (numpy math, no Qt, no IO) |
| **Current coverage** | 100% (18/18 statements, 9/9 branches) |
| **Target coverage** | 95%+ |
| **Test file** | `tests/unit/test_core_image_processing.py` |
| **Dependencies** | numpy |
| **Notes** | 23 tests covering apply_adjustments() and combine_channels(). Verifies clipping, per-channel intensity, None propagation, dtype/shape. |

**Key test cases:**
- Zero brightness/contrast returns unchanged image
- Positive/negative brightness shifts pixel values correctly
- Contrast scaling works at boundaries (all-black, all-white)
- `combine_channels()` produces correct RGB from three grayscale arrays
- Output is clipped to [0, 255] range

---

### `src/services/processor.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 2 — Service/orchestration logic (no Qt, uses core modules) |
| **Current coverage** | 97% (83/84 statements, 27/29 branches) |
| **Target coverage** | 85%+ |
| **Test file** | `tests/unit/test_services_processor.py` |
| **Dependencies** | numpy, `src.core.align`, `src.core.image_processing` |
| **Notes** | 34 comprehensive tests covering `ChannelAdjustments` dataclass and `ImageProcessorService` class. Uses mocking for alignment and processing functions for deterministic testing. |

**Key test cases:**
- `load_channel_from_array()` stores RGB, converts to grayscale, triggers alignment on 3rd channel
- `adjust_channel()` updates adjustments and calls apply_adjustments correctly
- `get_channel_preview()` returns processed image or None
- `get_channel()` returns full or cropped single-channel image
- `get_combined()` combines channels with optional crop and intensity adjustments
- `has_aligned_channels()` and `has_processed_channels()` state checks
- `get_image_dimensions()` returns correct dimensions
- `reset()` clears all state and allows reuse
- `ChannelAdjustments` dataclass defaults and initialization

---

### `src/ui/default_state.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure logic (dataclasses, no Qt, no IO) |
| **Current coverage** | 100% (16/16 statements, 4/4 branches) |
| **Target coverage** | 100% |
| **Test file** | `tests/unit/test_ui_default_state.py` |
| **Dependencies** | None (stdlib only) |
| **Notes** | Contains `SliderDefaults` dataclass and `DefaultState` config class. Trivial to test — verify constants and `get_slider_defaults()` output. |

**Key test cases:**
- `SliderDefaults` default values are brightness=0, contrast=0, intensity=100
- `DefaultState.SHOW_COMBINED` is True
- `DefaultState.CURRENT_CHANNEL` is 0
- `DefaultState.CROP_MODE` is False
- `get_slider_defaults()` returns correct dict

---

### `src/ui/widgets/grid_types.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure constants (no imports, no Qt, no IO) |
| **Current coverage** | 100% (12/12 statements) |
| **Target coverage** | 100% |
| **Test file** | `tests/unit/test_ui_grid_types.py` |
| **Dependencies** | None |
| **Notes** | Module defines 11 string constants. Test that all expected constants exist and have correct string values. |

**Key test cases:**
- All 11 grid type constants are defined and non-empty strings
- `GRID_TYPE_NONE` equals `"none"`
- No duplicate values among the constants

---

### `src/ui/app_state.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 2 — Service logic (Qt only in TYPE_CHECKING, testable with mocks) |
| **Current coverage** | 90% (23/25 statements, 5/6 branches) |
| **Target coverage** | 90%+ |
| **Test file** | `tests/unit/test_ui_app_state.py` |
| **Dependencies** | `src.ui.default_state` (runtime); `PyQt5.QtCore.QRect` (TYPE_CHECKING only) |
| **Notes** | Dataclass with a `reset()` method. Qt imports are behind TYPE_CHECKING so module loads without Qt at runtime for attribute tests. Need to mock or skip `QRect` type for `crop_rect` field. |

**Key test cases:**
- Default construction matches `DefaultState` values
- `reset()` restores all fields to defaults after modification
- `channel_paths` is a mutable list of 3 `None` values by default

---

### `src/ui/handlers/channels.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 2 — Orchestration logic (Qt only via TYPE_CHECKING for MainWindow) |
| **Current coverage** | 96% (50/51 statements, 14/16 branches) |
| **Target coverage** | 80%+ |
| **Test file** | `tests/unit/test_handlers_channels.py` |
| **Dependencies** | numpy, `src.ui.handlers.display`, `src.ui.handlers.image_loading` |
| **Notes** | Functions take a `MainWindow` instance. Test with a mock MainWindow providing `.svc`, `.state`, `.controllers`, `.status_handler` attributes. |

**Key test cases:**
- `_process_channel_image()` calls `svc.load_channel_from_array()` and updates display
- `load_channel()` handles successful load and error cases
- `load_channel_from_path()` restores from file path or reports error
- `adjust_channel()` reads slider values and delegates to service
- `show_single_channel()` updates state and triggers display refresh

---

### `src/ui/handlers/keyboard.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 3 — Helper function in UI layer (needs mock but no QApplication) |
| **Current coverage** | 96% (35/36 statements, 9/10 branches) |
| **Target coverage** | 75%+ |
| **Test file** | `tests/unit/test_handlers_keyboard.py` |
| **Dependencies** | `PyQt5.QtCore.Qt`, `PyQt5.QtGui.QKeyEvent` |
| **Notes** | Single `handle_key_press()` function dispatching key events. Can test with mocked key event objects and mock MainWindow. May need Qt constants imported. |

**Key test cases:**
- Keys 1, 2, 3 switch to respective channels
- Key A toggles combined view
- Unhandled keys are ignored gracefully

---

### `src/ui/handlers/display.py` ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Priority** | 3 — Helper with Qt types (QRectF, QPixmap) |
| **Current coverage** | 96% (35/36 statements, 11/12 branches) |
| **Target coverage** | 70%+ |
| **Test file** | `tests/unit/test_handlers_display.py` |
| **Dependencies** | `PyQt5.QtCore.QRectF`, `PyQt5.QtGui.QPixmap` |
| **Notes** | Requires QPixmap which needs QApplication. Consider mocking `convert_to_qimage` and testing logic flow, or mark as requiring QApplication fixture. |

**Key test cases:**
- `update_main_display()` dispatches to combined or single based on state
- `show_combined_image()` calls service and updates viewer
- `show_single_channel_image()` shows correct channel

---

### `src/ui/handlers/autosave.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — Service logic with IO (JSON read/write, mockable) |
| **Current coverage** | 0% (77 statements) |
| **Target coverage** | 85%+ |
| **Test file** | `tests/unit/test_handlers_autosave.py` |
| **Dependencies** | `json`, `pathlib`, `PyQt5.QtCore.QRect` |
| **Notes** | Uses `tmp_path` fixture for file IO. Mock the MainWindow; test JSON serialization/deserialization of session state. QRect can be patched. |

**Key test cases:**
- `save_autosave()` writes valid JSON with channel paths and slider values
- `restore_autosave()` reads JSON and restores state correctly
- `clear_autosave()` removes the autosave file
- Handles missing/corrupt autosave file gracefully

---

### `src/ui/handlers/image_loading.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — IO logic (file reads via rawpy, mockable) |
| **Current coverage** | 0% (22 statements) |
| **Target coverage** | 80%+ |
| **Test file** | `tests/unit/test_handlers_image_loading.py` |
| **Dependencies** | `rawpy`, `PyQt5.QtWidgets.QFileDialog` |
| **Notes** | Mock `rawpy.imread` and `QFileDialog.getOpenFileName`. Test successful load returns numpy array, error handling for invalid files. |

**Key test cases:**
- Successful RAW file load returns RGB numpy array and file path
- File dialog cancelled returns `(None, None, "No file selected")`
- Invalid/corrupt file returns appropriate error message
- `load_raw_image_from_path()` works without dialog

---

### `src/ui/handlers/image_saving.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — IO logic (file writes via cv2, mockable) |
| **Current coverage** | 0% (118 statements) |
| **Target coverage** | 75%+ |
| **Test file** | `tests/unit/test_handlers_image_saving.py` |
| **Dependencies** | `cv2`, `numpy`, `PyQt5.QtWidgets.QFileDialog` |
| **Notes** | Mock `cv2.imwrite` and `QFileDialog.getSaveFileName`. Test crop application logic with numpy arrays; verify correct format dispatch. |

**Key test cases:**
- `apply_crop()` correctly slices numpy array
- Save dispatches to correct format based on extension
- Dialog cancellation handled gracefully
- Per-channel save creates individual files
- Combined save produces 3-channel image

---

### `src/ui/handlers/presets.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — IO logic (JSON + PNG, mockable) |
| **Current coverage** | 0% (65 statements) |
| **Target coverage** | 75%+ |
| **Test file** | `tests/unit/test_handlers_presets.py` |
| **Dependencies** | `json`, `pathlib`, `cv2`, `PyQt5.QtWidgets` |
| **Notes** | Mock file IO and Qt dialogs. Test preset save/load cycle with `tmp_path`. |

**Key test cases:**
- `save_preset()` writes JSON with slider values and optional thumbnail
- `apply_preset()` reads JSON and sets slider values on controllers
- Empty preset name handled
- Missing preset file handled gracefully

---

### `src/ui/qt_utils.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Requires QApplication for QImage construction; no pure-logic path to test without Qt event loop. |

---

### `src/ui/widgets/sliders.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | QSlider subclass requiring QApplication for instantiation. |

---

### `src/ui/widgets/channel_controller.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Complex QGroupBox widget requiring QApplication and full widget tree. |

---

### `src/ui/widgets/image_viewer.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | QGraphicsView subclass requiring QApplication and event loop for interactions. |

---

### `src/ui/widgets/grid_overlay.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | QPainter-based rendering requiring active QApplication and paint device. |

---

### `src/ui/widgets/grid_settings_dialog.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | QFrame dialog requiring QApplication for widget instantiation. |

---

### `src/ui/widgets/crop_handler.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Heavy Qt widget integration (QGraphicsView, mouse events, QPainter). Requires running event loop. |

---

### `src/ui/widgets/preset_panel.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | QWidget with QScrollArea requiring QApplication; also does IO for thumbnail loading. |

---

### `src/ui/widgets/status_bar.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | QStatusBar wrapper requiring QApplication for instantiation. |

---

### `src/ui/main_window.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | QMainWindow subclass (344 statements) requiring full QApplication and all widgets. Integration-test candidate, not unit-testable. |

---

### `src/main.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Qt entry point; contains only `main()` which creates QApplication and runs event loop. |

---

### `src/__init__.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Empty package marker (license header only). |

---

### `src/core/__init__.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Empty package marker (license header only). |

---

### `src/services/__init__.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Empty package marker (license header only). |

---

### `src/ui/__init__.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Empty package marker (license header only). |

---

### `src/ui/handlers/__init__.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Empty package marker (license header only). |

---

### `src/ui/widgets/__init__.py`

| Field | Value |
|-------|-------|
| **Priority** | — |
| **Status** | SKIP |
| **Notes** | Empty package marker (license header only). |
