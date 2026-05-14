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
Pure geometry helpers for crop rectangle calculations.

This module contains no Qt imports. All functions operate on plain Python types
(int, float, dataclass). The Qt-dependent CropHandler delegates all arithmetic
here so that the geometry logic is unit-testable in isolation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Point:
    """Plain two-dimensional point with floating-point coordinates."""

    x: float
    y: float


@dataclass
class Rect:
    """Plain integer rectangle (left, top, width, height).

    Uses the half-open convention: right = left + width, bottom = top + height.
    """

    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def center_x(self) -> float:
        return self.left + self.width / 2

    @property
    def center_y(self) -> float:
        return self.top + self.height / 2


@dataclass
class EdgeConstraints:
    """Store edge coordinates for rectangle constraints."""

    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int


@dataclass
class ResizeParameters:
    """Store parameters for resize operations."""

    handle: str
    mouse: Point
    rect: Rect
    target_ratio: float
    center_point: int


@dataclass
class EdgeResizeContext:
    """Store context for edge resize operations."""

    handle: str
    mouse: Point
    rect: Rect
    bounds: Rect


def clamp_point_to_bounds(point: Point, bounds: Rect) -> Point:
    """Clamp a point so that it lies within the image bounds."""
    x = max(bounds.left, min(bounds.right, int(point.x)))
    y = max(bounds.top, min(bounds.bottom, int(point.y)))
    return Point(float(x), float(y))


def clamp_rect_to_bounds(rect: Rect, bounds: Rect) -> Rect:
    """Return the intersection of rect and bounds (both non-negative dimensions)."""
    left = max(rect.left, bounds.left)
    top = max(rect.top, bounds.top)
    right = min(rect.right, bounds.right)
    bottom = min(rect.bottom, bounds.bottom)
    width = max(0, right - left)
    height = max(0, bottom - top)
    return Rect(left, top, width, height)


