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

"""Widget tests for src/ui/qt_utils.py."""

import numpy as np
import pytest
from PyQt5.QtGui import QImage
from pytestqt.plugin import QtBot

from src.ui.qt_utils import convert_to_qimage


@pytest.mark.widget
class TestConvertToQimage:
    """
    Test Design Specification: convert_to_qimage
    Module under test: src/ui/qt_utils.py

    Widget base class: N/A — utility function; QApplication required to construct QImage.

    Contract:
        convert_to_qimage converts a numpy ndarray (grayscale 2-D or RGB 3-D,
        dtype uint8) into a PyQt5 QImage for display in Qt widgets. Returns an
        empty (null) QImage when input is None. 2-D arrays produce
        Format_Grayscale8; 3-D arrays produce Format_RGB888. Image data is
        referenced in-place (not copied).

    Infrastructure:
        - Requires qtbot fixture (provides QApplication via pytest-qt).
        - Requires QT_QPA_PLATFORM=offscreen.
        - No file IO or external services.

    What is tested:
        - None input returns a null QImage.
        - 2-D grayscale uint8 arrays produce QImage.Format_Grayscale8.
        - 3-D RGB uint8 arrays produce QImage.Format_RGB888.
        - Returned QImage dimensions match the input array shape.
        - Minimum valid array sizes (1×1, 1×1×3) do not raise.
        - Boundary pixel values (0 and 255) produce a valid, non-null QImage.

    What is NOT tested:
        - QPainter rendering or on-screen visual output.
        - Non-uint8 dtypes (outside the documented contract).
        - Arrays with more than 3 dimensions.

    Equivalence partitions:
        EP1  None input                    → empty QImage (isNull() == True)
        EP2  Valid 2-D grayscale uint8     → QImage.Format_Grayscale8
        EP3  Valid 3-D RGB uint8           → QImage.Format_RGB888
        EP4  Boundary pixel values (0/255) → valid, non-null QImage

    Boundary values:
        BV1  1×1 grayscale array   (minimum valid 2-D size)
        BV2  1×1×3 RGB array       (minimum valid 3-D size)
        BV3  pixel value = 0       (uint8 minimum)
        BV4  pixel value = 255     (uint8 maximum)

    Mocking strategy:
        No external dependencies require mocking.

    Constraints:
        QApplication must be running; satisfied by the qtbot fixture from pytest-qt.
    """

    def test_none_input_returns_null_qimage(self, qtbot: QtBot) -> None:
        """
        Given convert_to_qimage is called with None,
        When the function executes,
        Then an empty (null) QImage is returned.
        """
        # Act
        result = convert_to_qimage(None)
        # Assert
        assert result.isNull()

    @pytest.mark.parametrize(
        "shape,expected_width,expected_height",
        [
            ((120, 160), 160, 120),  # 2-D grayscale
            ((120, 160, 3), 160, 120),  # 3-D RGB
        ],
        ids=["grayscale", "rgb"],
    )
    def test_array_returns_correct_dimensions(self, qtbot: QtBot, shape: tuple, expected_width: int, expected_height: int) -> None:
        """
        Given a uint8 array of specified shape (2-D grayscale or 3-D RGB),
        When convert_to_qimage is called,
        Then the returned QImage has the correct width and height.
        """
        # Arrange
        image = np.zeros(shape, dtype=np.uint8)
        # Act
        result = convert_to_qimage(image)
        # Assert
        assert result.width() == expected_width
        assert result.height() == expected_height

    def test_grayscale_array_returns_grayscale8_format(self, qtbot: QtBot) -> None:
        """
        Given a 2-D grayscale uint8 array,
        When convert_to_qimage is called,
        Then the returned QImage has format Format_Grayscale8.
        """
        # Arrange
        image = np.zeros((10, 10), dtype=np.uint8)
        # Act
        result = convert_to_qimage(image)
        # Assert
        assert result.format() == QImage.Format_Grayscale8

    def test_rgb_array_returns_rgb888_format(self, qtbot: QtBot) -> None:
        """
        Given a 3-D RGB uint8 array,
        When convert_to_qimage is called,
        Then the returned QImage has format Format_RGB888.
        """
        # Arrange
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        # Act
        result = convert_to_qimage(image)
        # Assert
        assert result.format() == QImage.Format_RGB888

    def test_minimum_size_grayscale_array_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given a 2-D grayscale array of shape (1, 1) (minimum valid size),
        When convert_to_qimage is called,
        Then a valid non-null QImage is returned without raising.
        """
        # Arrange
        image = np.array([[128]], dtype=np.uint8)  # BV1
        # Act
        result = convert_to_qimage(image)
        # Assert
        assert not result.isNull()

    def test_minimum_size_rgb_array_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given a 3-D RGB array of shape (1, 1, 3) (minimum valid size),
        When convert_to_qimage is called,
        Then a valid non-null QImage is returned without raising.
        """
        # Arrange
        image = np.array([[[255, 0, 0]]], dtype=np.uint8)  # BV2
        # Act
        result = convert_to_qimage(image)
        # Assert
        assert not result.isNull()

    @pytest.mark.parametrize(
        "pixel_value",
        [
            0,    # BV3: uint8 minimum
            255,  # BV4: uint8 maximum
        ],
        ids=["min_pixel", "max_pixel"],
    )
    def test_boundary_pixel_values_produce_valid_qimage(self, qtbot: QtBot, pixel_value: int) -> None:
        """
        Given a grayscale array filled with a boundary pixel value (0 or 255),
        When convert_to_qimage is called,
        Then a valid non-null QImage is returned with correct pixel data.
        """
        # Arrange
        image = np.full((10, 10), pixel_value, dtype=np.uint8)  # EP4
        # Act
        result = convert_to_qimage(image)
        # Assert
        assert not result.isNull()
        # Verify pixel data is not corrupted (e.g., clamped to [1,254])
        bits = result.bits()
        bits.setsize(result.byteCount())
        pixel_data = np.array(bits, dtype=np.uint8).reshape((10, 10))
        assert np.all(pixel_data == pixel_value)

    def test_non_contiguous_array_slice(self, qtbot: QtBot) -> None:
        """
        Given a non-contiguous grayscale array created from a slice,
        When convert_to_qimage is called,
        Then a valid QImage is returned (not corrupted or out-of-bounds).
        """
        # Arrange: create non-contiguous array via slicing
        full_array = np.zeros((20, 20), dtype=np.uint8)
        full_array[::2, ::2] = 128  # every other row and column
        sliced = full_array[::2, ::2]  # non-contiguous slice
        assert not sliced.flags['C_CONTIGUOUS']  # verify it's non-contiguous
        # Act
        result = convert_to_qimage(sliced)
        # Assert: result should handle non-contiguous input gracefully
        assert not result.isNull()
        assert result.width() == sliced.shape[1]
        assert result.height() == sliced.shape[0]

    def test_non_contiguous_array_transpose(self, qtbot: QtBot) -> None:
        """
        Given a non-contiguous grayscale array created via transpose,
        When convert_to_qimage is called,
        Then a valid QImage is returned (not corrupted or out-of-bounds).
        """
        # Arrange: create non-contiguous array via transpose
        original = np.arange(120, dtype=np.uint8).reshape((10, 12))
        transposed = original.T  # non-contiguous transpose
        assert not transposed.flags['C_CONTIGUOUS']  # verify it's non-contiguous
        # Act
        result = convert_to_qimage(transposed)
        # Assert: result should handle non-contiguous input gracefully
        assert not result.isNull()
        assert result.width() == transposed.shape[1]
        assert result.height() == transposed.shape[0]

    def test_non_contiguous_array_fortran_order(self, qtbot: QtBot) -> None:
        """
        Given a non-contiguous grayscale array in Fortran (column-major) order,
        When convert_to_qimage is called,
        Then a valid QImage is returned (not corrupted or out-of-bounds).
        """
        # Arrange: create Fortran-order (non-contiguous) array
        array = np.asfortranarray(np.zeros((10, 10), dtype=np.uint8))
        assert not array.flags['C_CONTIGUOUS']  # verify it's non-contiguous
        assert array.flags['F_CONTIGUOUS']  # but it is F-contiguous
        # Act
        result = convert_to_qimage(array)
        # Assert: result should handle F-contiguous input gracefully
        assert not result.isNull()
        assert result.width() == array.shape[1]
        assert result.height() == array.shape[0]
