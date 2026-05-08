import pytest

"""Unit tests for src.ui.handlers.channels module.

Tests channel loading, adjustment, and display handlers.
"""

import pytest


# TODO: Add tests for channel handlers


class TestProcessChannelImage:
    """Test suite for _process_channel_image() helper."""

    # TODO: Test loads RGB image into service
    # TODO: Test updates status message
    # TODO: Test triggers adjustment on alignment
    # TODO: Test updates previews and main display


class TestLoadChannel:
    """Test suite for load_channel() function."""

    # TODO: Test successful file dialog load
    # TODO: Test stores file path in state
    # TODO: Test handles dialog cancellation
    # TODO: Test handles load errors


class TestLoadChannelFromPath:
    """Test suite for load_channel_from_path() function."""

    # TODO: Test loads from file path without dialog
    # TODO: Test handles missing file
    # TODO: Test handles corrupt file


class TestAdjustChannel:
    """Test suite for adjust_channel() function."""

    # TODO: Test reads slider values
    # TODO: Test delegates to service
    # TODO: Test updates previews and display
    # TODO: Test handles missing channel


class TestUpdateChannelPreview:
    """Test suite for update_channel_preview() function."""

    # TODO: Test retrieves preview from service
    # TODO: Test updates controller preview


class TestShowSingleChannel:
    """Test suite for show_single_channel() function."""

    # TODO: Test sets show_combined to False
    # TODO: Test sets current_channel
    # TODO: Test triggers display update
