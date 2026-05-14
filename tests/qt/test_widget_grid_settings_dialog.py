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

"""Widget tests for src/ui/widgets/grid_settings_dialog.py."""

import pytest
from pytestqt.plugin import QtBot

from src.ui.widgets.grid_settings_dialog import GridSettingsDialog
from src.ui.widgets.grid_types import GRID_TYPE_3X3, GRID_TYPE_GOLDEN_RATIO, GRID_TYPE_NONE


@pytest.mark.widget
class TestGridSettingsDialogInit:
    """
    Test Design Specification: GridSettingsDialog — Initialization
    Module under test: src/ui/widgets/grid_settings_dialog.py

    Widget base class: QFrame (Popup | FramelessWindowHint window flags)

    Contract:
        GridSettingsDialog is a floating overlay panel for configuring grid overlay settings.
        On construction it builds a line-width control (label + decrease/increase buttons) and a
        QListWidget populated from GRID_TYPES. It stores the supplied current_width and
        current_grid_type, pre-selects the matching list row when the type is known, and
        enables/disables the buttons to enforce MIN_LINE_WIDTH and MAX_LINE_WIDTH constraints.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - No file IO or external services.

    What is tested:
        - Widget is created without raising an exception.
        - Default line width (4) and custom line width are stored and displayed correctly.
        - Default grid type (GRID_TYPE_3X3) and custom grid type are stored correctly.
        - An unknown grid type is stored without raising an exception.
        - Grid list contains one entry per GRID_TYPES definition.
        - Button enable/disable states reflect width constraints at MIN, MAX, and default.

    What is NOT tested:
        - Visual appearance, colours, pixel positions, or font sizes.
        - QPainter or rendered frame content.
        - Fixed-size geometry (headless offscreen constraint).
        - Downstream rendering behaviour for an unknown grid type: GridSettingsDialog stores
          any string supplied to the constructor; how grid_overlay or other consumers handle
          an unrecognized type string is an integration concern out of scope for this file.

    Equivalence partitions:
        EP1  current_width in (MIN, MAX)     → both buttons enabled
        EP2  current_width = MIN_LINE_WIDTH  → decrease button disabled
        EP3  current_width = MAX_LINE_WIDTH  → increase button disabled
        EP4  current_grid_type = known type  → stored, list row pre-selected
        EP5  current_grid_type = unknown     → stored, list row not pre-selected

    Boundary values:
        BV1  current_width = MIN_LINE_WIDTH (1)
        BV2  current_width = MAX_LINE_WIDTH (10)

    Mocking strategy:
        No external dependencies require mocking.

    Constraints:
        - The Popup window flag is retained from the production widget; the offscreen
          platform handles it without requiring a physical display.
    """

    def test_initialization_creates_dialog_without_error(self, qtbot: QtBot) -> None:
        """
        Given no constructor arguments,
        When GridSettingsDialog is instantiated,
        Then the dialog object is created without raising an exception.
        """
        # Arrange + Act
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Assert
        assert dialog is not None

    def test_initialization_default_line_width_is_four(self, qtbot: QtBot) -> None:
        """
        Given no width argument,
        When GridSettingsDialog is instantiated,
        Then get_current_line_width returns 4.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act
        width = dialog.get_current_line_width()
        # Assert
        assert width == 4

    def test_initialization_default_grid_type_is_3x3(self, qtbot: QtBot) -> None:
        """
        Given no grid_type argument,
        When GridSettingsDialog is instantiated,
        Then get_current_grid_type returns GRID_TYPE_3X3.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act
        grid_type = dialog.get_current_grid_type()
        # Assert
        assert grid_type == GRID_TYPE_3X3

    def test_initialization_width_display_shows_default_width(self, qtbot: QtBot) -> None:
        """
        Given the default line width of 4,
        When GridSettingsDialog is instantiated,
        Then the width_display label text is "4".
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.width_display.text() == "4"

    def test_initialization_grid_list_has_correct_item_count(self, qtbot: QtBot) -> None:
        """
        Given the GRID_TYPES class attribute with N entries,
        When GridSettingsDialog is instantiated,
        Then the grid list widget contains exactly N items.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.grid_list.count() == len(GridSettingsDialog.GRID_TYPES)

    def test_initialization_with_custom_width_stores_supplied_value(self, qtbot: QtBot) -> None:
        """
        Given current_width=7,
        When GridSettingsDialog is instantiated,
        Then get_current_line_width returns 7.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=7)
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.get_current_line_width() == 7

    def test_initialization_with_custom_grid_type_stores_supplied_value(self, qtbot: QtBot) -> None:
        """
        Given current_grid_type=GRID_TYPE_GOLDEN_RATIO (EP4),
        When GridSettingsDialog is instantiated,
        Then get_current_grid_type returns GRID_TYPE_GOLDEN_RATIO.
        """
        # Arrange
        dialog = GridSettingsDialog(current_grid_type=GRID_TYPE_GOLDEN_RATIO)
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.get_current_grid_type() == GRID_TYPE_GOLDEN_RATIO

    def test_initialization_with_unknown_grid_type_stores_supplied_value(self, qtbot: QtBot) -> None:
        """
        Given current_grid_type="unknown_type" not present in GRID_TYPES (EP5),
        When GridSettingsDialog is instantiated,
        Then get_current_grid_type returns the supplied unknown value.
        """
        # Arrange
        dialog = GridSettingsDialog(current_grid_type="unknown_type")
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.get_current_grid_type() == "unknown_type"

    def test_initialization_decrease_button_disabled_at_minimum_width(self, qtbot: QtBot) -> None:
        """
        Given current_width=MIN_LINE_WIDTH (BV1, EP2),
        When GridSettingsDialog is instantiated,
        Then the decrease button is disabled.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MIN_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.decrease_btn.isEnabled() is False

    def test_initialization_increase_button_disabled_at_maximum_width(self, qtbot: QtBot) -> None:
        """
        Given current_width=MAX_LINE_WIDTH (BV2, EP3),
        When GridSettingsDialog is instantiated,
        Then the increase button is disabled.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MAX_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.increase_btn.isEnabled() is False

    def test_initialization_both_buttons_enabled_at_default_width(self, qtbot: QtBot) -> None:
        """
        Given default current_width=4 (EP1: strictly between MIN and MAX),
        When GridSettingsDialog is instantiated,
        Then both decrease and increase buttons are enabled.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act + Assert
        assert dialog.decrease_btn.isEnabled() is True
        assert dialog.increase_btn.isEnabled() is True


