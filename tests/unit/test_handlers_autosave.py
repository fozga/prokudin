pytestmark = pytest.mark.skip_coverage_enforcement

"""Unit tests for src.ui.handlers.autosave module.

Tests session state persistence and restoration via JSON autosave.
"""

import pytest


# TODO: Add tests for autosave handler


class TestSaveAutosave:
    """Test suite for save_autosave() function."""

    # TODO: Test writes valid JSON file
    # TODO: Test saves channel paths
    # TODO: Test saves slider values
    # TODO: Test saves crop rectangle
    # TODO: Test creates parent directory if needed


class TestRestoreAutosave:
    """Test suite for restore_autosave() function."""

    # TODO: Test reads JSON and restores channel paths
    # TODO: Test restores slider values to controllers
    # TODO: Test restores crop rectangle
    # TODO: Test handles missing autosave file
    # TODO: Test handles corrupt JSON file
    # TODO: Test triggers channel loading after restore


class TestClearAutosave:
    """Test suite for clear_autosave() function."""

    # TODO: Test removes autosave file
    # TODO: Test handles missing file gracefully
