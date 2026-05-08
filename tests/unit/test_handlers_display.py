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

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Mock PyQt5 before importing Qt-dependent modules
sys.modules["PyQt5"] = MagicMock()
sys.modules["PyQt5.QtCore"] = MagicMock()
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()

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
    """Tests for update_main_display dispatcher function."""

    def test_dispatches_to_combined_when_show_combined_true(self, mock_main_window: MagicMock) -> None:
        """Verify update_main_display calls show_combined_image when show_combined is True."""
        mock_main_window.state.show_combined = True
        # Pixmap is already configured in fixture, but ensure it's correct
        mock_pixmap = MagicMock()
        mock_pixmap.width.return_value = 100
        mock_pixmap.height.return_value = 100
        mock_main_window.viewer.photo.pixmap.return_value = mock_pixmap

        with patch("src.ui.handlers.display.show_combined_image") as mock_combined:
            with patch("src.ui.handlers.display.show_single_channel_image"):
                update_main_display(mock_main_window)

        mock_combined.assert_called_once_with(mock_main_window)

    def test_dispatches_to_single_when_show_combined_false(self, mock_main_window: MagicMock) -> None:
        """Verify update_main_display calls show_single_channel_image when show_combined is False."""
        mock_main_window.state.show_combined = False
        # Pixmap is already configured in fixture, but ensure it's correct
        mock_pixmap = MagicMock()
        mock_pixmap.width.return_value = 100
        mock_pixmap.height.return_value = 100
        mock_main_window.viewer.photo.pixmap.return_value = mock_pixmap

        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image") as mock_single:
                update_main_display(mock_main_window)

        mock_single.assert_called_once_with(mock_main_window)

    def test_sets_scene_rect_when_pixmap_exists(self, mock_main_window: MagicMock) -> None:
        """Verify update_main_display sets scene rect when pixmap exists."""
        mock_pixmap = MagicMock()
        mock_pixmap.width.return_value = 200
        mock_pixmap.height.return_value = 150
        mock_main_window.viewer.photo.pixmap.return_value = mock_pixmap

        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image"):
                with patch("src.ui.handlers.display.QRectF") as mock_qrect:
                    update_main_display(mock_main_window)

        mock_qrect.assert_called_once_with(0, 0, 200, 150)
        mock_main_window.viewer.setSceneRect.assert_called_once()

    def test_handles_no_pixmap(self, mock_main_window: MagicMock) -> None:
        """Verify update_main_display handles None pixmap gracefully."""
        mock_main_window.viewer.photo.pixmap.return_value = None

        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image"):
                # Should not raise an error
                update_main_display(mock_main_window)

        # setSceneRect should not be called if pixmap is None
        mock_main_window.viewer.setSceneRect.assert_not_called()

    def test_handles_no_photo(self, mock_main_window: MagicMock) -> None:
        """Verify update_main_display handles None photo gracefully."""
        mock_main_window.viewer.photo = None

        with patch("src.ui.handlers.display.show_combined_image"):
            with patch("src.ui.handlers.display.show_single_channel_image"):
                # Should not raise an error
                update_main_display(mock_main_window)

        mock_main_window.viewer.setSceneRect.assert_not_called()


class TestQrectToTuple:
    """Tests for _qrect_to_tuple helper function."""

    def test_converts_qrect_to_tuple(self) -> None:
        """Verify _qrect_to_tuple converts QRect to (x, y, width, height)."""
        mock_qrect = MagicMock()
        mock_qrect.left.return_value = 10
        mock_qrect.top.return_value = 20
        mock_qrect.width.return_value = 100
        mock_qrect.height.return_value = 150

        result = _qrect_to_tuple(mock_qrect)

        assert result == (10, 20, 100, 150)

    def test_returns_none_for_none_qrect(self) -> None:
        """Verify _qrect_to_tuple returns None for None input."""
        result = _qrect_to_tuple(None)

        assert result is None

    def test_zero_coordinates(self) -> None:
        """Verify _qrect_to_tuple handles zero coordinates."""
        mock_qrect = MagicMock()
        mock_qrect.left.return_value = 0
        mock_qrect.top.return_value = 0
        mock_qrect.width.return_value = 50
        mock_qrect.height.return_value = 75

        result = _qrect_to_tuple(mock_qrect)

        assert result == (0, 0, 50, 75)


