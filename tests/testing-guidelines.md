# Testing Guidelines

This document defines how to write unit tests and their documentation in this
project. Follow these guidelines every time you create or modify a test file.

---

## Project structure and naming

### Directory layout

All unit tests live under `tests/unit/`. The test runner and configuration
files live one level up in `tests/`.

```
tests/
├── conftest.py            # Shared pytest configuration and markers
├── coverage_config.py     # Coverage targets and thresholds
├── testing-guidelines.md  # This document
└── unit/
    ├── test_core_align.py
    ├── test_core_image_processing.py
    ├── test_handlers_channels.py
    └── ...
```

### File naming

Test files mirror the module path under `src/`, with dots replaced by
underscores and a `test_` prefix:

| Source module | Test file |
|---|---|
| `src/core/align.py` | `tests/unit/test_core_align.py` |
| `src/ui/handlers/channels.py` | `tests/unit/test_handlers_channels.py` |
| `src/services/processor.py` | `tests/unit/test_services_processor.py` |

### Class and function naming

- Test classes: `Test<DescriptiveName>` (e.g. `TestApplyAdjustments`,
  `TestAlignImages`).
- Test functions: `test_<what_is_being_tested>` using snake_case. The name
  should describe the scenario and expected outcome
  (e.g. `test_zero_brightness_returns_identical_image`).
- All test functions must have a `-> None` return type annotation.

---

## Two levels of test documentation

Every test module must contain two kinds of documentation, placed at different
granularities.

### TDS – Test Design Specification

**What it is:** A description of *why* and *how* a module is tested. It captures
design decisions, scope, exclusions, and the testing strategy for the module as
a whole.

**Where it lives:** In the docstring of the test class (preferred) or, if the
test file has no classes, in the module-level docstring.

**What it must contain:**
- Name and path of the module under test.
- Brief description of the function or class under test and its contract
  (what it does, what it returns, what it raises).
- The mathematical formula or algorithm, if applicable.
- Equivalence partitions (EP) used to design test cases.
- Boundary values (BVA) identified from the specification.
- Explicit exclusions: what is NOT tested and why.
- Known constraints: mocking requirements, filesystem access, external services,
  platform-specific behaviour, etc.

**Template:**

```python
class TestSomeFunction:
    """
    Test Design Specification: some_function()
    Module under test: src/module/path.py

    Contract:
        Brief description of what the function does, its inputs, outputs,
        and any side effects or exceptions it may raise.
        If the function implements a formula, state it here:
        output = clip(input * (1 + contrast / 100) + brightness, 0, 255)

    Equivalence partitions:
        EP1  <description of partition>  → <expected behaviour>
        EP2  <description of partition>  → <expected behaviour>
        EP3  <description of partition>  → <expected behaviour>

    Boundary values:
        BV1  <parameter> = <value>  (<explanation>)
        BV2  <parameter> = <value>  (<explanation>)

    Exclusions:
        - <what is not tested and why>
        - <what is not tested and why>

    Constraints:
        - <any setup requirements, mocking needs, platform restrictions>
    """
```

---

### TCS – Test Case Specification

**What it is:** A description of one specific test case: the exact inputs,
the action taken, and the expected output. Every test function must have a TCS
in its docstring.

**Where it lives:** In the docstring of each individual test function or method.

**Format:** Use **Given / When / Then** (GWT). This maps directly onto the AAA
body of the test and makes the contract explicit:

```
Given  <the initial state or input>
When   <the action or function call>
Then   <the expected observable outcome>
```

**Template:**

```python
def test_<descriptive_name>(self):
    """
    Given <the initial state or input>,
    When <the action performed>,
    Then <the expected outcome>.
    """
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

Short tests may collapse all three clauses onto one line if it remains readable:

```python
def test_returns_none_for_empty_input(self):
    """Given an empty input, when processed, then the result is None."""
