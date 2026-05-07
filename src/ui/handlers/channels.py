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

"""Handlers for loading, adjusting, and displaying individual color channels."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..main_window import MainWindow

from .display import update_main_display
from .image_loading import load_raw_image, load_raw_image_from_path

_CHANNEL_NAMES = {0: "Red", 1: "Green", 2: "Blue"}


def _process_channel_image(main_window: "MainWindow", channel_idx: int, rgb_image: np.ndarray) -> None:
    """Load an RGB image into the service and update UI after alignment."""
    main_window.svc.load_channel_from_array(channel_idx, rgb_image)

    main_window.status_handler.set_message(
        f"Successfully loaded image into {_CHANNEL_NAMES.get(channel_idx, 'Unknown')} channel",
        main_window.status_handler.MEDIUM_TIMEOUT,
    )

    if main_window.svc.has_aligned_channels():
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
    """Open file dialog and load a raw image for the specified channel."""
    rgb_image, file_path, err_msg = load_raw_image(main_window)

    if rgb_image is not None and file_path is not None:
        main_window.state.channel_paths[channel_idx] = file_path
        _process_channel_image(main_window, channel_idx, rgb_image)
    else:
        if err_msg != "No file selected":
            main_window.status_handler.set_message(
                err_msg or "Failed to load image. Please try again.",
                main_window.status_handler.LONG_TIMEOUT,
            )


def load_channel_from_path(main_window: "MainWindow", channel_idx: int, file_path: str) -> None:
    """Load a channel from a file path without dialog (used for session restore)."""
    rgb_image, err_msg = load_raw_image_from_path(file_path)
    if rgb_image is not None:
        main_window.state.channel_paths[channel_idx] = file_path
        _process_channel_image(main_window, channel_idx, rgb_image)
    elif err_msg:
        main_window.status_handler.set_message(
            f"Failed to restore {_CHANNEL_NAMES.get(channel_idx, 'Unknown')} channel: {err_msg}",
            main_window.status_handler.LONG_TIMEOUT,
        )


def adjust_channel(main_window: "MainWindow", channel_idx: int) -> None:
    """Read slider values and apply brightness/contrast adjustments."""
    if main_window.svc.aligned[channel_idx] is not None:
        main_window.status_handler.set_message("Processing image, please wait...")
        brightness: int = main_window.controllers[channel_idx].sliders["brightness"].value()
        contrast: int = main_window.controllers[channel_idx].sliders["contrast"].value()
        main_window.svc.adjust_channel(channel_idx, brightness, contrast)
        update_channel_preview(main_window, channel_idx)
        update_main_display(main_window)
        main_window.status_handler.set_message("")


def update_channel_preview(main_window: "MainWindow", channel_idx: int) -> None:
    """Update the preview image for a channel controller."""
    controller = main_window.controllers[channel_idx]
    controller.processed_image = main_window.svc.get_channel_preview(channel_idx)  # type: ignore[assignment]
    controller.update_preview()


def show_single_channel(main_window: "MainWindow", channel_idx: int) -> None:
    """Display a single channel in the main viewer."""
    main_window.state.show_combined = False
    main_window.state.current_channel = channel_idx
    update_main_display(main_window)
