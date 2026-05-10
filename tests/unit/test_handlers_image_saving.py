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

from src.ui.handlers.image_saving import (
    _create_combined_image,
    _extract_extension_from_filter,
    _get_file_path_info,
    _save_cropped_images,
    apply_crop,
    save_image,
    save_image_with_dialog,
)


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

    def test_is_bgr_true_applies_color_conversion(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given a 3-channel image and is_bgr=True,
        When save_image is called,
        Then cv2.cvtColor is called to convert RGB to BGR before writing.
        """
        # Arrange
        filepath = "/tmp/image.jpg"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            with patch("src.ui.handlers.image_saving.cv2.cvtColor") as mock_cvtcolor:
                mock_imwrite.return_value = True
                mock_cvtcolor.return_value = sample_rgb_image
                save_image(sample_rgb_image, filepath, "jpg", is_bgr=True)

        # Assert
        mock_cvtcolor.assert_called_once()

    def test_unknown_format_falls_through_to_plain_imwrite(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given an unrecognised format string (not jpg/png/tif),
        When save_image is called,
        Then cv2.imwrite is called without format-specific params.
        """
        # Arrange
        filepath = "/tmp/image.bmp"

        # Act
        with patch("src.ui.handlers.image_saving.cv2.imwrite") as mock_imwrite:
            mock_imwrite.return_value = True
            success, _ = save_image(sample_rgb_image, filepath, "bmp", is_bgr=False)

        # Assert
        assert success is True
        mock_imwrite.assert_called_once_with(filepath, sample_rgb_image)


class TestExtractExtensionFromFilter:
    """
    Test Design Specification: _extract_extension_from_filter()
    Module under test: src/ui/handlers/image_saving.py

    Contract:
        Extracts the first file extension from a Qt file dialog filter string
        such as "JPEG (*.jpg);;TIFF (*.tif)". Returns the extension as a
        lowercase string (without the dot), or None if no extension is found.

    Equivalence partitions:
        EP1  Filter with single extension → lowercase extension returned
        EP2  Filter with multiple extensions → first extension returned
        EP3  Filter string with no extension pattern → None returned
        EP4  Empty string → None returned

    Boundary values:
        BV1  Uppercase extension in filter → returned as lowercase

    Exclusions:
        - Caller is responsible for passing non-None filter strings.

    Constraints:
        - Pure string parsing; no mocking required.
    """

    def test_single_extension_extracted(self) -> None:
        """
        Given filter string "JPEG (*.jpg)",
        When _extract_extension_from_filter is called,
        Then returns "jpg".
        """
        # Arrange
        filter_str = "JPEG (*.jpg)"

        # Act
        result = _extract_extension_from_filter(filter_str)

        # Assert
        assert result == "jpg"

    def test_first_extension_returned_from_multi_extension_filter(self) -> None:
        """
        Given filter "JPEG (*.jpg);;TIFF (*.tif)",
        When _extract_extension_from_filter is called,
        Then returns the first extension "jpg".
        """
        # Arrange
        filter_str = "JPEG (*.jpg);;TIFF (*.tif)"

        # Act
        result = _extract_extension_from_filter(filter_str)

        # Assert
        assert result == "jpg"

    def test_no_extension_pattern_returns_none(self) -> None:
        """
        Given filter string with no *.ext pattern,
        When _extract_extension_from_filter is called,
        Then returns None.
        """
        # Arrange
        filter_str = "All Files (*)"

        # Act
        result = _extract_extension_from_filter(filter_str)

        # Assert
        assert result is None

    def test_empty_string_returns_none(self) -> None:
        """
        Given an empty filter string,
        When _extract_extension_from_filter is called,
        Then returns None.
        """
        # Arrange
        filter_str = ""

        # Act
        result = _extract_extension_from_filter(filter_str)

        # Assert
        assert result is None

    def test_uppercase_extension_returned_as_lowercase(self) -> None:
        """
        Given filter string with uppercase extension "*.TIF",
        When _extract_extension_from_filter is called,
        Then returns "tif" (lowercased).
        """
        # Arrange
        filter_str = "TIFF (*.TIF)"

        # Act
        result = _extract_extension_from_filter(filter_str)

        # Assert
        assert result == "tif"


class TestGetFilePathInfo:
    """
    Test Design Specification: _get_file_path_info()
    Module under test: src/ui/handlers/image_saving.py

    Contract:
        Opens a Qt Save File dialog and returns (filepath, file_format).
        If the dialog is cancelled (returns empty string), returns (None, None).
        If the returned filepath has an extension, extracts file_format from it.
        If the returned filepath has no extension, appends the extension from
        the selected filter and returns the updated filepath with format.
        If neither filepath has extension nor filter provides one, returns
        (filepath, None).

    Equivalence partitions:
        EP1  Dialog cancelled (empty filepath) → (None, None)
        EP2  Filepath with extension → (filepath, format_from_extension)
        EP3  Filepath without extension, filter provides extension
             → (filepath + ".ext", "ext")
        EP4  Filepath without extension, filter provides no extension
             → (filepath, None)

    Boundary values:
        BV1  filepath already ends with a dot (edge path) → extension is empty,
             treated as no extension

    Exclusions:
        - Actual Qt dialog rendering is not tested; QFileDialog is mocked.
        - main_window is passed directly to QFileDialog but not inspected.

    Constraints:
        - QFileDialog.getSaveFileName is patched at import location in
          src.ui.handlers.image_saving.
    """

    def test_cancelled_dialog_returns_none_tuple(self) -> None:
        """
        Given the file dialog returns an empty filepath (user cancelled),
        When _get_file_path_info is called,
        Then returns (None, None).
        """
        # Arrange
        mock_window = MagicMock()

        # Act
        with patch("src.ui.handlers.image_saving.QFileDialog.getSaveFileName", return_value=("", "")):
            filepath, file_format = _get_file_path_info(mock_window, "JPEG (*.jpg)")

        # Assert
        assert filepath is None
        assert file_format is None

    def test_filepath_with_extension_returns_format(self) -> None:
        """
        Given the dialog returns "/out/result.jpg",
        When _get_file_path_info is called,
        Then returns ("/out/result.jpg", "jpg").
        """
        # Arrange
        mock_window = MagicMock()

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result.jpg", "JPEG (*.jpg)"),
        ):
            filepath, file_format = _get_file_path_info(mock_window, "JPEG (*.jpg)")

        # Assert
        assert filepath == "/out/result.jpg"
        assert file_format == "jpg"

    def test_filepath_without_extension_uses_filter_extension(self) -> None:
        """
        Given the dialog returns a filepath with no extension and a JPEG filter,
        When _get_file_path_info is called,
        Then the extension from the filter is appended and format is "jpg".
        """
        # Arrange
        mock_window = MagicMock()

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result", "JPEG (*.jpg)"),
        ):
            filepath, file_format = _get_file_path_info(mock_window, "JPEG (*.jpg)")

        # Assert
        assert filepath == "/out/result.jpg"
        assert file_format == "jpg"

    def test_filepath_without_extension_and_no_filter_ext_returns_none_format(self) -> None:
        """
        Given the dialog returns a filepath with no extension and a filter with no *.ext,
        When _get_file_path_info is called,
        Then returns (filepath, None).
        """
        # Arrange
        mock_window = MagicMock()

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result", "All Files (*)"),
        ):
            filepath, file_format = _get_file_path_info(mock_window, "All Files (*)")

        # Assert
        assert filepath == "/out/result"
        assert file_format is None

    def test_png_extension_extracted_correctly(self) -> None:
        """
        Given the dialog returns "/out/photo.png" with a PNG filter,
        When _get_file_path_info is called,
        Then returns ("/out/photo.png", "png").
        """
        # Arrange
        mock_window = MagicMock()

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/photo.png", "PNG (*.png)"),
        ):
            filepath, file_format = _get_file_path_info(mock_window, "PNG (*.png)")

        # Assert
        assert filepath == "/out/photo.png"
        assert file_format == "png"