```

Do NOT use vague docstrings such as:
- `"Test brightness"` – missing Given and Then
- `"Should work"` – meaningless
- `"Tests that function returns correct value"` – no specifics

---

## Test body structure – Arrange / Act / Assert (AAA)

Every test function body must be divided into exactly three labelled sections
using inline comments.

```python
def test_<name>(self):
    """Given ... When ... Then ..."""
    # Arrange  ← set up inputs, fixtures, mocks
    ...
    # Act      ← call the single function or method under test
    ...
    # Assert   ← verify the outcome
    ...
```

Rules:
- **One Act per test.** Call exactly one function or method in the Act section.
- **One logical assertion per test.** Multiple `assert` statements are acceptable
  only when they all describe the same single observable fact (e.g. shape AND
  dtype of the same output).
- **Never put logic in the Assert section.** No loops, no conditionals.
- **Move reusable Arrange code into `@pytest.fixture`.**

---

## Test case design – Equivalence Partitioning (EP) + Boundary Value Analysis (BVA)

Before writing any test function, identify the equivalence partitions and
boundary values for the function under test. Record them in the TDS class
docstring. Then write exactly one representative test per partition and one
test per boundary value. Do not write multiple tests for the same partition.

### Equivalence Partitioning (EP)

Divide the input domain into classes where the function behaves identically
for all values in the class. Test one representative value per class.

Example for a numeric parameter with a valid range and a guard clause:

| Partition | Representative | Expected behaviour |
|---|---|---|
| EP1: null / None input | `None` | returns None, no exception |
| EP2: zero / neutral | `0` | identity, no change |
| EP3: positive range | `50` | expected positive effect |
| EP4: negative range | `-50` | expected negative effect |
| EP5: positive overflow | `value + delta > max` | clipped to max |
| EP6: negative overflow | `value + delta < min` | clipped to min |

### Boundary Value Analysis (BVA)

Test values at the edges of valid ranges and at the output clipping boundaries.
Typical BVA points: `min`, `min+1`, typical, `max-1`, `max`.

Example for an output clipped to `[0, 255]`:

| Boundary | Value | Reason |
|---|---|---|
| Lower clip | `0` | output must not go below 0 |
| Upper clip | `255` | output must not exceed 255 |
| Just below upper | `254` | no clipping should occur here |

---

## Parametrized tests – Specification by Example (SBE)

When one test function can cover multiple equivalence partitions or boundary
values by varying inputs, use `@pytest.mark.parametrize`. The parameter table
**is** the specification – it must be readable as a table of examples.

Rules:
- Give every parameter set a readable `id` string.
- Include an inline comment on each row explaining which EP or BV it covers.
- The test docstring still uses GWT format but may refer to parameters
  generically.

```python
@pytest.mark.parametrize("input_val, param, expected", [
    (100,   0, 100),  # EP2: neutral – identity
    (100,  50, 150),  # EP3: positive range
    (100, -50,  50),  # EP4: negative range
    (200, 100, 255),  # BV1: upper clip boundary
    ( 30,-100,   0),  # BV2: lower clip boundary
], ids=["identity", "positive", "negative", "upper_clip", "lower_clip"])
def test_parameter_effect(self, input_val, param, expected):
    """
    Given an input value and an adjustment parameter,
    When the function is applied,
    Then the output equals the expected value, clipped to the valid range.
    """
    # Arrange
    data = prepare_input(input_val)
    # Act
    result = function_under_test(data, param)
    # Assert
    assert result == expected
