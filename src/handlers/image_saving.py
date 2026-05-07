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
Handlers for saving processed images to files.
Provides functions to save images in various formats and handle file dialogs.
"""

import os
import re
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple

import cv2
import numpy as np
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QFileDialog

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ..main_window import MainWindow


def apply_crop(image: np.ndarray, crop_rect: QRect) -> np.ndarray:
    """
    Apply crop rectangle to an image.

    Args:
        image: NumPy array containing the image data
        crop_rect: QRect defining the crop region

    Returns:
        Cropped image as NumPy array
    """
    if image is None or image.size == 0:
        return np.array([])

    if crop_rect is None or not crop_rect.isValid():
        return image

    x, y, w, h = crop_rect.x(), crop_rect.y(), crop_rect.width(), crop_rect.height()

    # Ensure crop rectangle is within image bounds
    img_h, img_w = image.shape[:2]
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))

    cropped_image = image[y : y + h, x : x + w]

    # Apply crop
    return cropped_image


def _extract_extension_from_filter(filter_str: str) -> Optional[str]:
    """
    Extract the first file extension from a filter string.

    Args:
        filter_str: Filter string from QFileDialog (e.g., "JPEG (*.jpg *.jpeg)")

    Returns:
        The first extension found (e.g., "jpg") or None if no extension found
    """
    # Look for the pattern *.ext
    match = re.search(r"\*\.([a-zA-Z0-9]+)", filter_str)
    if match:
        return match.group(1).lower()
    return None


def _get_file_path_info(main_window: "MainWindow", file_filters: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Handle file dialog and path extraction.

    Args:
        main_window: MainWindow instance
        file_filters: String containing file filter options

    Returns:
        Tuple containing filepath and format
    """
    filepath, selected_filter = QFileDialog.getSaveFileName(main_window, "Save Images", "", file_filters)

    if not filepath:
        return None, None

    # Check if file has extension
    _, extension = os.path.splitext(filepath)

    # If no extension provided, get it from the selected filter
    if not extension:
        default_ext = _extract_extension_from_filter(selected_filter)
        if default_ext:
            filepath = f"{filepath}.{default_ext}"
            extension = f".{default_ext}"
        else:
            return filepath, None

    file_format = extension[1:].lower()  # Remove the dot and convert to lowercase
    return filepath, file_format


def _save_cropped_images(
    images: Sequence[Optional[np.ndarray]],
    filepath: str,
    channel_names: List[str],
    crop_rect: Optional[QRect],
    file_format: str,
) -> List[Tuple[bool, str]]:
    """
    Save individual cropped channel images.

    Args:
        images: Sequence of channel images (may contain None values)
        filepath: Full filepath including extension
        channel_names: List of channel name suffixes
        crop_rect: Optional crop rectangle
        file_format: Format for saving (jpg, png, etc.)

    Returns:
        List of (success, message) tuples
    """
    results = []

    # Get the filename without extension and the extension
    filename_without_ext, extension = os.path.splitext(filepath)

    for idx, img in enumerate(images):
        if img is not None:
            # Apply crop if needed
            img_to_save = apply_crop(img, crop_rect) if crop_rect and crop_rect.isValid() else img.copy()

            # Create filename with channel suffix
            channel_path = f"{filename_without_ext}_{channel_names[idx]}{extension}"
            success, message = save_image(img_to_save, channel_path, file_format, is_bgr=True)
            results.append((success, message))

    return results


def _create_combined_image(
    aligned_images: Sequence[Optional[np.ndarray]], crop_rect: Optional[QRect]
) -> Optional[np.ndarray]:
    """
    Create a combined RGB image from aligned grayscale channels.

    Args:
        aligned_images: Sequence of grayscale channel images (may contain None values)
        crop_rect: Optional crop rectangle

    Returns:
        Combined RGB image or None if no valid channels
    """
    available_channels = [img is not None for img in aligned_images]

    if not any(available_channels):
        return None

    # Find first valid image to get dimensions
    img_shape = None
    for img in aligned_images:
        if img is not None:
            img_shape = img.shape
            break

    if img_shape is None:
        return None

    # Initialize empty channels
    r_channel = np.zeros(img_shape, dtype=np.uint8)
    g_channel = np.zeros(img_shape, dtype=np.uint8)
    b_channel = np.zeros(img_shape, dtype=np.uint8)

    # Fill in available channels with cropped versions
    channels = [r_channel, g_channel, b_channel]
    for i, img in enumerate(aligned_images):
        if img is not None:
            channels[i] = apply_crop(img, crop_rect) if crop_rect and crop_rect.isValid() else img

    # Combine BGR channels (OpenCV uses BGR order)
    return cv2.merge([channels[2], channels[1], channels[0]])  # pylint: disable=E1101