class TestSaveCroppedImages:
    """
    Test Design Specification: _save_cropped_images()
    Module under test: src/ui/handlers/image_saving.py

    Contract:
        Iterates over a sequence of optional channel images, applies a crop
        rectangle to each non-None image, and saves each to a derived filepath
        with a channel-name suffix inserted before the extension.
        Returns a list of (success, message) tuples, one per saved image.
        None images are silently skipped (not included in results).

    Equivalence partitions:
        EP1  All images are None → returns empty list
        EP2  All images are valid → saves all and returns results for each
        EP3  Mixed None and valid images → skips None, saves valid

    Boundary values:
        BV1  Single-element list with one valid image
        BV2  Three-element list (full channel set)

    Exclusions:
        - Actual cv2.imwrite is mocked; disk writes not tested here.
        - crop_rect correctness is covered by TestApplyCrop.

    Constraints:
        - save_image is patched at import location in image_saving module.
    """

    def test_all_none_images_returns_empty_list(self) -> None:
        """
        Given a list of three None images,
        When _save_cropped_images is called,
        Then returns an empty list.
        """
        # Arrange
        images = [None, None, None]

        # Act
        results = _save_cropped_images(images, "/out/result.jpg", ["ir", "vis", "uv"], None, "jpg")

        # Assert
        assert results == []

    def test_valid_images_generate_one_result_each(self) -> None:
        """
        Given two valid images and one None,
        When _save_cropped_images is called,
        Then returns a list with two results (one per non-None image).
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        images = [img, None, img]

        # Act
        with patch("src.ui.handlers.image_saving.save_image", return_value=(True, "/out/result_ir.jpg")):
            results = _save_cropped_images(images, "/out/result.jpg", ["ir", "vis", "uv"], None, "jpg")

        # Assert
        assert len(results) == 2

    def test_channel_name_inserted_into_filepath(self) -> None:
        """
        Given images list with one valid image at index 0 (channel "ir"),
        When _save_cropped_images is called with filepath "/out/result.jpg",
        Then save_image is called with "/out/result_ir.jpg".
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        images = [img, None, None]

        # Act
        with patch("src.ui.handlers.image_saving.save_image", return_value=(True, "/out/result_ir.jpg")) as mock_save:
            _save_cropped_images(images, "/out/result.jpg", ["ir", "vis", "uv"], None, "jpg")

        # Assert
        mock_save.assert_called_once_with(img, "/out/result_ir.jpg", "jpg", is_bgr=True)

    def test_crop_applied_before_saving(self) -> None:
        """
        Given a valid image and a non-None crop_rect,
        When _save_cropped_images is called,
        Then save_image receives a cropped (smaller) image, not the original.
        """
        # Arrange
        img = np.zeros((100, 100), dtype=np.uint8)
        images = [img, None, None]
        crop_rect = (0, 0, 50, 50)
        saved_images = []

        def capture_save(image: np.ndarray, *args, **kwargs):
            """Capture saved images."""
            saved_images.append(image)
            return (True, args[0])

        # Act
        with patch("src.ui.handlers.image_saving.save_image", side_effect=capture_save):
            _save_cropped_images(images, "/out/result.jpg", ["ir", "vis", "uv"], crop_rect, "jpg")

        # Assert
        assert saved_images[0].shape == (50, 50)

    def test_all_three_channels_produce_three_results(self) -> None:
        """
        Given three valid images,
        When _save_cropped_images is called,
        Then returns a list with three results.
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        images = [img, img, img]

        # Act
        with patch("src.ui.handlers.image_saving.save_image", return_value=(True, "path")):
            results = _save_cropped_images(images, "/out/r.tif", ["ir", "vis", "uv"], None, "tif")

        # Assert
        assert len(results) == 3


class TestCreateCombinedImage:
    """
    Test Design Specification: _create_combined_image()
    Module under test: src/ui/handlers/image_saving.py

    Contract:
        Takes a sequence of up to three optional grayscale channel arrays and an
        optional crop rectangle. Creates a 3-channel BGR image by:
          - Substituting zero-filled arrays for missing (None) channels.
          - Applying the crop rectangle to each present channel if crop_rect is set.
          - Merging channels in BGR order (B=aligned[2], G=aligned[1], R=aligned[0]).
        Returns None if all channels are None.

    Equivalence partitions:
        EP1  All channels None → returns None
        EP2  All channels present, no crop → 3-channel image from all channels
        EP3  Some channels None → missing channels replaced by zeros
        EP4  All channels present, crop_rect set → channels are cropped

    Boundary values:
        BV1  Single non-None channel at index 0 → only R component non-zero
        BV2  crop_rect covering entire image → output same as uncropped

    Exclusions:
        - BGR merge order correctness is delegated to cv2.merge; only shape
          and dtype are verified here.

    Constraints:
        - cv2.merge is called internally; patched where needed to isolate logic.
    """

    def test_all_none_returns_none(self) -> None:
        """
        Given all channels are None,
        When _create_combined_image is called,
        Then returns None.
        """
        # Arrange
        images = [None, None, None]

        # Act
        result = _create_combined_image(images, None)

        # Assert
        assert result is None

    def test_all_valid_channels_returns_3channel_image(self) -> None:
        """
        Given three valid grayscale images,
        When _create_combined_image is called with no crop,
        Then returns a 3-channel image with the same spatial dimensions.
        """
        # Arrange
        img = np.zeros((10, 20), dtype=np.uint8)
        images = [img, img, img]

        # Act
        result = _create_combined_image(images, None)

        # Assert
        assert result is not None
        assert result.shape == (10, 20, 3)

    def test_missing_channel_replaced_with_zeros(self) -> None:
        """
        Given channels [img, None, None] where only index 0 is set,
        When _create_combined_image is called,
        Then the B and G channels of the result are all zeros.
        """
        # Arrange
        img = np.full((4, 4), 128, dtype=np.uint8)
        images = [img, None, None]

        # Act
        result = _create_combined_image(images, None)

        # Assert
        assert result is not None
        # cv2 merge order is [B, G, R] = [channels[2], channels[1], channels[0]]
        # channels[0]=img(128), channels[1]=zeros, channels[2]=zeros
        # result[:,:,0] = B = channels[2] = zeros
        np.testing.assert_array_equal(result[:, :, 0], np.zeros((4, 4), dtype=np.uint8))
        np.testing.assert_array_equal(result[:, :, 1], np.zeros((4, 4), dtype=np.uint8))

    def test_crop_rect_applied_to_channels(self) -> None:
        """
        Given three valid images and a crop_rect of (0, 0, 5, 5) on a 10x10 image,
        When _create_combined_image is called,
        Then the resulting image has shape (5, 5, 3).
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        images = [img, img, img]
        crop_rect = (0, 0, 5, 5)

        # Act
        result = _create_combined_image(images, crop_rect)

        # Assert
        assert result is not None
        assert result.shape == (5, 5, 3)

    def test_output_dtype_is_uint8(self) -> None:
        """
        Given valid uint8 grayscale channels,
        When _create_combined_image is called,
        Then the result dtype is uint8.
        """
        # Arrange
        img = np.zeros((8, 8), dtype=np.uint8)
        images = [img, img, img]

        # Act
        result = _create_combined_image(images, None)

        # Assert
        assert result is not None
        assert result.dtype == np.uint8

    def test_partial_channels_with_crop_raises_no_error(self) -> None:
        """
        Given channels [img, None, None] and a crop_rect,
        When _create_combined_image is called,
        Then a 3-channel image is returned without error (correct channels at cropped size).
        """
        # Arrange
        img = np.zeros((100, 100), dtype=np.uint8)
        images = [img, None, None]
        crop_rect = (0, 0, 50, 50)

        # Act
        result = _create_combined_image(images, crop_rect)

        # Assert
        assert result is not None
        assert result.shape == (50, 50, 3)


