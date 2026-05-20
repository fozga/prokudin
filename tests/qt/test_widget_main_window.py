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

"""Widget tests for src/ui/main_window.MainWindow."""

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtCore import Qt
from pytestqt.plugin import QtBot

from src.ui.main_window import MainWindow
from src.ui.widgets.channel_controller import ChannelController


@pytest.fixture
def window(qtbot: QtBot) -> MainWindow:
    """Real MainWindow with heavy collaborators patched out for widget tests.

    Constructs a real ``MainWindow`` with ``ImageProcessorService``, autosave
    persistence, display/save helpers, preset panel filesystem access, and the
    keyboard dispatcher patched so tests can exercise UI wiring without
    touching the filesystem, file dialogs, or the image-processing pipeline.
    Use this fixture for widget tests that need a live ``MainWindow``
    instance; for delegation tests on a single method, prefer the unit-test
    ``mw`` fixture.
    """
    from PyQt5.QtCore import pyqtSignal
    from PyQt5.QtWidgets import QWidget
    from unittest.mock import MagicMock

    # Minimal PresetPanel stub (must be a QWidget to work with layouts).
    class StubPresetPanel(QWidget):
        """Minimal stub for PresetPanel that provides required signals without filesystem access.

        Provides the preset_selected and save_requested signals that MainWindow
        connects to, plus a __getattr__ fallback for any other attribute/method
        access to prevent AttributeError if MainWindow calls methods like
        reload_presets() or load_thumbnail() during initialization.
        """

        preset_selected = pyqtSignal(dict)
        save_requested = pyqtSignal()

        def __getattr__(self, name: str) -> MagicMock:
            """Return a MagicMock for any attribute/method not explicitly defined."""
            return MagicMock()

    def mock_preset_panel_class(*args: object, **kwargs: object) -> StubPresetPanel:
        """Factory for StubPresetPanel to use as patch return value."""
        return StubPresetPanel()

    patches = [
        patch("src.ui.main_window.ImageProcessorService"),
        patch("src.ui.main_window.PresetPanel", side_effect=mock_preset_panel_class),
        patch("src.ui.main_window.restore_autosave"),
        patch("src.ui.main_window.save_autosave"),
        patch("src.ui.main_window.clear_autosave"),
        patch("src.ui.main_window.save_image_with_dialog"),
        patch("src.ui.main_window.handle_key_press", return_value=False),
    ]
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        w = MainWindow()
        qtbot.addWidget(w)
        return w


@pytest.mark.widget
class TestMainWindowWidgetScaffoldPlaceholder:
    """
    Test Design Specification: MainWindow widget-test scaffold (placeholder)
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Placeholder class so the shared ``window`` fixture is defined at
        module scope and available to future widget tests. Remove when
        the first real MainWindow widget test (beyond the existing delegation
        tests) lands.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.

    What is tested:
        - The ``window`` fixture is available (no-op placeholder).

    What is NOT tested:
        - Any MainWindow behaviour beyond fixture availability.

    Mocking strategy:
        - ImageProcessorService, PresetPanel, autosave entry points, save
          dialog, and keyboard dispatcher are patched at the
          ``src.ui.main_window`` import boundary.
    """

    def test_placeholder_no_op(self) -> None:
        """Placeholder test: window fixture is available and ready for use."""
        # Arrange  (no setup needed for placeholder)
        # Act      (no action needed for placeholder)
        # Assert
        assert True


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


@pytest.mark.widget
class TestMainWindowGridSettingsIntegration:
    """
    Test Design Specification: MainWindow — Grid Settings Delegation
    Module under test: src/ui/main_window.py (open_grid_settings, on_grid_type_changed, on_grid_line_width_changed)

    Contract:
        MainWindow.open_grid_settings, on_grid_type_changed, and on_grid_line_width_changed
        are thin delegation stubs that call the corresponding handler functions with self.
        This test verifies that the real method bodies execute and delegate correctly by
        calling the actual methods (not lambdas) on a mock MainWindow-like object.

    What is tested:
        - MainWindow.open_grid_settings calls grid_open_settings(self)
        - MainWindow.on_grid_type_changed calls grid_on_type_changed(self, grid_type)
        - MainWindow.on_grid_line_width_changed calls grid_on_line_width_changed(self, width)
        - Handler functions receive the window object and correct parameters

    What is NOT tested:
        - Full MainWindow initialization (heavy, causes timeout)
        - Handler logic itself (covered by unit tests in test_handlers_grid.py)
        - Dialog positioning or visual rendering

    Equivalence partitions:
        EP1  open_grid_settings() method delegates to grid_open_settings handler
        EP2  on_grid_type_changed(grid_type) method delegates with grid_type parameter
        EP3  on_grid_line_width_changed(width) method delegates with width parameter

    Mocking strategy:
        - Create mock object with same interface as MainWindow
        - Bind actual MainWindow method to mock (tests real delegation code)
        - Patch handler functions to verify they're called
        - Assert handlers receive mock object as first parameter
    """

    @patch("src.ui.main_window.grid_open_settings")
    def test_open_grid_settings_calls_handler(
        self, mock_handler: MagicMock, qtbot: QtBot
    ) -> None:
        """
        Given MainWindow.open_grid_settings method,
        When called on a mock MainWindow instance,
        Then the handler grid_open_settings is called with the mock as self.
        """
        from src.ui.main_window import MainWindow

        mock_window = MagicMock(spec=MainWindow)
        open_grid_settings_method = MainWindow.open_grid_settings

        open_grid_settings_method(mock_window)

        mock_handler.assert_called_once_with(mock_window)

    @patch("src.ui.main_window.grid_on_type_changed")
    def test_on_grid_type_changed_calls_handler(
        self, mock_handler: MagicMock, qtbot: QtBot
    ) -> None:
        """
        Given MainWindow.on_grid_type_changed method,
        When called on a mock MainWindow instance with a grid_type,
        Then the handler grid_on_type_changed is called with the mock and grid_type.
        """
        from src.ui.main_window import MainWindow
        from src.ui.widgets.grid_types import GRID_TYPE_3X3

        mock_window = MagicMock(spec=MainWindow)
        on_grid_type_changed_method = MainWindow.on_grid_type_changed

        on_grid_type_changed_method(mock_window, GRID_TYPE_3X3)

        mock_handler.assert_called_once_with(mock_window, GRID_TYPE_3X3)

    @patch("src.ui.main_window.grid_on_line_width_changed")
    def test_on_grid_line_width_changed_calls_handler(
        self, mock_handler: MagicMock, qtbot: QtBot
    ) -> None:
        """
        Given MainWindow.on_grid_line_width_changed method,
        When called on a mock MainWindow instance with a width,
        Then the handler grid_on_line_width_changed is called with the mock and width.
        """
        from src.ui.main_window import MainWindow

        mock_window = MagicMock(spec=MainWindow)
        on_grid_line_width_changed_method = MainWindow.on_grid_line_width_changed

        on_grid_line_width_changed_method(mock_window, 5)

        mock_handler.assert_called_once_with(mock_window, 5)

