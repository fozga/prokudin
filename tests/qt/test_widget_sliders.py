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

"""Widget tests for src/ui/widgets/sliders.py."""

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QSlider
from pytestqt.plugin import QtBot

from src.ui.widgets.sliders import ResetSlider


@pytest.mark.widget
class TestResetSlider:
    """
    Test Design Specification: ResetSlider
    Module under test: src/ui/widgets/sliders.py

    Widget base class: QSlider

    Contract:
        ResetSlider is a QSlider subclass that emits a custom doubleClicked
        signal when the user double-clicks the slider. All standard QSlider
        behaviour (value, minimum, maximum, orientation) is inherited unchanged.
        The doubleClicked signal is intended to be connected to a reset slot by
        the parent widget (ChannelController). mouseDoubleClickEvent(None) is
        handled defensively by returning early before forwarding to the base class.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - No file IO or external services.
        - Mouse event simulation requires widget.show() — see Constraints.

    What is tested:
        - Default instantiation produces a valid QSlider.
        - setValue / value round-trip for values within [minimum, maximum].
        - Values outside [minimum, maximum] are clamped by Qt.
        - Double-clicking the widget emits the doubleClicked signal.
        - mouseDoubleClickEvent(None) returns early without raising.
        - doubleClicked is emitted before the None early-return check.

    What is NOT tested:
        - Visual appearance, groove, or handle pixel positions.
        - Drag behaviour or continuous value changes during drag.
        - Keyboard navigation (arrow keys, Page Up/Down).

    Equivalence partitions:
        EP1  Default instantiation         → valid QSlider, value=0, min=0, max=99
        EP2  setValue within [min, max]    → value stored exactly
        EP3  setValue below minimum        → value clamped to minimum
        EP4  setValue above maximum        → value clamped to maximum
        EP5  double-click event            → doubleClicked signal emitted
        EP6  mouseDoubleClickEvent(None)   → early return, no exception

    Boundary values:
        BV1  setValue(0)   — QSlider default minimum
        BV2  setValue(99)  — QSlider default maximum
        BV3  setValue(-1)  — one below minimum, clamped to 0
        BV4  setValue(100) — one above maximum, clamped to 99

    Mocking strategy:
        No external dependencies require mocking.

    Constraints:
        - Mouse event simulation via qtbot.mouseDClick requires widget.show()
          so that the widget has a valid geometry for hit-testing.
    """

    def test_default_initialization_creates_valid_slider(self, qtbot: QtBot) -> None:
        """
        Given ResetSlider is instantiated with no arguments,
        When the widget is created,
        Then it is a QSlider with value 0, minimum 0, and maximum 99.
        """
        # Arrange + Act
        slider = ResetSlider()
        qtbot.addWidget(slider)
        # Assert
        assert isinstance(slider, QSlider)
        assert slider.value() == 0
        assert slider.minimum() == 0
        assert slider.maximum() == 99

    def test_horizontal_orientation_is_set_correctly(self, qtbot: QtBot) -> None:
        """
        Given ResetSlider is instantiated with Qt.Horizontal orientation,
        When the widget is created,
        Then its orientation is horizontal.
        """
        # Arrange + Act
        slider = ResetSlider(Qt.Horizontal)
        qtbot.addWidget(slider)
        # Assert
        assert slider.orientation() == Qt.Horizontal

    def test_vertical_orientation_is_set_correctly(self, qtbot: QtBot) -> None:
        """
        Given ResetSlider is instantiated with Qt.Vertical orientation,
        When the widget is created,
        Then its orientation is vertical.
        """
        # Arrange + Act
        slider = ResetSlider(Qt.Vertical)
        qtbot.addWidget(slider)
        # Assert
        assert slider.orientation() == Qt.Vertical

    @pytest.mark.parametrize(
        "value",
        [
            0,   # BV1: default minimum
            99,  # BV2: default maximum
            50,  # EP2: midrange value
        ],
        ids=["min", "max", "mid"],
    )
    def test_set_value_within_range_stores_value(self, qtbot: QtBot, value: int) -> None:
        """
        Given a ResetSlider with default range [0, 99],
        When setValue is called with a value within the range,
        Then value() returns exactly that value.
        """
        # Arrange
        slider = ResetSlider()
        qtbot.addWidget(slider)
        # Act
        slider.setValue(value)
        # Assert
        assert slider.value() == value

    def test_set_value_below_minimum_clamps_to_minimum(self, qtbot: QtBot) -> None:
        """
        Given a ResetSlider with default minimum 0,
        When setValue is called with -1 (one below minimum),
        Then value() is clamped to 0.
        """
        # Arrange
        slider = ResetSlider()
        qtbot.addWidget(slider)
        # Act
        slider.setValue(-1)  # BV3
        # Assert
        assert slider.value() == slider.minimum()

    def test_set_value_above_maximum_clamps_to_maximum(self, qtbot: QtBot) -> None:
        """
        Given a ResetSlider with default maximum 99,
        When setValue is called with 100 (one above maximum),
        Then value() is clamped to 99.
        """
        # Arrange
        slider = ResetSlider()
        qtbot.addWidget(slider)
        # Act
        slider.setValue(100)  # BV4
        # Assert
        assert slider.value() == slider.maximum()

    def test_double_click_emits_double_clicked_signal(self, qtbot: QtBot) -> None:
        """
        Given a visible ResetSlider,
        When the slider is double-clicked,
        Then the doubleClicked signal is emitted.
        """
        # Arrange
        slider = ResetSlider(Qt.Horizontal)
        qtbot.addWidget(slider)
        slider.show()
        # Act + Assert
        with qtbot.waitSignal(slider.doubleClicked, timeout=1000):
            qtbot.mouseDClick(slider, Qt.LeftButton)

    def test_mouse_double_click_event_with_none_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given a ResetSlider,
        When mouseDoubleClickEvent is called with None,
        Then the doubleClicked signal is emitted and no exception is raised.
        """
        # Arrange
        slider = ResetSlider()
        qtbot.addWidget(slider)
        # Act + Assert
        with qtbot.waitSignal(slider.doubleClicked, timeout=1000):
            slider.mouseDoubleClickEvent(None)

    def test_double_clicked_signal_is_emitted_before_none_guard(self, qtbot: QtBot) -> None:
        """
        Given a ResetSlider,
        When mouseDoubleClickEvent is called with None,
        Then doubleClicked is emitted (the signal emit precedes the None check).
        """
        # Arrange
        slider = ResetSlider()
        qtbot.addWidget(slider)
        emitted = []
        slider.doubleClicked.connect(lambda: emitted.append(True))
        # Act
        slider.mouseDoubleClickEvent(None)
        # Assert
        assert emitted == [True]
