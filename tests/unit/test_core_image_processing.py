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

"""Unit tests for src.core.image_processing module."""

import numpy as np
import pytest

from src.core.image_processing import apply_adjustments, combine_channels


@pytest.fixture
def gray_mid() -> np.ndarray:
    """128-value grayscale image — mid-range so both positive and negative shifts are testable."""
    return np.full((4, 4), 128, dtype=np.uint8)


@pytest.fixture
def gray_black() -> np.ndarray:
    """All-zero grayscale image."""
    return np.zeros((4, 4), dtype=np.uint8)


@pytest.fixture
def gray_white() -> np.ndarray:
    """All-255 grayscale image."""
    return np.full((4, 4), 255, dtype=np.uint8)


@pytest.fixture
def three_channels(gray_mid: np.ndarray) -> list:
    """Three independent copies of the mid-grey image."""
    return [gray_mid.copy(), gray_mid.copy(), gray_mid.copy()]


class TestApplyAdjustments:
    """Tests for apply_adjustments()."""

    def test_none_input_returns_none(self) -> None:
        """None input must propagate as None — callers rely on this sentinel."""
        assert apply_adjustments(None) is None

    def test_zero_adjustments_returns_identical_image(self, gray_mid: np.ndarray) -> None:
        """Brightness=0, contrast=0 should leave every pixel unchanged."""
        result = apply_adjustments(gray_mid, brightness=0, contrast=0)
        np.testing.assert_array_equal(result, gray_mid)

    def test_positive_brightness_increases_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Positive brightness adds to each pixel value."""
        result = apply_adjustments(gray_mid, brightness=10, contrast=0)
        np.testing.assert_array_equal(result, np.full((4, 4), 138, dtype=np.uint8))

    def test_negative_brightness_decreases_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Negative brightness subtracts from each pixel value."""
        result = apply_adjustments(gray_mid, brightness=-10, contrast=0)
        np.testing.assert_array_equal(result, np.full((4, 4), 118, dtype=np.uint8))

    def test_positive_contrast_multiplies_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Positive contrast multiplies by (1 + contrast/100), increasing values above zero."""
        result = apply_adjustments(gray_mid, brightness=0, contrast=100)
        # 128 * (1 + 1.0) = 256 → clipped to 255
        np.testing.assert_array_equal(result, np.full((4, 4), 255, dtype=np.uint8))

    def test_negative_contrast_reduces_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Negative contrast multiplies by (1 + contrast/100), reducing values."""
        result = apply_adjustments(gray_mid, brightness=0, contrast=-50)
        # 128 * 0.5 = 64
        np.testing.assert_array_equal(result, np.full((4, 4), 64, dtype=np.uint8))

    def test_high_brightness_clips_to_255(self, gray_white: np.ndarray) -> None:
        """Values above 255 must be clipped to 255."""
        result = apply_adjustments(gray_white, brightness=100, contrast=0)
        np.testing.assert_array_equal(result, np.full((4, 4), 255, dtype=np.uint8))

    def test_low_brightness_clips_to_0(self, gray_black: np.ndarray) -> None:
        """Values below 0 must be clipped to 0."""
        result = apply_adjustments(gray_black, brightness=-100, contrast=0)
        np.testing.assert_array_equal(result, np.zeros((4, 4), dtype=np.uint8))

    def test_black_image_unaffected_by_contrast_alone(self, gray_black: np.ndarray) -> None:
        """Multiplying zero pixels by any contrast factor still yields zero."""
        result = apply_adjustments(gray_black, brightness=0, contrast=50)
        np.testing.assert_array_equal(result, gray_black)

    def test_output_dtype_is_uint8(self, gray_mid: np.ndarray) -> None:
        """Output must always be uint8 regardless of input values."""
        result = apply_adjustments(gray_mid, brightness=20, contrast=10)
        assert result is not None
        assert result.dtype == np.uint8

    def test_output_shape_matches_input(self, gray_mid: np.ndarray) -> None:
        """Output shape must equal input shape."""
        result = apply_adjustments(gray_mid, brightness=5, contrast=5)
        assert result is not None
        assert result.shape == gray_mid.shape

    def test_combined_brightness_and_contrast(self) -> None:
        """Formula: pixel * (1 + contrast/100) + brightness, clipped."""
        img = np.full((2, 2), 100, dtype=np.uint8)
        # 100 * (1 + 0.1) + 10 = 120
        result = apply_adjustments(img, brightness=10, contrast=10)
        np.testing.assert_array_equal(result, np.full((2, 2), 120, dtype=np.uint8))