def save_image_with_dialog(main_window: "MainWindow") -> Tuple[bool, str]:
    """
    Open a file dialog to get a filepath and save combined image plus individual channel images.

    Saves:
    - base_name.ext for combined RGB image
    - base_name_r.ext for red channel
    - base_name_g.ext for green channel
    - base_name_b.ext for blue channel

    Args:
        main_window: MainWindow instance containing aligned and processed images

    Returns:
        Tuple containing:
            - Boolean indicating success or failure
            - String with status message
    """
    # Check if there are any images to save
    if not any(img is not None for img in main_window.state.aligned):
        return False, "No images to save"

    # Create file format options
    file_filters = "JPEG (*.jpg);;TIFF (*.tif);;PNG (*.png);;All Files (*)"

    # Get file path info
    filepath, file_format = _get_file_path_info(main_window, file_filters)

    if not filepath:
        return False, "Save operation cancelled"

    if not file_format:
        return False, "No file extension provided or determined from filter"

    # Get crop rectangle if available
    crop_rect = main_window.viewer.get_saved_crop_rect() if main_window.viewer else None

    results = []
    channel_names = ["ir", "vis", "uv"]

    # Save RGB channel images if available
    if any(img is not None for img in main_window.state.aligned_rgb):
        results.extend(
            _save_cropped_images(main_window.state.aligned_rgb, filepath, channel_names, crop_rect, file_format)
        )

    # Create and save combined image from grayscale channels
    combined = _create_combined_image(main_window.state.aligned, crop_rect)

    if combined is not None:
        success, message = save_image(combined, filepath, file_format, is_bgr=False)
        results.append((success, message))

    # Create a summary message
    success_count = sum(1 for success, _ in results if success)

    if success_count == 0:
        return False, "Failed to save any images"
    if success_count < len(results):
        return True, f"Saved {success_count} out of {len(results)} images"
    return True, f"Successfully saved all images to {os.path.dirname(filepath)}"


def save_image(
    image: np.ndarray, filepath: Optional[str] = None, file_format: Optional[str] = None, is_bgr: bool = False
) -> Tuple[bool, str]:
    """
    Save a NumPy array image to a file.

    Args:
        image: NumPy array containing the image data to save
        filepath: Path to save the file to. Required.
        file_format: Optional format override (e.g., 'jpg', 'png', 'tiff')
        is_bgr: Whether the input image is in RGB format (needs conversion to BGR)

    Returns:
        Tuple containing:
            - Boolean indicating success or failure
            - String with filepath if successful, error message if failed
    """
    if image is None or image.size == 0:
        return False, "No image data to save"

    # Check if filepath is provided
    if filepath is None:
        return False, "No filepath provided"

    # Determine format from extension if not explicitly provided
    if file_format is None:
        _, extension = os.path.splitext(filepath)
        if not extension:
            return False, "No file extension provided and no format specified"
        file_format = extension[1:].lower()  # Remove the dot and convert to lowercase

    try:
        # Convert from RGB to BGR if needed (OpenCV uses BGR)
        if is_bgr and len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # pylint: disable=E1101

        # Handle image format based on extension
        if file_format in ["jpg", "jpeg"]:
            success = cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, 95])  # pylint: disable=E1101
        elif file_format == "png":
            success = cv2.imwrite(filepath, image, [cv2.IMWRITE_PNG_COMPRESSION, 9])  # pylint: disable=E1101
        elif file_format in ["tif", "tiff"]:
            success = cv2.imwrite(filepath, image)  # pylint: disable=E1101
        else:
            # Default case - try to save with the given extension
            success = cv2.imwrite(filepath, image)  # pylint: disable=E1101

        if success:
            return True, filepath
        return False, f"Failed to save image to {filepath}"

    except (
        FileNotFoundError,
        PermissionError,
    ) as e:
        return False, f"Error saving image: {str(e)}"
