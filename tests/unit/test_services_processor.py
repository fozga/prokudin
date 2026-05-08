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
    """Tests for ChannelAdjustments dataclass."""

    def test_default_values(self) -> None:
        """Verify default brightness and contrast are zero."""
        adj = ChannelAdjustments()
        assert adj.brightness == 0
        assert adj.contrast == 0

    def test_custom_values(self) -> None:
        """Verify custom brightness and contrast can be set."""
        adj = ChannelAdjustments(brightness=10, contrast=-5)
        assert adj.brightness == 10
        assert adj.contrast == -5

    def test_partial_init(self) -> None:
        """Verify partial initialization uses defaults for unspecified fields."""
        adj = ChannelAdjustments(brightness=20)
        assert adj.brightness == 20
        assert adj.contrast == 0


class TestImageProcessorServiceInit:
    """Tests for ImageProcessorService initialization."""

    def test_init_creates_empty_lists(self) -> None:
        """Verify initialization creates empty state lists."""
        svc = ImageProcessorService()
        assert len(svc.original_images) == 3
        assert len(svc.aligned) == 3
        assert len(svc.processed) == 3
        assert len(svc.original_rgb_images) == 3
        assert len(svc.aligned_rgb) == 3
        assert all(img is None for img in svc.original_images)
        assert all(img is None for img in svc.aligned)
        assert all(img is None for img in svc.processed)

    def test_init_creates_adjustments(self) -> None:
        """Verify initialization creates three ChannelAdjustments with defaults."""
        svc = ImageProcessorService()
        assert len(svc.adjustments) == 3
        for adj in svc.adjustments:
            assert isinstance(adj, ChannelAdjustments)
            assert adj.brightness == 0
            assert adj.contrast == 0


class TestLoadChannelFromArray:
    """Tests for loading channels and triggering alignment."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_load_single_channel_stores_rgb(self) -> None:
        """Verify loading a channel stores the RGB array."""
        svc = ImageProcessorService()
        rgb = self._make_rgb_image()

        svc.load_channel_from_array(0, rgb)

        assert svc.original_rgb_images[0] is rgb

    def test_load_single_channel_converts_to_grayscale(self) -> None:
        """Verify RGB is converted to grayscale and stored."""
        svc = ImageProcessorService()
        rgb = self._make_rgb_image()

        svc.load_channel_from_array(0, rgb)

        assert svc.original_images[0] is not None
        assert svc.original_images[0].ndim == 2
        assert svc.original_images[0].shape == (100, 100)
        assert svc.original_images[0].dtype == np.uint8

    def test_load_single_channel_copies_to_processed(self) -> None:
        """Verify processed image is initialized as a copy of original."""
        svc = ImageProcessorService()
        rgb = self._make_rgb_image()

        svc.load_channel_from_array(0, rgb)

        assert svc.processed[0] is not None
        np.testing.assert_array_equal(svc.processed[0], svc.original_images[0])
        assert svc.processed[0] is not svc.original_images[0]

    def test_load_two_channels_no_alignment_yet(self) -> None:
        """Verify alignment is not triggered with fewer than 3 channels."""
        svc = ImageProcessorService()
        rgb1 = self._make_rgb_image(seed=1)
        rgb2 = self._make_rgb_image(seed=2)

        svc.load_channel_from_array(0, rgb1)
        svc.load_channel_from_array(1, rgb2)

        assert svc.aligned[0] is None
        assert svc.aligned[1] is None

    @patch("src.services.processor.align_images")
    def test_load_three_channels_triggers_alignment(self, mock_align: MagicMock) -> None:
        """Verify alignment is triggered when all 3 channels are loaded."""
        # Setup mock to return aligned grayscale and RGB arrays
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

        svc.load_channel_from_array(0, rgb1)
        svc.load_channel_from_array(1, rgb2)
        svc.load_channel_from_array(2, rgb3)

        mock_align.assert_called_once()
        assert svc.aligned[0] is not None
        assert svc.aligned[1] is not None
        assert svc.aligned[2] is not None
        np.testing.assert_array_equal(svc.aligned[0], gray_aligned[0])


class TestAdjustChannel:
    """Tests for adjusting brightness and contrast."""

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
        """Verify adjust_channel updates the adjustment parameters."""
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

        svc.adjust_channel(0, brightness=10, contrast=-5)

        assert svc.adjustments[0].brightness == 10
        assert svc.adjustments[0].contrast == -5

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.apply_adjustments")
    def test_adjust_channel_calls_apply_adjustments(
        self, mock_apply: MagicMock, mock_align: MagicMock
    ) -> None:
        """Verify adjust_channel invokes apply_adjustments with correct parameters."""
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

        svc.adjust_channel(1, brightness=20, contrast=10)

        mock_apply.assert_called()
        call_args = mock_apply.call_args
        assert call_args[0][1] == 20  # brightness
        assert call_args[0][2] == 10  # contrast

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.apply_adjustments")
    def test_adjust_channel_updates_processed_image(
        self, mock_apply: MagicMock, mock_align: MagicMock
    ) -> None:
        """Verify adjust_channel updates the processed image."""
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

        svc.adjust_channel(0, brightness=10, contrast=-5)

        np.testing.assert_array_equal(svc.processed[0], adjusted)


class TestGetChannelPreview:
    """Tests for getting single-channel previews."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_channel_preview_before_load_returns_none(self) -> None:
        """Verify get_channel_preview returns None if channel not loaded."""
        svc = ImageProcessorService()
        result = svc.get_channel_preview(0)
        assert result is None

    @patch("src.services.processor.align_images")
    def test_get_channel_preview_returns_processed_image(self, mock_align: MagicMock) -> None:
        """Verify get_channel_preview returns the processed image after loading."""
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

        preview = svc.get_channel_preview(1)
        assert preview is not None
        np.testing.assert_array_equal(preview, svc.processed[1])