class TestShowCombinedImage:
    """Tests for show_combined_image function."""

    def test_calls_service_get_combined(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify show_combined_image calls svc.get_combined."""
        mock_main_window.svc.get_combined.return_value = sample_rgb_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        mock_main_window.svc.get_combined.assert_called_once()

    def test_passes_crop_tuple_to_service(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify show_combined_image passes crop tuple from saved rect."""
        mock_rect = MagicMock()
        mock_rect.left.return_value = 5
        mock_rect.top.return_value = 10
        mock_rect.width.return_value = 80
        mock_rect.height.return_value = 90
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = False
        mock_main_window.svc.get_combined.return_value = sample_rgb_image

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        call_args = mock_main_window.svc.get_combined.call_args
        assert call_args[1]["crop"] == (5, 10, 80, 90)

    def test_ignores_crop_when_crop_mode_true(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify show_combined_image ignores saved crop when crop_mode is True."""
        mock_rect = MagicMock()
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = True
        mock_main_window.svc.get_combined.return_value = sample_rgb_image

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        call_args = mock_main_window.svc.get_combined.call_args
        assert call_args[1]["crop"] is None

    def test_passes_intensity_values_to_service(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify show_combined_image passes intensity values from controllers."""
        mock_main_window.svc.get_combined.return_value = sample_rgb_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        for i, ctrl in enumerate(mock_main_window.controllers):
            ctrl.sliders["intensity"].value.return_value = 80 + i

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_combined_image(mock_main_window)

        call_args = mock_main_window.svc.get_combined.call_args
        assert call_args[1]["intensities"] == [80, 81, 82]

    def test_updates_viewer_with_pixmap(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify show_combined_image sets image on viewer."""
        mock_main_window.svc.get_combined.return_value = sample_rgb_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        with patch("src.ui.handlers.display.convert_to_qimage") as mock_convert:
            with patch("src.ui.handlers.display.QPixmap") as mock_pixmap_class:
                mock_convert.return_value = MagicMock()
                show_combined_image(mock_main_window)

        mock_main_window.viewer.set_image.assert_called_once()

    def test_handles_none_combined_image(self, mock_main_window: MagicMock) -> None:
        """Verify show_combined_image handles None return from service."""
        mock_main_window.svc.get_combined.return_value = None
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                # Should not raise an error
                show_combined_image(mock_main_window)

        mock_main_window.viewer.set_image.assert_not_called()


class TestShowSingleChannelImage:
    """Tests for show_single_channel_image function."""

    def test_calls_service_get_channel(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Verify show_single_channel_image calls svc.get_channel."""
        mock_main_window.state.current_channel = 1
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        mock_main_window.svc.get_channel.assert_called_once_with(1, crop=None)

    def test_uses_current_channel_index(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Verify show_single_channel_image uses state.current_channel."""
        for channel_idx in range(3):
            mock_main_window.state.current_channel = channel_idx
            mock_main_window.svc.get_channel.return_value = sample_grayscale_image
            mock_main_window.viewer.get_saved_crop_rect.return_value = None

            with patch("src.ui.handlers.display.convert_to_qimage"):
                with patch("src.ui.handlers.display.QPixmap"):
                    show_single_channel_image(mock_main_window)

            mock_main_window.svc.get_channel.assert_called_with(channel_idx, crop=None)

    def test_passes_crop_tuple_to_service(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Verify show_single_channel_image passes crop tuple from saved rect."""
        mock_rect = MagicMock()
        mock_rect.left.return_value = 15
        mock_rect.top.return_value = 25
        mock_rect.width.return_value = 70
        mock_rect.height.return_value = 85
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = False
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        call_args = mock_main_window.svc.get_channel.call_args
        assert call_args[1]["crop"] == (15, 25, 70, 85)

    def test_ignores_crop_when_crop_mode_true(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Verify show_single_channel_image ignores saved crop when crop_mode is True."""
        mock_rect = MagicMock()
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect
        mock_main_window.state.crop_mode = True
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        call_args = mock_main_window.svc.get_channel.call_args
        assert call_args[1]["crop"] is None

    def test_stacks_grayscale_to_rgb(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Verify show_single_channel_image stacks grayscale to RGB."""
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        with patch("src.ui.handlers.display.convert_to_qimage") as mock_convert:
            with patch("src.ui.handlers.display.QPixmap"):
                show_single_channel_image(mock_main_window)

        # Verify convert_to_qimage was called with stacked RGB image
        mock_convert.assert_called_once()
        rgb_image = mock_convert.call_args[0][0]
        assert rgb_image.shape == (100, 100, 3)
        # All channels should be the same (grayscale stacked)
        np.testing.assert_array_equal(rgb_image[:, :, 0], sample_grayscale_image)
        np.testing.assert_array_equal(rgb_image[:, :, 1], sample_grayscale_image)
        np.testing.assert_array_equal(rgb_image[:, :, 2], sample_grayscale_image)

    def test_updates_viewer_with_pixmap(self, mock_main_window: MagicMock, sample_grayscale_image: np.ndarray) -> None:
        """Verify show_single_channel_image sets image on viewer."""
        mock_main_window.svc.get_channel.return_value = sample_grayscale_image
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        with patch("src.ui.handlers.display.convert_to_qimage") as mock_convert:
            with patch("src.ui.handlers.display.QPixmap") as mock_pixmap_class:
                mock_convert.return_value = MagicMock()
                show_single_channel_image(mock_main_window)

        mock_main_window.viewer.set_image.assert_called_once()

    def test_handles_none_channel_image(self, mock_main_window: MagicMock) -> None:
        """Verify show_single_channel_image handles None return from service."""
        mock_main_window.svc.get_channel.return_value = None
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        with patch("src.ui.handlers.display.convert_to_qimage"):
            with patch("src.ui.handlers.display.QPixmap"):
                # Should not raise an error
                show_single_channel_image(mock_main_window)

        mock_main_window.viewer.set_image.assert_not_called()
