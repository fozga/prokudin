# Widget Testing Guidelines

This document defines how to write widget tests and their documentation in this
project. Follow these guidelines every time you create or modify a test file
under `tests/qt/`.

Widget tests cover Qt components that require a running `QApplication`. They
follow the same documentation and design standards as unit tests in
`tests/unit/` but introduce additional rules for Qt infrastructure, signal
testing, and isolation.

---

## Project structure and naming

### Directory layout

All widget tests live under `tests/qt/`. The folder sits alongside
`tests/unit/` and shares the top-level `tests/` configuration files.

```
tests/
├── conftest.py                      # Shared pytest configuration and markers
├── coverage_config.py               # Coverage targets and thresholds
├── testing-guidelines.md            # Unit test guidelines
├── widget-testing-guidelines.md     # This document
├── unit/
│   └── ...
└── widget/
    ├── conftest.py                  # QApplication fixture (session-scoped)
    ├── test_widget_qt_utils.py
    ├── test_widget_sliders.py
    ├── test_widget_status_bar.py
    ├── test_widget_grid_settings_dialog.py
    ├── test_widget_preset_panel.py
    ├── test_widget_channel_controller.py
    ├── test_widget_image_viewer.py
    └── test_widget_grid_overlay.py
```

### File naming

Test files use the same convention as unit tests: mirror the module path
under `src/`, replace dots with underscores, add a `test_widget_` prefix:

| Source module | Test file |
|---|---|
| `src/ui/qt_utils.py` | `tests/qt/test_widget_qt_utils.py` |
| `src/ui/widgets/sliders.py` | `tests/qt/test_widget_sliders.py` |
| `src/ui/widgets/channel_controller.py` | `tests/qt/test_widget_channel_controller.py` |

### Class and function naming

Identical to unit test conventions:

- Test classes: `Test<DescriptiveName>` (e.g. `TestResetSlider`,
  `TestChannelControllerSync`).
- Test functions: `test_<what_is_being_tested>` in snake_case, describing
  scenario and expected outcome
  (e.g. `test_out_of_range_text_input_is_clamped_to_maximum`).
- All test functions must have a `-> None` return type annotation.

---

## Infrastructure

### `tests/qt/conftest.py`

Every widget test file depends on a live `QApplication`. The session-scoped
fixture in `tests/qt/conftest.py` creates exactly one instance for the
entire test session:

```python
import pytest
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Session-scoped QApplication required by all widget tests."""
    app = QApplication.instance() or QApplication([])
    yield app
```

`pytest-qt` also provides a `qtbot` fixture that creates `QApplication`
automatically. Both coexist. Use `qtbot` in every test function — it registers
widgets for cleanup and provides helpers for signal and event testing.

### Headless platform

Widget tests must run without a physical display. Set the environment variable
before running:

```bash
QT_QPA_PLATFORM=offscreen pytest tests/qt/
```

On Linux CI, install the required system packages:

```bash
apt-get install -y libxkbcommon-x11-0 libgl1
```

Do not rely on a real display in any test. If a test fails only on headless
environments, the test itself is the problem, not the environment.

### Running widget tests

```bash
# Widget tests only:
QT_QPA_PLATFORM=offscreen pytest tests/qt/

# Unit and widget tests together:
QT_QPA_PLATFORM=offscreen pytest tests/unit/ tests/qt/

# Single file:
QT_QPA_PLATFORM=offscreen pytest tests/qt/test_widget_status_bar.py

# With verbose coverage:
QT_QPA_PLATFORM=offscreen pytest tests/qt/ --cov=src/ui/widgets --cov-report=term-missing
```

### Dependencies

Add to `requirements-test.txt`:

```
pytest-qt>=4.4.0
```

No additional system-level Qt libraries are required beyond what the main
application already installs.

---

## Two levels of test documentation

