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

"""Integration tests for src/ui/main_window.MainWindow."""

import pytest

from src.ui.main_window import MainWindow


@pytest.mark.integration
class TestMainWindowIntegrationScaffoldPlaceholder:
    """
    Test Design Specification: MainWindow integration-test scaffold (placeholder)
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Placeholder smoke test to verify the shared ``real_window`` fixture
        constructs a fully real ``MainWindow`` (no handler mocks beyond the
        suppressed autosave restore). Remove when the first real integration
        test lands.

    Infrastructure:
        - Requires session-scoped ``qapp`` and module-scoped ``real_window``
          fixtures from ``tests/integration/conftest.py``.
        - Requires QT_QPA_PLATFORM=offscreen.

    What is tested:
        - The ``real_window`` fixture yields a visible MainWindow with all
          collaborators wired up.

    What is NOT tested:
        - Any user-facing flow (covered by follow-up integration PRs).

    Mocking strategy:
        - Only ``restore_autosave`` is patched; everything else is real.
    """

    def test_real_window_fixture_constructs_visible_main_window(
        self, real_window: MainWindow
    ) -> None:
        """
        Given the shared ``real_window`` fixture,
        When the fixture finishes setup,
        Then the produced object is a real MainWindow that is visible and wired.
        """
        # Arrange  (fixture provides ``real_window``)
        # Act      (inspection only)
        # Assert
        assert isinstance(real_window, MainWindow)
        assert real_window.isVisible()
        assert len(real_window.controllers) == 3