@pytest.mark.widget
class TestGridSettingsDialogLineWidth:
    """
    Test Design Specification: GridSettingsDialog — Line Width Controls
    Module under test: src/ui/widgets/grid_settings_dialog.py

    Widget base class: QFrame

    Contract:
        _decrease_width and _increase_width adjust the stored line width by 1, clamped
        to [MIN_LINE_WIDTH, MAX_LINE_WIDTH]. Each successful change updates width_display,
        refreshes button enable/disable states, and emits line_width_changed with the new
        value. At the boundaries the operation is a no-op and the signal is not emitted.

    Infrastructure:
        - Requires qtbot fixture.
        - QT_QPA_PLATFORM=offscreen.

    What is tested:
        - Decrease reduces width by 1 and updates the display label.
        - Increase raises width by 1 and updates the display label.
        - Both operations emit line_width_changed on success.
        - Decrease at MIN_LINE_WIDTH is a no-op; signal is not emitted.
        - Increase at MAX_LINE_WIDTH is a no-op; signal is not emitted.
        - Button states are updated correctly after each change.

    What is NOT tested:
        - Visual appearance of buttons or the display label.

    Equivalence partitions:
        EP1  width in (MIN, MAX)    → operation succeeds, signal emitted
        EP2  width = MIN (1)        → decrease is a no-op, no signal
        EP3  width = MAX (10)       → increase is a no-op, no signal

    Boundary values:
        BV1  current_width = MIN_LINE_WIDTH (1)
        BV2  current_width = MIN_LINE_WIDTH + 1 (2) — just above min; decrease succeeds
        BV3  current_width = MAX_LINE_WIDTH (10)
        BV4  current_width = MAX_LINE_WIDTH - 1 (9) — just below max; increase succeeds

    Mocking strategy:
        No external dependencies require mocking.

    Constraints:
        - _decrease_width() and _increase_width() are invoked directly rather than via
          button click simulation because the Popup-flagged QFrame requires a visible
          window for mouse event routing in offscreen mode.
    """

    def test_decrease_reduces_width_by_one(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=4 (EP1),
        When _decrease_width is called,
        Then get_current_line_width returns 3.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=4)
        qtbot.addWidget(dialog)
        # Act
        dialog._decrease_width()
        # Assert
        assert dialog.get_current_line_width() == 3

    def test_decrease_updates_width_display(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=4,
        When _decrease_width is called,
        Then width_display text is "3".
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=4)
        qtbot.addWidget(dialog)
        # Act
        dialog._decrease_width()
        # Assert
        assert dialog.width_display.text() == "3"

    def test_decrease_emits_line_width_changed(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=4 (EP1),
        When _decrease_width is called,
        Then line_width_changed is emitted exactly once.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=4)
        qtbot.addWidget(dialog)
        # Act + Assert
        with qtbot.waitSignal(dialog.line_width_changed, timeout=1000):
            dialog._decrease_width()

    def test_decrease_at_minimum_is_noop(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=MIN_LINE_WIDTH (BV1, EP2),
        When _decrease_width is called,
        Then get_current_line_width still returns MIN_LINE_WIDTH.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MIN_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act
        dialog._decrease_width()
        # Assert
        assert dialog.get_current_line_width() == GridSettingsDialog.MIN_LINE_WIDTH

    def test_decrease_at_minimum_does_not_emit_signal(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=MIN_LINE_WIDTH (BV1, EP2),
        When _decrease_width is called,
        Then line_width_changed is not emitted.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MIN_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act + Assert
        with qtbot.assertNotEmitted(dialog.line_width_changed):
            dialog._decrease_width()

    def test_decrease_enables_increase_button_when_leaving_maximum(self, qtbot: QtBot) -> None:
        """
        Given a dialog at MAX_LINE_WIDTH with the increase button disabled (BV3),
        When _decrease_width is called,
        Then the increase button becomes enabled.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MAX_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act
        dialog._decrease_width()
        # Assert
        assert dialog.increase_btn.isEnabled() is True

    def test_increase_raises_width_by_one(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=4 (EP1),
        When _increase_width is called,
        Then get_current_line_width returns 5.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=4)
        qtbot.addWidget(dialog)
        # Act
        dialog._increase_width()
        # Assert
        assert dialog.get_current_line_width() == 5

    def test_increase_updates_width_display(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=4,
        When _increase_width is called,
        Then width_display text is "5".
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=4)
        qtbot.addWidget(dialog)
        # Act
        dialog._increase_width()
        # Assert
        assert dialog.width_display.text() == "5"

    def test_increase_emits_line_width_changed(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=4 (EP1),
        When _increase_width is called,
        Then line_width_changed is emitted exactly once.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=4)
        qtbot.addWidget(dialog)
        # Act + Assert
        with qtbot.waitSignal(dialog.line_width_changed, timeout=1000):
            dialog._increase_width()

    def test_increase_at_maximum_is_noop(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=MAX_LINE_WIDTH (BV3, EP3),
        When _increase_width is called,
        Then get_current_line_width still returns MAX_LINE_WIDTH.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MAX_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act
        dialog._increase_width()
        # Assert
        assert dialog.get_current_line_width() == GridSettingsDialog.MAX_LINE_WIDTH

    def test_increase_at_maximum_does_not_emit_signal(self, qtbot: QtBot) -> None:
        """
        Given a dialog with current_width=MAX_LINE_WIDTH (BV3, EP3),
        When _increase_width is called,
        Then line_width_changed is not emitted.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MAX_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act + Assert
        with qtbot.assertNotEmitted(dialog.line_width_changed):
            dialog._increase_width()

    def test_increase_enables_decrease_button_when_leaving_minimum(self, qtbot: QtBot) -> None:
        """
        Given a dialog at MIN_LINE_WIDTH with the decrease button disabled (BV1),
        When _increase_width is called,
        Then the decrease button becomes enabled.
        """
        # Arrange
        dialog = GridSettingsDialog(current_width=GridSettingsDialog.MIN_LINE_WIDTH)
        qtbot.addWidget(dialog)
        # Act
        dialog._increase_width()
        # Assert
        assert dialog.decrease_btn.isEnabled() is True


@pytest.mark.widget
class TestGridSettingsDialogGridType:
    """
    Test Design Specification: GridSettingsDialog — Grid Type Selection
    Module under test: src/ui/widgets/grid_settings_dialog.py

    Widget base class: QFrame

    Contract:
        When the user selects a row in the QListWidget, _on_grid_type_changed is triggered
        via the currentRowChanged signal. It resolves the grid type value through
        _get_grid_type_value and emits grid_type_changed with that value. For out-of-bounds
        row indices (including -1), _get_grid_type_value returns GRID_TYPE_NONE.
        get_current_grid_type and get_current_line_width expose the stored state.

    Infrastructure:
        - Requires qtbot fixture.
        - QT_QPA_PLATFORM=offscreen.

    What is tested:
        - Changing the selected row updates _current_grid_type via the signal chain.
        - Changing the selected row emits grid_type_changed.
        - _get_grid_type_value with an out-of-bounds positive index returns GRID_TYPE_NONE.
        - _get_grid_type_value with a negative index returns GRID_TYPE_NONE.
        - _on_grid_type_changed called with row=-1 sets _current_grid_type to GRID_TYPE_NONE.

    What is NOT tested:
        - Visual highlighting of the selected list row.
        - Scroll position of the list widget.

    Equivalence partitions:
        EP1  row in [0, len(GRID_TYPES)-1]  → valid grid type returned and stored
        EP2  row < 0                         → GRID_TYPE_NONE returned
        EP3  row >= len(GRID_TYPES)          → GRID_TYPE_NONE returned

    Boundary values:
        BV1  row = 0                          (first valid row)
        BV2  row = len(GRID_TYPES) - 1       (last valid row)
        BV3  row = len(GRID_TYPES)           (first out-of-bounds)
        BV4  row = -1                        (below-zero sentinel)

    Mocking strategy:
        No external dependencies require mocking.

    Constraints:
        - currentRowChanged is connected AFTER setCurrentRow in _init_ui, so
          initialization does not trigger _on_grid_type_changed.
        - Tests change away from the default selection (3X3, row 1) to ensure
          currentRowChanged actually fires.
    """

    def test_selecting_different_row_updates_current_grid_type(self, qtbot: QtBot) -> None:
        """
        Given a dialog initialized with GRID_TYPE_3X3 at row 1 (EP1),
        When the grid list current row is set to the GRID_TYPE_NONE row (0),
        Then get_current_grid_type returns GRID_TYPE_NONE.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        none_row = next(i for i, (_, v) in enumerate(GridSettingsDialog.GRID_TYPES) if v == GRID_TYPE_NONE)
        # Act
        dialog.grid_list.setCurrentRow(none_row)
        # Assert
        assert dialog.get_current_grid_type() == GRID_TYPE_NONE

    def test_selecting_different_row_emits_grid_type_changed(self, qtbot: QtBot) -> None:
        """
        Given a dialog initialized with GRID_TYPE_3X3 at row 1,
        When the grid list current row is changed to a different row,
        Then grid_type_changed is emitted.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        none_row = next(i for i, (_, v) in enumerate(GridSettingsDialog.GRID_TYPES) if v == GRID_TYPE_NONE)
        # Act + Assert
        with qtbot.waitSignal(dialog.grid_type_changed, timeout=1000):
            dialog.grid_list.setCurrentRow(none_row)

    def test_get_grid_type_value_with_out_of_bounds_index_returns_none_type(self, qtbot: QtBot) -> None:
        """
        Given a dialog (EP3, BV3),
        When _get_grid_type_value is called with index == len(GRID_TYPES),
        Then GRID_TYPE_NONE is returned.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act
        result = dialog._get_grid_type_value(len(GridSettingsDialog.GRID_TYPES))
        # Assert
        assert result == GRID_TYPE_NONE

    def test_get_grid_type_value_with_negative_index_returns_none_type(self, qtbot: QtBot) -> None:
        """
        Given a dialog (EP2, BV4),
        When _get_grid_type_value is called with index -1,
        Then GRID_TYPE_NONE is returned.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act
        result = dialog._get_grid_type_value(-1)
        # Assert
        assert result == GRID_TYPE_NONE

    def test_on_grid_type_changed_with_negative_row_stores_none_type(self, qtbot: QtBot) -> None:
        """
        Given a dialog initialized with GRID_TYPE_3X3 (EP2, BV4),
        When _on_grid_type_changed is called directly with row=-1,
        Then get_current_grid_type returns GRID_TYPE_NONE.
        """
        # Arrange
        dialog = GridSettingsDialog()
        qtbot.addWidget(dialog)
        # Act
        dialog._on_grid_type_changed(-1)
        # Assert
        assert dialog.get_current_grid_type() == GRID_TYPE_NONE
