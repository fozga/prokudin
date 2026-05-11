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
    """
    Test Design Specification: SliderDefaults dataclass
    Module under test: src/ui/default_state.py

    Contract:
        SliderDefaults is a dataclass storing default values for adjustment sliders.
        Three fields: brightness (default 0), contrast (default 0), intensity (default 100).
        Supports partial or full customization. Accepts any integer value (no validation).
        No side effects; pure data structure for configuration.

    Equivalence partitions:
        EP1  Default initialization             → brightness=0, contrast=0, intensity=100
        EP2  Custom brightness                  → specified brightness, others default
        EP3  Custom contrast                    → specified contrast, others default
        EP4  Custom intensity                   → specified intensity, others default
        EP5  Custom all fields                  → all customized
        EP6  Negative values                    → accepts negative brightness/contrast
        EP7  Zero intensity                     → accepts intensity=0
        EP8  Out-of-range values                → accepts values beyond UI limits

    Boundary values:
        BV1  brightness = -100 (min typical)
        BV2  brightness = 0 (default/neutral)
        BV3  brightness = 100 (max typical)
        BV4  contrast = -100 (min typical)
        BV5  contrast = 0 (default/neutral)
        BV6  contrast = 100 (max typical)
        BV7  intensity = 0 (minimum)
        BV8  intensity = 100 (default)
        BV9  intensity = 150 (beyond typical range)

    Exclusions:
        - Range validation (dataclass accepts any int; UI layer enforces [-100,100] and [0,100])
        - Type validation (assumes int inputs)
        - Slider widget integration (testing dataclass only)

    Constraints:
        - Pure dataclass; no external dependencies
        - No validation at this layer; validation is UI responsibility
        - Used by DefaultState as SLIDER_DEFAULTS constant
    """

    def test_default_brightness(self) -> None:
        """
        Given: SliderDefaults instantiated with no arguments
        When: brightness field is accessed
        Then: it defaults to 0
        """
        defaults = SliderDefaults()
        assert defaults.brightness == 0

    def test_default_contrast(self) -> None:
        """
        Given: SliderDefaults instantiated with no arguments
        When: contrast field is accessed
        Then: it defaults to 0
        """
        defaults = SliderDefaults()
        assert defaults.contrast == 0

    def test_default_intensity(self) -> None:
        """
        Given: SliderDefaults instantiated with no arguments
        When: intensity field is accessed
        Then: it defaults to 100
        """
        defaults = SliderDefaults()
        assert defaults.intensity == 100

    def test_custom_brightness(self) -> None:
        """
        Given: custom brightness value of 50
        When: SliderDefaults is initialized with this value
        Then: brightness is set to 50 while contrast and intensity keep defaults
        """
        # Arrange & Act
        defaults = SliderDefaults(brightness=50)
        # Assert
        assert defaults.brightness == 50
        assert defaults.contrast == 0
        assert defaults.intensity == 100

    def test_custom_contrast(self) -> None:
        """
        Given: custom contrast value of -30
        When: SliderDefaults is initialized with this value
        Then: contrast is set to -30 while brightness and intensity keep defaults
        """
        # Arrange & Act
        defaults = SliderDefaults(contrast=-30)
        # Assert
        assert defaults.brightness == 0
        assert defaults.contrast == -30
        assert defaults.intensity == 100

    def test_custom_intensity(self) -> None:
        """
        Given: custom intensity value of 75
        When: SliderDefaults is initialized with this value
        Then: intensity is set to 75 while brightness and contrast keep defaults
        """
        # Arrange & Act
        defaults = SliderDefaults(intensity=75)
        # Assert
        assert defaults.brightness == 0
        assert defaults.contrast == 0
        assert defaults.intensity == 75

    def test_custom_all_values(self) -> None:
        """
        Given: custom values for all three slider defaults
        When: SliderDefaults is initialized with these values
        Then: all three fields are set to the specified custom values
        """
        # Arrange & Act
        defaults = SliderDefaults(brightness=20, contrast=-10, intensity=150)
        # Assert
        assert defaults.brightness == 20
        assert defaults.contrast == -10
        assert defaults.intensity == 150

    def test_negative_brightness(self) -> None:
        """
        Given: negative brightness value of -100
        When: SliderDefaults is initialized with this value
        Then: negative values are accepted by the dataclass (no validation)
        """
        defaults = SliderDefaults(brightness=-100)
        assert defaults.brightness == -100

    def test_zero_intensity(self) -> None:
        """
        Given: intensity value of 0
        When: SliderDefaults is initialized with this value
        Then: zero values are accepted by the dataclass (no validation)
        """
        defaults = SliderDefaults(intensity=0)
        assert defaults.intensity == 0

    @pytest.mark.parametrize("field,value", [
        ("brightness", -200),  # BV1: negative overflow beyond UI range
        ("contrast", 200),     # BV1: positive overflow beyond UI range
        ("intensity", 150),    # BV1: positive overflow beyond UI range
    ], ids=["brightness_overflow", "contrast_overflow", "intensity_overflow"])
    def test_out_of_range_values_accepted(self, field: str, value: int) -> None:
        """
        Given: an out-of-range value for a slider field
        When: SliderDefaults is initialized with this extreme value
        Then: the value is accepted without validation at the dataclass layer
        """
        # Arrange
        kwargs = {field: value}
        # Act
        defaults = SliderDefaults(**kwargs)
        # Assert
        assert getattr(defaults, field) == value



