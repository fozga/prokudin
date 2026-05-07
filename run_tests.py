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
    """Get hash of requirements-test.txt."""
    req_file = Path("requirements-test.txt")
    if not req_file.exists():
        raise FileNotFoundError("requirements-test.txt not found. Run this script from the project root.")
    with open(req_file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


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
    """Install test dependencies if they've changed or are missing."""
    if not requirements_changed():
        return

    print("Installing test dependencies...")
    subprocess.check_call(
        [str(PYTHON_EXE), "-m", "pip", "install", "-q", "-r", "requirements-test.txt"],
        cwd=Path.cwd(),
    )
    VENV_MARKER.write_text(get_requirements_hash())


def run_tests(args: list[str]) -> int:
    """Run unit tests with coverage."""
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


def main() -> None:
    """Main entry point."""
    try:
        create_venv()
        install_dependencies()
        sys.exit(run_tests(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