```

---

## Handling discovered bugs

If, while writing a test, you discover that the existing implementation
contains a bug or incorrect behaviour:

1. **Write the test to verify the correct behaviour, not the current broken
   behaviour.** Base the assertion on the documented contract (docstring, type
   hints, specification) — not on what the code currently produces.

2. **Do NOT adjust the assertion to make the test pass against broken code.**
   A passing test that validates wrong behaviour is worse than no test at all —
   it creates false confidence and hides real defects.

3. **Mark the test with `@pytest.mark.xfail` and describe the bug** in the
   `reason` string:

   ```python
   @pytest.mark.xfail(
       reason="Bug: output is clipped before the offset is added, "
              "should be clipped after. Needs fix in function_under_test()."
   )
   def test_correct_operation_order(self):
       """
       Given input=200 and offset=10,
       When function_under_test is called,
       Then output equals 210 (clipping happens after addition).
       """
       # Arrange
       data = prepare_input(200)
       # Act
       result = function_under_test(data, offset=10)
       # Assert
       assert result == 210
   ```

   This keeps CI green while making the defect explicit and trackable.

4. **Create a bug report / GitHub issue** for the defect and reference its
   number in the `reason` string once it exists.

5. **Add a note in the TDS** (class docstring) under a "Known Issues" section
   referencing the bug.

---

## Isolation rules

- Tests must not depend on external services, network calls, or shared
  mutable state.
- Tests must not read from or write to the real filesystem unless using
  the `tmp_path` pytest fixture.
- Use `unittest.mock.patch` or `pytest-mock`'s `mocker` fixture to replace
  external dependencies (databases, file I/O, heavy computations, third-party
  APIs).
- Each test must be independently runnable in any order.

### Module-level import mocking

Some modules import heavy or unavailable dependencies at the top of the file
(e.g. Qt, GPU libraries, optional C extensions). Do NOT mock these by mutating
`sys.modules` directly at module level:

```python
# ❌ BAD – permanently pollutes sys.modules for the entire process
sys.modules["PyQt5"] = MagicMock()
sys.modules["rawpy"] = MagicMock()
```

This pattern breaks test isolation: other test files running in the same
process will see the mocked modules, potentially causing silent failures or
false negatives that are order-dependent and hard to diagnose.

**Preferred approach A – `patch` the specific import path inside the test:**

```python
# ✅ GOOD – patch is applied and reversed within the test scope only
@patch("src.ui.handlers.image_loading.rawpy")
def test_something(self, mock_rawpy):
    mock_rawpy.imread.return_value = ...
    ...
```

**Preferred approach B – declare in `conftest.py` as a scoped fixture:**

```python
# conftest.py – applies before the affected tests, cleanly removed after
@pytest.fixture(autouse=True, scope="session")
def mock_pyqt5():
    with patch.dict("sys.modules", {
        "PyQt5": MagicMock(),
        "PyQt5.QtWidgets": MagicMock(),
    }):
        yield
```

This keeps the mock scoped and reversible regardless of test execution order.
The `conftest.py` approach is preferred when an unavailable dependency affects
an entire test subpackage (e.g. all tests under `tests/unit/ui/`).

## Fixtures

### When to use fixtures

Extract Arrange code into a `@pytest.fixture` when:
- Two or more tests in the same class share identical setup.
- The setup involves more than two lines of non-trivial construction.

Do NOT create a fixture for a one-liner that is clearer inline.

### Where to place fixtures

| Scope | Location |
|---|---|
| Used by one test file | Inside that test file, above the test class |
| Used by multiple test files | `tests/conftest.py` |

### Fixture scope

All fixtures use the default `function` scope (recreated for every test)
unless there is a measured performance reason to share them. Shared mutable
fixtures (e.g. `session`-scoped numpy arrays) lead to test-order dependencies —
avoid them.

### Naming

Name fixtures after what they **are**, not what they **do**:

```python
# Good
@pytest.fixture
def gray_mid() -> np.ndarray:
    """128-value grayscale image — mid-range."""
    return np.full((4, 4), 128, dtype=np.uint8)

# Bad — reads as an action, not a value
@pytest.fixture
def create_gray_image():
    ...
```

### Type hints

Always type-hint the return value of a fixture and the fixture parameter in
tests:

```python
@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

def test_something(self, sample_rgb_image: np.ndarray) -> None:
    ...
