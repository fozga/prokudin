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

"""Qt utilities for converting numpy images to QImage."""

from typing import Union

import numpy as np
from PyQt5.QtGui import QImage


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
    if not image.flags['C_CONTIGUOUS']:
        image = np.ascontiguousarray(image)

    if len(image.shape) == 2:  # Grayscale
        return QImage(bytes(image.tobytes()), image.shape[1], image.shape[0],
                      image.strides[0], QImage.Format_Grayscale8)

    return QImage(bytes(image.tobytes()), image.shape[1], image.shape[0],
                  image.strides[0], QImage.Format_RGB888)
