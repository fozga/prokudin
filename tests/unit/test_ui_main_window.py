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

"""Unit tests for src.ui.main_window module (business-logic methods only)."""

from unittest.mock import MagicMock

import pytest

from src.ui.app_state import AppState
from src.ui.widgets.grid_types import (
    GRID_TYPE_3X3,
    GRID_TYPE_DIAGONAL_1_1,
    GRID_TYPE_DIAGONAL_2_3,
    GRID_TYPE_DIAGONAL_3_2,
    GRID_TYPE_DIAGONAL_3_4,
    GRID_TYPE_DIAGONAL_4_3,
    GRID_TYPE_DIAGONAL_GOLDEN_H,
    GRID_TYPE_DIAGONAL_GOLDEN_V,
    GRID_TYPE_DIAGONAL_THIRDS_H,
    GRID_TYPE_DIAGONAL_THIRDS_V,
    GRID_TYPE_GOLDEN_RATIO,
)


# Mirror of ``MainWindow.GRID_TYPE_STATUS_MESSAGES``. Duplicated here because
# ``tests/unit/conftest.py`` mocks PyQt5 at import time, which makes
# ``MainWindow`` itself a Mock and prevents the unit-test scaffold from
# reading the real class attribute.
_GRID_TYPE_STATUS_MESSAGES = {
    GRID_TYPE_3X3: "3x3 grid overlay enabled",
    GRID_TYPE_GOLDEN_RATIO: "Golden ratio grid overlay enabled",
    GRID_TYPE_DIAGONAL_1_1: "Diagonal 1:1 grid overlay enabled",
    GRID_TYPE_DIAGONAL_2_3: "Diagonal 2:3 grid overlay enabled",
    GRID_TYPE_DIAGONAL_3_2: "Diagonal 3:2 grid overlay enabled",
    GRID_TYPE_DIAGONAL_3_4: "Diagonal 3:4 grid overlay enabled",
    GRID_TYPE_DIAGONAL_4_3: "Diagonal 4:3 grid overlay enabled",
    GRID_TYPE_DIAGONAL_THIRDS_V: "Diagonal + thirds V grid overlay enabled",
    GRID_TYPE_DIAGONAL_THIRDS_H: "Diagonal + thirds H grid overlay enabled",
    GRID_TYPE_DIAGONAL_GOLDEN_V: "Diagonal + golden V grid overlay enabled",
    GRID_TYPE_DIAGONAL_GOLDEN_H: "Diagonal + golden H grid overlay enabled",
}


@pytest.fixture
def mw() -> MagicMock:
    """MainWindow stub for unit tests of business-logic methods.

    Provides a MagicMock with the collaborators that the method-under-test
    typically touches pre-wired (state, services, status handler, viewer,
    buttons, controllers, autosave timer). Tests call the real method via
    ``MainWindow.<method>(mw, ...)`` to exercise the actual body against
    this stub.

    Note: a plain ``MagicMock()`` is used rather than ``MagicMock(spec=MainWindow)``
    because ``tests/unit/conftest.py`` mocks PyQt5 at import time, which makes
    ``MainWindow`` itself a Mock and therefore unusable as a spec.
    """
    m = MagicMock()
    m.state = AppState()
    m.svc = MagicMock()
    m.status_handler = MagicMock()
    m.status_handler.SHORT_TIMEOUT = 3000
    m.status_handler.MEDIUM_TIMEOUT = 6000
    m.viewer = MagicMock()
    m.save_btn = MagicMock()
    m.crop_mode_btn = MagicMock()
    m.crop_controls = MagicMock()
    m.controllers = [MagicMock(), MagicMock(), MagicMock()]
    m._autosave_timer = MagicMock()
    m.GRID_TYPE_STATUS_MESSAGES = _GRID_TYPE_STATUS_MESSAGES
    return m


class TestMainWindowUnitScaffoldPlaceholder:
    """
    Test Design Specification: MainWindow unit-test scaffold (placeholder)
    Module under test: src/ui/main_window.py

    Contract:
        Placeholder class so the file is collected by pytest and the shared
        ``mw`` fixture is wired up. Remove this class when the first real
        unit test for MainWindow lands.

    What is tested:
        - The shared ``mw`` fixture builds a MagicMock with the standard
          collaborators pre-wired.

    What is NOT tested:
        - Any real MainWindow behaviour (covered by follow-up unit-test PRs).

    Constraints:
        - PyQt5 is mocked at module import time via ``tests/unit/conftest.py``,
          so ``MainWindow`` cannot be imported here as a real class. The
          ``mw`` fixture is therefore a plain ``MagicMock`` rather than a
          ``MagicMock(spec=MainWindow)``.
    """

    def test_fixture_provides_prewired_mainwindow_stub(self, mw: MagicMock) -> None:
        """
        Given the shared ``mw`` fixture,
        When inspecting the produced mock,
        Then it is a MagicMock with an AppState attached and the grid-status dict wired up.
        """
        # Arrange  (fixture provides ``mw``)
        # Act      (inspection only)
        # Assert
        assert isinstance(mw, MagicMock)
        assert isinstance(mw.state, AppState)
        assert mw.GRID_TYPE_STATUS_MESSAGES is _GRID_TYPE_STATUS_MESSAGES
