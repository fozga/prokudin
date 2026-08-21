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

import sys
from unittest.mock import MagicMock, patch

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
# reading the real class attribute. **IMPORTANT**: if MainWindow.GRID_TYPE_STATUS_MESSAGES
# changes, update this dict to match to ensure test fixtures stay in sync.
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


def _get_real_mainwindow_method(method_name: str):
    """Import and retrieve real MainWindow method via the existing PyQt5 mock.

    The conftest PyQt5 mock is already active, so MainWindow can be imported
    normally: its base class (QMainWindow) resolves to a MagicMock, but all
    methods defined in the class body are real Python functions and are fully
    accessible. No temporary un-patching is needed, and this approach works
    on CI environments where PyQt5 is not installed.
    """
    from src.ui.main_window import MainWindow

    return getattr(MainWindow, method_name)


@pytest.fixture
def mw() -> MagicMock:
    """MainWindow stub for unit tests of business-logic methods.

    Provides a MagicMock with the collaborators that the method-under-test
    typically touches pre-wired (state, services, status handler, viewer,
    buttons, controllers, autosave timer). Tests call the real method via
    unbound syntax using _get_real_mainwindow_method helper.

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


class TestUpdateModeFromState:
    """
    Test Design Specification: _update_mode_from_state()
    Module under test: src/ui/main_window.py

    Contract:
        Counts non-None entries in svc.original_images, forwards count and
        state.crop_mode to status_handler.update_mode_from_state.

    Equivalence partitions:
        EP1  all three original_images are None → count = 0 forwarded
        EP2  one image loaded → count = 1 forwarded
        EP3  all three loaded → count = 3 forwarded
        EP4  state.crop_mode = True → True forwarded as second argument
    """

    def test_all_channels_none(self, mw: MagicMock) -> None:
        """
        Given svc.original_images = [None, None, None],
        When _update_mode_from_state is called,
        Then status_handler.update_mode_from_state is called with count=0 and crop_mode.
        """
        # Arrange
        method = _get_real_mainwindow_method("_update_mode_from_state")
        mw.svc.original_images = [None, None, None]
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mw.status_handler.update_mode_from_state.assert_called_once_with(0, False)

    def test_one_channel_loaded(self, mw: MagicMock) -> None:
        """
        Given svc.original_images = [<img>, None, None],
        When _update_mode_from_state is called,
        Then status_handler.update_mode_from_state is called with count=1.
        """
        # Arrange
        method = _get_real_mainwindow_method("_update_mode_from_state")
        mw.svc.original_images = [MagicMock(), None, None]
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mw.status_handler.update_mode_from_state.assert_called_once_with(1, False)

    def test_all_channels_loaded(self, mw: MagicMock) -> None:
        """
        Given svc.original_images = [<img>, <img>, <img>],
        When _update_mode_from_state is called,
        Then status_handler.update_mode_from_state is called with count=3.
        """
        # Arrange
        method = _get_real_mainwindow_method("_update_mode_from_state")
        mw.svc.original_images = [MagicMock(), MagicMock(), MagicMock()]
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mw.status_handler.update_mode_from_state.assert_called_once_with(3, False)

    def test_crop_mode_true(self, mw: MagicMock) -> None:
        """
        Given state.crop_mode = True,
        When _update_mode_from_state is called,
        Then True is forwarded as second argument to status_handler.
        """
        # Arrange
        method = _get_real_mainwindow_method("_update_mode_from_state")
        mw.svc.original_images = [None, None, None]
        mw.state.crop_mode = True

        # Act
        method(mw)

        # Assert
        mw.status_handler.update_mode_from_state.assert_called_once_with(0, True)


class TestUpdateSaveButtonState:
    """
    Test Design Specification: update_save_button_state()
    Module under test: src/ui/main_window.py

    Contract:
        Enables save_btn iff svc.has_aligned_channels() is True; enables
        crop_mode_btn iff svc.has_processed_channels() is True; always calls
        _update_mode_from_state.

    Equivalence partitions:
        EP1  has_aligned=True, has_processed=True    → both buttons enabled
        EP2  has_aligned=False, has_processed=False  → both buttons disabled
        EP3  has_aligned=True, has_processed=False   → save enabled, crop disabled
        EP4  has_aligned=False, has_processed=True   → save disabled, crop enabled
        EP5  _update_mode_from_state called in all cases (verify via spy)
    """

    @pytest.mark.parametrize("has_aligned,has_processed", [
        (True, True),
        (False, False),
        (True, False),
        (False, True),
    ])
    def test_button_enable_combinations(self, mw: MagicMock, has_aligned: bool, has_processed: bool) -> None:
        """
        Given svc.has_aligned_channels() and svc.has_processed_channels() return specified values,
        When update_save_button_state is called,
        Then correct buttons are enabled/disabled and _update_mode_from_state is called.
        """
        # Arrange
        method = _get_real_mainwindow_method("update_save_button_state")
        real_update_mode = _get_real_mainwindow_method("_update_mode_from_state")
        mw.svc.has_aligned_channels.return_value = has_aligned
        mw.svc.has_processed_channels.return_value = has_processed
        mw._update_mode_from_state = real_update_mode.__get__(mw, type(mw))

        # Act
        method(mw)

        # Assert
        mw.save_btn.setEnabled.assert_called_once_with(has_aligned)
        mw.crop_mode_btn.setEnabled.assert_called_once_with(has_processed)
        mw.status_handler.update_mode_from_state.assert_called_once()


class TestScheduleAutosave:
    """
    Test Design Specification: _schedule_autosave()
    Module under test: src/ui/main_window.py

    Contract:
        Restarts _autosave_timer (single-shot, so restarting cancels any pending
        fire and schedules a fresh one).

    Equivalence partitions:
        EP1  first call → _autosave_timer.start() called once
        EP2  consecutive calls → start() called multiple times (timer restarts)
    """

    def test_timer_started_once(self, mw: MagicMock) -> None:
        """
        Given a mock autosave timer,
        When _schedule_autosave is called,
        Then timer.start() is called.
        """
        # Arrange
        method = _get_real_mainwindow_method("_schedule_autosave")
        mw._autosave_timer = MagicMock()

        # Act
        method(mw)

        # Assert
        mw._autosave_timer.start.assert_called_once()

    def test_timer_restarted_on_consecutive_calls(self, mw: MagicMock) -> None:
        """
        Given a mock autosave timer,
        When _schedule_autosave is called twice,
        Then start() is called twice (timer restart behavior).
        """
        # Arrange
        method = _get_real_mainwindow_method("_schedule_autosave")
        mw._autosave_timer = MagicMock()

        # Act
        method(mw)
        method(mw)

        # Assert
        assert mw._autosave_timer.start.call_count == 2


class TestOnGridTypeChanged:
    """
    Test Design Specification: on_grid_type_changed()
    Module under test: src/ui/main_window.py

    Contract:
        Delegates to handlers.grid.on_grid_type_changed. Grid overlay enable/disable,
        type setting, and status messages are handled by delegate.

    Equivalence partitions:
        EP1  Delegation works with correct parameters
    """

    @patch("src.ui.main_window.grid_on_type_changed")
    def test_delegates_to_handler(self, mock_handler: MagicMock, mw: MagicMock) -> None:
        """
        Given a grid type string,
        When on_grid_type_changed is called,
        Then the handler is called with mainwindow and grid type.
        """
        # Arrange
        method = _get_real_mainwindow_method("on_grid_type_changed")
        grid_type = GRID_TYPE_3X3

        # Act
        method(mw, grid_type)

        # Assert
        mock_handler.assert_called_once_with(mw, grid_type)


class TestOnGridLineWidthChanged:
    """
    Test Design Specification: on_grid_line_width_changed()
    Module under test: src/ui/main_window.py

    Contract:
        Delegates to handlers.grid.on_grid_line_width_changed.

    Equivalence partitions:
        EP1  width = 1   → delegate called with 1
        EP2  width = 10  → delegate called with 10
        BV1  width = 0   → no exception, delegate called
    """

    @patch("src.ui.main_window.grid_on_line_width_changed")
    def test_delegates_to_handler(self, mock_handler: MagicMock, mw: MagicMock) -> None:
        """
        Given a line width value,
        When on_grid_line_width_changed is called,
        Then the handler is called with mainwindow and width.
        """
        # Arrange
        method = _get_real_mainwindow_method("on_grid_line_width_changed")
        width = 5

        # Act
        method(mw, width)

        # Assert
        mock_handler.assert_called_once_with(mw, width)

    @patch("src.ui.main_window.grid_on_line_width_changed")
    def test_zero_width(self, mock_handler: MagicMock, mw: MagicMock) -> None:
        """
        Given width = 0,
        When on_grid_line_width_changed is called,
        Then no exception is raised and handler is called.
        """
        # Arrange
        method = _get_real_mainwindow_method("on_grid_line_width_changed")
        width = 0

        # Act
        method(mw, width)

        # Assert
        mock_handler.assert_called_once_with(mw, width)


class TestSaveImages:
    """
    Test Design Specification: save_images()
    Module under test: src/ui/main_window.py

    Contract:
        Calls save_image_with_dialog(self), then updates status based on return.

    Equivalence partitions:
        EP1  returns (True, "")     → status shows "Image saved successfully"
        EP2  returns (False, "msg") → status shows the error message
    """

    @patch("src.ui.main_window.save_image_with_dialog")
    def test_save_success(self, mock_save: MagicMock, mw: MagicMock) -> None:
        """
        Given save_image_with_dialog returns (True, ""),
        When save_images is called,
        Then status message is "Image saved successfully".
        """
        # Arrange
        method = _get_real_mainwindow_method("save_images")
        mock_save.return_value = (True, "")

        # Act
        method(mw)

        # Assert
        mw.status_handler.set_message.assert_called_with("Image saved successfully")

    @patch("src.ui.main_window.save_image_with_dialog")
    def test_save_failure(self, mock_save: MagicMock, mw: MagicMock) -> None:
        """
        Given save_image_with_dialog returns (False, "Disk full"),
        When save_images is called,
        Then status message is "Disk full".
        """
        # Arrange
        method = _get_real_mainwindow_method("save_images")
        mock_save.return_value = (False, "Disk full")

        # Act
        method(mw)

        # Assert
        mw.status_handler.set_message.assert_called_with("Disk full")

    @patch("src.ui.main_window.save_image_with_dialog")
    def test_mode_update_called(self, mock_save: MagicMock, mw: MagicMock) -> None:
        """
        Given save_image_with_dialog is called,
        When save_images is called,
        Then _update_mode_from_state is called.
        """
        # Arrange
        method = _get_real_mainwindow_method("save_images")
        mock_save.return_value = (True, "")
        mw._update_mode_from_state = MagicMock()

        # Act
        method(mw)

        # Assert
        mw._update_mode_from_state.assert_called()


class TestResetToDefaults:
    """
    Test Design Specification: reset_to_defaults()
    Module under test: src/ui/main_window.py

    Contract:
        Resets state, clears viewer crop rects, resets all controller sliders,
        calls clear_autosave, shows status message. If crop_mode was active,
        restores crop button and hides controls first.

    Equivalence partitions:
        EP1  crop_mode = False → state.reset() called
        EP2  crop_mode = True  → crop UI restored before state.reset()
        EP3  crop rects cleared (both saved and current)
        EP4  all three controllers get reset_all_sliders called
        EP5  clear_autosave called
        EP6  status message shown
    """

    def test_reset_without_crop_mode(self, mw: MagicMock) -> None:
        """
        Given state.crop_mode = False,
        When reset_to_defaults is called,
        Then state.reset() is called.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False
        mw.state.reset = MagicMock()

        # Act
        method(mw)

        # Assert
        mw.state.reset.assert_called_once()

    def test_reset_with_crop_mode(self, mw: MagicMock) -> None:
        """
        Given state.crop_mode = True,
        When reset_to_defaults is called,
        Then crop button shown and controls hidden.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = True
        mw.state.reset = MagicMock()

        # Act
        method(mw)

        # Assert
        mw.crop_mode_btn.setVisible.assert_called_once_with(True)
        mw.crop_controls.setVisible.assert_called_once_with(False)
        mw.viewer.set_crop_mode.assert_called_once_with(False)

    def test_crop_rects_cleared(self, mw: MagicMock) -> None:
        """
        Given a mainwindow with viewer,
        When reset_to_defaults is called,
        Then both saved and current crop rects are cleared.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mw.viewer.set_saved_crop_rect.assert_called_once_with(None)
        mw.viewer.set_crop_rect.assert_called_once_with(None)

    def test_all_controllers_reset(self, mw: MagicMock) -> None:
        """
        Given three controllers,
        When reset_to_defaults is called,
        Then reset_all_sliders is called on each controller.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False
        mw.controllers = [MagicMock(), MagicMock(), MagicMock()]

        # Act
        method(mw)

        # Assert
        for controller in mw.controllers:
            controller.reset_all_sliders.assert_called_once()

    @patch("src.ui.main_window.clear_autosave")
    def test_clear_autosave_called(self, mock_clear_autosave: MagicMock, mw: MagicMock) -> None:
        """
        Given a mainwindow,
        When reset_to_defaults is called,
        Then clear_autosave is called.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mock_clear_autosave.assert_called_once_with(mw)

    def test_crop_controls_reset(self, mw: MagicMock) -> None:
        """
        Given crop_controls widget,
        When reset_to_defaults is called,
        Then reset() is called on crop_controls.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mw.crop_controls.reset.assert_called_once()

    def test_status_message_shown(self, mw: MagicMock) -> None:
        """
        Given a mainwindow,
        When reset_to_defaults is called,
        Then status message is set.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mw.status_handler.set_message.assert_called_once()

    def test_service_reset_called(self, mw: MagicMock) -> None:
        """
        EP7  svc.reset() is called so channel images are purged from memory.

        Given a mainwindow with a service that has loaded channel data,
        When reset_to_defaults is called,
        Then svc.reset() is called before any UI update so no stale image
        arrays remain accessible after the reset.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False

        # Act
        method(mw)

        # Assert
        mw.svc.reset.assert_called_once()

    def test_service_reset_called_before_state_reset(self, mw: MagicMock) -> None:
        """
        EP8  svc.reset() precedes state.reset() in the call sequence.

        Regression guard: the image data must be cleared before AppState is
        reset so that any state-dependent query on svc during the reset
        sequence observes an already-empty service.
        """
        # Arrange
        method = _get_real_mainwindow_method("reset_to_defaults")
        mw.state.crop_mode = False
        call_order: list[str] = []
        mw.svc.reset.side_effect = lambda: call_order.append("svc.reset")
        mw.state.reset = MagicMock(side_effect=lambda: call_order.append("state.reset"))

        # Act
        method(mw)

        # Assert
        assert call_order.index("svc.reset") < call_order.index("state.reset")
