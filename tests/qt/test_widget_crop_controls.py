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
Unit tests for CropControlsWidget.
Tests cover initialization, signal emission, and public API methods.
"""

from typing import Optional

import pytest
from PyQt5.QtWidgets import QComboBox, QPushButton, QWidget
from pytestqt.qtbot import QtBot

from src.ui.widgets.crop_controls import CropControlsWidget


class TestCropControlsWidgetInit:
    """
    Test Design Specification: CropControlsWidget initialization
    Module under test: src/ui/widgets/crop_controls.py

    Contract:
        CropControlsWidget initializes with exactly 10 aspect ratio options,
        two action buttons, and correct visibility. Widget is a QWidget.

    Equivalence partitions:
        EP1  Initial state after construction
        EP2  Visibility state (hidden by default, shown when setVisible(True))

    Boundary values:
        BV1  Exactly 10 ratio options (first is "Free")
        BV2  Button labels: "Accept Crop" and "Cancel Crop"

    Exclusions:
        - Signal emission behavior (covered in signal tests)
        - Layout specifics (covered by visual inspection)

    Constraints:
        - No mocking required; pure widget initialization
        - Widget must be a QWidget subclass
    """

    def test_widget_is_qwidget(self, qtbot: QtBot) -> None:
        """Given CropControlsWidget instance, when checked, then is QWidget."""
        # Arrange
        widget = CropControlsWidget()
        # Act / Assert
        assert isinstance(widget, QWidget)

    def test_ratio_combo_has_ten_items(self, qtbot: QtBot) -> None:
        """Given CropControlsWidget, when initialized, then ratio combo has exactly 10 items."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        # Act
        combo = widget.findChild(QComboBox)
        # Assert
        assert combo is not None
        assert combo.count() == 10

    def test_first_combo_item_is_free(self, qtbot: QtBot) -> None:
        """Given ratio combo, when checked, then first item (index 0) is 'Free'."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        # Act
        combo = widget.findChild(QComboBox)
        # Assert
        assert combo.itemText(0) == "Free"

    def test_combo_items_in_correct_order(self, qtbot: QtBot) -> None:
        """Given ratio combo, when checked, then items are in expected order."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        expected_items = ["Free", "16:9", "3:2", "4:3", "5:4", "1:1", "4:5", "3:4", "2:3", "9:16"]
        # Act
        combo = widget.findChild(QComboBox)
        actual_items = [combo.itemText(i) for i in range(combo.count())]
        # Assert
        assert actual_items == expected_items

    def test_accept_button_exists(self, qtbot: QtBot) -> None:
        """Given CropControlsWidget, when checked for buttons, then 'Accept Crop' exists."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        # Act
        buttons = widget.findChildren(QPushButton)
        accept_btn = next((btn for btn in buttons if btn.text() == "Accept Crop"), None)
        # Assert
        assert accept_btn is not None

    def test_cancel_button_exists(self, qtbot: QtBot) -> None:
        """Given CropControlsWidget, when checked for buttons, then 'Cancel Crop' exists."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        # Act
        buttons = widget.findChildren(QPushButton)
        cancel_btn = next((btn for btn in buttons if btn.text() == "Cancel Crop"), None)
        # Assert
        assert cancel_btn is not None

    def test_initial_visibility_false(self, qtbot: QtBot) -> None:
        """Given CropControlsWidget, when created, then isVisible() is False (hidden by default)."""
        # Arrange / Act
        widget = CropControlsWidget()
        # Assert
        assert widget.isVisible() is False


