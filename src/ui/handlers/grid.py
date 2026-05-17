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

"""Handlers for grid overlay settings and positioning."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main_window import MainWindow

from ..qt_utils import position_popup_near_button
from ..widgets.grid_settings_dialog import GridSettingsDialog
from ..widgets.grid_types import GRID_TYPE_NONE


def open_grid_settings(main_window: MainWindow) -> None:
    """Open the grid settings dialog as an overlay near the grid button.

    Creates and positions the GridSettingsDialog if it doesn't already exist,
    connects grid type and line width changed signals, and positions the dialog
    near the grid button with screen boundary checks.

    Args:
        main_window: The MainWindow instance.

    Returns:
        None

    Cross-references:
        - ui.widgets.grid_settings_dialog.GridSettingsDialog
        - ui.qt_utils.position_popup_near_button
    """
    if main_window.state.grid_settings_dialog is None:
        current_width = main_window.viewer.grid_overlay.get_line_width()

        if main_window.viewer.grid_overlay.is_enabled():
            current_type = main_window.viewer.grid_overlay.get_grid_type()
        else:
            current_type = GRID_TYPE_NONE

        main_window.state.grid_settings_dialog = GridSettingsDialog(
            current_width=current_width, current_grid_type=current_type, parent=main_window
        )

        main_window.state.grid_settings_dialog.grid_type_changed.connect(
            lambda grid_type: on_grid_type_changed(main_window, grid_type)
        )
        main_window.state.grid_settings_dialog.line_width_changed.connect(
            lambda width: on_grid_line_width_changed(main_window, width)
        )

    position_popup_near_button(main_window.state.grid_settings_dialog, main_window.grid_btn)

    main_window.state.grid_settings_dialog.show()
    main_window.state.grid_settings_dialog.raise_()


def on_grid_type_changed(main_window: MainWindow, grid_type: str) -> None:
    """Handle grid type selection change.

    Enables or disables the grid overlay based on grid type selection, updates
    the grid overlay type, and displays a status message reflecting the change.

    Args:
        main_window: The MainWindow instance.
        grid_type: The selected grid type string.

    Returns:
        None

    Cross-references:
        - ui.main_window.MainWindow.GRID_TYPE_STATUS_MESSAGES
    """
    if grid_type == GRID_TYPE_NONE:
        main_window.viewer.grid_overlay.set_enabled(False)
        main_window.status_handler.set_message("Grid overlay disabled", main_window.status_handler.SHORT_TIMEOUT)
    else:
        message = main_window.GRID_TYPE_STATUS_MESSAGES.get(grid_type)
        if message is None:
            main_window.viewer.grid_overlay.set_enabled(False)
            main_window.status_handler.set_message(
                "Unsupported grid type selected", main_window.status_handler.SHORT_TIMEOUT
            )
            main_window.viewer.viewport().update()  # type: ignore[union-attr]
            return

        main_window.viewer.grid_overlay.set_enabled(True)
        try:
            main_window.viewer.grid_overlay.set_grid_type(grid_type)
        except ValueError:
            main_window.viewer.grid_overlay.set_enabled(False)
            main_window.status_handler.set_message(
                "Unsupported grid type selected", main_window.status_handler.SHORT_TIMEOUT
            )
            main_window.viewer.viewport().update()  # type: ignore[union-attr]
            return
        main_window.status_handler.set_message(message, main_window.status_handler.SHORT_TIMEOUT)

    main_window.viewer.viewport().update()  # type: ignore[union-attr]


def on_grid_line_width_changed(main_window: MainWindow, width: int) -> None:
    """Handle grid line width change.

    Updates the grid overlay line width and displays a status message showing
    the new width in pixels.

    Args:
        main_window: The MainWindow instance.
        width: The new line width in pixels.

    Returns:
        None
    """
    main_window.viewer.grid_overlay.set_line_width(width)
    main_window.viewer.viewport().update()  # type: ignore[union-attr]
    main_window.status_handler.set_message(f"Grid line width: {width}px", main_window.status_handler.SHORT_TIMEOUT)
