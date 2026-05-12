#!/usr/bin/env python3
"""Cross-platform script to run unit and Qt tests with automatic venv management.

Usage:
    python3 run_tests.py                    # Run unit tests with summary output
    python3 run_tests.py -v, --verbose      # Show detailed coverage report
    python3 run_tests.py -m core.align      # Run tests for specific module
    python3 run_tests.py -m handlers.channels -v  # Module tests with verbose output
    python3 run_tests.py --pytest-only      # Run pytest only (no coverage/docs checks)
    python3 run_tests.py --pytest-only -k "test_align"  # Pytest only with filter
    python3 run_tests.py --qt           # Run Qt tests (QT_QPA_PLATFORM=offscreen set automatically)
    python3 run_tests.py --qt -v        # Qt tests with detailed coverage report
    python3 run_tests.py --qt --pytest-only  # Qt pytest only (visible output)
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


def install_dependencies(*, suite: str = "all") -> None:
    """Install test and production dependencies if they've changed or are missing.

    Args:
        suite: Test suite to prepare for: 'all', 'business-logic', or 'qt'.
               'all' and 'qt' trigger Qt dependency installation.
    """
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
    if suite in ("all", "qt"):
        print("Installing pytest-qt and PyQt5 for Qt testing...")
        subprocess.check_call(
            [str(PYTHON_EXE), "-m", "pip", "install", "-q", "pytest-qt>=4.4.0", "PyQt5==5.15.10"],
            cwd=Path.cwd(),
        )
    VENV_MARKER.write_text(get_requirements_hash())


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


def check_module_coverage(output: str, coverage_targets: list[str], threshold: int) -> tuple[bool, list[str]]:
    """Check that each module meets minimum coverage threshold.

    Args:
        output: pytest coverage report output
        coverage_targets: list of modules to check (e.g., ["src.core.align"])
        threshold: minimum coverage percentage required

    Returns:
        Tuple of (all_pass, list_of_failures)
    """
    failures = []
    module_lines = {}

    # Parse coverage lines for each module
    for line in output.split("\n"):
        for target in coverage_targets:
            # Match lines like "src/core/align.py            27      1     10      1    95%   98"
            if target.replace(".", "/") + ".py" in line and "%" in line:
                match = re.search(r"(\d+\.?\d*)\s*%", line)
                if match:
                    pct = float(match.group(1))
                    module_lines[target] = pct
                    if pct < threshold:
                        failures.append(f"{target}: {pct}% (required {threshold}%)")

    return len(failures) == 0, failures


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



def run_tests(*, module: str | None = None, verbose: bool = False, args: list[str] | None = None) -> int:
    """Run business logic unit tests with coverage.

    Args:
        module: Specific module to test (e.g., "core.align"), or None for all
        verbose: Show detailed coverage report
        args: Additional pytest arguments

    Coverage enforcement: 90% minimum on non-UI modules (from coverage_config.py).
    """
    args = args or []

    # Import coverage config (single source of truth)
    sys.path.insert(0, str(Path.cwd() / "tests"))
    try:
        from coverage_config import get_business_logic_modules, BUSINESS_LOGIC_THRESHOLD
    finally:
        sys.path.pop(0)

    # Coverage targets from coverage_config.py get_business_logic_modules()
    coverage_targets = get_business_logic_modules()

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "pytest",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
    ]

    # Add coverage targets
    for target in coverage_targets:
        cmd.insert(3, f"--cov={target}")

    if module:
        # Run tests for specific module
        test_file = f"tests/unit/test_{module.replace('.', '_')}.py"
        cmd.append(test_file)

    cmd.extend(args)

    print(f"\n{'=' * 60}")
    print("Running business logic unit tests...")
    print("=" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print output and check coverage per-module
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

        # Check per-module coverage thresholds
        coverage_ok, failures = check_module_coverage(result.stdout, coverage_targets, BUSINESS_LOGIC_THRESHOLD)
        if not coverage_ok:
            print(f"\n⚠️  Per-module coverage check failed:")
            for failure in failures:
                print(f"  - {failure}")
            return 1

        if result.returncode != 0 and not verbose:
            print("\n⚠️  Tests failed. Run with -v/--verbose for details.")
            return result.returncode

        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running tests: {e}")
        return 1


def check_test_docs(module: str | None = None, verbose: bool = False, test_dir: str = "tests") -> int:
    """Check that all tests are documented.

    Args:
        module: Specific module to check, or None for all
        verbose: Show detailed documentation report
        test_dir: Directory to check (default "tests"; use "tests/qt" for Qt tests)

    Documentation coverage is always enforced at 100% for test files.
    """
    if module:
        # Check specific module's test file
        target = f"tests/unit/test_{module.replace('.', '_')}.py"
    else:
        # Check all test files in the given directory
        target = test_dir

    print(f"\n{'=' * 60}")
    print("Checking test documentation...")
    print("=" * 60)

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "interrogate",
        "--ignore-init-method",
        "--fail-under=100",
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


def run_qt_tests(*, verbose: bool = False, args: list[str] | None = None) -> int:
    """Run Qt tests from tests/qt/ with coverage enforcement at 80% threshold.

    Sets QT_QPA_PLATFORM=offscreen automatically. Coverage is measured for all
    modules in src/ui with per-module threshold enforcement.

    Args:
        verbose: Show full pytest output and coverage report
        args: Additional pytest arguments

    Coverage enforcement: 80% minimum on modules in src/ui (from coverage_config.py).
    """
    args = args or []

    # Import coverage config (single source of truth)
    sys.path.insert(0, str(Path.cwd() / "tests"))
    try:
        from coverage_config import get_qt_modules, QT_COVERAGE_THRESHOLD
    finally:
        sys.path.pop(0)

    # Coverage targets from coverage_config.py get_qt_modules()
    coverage_targets = get_qt_modules()

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "pytest",
        "tests/qt/",
        "--cov-branch",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov-qt",
    ]

    # Add coverage targets
    for target in coverage_targets:
        cmd.insert(3, f"--cov={target}")

    cmd.extend(args)

    print(f"\n{'=' * 60}")
    print("Running Qt tests (QT_QPA_PLATFORM=offscreen)...")
    print("=" * 60)

    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if verbose:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        else:
            test_summary = extract_test_summary(result.stdout)
            coverage_pct = extract_coverage_summary(result.stdout)
            print(test_summary)
            if coverage_pct[0] != "N/A":
                print(f"Code Coverage: {coverage_pct[0]}%")

        # Check per-module coverage thresholds
        coverage_ok, failures = check_module_coverage(result.stdout, coverage_targets, QT_COVERAGE_THRESHOLD)
        if not coverage_ok:
            print(f"\n⚠️  Per-module Qt coverage check failed:")
            for failure in failures:
                print(f"  - {failure}")
            return 1

        if result.returncode != 0 and not verbose:
            print("\n⚠️  Tests failed. Run with -v/--verbose for details.")

        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running Qt tests: {e}")
        return 1


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run unit or Qt tests with coverage and documentation checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            Run all tests (unit + Qt) with summary output
  %(prog)s -v                         Run all tests with detailed coverage report
  %(prog)s --fail-fast                Run all tests, stop at first failure
  %(prog)s --suite business-logic     Run business logic unit tests (90 pct threshold)
  %(prog)s --suite qt                 Run Qt tests (80 pct threshold)
  %(prog)s --suite business-logic -v  Business logic with detailed coverage
  %(prog)s -m core.align              Run tests for align module only
  %(prog)s -m handlers.channels -v    Module tests with verbose output
  %(prog)s --pytest-only              Run pytest directly (visible output, no checks)
  %(prog)s --pytest-only -k "test_align"  Pytest only, filtered by keyword
        """,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed coverage and documentation reports",
    )
    parser.add_argument(
        "--pytest-only",
        action="store_true",
        help="Run pytest directly with visible output (no coverage enforcement or doc checks)",
    )
    parser.add_argument(
        "-m",
        "--module",
        type=str,
        help="Run tests for specific module (e.g., core.align, handlers.channels). Only with unit tests.",
    )
    parser.add_argument(
        "--suite",
        type=str,
        choices=["all", "business-logic", "qt"],
        default="all",
        help="Test suite to run: 'all' (default) runs both unit and Qt tests, "
        "'business-logic' runs unit tests only, 'qt' runs Qt tests only",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after first test suite fails. Only applies to --suite all.",
    )
    parser.add_argument(
        "--qt",
        action="store_true",
        help="Deprecated: use --suite qt instead",
    )

    args, pytest_args = parser.parse_known_args()

    # Handle deprecated --qt flag
    if args.qt:
        args.suite = "qt"

    try:
        create_venv()
        install_dependencies(suite=args.suite)

        if args.pytest_only:
            if args.suite == "qt":
                cmd = [str(PYTHON_EXE), "-m", "pytest", "tests/qt/"]
                env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
                result = subprocess.run(cmd + pytest_args, env=env)
                sys.exit(result.returncode)
            elif args.suite == "business-logic":
                cmd = [str(PYTHON_EXE), "-m", "pytest"]
                if args.module:
                    cmd.append(f"tests/unit/test_{args.module.replace('.', '_')}.py")
                result = subprocess.run(cmd + pytest_args)
                sys.exit(result.returncode)
            elif args.suite == "all":
                # Run both suites as separate pytest calls (can't mix in same session due to Qt mocking)
                unit_cmd = [str(PYTHON_EXE), "-m", "pytest", "tests/unit/"]
                if args.module:
                    unit_cmd = [str(PYTHON_EXE), "-m", "pytest", f"tests/unit/test_{args.module.replace('.', '_')}.py"]
                print("Running business logic pytest...")
                result = subprocess.run(unit_cmd + pytest_args)
                if result.returncode != 0 and args.fail_fast:
                    sys.exit(result.returncode)

                print("\nRunning Qt pytest...")
                qt_cmd = [str(PYTHON_EXE), "-m", "pytest", "tests/qt/"]
                env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
                result = subprocess.run(qt_cmd + pytest_args, env=env)
                sys.exit(result.returncode)

        print("\n" + "=" * 60)
        print("TEST COVERAGE REPORT")
        print("=" * 60)

        if args.suite == "all":
            # Run both test suites
            test_result = run_tests(module=args.module, verbose=args.verbose, args=pytest_args)
            doc_result = check_test_docs(module=args.module, verbose=args.verbose)

            if test_result != 0 and args.fail_fast:
                print("\n" + "=" * 60)
                print("SUMMARY")
                print("=" * 60)
                print("❌ Business logic tests failed (fail-fast mode)")
                sys.exit(1)

            qt_result = run_qt_tests(verbose=args.verbose, args=pytest_args)
            qt_doc_result = check_test_docs(verbose=args.verbose, test_dir="tests/qt")

            results = {
                "Business Logic Tests": test_result,
                "Business Logic Docs": doc_result,
                "Qt Tests": qt_result,
                "Qt Docs": qt_doc_result,
            }
            overall_result = max(test_result, doc_result, qt_result, qt_doc_result)
        elif args.suite == "business-logic":
            test_result = run_tests(module=args.module, verbose=args.verbose, args=pytest_args)
            doc_result = check_test_docs(module=args.module, verbose=args.verbose)
            results = {
                "Business Logic Tests": test_result,
                "Business Logic Docs": doc_result,
            }
            overall_result = max(test_result, doc_result)
        elif args.suite == "qt":
            test_result = run_qt_tests(verbose=args.verbose, args=pytest_args)
            doc_result = check_test_docs(verbose=args.verbose, test_dir="tests/qt")
            results = {
                "Qt Tests": test_result,
                "Qt Docs": doc_result,
            }
            overall_result = max(test_result, doc_result)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if overall_result == 0:
            print("✅ All checks passed!")
            sys.exit(0)
        else:
            for name, result in results.items():
                if result != 0:
                    print(f"❌ {name} failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
