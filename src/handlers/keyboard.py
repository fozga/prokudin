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
Keyboard shortcut handlers for channel switching and display modes in the application.
"""

from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent

from .display import update_main_display

if TYPE_CHECKING:
    from ..main_window import MainWindow


def handle_key_press(main_window: "MainWindow", event: QKeyEvent) -> bool:
    """
    Handles keyboard shortcuts for channel switching and display modes.

    Args:
        main_window (QMainWindow): Reference to the main application window.
        event (QKeyEvent): QKeyEvent from PyQt5's key press handler.

    Returns:
        bool: True if the key was handled, False otherwise (allows event propagation).

    Key Bindings:
        - 1: Show Red channel (index 0)
        - 2: Show Green channel (index 1)
        - 3: Show Blue channel (index 2)
        - A: Show combined RGB view

    Behavior:
        - Updates display state in main_window
        - Calls update_main_display() to refresh the UI
        - Accepts the event if handled to prevent further propagation

    Cross-references:
        - update_main_display
        - main_window.MainWindow
    """
    if event.key() == Qt.Key.Key_1:
        main_window.state.show_combined = False
        main_window.state.current_channel = 0
        main_window.status_handler.set_message("Viewing Red channel", main_window.status_handler.MEDIUM_TIMEOUT)
        update_main_display(main_window)
        event.accept()
        return True
    if event.key() == Qt.Key.Key_2:
        main_window.state.show_combined = False
        main_window.state.current_channel = 1
        main_window.status_handler.set_message("Viewing Green channel", main_window.status_handler.MEDIUM_TIMEOUT)
        update_main_display(main_window)
        event.accept()
        return True
    if event.key() == Qt.Key.Key_3:
        main_window.state.show_combined = False
        main_window.state.current_channel = 2
        main_window.status_handler.set_message("Viewing Blue channel", main_window.status_handler.MEDIUM_TIMEOUT)
        update_main_display(main_window)
        event.accept()
        return True
    if event.key() == Qt.Key.Key_A:
        main_window.state.show_combined = True
        main_window.status_handler.set_message(
            "Viewing combined RGB channel", main_window.status_handler.MEDIUM_TIMEOUT
        )
        update_main_display(main_window)
        event.accept()
        return True
    return False
