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

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.core.align import AlignmentResult, TransformParams
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
    main_window.svc.last_alignment_result = AlignmentResult(
        aligned_grayscale=[np.zeros((4, 4), dtype=np.uint8)] * 3,
        aligned_rgb=[np.zeros((4, 4, 3), dtype=np.uint8)] * 3,
        method_used="ORB",
        channel_params=[TransformParams() for _ in range(3)],
    )
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
    """
    Test Design Specification: _process_channel_image()
    Module under test: src/ui/handlers/channels.py

    Contract:
        Internal handler that loads an RGB image into the service, manages alignment,
        updates channel preview(s), and refreshes the UI. Takes MainWindow reference,
        channel index (0-2 for R/G/B), and numpy RGB array. Returns None.
        Side effects: loads image via svc.load_channel_from_array(), may trigger
        adjust_channel() for all channels if aligned, always updates previews and
        main display, updates save button state.

    Equivalence partitions:
        EP1  All channels aligned     → adjust_channel called 3x, all previews updated
        EP2  Not all channels aligned → adjust_channel not called, only target preview updated
        EP3  Channel index 0 (Red)    → correct channel preview fetched
        EP4  Channel index 1 (Green)  → correct channel preview fetched
        EP5  Channel index 2 (Blue)   → correct channel preview fetched

    Boundary values:
        BV1  channel_idx = 0 (Red channel boundary)
        BV2  channel_idx = 2 (Blue channel boundary)
        BV3  has_aligned_channels returns True (triggers multi-channel update)
        BV4  has_aligned_channels returns False (skips multi-channel update)

    Exclusions:
        - Image validation (assumes valid numpy array from caller)
        - Service error handling (assumes svc methods succeed)
        - Actual preview image generation (mocked in tests)

    Constraints:
        - Requires mocking: svc.load_channel_from_array(), svc.has_aligned_channels(),
          svc.get_channel_preview(), adjust_channel(), update_channel_preview(),
          update_main_display(), main_window.update_save_button_state()
        - MainWindow fixture must have status_handler with timeout constants
        - PyQt5 mocked in sys.modules
    """

    def test_calls_load_channel_from_array(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: an RGB image and MainWindow with has_aligned_channels=False
        When: _process_channel_image is called
        Then: svc.load_channel_from_array is called with channel index and image."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = False

        # Act
        with patch("src.ui.handlers.channels.update_main_display"):
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        # Assert
        mock_main_window.svc.load_channel_from_array.assert_called_once_with(0, sample_rgb_image)

    def test_sets_status_message_on_load(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: _process_channel_image is called with channel 0 (Red)
        When: the channel is processed
        Then: a status message containing 'Red' is set."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = False

        # Act
        with patch("src.ui.handlers.channels.update_main_display"):
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        # Assert
        assert mock_main_window.status_handler.set_message.call_count >= 1
        call_args = mock_main_window.status_handler.set_message.call_args_list[0]
        assert "Red" in call_args[0][0]

    def test_updates_single_channel_preview(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: has_aligned_channels returns False (not all channels loaded)
        When: _process_channel_image is called for channel 1
        Then: update_channel_preview is called once for that channel only."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = False
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))

        # Act
        with patch("src.ui.handlers.channels.update_main_display"):
            with patch("src.ui.handlers.channels.update_channel_preview") as mock_update:
                _process_channel_image(mock_main_window, 1, sample_rgb_image)

        # Assert
        mock_update.assert_called_once_with(mock_main_window, 1)

    def test_updates_all_previews_when_aligned(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: has_aligned_channels returns True (all channels loaded)
        When: _process_channel_image is called for channel 2
        Then: update_channel_preview is called 6 times (3 from adjust + 3 direct)."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = True
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))

        # Act
        with patch("src.ui.handlers.channels.update_main_display"):
            with patch("src.ui.handlers.channels.update_channel_preview") as mock_update:
                _process_channel_image(mock_main_window, 2, sample_rgb_image)

        # Assert
        assert mock_update.call_count == 6

    def test_calls_adjust_channel_when_aligned(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: has_aligned_channels returns True
        When: _process_channel_image is called
        Then: adjust_channel is called for all three channels."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = True

        # Act
        with patch("src.ui.handlers.channels.update_main_display"):
            with patch("src.ui.handlers.channels.adjust_channel") as mock_adjust:
                _process_channel_image(mock_main_window, 0, sample_rgb_image)

        # Assert
        assert mock_adjust.call_count == 3

    def test_updates_main_display(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: _process_channel_image is called with valid image
        When: processing completes
        Then: update_main_display is called once."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = False

        # Act
        with patch("src.ui.handlers.channels.update_main_display") as mock_display:
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        # Assert
        mock_display.assert_called_once_with(mock_main_window)

    def test_updates_save_button_state(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: _process_channel_image is called with valid image
        When: processing completes
        Then: update_save_button_state is called once."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = False

        # Act
        with patch("src.ui.handlers.channels.update_main_display"):
            _process_channel_image(mock_main_window, 0, sample_rgb_image)

        # Assert
        mock_main_window.update_save_button_state.assert_called_once()


class TestLoadChannel:
    """
    Test Design Specification: load_channel()
    Module under test: src/ui/handlers/channels.py

    Contract:
        Public handler that opens file dialog (via load_raw_image), loads a channel
        image from selected file, and processes it. Takes MainWindow and channel
        index (0-2). Returns None. Sets channel_paths[idx] on success, shows error
        message on failure (unless user cancels, special case). Always calls
        _process_channel_image on successful load.

    Equivalence partitions:
        EP1  Successful load       → channel_paths set, _process_channel_image called
        EP2  User cancels dialog   → "No file selected" error, no message shown, paths unchanged
        EP3  Load fails (error)    → error message shown, paths unchanged, process not called
        EP4  Channel index 0 (Red) → correct channel path stored
        EP5  Channel index 1 (Green) → correct channel path stored
        EP6  Channel index 2 (Blue) → correct channel path stored

    Boundary values:
        BV1  channel_idx = 0 (first channel)
        BV2  channel_idx = 2 (last channel)
        BV3  err_msg = "No file selected" (special case: no user notification)
        BV4  err_msg = other error (displays message to user)

    Exclusions:
        - File dialog implementation (mocked load_raw_image)
        - Actual file I/O (mocked)
        - Image format validation (delegate to load_raw_image)

    Constraints:
        - Requires mocking: load_raw_image(), _process_channel_image()
        - MainWindow.state.channel_paths must be mutable list with 3 slots
        - status_handler.set_message() called for non-special errors
    """

    def test_successful_load(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: load_raw_image returns (image, path, None)
        When: load_channel is called for channel 0
        Then: channel_paths[0] is set and _process_channel_image is called."""
        # Arrange
        file_path = "/path/to/image.tif"
        mock_main_window.svc.has_aligned_channels.return_value = False

        # Act
        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            with patch("src.ui.handlers.channels._process_channel_image") as mock_process:
                mock_load.return_value = (sample_rgb_image, file_path, None)
                load_channel(mock_main_window, 0)

        # Assert
        assert mock_main_window.state.channel_paths[0] == file_path
        mock_process.assert_called_once_with(mock_main_window, 0, sample_rgb_image)

    def test_load_channel_handles_no_file_selected(self, mock_main_window: MagicMock) -> None:
        """Given: load_raw_image returns error "No file selected"
        When: load_channel is called
        Then: no error message is shown (special case for cancellation)."""
        # Arrange
        # Act
        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            mock_load.return_value = (None, None, "No file selected")
            load_channel(mock_main_window, 0)

        # Assert
        assert mock_main_window.state.channel_paths[0] is None
        mock_main_window.status_handler.set_message.assert_not_called()

    def test_load_channel_shows_error_on_failure(self, mock_main_window: MagicMock) -> None:
        """Given: load_raw_image returns actual error message
        When: load_channel is called for channel 1
        Then: error message is shown and channel_paths[1] remains None."""
        # Arrange
        err_msg = "Failed to decode RAW file"

        # Act
        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            mock_load.return_value = (None, None, err_msg)
            load_channel(mock_main_window, 1)

        # Assert
        assert mock_main_window.state.channel_paths[1] is None
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert err_msg in call_args[0]

    def test_load_channel_all_channels(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: load_channel is called for each of channels 0, 1, 2
        When: all channels are loaded successfully
        Then: all channel_paths are set correctly."""
        # Arrange
        mock_main_window.svc.has_aligned_channels.return_value = False

        # Act & Assert
        with patch("src.ui.handlers.channels.load_raw_image") as mock_load:
            with patch("src.ui.handlers.channels._process_channel_image"):
                for channel_idx in range(3):
                    file_path = f"/path/channel_{channel_idx}.tif"
                    mock_load.return_value = (sample_rgb_image, file_path, None)
                    load_channel(mock_main_window, channel_idx)
                    assert mock_main_window.state.channel_paths[channel_idx] == file_path


class TestLoadChannelFromPath:
    """
    Test Design Specification: load_channel_from_path()
    Module under test: src/ui/handlers/channels.py

    Contract:
        Handler for loading a channel from a preset file path (used for session
        restore) without dialog. Takes MainWindow, channel index (0-2), and
        file_path string. Returns None. Sets channel_paths[idx] on success,
        shows formatted error message on failure.

    Equivalence partitions:
        EP1  File exists, readable  → channel_paths set, _process_channel_image called
        EP2  File not found         → error message shown with channel name, paths unchanged
        EP3  Channel index 0 (Red)  → "Red channel" in error message
        EP4  Channel index 1 (Green) → "Green channel" in error message
        EP5  Channel index 2 (Blue)  → "Blue channel" in error message

    Boundary values:
        BV1  channel_idx = 0 (first channel)
        BV2  channel_idx = 2 (last channel)

    Exclusions:
        - File dialog (not used)
        - Actual file I/O (mocked load_raw_image_from_path)
        - Path validation (assumes caller provides valid path)

    Constraints:
        - Requires mocking: load_raw_image_from_path(), _process_channel_image()
        - Error messages include channel name and error details
        - MainWindow.status_handler.set_message() called on error
    """

    def test_successful_load_from_path(self, mock_main_window: MagicMock, sample_rgb_image: np.ndarray) -> None:
        """Given: load_raw_image_from_path returns (image, None)
        When: load_channel_from_path is called for channel 2
        Then: channel_paths[2] is set and _process_channel_image is called."""
        # Arrange
        file_path = "/path/to/image.tif"
        mock_main_window.svc.has_aligned_channels.return_value = False

        # Act
        with patch("src.ui.handlers.channels.load_raw_image_from_path") as mock_load:
            with patch("src.ui.handlers.channels._process_channel_image") as mock_process:
                mock_load.return_value = (sample_rgb_image, None)
                load_channel_from_path(mock_main_window, 2, file_path)

        # Assert
        assert mock_main_window.state.channel_paths[2] == file_path
        mock_process.assert_called_once_with(mock_main_window, 2, sample_rgb_image)

    def test_load_from_path_handles_error(self, mock_main_window: MagicMock) -> None:
        """Given: load_raw_image_from_path returns (None, error_msg)
        When: load_channel_from_path is called for channel 0
        Then: error message contains 'Red' and error details."""
        # Arrange
        file_path = "/path/invalid.tif"
        err_msg = "File not found"

        # Act
        with patch("src.ui.handlers.channels.load_raw_image_from_path") as mock_load:
            mock_load.return_value = (None, err_msg)
            load_channel_from_path(mock_main_window, 0, file_path)

        # Assert
        assert mock_main_window.state.channel_paths[0] is None
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "Red" in call_args[0]
        assert err_msg in call_args[0]


class TestAdjustChannel:
    """
    Test Design Specification: adjust_channel()
    Module under test: src/ui/handlers/channels.py

    Contract:
        Reads brightness and contrast slider values from controller, applies
        adjustments via service, updates preview and main display. Takes MainWindow
        and channel index (0-2). Returns None. Skips processing if channel not loaded
        (aligned[idx] is None).

    Equivalence partitions:
        EP1  Channel loaded         → svc.adjust_channel called with slider values
        EP2  Channel not loaded     → svc.adjust_channel not called
        EP3  Channel 0 (Red)        → reads controller[0] sliders
        EP4  Channel 1 (Green)      → reads controller[1] sliders
        EP5  Channel 2 (Blue)       → reads controller[2] sliders
        EP6  All channels loaded    → adjust works independently for each

    Boundary values:
        BV1  channel_idx = 0 (first channel)
        BV2  channel_idx = 2 (last channel)
        BV3  brightness = 0 (neutral)
        BV4  contrast = 0 (neutral)
        BV5  brightness != 0 (affects output)
        BV6  contrast != 0 (affects output)

    Exclusions:
        - Slider range validation (service handles clamping)
        - Preview image validation
        - Display rendering (mocked update_main_display)

    Constraints:
        - Requires mocking: update_channel_preview(), update_main_display()
        - MainWindow.svc.aligned must be list/array with 3 elements
        - Controllers must have sliders dict with "brightness" and "contrast" keys
        - Status message shown during processing
    """

    def test_adjust_channel_reads_slider_values(self, mock_main_window: MagicMock) -> None:
        """Given: channel 0 loaded with sliders brightness=25, contrast=-15
        When: adjust_channel is called for channel 0
        Then: svc.adjust_channel is called with those slider values."""
        # Arrange
        mock_main_window.svc.aligned = [np.zeros((100, 100)), None, None]
        brightness_val = 25
        contrast_val = -15
        mock_main_window.controllers[0].sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=brightness_val)),
            "contrast": MagicMock(value=MagicMock(return_value=contrast_val)),
        }

        # Act
        with patch("src.ui.handlers.channels.update_channel_preview"):
            with patch("src.ui.handlers.channels.update_main_display"):
                adjust_channel(mock_main_window, 0)

        # Assert
        mock_main_window.svc.adjust_channel.assert_called_once_with(0, brightness_val, contrast_val)

    def test_adjust_channel_skips_empty_channels(self, mock_main_window: MagicMock) -> None:
        """Given: all channels are None (not loaded)
        When: adjust_channel is called
        Then: svc.adjust_channel is not called."""
        mock_main_window.svc.aligned = [None, None, None]

        adjust_channel(mock_main_window, 0)

        mock_main_window.svc.adjust_channel.assert_not_called()

    def test_adjust_channel_updates_preview(self, mock_main_window: MagicMock) -> None:
        """Given: channel 0 is loaded with valid sliders
        When: adjust_channel is called
        Then: update_channel_preview is called once."""
        # Arrange
        mock_main_window.svc.aligned = [np.zeros((100, 100)), None, None]
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))
        mock_main_window.controllers[0].sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=0)),
            "contrast": MagicMock(value=MagicMock(return_value=0)),
        }

        # Act
        with patch("src.ui.handlers.channels.update_channel_preview") as mock_update:
            with patch("src.ui.handlers.channels.update_main_display"):
                adjust_channel(mock_main_window, 0)

        # Assert
        mock_update.assert_called_once()

    def test_adjust_channel_updates_display(self, mock_main_window: MagicMock) -> None:
        """Given: channel 0 is loaded with valid sliders
        When: adjust_channel is called
        Then: update_main_display is called once."""
        # Arrange
        mock_main_window.svc.aligned = [np.zeros((100, 100)), None, None]
        mock_main_window.controllers[0].sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=0)),
            "contrast": MagicMock(value=MagicMock(return_value=0)),
        }

        # Act
        with patch("src.ui.handlers.channels.update_channel_preview"):
            with patch("src.ui.handlers.channels.update_main_display") as mock_display:
                adjust_channel(mock_main_window, 0)

        # Assert
        mock_display.assert_called_once()

    def test_adjust_channel_all_channels(self, mock_main_window: MagicMock) -> None:
        """Given: all three channels are loaded with valid sliders
        When: adjust_channel is called for each channel
        Then: svc.adjust_channel is called three times total."""
        # Arrange
        for i in range(3):
            mock_main_window.svc.aligned[i] = np.zeros((100, 100))
            mock_main_window.controllers[i].sliders = {
                "brightness": MagicMock(value=MagicMock(return_value=0)),
                "contrast": MagicMock(value=MagicMock(return_value=0)),
            }

        # Act
        with patch("src.ui.handlers.channels.update_channel_preview"):
            with patch("src.ui.handlers.channels.update_main_display"):
                for channel_idx in range(3):
                    adjust_channel(mock_main_window, channel_idx)

        # Assert
        assert mock_main_window.svc.adjust_channel.call_count == 3


