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
- On test/unit-test-infrastructure (superior) branch: no minimum coverage required
- On module branches (test/core-*, test/services-*, test/ui-*, test/handlers-*, test/widgets-*):
  90% minimum coverage required unless @pytest.mark.skip_coverage_enforcement is set
"""

import subprocess
from typing import Any

import pytest


def pytest_configure(config: Any) -> None:
    """Register custom markers."""
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

    # On module branches (test/*-*), enforce 90% coverage by default
    # On superior branch (test/unit-test-infrastructure), don't enforce
    if current_branch.startswith("test/") and current_branch != "test/unit-test-infrastructure":
        # Add coverage fail-under option for module branches
        config.option.cov_fail_under = 90


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    """Skip coverage enforcement for marked tests."""
    for item in items:
        if item.get_closest_marker("skip_coverage_enforcement"):
            # Remove the cov_fail_under setting for this module
            config.option.cov_fail_under = 0


