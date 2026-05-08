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
Unit tests for src.ui.default_state module.

Tests SliderDefaults dataclass and DefaultState configuration class.
"""

import pytest

from src.ui.default_state import DefaultState, SliderDefaults


class TestSliderDefaults:
    """Tests for SliderDefaults dataclass."""

    def test_default_brightness(self) -> None:
        """Verify brightness default is 0."""
        defaults = SliderDefaults()
        assert defaults.brightness == 0

    def test_default_contrast(self) -> None:
        """Verify contrast default is 0."""
        defaults = SliderDefaults()
        assert defaults.contrast == 0

    def test_default_intensity(self) -> None:
        """Verify intensity default is 100."""
        defaults = SliderDefaults()
        assert defaults.intensity == 100

    def test_custom_brightness(self) -> None:
        """Verify brightness can be customized."""
        defaults = SliderDefaults(brightness=50)
        assert defaults.brightness == 50
        assert defaults.contrast == 0
        assert defaults.intensity == 100

    def test_custom_contrast(self) -> None:
        """Verify contrast can be customized."""
        defaults = SliderDefaults(contrast=-30)
        assert defaults.brightness == 0
        assert defaults.contrast == -30
        assert defaults.intensity == 100

    def test_custom_intensity(self) -> None:
        """Verify intensity can be customized."""
        defaults = SliderDefaults(intensity=75)
        assert defaults.brightness == 0
        assert defaults.contrast == 0
        assert defaults.intensity == 75

    def test_custom_all_values(self) -> None:
        """Verify all values can be customized together."""
        defaults = SliderDefaults(brightness=20, contrast=-10, intensity=150)
        assert defaults.brightness == 20
        assert defaults.contrast == -10
        assert defaults.intensity == 150

    def test_negative_brightness(self) -> None:
        """Verify negative brightness values are allowed."""
        defaults = SliderDefaults(brightness=-100)
        assert defaults.brightness == -100

    def test_zero_intensity(self) -> None:
        """Verify zero intensity is allowed."""
        defaults = SliderDefaults(intensity=0)
        assert defaults.intensity == 0

    def test_out_of_range_values_accepted(self) -> None:
        """Verify dataclass accepts out-of-range values (no validation at this layer).

        Note: UI layer enforces ranges (brightness/contrast: -100 to 100, intensity: 0 to 100).
        This test documents that SliderDefaults does not validate; constraints are enforced
        by UI widgets (channel_controller.py) via slider min/max.
        """
        # Brightness beyond UI range
        defaults = SliderDefaults(brightness=-200)
        assert defaults.brightness == -200

        # Contrast beyond UI range
        defaults = SliderDefaults(contrast=200)
        assert defaults.contrast == 200

        # Intensity beyond UI range
        defaults = SliderDefaults(intensity=150)
        assert defaults.intensity == 150



class TestDefaultState:
    """Tests for DefaultState configuration class."""

    def test_slider_defaults_exists(self) -> None:
        """Verify SLIDER_DEFAULTS class variable is defined."""
        assert hasattr(DefaultState, "SLIDER_DEFAULTS")
        assert isinstance(DefaultState.SLIDER_DEFAULTS, SliderDefaults)

    def test_slider_defaults_brightness(self) -> None:
        """Verify SLIDER_DEFAULTS brightness is 0."""
        assert DefaultState.SLIDER_DEFAULTS.brightness == 0

    def test_slider_defaults_contrast(self) -> None:
        """Verify SLIDER_DEFAULTS contrast is 0."""
        assert DefaultState.SLIDER_DEFAULTS.contrast == 0

    def test_slider_defaults_intensity(self) -> None:
        """Verify SLIDER_DEFAULTS intensity is 100."""
        assert DefaultState.SLIDER_DEFAULTS.intensity == 100

    def test_show_combined_default(self) -> None:
        """Verify SHOW_COMBINED is True by default."""
        assert DefaultState.SHOW_COMBINED is True
        assert isinstance(DefaultState.SHOW_COMBINED, bool)

    def test_current_channel_default(self) -> None:
        """Verify CURRENT_CHANNEL is 0 (red) by default."""
        assert DefaultState.CURRENT_CHANNEL == 0
        assert isinstance(DefaultState.CURRENT_CHANNEL, int)

    def test_crop_mode_default(self) -> None:
        """Verify CROP_MODE is False by default."""
        assert DefaultState.CROP_MODE is False
        assert isinstance(DefaultState.CROP_MODE, bool)

    def test_get_slider_defaults_returns_dict(self) -> None:
        """Verify get_slider_defaults returns a dictionary."""
        result = DefaultState.get_slider_defaults()
        assert isinstance(result, dict)

    def test_get_slider_defaults_has_required_keys(self) -> None:
        """Verify returned dict contains brightness, contrast, intensity keys."""
        result = DefaultState.get_slider_defaults()
        assert "brightness" in result
        assert "contrast" in result
        assert "intensity" in result

    def test_get_slider_defaults_brightness_value(self) -> None:
        """Verify get_slider_defaults brightness is 0."""
        result = DefaultState.get_slider_defaults()
        assert result["brightness"] == 0

    def test_get_slider_defaults_contrast_value(self) -> None:
        """Verify get_slider_defaults contrast is 0."""
        result = DefaultState.get_slider_defaults()
        assert result["contrast"] == 0

    def test_get_slider_defaults_intensity_value(self) -> None:
        """Verify get_slider_defaults intensity is 100."""
        result = DefaultState.get_slider_defaults()
        assert result["intensity"] == 100

    def test_get_slider_defaults_all_values(self) -> None:
        """Verify get_slider_defaults returns correct all values."""
        result = DefaultState.get_slider_defaults()
        assert result == {"brightness": 0, "contrast": 0, "intensity": 100}

    def test_get_slider_defaults_only_three_keys(self) -> None:
        """Verify get_slider_defaults returns exactly three keys."""
        result = DefaultState.get_slider_defaults()
        assert len(result) == 3

    def test_get_slider_defaults_value_types(self) -> None:
        """Verify all values returned by get_slider_defaults are integers."""
        result = DefaultState.get_slider_defaults()
        assert isinstance(result["brightness"], int)
        assert isinstance(result["contrast"], int)
        assert isinstance(result["intensity"], int)

    def test_get_slider_defaults_consistency(self) -> None:
        """Verify get_slider_defaults matches SLIDER_DEFAULTS values."""
        result = DefaultState.get_slider_defaults()
        assert result["brightness"] == DefaultState.SLIDER_DEFAULTS.brightness
        assert result["contrast"] == DefaultState.SLIDER_DEFAULTS.contrast
        assert result["intensity"] == DefaultState.SLIDER_DEFAULTS.intensity

    def test_multiple_calls_to_get_slider_defaults_consistent(self) -> None:
        """Verify multiple calls to get_slider_defaults return identical values."""
        result1 = DefaultState.get_slider_defaults()
        result2 = DefaultState.get_slider_defaults()
        assert result1 == result2

    def test_get_slider_defaults_returns_new_dict(self) -> None:
        """Verify get_slider_defaults returns a new dict each time."""
        result1 = DefaultState.get_slider_defaults()
        result2 = DefaultState.get_slider_defaults()
        assert result1 is not result2
        assert result1 == result2
