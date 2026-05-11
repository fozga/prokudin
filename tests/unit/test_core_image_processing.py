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
    """
    Test Design Specification: apply_adjustments()
    Module under test: src/core/image_processing.py

    Contract:
        Applies brightness and contrast adjustments to a grayscale image.
        Formula: output = clip(pixel * (1 + contrast/100) + brightness, 0, 255).
        Input None returns None (sentinel for missing channel).
        Output is uint8, same shape as input.

    Equivalence partitions:
        EP1  None input                     → returns None
        EP2  Zero adjustments               → identity (output equals input)
        EP3  Positive brightness only       → all pixels shifted up
        EP4  Negative brightness only       → all pixels shifted down
        EP5  Positive contrast only         → pixels multiplied, above zero increased
        EP6  Negative contrast only         → pixels multiplied, values reduced
        EP7  Combined brightness+contrast   → both applied in order
        EP8  All-zero input (black)         → contrast has no effect
        EP9  All-255 input (white)          → may saturate
        EP10 Mid-range input (128)          → both directions testable

    Boundary values:
        BV1  Brightness = +100 (large positive)
        BV2  Brightness = -100 (large negative)
        BV3  Contrast = +100 (doubles pixels from mid-point)
        BV4  Contrast = -50 (halves pixels)
        BV5  Output = 255 (upper clip boundary)
        BV6  Output = 0 (lower clip boundary)

    Exclusions:
        - Non-numeric input types (caller validates)
        - Non-uint8 input dtype (caller handles conversion)
        - NaN, inf values (assumed not present in images)

    Constraints:
        - Output always uint8 (clipped to [0, 255])
        - Same shape as input
        - Formula applied per-pixel
    """

    def test_none_input_returns_none(self) -> None:
        """Given: apply_adjustments called with None
        When: no image is provided
        Then: None is returned as sentinel value."""
        assert apply_adjustments(None) is None

    def test_zero_adjustments_returns_identical_image(self, gray_mid: np.ndarray) -> None:
        """Given: grayscale image with brightness=0, contrast=0
        When: apply_adjustments is called with zero values
        Then: the returned image is identical to the input."""
        # Act
        result = apply_adjustments(gray_mid, brightness=0, contrast=0)
        # Assert
        np.testing.assert_array_equal(result, gray_mid)

    def test_positive_brightness_increases_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Given: grayscale image with brightness=10, contrast=0
        When: apply_adjustments is applied
        Then: each pixel value is increased by 10."""
        # Act
        result = apply_adjustments(gray_mid, brightness=10, contrast=0)
        # Assert
        np.testing.assert_array_equal(result, np.full((4, 4), 138, dtype=np.uint8))

    def test_negative_brightness_decreases_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Given: grayscale image with brightness=-10, contrast=0
        When: apply_adjustments is applied
        Then: each pixel value is decreased by 10."""
        # Act
        result = apply_adjustments(gray_mid, brightness=-10, contrast=0)
        # Assert
        np.testing.assert_array_equal(result, np.full((4, 4), 118, dtype=np.uint8))

    def test_positive_contrast_multiplies_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Given: grayscale image with brightness=0, contrast=100
        When: apply_adjustments is applied
        Then: pixel values are multiplied by (1 + contrast/100) and clipped."""
        # Act
        result = apply_adjustments(gray_mid, brightness=0, contrast=100)
        # Assert - 128 * (1 + 1.0) = 256 → clipped to 255
        np.testing.assert_array_equal(result, np.full((4, 4), 255, dtype=np.uint8))

    def test_negative_contrast_reduces_pixel_values(self, gray_mid: np.ndarray) -> None:
        """Given: grayscale image with brightness=0, contrast=-50
        When: apply_adjustments is applied
        Then: pixel values are multiplied by (1 - 0.5) = 0.5."""
        # Act
        result = apply_adjustments(gray_mid, brightness=0, contrast=-50)
        # Assert - 128 * 0.5 = 64
        np.testing.assert_array_equal(result, np.full((4, 4), 64, dtype=np.uint8))

    def test_high_brightness_clips_to_255(self, gray_white: np.ndarray) -> None:
        """Given: white image with brightness=100
        When: apply_adjustments is applied
        Then: values exceed 255 are clipped to 255."""
        # Act
        result = apply_adjustments(gray_white, brightness=100, contrast=0)
        # Assert
        np.testing.assert_array_equal(result, np.full((4, 4), 255, dtype=np.uint8))

    def test_low_brightness_clips_to_0(self, gray_black: np.ndarray) -> None:
        """Given: black image with brightness=-100
        When: apply_adjustments is applied
        Then: values below 0 are clipped to 0."""
        # Act
        result = apply_adjustments(gray_black, brightness=-100, contrast=0)
        # Assert
        np.testing.assert_array_equal(result, np.zeros((4, 4), dtype=np.uint8))

    def test_black_image_unaffected_by_contrast_alone(self, gray_black: np.ndarray) -> None:
        """Given: black image with brightness=0, contrast=50
        When: apply_adjustments is applied
        Then: zero pixels remain zero regardless of contrast multiplier."""
        # Act
        result = apply_adjustments(gray_black, brightness=0, contrast=50)
        # Assert
        np.testing.assert_array_equal(result, gray_black)

    def test_output_dtype_is_uint8(self, gray_mid: np.ndarray) -> None:
        """Given: grayscale image with brightness=20, contrast=10
        When: apply_adjustments is applied
        Then: the output dtype is always uint8."""
        # Act
        result = apply_adjustments(gray_mid, brightness=20, contrast=10)
        # Assert
        assert result is not None
        assert result.dtype == np.uint8

    def test_output_shape_matches_input(self, gray_mid: np.ndarray) -> None:
        """Given: grayscale image with brightness=5, contrast=5
        When: apply_adjustments is applied
        Then: the output shape matches the input shape."""
        # Act
        result = apply_adjustments(gray_mid, brightness=5, contrast=5)
        # Assert
        assert result is not None
        assert result.shape == gray_mid.shape

    def test_combined_brightness_and_contrast(self) -> None:
        """Given: image with brightness=10, contrast=10
        When: apply_adjustments is applied to pixels=100
        Then: formula pixel*(1+contrast/100)+brightness gives 120."""
        # Arrange
        img = np.full((2, 2), 100, dtype=np.uint8)
        # Act
        result = apply_adjustments(img, brightness=10, contrast=10)
        # Assert - 100 * (1 + 0.1) + 10 = 120
        np.testing.assert_array_equal(result, np.full((2, 2), 120, dtype=np.uint8))


class TestCombineChannels:
    """
    Test Design Specification: combine_channels()
    Module under test: src/core/image_processing.py

    Contract:
        Combines three grayscale channel images into a single RGB image with
        per-channel intensity multipliers. Returns (H, W, 3) uint8 array.
        If any channel is None, returns None (sentinel). Intensities are percentages
        (100 = 1.0x). Formula: output[..., i] = clip(channel[i] * intensity[i]/100, 0, 255).

    Equivalence partitions:
        EP1  Any channel is None            → returns None (short-circuit)
        EP2  All channels are None          → returns None
        EP3  All channels present, 100% intensity  → preserves pixel values
        EP4  Intensity > 100%               → pixels amplified and clipped
        EP5  Intensity < 100%               → pixels dampened
        EP6  Intensity = 0%                 → black pixels (0)
        EP7  Different intensity per channel → independent per-channel scaling
        EP8  Output shape (H, W, 3)         → stacked HWC format

    Boundary values:
        BV1  Intensity = 0% (minimum)
        BV2  Intensity = 100% (identity)
        BV3  Intensity = 200% (double)
        BV4  Output pixel = 0 (all channels)
        BV5  Output pixel = 255 (clipped)
        BV6  Different intensities [100, 50, 200] per R, G, B

    Exclusions:
        - Channel size mismatch (assumed caller validates)
        - Non-uint8 input dtype (assumed caller converts)
        - Fewer than 3 channels (tested separately; extras ignored)
        - Non-numeric intensities (caller validates)

    Constraints:
        - Output shape is always (H, W, 3) when not None
        - Output dtype is uint8
        - Channels combined in RGB order (R=channels[0], G=channels[1], B=channels[2])
        - Clipping happens per-pixel after intensity multiplication
    """

    @pytest.mark.parametrize("none_channel_idx", [
        0,  # EP1: red channel is None
        1,  # EP1: green channel is None
        2,  # EP1: blue channel is None
    ], ids=["red_none", "green_none", "blue_none"])
    def test_any_none_channel_returns_none(self, gray_mid: np.ndarray, none_channel_idx: int) -> None:
        """Given: one channel is None
        When: combine_channels is called
        Then: the result is None as sentinel."""
        # Arrange
        channels = [gray_mid.copy() for _ in range(3)]
        channels[none_channel_idx] = None
        intensities = [100, 100, 100]
        # Act
        result = combine_channels(channels, intensities)
        # Assert
        assert result is None

    def test_all_none_channels_returns_none(self) -> None:
        """Given: all three channels are None
        When: combine_channels is called
        Then: None is returned."""
        assert combine_channels([None, None, None], [100, 100, 100]) is None

    def test_100_percent_intensity_preserves_pixel_values(self, three_channels: list) -> None:
        """Given: three channels with 100% intensity
        When: combine_channels is called
        Then: output RGB preserves original pixel values."""
        # Act
        result = combine_channels(three_channels, [100, 100, 100])
        # Assert
        assert result is not None
        expected = np.full((4, 4, 3), 128, dtype=np.uint8)
        np.testing.assert_array_equal(result, expected)

    def test_200_percent_intensity_doubles_and_clips(self, three_channels: list) -> None:
        """Given: three channels with 200% intensity
        When: combine_channels is applied
        Then: pixel values are doubled and clipped to 255."""
        # Act
        result = combine_channels(three_channels, [200, 200, 200])
        # Assert
        assert result is not None
        # 128 * 2 = 256 → 255
        np.testing.assert_array_equal(result, np.full((4, 4, 3), 255, dtype=np.uint8))

    def test_0_percent_intensity_produces_black_channel(self, gray_mid: np.ndarray) -> None:
        """Given: three channels with 0% intensity
        When: combine_channels is called
        Then: output is all-black (zero values)."""
        # Act
        result = combine_channels([gray_mid, gray_mid, gray_mid], [0, 0, 0])
        # Assert
        assert result is not None
        np.testing.assert_array_equal(result, np.zeros((4, 4, 3), dtype=np.uint8))

    def test_independent_per_channel_intensity(self, gray_mid: np.ndarray) -> None:
        """Given: three channels with different intensities [100, 50, 0]
        When: combine_channels is called
        Then: each channel is scaled independently per its intensity."""
        # Arrange
        ch = gray_mid.copy()  # all pixels 128
        # Act
        result = combine_channels([ch, ch, ch], [100, 50, 0])
        # Assert
        assert result is not None
        # R: 128*1.0=128, G: 128*0.5=64, B: 128*0.0=0
        np.testing.assert_array_equal(result[:, :, 0], np.full((4, 4), 128, dtype=np.uint8))
        np.testing.assert_array_equal(result[:, :, 1], np.full((4, 4), 64, dtype=np.uint8))
        np.testing.assert_array_equal(result[:, :, 2], np.zeros((4, 4), dtype=np.uint8))

    def test_output_shape_is_hwc_3(self, gray_mid: np.ndarray) -> None:
        """Given: three channels with 100% intensity
        When: combine_channels is called
        Then: output shape is (H, W, 3)."""
        # Act
        result = combine_channels([gray_mid, gray_mid, gray_mid], [100, 100, 100])
        # Assert
        assert result is not None
        assert result.shape == (4, 4, 3)

    def test_output_dtype_is_uint8(self, gray_mid: np.ndarray) -> None:
        """Given: three channels with 100% intensity
        When: combine_channels is called
        Then: output dtype is uint8."""
        # Act
        result = combine_channels([gray_mid, gray_mid, gray_mid], [100, 100, 100])
        # Assert
        assert result is not None
        assert result.dtype == np.uint8

    def test_channels_map_to_correct_rgb_planes(self) -> None:
        """Given: three distinct channels (R=100, G=150, B=200)
        When: combine_channels is called at 100% intensity
        Then: R, G, B planes contain the respective channel values."""
        # Arrange
        r = np.full((2, 2), 100, dtype=np.uint8)
        g = np.full((2, 2), 150, dtype=np.uint8)
        b = np.full((2, 2), 200, dtype=np.uint8)
        # Act
        result = combine_channels([r, g, b], [100, 100, 100])
        # Assert
        assert result is not None
        np.testing.assert_array_equal(result[:, :, 0], r)
        np.testing.assert_array_equal(result[:, :, 1], g)
        np.testing.assert_array_equal(result[:, :, 2], b)

    def test_output_is_clipped_to_255(self) -> None:
        """Given: bright channels with 200% intensity
        When: combine_channels is called
        Then: output values are clipped to 255 maximum."""
        # Arrange
        bright = np.full((2, 2), 200, dtype=np.uint8)
        # Act
        result = combine_channels([bright, bright, bright], [200, 200, 200])
        # Assert
        assert result is not None
        assert result.max() <= 255

    def test_output_is_clipped_to_0(self) -> None:
        """Given: dark channels with 0% intensity
        When: combine_channels is called
        Then: output values are clipped to 0 minimum."""
        # Arrange
        dark = np.zeros((2, 2), dtype=np.uint8)
        # Act
        result = combine_channels([dark, dark, dark], [0, 0, 0])
        # Assert
        assert result is not None
        assert result.min() >= 0

    def test_fewer_than_three_channels_raises_index_error(self, gray_mid: np.ndarray) -> None:
        """Given: only two channels provided
        When: combine_channels is called
        Then: IndexError is raised."""
        with pytest.raises(IndexError):
            combine_channels([gray_mid, gray_mid], [100, 100, 100])

    def test_more_than_three_channels_ignored(self, gray_mid: np.ndarray) -> None:
        """Given: four channels provided (one extra)
        When: combine_channels is called
        Then: extra channels are silently ignored and only first three are used."""
        # Arrange
        r = np.full((2, 2), 100, dtype=np.uint8)
        g = np.full((2, 2), 150, dtype=np.uint8)
        b = np.full((2, 2), 200, dtype=np.uint8)
        extra = np.full((2, 2), 50, dtype=np.uint8)
        # Act
        result = combine_channels([r, g, b, extra], [100, 100, 100, 100])
        # Assert
        assert result is not None
        # Fourth channel should be ignored; output should match three-channel call
        expected = combine_channels([r, g, b], [100, 100, 100])
        assert expected is not None
        np.testing.assert_array_equal(result, expected)

    def test_exactly_three_channels_preserved(self) -> None:
        """Given: exactly three channels provided
        When: combine_channels is called with 100% intensity
        Then: all three channels are properly combined into RGB output."""
        # Arrange
        r = np.full((2, 2), 100, dtype=np.uint8)
        g = np.full((2, 2), 150, dtype=np.uint8)
        b = np.full((2, 2), 200, dtype=np.uint8)
        # Act
        result = combine_channels([r, g, b], [100, 100, 100])
        # Assert
        assert result is not None
        np.testing.assert_array_equal(result[:, :, 0], r)
        np.testing.assert_array_equal(result[:, :, 1], g)
        np.testing.assert_array_equal(result[:, :, 2], b)

    def test_empty_channel_list_raises_error(self) -> None:
        """Given: empty channel list
        When: combine_channels is called
        Then: IndexError or ValueError is raised."""
        with pytest.raises((IndexError, ValueError)):
            combine_channels([], [100, 100, 100])

    def test_fewer_than_three_intensities_raises_index_error(self, gray_mid: np.ndarray) -> None:
        """Given: only two intensities provided
        When: combine_channels is called
        Then: IndexError is raised."""
        with pytest.raises(IndexError):
            combine_channels([gray_mid, gray_mid, gray_mid], [100, 100])
