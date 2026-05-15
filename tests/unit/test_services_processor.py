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

"""Unit tests for services.processor module."""

from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from src.services.processor import ChannelAdjustments, ImageProcessorService


class TestChannelAdjustments:
    """
    Test Design Specification: ChannelAdjustments dataclass
    Module under test: src/services/processor.py

    Contract:
        ChannelAdjustments is a dataclass that stores per-channel adjustment parameters.
        It accepts optional brightness and contrast integer values (default 0 for each).
        Fields are mutable and can be initialized with partial or complete arguments.
        Returns instances with the specified or default field values.

    Equivalence partitions:
        EP1  Default initialization (no args)    → brightness=0, contrast=0
        EP2  Custom single field (brightness)    → specified brightness, contrast=0
        EP3  Custom single field (contrast)      → brightness=0, specified contrast
        EP4  Custom both fields                  → specified brightness and contrast
        EP5  Negative values                     → accepts negative brightness/contrast
        EP6  Partial initialization              → unspecified fields use defaults

    Boundary values:
        BV1  brightness = 0 (neutral/default)
        BV2  contrast = 0 (neutral/default)
        BV3  brightness = -100 (minimum typical)
        BV4  brightness = 100 (maximum typical)
        BV5  contrast = -100 (minimum typical)
        BV6  contrast = 100 (maximum typical)

    Exclusions:
        - Out-of-range validation (dataclass accepts any int; UI layer enforces limits)
        - Type checking (assumes int inputs, caller responsible for validation)
        - State mutation after initialization (only test initialization contract)

    Constraints:
        - No external dependencies; pure dataclass initialization
        - Mutable after creation (allows field reassignment)
        - No side effects during instantiation
    """

    def test_default_values(self) -> None:
        """Given: ChannelAdjustments created with no arguments
        When: default values are accessed
        Then: brightness and contrast are both zero."""
        # Arrange & Act
        adj = ChannelAdjustments()
        # Assert
        assert adj.brightness == 0
        assert adj.contrast == 0

    def test_custom_values(self) -> None:
        """Given: ChannelAdjustments with custom brightness and contrast
        When: the instance is created with brightness=10, contrast=-5
        Then: those values are stored correctly."""
        adj = ChannelAdjustments(brightness=10, contrast=-5)
        assert adj.brightness == 10
        assert adj.contrast == -5

    def test_partial_init(self) -> None:
        """Given: ChannelAdjustments initialized with only brightness=20
        When: the instance is created
        Then: brightness is 20 and contrast defaults to zero."""
        # Arrange & Act
        adj = ChannelAdjustments(brightness=20)
        # Assert
        assert adj.brightness == 20
        assert adj.contrast == 0


class TestImageProcessorServiceInit:
    """
    Test Design Specification: ImageProcessorService.__init__()
    Module under test: src/services/processor.py

    Contract:
        Initializes the ImageProcessorService with empty state for image processing.
        Creates three lists (original_images, aligned, processed, original_rgb_images, aligned_rgb),
        each with three None slots for RGB channels. Creates a list of three ChannelAdjustments,
        each initialized to brightness=0, contrast=0.
        Returns a fully initialized service ready to load channels.

    Equivalence partitions:
        EP1  Fresh initialization             → all image lists contain [None, None, None]
        EP2  Adjustment initialization        → all three ChannelAdjustments with defaults
        EP3  List structure validity          → each list has exactly 3 slots
        EP4  Type correctness                 → adjustments are ChannelAdjustments instances

    Boundary values:
        BV1  List length = 3 (exactly three channels)
        BV2  All initial values = None (no image data)
        BV3  All adjustments = 0 (neutral state)

    Exclusions:
        - Loading channels post-init (tested separately in TestLoadChannelFromArray)
        - Mutation of initial lists after construction (tested in service mutation tests)
        - Memory allocation patterns (not a concern for tests)

    Constraints:
        - No external dependencies at init time
        - Lists are mutable references (internal state)
        - No file I/O or alignment performed during __init__
    """

    def test_init_creates_empty_lists(self) -> None:
        """Given: ImageProcessorService is instantiated
        When: __init__ is called
        Then: all image lists are initialized with 3 None slots each."""
        # Arrange
        # Act
        svc = ImageProcessorService()
        # Assert — all lists initialized with 3 None slots each
        for list_name in ["original_images", "aligned", "processed", "original_rgb_images", "aligned_rgb"]:
            list_obj = getattr(svc, list_name)
            assert len(list_obj) == 3, f"{list_name} length should be 3"
            assert all(img is None for img in list_obj), f"all {list_name} should be None"

    def test_init_creates_adjustments(self) -> None:
        """Given: ImageProcessorService is instantiated
        When: __init__ is called
        Then: three ChannelAdjustments objects are created with default values."""
        # Act
        svc = ImageProcessorService()
        # Assert
        assert len(svc.adjustments) == 3
        for adj in svc.adjustments:
            assert isinstance(adj, ChannelAdjustments)
            assert adj.brightness == 0
            assert adj.contrast == 0


