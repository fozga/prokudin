#!/usr/bin/env python3
"""Cross-platform script to run unit tests with automatic venv management.

Usage:
    python3 run_tests.py                    # Run with summary output
    python3 run_tests.py -v, --verbose      # Show detailed coverage report
    python3 run_tests.py -m core.align      # Run tests for specific module
    python3 run_tests.py -m handlers.channels -v  # Module tests with verbose output
"""

import argparse
import hashlib
import os
import re
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


def get_current_branch() -> str:
    """Get current git branch name."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "main"


def extract_coverage_summary(output: str) -> tuple[str, str]:
    """Extract total coverage from pytest output.

    Returns:
        Tuple of (total_coverage_pct, pass_fail_status)
    """
    # Look for "TOTAL" line in coverage output
    for line in output.split("\n"):
        if "TOTAL" in line and "%" in line:
            # Extract percentage
            match = re.search(r"(\d+\.?\d*)\s*%", line)
            if match:
                return match.group(1), ""
    return "N/A", ""


def extract_test_summary(output: str) -> str:
    """Extract test result summary."""
    for line in output.split("\n"):
        if "passed" in line or "failed" in line or "skipped" in line:
            if "==" in line:  # Summary line
                return line.strip().strip("=").strip()
    return "No summary found"


def extract_interrogate_summary(output: str) -> str:
    """Extract interrogate documentation coverage percentage.

    Returns:
        Coverage percentage string (e.g., "95.2%") or "N/A"
    """
    for line in output.split("\n"):
        if "RESULT:" in line and "%" in line:
            # Extract percentage from "RESULT: PASSED (minimum: 0.0%, actual: 95.2%)"
            match = re.search(r"actual:\s*([\d.]+)%", line)
            if match:
                return match.group(1)
    return "N/A"



def run_tests(module: str | None = None, verbose: bool = False, args: list[str] | None = None) -> int:
    """Run unit tests with coverage.

    Args:
        module: Specific module to test (e.g., "core.align"), or None for all
        verbose: Show detailed coverage report
        args: Additional pytest arguments

    Coverage thresholds are handled by conftest.py based on git branch:
    - test/unit-test-infrastructure (superior): 0% threshold
    - test/core-*, test/services-*, etc (module): 90% threshold on specific module
    """
    args = args or []

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "pytest",
        "--cov=src",
        "--cov-branch",
        "--cov-report=term-missing" if verbose else "--cov-report=term",
        "--cov-report=html:htmlcov",
    ]

    if module:
        # Run tests for specific module
        test_file = f"tests/unit/test_{module.replace('.', '_')}.py"
        cmd.append(test_file)

    cmd.extend(args)

    print(f"\n{'=' * 60}")
    print("Running unit tests...")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print output
        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        else:
            # Extract and show summary only
            test_summary = extract_test_summary(result.stdout)
            coverage_pct = extract_coverage_summary(result.stdout)
            print(test_summary)
            if coverage_pct[0] != "N/A":
                print(f"Code Coverage: {coverage_pct[0]}%")

        if result.returncode != 0 and not verbose:
            print("\n⚠️  Tests failed. Run with -v/--verbose for details.")

        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        return 1


def check_test_docs(module: str | None = None, verbose: bool = False) -> int:
    """Check that all tests are documented.

    Args:
        module: Specific module to check, or None for all
        verbose: Show detailed documentation report

    Documentation coverage is enforced at:
    - Superior branch (test/unit-test-infrastructure): 0% (no enforcement)
    - Module branches (test/core-*, test/handlers-*, etc): 100% required
    """
    current_branch = get_current_branch()

    # Determine what to check and threshold based on branch
    if module:
        # Check specific module
        target = f"tests/unit/test_{module.replace('.', '_')}.py"
        fail_under = 100
    elif current_branch == "test/unit-test-infrastructure":
        # Superior branch: check all tests with no threshold
        target = "tests"
        fail_under = 0
    else:
        # Module branch: check only the specific module's test file
        branch_module = current_branch.replace("test/", "").replace("-", "_")
        target = f"tests/unit/test_{branch_module}.py"
        fail_under = 100

    print(f"\n{'=' * 60}")
    print("Checking test documentation...")
    print("=" * 60)

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "interrogate",
        "--ignore-init-method",
        f"--fail-under={fail_under}",
        "-vv",  # Always use verbose to capture summary
        target,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        else:
            # Extract and show summary only
            doc_pct = extract_interrogate_summary(result.stdout)
            if doc_pct != "N/A":
                print(f"Test Specification Coverage: {doc_pct}%")
            if result.returncode != 0 and not verbose:
                print("⚠️  Documentation check failed. Run with -v/--verbose for details.")


        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error checking documentation: {e}")
        return 1


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run unit tests with coverage and documentation checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Run all tests with summary output
  %(prog)s -v                       Run with detailed coverage report
  %(prog)s -m core.align            Run tests for align module only
  %(prog)s -m handlers.channels -v  Run module tests with verbose output
        """,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed coverage and documentation reports",
    )
    parser.add_argument(
        "-m",
        "--module",
        type=str,
        help="Run tests for specific module (e.g., core.align, handlers.channels)",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional arguments to pass to pytest",
    )

    args = parser.parse_args()

    try:
        create_venv()
        install_dependencies()

        print("\n" + "=" * 60)
        print("TEST COVERAGE REPORT")
        print("=" * 60)

        test_result = run_tests(module=args.module, verbose=args.verbose, args=args.pytest_args)
        doc_result = check_test_docs(module=args.module, verbose=args.verbose)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if test_result == 0 and doc_result == 0:
            print("✅ All checks passed!")
            sys.exit(0)
        else:
            if test_result != 0:
                print("❌ Code coverage check failed")
            if doc_result != 0:
                print("❌ Documentation check failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
