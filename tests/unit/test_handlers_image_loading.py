"""Unit tests for src.ui.handlers.image_loading module.

Tests RAW image loading from Sony ARW files.
"""

import pytest

pytestmark = pytest.mark.skip_coverage_enforcement



# TODO: Add tests for image loading handler


class TestLoadRawImage:
    """Test suite for load_raw_image() function."""

    # TODO: Test successful file selection and load
    # TODO: Test returns RGB numpy array
    # TODO: Test returns file path
    # TODO: Test dialog cancellation returns None values
    # TODO: Test handles invalid file format
    # TODO: Test handles corrupted RAW file


class TestLoadRawImageFromPath:
    """Test suite for load_raw_image_from_path() function."""

    # TODO: Test loads from given file path
    # TODO: Test returns RGB numpy array
    # TODO: Test handles missing file
    # TODO: Test handles corrupt file
    # TODO: Test handles unsupported format