class TestGetChannel:
    """Tests for retrieving single channels with optional cropping."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_channel_before_load_returns_none(self) -> None:
        """Verify get_channel returns None if channel not loaded."""
        svc = ImageProcessorService()
        result = svc.get_channel(0)
        assert result is None

    @patch("src.services.processor.align_images")
    def test_get_channel_without_crop_returns_full_image(self, mock_align: MagicMock) -> None:
        """Verify get_channel without crop returns the full processed image."""
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

        result = svc.get_channel(2)
        np.testing.assert_array_equal(result, svc.processed[2])

    @patch("src.services.processor.align_images")
    def test_get_channel_with_crop_returns_cropped_region(self, mock_align: MagicMock) -> None:
        """Verify get_channel with crop returns the specified region."""
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
        result = svc.get_channel(0, crop=crop)

        expected = svc.processed[0][20:60, 10:40]
        np.testing.assert_array_equal(result, expected)

    @patch("src.services.processor.align_images")
    def test_get_channel_crop_creates_copy(self, mock_align: MagicMock) -> None:
        """Verify get_channel with crop returns a copy, not a view."""
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * i for i in range(1, 4)
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        for i in range(3):
            svc.load_channel_from_array(i, self._make_rgb_image(seed=i))

        crop = (10, 20, 30, 40)
        result = svc.get_channel(0, crop=crop)

        # Verify it's a copy by checking the base is None (not a view)
        assert result.base is None or result.base is not svc.processed[0]


class TestGetCombined:
    """Tests for retrieving combined RGB images."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_combined_before_load_returns_none(self) -> None:
        """Verify get_combined returns None if channels not loaded."""
        svc = ImageProcessorService()
        result = svc.get_combined()
        assert result is None

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_without_crop_calls_combine_channels(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Verify get_combined invokes combine_channels."""
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

        result = svc.get_combined()

        mock_combine.assert_called_once()
        np.testing.assert_array_equal(result, combined_rgb)

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_with_intensities(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Verify get_combined passes intensities to combine_channels."""
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
        result = svc.get_combined(intensities=intensities)

        call_args = mock_combine.call_args
        assert call_args[0][1] == intensities

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_uses_default_intensities(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Verify get_combined uses default intensities [100, 100, 100]."""
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

        svc.get_combined()

        call_args = mock_combine.call_args
        assert call_args[0][1] == [100, 100, 100]

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_with_crop(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Verify get_combined with crop returns cropped region."""
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
        result = svc.get_combined(crop=crop)

        expected = combined_rgb[20:60, 10:40]
        np.testing.assert_array_equal(result, expected)

    @patch("src.services.processor.align_images")
    @patch("src.services.processor.combine_channels")
    def test_get_combined_returns_none_when_combine_channels_returns_none(
        self, mock_combine: MagicMock, mock_align: MagicMock
    ) -> None:
        """Verify get_combined returns None if combine_channels returns None."""
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

        result = svc.get_combined()
        assert result is None


class TestHasAlignedChannels:
    """Tests for checking aligned channel state."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_has_aligned_channels_false_initially(self) -> None:
        """Verify has_aligned_channels returns False initially."""
        svc = ImageProcessorService()
        assert svc.has_aligned_channels() is False

    @patch("src.services.processor.align_images")
    def test_has_aligned_channels_true_after_load(self, mock_align: MagicMock) -> None:
        """Verify has_aligned_channels returns True after loading all channels."""
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

        assert svc.has_aligned_channels() is True


class TestHasProcessedChannels:
    """Tests for checking processed channel state."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_has_processed_channels_false_initially(self) -> None:
        """Verify has_processed_channels returns False initially."""
        svc = ImageProcessorService()
        assert svc.has_processed_channels() is False

    @patch("src.services.processor.align_images")
    def test_has_processed_channels_true_after_load(self, mock_align: MagicMock) -> None:
        """Verify has_processed_channels returns True after loading a channel."""
        gray_aligned = [
            np.ones((100, 100), dtype=np.uint8) * 50,
            np.ones((100, 100), dtype=np.uint8) * 100,
            np.ones((100, 100), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        svc.load_channel_from_array(0, self._make_rgb_image(seed=0))

        assert svc.has_processed_channels() is True


class TestGetImageDimensions:
    """Tests for retrieving image dimensions."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    def test_get_image_dimensions_before_load_returns_none(self) -> None:
        """Verify get_image_dimensions returns None initially."""
        svc = ImageProcessorService()
        result = svc.get_image_dimensions()
        assert result is None

    @patch("src.services.processor.align_images")
    def test_get_image_dimensions_after_load(self, mock_align: MagicMock) -> None:
        """Verify get_image_dimensions returns correct dimensions after loading."""
        gray_aligned = [
            np.ones((50, 75), dtype=np.uint8) * 50,
            np.ones((50, 75), dtype=np.uint8) * 100,
            np.ones((50, 75), dtype=np.uint8) * 150,
        ]
        rgb_aligned = [np.dstack([g] * 3) for g in gray_aligned]
        mock_align.return_value = (gray_aligned, rgb_aligned)

        svc = ImageProcessorService()
        rgb = self._make_rgb_image(height=50, width=75)
        for i in range(3):
            svc.load_channel_from_array(i, rgb)

        dims = svc.get_image_dimensions()
        assert dims == (50, 75)


class TestReset:
    """Tests for resetting service state."""

    @staticmethod
    def _make_rgb_image(height: int = 100, width: int = 100, seed: int = 42) -> np.ndarray:
        """Create a synthetic RGB image for testing."""
        rng = np.random.RandomState(seed)
        return rng.randint(0, 256, (height, width, 3), dtype=np.uint8)

    @patch("src.services.processor.align_images")
    def test_reset_clears_all_images(self, mock_align: MagicMock) -> None:
        """Verify reset clears all image arrays."""
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

        svc.reset()

        assert all(img is None for img in svc.original_images)
        assert all(img is None for img in svc.aligned)
        assert all(img is None for img in svc.processed)
        assert all(img is None for img in svc.original_rgb_images)
        assert all(img is None for img in svc.aligned_rgb)

    @patch("src.services.processor.align_images")
    def test_reset_resets_adjustments(self, mock_align: MagicMock) -> None:
        """Verify reset resets all adjustment values."""
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

        # Modify adjustments
        svc.adjust_channel(0, brightness=10, contrast=-5)
        svc.adjust_channel(1, brightness=-10, contrast=5)

        svc.reset()

        for adj in svc.adjustments:
            assert adj.brightness == 0
            assert adj.contrast == 0

    @patch("src.services.processor.align_images")
    def test_reset_allows_reuse(self, mock_align: MagicMock) -> None:
        """Verify service can be reused after reset."""
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

        svc.reset()

        rgb2 = np.ones((50, 50, 3), dtype=np.uint8) * 200
        svc.load_channel_from_array(0, rgb2)

        assert svc.original_rgb_images[0] is not None
        assert svc.original_images[0] is not None
