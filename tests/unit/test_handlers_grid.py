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

"""
Unit tests for src.ui.handlers.grid module.

Tests grid settings dialog opening, grid type changes, and line width changes.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from src.ui.handlers.grid import on_grid_line_width_changed, on_grid_type_changed, open_grid_settings
from src.ui.widgets.grid_types import GRID_TYPE_3X3, GRID_TYPE_GOLDEN_RATIO, GRID_TYPE_NONE


@pytest.fixture
def mock_main_window() -> MagicMock:
    """Create a mock MainWindow with required attributes."""
    main_window = MagicMock()
    main_window.state = MagicMock()
    main_window.state.grid_settings_dialog = None
    main_window.viewer = MagicMock()
    main_window.viewer.grid_overlay = MagicMock()
    main_window.viewer.grid_overlay.get_line_width.return_value = 2
    main_window.viewer.grid_overlay.is_enabled.return_value = True
    main_window.viewer.grid_overlay.get_grid_type.return_value = GRID_TYPE_3X3
    main_window.viewer.viewport.return_value = MagicMock()
    main_window.grid_btn = MagicMock()
    main_window.grid_btn.width.return_value = 50
    main_window.grid_btn.height.return_value = 30
    main_window.status_handler = MagicMock()
    main_window.status_handler.SHORT_TIMEOUT = "short"
    main_window.GRID_TYPE_STATUS_MESSAGES = {
        GRID_TYPE_3X3: "3x3 grid overlay enabled",
        GRID_TYPE_GOLDEN_RATIO: "Golden ratio grid overlay enabled",
    }
    return main_window


class TestOpenGridSettings:
    """
    Test Design Specification: open_grid_settings()
    Module under test: src/ui/handlers/grid.py

    Contract:
        Opens the grid settings dialog near the grid button. If the dialog doesn't
        exist, creates it with current grid settings from the viewer, connects signals
        for grid type and line width changes, positions it near the button with screen
        boundary checks, shows it, and brings it to front. If dialog exists, just
        re-positions, shows, and raises it.

    Equivalence partitions:
        EP1  Dialog is None (first call)     → create, connect signals, position, show, raise
        EP2  Dialog exists (already created) → reuse dialog, position, show, raise
        EP3  Grid enabled, specific type     → current_type = grid_overlay.get_grid_type()
        EP4  Grid disabled                   → current_type = GRID_TYPE_NONE

    Boundary values:
        BV1  Line width = 1 (min)
        BV2  Line width = 10 (max)

    Mocking strategy:
        - GridSettingsDialog mocked to verify creation and signal connection
        - position_popup_near_button patched to verify it's called
        - Dialog signal emission tested via lambda
    """

    @patch("src.ui.handlers.grid.position_popup_near_button")
    @patch("src.ui.handlers.grid.GridSettingsDialog")
    def test_creates_dialog_when_none(
        self, mock_dialog_class: MagicMock, mock_position: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given main_window with no grid_settings_dialog,
        When open_grid_settings is called,
        Then GridSettingsDialog is created with current width and grid type.
        """
        mock_dialog_instance = MagicMock()
        mock_dialog_class.return_value = mock_dialog_instance
        mock_main_window.viewer.grid_overlay.is_enabled.return_value = True
        mock_main_window.viewer.grid_overlay.get_grid_type.return_value = GRID_TYPE_3X3
        mock_main_window.viewer.grid_overlay.get_line_width.return_value = 3

        open_grid_settings(mock_main_window)

        mock_dialog_class.assert_called_once_with(
            current_width=3, current_grid_type=GRID_TYPE_3X3, parent=mock_main_window
        )
        assert mock_main_window.state.grid_settings_dialog == mock_dialog_instance

    @patch("src.ui.handlers.grid.position_popup_near_button")
    @patch("src.ui.handlers.grid.GridSettingsDialog")
    def test_connects_grid_type_changed_signal(
        self, mock_dialog_class: MagicMock, mock_position: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given a newly created dialog,
        When open_grid_settings is called,
        Then grid_type_changed signal is connected to on_grid_type_changed handler.
        """
        mock_dialog_instance = MagicMock()
        mock_dialog_class.return_value = mock_dialog_instance

        open_grid_settings(mock_main_window)

        mock_dialog_instance.grid_type_changed.connect.assert_called_once()
        connect_call = mock_dialog_instance.grid_type_changed.connect.call_args
        handler = connect_call[0][0]
        handler(GRID_TYPE_GOLDEN_RATIO)
        mock_main_window.viewer.grid_overlay.set_grid_type.assert_called_with(GRID_TYPE_GOLDEN_RATIO)

    @patch("src.ui.handlers.grid.position_popup_near_button")
    @patch("src.ui.handlers.grid.GridSettingsDialog")
    def test_connects_line_width_changed_signal(
        self, mock_dialog_class: MagicMock, mock_position: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given a newly created dialog,
        When open_grid_settings is called,
        Then line_width_changed signal is connected to on_grid_line_width_changed handler.
        """
        mock_dialog_instance = MagicMock()
        mock_dialog_class.return_value = mock_dialog_instance

        open_grid_settings(mock_main_window)

        mock_dialog_instance.line_width_changed.connect.assert_called_once()
        connect_call = mock_dialog_instance.line_width_changed.connect.call_args
        handler = connect_call[0][0]
        handler(5)
        mock_main_window.viewer.grid_overlay.set_line_width.assert_called_with(5)

    @patch("src.ui.handlers.grid.position_popup_near_button")
    @patch("src.ui.handlers.grid.GridSettingsDialog")
    def test_positions_dialog_near_button(
        self, mock_dialog_class: MagicMock, mock_position: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given a main_window with grid_btn,
        When open_grid_settings is called,
        Then position_popup_near_button is called with dialog and button.
        """
        mock_dialog_instance = MagicMock()
        mock_dialog_class.return_value = mock_dialog_instance

        open_grid_settings(mock_main_window)

        mock_position.assert_called_once_with(mock_dialog_instance, mock_main_window.grid_btn)

    @patch("src.ui.handlers.grid.position_popup_near_button")
    @patch("src.ui.handlers.grid.GridSettingsDialog")
    def test_shows_and_raises_dialog(
        self, mock_dialog_class: MagicMock, mock_position: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given a main_window with grid_btn,
        When open_grid_settings is called,
        Then dialog is shown and raised to front.
        """
        mock_dialog_instance = MagicMock()
        mock_dialog_class.return_value = mock_dialog_instance

        open_grid_settings(mock_main_window)

        mock_dialog_instance.show.assert_called_once()
        mock_dialog_instance.raise_.assert_called_once()

    @patch("src.ui.handlers.grid.position_popup_near_button")
    @patch("src.ui.handlers.grid.GridSettingsDialog")
    def test_uses_grid_type_none_when_disabled(
        self, mock_dialog_class: MagicMock, mock_position: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given grid overlay is disabled,
        When open_grid_settings is called,
        Then GridSettingsDialog is created with GRID_TYPE_NONE.
        """
        mock_dialog_instance = MagicMock()
        mock_dialog_class.return_value = mock_dialog_instance
        mock_main_window.viewer.grid_overlay.is_enabled.return_value = False

        open_grid_settings(mock_main_window)

        call_kwargs = mock_dialog_class.call_args[1]
        assert call_kwargs["current_grid_type"] == GRID_TYPE_NONE

    @patch("src.ui.handlers.grid.position_popup_near_button")
    def test_reuses_existing_dialog(self, mock_position: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given main_window with existing grid_settings_dialog,
        When open_grid_settings is called,
        Then GridSettingsDialog is reused (not recreated).
        """
        existing_dialog = MagicMock()
        mock_main_window.state.grid_settings_dialog = existing_dialog

        open_grid_settings(mock_main_window)

        assert mock_main_window.state.grid_settings_dialog == existing_dialog
        mock_position.assert_called_once_with(existing_dialog, mock_main_window.grid_btn)


class TestOnGridTypeChanged:
    """
    Test Design Specification: on_grid_type_changed()
    Module under test: src/ui/handlers/grid.py

    Contract:
        Handles grid type selection change. Disables overlay for GRID_TYPE_NONE,
        enables overlay and sets type for valid types, shows error for invalid types.
        Updates status message and refreshes viewport.

    Equivalence partitions:
        EP1  grid_type = GRID_TYPE_NONE              → disable overlay, show disabled message
        EP2  grid_type = valid (3x3, golden, etc.)   → enable overlay, set type, show type message
        EP3  grid_type = unsupported (not in dict)   → disable overlay, show unsupported message
        EP4  grid_type = invalid (raises ValueError) → disable overlay, show unsupported message

    Boundary values:
        BV1  First valid type (3x3)
        BV2  Last valid type (diagonal + golden)
    """

    def test_disables_overlay_for_none_type(self, mock_main_window: MagicMock) -> None:
        """
        Given grid_type = GRID_TYPE_NONE,
        When on_grid_type_changed is called,
        Then grid overlay is disabled and appropriate message is shown.
        """
        on_grid_type_changed(mock_main_window, GRID_TYPE_NONE)

        mock_main_window.viewer.grid_overlay.set_enabled.assert_called_with(False)
        mock_main_window.status_handler.set_message.assert_called_with(
            "Grid overlay disabled", mock_main_window.status_handler.SHORT_TIMEOUT
        )

    def test_enables_overlay_for_valid_type(self, mock_main_window: MagicMock) -> None:
        """
        Given grid_type = GRID_TYPE_3X3,
        When on_grid_type_changed is called,
        Then grid overlay is enabled, type is set, and status message is shown.
        """
        on_grid_type_changed(mock_main_window, GRID_TYPE_3X3)

        assert mock_main_window.viewer.grid_overlay.set_enabled.call_args_list[0] == call(True)
        mock_main_window.viewer.grid_overlay.set_grid_type.assert_called_with(GRID_TYPE_3X3)
        mock_main_window.status_handler.set_message.assert_called_with(
            "3x3 grid overlay enabled", mock_main_window.status_handler.SHORT_TIMEOUT
        )

    def test_shows_error_for_unsupported_type(self, mock_main_window: MagicMock) -> None:
        """
        Given grid_type = unsupported type (not in GRID_TYPE_STATUS_MESSAGES),
        When on_grid_type_changed is called,
        Then grid overlay is disabled and error message is shown.
        """
        unsupported_type = "UNSUPPORTED_TYPE"
        on_grid_type_changed(mock_main_window, unsupported_type)

        mock_main_window.viewer.grid_overlay.set_enabled.assert_called_with(False)
        mock_main_window.status_handler.set_message.assert_called_with(
            "Unsupported grid type selected", mock_main_window.status_handler.SHORT_TIMEOUT
        )

    def test_handles_invalid_type_exception(self, mock_main_window: MagicMock) -> None:
        """
        Given set_grid_type raises ValueError,
        When on_grid_type_changed is called,
        Then grid overlay is disabled and error message is shown.
        """
        mock_main_window.viewer.grid_overlay.set_grid_type.side_effect = ValueError("Invalid type")

        on_grid_type_changed(mock_main_window, GRID_TYPE_3X3)

        mock_main_window.viewer.grid_overlay.set_enabled.assert_called_with(False)
        mock_main_window.status_handler.set_message.assert_called_with(
            "Unsupported grid type selected", mock_main_window.status_handler.SHORT_TIMEOUT
        )

    def test_updates_viewport_after_type_change(self, mock_main_window: MagicMock) -> None:
        """
        Given any grid type change,
        When on_grid_type_changed is called,
        Then viewport is updated to reflect changes.
        """
        on_grid_type_changed(mock_main_window, GRID_TYPE_3X3)

        mock_main_window.viewer.viewport().update.assert_called()

    def test_multiple_valid_types(self, mock_main_window: MagicMock) -> None:
        """
        Given multiple valid grid types in GRID_TYPE_STATUS_MESSAGES,
        When on_grid_type_changed is called with each,
        Then each type is set correctly with appropriate status message.
        """
        for grid_type, expected_message in mock_main_window.GRID_TYPE_STATUS_MESSAGES.items():
            mock_main_window.reset_mock()

            on_grid_type_changed(mock_main_window, grid_type)

            mock_main_window.viewer.grid_overlay.set_grid_type.assert_called_with(grid_type)
            mock_main_window.status_handler.set_message.assert_called_with(
                expected_message, mock_main_window.status_handler.SHORT_TIMEOUT
            )


class TestOnGridLineWidthChanged:
    """
    Test Design Specification: on_grid_line_width_changed()
    Module under test: src/ui/handlers/grid.py

    Contract:
        Updates grid overlay line width and displays a status message. Refreshes
        viewport to show changes. Takes main_window and width in pixels.

    Equivalence partitions:
        EP1  width = 1 (minimum)
        EP2  width = 5 (typical)
        EP3  width = 10 (maximum)

    Boundary values:
        BV1  width = 0 (invalid but allowed)
        BV2  width = 1 (minimum valid)
        BV3  width = 10 (maximum valid)
    """

    def test_updates_grid_line_width(self, mock_main_window: MagicMock) -> None:
        """
        Given width = 5,
        When on_grid_line_width_changed is called,
        Then grid overlay line width is set to 5.
        """
        on_grid_line_width_changed(mock_main_window, 5)

        mock_main_window.viewer.grid_overlay.set_line_width.assert_called_with(5)

    def test_shows_status_message_with_width(self, mock_main_window: MagicMock) -> None:
        """
        Given width = 3,
        When on_grid_line_width_changed is called,
        Then status message displays "Grid line width: 3px".
        """
        on_grid_line_width_changed(mock_main_window, 3)

        mock_main_window.status_handler.set_message.assert_called_with(
            "Grid line width: 3px", mock_main_window.status_handler.SHORT_TIMEOUT
        )

    def test_updates_viewport_after_width_change(self, mock_main_window: MagicMock) -> None:
        """
        Given any line width change,
        When on_grid_line_width_changed is called,
        Then viewport is updated.
        """
        on_grid_line_width_changed(mock_main_window, 5)

        mock_main_window.viewer.viewport().update.assert_called()

    def test_minimum_width(self, mock_main_window: MagicMock) -> None:
        """
        Given width = 1 (minimum),
        When on_grid_line_width_changed is called,
        Then line width is set and status message is shown.
        """
        on_grid_line_width_changed(mock_main_window, 1)

        mock_main_window.viewer.grid_overlay.set_line_width.assert_called_with(1)
        mock_main_window.status_handler.set_message.assert_called_with(
            "Grid line width: 1px", mock_main_window.status_handler.SHORT_TIMEOUT
        )

    def test_maximum_width(self, mock_main_window: MagicMock) -> None:
        """
        Given width = 10 (maximum),
        When on_grid_line_width_changed is called,
        Then line width is set and status message is shown.
        """
        on_grid_line_width_changed(mock_main_window, 10)

        mock_main_window.viewer.grid_overlay.set_line_width.assert_called_with(10)
        mock_main_window.status_handler.set_message.assert_called_with(
            "Grid line width: 10px", mock_main_window.status_handler.SHORT_TIMEOUT
        )
