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

"""
Unit tests for src.ui.handlers.display module.

Tests display update and image rendering handlers.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.ui.handlers.display import (
    update_main_display,
    show_combined_image,
    show_single_channel_image,
    _qrect_to_tuple,
)


@pytest.fixture
def mock_main_window() -> MagicMock:
    """Create a mock MainWindow with required attributes."""
    main_window = MagicMock()
    main_window.state = MagicMock()
    main_window.state.show_combined = True
    main_window.state.current_channel = 0
    main_window.state.crop_mode = False
    main_window.svc = MagicMock()
    main_window.viewer = MagicMock()
    main_window.viewer.photo = MagicMock()
    # Mock pixmap to have width() and height() as callable methods
    mock_pixmap = MagicMock()
    mock_pixmap.width.return_value = 100
    mock_pixmap.height.return_value = 100
    main_window.viewer.photo.pixmap.return_value = mock_pixmap
    main_window.controllers = [MagicMock(), MagicMock(), MagicMock()]
    for i, ctrl in enumerate(main_window.controllers):
        ctrl.sliders = {"intensity": MagicMock(value=MagicMock(return_value=100))}
    return main_window


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create a sample RGB image array."""
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_grayscale_image() -> np.ndarray:
    """Create a sample grayscale image array."""
    return np.random.randint(0, 256, (100, 100), dtype=np.uint8)


class TestUpdateMainDisplay:
    """
    Test Design Specification: update_main_display()
    Module under test: src/ui/handlers/display.py

    Contract:
        Dispatcher that routes display updates based on show_combined flag.
        If show_combined=True, calls show_combined_image; else calls
        show_single_channel_image. Always updates scene rect if pixmap exists
        and is truthy. Returns None.

    Equivalence partitions:
        EP1  show_combined=True   → dispatches to show_combined_image
        EP2  show_combined=False  → dispatches to show_single_channel_image
        EP3  Pixmap exists, truthy → scene rect set to pixmap dimensions
        EP4  Pixmap is None       → scene rect not set
        EP5  Pixmap exists, falsy → scene rect not set

    Boundary values:
        BV1  pixmap.width() = 0 (degenerate rect)
        BV2  pixmap.height() = 0 (degenerate rect)
        BV3  pixmap None (edge case)
        BV4  photo is None (edge case)
        BV5  pixmap is falsy but non-None (null QPixmap)

    Exclusions:
        - Combined image generation (delegated to show_combined_image)
        - Single channel image generation (delegated to show_single_channel_image)
        - QRectF/QPixmap creation specifics

    Constraints:
        - Requires mocking: show_combined_image(), show_single_channel_image(), QRectF
        - Accesses main_window.state.show_combined
        - Accesses main_window.viewer.photo.pixmap()
        - Calls main_window.viewer.setSceneRect()
    """

    def test_dispatches_to_combined_when_show_combined_true(self, mock_main_window: MagicMock) -> None:
        """Given show_combined is True, when update_main_display is called, then show_combined_image is called."""
        # Arrange
        mock_main_window.state.show_combined = True

        # Act
        with patch("src.ui.handlers.display.show_combined_image") as mock_combined:
            with patch("src.ui.handlers.display.show_single_channel_image"):
                update_main_display(mock_main_window)

        # Assert
        mock_combined.assert_called_once_with(mock_main_window)

    def test_dispatches_to_single_when_show_combined_false(self, mock_main_window: MagicMock) -> None:
        """Given show_combined is False, when update_main_display is called, then show_single_channel_image is called."""
        # Arrange
        mock_main_window.state.show_combined = False

        # Act
        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image") as mock_single:
                update_main_display(mock_main_window)

        # Assert
        mock_single.assert_called_once_with(mock_main_window)

    def test_sets_scene_rect_when_pixmap_exists(self, mock_main_window: MagicMock) -> None:
        """Given a valid pixmap exists, when update_main_display is called, then scene rect is set."""
        # Arrange
        mock_pixmap = MagicMock()
        mock_pixmap.width.return_value = 200
        mock_pixmap.height.return_value = 150
        mock_main_window.viewer.photo.pixmap.return_value = mock_pixmap

        # Act
        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image"):
                with patch("src.ui.handlers.display.QRectF") as mock_qrect:
                    update_main_display(mock_main_window)

        # Assert
        mock_qrect.assert_called_once_with(0, 0, 200, 150)
        mock_main_window.viewer.setSceneRect.assert_called_once()

    def test_handles_no_pixmap(self, mock_main_window: MagicMock) -> None:
        """Given pixmap is None, when update_main_display is called, then no error is raised and scene rect is not set."""
        # Arrange
        mock_main_window.viewer.photo.pixmap.return_value = None

        # Act
        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image"):
                update_main_display(mock_main_window)

        # Assert
        mock_main_window.viewer.setSceneRect.assert_not_called()

    def test_handles_falsy_pixmap(self, mock_main_window: MagicMock) -> None:
        """Given a falsy (non-None) pixmap, when update_main_display is called, then scene rect is not set."""
        # Arrange
        falsy_pixmap = MagicMock()
        falsy_pixmap.__bool__.return_value = False
        mock_main_window.viewer.photo.pixmap.return_value = falsy_pixmap

        # Act
        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image"):
                update_main_display(mock_main_window)

        # Assert
        mock_main_window.viewer.setSceneRect.assert_not_called()

    def test_handles_no_photo(self, mock_main_window: MagicMock) -> None:
        """Given photo is None, when update_main_display is called, then scene rect is not set."""
        # Arrange
        mock_main_window.viewer.photo = None

        # Act
        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image"):
                update_main_display(mock_main_window)

        # Assert
        mock_main_window.viewer.setSceneRect.assert_not_called()