def adjust_dimensions_to_ratio(
    dimensions: tuple[int, int],
    fixed_point: tuple[int, int],
    corner: str,
    ratio: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Adjust width/height to maintain aspect ratio and compute the moving corner's coordinates.

    Returns (width, height, moving_x, moving_y).
    """
    w, h = ratio
    target_ratio = w / h
    width, height = dimensions

    if width / target_ratio > height:
        width = int(height * target_ratio)
    else:
        height = int(width / target_ratio)

    fixed_x, fixed_y = fixed_point
    moving_x, moving_y = 0, 0

    if corner == "top_left":
        moving_x = fixed_x - width
        moving_y = fixed_y - height
    elif corner == "top_right":
        moving_x = fixed_x + width
        moving_y = fixed_y - height
    elif corner == "bottom_left":
        moving_x = fixed_x - width
        moving_y = fixed_y + height
    elif corner == "bottom_right":
        moving_x = fixed_x + width
        moving_y = fixed_y + height

    return width, height, moving_x, moving_y


def resize_top_left(
    mouse: Point,
    fixed_edges: dict[str, int],
    bounds: Rect,
    ratio: Optional[tuple[int, int]] = None,
) -> Rect:
    """Compute new crop rect when dragging the top-left corner."""
    fixed_right = fixed_edges["right"]
    fixed_bottom = fixed_edges["bottom"]
    moving_x = min(int(mouse.x), fixed_right - 10)
    moving_y = min(int(mouse.y), fixed_bottom - 10)

    width = fixed_right - moving_x
    height = fixed_bottom - moving_y

    if ratio:
        width, height, moving_x, moving_y = adjust_dimensions_to_ratio(
            (width, height), (fixed_right, fixed_bottom), "top_left", ratio
        )

    return clamp_rect_to_bounds(Rect(moving_x, moving_y, width, height), bounds)


def resize_top_right(
    mouse: Point,
    fixed_edges: dict[str, int],
    bounds: Rect,
    ratio: Optional[tuple[int, int]] = None,
) -> Rect:
    """Compute new crop rect when dragging the top-right corner."""
    fixed_left = fixed_edges["left"]
    fixed_bottom = fixed_edges["bottom"]
    moving_x = max(int(mouse.x), fixed_left + 10)
    moving_y = min(int(mouse.y), fixed_bottom - 10)

    width = moving_x - fixed_left
    height = fixed_bottom - moving_y

    if ratio:
        width, height, moving_x, moving_y = adjust_dimensions_to_ratio(
            (width, height), (fixed_left, fixed_bottom), "top_right", ratio
        )

    return clamp_rect_to_bounds(Rect(fixed_left, moving_y, width, height), bounds)


def resize_bottom_left(
    mouse: Point,
    fixed_edges: dict[str, int],
    bounds: Rect,
    ratio: Optional[tuple[int, int]] = None,
) -> Rect:
    """Compute new crop rect when dragging the bottom-left corner."""
    fixed_right = fixed_edges["right"]
    fixed_top = fixed_edges["top"]
    moving_x = min(int(mouse.x), fixed_right - 10)
    moving_y = max(int(mouse.y), fixed_top + 10)

    width = fixed_right - moving_x
    height = moving_y - fixed_top

    if ratio:
        width, height, moving_x, moving_y = adjust_dimensions_to_ratio(
            (width, height), (fixed_right, fixed_top), "bottom_left", ratio
        )

    return clamp_rect_to_bounds(Rect(moving_x, fixed_top, width, height), bounds)


def resize_bottom_right(
    mouse: Point,
    fixed_edges: dict[str, int],
    bounds: Rect,
    ratio: Optional[tuple[int, int]] = None,
) -> Rect:
    """Compute new crop rect when dragging the bottom-right corner."""
    fixed_left = fixed_edges["left"]
    fixed_top = fixed_edges["top"]
    moving_x = max(int(mouse.x), fixed_left + 10)
    moving_y = max(int(mouse.y), fixed_top + 10)

    width = moving_x - fixed_left
    height = moving_y - fixed_top

    if ratio:
        width, height, moving_x, moving_y = adjust_dimensions_to_ratio(
            (width, height), (fixed_left, fixed_top), "bottom_right", ratio
        )

    return clamp_rect_to_bounds(Rect(fixed_left, fixed_top, width, height), bounds)


def get_horizontal_constraints(params: ResizeParameters) -> EdgeConstraints:
    """Compute edge constraints for horizontal (left/right) edge resizing with fixed ratio."""
    handle = params.handle
    mouse = params.mouse
    rect = params.rect
    target_ratio = params.target_ratio
    center_y = params.center_point

    if handle == "left":
        fixed_right = rect.right
        new_left = min(int(mouse.x), fixed_right - 10)
        width = fixed_right - new_left
        height = int(round(width / target_ratio))
        new_top = int(round(center_y - height / 2))
        return EdgeConstraints(
            left=new_left, top=new_top, right=fixed_right, bottom=new_top + height, width=width, height=height
        )

    # handle == "right"
    fixed_left = rect.left
    new_right = max(int(mouse.x), fixed_left + 10)
    width = new_right - fixed_left
    height = int(round(width / target_ratio))
    new_top = int(round(center_y - height / 2))
    return EdgeConstraints(
        left=fixed_left, top=new_top, right=new_right, bottom=new_top + height, width=width, height=height
    )


def apply_horizontal_bounds_constraints(
    c: EdgeConstraints, bounds: Rect, edge: str, target_ratio: float
) -> Rect:
    """Clamp horizontally-resized rectangle to image bounds, preserving aspect ratio."""
    new_left, new_top = c.left, c.top
    new_width, new_height = c.width, c.height
    new_bottom = c.bottom
    right_edge = c.right

    if new_left < bounds.left:
        new_left = bounds.left
        new_width = right_edge - new_left if edge == "left" else new_width
        new_height = int(round(new_width / target_ratio))
        new_top = int(round((c.top + c.bottom) / 2 - new_height / 2))
        new_bottom = new_top + new_height

    if new_top < bounds.top:
        new_top = bounds.top
        new_height = new_bottom - new_top
        new_width = int(round(new_height * target_ratio))
        if edge == "left":
            new_left = right_edge - new_width

    if new_bottom > bounds.bottom:
        new_bottom = bounds.bottom
        new_height = new_bottom - new_top
        new_width = int(round(new_height * target_ratio))
        if edge == "left":
            new_left = right_edge - new_width

    return Rect(new_left, new_top, new_width, new_height)


def get_vertical_constraints(params: ResizeParameters) -> EdgeConstraints:
    """Compute edge constraints for vertical (top/bottom) edge resizing with fixed ratio."""
    handle = params.handle
    mouse = params.mouse
    rect = params.rect
    target_ratio = params.target_ratio
    center_x = params.center_point

    if handle == "top":
        fixed_bottom = rect.bottom
        new_top = min(int(mouse.y), fixed_bottom - 10)
        height = fixed_bottom - new_top
        width = int(round(height * target_ratio))
        new_left = int(round(center_x - width / 2))
        return EdgeConstraints(
            left=new_left, top=new_top, right=new_left + width, bottom=fixed_bottom, width=width, height=height
        )

    # handle == "bottom"
    fixed_top = rect.top
    new_bottom = max(int(mouse.y), fixed_top + 10)
    height = new_bottom - fixed_top
    width = int(round(height * target_ratio))
    new_left = int(round(center_x - width / 2))
    return EdgeConstraints(
        left=new_left, top=fixed_top, right=new_left + width, bottom=new_bottom, width=width, height=height
    )


def apply_vertical_bounds_constraints(
    c: EdgeConstraints, bounds: Rect, edge: str, target_ratio: float
) -> Rect:
    """Clamp vertically-resized rectangle to image bounds, preserving aspect ratio."""
    new_left, new_top = c.left, c.top
    new_width, new_height = c.width, c.height
    new_right = c.right
    bottom_edge = c.bottom

    if new_top < bounds.top and edge == "top":
        new_top = bounds.top
        new_height = bottom_edge - new_top
        new_width = int(round(new_height * target_ratio))
        new_left = int(round((c.left + c.right) / 2 - new_width / 2))
        new_right = new_left + new_width

    if new_left < bounds.left:
        new_left = bounds.left
        new_width = new_right - new_left
        new_height = int(round(new_width / target_ratio))
        if edge == "top":
            new_top = bottom_edge - new_height

    if new_right > bounds.right:
        new_right = bounds.right
        new_width = new_right - new_left
        new_height = int(round(new_width / target_ratio))
        if edge == "top":
            new_top = bottom_edge - new_height
        else:
            bottom_edge = new_top + new_height

    return Rect(new_left, new_top, new_width, new_height)


def edge_resize_free_aspect(context: EdgeResizeContext) -> Rect:
    """Resize a single edge with no aspect ratio constraint, clamped to bounds."""
    handle = context.handle
    mouse = context.mouse
    bounds = context.bounds
    rect = context.rect

    left = rect.left
    right = rect.right
    top = rect.top
    bottom = rect.bottom

    if handle == "left":
        left = min(int(mouse.x), right - 10)
    elif handle == "right":
        right = max(int(mouse.x), left + 10)
    elif handle == "top":
        top = min(int(mouse.y), bottom - 10)
    elif handle == "bottom":
        bottom = max(int(mouse.y), top + 10)

    left = max(bounds.left, left)
    right = min(bounds.right, right)
    top = max(bounds.top, top)
    bottom = min(bounds.bottom, bottom)

    return Rect(left, top, right - left, bottom - top)


def get_anchor_point(handle: str, rect: Optional[Rect]) -> Point:
    """Return the fixed anchor point opposite the given handle on a rectangle."""
    if rect is None:
        return Point(0.0, 0.0)

    anchor_points = {
        "top_left": Point(float(rect.right), float(rect.bottom)),
        "top_right": Point(float(rect.left), float(rect.bottom)),
        "bottom_left": Point(float(rect.right), float(rect.top)),
        "bottom_right": Point(float(rect.left), float(rect.top)),
        "left": Point(float(rect.left), rect.center_y),
        "right": Point(float(rect.right), rect.center_y),
        "top": Point(rect.center_x, float(rect.top)),
        "bottom": Point(rect.center_x, float(rect.bottom)),
    }

    return anchor_points.get(handle, Point(rect.center_x, rect.center_y))
