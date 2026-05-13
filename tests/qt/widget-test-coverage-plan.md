# Widget Test Coverage Plan

Supplement to the unit test coverage plan, covering Qt widget components.
All tests in this plan require `pytest-qt` and run in headless mode (`QT_QPA_PLATFORM=offscreen`).

---

## Folder Structure

```
tests/
├── unit/          # existing tests — no Qt, no QApplication required
├── qt/            # widget tests — require QApplication (offscreen)
│   ├── conftest.py
│   ├── test_widget_qt_utils.py                ✅ done
│   ├── test_widget_sliders.py                 ✅ done
│   ├── test_widget_status_bar.py              ✅ done
│   ├── test_widget_grid_settings_dialog.py    ✅ done
│   ├── test_widget_preset_panel.py            ✅ done
│   ├── test_widget_channel_controller.py      ✅ done
│   ├── test_widget_image_viewer.py
│   └── test_widget_grid_overlay.py            ✅ done
└── integration/   # future tests — main_window, smoke tests, cross-component flows
```

---

## Running Tests

```bash
# Unit tests only — no Qt needed (fast CI pipeline):
pytest tests/unit/

# Widget tests — requires Xvfb or offscreen platform:
QT_QPA_PLATFORM=offscreen pytest tests/qt/

# Full suite:
QT_QPA_PLATFORM=offscreen pytest tests/unit/ tests/qt/

# Single file:
QT_QPA_PLATFORM=offscreen pytest tests/qt/test_widget_status_bar.py
```

---

## Infrastructure Setup

### `tests/qt/conftest.py`

```python
import pytest
from PyQt5.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication for all widget tests."""
    app = QApplication.instance() or QApplication([])
    yield app
```

`pytest-qt` creates a `QApplication` automatically via the `qtbot` fixture, but an explicit
`conftest.py` documents the folder's infrastructure requirements and enables session-scoped setup.

### `pyproject.toml` / `pytest.ini`

```ini
[pytest]
markers =
    unit: No Qt required
    widget: Requires QApplication (offscreen)
    integration: Requires full Qt application
```

### CI — add installation step:

```bash
pip install pytest-qt
# Linux CI:
apt-get install -y xvfb libxkbcommon-x11-0 libgl1
export QT_QPA_PLATFORM=offscreen
```

---

## Widget Testing Philosophy

### What to test

- **Internal state** — widget initializes with correct default values
- **Validation logic** — value clamping, invalid input handling
- **Qt signals** — widget emits the correct signal on value change (`qtbot.waitSignal`)
- **Call flow** — widget delegates to service correctly (via mock)
- **Boundary behaviour** — min/max values, None input, empty state

### What **not** to test

- Pixel-level rendering (appearance, colours, on-screen positions)
- Animations and visual effects
- Actual `QPainter.drawLine()` output — test the input calculations, not the graphical output

### Test pattern

```python
def test_widget_name(qtbot):
    widget = WidgetName(...)
    qtbot.addWidget(widget)       # registers widget for cleanup after test
    # arrange / act / assert
    assert widget.some_value() == expected
```

---

## Coverage Summary — widget modules only

| Module | Stmts | Coverage | Target | Test file | Priority |
|--------|-------|----------|--------|-----------|----------|
| `src/ui/qt_utils.py` | 12 | ✅ 100% | 90%+ | `test_widget_qt_utils.py` | 1 — done |
| `src/ui/widgets/sliders.py` | 12 | ✅ 100% | 90%+ | `test_widget_sliders.py` | 1 — done |
| `src/ui/widgets/status_bar.py` | 27 | ✅ 100% | 80%+ | `test_widget_status_bar.py` | 1 — done |
| `src/ui/widgets/grid_settings_dialog.py` | 86 | ✅ 100% | 75%+ | `test_widget_grid_settings_dialog.py` | 2 — done |
| `src/ui/widgets/preset_panel.py` | 98 | ✅ 97% | 70%+ | `test_widget_preset_panel.py` | 2 — done |
| `src/ui/widgets/channel_controller.py` | 136 | ✅ 100% | 90%+ | `test_widget_channel_controller.py` | 2 — done |
| `src/ui/widgets/image_viewer.py` | 140 | 0% | 60%+ | `test_widget_image_viewer.py` | 3 — QGraphicsView, zoom, pan |
| `src/ui/widgets/grid_overlay.py` | 193 | ✅ 100% | 70%+ | `test_widget_grid_overlay.py` | 2 — done |

