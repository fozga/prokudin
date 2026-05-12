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

"""Widget tests for src/ui/widgets/status_bar.py."""

import pytest
from PyQt5.QtWidgets import QStatusBar
from pytestqt.plugin import QtBot

from src.ui.widgets.status_bar import StatusBarHandler


@pytest.mark.widget
class TestStatusBarHandler:
    """
    Test Design Specification: StatusBarHandler
    Module under test: src/ui/widgets/status_bar.py

    Widget base class: QObject (wraps QStatusBar; not a widget itself)

    Contract:
        StatusBarHandler manages a QStatusBar instance owned by the caller.
        On construction it disables the size grip, installs a permanent mode
        label (QLabel) with text "Load images", and sets an initial "Ready"
        status message.  Three public methods complete the API:
          - set_message(message, timeout) — forwards to QStatusBar.showMessage.
          - set_mode(mode) — sets the text of the permanent mode label.
          - update_mode_from_state(loaded_channels, crop_mode, saving) —
            resolves the correct mode string from application state and
            delegates to set_mode.  Priority: saving > crop_mode > channel count.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - QStatusBar is registered with qtbot.addWidget; StatusBarHandler
          is a QObject and does not need separate registration.
        - No file IO or external services.

    What is tested:
        - Initialization: size grip disabled, mode label text, initial message.
        - set_message: message visible via QStatusBar.currentMessage().
        - set_message with empty string, with timeout constant, with long text.
        - set_mode: mode label text updated to the supplied string.
        - update_mode_from_state: all four outcome branches (saving, cropping,
          load images, editing) and saving-over-crop priority.
        - Boundary values for loaded_channels threshold (2 vs 3).

    What is NOT tested:
        - Visual appearance, colours, pixel positions, font sizes.
        - QPainter or rendering output.
        - Actual timer expiry after a finite timeout (Qt-internal behaviour).
        - QStatusBar size-grip visual handle geometry.

    Equivalence partitions:
        EP1  saving=True               → mode "Saving" (any channel count)
        EP2  crop_mode=True, no save   → mode "Cropping"
        EP3  loaded_channels < 3       → mode "Load images"
        EP4  loaded_channels >= 3      → mode "Editing"
        EP5  saving=True, crop_mode=True → mode "Saving" (saving wins)

    Boundary values:
        BV1  loaded_channels=2  (one below threshold, still "Load images")
        BV2  loaded_channels=3  (at threshold, first value for "Editing")
        BV3  loaded_channels=0  (minimum realistic count)

    Mocking strategy:
        No external dependencies require mocking.

    Constraints:
        - StatusBarHandler is a QObject, not a QWidget; only the wrapped
          QStatusBar is registered with qtbot.addWidget.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_handler(self, qtbot: QtBot) -> tuple[StatusBarHandler, QStatusBar]:
        """Create a fresh StatusBarHandler with its QStatusBar registered in qtbot."""
        status_bar = QStatusBar()
        qtbot.addWidget(status_bar)
        handler = StatusBarHandler(status_bar)
        return handler, status_bar

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def test_initialization_creates_handler_without_error(self, qtbot: QtBot) -> None:
        """
        Given a QStatusBar,
        When StatusBarHandler is instantiated,
        Then the handler is created without raising an exception.
        """
        # Arrange
        status_bar = QStatusBar()
        qtbot.addWidget(status_bar)
        # Act + Assert
        handler = StatusBarHandler(status_bar)
        assert handler is not None

    def test_initialization_disables_size_grip(self, qtbot: QtBot) -> None:
        """
        Given a QStatusBar with a size grip enabled by default,
        When StatusBarHandler is instantiated,
        Then the size grip is disabled.
        """
        # Arrange
        status_bar = QStatusBar()
        qtbot.addWidget(status_bar)
        # Act
        StatusBarHandler(status_bar)
        # Assert
        assert status_bar.isSizeGripEnabled() is False

    def test_initialization_mode_label_text_is_load_images(self, qtbot: QtBot) -> None:
        """
        Given a QStatusBar,
        When StatusBarHandler is instantiated,
        Then the mode label is created with text "Load images".
        """
        # Arrange + Act
        handler, _ = self._make_handler(qtbot)
        # Assert
        assert handler.mode_label.text() == "Load images"

    def test_initialization_sets_ready_status_message(self, qtbot: QtBot) -> None:
        """
        Given a QStatusBar,
        When StatusBarHandler is instantiated,
        Then the status bar displays a message that contains "Ready".
        """
        # Arrange + Act
        _, status_bar = self._make_handler(qtbot)
        # Assert
        assert "Ready" in status_bar.currentMessage()

    # ------------------------------------------------------------------
    # set_message
    # ------------------------------------------------------------------

    def test_set_message_displays_text_in_status_bar(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler,
        When set_message is called with a non-empty string,
        Then QStatusBar.currentMessage returns that string.
        """
        # Arrange
        handler, status_bar = self._make_handler(qtbot)
        # Act
        handler.set_message("Processing complete")
        # Assert
        assert status_bar.currentMessage() == "Processing complete"

    def test_set_message_with_empty_string_stores_empty_message(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler showing a non-empty message,
        When set_message is called with an empty string,
        Then QStatusBar.currentMessage returns an empty string.
        """
        # Arrange
        handler, status_bar = self._make_handler(qtbot)
        handler.set_message("Some message")
        # Act
        handler.set_message("")
        # Assert
        assert status_bar.currentMessage() == ""

    def test_set_message_with_short_timeout_does_not_crash(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler,
        When set_message is called with SHORT_TIMEOUT,
        Then the message is displayed without raising an exception.
        """
        # Arrange
        handler, status_bar = self._make_handler(qtbot)
        # Act
        handler.set_message("Temporary", StatusBarHandler.SHORT_TIMEOUT)
        # Assert
        assert status_bar.currentMessage() == "Temporary"

    def test_set_message_with_long_text_does_not_crash(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler,
        When set_message is called with a 1000-character string,
        Then the message is displayed without raising an exception.
        """
        # Arrange
        handler, status_bar = self._make_handler(qtbot)
        long_text = "A" * 1000
        # Act
        handler.set_message(long_text)
        # Assert
        assert status_bar.currentMessage() == long_text

    # ------------------------------------------------------------------
    # set_mode
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "mode",
        [
            "Editing",     # EP4: all channels loaded
            "Cropping",    # EP2: crop mode active
            "Saving",      # EP1: saving in progress
            "Load images", # EP3: waiting for channel load
            "",            # empty string: mode cleared
        ],
        ids=["editing", "cropping", "saving", "load_images", "empty"],
    )
    def test_set_mode_updates_mode_label_text(self, qtbot: QtBot, mode: str) -> None:
        """
        Given a StatusBarHandler with its default mode label,
        When set_mode is called with a mode string,
        Then the mode label text equals the supplied string.
        """
        # Arrange
        handler, _ = self._make_handler(qtbot)
        # Act
        handler.set_mode(mode)
        # Assert
        assert handler.mode_label.text() == mode

    # ------------------------------------------------------------------
    # update_mode_from_state
    # ------------------------------------------------------------------

    def test_update_mode_from_state_saving_sets_saving_mode(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler and saving=True,
        When update_mode_from_state is called,
        Then the mode label shows "Saving".
        """
        # Arrange
        handler, _ = self._make_handler(qtbot)
        # Act
        handler.update_mode_from_state(loaded_channels=3, saving=True)
        # Assert
        assert handler.mode_label.text() == "Saving"

    def test_update_mode_from_state_crop_mode_sets_cropping_mode(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler and crop_mode=True with saving=False,
        When update_mode_from_state is called,
        Then the mode label shows "Cropping".
        """
        # Arrange
        handler, _ = self._make_handler(qtbot)
        # Act
        handler.update_mode_from_state(loaded_channels=3, crop_mode=True)
        # Assert
        assert handler.mode_label.text() == "Cropping"

    @pytest.mark.parametrize(
        "loaded_channels",
        [
            0,  # BV3: zero channels
            1,  # EP3: below threshold
            2,  # BV1: one below threshold
        ],
        ids=["zero", "one", "two"],
    )
    def test_update_mode_from_state_fewer_than_three_channels_sets_load_images(
        self, qtbot: QtBot, loaded_channels: int
    ) -> None:
        """
        Given a StatusBarHandler and loaded_channels < 3 with no crop or save,
        When update_mode_from_state is called,
        Then the mode label shows "Load images".
        """
        # Arrange
        handler, _ = self._make_handler(qtbot)
        # Act
        handler.update_mode_from_state(loaded_channels=loaded_channels)
        # Assert
        assert handler.mode_label.text() == "Load images"

    def test_update_mode_from_state_three_channels_sets_editing_mode(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler and loaded_channels=3 (BV2: at threshold),
        When update_mode_from_state is called with no crop or save,
        Then the mode label shows "Editing".
        """
        # Arrange
        handler, _ = self._make_handler(qtbot)
        # Act
        handler.update_mode_from_state(loaded_channels=3)  # BV2
        # Assert
        assert handler.mode_label.text() == "Editing"

    def test_update_mode_from_state_saving_takes_priority_over_crop_mode(self, qtbot: QtBot) -> None:
        """
        Given a StatusBarHandler with both saving=True and crop_mode=True,
        When update_mode_from_state is called,
        Then the mode label shows "Saving" (saving beats crop_mode).
        """
        # Arrange
        handler, _ = self._make_handler(qtbot)
        # Act
        handler.update_mode_from_state(loaded_channels=3, crop_mode=True, saving=True)  # EP5
        # Assert
        assert handler.mode_label.text() == "Saving"