class TestSaveImageWithDialog:
    """
    Test Design Specification: save_image_with_dialog()
    Module under test: src/ui/handlers/image_saving.py

    Contract:
        Orchestrates the full save flow: checks for aligned channels, opens a file
        dialog, saves per-channel RGB images and a combined BGR image.
        Returns (False, "No images to save") if no channels are aligned.
        Returns (False, "Save operation cancelled") if dialog is cancelled.
        Returns (False, "No file extension …") if format cannot be determined.
        Returns (True, …) with count message when at least one image saved.
        Returns (False, "Failed to save any images") when all saves fail.

    Equivalence partitions:
        EP1  No aligned channels → (False, "No images to save")
        EP2  Dialog cancelled → (False, "Save operation cancelled")
        EP3  No file format from filepath/filter → (False, error message)
        EP4  All saves succeed → (True, "Successfully saved all …")
        EP5  Some saves fail → (True, "Saved N out of M …")
        EP6  All saves fail → (False, "Failed to save any images")

    Boundary values:
        BV1  crop_mode=True → crop_rect set to None (no crop applied)
        BV2  saved_crop_rect present and crop_mode=False → crop applied

    Exclusions:
        - Actual disk writes are mocked throughout.
        - viewer being None is handled by the implementation; covered in EP1/EP2.

    Constraints:
        - QFileDialog.getSaveFileName is patched at the import location.
        - save_image and _save_cropped_images are patched to avoid disk IO.
        - main_window is built with MagicMock with explicit attribute assignment.
    """

    def _make_window(
        self,
        has_aligned: bool = True,
        aligned_rgb: list = None,
        aligned: list = None,
        crop_mode: bool = False,
        saved_crop_rect=None,
    ) -> MagicMock:
        """Build a mock MainWindow for save_image_with_dialog tests."""
        window = MagicMock()
        window.svc.has_aligned_channels.return_value = has_aligned
        window.svc.aligned_rgb = aligned_rgb if aligned_rgb is not None else [None, None, None]
        window.svc.aligned = aligned if aligned is not None else [None, None, None]
        window.state.crop_mode = crop_mode
        if saved_crop_rect is None:
            window.viewer.get_saved_crop_rect.return_value = None
        else:
            window.viewer.get_saved_crop_rect.return_value = saved_crop_rect
        return window

    def test_no_aligned_channels_returns_error(self) -> None:
        """
        Given no aligned channels in the service,
        When save_image_with_dialog is called,
        Then returns (False, "No images to save").
        """
        # Arrange
        window = self._make_window(has_aligned=False)

        # Act
        success, message = save_image_with_dialog(window)

        # Assert
        assert success is False
        assert "No images to save" in message

    def test_cancelled_dialog_returns_error(self) -> None:
        """
        Given dialog returns empty filepath (user cancelled),
        When save_image_with_dialog is called,
        Then returns (False, "Save operation cancelled").
        """
        # Arrange
        window = self._make_window()

        # Act
        with patch("src.ui.handlers.image_saving.QFileDialog.getSaveFileName", return_value=("", "")):
            success, message = save_image_with_dialog(window)

        # Assert
        assert success is False
        assert "Save operation cancelled" in message

    def test_no_file_format_returns_error(self) -> None:
        """
        Given filepath with no extension and filter providing no extension,
        When save_image_with_dialog is called,
        Then returns (False, error message about missing extension).
        """
        # Arrange
        window = self._make_window()

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result", "All Files (*)"),
        ):
            success, message = save_image_with_dialog(window)

        # Assert
        assert success is False
        assert "No file extension" in message

    def test_all_saves_succeed_returns_success(self) -> None:
        """
        Given valid aligned channels and a successful dialog,
        When save_image_with_dialog is called and all saves succeed,
        Then returns (True, message containing "Successfully saved").
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        window = self._make_window(
            aligned_rgb=[img, img, img],
            aligned=[img, img, img],
        )

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result.jpg", "JPEG (*.jpg)"),
        ):
            with patch("src.ui.handlers.image_saving._save_cropped_images", return_value=[(True, "p1"), (True, "p2")]):
                with patch("src.ui.handlers.image_saving.save_image", return_value=(True, "/out/result.jpg")):
                    success, message = save_image_with_dialog(window)

        # Assert
        assert success is True
        assert "Successfully saved" in message

    def test_all_saves_fail_returns_error(self) -> None:
        """
        Given valid aligned channels but all save calls return failure,
        When save_image_with_dialog is called,
        Then returns (False, "Failed to save any images").
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        window = self._make_window(
            aligned_rgb=[img, img, img],
            aligned=[img, img, img],
        )

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result.jpg", "JPEG (*.jpg)"),
        ):
            with patch(
                "src.ui.handlers.image_saving._save_cropped_images",
                return_value=[(False, "err1"), (False, "err2")],
            ):
                with patch("src.ui.handlers.image_saving.save_image", return_value=(False, "err")):
                    success, message = save_image_with_dialog(window)

        # Assert
        assert success is False
        assert "Failed to save any images" in message

    def test_partial_save_success_returns_partial_message(self) -> None:
        """
        Given two channel saves succeed and the combined save fails,
        When save_image_with_dialog is called,
        Then returns (True, message indicating partial success).
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        window = self._make_window(
            aligned_rgb=[img, img, img],
            aligned=[img, img, img],
        )

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result.jpg", "JPEG (*.jpg)"),
        ):
            with patch(
                "src.ui.handlers.image_saving._save_cropped_images",
                return_value=[(True, "p1"), (True, "p2")],
            ):
                with patch("src.ui.handlers.image_saving.save_image", return_value=(False, "combined_err")):
                    success, message = save_image_with_dialog(window)

        # Assert
        assert success is True
        assert "out of" in message

    def test_crop_mode_true_disables_crop(self) -> None:
        """
        Given crop_mode=True on the window state,
        When save_image_with_dialog is called,
        Then _save_cropped_images receives crop_rect=None (no crop applied).
        """
        # Arrange
        img = np.zeros((10, 10), dtype=np.uint8)
        mock_rect = MagicMock()
        mock_rect.left.return_value = 5
        mock_rect.top.return_value = 5
        mock_rect.width.return_value = 20
        mock_rect.height.return_value = 20
        window = self._make_window(
            aligned_rgb=[img, None, None],
            aligned=[img, None, None],
            crop_mode=True,
            saved_crop_rect=mock_rect,
        )
        captured_crop: list = []

        def capture(*args, **kwargs):
            """Capture crop_rect argument."""
            captured_crop.append(args[3])
            return [(True, "p")]

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result.jpg", "JPEG (*.jpg)"),
        ):
            with patch("src.ui.handlers.image_saving._save_cropped_images", side_effect=capture):
                with patch("src.ui.handlers.image_saving._create_combined_image", return_value=None):
                    with patch("src.ui.handlers.image_saving.save_image", return_value=(True, "p")):
                        save_image_with_dialog(window)

        # Assert
        assert captured_crop[0] is None

    def test_saved_crop_rect_applied_when_crop_mode_false(self) -> None:
        """
        Given crop_mode=False and a non-None saved_crop_rect,
        When save_image_with_dialog is called,
        Then _save_cropped_images receives the crop tuple from saved_crop_rect.
        """
        # Arrange
        img = np.zeros((100, 100), dtype=np.uint8)
        mock_rect = MagicMock()
        mock_rect.left.return_value = 10
        mock_rect.top.return_value = 20
        mock_rect.width.return_value = 30
        mock_rect.height.return_value = 40
        window = self._make_window(
            aligned_rgb=[img, None, None],
            aligned=[img, None, None],
            crop_mode=False,
            saved_crop_rect=mock_rect,
        )
        captured_crop: list = []

        def capture(*args, **kwargs):
            """Capture crop_rect argument."""
            captured_crop.append(args[3])
            return [(True, "p")]

        # Act
        with patch(
            "src.ui.handlers.image_saving.QFileDialog.getSaveFileName",
            return_value=("/out/result.jpg", "JPEG (*.jpg)"),
        ):
            with patch("src.ui.handlers.image_saving._save_cropped_images", side_effect=capture):
                with patch("src.ui.handlers.image_saving._create_combined_image", return_value=None):
                    with patch("src.ui.handlers.image_saving.save_image", return_value=(True, "p")):
                        save_image_with_dialog(window)

        # Assert
        assert captured_crop[0] == (10, 20, 30, 40)