```

---

## NumPy array assertions

Standard `assert ==` does not work for numpy arrays. Use the helpers from
`np.testing`:

| Assertion | Use when |
|---|---|
| `np.testing.assert_array_equal(a, b)` | Exact integer equality (uint8 images) |
| `np.testing.assert_allclose(a, b, atol=1e-6)` | Floating-point with tolerance |
| `assert result.shape == (H, W, 3)` | Checking shape only |
| `assert result.dtype == np.uint8` | Checking dtype only |

Example — verifying pixel values after an adjustment:

```python
result = apply_adjustments(gray_mid, brightness=10, contrast=0)
np.testing.assert_array_equal(result, np.full((4, 4), 138, dtype=np.uint8))
```

When a single test checks both shape and content, that counts as one logical
assertion (the AAA rule is not violated):

```python
assert result.shape == (4, 4)
np.testing.assert_array_equal(result, expected)
```

---

## Exception testing

Use `pytest.raises` to verify that a function raises the expected exception
for invalid-input partitions identified in the TDS:

```python
def test_fewer_than_three_channels_raises(self):
    """
    Given a list with only two channels,
    When combine_channels is called,
    Then an IndexError is raised.
    """
    # Act / Assert
    with pytest.raises(IndexError):
        combine_channels([gray_mid, gray_mid], [100, 100, 100])
```

Rules:
- The `with pytest.raises(...)` block replaces the Act and Assert sections.
  Label it `# Act / Assert`.
- To accept multiple exception types, pass a tuple:
  `pytest.raises((IndexError, ValueError))`.
- If the exception message matters, use `match`:
  `pytest.raises(ValueError, match="must be positive")`.
- Do NOT catch overly broad exceptions like `Exception` unless the contract
  explicitly says "raises Exception".

---

## Complete example

The following is a complete, correctly structured test class. Use it as a
reference when writing new test files.

```python
"""Unit tests for src/module/converter.py."""

import pytest

from src.module.converter import convert


class TestConvert:
    """
    Test Design Specification: convert()
    Module under test: src/module/converter.py

    Contract:
        Converts a numeric input value using a scale factor and an offset.
        Returns None if the input is None.
        Clips the result to the range [0, 100].
        Formula: output = clip(input * scale + offset, 0, 100)

    Equivalence partitions:
        EP1  None input       → returns None (guard clause)
        EP2  scale=1, offset=0 → identity, output equals input
        EP3  scale > 1        → output larger than input
        EP4  scale < 1        → output smaller than input
        EP5  result > 100     → clipped to 100
        EP6  result < 0       → clipped to 0

    Boundary values:
        BV1  output = 100 (upper clip boundary)
        BV2  output = 0   (lower clip boundary)

    Exclusions:
        - Non-numeric string input (caller is responsible for type validation)
        - Scale = 0 (division-by-zero scenarios handled at call site)

    Constraints:
        - No external dependencies; pure arithmetic only.
    """

    def test_none_input_returns_none(self):
        """
        Given the input value is None,
        When convert is called,
        Then the return value is None.
        """
        # Arrange  (nothing to prepare)
        # Act
        result = convert(None, scale=2, offset=0)
        # Assert
        assert result is None

    def test_identity_with_neutral_parameters(self):
        """
        Given input=50, scale=1, offset=0,
        When convert is called,
        Then the output equals 50 (identity transformation).
        """
        # Arrange
        value = 50
        # Act
        result = convert(value, scale=1, offset=0)
        # Assert
        assert result == 50

    @pytest.mark.parametrize("value, scale, offset, expected", [
        (50,   1,   0,  50),  # EP2: identity
        (30,   2,   0,  60),  # EP3: scale > 1
        (60, 0.5,   0,  30),  # EP4: scale < 1
        (60,   2,   0, 100),  # BV1: upper clip
        (10,   1, -20,   0),  # BV2: lower clip
    ], ids=["identity", "scale_up", "scale_down", "upper_clip", "lower_clip"])
    def test_conversion_cases(self, value, scale, offset, expected):
        """
        Given a numeric input, scale, and offset,
        When convert is called,
        Then the output equals the expected value clipped to [0, 100].
        """
        # Arrange  (inline – inputs are simple scalars)
        # Act
        result = convert(value, scale=scale, offset=offset)
        # Assert
        assert result == expected
```

---

## Running tests

Use `run_tests.py` to execute the full test suite with coverage enforcement
and documentation checks:

