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

"""Widget tests for src/ui/widgets/grid_overlay.py."""

from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QRect, QRectF, Qt
from PyQt5.QtGui import QColor, QPen
from pytestqt.plugin import QtBot

from src.ui.widgets.grid_overlay import GridOverlay
from src.ui.widgets.grid_types import (
    GRID_TYPE_3X3,
    GRID_TYPE_DIAGONAL_1_1,
    GRID_TYPE_DIAGONAL_2_3,
    GRID_TYPE_DIAGONAL_3_2,
    GRID_TYPE_DIAGONAL_3_4,
    GRID_TYPE_DIAGONAL_4_3,
    GRID_TYPE_DIAGONAL_GOLDEN_H,
    GRID_TYPE_DIAGONAL_GOLDEN_V,
    GRID_TYPE_DIAGONAL_THIRDS_H,
    GRID_TYPE_DIAGONAL_THIRDS_V,
    GRID_TYPE_GOLDEN_RATIO,
)


@pytest.mark.widget
class TestGridOverlayInit:
    """
    Test Design Specification: GridOverlay — Initialization
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget). Uses Qt types.

    Contract:
        GridOverlay manages and draws composition grid overlays on images. It
        maintains state (enabled flag, colour, line width, opacity, grid type) and
        delegates all painting to a QPainter passed into draw_grid(). On construction
        the overlay is enabled, white, semi-transparent (opacity=128), 4 pixels wide,
        and uses the 3×3 rule-of-thirds grid.

    Infrastructure:
        - Requires qtbot fixture (QApplication must be running for QColor construction).
        - Requires QT_QPA_PLATFORM=offscreen.
        - No service or file IO dependencies.
        - GridOverlay is NOT a QWidget — qtbot.addWidget() is never called.

    What is tested:
        - Default enabled state, grid type, opacity, line width, and colour.

    What is NOT tested:
        - Visual rendering or pixel output.
        - QPainter rendering on a real paint device.

    Equivalence partitions:
        EP1  Fresh GridOverlay instance → all default values as specified.

    Boundary values:
        BV1  opacity = 128  (mid-range default)
        BV2  line_width = 4  (default)

    Mocking strategy:
        None for init tests.

    Constraints:
        QApplication must be running (provided by qtbot) for QColor("white").
    """

    def test_default_enabled_is_true(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed GridOverlay,
        When is_enabled() is called,
        Then it returns True.
        """
        # Arrange / Act
        overlay = GridOverlay()
        # Assert
        assert overlay.is_enabled() is True

    def test_default_grid_type_is_3x3(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed GridOverlay,
        When get_grid_type() is called,
        Then it returns GRID_TYPE_3X3.
        """
        # Arrange / Act
        overlay = GridOverlay()
        # Assert
        assert overlay.get_grid_type() == GRID_TYPE_3X3

    def test_default_opacity_is_128(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed GridOverlay,
        When the _opacity attribute is read,
        Then it equals 128 (semi-transparent default).
        """
        # Arrange / Act
        overlay = GridOverlay()
        # Assert
        assert overlay._opacity == 128  # pylint: disable=protected-access

    def test_default_line_width_is_4(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed GridOverlay,
        When get_line_width() is called,
        Then it returns 4.
        """
        # Arrange / Act
        overlay = GridOverlay()
        # Assert
        assert overlay.get_line_width() == 4

    def test_default_color_is_white(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed GridOverlay,
        When the _color attribute is read,
        Then it represents white.
        """
        # Arrange / Act
        overlay = GridOverlay()
        # Assert
        assert overlay._color == QColor("white")  # pylint: disable=protected-access


@pytest.mark.widget
class TestGridOverlayStateSetters:
    """
    Test Design Specification: GridOverlay — State Setters and Getters
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        The public setters (set_enabled, set_grid_type, set_color, set_line_width,
        set_opacity) mutate internal state. set_grid_type raises ValueError for
        unrecognised type strings. set_opacity clamps the input to [0, 255].

    Infrastructure:
        - Requires qtbot for QApplication (QColor construction).
        - No IO or service dependencies.

    What is tested:
        - set_enabled(False/True) ↔ is_enabled() round-trip.
        - set_grid_type with all valid type constants → get_grid_type() matches.
        - set_grid_type with unknown string → ValueError.
        - set_color → stored colour matches.
        - set_line_width → get_line_width() matches.
        - set_opacity at 0 (min), 255 (max), above max (clamped), below min (clamped).

    What is NOT tested:
        - Visual appearance.

    Equivalence partitions:
        EP1  enabled = False    → is_enabled() returns False
        EP2  enabled = True     → is_enabled() returns True
        EP3  grid_type = valid  → stored without error
        EP4  grid_type = invalid → ValueError raised
        EP5  opacity in [0, 255] → stored as-is
        EP6  opacity > 255       → clamped to 255
        EP7  opacity < 0         → clamped to 0

    Boundary values:
        BV1  opacity = 0    (lower bound)
        BV2  opacity = 255  (upper bound)
        BV3  opacity = 256  (one above upper bound)
        BV4  opacity = -1   (one below lower bound)

    Mocking strategy:
        None.

    Constraints:
        QApplication must be running for QColor construction.
    """

    def test_set_enabled_false_returns_false(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay (enabled by default),
        When set_enabled(False) is called,
        Then is_enabled() returns False.
        """
        # Arrange
        overlay = GridOverlay()
        # Act
        overlay.set_enabled(False)
        # Assert
        assert overlay.is_enabled() is False

    def test_set_enabled_true_returns_true(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay with enabled=False,
        When set_enabled(True) is called,
        Then is_enabled() returns True.
        """
        # Arrange
        overlay = GridOverlay()
        overlay.set_enabled(False)
        # Act
        overlay.set_enabled(True)
        # Assert
        assert overlay.is_enabled() is True

    @pytest.mark.parametrize(
        "grid_type",
        [
            GRID_TYPE_3X3,
            GRID_TYPE_GOLDEN_RATIO,
            GRID_TYPE_DIAGONAL_1_1,
            GRID_TYPE_DIAGONAL_2_3,
            GRID_TYPE_DIAGONAL_3_2,
            GRID_TYPE_DIAGONAL_3_4,
            GRID_TYPE_DIAGONAL_4_3,
            GRID_TYPE_DIAGONAL_THIRDS_V,
            GRID_TYPE_DIAGONAL_THIRDS_H,
            GRID_TYPE_DIAGONAL_GOLDEN_V,
            GRID_TYPE_DIAGONAL_GOLDEN_H,
        ],
        ids=[
            "3x3",
            "golden_ratio",
            "diagonal_1_1",
            "diagonal_2_3",
            "diagonal_3_2",
            "diagonal_3_4",
            "diagonal_4_3",
            "diagonal_thirds_v",
            "diagonal_thirds_h",
            "diagonal_golden_v",
            "diagonal_golden_h",
        ],
    )
    def test_set_grid_type_stores_valid_type(self, qtbot: QtBot, grid_type: str) -> None:
        """
        Given a GridOverlay,
        When set_grid_type is called with a recognised type constant,
        Then get_grid_type() returns that type.
        """
        # Arrange
        overlay = GridOverlay()
        # Act
        overlay.set_grid_type(grid_type)
        # Assert
        assert overlay.get_grid_type() == grid_type

    def test_set_grid_type_invalid_raises_value_error(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When set_grid_type is called with an unknown string,
        Then a ValueError is raised.
        """
        # Arrange
        overlay = GridOverlay()
        # Act / Assert
        with pytest.raises(ValueError):
            overlay.set_grid_type("nonexistent_grid_type")

    def test_set_color_stores_color(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When set_color is called with QColor("red"),
        Then the internal _color equals QColor("red").
        """
        # Arrange
        overlay = GridOverlay()
        red = QColor("red")
        # Act
        overlay.set_color(red)
        # Assert
        assert overlay._color == red  # pylint: disable=protected-access

    def test_set_line_width_stores_width(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When set_line_width(2) is called,
        Then get_line_width() returns 2.
        """
        # Arrange
        overlay = GridOverlay()
        # Act
        overlay.set_line_width(2)
        # Assert
        assert overlay.get_line_width() == 2

    def test_set_opacity_at_minimum_stores_zero(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When set_opacity(0) is called,
        Then _opacity is 0 (lower boundary, EP5 + BV1).
        """
        # Arrange
        overlay = GridOverlay()
        # Act
        overlay.set_opacity(0)
        # Assert
        assert overlay._opacity == 0  # pylint: disable=protected-access

    def test_set_opacity_at_maximum_stores_255(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When set_opacity(255) is called,
        Then _opacity is 255 (upper boundary, EP5 + BV2).
        """
        # Arrange
        overlay = GridOverlay()
        # Act
        overlay.set_opacity(255)
        # Assert
        assert overlay._opacity == 255  # pylint: disable=protected-access

    def test_set_opacity_above_maximum_is_clamped_to_255(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When set_opacity(300) is called (one-above-max region, EP6 + BV3),
        Then _opacity is clamped to 255.
        """
        # Arrange
        overlay = GridOverlay()
        # Act
        overlay.set_opacity(300)
        # Assert
        assert overlay._opacity == 255  # pylint: disable=protected-access

    def test_set_opacity_below_minimum_is_clamped_to_zero(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When set_opacity(-1) is called (below-min region, EP7 + BV4),
        Then _opacity is clamped to 0.
        """
        # Arrange
        overlay = GridOverlay()
        # Act
        overlay.set_opacity(-1)
        # Assert
        assert overlay._opacity == 0  # pylint: disable=protected-access


@pytest.mark.widget
class TestGridOverlayDrawGrid:
    """
    Test Design Specification: GridOverlay — draw_grid Early-Exit and Infrastructure
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        draw_grid(painter, rect) is the entry point for all rendering. It guards
        against three early-exit conditions: overlay disabled, rect width ≤ 0,
        rect height ≤ 0. When rendering proceeds, it saves painter state, configures
        the pen, dispatches to the appropriate private method, and restores state.
        A QRect input is automatically promoted to QRectF. An unknown _grid_type
        falls back silently to _draw_3x3_grid.

    Infrastructure:
        - Requires qtbot for QApplication (QPen, QColor construction inside draw_grid).
        - QPainter replaced with MagicMock — no real paint device needed.
        - GridOverlay is NOT a QWidget — qtbot.addWidget() never called.

    What is tested:
        - draw_grid with enabled=False → painter.drawLine never called.
        - draw_grid with zero-width rect → painter.drawLine never called.
        - draw_grid with zero-height rect → painter.drawLine never called.
        - draw_grid with negative-width rect → painter.drawLine never called.
        - draw_grid saves and restores painter state.
        - draw_grid with QRect (not QRectF) → successfully draws (conversion branch).
        - draw_grid with unknown _grid_type set directly → falls back to 3×3 (4 lines).

    What is NOT tested:
        - Exact pixel coordinates in this class (covered by grid-specific classes).
        - Pen colour values or alpha application.

    Equivalence partitions:
        EP1  enabled=False         → no drawing
        EP2  rect.width() = 0      → no drawing
        EP3  rect.height() = 0     → no drawing
        EP4  rect.width() < 0      → no drawing
        EP5  enabled=True, valid rect → drawing proceeds

    Boundary values:
        BV1  rect.width() = 0  (boundary: invalid)
        BV2  rect.width() = 1  (boundary: valid)

    Mocking strategy:
        QPainter replaced with MagicMock. All painter method calls are absorbed silently.

    Constraints:
        QApplication must be running for QColor and QPen construction inside draw_grid.
    """

    def test_draw_grid_when_disabled_does_not_call_draw_line(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay with enabled=False,
        When draw_grid is called with a valid rect,
        Then painter.drawLine is never called (EP1).
        """
        # Arrange
        overlay = GridOverlay()
        overlay.set_enabled(False)
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 0

    def test_draw_grid_with_zero_width_rect_does_not_draw(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay,
        When draw_grid is called with a rect of width=0 (BV1),
        Then painter.drawLine is never called (EP2).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 0, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 0

    def test_draw_grid_with_zero_height_rect_does_not_draw(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay,
        When draw_grid is called with a rect of height=0 (EP3),
        Then painter.drawLine is never called.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 0)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 0

    def test_draw_grid_with_negative_width_rect_does_not_draw(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay,
        When draw_grid is called with a rect of negative width (EP4),
        Then painter.drawLine is never called.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, -100, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 0

    def test_draw_grid_saves_and_restores_painter_state(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay with a valid rect,
        When draw_grid is called,
        Then painter.save() and painter.restore() are each called exactly once.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.save.call_count == 1
        assert mock_painter.restore.call_count == 1

    def test_draw_grid_with_qrect_input_draws_successfully(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay (default 3×3),
        When draw_grid is called with a QRect (not QRectF),
        Then painter.drawLine is called 4 times (QRect→QRectF conversion branch).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRect(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 4

    def test_draw_grid_unknown_type_falls_back_to_3x3(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay whose _grid_type is set to an unknown value,
        When draw_grid is called with a valid rect,
        Then it falls back to _draw_3x3_grid and calls painter.drawLine 4 times.
        """
        # Arrange
        overlay = GridOverlay()
        overlay._grid_type = "unknown_type"  # pylint: disable=protected-access
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 4


@pytest.mark.widget
class TestGridOverlay3x3Grid:
    """
    Test Design Specification: GridOverlay — _draw_3x3_grid
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        _draw_3x3_grid(painter, rect) draws two vertical and two horizontal lines
        at rule-of-thirds positions. For a rect of dimensions W×H at offset (L, T):
          vertical x1 = L + W/3, x2 = L + 2W/3  (truncated to int)
          horizontal y1 = T + H/3, y2 = T + 2H/3 (truncated to int)

    Infrastructure:
        - Requires qtbot for QApplication.
        - QPainter replaced with MagicMock.

    What is tested:
        - Exactly 4 drawLine calls are made.
        - Vertical line 1 at x = W/3 (first and third positional arg equal).
        - Vertical line 2 at x = 2W/3.
        - Horizontal line 1 at y = H/3 (second and fourth positional arg equal).
        - Horizontal line 2 at y = 2H/3.

    What is NOT tested:
        - Pen setup or painter state (covered by TestGridOverlayDrawGrid).
        - Non-zero rect origin (not a specified invariant).

    Equivalence partitions:
        EP1  Square 300×300 at origin → known integer positions.

    Boundary values:
        BV1  width = 300  → x1 = 100, x2 = 200 (exact integer thirds)

    Mocking strategy:
        QPainter replaced with MagicMock. drawLine positional args inspected via
        call_args_list.

    Constraints:
        _draw_3x3_grid is called directly (not via draw_grid) so only drawLine
        calls appear — no save/restore/setPen overhead.
    """

    def test_3x3_draws_four_lines(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When _draw_3x3_grid is called with a mock painter,
        Then painter.drawLine is called exactly 4 times.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_3x3_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        assert mock_painter.drawLine.call_count == 4

    def test_3x3_vertical_line_1_at_one_third_x(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect starting at origin,
        When _draw_3x3_grid is called,
        Then the first drawLine call has x1 = x2 = 100 (300 / 3).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_3x3_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[0][0]  # (x1, y1, x2, y2)
        assert args[0] == 100  # x1
        assert args[2] == 100  # x2 (vertical line — same x)

    def test_3x3_vertical_line_2_at_two_thirds_x(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect starting at origin,
        When _draw_3x3_grid is called,
        Then the second drawLine call has x1 = x2 = 200 (2 * 300 / 3).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_3x3_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[1][0]  # (x1, y1, x2, y2)
        assert args[0] == 200  # x1
        assert args[2] == 200  # x2

    def test_3x3_horizontal_line_1_at_one_third_y(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect starting at origin,
        When _draw_3x3_grid is called,
        Then the third drawLine call has y1 = y2 = 100 (300 / 3).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_3x3_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[2][0]  # (x1, y1, x2, y2)
        assert args[1] == 100  # y1
        assert args[3] == 100  # y2 (horizontal line — same y)

    def test_3x3_horizontal_line_2_at_two_thirds_y(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect starting at origin,
        When _draw_3x3_grid is called,
        Then the fourth drawLine call has y1 = y2 = 200 (2 * 300 / 3).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_3x3_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[3][0]  # (x1, y1, x2, y2)
        assert args[1] == 200  # y1
        assert args[3] == 200  # y2


@pytest.mark.widget
class TestGridOverlayGoldenRatioGrid:
    """
    Test Design Specification: GridOverlay — _draw_golden_ratio_grid
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        _draw_golden_ratio_grid(painter, rect) draws two vertical and two horizontal
        lines at golden-ratio positions (0.382 and 0.618 of the respective dimension).
        Coordinates are truncated to int before calling painter.drawLine.

    Infrastructure:
        - Requires qtbot for QApplication.
        - QPainter replaced with MagicMock.

    What is tested:
        - Exactly 4 drawLine calls.
        - Vertical line 1 at x ≈ int(W * 0.382).
        - Vertical line 2 at x ≈ int(W * 0.618).
        - Horizontal line 1 at y ≈ int(H * 0.382).
        - Horizontal line 2 at y ≈ int(H * 0.618).

    What is NOT tested:
        - Pen or painter state setup.

    Equivalence partitions:
        EP1  Square 300×300 at origin → golden ratio positions at 114, 185.

    Boundary values:
        BV1  width = 300 → int(300 * 0.382) = 114, int(300 * 0.618) = 185

    Mocking strategy:
        QPainter replaced with MagicMock.

    Constraints:
        _draw_golden_ratio_grid is called directly, so only drawLine calls appear.
    """

    def test_golden_ratio_draws_four_lines(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When _draw_golden_ratio_grid is called with a mock painter,
        Then painter.drawLine is called exactly 4 times.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_golden_ratio_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        assert mock_painter.drawLine.call_count == 4

    def test_golden_ratio_vertical_line_1_at_0_382_x(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When _draw_golden_ratio_grid is called,
        Then the first drawLine call has x1 = x2 = int(300 * 0.382) = 114 (BV1).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        expected_x = int(300 * 0.382)  # 114
        # Act
        overlay._draw_golden_ratio_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[0][0]
        assert args[0] == expected_x  # x1
        assert args[2] == expected_x  # x2

    def test_golden_ratio_vertical_line_2_at_0_618_x(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When _draw_golden_ratio_grid is called,
        Then the second drawLine call has x1 = x2 = int(300 * 0.618) = 185 (BV1).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        expected_x = int(300 * 0.618)  # 185
        # Act
        overlay._draw_golden_ratio_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[1][0]
        assert args[0] == expected_x
        assert args[2] == expected_x

    def test_golden_ratio_horizontal_line_1_at_0_382_y(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When _draw_golden_ratio_grid is called,
        Then the third drawLine call has y1 = y2 = int(300 * 0.382) = 114.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        expected_y = int(300 * 0.382)  # 114
        # Act
        overlay._draw_golden_ratio_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[2][0]
        assert args[1] == expected_y  # y1
        assert args[3] == expected_y  # y2

    def test_golden_ratio_horizontal_line_2_at_0_618_y(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When _draw_golden_ratio_grid is called,
        Then the fourth drawLine call has y1 = y2 = int(300 * 0.618) = 185.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        expected_y = int(300 * 0.618)  # 185
        # Act
        overlay._draw_golden_ratio_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        args = mock_painter.drawLine.call_args_list[3][0]
        assert args[1] == expected_y
        assert args[3] == expected_y


@pytest.mark.widget
class TestGridOverlayDiagonal1_1Grid:
    """
    Test Design Specification: GridOverlay — _draw_diagonal_1_1_grid
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        _draw_diagonal_1_1_grid draws four 45-degree diagonal lines from the four
        corners. Each line extends until it hits an adjacent edge. The branch that
        determines which edge is reached first depends on whether width ≤ height
        (hits the far edge in the width direction) or width > height (hits the far
        edge in the height direction).

    Infrastructure:
        - Requires qtbot for QApplication.
        - QPainter replaced with MagicMock.

    What is tested:
        - Square rect (width = height) → 4 drawLine calls (width ≤ height branch).
        - Tall rect (width < height) → 4 drawLine calls (width ≤ height branch).
        - Wide rect (width > height) → 4 drawLine calls (width > height branch).

    What is NOT tested:
        - Exact endpoint coordinates (covered by plan notes as non-critical).

    Equivalence partitions:
        EP1  width < height  → width ≤ height branch for all 4 diagonals
        EP2  width = height  → width ≤ height branch (boundary)
        EP3  width > height  → width > height branch for all 4 diagonals

    Boundary values:
        BV1  width = height = 300  (square, boundary between EP1 and EP3)

    Mocking strategy:
        QPainter replaced with MagicMock.

    Constraints:
        _draw_diagonal_1_1_grid called directly.
    """

    def test_diagonal_1_1_square_draws_four_lines(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a square 300×300 rect (BV1, EP2),
        When _draw_diagonal_1_1_grid is called,
        Then painter.drawLine is called exactly 4 times.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_diagonal_1_1_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        assert mock_painter.drawLine.call_count == 4

    def test_diagonal_1_1_tall_rect_draws_four_lines(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a tall 200×400 rect (EP1: width < height),
        When _draw_diagonal_1_1_grid is called,
        Then painter.drawLine is called exactly 4 times.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 200, 400)
        # Act
        overlay._draw_diagonal_1_1_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        assert mock_painter.drawLine.call_count == 4

    def test_diagonal_1_1_wide_rect_draws_four_lines(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay and a wide 400×300 rect (EP3: width > height),
        When _draw_diagonal_1_1_grid is called,
        Then painter.drawLine is called exactly 4 times.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 400, 300)
        # Act
        overlay._draw_diagonal_1_1_grid(mock_painter, rect)  # pylint: disable=protected-access
        # Assert
        assert mock_painter.drawLine.call_count == 4


@pytest.mark.widget
class TestGridOverlayDiagonalRatioGrids:
    """
    Test Design Specification: GridOverlay — _draw_diagonal_ratio_grid and wrappers
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        _draw_diagonal_ratio_grid(painter, rect, vertical_ratio, horizontal_ratio)
        draws four corner-to-edge diagonals at the given slope. It guards against
        non-positive ratios and returns early without drawing. The four public
        wrappers (_draw_diagonal_2_3_grid etc.) each delegate to this method with
        fixed ratio values.

    Infrastructure:
        - Requires qtbot for QApplication.
        - QPainter replaced with MagicMock.

    What is tested:
        - Each ratio wrapper produces exactly 4 drawLine calls.
        - _draw_diagonal_ratio_grid with vertical_ratio=0 → 0 drawLine calls.
        - _draw_diagonal_ratio_grid with horizontal_ratio=0 → 0 drawLine calls.

    What is NOT tested:
        - Exact endpoint positions of diagonal lines.

    Equivalence partitions:
        EP1  vertical_ratio > 0 and horizontal_ratio > 0  → draws 4 lines
        EP2  vertical_ratio = 0                           → early return, no drawing
        EP3  horizontal_ratio = 0                         → early return, no drawing

    Boundary values:
        BV1  vertical_ratio = 0    (boundary: invalid ratio)
        BV2  horizontal_ratio = 0  (boundary: invalid ratio)

    Mocking strategy:
        QPainter replaced with MagicMock.

    Constraints:
        _draw_diagonal_ratio_grid is a private method; called directly for ratio
        guard tests since the public wrappers always pass valid ratios.
    """

    @pytest.mark.parametrize(
        "method_name",
        [
            "_draw_diagonal_2_3_grid",
            "_draw_diagonal_3_2_grid",
            "_draw_diagonal_3_4_grid",
            "_draw_diagonal_4_3_grid",
        ],
        ids=["2_3", "3_2", "3_4", "4_3"],
    )
    def test_diagonal_ratio_wrapper_draws_four_lines(self, qtbot: QtBot, method_name: str) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When the parametrized ratio wrapper is called (EP1),
        Then painter.drawLine is called exactly 4 times.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        method = getattr(overlay, method_name)
        # Act
        method(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 4

    def test_diagonal_ratio_zero_vertical_ratio_does_not_draw(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When _draw_diagonal_ratio_grid is called with vertical_ratio=0 (BV1, EP2),
        Then painter.drawLine is never called (early-return guard).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_diagonal_ratio_grid(mock_painter, rect, 0, 1)  # pylint: disable=protected-access
        # Assert
        assert mock_painter.drawLine.call_count == 0

    def test_diagonal_ratio_zero_horizontal_ratio_does_not_draw(self, qtbot: QtBot) -> None:
        """
        Given a GridOverlay,
        When _draw_diagonal_ratio_grid is called with horizontal_ratio=0 (BV2, EP3),
        Then painter.drawLine is never called (early-return guard).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay._draw_diagonal_ratio_grid(mock_painter, rect, 1, 0)  # pylint: disable=protected-access
        # Assert
        assert mock_painter.drawLine.call_count == 0


@pytest.mark.widget
class TestGridOverlayDiagonalCompositeGrids:
    """
    Test Design Specification: GridOverlay — diagonal composite grid methods
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        The four composite diagonal methods each draw corner-to-corner diagonals
        plus additional lines to rule-of-thirds or golden-ratio division points on
        opposing edges. Each method produces exactly 6 QLineF drawLine calls.

    Infrastructure:
        - Requires qtbot for QApplication.
        - QPainter replaced with MagicMock.

    What is tested:
        - _draw_diagonal_thirds_v_grid → 6 drawLine calls.
        - _draw_diagonal_thirds_h_grid → 6 drawLine calls.
        - _draw_diagonal_golden_v_grid → 6 drawLine calls.
        - _draw_diagonal_golden_h_grid → 6 drawLine calls.

    What is NOT tested:
        - Exact positions of the division-point lines.

    Equivalence partitions:
        EP1  Any composite diagonal method with a valid rect → 6 drawLine calls.

    Mocking strategy:
        QPainter replaced with MagicMock.

    Constraints:
        Each method is called directly (not via draw_grid).
    """

    @pytest.mark.parametrize(
        "method_name",
        [
            "_draw_diagonal_thirds_v_grid",
            "_draw_diagonal_thirds_h_grid",
            "_draw_diagonal_golden_v_grid",
            "_draw_diagonal_golden_h_grid",
        ],
        ids=["thirds_v", "thirds_h", "golden_v", "golden_h"],
    )
    def test_composite_diagonal_draws_six_lines(self, qtbot: QtBot, method_name: str) -> None:
        """
        Given a GridOverlay and a 300×300 rect,
        When the parametrized composite diagonal method is called (EP1),
        Then painter.drawLine is called exactly 6 times.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        method = getattr(overlay, method_name)
        # Act
        method(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == 6


@pytest.mark.widget
class TestGridOverlayPenSetup:
    """
    Test Design Specification: GridOverlay — QPen configuration in draw_grid
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        draw_grid creates a QPen from the overlay's colour (with opacity applied
        as alpha), line width, and line style, then calls painter.setPen() exactly
        once before drawing. It also calls painter.setBrush(Qt.BrushStyle.NoBrush)
        to ensure grid lines are drawn without fill. Regressions in pen setup
        (wrong alpha, wrong width, brush left as default) would not affect
        coverage metrics but would silently break rendering.

    Infrastructure:
        - Requires qtbot for QApplication (QPen, QColor construction).
        - QPainter replaced with MagicMock to intercept setPen and setBrush calls.

    What is tested:
        - painter.setPen is called exactly once per draw_grid invocation.
        - The QPen passed to setPen has width equal to _line_width (default 4).
        - The QPen colour has alpha equal to _opacity (default 128).
        - painter.setBrush is called with Qt.BrushStyle.NoBrush.

    What is NOT tested:
        - Exact RGBA colour value beyond the alpha channel (colour correctness
          is validated by set_color round-trip tests in TestGridOverlayStateSetters).

    Equivalence partitions:
        EP1  Default overlay state → pen width 4, alpha 128, NoBrush.
        EP2  Custom opacity (255)  → pen alpha 255.
        EP3  Custom line width (2) → pen width 2.

    Boundary values:
        BV1  opacity = 255  (upper bound applied to alpha)
        BV2  line_width = 1 (minimum practical width)

    Mocking strategy:
        QPainter replaced with MagicMock. The QPen arg to setPen is a real Qt
        object and its properties are inspected via pen.width() / pen.color().alpha().

    Constraints:
        QApplication must be running for QPen and QColor construction inside draw_grid.
    """

    def test_set_pen_called_exactly_once(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay with a valid rect,
        When draw_grid is called,
        Then painter.setPen is called exactly once.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.setPen.call_count == 1

    def test_pen_width_equals_line_width(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay with default line_width=4 (EP1),
        When draw_grid is called,
        Then the QPen passed to painter.setPen has width() == 4.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        pen = mock_painter.setPen.call_args[0][0]
        assert isinstance(pen, QPen)
        assert pen.width() == 4

    def test_pen_color_alpha_equals_opacity(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay with default opacity=128 (EP1),
        When draw_grid is called,
        Then the QPen's colour alpha equals 128 (opacity applied via setAlpha).
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        pen = mock_painter.setPen.call_args[0][0]
        assert pen.color().alpha() == 128

    def test_pen_color_alpha_reflects_custom_opacity(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay with opacity set to 255 (EP2, BV1),
        When draw_grid is called,
        Then the QPen's colour alpha equals 255.
        """
        # Arrange
        overlay = GridOverlay()
        overlay.set_opacity(255)
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        pen = mock_painter.setPen.call_args[0][0]
        assert pen.color().alpha() == 255

    def test_pen_width_reflects_custom_line_width(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay with line_width set to 2 (EP3),
        When draw_grid is called,
        Then the QPen passed to setPen has width() == 2.
        """
        # Arrange
        overlay = GridOverlay()
        overlay.set_line_width(2)
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        pen = mock_painter.setPen.call_args[0][0]
        assert pen.width() == 2

    def test_set_brush_called_with_no_brush(self, qtbot: QtBot) -> None:
        """
        Given an enabled GridOverlay with a valid rect,
        When draw_grid is called,
        Then painter.setBrush is called exactly once with Qt.BrushStyle.NoBrush.
        """
        # Arrange
        overlay = GridOverlay()
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.setBrush.call_count == 1
        assert mock_painter.setBrush.call_args[0][0] == Qt.BrushStyle.NoBrush


@pytest.mark.widget
class TestGridOverlayDispatch:
    """
    Test Design Specification: GridOverlay — draw_grid dispatch to private methods
    Module under test: src/ui/widgets/grid_overlay.py

    Widget base class: Plain Python class (not a QWidget).

    Contract:
        draw_grid uses a dictionary to dispatch to the private drawing method that
        matches the current _grid_type. Each valid type must map to the correct
        method so that setting a type via the public API and then calling draw_grid
        produces the expected number of lines. A mis-wired entry in
        _grid_drawing_methods (e.g., swapped keys) would be silent under the
        existing test suite but is caught here.

    Infrastructure:
        - Requires qtbot for QApplication (QPen, QColor construction inside draw_grid).
        - QPainter replaced with MagicMock.

    What is tested:
        - For every valid grid type constant, setting the type via set_grid_type
          then calling draw_grid produces the documented drawLine call count.

    What is NOT tested:
        - Exact line positions (covered by grid-specific test classes).
        - Early-exit conditions (covered by TestGridOverlayDrawGrid).

    Equivalence partitions:
        EP1  4-line grid types (3x3, golden ratio, four diagonal ratio variants,
             diagonal 1:1) → drawLine called 4 times.
        EP2  6-line composite types (four diagonal+division-point variants)
             → drawLine called 6 times.

    Boundary values:
        None (dispatch is categorical, not numeric).

    Mocking strategy:
        QPainter replaced with MagicMock.

    Constraints:
        draw_grid is called through the public API (set_grid_type → draw_grid)
        to verify the full setter→dispatch integration.
    """

    @pytest.mark.parametrize(
        "grid_type, expected_calls",
        [
            (GRID_TYPE_3X3, 4),                      # EP1: rule-of-thirds
            (GRID_TYPE_GOLDEN_RATIO, 4),              # EP1: golden ratio
            (GRID_TYPE_DIAGONAL_1_1, 4),              # EP1: 45-degree diagonals
            (GRID_TYPE_DIAGONAL_2_3, 4),              # EP1: 2:3 ratio diagonals
            (GRID_TYPE_DIAGONAL_3_2, 4),              # EP1: 3:2 ratio diagonals
            (GRID_TYPE_DIAGONAL_3_4, 4),              # EP1: 3:4 ratio diagonals
            (GRID_TYPE_DIAGONAL_4_3, 4),              # EP1: 4:3 ratio diagonals
            (GRID_TYPE_DIAGONAL_THIRDS_V, 6),         # EP2: diagonals + vertical thirds
            (GRID_TYPE_DIAGONAL_THIRDS_H, 6),         # EP2: diagonals + horizontal thirds
            (GRID_TYPE_DIAGONAL_GOLDEN_V, 6),         # EP2: diagonals + vertical golden
            (GRID_TYPE_DIAGONAL_GOLDEN_H, 6),         # EP2: diagonals + horizontal golden
        ],
        ids=[
            "3x3",
            "golden_ratio",
            "diagonal_1_1",
            "diagonal_2_3",
            "diagonal_3_2",
            "diagonal_3_4",
            "diagonal_4_3",
            "diagonal_thirds_v",
            "diagonal_thirds_h",
            "diagonal_golden_v",
            "diagonal_golden_h",
        ],
    )
    def test_draw_grid_dispatches_to_correct_method(
        self, qtbot: QtBot, grid_type: str, expected_calls: int
    ) -> None:
        """
        Given a GridOverlay with grid type set via the public setter,
        When draw_grid is called with a 300×300 rect,
        Then painter.drawLine is called the expected number of times for that type.
        """
        # Arrange
        overlay = GridOverlay()
        overlay.set_grid_type(grid_type)
        mock_painter = MagicMock()
        rect = QRectF(0, 0, 300, 300)
        # Act
        overlay.draw_grid(mock_painter, rect)
        # Assert
        assert mock_painter.drawLine.call_count == expected_calls