class TestQrectToTuple:
    """
    Test Design Specification: _qrect_to_tuple()
    Module under test: src/ui/handlers/display.py

    Contract:
        Utility converter that extracts coordinates and dimensions from QRect-like
        object. Takes optional QRect and returns tuple (x, y, width, height) or
        None. Formula: result = (qrect.left(), qrect.top(), qrect.width(), qrect.height())

    Equivalence partitions:
        EP1  Valid QRect with positive coords → returns (left, top, width, height)
        EP2  QRect at origin (0, 0)         → returns (0, 0, width, height)
        EP3  Input is None                   → returns None

    Boundary values:
        BV1  left = 0 (minimum coordinate)
        BV2  top = 0 (minimum coordinate)
        BV3  width = 50 (arbitrary positive)
        BV4  height = 75 (arbitrary positive)

    Exclusions:
        - Negative coordinates (not expected from QRect)
        - QRect validation
        - Real QRect objects (uses mock interface)

    Constraints:
        - Input must have left(), top(), width(), height() methods or None
        - Works with MagicMock QRect objects
    """

    def test_converts_qrect_to_tuple(self) -> None:
        """Given a QRect with coordinates, when _qrect_to_tuple is called, then tuple (x, y, width, height) is returned."""
        mock_qrect = MagicMock()
        mock_qrect.left.return_value = 10
        mock_qrect.top.return_value = 20
        mock_qrect.width.return_value = 100
        mock_qrect.height.return_value = 150

        result = _qrect_to_tuple(mock_qrect)

        assert result == (10, 20, 100, 150)

    def test_returns_none_for_none_qrect(self) -> None:
        """Given input is None, when _qrect_to_tuple is called, then None is returned."""
        result = _qrect_to_tuple(None)

        assert result is None

    def test_zero_coordinates(self) -> None:
        """Given a QRect with zero coordinates, when _qrect_to_tuple is called, then tuple (0, 0, width, height) is returned."""
        mock_qrect = MagicMock()
        mock_qrect.left.return_value = 0
        mock_qrect.top.return_value = 0
        mock_qrect.width.return_value = 50
        mock_qrect.height.return_value = 75

        result = _qrect_to_tuple(mock_qrect)

        assert result == (0, 0, 50, 75)


