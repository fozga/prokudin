#!/usr/bin/env python3
"""Cross-platform script to run unit and Qt tests with automatic venv management.

Usage:
    python3 run_tests.py                    # Run all tests with combined summary
    python3 run_tests.py -v, --verbose      # Show detailed combined coverage report
    python3 run_tests.py --suite business-logic  # Run business logic tests only (90%)
    python3 run_tests.py --suite qt         # Run Qt tests only (80%)
    python3 run_tests.py -m core.align      # Run tests for specific module
    python3 run_tests.py --skip-docs        # Skip documentation coverage checks
    python3 run_tests.py --pytest-only      # Run pytest only (no coverage/docs checks)
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
    """Extract total coverage from pytest or coverage report output.

    Returns:
        Tuple of (total_coverage_pct, pass_fail_status)
    """
    for line in output.split("\n"):
        if "TOTAL" in line and "%" in line:
            match = re.search(r"(\d+\.?\d*)\s*%", line)
            if match:
                return match.group(1), ""
    return "N/A", ""


def check_module_coverage(output: str, coverage_targets: list[str], threshold: int) -> tuple[bool, list[str]]:
    """Check that each module meets minimum coverage threshold.

    Args:
        output: coverage report output (from pytest-cov or coverage report)
        coverage_targets: list of modules to check (e.g., ["src.core.align"])
        threshold: minimum coverage percentage required

    Returns:
        Tuple of (all_pass, list_of_failures)
    """
    failures = []

    for line in output.split("\n"):
        for target in coverage_targets:
            if target.replace(".", "/") + ".py" in line and "%" in line:
                match = re.search(r"(\d+\.?\d*)\s*%", line)
                if match:
                    pct = float(match.group(1))
                    if pct < threshold:
                        failures.append(f"{target}: {pct}% (required {threshold}%)")

    return len(failures) == 0, failures


def extract_test_summary(output: str) -> str:
    """Extract test result summary line (e.g. '521 passed, 3 skipped')."""
    for line in output.split("\n"):
        if "passed" in line or "failed" in line or "skipped" in line:
            if "==" in line:
                return line.strip().strip("=").strip()
    return "No summary found"


def combine_test_summaries(summary1: str, summary2: str) -> str:
    """Combine two test summary lines into one (e.g. '672 passed, 3 skipped')."""
    counts: dict[str, int] = {}
    for summary in (summary1, summary2):
        for match in re.finditer(r"(\d+)\s+(\w+)", summary):
            count, label = int(match.group(1)), match.group(2)
            counts[label] = counts.get(label, 0) + count
    order = ["passed", "failed", "skipped", "xfailed", "xpassed", "error", "warnings"]
    parts = []
    for label in order:
        if label in counts:
            parts.append(f"{counts[label]} {label}")
    for label, count in counts.items():
        if label not in order:
            parts.append(f"{count} {label}")
    return ", ".join(parts)


def extract_interrogate_summary(output: str) -> str:
    """Extract interrogate documentation coverage percentage.

    Returns:
        Coverage percentage string (e.g., "95.2") or "N/A"
    """
    for line in output.split("\n"):
        if "RESULT:" in line and "%" in line:
            match = re.search(r"actual:\s*([\d.]+)%", line)
            if match:
                return match.group(1)
    return "N/A"


def run_tests(*, module: str | None = None, args: list[str] | None = None, combined: bool = False) -> tuple[int, str]:
    """Run business logic unit tests with coverage.

    Args:
        module: Specific module to test (e.g., "core.align"), or None for all
        args: Additional pytest arguments
        combined: If True, suppress reports and write to .coverage.unit for later combining

    Returns:
        Tuple of (returncode, raw_stdout)
    """
    args = args or []

    sys.path.insert(0, str(Path.cwd() / "tests"))
    try:
        from coverage_config import get_business_logic_modules
    finally:
        sys.path.pop(0)

    coverage_targets = get_business_logic_modules()

    cmd = [str(PYTHON_EXE), "-m", "pytest"]

    if combined:
        cmd.extend(["--cov-branch", "--cov-report="])
    else:
        cmd.extend(["--cov-branch", "--cov-report=term-missing", "--cov-report=html:htmlcov"])

    for target in coverage_targets:
        cmd.insert(3, f"--cov={target}")

    if module:
        cmd.append(f"tests/unit/test_{module.replace('.', '_')}.py")

    cmd.extend(args)

    env = {**os.environ}
    if combined:
        env["COVERAGE_FILE"] = ".coverage.unit"

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout


def run_qt_tests(*, args: list[str] | None = None, combined: bool = False) -> tuple[int, str]:
    """Run Qt tests from tests/qt/ with coverage.

    Args:
        args: Additional pytest arguments
        combined: If True, suppress reports and write to .coverage.qt for later combining

    Returns:
        Tuple of (returncode, raw_stdout)
    """
    args = args or []

    sys.path.insert(0, str(Path.cwd() / "tests"))
    try:
        from coverage_config import get_qt_modules
    finally:
        sys.path.pop(0)

    coverage_targets = get_qt_modules()

    cmd = [str(PYTHON_EXE), "-m", "pytest", "tests/qt/"]

    if combined:
        cmd.extend(["--cov-branch", "--cov-report="])
    else:
        cmd.extend(["--cov-branch", "--cov-report=term-missing", "--cov-report=html:htmlcov-qt"])

    for target in coverage_targets:
        cmd.insert(3, f"--cov={target}")

    cmd.extend(args)

    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    if combined:
        env["COVERAGE_FILE"] = ".coverage.qt"

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout


def combine_coverage_reports() -> tuple[int, str]:
    """Combine .coverage.unit and .coverage.qt into a single report.

    Returns:
        Tuple of (returncode, coverage_report_output)
    """
    # Combine coverage data files
    subprocess.run(
        [str(PYTHON_EXE), "-m", "coverage", "combine", ".coverage.unit", ".coverage.qt"],
        capture_output=True, text=True,
    )

    # Generate terminal report (branch info already included from pytest --cov-branch)
    report_result = subprocess.run(
        [str(PYTHON_EXE), "-m", "coverage", "report", "--show-missing"],
        capture_output=True, text=True,
    )

    # Generate combined HTML report
    subprocess.run(
        [str(PYTHON_EXE), "-m", "coverage", "html", "-d", "htmlcov"],
        capture_output=True, text=True,
    )

    # Clean up temporary coverage files
    for f in [".coverage.unit", ".coverage.qt", ".coverage"]:
        Path(f).unlink(missing_ok=True)

    return report_result.returncode, report_result.stdout


def run_docs_check(*, module: str | None = None, test_dir: str = "tests") -> tuple[int, str]:
    """Run interrogate documentation coverage check.

    Args:
        module: Specific module to check, or None for all
        test_dir: Directory to check

    Returns:
        Tuple of (returncode, raw_stdout)
    """
    if module:
        target = f"tests/unit/test_{module.replace('.', '_')}.py"
    else:
        target = test_dir

    cmd = [
        str(PYTHON_EXE), "-m", "interrogate",
        "--ignore-init-method", "--fail-under=100", "-vv",
        target,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout


def print_suite_report(
    *,
    test_summary: str,
    coverage_output: str,
    doc_pct: str | None,
    verbose: bool,
    coverage_failures: list[str] | None = None,
) -> None:
    """Print the formatted test report for any suite mode."""
    if not verbose:
        coverage_pct = extract_coverage_summary(coverage_output)
        if doc_pct:
            print(f"Test Specification Coverage: {doc_pct}%")
        print(f"\n{test_summary}")
        if coverage_pct[0] != "N/A":
            print(f"Code Coverage: {coverage_pct[0]}%")
    else:
        if doc_pct:
            print(f"Test Specification Coverage: {doc_pct}%")
        print(f"\n{test_summary}")
        print(coverage_output.rstrip())

    if coverage_failures:
        print(f"\n⚠️  Per-module coverage check failed:")
        for failure in coverage_failures:
            print(f"  - {failure}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run unit or Qt tests with coverage and documentation checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            Run all tests with combined summary
  %(prog)s -v                         Run all tests with detailed coverage report
  %(prog)s --fail-fast                Run all tests, stop at first failure
  %(prog)s --skip-docs                Skip documentation coverage checks
  %(prog)s --suite business-logic     Run business logic unit tests only (90 pct)
  %(prog)s --suite qt                 Run Qt tests only (80 pct)
  %(prog)s -m core.align              Run tests for align module only
  %(prog)s --pytest-only              Run pytest directly (visible output, no checks)
  %(prog)s --pytest-only -k "test_align"  Pytest only, filtered by keyword
        """,
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show detailed coverage and documentation reports")
    parser.add_argument("--pytest-only", action="store_true",
                        help="Run pytest directly with visible output (no coverage enforcement or doc checks)")
    parser.add_argument("-m", "--module", type=str,
                        help="Run tests for specific module (e.g., core.align, handlers.channels)")
    parser.add_argument("--suite", type=str, choices=["all", "business-logic", "qt"], default="all",
                        help="Test suite to run (default: all)")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Stop after first test suite fails (only with --suite all)")
    parser.add_argument("--skip-docs", action="store_true",
                        help="Skip documentation coverage checks")
    parser.add_argument("--qt", action="store_true",
                        help="Deprecated: use --suite qt instead")

    args, pytest_args = parser.parse_known_args()

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
                unit_cmd = [str(PYTHON_EXE), "-m", "pytest", "tests/unit/"]
                if args.module:
                    unit_cmd = [str(PYTHON_EXE), "-m", "pytest",
                                f"tests/unit/test_{args.module.replace('.', '_')}.py"]
                print("Running business logic pytest...")
                result = subprocess.run(unit_cmd + pytest_args)
                if result.returncode != 0 and args.fail_fast:
                    sys.exit(result.returncode)
                print("\nRunning Qt pytest...")
                qt_cmd = [str(PYTHON_EXE), "-m", "pytest", "tests/qt/"]
                env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
                result = subprocess.run(qt_cmd + pytest_args, env=env)
                sys.exit(result.returncode)

        # Import thresholds
        sys.path.insert(0, str(Path.cwd() / "tests"))
        try:
            from coverage_config import (
                get_business_logic_modules, get_qt_modules,
                BUSINESS_LOGIC_THRESHOLD, QT_COVERAGE_THRESHOLD,
            )
        finally:
            sys.path.pop(0)

        print("\n" + "=" * 60)
        print("TEST COVERAGE REPORT")
        print("=" * 60)

        if args.suite == "all":
            # === Combined mode: one summary, one HTML report ===

            # 1. Run docs (combined)
            doc_pct = None
            doc_result = 0
            if not args.skip_docs:
                unit_doc_rc, unit_doc_out = run_docs_check(module=args.module)
                qt_doc_rc, qt_doc_out = run_docs_check(test_dir="tests/qt")
                doc_result = max(unit_doc_rc, qt_doc_rc)
                pct1 = extract_interrogate_summary(unit_doc_out)
                pct2 = extract_interrogate_summary(qt_doc_out)
                if pct1 != "N/A" and pct2 != "N/A":
                    doc_pct = f"{min(float(pct1), float(pct2)):.1f}"
                elif pct1 != "N/A":
                    doc_pct = pct1
                elif pct2 != "N/A":
                    doc_pct = pct2

            # 2. Run both test suites (suppress individual reports)
            test_rc, test_stdout = run_tests(module=args.module, args=pytest_args, combined=True)

            if test_rc != 0 and args.fail_fast:
                print("\n❌ Business logic tests failed (fail-fast mode)")
                sys.exit(1)

            qt_rc, qt_stdout = run_qt_tests(args=pytest_args, combined=True)

            # 3. Combine coverage data → one HTML report + one terminal table
            _, coverage_output = combine_coverage_reports()

            # 4. Combine test summaries
            test_summary = combine_test_summaries(
                extract_test_summary(test_stdout),
                extract_test_summary(qt_stdout),
            )

            # 5. Check thresholds against combined output
            biz_ok, biz_failures = check_module_coverage(
                coverage_output, get_business_logic_modules(), BUSINESS_LOGIC_THRESHOLD)
            qt_ok, qt_failures = check_module_coverage(
                coverage_output, get_qt_modules(), QT_COVERAGE_THRESHOLD)
            all_failures = biz_failures + qt_failures
            coverage_result = 0 if (biz_ok and qt_ok) else 1

            # 6. Print combined report
            print_suite_report(
                test_summary=test_summary,
                coverage_output=coverage_output,
                doc_pct=doc_pct,
                verbose=args.verbose,
                coverage_failures=all_failures if all_failures else None,
            )

            overall_result = max(test_rc, qt_rc, coverage_result, doc_result)
            results = {"Tests": max(test_rc, qt_rc), "Coverage Thresholds": coverage_result}
            if not args.skip_docs:
                results["Documentation"] = doc_result

        elif args.suite == "business-logic":
            # === Single suite: business logic only ===
            doc_pct = None
            doc_result = 0
            if not args.skip_docs:
                doc_rc, doc_out = run_docs_check(module=args.module)
                doc_result = doc_rc
                doc_pct = extract_interrogate_summary(doc_out)
                if doc_pct == "N/A":
                    doc_pct = None

            test_rc, test_stdout = run_tests(module=args.module, args=pytest_args)
            test_summary = extract_test_summary(test_stdout)

            biz_ok, biz_failures = check_module_coverage(
                test_stdout, get_business_logic_modules(), BUSINESS_LOGIC_THRESHOLD)
            coverage_result = 0 if biz_ok else 1

            print_suite_report(
                test_summary=test_summary,
                coverage_output=test_stdout,
                doc_pct=doc_pct,
                verbose=args.verbose,
                coverage_failures=biz_failures if biz_failures else None,
            )

            overall_result = max(test_rc, coverage_result, doc_result)
            results = {"Tests": test_rc, "Coverage Thresholds": coverage_result}
            if not args.skip_docs:
                results["Documentation"] = doc_result

        elif args.suite == "qt":
            # === Single suite: Qt only ===
            doc_pct = None
            doc_result = 0
            if not args.skip_docs:
                doc_rc, doc_out = run_docs_check(test_dir="tests/qt")
                doc_result = doc_rc
                doc_pct = extract_interrogate_summary(doc_out)
                if doc_pct == "N/A":
                    doc_pct = None

            test_rc, test_stdout = run_qt_tests(args=pytest_args)
            test_summary = extract_test_summary(test_stdout)

            qt_ok, qt_failures = check_module_coverage(
                test_stdout, get_qt_modules(), QT_COVERAGE_THRESHOLD)
            coverage_result = 0 if qt_ok else 1

            print_suite_report(
                test_summary=test_summary,
                coverage_output=test_stdout,
                doc_pct=doc_pct,
                verbose=args.verbose,
                coverage_failures=qt_failures if qt_failures else None,
            )

            overall_result = max(test_rc, coverage_result, doc_result)
            results = {"Tests": test_rc, "Coverage Thresholds": coverage_result}
            if not args.skip_docs:
                results["Documentation"] = doc_result

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
