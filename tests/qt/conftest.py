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

"""Pytest configuration for widget tests."""

import pytest
from PyQt5.QtWidgets import QApplication
from unittest.mock import patch


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Session-scoped QApplication required by all widget tests."""
    app = QApplication.instance() or QApplication([])
    yield app  # type: ignore[misc]


@pytest.fixture(scope="session", autouse=True)
def suppress_dialogs() -> None:
    """Patch QMessageBox to prevent save/close dialogs from blocking tests.

    Prevents dialogs from appearing during test teardown when widgets are
    destroyed and closeEvent handlers try to show confirmation dialogs.
    """
    with patch("PyQt5.QtWidgets.QMessageBox.question", return_value=0):
        yield

