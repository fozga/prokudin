# Contributing to Prokudin

Thank you for your interest in contributing! This project uses several automated checks to ensure code quality, consistency, and compliance. Please read the following guidelines before submitting a pull request.

---

## Automated Checks and Workflows

This repository uses GitHub Actions workflows to automatically check code quality, formatting, documentation, licensing, and more. These workflows run on every pull request and on pushes to certain branches.

### Overview of Workflows

- **Formatting Check**: Ensures code is formatted with [Black](https://black.readthedocs.io/en/stable/) and imports are ordered with [isort](https://pycqa.github.io/isort/).
- **PEP 8 Compliance Check**: Uses [flake8](https://flake8.pycqa.org/) to check for PEP 8 compliance and common Python issues.
- **Static Code Analysis**: Runs [pylint](https://pylint.org/) for deeper static analysis and code quality checks.
- **Type Checking**: Uses [mypy](http://mypy-lang.org/) to check for type errors and enforce type annotations.
- **Documentation Coverage**: Uses [interrogate](https://interrogate.readthedocs.io/) to ensure all code is properly documented with docstrings.
- **Build and Deploy Documentation**: Builds API documentation using [pdoc](https://pdoc.dev/) and deploys it to GitHub Pages.
- **License and Open Source Compliance Check**: Uses [pip-licenses](https://github.com/raimon49/pip-licenses) to ensure all dependencies have acceptable licenses.
- **Publish to GHCR**: Builds and publishes a Docker image to GitHub Container Registry (GHCR) on pushes to `main`.

---

## Running Checks Locally

Before submitting a pull request, run all checks locally with a single command:

```sh
python3 run_checks.py
```

This script automatically:
- Creates and manages a virtual environment (`.venv/`)
- Installs all dev tools on first run
- Caches dependencies — subsequent runs are fast (~35s)
- Runs all quality checks: black, isort, flake8, pylint, mypy, interrogate
- Works cross-platform (Linux, macOS, Windows)

The virtual environment is created in `.venv/` and is ignored by git. On first run with fresh dependencies, it takes ~1.5 minutes. Subsequent runs skip the install step.

If you want to run individual checks, activate the venv manually:
- **Linux/macOS**: `source .venv/bin/activate`
- **Windows**: `.venv\Scripts\activate`

Then run any check tool directly: `black src/`, `isort src/`, etc.

---

## Purpose of Each Workflow

- **Formatting Check**: Prevents unformatted code and unordered imports from being merged.
- **PEP 8 Compliance Check**: Ensures code follows Python style guidelines.
- **Static Code Analysis**: Detects code smells, bugs, and anti-patterns.
- **Type Checking**: Catches type errors and enforces type safety.
- **Documentation Coverage**: Ensures all public code is documented.
- **Build and Deploy Documentation**: Keeps API documentation up-to-date and available online.
- **License and Open Source Compliance Check**: Ensures all dependencies are properly licensed.
- **Publish to GHCR**: Provides up-to-date Docker images for deployment and testing.

---

## Submitting a Pull Request

1. Fork the repository and create your branch from `main`.
2. Make your changes.
3. Run all checks locally (see above).
4. Commit and push your changes.
5. Open a pull request and ensure all GitHub Actions checks pass.

If you have any questions, feel free to open an issue or ask in your pull request!

---
