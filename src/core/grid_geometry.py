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
Pure geometry calculations for grid overlays.

This module contains no Qt imports. All functions operate on plain Python types
(float, tuple). The GridOverlay widget delegates all coordinate arithmetic here
so that grid geometry logic is unit-testable in isolation.

Coordinate system:
  - Input rect: (left, top, width, height) in float coordinates
  - Output lines: list of (x1, y1, x2, y2) tuples in float coordinates
"""


def calculate_3x3_lines(rect: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """
    Calculate rule-of-thirds grid lines (3×3 division).

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 4 line tuples: (x1, y1, x2, y2)
        - 2 vertical lines at 1/3 and 2/3 of width
        - 2 horizontal lines at 1/3 and 2/3 of height
    """
    left, top, width, height = rect

    # Vertical lines at rule-of-thirds positions
    x1 = left + width / 3.0
    x2 = left + 2.0 * width / 3.0

    # Horizontal lines at rule-of-thirds positions
    y1 = top + height / 3.0
    y2 = top + 2.0 * height / 3.0

    return [
        (x1, top, x1, top + height),  # Vertical line 1 at 1/3
        (x2, top, x2, top + height),  # Vertical line 2 at 2/3
        (left, y1, left + width, y1),  # Horizontal line 1 at 1/3
        (left, y2, left + width, y2),  # Horizontal line 2 at 2/3
    ]


def calculate_golden_ratio_lines(rect: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """
    Calculate golden ratio grid lines (1:0.618:1 division).

    The golden ratio divides the image using the ratio 1:0.618:1,
    placing lines at approximately 0.382 and 0.618 of each dimension.

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 4 line tuples: (x1, y1, x2, y2)
        - 2 vertical lines at golden ratio positions
        - 2 horizontal lines at golden ratio positions
    """
    left, top, width, height = rect

    golden_ratio_small = 0.382
    golden_ratio_large = 0.618

    x1 = left + width * golden_ratio_small
    x2 = left + width * golden_ratio_large

    y1 = top + height * golden_ratio_small
    y2 = top + height * golden_ratio_large

    return [
        (x1, top, x1, top + height),
        (x2, top, x2, top + height),
        (left, y1, left + width, y1),
        (left, y2, left + width, y2),
    ]


def calculate_diagonal_1_1_lines(rect: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """
    Calculate 45-degree diagonal lines from each corner (1:1 aspect ratio).

    Each diagonal extends until it hits an adjacent edge of the rectangle.
    The choice of which edge (right/bottom or left/top) depends on whether
    the rectangle is tall or wide.

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 4 line tuples: (x1, y1, x2, y2)
    """
    left, top, width, height = rect
    right = left + width
    bottom = top + height
    is_tall = width <= height

    lines = []

    # Diagonal from top-left corner (going down-right at 45°)
    lines.append((left, top, (right if is_tall else left + height), (top + width if is_tall else bottom)))

    # Diagonal from top-right corner (going down-left at 135°)
    lines.append((right, top, (left if is_tall else right - height), (top + width if is_tall else bottom)))

    # Diagonal from bottom-left corner (going up-right at -45°/315°)
    lines.append((left, bottom, (right if is_tall else left + height), (bottom - width if is_tall else top)))

    # Diagonal from bottom-right corner (going up-left at -135°/225°)
    lines.append((right, bottom, (left if is_tall else right - height), (bottom - width if is_tall else top)))

    return lines


def _calculate_diagonal_ratio_lines(
    rect: tuple[float, float, float, float], vertical_ratio: float, horizontal_ratio: float
) -> list[tuple[float, float, float, float]]:
    """
    Calculate corner-to-edge diagonal lines for a parameterized vertical:horizontal ratio.

    Args:
        rect: (left, top, width, height)
        vertical_ratio: vertical component of slope
        horizontal_ratio: horizontal component of slope

    Returns:
        List of 4 line tuples, or empty list if ratios are non-positive.
    """
    if vertical_ratio <= 0 or horizontal_ratio <= 0:
        return []

    left, top, width, height = rect
    right = left + width
    bottom = top + height

    if width * vertical_ratio <= height * horizontal_ratio:
        x_offset = width
        y_offset = width * vertical_ratio / horizontal_ratio
    else:
        x_offset = height * horizontal_ratio / vertical_ratio
        y_offset = height

    return [
        (left, top, left + x_offset, top + y_offset),
        (right, top, right - x_offset, top + y_offset),
        (left, bottom, left + x_offset, bottom - y_offset),
        (right, bottom, right - x_offset, bottom - y_offset),
    ]


def calculate_diagonal_2_3_lines(rect: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonal lines at arctan(2/3) ≈ 33.69° from each corner.

    Aspect ratio 2:3.

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 4 line tuples: (x1, y1, x2, y2)
    """
    return _calculate_diagonal_ratio_lines(rect, vertical_ratio=2.0, horizontal_ratio=3.0)


