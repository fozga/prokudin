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
Unit tests for src.ui.handlers.channels module.

Tests channel loading, adjustment, and display handlers.
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

from src.ui.handlers.channels import (
    _process_channel_image,
    load_channel,
    load_channel_from_path,
    adjust_channel,
    update_channel_preview,
    show_single_channel,
)


@pytest.fixture
def mock_main_window() -> MagicMock:
    """Create a mock MainWindow with required attributes."""
    main_window = MagicMock()
    main_window.svc = MagicMock()
    main_window.state = MagicMock()
    main_window.state.channel_paths = [None, None, None]
    main_window.state.show_combined = True
    main_window.state.current_channel = 0
    main_window.controllers = [MagicMock(), MagicMock(), MagicMock()]
    main_window.status_handler = MagicMock()
    main_window.status_handler.MEDIUM_TIMEOUT = "medium"
    main_window.status_handler.LONG_TIMEOUT = "long"
    main_window.status_handler.NO_TIMEOUT = "none"
    return main_window


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create a sample RGB image array for testing."""
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


class TestProcessChannelImage:
    """Tests for _process_channel_image internal function."""

    def test_calls_load_channel_from_array(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify _process_channel_image calls svc.load_channel_from_array()."""
        mock_main_window.svc.has_aligned_channels.return_value = False

        with patch("src.ui.handlers.channels.update_main_display"):
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        mock_main_window.svc.load_channel_from_array.assert_called_once_with(0, sample_rgb_image)

    def test_sets_status_message_on_load(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify status message is set after loading."""
        mock_main_window.svc.has_aligned_channels.return_value = False

        with patch("src.ui.handlers.channels.update_main_display"):
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        assert mock_main_window.status_handler.set_message.call_count >= 1
        call_args = mock_main_window.status_handler.set_message.call_args_list[0]
        assert "Red" in call_args[0][0]

    def test_updates_single_channel_preview(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify preview is updated for single channel when not all aligned."""
        mock_main_window.svc.has_aligned_channels.return_value = False
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))

        with patch("src.ui.handlers.channels.update_main_display"):
            with patch("src.ui.handlers.channels.update_channel_preview") as mock_update:
                _process_channel_image(mock_main_window, 1, sample_rgb_image)

        mock_update.assert_called_once_with(mock_main_window, 1)

    def test_updates_all_previews_when_aligned(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify all channel previews are updated when all channels are aligned."""
        mock_main_window.svc.has_aligned_channels.return_value = True
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))

        with patch("src.ui.handlers.channels.update_main_display"):
            with patch("src.ui.handlers.channels.update_channel_preview") as mock_update:
                _process_channel_image(mock_main_window, 2, sample_rgb_image)

        # update_channel_preview is called 6 times: 3 from adjust_channel + 3 directly in loop
        assert mock_update.call_count == 6

    def test_calls_adjust_channel_when_aligned(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify adjust_channel is called for all channels when aligned."""
        mock_main_window.svc.has_aligned_channels.return_value = True

        with patch("src.ui.handlers.channels.update_main_display"):
            with patch("src.ui.handlers.channels.adjust_channel") as mock_adjust:
                _process_channel_image(mock_main_window, 0, sample_rgb_image)

        assert mock_adjust.call_count == 3

    def test_updates_main_display(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify main display is updated."""
        mock_main_window.svc.has_aligned_channels.return_value = False

        with patch("src.ui.handlers.channels.update_main_display") as mock_display:
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        mock_display.assert_called_once_with(mock_main_window)

    def test_updates_save_button_state(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify save button state is updated."""
        mock_main_window.svc.has_aligned_channels.return_value = False

        with patch("src.ui.handlers.channels.update_main_display"):
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        mock_main_window.update_save_button_state.assert_called_once()


class TestLoadChannel:
    """Tests for load_channel function."""

    def test_successful_load(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify successful channel load stores path and processes image."""
        file_path = "/path/to/image.tif"
        mock_main_window.svc.has_aligned_channels.return_value = False

        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            with patch("src.ui.handlers.channels._process_channel_image") as mock_process:
                mock_load.return_value = (sample_rgb_image, file_path, None)
                load_channel(mock_main_window, 0)

        assert mock_main_window.state.channel_paths[0] == file_path
        mock_process.assert_called_once_with(mock_main_window, 0, sample_rgb_image)

    def test_load_channel_handles_no_file_selected(self, mock_main_window: MagicMock) -> None:
        """Verify load_channel handles file dialog cancellation without error message.

        When user cancels file dialog, load_raw_image returns (None, None, "No file selected").
        This is a special case - no error message should be shown to the user (cancellation
        is not an error). Production code explicitly checks for this string (line 66).
        """
        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            mock_load.return_value = (None, None, "No file selected")
            load_channel(mock_main_window, 0)

        assert mock_main_window.state.channel_paths[0] is None
        # Special case: "No file selected" does not trigger error message
        mock_main_window.status_handler.set_message.assert_not_called()

    def test_load_channel_shows_error_on_failure(self, mock_main_window: MagicMock) -> None:
        """Verify error message is shown when load fails with actual error.

        When file load fails (not cancellation), load_raw_image returns an error message.
        This message is displayed to inform the user of the problem.
        """
        err_msg = "Failed to decode RAW file"

        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            mock_load.return_value = (None, None, err_msg)
            load_channel(mock_main_window, 1)

        assert mock_main_window.state.channel_paths[1] is None
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert err_msg in call_args[0]

    def test_load_channel_all_channels(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify load_channel works for all three channels."""
        mock_main_window.svc.has_aligned_channels.return_value = False

        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            with patch("src.ui.handlers.channels._process_channel_image"):
                for channel_idx in range(3):
                    file_path = f"/path/channel_{channel_idx}.tif"
                    mock_load.return_value = (sample_rgb_image, file_path, None)
                    load_channel(mock_main_window, channel_idx)
                    assert mock_main_window.state.channel_paths[channel_idx] == file_path


class TestLoadChannelFromPath:
    """Tests for load_channel_from_path function."""

    def test_successful_load_from_path(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Verify successful load from path stores path and processes image."""
        file_path = "/path/to/image.tif"
        mock_main_window.svc.has_aligned_channels.return_value = False

        with patch("src.ui.handlers.channels.load_raw_image_from_path") as mock_load:
            with patch("src.ui.handlers.channels._process_channel_image") as mock_process:
                mock_load.return_value = (sample_rgb_image, None)
                load_channel_from_path(mock_main_window, 2, file_path)

        assert mock_main_window.state.channel_paths[2] == file_path
        mock_process.assert_called_once_with(mock_main_window, 2, sample_rgb_image)

    def test_load_from_path_handles_error(self, mock_main_window: MagicMock) -> None:
        """Verify error message is shown on load failure."""
        file_path = "/path/invalid.tif"
        err_msg = "File not found"

        with patch("src.ui.handlers.channels.load_raw_image_from_path") as mock_load:
            mock_load.return_value = (None, err_msg)
            load_channel_from_path(mock_main_window, 0, file_path)

        assert mock_main_window.state.channel_paths[0] is None
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "Red" in call_args[0]
        assert err_msg in call_args[0]


class TestAdjustChannel:
    """Tests for adjust_channel function."""

    def test_adjust_channel_reads_slider_values(self, mock_main_window: MagicMock) -> None:
        """Verify adjust_channel reads brightness and contrast from sliders."""
        mock_main_window.svc.aligned = [np.zeros((100, 100)), None, None]
        brightness_val = 25
        contrast_val = -15
        mock_main_window.controllers[0].sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=brightness_val)),
            "contrast": MagicMock(value=MagicMock(return_value=contrast_val)),
        }

        with patch("src.ui.handlers.channels.update_channel_preview"):
            with patch("src.ui.handlers.channels.update_main_display"):
                adjust_channel(mock_main_window, 0)

        mock_main_window.svc.adjust_channel.assert_called_once_with(0, brightness_val, contrast_val)

    def test_adjust_channel_skips_empty_channels(self, mock_main_window: MagicMock) -> None:
        """Verify adjust_channel skips channels that haven't been loaded."""
        mock_main_window.svc.aligned = [None, None, None]

        adjust_channel(mock_main_window, 0)

        mock_main_window.svc.adjust_channel.assert_not_called()

    def test_adjust_channel_updates_preview(self, mock_main_window: MagicMock) -> None:
        """Verify adjust_channel updates channel preview."""
        mock_main_window.svc.aligned = [np.zeros((100, 100)), None, None]
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))
        mock_main_window.controllers[0].sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=0)),
            "contrast": MagicMock(value=MagicMock(return_value=0)),
        }

        with patch("src.ui.handlers.channels.update_channel_preview") as mock_update:
            with patch("src.ui.handlers.channels.update_main_display"):
                adjust_channel(mock_main_window, 0)

        mock_update.assert_called_once()

    def test_adjust_channel_updates_display(self, mock_main_window: MagicMock) -> None:
        """Verify adjust_channel updates main display."""
        mock_main_window.svc.aligned = [np.zeros((100, 100)), None, None]
        mock_main_window.controllers[0].sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=0)),
            "contrast": MagicMock(value=MagicMock(return_value=0)),
        }

        with patch("src.ui.handlers.channels.update_channel_preview"):
            with patch("src.ui.handlers.channels.update_main_display") as mock_display:
                adjust_channel(mock_main_window, 0)

        mock_display.assert_called_once()

    def test_adjust_channel_all_channels(self, mock_main_window: MagicMock) -> None:
        """Verify adjust_channel works for all three channels."""
        for i in range(3):
            mock_main_window.svc.aligned[i] = np.zeros((100, 100))
            mock_main_window.controllers[i].sliders = {
                "brightness": MagicMock(value=MagicMock(return_value=0)),
                "contrast": MagicMock(value=MagicMock(return_value=0)),
            }

        with patch("src.ui.handlers.channels.update_channel_preview"):
            with patch("src.ui.handlers.channels.update_main_display"):
                for channel_idx in range(3):
                    adjust_channel(mock_main_window, channel_idx)

        assert mock_main_window.svc.adjust_channel.call_count == 3


