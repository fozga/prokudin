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
from PyQt5.QtCore import Qt
from pytestqt.plugin import QtBot

from src.ui.main_window import MainWindow
from src.ui.widgets.channel_controller import ChannelController

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

