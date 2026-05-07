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
Default state configuration for the application.
Provides a centralized location for all default values and state initialization.
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class SliderDefaults:
    """Default values for adjustment sliders."""

    brightness: int = 0
    contrast: int = 0
    intensity: int = 100


class DefaultState:  # pylint: disable=too-few-public-methods
    """
    Holds default values for the entire application state.

    This class serves as a single source of truth for all default values,
    ensuring consistency between application startup and reset operations.

    Attributes:
        SLIDER_DEFAULTS: Default values for channel adjustment sliders
        SHOW_COMBINED: Default display mode (True = combined RGB, False = single channel)
        CURRENT_CHANNEL: Default selected channel (0 = red, 1 = green, 2 = blue)
        CROP_MODE: Default crop mode state
    """

    # Slider defaults
    SLIDER_DEFAULTS: ClassVar[SliderDefaults] = SliderDefaults()

    # Display defaults
    SHOW_COMBINED: ClassVar[bool] = True
    CURRENT_CHANNEL: ClassVar[int] = 0

    # Crop defaults
    CROP_MODE: ClassVar[bool] = False

    @classmethod
    def get_slider_defaults(cls) -> dict[str, int]:
        """
        Get slider default values as a dictionary.

        Returns:
            dict: Dictionary with slider names as keys and default values
        """
        return {
            "brightness": cls.SLIDER_DEFAULTS.brightness,
            "contrast": cls.SLIDER_DEFAULTS.contrast,
            "intensity": cls.SLIDER_DEFAULTS.intensity,
        }