> **Note:** `crop_handler.py` and `main_window.py` are excluded from this plan.
> `crop_handler.py` requires prior refactoring (extracting geometry logic into `src/core/crop_geometry.py`),
> after which the pure geometry will move to `tests/unit/` and the Qt integration to `tests/integration/`.
> `main_window.py` is an integration test candidate only.

---

## Module Plan

---

### `src/ui/qt_utils.py`

| Field | Value |
|-------|-------|
| **Priority** | 1 — done |
| **Current coverage** | ✅ 100% (12 statements, 6 branches) |
| **Target coverage** | 90%+ |
| **Test file** | `tests/qt/test_widget_qt_utils.py` |
| **Dependencies** | `pytest-qt`, `numpy`, `PyQt5.QtGui.QImage` |
| **Notes** | Complete. Tests cover None input, grayscale/RGB format, dimensions, minimum sizes, boundary pixel values, and non-contiguous arrays (slice, transpose, F-order). Implementation handles non-contiguous input via `np.ascontiguousarray`. |

---

### `src/ui/widgets/sliders.py`

| Field | Value |
|-------|-------|
| **Priority** | 1 — done |
| **Current coverage** | ✅ 100% (12 statements, 2 branches) |
| **Target coverage** | 90%+ |
| **Test file** | `tests/qt/test_widget_sliders.py` |
| **Dependencies** | `pytest-qt`, `PyQt5.QtWidgets`, `PyQt5.QtCore.Qt` |
| **Notes** | Complete. Tests cover instantiation, orientation, setValue clamping at boundaries, doubleClicked signal via qtbot.mouseDClick, and mouseDoubleClickEvent(None) early-return path. |

---

### `src/ui/widgets/status_bar.py`

| Field | Value |
|-------|-------|
| **Priority** | 1 — done |
| **Current coverage** | ✅ 100% (27 statements, 6 branches) |
| **Target coverage** | 80%+ |
| **Test file** | `tests/qt/test_widget_status_bar.py` |
| **Dependencies** | `pytest-qt`, `PyQt5.QtWidgets.QStatusBar` |
| **Notes** | Complete. Tests cover initialization (size grip, mode label, initial message), set_message (text, empty string, timeout constant, long text), set_mode (parametrized across all modes), and all four branches of update_mode_from_state including saving-over-crop priority and loaded_channels boundary values (0, 2, 3). |

---

### `src/ui/widgets/grid_settings_dialog.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — done |
| **Current coverage** | ✅ 100% (86 statements, 14 branches) |
| **Target coverage** | 75%+ |
| **Test file** | `tests/qt/test_widget_grid_settings_dialog.py` |
| **Dependencies** | `pytest-qt`, `PyQt5.QtWidgets` |
| **Notes** | Complete. 28 tests across 3 classes (Init, LineWidth, GridType). Covers default and custom init values, button enable/disable states at MIN/MAX boundaries, decrease/increase no-op paths at limits, signal emission on width and grid-type changes, _get_grid_type_value out-of-bounds (positive and negative), and _on_grid_type_changed with row=-1. Private methods are called directly because the Popup-flagged QFrame requires a visible window for mouse-event routing in headless mode. |

---

### `src/ui/widgets/preset_panel.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — done |
| **Current coverage** | ✅ 97% (98 statements, 20 branches) |
| **Target coverage** | 70%+ |
| **Test file** | `tests/qt/test_widget_preset_panel.py` |
| **Dependencies** | `pytest-qt`, `PyQt5.QtWidgets`, `tmp_path` |
| **Notes** | Complete. 21 tests across 2 classes (PresetItem, PresetPanel). Covers thumbnail-missing ("No image") and thumbnail-exists branches, name/Unnamed fallback, mousePressEvent signal emission and payload, enterEvent/leaveEvent stylesheet changes with None and real QEvent, panel with nonexistent dir, empty dir, 1 and 2 preset files, non-.json skip, invalid-JSON skip, reload_presets idempotency (no duplication), save_requested and preset_selected signals. Two uncovered paths: super().mousePressEvent(event) (line 77) requires a visible widget for mouse routing; the item.widget() == None defensive check (line 145 branch) cannot be triggered via takeAt() in Qt's normal behaviour — both excluded from coverage targets by design. |

---

