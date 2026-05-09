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
Unit tests for src.ui.handlers.keyboard module.

Tests keyboard event handling for channel switching and display modes.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock PyQt5 before importing Qt-dependent modules
sys.modules["PyQt5"] = MagicMock()
sys.modules["PyQt5.QtCore"] = MagicMock()
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()

# Set up Qt constants
class MockQt:
    """Mock Qt enum for key codes."""

    class Key:
        """Mock Qt.Key enum with key code constants."""

        Key_1 = 49
        Key_2 = 50
        Key_3 = 51
        Key_A = 65
        Key_B = 66
        Key_Escape = 16777216

sys.modules["PyQt5.QtCore"].Qt = MockQt()

from src.ui.handlers.keyboard import handle_key_press


@pytest.fixture
def mock_main_window() -> MagicMock:
    """Create a mock MainWindow with required attributes."""
    main_window = MagicMock()
    main_window.state = MagicMock()
    main_window.state.show_combined = True
    main_window.state.current_channel = 0
    main_window.status_handler = MagicMock()
    main_window.status_handler.MEDIUM_TIMEOUT = "medium"
    return main_window


@pytest.fixture
def mock_key_event() -> MagicMock:
    """Create a mock QKeyEvent."""
    return MagicMock()


class TestHandleKeyPressChannelSwitching:
    """Tests for channel switching key handlers (1, 2, 3)."""

    def test_key_1_switches_to_red_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify key 1 switches to Red channel (index 0)."""
        mock_key_event.key.return_value = 49  # Qt.Key.Key_1

        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        assert result is True
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 0
        mock_key_event.accept.assert_called_once()

    def test_key_2_switches_to_green_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify key 2 switches to Green channel (index 1)."""
        mock_key_event.key.return_value = 50  # Qt.Key.Key_2

        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        assert result is True
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 1
        mock_key_event.accept.assert_called_once()

    def test_key_3_switches_to_blue_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify key 3 switches to Blue channel (index 2)."""
        mock_key_event.key.return_value = 51  # Qt.Key.Key_3

        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        assert result is True
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 2
        mock_key_event.accept.assert_called_once()

    def test_channel_key_sets_status_message(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify channel switch sets appropriate status message."""
        mock_key_event.key.return_value = 49  # Qt.Key.Key_1

        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "Red" in call_args[0]

    def test_channel_key_updates_display(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify channel switch updates main display."""
        mock_key_event.key.return_value = 50  # Qt.Key.Key_2

        with patch("src.ui.handlers.keyboard.update_main_display") as mock_display:
            handle_key_press(mock_main_window, mock_key_event)

        mock_display.assert_called_once_with(mock_main_window)

    def test_all_channel_keys_set_correct_messages(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify each channel key sets the correct message."""
        messages = {
            49: "Red",      # Key_1
            50: "Green",    # Key_2
            51: "Blue",     # Key_3
        }

        for key_code, expected_color in messages.items():
            mock_key_event.key.return_value = key_code
            mock_main_window.status_handler.reset_mock()

            with patch("src.ui.handlers.keyboard.update_main_display"):
                handle_key_press(mock_main_window, mock_key_event)

            call_args = mock_main_window.status_handler.set_message.call_args[0]
            assert expected_color in call_args[0]


class TestHandleKeyPressCombinedView:
    """Tests for combined view key handler (A)."""

    def test_key_a_shows_combined_view(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify key A shows combined RGB view."""
        mock_main_window.state.show_combined = False
        mock_main_window.state.current_channel = 1
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        assert result is True
        assert mock_main_window.state.show_combined is True
        mock_key_event.accept.assert_called_once()

    def test_key_a_sets_status_message(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify key A sets combined view status message."""
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "combined" in call_args[0].lower()

    def test_key_a_updates_display(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify key A updates main display."""
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        with patch("src.ui.handlers.keyboard.update_main_display") as mock_display:
            handle_key_press(mock_main_window, mock_key_event)

        mock_display.assert_called_once_with(mock_main_window)

    def test_key_a_from_single_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify key A switches from single channel to combined."""
        mock_main_window.state.show_combined = False
        mock_main_window.state.current_channel = 2
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        assert result is True
        assert mock_main_window.state.show_combined is True
        # current_channel is not modified by key A
        assert mock_main_window.state.current_channel == 2

    def test_key_a_when_already_in_combined_view(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify pressing 'A' when already in combined view remains in combined (no-op)."""
        mock_main_window.state.show_combined = True
        mock_main_window.state.current_channel = 0
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        assert result is True
        assert mock_main_window.state.show_combined is True
        # current_channel remains unchanged
        assert mock_main_window.state.current_channel == 0
        # Event is still accepted
        mock_key_event.accept.assert_called_once()


class TestHandleKeyPressUnhandledKeys:
    """Tests for unhandled key behavior."""

    def test_unhandled_key_returns_false(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify unhandled keys return False."""
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        result = handle_key_press(mock_main_window, mock_key_event)

        assert result is False

    def test_unhandled_key_does_not_accept_event(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify unhandled keys do not accept the event."""
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        handle_key_press(mock_main_window, mock_key_event)

        mock_key_event.accept.assert_not_called()

    def test_unhandled_key_does_not_modify_state(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify unhandled keys do not modify application state."""
        original_combined = mock_main_window.state.show_combined
        original_channel = mock_main_window.state.current_channel
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        handle_key_press(mock_main_window, mock_key_event)

        assert mock_main_window.state.show_combined == original_combined
        assert mock_main_window.state.current_channel == original_channel

    def test_unhandled_key_does_not_set_message(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify unhandled keys do not set status messages."""
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        handle_key_press(mock_main_window, mock_key_event)

        mock_main_window.status_handler.set_message.assert_not_called()

    def test_escape_key_unhandled(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify Escape key is not handled."""
        mock_key_event.key.return_value = 16777216  # Qt.Key.Key_Escape

        result = handle_key_press(mock_main_window, mock_key_event)

        assert result is False


class TestHandleKeyPressStatusMessages:
    """Tests for status message behavior."""

    def test_status_message_includes_timeout(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify status messages include timeout parameter."""
        mock_key_event.key.return_value = 49  # Qt.Key.Key_1

        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert len(call_args) == 2
        assert call_args[1] == "medium"

    def test_all_handlers_use_medium_timeout(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify all key handlers use MEDIUM_TIMEOUT."""
        keys_to_test = [49, 50, 51, 65]  # Keys 1, 2, 3, A

        for key_code in keys_to_test:
            mock_key_event.key.return_value = key_code
            mock_main_window.status_handler.reset_mock()

            with patch("src.ui.handlers.keyboard.update_main_display"):
                handle_key_press(mock_main_window, mock_key_event)

            call_args = mock_main_window.status_handler.set_message.call_args[0]
            assert call_args[1] == "medium"


class TestHandleKeyPressSequential:
    """Tests for sequential key presses."""

    def test_sequential_channel_switches(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify sequential channel switches update state correctly."""
        channels = [49, 50, 51]  # Keys 1, 2, 3

        for i, key_code in enumerate(channels):
            mock_key_event.key.return_value = key_code

            with patch("src.ui.handlers.keyboard.update_main_display"):
                result = handle_key_press(mock_main_window, mock_key_event)

            assert result is True
            assert mock_main_window.state.current_channel == i

    def test_channel_to_combined_to_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Verify switching between single and combined views."""
        # Start with channel 0
        mock_key_event.key.return_value = 49
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)
        assert mock_main_window.state.show_combined is False

        # Switch to combined
        mock_key_event.key.return_value = 65
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)
        assert mock_main_window.state.show_combined is True

        # Switch to channel 2
        mock_key_event.key.return_value = 51
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 2