class TestCombineChannels:
    """Tests for combine_channels()."""

    def test_any_none_channel_returns_none(self, gray_mid: np.ndarray) -> None:
        """If any channel is None the function must return None."""
        assert combine_channels([gray_mid, None, gray_mid], [100, 100, 100]) is None
        assert combine_channels([None, gray_mid, gray_mid], [100, 100, 100]) is None
        assert combine_channels([gray_mid, gray_mid, None], [100, 100, 100]) is None

    def test_all_none_channels_returns_none(self) -> None:
        """All-None channel list must return None."""
        assert combine_channels([None, None, None], [100, 100, 100]) is None

    def test_100_percent_intensity_preserves_pixel_values(self, three_channels: list) -> None:
        """At 100% intensity each channel pixel should equal the input pixel value."""
        result = combine_channels(three_channels, [100, 100, 100])
        assert result is not None
        expected = np.full((4, 4, 3), 128, dtype=np.uint8)
        np.testing.assert_array_equal(result, expected)

    def test_200_percent_intensity_doubles_and_clips(self, three_channels: list) -> None:
        """200% intensity doubles values; anything exceeding 255 is clipped."""
        result = combine_channels(three_channels, [200, 200, 200])
        assert result is not None
        # 128 * 2 = 256 → 255
        np.testing.assert_array_equal(result, np.full((4, 4, 3), 255, dtype=np.uint8))

    def test_0_percent_intensity_produces_black_channel(self, gray_mid: np.ndarray) -> None:
        """0% intensity on all channels produces an all-black image."""
        result = combine_channels([gray_mid, gray_mid, gray_mid], [0, 0, 0])
        assert result is not None
        np.testing.assert_array_equal(result, np.zeros((4, 4, 3), dtype=np.uint8))

    def test_independent_per_channel_intensity(self, gray_mid: np.ndarray) -> None:
        """Each channel's intensity is applied independently."""
        ch = gray_mid.copy()  # all pixels 128
        result = combine_channels([ch, ch, ch], [100, 50, 0])
        assert result is not None
        # R: 128*1.0=128, G: 128*0.5=64, B: 128*0.0=0
        np.testing.assert_array_equal(result[:, :, 0], np.full((4, 4), 128, dtype=np.uint8))
        np.testing.assert_array_equal(result[:, :, 1], np.full((4, 4), 64, dtype=np.uint8))
        np.testing.assert_array_equal(result[:, :, 2], np.zeros((4, 4), dtype=np.uint8))

    def test_output_shape_is_hwc_3(self, gray_mid: np.ndarray) -> None:
        """Output shape must be (H, W, 3)."""
        result = combine_channels([gray_mid, gray_mid, gray_mid], [100, 100, 100])
        assert result is not None
        assert result.shape == (4, 4, 3)

    def test_output_dtype_is_uint8(self, gray_mid: np.ndarray) -> None:
        """Output must be uint8."""
        result = combine_channels([gray_mid, gray_mid, gray_mid], [100, 100, 100])
        assert result is not None
        assert result.dtype == np.uint8

    def test_channels_map_to_correct_rgb_planes(self) -> None:
        """First channel → R plane, second → G, third → B."""
        r = np.full((2, 2), 100, dtype=np.uint8)
        g = np.full((2, 2), 150, dtype=np.uint8)
        b = np.full((2, 2), 200, dtype=np.uint8)
        result = combine_channels([r, g, b], [100, 100, 100])
        assert result is not None
        np.testing.assert_array_equal(result[:, :, 0], r)
        np.testing.assert_array_equal(result[:, :, 1], g)
        np.testing.assert_array_equal(result[:, :, 2], b)

    def test_output_is_clipped_to_255(self) -> None:
        """Values produced by high intensity must not exceed 255."""
        bright = np.full((2, 2), 200, dtype=np.uint8)
        result = combine_channels([bright, bright, bright], [200, 200, 200])
        assert result is not None
        assert result.max() <= 255

    def test_output_is_clipped_to_0(self) -> None:
        """Output values must never be negative (lower-bound clipping)."""
        dark = np.zeros((2, 2), dtype=np.uint8)
        result = combine_channels([dark, dark, dark], [0, 0, 0])
        assert result is not None
        assert result.min() >= 0