class TestUpdateChannelPreview:
    """Tests for update_channel_preview function."""

    def test_update_channel_preview_fetches_and_sets(self, mock_main_window: MagicMock) -> None:
        """Verify preview is fetched from service and set on controller."""
        preview_image = np.zeros((100, 100))
        mock_main_window.svc.get_channel_preview.return_value = preview_image

        update_channel_preview(mock_main_window, 0)

        mock_main_window.svc.get_channel_preview.assert_called_once_with(0)
        assert mock_main_window.controllers[0].processed_image is preview_image
        mock_main_window.controllers[0].update_preview.assert_called_once()

    def test_update_preview_all_channels(self, mock_main_window: MagicMock) -> None:
        """Verify update_channel_preview works for all channels."""
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))

        for channel_idx in range(3):
            update_channel_preview(mock_main_window, channel_idx)

        assert mock_main_window.svc.get_channel_preview.call_count == 3


class TestShowSingleChannel:
    """Tests for show_single_channel function."""

    def test_show_single_channel_disables_combined(self, mock_main_window: MagicMock) -> None:
        """Verify show_single_channel sets show_combined to False."""
        mock_main_window.state.show_combined = True

        with patch("src.ui.handlers.channels.update_main_display"):
            show_single_channel(mock_main_window, 0)

        assert mock_main_window.state.show_combined is False

    def test_show_single_channel_sets_current_channel(self, mock_main_window: MagicMock) -> None:
        """Verify show_single_channel sets current_channel."""
        with patch("src.ui.handlers.channels.update_main_display"):
            for channel_idx in range(3):
                show_single_channel(mock_main_window, channel_idx)
                assert mock_main_window.state.current_channel == channel_idx

    def test_show_single_channel_updates_display(self, mock_main_window: MagicMock) -> None:
        """Verify show_single_channel updates main display."""
        with patch("src.ui.handlers.channels.update_main_display") as mock_display:
            show_single_channel(mock_main_window, 1)

        mock_display.assert_called_once_with(mock_main_window)

    def test_show_single_channel_all_channels(self, mock_main_window: MagicMock) -> None:
        """Verify show_single_channel works for all three channels."""
        with patch("src.ui.handlers.channels.update_main_display"):
            for channel_idx in range(3):
                show_single_channel(mock_main_window, channel_idx)
                assert mock_main_window.state.current_channel == channel_idx