class TestShowCombinedImage:
    """
    Test Design Specification: show_combined_image()
    Module under test: src/ui/handlers/display.py

    Contract:
        Displays combined RGB image in main viewer. Retrieves combined image from
        service with optional crop region and intensity values from sliders.
        Takes MainWindow reference. Returns None. Converts image to QPixmap and
        sets on viewer if result is not None.

    Equivalence partitions:
        EP1  crop_mode=False, saved crop exists → passes crop tuple to service
        EP2  crop_mode=True, saved crop exists  → passes crop=None to service
        EP3  crop_mode=False, no saved crop    → passes crop=None to service
        EP4  Combined image returned            → converted to QPixmap, set on viewer
        EP5  Service returns None               → viewer.set_image not called

    Boundary values:
        BV1  crop=(0, 0, width, height) (full rect)
        BV2  crop=(5, 10, 80, 90) (partial rect)
        BV3  intensities=[100, 100, 100] (neutral)
        BV4  intensities=[80, 81, 82] (varied values)

    Exclusions:
        - Crop rect validation
        - QPixmap rendering
        - Intensity value clamping (service responsibility)
        - Combined image generation algorithm (service responsibility)

    Constraints:
        - Requires mocking: convert_to_qimage(), QPixmap, svc.get_combined()
        - MainWindow.controllers[0-2] must have sliders["intensity"].value()
        - MainWindow.viewer.get_saved_crop_rect() returns QRect or None
        - MainWindow.state.crop_mode boolean flag
    """

    def test_calls_service_get_combined(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given a MainWindow, when show_combined_image is called, then svc.get_combined is called."""
        # Arrange
        mock_main_window.svc.get_combined.return_value = sample_rgb_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        # Assert
        mock_main_window.svc.get_combined.assert_called_once()

    def test_passes_crop_tuple_to_service(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given crop_mode is False and saved crop rect exists, when show_combined_image is called, then crop tuple is passed to service."""
        # Arrange
        mock_rect = MagicMock()
        mock_rect.left.return_value = 5
        mock_rect.top.return_value = 10
        mock_rect.width.return_value = 80
        mock_rect.height.return_value = 90
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = False
        mock_main_window.svc.get_combined.return_value = sample_rgb_image

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        # Assert
        call_args = mock_main_window.svc.get_combined.call_args
        assert call_args[1]["crop"] == (5, 10, 80, 90)

    def test_ignores_crop_when_crop_mode_true(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given crop_mode is True and saved crop rect exists, when show_combined_image is called, then crop is ignored."""
        # Arrange
        mock_rect = MagicMock()
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = True
        mock_main_window.svc.get_combined.return_value = sample_rgb_image

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        # Assert
        call_args = mock_main_window.svc.get_combined.call_args
        assert call_args[1]["crop"] is None

    def test_passes_intensity_values_to_service(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given controller sliders with intensity values, when show_combined_image is called, then intensities are passed to service."""
        # Arrange
        mock_main_window.svc.get_combined.return_value = sample_rgb_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        for i, ctrl in enumerate(mock_main_window.controllers):
            ctrl.sliders["intensity"].value.return_value = 80 + i

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        # Assert
        call_args = mock_main_window.svc.get_combined.call_args
        assert call_args[1]["intensities"] == [80, 81, 82]

    def test_updates_viewer_with_pixmap(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given a combined image from service, when show_combined_image is called, then image is set on viewer."""
        # Arrange
        mock_main_window.svc.get_combined.return_value = sample_rgb_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage") as mock_convert:
            with patch("src.ui.handlers.display.QPixmap") as mock_pixmap_class:
                mock_convert.return_value = MagicMock()
                show_combined_image(mock_main_window)

        # Assert
        mock_main_window.viewer.set_image.assert_called_once()

    def test_handles_none_combined_image(self, mock_main_window: MagicMock) -> None:
        """Given service returns None, when show_combined_image is called, then no error is raised and viewer is not updated."""
        # Arrange
        mock_main_window.svc.get_combined.return_value = None
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        # Assert
        mock_main_window.viewer.set_image.assert_not_called()


class TestShowSingleChannelImage:
    """
    Test Design Specification: show_single_channel_image()
    Module under test: src/ui/handlers/display.py

    Contract:
        Displays single grayscale channel in main viewer as RGB. Retrieves channel
        image from service with optional crop, stacks grayscale to RGB (replicate
        across 3 channels), converts to QPixmap, and sets on viewer. Takes
        MainWindow. Returns None.

    Equivalence partitions:
        EP1  crop_mode=False, saved crop exists → passes crop tuple to service
        EP2  crop_mode=True, saved crop exists  → passes crop=None to service
        EP3  crop_mode=False, no saved crop    → passes crop=None to service
        EP4  Channel image returned             → stacked to RGB, set on viewer
        EP5  Service returns None               → viewer.set_image not called
        EP6  current_channel=0 (Red)           → service called with idx=0
        EP7  current_channel=1 (Green)         → service called with idx=1
        EP8  current_channel=2 (Blue)          → service called with idx=2

    Boundary values:
        BV1  channel_idx = 0 (first)
        BV2  channel_idx = 2 (last)
        BV3  crop=(15, 25, 70, 85) (arbitrary rect)
        BV4  grayscale shape=(100, 100) → stacked to (100, 100, 3)

    Exclusions:
        - Crop rect validation
        - QPixmap rendering
        - Grayscale channel extraction (service responsibility)

    Constraints:
        - Requires mocking: convert_to_qimage(), QPixmap, svc.get_channel()
        - MainWindow.state.current_channel selects which channel
        - MainWindow.viewer.get_saved_crop_rect() returns QRect or None
        - MainWindow.state.crop_mode boolean flag
        - Grayscale image stacked to RGB via np.stack([img] * 3, axis=-1)
    """

    def test_calls_service_get_channel(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Given a MainWindow, when show_single_channel_image is called, then svc.get_channel is called."""
        # Arrange
        mock_main_window.state.current_channel = 1
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        # Assert
        mock_main_window.svc.get_channel.assert_called_once_with(1, crop=None)

    def test_uses_current_channel_index(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Given varying current_channel values, when show_single_channel_image is called, then correct channel index is used."""
        # Arrange
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act & Assert
        for channel_idx in range(3):
            mock_main_window.state.current_channel = channel_idx

            with patch("src.ui.handlers.display.convert_to_qimage"):
                with patch("src.ui.handlers.display.QPixmap"):
                    show_single_channel_image(mock_main_window)

            mock_main_window.svc.get_channel.assert_called_with(channel_idx, crop=None)

    def test_passes_crop_tuple_to_service(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Given crop_mode is False and saved crop rect exists, when show_single_channel_image is called, then crop tuple is passed to service."""
        # Arrange
        mock_rect = MagicMock()
        mock_rect.left.return_value = 15
        mock_rect.top.return_value = 25
        mock_rect.width.return_value = 70
        mock_rect.height.return_value = 85
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = False
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        # Assert
        call_args = mock_main_window.svc.get_channel.call_args
        assert call_args[1]["crop"] == (15, 25, 70, 85)

    def test_ignores_crop_when_crop_mode_true(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Given crop_mode is True and saved crop rect exists, when show_single_channel_image is called, then crop is ignored."""
        # Arrange
        mock_rect = MagicMock()
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = True
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        # Assert
        call_args = mock_main_window.svc.get_channel.call_args
        assert call_args[1]["crop"] is None

    def test_stacks_grayscale_to_rgb(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Given a grayscale image from service, when show_single_channel_image is called, then image is stacked to RGB."""
        # Arrange
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage") as mock_convert:
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        # Assert
        mock_convert.assert_called_once()
        rgb_image = mock_convert.call_args[0][0]
        assert rgb_image.shape == (100, 100, 3)
        np.testing.assert_array_equal(rgb_image[:, :, 0], sample_grayscale_image)
        np.testing.assert_array_equal(rgb_image[:, :, 1], sample_grayscale_image)
        np.testing.assert_array_equal(rgb_image[:, :, 2], sample_grayscale_image)

    def test_updates_viewer_with_pixmap(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Given a channel image from service, when show_single_channel_image is called, then image is set on viewer."""
        # Arrange
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage") as mock_convert:
            with patch("src.ui.handlers.display.QPixmap") as mock_pixmap_class:
                mock_convert.return_value = MagicMock()
                show_single_channel_image(mock_main_window)

        # Assert
        mock_main_window.viewer.set_image.assert_called_once()

    def test_handles_none_channel_image(self, mock_main_window: MagicMock) -> None:
        """Given service returns None, when show_single_channel_image is called, then no error is raised and viewer is not updated."""
        # Arrange
        mock_main_window.svc.get_channel.return_value = None
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        # Assert
        mock_main_window.viewer.set_image.assert_not_called()
