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

# pylint: disable=too-few-public-methods

"""
Custom slider widgets for the application's UI.
Provides a ResetSlider that emits a signal on double-click for quick reset functionality.
"""

from typing import Union

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QSlider


class ResetSlider(QSlider):
    """
    QSlider subclass with double-click reset functionality.

    Cross-references:
        - ChannelController: Used for brightness, contrast, intensity sliders.
    """

    doubleClicked = pyqtSignal()
    """
    Signal emitted when the slider is double-clicked.
    Can be connected to a slot to reset the slider or perform other actions.
    """

    def mouseDoubleClickEvent(self, event: Union[QMouseEvent, None]) -> None:  # pylint: disable=C0103
        """
        Handles the mouse double-click event.
        Emits the doubleClicked signal and then calls the base class implementation.
        Args:
            event (QMouseEvent | None): The mouse double-click event.
        """
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
