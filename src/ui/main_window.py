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
Main application window and UI layout for Prokudin.
Handles state management, user interactions, and connects UI components to processing logic.
"""

from typing import Optional, Union

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QPushButton, QStatusBar, QVBoxLayout, QWidget

from ..services.processor import ImageProcessorService
from .app_state import AppState
from .config import get_config_dir, get_presets_dir
from .handlers.autosave import clear_autosave, restore_autosave, save_autosave
from .handlers.channels import adjust_channel, load_channel, show_single_channel
from .handlers.crop import apply_crop as crop_apply_crop
from .handlers.crop import cancel_crop as crop_cancel_crop
from .handlers.crop import set_crop_ratio as crop_set_crop_ratio
from .handlers.crop import toggle_crop_mode as crop_toggle_crop_mode
from .handlers.grid import on_grid_line_width_changed as grid_on_line_width_changed
from .handlers.grid import on_grid_type_changed as grid_on_type_changed
from .handlers.grid import open_grid_settings as grid_open_settings
from .handlers.image_saving import save_image_with_dialog
from .handlers.keyboard import handle_key_press
from .handlers.presets import apply_preset, save_preset
from .widgets.channel_controller import ChannelController
from .widgets.crop_controls import CropControlsWidget
from .widgets.grid_types import (
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
from .widgets.image_viewer import ImageViewer
from .widgets.preset_panel import PresetPanel
from .widgets.status_bar import StatusBarHandler


class MainWindow(QMainWindow):  # pylint: disable=too-many-instance-attributes
    """
        Main application window for Prokudin.

        This window manages the overall GUI layout, holds the state of loaded and processed images,
        and connects user interactions (buttons, sliders, keyboard) to the processing logic.

        Related components:
            - ImageViewer (widgets.image_viewer): Displays the main image.
            - ChannelController (widgets.channel_controller): Controls for each RGB channel.
    - StatusBarHandler (widgets.status_bar): Manages the status bar.
            - handlers.channels: Functions for loading and adjusting channels.
            - handlers.display: Functions for updating the main display.
            - handlers.keyboard: Keyboard shortcut handling.
    """

    GRID_TYPE_STATUS_MESSAGES = {
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

    def __init__(self) -> None:
        """
        Initialize the main window, set up the title, geometry, internal state,
        and construct the user interface.

        Args:
            self (MainWindow): The instance of the main window.

        Returns:
            None
        """
        super().__init__()
        self.setWindowTitle("Prokudin")
        self.setGeometry(100, 100, 1200, 800)

        self.svc = ImageProcessorService()
        self.state = AppState()

        self.presets_dir = get_presets_dir()
        self.config_dir = get_config_dir()

        assert self.presets_dir is not None
        assert self.config_dir is not None
        self.init_ui()

        # Debounce timer: autosave fires 500 ms after the last slider change
        self._autosave_timer = QTimer()
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(500)
        self._autosave_timer.timeout.connect(lambda: save_autosave(self))

        # Update the mode based on initial state
        self._update_mode_from_state()

        # Restore previous session (loads images, sets sliders, applies crop)
        restore_autosave(self)

    def init_ui(self) -> None:  # pylint: disable=too-many-statements
        """
        Build the main UI layout: image viewer and channel controllers.

        Args:
            self (MainWindow): The instance of the main window.

        Returns:
            None

        - Adds an ImageViewer widget for displaying images.
        - Adds three ChannelController widgets (R, G, B) with sliders and load buttons.
        - Connects controller signals to appropriate handler functions.

        Cross-references:
            - ImageViewer
            - ChannelController
            - handlers.channels.load_channel, adjust_channel, update_channel_preview, show_single_channel
        """
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        # Add status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_handler = StatusBarHandler(status_bar)

        # Add save button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_images)
        self.save_btn.setEnabled(False)  # Initially disabled

        # Add New button to reset the application
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self.reset_to_defaults)

        # Add crop mode button (QPushButton)
        self.crop_mode_btn = QPushButton("Crop")
        self.crop_mode_btn.clicked.connect(self.toggle_crop_mode)

        # Crop controls widget
        self.crop_controls = CropControlsWidget()
        self.crop_controls.setVisible(False)
        self.crop_controls.ratio_changed.connect(self.set_crop_ratio)
        self.crop_controls.accept_requested.connect(self.apply_crop)
        self.crop_controls.cancel_requested.connect(self.cancel_crop)

        # Left sidebar: preset panel + grid button
        left_sidebar = QVBoxLayout()

        self.preset_panel = PresetPanel(self.presets_dir)  # type: ignore[arg-type]
        self.preset_panel.preset_selected.connect(lambda data: apply_preset(self, data))
        self.preset_panel.save_requested.connect(lambda: save_preset(self))
        left_sidebar.addWidget(self.preset_panel)

        # Grid button at the bottom
        self.grid_btn = QPushButton("Grid")
        self.grid_btn.clicked.connect(self.open_grid_settings)
        left_sidebar.addWidget(self.grid_btn)

        main_layout.addLayout(left_sidebar, 18)

        # Center panel for image viewer
        center_panel = QVBoxLayout()

        # Create a horizontal layout for the buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.new_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.crop_mode_btn)

        # Add the buttons layout to the center panel
        center_panel.addLayout(buttons_layout)
        center_panel.addWidget(self.crop_controls)
        self.viewer = ImageViewer()
        center_panel.addWidget(self.viewer, 70)

        main_layout.addLayout(center_panel, 65)

        # Right panel with channel controllers
        right_panel = QVBoxLayout()
        self.controllers = [
            ChannelController("red", Qt.GlobalColor.red),
            ChannelController("green", Qt.GlobalColor.green),
            ChannelController("blue", Qt.GlobalColor.blue),
        ]

        for idx, controller in enumerate(self.controllers):
            # Connect load button and sliders to handlers
            controller.btn_load.clicked.connect(lambda _, i=idx: load_channel(self, i))
            controller.btn_load.clicked.connect(lambda _, i=idx: save_autosave(self))

            # Connect controller value changes to adjust channel (handles both slider and text input)
            controller.value_changed.connect(lambda i=idx: adjust_channel(self, i))
            controller.value_changed.connect(self._schedule_autosave)

            # Connect preview_clicked signal to show single channel
            controller.preview_clicked.connect(lambda i=idx: self._on_preview_clicked(i))

            right_panel.addWidget(controller)
        right_panel.addStretch()
        main_layout.addLayout(right_panel, 30)

        self.setCentralWidget(main_widget)

        # After connecting all signals for loading/adjusting channels, update save button state
        self.update_save_button_state()

    def _update_mode_from_state(self) -> None:
        """Update the mode indicator based on the current application state."""
        loaded_channels = sum(1 for img in self.svc.original_images if img is not None)
        self.status_handler.update_mode_from_state(loaded_channels, self.state.crop_mode)

    def toggle_crop_mode(self) -> None:
        """Toggle crop mode; initializes default crop rect from image dimensions.

        Cross-references:
            - handlers.crop.toggle_crop_mode
        """
        crop_toggle_crop_mode(self)

    def cancel_crop(self) -> None:
        """
        Cancel the current crop operation.

        Cross-references:
            - handlers.crop.cancel_crop
        """
        crop_cancel_crop(self)

    def set_crop_ratio(self, ratio: Optional[tuple[int, int]]) -> None:
        """
        Set the aspect ratio for the crop rectangle.

        Args:
            ratio: The aspect ratio as (width, height) tuple, or None for free aspect.

        Cross-references:
            - handlers.crop.set_crop_ratio
        """
        crop_set_crop_ratio(self, ratio)

    def apply_crop(self) -> None:
        """
        Apply the current crop rectangle to the processed images.

        Cross-references:
            - handlers.crop.apply_crop
        """
        crop_apply_crop(self)

    def save_images(self) -> None:
        """
        Handle save button click by opening save dialog and saving images.

        Args:
            self (MainWindow): The instance of the main window.

        Returns:
            None
        """
        # Set mode to Saving before starting operation
        self.status_handler.update_mode_from_state(3, False, True)

        success, msg = save_image_with_dialog(self)

        # Restore appropriate mode after saving
        self._update_mode_from_state()

        if success:
            self.status_handler.set_message("Image saved successfully")
        else:
            self.status_handler.set_message(msg)

    def reset_to_defaults(self) -> None:
        """
        Reset the entire application to its default state.

        This method:
        - Clears all loaded images (original, aligned, processed, RGB)
        - Resets all channel sliders to default values
        - Clears crop settings and exits crop mode
        - Resets display mode to combined view
        - Clears the main viewer
        - Updates all UI elements to reflect the reset state

        Args:
            self (MainWindow): The instance of the main window.

        Returns:
            None
        """
        # Handle UI cleanup before state reset (crop mode needs UI update first)
        if self.state.crop_mode:
            self.crop_mode_btn.setVisible(True)
            self.crop_controls.setVisible(False)
            self.viewer.set_crop_mode(False)

        # Reset all mutable state to defaults
        self.state.reset()

        # Clear saved crop from viewer
        if self.viewer:
            self.viewer.set_saved_crop_rect(None)
            self.viewer.set_crop_rect(None)

        # Reset crop ratio combo box to "Free"
        self.crop_controls.reset()

        # Reset all channel controllers
        for controller in self.controllers:
            controller.reset_all_sliders()
            controller.clear_image()

        # Clear the main viewer
        if self.viewer:
            self.viewer.clear_image()

        # Update UI state (manages save and crop button states, and mode indicator)
        self.update_save_button_state()

        clear_autosave(self)

        # Show status message
        self.status_handler.set_message("Application reset to default state", self.status_handler.MEDIUM_TIMEOUT)

    def open_grid_settings(self) -> None:
        """Open the grid settings dialog as an overlay.

        Returns:
            None

        Cross-references:
            - handlers.grid.open_grid_settings
        """
        grid_open_settings(self)

    def on_grid_type_changed(self, grid_type: str) -> None:
        """Handle grid type selection change.

        Args:
            grid_type: The selected grid type (grid type constant).

        Returns:
            None

        Cross-references:
            - handlers.grid.on_grid_type_changed
        """
        grid_on_type_changed(self, grid_type)

    def on_grid_line_width_changed(self, width: int) -> None:
        """Handle grid line width change.

        Args:
            width: The new line width in pixels.

        Returns:
            None

        Cross-references:
            - handlers.grid.on_grid_line_width_changed
        """
        grid_on_line_width_changed(self, width)

    def _schedule_autosave(self) -> None:
        """Restart the debounce timer so autosave fires 500 ms after the last slider change."""
        self._autosave_timer.start()

    def _on_preview_clicked(self, index: int) -> None:
        """
        Handle preview label click event.

        Args:
            index: Index of the channel whose preview was clicked (0=red, 1=green, 2=blue).
        """
        channel_name = self.controllers[index].channel_name
        self.status_handler.set_message(
            f"Viewing {channel_name.capitalize()} channel", self.status_handler.MEDIUM_TIMEOUT
        )
        show_single_channel(self, index)

    def update_save_button_state(self) -> None:
        """Update save and crop button states based on loaded images."""
        self.save_btn.setEnabled(self.svc.has_aligned_channels())
        self.crop_mode_btn.setEnabled(self.svc.has_processed_channels())
        self._update_mode_from_state()

    def closeEvent(self, event: Union[QCloseEvent, None]) -> None:  # pylint: disable=C0103
        """
        Prompt the user to save session state when closing the window.

        If the user chooses not to save, the autosave file is cleared so the
        next launch opens with a clean state. Choosing Cancel aborts the close.

        Args:
            event: The close event.
        """
        if event is None:
            return
        if self.svc.has_processed_channels():
            reply = QMessageBox.question(
                self,
                "Save Session",
                "Save session state for next launch?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,  # type: ignore[attr-defined]
                QMessageBox.Yes,  # type: ignore[attr-defined]
            )
            if reply == QMessageBox.Cancel:  # type: ignore[attr-defined]
                event.ignore()
                return
            if reply == QMessageBox.No:  # type: ignore[attr-defined]
                clear_autosave(self)
        event.accept()

    def keyPressEvent(self, event: Union[QKeyEvent, None]) -> None:  # pylint: disable=C0103
        """
        Handle key press events for channel switching and display mode.

        Args:
            self (MainWindow): The instance of the main window.
            event (QKeyEvent): The key press event.

        Returns:
            None

        Delegates to handle_key_press; falls back to default if not handled.

        Cross-references:
            - handlers.keyboard.handle_key_press
            - toggle_crop_mode
            - cancel_crop
            - apply_crop
        """
        if event is None:
            return
        if self.state.crop_mode:
            if event.key() == Qt.Key.Key_Escape:
                self.cancel_crop()
            elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.apply_crop()
            # Do not allow toggling crop mode with 'C' while in crop mode
            else:
                super().keyPressEvent(event)
        else:
            if event.key() == Qt.Key.Key_C:
                self.toggle_crop_mode()
            elif not handle_key_press(self, event):
                super().keyPressEvent(event)
