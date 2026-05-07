#!/usr/bin/env python3
"""Cross-platform script to run code quality checks with automatic venv management."""

import hashlib
import os
import subprocess
import sys
import venv
from pathlib import Path


VENV_DIR = Path(".venv")
VENV_BIN = VENV_DIR / ("Scripts" if sys.platform == "win32" else "bin")
PYTHON_EXE = VENV_BIN / ("python.exe" if sys.platform == "win32" else "python")
VENV_MARKER = VENV_DIR / ".requirements-hash"


def get_requirements_hash() -> str:
    """Get hash of requirements-dev.txt."""
    req_file = Path("requirements-dev.txt")
    if not req_file.exists():
        raise FileNotFoundError("requirements-dev.txt not found. Run this script from the project root.")
    with open(req_file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def requirements_changed() -> bool:
    """Check if requirements-dev.txt has changed since last install."""
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
    """Install dev dependencies if they've changed or are missing."""
    if not requirements_changed():
        return

    print("Installing dev dependencies...")
    subprocess.check_call(
        [str(PYTHON_EXE), "-m", "pip", "install", "-q", "-r", "requirements-dev.txt"],
        cwd=Path.cwd(),
    )
    VENV_MARKER.write_text(get_requirements_hash())


def run_checks() -> int:
    """Run all code quality checks."""
    checks = [
        ("black", ["black", "--check", "src/"]),
        ("isort", ["isort", "--check-only", "src/"]),
        ("flake8", ["flake8", "src/"]),
        ("pylint", ["pylint", "src/"]),
        ("mypy", ["mypy", "--explicit-package-bases", "src/"]),
        ("interrogate", ["interrogate", "--ignore-init-method", "--fail-under=100", "--exclude=.venv", "-vv", "."]),
        ("pip-licenses", ["pip-licenses", "--from=mixed", "--fail-on=restricted"]),
    ]

    failed = []
    for check_name, cmd in checks:
        print(f"\n{'=' * 50}")
        print(f"Running {check_name}...")
        print("=" * 50)
        try:
            if check_name == "pip-licenses":
                subprocess.check_call([str(VENV_BIN / "pip-licenses")] + cmd[1:])
            else:
                subprocess.check_call([str(PYTHON_EXE), "-m"] + cmd)
        except subprocess.CalledProcessError:
            failed.append(check_name)

    print(f"\n{'=' * 50}")
    if failed:
        print(f"❌ {len(failed)} check(s) failed: {', '.join(failed)}")
        return 1
    print("✅ All checks passed!")
    return 0


def main() -> None:
    """Main entry point."""
    try:
        create_venv()
        install_dependencies()
        sys.exit(run_checks())
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
