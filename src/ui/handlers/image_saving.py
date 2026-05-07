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

"""Handlers for saving processed images to files."""

import os
import re
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple

import cv2
import numpy as np
from PyQt5.QtWidgets import QFileDialog

if TYPE_CHECKING:
    from ..main_window import MainWindow


def apply_crop(image: np.ndarray, crop_rect: Optional[Tuple[int, int, int, int]]) -> np.ndarray:
    """Apply crop rectangle to an image.

    Args:
        image: NumPy array containing the image data
        crop_rect: Crop region as (x, y, width, height) or None

    Returns:
        Cropped image as NumPy array
    """
    if image is None or image.size == 0:
        return np.array([])

    if crop_rect is None:
        return image

    x, y, w, h = crop_rect

    img_h, img_w = image.shape[:2]
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))

    return image[y : y + h, x : x + w]


def _extract_extension_from_filter(filter_str: str) -> Optional[str]:
    """Extract the first file extension from a filter string."""
    match = re.search(r"\*\.([a-zA-Z0-9]+)", filter_str)
    if match:
        return match.group(1).lower()
    return None


def _get_file_path_info(main_window: "MainWindow", file_filters: str) -> Tuple[Optional[str], Optional[str]]:
    """Handle file dialog and path extraction."""
    filepath, selected_filter = QFileDialog.getSaveFileName(main_window, "Save Images", "", file_filters)

    if not filepath:
        return None, None

    _, extension = os.path.splitext(filepath)

    if not extension:
        default_ext = _extract_extension_from_filter(selected_filter)
        if default_ext:
            filepath = f"{filepath}.{default_ext}"
            extension = f".{default_ext}"
        else:
            return filepath, None

    file_format = extension[1:].lower()
    return filepath, file_format


def _save_cropped_images(
    images: Sequence[Optional[np.ndarray]],
    filepath: str,
    channel_names: List[str],
    crop_rect: Optional[Tuple[int, int, int, int]],
    file_format: str,
) -> List[Tuple[bool, str]]:
    """Save individual cropped channel images."""
    results = []
    filename_without_ext, extension = os.path.splitext(filepath)

    for idx, img in enumerate(images):
        if img is not None:
            img_to_save = apply_crop(img, crop_rect)
            channel_path = f"{filename_without_ext}_{channel_names[idx]}{extension}"
            success, message = save_image(img_to_save, channel_path, file_format, is_bgr=True)
            results.append((success, message))

    return results


def _create_combined_image(
    aligned_images: Sequence[Optional[np.ndarray]], crop_rect: Optional[Tuple[int, int, int, int]]
) -> Optional[np.ndarray]:
    """Create a combined RGB image from aligned grayscale channels."""
    available_channels = [img is not None for img in aligned_images]

    if not any(available_channels):
        return None

    img_shape = None
    for img in aligned_images:
        if img is not None:
            img_shape = img.shape
            break

    if img_shape is None:
        return None

    r_channel = np.zeros(img_shape, dtype=np.uint8)
    g_channel = np.zeros(img_shape, dtype=np.uint8)
    b_channel = np.zeros(img_shape, dtype=np.uint8)

    channels = [r_channel, g_channel, b_channel]
    for i, img in enumerate(aligned_images):
        if img is not None:
            channels[i] = apply_crop(img, crop_rect) if crop_rect else img

    return cv2.merge([channels[2], channels[1], channels[0]])  # pylint: disable=E1101


def save_image_with_dialog(main_window: "MainWindow") -> Tuple[bool, str]:
    """Open file dialog and save combined image plus individual channel images."""
    if not main_window.svc.has_aligned_channels():
        return False, "No images to save"

    file_filters = "JPEG (*.jpg);;TIFF (*.tif);;PNG (*.png);;All Files (*)"
    filepath, file_format = _get_file_path_info(main_window, file_filters)

    if not filepath:
        return False, "Save operation cancelled"

    if not file_format:
        return False, "No file extension provided or determined from filter"

    saved_crop_rect = main_window.viewer.get_saved_crop_rect() if main_window.viewer else None
    crop_rect = (
        None
        if main_window.state.crop_mode
        else (
            (saved_crop_rect.left(), saved_crop_rect.top(), saved_crop_rect.width(), saved_crop_rect.height())
            if saved_crop_rect
            else None
        )
    )

    results = []
    channel_names = ["ir", "vis", "uv"]

    if any(img is not None for img in main_window.svc.aligned_rgb):
        results.extend(
            _save_cropped_images(main_window.svc.aligned_rgb, filepath, channel_names, crop_rect, file_format)
        )

    combined = _create_combined_image(main_window.svc.aligned, crop_rect)

    if combined is not None:
        success, message = save_image(combined, filepath, file_format, is_bgr=False)
        results.append((success, message))

    success_count = sum(1 for success, _ in results if success)

    if success_count == 0:
        return False, "Failed to save any images"
    if success_count < len(results):
        return True, f"Saved {success_count} out of {len(results)} images"
    return True, f"Successfully saved all images to {os.path.dirname(filepath)}"


def save_image(
    image: np.ndarray, filepath: Optional[str] = None, file_format: Optional[str] = None, is_bgr: bool = False
) -> Tuple[bool, str]:
    """Save a NumPy array image to a file."""
    if image is None or image.size == 0:
        return False, "No image data to save"

    if filepath is None:
        return False, "No filepath provided"

    if file_format is None:
        _, extension = os.path.splitext(filepath)
        if not extension:
            return False, "No file extension provided and no format specified"
        file_format = extension[1:].lower()

    try:
        if is_bgr and len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # pylint: disable=E1101

        if file_format in ["jpg", "jpeg"]:
            success = cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])  # pylint: disable=E1101
        elif file_format == "png":
            success = cv2.imwrite(filepath, image, [cv2.IMWRITE_PNG_COMPRESSION, 9])  # pylint: disable=E1101
        elif file_format in ["tif", "tiff"]:
            success = cv2.imwrite(filepath, image)  # pylint: disable=E1101
        else:
            success = cv2.imwrite(filepath, image)  # pylint: disable=E1101

        if success:
            return True, filepath
        return False, f"Failed to save image to {filepath}"

    except (FileNotFoundError, PermissionError) as e:
        return False, f"Error saving image: {str(e)}"
