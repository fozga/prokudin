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

---

## Coverage Summary

| Module | Stmts | Miss | Branch | Cover | Status |
|--------|-------|------|--------|-------|--------|
| `src/core/align.py` | 27 | 27 | — | 0% | PLAN |
| `src/core/image_processing.py` | 18 | 18 | — | 0% | PLAN |
| `src/services/processor.py` | 84 | 84 | — | 0% | PLAN |
| `src/ui/default_state.py` | 16 | 16 | — | 0% | PLAN |
| `src/ui/widgets/grid_types.py` | 12 | 12 | — | 0% | PLAN |
| `src/ui/app_state.py` | 25 | 25 | — | 0% | PLAN |
| `src/ui/handlers/channels.py` | 51 | 51 | — | 0% | PLAN |
| `src/ui/handlers/keyboard.py` | 36 | 36 | — | 0% | PLAN |
| `src/ui/handlers/display.py` | 36 | 36 | — | 0% | PLAN |
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

### `src/core/align.py`

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure logic (numpy/cv2 computation, no Qt, no IO) |
| **Current coverage** | 0% (27 statements) |
| **Target coverage** | 90%+ |
| **Test file** | `tests/unit/test_core_align.py` |
| **Dependencies** | numpy, cv2 (OpenCV) |
| **Notes** | Contains `align_images()` and `AlignmentError`. Test with synthetic image arrays; verify alignment on known offset pairs and error raising on invalid input. |

**Key test cases:**
- Aligned identical images produce zero offset
- Known pixel-shifted images produce correct alignment
- Single-channel input raises `AlignmentError`
- Empty or mismatched array shapes raise appropriate errors

---

### `src/core/image_processing.py`

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure logic (numpy math, no Qt, no IO) |
| **Current coverage** | 0% (18 statements) |
| **Target coverage** | 95%+ |
| **Test file** | `tests/unit/test_core_image_processing.py` |
| **Dependencies** | numpy |
| **Notes** | Contains `apply_adjustments()` and `combine_channels()`. Pure array-in/array-out functions ideal for parametrized tests. |

**Key test cases:**
- Zero brightness/contrast returns unchanged image
- Positive/negative brightness shifts pixel values correctly
- Contrast scaling works at boundaries (all-black, all-white)
- `combine_channels()` produces correct RGB from three grayscale arrays
- Output is clipped to [0, 255] range

---

### `src/services/processor.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — Service/orchestration logic (no Qt, uses core modules) |
| **Current coverage** | 0% (84 statements) |
| **Target coverage** | 85%+ |
| **Test file** | `tests/unit/test_services_processor.py` |
| **Dependencies** | numpy, `src.core.align`, `src.core.image_processing` |
| **Notes** | Contains `ChannelAdjustments` dataclass and `ImageProcessorService` class. Test with real numpy arrays; mock alignment for deterministic results. |

**Key test cases:**
- `load_channel_from_array()` stores channel and triggers alignment
- `adjust_channel()` applies brightness/contrast via core functions
- `has_aligned_channels()` returns correct state
- `get_channel_preview()` returns processed single-channel image
- `get_combined_image()` with and without crop rect
- `ChannelAdjustments` dataclass defaults

---

### `src/ui/default_state.py`

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure logic (dataclasses, no Qt, no IO) |
| **Current coverage** | 0% (16 statements) |
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

### `src/ui/widgets/grid_types.py`

| Field | Value |
|-------|-------|
| **Priority** | 1 — Pure constants (no imports, no Qt, no IO) |
| **Current coverage** | 0% (12 statements) |
| **Target coverage** | 100% |
| **Test file** | `tests/unit/test_ui_grid_types.py` |
| **Dependencies** | None |
| **Notes** | Module defines 11 string constants. Test that all expected constants exist and have correct string values. |

**Key test cases:**
- All 11 grid type constants are defined and non-empty strings
- `GRID_TYPE_NONE` equals `"none"`
- No duplicate values among the constants

---

### `src/ui/app_state.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — Service logic (Qt only in TYPE_CHECKING, testable with mocks) |
| **Current coverage** | 0% (25 statements) |
| **Target coverage** | 90%+ |
| **Test file** | `tests/unit/test_ui_app_state.py` |
| **Dependencies** | `src.ui.default_state` (runtime); `PyQt5.QtCore.QRect` (TYPE_CHECKING only) |
| **Notes** | Dataclass with a `reset()` method. Qt imports are behind TYPE_CHECKING so module loads without Qt at runtime for attribute tests. Need to mock or skip `QRect` type for `crop_rect` field. |

**Key test cases:**
- Default construction matches `DefaultState` values
- `reset()` restores all fields to defaults after modification
- `channel_paths` is a mutable list of 3 `None` values by default

---

### `src/ui/handlers/channels.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — Orchestration logic (Qt only via TYPE_CHECKING for MainWindow) |
| **Current coverage** | 0% (51 statements) |
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

### `src/ui/handlers/keyboard.py`

| Field | Value |
|-------|-------|
| **Priority** | 3 — Helper function in UI layer (needs mock but no QApplication) |
| **Current coverage** | 0% (36 statements) |
| **Target coverage** | 75%+ |
| **Test file** | `tests/unit/test_handlers_keyboard.py` |
| **Dependencies** | `PyQt5.QtCore.Qt`, `PyQt5.QtGui.QKeyEvent` |
| **Notes** | Single `handle_key_press()` function dispatching key events. Can test with mocked key event objects and mock MainWindow. May need Qt constants imported. |

**Key test cases:**
- Keys 1, 2, 3 switch to respective channels
- Key A toggles combined view
- Unhandled keys are ignored gracefully

---

### `src/ui/handlers/display.py`

| Field | Value |
|-------|-------|
| **Priority** | 3 — Helper with Qt types (QRectF, QPixmap) |
| **Current coverage** | 0% (36 statements) |
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
