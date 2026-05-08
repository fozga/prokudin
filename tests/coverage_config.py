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

Auto-discovers all modules in src/ and enforces 90% coverage on all except
those listed in EXCLUDED_MODULES. Coverage is enabled incrementally by removing
modules from the exclusion list as they gain test coverage.
"""

from pathlib import Path

# Coverage enforcement threshold (%)
COVERAGE_THRESHOLD = 90


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


# Modules excluded from coverage enforcement (add modules here as tests reach 90%)
EXCLUDED_MODULES = {
    "src.ui.main_window",
    "src.ui.qt_utils",
    "src.ui.handlers.autosave",
    "src.ui.handlers.channels",
    "src.ui.handlers.display",
    "src.ui.handlers.image_loading",
    "src.ui.handlers.image_saving",
    "src.ui.handlers.presets",
    "src.ui.widgets.channel_controller",
    "src.ui.widgets.crop_handler",
    "src.ui.widgets.grid_overlay",
    "src.ui.widgets.grid_settings_dialog",
    "src.ui.widgets.image_viewer",
    "src.ui.widgets.preset_panel",
    "src.ui.widgets.sliders",
    "src.ui.widgets.status_bar",
}

# Discover and filter: all modules except those explicitly excluded
ALL_MODULES = _discover_modules()
COVERAGE_TARGETS = [m for m in ALL_MODULES if m not in EXCLUDED_MODULES]

# For backwards compatibility and clarity
TEST_TO_MODULE_MAP = {m.replace("src.", "test_").replace(".", "_"): m for m in COVERAGE_TARGETS}
