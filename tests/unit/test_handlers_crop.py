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
Unit tests for src.ui.handlers.crop module.

Tests crop mode toggling, cancellation, aspect ratio setting, and crop application.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.ui.handlers.crop import _get_aspect_crop_rect, apply_crop, cancel_crop, set_crop_ratio, toggle_crop_mode


@pytest.fixture
def mock_main_window() -> MagicMock:
    """Create a mock MainWindow with required attributes for crop handlers."""
    main_window = MagicMock()
    main_window.state = MagicMock()
    main_window.state.crop_mode = False
    main_window.state.crop_ratio = None
    main_window.state.crop_rect = None
    main_window.state.show_combined = True
    main_window.svc = MagicMock()
    main_window.svc.has_processed_channels.return_value = True
    main_window.svc.get_image_dimensions.return_value = (600, 800)  # (height, width)
    main_window.viewer = MagicMock()
    main_window.viewer.get_saved_crop_rect.return_value = None
    # Create a mock rect that behaves like a real QRect for method calls
    def create_mock_rect(x: int = 100, y: int = 100, w: int = 200, h: int = 200) -> MagicMock:
        """Create a mock QRect with proper width/height/isValid behavior."""
        rect = MagicMock()
        rect.width.return_value = w
        rect.height.return_value = h
        rect.isValid.return_value = True
        rect.x.return_value = x
        rect.y.return_value = y
        return rect

    mock_rect = create_mock_rect()
    main_window.viewer.get_crop_rect.return_value = mock_rect
    main_window.crop_mode_btn = MagicMock()
    main_window.crop_controls = MagicMock()
    main_window.controllers = [MagicMock(), MagicMock(), MagicMock()]
    main_window.status_handler = MagicMock()
    main_window.status_handler.NO_TIMEOUT = "none"
    main_window.status_handler.MEDIUM_TIMEOUT = "medium"
    main_window.update_save_button_state = MagicMock()
    main_window._update_mode_from_state = MagicMock()
    return main_window