class TestUpdateChannelPreview:
    """
    Test Design Specification: update_channel_preview()
    Module under test: src/ui/handlers/channels.py

    Contract:
        Fetches processed preview image for a channel from service and sets it on
        the corresponding controller. Takes MainWindow and channel index (0-2).
        Returns None. Calls svc.get_channel_preview() and controller.update_preview().

    Equivalence partitions:
        EP1  Channel 0 (Red)    → fetches preview for index 0, sets on controller[0]
        EP2  Channel 1 (Green)  → fetches preview for index 1, sets on controller[1]
        EP3  Channel 2 (Blue)   → fetches preview for index 2, sets on controller[2]

    Boundary values:
        BV1  channel_idx = 0 (first channel)
        BV2  channel_idx = 2 (last channel)

    Exclusions:
        - Preview image validation
        - Controller UI updates (mocked)
        - Service preview generation logic

    Constraints:
        - Requires mocking: svc.get_channel_preview() returns numpy array
        - MainWindow.controllers must be indexable with 3 items
        - Each controller must have processed_image attribute and update_preview() method
    """

    def test_update_channel_preview_fetches_and_sets(self, mock_main_window: MagicMock) -> None:
        """Given: svc.get_channel_preview returns a preview image
        When: update_channel_preview is called for channel 0
        Then: preview is set on controller[0] and update_preview is called."""
        # Arrange
        preview_image = np.zeros((100, 100))
        mock_main_window.svc.get_channel_preview.return_value = preview_image

        # Act
        update_channel_preview(mock_main_window, 0)

        # Assert
        mock_main_window.svc.get_channel_preview.assert_called_once_with(0)
        assert mock_main_window.controllers[0].processed_image is preview_image
        mock_main_window.controllers[0].update_preview.assert_called_once()

    def test_update_preview_all_channels(self, mock_main_window: MagicMock) -> None:
        """Given: update_channel_preview is called for each channel 0, 1, 2
        When: all channels are updated
        Then: svc.get_channel_preview is called three times."""
        # Arrange
        mock_main_window.svc.get_channel_preview.return_value = np.zeros((100, 100))

        # Act
        for channel_idx in range(3):
            update_channel_preview(mock_main_window, channel_idx)

        # Assert
        assert mock_main_window.svc.get_channel_preview.call_count == 3


