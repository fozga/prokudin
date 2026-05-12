# Copyright (C) 2025 fozga
#
# This file is part of Prokudin.
#
# Prokudin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prokudin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prokudin.  If not, see <https://www.gnu.org/licenses/>.

"""Coverage configuration (single source of truth for coverage targets).

Auto-discovers all modules in src/ and enforces separate thresholds:
- Business logic (non-UI): 90% coverage
- Qt modules (src/ui): 80% coverage
Modules in EXCLUDED_MODULES are excluded from enforcement in both suites.
"""

from pathlib import Path

# Coverage enforcement thresholds (%)
BUSINESS_LOGIC_THRESHOLD = 90
QT_COVERAGE_THRESHOLD = 80


def _discover_modules() -> list[str]:
    """Auto-discover all importable modules in src/ (excluding __init__ and main)."""
    modules = []
    src_path = Path(__file__).parent.parent / "src"

    for py_file in sorted(src_path.rglob("*.py")):
        # Skip __init__.py, main.py, and __pycache__
        if py_file.name in ("__init__.py", "main.py") or "__pycache__" in py_file.parts:
            continue

        # Convert file path to module name
        relative = py_file.relative_to(src_path.parent)
        module = str(relative).replace("/", ".").replace(".py", "")
        modules.append(module)

    return modules


# Modules excluded from coverage enforcement (applies to both suites)
EXCLUDED_MODULES = {
    "src.ui.main_window",
    "src.ui.qt_utils",
    "src.ui.widgets.channel_controller",
    "src.ui.widgets.crop_handler",
    "src.ui.widgets.grid_overlay",
    "src.ui.widgets.grid_settings_dialog",
    "src.ui.widgets.image_viewer",
    "src.ui.widgets.preset_panel",
    "src.ui.widgets.sliders",
    "src.ui.widgets.status_bar",
}


def _is_qt_module(module: str) -> bool:
    """Check if a module is a Qt-related module (in src/ui)."""
    return module.startswith("src.ui")


def get_qt_modules() -> list[str]:
    """Get all Qt modules (src/ui) excluding those in EXCLUDED_MODULES.

    Returns:
        List of modules with 80% coverage threshold requirement.
    """
    all_modules = _discover_modules()
    return [m for m in all_modules if _is_qt_module(m) and m not in EXCLUDED_MODULES]


def get_business_logic_modules() -> list[str]:
    """Get all business logic modules (non-ui) excluding those in EXCLUDED_MODULES.

    Returns:
        List of modules with 90% coverage threshold requirement.
    """
    all_modules = _discover_modules()
    return [m for m in all_modules if not _is_qt_module(m) and m not in EXCLUDED_MODULES]


def get_all_modules() -> list[str]:
    """Get all modules (both Qt and business logic) excluding EXCLUDED_MODULES.

    Returns:
        Combined list of all modules under coverage enforcement.
    """
    return get_qt_modules() + get_business_logic_modules()


# Legacy exports for backwards compatibility with existing test code
ALL_MODULES = _discover_modules()
COVERAGE_TARGETS = get_all_modules()
COVERAGE_THRESHOLD = BUSINESS_LOGIC_THRESHOLD

# For backwards compatibility with unit test run_tests.py
TEST_TO_MODULE_MAP = {m.replace("src.", "test_").replace(".", "_"): m for m in get_business_logic_modules()}