### `src/ui/widgets/channel_controller.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — done |
| **Current coverage** | ✅ 100% (136 statements, 30 branches) |
| **Target coverage** | 90%+ |
| **Test file** | `tests/qt/test_widget_channel_controller.py` |
| **Dependencies** | `pytest-qt`, `numpy`, `PyQt5.QtWidgets`, `PyQt5.QtCore.Qt` |
| **Notes** | Complete. 58 tests across 4 classes (Init, SliderTextSync, Reset, Preview, PreviewCrop). Covers default init values/slider ranges/channel abbreviations, slider→text sync, text→slider sync with full EP/BVA clamping table, non-numeric and empty text restore, signal emission on every change, single and bulk slider reset, doubleClicked reset path, invalid-name no-op path, defensive reset_all_sliders guard, clear_image, update_preview (None and array), _set_preview with standard/wide/tall aspect ratios, and all 5 branches of the parent-traversal crop path (no viewer, None rect, crop_mode=True, valid intersection, empty intersection). |

---

### `src/ui/widgets/image_viewer.py`

| Field | Value |
|-------|-------|
| **Priority** | 3 — QGraphicsView; test state, not rendering |
| **Current coverage** | 0% (140 statements) |
| **Target coverage** | 60%+ |
| **Test file** | `tests/qt/test_widget_image_viewer.py` |
| **Dependencies** | `pytest-qt`, `PyQt5.QtWidgets`, `PyQt5.QtGui.QPixmap` |
| **Notes** | Zoom and pan require a shown widget — use `qtbot.addWidget` + `widget.show()`. Test crop via mocked `CropHandler`. |

**Key test cases:**

- Widget initializes with default zoom=1.0, fit_to_view=False
- `set_image(pixmap)` — scene contains QGraphicsPixmapItem
- `clear_image()` — scene contains no pixmap
- `toggle_view()` — display mode changes
- Zoom via `wheelEvent` with Ctrl — `zoom` changes up/down
- `set_crop_mode(True)` delegates to `CropHandler.set_crop_mode` (mock)
- `get_saved_crop_rect()` returns None before being set
- `set_saved_crop_rect(rect)` / `get_saved_crop_rect()` round-trip

---

### `src/ui/widgets/grid_overlay.py`

| Field | Value |
|-------|-------|
| **Priority** | 2 — done |
| **Current coverage** | ✅ 100% (193 statements, 20 branches) |
| **Target coverage** | 70%+ |
| **Test file** | `tests/qt/test_widget_grid_overlay.py` |
| **Dependencies** | `pytest-qt`, `PyQt5.QtGui`, `unittest.mock` |
| **Notes** | Complete. 46 tests across 8 classes (Init, StateSetters, DrawGrid, 3x3Grid, GoldenRatioGrid, Diagonal1_1Grid, DiagonalRatioGrids, DiagonalCompositeGrids). Covers all default state values, all 11 grid type setter/getter round-trips, ValueError on invalid type, opacity clamping at 0/255/above/below, draw_grid disabled guard, zero-width/zero-height/negative-width early exit, painter save/restore, QRect→QRectF conversion, unknown-type fallback to 3×3, exact int-truncated positions for 3×3 and golden ratio lines, all 3 aspect-ratio branches of diagonal 1:1 (square/tall/wide), all 4 ratio wrappers (2:3, 3:2, 3:4, 4:3), zero-ratio guard in _draw_diagonal_ratio_grid, and all 4 composite diagonal methods (6 lines each). QPainter is mocked throughout — no real paint device required. |

---

## Modules Excluded from This Plan

| Module | Reason | Target location |
|--------|--------|-----------------|
| `src/ui/widgets/crop_handler.py` | Requires refactoring — geometry separation before tests | geometry → `tests/unit/`, Qt → `tests/integration/` |
| `src/ui/main_window.py` | System orchestrator — integration test by definition | `tests/integration/` |
| `src/main.py` | Qt entry point — smoke test only | `tests/integration/` |

---

## Implementation Order

1. ✅ **Infrastructure** — `pip install pytest-qt`, `conftest.py`, `widget` marker in `pytest.ini`, CI with `QT_QPA_PLATFORM=offscreen`
2. ✅ **`qt_utils.py`** — 100% coverage, 12 tests, non-contiguous array handling added to implementation
3. ✅ **`sliders.py`** — 100% coverage, 9 tests, both branches of mouseDoubleClickEvent covered
4. ✅ **`status_bar.py`** — 100% coverage, 20 tests, all four update_mode_from_state branches and BVA on loaded_channels threshold
5. ✅ **Dialogs and panels** — `grid_settings_dialog.py` (100%, 28 tests), `preset_panel.py` (97%, 21 tests)
6. ✅ **Central widget** — `channel_controller.py` (100%, 58 tests)
7. ✅ **Grid overlay** — `grid_overlay.py` (100%, 46 tests, all 11 grid types + mock QPainter math)
8. **Image viewer** — `image_viewer.py` (QGraphicsView, zoom, pan, crop delegation)
