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
def suppress_closevent_dialogs() -> None:
    """Patch MainWindow.closeEvent to prevent save session dialog during teardown.

    During test teardown, qtbot destroys widgets which triggers closeEvent,
    normally showing a QMessageBox asking to save session. Patching closeEvent
    to no-op prevents dialogs from blocking test cleanup without masking other
    tests' closeEvent behavior.
    """
    from src.ui.main_window import MainWindow

    original_close_event = MainWindow.closeEvent

    def patched_close_event(self: MainWindow, event: object) -> None:
        """Accept close event without prompting (for tests only)."""
        # During tests, accept the close without showing dialog
        if event is not None and hasattr(event, "accept"):
            event.accept()  # type: ignore[union-attr]

    with patch.object(MainWindow, "closeEvent", patched_close_event):
        yield