def calculate_diagonal_3_2_lines(rect: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonal lines at arctan(3/2) ≈ 56.31° from each corner.

    Aspect ratio 3:2.

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 4 line tuples: (x1, y1, x2, y2)
    """
    return _calculate_diagonal_ratio_lines(rect, vertical_ratio=3.0, horizontal_ratio=2.0)


def calculate_diagonal_3_4_lines(rect: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonal lines at 36.87 degrees from each corner.

    Aspect ratio 3:4. This is complementary to the 53.13° diagonal (4:3 ratio).

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 4 line tuples: (x1, y1, x2, y2)
    """
    return _calculate_diagonal_ratio_lines(rect, vertical_ratio=3.0, horizontal_ratio=4.0)


def calculate_diagonal_4_3_lines(rect: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonal lines at 53.13 degrees from each corner.

    Aspect ratio 4:3. This is complementary to the 36.87° diagonal (3:4 ratio).

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 4 line tuples: (x1, y1, x2, y2)
    """
    return _calculate_diagonal_ratio_lines(rect, vertical_ratio=4.0, horizontal_ratio=3.0)


def calculate_diagonal_thirds_v_lines(
    rect: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonals from all corners plus vertical lines to rule-of-thirds division points.

    Each corner has exactly 2 lines:
    - One diagonal to the opposite corner
    - One vertical line to a thirds division point on the top or bottom edge

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 6 line tuples: (x1, y1, x2, y2)
    """
    left, top, width, height = rect
    right = left + width
    bottom = top + height

    third_x1 = left + width / 3.0
    third_x2 = left + 2.0 * width / 3.0

    return [
        # Diagonals
        (left, top, right, bottom),
        (right, top, left, bottom),
        # Vertical lines to thirds points
        (left, top, third_x1, bottom),
        (right, top, third_x2, bottom),
        (left, bottom, third_x1, top),
        (right, bottom, third_x2, top),
    ]


def calculate_diagonal_thirds_h_lines(
    rect: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonals from all corners plus horizontal lines to rule-of-thirds division points.

    Each corner has exactly 2 lines:
    - One diagonal to the opposite corner
    - One horizontal line to a thirds division point on the left or right edge

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 6 line tuples: (x1, y1, x2, y2)
    """
    left, top, width, height = rect
    right = left + width
    bottom = top + height

    third_y1 = top + height / 3.0
    third_y2 = top + 2.0 * height / 3.0

    return [
        # Diagonals
        (left, top, right, bottom),
        (right, top, left, bottom),
        # Horizontal lines to thirds points
        (left, top, right, third_y1),
        (right, top, left, third_y1),
        (left, bottom, right, third_y2),
        (right, bottom, left, third_y2),
    ]


def calculate_diagonal_golden_v_lines(
    rect: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonals from all corners plus vertical lines to golden ratio division points.

    Each corner has exactly 2 lines:
    - One diagonal to the opposite corner
    - One vertical line to a golden ratio division point on the top or bottom edge

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 6 line tuples: (x1, y1, x2, y2)
    """
    left, top, width, height = rect
    right = left + width
    bottom = top + height

    golden_x1 = left + width * 0.382
    golden_x2 = left + width * 0.618

    return [
        # Diagonals
        (left, top, right, bottom),
        (right, top, left, bottom),
        # Vertical lines to golden points
        (left, top, golden_x1, bottom),
        (right, top, golden_x2, bottom),
        (left, bottom, golden_x1, top),
        (right, bottom, golden_x2, top),
    ]


def calculate_diagonal_golden_h_lines(
    rect: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    """
    Calculate diagonals from all corners plus horizontal lines to golden ratio division points.

    Each corner has exactly 2 lines:
    - One diagonal to the opposite corner
    - One horizontal line to a golden ratio division point on the left or right edge

    Args:
        rect: (left, top, width, height)

    Returns:
        List of 6 line tuples: (x1, y1, x2, y2)
    """
    left, top, width, height = rect
    right = left + width
    bottom = top + height

    golden_y1 = top + height * 0.382
    golden_y2 = top + height * 0.618

    return [
        # Diagonals
        (left, top, right, bottom),
        (right, top, left, bottom),
        # Horizontal lines to golden points
        (left, top, right, golden_y1),
        (right, top, left, golden_y1),
        (left, bottom, right, golden_y2),
        (right, bottom, left, golden_y2),
    ]
