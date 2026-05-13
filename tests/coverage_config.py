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


# Qt widget modules with tests in tests/qt/ (80% threshold).
# These require a live QApplication and are tested with pytest-qt.
# Move modules here from EXCLUDED_MODULES as Qt tests are added.
QT_MODULES = {
    "src.ui.qt_utils",
    "src.ui.widgets.channel_controller",
    "src.ui.widgets.grid_overlay",
    "src.ui.widgets.grid_settings_dialog",
    "src.ui.widgets.image_viewer",
    "src.ui.widgets.preset_panel",
    "src.ui.widgets.sliders",
    "src.ui.widgets.status_bar",
}

# Modules excluded from ALL coverage enforcement (no tests yet).
# Remove modules from here as tests are added to either tests/unit/ or tests/qt/.
EXCLUDED_MODULES = {
    "src.ui.main_window",
    "src.ui.widgets.crop_handler",
}


def get_qt_modules() -> list[str]:
    """Get Qt widget modules tested in tests/qt/ (80% threshold).

    Returns:
        Sorted list of Qt widget modules under coverage enforcement.
    """
    return sorted(QT_MODULES)


def get_business_logic_modules() -> list[str]:
    """Get all modules tested in tests/unit/ (90% threshold).

    Includes everything auto-discovered in src/ except Qt widget modules
    and excluded modules. This covers core, services, handlers, and
    UI state/types that are tested with mocked Qt.

    Returns:
        Sorted list of business logic modules under coverage enforcement.
    """
    all_modules = _discover_modules()
    return [m for m in all_modules if m not in QT_MODULES and m not in EXCLUDED_MODULES]


def get_all_modules() -> list[str]:
    """Get all modules under coverage enforcement (both suites).

    Returns:
        Combined list of all modules under coverage enforcement.
    """
    return get_business_logic_modules() + get_qt_modules()
