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

"""Handlers for crop mode orchestration and aspect ratio management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import QRect

from .autosave import save_autosave
from .channels import update_channel_preview
from .display import show_combined_image, show_single_channel_image, update_main_display

if TYPE_CHECKING:
    from ..main_window import MainWindow


def _get_aspect_crop_rect(rect: QRect, ratio: tuple[int, int]) -> QRect:
    """
    Calculate the largest rectangle with the given aspect ratio that fits within the given rect.

    The result is centered at the same point as the original rect.

    Args:
        rect: The bounding rectangle.
        ratio: The desired aspect ratio as (width, height) tuple.

    Returns:
        QRect: The adjusted rectangle maintaining the aspect ratio.
    """
    if not rect or not ratio:
        return rect
    orig_w = rect.width()
    orig_h = rect.height()
    center = rect.center()
    w, h = ratio
    target_ratio = w / h
    # Try to maintain width first
    new_w = orig_w
    new_h = int(new_w / target_ratio)
    if new_h > orig_h:
        new_h = orig_h
        new_w = int(new_h * target_ratio)
    # Center the new rect
    new_left = center.x() - new_w // 2
    new_top = center.y() - new_h // 2
    return QRect(new_left, new_top, new_w, new_h)


def toggle_crop_mode(main_window: MainWindow) -> None:
    """
    Toggle crop mode; initializes default crop rect from image dimensions.

    Args:
        main_window: The MainWindow instance.

    Returns:
        None

    Side effects:
        - Toggles main_window.state.crop_mode to True
        - Hides/shows crop mode button and crop controls widget
        - Initializes crop rectangle from saved state or image dimensions
        - Updates main display and mode indicator
        - Sets status message

    Cross-references:
        - ImageViewer.get_saved_crop_rect, set_crop_mode, set_crop_rect
        - update_main_display, _update_mode_from_state
    """
    if main_window.state.crop_mode:
        return
    if not main_window.svc.has_processed_channels():
        return
    main_window.state.crop_mode = True
    main_window.crop_mode_btn.setVisible(False)
    main_window.crop_controls.setVisible(True)
    saved_crop_rect = main_window.viewer.get_saved_crop_rect() if main_window.viewer else None
    if saved_crop_rect:
        main_window.state.crop_rect = QRect(saved_crop_rect)
    else:
        dims = main_window.svc.get_image_dimensions()
        if dims:
            img_h, img_w = dims
            rect_w = int(img_w * 0.8)
            rect_h = int(img_h * 0.8)
            x = (img_w - rect_w) // 2
            y = (img_h - rect_h) // 2
            main_window.state.crop_rect = QRect(x, y, rect_w, rect_h)
            if main_window.state.crop_ratio and main_window.state.crop_rect is not None:
                main_window.state.crop_rect = _get_aspect_crop_rect(
                    main_window.state.crop_rect, main_window.state.crop_ratio
                )
    main_window.viewer.set_crop_mode(main_window.state.crop_mode)
    if main_window.state.crop_rect:
        main_window.viewer.set_crop_rect(main_window.state.crop_rect)
    update_main_display(main_window)
    main_window._update_mode_from_state()  # pylint: disable=protected-access
    main_window.status_handler.set_message(
        "Crop mode activated - Select region to crop", main_window.status_handler.NO_TIMEOUT
    )


def cancel_crop(main_window: MainWindow) -> None:
    """
    Cancel the current crop operation and exit crop mode.

    Exits crop mode without applying changes. Restores the last saved crop rectangle
    if available.

    Args:
        main_window: The MainWindow instance.

    Returns:
        None

    Side effects:
        - Sets main_window.state.crop_mode to False
        - Hides/shows crop mode button and crop controls widget
        - Restores or clears crop rectangle based on saved state
        - Updates main display and mode indicator
        - Sets status message

    Cross-references:
        - ImageViewer.get_saved_crop_rect, set_crop_mode, set_crop_rect
        - update_main_display, _update_mode_from_state
    """
    main_window.state.crop_mode = False
    main_window.crop_mode_btn.setVisible(True)
    main_window.crop_controls.setVisible(False)
    saved_crop_rect = main_window.viewer.get_saved_crop_rect() if main_window.viewer else None
    if saved_crop_rect:
        main_window.state.crop_rect = QRect(saved_crop_rect)
        main_window.viewer.set_crop_rect(main_window.state.crop_rect)
    else:
        main_window.state.crop_rect = None
    main_window.viewer.set_crop_mode(False)
    update_main_display(main_window)

    # Update mode indicator and status message
    main_window._update_mode_from_state()  # pylint: disable=protected-access
    main_window.status_handler.set_message("Crop operation cancelled", main_window.status_handler.MEDIUM_TIMEOUT)


def set_crop_ratio(main_window: MainWindow, ratio: Optional[tuple[int, int]]) -> None:
    """
    Set the aspect ratio for the crop rectangle.

    Adjusts the crop rectangle to maintain the selected aspect ratio and syncs
    with the viewer.

    Args:
        main_window: The MainWindow instance.
        ratio: The aspect ratio as (width, height) tuple, or None for free aspect.

    Returns:
        None

    Side effects:
        - Updates main_window.state.crop_ratio
        - Adjusts main_window.state.crop_rect to match aspect ratio
        - Updates ImageViewer crop ratio and rectangle
        - Updates main display

    Cross-references:
        - ImageViewer.get_crop_rect, set_crop_ratio, set_crop_rect
        - _get_aspect_crop_rect, update_main_display
    """
    main_window.state.crop_ratio = ratio
    # Always get the current rectangle from the viewer
    current_rect = main_window.viewer.get_crop_rect() if main_window.viewer else main_window.state.crop_rect
    if current_rect and main_window.state.crop_ratio:
        new_rect = _get_aspect_crop_rect(current_rect, main_window.state.crop_ratio)
        main_window.state.crop_rect = new_rect
        main_window.viewer.set_crop_ratio(main_window.state.crop_ratio)
        main_window.viewer.set_crop_rect(new_rect)
        # Keep viewer._crop_rect and self.state.crop_rect in sync
    elif current_rect:
        # Free mode
        main_window.viewer.set_crop_ratio(None)
        main_window.viewer.set_crop_rect(current_rect)
        main_window.state.crop_rect = current_rect
    update_main_display(main_window)


def apply_crop(main_window: MainWindow) -> None:
    """
    Apply the current crop rectangle to the processed images.

    Saves the crop rectangle for future use, exits crop mode, and updates
    channel previews and the main display.

    Args:
        main_window: The MainWindow instance.

    Returns:
        None

    Side effects:
        - Saves crop rectangle to ImageViewer
        - Updates all channel previews
        - Resets main_window.state.crop_mode to False
        - Hides/shows crop mode button and crop controls widget
        - Updates save button state and mode indicator
        - Updates main display (combined or single channel)
        - Triggers autosave

    Cross-references:
        - ImageViewer.get_crop_rect, confirm_crop, set_saved_crop_rect
        - update_channel_preview, show_combined_image, show_single_channel_image
        - update_save_button_state, _update_mode_from_state, save_autosave
    """
    crop_rect = main_window.viewer.get_crop_rect() if main_window.viewer else main_window.state.crop_rect
    if not crop_rect or not main_window.svc.has_processed_channels():
        return

    crop_rect = main_window.viewer.get_crop_rect()
    saved_rect = QRect(crop_rect) if crop_rect is not None else None
    if saved_rect is None:
        return

    dims = main_window.svc.get_image_dimensions()
    if dims:
        img_height, img_width = dims
        valid_rect = QRect(0, 0, img_width, img_height).intersected(saved_rect)
        saved_rect = valid_rect

    if not saved_rect.isValid() or saved_rect.width() <= 0 or saved_rect.height() <= 0:
        return

    # Apply crop to the image in the viewer's scene (visual only)
    main_window.viewer.confirm_crop()

    # Store the crop rectangle for on-the-fly cropping during display
    # Don't modify the underlying images - this is the key change!
    main_window.viewer.set_saved_crop_rect(saved_rect)

    # Update all channel previews
    for i in range(3):
        update_channel_preview(main_window, i)

    # Reset crop mode and UI
    main_window.state.crop_mode = False
    main_window.crop_mode_btn.setVisible(True)
    main_window.crop_controls.setVisible(False)
    main_window.viewer.set_crop_mode(False)

    # Update save button state after crop
    main_window.update_save_button_state()

    # Update mode indicator and status message
    main_window._update_mode_from_state()  # pylint: disable=protected-access
    main_window.status_handler.set_message("Crop applied successfully", main_window.status_handler.MEDIUM_TIMEOUT)

    # Force a full display update
    if main_window.state.show_combined:
        show_combined_image(main_window)
    else:
        show_single_channel_image(main_window)

    save_autosave(main_window)
