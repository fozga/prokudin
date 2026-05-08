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

"""Pytest configuration for unit tests.

Coverage enforcement:
- On test/unit-test-infrastructure (superior) branch: 0% minimum (no threshold)
- On module branches (test/core-*, test/services-*, test/ui-*, etc):
  90% minimum coverage required on the specific tested module
"""

import subprocess
from typing import Any

import pytest


# Map test files to their source modules for targeted coverage measurement
TEST_TO_MODULE_MAP = {
    "test_core_align": "src.core.align",
    "test_core_image_processing": "src.core.image_processing",
    "test_services_processor": "src.services.processor",
    "test_ui_default_state": "src.ui.default_state",
    "test_ui_app_state": "src.ui.app_state",
    "test_ui_grid_types": "src.ui.widgets.grid_types",
    "test_handlers_channels": "src.ui.handlers.channels",
    "test_handlers_keyboard": "src.ui.handlers.keyboard",
    "test_handlers_display": "src.ui.handlers.display",
    "test_handlers_autosave": "src.ui.handlers.autosave",
    "test_handlers_image_loading": "src.ui.handlers.image_loading",
    "test_handlers_image_saving": "src.ui.handlers.image_saving",
    "test_handlers_presets": "src.ui.handlers.presets",
}


def pytest_configure(config: Any) -> None:
    """Register custom markers and configure coverage based on branch."""
    config.addinivalue_line(
        "markers",
        "skip_coverage_enforcement: skip 90% minimum coverage requirement for this module",
    )

    # Get current git branch
    try:
        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        current_branch = ""

    # Default: no coverage threshold (superior branch or other)
    config.option.cov_fail_under = 0

    # On module branches ONLY, measure coverage for specific module with 90% threshold
    if current_branch.startswith("test/") and current_branch != "test/unit-test-infrastructure":
        # Extract module from branch name (e.g., test/core-align -> core_align)
        branch_module = current_branch.replace("test/", "").replace("-", "_")

        # Find matching source module
        for test_name, src_module in TEST_TO_MODULE_MAP.items():
            if branch_module.startswith(test_name.replace("test_", "")):
                # Override --cov to measure only this module
                config.option.cov = src_module
                config.option.cov_fail_under = 90
                break


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Skip coverage enforcement for marked tests or modules."""
    # Check if any test item has skip_coverage_enforcement marker
    skip_coverage = False
    for item in items:
        if item.get_closest_marker("skip_coverage_enforcement"):
            skip_coverage = True
            break

    # If marker found, disable coverage threshold
    if skip_coverage:
        config.option.cov_fail_under = 0


