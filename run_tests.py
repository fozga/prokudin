#!/usr/bin/env python3
"""Cross-platform script to run unit tests with automatic venv management."""

import hashlib
import os
import subprocess
import sys
import venv
from pathlib import Path


VENV_DIR = Path(".venv-test")
VENV_BIN = VENV_DIR / ("Scripts" if sys.platform == "win32" else "bin")
PYTHON_EXE = VENV_BIN / ("python.exe" if sys.platform == "win32" else "python")
VENV_MARKER = VENV_DIR / ".requirements-hash"


def get_requirements_hash() -> str:
    """Get hash of both requirements-test.txt and requirements.txt."""
    req_files = [Path("requirements.txt"), Path("requirements-test.txt")]
    combined = b""
    for req_file in req_files:
        if not req_file.exists():
            raise FileNotFoundError(f"{req_file.name} not found. Run this script from the project root.")
        with open(req_file, "rb") as f:
            combined += f.read()
    return hashlib.md5(combined).hexdigest()


def requirements_changed() -> bool:
    """Check if requirements-test.txt has changed since last install."""
    current_hash = get_requirements_hash()
    if not VENV_MARKER.exists():
        return True
    return VENV_MARKER.read_text().strip() != current_hash


def create_venv() -> None:
    """Create virtual environment if it doesn't exist."""
    if not VENV_DIR.exists():
        print(f"Creating virtual environment at {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)


def install_dependencies() -> None:
    """Install test and production dependencies if they've changed or are missing."""
    if not requirements_changed():
        return

    print("Installing production and test dependencies...")
    subprocess.check_call(
        [str(PYTHON_EXE), "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        cwd=Path.cwd(),
    )
    subprocess.check_call(
        [str(PYTHON_EXE), "-m", "pip", "install", "-q", "-r", "requirements-test.txt"],
        cwd=Path.cwd(),
    )
    VENV_MARKER.write_text(get_requirements_hash())


def run_tests(args: list[str]) -> int:
    """Run unit tests with coverage.

    Coverage thresholds are handled by conftest.py based on git branch:
    - test/unit-test-infrastructure (superior): 0% threshold (no enforcement)
    - test/core-*, test/services-*, etc (module): 90% threshold on specific module
    """
    cmd = [
        str(PYTHON_EXE),
        "-m",
        "pytest",
        "--cov=src",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
    ]
    cmd.extend(args)

    print(f"\n{'=' * 50}")
    print("Running unit tests...")
    print("=" * 50)
    try:
        subprocess.check_call(cmd)
        return 0
    except subprocess.CalledProcessError:
        return 1


def check_test_docs() -> int:
    """Check that all tests are documented.

    Documentation coverage is enforced at 100% on both superior and module branches.
    Placeholder test methods satisfy this requirement with docstrings.
    """
    print(f"\n{'=' * 50}")
    print("Checking test documentation...")
    print("=" * 50)
    try:
        subprocess.check_call(
            [str(PYTHON_EXE), "-m", "interrogate", "--ignore-init-method", "--fail-under=100", "-vv", "tests"]
        )
        return 0
    except subprocess.CalledProcessError:
        return 1


def main() -> None:
    """Main entry point."""
    try:
        create_venv()
        install_dependencies()

        test_result = run_tests(sys.argv[1:])
        doc_result = check_test_docs()

        if test_result != 0 or doc_result != 0:
            sys.exit(1)
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