```bash
python3 run_tests.py                              # Summary output
python3 run_tests.py -v                           # Detailed coverage report
python3 run_tests.py -m core.align                # Single module
python3 run_tests.py -m handlers.channels -v      # Module with verbose
python3 run_tests.py --pytest-only                # Pytest only, no checks
python3 run_tests.py --pytest-only -k "test_align"  # With pytest filter
```

`run_tests.py` automatically:
- Creates and manages the `.venv-test` virtual environment.
- Installs dependencies from `requirements-test.txt`.
- Runs pytest with per-module coverage.
- Runs interrogate to check test docstring coverage.
- Reports pass/fail against the configured thresholds.

For quick iteration during development, use `--pytest-only` to skip coverage
and documentation checks.

---

## MainWindow test structure

`MainWindow` is exercised at three levels, each with its own shared fixture.
Choose the lowest level that lets you exercise the behaviour under test.

| Level | Fixture | File | Use when |
|---|---|---|---|
| Unit | `mw` | `tests/unit/test_ui_main_window.py` | Testing a single `MainWindow` method against a `MagicMock(spec=MainWindow)`. No `QApplication`. Call the real method via `MainWindow.<method>(mw, ...)`. |
| Widget | `window` | `tests/qt/test_widget_main_window.py` | Testing UI wiring on a real `MainWindow` with heavy collaborators (services, autosave, dialogs) patched out. |
| Integration | `real_window` | `tests/integration/test_main_window_integration.py` | End-to-end flows with a fully real `MainWindow`; only autosave restore is suppressed. |

See `tests/qt/qt-testing-guidelines.md` for the widget and integration
fixtures (Qt infrastructure, mocking strategy, lifecycle).

---

## Coverage requirements and tooling

### Code coverage

Every module listed in `tests/coverage_config.py` must maintain **≥ 90 %
branch coverage**. Coverage is measured per-module, not as a project-wide
aggregate.

Modules that do not yet meet this threshold are listed in `EXCLUDED_MODULES`
inside `coverage_config.py`. As you add tests and reach 90 %, remove the
module from the exclusion list so it becomes enforced.

### Documentation coverage

All test files must have **100 % docstring coverage**, enforced by
[interrogate](https://interrogate.readthedocs.io/). Every public class,
method, and function in a test file must have a docstring (TDS for classes,
GWT for test functions).

### Formatting and type checking

| Tool | Requirement |
|---|---|
| **black** | Line length 120, target Python 3.10 |
| **isort** | Profile "black", line length 120 |
| **mypy** | Strict — `disallow_untyped_defs`, `warn_return_any` |

All test functions must have type annotations (return `-> None` for tests).

### Dependencies

Test dependencies are listed in `requirements-test.txt`:
- `pytest 8.3.0` — test runner
- `pytest-cov 6.0.0` — coverage plugin
- `interrogate 1.5.0` — docstring coverage
- `coverage[toml] 7.5.0` — coverage engine

---

## Quick reference checklist

Before committing a test file, verify:

- [ ] Test file is named `test_<module_path>.py` and placed in `tests/unit/`.
- [ ] PyQt5 is mocked in `sys.modules` before any project imports (if the
      module under test depends on Qt).
- [ ] The test class has a TDS docstring (module under test, contract, EP list,
      BV list, exclusions, constraints).
- [ ] Every test function has a GWT docstring.
- [ ] Every test function body has `# Arrange`, `# Act`, `# Assert` comments.
- [ ] Every test function has a `-> None` return type annotation.
- [ ] Each row in a parametrized test has an inline comment identifying which
      EP or BV it covers, and a readable `id`.
- [ ] Patches target the import location, not the definition site.
- [ ] Fixtures are type-hinted and named after what they are.
- [ ] NumPy arrays are compared with `np.testing` helpers, not `assert ==`.
- [ ] Exception paths use `pytest.raises`, not try/except in tests.
- [ ] Discovered bugs are marked `@pytest.mark.xfail` with a descriptive reason,
      not silently hidden by adjusted assertions.
- [ ] All tests pass (or are legitimately `xfail`) in isolation and in any order.
- [ ] `run_tests.py` passes (coverage ≥ 90 %, interrogate = 100 %).
