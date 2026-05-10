"""Unit tests for src/ui/handlers/image_saving.py."""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

# Mock PyQt5 before importing Qt-dependent modules
sys.modules["PyQt5"] = MagicMock()
sys.modules["PyQt5.QtCore"] = MagicMock()
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()

from src.ui.handlers.image_saving import apply_crop, save_image


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """RGB image (100x100x3) for testing."""
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_grayscale_image() -> np.ndarray:
    """Grayscale image (100x100) for testing."""
    return np.random.randint(0, 256, (100, 100), dtype=np.uint8)


class TestApplyCrop:
    """
    Test Design Specification: apply_crop()
    Module under test: src/ui/handlers/image_saving.py

    Contract:
        Extracts a rectangular region from an image based on crop coordinates.
        Accepts an image array (2D or 3D) and a crop rectangle as (x, y, width, height).
        Validates coordinates to prevent out-of-bounds access (clamps to image boundaries).
        Returns the cropped region as a numpy array with original dtype and channels preserved.
        If crop_rect is None, returns the image unchanged.
        If image is None or empty, returns empty array.

    Equivalence partitions:
        EP1  None image → returns empty array
        EP2  Empty image (size=0) → returns empty array
        EP3  None crop_rect → returns image unchanged
        EP4  Valid crop_rect within bounds → returns correct cropped region
        EP5  Crop rect with origin offset (x > 0, y > 0) → correct subregion extracted
        EP6  Crop rect with out-of-bounds coordinates → clamped to valid range

    Boundary values:
        BV1  crop_rect = (0, 0, w, h) → full image crop
        BV2  crop_rect at image edge → correct boundary handling
        BV3  crop_rect exceeds image dimensions → clamped to image size
        BV4  crop_rect with negative coordinates → clamped to 0
        BV5  Minimum valid crop (1x1) → returns single pixel

    Exclusions:
        - Validation of image dtype is delegated to numpy; we assume uint8.
        - Performance optimization is not tested; correctness is primary.

    Constraints:
        - Tests use synthetic numpy arrays (no file IO).
        - Cropping logic verified via array shape and pixel value assertions.
    """

    def test_none_image_returns_empty_array(self) -> None:
        """
        Given image is None,
        When apply_crop is called,
        Then returns empty numpy array.
        """
        # Arrange
        crop_rect = (10, 10, 50, 50)

        # Act
        result = apply_crop(None, crop_rect)

        # Assert
        assert isinstance(result, np.ndarray)
        assert result.size == 0

    def test_empty_image_returns_empty_array(self) -> None:
        """
        Given image array with size 0,
        When apply_crop is called,
        Then returns empty numpy array.
        """
        # Arrange
        empty_image = np.array([], dtype=np.uint8)
        crop_rect = (0, 0, 10, 10)

        # Act
        result = apply_crop(empty_image, crop_rect)

        # Assert
        assert result.size == 0

    def test_none_crop_rect_returns_full_image(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given crop_rect is None,
        When apply_crop is called,
        Then returns image unchanged.
        """
        # Arrange
        crop_rect = None

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        np.testing.assert_array_equal(result, sample_rgb_image)

    def test_crop_at_origin_extracts_region(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given crop_rect = (0, 0, 50, 50),
        When apply_crop is called,
        Then returns top-left 50x50 region.
        """
        # Arrange
        crop_rect = (0, 0, 50, 50)

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        assert result.shape == (50, 50, 3)
        np.testing.assert_array_equal(result, sample_rgb_image[0:50, 0:50, :])

    def test_crop_with_offset_extracts_correct_region(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given crop_rect = (20, 30, 40, 40),
        When apply_crop is called,
        Then returns region starting at (x=20, y=30) with width=40, height=40.
        """
        # Arrange
        crop_rect = (20, 30, 40, 40)

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        assert result.shape == (40, 40, 3)
        np.testing.assert_array_equal(result, sample_rgb_image[30:70, 20:60, :])

    def test_crop_preserves_channels(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given a 3-channel RGB image,
        When apply_crop is called,
        Then result preserves all 3 channels.
        """
        # Arrange
        crop_rect = (10, 10, 50, 50)

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        assert len(result.shape) == 3
        assert result.shape[2] == 3

    def test_crop_clamps_width_to_image_boundary(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given crop_rect with width extending beyond image,
        When apply_crop is called,
        Then width is clamped to remaining pixels.
        """
        # Arrange
        crop_rect = (80, 10, 50, 30)

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        assert result.shape == (30, 20, 3)

    def test_crop_clamps_height_to_image_boundary(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given crop_rect with height extending beyond image,
        When apply_crop is called,
        Then height is clamped to remaining pixels.
        """
        # Arrange
        crop_rect = (10, 80, 50, 50)

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        assert result.shape == (20, 50, 3)

    def test_crop_clamps_negative_origin_to_zero(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given crop_rect with negative x or y,
        When apply_crop is called,
        Then negative coordinates are clamped to 0.
        """
        # Arrange
        crop_rect = (-10, -20, 50, 50)

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        assert result.shape == (50, 50, 3)
        np.testing.assert_array_equal(result, sample_rgb_image[0:50, 0:50, :])

    def test_minimum_crop_size(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given crop_rect = (0, 0, 1, 1),
        When apply_crop is called,
        Then returns single-pixel region.
        """
        # Arrange
        crop_rect = (0, 0, 1, 1)

        # Act
        result = apply_crop(sample_rgb_image, crop_rect)

        # Assert
        assert result.shape == (1, 1, 3)

    def test_grayscale_image_crop(self, sample_grayscale_image: np.ndarray) -> None:
        """
        Given a grayscale (2D) image,
        When apply_crop is called,
        Then 2D structure is preserved.
        """
        # Arrange
        crop_rect = (10, 10, 50, 50)

        # Act
        result = apply_crop(sample_grayscale_image, crop_rect)

        # Assert
        assert len(result.shape) == 2
        assert result.shape == (50, 50)


class TestSaveImage:
    """
    Test Design Specification: save_image()
    Module under test: src/ui/handlers/image_saving.py

    Contract:
        Saves a numpy array as an image file in specified format (JPEG, PNG, TIFF, etc).
        Handles both grayscale (2D) and RGB/BGR (3D) images.
        For RGB images, converts to BGR before saving if is_bgr=False.
        Dispatches to cv2.imwrite with format-specific parameters (quality/compression).
        Returns (True, filepath) on success.
        Returns (False, error_message) on failure (invalid path, permission error, etc).

    Equivalence partitions:
        EP1  Valid image + valid filepath + JPEG format → saved successfully
        EP2  Valid image + valid filepath + PNG format → saved successfully
        EP3  Valid image + valid filepath + TIFF format → saved successfully
        EP4  image is None → returns False with error message
        EP5  image.size == 0 (empty) → returns False with error message
        EP6  filepath is None → returns False with error message
        EP7  filepath with invalid directory → FileNotFoundError caught
        EP8  filepath with no write permission → PermissionError caught
        EP9  is_bgr=True and 3-channel image → RGB→BGR conversion applied
        EP10 is_bgr=False and 3-channel image → no color conversion
        EP11 2D grayscale image → saved as-is without conversion

    Boundary values:
        BV1  Minimum image (1x1 single pixel)
        BV2  Large image (4000x3000)
        BV3  file_format from extension (auto-detect from filepath)
        BV4  file_format explicitly specified (overrides extension)

    Exclusions:
        - cv2.imwrite success/failure is mocked; actual file writing not tested.
        - Multi-channel images beyond 3 channels not tested (out of spec).

    Constraints:
        - cv2.imwrite is mocked to avoid actual disk writes.
        - Tests verify correct parameters passed to cv2 and error handling.
    """

    def test_none_image_returns_error(self) -> None:
        """
        Given image is None,
        When save_image is called,
        Then returns (False, error_message).
        """
        # Arrange
        filepath = "/tmp/image.jpg"

        # Act
        success, message = save_image(None, filepath, "jpg")

        # Assert
        assert success is False
        assert "No image data to save" in message

    def test_empty_image_returns_error(self) -> None:
        """
        Given image array with size 0,
        When save_image is called,
        Then returns (False, error_message).
        """
        # Arrange
        empty_image = np.array([], dtype=np.uint8)
        filepath = "/tmp/image.jpg"

        # Act
        success, message = save_image(empty_image, filepath, "jpg")

        # Assert
        assert success is False
        assert "No image data to save" in message

    def test_none_filepath_returns_error(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given filepath is None,
        When save_image is called,
        Then returns (False, error_message).
        """
        # Arrange
        filepath = None

        # Act
        success, message = save_image(sample_rgb_image, filepath, "jpg")

        # Assert
        assert success is False
        assert "No filepath provided" in message

    def test_successful_jpeg_save(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given valid image and JPEG format,
        When save_image is called,
        Then returns (True, filepath).
        """
        # Arrange
        filepath = "/tmp/image.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            success, message = save_image(sample_rgb_image, filepath, "jpg", is_bgr=False)

        # Assert
        assert success is True
        assert message == filepath

    def test_successful_png_save(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given valid image and PNG format,
        When save_image is called,
        Then returns (True, filepath).
        """
        # Arrange
        filepath = "/tmp/image.png"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            success, message = save_image(sample_rgb_image, filepath, "png", is_bgr=False)

        # Assert
        assert success is True
        assert message == filepath

    def test_successful_tiff_save(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given valid image and TIFF format,
        When save_image is called,
        Then returns (True, filepath).
        """
        # Arrange
        filepath = "/tmp/image.tif"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            success, message = save_image(sample_rgb_image, filepath, "tif", is_bgr=False)

        # Assert
        assert success is True

    def test_format_detection_from_filepath(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given filepath with .jpg extension and no format specified,
        When save_image is called,
        Then format is extracted from filepath and image is saved.
        """
        # Arrange
        filepath = "/tmp/image.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            success, message = save_image(sample_rgb_image, filepath, None, is_bgr=False)

        # Assert
        assert success is True

    def test_no_extension_no_format_returns_error(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given filepath without extension and format not specified,
        When save_image is called,
        Then returns error message.
        """
        # Arrange
        filepath = "/tmp/image"

        # Act
        success, message = save_image(sample_rgb_image, filepath, None)

        # Assert
        assert success is False
        assert "No file extension" in message

    def test_3_channel_image_saved_successfully(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given 3-channel image and valid filepath,
        When save_image is called,
        Then image is saved successfully.
        """
        # Arrange
        filepath = "/tmp/image.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            success, message = save_image(sample_rgb_image, filepath, "jpg", is_bgr=False)

        # Assert
        assert success is True

    def test_grayscale_image_saved_without_color_handling(self, sample_grayscale_image: np.ndarray) -> None:
        """
        Given 2D grayscale image,
        When save_image is called with is_bgr=True,
        Then image is saved (no color conversion on 2D images).
        """
        # Arrange
        filepath = "/tmp/gray.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            save_image(sample_grayscale_image, filepath, "jpg", is_bgr=True)

        # Assert
        mock_imwrite.assert_called_once()

    def test_cv2_imwrite_failure_returns_error(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given cv2.imwrite returns False,
        When save_image is called,
        Then returns (False, error_message).
        """
        # Arrange
        filepath = "/tmp/image.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = False
            success, message = save_image(sample_rgb_image, filepath, "jpg", is_bgr=False)

        # Assert
        assert success is False
        assert "Failed to save image" in message

    def test_file_not_found_error_caught(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given cv2.imwrite raises FileNotFoundError,
        When save_image is called,
        Then exception is caught and error message returned.
        """
        # Arrange
        filepath = "/invalid/path/image.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.side_effect = FileNotFoundError("Invalid path")
            success, message = save_image(sample_rgb_image, filepath, "jpg", is_bgr=False)

        # Assert
        assert success is False
        assert "Error saving image" in message

    def test_permission_error_caught(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given cv2.imwrite raises PermissionError,
        When save_image is called,
        Then exception is caught and error message returned.
        """
        # Arrange
        filepath = "/root/image.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.side_effect = PermissionError("Access denied")
            success, message = save_image(sample_rgb_image, filepath, "jpg", is_bgr=False)

        # Assert
        assert success is False
        assert "Error saving image" in message

    def test_grayscale_image_saved_without_conversion(self, sample_grayscale_image: np.ndarray) -> None:
        """
        Given 2D grayscale image,
        When save_image is called,
        Then cv2.cvtColor is not called (no color conversion).
        """
        # Arrange
        filepath = "/tmp/gray.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            with patch("src.ui.handlers.image_saving.cv2.cvtColor") as mock_cvtcolor:
                mock_imwrite.return_value = True
                save_image(sample_grayscale_image, filepath, "jpg", is_bgr=False)

        # Assert
        mock_cvtcolor.assert_not_called()

    def test_jpeg_format_variations(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given 'jpeg' format string (not 'jpg'),
        When save_image is called,
        Then image is saved successfully.
        """
        # Arrange
        filepath = "/tmp/image.jpeg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            save_image(sample_rgb_image, filepath, "jpeg", is_bgr=False)

        # Assert
        mock_imwrite.assert_called_once()

    def test_tiff_format_variations(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given 'tiff' format string (not 'tif'),
        When save_image is called,
        Then image is saved successfully.
        """
        # Arrange
        filepath = "/tmp/image.tiff"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            save_image(sample_rgb_image, filepath, "tiff", is_bgr=False)

        # Assert
        mock_imwrite.assert_called_once()

