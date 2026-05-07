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

"""Display handlers for updating the main image view."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPixmap

if TYPE_CHECKING:
    from ..main_window import MainWindow

from ..qt_utils import convert_to_qimage


def update_main_display(main_window: "MainWindow") -> None:
    """Update the main display based on current show_combined state."""
    if main_window.state.show_combined:
        show_combined_image(main_window)
    else:
        show_single_channel_image(main_window)

    if main_window.viewer.photo is not None and main_window.viewer.photo.pixmap():
        pixmap = main_window.viewer.photo.pixmap()
        main_window.viewer.setSceneRect(QRectF(0, 0, pixmap.width(), pixmap.height()))


def _qrect_to_tuple(qrect) -> Optional[Tuple[int, int, int, int]]:  # type: ignore
    """Convert QRect to (x, y, width, height) tuple."""
    if qrect is None:
        return None
    return (qrect.left(), qrect.top(), qrect.width(), qrect.height())


def show_combined_image(main_window: "MainWindow") -> None:
    """Display the combined RGB image in the main viewer."""
    saved_crop_rect = main_window.viewer.get_saved_crop_rect()
    crop_tuple = None if main_window.state.crop_mode else _qrect_to_tuple(saved_crop_rect)
    intensities = [ctrl.sliders["intensity"].value() for ctrl in main_window.controllers]

    combined = main_window.svc.get_combined(crop=crop_tuple, intensities=intensities)
    if combined is not None:
        q_img = convert_to_qimage(combined)
        main_window.viewer.set_image(QPixmap.fromImage(q_img))


def show_single_channel_image(main_window: "MainWindow") -> None:
    """Display a single selected channel as grayscale in the main viewer."""
    saved_crop_rect = main_window.viewer.get_saved_crop_rect()
    crop_tuple = None if main_window.state.crop_mode else _qrect_to_tuple(saved_crop_rect)

    img = main_window.svc.get_channel(main_window.state.current_channel, crop=crop_tuple)
    if img is not None:
        rgb_img = np.stack([img] * 3, axis=-1)
        q_img = convert_to_qimage(rgb_img)
        main_window.viewer.set_image(QPixmap.fromImage(q_img))