Widget tests use the same two-level documentation system as unit tests: a
Test Design Specification (TDS) at the class level and a Test Case
Specification (TCS) as a GWT docstring on each test function. The content
of both is adapted for Qt-specific concerns.

### TDS – Test Design Specification

**Where it lives:** In the docstring of the test class.

**What it must contain (widget-specific additions in bold):**

- Name and path of the widget under test.
- Brief description of the widget's responsibility and public API contract.
- **Qt base class** (e.g. QGroupBox, QSlider, QStatusBar).
- **Infrastructure requirements**: which fixtures are needed (`qtbot`,
  session-scoped `qapp`, `tmp_path` for IO).
- **What is tested**: state changes, signal emission, validation logic,
  delegation to mocked dependencies.
- **What is NOT tested**: pixel rendering, visual appearance, animations,
  actual QPainter output.
- Equivalence partitions (EP) for input validation logic.
- Boundary values (BVA) for numeric parameters.
- **Mocking strategy**: which dependencies are replaced and how.
- Known constraints: headless-only, offscreen platform requirement, any
  widget that must be shown before certain properties are accessible.

**Template:**

```python
class TestSomeWidget:
    """
    Test Design Specification: SomeWidget
    Module under test: src/ui/widgets/some_widget.py

    Widget base class: QSomeBase

    Contract:
        Brief description of the widget's responsibility, its public
        methods, the signals it emits, and any validation it performs.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - File IO mocked via unittest.mock.patch (if applicable).

    What is tested:
        - Initialization with correct default values.
        - State changes via public setters.
        - Signal emission on value changes.
        - Input validation and clamping logic.
        - Delegation to dependencies (via mocks).

    What is NOT tested:
        - Visual appearance, colours, pixel positions.
        - QPainter output or rendered frame content.
        - Animations and transitions.

    Equivalence partitions:
        EP1  <description>  → <expected behaviour>
        EP2  <description>  → <expected behaviour>

    Boundary values:
        BV1  <parameter> = <value>  (<explanation>)
        BV2  <parameter> = <value>  (<explanation>)

    Mocking strategy:
        - <DependencyClass> replaced with MagicMock to isolate widget.
        - File IO patched at src.ui.widgets.some_widget.<function>.

    Constraints:
        - Widget must be added to qtbot before assertions on geometry.
    """
```

### TCS – Test Case Specification

Identical to unit test conventions. Use Given / When / Then in every test
function docstring. Map directly onto the Arrange / Act / Assert body.

```python
def test_out_of_range_text_input_is_clamped_to_maximum(self, qtbot: QtBot) -> None:
    """
    Given a slider with maximum value 100,
    When the user types 150 into the linked text field,
    Then the slider value is set to 100 and the text field shows "100".
    """
    # Arrange
    widget = ChannelController("red", Qt.red)
    qtbot.addWidget(widget)
    text_input = widget.text_inputs["brightness"]
    # Act
    text_input.setText("150")
    text_input.editingFinished.emit()
    # Assert
    assert widget.sliders["brightness"].value() == 100
    assert text_input.text() == "100"
```

---

## Test body structure – Arrange / Act / Assert (AAA)

Every test function body uses the same three-section structure as unit tests.
Widget tests have one additional rule: **register every widget with qtbot
in the Arrange section**, before any Act or Assert calls.

```python
def test_<name>(self, qtbot: QtBot) -> None:
    """Given ... When ... Then ..."""
    # Arrange
    widget = SomeWidget(...)
    qtbot.addWidget(widget)   # always first after instantiation
    ...
    # Act
    ...
    # Assert
    ...
```

Rules inherited from unit tests:

- One Act per test.
- One logical assertion per test.
- No logic in the Assert section.
- Move reusable Arrange code into `@pytest.fixture`.

Widget-specific rule:

- **Never call `widget.show()` unless the test explicitly requires a visible
  widget.** Some Qt properties (geometry, size hints) are only finalized after
  `show()`. Document in the TDS if `show()` is required.

---

## Signal testing