class TestDefaultState:
    """
    Test Design Specification: DefaultState configuration class
    Module under test: src/ui/default_state.py

    Contract:
        DefaultState is a configuration class providing centralized default values for the app.
        Holds class variables: SLIDER_DEFAULTS (SliderDefaults), SHOW_COMBINED (True),
        CURRENT_CHANNEL (0), CROP_MODE (False).
        Provides class method get_slider_defaults() returning dict with keys
        'brightness', 'contrast', 'intensity' and integer values.
        Multiple calls to get_slider_defaults() return new dict instances (not cached).

    Equivalence partitions:
        EP1  SLIDER_DEFAULTS exists             → is SliderDefaults instance
        EP2  SHOW_COMBINED constant             → is True (bool type)
        EP3  CURRENT_CHANNEL constant           → is 0 (int type)
        EP4  CROP_MODE constant                 → is False (bool type)
        EP5  get_slider_defaults() returns dict → dict with 3 keys
        EP6  Dict contains correct keys         → 'brightness', 'contrast', 'intensity'
        EP7  Dict values match SLIDER_DEFAULTS  → consistent with class variable
        EP8  Multiple calls to getter           → each returns new dict instance

    Boundary values:
        BV1  SLIDER_DEFAULTS.brightness = 0
        BV2  SLIDER_DEFAULTS.contrast = 0
        BV3  SLIDER_DEFAULTS.intensity = 100
        BV4  SHOW_COMBINED = True
        BV5  CURRENT_CHANNEL = 0
        BV6  CROP_MODE = False
        BV7  get_slider_defaults() dict length = 3

    Exclusions:
        - Modification of class variables (tests read-only access)
        - Subclassing DefaultState
        - get_slider_defaults() caching (tests each call is independent)

    Constraints:
        - No external dependencies
        - Pure configuration class (no side effects)
        - Uses ClassVar type hints for constants
    """

    def test_slider_defaults_exists(self) -> None:
        """
        Given: DefaultState configuration class
        When: the SLIDER_DEFAULTS class variable is accessed
        Then: it exists and is an instance of SliderDefaults
        """
        # Arrange & Act
        # Assert
        assert hasattr(DefaultState, "SLIDER_DEFAULTS")
        assert isinstance(DefaultState.SLIDER_DEFAULTS, SliderDefaults)

    def test_slider_defaults_brightness(self) -> None:
        """
        Given: DefaultState.SLIDER_DEFAULTS constant
        When: the brightness field is accessed
        Then: it equals 0
        """
        assert DefaultState.SLIDER_DEFAULTS.brightness == 0

    def test_slider_defaults_contrast(self) -> None:
        """
        Given: DefaultState.SLIDER_DEFAULTS constant
        When: the contrast field is accessed
        Then: it equals 0
        """
        assert DefaultState.SLIDER_DEFAULTS.contrast == 0

    def test_slider_defaults_intensity(self) -> None:
        """
        Given: DefaultState.SLIDER_DEFAULTS constant
        When: the intensity field is accessed
        Then: it equals 100
        """
        assert DefaultState.SLIDER_DEFAULTS.intensity == 100

    def test_show_combined_default(self) -> None:
        """
        Given: DefaultState configuration class
        When: SHOW_COMBINED constant is accessed
        Then: it equals True and is of type bool
        """
        # Arrange & Act
        # Assert
        assert DefaultState.SHOW_COMBINED is True
        assert isinstance(DefaultState.SHOW_COMBINED, bool)

    def test_current_channel_default(self) -> None:
        """
        Given: DefaultState configuration class
        When: CURRENT_CHANNEL constant is accessed
        Then: it equals 0 (red channel) and is of type int
        """
        # Arrange & Act
        # Assert
        assert DefaultState.CURRENT_CHANNEL == 0
        assert isinstance(DefaultState.CURRENT_CHANNEL, int)

    def test_crop_mode_default(self) -> None:
        """
        Given: DefaultState configuration class
        When: CROP_MODE constant is accessed
        Then: it equals False and is of type bool
        """
        # Arrange & Act
        # Assert
        assert DefaultState.CROP_MODE is False
        assert isinstance(DefaultState.CROP_MODE, bool)

    def test_get_slider_defaults_returns_dict(self) -> None:
        """
        Given: DefaultState class
        When: get_slider_defaults() class method is called
        Then: it returns a dictionary object
        """
        result = DefaultState.get_slider_defaults()
        assert isinstance(result, dict)

    def test_get_slider_defaults_has_required_keys(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the dictionary is examined
        Then: it contains keys for brightness, contrast, and intensity
        """
        # Arrange & Act
        result = DefaultState.get_slider_defaults()
        # Assert
        assert "brightness" in result
        assert "contrast" in result
        assert "intensity" in result

    def test_get_slider_defaults_brightness_value(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the brightness key is accessed
        Then: its value equals 0
        """
        result = DefaultState.get_slider_defaults()
        assert result["brightness"] == 0

    def test_get_slider_defaults_contrast_value(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the contrast key is accessed
        Then: its value equals 0
        """
        result = DefaultState.get_slider_defaults()
        assert result["contrast"] == 0

    def test_get_slider_defaults_intensity_value(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the intensity key is accessed
        Then: its value equals 100
        """
        result = DefaultState.get_slider_defaults()
        assert result["intensity"] == 100

    def test_get_slider_defaults_all_values(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the entire dictionary is examined
        Then: it equals the expected dictionary with all default values
        """
        result = DefaultState.get_slider_defaults()
        assert result == {"brightness": 0, "contrast": 0, "intensity": 100}

    def test_get_slider_defaults_only_three_keys(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the number of keys is checked
        Then: the dictionary contains exactly three keys
        """
        result = DefaultState.get_slider_defaults()
        assert len(result) == 3

    def test_get_slider_defaults_value_types(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the types of each value are checked
        Then: all values are integers
        """
        # Arrange & Act
        result = DefaultState.get_slider_defaults()
        # Assert
        assert isinstance(result["brightness"], int)
        assert isinstance(result["contrast"], int)
        assert isinstance(result["intensity"], int)

    def test_get_slider_defaults_consistency(self) -> None:
        """
        Given: result from get_slider_defaults() method
        When: the values are compared to SLIDER_DEFAULTS fields
        Then: the dictionary values match the corresponding field values
        """
        # Arrange & Act
        result = DefaultState.get_slider_defaults()
        # Assert
        assert result["brightness"] == DefaultState.SLIDER_DEFAULTS.brightness
        assert result["contrast"] == DefaultState.SLIDER_DEFAULTS.contrast
        assert result["intensity"] == DefaultState.SLIDER_DEFAULTS.intensity

    def test_multiple_calls_to_get_slider_defaults_consistent(self) -> None:
        """
        Given: two separate calls to get_slider_defaults() method
        When: the results are compared
        Then: both calls return identical dictionary values
        """
        result1 = DefaultState.get_slider_defaults()
        result2 = DefaultState.get_slider_defaults()
        assert result1 == result2

    def test_get_slider_defaults_returns_new_dict(self) -> None:
        """
        Given: two separate calls to get_slider_defaults() method
        When: the results are compared by identity and equality
        Then: they are different objects but with identical values
        """
        # Act
        result1 = DefaultState.get_slider_defaults()
        result2 = DefaultState.get_slider_defaults()
        # Assert
        assert result1 is not result2
        assert result1 == result2
