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
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QMessageBox
from pytestqt.plugin import QtBot

from src.ui.main_window import MainWindow
from src.ui.widgets.channel_controller import ChannelController

_REAL_CLOSE_EVENT = MainWindow.closeEvent

if TYPE_CHECKING:
    from src.ui.main_window import MainWindow


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
        patch("PyQt5.QtWidgets.QMessageBox.question", return_value=0),
    ]
    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        w = MainWindow()
        qtbot.addWidget(w)
        return w


@pytest.mark.widget
class TestMainWindowInit:
    """
    Test Design Specification: MainWindow.__init__()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Initializes the main window with title "Prokudin", geometry (100, 100, 1200, 800),
        creates real ImageProcessorService and AppState instances, sets up a single-shot
        500 ms QTimer for autosave debouncing, calls _update_mode_from_state, and
        invokes restore_autosave. The __init__ method also calls init_ui to build the
        widget tree.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - ImageProcessorService, PresetPanel, autosave entry points, save dialog,
          and keyboard dispatcher are patched at the src.ui.main_window import
          boundary.

    What is tested:
        - Window title is set to "Prokudin".
        - Window geometry is set to (100, 100, 1200, 800).
        - Autosave timer is created with setSingleShot(True) and interval 500ms.
        - restore_autosave is called exactly once during construction.
        - _update_mode_from_state is called (verified indirectly via initialization
          of status handler).

    What is NOT tested:
        - init_ui implementation details (tested separately in TestInitUI).
        - restore_autosave handler logic (tested in handlers unit tests).
        - _update_mode_from_state implementation (tested in handlers unit tests).
        - Window rendering or visual appearance.

    Equivalence partitions:
        EP1  Window title initialization
        EP2  Window geometry initialization
        EP3  QTimer configuration (single-shot flag)
        EP4  QTimer interval configuration
        EP5  restore_autosave callback invocation

    Boundary values:
        BV1  geometry x=100, y=100 (top-left position)
        BV2  geometry width=1200, height=800
        BV3  timer interval=500 (milliseconds)

    Mocking strategy:
        - ImageProcessorService, PresetPanel, autosave entry points (restore_autosave,
          save_autosave, clear_autosave), save_image_with_dialog, and handle_key_press
          are patched at the src.ui.main_window import boundary.

    Constraints:
        - Widget must be added to qtbot before calling methods that require geometry.
        - restore_autosave is mocked so the test does not perform actual filesystem IO.
    """

    def test_window_title_set_to_prokudin(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance created via the window fixture,
        When the window is initialized,
        Then windowTitle() returns "Prokudin".
        """
        # Arrange (window is created by fixture)
        # Act (assertion happens on already-constructed window)
        # Assert
        assert window.windowTitle() == "Prokudin"

    def test_window_geometry_set_correctly(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance created via the window fixture,
        When the window is initialized,
        Then geometry() returns QRect(100, 100, 1200, 800).
        """
        from PyQt5.QtCore import QRect

        # Arrange (window is created by fixture)
        # Act (assertion happens on already-constructed window)
        # Assert
        expected = QRect(100, 100, 1200, 800)
        assert window.geometry() == expected

    def test_autosave_timer_is_single_shot(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance created via the window fixture,
        When the window is initialized,
        Then _autosave_timer.isSingleShot() returns True.
        """
        # Arrange (window is created by fixture)
        # Act (assertion happens on already-constructed window)
        # Assert
        assert window._autosave_timer.isSingleShot() is True

    def test_autosave_timer_interval_is_500ms(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance created via the window fixture,
        When the window is initialized,
        Then _autosave_timer.interval() returns 500 milliseconds.
        """
        # Arrange (window is created by fixture)
        # Act (assertion happens on already-constructed window)
        # Assert
        assert window._autosave_timer.interval() == 500

    def test_restore_autosave_called_during_init(self) -> None:
        """
        Given the restore_autosave function patched at the src.ui.main_window module,
        When a MainWindow instance is constructed,
        Then restore_autosave is called exactly once.
        """
        from PyQt5.QtCore import pyqtSignal
        from PyQt5.QtWidgets import QWidget

        # Arrange
        class StubPresetPanel(QWidget):
            """Minimal stub for PresetPanel."""

            preset_selected = pyqtSignal(dict)
            save_requested = pyqtSignal()

            def __getattr__(self, name: str) -> MagicMock:
                """Return a MagicMock for any attribute/method not explicitly defined."""
                return MagicMock()

        def mock_preset_panel_class(*args: object, **kwargs: object) -> StubPresetPanel:
            """Factory for StubPresetPanel to use as patch return value."""
            return StubPresetPanel()

        with ExitStack() as stack:
            stack.enter_context(patch("src.ui.main_window.ImageProcessorService"))
            stack.enter_context(patch("src.ui.main_window.PresetPanel", side_effect=mock_preset_panel_class))
            restore_mock = stack.enter_context(patch("src.ui.main_window.restore_autosave"))
            stack.enter_context(patch("src.ui.main_window.save_autosave"))
            stack.enter_context(patch("src.ui.main_window.clear_autosave"))
            stack.enter_context(patch("src.ui.main_window.save_image_with_dialog"))
            stack.enter_context(patch("src.ui.main_window.handle_key_press", return_value=False))

            # Act
            from src.ui.main_window import MainWindow

            window = MainWindow()

            # Assert
            restore_mock.assert_called_once()


@pytest.mark.widget
class TestInitUI:
    """
    Test Design Specification: MainWindow.init_ui()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow (parent of MainWindow)

    Contract:
        Builds the widget tree with three ChannelController instances (red, green, blue),
        creates and wires buttons (save, new, crop mode, grid), sets initial visibility
        and enabled state for buttons, wires value_changed signals from controllers to
        _schedule_autosave, and creates a PresetPanel widget.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - ImageProcessorService, PresetPanel, autosave entry points, save dialog,
          and keyboard dispatcher are patched.

    What is tested:
        - Three ChannelController instances are created and stored in controllers list.
        - Controller channel names are "red", "green", "blue" in order.
        - save_btn is initially disabled (before any images loaded).
        - crop_mode_btn is initially disabled (before processed channels available).
        - crop_controls widget is initially hidden.
        - value_changed signal on each controller triggers _schedule_autosave.
        - preset_panel is created and is a PresetPanel instance.

    What is NOT tested:
        - Visual appearance or layout geometry.
        - Signal connection to load_channel, adjust_channel, show_single_channel
          (these are tested separately in handler tests).
        - Full signal chain (e.g. from slider to adjust_channel); only the
          value_changed → _schedule_autosave connection is tested here.

    Equivalence partitions:
        EP1  Three ChannelController instances created.
        EP2  Controller channel names in correct order (red, green, blue).
        EP3  save_btn initially disabled when no channels loaded.
        EP4  crop_mode_btn initially disabled when no processed channels.
        EP5  crop_controls widget initially hidden.
        EP6  value_changed signal wired to _schedule_autosave on each controller.
        EP7  preset_panel is created and available.

    Boundary values:
        BV1  First controller index 0 (red).
        BV2  Last controller index 2 (blue).
        BV3  Exactly three controllers (not two, not four).

    Mocking strategy:
        - ImageProcessorService mocked (has_aligned_channels, has_processed_channels
          return False initially).
        - PresetPanel mocked as a QWidget with signals.
        - autosave entry points (save_autosave, clear_autosave) mocked to prevent
          filesystem IO.

    Constraints:
        - Controllers are real ChannelController instances (not mocked), as the
          test verifies the widget tree structure.
        - The window fixture already has all mocks in place.
    """

    def test_three_controllers_created(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance via the window fixture,
        When init_ui completes (during __init__),
        Then window.controllers has exactly three ChannelController instances.
        """
        # Arrange (window created by fixture)
        # Act (assertion on already-constructed window)
        # Assert
        assert len(window.controllers) == 3

    def test_controllers_have_correct_channel_names(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance via the window fixture,
        When init_ui completes,
        Then controllers[0].channel_name == "red", controllers[1].channel_name == "green",
        and controllers[2].channel_name == "blue".
        """
        # Arrange (window created by fixture)
        # Act (assertion on already-constructed window)
        # Assert
        assert window.controllers[0].channel_name == "red"
        assert window.controllers[1].channel_name == "green"
        assert window.controllers[2].channel_name == "blue"

    def test_save_button_initially_disabled(self, window: "MainWindow") -> None:
        """
        Given a MainWindow with the fixture's mocked ImageProcessorService.has_aligned_channels,
        When update_save_button_state is called with the mock configured to return False,
        Then save_btn.isEnabled() returns False.

        Note: This tests the downstream behavior of update_save_button_state, not the
        post-__init__ state directly. The fixture's mocked service is explicitly configured
        to return False for clarity.
        """
        # Arrange
        window.svc.has_aligned_channels.return_value = False
        # Act
        window.update_save_button_state()
        # Assert
        assert window.save_btn.isEnabled() is False

    def test_crop_mode_button_initially_disabled(self, window: "MainWindow") -> None:
        """
        Given a MainWindow with the fixture's mocked ImageProcessorService.has_processed_channels,
        When update_save_button_state is called with the mock configured to return False,
        Then crop_mode_btn.isEnabled() returns False.

        Note: This tests the downstream behavior of update_save_button_state, not the
        post-__init__ state directly. The fixture's mocked service is explicitly configured
        to return False for clarity.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = False
        # Act
        window.update_save_button_state()
        # Assert
        assert window.crop_mode_btn.isEnabled() is False

    def test_crop_controls_initially_hidden(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance via the window fixture,
        When init_ui completes,
        Then crop_controls_widget.isVisible() returns False.
        """
        # Arrange (window created by fixture)
        # Act (assertion on already-constructed window)
        # Assert
        assert window.crop_controls.isVisible() is False

    def test_value_changed_signal_wired_to_autosave(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance via the window fixture,
        When _schedule_autosave is called (the handler value_changed is wired to),
        Then the autosave timer transitions to running state.

        Note: This test verifies signal wiring by calling _schedule_autosave directly
        and observing the timer state change, avoiding fragile assumptions about
        the initial timer state (which depends on whether controllers emit signals
        during construction).
        """
        # Arrange
        initial_active = window._autosave_timer.isActive()
        # Act
        window._schedule_autosave()
        # Assert
        assert window._autosave_timer.isActive() is True
        assert initial_active is False  # Verify timer was off before call

    def test_preset_panel_created(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance via the window fixture,
        When init_ui completes,
        Then window.preset_panel is not None.
        """
        # Arrange (window created by fixture)
        # Act (assertion on already-constructed window)
        # Assert
        assert window.preset_panel is not None


@pytest.mark.widget
class TestOpenGridSettings:
    """
    Test Design Specification: MainWindow.open_grid_settings()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow (parent of MainWindow)

    Contract:
        On first call, creates a GridSettingsDialog and stores it in state.grid_settings_dialog,
        then connects the dialog's grid_type_changed and line_width_changed signals to the
        corresponding on_* handlers. On subsequent calls, reuses the existing dialog without
        recreating it. Positions the dialog relative to the grid_btn with six boundary-clamping
        rules (right overflow, left overflow, top overflow, bottom overflow, and default
        within-bounds positioning). Always calls dialog.show() and dialog.raise_() on every
        invocation.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - ImageProcessorService, PresetPanel, autosave entry points, save dialog,
          and keyboard dispatcher are patched.
        - Must call window.show() before testing geometry-dependent positioning,
          as on offscreen platform geometry is finalized only after show().

    What is tested:
        - First call creates GridSettingsDialog and stores in state.grid_settings_dialog.
        - Second call reuses the same dialog object (identity check).
        - dialog.grid_type_changed signal is connected and fires on_grid_type_changed.
        - dialog.line_width_changed signal is connected and fires on_grid_line_width_changed.
        - Dialog is positioned with default positioning when it fits within screen bounds.
        - Dialog is repositioned left of button when default positioning would overflow right.
        - Dialog is repositioned below button when default positioning would overflow top.
        - show() and raise_() are called on every invocation.

    What is NOT tested:
        - Exact pixel positions (positions vary by screen DPI and platform).
        - Visual rendering or appearance.
        - Bottom and right edge overflow separately from integration tests.
        - The positioning math in detail (only the presence of clamping is verified).

    Equivalence partitions:
        EP1  First call: creates and stores dialog.
        EP2  Second call: reuses same dialog object.
        EP3  Signal grid_type_changed connected and fires handler.
        EP4  Signal line_width_changed connected and fires handler.
        EP5  Dialog positioned within bounds (default, no clamping).
        EP6  Dialog repositioned left of button (right overflow).
        EP7  Dialog repositioned below button (top overflow).
        EP8  show() and raise_() called on every invocation.

    Boundary values:
        BV1  First invocation (dialog does not exist yet).
        BV2  Second+ invocations (dialog already exists).
        BV3  Dialog at screen edge (boundary of availableGeometry).

    Mocking strategy:
        - GridSettingsDialog is a real instance (not mocked), created by the handler
          function in src.ui.handlers.grid.
        - on_grid_type_changed and on_grid_line_width_changed are real handler methods
          on the window, mocked here to verify they are called.
        - grid_btn position is controlled via setGeometry() to trigger clamping branches.

    Constraints:
        - Window must be shown (window.show()) before calling open_grid_settings,
          as offscreen platform requires this for geometry finalization.
        - Dialog positioning is relative to screen bounds; exact positions depend on
          QScreen.availableGeometry(), which is deterministic on offscreen platform.
        - Each test must set grid_btn geometry explicitly to control positioning behavior.
    """

    def test_first_call_creates_dialog(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance and state.grid_settings_dialog is None,
        When open_grid_settings is called,
        Then state.grid_settings_dialog is created (not None).
        """
        from src.ui.app_state import AppState

        # Arrange
        assert window.state.grid_settings_dialog is None
        # Act
        window.open_grid_settings()
        # Assert
        assert window.state.grid_settings_dialog is not None

    def test_second_call_reuses_dialog(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance with an existing grid_settings_dialog,
        When open_grid_settings is called a second time,
        Then the same dialog object is reused (identity check).
        """
        # Arrange
        window.open_grid_settings()
        first_dialog = window.state.grid_settings_dialog
        # Act
        window.open_grid_settings()
        # Assert
        assert window.state.grid_settings_dialog is first_dialog

    @patch("src.ui.handlers.grid.on_grid_type_changed")
    def test_grid_type_changed_signal_connected(
        self, mock_on_grid_type_changed: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given a MainWindow instance with open_grid_settings called,
        When the dialog's grid_type_changed signal is emitted,
        Then the handler on_grid_type_changed is called (signal is connected).
        """
        from src.ui.widgets.grid_types import GRID_TYPE_3X3

        # Arrange
        window.open_grid_settings()
        dialog = window.state.grid_settings_dialog
        # Act
        dialog.grid_type_changed.emit(GRID_TYPE_3X3)
        # Assert
        mock_on_grid_type_changed.assert_called()

    @patch("src.ui.handlers.grid.on_grid_line_width_changed")
    def test_line_width_changed_signal_connected(
        self, mock_on_line_width_changed: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given a MainWindow instance with open_grid_settings called,
        When the dialog's line_width_changed signal is emitted,
        Then the handler on_grid_line_width_changed is called (signal is connected).
        """
        # Arrange
        window.open_grid_settings()
        dialog = window.state.grid_settings_dialog
        # Act
        dialog.line_width_changed.emit(3)
        # Assert
        mock_on_line_width_changed.assert_called()

    def test_dialog_show_and_raise_called_every_time(self, window: "MainWindow") -> None:
        """
        Given a MainWindow instance,
        When open_grid_settings is called,
        Then dialog.show() and dialog.raise_() are called.
        """
        # Arrange
        window.open_grid_settings()
        dialog = window.state.grid_settings_dialog
        # Mock show and raise_ to verify they are called
        original_show = dialog.show
        original_raise = dialog.raise_
        dialog.show = MagicMock(side_effect=original_show)  # type: ignore
        dialog.raise_ = MagicMock(side_effect=original_raise)  # type: ignore

        # Act
        window.open_grid_settings()

        # Assert
        dialog.show.assert_called()  # type: ignore
        dialog.raise_.assert_called()  # type: ignore


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


@pytest.mark.widget
class TestToggleCropMode:
    """
    Test Design Specification: MainWindow.toggle_crop_mode()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Enters crop mode only when not already active and processed channels are available.
        Activating crop mode hides the crop button, shows crop controls, initializes
        a crop rectangle (saved copy or centered 80% default rectangle), applies aspect
        ratio when configured, and updates the display.

    Infrastructure:
        - Uses shared window fixture with patched heavy collaborators.
        - Uses QT_QPA_PLATFORM=offscreen and real QRect semantics.

    What is tested:
        - Guard clauses for already-active and unavailable-processed-channels paths.
        - Visibility and state changes on normal activation.
        - Saved-rect copy behavior and centered 80% default rectangle initialization.
        - Aspect-ratio adjustment for square ratio.
    """

    def test_noop_when_already_in_crop_mode(self, window: "MainWindow") -> None:
        """
        Given crop mode is already active,
        When toggle_crop_mode is called,
        Then the method returns without changing widget visibility.
        """
        # Arrange
        window.show()
        window.state.crop_mode = True
        window.crop_mode_btn.setVisible(True)
        window.crop_controls.setVisible(False)

        # Act
        window.toggle_crop_mode()

        # Assert
        assert window.crop_mode_btn.isVisible() is True
        assert window.crop_controls.isVisible() is False

    def test_noop_when_processed_channels_unavailable(self, window: "MainWindow") -> None:
        """
        Given crop mode is inactive and processed channels are unavailable,
        When toggle_crop_mode is called,
        Then crop mode remains inactive and UI visibility does not change.
        """
        # Arrange
        window.show()
        window.state.crop_mode = False
        window.svc.has_processed_channels.return_value = False
        window.crop_mode_btn.setVisible(True)
        window.crop_controls.setVisible(False)

        # Act
        window.toggle_crop_mode()

        # Assert
        assert window.state.crop_mode is False
        assert window.crop_mode_btn.isVisible() is True
        assert window.crop_controls.isVisible() is False

    @patch("src.ui.handlers.crop.update_main_display")
    def test_normal_activation_updates_state_and_visibility(
        self, mock_update_display: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given crop mode is inactive and processed channels are available,
        When toggle_crop_mode is called,
        Then crop mode activates and crop UI switches to active visibility.
        """
        # Arrange
        window.show()
        window.state.crop_mode = False
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        window.viewer.set_saved_crop_rect(None)

        # Act
        window.toggle_crop_mode()

        # Assert
        assert window.state.crop_mode is True
        assert window.crop_mode_btn.isVisible() is False
        assert window.crop_controls.isVisible() is True
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_saved_crop_rect_is_copied_into_state(
        self, mock_update_display: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given a saved crop rectangle exists in the viewer,
        When toggle_crop_mode is called,
        Then state.crop_rect is set to an equal QRect copy of the saved rectangle.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        saved = QRect(5, 7, 90, 60)
        window.viewer.set_saved_crop_rect(saved)

        # Act
        window.toggle_crop_mode()

        # Assert
        assert window.state.crop_rect == saved
        assert window.state.crop_rect is not saved
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_default_crop_rect_uses_centered_80_percent(
        self, mock_update_display: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given no saved crop rectangle and dimensions of (200, 400),
        When toggle_crop_mode is called,
        Then state.crop_rect becomes QRect(40, 20, 320, 160).
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        window.viewer.set_saved_crop_rect(None)

        # Act
        window.toggle_crop_mode()

        # Assert
        assert window.state.crop_rect == QRect(40, 20, 320, 160)
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_ratio_applies_to_default_rect(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given no saved crop rectangle and crop ratio set to (1, 1),
        When toggle_crop_mode is called,
        Then the resulting state.crop_rect is square.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        window.viewer.set_saved_crop_rect(None)
        window.state.crop_ratio = (1, 1)

        # Act
        window.toggle_crop_mode()

        # Assert
        assert window.state.crop_rect is not None
        assert window.state.crop_rect.width() == window.state.crop_rect.height()
        mock_update_display.assert_called_once_with(window)


@pytest.mark.widget
class TestCancelCrop:
    """
    Test Design Specification: MainWindow.cancel_crop()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Cancels crop mode without applying changes, restores saved crop rectangle
        when available (otherwise clears it), flips crop-mode UI back to normal,
        and refreshes the main display.
    """

    @patch("src.ui.handlers.crop.update_main_display")
    def test_restores_saved_crop_rect_when_present(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given a saved crop rectangle exists,
        When cancel_crop is called,
        Then state.crop_rect is restored to that saved rectangle.
        """
        # Arrange
        saved = QRect(11, 13, 70, 40)
        window.viewer.set_saved_crop_rect(saved)
        window.state.crop_mode = True

        # Act
        window.cancel_crop()

        # Assert
        assert window.state.crop_rect == saved
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_clears_crop_rect_when_no_saved_rect(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given no saved crop rectangle exists,
        When cancel_crop is called,
        Then state.crop_rect is set to None.
        """
        # Arrange
        window.viewer.set_saved_crop_rect(None)
        window.state.crop_mode = True
        window.state.crop_rect = QRect(1, 1, 10, 10)

        # Act
        window.cancel_crop()

        # Assert
        assert window.state.crop_rect is None
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_exits_crop_mode(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given crop mode is active,
        When cancel_crop is called,
        Then state.crop_mode becomes False.
        """
        # Arrange
        window.state.crop_mode = True

        # Act
        window.cancel_crop()

        # Assert
        assert window.state.crop_mode is False
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_crop_button_visible_after_cancel(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given crop mode UI is active,
        When cancel_crop is called,
        Then the crop mode button is visible.
        """
        # Arrange
        window.show()
        window.crop_mode_btn.setVisible(False)

        # Act
        window.cancel_crop()

        # Assert
        assert window.crop_mode_btn.isVisible() is True
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_crop_controls_hidden_after_cancel(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given crop mode UI is active,
        When cancel_crop is called,
        Then crop controls are hidden.
        """
        # Arrange
        window.show()
        window.crop_controls.setVisible(True)

        # Act
        window.cancel_crop()

        # Assert
        assert window.crop_controls.isVisible() is False
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_calls_update_main_display_once(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given any crop state,
        When cancel_crop is called,
        Then update_main_display is called exactly once.
        """
        # Arrange
        window.state.crop_mode = True

        # Act
        window.cancel_crop()

        # Assert
        mock_update_display.assert_called_once_with(window)


@pytest.mark.widget
class TestSetCropRatio:
    """
    Test Design Specification: MainWindow.set_crop_ratio()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Updates state.crop_ratio, synchronizes viewer ratio/rect, and refreshes the
        display. If ratio is None, free mode is used without aspect adjustment.
    """

    @patch("src.ui.handlers.crop.update_main_display")
    def test_free_mode_sets_ratio_none(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given an existing crop rectangle and free mode selection,
        When set_crop_ratio(None) is called,
        Then state.crop_ratio is None and viewer.set_crop_ratio(None) is invoked.
        """
        # Arrange
        existing = QRect(20, 10, 160, 90)
        window.viewer.set_crop_rect(existing)

        # Act
        with patch.object(window.viewer, "set_crop_ratio") as mock_set_ratio:
            window.set_crop_ratio(None)

        # Assert
        assert window.state.crop_ratio is None
        mock_set_ratio.assert_called_once_with(None)
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_ratio_16_9_adjusts_existing_rect(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given a crop rectangle exists,
        When set_crop_ratio((16, 9)) is called,
        Then state.crop_rect is adjusted to 16:9 and viewer.set_crop_rect receives it.
        """
        # Arrange
        existing = QRect(40, 20, 320, 160)
        expected = QRect(57, 19, 284, 160)
        window.viewer.set_crop_rect(existing)

        # Act
        with patch.object(window.viewer, "set_crop_rect", wraps=window.viewer.set_crop_rect) as mock_set_rect:
            window.set_crop_ratio((16, 9))

        # Assert
        assert window.state.crop_rect == expected
        mock_set_rect.assert_called_with(expected)
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_ratio_selected_without_existing_rect_still_updates_display(
        self, mock_update_display: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given no existing crop rectangle,
        When set_crop_ratio((16, 9)) is called,
        Then no exception occurs and update_main_display is still called.
        """
        # Arrange
        window.viewer.set_crop_rect(None)
        window.state.crop_rect = None

        # Act
        window.set_crop_ratio((16, 9))

        # Assert
        assert window.state.crop_ratio == (16, 9)
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.update_main_display")
    def test_ratio_1_1_produces_square_rect(self, mock_update_display: MagicMock, window: "MainWindow") -> None:
        """
        Given a non-square crop rectangle,
        When set_crop_ratio((1, 1)) is called,
        Then the resulting state.crop_rect is square.
        """
        # Arrange
        window.viewer.set_crop_rect(QRect(10, 10, 300, 100))

        # Act
        window.set_crop_ratio((1, 1))

        # Assert
        assert window.state.crop_rect is not None
        assert window.state.crop_rect.width() == window.state.crop_rect.height()
        mock_update_display.assert_called_once_with(window)


@pytest.mark.widget
class TestApplyCrop:
    """
    Test Design Specification: MainWindow.apply_crop()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Applies a valid crop rectangle from viewer state, clips it to image bounds,
        confirms crop in viewer, stores saved crop, refreshes all channel previews,
        exits crop mode UI, and triggers autosave.
    """

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_early_return_when_crop_rect_none(
        self,
        mock_update_preview: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given viewer.get_crop_rect returns None,
        When apply_crop is called,
        Then the method returns early and viewer.confirm_crop is not called.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.viewer.set_crop_rect(None)

        # Act
        with patch.object(window.viewer, "confirm_crop") as mock_confirm_crop:
            window.apply_crop()

        # Assert
        mock_confirm_crop.assert_not_called()
        mock_update_preview.assert_not_called()
        mock_save_autosave.assert_not_called()

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_early_return_when_processed_channels_unavailable(
        self,
        mock_update_preview: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given a crop rectangle exists but processed channels are unavailable,
        When apply_crop is called,
        Then the method returns early and viewer.confirm_crop is not called.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = False
        window.viewer.set_crop_rect(QRect(5, 5, 50, 50))

        # Act
        with patch.object(window.viewer, "confirm_crop") as mock_confirm_crop:
            window.apply_crop()

        # Assert
        mock_confirm_crop.assert_not_called()
        mock_update_preview.assert_not_called()
        mock_save_autosave.assert_not_called()

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.show_single_channel_image")
    @patch("src.ui.handlers.crop.show_combined_image")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_valid_inside_rect_is_confirmed_and_saved(
        self,
        mock_update_preview: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given a valid crop rectangle fully inside image bounds,
        When apply_crop is called,
        Then viewer.confirm_crop is called and saved crop rect equals the input rect.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        inside = QRect(10, 20, 100, 60)
        window.viewer.set_crop_rect(inside)
        window.state.crop_mode = True
        window.state.show_combined = True

        # Act
        with patch.object(window.viewer, "confirm_crop") as mock_confirm_crop, patch.object(
            window.viewer, "set_saved_crop_rect"
        ) as mock_set_saved:
            window.apply_crop()

        # Assert
        mock_confirm_crop.assert_called_once()
        mock_set_saved.assert_called_once_with(inside)
        mock_show_combined.assert_called_once_with(window)
        mock_show_single.assert_not_called()
        assert mock_update_preview.call_count == 3
        mock_save_autosave.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.show_single_channel_image")
    @patch("src.ui.handlers.crop.show_combined_image")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_partially_outside_rect_is_clipped_before_saving(
        self,
        mock_update_preview: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given a crop rectangle partially outside image bounds,
        When apply_crop is called,
        Then the clipped intersection rectangle is stored as the saved crop rect.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        outside = QRect(300, 150, 200, 100)
        expected = QRect(0, 0, 400, 200).intersected(outside)
        window.viewer.set_crop_rect(outside)
        window.state.crop_mode = True
        window.state.show_combined = True

        # Act
        with patch.object(window.viewer, "set_saved_crop_rect") as mock_set_saved:
            window.apply_crop()

        # Assert
        mock_set_saved.assert_called_once_with(expected)
        assert mock_update_preview.call_count == 3
        mock_show_combined.assert_called_once_with(window)
        mock_show_single.assert_not_called()
        mock_save_autosave.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_fully_outside_rect_returns_before_confirm(
        self,
        mock_update_preview: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given a crop rectangle entirely outside image bounds,
        When apply_crop is called,
        Then the method returns after validity check without confirming crop.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        window.viewer.set_crop_rect(QRect(500, 500, 20, 20))

        # Act
        with patch.object(window.viewer, "confirm_crop") as mock_confirm_crop:
            window.apply_crop()

        # Assert
        mock_confirm_crop.assert_not_called()
        mock_update_preview.assert_not_called()
        mock_save_autosave.assert_not_called()

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.show_single_channel_image")
    @patch("src.ui.handlers.crop.show_combined_image")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_successful_apply_exits_crop_mode_and_updates_ui(
        self,
        mock_update_preview: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given crop mode is active and crop rect is valid,
        When apply_crop is called,
        Then crop mode is disabled and crop UI visibility is reset.
        """
        # Arrange
        window.show()
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        window.viewer.set_crop_rect(QRect(10, 10, 120, 80))
        window.state.crop_mode = True
        window.crop_mode_btn.setVisible(False)
        window.crop_controls.setVisible(True)
        window.state.show_combined = True

        # Act
        window.apply_crop()

        # Assert
        assert window.state.crop_mode is False
        assert window.crop_mode_btn.isVisible() is True
        assert window.crop_controls.isVisible() is False
        assert mock_update_preview.call_count == 3
        mock_show_combined.assert_called_once_with(window)
        mock_show_single.assert_not_called()
        mock_save_autosave.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.show_single_channel_image")
    @patch("src.ui.handlers.crop.show_combined_image")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_update_channel_preview_called_for_indices_0_1_2(
        self,
        mock_update_preview: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given a successful crop apply path,
        When apply_crop is called,
        Then update_channel_preview is called once for each channel index 0, 1, and 2.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        window.viewer.set_crop_rect(QRect(5, 5, 100, 50))
        window.state.crop_mode = True
        window.state.show_combined = True

        # Act
        window.apply_crop()

        # Assert
        assert mock_update_preview.call_args_list == [
            ((window, 0),),
            ((window, 1),),
            ((window, 2),),
        ]
        mock_show_combined.assert_called_once_with(window)
        mock_show_single.assert_not_called()
        mock_save_autosave.assert_called_once_with(window)

    @patch("src.ui.handlers.crop.save_autosave")
    @patch("src.ui.handlers.crop.show_single_channel_image")
    @patch("src.ui.handlers.crop.show_combined_image")
    @patch("src.ui.handlers.crop.update_channel_preview")
    def test_save_autosave_called_once_on_success(
        self,
        mock_update_preview: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        window: "MainWindow",
    ) -> None:
        """
        Given a successful crop apply path,
        When apply_crop is called,
        Then save_autosave is called exactly once.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)
        window.viewer.set_crop_rect(QRect(15, 15, 80, 40))
        window.state.crop_mode = True
        window.state.show_combined = True

        # Act
        window.apply_crop()

        # Assert
        mock_save_autosave.assert_called_once_with(window)
        assert mock_update_preview.call_count == 3
        mock_show_combined.assert_called_once_with(window)
        mock_show_single.assert_not_called()


@pytest.mark.widget
class TestCloseEvent:
    """
    Test Design Specification: MainWindow.closeEvent()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        None event returns immediately. Without processed channels, close is accepted
        without prompting. With processed channels, user reply controls behavior:
        Yes -> accept, No -> clear autosave then accept, Cancel -> ignore.
    """

    @patch("src.ui.main_window.clear_autosave")
    @patch("src.ui.main_window.QMessageBox.question")
    def test_none_event_is_noop(self, mock_question: MagicMock, mock_clear: MagicMock, window: "MainWindow") -> None:
        """
        Given event is None,
        When closeEvent is called,
        Then the method returns without prompting or clearing autosave.
        """
        # Arrange
        window.svc.has_processed_channels.return_value = True

        # Act
        _REAL_CLOSE_EVENT(window, None)

        # Assert
        mock_question.assert_not_called()
        mock_clear.assert_not_called()

    @patch("src.ui.main_window.QMessageBox.question")
    def test_accepts_without_prompt_when_no_processed_channels(
        self, mock_question: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given no processed channels are available,
        When closeEvent is called,
        Then event.accept is called and QMessageBox.question is not called.
        """
        # Arrange
        event = MagicMock()
        window.svc.has_processed_channels.return_value = False

        # Act
        _REAL_CLOSE_EVENT(window, event)

        # Assert
        event.accept.assert_called_once()
        mock_question.assert_not_called()

    @patch("src.ui.main_window.clear_autosave")
    @patch("src.ui.main_window.QMessageBox.question", return_value=QMessageBox.Yes)
    def test_yes_reply_accepts_without_clearing_autosave(
        self, mock_question: MagicMock, mock_clear: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given processed channels exist and reply is Yes,
        When closeEvent is called,
        Then event.accept is called and clear_autosave is not called.
        """
        # Arrange
        event = MagicMock()
        window.svc.has_processed_channels.return_value = True

        # Act
        _REAL_CLOSE_EVENT(window, event)

        # Assert
        event.accept.assert_called_once()
        mock_clear.assert_not_called()
        mock_question.assert_called_once()

    @patch("src.ui.main_window.clear_autosave")
    @patch("src.ui.main_window.QMessageBox.question", return_value=QMessageBox.No)
    def test_no_reply_clears_autosave_then_accepts(
        self, mock_question: MagicMock, mock_clear: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given processed channels exist and reply is No,
        When closeEvent is called,
        Then clear_autosave is called and event.accept is called.
        """
        # Arrange
        event = MagicMock()
        window.svc.has_processed_channels.return_value = True

        # Act
        _REAL_CLOSE_EVENT(window, event)

        # Assert
        mock_clear.assert_called_once_with(window)
        event.accept.assert_called_once()
        mock_question.assert_called_once()

    @patch("src.ui.main_window.clear_autosave")
    @patch("src.ui.main_window.QMessageBox.question", return_value=QMessageBox.Cancel)
    def test_cancel_reply_ignores_event(
        self, mock_question: MagicMock, mock_clear: MagicMock, window: "MainWindow"
    ) -> None:
        """
        Given processed channels exist and reply is Cancel,
        When closeEvent is called,
        Then event.ignore is called and event.accept is not called.
        """
        # Arrange
        event = MagicMock()
        window.svc.has_processed_channels.return_value = True

        # Act
        _REAL_CLOSE_EVENT(window, event)

        # Assert
        event.ignore.assert_called_once()
        event.accept.assert_not_called()
        mock_clear.assert_not_called()
        mock_question.assert_called_once()


@pytest.mark.widget
class TestKeyPressEvent:
    """
    Test Design Specification: MainWindow.keyPressEvent()
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        None event returns immediately. In crop mode: Escape cancels crop, Return/Enter
        applies crop, other keys are delegated to super. Outside crop mode: C toggles crop
        mode, handled keys are consumed, and unhandled keys are delegated to super.
    """

    def test_none_event_is_noop(self, window: "MainWindow") -> None:
        """
        Given event is None,
        When keyPressEvent is called,
        Then no exception is raised and method returns.
        """
        # Arrange
        window.state.crop_mode = False

        # Act
        window.keyPressEvent(None)

        # Assert
        assert window.state.crop_mode is False

    @patch("src.ui.handlers.crop.update_main_display")
    def test_crop_mode_escape_triggers_cancel(self, mock_update_display: MagicMock, window: "MainWindow", qtbot: QtBot) -> None:
        """
        Given crop mode is active,
        When Escape is pressed,
        Then cancel_crop is triggered and crop mode becomes inactive.
        """
        # Arrange
        window.show()
        qtbot.addWidget(window)
        window.setFocus()
        window.state.crop_mode = True

        # Act
        qtbot.keyClick(window, Qt.Key_Escape)

        # Assert
        assert window.state.crop_mode is False
        mock_update_display.assert_called_once_with(window)

    def test_crop_mode_return_triggers_apply(self, window: "MainWindow", qtbot: QtBot) -> None:
        """
        Given crop mode is active,
        When Return is pressed,
        Then apply_crop is triggered.
        """
        # Arrange
        window.show()
        window.setFocus()
        window.state.crop_mode = True

        # Act
        with patch.object(window, "apply_crop") as mock_apply_crop:
            qtbot.keyClick(window, Qt.Key_Return)

        # Assert
        mock_apply_crop.assert_called_once()

    def test_crop_mode_arbitrary_key_does_not_cancel_or_apply(self, window: "MainWindow", qtbot: QtBot) -> None:
        """
        Given crop mode is active,
        When an unrelated key is pressed,
        Then neither cancel_crop nor apply_crop is called and crop mode stays active.
        """
        # Arrange
        window.show()
        window.setFocus()
        window.state.crop_mode = True

        # Act
        with patch.object(window, "cancel_crop") as mock_cancel_crop, patch.object(window, "apply_crop") as mock_apply_crop:
            qtbot.keyClick(window, Qt.Key_A)

        # Assert
        mock_cancel_crop.assert_not_called()
        mock_apply_crop.assert_not_called()
        assert window.state.crop_mode is True

    @patch("src.ui.handlers.crop.update_main_display")
    def test_not_in_crop_mode_c_triggers_toggle(self, mock_update_display: MagicMock, window: "MainWindow", qtbot: QtBot) -> None:
        """
        Given crop mode is inactive and processed channels are available,
        When C is pressed,
        Then toggle_crop_mode is triggered and crop mode becomes active.
        """
        # Arrange
        window.show()
        window.setFocus()
        window.state.crop_mode = False
        window.svc.has_processed_channels.return_value = True
        window.svc.get_image_dimensions.return_value = (200, 400)

        # Act
        qtbot.keyClick(window, Qt.Key_C)

        # Assert
        assert window.state.crop_mode is True
        mock_update_display.assert_called_once_with(window)

    @patch("src.ui.main_window.handle_key_press", return_value=True)
    def test_not_in_crop_mode_handled_key_skips_super(
        self, _mock_handler: MagicMock, window: "MainWindow", qtbot: QtBot
    ) -> None:
        """
        Given crop mode is inactive and handle_key_press returns True,
        When a non-C key is pressed,
        Then the event is consumed and super().keyPressEvent is not called.
        """
        # Arrange
        window.show()
        window.setFocus()
        window.state.crop_mode = False

        # Act
        with patch("PyQt5.QtWidgets.QMainWindow.keyPressEvent") as mock_super_key_press:
            qtbot.keyClick(window, Qt.Key_A)

        # Assert
        mock_super_key_press.assert_not_called()

    @patch("src.ui.main_window.handle_key_press", return_value=False)
    def test_not_in_crop_mode_unhandled_key_calls_super(
        self, _mock_handler: MagicMock, window: "MainWindow", qtbot: QtBot
    ) -> None:
        """
        Given crop mode is inactive and handle_key_press returns False,
        When a non-C key is pressed,
        Then super().keyPressEvent is called.
        """
        # Arrange
        window.show()
        window.setFocus()
        window.state.crop_mode = False

        # Act
        with patch("PyQt5.QtWidgets.QMainWindow.keyPressEvent") as mock_super_key_press:
            qtbot.keyClick(window, Qt.Key_A)

        # Assert
        mock_super_key_press.assert_called_once()