Use `qtbot.waitSignal` to assert that a signal is emitted. Never sleep or
poll manually.

```python
def test_value_changed_emitted_on_slider_move(self, qtbot: QtBot) -> None:
    """
    Given a ChannelController at its default state,
    When a slider value is changed programmatically,
    Then the value_changed signal is emitted exactly once.
    """
    # Arrange
    widget = ChannelController("red", Qt.red)
    qtbot.addWidget(widget)
    # Act + Assert  (waitSignal acts as both)
    with qtbot.waitSignal(widget.value_changed, timeout=1000):
        widget.sliders["brightness"].setValue(10)
```

Rules:

- Always set an explicit `timeout` (milliseconds). Use 1000 ms as the default.
  Increase only if the signal is known to be delayed.
- Use `qtbot.assertNotEmitted` to verify a signal is NOT emitted:
  ```python
  with qtbot.assertNotEmitted(widget.value_changed):
      widget.reset_all_sliders()   # if reset should suppress signals
  ```
- Do not test that a signal carries a specific value by inspecting Qt
  internals. Instead, inspect the widget state after the signal.

---

## Mouse and keyboard event simulation

Use `qtbot` helpers to simulate user interaction. Never construct raw
`QMouseEvent` or `QKeyEvent` objects manually.

```python
# Click a button
qtbot.mouseClick(widget.load_button, Qt.LeftButton)

# Double-click to trigger reset on ResetSlider
qtbot.mouseDClick(slider, Qt.LeftButton)

# Type into a text field
qtbot.keyClicks(text_input, "42")
qtbot.keyClick(text_input, Qt.Key_Return)
```

Rules:

- Call `widget.show()` before simulating mouse events that depend on widget
  geometry. Document this in the TDS under Constraints.
- Do not test that a specific cursor shape is set. Cursor behaviour is
  rendering-level and not observable in headless mode.

---

## Mocking Qt dependencies

Widget tests isolate the widget from its collaborators using
`unittest.mock.MagicMock`. The same patching rules as unit tests apply:
patch at the import location, not the definition site.

### Mocking a service dependency

```python
from unittest.mock import MagicMock, patch

def test_preview_updated_after_image_load(self, qtbot: QtBot) -> None:
    """
    Given a ChannelController with a mocked service,
    When update_preview is called with a valid image array,
    Then the preview label is updated without error.
    """
    # Arrange
    mock_svc = MagicMock()
    mock_svc.get_channel_preview.return_value = np.zeros((120, 160), dtype=np.uint8)
    widget = ChannelController("red", Qt.red)
    widget.svc = mock_svc
    qtbot.addWidget(widget)
    # Act
    widget.update_preview()
    # Assert
    mock_svc.get_channel_preview.assert_called_once()
```

### Mocking QPainter

To test that drawing methods issue the correct calls without rendering, pass
a `MagicMock` in place of `QPainter`:

```python
from unittest.mock import MagicMock, call

def test_3x3_grid_draws_four_lines(self, qtbot: QtBot) -> None:
    """
    Given a GridOverlay configured as 3x3 and a 300x300 bounding rect,
    When draw_grid is called,
    Then painter.drawLine is called exactly four times.
    """
    # Arrange
    overlay = GridOverlay()
    mock_painter = MagicMock()
    rect = QRectF(0, 0, 300, 300)
    # Act
    overlay.draw_grid(mock_painter, rect)
    # Assert
    assert mock_painter.drawLine.call_count == 4
```

Do not assert on pixel coordinates in QPainter calls unless testing a
specific mathematical property (e.g. confirming golden ratio positions).
Coordinate assertions must include a tolerance:

```python
args = mock_painter.drawLine.call_args_list[0][0]  # (x1, y1, x2, y2)
assert abs(args[0] - 114.6) < 1.0   # 300 * 0.382 ≈ 114.6
```

### Mocking file IO

Mock at the widget's module boundary, not at the stdlib level:

```python
with patch("src.ui.widgets.preset_panel.cv2.imread") as mock_imread:
    mock_imread.return_value = np.zeros((64, 64, 3), dtype=np.uint8)
    widget.load_thumbnail("fake/path.png")
```

---

## Isolation rules

Rules inherited from unit tests:

- Tests must not depend on external services or shared mutable state.
- Tests must not read from or write to the real filesystem unless using
  `tmp_path`.
- Each test must be independent and produce the same result in any order.

Widget-specific rules:

- **Never share a widget instance between tests.** Instantiate a fresh widget
  in every test function or fixture. Qt widget state is mutable and bleeds
  across tests if shared.
- **Never use `time.sleep()` to wait for Qt events.** Use `qtbot.waitSignal`,
  `qtbot.waitUntil`, or `qtbot.wait(ms)`.
- **Do not access `QApplication.instance()` directly in tests.** Let the
  session fixture and `qtbot` manage the application lifecycle.
- **Do not test `closeEvent` or `__del__` behaviour.** Widget destruction in
  headless mode is implementation-defined and unreliable.

---

## Test case design – EP and BVA

Use the same Equivalence Partitioning and Boundary Value Analysis approach
as unit tests. For widget tests, the input domain includes not only numeric
parameters but also Qt-specific inputs: empty vs. non-empty text fields,
None vs. valid pixmaps, enabled vs. disabled widget state.

Example partition table for a text input that syncs to a slider:

| Partition | Representative | Expected behaviour |
|---|---|---|
| EP1: empty string | `""` | restores previous slider value |
| EP2: non-numeric string | `"abc"` | restores previous slider value |
| EP3: value within range | `"50"` | slider set to 50 |
| EP4: value below minimum | `"-999"` | slider clamped to minimum |
| EP5: value above maximum | `"999"` | slider clamped to maximum |
| EP6: value equal to minimum | `str(min_val)` | slider set to minimum, no clamping |
| EP7: value equal to maximum | `str(max_val)` | slider set to maximum, no clamping |

---

## Parametrized tests

Same rules as unit tests. Use `@pytest.mark.parametrize` when one test
function covers multiple partitions or boundary values by varying inputs.
Every parameter set must have a readable `id` and an inline comment.

```python
@pytest.mark.parametrize("text, expected_value", [
    ("50",   50),   # EP3: valid value within range
    ("-999",  -100), # EP4: below minimum, clamped
    ("999",   100),  # EP5: above maximum, clamped
    ("-100", -100),  # EP6: equal to minimum
    ("100",   100),  # EP7: equal to maximum
], ids=["valid", "below_min", "above_max", "at_min", "at_max"])
def test_text_input_sets_slider_value(
    self, qtbot: QtBot, text: str, expected_value: int
) -> None:
    """
    Given a ChannelController with slider range [-100, 100],
    When the user enters a value in the text field,
    Then the slider is set to the expected value, clamped to the valid range.
    """
    # Arrange
    widget = ChannelController("red", Qt.red)
    qtbot.addWidget(widget)
    text_input = widget.text_inputs["brightness"]
    # Act
    text_input.setText(text)
    text_input.editingFinished.emit()
    # Assert
    assert widget.sliders["brightness"].value() == expected_value
```

---

## Handling discovered bugs

Identical procedure to unit tests:

1. Write the test against the correct behaviour, not the current broken one.
2. Mark with `@pytest.mark.xfail(reason="...")` describing the bug.
3. Create a GitHub issue and reference it in the reason string.
4. Add a Known Issues note to the TDS.

---

## MainWindow test structure

`MainWindow` is exercised at three levels. The widget and integration
levels live under `tests/qt/` and `tests/integration/` respectively and
share fixtures with the unit-level scaffold in `tests/unit/`.