class TestLoadChannelFromArray:
    """
    Test Design Specification: ImageProcessorService.load_channel_from_array()
    Module under test: src/services/processor.py

    Contract:
        Loads a single RGB channel from a numpy array into the service.
        Converts RGB (HxWx3 uint8) to grayscale (HxW uint8) using cv2.cvtColor.
        Stores original RGB, original grayscale, and an initial copy in processed.
        Triggers automatic alignment via align_images() when all 3 channels are loaded.
        After alignment, re-applies all current adjustments to aligned images.
        Side effects: populates service state, calls align_images when count reaches 3.

    Equivalence partitions:
        EP1  First channel load (count=1)     → stores RGB/gray, no alignment yet
        EP2  Second channel load (count=2)    → stores RGB/gray, no alignment yet
        EP3  Third channel load (count=3)     → stores RGB/gray, TRIGGERS alignment
        EP4  Conversion correctness           → RGB→gray conversion valid, shape correct
        EP5  Copy independence                → processed is independent copy of original

    Boundary values:
        BV1  channel_idx = 0 (red channel)
        BV2  channel_idx = 1 (green channel)
        BV3  channel_idx = 2 (blue channel)
        BV4  Image size = 100x100 (typical)
        BV5  Image size = 50x75 (non-square)

    Exclusions:
        - Out-of-bounds channel index (caller responsible for [0,2] range)
        - Invalid RGB shape (assumes HxWx3 input)
        - Non-uint8 dtypes (assumes uint8 input)
        - Re-loading same channel (not tested; specification doesn't define behavior)

    Constraints:
        - Requires cv2 (OpenCV) available and cv2.cvtColor working
        - Requires mocked align_images for testing (patched in tests)
        - Tests use synthetic random RGB images created with numpy RandomState
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_load_single_channel_stores_rgb(self) -> None:
        """Given: an ImageProcessorService and RGB image
        When: load_channel_from_array is called with channel 0
        Then: the original RGB image is stored in original_rgb_images[0]."""
        # Arrange
        svc = ImageProcessorService()
        rgb = self._make_rgb_image()
        # Act
        svc.load_channel_from_array(0, rgb)
        # Assert
        assert svc.original_rgb_images[0] is rgb

    def test_load_single_channel_converts_to_grayscale(self) -> None:
        """Given: an RGB image (HxWx3 uint8)
        When: load_channel_from_array converts it
        Then: a grayscale (HxW uint8) image is stored in original_images."""
        # Arrange
        svc = ImageProcessorService()
        rgb = self._make_rgb_image()
        # Act
        svc.load_channel_from_array(0, rgb)
        # Assert
        assert svc.original_images[0] is not None
        assert svc.original_images[0].ndim == 2
        assert svc.original_images[0].shape == (100, 100)
        assert svc.original_images[0].dtype == np.uint8

    def test_load_single_channel_copies_to_processed(self) -> None:
        """Given: a grayscale original image loaded
        When: load_channel_from_array initializes the processed list
        Then: processed[0] contains an independent copy of the original."""
        # Arrange
        svc = ImageProcessorService()
        rgb = self._make_rgb_image()
        # Act
        svc.load_channel_from_array(0, rgb)
        # Assert
        assert svc.processed[0] is not None
        np.testing.assert_array_equal(svc.processed[0], svc.original_images[0])
        assert svc.processed[0] is not svc.original_images[0]

    def test_load_two_channels_no_alignment_yet(self) -> None:
        """Given: fewer than 3 channels loaded (2 channels)
        When: load_channel_from_array is called
        Then: alignment is not triggered and aligned list remains None."""
        # Arrange
        svc = ImageProcessorService()
        rgb1 = self._make_rgb_image(seed=1)
        rgb2 = self._make_rgb_image(seed=2)
        # Act
        svc.load_channel_from_array(0, rgb1)
        svc.load_channel_from_array(1, rgb2)
        # Assert
        assert svc.aligned[0] is None
        assert svc.aligned[1] is None

    @patch("src.services.processor.align_images")
    def test_load_three_channels_triggers_alignment(self, mock_align: MagicMock) -> None:
        """Given: align_images mocked to return aligned gray and RGB arrays
        When: all 3 channels are loaded sequentially
        Then: align_images is called once and aligned arrays are populated."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [
            np.dstack([gray_aligned[0]] * 3),
            np.dstack([gray_aligned[1]] * 3),
            np.dstack([gray_aligned[2]] * 3),
        ]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        rgb1 = self._make_rgb_image(seed=1)
        rgb2 = self._make_rgb_image(seed=2)
        rgb3 = self._make_rgb_image(seed=3)
        # Act
        svc.load_channel_from_array(0, rgb1)
        svc.load_channel_from_array(1, rgb2)
        svc.load_channel_from_array(2, rgb3)
        # Assert
        mock_align.assert_called_once()
        assert svc.aligned[0] is not None
        assert svc.aligned[1] is not None
        assert svc.aligned[2] is not None
        np.testing.assert_array_equal(svc.aligned[0], gray_aligned[0])


