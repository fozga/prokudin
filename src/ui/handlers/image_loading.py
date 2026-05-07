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
Image loading utilities for selecting and processing Sony ARW RAW files.
Provides functions to open file dialogs, load RAW images, and convert them for further processing.
"""

from typing import Union

import numpy as np
import rawpy  # type: ignore
from PyQt5.QtWidgets import QFileDialog, QWidget


def load_raw_image_from_path(file_path: str) -> Union[tuple[np.ndarray, None], tuple[None, str]]:
    """
    Load a Sony ARW RAW image from a known file path without opening a file dialog.

    Args:
        file_path (str): Absolute path to the ARW file.

    Returns:
        tuple: Either (numpy.ndarray, None) on success or (None, str) with an error message.
    """
    try:
        with rawpy.imread(file_path) as raw:
            rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=8)
        result: np.ndarray = rgb
        return result, None
    except (
        rawpy.LibRawFileUnsupportedError,  # pylint: disable=E1101
        rawpy.LibRawIOError,  # pylint: disable=E1101
        FileNotFoundError,
        PermissionError,
    ) as e:  # pylint: disable=E1101
        return None, f"Error loading ARW file: {e}"


def load_raw_image(parent: QWidget) -> Union[tuple[np.ndarray, str, None], tuple[None, None, str]]:
    """
    Opens a file dialog for the user to select a Sony ARW RAW image,
    loads the image using rawpy, and processes it to an 8-bit RGB image.

    Args:
        parent (QWidget): The parent widget for the QFileDialog (typically the main window).

    Returns:
        tuple: Either (numpy.ndarray, path, None) on success or (None, None, str) with an error.

    Cross-references:
        - handlers.channels.load_channel
    """
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(parent, "Select ARW File", "", "Sony RAW Files (*.arw)", options=options)

    if not filename:
        return None, None, "No file selected"

    rgb_image, err = load_raw_image_from_path(filename)
    if rgb_image is not None:
        return rgb_image, filename, None
    return None, None, err or "Unknown error"
