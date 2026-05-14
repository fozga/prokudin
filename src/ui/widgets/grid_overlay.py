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
Grid overlay for image viewer.
Provides various grid types for composition guidance, including rule-of-thirds (3x3),
golden ratio grids, and diagonal lines.
"""

from typing import Callable, Dict, Union

from PyQt5.QtCore import QRect, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen

from src.core.grid_geometry import (
    calculate_3x3_lines,
    calculate_diagonal_1_1_lines,
    calculate_diagonal_2_3_lines,
    calculate_diagonal_3_2_lines,
    calculate_diagonal_3_4_lines,
    calculate_diagonal_4_3_lines,
    calculate_diagonal_golden_h_lines,
    calculate_diagonal_golden_v_lines,
    calculate_diagonal_thirds_h_lines,
    calculate_diagonal_thirds_v_lines,
    calculate_golden_ratio_lines,
)

from .grid_types import (
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


class GridOverlay:
    """
    Manages and draws grid overlays on images.

    Supports multiple grid types:
    - 3x3: Divides the image into 9 equal parts (rule-of-thirds)
    - Golden Ratio: Uses the golden ratio (1:0.618:1) for grid lines
    - Diagonal 1:1: Draws 45-degree lines from each corner
    - Diagonal 2:3: Draws lines at arctan(2/3) degrees from each corner (2:3 aspect ratio)
    - Diagonal 3:2: Draws lines at arctan(3/2) degrees from each corner (3:2 aspect ratio)
    - Diagonal 3:4: Draws lines at 36.87 degrees from each corner (3:4 aspect ratio)
    - Diagonal 4:3: Draws lines at 53.13 degrees from each corner (4:3 aspect ratio)
    - Diagonal + Thirds V: Diagonals plus vertical lines to rule-of-thirds division points
    - Diagonal + Thirds H: Diagonals plus horizontal lines to rule-of-thirds division points
    - Diagonal + Golden V: Diagonals plus vertical lines to golden ratio division points
    - Diagonal + Golden H: Diagonals plus horizontal lines to golden ratio division points
    """

    def __init__(self) -> None:
        """Initialize the grid overlay with default settings."""
        self._enabled = True
        self._color = QColor("white")
        self._line_width = 4
        self._line_style = Qt.PenStyle.SolidLine
        self._opacity = 128  # Semi-transparent (0-255)
        self._grid_type = GRID_TYPE_3X3  # Default to 3x3 grid

        # Mapping of grid types to their drawing methods
        self._grid_drawing_methods: Dict[str, Callable[[QPainter, QRectF], None]] = {
            GRID_TYPE_3X3: self._draw_3x3_grid,
            GRID_TYPE_GOLDEN_RATIO: self._draw_golden_ratio_grid,
            GRID_TYPE_DIAGONAL_1_1: self._draw_diagonal_1_1_grid,
            GRID_TYPE_DIAGONAL_2_3: self._draw_diagonal_2_3_grid,
            GRID_TYPE_DIAGONAL_3_2: self._draw_diagonal_3_2_grid,
            GRID_TYPE_DIAGONAL_3_4: self._draw_diagonal_3_4_grid,
            GRID_TYPE_DIAGONAL_4_3: self._draw_diagonal_4_3_grid,
            GRID_TYPE_DIAGONAL_THIRDS_V: self._draw_diagonal_thirds_v_grid,
            GRID_TYPE_DIAGONAL_THIRDS_H: self._draw_diagonal_thirds_h_grid,
            GRID_TYPE_DIAGONAL_GOLDEN_V: self._draw_diagonal_golden_v_grid,
            GRID_TYPE_DIAGONAL_GOLDEN_H: self._draw_diagonal_golden_h_grid,
        }

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the grid overlay.

        Args:
            enabled: True to show the grid, False to hide it.
        """
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """
        Check if the grid is enabled.

        Returns:
            bool: True if grid is enabled, False otherwise.
        """
        return self._enabled

    def set_color(self, color: QColor) -> None:
        """
        Set the color of the grid lines.

        Args:
            color: The color to use for grid lines.
        """
        self._color = color

    def set_line_width(self, width: int) -> None:
        """
        Set the width of the grid lines.

        Args:
            width: Line width in pixels.
        """
        self._line_width = width

    def get_line_width(self) -> int:
        """
        Get the current line width.

        Returns:
            int: The current line width in pixels.
        """
        return self._line_width

    def set_opacity(self, opacity: int) -> None:
        """
        Set the opacity of the grid lines.

        Args:
            opacity: Opacity value from 0 (transparent) to 255 (opaque).
        """
        self._opacity = max(0, min(255, opacity))

    def set_grid_type(self, grid_type: str) -> None:
        """
        Set the grid type.

        Args:
            grid_type: The grid type to use (GRID_TYPE_3X3 or GRID_TYPE_GOLDEN_RATIO).
        """
        if grid_type not in self._grid_drawing_methods:
            raise ValueError(f"Unsupported grid type: {grid_type}")
        self._grid_type = grid_type

    def get_grid_type(self) -> str:
        """
        Get the current grid type.

        Returns:
            str: The current grid type.
        """
        return self._grid_type

    def draw_grid(self, painter: QPainter, rect: Union[QRect, QRectF]) -> None:
        """
        Draw the grid lines on the given rectangle.

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on (QRect or QRectF).
        """
        if not self._enabled:
            return

        # Convert QRect to QRectF if needed
        if isinstance(rect, QRect):
            rect = QRectF(rect)

        # Nothing to draw for invalid or zero-area rectangles.
        if rect.width() <= 0 or rect.height() <= 0:
            return

        # Save the current painter state
        painter.save()

        # Set up the pen for drawing grid lines
        color = QColor(self._color)
        color.setAlpha(self._opacity)
        pen = QPen(color, self._line_width, self._line_style)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw grid based on type using dictionary dispatch
        draw_method = self._grid_drawing_methods.get(self._grid_type, self._draw_3x3_grid)
        draw_method(painter, rect)

        # Restore the painter state
        painter.restore()

    def _draw_diagonal_thirds_v_grid(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw diagonals connecting corners, plus vertical lines from each corner to
        rule-of-thirds division points.

        Each corner has exactly 2 lines:
        - One diagonal to opposite corner
        - One vertical line to a thirds division point on top or bottom edge
        """
        lines = calculate_diagonal_thirds_v_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_thirds_h_grid(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw diagonals connecting corners, plus horizontal lines from each corner to rule-of-thirds division points.

        Each corner has exactly 2 lines:
        - One diagonal to opposite corner
        - One horizontal line to a thirds division point on left or right edge
        """
        lines = calculate_diagonal_thirds_h_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_golden_v_grid(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw diagonals connecting corners, plus vertical lines from each corner to golden ratio division points.

        Each corner has exactly 2 lines:
        - One diagonal to opposite corner
        - One vertical line to a golden ratio division point on top or bottom edge
        """
        lines = calculate_diagonal_golden_v_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_golden_h_grid(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw diagonals connecting corners, plus horizontal lines from each corner to golden ratio division points.

        Each corner has exactly 2 lines:
        - One diagonal to opposite corner
        - One horizontal line to a golden ratio division point on left or right edge
        """
        lines = calculate_diagonal_golden_h_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_3x3_grid(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw a rule-of-thirds (3x3) grid.

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on.
        """
        lines = calculate_3x3_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_golden_ratio_grid(self, painter: QPainter, rect: QRectF) -> None:
        """
        Draw a golden ratio grid (1:0.618:1).

        The golden ratio divides the image using the ratio 1:0.618:1,
        which is approximately 0.382 and 0.618 of the total dimension.

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on.
        """
        lines = calculate_golden_ratio_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_1_1_grid(self, painter: QPainter, rect: QRectF) -> None:  # pylint: disable=too-many-locals
        """
        Draw diagonal lines at 45 degrees from each corner (1:1 aspect ratio).

        Draws four diagonal lines:
        - From top-left corner at 45 degrees
        - From top-right corner at 135 degrees
        - From bottom-left corner at -45 degrees (315 degrees)
        - From bottom-right corner at -135 degrees (225 degrees)

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on.
        """
        lines = calculate_diagonal_1_1_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_2_3_grid(self, painter: QPainter, rect: QRectF) -> None:  # pylint: disable=too-many-locals
        """
        Draw diagonal lines at arctan(2/3) degrees from each corner (2:3 aspect ratio).

        The angle corresponds to arctan(2/3) ≈ 33.69°, creating lines with a 2:3 slope.
        For every 3 units horizontally, we go 2 units vertically.

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on.
        """
        lines = calculate_diagonal_2_3_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_3_2_grid(self, painter: QPainter, rect: QRectF) -> None:  # pylint: disable=too-many-locals
        """
        Draw diagonal lines at arctan(3/2) degrees from each corner (3:2 aspect ratio).

        The angle corresponds to arctan(3/2) ≈ 56.31°, creating lines with a 3:2 slope.
        For every 2 units horizontally, we go 3 units vertically.

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on.
        """
        lines = calculate_diagonal_3_2_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_3_4_grid(self, painter: QPainter, rect: QRectF) -> None:  # pylint: disable=too-many-locals
        """
        Draw diagonal lines at 36.87 degrees from each corner (3:4 aspect ratio).

        The angle of 36.87° corresponds to arctan(3/4), creating lines with a 3:4 slope.
        This is complementary to the 53.13° diagonal (4:3 ratio).

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on.
        """
        lines = calculate_diagonal_3_4_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _draw_diagonal_4_3_grid(self, painter: QPainter, rect: QRectF) -> None:  # pylint: disable=too-many-locals
        """
        Draw diagonal lines at 53.13 degrees from each corner (4:3 aspect ratio).

        The angle of 53.13° corresponds to arctan(4/3), creating lines with a 4:3 slope.
        This is complementary to the 36.87° diagonal (3:4 ratio).

        Args:
            painter: QPainter object to draw with.
            rect: The rectangle area to draw the grid on.
        """
        lines = calculate_diagonal_4_3_lines((rect.left(), rect.top(), rect.width(), rect.height()))
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