class TestAdjustChannel:
    """
    Test Design Specification: ImageProcessorService.adjust_channel()
    Module under test: src/services/processor.py

    Contract:
        Updates brightness and contrast adjustment parameters for a single channel
        and recomputes the processed image by applying adjustments to the aligned base.
        Stores new ChannelAdjustments with given brightness/contrast values.
        Calls apply_adjustments(aligned_img, brightness, contrast) to update processed.
        Side effects: updates self.adjustments[channel_idx] and self.processed[channel_idx].

    Equivalence partitions:
        EP1  Positive brightness adjustment      → processed image updated with brightness
        EP2  Negative brightness adjustment      → processed image updated with brightness
        EP3  Positive contrast adjustment        → processed image updated with contrast
        EP4  Negative contrast adjustment        → processed image updated with contrast
        EP5  Zero adjustment (identity)          → processed matches input
        EP6  Combined brightness and contrast    → both applied together

    Boundary values:
        BV1  brightness = -100 (maximum darkness)
        BV2  brightness = 0 (neutral)
        BV3  brightness = 100 (maximum brightness)
        BV4  contrast = -100 (maximum reduction)
        BV5  contrast = 0 (neutral)
        BV6  contrast = 100 (maximum increase)

    Exclusions:
        - Out-of-bounds channel index (caller ensures [0,2])
        - Adjustment before channels loaded (test assumes channels pre-loaded)
        - Value range enforcement (UI layer enforces [-100, 100])
        - Chained adjustments (each call replaces all adjustments)

    Constraints:
        - Requires ImageProcessorService fully initialized with 3 channels loaded
        - Requires mocked apply_adjustments (patched in tests)
        - Requires mocked align_images (for channel loading in test setup)
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.apply_adjustments")
    def test_adjust_channel_updates_adjustment_values(
        self, mock_apply: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: all 3 channels loaded and mocks configured
        When: adjust_channel is called with brightness=10, contrast=-5
        Then: adjustments[0] stores the new brightness and contrast values."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        mock_apply.return_value = np.ones((100, 100), dtype=np.uint8) * 75

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))
        # Act
        svc.adjust_channel(0, brightness=10, contrast=-5)
        # Assert
        assert svc.adjustments[0].brightness == 10
        assert svc.adjustments[0].contrast == -5

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.apply_adjustments")
    def test_adjust_channel_calls_apply_adjustments(
        self, mock_apply: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: all 3 channels loaded with mocked apply_adjustments
        When: adjust_channel is called with brightness=20, contrast=10
        Then: apply_adjustments is invoked with the correct parameters."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        adjusted = np.ones((100, 100), dtype=np.uint8) * 75
        mock_apply.return_value = adjusted

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))
        # Act
        svc.adjust_channel(1, brightness=20, contrast=10)
        # Assert
        mock_apply.assert_called()
        call_args = mock_apply.call_args
        assert call_args[0][1] == 20  # brightness
        assert call_args[0][2] == 10  # contrast

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.apply_adjustments")
    def test_adjust_channel_updates_processed_image(
        self, mock_apply: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: all 3 channels loaded and apply_adjustments returns adjusted image
        When: adjust_channel is called with brightness=10, contrast=-5
        Then: processed[0] is updated with the adjusted image."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        adjusted = np.ones((100, 100), dtype=np.uint8) * 75
        mock_apply.return_value = adjusted

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))
        # Act
        svc.adjust_channel(0, brightness=10, contrast=-5)
        # Assert
        np.testing.assert_array_equal(svc.processed[0], adjusted)


class TestGetChannelPreview:
    """
    Test Design Specification: ImageProcessorService.get_channel_preview()
    Module under test: src/services/processor.py

    Contract:
        Returns the processed (adjusted, aligned) grayscale image for a single channel.
        Returns None if the channel has not been loaded.
        Does not crop or modify the image; returns the internal processed array directly.
        No side effects; read-only access to service state.

    Equivalence partitions:
        EP1  Channel not loaded (is None)        → returns None
        EP2  Channel loaded and aligned          → returns processed image
        EP3  Channel after adjustments applied   → returns adjusted processed image
        EP4  Valid channel index (0, 1, 2)       → each returns correct channel

    Boundary values:
        BV1  channel_idx = 0 (first channel)
        BV2  channel_idx = 1 (middle channel)
        BV3  channel_idx = 2 (last channel)

    Exclusions:
        - Out-of-bounds channel index (caller ensures [0,2])
        - Cropping (use get_channel() for cropped preview)
        - Copy semantics (returns internal reference, not copy)
        - Null channel handling beyond returning None

    Constraints:
        - Requires ImageProcessorService initialized
        - No external dependencies
        - Returns direct internal reference (caller must not mutate)
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_channel_preview_before_load_returns_none(self) -> None:
        """Given: an ImageProcessorService with no channels loaded
        When: get_channel_preview is called
        Then: None is returned."""
        svc = ImageProcessorService()
        result = svc.get_channel_preview(0)
        assert result is None

    @patch("src.services.processor.align_images")
    def test_get_channel_preview_returns_processed_image(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded with mocked align_images
        When: get_channel_preview is called for channel 1
        Then: the processed image for that channel is returned."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))
        # Act
        preview = svc.get_channel_preview(1)
        # Assert
        assert preview is not None
        np.testing.assert_array_equal(preview, svc.processed[1])


class TestGetChannel:
    """
    Test Design Specification: ImageProcessorService.get_channel()
    Module under test: src/services/processor.py

    Contract:
        Returns an independent copy of a single channel's processed image, optionally cropped.
        Returns None if the channel has not been loaded.
        Crop tuple is (x, y, width, height); extracts region [y:y+h, x:x+w].
        Both cropped and non-cropped paths return .copy() (independent copies).
        Modifying returned arrays never affects service state.
        No side effects except copy creation.

    Equivalence partitions:
        EP1  No crop provided                    → returns full processed image
        EP2  Crop provided (valid region)        → returns cropped region as copy
        EP3  Channel not loaded                  → returns None
        EP4  Full-image crop (x=0,y=0,w=W,h=H) → returns full image copy

    Boundary values:
        BV1  channel_idx = 0 (red)
        BV2  channel_idx = 1 (green)
        BV3  channel_idx = 2 (blue)
        BV4  crop.x = 0 (left edge)
        BV5  crop.y = 0 (top edge)
        BV6  crop.width = image width (full width)
        BV7  crop.height = image height (full height)

    Exclusions:
        - Out-of-bounds crop region (assumes caller validates crop bounds)
        - Crop region exceeding image bounds (no clipping applied)
        - Out-of-bounds channel index
        - Type validation on crop tuple

    Constraints:
        - Requires ImageProcessorService initialized with channels loaded
        - Mocked align_images for test setup
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_channel_before_load_returns_none(self) -> None:
        """Given: an ImageProcessorService with no channels loaded
        When: get_channel is called
        Then: None is returned."""
        svc = ImageProcessorService()
        result = svc.get_channel(0)
        assert result is None

    @patch("src.services.processor.align_images")
    def test_get_channel_without_crop_returns_full_image(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded with mocked align_images
        When: get_channel is called without crop for channel 2
        Then: the full processed image is returned."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))
        # Act
        result = svc.get_channel(2)
        # Assert
        np.testing.assert_array_equal(result, svc.processed[2])

    @patch("src.services.processor.align_images")
    def test_get_channel_with_crop_returns_cropped_region(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded with mocked align_images
        When: get_channel is called with crop=(10, 20, 30, 40)
        Then: the cropped region [y:y+h, x:x+w] is returned."""
        # Arrange
        gray_aligned = [
            np.arange(10000, dtype=np.uint32).reshape(100, 100) % 256,
            (np.arange(10000, dtype=np.uint32) + 100).reshape(100, 100) % 256,
            (np.arange(10000, dtype=np.uint32) + 200).reshape(100, 100) % 256,
        ]
        gray_aligned = [img.astype(np.uint8) for img in gray_aligned]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        crop = (10, 20, 30, 40)  # x=10, y=20, width=30, height=40
        # Act
        result = svc.get_channel(0, crop=crop)
        # Assert
        expected = svc.processed[0][20:60, 10:40]
        np.testing.assert_array_equal(result, expected)

    @patch("src.services.processor.align_images")
    def test_get_channel_crop_creates_copy(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded with mocked align_images
        When: get_channel is called with a crop region
        Then: the returned array is an independent copy, not a view."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * i for i in range(1, 4)
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        crop = (10, 20, 30, 40)
        # Act
        result = svc.get_channel(0, crop=crop)
        # Assert
        assert result.base is None or result.base is not svc.processed[0]

    @patch("src.services.processor.align_images")
    def test_get_channel_without_crop_returns_independent_copy(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded without crop argument
        When: get_channel is called and the result is mutated
        Then: the service state should remain unchanged (copy, not reference)."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        # Act
        result = svc.get_channel(0)
        original_value = svc.processed[0][0, 0]
        result[0, 0] = 255
        # Assert
        assert svc.processed[0][0, 0] == original_value


class TestGetCombined:
    """
    Test Design Specification: ImageProcessorService.get_combined()
    Module under test: src/services/processor.py

    Contract:
        Combines three processed channel images into a single RGB image (HxWx3 uint8).
        Optionally applies per-channel intensity scaling via intensities list [r, g, b].
        Defaults to intensities [100, 100, 100] (no scaling) if not specified.
        Optionally crops result to a rectangular region (x, y, width, height).
        Returns None if channels not loaded or combine_channels returns None.
        Delegates combining to combine_channels() function (mocked in tests).

    Equivalence partitions:
        EP1  No crop, default intensities      → combines all channels at 100%
        EP2  Custom intensities provided       → channels scaled per intensity value
        EP3  Crop provided                     → returns cropped region from combined RGB
        EP4  Channels not fully loaded         → returns None
        EP5  combine_channels returns None     → propagates None

    Boundary values:
        BV1  intensities = [100, 100, 100] (neutral/default)
        BV2  intensities = [0, 0, 0] (zero/black)
        BV3  intensities = [200, 200, 200] (doubled)
        BV4  crop.x = 0 (left edge)
        BV5  crop.y = 0 (top edge)

    Exclusions:
        - Out-of-bounds channel indices (assumes channels 0-2)
        - Intensity range validation (caller ensures valid values)
        - Crop bounds validation (assumes valid crop rect)
        - Error handling for missing channels (just returns None)

    Constraints:
        - Requires ImageProcessorService with channels loaded
        - Requires mocked combine_channels (patched in tests)
        - Requires mocked align_images (for channel loading setup)
        - RGB array dtype assumed uint8
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_combined_before_load_returns_none(self) -> None:
        """Given: an ImageProcessorService with no channels loaded
        When: get_combined is called
        Then: None is returned."""
        svc = ImageProcessorService()
        result = svc.get_combined()
        assert result is None

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_without_crop_calls_combine_channels(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: all 3 channels loaded with mocked combine_channels
        When: get_combined is called without crop
        Then: combine_channels is invoked once and RGB result is returned."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        combined_rgb = np.ones((100, 100, 3), dtype=np.uint8) * 100
        mock_combine.return_value = combined_rgb

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        # Act
        result = svc.get_combined()
        # Assert
        mock_combine.assert_called_once()
        np.testing.assert_array_equal(result, combined_rgb)

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_with_intensities(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: all 3 channels loaded and combine_channels mocked
        When: get_combined is called with intensities=[120, 100, 80]
        Then: combine_channels receives the intensities parameter."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        combined_rgb = np.ones((100, 100, 3), dtype=np.uint8) * 100
        mock_combine.return_value = combined_rgb

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        intensities = [120, 100, 80]
        # Act
        result = svc.get_combined(intensities=intensities)
        # Assert
        call_args = mock_combine.call_args
        assert call_args[0][1] == intensities

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_uses_default_intensities(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: all 3 channels loaded without intensities argument
        When: get_combined is called
        Then: combine_channels receives default intensities [100, 100, 100]."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        combined_rgb = np.ones((100, 100, 3), dtype=np.uint8) * 100
        mock_combine.return_value = combined_rgb

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        # Act
        result = svc.get_combined()
        # Assert
        mock_combine.assert_called_once()
        call_args = mock_combine.call_args
        assert call_args[0][1] == [100, 100, 100]
        np.testing.assert_array_equal(result, combined_rgb)

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_with_crop(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: combined RGB image and crop=(10, 20, 30, 40)
        When: get_combined is called with crop
        Then: the cropped region [y:y+h, x:x+w] is returned."""
        # Arrange
        gray_aligned = [
            np.arange(10000, dtype=np.uint32).reshape(100, 100) % 256,
            (np.arange(10000, dtype=np.uint32) + 100).reshape(100, 100) % 256,
            (np.arange(10000, dtype=np.uint32) + 200).reshape(100, 100) % 256,
        ]
        gray_aligned = [img.astype(np.uint8) for img in gray_aligned]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        combined_rgb = np.arange(30000, dtype=np.uint32).reshape(100, 100, 3) % 256
        combined_rgb = combined_rgb.astype(np.uint8)
        mock_combine.return_value = combined_rgb

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        crop = (10, 20, 30, 40)
        # Act
        result = svc.get_combined(crop=crop)
        # Assert
        expected = combined_rgb[20:60, 10:40]
        np.testing.assert_array_equal(result, expected)

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_returns_none_when_combine_channels_returns_none(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Given: all 3 channels loaded but combine_channels returns None
        When: get_combined is called
        Then: None is returned without error."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)
        mock_combine.return_value = None

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        # Act
        result = svc.get_combined()
        # Assert
        assert result is None


class TestHasAlignedChannels:
    """
    Test Design Specification: ImageProcessorService.has_aligned_channels()
    Module under test: src/services/processor.py

    Contract:
        Returns True if all three channels have been aligned (self.aligned is fully populated).
        Returns False if any channel is None (not yet aligned).
        No side effects; read-only predicate check.

    Equivalence partitions:
        EP1  No channels loaded                 → returns False
        EP2  Partial channels loaded (count<3)  → returns False
        EP3  All channels loaded and aligned    → returns True

    Boundary values:
        BV1  aligned = [None, None, None] (initial state)
        BV2  aligned = [img, img, img] (fully aligned)
        BV3  aligned = [img, None, img] (partially filled)

    Exclusions:
        - Definition of "aligned" (assumes align_images populates self.aligned)
        - Alignment quality validation (just checks existence)
        - Channel state after reset

    Constraints:
        - No external dependencies
        - Requires mocked align_images for test setup
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_has_aligned_channels_false_initially(self) -> None:
        """Given: an ImageProcessorService with no channels loaded
        When: has_aligned_channels is called
        Then: False is returned."""
        svc = ImageProcessorService()
        assert svc.has_aligned_channels() is False

    @patch("src.services.processor.align_images")
    def test_has_aligned_channels_true_after_load(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded with mocked align_images
        When: has_aligned_channels is called
        Then: True is returned."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        # Act
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))
        # Assert
        assert svc.has_aligned_channels() is True


class TestHasProcessedChannels:
    """
    Test Design Specification: ImageProcessorService.has_processed_channels()
    Module under test: src/services/processor.py

    Contract:
        Returns True if at least one processed channel exists (any element is not None).
        Returns False if all processed channels are None.
        No side effects; read-only predicate check.

    Equivalence partitions:
        EP1  No channels loaded                 → returns False (all None)
        EP2  At least one channel loaded        → returns True
        EP3  Multiple channels loaded           → returns True
        EP4  All channels loaded                → returns True

    Boundary values:
        BV1  processed = [None, None, None] (initial)
        BV2  processed = [img, None, None] (first only)
        BV3  processed = [None, img, None] (middle only)
        BV4  processed = [None, None, img] (last only)
        BV5  processed = [img, img, img] (all filled)

    Exclusions:
        - Relationship to alignment (test only checks processed existence)
        - Quality of processed images (just existence check)

    Constraints:
        - No external dependencies
        - Minimal dependencies on other service methods
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_has_processed_channels_false_initially(self) -> None:
        """Given: an ImageProcessorService with no channels loaded
        When: has_processed_channels is called
        Then: False is returned."""
        svc = ImageProcessorService()
        assert svc.has_processed_channels() is False

    @patch("src.services.processor.align_images")
    def test_has_processed_channels_true_after_single_channel_load(self, mock_align: MagicMock) -> None:
        """Given: one channel loaded with mocked align_images
        When: has_processed_channels is called
        Then: True is returned."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        # Act
        svc.load_channel_from_array(0, self._make_rgb_image(seed=0))
        # Assert
        assert svc.has_processed_channels() is True


class TestGetImageDimensions:
    """
    Test Design Specification: ImageProcessorService.get_image_dimensions()
    Module under test: src/services/processor.py

    Contract:
        Returns a tuple (height, width) of loaded images.
        Returns None if no channels have been loaded.
        Assumes all loaded channels have identical dimensions (alignment enforces this).
        No side effects; read-only access to image metadata.

    Equivalence partitions:
        EP1  No channels loaded                 → returns None
        EP2  Channels loaded                    → returns (height, width) tuple
        EP3  Square images (100x100)            → returns (100, 100)
        EP4  Rectangular images (50x75)         → returns (50, 75)

    Boundary values:
        BV1  height = 50 (minimum in tests)
        BV2  width = 75 (in rectangular test)
        BV3  height = width = 100 (square case)

    Exclusions:
        - Image dtype or channel count (returns only spatial dims)
        - Handling of partially loaded channels (assumes all or none)
        - Validation that aligned images match original shapes

    Constraints:
        - Requires ImageProcessorService initialized
        - Requires mocked align_images for test setup
        - Assumes aligned[0] exists and has valid .shape attribute
    """
    """Tests for retrieving image dimensions."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_image_dimensions_before_load_returns_none(self) -> None:
        """Given: an ImageProcessorService with no channels loaded
        When: get_image_dimensions is called
        Then: None is returned."""
        svc = ImageProcessorService()
        result = svc.get_image_dimensions()
        assert result is None

    @patch("src.services.processor.align_images")
    def test_get_image_dimensions_after_load(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded with dimensions 50x75
        When: get_image_dimensions is called
        Then: (50, 75) tuple is returned."""
        # Arrange
        gray_aligned = [
            np.ones((50, 75), dtype=np.uint8) * 50,
            np.ones((50, 75), dtype=np.uint8) * 100,
            np.ones((50, 75), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        rgb = self._make_rgb_image(height=50, width=75)
        # Act
        for i in range(3):
            svc.load_channel_from_array(i, rgb)
        # Assert
        dims = svc.get_image_dimensions()
        assert dims == (50, 75)


class TestReset:
    """
    Test Design Specification: ImageProcessorService.reset()
    Module under test: src/services/processor.py

    Contract:
        Clears all internal image state to restore service to initial empty state.
        Sets all entries in original_images, aligned, processed, original_rgb_images,
        and aligned_rgb to None. Resets all ChannelAdjustments to brightness=0, contrast=0.
        After reset, service can be reused to load new channels.
        No return value; operates by side effect only.

    Equivalence partitions:
        EP1  Reset after channel load           → all lists cleared to None values
        EP2  Reset after adjustment            → adjustments reset to defaults
        EP3  Multiple consecutive resets        → each reset returns to same state

    Boundary values:
        BV1  All image lists → [None, None, None]
        BV2  All adjustments → ChannelAdjustments(brightness=0, contrast=0)

    Exclusions:
        - Selective field reset (full reset only)
        - Memory deallocation (just replaces references)
        - Return value (None return)

    Constraints:
        - Requires ImageProcessorService fully initialized
        - Requires mocked align_images for test setup
        - Reset must be idempotent (multiple calls yield same state)
    """

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    @patch("src.services.processor.align_images")
    def test_reset_clears_all_images(self, mock_align: MagicMock) -> None:
        """Given: all 3 channels loaded with image data
        When: reset is called
        Then: all image lists are cleared to [None, None, None]."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))
        # Act
        svc.reset()
        # Assert
        assert all(img is None for img in svc.original_images)
        assert all(img is None for img in svc.aligned)
        assert all(img is None for img in svc.processed)
        assert all(img is None for img in svc.original_rgb_images)
        assert all(img is None for img in svc.aligned_rgb)

    @patch("src.services.processor.align_images")
    def test_reset_resets_adjustments(self, mock_align: MagicMock) -> None:
        """Given: channels loaded with adjustments modified
        When: reset is called
        Then: all adjustments are reset to brightness=0, contrast=0."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        # Act - Modify adjustments
        svc.adjust_channel(0, brightness=10, contrast=-5)
        svc.adjust_channel(1, brightness=-10, contrast=5)

        svc.reset()
        # Assert
        for adj in svc.adjustments:
            assert adj.brightness == 0
            assert adj.contrast == 0

    @patch("src.services.processor.align_images")
    def test_reset_allows_reuse(self, mock_align: MagicMock) -> None:
        """Given: channels loaded and reset called
        When: new channels are loaded with different dimensions
        Then: the service accepts the new data without conflicts."""
        # Arrange
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, np.ones((100, 100, 3), dtype=np.uint8))

        # Act
        svc.reset()

        rgb2 = np.ones((50, 50, 3), dtype=np.uint8) * 200
        svc.load_channel_from_array(0, rgb2)
        # Assert
        assert svc.original_rgb_images[0] is not None
        assert svc.original_images[0] is not None