| Level | Fixture | File | Use when |
|---|---|---|---|
| Widget | `window` | `tests/qt/test_widget_main_window.py` | Real `MainWindow` with `ImageProcessorService`, autosave entry points, save dialog, and keyboard dispatcher patched at the `src.ui.main_window` import boundary. Use for UI wiring tests (button enablement, signal routing) where you need a live widget but not real services. |
| Integration | `real_window` | `tests/integration/test_main_window_integration.py` (fixture in `tests/integration/conftest.py`) | Fully real `MainWindow` with only `restore_autosave` suppressed. Module-scoped — do not mutate state across tests in the same module. Use for end-to-end flows. |

Cross-reference: unit-level fixture `mw` lives in
`tests/unit/test_ui_main_window.py` and provides a
`MagicMock(spec=MainWindow)` for delegation/business-logic tests that run
without a `QApplication`.

---

## Coverage requirements and tooling

### Code coverage

Every widget module listed in `tests/coverage_config.py` must maintain its
configured branch coverage threshold. Widget modules use lower default targets
than pure-logic modules because rendering paths are excluded by design:

| Module category | Default target |
|---|---|
| Pure logic (`src/core/`) | 90%+ |
| Handlers (`src/ui/handlers/`) | 85%+ |
| Widgets (`src/ui/widgets/`) | 70%+ |
| Simple wrappers (status bar, sliders) | 80%+ |

Coverage is measured per-module. Rendering code paths that require an active
paint device may be excluded with `# pragma: no cover` only when the
exclusion is documented in the TDS under Exclusions.

### Documentation coverage

Same requirement as unit tests: 100% docstring coverage enforced by
`interrogate`. Every public class and method in a test file must have a
docstring.

### Formatting and type checking

Same tools and configuration as unit tests:

| Tool | Requirement |
|---|---|
| **black** | Line length 120, target Python 3.10 |
| **isort** | Profile "black", line length 120 |
| **mypy** | Strict — `disallow_untyped_defs`, `warn_return_any` |

Type-annotate `qtbot` parameters using `pytest_qt.plugin.QtBot`:

```python
from pytestqt.plugin import QtBot

def test_example(self, qtbot: QtBot) -> None:
    ...
```

---

## Quick reference checklist

Before committing a widget test file, verify:

- [ ] Test file is named `test_widget_<module_path>.py` and placed in
      `tests/qt/`.
- [ ] `tests/qt/conftest.py` exists with a session-scoped `qapp` fixture.
- [ ] `QT_QPA_PLATFORM=offscreen` is set in the CI environment.
- [ ] The test class has a TDS docstring (widget base class, infrastructure,
      what is tested, what is NOT tested, EP list, BV list, mocking strategy,
      constraints).
- [ ] Every test function has a GWT docstring.
- [ ] Every test function body has `# Arrange`, `# Act`, `# Assert` comments.
- [ ] Every test function has a `-> None` return type annotation.
- [ ] `qtbot` is type-annotated as `QtBot` in every test function signature.
- [ ] Every widget is registered with `qtbot.addWidget(widget)` immediately
      after instantiation in the Arrange section.
- [ ] No widget instance is shared between test functions.
- [ ] Signals are tested with `qtbot.waitSignal` or `qtbot.assertNotEmitted`,
      never with `time.sleep`.
- [ ] Mouse and keyboard events use `qtbot.mouseClick`, `qtbot.keyClicks`,
      etc., never raw event constructors.
- [ ] Service and IO dependencies are replaced with `MagicMock`.
- [ ] QPainter is mocked when testing drawing logic; pixel coordinates are
      verified with a numeric tolerance.
- [ ] Each row in a parametrized test has an inline comment identifying the
      EP or BV it covers, and a readable `id`.
- [ ] Discovered bugs are marked `@pytest.mark.xfail` with a descriptive
      reason, not hidden by adjusted assertions.
- [ ] `# pragma: no cover` is used only for rendering paths and is documented
      in the TDS under Exclusions.
- [ ] All tests pass (or are legitimately `xfail`) in isolation and in any order.
