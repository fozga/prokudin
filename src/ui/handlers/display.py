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
Display handlers for updating the main image view and channel previews in the application.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

import numpy as np
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPixmap

if TYPE_CHECKING:
    from ..main_window import MainWindow

from ..core.image_processing import combine_channels
from ..ui.qt_utils import convert_to_qimage


def update_main_display(main_window: "MainWindow") -> None:
    """
    Updates the main display of the application based on the current state of the main window.

    Args:
        main_window (QMainWindow): The main window object containing the display settings and viewer.

    Returns:
        None
    """
    if main_window.state.show_combined:
        show_combined_image(main_window)
    else:
        show_single_channel_image(main_window)

    # Add null check before accessing pixmap()
    if main_window.viewer.photo is not None and main_window.viewer.photo.pixmap():
        pixmap = main_window.viewer.photo.pixmap()
        main_window.viewer.setSceneRect(QRectF(0, 0, pixmap.width(), pixmap.height()))


def show_combined_image(main_window: "MainWindow") -> None:
    """
    Displays the combined RGB image in the main viewer.

    Args:
        main_window (QMainWindow): Reference to the main application window.

    Returns:
        None
    """
    if any(img is None for img in main_window.state.processed):
        return

    # If not in crop mode and a crop rectangle is set, crop the processed images on-the-fly
    saved_crop_rect = main_window.viewer.get_saved_crop_rect()
    if not main_window.state.crop_mode and saved_crop_rect is not None:
        cropped_channels: List[np.ndarray | None] = []
        for img in main_window.state.processed:
            if img is not None:
                cropped = img[
                    saved_crop_rect.top() : saved_crop_rect.bottom() + 1,
                    saved_crop_rect.left() : saved_crop_rect.right() + 1,
                ].copy()
                cropped_channels.append(cropped)
            else:
                cropped_channels.append(None)
        intensities = [ctrl.sliders["intensity"].value() for ctrl in main_window.controllers]
        combined = combine_channels(cropped_channels, intensities)
        q_img = convert_to_qimage(combined)
        main_window.viewer.set_image(QPixmap.fromImage(q_img))
        return

    # Otherwise use full images
    channels: List[np.ndarray | None] = []
    for img in main_window.state.processed:
        if img is not None:
            channels.append(img.copy())
        else:
            channels.append(None)

    intensities = [ctrl.sliders["intensity"].value() for ctrl in main_window.controllers]
    combined = combine_channels(channels, intensities)

    if combined is not None:
        q_img = convert_to_qimage(combined)
        main_window.viewer.set_image(QPixmap.fromImage(q_img))


def show_single_channel_image(main_window: "MainWindow") -> None:
    """
    Displays a single selected channel as a grayscale image in the main viewer.

    Args:
        main_window (QMainWindow): Reference to the main application window.

    Returns:
        None
    """
    img = main_window.state.processed[main_window.state.current_channel]
    if img is not None:
        # If not in crop mode and a crop rectangle is set, crop the processed image on-the-fly
        saved_crop_rect = main_window.viewer.get_saved_crop_rect()
        if not main_window.state.crop_mode and saved_crop_rect is not None:
            img = img[
                saved_crop_rect.top() : saved_crop_rect.bottom() + 1,
                saved_crop_rect.left() : saved_crop_rect.right() + 1,
            ].copy()

        # Convert to RGB (by stacking the same channel 3 times)
        rgb_img = np.stack([img] * 3, axis=-1)

        # Convert to QImage and display
        q_img = convert_to_qimage(rgb_img)
        main_window.viewer.set_image(QPixmap.fromImage(q_img))
