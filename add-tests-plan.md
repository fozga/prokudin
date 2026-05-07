# Scaffolding Plan: Local & CI Unit Testing with Coverage (0% initial)

This plan adds a minimal Python testing and coverage setup to the project, both locally and in CI, **without actually testing any production code yet**. The initial coverage will be effectively **0%** for the main codebase, by design. The goal is to:

- establish a standard test/coverage toolchain (pytest + pytest-cov + coverage.py),[web:43][web:62]
- add a CI workflow that runs tests with coverage,
- create a **test scaffolding** (directories and empty / placeholder test files) that we can gradually fill in later.

---

## Assumptions

- The project is a Python project with source code under `src/` (or a similar directory).
- We are okay with:
  - adding new dev dependencies,
  - adding a new test directory structure under `tests/`,
  - adding a new GitHub Actions workflow in `.github/workflows/`.

If any of these assumptions are wrong, adjust paths/names accordingly.

---

## Step 1 – Add local test & coverage dependencies

**Goal:** Make it possible to run `pytest` with coverage locally.

1. Add the following tools to the development dependencies (e.g. in `requirements-dev.txt` or equivalent):

   - `pytest` – test runner.
   - `pytest-cov` – coverage plugin for pytest.[web:43]
   - `coverage[toml]` – coverage.py engine (used under the hood by pytest-cov).[web:62]

2. Keep versions pinned in a style consistent with the rest of the file, for example:

   ```txt
   # Test tools
   pytest==8.3.0
   pytest-cov==6.0.0
   coverage[toml]==7.5.0
   ```

3. Do **not** change existing dependency versions unless necessary.

---

## Step 2 – Basic pytest configuration (optional but recommended)

**Goal:** Standardize how pytest discovers tests.

1. (Optional) Create a `pytest.ini` or `pyproject.toml`/`setup.cfg` section with basic configuration:

   ```ini
   # pytest.ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   ```

2. This step is not strictly required but makes test discovery more predictable.

---

## Step 3 – Coverage configuration

**Goal:** Configure coverage to measure the main source tree and allow 0% coverage initially.

1. Add a coverage configuration file if it does not exist yet. Prefer one of:

   - `setup.cfg` with `[coverage:run]` and `[coverage:report]` sections, or
   - a standalone `.coveragerc`.

2. Example `setup.cfg` coverage config:

   ```ini
   [coverage:run]
   branch = True
   source = src
   omit =
       */tests/*
       */__init__.py

   [coverage:report]
   show_missing = True
   # Do NOT set fail_under yet – we intentionally start with 0% coverage.
   # fail_under = 0

   [coverage:html]
   directory = htmlcov
   title = Project – Coverage Report
   ```

3. Make sure **no coverage thresholds** (`fail_under`) are enforced yet. We want CI to pass even when coverage is 0%.

---

## Step 4 – Local test command with coverage

**Goal:** Define a standard way to run tests with coverage locally.

1. Decide on a canonical local command, e.g.:

   ```bash
   pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=html:htmlcov
   ```

   - `--cov=src` – measure coverage for the `src` package.[web:62]
   - `--cov-branch` – enable branch coverage.
   - `--cov-report=term-missing` – show missing lines in the terminal.
   - `--cov-report=html:htmlcov` – generate an HTML report in the `htmlcov` directory.

2. Optionally, add a small helper:

   - A `make test` / `make coverage` target, or
   - A simple script `run_tests.py` that just calls pytest with the options above.

3. Do not run any tests against production code yet; the scaffolding in Step 5 will ensure coverage is effectively 0%.

---

## Step 5 – Test scaffolding with 0% coverage

**Goal:** Create the test directory structure and placeholder files so that:

- `pytest` runs successfully,
- coverage is collected,
- but **no production code is executed by tests**, so coverage remains 0%.

1. Create the following folder structure (paths can be adjusted if the project uses a different layout):

   ```text
   tests/
     __init__.py
     unit/
       __init__.py
       test_core_placeholder.py
       test_services_placeholder.py
       test_ui_placeholder.py
   ```

2. Each placeholder test file should contain at least one **no-op or skipped** test that does **not import any code from `src/`**. For example:

   ```python
   # tests/unit/test_core_placeholder.py
   import pytest

   @pytest.mark.skip(reason="Placeholder test file – real unit tests will be added later.")
   def test_placeholder_core():
       assert True
   ```

   ```python
   # tests/unit/test_services_placeholder.py
   import pytest

   @pytest.mark.skip(reason="Placeholder test file – real unit tests will be added later.")
   def test_placeholder_services():
       assert True
   ```

   ```python
   # tests/unit/test_ui_placeholder.py
   import pytest

   @pytest.mark.skip(reason="Placeholder test file – real unit tests will be added later.")
   def test_placeholder_ui():
       assert True
   ```

3. Key points:

   - Using `@pytest.mark.skip` ensures tests are discovered but not executed.
   - The tests do **not** import any production code (e.g. nothing from `src.*`).
   - When running `pytest --cov=src`, coverage will include all measured modules under `src`, but no lines will be executed, so coverage will be 0% (or very close to 0%, depending on how the source tree is interpreted).[web:47]

---

## Step 6 – GitHub Actions workflow for tests + coverage

**Goal:** Add a CI job that runs pytest with coverage and publishes the report, even if coverage is 0%.

1. Create a new workflow file, e.g. `.github/workflows/tests.yml`.

2. Recommended triggers:

   ```yaml
   on:
     push:
       branches:
         - main
         - feature/*
     pull_request:
       branches:
         - main
   ```

3. Add a single job that:

   - Checks out the code.
   - Sets up Python.
   - Installs dependencies (runtime + dev, including pytest and pytest-cov).
   - Runs pytest with coverage options as defined in Step 4.
   - Uploads the HTML coverage report as an artifact.

   Example skeleton:

   ```yaml
   name: Tests with Coverage

   on:
     push:
       branches:
         - main
         - feature/*
     pull_request:
       branches:
         - main

   jobs:
     tests:
       runs-on: ubuntu-latest

       steps:
         - name: Checkout
           uses: actions/checkout@v4

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.x'

         - name: Install dependencies
           run: |
             pip install -r requirements.txt || true
             if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

         - name: Run pytest with coverage
           run: |
             pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=html:htmlcov

         - name: Upload coverage HTML report
           if: always()
           uses: actions/upload-artifact@v4
           with:
             name: coverage-html
             path: htmlcov
   ```

4. Do **not** add a `--cov-fail-under` threshold yet. CI should pass even with 0% coverage.[web:62][web:60]

---

## Step 7 – Future work: increasing coverage over time

Once the scaffolding is in place and CI is green, we can:

1. Gradually replace placeholder tests with real unit tests that import and exercise production code.
2. Start tracking coverage trends and optionally:
   - introduce a minimum coverage threshold (`--cov-fail-under` or `[coverage:report] fail_under = X`),
   - add per-module coverage targets if needed.

These future steps are **out of scope** for this scaffolding plan, but the structure created here is designed to support them.