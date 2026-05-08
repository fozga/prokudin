pytestmark = pytest.mark.skip_coverage_enforcement

"""Unit tests for src.ui.handlers.image_saving module.

Tests image export to JPEG, PNG, TIFF with optional cropping and per-channel save.
"""

import pytest


# TODO: Add tests for image saving handler


class TestApplyCrop:
    """Test suite for apply_crop() function."""

    # TODO: Test crops numpy array correctly
    # TODO: Test handles crop with origin offset
    # TODO: Test preserves channel count
    # TODO: Test handles missing crop rectangle


class TestSaveImage:
    """Test suite for save_image() function."""

    # TODO: Test JPEG export
    # TODO: Test PNG export
    # TODO: Test TIFF export
    # TODO: Test per-channel save creates individual files
    # TODO: Test combined RGB save creates 3-channel image
    # TODO: Test handles file write errors


class TestSaveImageWithDialog:
    """Test suite for save_image_with_dialog() function."""

    # TODO: Test opens file save dialog
    # TODO: Test dialog cancellation handled gracefully
    # TODO: Test dispatches to save_image() on selection
    # TODO: Test format detection from file extension
    # TODO: Test handles dialog errors
