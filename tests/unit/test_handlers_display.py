pytestmark = pytest.mark.skip_coverage_enforcement

"""Unit tests for src.ui.handlers.display module.

Tests display update handlers for combined and single-channel viewing.
"""

import pytest


# TODO: Add tests for display handlers


class TestUpdateMainDisplay:
    """Test suite for update_main_display() function."""

    # TODO: Test dispatches to combined view when show_combined is True
    # TODO: Test dispatches to single channel when show_combined is False
    # TODO: Test handles missing image data


class TestShowCombinedImage:
    """Test suite for show_combined_image() function."""

    # TODO: Test retrieves combined image from service
    # TODO: Test updates viewer with QPixmap
    # TODO: Test applies crop if present


class TestShowSingleChannelImage:
    """Test suite for show_single_channel_image() function."""

    # TODO: Test retrieves single channel from service
    # TODO: Test displays grayscale preview
    # TODO: Test updates correct channel viewer