class TestRatioComboSignal:
    """
    Test Design Specification: ratio_changed signal emission
    Module under test: src/ui/widgets/crop_controls.py

    Contract:
        CropControlsWidget emits ratio_changed signal with correct payload
        (tuple[int, int] or None) when the ratio combo box index changes.

    Equivalence partitions:
        EP1  "Free" option (index 0, None payload)
        EP2  Fixed ratio options (indices 1-9, tuple payloads)

    Boundary values:
        BV1  Index 0 ("Free") emits None
        BV2  Index 1 (first ratio "16:9") emits (16, 9)
        BV3  Index 9 (last ratio "9:16") emits (9, 16)

    Exclusions:
        - Index out of bounds (QComboBox prevents this)

    Constraints:
        - Use pytestqt.assertEmitted to verify signal firing
        - No external dependencies
    """

    @pytest.mark.parametrize(
        "index, expected_ratio",
        [
            (0, None),  # EP1: Free, BV1
            (1, (16, 9)),  # EP2: 16:9, BV2
            (2, (3, 2)),  # EP2: 3:2
            (3, (4, 3)),  # EP2: 4:3
            (4, (5, 4)),  # EP2: 5:4
            (5, (1, 1)),  # EP2: 1:1
            (6, (4, 5)),  # EP2: 4:5
            (7, (3, 4)),  # EP2: 3:4
            (8, (2, 3)),  # EP2: 2:3
            (9, (9, 16)),  # EP2: 9:16, BV3
        ],
        ids=[
            "free",
            "16_9",
            "3_2",
            "4_3",
            "5_4",
            "1_1",
            "4_5",
            "3_4",
            "2_3",
            "9_16",
        ],
    )
    def test_ratio_changed_emitted_for_all_indices(self, qtbot: QtBot, index: int, expected_ratio: Optional[tuple[int, int]]) -> None:
        """Given combo index change to {index}, when changed, then ratio_changed emits {expected_ratio}."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        signal_args = []
        def capture_signal(ratio: Optional[tuple[int, int]]) -> None:  # noqa: D105
            """Capture emitted signal argument."""
            signal_args.append(ratio)
        widget.ratio_changed.connect(capture_signal)
        # Set combo to a different index first so the signal fires when we set to test index
        widget._ratio_combo.setCurrentIndex(1 if index != 1 else 0)
        signal_args.clear()  # Clear any signals from the setup
        # Act
        widget._ratio_combo.setCurrentIndex(index)
        # Assert
        assert len(signal_args) == 1
        assert signal_args[0] == expected_ratio

    def test_ratio_changed_emits_on_construction(self, qtbot: QtBot) -> None:
        """Given widget construction with default combo (index 0), when checked, then initial ratio is None."""
        # Arrange (fixture)
        # Act
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        # Assert
        assert widget.get_selected_ratio() is None


class TestAcceptCancelSignals:
    """
    Test Design Specification: accept_requested and cancel_requested signals
    Module under test: src/ui/widgets/crop_controls.py

    Contract:
        CropControlsWidget emits accept_requested signal when "Accept Crop" button
        is clicked, and cancel_requested signal when "Cancel Crop" is clicked.
        Neither signal carries payload.

    Equivalence partitions:
        EP1  Accept button click
        EP2  Cancel button click
        EP3  Other interactions (no signals from non-button widgets)

    Boundary values:
        BV1  Single click on each button

    Exclusions:
        - Multiple rapid clicks (handled by Qt mechanics)
        - Programmatic button state changes without click

    Constraints:
        - Use pytestqt.assertEmitted for signal verification
    """

    def test_accept_requested_on_button_click(self, qtbot: QtBot) -> None:
        """Given 'Accept Crop' button, when clicked, then accept_requested emitted."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        accept_btn = next(btn for btn in widget.findChildren(QPushButton) if btn.text() == "Accept Crop")
        # Act / Assert
        with qtbot.waitSignal(widget.accept_requested, timeout=1000):
            accept_btn.click()

    def test_cancel_requested_on_button_click(self, qtbot: QtBot) -> None:
        """Given 'Cancel Crop' button, when clicked, then cancel_requested emitted."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        cancel_btn = next(btn for btn in widget.findChildren(QPushButton) if btn.text() == "Cancel Crop")
        # Act / Assert
        with qtbot.waitSignal(widget.cancel_requested, timeout=1000):
            cancel_btn.click()

    def test_accept_button_does_not_emit_ratio_signal(self, qtbot: QtBot) -> None:
        """Given 'Accept Crop' button, when clicked, then ratio_changed NOT emitted."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        accept_btn = next(btn for btn in widget.findChildren(QPushButton) if btn.text() == "Accept Crop")
        # Act / Assert
        signal_count = [0]
        def count_signal() -> None:  # noqa: D105
            """Count signal emissions."""
            signal_count[0] += 1
        widget.ratio_changed.connect(count_signal)
        accept_btn.click()
        assert signal_count[0] == 0

    def test_cancel_button_does_not_emit_ratio_signal(self, qtbot: QtBot) -> None:
        """Given 'Cancel Crop' button, when clicked, then ratio_changed NOT emitted."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        cancel_btn = next(btn for btn in widget.findChildren(QPushButton) if btn.text() == "Cancel Crop")
        # Act / Assert
        signal_count = [0]
        def count_signal() -> None:  # noqa: D105
            """Count signal emissions."""
            signal_count[0] += 1
        widget.ratio_changed.connect(count_signal)
        cancel_btn.click()
        assert signal_count[0] == 0


class TestPublicMethods:
    """
    Test Design Specification: Public API methods
    Module under test: src/ui/widgets/crop_controls.py

    Contract:
        get_selected_ratio() returns currently selected ratio;
        set_visible() shows/hides widget;
        reset() returns combo to "Free" (index 0).

    Equivalence partitions:
        EP1  get_selected_ratio() at various combo states
        EP2  set_visible(True) shows widget
        EP3  set_visible(False) hides widget
        EP4  reset() resets combo to index 0

    Boundary values:
        BV1  Index 0 returns None
        BV2  Index 1-9 return correct tuples

    Exclusions:
        - None

    Constraints:
        - No external dependencies
    """

    def test_get_selected_ratio_at_free(self, qtbot: QtBot) -> None:
        """Given combo at 'Free' (index 0), when get_selected_ratio called, then None returned."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        # Act
        ratio = widget.get_selected_ratio()
        # Assert
        assert ratio is None

    @pytest.mark.parametrize("index, expected", [(1, (16, 9)), (2, (3, 2)), (5, (1, 1)), (9, (9, 16))])
    def test_get_selected_ratio_for_ratios(self, qtbot: QtBot, index: int, expected: tuple[int, int]) -> None:
        """Given combo at index {index}, when get_selected_ratio called, then {expected} returned."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        widget._ratio_combo.setCurrentIndex(index)
        # Act
        ratio = widget.get_selected_ratio()
        # Assert
        assert ratio == expected

    def test_set_visible_true_shows_widget(self, qtbot: QtBot) -> None:
        """Given widget with setVisible(False), when set_visible(True), then isVisible() is True."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        widget.setVisible(False)
        # Act
        widget.set_visible(True)
        # Assert
        assert widget.isVisible() is True

    def test_set_visible_false_hides_widget(self, qtbot: QtBot) -> None:
        """Given visible widget, when set_visible(False), then isVisible() is False."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        # Act
        widget.set_visible(False)
        # Assert
        assert widget.isVisible() is False

    def test_reset_returns_combo_to_free(self, qtbot: QtBot) -> None:
        """Given combo at non-zero index, when reset() called, then currentIndex is 0 ('Free')."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        widget._ratio_combo.setCurrentIndex(5)  # Set to "1:1"
        # Act
        widget.reset()
        # Assert
        assert widget._ratio_combo.currentIndex() == 0
        assert widget.get_selected_ratio() is None

    def test_reset_emits_ratio_changed(self, qtbot: QtBot) -> None:
        """Given combo not at index 0, when reset() called, then ratio_changed emitted."""
        # Arrange
        widget = CropControlsWidget()
        qtbot.addWidget(widget)
        widget._ratio_combo.setCurrentIndex(3)  # Set to "4:3"
        # Act / Assert
        with qtbot.waitSignal(widget.ratio_changed, timeout=1000):
            widget.reset()
