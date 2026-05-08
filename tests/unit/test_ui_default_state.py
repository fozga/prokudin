"""Unit tests for src.ui.default_state module.

Tests default configuration and slider default values.
"""

import pytest

from src.ui.default_state import DefaultState, SliderDefaults


class TestSliderDefaults:
    """Test suite for SliderDefaults dataclass."""

    def test_default_values(self) -> None:
        """Test SliderDefaults has correct default values."""
        defaults = SliderDefaults()
        assert defaults.brightness == 0
        assert defaults.contrast == 0
        assert defaults.intensity == 100


class TestDefaultState:
    """Test suite for DefaultState configuration class."""

    def test_show_combined_default(self) -> None:
        """Test SHOW_COMBINED default is True."""
        assert DefaultState.SHOW_COMBINED is True

    def test_current_channel_default(self) -> None:
        """Test CURRENT_CHANNEL default is 0 (red)."""
        assert DefaultState.CURRENT_CHANNEL == 0

    def test_crop_mode_default(self) -> None:
        """Test CROP_MODE default is False."""
        assert DefaultState.CROP_MODE is False

    def test_get_slider_defaults(self) -> None:
        """Test get_slider_defaults() returns correct dict."""
        defaults_dict = DefaultState.get_slider_defaults()
        assert defaults_dict["brightness"] == 0
        assert defaults_dict["contrast"] == 0
        assert defaults_dict["intensity"] == 100