class TestShowSingleChannel:
    """
    Test Design Specification: show_single_channel()
    Module under test: src/ui/handlers/channels.py

    Contract:
        Sets application state to display a single channel in the main viewer.
        Takes MainWindow and channel index (0-2). Returns None. Sets
        show_combined=False and current_channel=idx, then updates display.

    Equivalence partitions:
        EP1  Channel 0 (Red)    → show_combined False, current_channel = 0
        EP2  Channel 1 (Green)  → show_combined False, current_channel = 1
        EP3  Channel 2 (Blue)   → show_combined False, current_channel = 2
        EP4  Switch from combined → show_combined True -> False
        EP5  Switch between channels → current_channel changes

    Boundary values:
        BV1  channel_idx = 0 (first channel)
        BV2  channel_idx = 2 (last channel)

    Exclusions:
        - Display rendering (mocked update_main_display)
        - state validation
        - Channel data availability (assumes channel exists)

    Constraints:
        - Requires mocking: update_main_display()
        - MainWindow.state must have mutable show_combined and current_channel attributes
    """

    def test_show_single_channel_disables_combined(self, mock_main_window: MagicMock) -> None:
        """Given: state.show_combined is True
        When: show_single_channel is called
        Then: state.show_combined is set to False."""
        # Arrange
        mock_main_window.state.show_combined = True

        # Act
        with patch("src.ui.handlers.channels.update_main_display"):
            show_single_channel(mock_main_window, 0)

        # Assert
        assert mock_main_window.state.show_combined is False

    def test_show_single_channel_sets_current_channel(self, mock_main_window: MagicMock) -> None:
        """Given: show_single_channel is called for channels 0, 1, 2
        When: each channel is activated
        Then: state.current_channel is set to the correct index."""
        # Arrange & Act
        with patch("src.ui.handlers.channels.update_main_display"):
            for channel_idx in range(3):
                show_single_channel(mock_main_window, channel_idx)
                # Assert
                assert mock_main_window.state.current_channel == channel_idx

    def test_show_single_channel_updates_display(self, mock_main_window: MagicMock) -> None:
        """Given: show_single_channel is called for channel 1
        When: display is updated
        Then: update_main_display is called once."""
        # Arrange & Act
        with patch("src.ui.handlers.channels.update_main_display") as mock_display:
            show_single_channel(mock_main_window, 1)

        # Assert
        mock_display.assert_called_once_with(mock_main_window)

    def test_show_single_channel_all_channels(self, mock_main_window: MagicMock) -> None:
        """Given: show_single_channel is called for channels 0, 1, 2 sequentially
        When: each channel is activated
        Then: state.current_channel reflects the correct channel index."""
        # Arrange & Act
        with patch("src.ui.handlers.channels.update_main_display"):
            for channel_idx in range(3):
                show_single_channel(mock_main_window, channel_idx)
                # Assert
                assert mock_main_window.state.current_channel == channel_idx
