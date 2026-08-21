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

"""Service layer for image processing and channel management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, cast

import cv2  # type: ignore
import numpy as np

from ..core.align import AlignmentDOF, AlignmentResult, align_images_with_result
from ..core.image_processing import apply_adjustments, combine_channels


@dataclass
class ChannelAdjustments:  # pylint: disable=too-few-public-methods
    """Stores per-channel brightness and contrast adjustment parameters."""

    brightness: int = 0
    contrast: int = 0


class ImageProcessorService:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Service for managing image processing state and operations.

    Owns all image arrays (original, aligned, processed) and per-channel
    adjustments. Provides methods for loading channels, adjusting brightness/contrast,
    and retrieving processed images with optional cropping.
    """

    def __init__(self) -> None:
        """Initialize the image processor service with empty state."""
        self.original_images: List[Optional[np.ndarray]] = [None, None, None]
        self.aligned: List[Optional[np.ndarray]] = [None, None, None]
        self.processed: List[Optional[np.ndarray]] = [None, None, None]
        self.original_rgb_images: List[Optional[np.ndarray]] = [None, None, None]
        self.aligned_rgb: List[Optional[np.ndarray]] = [None, None, None]
        self.adjustments: List[ChannelAdjustments] = [
            ChannelAdjustments(),
            ChannelAdjustments(),
            ChannelAdjustments(),
        ]
        self.alignment_dof: AlignmentDOF = AlignmentDOF.TRANSLATION_ROTATION_SCALE
        self.last_alignment_result: Optional[AlignmentResult] = None

    def load_channel_from_array(self, channel_idx: int, rgb_array: np.ndarray) -> None:
        """Load a channel from an RGB array.

        Stores the RGB array, converts to grayscale, and triggers alignment
        when all 3 channels are loaded. After alignment, re-applies current
        adjustments to the aligned images.

        Args:
            channel_idx (int): Channel index (0=Red, 1=Green, 2=Blue).
            rgb_array (np.ndarray): RGB image as HxWx3 uint8 numpy array.
        """
        self.original_rgb_images[channel_idx] = rgb_array

        gray = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)  # pylint: disable=E1101
        self.original_images[channel_idx] = gray
        self.processed[channel_idx] = gray.copy()

        if all(img is not None for img in self.original_images):
            self._perform_alignment()
            for i in range(3):
                self._update_processed_image(i)

    def _perform_alignment(self) -> None:
        """Align all loaded channels to red channel using feature matching."""
        gray_images = [img for img in self.original_images if img is not None]
        rgb_images = [img for img in self.original_rgb_images if img is not None]

        if len(gray_images) == 3 and len(rgb_images) == 3:
            result = align_images_with_result(gray_images, rgb_images, self.alignment_dof)
            self.last_alignment_result = result
            self.aligned = cast(List[Optional[np.ndarray]], result.aligned_grayscale)
            self.aligned_rgb = cast(List[Optional[np.ndarray]], result.aligned_rgb)
            self.processed = [img.copy() for img in result.aligned_grayscale]

    def adjust_channel(self, channel_idx: int, brightness: int, contrast: int) -> None:
        """Adjust brightness and contrast for a channel.

        Updates the adjustment parameters and re-computes the processed image
        for the channel by applying adjustments to the aligned base image.

        Args:
            channel_idx (int): Channel index (0=Red, 1=Green, 2=Blue).
            brightness (int): Brightness adjustment [-100, 100].
            contrast (int): Contrast adjustment [-100, 100].
        """
        self.adjustments[channel_idx] = ChannelAdjustments(brightness=brightness, contrast=contrast)
        self._update_processed_image(channel_idx)

    def _update_processed_image(self, channel_idx: int) -> None:
        """Update the processed image for a channel based on current adjustments."""
        if self.aligned[channel_idx] is None:
            return
        base_image = self.aligned[channel_idx]
        adj = self.adjustments[channel_idx]
        adjusted = apply_adjustments(base_image, adj.brightness, adj.contrast)
        self.processed[channel_idx] = adjusted

    def get_channel_preview(self, channel_idx: int) -> Optional[np.ndarray]:
        """Get the preview image for a single channel.

        Args:
            channel_idx (int): Channel index (0=Red, 1=Green, 2=Blue).

        Returns:
            np.ndarray | None: Processed grayscale image (HxW uint8) or None if not loaded.
        """
        return self.processed[channel_idx]

    def get_channel(self, channel_idx: int, crop: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Get a single channel image, optionally cropped.

        Returns an independent copy of the processed image. Modifying the returned
        array does not affect the service's internal state.

        Args:
            channel_idx (int): Channel index (0=Red, 1=Green, 2=Blue).
            crop (tuple[int,int,int,int] | None): Crop rect as (x, y, width, height) or None.

        Returns:
            np.ndarray | None: Independent copy of grayscale image (HxW uint8) or None if not loaded.
        """
        if self.processed[channel_idx] is None:
            return None

        img = self.processed[channel_idx]
        assert img is not None
        if crop is not None:
            x, y, w, h = crop
            return cast(np.ndarray, img[y : y + h, x : x + w].copy())
        return cast(np.ndarray, img.copy())

    def get_combined(
        self, crop: Optional[Tuple[int, int, int, int]] = None, intensities: Optional[List[int]] = None
    ) -> Optional[np.ndarray]:
        """Get combined RGB image with optional cropping and intensity adjustments.

        Returns the combined RGB image. When no crop is specified, the returned array
        is freshly allocated by combine_channels() and safe to modify.
        When crop is specified, returns an independent copy of the cropped region.

        Args:
            crop (tuple[int,int,int,int] | None): Crop rect as (x, y, width, height) or None.
            intensities (list[int] | None): Intensity multipliers [R%, G%, B%] or None for [100, 100, 100].

        Returns:
            np.ndarray | None: RGB image (HxWx3 uint8) or None if any channel missing.
        """
        if intensities is None:
            intensities = [100, 100, 100]

        combined = combine_channels(self.processed, intensities)
        if combined is None:
            return None

        if crop is not None:
            x, y, w, h = crop
            return cast(np.ndarray, combined[y : y + h, x : x + w].copy())
        return combined

    def has_aligned_channels(self) -> bool:
        """Check if any aligned channels exist.

        Returns:
            bool: True if at least one channel has been aligned.
        """
        return any(img is not None for img in self.aligned)

    def has_processed_channels(self) -> bool:
        """Check if any processed channels exist.

        Returns:
            bool: True if at least one channel has been processed.
        """
        return any(img is not None for img in self.processed)

    def get_image_dimensions(self) -> Optional[Tuple[int, int]]:
        """Get the dimensions of loaded images.

        Returns:
            tuple[int, int] | None: (height, width) of loaded images or None if none loaded.
        """
        for img in self.processed:
            if img is not None:
                return cast(Tuple[int, int], img.shape[:2])
        return None

    def reset(self) -> None:
        """Reset all state to empty."""
        self.original_images = [None, None, None]
        self.aligned = [None, None, None]
        self.processed = [None, None, None]
        self.original_rgb_images = [None, None, None]
        self.aligned_rgb = [None, None, None]
        self.adjustments = [
            ChannelAdjustments(),
            ChannelAdjustments(),
            ChannelAdjustments(),
        ]
        self.last_alignment_result = None
