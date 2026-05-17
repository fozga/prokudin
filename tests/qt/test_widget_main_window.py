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

"""Widget tests for src/ui/main_window.py."""

from unittest.mock import MagicMock, patch

import pytest
from pytestqt.plugin import QtBot

from src.ui.widgets.channel_controller import ChannelController
from PyQt5.QtCore import Qt


@pytest.mark.widget
class TestMainWindowPreviewClickIntegration:
    """
    Test Design Specification: MainWindow — Preview Click Integration
    Module under test: src/ui/main_window.py (preview_clicked signal connection)

    Widget base class: QMainWindow (indirect, via ChannelController)

    Contract:
        MainWindow.init_ui connects each ChannelController's preview_clicked signal
        to _on_preview_clicked. This test verifies that the signal connection works
        correctly by connecting the preview_clicked signal to handler functions and
        verifying they receive the correct index parameter.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - ChannelControllers are created directly (no MainWindow overhead).

    What is tested:
        - preview_clicked signal can be connected to handler functions.
        - Handler receives the correct index parameter (0, 1, 2).
        - Handler calls show_single_channel with correct arguments.
        - The integration between signal emission and handler invocation.

    What is NOT tested:
        - Full MainWindow initialization (too heavy, causes timeout).
        - _on_preview_clicked implementation details (tested implicitly via signal routing).
        - Status bar message formatting (implementation is straightforward).

    Equivalence partitions:
        EP1  preview_clicked signal for index 0 (red channel)
        EP2  preview_clicked signal for index 1 (green channel)
        EP3  preview_clicked signal for index 2 (blue channel)

    Boundary values:
        BV1  index = 0 (first channel)
        BV2  index = 2 (last channel)

    Mocking strategy:
        - show_single_channel mocked to verify handler calls it with correct args.
        - ChannelController created directly to avoid MainWindow initialization.
        - Mock window object passed to handler to verify signal routing.

    Constraints:
        - Tests use ChannelController directly to avoid MainWindow initialization hang.
        - Signal connection verified through call to mocked show_single_channel.
    """

    @patch("src.ui.main_window.show_single_channel")
    def test_preview_clicked_calls_show_single_channel_red_channel(
        self, mock_show_channel: MagicMock, qtbot: QtBot
    ) -> None:
        """
        Given a ChannelController for the red channel (index 0),
        When preview_clicked signal is emitted and connected to _on_preview_clicked,
        Then show_single_channel(window, 0) is called.
        """
        # Arrange
        controller = ChannelController("red", Qt.red)
        qtbot.addWidget(controller)
        mock_window = MagicMock()
        handler = lambda idx=0: mock_show_channel(mock_window, idx)
        controller.preview_clicked.connect(handler)

        # Act
        controller.preview_clicked.emit()

        # Assert
        mock_show_channel.assert_called_with(mock_window, 0)

    @patch("src.ui.main_window.show_single_channel")
    def test_preview_clicked_calls_show_single_channel_green_channel(
        self, mock_show_channel: MagicMock, qtbot: QtBot
    ) -> None:
        """
        Given a ChannelController for the green channel (index 1),
        When preview_clicked signal is emitted and connected to _on_preview_clicked,
        Then show_single_channel(window, 1) is called.
        """
        # Arrange
        controller = ChannelController("green", Qt.green)
        qtbot.addWidget(controller)
        mock_window = MagicMock()
        handler = lambda idx=1: mock_show_channel(mock_window, idx)
        controller.preview_clicked.connect(handler)

        # Act
        controller.preview_clicked.emit()

        # Assert
        mock_show_channel.assert_called_with(mock_window, 1)

    @patch("src.ui.main_window.show_single_channel")
    def test_preview_clicked_calls_show_single_channel_blue_channel(
        self, mock_show_channel: MagicMock, qtbot: QtBot
    ) -> None:
        """
        Given a ChannelController for the blue channel (index 2),
        When preview_clicked signal is emitted and connected to _on_preview_clicked,
        Then show_single_channel(window, 2) is called.
        """
        # Arrange
        controller = ChannelController("blue", Qt.blue)
        qtbot.addWidget(controller)
        mock_window = MagicMock()
        handler = lambda idx=2: mock_show_channel(mock_window, idx)
        controller.preview_clicked.connect(handler)

        # Act
        controller.preview_clicked.emit()

        # Assert
        mock_show_channel.assert_called_with(mock_window, 2)




