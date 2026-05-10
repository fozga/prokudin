"""Unit tests for src/ui/handlers/image_loading.py."""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Mock PyQt5 before importing Qt-dependent modules
sys.modules["PyQt5"] = MagicMock()
sys.modules["PyQt5.QtCore"] = MagicMock()
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()

# Create real exception classes for rawpy (these are what will be caught)
class LibRawFileUnsupportedError(Exception):
    """Mock rawpy.LibRawFileUnsupportedError."""

    pass


class LibRawIOError(Exception):
    """Mock rawpy.LibRawIOError."""

    pass


# Patch rawpy's exception classes before importing
import rawpy

rawpy.LibRawFileUnsupportedError = LibRawFileUnsupportedError
rawpy.LibRawIOError = LibRawIOError

from src.ui.handlers.image_loading import load_raw_image, load_raw_image_from_path


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """8-bit RGB image (100x100x3) for testing."""
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


class TestLoadRawImageFromPath:
    """
    Test Design Specification: load_raw_image_from_path()
    Module under test: src/ui/handlers/image_loading.py

    Contract:
        Loads a Sony ARW RAW image from a file path without opening a dialog.
        Calls rawpy.imread() with the provided path, postprocesses with camera white balance,
        and returns the result as an 8-bit RGB numpy array.
        On success, returns (rgb_array, None).
        On error (LibRawFileUnsupportedError, LibRawIOError, FileNotFoundError, PermissionError),
        returns (None, error_message_string).

    Equivalence partitions:
        EP1  Valid ARW file path → loads successfully, returns (ndarray, None)
        EP2  File does not exist → FileNotFoundError, returns (None, error_msg)
        EP3  Permission denied → PermissionError, returns (None, error_msg)
        EP4  Unsupported file format → LibRawFileUnsupportedError, returns (None, error_msg)
        EP5  File is corrupted → LibRawIOError, returns (None, error_msg)

    Boundary values:
        BV1  Minimum valid RGB image (1x1x3)
        BV2  Large RGB image (4000x3000x3) typical for RAW cameras

    Exclusions:
        - The rawpy postprocessing parameters (camera_wb, auto_bright, output_bps) are assumed correct;
          we test the interface, not the rawpy library itself.

    Constraints:
        - rawpy.imread is mocked; no real RAW files are read.
        - Tests verify that rawpy is called with correct arguments.
    """

    def test_successful_load_returns_array_and_none(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given a valid ARW file path,
        When load_raw_image_from_path is called,
        Then returns (numpy.ndarray, None) with RGB data.
        """
        # Arrange
        file_path = "/path/to/image.arw"
        mock_raw = MagicMock()
        mock_raw.postprocess.return_value = sample_rgb_image

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.return_value.__enter__.return_value = mock_raw
            result_array, result_error = load_raw_image_from_path(file_path)

        # Assert
        assert result_error is None
        np.testing.assert_array_equal(result_array, sample_rgb_image)
        mock_imread.assert_called_once_with(file_path)

    def test_postprocess_called_with_correct_parameters(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given a valid ARW file path,
        When load_raw_image_from_path is called,
        Then postprocess is called with use_camera_wb=True, no_auto_bright=True, output_bps=8.
        """
        # Arrange
        file_path = "/path/to/image.arw"
        mock_raw = MagicMock()
        mock_raw.postprocess.return_value = sample_rgb_image

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.return_value.__enter__.return_value = mock_raw
            load_raw_image_from_path(file_path)

        # Assert
        mock_raw.postprocess.assert_called_once_with(use_camera_wb=True, no_auto_bright=True, output_bps=8)

    def test_file_not_found_returns_none_and_error(self) -> None:
        """
        Given a file path that does not exist,
        When load_raw_image_from_path is called,
        Then returns (None, error_message_string) describing FileNotFoundError.
        """
        # Arrange
        file_path = "/nonexistent/file.arw"

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.side_effect = FileNotFoundError("File not found")
            result_array, result_error = load_raw_image_from_path(file_path)

        # Assert
        assert result_array is None
        assert result_error is not None
        assert "Error loading ARW file" in result_error

    def test_permission_denied_returns_none_and_error(self) -> None:
        """
        Given a file path without read permission,
        When load_raw_image_from_path is called,
        Then returns (None, error_message_string) describing PermissionError.
        """
        # Arrange
        file_path = "/restricted/file.arw"

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.side_effect = PermissionError("Permission denied")
            result_array, result_error = load_raw_image_from_path(file_path)

        # Assert
        assert result_array is None
        assert result_error is not None
        assert "Error loading ARW file" in result_error

    def test_unsupported_file_format_returns_none_and_error(self) -> None:
        """
        Given a file with unsupported format,
        When load_raw_image_from_path is called,
        Then returns (None, error_message_string) for LibRawFileUnsupportedError.
        """
        # Arrange
        file_path = "/path/to/image.jpg"

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.side_effect = LibRawFileUnsupportedError("Unsupported format")
            result_array, result_error = load_raw_image_from_path(file_path)

        # Assert
        assert result_array is None
        assert result_error is not None
        assert "Error loading ARW file" in result_error

    def test_corrupted_file_returns_none_and_error(self) -> None:
        """
        Given a corrupted RAW file,
        When load_raw_image_from_path is called,
        Then returns (None, error_message_string) for LibRawIOError.
        """
        # Arrange
        file_path = "/path/to/corrupted.arw"

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.side_effect = LibRawIOError("Corrupted file")
            result_array, result_error = load_raw_image_from_path(file_path)

        # Assert
        assert result_array is None
        assert result_error is not None
        assert "Error loading ARW file" in result_error

    def test_minimum_valid_image_size(self) -> None:
        """
        Given a valid ARW file returning a 1x1x3 RGB image,
        When load_raw_image_from_path is called,
        Then returns (array, None) with correct shape and dtype.
        """
        # Arrange
        file_path = "/path/to/tiny.arw"
        tiny_image = np.ones((1, 1, 3), dtype=np.uint8)
        mock_raw = MagicMock()
        mock_raw.postprocess.return_value = tiny_image

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.return_value.__enter__.return_value = mock_raw
            result_array, result_error = load_raw_image_from_path(file_path)

        # Assert
        assert result_error is None
        assert result_array.shape == (1, 1, 3)
        assert result_array.dtype == np.uint8

    def test_large_image_size(self) -> None:
        """
        Given a valid ARW file returning a large RGB image (4000x3000x3),
        When load_raw_image_from_path is called,
        Then returns (array, None) with correct shape and dtype.
        """
        # Arrange
        file_path = "/path/to/large.arw"
        large_image = np.ones((4000, 3000, 3), dtype=np.uint8)
        mock_raw = MagicMock()
        mock_raw.postprocess.return_value = large_image

        # Act
        with patch("src.ui.handlers.image_loading.rawpy.imread") as mock_imread:
            mock_imread.return_value.__enter__.return_value = mock_raw
            result_array, result_error = load_raw_image_from_path(file_path)

        # Assert
        assert result_error is None
        assert result_array.shape == (4000, 3000, 3)
        assert result_array.dtype == np.uint8


class TestLoadRawImage:
    """
    Test Design Specification: load_raw_image()
    Module under test: src/ui/handlers/image_loading.py

    Contract:
        Opens a PyQt5 file dialog for the user to select a Sony ARW RAW image file.
        If a file is selected, loads it via load_raw_image_from_path() and returns (array, path, None).
        If the dialog is cancelled, returns (None, None, "No file selected").
        If loading fails, returns (None, None, error_message).
        The parent widget is used for the dialog's parent context.

    Equivalence partitions:
        EP1  Valid file selected and loads successfully → (array, path, None)
        EP2  User cancels file dialog → (None, None, "No file selected")
        EP3  Valid file selected but loading fails → (None, None, error_msg)

    Boundary values:
        BV1  Empty filename string (same as cancelled) → (None, None, ...)
        BV2  Path with special characters → handled correctly

    Exclusions:
        - The actual QFileDialog behavior is mocked; we test logic flow only.
        - Filesystem and rawpy behavior delegated to load_raw_image_from_path.

    Constraints:
        - QFileDialog is mocked via sys.modules["PyQt5.QtWidgets"].
        - Tests mock QFileDialog.getOpenFileName return values.
    """

    def test_successful_file_selection_and_load(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given the user selects a valid ARW file in the dialog,
        When load_raw_image is called,
        Then returns (numpy.ndarray, path, None) with RGB data and file path.
        """
        # Arrange
        file_path = "/path/to/image.arw"
        parent = MagicMock()

        # Act
        with patch("src.ui.handlers.image_loading.QFileDialog.getOpenFileName") as mock_dialog:
            with patch("src.ui.handlers.image_loading.load_raw_image_from_path") as mock_load:
                mock_dialog.return_value = (file_path, "")
                mock_load.return_value = (sample_rgb_image, None)
                result_array, result_path, result_error = load_raw_image(parent)

        # Assert
        assert result_error is None
        np.testing.assert_array_equal(result_array, sample_rgb_image)
        assert result_path == file_path

    def test_dialog_opens_with_arw_filter(self) -> None:
        """
        Given load_raw_image is called,
        When the QFileDialog is opened,
        Then the filter is set to "Sony RAW Files (*.arw)".
        """
        # Arrange
        parent = MagicMock()

        # Act
        with patch("src.ui.handlers.image_loading.QFileDialog.getOpenFileName") as mock_dialog:
            with patch("src.ui.handlers.image_loading.load_raw_image_from_path"):
                mock_dialog.return_value = (None, "")
                load_raw_image(parent)

        # Assert
        mock_dialog.assert_called_once()
        call_args = mock_dialog.call_args
        assert call_args[0][0] is parent
        assert call_args[0][3] == "Sony RAW Files (*.arw)"

    def test_user_cancels_dialog_returns_none_messages(self) -> None:
        """
        Given the user cancels the file dialog (selects no file),
        When load_raw_image is called,
        Then returns (None, None, "No file selected").
        """
        # Arrange
        parent = MagicMock()

        # Act
        with patch("src.ui.handlers.image_loading.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("", "")
            result_array, result_path, result_error = load_raw_image(parent)

        # Assert
        assert result_array is None
        assert result_path is None
        assert result_error == "No file selected"

    def test_empty_filename_treated_as_cancelled(self) -> None:
        """
        Given the file dialog returns an empty filename string,
        When load_raw_image is called,
        Then returns (None, None, "No file selected").
        """
        # Arrange
        parent = MagicMock()

        # Act
        with patch("src.ui.handlers.image_loading.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("", "")
            result_array, result_path, result_error = load_raw_image(parent)

        # Assert
        assert result_array is None
        assert result_path is None
        assert result_error == "No file selected"

    def test_file_selected_but_loading_fails(self) -> None:
        """
        Given the user selects a file but loading fails,
        When load_raw_image is called,
        Then returns (None, None, error_message) from load_raw_image_from_path.
        """
        # Arrange
        file_path = "/path/to/corrupted.arw"
        error_msg = "Error loading ARW file: corrupted"
        parent = MagicMock()

        # Act
        with patch("src.ui.handlers.image_loading.QFileDialog.getOpenFileName") as mock_dialog:
            with patch("src.ui.handlers.image_loading.load_raw_image_from_path") as mock_load:
                mock_dialog.return_value = (file_path, "")
                mock_load.return_value = (None, error_msg)
                result_array, result_path, result_error = load_raw_image(parent)

        # Assert
        assert result_array is None
        assert result_path is None
        assert result_error == error_msg

    def test_path_with_special_characters(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given a file path containing special characters or spaces,
        When load_raw_image is called,
        Then the path is passed to load_raw_image_from_path and returned correctly.
        """
        # Arrange
        file_path = "/path/with spaces/and-dashes/image_2025.arw"
        parent = MagicMock()

        # Act
        with patch("src.ui.handlers.image_loading.QFileDialog.getOpenFileName") as mock_dialog:
            with patch("src.ui.handlers.image_loading.load_raw_image_from_path") as mock_load:
                mock_dialog.return_value = (file_path, "")
                mock_load.return_value = (sample_rgb_image, None)
                result_array, result_path, result_error = load_raw_image(parent)

        # Assert
        assert result_path == file_path
        mock_load.assert_called_once_with(file_path)

    def test_delegates_to_load_raw_image_from_path(self, sample_rgb_image: np.ndarray) -> None:
        """
        Given a file is selected,
        When load_raw_image is called,
        Then load_raw_image_from_path is called with the selected file path.
        """
        # Arrange
        file_path = "/path/to/image.arw"
        parent = MagicMock()

        # Act
        with patch("src.ui.handlers.image_loading.QFileDialog.getOpenFileName") as mock_dialog:
            with patch("src.ui.handlers.image_loading.load_raw_image_from_path") as mock_load:
                mock_dialog.return_value = (file_path, "")
                mock_load.return_value = (sample_rgb_image, None)
                load_raw_image(parent)

        # Assert
        mock_load.assert_called_once_with(file_path)
