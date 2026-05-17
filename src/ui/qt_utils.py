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

"""Qt utilities for converting numpy images to QImage and positioning popup widgets."""

from typing import Union

import numpy as np
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget


def convert_to_qimage(image: Union[np.ndarray, None]) -> QImage:
    """Convert numpy image to QImage for PyQt5 display.

    Args:
        image (numpy.ndarray | None):
            - Grayscale: HxW (uint8)
            - RGB: HxWx3 (uint8)
            Arrays may be non-contiguous; they will be copied to C-contiguous
            layout if necessary.

    Returns:
        QImage: Empty QImage if input invalid, otherwise formatted image.

    Cross-references:
        - ui.handlers.display.show_combined_image
        - ui.handlers.display.show_single_channel_image
    """
    if image is None:
        return QImage()

    # Ensure C-contiguous layout for QImage compatibility
    if not image.flags["C_CONTIGUOUS"]:
        image = np.ascontiguousarray(image)

    if len(image.shape) == 2:  # Grayscale
        fmt = QImage.Format_Grayscale8
        return QImage(bytes(image.tobytes()), image.shape[1], image.shape[0], image.strides[0], fmt)

    fmt = QImage.Format_RGB888
    return QImage(bytes(image.tobytes()), image.shape[1], image.shape[0], image.strides[0], fmt)


def position_popup_near_button(popup: QWidget, button: QPushButton, margin: int = 10) -> None:
    """Position a popup widget near a button with intelligent screen boundary handling.

    Attempts to position popup to the right of button, above it. Falls back to left
    if right goes off-screen, or below if above goes off-screen. Clamps to screen
    edges if both horizontal or both vertical positions exceed boundaries.

    Args:
        popup: The popup widget to position (dialog, frame, etc.).
        button: The button to position relative to.
        margin: Distance in pixels between button and popup (default 10).

    Returns:
        None. Popup position is updated in-place via popup.move().

    Cross-references:
        - ui.handlers.grid.open_grid_settings
        - ui.main_window.MainWindow.open_grid_settings
    """
    button_pos = button.mapToGlobal(button.rect().topLeft())

    screen = button.screen()
    if screen:
        screen_geometry = screen.availableGeometry()
    else:
        screen_geometry = QApplication.desktop().availableGeometry()  # type: ignore[union-attr]

    popup_width = popup.width()
    popup_height = popup.height()

    dialog_x = button_pos.x() + button.width() + margin
    dialog_y = button_pos.y() - popup_height

    if dialog_x + popup_width > screen_geometry.right():
        dialog_x = button_pos.x() - popup_width - margin

    if dialog_x < screen_geometry.left():
        dialog_x = screen_geometry.left() + margin

    if dialog_y < screen_geometry.top():
        dialog_y = button_pos.y() + button.height() + margin

    if dialog_y + popup_height > screen_geometry.bottom():
        dialog_y = screen_geometry.bottom() - popup_height - margin

    popup.move(dialog_x, dialog_y)
