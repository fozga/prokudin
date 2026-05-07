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
Handlers for loading, adjusting, and displaying individual color channels in the application.
Provides functions to load raw images, apply adjustments, update previews, and manage display modes.
"""

from __future__ import annotations

# Standard library imports
from typing import TYPE_CHECKING, List, Optional, cast

# Third-party imports
import cv2
import numpy as np

# Conditional imports for type checking
if TYPE_CHECKING:
    from ..main_window import MainWindow

# Local application imports
from ..core.align import align_images
from ..core.image_processing import apply_adjustments
from .display import update_main_display
from .image_loading import load_raw_image, load_raw_image_from_path

_CHANNEL_NAMES = {0: "Red", 1: "Green", 2: "Blue"}


def _process_channel_image(main_window: "MainWindow", channel_idx: int, rgb_image: np.ndarray) -> None:
    """Store and process a loaded RGB image for the given channel, triggering alignment when all 3 are ready."""

    original_rgb_images: List[Optional[np.ndarray]] = list(main_window.original_rgb_images)
    original_rgb_images[channel_idx] = rgb_image
    main_window.original_rgb_images = original_rgb_images  # type: ignore

    image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)  # pylint: disable=E1101

    original_images: List[Optional[np.ndarray]] = list(main_window.original_images)
    processed: List[Optional[np.ndarray]] = list(main_window.processed)

    original_images[channel_idx] = image
    processed[channel_idx] = image.copy()

    main_window.original_images = original_images  # type: ignore
    main_window.processed = processed  # type: ignore

    main_window.status_handler.set_message(
        f"Successfully loaded image into {_CHANNEL_NAMES.get(channel_idx, 'Unknown')} channel",
        main_window.status_handler.MEDIUM_TIMEOUT,
    )

    if all(img is not None for img in main_window.original_images):
        gray_images: List[np.ndarray] = []
        rgb_images: List[np.ndarray] = []

        for i in range(3):
            if main_window.original_images[i] is not None and main_window.original_rgb_images[i] is not None:
                gray_img = cast(np.ndarray, main_window.original_images[i])
                rgb_img = cast(np.ndarray, main_window.original_rgb_images[i])
                gray_images.append(gray_img)
                rgb_images.append(rgb_img)

        if len(gray_images) == 3 and len(rgb_images) == 3:
            main_window.status_handler.set_message("Aligning images, please wait...")
            aligned_gray, aligned_rgb = align_images(gray_images, rgb_images)

            main_window.aligned = aligned_gray  # type: ignore
            main_window.aligned_rgb = aligned_rgb  # type: ignore

            new_processed: List[Optional[np.ndarray]] = [img.copy() for img in aligned_gray]
            main_window.processed = new_processed  # type: ignore

            for i in range(3):
                adjust_channel(main_window, i)
                update_channel_preview(main_window, i)
            main_window.status_handler.set_message(
                "All channels loaded successfully - Ready for editing!", main_window.status_handler.NO_TIMEOUT
            )
    else:
        update_channel_preview(main_window, channel_idx)

    update_main_display(main_window)
    main_window.update_save_button_state()


def load_channel(main_window: "MainWindow", channel_idx: int) -> None:
    """
    Opens a file dialog, loads a raw image for the specified channel, and updates application state.

    Args:
        main_window (MainWindow): Reference to the main application window.
        channel_idx (int): Index of the channel to load (0=R, 1=G, 2=B).
    """
    rgb_image, file_path, err_msg = load_raw_image(main_window)

    if rgb_image is not None and file_path is not None:
        main_window.channel_paths[channel_idx] = file_path
        _process_channel_image(main_window, channel_idx, rgb_image)
    else:
        if err_msg != "No file selected":
            main_window.status_handler.set_message(
                err_msg or "Failed to load image. Please try again.",
                main_window.status_handler.LONG_TIMEOUT,
            )


def load_channel_from_path(main_window: "MainWindow", channel_idx: int, file_path: str) -> None:
    """
    Load a channel from a known file path without opening a dialog (used for session restore).

    Args:
        main_window (MainWindow): Reference to the main application window.
        channel_idx (int): Index of the channel to load (0=R, 1=G, 2=B).
        file_path (str): Absolute path to the ARW file.
    """
    rgb_image, err_msg = load_raw_image_from_path(file_path)
    if rgb_image is not None:
        main_window.channel_paths[channel_idx] = file_path
        _process_channel_image(main_window, channel_idx, rgb_image)
    elif err_msg:
        main_window.status_handler.set_message(
            f"Failed to restore {_CHANNEL_NAMES.get(channel_idx, 'Unknown')} channel: {err_msg}",
            main_window.status_handler.LONG_TIMEOUT,
        )


def adjust_channel(main_window: "MainWindow", channel_idx: int) -> None:
    """
    Applies brightness and contrast adjustments to the specified channel and updates its preview.

    Args:
        main_window ("MainWindow"): Reference to the main application window.
        channel_idx (int): Index of the channel to adjust (0=R, 1=G, 2=B).

    Returns:
        None

    Cross-references:
        - apply_adjustments
        - update_channel_preview
        - update_main_display
    """
    if main_window.aligned[channel_idx] is not None:
        main_window.status_handler.set_message("Processing image, please wait...")
        brightness: int = main_window.controllers[channel_idx].sliders["brightness"].value()
        contrast: int = main_window.controllers[channel_idx].sliders["contrast"].value()
        result = apply_adjustments(main_window.aligned[channel_idx], brightness, contrast)
        if result is not None:
            # Create a new list to avoid assignment issues
            processed: List[Optional[np.ndarray]] = list(main_window.processed)
            processed[channel_idx] = result
            main_window.processed = processed  # type: ignore

            update_channel_preview(main_window, channel_idx)
            update_main_display(main_window)
        main_window.status_handler.set_message("")  # No timeout needed for clearing message


def update_channel_preview(main_window: "MainWindow", channel_idx: int) -> None:
    """
    Updates the preview image for a specific channel controller.

    Args:
        main_window ("MainWindow"): Reference to the main application window.
        channel_idx (int): Index of the channel to update (0=R, 1=G, 2=B).

    Returns:
        None

    Cross-references:
        - ChannelController.update_preview
    """
    controller = main_window.controllers[channel_idx]
    controller.processed_image = main_window.processed[channel_idx]
    controller.update_preview()


def show_single_channel(main_window: "MainWindow", channel_idx: int) -> None:
    """
    Updates the main window to display a single channel.

    This function sets the main window to show only the specified channel
    by disabling the combined view and updating the current channel index.
    It then refreshes the main display to reflect the changes.

    Args:
        main_window ("MainWindow"): Reference to the main application window.
        channel_idx (int): Index of the channel to display (0=R, 1=G, 2=B).

    Returns:
        None

    Cross-references:
        - update_main_display
    """
    main_window.show_combined = False
    main_window.current_channel = channel_idx
    update_main_display(main_window)
