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

from unittest.mock import MagicMock, patch

import pytest

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
    """
    Test Design Specification: handle_key_press() - channel switching keys
    Module under test: src/ui/handlers/keyboard.py

    Contract:
        Handler for key press events. Detects channel switching keys (1, 2, 3)
        and combined view key (A). For each handled key: sets show_combined=False
        (or True for A), sets current_channel to index, displays status message,
        updates display, accepts event, returns True. For unhandled keys: returns
        False without state changes.

    Equivalence partitions:
        EP1  Key=1 (Qt.Key_1)       → show_combined=False, current_channel=0, status "Red"
        EP2  Key=2 (Qt.Key_2)       → show_combined=False, current_channel=1, status "Green"
        EP3  Key=3 (Qt.Key_3)       → show_combined=False, current_channel=2, status "Blue"
        EP4  Key=A (Qt.Key_A)       → show_combined=True, status "combined", returns True
        EP5  Other keys (B, Esc)    → returns False, no state change

    Boundary values:
        BV1  key=49 (Qt.Key_1 code)
        BV2  key=50 (Qt.Key_2 code)
        BV3  key=51 (Qt.Key_3 code)
        BV4  key=65 (Qt.Key_A code)
        BV5  key=66 (Qt.Key_B code, unhandled)
        BV6  key=16777216 (Qt.Key_Escape, unhandled)

    Exclusions:
        - Key code validation (uses Qt constants as-is)
        - Qt event loop behavior
        - Display rendering (mocked update_main_display)

    Constraints:
        - Requires mocking: update_main_display()
        - Qt key codes from MockQt.Key class
        - Status timeout = status_handler.MEDIUM_TIMEOUT
        - event.accept() called for handled keys
        - event.key() method exists on mock
    """

    def test_key_1_switches_to_red_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given key 1 is pressed, when handle_key_press is called, then show_combined is False and current_channel is 0."""
        # Arrange
        mock_key_event.key.return_value = 49  # Qt.Key.Key_1

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert result is True
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 0
        mock_key_event.accept.assert_called_once()

    def test_key_2_switches_to_green_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given key 2 is pressed, when handle_key_press is called, then show_combined is False and current_channel is 1."""
        # Arrange
        mock_key_event.key.return_value = 50  # Qt.Key.Key_2

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert result is True
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 1
        mock_key_event.accept.assert_called_once()

    def test_key_3_switches_to_blue_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given key 3 is pressed, when handle_key_press is called, then show_combined is False and current_channel is 2."""
        # Arrange
        mock_key_event.key.return_value = 51  # Qt.Key.Key_3

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert result is True
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 2
        mock_key_event.accept.assert_called_once()

    def test_channel_key_sets_status_message(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given a channel key is pressed, when handle_key_press is called, then status message includes channel name."""
        # Arrange
        mock_key_event.key.return_value = 49  # Qt.Key.Key_1

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "Red" in call_args[0]

    def test_channel_key_updates_display(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given a channel key is pressed, when handle_key_press is called, then update_main_display is called."""
        # Arrange
        mock_key_event.key.return_value = 50  # Qt.Key.Key_2

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display") as mock_display:
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        mock_display.assert_called_once_with(mock_main_window)

    def test_all_channel_keys_set_correct_messages(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given varying channel keys (1, 2, 3), when handle_key_press is called, then correct message is set for each."""
        # Arrange
        messages = {
            49: "Red",      # Key_1
            50: "Green",    # Key_2
            51: "Blue",     # Key_3
        }

        # Act & Assert
        for key_code, expected_color in messages.items():
            mock_key_event.key.return_value = key_code
            mock_main_window.status_handler.reset_mock()

            with patch("src.ui.handlers.keyboard.update_main_display"):
                handle_key_press(mock_main_window, mock_key_event)

            call_args = mock_main_window.status_handler.set_message.call_args[0]
            assert expected_color in call_args[0]


class TestHandleKeyPressCombinedView:
    """
    Test Design Specification: handle_key_press() - combined view key A
    Module under test: src/ui/handlers/keyboard.py

    Contract:
        Handles key A for combined RGB view. Sets show_combined=True (idempotent),
        does not modify current_channel, displays status message, accepts event,
        returns True. Works from any prior state (single or already combined).

    Equivalence partitions:
        EP1  show_combined=False -> True       → transition to combined
        EP2  show_combined=True -> True        → already combined (no-op)
        EP3  current_channel preserved         → unchanged from any prior state

    Boundary values:
        BV1  key=65 (Qt.Key_A code)
        BV2  show_combined False->True (edge transition)
        BV3  current_channel any value (0, 1, 2)

    Exclusions:
        - current_channel validation
        - status message wording details
        - Display rendering

    Constraints:
        - Requires mocking: update_main_display()
        - Sets status message with "combined" keyword
        - event.accept() called
        - Returns True
    """

    def test_key_a_shows_combined_view(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given key A is pressed from single channel view, when handle_key_press is called, then show_combined is True."""
        # Arrange
        mock_main_window.state.show_combined = False
        mock_main_window.state.current_channel = 1
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert result is True
        assert mock_main_window.state.show_combined is True
        mock_key_event.accept.assert_called_once()

    def test_key_a_sets_status_message(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given key A is pressed, when handle_key_press is called, then status message includes "combined"."""
        # Arrange
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "combined" in call_args[0].lower()

    def test_key_a_updates_display(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given key A is pressed, when handle_key_press is called, then update_main_display is called."""
        # Arrange
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display") as mock_display:
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        mock_display.assert_called_once_with(mock_main_window)

    def test_key_a_from_single_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given single channel view is active, when key A is pressed, then show_combined becomes True and current_channel unchanged."""
        # Arrange
        mock_main_window.state.show_combined = False
        mock_main_window.state.current_channel = 2
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert result is True
        assert mock_main_window.state.show_combined is True
        assert mock_main_window.state.current_channel == 2

    def test_key_a_when_already_in_combined_view(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given already in combined view, when key A is pressed, then show_combined remains True (idempotent)."""
        # Arrange
        mock_main_window.state.show_combined = True
        mock_main_window.state.current_channel = 0
        mock_key_event.key.return_value = 65  # Qt.Key.Key_A

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            result = handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert result is True
        assert mock_main_window.state.show_combined is True
        assert mock_main_window.state.current_channel == 0
        mock_key_event.accept.assert_called_once()


class TestHandleKeyPressUnhandledKeys:
    """
    Test Design Specification: handle_key_press() - unhandled key behavior
    Module under test: src/ui/handlers/keyboard.py

    Contract:
        For keys not in {1, 2, 3, A}: returns False without accepting event,
        without modifying state, without setting status messages. Allows event
        propagation to parent handlers.

    Equivalence partitions:
        EP1  Alphanumeric keys (B, C, ...)    → returns False
        EP2  Special keys (Escape, Enter, ...) → returns False
        EP3  All unhandled keys               → no side effects

    Boundary values:
        BV1  key=66 (Qt.Key_B)
        BV2  key=16777216 (Qt.Key_Escape)

    Exclusions:
        - Specific unhandled key enumeration (only show representative)
        - Qt event propagation mechanics

    Constraints:
        - Requires: no mocking for unhandled keys
        - Verifies: event.accept() NOT called
        - Verifies: status_handler.set_message() NOT called
        - Verifies: state unchanged (show_combined, current_channel)
    """

    def test_unhandled_key_returns_false(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given an unhandled key is pressed, when handle_key_press is called, then False is returned."""
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        result = handle_key_press(mock_main_window, mock_key_event)

        assert result is False

    def test_unhandled_key_does_not_accept_event(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given an unhandled key is pressed, when handle_key_press is called, then event.accept is not called."""
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        handle_key_press(mock_main_window, mock_key_event)

        mock_key_event.accept.assert_not_called()

    def test_unhandled_key_does_not_modify_state(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given an unhandled key is pressed, when handle_key_press is called, then application state is unchanged."""
        # Arrange
        original_combined = mock_main_window.state.show_combined
        original_channel = mock_main_window.state.current_channel
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        # Act
        handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert mock_main_window.state.show_combined == original_combined
        assert mock_main_window.state.current_channel == original_channel

    def test_unhandled_key_does_not_set_message(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given an unhandled key is pressed, when handle_key_press is called, then status message is not set."""
        mock_key_event.key.return_value = 66  # Qt.Key.Key_B

        handle_key_press(mock_main_window, mock_key_event)

        mock_main_window.status_handler.set_message.assert_not_called()

    def test_escape_key_unhandled(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given Escape key is pressed, when handle_key_press is called, then False is returned."""
        mock_key_event.key.return_value = 16777216  # Qt.Key.Key_Escape

        result = handle_key_press(mock_main_window, mock_key_event)

        assert result is False


class TestHandleKeyPressStatusMessages:
    """
    Test Design Specification: handle_key_press() - status message behavior
    Module under test: src/ui/handlers/keyboard.py

    Contract:
        All handled keys (1, 2, 3, A) produce status messages with consistent
        timeout value (MEDIUM_TIMEOUT). Messages include descriptive text
        (channel name or "combined").

    Equivalence partitions:
        EP1  Key 1, 2, 3 (channel keys)    → message includes "Red"/"Green"/"Blue"
        EP2  Key A (combined key)          → message includes "combined"
        EP3  All keys use MEDIUM_TIMEOUT   → timeout param = status_handler.MEDIUM_TIMEOUT

    Boundary values:
        BV1  timeout = "medium" constant
        BV2  message length varies by channel

    Exclusions:
        - Exact message wording validation
        - Timeout implementation details

    Constraints:
        - Requires mocking: update_main_display(), status_handler.set_message()
        - All handled keys pass 2-tuple to set_message: (message, timeout)
        - Timeout must equal status_handler.MEDIUM_TIMEOUT
    """

    def test_status_message_includes_timeout(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given a handled key is pressed, when handle_key_press is called, then status message includes timeout."""
        # Arrange
        mock_key_event.key.return_value = 49  # Qt.Key.Key_1

        # Act
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert len(call_args) == 2
        assert call_args[1] == "medium"

    def test_all_handlers_use_medium_timeout(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given varying handled keys (1, 2, 3, A), when handle_key_press is called, then all use MEDIUM_TIMEOUT."""
        # Arrange
        keys_to_test = [49, 50, 51, 65]  # Keys 1, 2, 3, A

        # Act & Assert
        for key_code in keys_to_test:
            mock_key_event.key.return_value = key_code
            mock_main_window.status_handler.reset_mock()

            with patch("src.ui.handlers.keyboard.update_main_display"):
                handle_key_press(mock_main_window, mock_key_event)

            call_args = mock_main_window.status_handler.set_message.call_args[0]
            assert call_args[1] == "medium"


class TestHandleKeyPressSequential:
    """
    Test Design Specification: handle_key_press() - sequential key sequences
    Module under test: src/ui/handlers/keyboard.py

    Contract:
        Handler manages state correctly across multiple sequential key presses.
        Each call independently sets state and updates display. State transitions
        are idempotent and composable (channel->combined->channel work correctly).

    Equivalence partitions:
        EP1  Sequential channel keys (1->2->3)    → each sets correct index
        EP2  Channel to combined to channel        → transitions preserve correctness
        EP3  Multiple combined presses             → idempotent (show_combined stays True)
        EP4  State from any prior key              → independent handling

    Boundary values:
        BV1  First key press (initial state)
        BV2  Consecutive same key (idempotent)
        BV3  All three channels in sequence
        BV4  Alternating channel and combined

    Exclusions:
        - Key code enumeration (uses representative subset)
        - Display rendering
        - State persistence beyond handler call

    Constraints:
        - Requires mocking: update_main_display()
        - Each call is stateless with respect to prior calls
        - mock_main_window state mutated by each call
        - event.accept() called for all handled keys
    """

    def test_sequential_channel_switches(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given sequential channel keys (1, 2, 3) are pressed, when handle_key_press is called for each, then state updates correctly."""
        # Arrange
        channels = [49, 50, 51]  # Keys 1, 2, 3

        # Act & Assert
        for i, key_code in enumerate(channels):
            mock_key_event.key.return_value = key_code

            with patch("src.ui.handlers.keyboard.update_main_display"):
                result = handle_key_press(mock_main_window, mock_key_event)

            assert result is True
            assert mock_main_window.state.current_channel == i

    def test_channel_to_combined_to_channel(self, mock_main_window: MagicMock, mock_key_event: MagicMock) -> None:
        """Given channel, combined, and channel keys are pressed in sequence, when handle_key_press is called for each, then view toggles correctly."""
        # Arrange
        # Start with channel 0
        mock_key_event.key.return_value = 49

        # Act: First key press (channel 0)
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert mock_main_window.state.show_combined is False

        # Act: Switch to combined
        mock_key_event.key.return_value = 65
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert mock_main_window.state.show_combined is True

        # Act: Switch to channel 2
        mock_key_event.key.return_value = 51
        with patch("src.ui.handlers.keyboard.update_main_display"):
            handle_key_press(mock_main_window, mock_key_event)

        # Assert
        assert mock_main_window.state.show_combined is False
        assert mock_main_window.state.current_channel == 2