@patch("src.ui.handlers.crop.update_main_display")
class TestToggleCropMode:
    """
    Test Design Specification: toggle_crop_mode()
    Module under test: src/ui/handlers/crop.py

    Contract:
        Toggles crop mode on if not already active. Returns early if already active
        or if no processed channels. Initializes crop rect from saved state or image
        dimensions (80% of image). Updates UI visibility and viewer state. Updates
        main display and mode indicator.

    Equivalence partitions:
        EP1  Already in crop mode     → returns early, no changes
        EP2  No processed channels    → returns early, no changes
        EP3  Enter crop mode, no saved rect, has dimensions → initializes from image
        EP4  Enter crop mode, with saved crop rect → uses saved rect
        EP5  With crop ratio set during initialization → applies ratio to default rect

    Boundary values:
        BV1  Image dimensions very small (50x50) → 80% = 40x40
        BV2  Image dimensions large (4000x3000) → 80% = 3200x2400

    Exclusions:
        - Pixel-perfect geometry testing (geometry changes based on image aspect)
        - Animation or visual feedback timing

    Constraints:
        - Requires mocking ImageViewer, AppState, ImageProcessorService
        - Requires mocking update_main_display
        - MainWindow._update_mode_from_state must exist
    """

    def test_returns_early_if_already_in_crop_mode(self, mock_update_main_display: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given main_window is already in crop mode,
        When toggle_crop_mode is called,
        Then the function returns early without changes.
        """
        # Arrange
        mock_main_window.state.crop_mode = True
        # Act
        toggle_crop_mode(mock_main_window)
        # Assert
        mock_update_main_display.assert_not_called()
        mock_main_window.crop_mode_btn.setVisible.assert_not_called()

    def test_returns_early_if_no_processed_channels(self, mock_update_main_display: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given main_window.svc has no processed channels,
        When toggle_crop_mode is called,
        Then the function returns early without changes.
        """
        # Arrange
        mock_main_window.state.crop_mode = False
        mock_main_window.svc.has_processed_channels.return_value = False
        # Act
        toggle_crop_mode(mock_main_window)
        # Assert
        mock_update_main_display.assert_not_called()
        mock_main_window.crop_mode_btn.setVisible.assert_not_called()

    def test_enters_crop_mode_with_default_rect(self, mock_update_main_display: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given no saved crop rect and image dimensions 800x600,
        When toggle_crop_mode is called,
        Then crop mode is enabled, UI updated, and rect initialized to 80% of image.
        """
        # Arrange
        mock_main_window.state.crop_mode = False
        mock_main_window.svc.has_processed_channels.return_value = True
        mock_main_window.svc.get_image_dimensions.return_value = (600, 800)  # (height, width)
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        # Act
        toggle_crop_mode(mock_main_window)
        # Assert
        assert mock_main_window.state.crop_mode is True
        mock_main_window.crop_mode_btn.setVisible.assert_called_once_with(False)
        mock_main_window.crop_controls.setVisible.assert_called_once_with(True)
        assert mock_main_window.state.crop_rect is not None
        mock_update_main_display.assert_called_once_with(mock_main_window)

    @patch("src.ui.handlers.crop._get_aspect_crop_rect")
    def test_applies_crop_ratio_to_default_rect(
        self,
        mock_aspect_rect: MagicMock,
        mock_update_main_display: MagicMock,
        mock_main_window: MagicMock
    ) -> None:
        """
        Given a crop ratio is set and no saved rect exists,
        When toggle_crop_mode is called,
        Then the aspect ratio is applied to the default rect.
        """
        # Arrange
        mock_main_window.state.crop_mode = False
        mock_main_window.state.crop_ratio = (16, 9)
        mock_main_window.svc.has_processed_channels.return_value = True
        mock_main_window.svc.get_image_dimensions.return_value = (600, 800)
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        adjusted_rect = MagicMock()
        mock_aspect_rect.return_value = adjusted_rect
        # Act
        toggle_crop_mode(mock_main_window)
        # Assert
        mock_aspect_rect.assert_called_once()
        assert mock_main_window.state.crop_rect == adjusted_rect

    def test_sets_viewer_crop_mode_and_rect(self, mock_update_main_display: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given crop mode is being toggled on,
        When toggle_crop_mode is called,
        Then viewer.set_crop_mode and viewer.set_crop_rect are called.
        """
        # Arrange
        mock_main_window.state.crop_mode = False
        mock_main_window.svc.has_processed_channels.return_value = True
        mock_main_window.svc.get_image_dimensions.return_value = (600, 800)
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        # Act
        toggle_crop_mode(mock_main_window)
        # Assert
        mock_main_window.viewer.set_crop_mode.assert_called_once_with(True)
        mock_main_window.viewer.set_crop_rect.assert_called_once()
        mock_main_window._update_mode_from_state.assert_called_once()
        mock_main_window.status_handler.set_message.assert_called_once()


@patch("src.ui.handlers.crop.update_main_display")
class TestCancelCrop:
    """
    Test Design Specification: cancel_crop()
    Module under test: src/ui/handlers/crop.py

    Contract:
        Exits crop mode without applying changes. Restores the last saved crop
        rectangle from the viewer if available, otherwise clears the crop rect.
        Updates UI visibility, viewer state, and displays status message.

    Equivalence partitions:
        EP1  Exit crop mode, with saved crop rect → restores saved rect
        EP2  Exit crop mode, no saved crop rect  → clears crop rect

    Boundary values:
        BV1  Saved rect at image edge (0, 0, width, height)
        BV2  Saved rect in center of image

    Exclusions:
        - Geometry validation (contract assumes saved rect is valid)

    Constraints:
        - Requires mocking ImageViewer, AppState, StatusBarHandler
        - MainWindow._update_mode_from_state must exist
    """

    def test_exits_crop_mode_with_saved_rect(self, mock_update_main_display: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given a saved crop rect exists and crop mode is active,
        When cancel_crop is called,
        Then crop mode is disabled and the saved rect is restored.
        """
        # Arrange
        saved_rect = MagicMock()
        mock_main_window.state.crop_mode = True
        mock_main_window.viewer.get_saved_crop_rect.return_value = saved_rect
        # Act
        cancel_crop(mock_main_window)
        # Assert
        assert mock_main_window.state.crop_mode is False
        mock_main_window.crop_mode_btn.setVisible.assert_called_once_with(True)
        mock_main_window.crop_controls.setVisible.assert_called_once_with(False)
        mock_update_main_display.assert_called_once_with(mock_main_window)

    def test_exits_crop_mode_without_saved_rect(self, mock_update_main_display: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given no saved crop rect exists,
        When cancel_crop is called,
        Then crop mode is disabled and crop rect is cleared.
        """
        # Arrange
        mock_main_window.state.crop_mode = True
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        # Act
        cancel_crop(mock_main_window)
        # Assert
        assert mock_main_window.state.crop_mode is False
        assert mock_main_window.state.crop_rect is None
        mock_main_window.viewer.set_crop_mode.assert_called_once_with(False)
        mock_update_main_display.assert_called_once_with(mock_main_window)

    def test_sets_status_message_on_cancel(self, mock_update_main_display: MagicMock, mock_main_window: MagicMock) -> None:
        """
        Given crop mode is being cancelled,
        When cancel_crop is called,
        Then a status message is set via status_handler.
        """
        # Arrange
        mock_main_window.state.crop_mode = True
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        # Act
        cancel_crop(mock_main_window)
        # Assert
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "cancelled" in call_args[0].lower()


@patch("src.ui.handlers.crop.update_main_display")
@patch("src.ui.handlers.crop._get_aspect_crop_rect")
class TestSetCropRatio:
    """
    Test Design Specification: set_crop_ratio()
    Module under test: src/ui/handlers/crop.py

    Contract:
        Sets the aspect ratio for the crop rectangle. If ratio is provided and
        a current crop rect exists, adjusts rect to maintain the aspect ratio.
        If ratio is None (free mode), uses current rect as-is. Syncs state and
        viewer crop rect. Updates main display.

    Equivalence partitions:
        EP1  Set to specific aspect ratio with rect     → applies ratio, adjusts rect
        EP2  Set to None (free mode) with rect          → uses rect as-is
        EP3  Set ratio with no current rect             → no change to rect
        EP4  Change from one ratio to another           → re-applies aspect

    Boundary values:
        BV1  Very wide aspect ratio (21:9)
        BV2  Very tall aspect ratio (9:21)
        BV3  Square aspect ratio (1:1)

    Exclusions:
        - Aspect ratio clamping to image bounds (delegated to _get_aspect_crop_rect)

    Constraints:
        - Requires mocking ImageViewer, AppState
        - Calls _get_aspect_crop_rect for calculations
    """

    def test_applies_aspect_ratio_to_current_rect(
        self,
        mock_aspect_rect: MagicMock,
        mock_update_main_display: MagicMock,
        mock_main_window: MagicMock
    ) -> None:
        """
        Given a current crop rect and a target aspect ratio,
        When set_crop_ratio is called,
        Then the aspect ratio is applied to the rect.
        """
        # Arrange
        current_rect = MagicMock()
        adjusted_rect = MagicMock()
        mock_main_window.viewer.get_crop_rect.return_value = current_rect
        mock_aspect_rect.return_value = adjusted_rect
        ratio = (16, 9)
        # Act
        set_crop_ratio(mock_main_window, ratio)
        # Assert
        assert mock_main_window.state.crop_ratio == ratio
        assert mock_main_window.state.crop_rect == adjusted_rect
        mock_main_window.viewer.set_crop_ratio.assert_called_once_with(ratio)
        mock_update_main_display.assert_called_once_with(mock_main_window)

    def test_free_mode_uses_current_rect_as_is(
        self,
        mock_aspect_rect: MagicMock,
        mock_update_main_display: MagicMock,
        mock_main_window: MagicMock
    ) -> None:
        """
        Given a current crop rect and ratio is set to None,
        When set_crop_ratio is called,
        Then the rect is used as-is without aspect adjustment.
        """
        # Arrange
        current_rect = MagicMock()
        mock_main_window.viewer.get_crop_rect.return_value = current_rect
        # Act
        set_crop_ratio(mock_main_window, None)
        # Assert
        assert mock_main_window.state.crop_ratio is None
        assert mock_main_window.state.crop_rect == current_rect
        mock_main_window.viewer.set_crop_ratio.assert_called_once_with(None)
        mock_update_main_display.assert_called_once_with(mock_main_window)

    def test_no_change_if_no_current_rect(
        self,
        mock_aspect_rect: MagicMock,
        mock_update_main_display: MagicMock,
        mock_main_window: MagicMock
    ) -> None:
        """
        Given no current crop rect,
        When set_crop_ratio is called,
        Then no rect adjustment is made.
        """
        # Arrange
        mock_main_window.viewer.get_crop_rect.return_value = None
        ratio = (16, 9)
        # Act
        set_crop_ratio(mock_main_window, ratio)
        # Assert
        assert mock_main_window.state.crop_ratio == ratio
        mock_update_main_display.assert_called_once_with(mock_main_window)

    def test_viewer_sync_in_aspect_mode(
        self,
        mock_aspect_rect: MagicMock,
        mock_update_main_display: MagicMock,
        mock_main_window: MagicMock
    ) -> None:
        """
        Given setting a specific aspect ratio,
        When set_crop_ratio is called,
        Then viewer is updated with both the ratio and the adjusted rect.
        """
        # Arrange
        current_rect = MagicMock()
        adjusted_rect = MagicMock()
        mock_main_window.viewer.get_crop_rect.return_value = current_rect
        mock_aspect_rect.return_value = adjusted_rect
        ratio = (4, 3)
        # Act
        set_crop_ratio(mock_main_window, ratio)
        # Assert
        mock_main_window.viewer.set_crop_ratio.assert_called_once_with(ratio)
        mock_main_window.viewer.set_crop_rect.assert_called_once_with(adjusted_rect)
        assert mock_main_window.state.crop_ratio == ratio
        assert mock_main_window.state.crop_rect == adjusted_rect


@patch("src.ui.handlers.crop.save_autosave")
@patch("src.ui.handlers.crop.show_single_channel_image")
@patch("src.ui.handlers.crop.show_combined_image")
@patch("src.ui.handlers.crop.update_channel_preview")
class TestApplyCrop:
    """
    Test Design Specification: apply_crop()
    Module under test: src/ui/handlers/crop.py

    Contract:
        Applies the current crop rectangle to the processed images by saving the
        rect for on-the-fly cropping (not modifying underlying images). Exits crop
        mode, updates all channel previews, updates UI state, and triggers autosave.
        Returns early if no valid crop rect or no processed channels.

    Equivalence partitions:
        EP1  Valid crop with processed channels    → applies crop, exits mode, updates UI
        EP2  No crop rect                          → returns early, no changes
        EP3  No processed channels                 → returns early, no changes

    Exclusions:
        - Rect intersection with image bounds (complex Qt mocking required)
        - Actual image pixel data modifications (visual only)

    Constraints:
        - Requires mocking ImageViewer, AppState, ImageProcessorService, StatusBarHandler
        - Calls update_channel_preview for each of 3 channels
        - Calls show_combined_image or show_single_channel_image based on state
    """

    def test_returns_early_if_no_crop_rect(
        self,
        mock_update_channel: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        mock_main_window: MagicMock
    ) -> None:
        """
        Given no crop rect,
        When apply_crop is called,
        Then the function returns early without changes.
        """
        # Arrange
        mock_main_window.viewer.get_crop_rect.return_value = None
        # Act
        apply_crop(mock_main_window)
        # Assert
        mock_main_window.viewer.confirm_crop.assert_not_called()
        mock_update_channel.assert_not_called()
        mock_save_autosave.assert_not_called()

    def test_returns_early_if_no_processed_channels(
        self,
        mock_update_channel: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        mock_main_window: MagicMock
    ) -> None:
        """
        Given crop rect exists but no processed channels,
        When apply_crop is called,
        Then the function returns early without changes.
        """
        # Arrange
        crop_rect = MagicMock()
        mock_main_window.viewer.get_crop_rect.return_value = crop_rect
        mock_main_window.svc.has_processed_channels.return_value = False
        # Act
        apply_crop(mock_main_window)
        # Assert
        mock_main_window.viewer.confirm_crop.assert_not_called()
        mock_save_autosave.assert_not_called()

    def test_returns_early_if_saved_rect_invalid(
        self,
        mock_update_channel: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        mock_main_window: MagicMock,
    ) -> None:
        """
        Given the intersected saved rect has isValid() == False,
        When apply_crop is called,
        Then the function returns early before confirming the crop.
        """
        # Arrange
        crop_rect = MagicMock()
        mock_main_window.viewer.get_crop_rect.return_value = crop_rect
        mock_main_window.svc.has_processed_channels.return_value = True
        mock_main_window.svc.get_image_dimensions.return_value = (600, 800)
        invalid_rect = MagicMock()
        invalid_rect.isValid.return_value = False
        invalid_rect.width.return_value = 0
        invalid_rect.height.return_value = 0
        qrect_instance = MagicMock()
        qrect_instance.intersected.return_value = invalid_rect
        # Act
        with patch("src.ui.handlers.crop.QRect", return_value=qrect_instance):
            apply_crop(mock_main_window)
        # Assert
        mock_main_window.viewer.confirm_crop.assert_not_called()
        mock_save_autosave.assert_not_called()

    def test_happy_path_combined_display(
        self,
        mock_update_channel: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        mock_main_window: MagicMock,
    ) -> None:
        """
        Given a valid crop rect and show_combined=True,
        When apply_crop is called,
        Then crop is confirmed, channel previews update, and combined image is shown.
        """
        # Arrange
        mock_main_window.viewer.get_crop_rect.return_value = MagicMock()
        mock_main_window.svc.has_processed_channels.return_value = True
        mock_main_window.svc.get_image_dimensions.return_value = (600, 800)
        mock_main_window.state.show_combined = True
        valid_rect = MagicMock()
        valid_rect.isValid.return_value = True
        valid_rect.width.return_value = 200
        valid_rect.height.return_value = 200
        qrect_instance = MagicMock()
        qrect_instance.intersected.return_value = valid_rect
        # Act
        with patch("src.ui.handlers.crop.QRect", return_value=qrect_instance):
            apply_crop(mock_main_window)
        # Assert
        mock_main_window.viewer.confirm_crop.assert_called_once()
        mock_main_window.viewer.set_saved_crop_rect.assert_called_once_with(valid_rect)
        assert mock_update_channel.call_count == 3
        assert mock_main_window.state.crop_mode is False
        mock_show_combined.assert_called_once_with(mock_main_window)
        mock_show_single.assert_not_called()
        mock_save_autosave.assert_called_once_with(mock_main_window)

    def test_happy_path_single_channel_display(
        self,
        mock_update_channel: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        mock_main_window: MagicMock,
    ) -> None:
        """
        Given a valid crop rect and show_combined=False,
        When apply_crop is called,
        Then show_single_channel_image is called instead of show_combined_image.
        """
        # Arrange
        mock_main_window.viewer.get_crop_rect.return_value = MagicMock()
        mock_main_window.svc.has_processed_channels.return_value = True
        mock_main_window.svc.get_image_dimensions.return_value = (600, 800)
        mock_main_window.state.show_combined = False
        valid_rect = MagicMock()
        valid_rect.isValid.return_value = True
        valid_rect.width.return_value = 200
        valid_rect.height.return_value = 200
        qrect_instance = MagicMock()
        qrect_instance.intersected.return_value = valid_rect
        # Act
        with patch("src.ui.handlers.crop.QRect", return_value=qrect_instance):
            apply_crop(mock_main_window)
        # Assert
        mock_show_single.assert_called_once_with(mock_main_window)
        mock_show_combined.assert_not_called()

    def test_happy_path_without_image_dimensions(
        self,
        mock_update_channel: MagicMock,
        mock_show_combined: MagicMock,
        mock_show_single: MagicMock,
        mock_save_autosave: MagicMock,
        mock_main_window: MagicMock,
    ) -> None:
        """
        Given get_image_dimensions returns None,
        When apply_crop is called,
        Then the original copied rect is used without intersection clamping.
        """
        # Arrange
        mock_main_window.viewer.get_crop_rect.return_value = MagicMock()
        mock_main_window.svc.has_processed_channels.return_value = True
        mock_main_window.svc.get_image_dimensions.return_value = None
        qrect_instance = MagicMock()
        qrect_instance.isValid.return_value = True
        qrect_instance.width.return_value = 200
        qrect_instance.height.return_value = 200
        # Act
        with patch("src.ui.handlers.crop.QRect", return_value=qrect_instance):
            apply_crop(mock_main_window)
        # Assert
        mock_main_window.viewer.confirm_crop.assert_called_once()
        mock_main_window.viewer.set_saved_crop_rect.assert_called_once_with(qrect_instance)
        mock_save_autosave.assert_called_once_with(mock_main_window)


@patch("src.ui.handlers.crop.update_main_display")
class TestToggleCropModeExtra:
    """
    Test Design Specification: toggle_crop_mode() — additional edge cases.
    Module under test: src/ui/handlers/crop.py

    Contract (covered here):
        Branches not exercised by TestToggleCropMode:
        - saved_crop_rect path (uses saved rect instead of computing default).
        - get_image_dimensions returns None (no default rect computed).

    Equivalence partitions:
        EP6  Saved crop rect exists      → state.crop_rect set from QRect(saved).
        EP7  No saved rect, dims is None → crop_rect stays None, set_crop_rect skipped.

    Constraints:
        - QRect is patched at the crop module boundary because PyQt5 is mocked
          globally in tests/unit/conftest.py.
    """

    def test_uses_saved_crop_rect_when_available(
        self, mock_update_main_display: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given a saved crop rect exists on the viewer,
        When toggle_crop_mode is called,
        Then state.crop_rect is set from a fresh QRect copy of the saved rect.
        """
        # Arrange
        saved = MagicMock()
        mock_main_window.viewer.get_saved_crop_rect.return_value = saved
        copied = MagicMock()
        # Act
        with patch("src.ui.handlers.crop.QRect", return_value=copied) as mock_qrect:
            toggle_crop_mode(mock_main_window)
        # Assert
        mock_qrect.assert_called_once_with(saved)
        assert mock_main_window.state.crop_rect is copied

    def test_dims_none_leaves_crop_rect_unset(
        self, mock_update_main_display: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given no saved rect and get_image_dimensions returns None,
        When toggle_crop_mode is called,
        Then state.crop_rect remains None and viewer.set_crop_rect is not called.
        """
        # Arrange
        mock_main_window.viewer.get_saved_crop_rect.return_value = None
        mock_main_window.svc.get_image_dimensions.return_value = None
        mock_main_window.state.crop_rect = None
        # Act
        toggle_crop_mode(mock_main_window)
        # Assert
        assert mock_main_window.state.crop_rect is None
        mock_main_window.viewer.set_crop_rect.assert_not_called()


class TestGetAspectCropRect:
    """
    Test Design Specification: _get_aspect_crop_rect()
    Module under test: src/ui/handlers/crop.py

    Contract:
        Returns the largest rectangle with the given aspect ratio that fits
        within rect, centred on rect.center(). Returns rect unchanged if rect
        or ratio is falsy.

    Equivalence partitions:
        EP1  rect is None / falsy        → returns rect as-is.
        EP2  ratio is None / falsy       → returns rect as-is.
        EP3  ratio wider than rect       → height shrinks (width-fits path).
        EP4  ratio narrower than rect    → width shrinks (height-limited path).
        EP5  ratio equals rect ratio     → result equals rect dimensions.

    Boundary values:
        BV1  1:1 ratio on square rect    → identity dimensions.
        BV2  1:1 ratio on wide rect      → square inscribed and centred.
        BV3  Zero width rect             → result has zero width.
        BV4  Zero height rect            → result has zero height.

    Exclusions:
        - Negative width/height not tested: undefined/invalid for callers.

    Constraints:
        - PyQt5 mocked globally; QRect is patched at the module boundary so
          we can verify the (left, top, w, h) tuple passed to its constructor.
    """

    @staticmethod
    def _make_rect(width: int, height: int, cx: int = 0, cy: int = 0) -> MagicMock:
        """Build a rect-like MagicMock returning int values from width/height/center."""
        rect = MagicMock()
        rect.width.return_value = width
        rect.height.return_value = height
        center = MagicMock()
        center.x.return_value = cx
        center.y.return_value = cy
        rect.center.return_value = center
        return rect

    def test_returns_rect_when_rect_falsy(self) -> None:
        """
        Given rect is None,
        When _get_aspect_crop_rect is called,
        Then None is returned unchanged.
        """
        # Arrange / Act
        result = _get_aspect_crop_rect(None, (16, 9))
        # Assert
        assert result is None

    def test_returns_rect_when_ratio_falsy(self) -> None:
        """
        Given a valid rect and ratio is None,
        When _get_aspect_crop_rect is called,
        Then the original rect is returned unchanged.
        """
        # Arrange
        rect = self._make_rect(100, 100)
        # Act
        result = _get_aspect_crop_rect(rect, None)
        # Assert
        assert result is rect

    def test_square_ratio_on_square_rect_is_identity(self) -> None:
        """
        Given a square rect and 1:1 aspect ratio,
        When _get_aspect_crop_rect is called,
        Then a 100x100 rect is constructed at the centred position.
        """
        # Arrange
        rect = self._make_rect(100, 100, cx=50, cy=50)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            _get_aspect_crop_rect(rect, (1, 1))
        # Assert
        mock_qrect.assert_called_once_with(0, 0, 100, 100)

    def test_square_ratio_on_wide_rect_inscribes_square(self) -> None:
        """
        Given a 200x100 rect and 1:1 ratio,
        When _get_aspect_crop_rect is called,
        Then a 100x100 square is constructed centred on the original rect.
        """
        # Arrange
        rect = self._make_rect(200, 100, cx=100, cy=50)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            _get_aspect_crop_rect(rect, (1, 1))
        # Assert
        mock_qrect.assert_called_once_with(50, 0, 100, 100)

    def test_wider_target_ratio_keeps_full_width(self) -> None:
        """
        Given a 100x100 rect and a 2:1 target ratio (wider),
        When _get_aspect_crop_rect is called,
        Then a 100x50 rect is constructed (width kept, height halved).
        """
        # Arrange
        rect = self._make_rect(100, 100, cx=50, cy=50)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            _get_aspect_crop_rect(rect, (2, 1))
        # Assert
        mock_qrect.assert_called_once_with(0, 25, 100, 50)

    def test_taller_target_ratio_triggers_height_limited_path(self) -> None:
        """
        Given a 100x100 rect and a 1:2 ratio (taller, width-fits-not),
        When _get_aspect_crop_rect is called,
        Then height is kept at 100 and width is shrunk to 50.
        """
        # Arrange
        rect = self._make_rect(100, 100, cx=50, cy=50)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            _get_aspect_crop_rect(rect, (1, 2))
        # Assert
        mock_qrect.assert_called_once_with(25, 0, 50, 100)

    def test_zero_width_rect_yields_zero_width(self) -> None:
        """
        Given a rect with zero width,
        When _get_aspect_crop_rect is called with 1:1 ratio,
        Then a rect of width 0 is constructed.
        """
        # Arrange
        rect = self._make_rect(0, 100, cx=0, cy=50)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            _get_aspect_crop_rect(rect, (1, 1))
        # Assert
        args, _ = mock_qrect.call_args
        assert args[2] == 0  # width

    def test_zero_height_rect_yields_zero_height(self) -> None:
        """
        Given a rect with zero height,
        When _get_aspect_crop_rect is called with 1:1 ratio,
        Then a rect of height 0 is constructed.
        """
        # Arrange
        rect = self._make_rect(100, 0, cx=50, cy=0)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            _get_aspect_crop_rect(rect, (1, 1))
        # Assert
        args, _ = mock_qrect.call_args
        assert args[3] == 0  # height


@patch("src.ui.handlers.crop.update_main_display")
class TestSetCropRatioBoundary:
    """
    Test Design Specification: set_crop_ratio() — boundary values for tiny rects.
    Module under test: src/ui/handlers/crop.py

    Contract (covered here):
        Behaviour when the current rect is at the smallest meaningful size and
        ratio enforcement is applied.

    Boundary values:
        BV1  1x1 viewer rect, 1:1 ratio  → 1x1 result (no further shrink).
        BV2  1x1 viewer rect, 16:9 ratio → height collapses to 0.

    Constraints:
        - QRect is patched at the crop module boundary; the rect-like input
          is a configured MagicMock returning int values for width/height/center.
    """

    @staticmethod
    def _rect_mock(width: int, height: int) -> MagicMock:
        """Build a rect-like MagicMock returning int values."""
        rect = MagicMock()
        rect.width.return_value = width
        rect.height.return_value = height
        center = MagicMock()
        center.x.return_value = width // 2
        center.y.return_value = height // 2
        rect.center.return_value = center
        return rect

    def test_tiny_rect_square_ratio_preserves_size(
        self, mock_update_main_display: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given a 1x1 viewer crop rect and a 1:1 ratio,
        When set_crop_ratio is called,
        Then QRect is constructed with width=1, height=1.
        """
        # Arrange
        mock_main_window.viewer.get_crop_rect.return_value = self._rect_mock(1, 1)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            set_crop_ratio(mock_main_window, (1, 1))
        # Assert
        args, _ = mock_qrect.call_args
        assert (args[2], args[3]) == (1, 1)

    def test_tiny_rect_wide_ratio_collapses_height(
        self, mock_update_main_display: MagicMock, mock_main_window: MagicMock
    ) -> None:
        """
        Given a 1x1 viewer crop rect and a 16:9 ratio,
        When set_crop_ratio is called,
        Then the constructed rect has height 0 (height-limited collapse).
        """
        # Arrange
        mock_main_window.viewer.get_crop_rect.return_value = self._rect_mock(1, 1)
        # Act
        with patch("src.ui.handlers.crop.QRect") as mock_qrect:
            set_crop_ratio(mock_main_window, (16, 9))
        # Assert
        args, _ = mock_qrect.call_args
        assert args[3] == 0
