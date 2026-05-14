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
Handler for crop functionality in the image viewer.
Manages crop rectangle, handles, and interactions.
"""

from typing import Union

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, Qt
from PyQt5.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QGraphicsPixmapItem, QGraphicsView

from src.core.crop_geometry import (
    EdgeResizeContext,
    Point,
    Rect,
    ResizeParameters,
    apply_horizontal_bounds_constraints,
    apply_vertical_bounds_constraints,
    clamp_point_to_bounds,
    clamp_rect_to_bounds,
    edge_resize_free_aspect,
)
from src.core.crop_geometry import get_anchor_point as _geo_get_anchor_point
from src.core.crop_geometry import (
    get_horizontal_constraints,
    get_vertical_constraints,
    resize_bottom_left,
    resize_bottom_right,
    resize_top_left,
    resize_top_right,
)

from .grid_overlay import GridOverlay


def _qrect_to_rect(r: QRect) -> Rect:
    """Convert a QRect to a plain Rect."""
    return Rect(r.left(), r.top(), r.width(), r.height())


def _qrectf_to_rect(r: QRectF) -> Rect:
    """Convert a QRectF to a plain Rect (truncates to int)."""
    return Rect(int(r.left()), int(r.top()), int(r.width()), int(r.height()))


def _rect_to_qrect(r: Rect) -> QRect:
    """Convert a plain Rect to a QRect."""
    return QRect(r.left, r.top, r.width, r.height)


class CropHandler:  # pylint: disable=too-many-public-methods
    """
    Handles crop-related functionality for an image viewer.

    This class encapsulates:
    - Crop rectangle creation and manipulation
    - Handle detection and interaction
    - Crop ratio maintenance
    - Drawing crop overlay and handles

    Pure geometry calculations are delegated to src.core.crop_geometry.
    """

    def __init__(self, view: QGraphicsView, grid_overlay: GridOverlay) -> None:
        """
        Initialize the crop handler.

        Args:
            view: The QGraphicsView instance.
            grid_overlay: Shared GridOverlay instance from the viewer.
        """
        self.view = view
        # Group related attributes into dictionaries
        self._state = {
            "crop_mode": False,
            "dragging": False,
            "min_crop_size": 50,
            "crop_handle_size": 20,
        }
        self._rectangles: dict[str, Union[QRect, None]] = {
            "current": None,  # Current temporary crop rectangle
            "saved": None,  # Last confirmed crop rectangle
            "original": None,  # Original rectangle during drag
        }
        self._drag_info: dict[str, Union[QPointF, str, dict[str, int], None]] = {
            "start": None,  # Starting point of drag
            "handle": None,  # Current handle being dragged
            "anchor_point": None,  # Fixed point during resize
            "fixed_edges": None,  # Fixed edges during corner resize
        }
        self._crop_ratio: Union[tuple[int, int], None] = None  # Keep this separate as it's used frequently

        # Use shared grid overlay instance from viewer
        self._grid_overlay = grid_overlay

    def set_crop_mode(self, enabled: bool, photo: Union[QGraphicsPixmapItem, None]) -> None:
        """
        Enables or disables crop mode.
        """
        self._state["crop_mode"] = enabled
        if enabled and photo is not None:
            if photo.pixmap():
                if self._rectangles["saved"]:
                    # Use last saved crop rectangle if available
                    self._rectangles["current"] = QRect(self._rectangles["saved"])
                else:
                    # Initialize to 80% of image size, centered
                    img_width = photo.pixmap().width()
                    img_height = photo.pixmap().height()
                    rect_width = int(img_width * 0.8)
                    rect_height = int(img_height * 0.8)
                    x = (img_width - rect_width) // 2
                    y = (img_height - rect_height) // 2
                    self._rectangles["current"] = QRect(x, y, rect_width, rect_height)

                if self._crop_ratio:
                    self.adjust_crop_rect_to_ratio(photo)
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            # Discard temporary crop rectangle when exiting crop mode
            self._rectangles["current"] = None
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
        self.view.viewport().update()  # type: ignore[union-attr]

    def is_crop_mode(self) -> bool:
        """Return whether crop mode is enabled."""
        return bool(self._state["crop_mode"])

    def confirm_crop(self, photo: QGraphicsPixmapItem) -> None:
        """Confirm the current crop rectangle."""
        if self._rectangles["current"]:
            self._rectangles["saved"] = QRect(self._rectangles["current"])
        self.set_crop_mode(False, photo)

    def cancel_crop(self) -> None:
        """Cancel the current crop operation."""
        self._rectangles["current"] = None
        self.set_crop_mode(False, None)

    def get_saved_crop_rect(self) -> Union[QRect, None]:
        """Return the saved crop rectangle."""
        return self._rectangles["saved"]

    def set_saved_crop_rect(self, rect: Union[QRect, None]) -> None:
        """
        Set the saved crop rectangle.

        Args:
            rect: The crop rectangle to save, or None to clear it.
        """
        self._rectangles["saved"] = rect

    def get_crop_rect(self) -> Union[QRect, None]:
        """Return the current crop rectangle."""
        return self._rectangles["current"]

    def set_crop_rect(self, rect: Union[QRect, None]) -> None:
        """
        Set the crop rectangle.

        Args:
            rect: The crop rectangle to set, or None to clear it.
        """
        self._rectangles["current"] = rect
        self.view.viewport().update()  # type: ignore[union-attr]

    def set_crop_ratio(self, ratio: Union[tuple[int, int], None], photo: Union[QGraphicsPixmapItem, None]) -> None:
        """Set the aspect ratio for the crop rectangle."""
        if ratio is None or not isinstance(ratio, tuple) or len(ratio) != 2:
            return

        # Update the ratio
        self._crop_ratio = ratio

        # Adjust the current rectangle to the new ratio
        self.adjust_crop_rect_to_ratio(photo)

    def adjust_crop_rect_to_ratio(self, photo: Union[QGraphicsPixmapItem, None]) -> None:
        """Adjust the current crop rectangle to maintain the set aspect ratio."""
        if photo is None:
            return
        if not self._crop_ratio or not self._rectangles["current"]:
            return

        # Get current dimensions
        crop_rect = self._rectangles["current"]
        original_width = crop_rect.width()
        original_height = crop_rect.height()

        # Calculate new dimensions based on ratio
        w, h = self._crop_ratio
        target_ratio = w / h

        # First try to maintain width and adjust height
        new_width = original_width
        new_height = int(new_width / target_ratio)

        # If new height would exceed original height, maintain height instead
        if new_height > original_height:
            new_height = original_height
            new_width = int(new_height * target_ratio)

        # Create new rectangle maintaining the top-left corner position
        new_rect = QRect(crop_rect.left(), crop_rect.top(), new_width, new_height)

        # Ensure the new rectangle stays within image bounds
        bounds = photo.boundingRect()
        if new_rect.right() > bounds.right():
            new_rect.setRight(int(bounds.right()))
            new_rect.setWidth(int(new_rect.height() * target_ratio))
        if new_rect.bottom() > bounds.bottom():
            new_rect.setBottom(int(bounds.bottom()))
            new_rect.setHeight(int(new_rect.width() / target_ratio))

        self._rectangles["current"] = new_rect
        self.view.viewport().update()  # type: ignore[union-attr]

    def get_handle_at(self, pos: QPoint) -> Union[str, None]:
        """Determine which crop handle is under the given mouse position."""
        if not self._rectangles["current"]:
            return None

        # Convert view coordinates to scene coordinates
        scene_pos = self.view.mapToScene(int(pos.x()), int(pos.y()))
        rect = self._rectangles["current"]
        handle_size = self._state["crop_handle_size"]

        # Define handle areas with larger hit regions
        handles = {
            "top_left": QRectF(rect.left() - handle_size, rect.top() - handle_size, handle_size * 2, handle_size * 2),
            "top_right": QRectF(rect.right() - handle_size, rect.top() - handle_size, handle_size * 2, handle_size * 2),
            "bottom_left": QRectF(
                rect.left() - handle_size, rect.bottom() - handle_size, handle_size * 2, handle_size * 2
            ),
            "bottom_right": QRectF(
                rect.right() - handle_size, rect.bottom() - handle_size, handle_size * 2, handle_size * 2
            ),
            "top": QRectF(
                rect.left() + handle_size, rect.top() - handle_size, rect.width() - handle_size * 2, handle_size * 2
            ),
            "bottom": QRectF(
                rect.left() + handle_size, rect.bottom() - handle_size, rect.width() - handle_size * 2, handle_size * 2
            ),
            "left": QRectF(
                rect.left() - handle_size, rect.top() + handle_size, handle_size * 2, rect.height() - handle_size * 2
            ),
            "right": QRectF(
                rect.right() - handle_size, rect.top() + handle_size, handle_size * 2, rect.height() - handle_size * 2
            ),
        }

        # First check corners and edges
        for handle, handle_rect in handles.items():
            if handle_rect.contains(scene_pos):
                return handle

        # Then check if inside crop rect (for moving)
        if rect.contains(scene_pos.toPoint()):
            return "move"

        return None

    def update_cursor_for_handle(self, handle: Union[str, None]) -> None:
        """Update cursor based on the handle under the mouse."""
        if self._state["dragging"] and self._drag_info["handle"] == "move":
            self.view.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif handle == "move":
            self.view.setCursor(Qt.CursorShape.SizeAllCursor)  # Four arrows for center area
        elif handle in ["top_left", "bottom_right"]:
            self.view.setCursor(Qt.CursorShape.SizeFDiagCursor)  # Diagonal arrow for top-left/bottom-right
        elif handle in ["top_right", "bottom_left"]:
            self.view.setCursor(Qt.CursorShape.SizeBDiagCursor)  # Diagonal arrow for top-right/bottom-left
        elif handle in ["left", "right"]:
            self.view.setCursor(Qt.CursorShape.SizeHorCursor)  # Horizontal arrow for left/right
        elif handle in ["top", "bottom"]:
            self.view.setCursor(Qt.CursorShape.SizeVerCursor)  # Vertical arrow for top/bottom
        else:
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
        # Force immediate cursor update
        QApplication.processEvents()

    def get_anchor_point(self, handle: str, rect: Union[QRect, None]) -> QPointF:
        """Return the fixed anchor point for a given handle and rectangle."""
        r = _qrect_to_rect(rect) if rect is not None else None
        pt = _geo_get_anchor_point(handle, r)
        return QPointF(pt.x, pt.y)

    def resize_crop_rect_from_anchor(
        self, handle: Union[str, None], mouse_scene_pos: QPointF, photo: Union[QGraphicsPixmapItem, None]
    ) -> None:
        """Resize the crop rectangle based on the dragged handle and anchor."""
        if not all([photo, handle, self._rectangles["original"]]) or photo is None:
            return

        bounds_qrectf = photo.boundingRect()
        bounds = _qrectf_to_rect(bounds_qrectf)
        clamped = clamp_point_to_bounds(Point(mouse_scene_pos.x(), mouse_scene_pos.y()), bounds)
        mouse = QPointF(clamped.x, clamped.y)

        # Dispatch to appropriate handler based on handle type
        if handle in ["top_left", "top_right", "bottom_left", "bottom_right"] and self._drag_info["fixed_edges"]:
            new_rect = self._handle_corner_resize(handle, mouse, bounds_qrectf)
        elif handle in ["left", "right", "top", "bottom"]:
            new_rect = self._handle_edge_resize(handle, mouse, {"bounds": bounds_qrectf})
        else:
            return

        # Ensure minimum size and update crop rectangle
        if (
            new_rect
            and new_rect.width() >= self._state["min_crop_size"]
            and new_rect.height() >= self._state["min_crop_size"]
        ):
            self._rectangles["current"] = new_rect

    def _handle_corner_resize(self, handle: str, mouse: QPointF, bounds: QRectF) -> Union[QRect, None]:
        """Handle resizing from a corner handle."""
        fe = self._drag_info["fixed_edges"]
        if not fe or not isinstance(fe, dict):
            return None

        bounds_rect = _qrectf_to_rect(bounds)
        mouse_pt = Point(mouse.x(), mouse.y())

        resize_funcs = {
            "top_left": resize_top_left,
            "top_right": resize_top_right,
            "bottom_left": resize_bottom_left,
            "bottom_right": resize_bottom_right,
        }
        if handle in resize_funcs:
            result = resize_funcs[handle](mouse_pt, fe, bounds_rect, self._crop_ratio)
            return _rect_to_qrect(result)
        return None

    def _handle_edge_resize(self, handle: str, mouse: QPointF, params: dict) -> Union[QRect, None]:
        """Handle resizing from an edge handle."""
        original_rect = self._rectangles["original"]
        if not original_rect:
            return None

        rect = _qrect_to_rect(original_rect)
        bounds = _qrectf_to_rect(params["bounds"])
        context = EdgeResizeContext(handle=handle, mouse=Point(mouse.x(), mouse.y()), rect=rect, bounds=bounds)

        if self._crop_ratio:
            result = self._edge_resize_with_ratio(context)
        else:
            result = edge_resize_free_aspect(context)

        return _rect_to_qrect(result)

    def _edge_resize_with_ratio(self, context: EdgeResizeContext) -> Rect:
        """Handle edge resizing with fixed aspect ratio."""
        if context.handle in ["left", "right"]:
            return self._resize_horizontal_edge_with_ratio(context)
        return self._resize_vertical_edge_with_ratio(context)

    def _resize_horizontal_edge_with_ratio(self, context: EdgeResizeContext) -> Rect:
        """Handle resizing horizontal edges with fixed aspect ratio."""
        if not self._crop_ratio:
            return Rect(0, 0, 0, 0)

        w, h = self._crop_ratio
        target_ratio = w / h
        center_y = int(context.rect.center_y)

        params = ResizeParameters(
            handle=context.handle,
            mouse=context.mouse,
            rect=context.rect,
            target_ratio=target_ratio,
            center_point=center_y,
        )
        constraints = get_horizontal_constraints(params)
        return apply_horizontal_bounds_constraints(constraints, context.bounds, context.handle, target_ratio)

    def _resize_vertical_edge_with_ratio(self, context: EdgeResizeContext) -> Rect:
        """Handle resizing vertical edges with fixed aspect ratio."""
        if not self._crop_ratio:
            return Rect(0, 0, 0, 0)

        w, h = self._crop_ratio
        target_ratio = w / h
        center_x = int(context.rect.center_x)

        params = ResizeParameters(
            handle=context.handle,
            mouse=context.mouse,
            rect=context.rect,
            target_ratio=target_ratio,
            center_point=center_x,
        )
        constraints = get_vertical_constraints(params)
        return apply_vertical_bounds_constraints(constraints, context.bounds, context.handle, target_ratio)

    def _clamp_point_to_bounds(self, point: QPointF, bounds: QRectF) -> QPointF:
        """Clamp a point to image bounds."""
        result = clamp_point_to_bounds(Point(point.x(), point.y()), _qrectf_to_rect(bounds))
        return QPointF(result.x, result.y)

    def _clamp_rect_to_bounds(self, rect: QRect, bounds: QRectF) -> QRect:
        """Clamp a rectangle to image bounds."""
        result = clamp_rect_to_bounds(_qrect_to_rect(rect), _qrectf_to_rect(bounds))
        return _rect_to_qrect(result)

    def constrain_crop_rect(self, photo: Union[QGraphicsPixmapItem, None]) -> None:
        """Constrain the crop rectangle to stay within image bounds."""
        if not self._rectangles["current"] or not photo:
            return

        # Get image bounds
        bounds = photo.boundingRect()
        min_x = int(bounds.left())
        max_x = int(bounds.right())
        min_y = int(bounds.top())
        max_y = int(bounds.bottom())

        # Store original dimensions
        crop_rect = self._rectangles["current"]
        original_width = crop_rect.width()
        original_height = crop_rect.height()

        # Create a new rectangle with constrained coordinates
        new_rect = QRect(
            int(max(min_x, min(max_x - original_width, crop_rect.left()))),
            int(max(min_y, min(max_y - original_height, crop_rect.top()))),
            original_width,
            original_height,
        )

        # Update the crop rectangle
        self._rectangles["current"] = new_rect

        # If we have a fixed ratio, maintain it
        if self._crop_ratio:
            self.adjust_crop_rect_to_ratio(photo)

    def draw_foreground(self, painter: QPainter, _: QRectF, scene_rect: QRectF) -> None:
        """Draw the crop rectangle and handles when in crop mode."""
        if not self._state["crop_mode"] or not self._rectangles["current"]:
            return

        crop_rect = self._rectangles["current"]

        # Draw semi-transparent overlay
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setBrush(QColor(0, 0, 0, 128))
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw overlay only outside the crop rectangle
        painter.drawRect(
            QRectF(scene_rect.left(), scene_rect.top(), crop_rect.left() - scene_rect.left(), scene_rect.height())
        )
        painter.drawRect(
            QRectF(
                crop_rect.right(),
                scene_rect.top(),
                scene_rect.right() - crop_rect.right(),
                scene_rect.height(),
            )
        )
        painter.drawRect(
            QRectF(
                crop_rect.left(),
                scene_rect.top(),
                crop_rect.width(),
                crop_rect.top() - scene_rect.top(),
            )
        )
        painter.drawRect(
            QRectF(
                crop_rect.left(),
                crop_rect.bottom(),
                crop_rect.width(),
                scene_rect.bottom() - crop_rect.bottom(),
            )
        )

        # Draw grid within the crop rectangle only if valid
        if crop_rect.isValid() and not crop_rect.isEmpty():
            self._grid_overlay.draw_grid(painter, crop_rect)

        # Draw crop rectangle
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(QColor("white"), 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawRect(crop_rect)

        # Draw handles
        handle_size = 8
        pen = QPen(QColor("white"), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(QColor("white"))

        self._draw_crop_handles(painter, crop_rect, handle_size)

    def _draw_crop_handles(self, painter: QPainter, rect: QRect, handle_size: int) -> None:
        """Draw the crop handles at the corners and edges of the crop rectangle."""
        # Draw corner handles
        corners = [
            (rect.left(), rect.top(), "top_left"),
            (rect.right(), rect.top(), "top_right"),
            (rect.left(), rect.bottom(), "bottom_left"),
            (rect.right(), rect.bottom(), "bottom_right"),
        ]
        for x, y, _ in corners:
            handle_rect = QRectF(
                float(x) - handle_size / 2, float(y) - handle_size / 2, float(handle_size), float(handle_size)
            )
            painter.drawRect(handle_rect)

        # Draw edge handles
        edges = [
            (int(rect.left() + rect.width() / 2), rect.top(), "top"),
            (rect.right(), int(rect.top() + rect.height() / 2), "right"),
            (int(rect.left() + rect.width() / 2), rect.bottom(), "bottom"),
            (rect.left(), int(rect.top() + rect.height() / 2), "left"),
        ]
        for x, y, _ in edges:
            handle_rect = QRectF(
                float(x) - handle_size / 2, float(y) - handle_size / 2, float(handle_size), float(handle_size)
            )
            painter.drawRect(handle_rect)

    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        """Handle mouse press events for crop mode."""
        if not self._state["crop_mode"]:
            return False

        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_info["handle"] = self.get_handle_at(event.pos())
            if self._drag_info["handle"]:
                self._state["dragging"] = True
                self._drag_info["start"] = self.view.mapToScene(event.pos())
                self._rectangles["original"] = self._rectangles["current"]  # Store original rect

                self._drag_info["anchor_point"] = self.get_anchor_point(
                    str(self._drag_info["handle"]), self._rectangles["current"]
                )

                # Store fixed edges for corner handles
                # Convert Qt's inclusive edges to exclusive edges for pure geometry functions
                if (
                    self._drag_info["handle"] in ["top_left", "top_right", "bottom_left", "bottom_right"]
                    and self._rectangles["current"] is not None
                ):
                    rect = self._rectangles["current"]
                    self._drag_info["fixed_edges"] = {
                        "top": rect.top(),
                        "bottom": rect.bottom() + 1,  # Qt's .bottom() is inclusive; convert to exclusive
                        "left": rect.left(),
                        "right": rect.right() + 1,  # Qt's .right() is inclusive; convert to exclusive
                    }
                else:
                    self._drag_info["fixed_edges"] = None

                if self._drag_info["handle"] == "move":
                    self.view.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return True
        return False

    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        """Handle mouse release events for crop mode."""
        if not self._state["crop_mode"]:
            return False

        if event.button() == Qt.MouseButton.LeftButton and self._state["dragging"]:
            self._state["dragging"] = False
            self._drag_info["handle"] = None
            # Update cursor based on current position
            handle = self.get_handle_at(event.pos())
            self.update_cursor_for_handle(handle)
            event.accept()
            return True
        return False

    def handle_mouse_move(self, event: QMouseEvent, photo: Union[QGraphicsPixmapItem, None]) -> bool:
        """Handle mouse move events for crop mode."""
        if not self._state["crop_mode"]:
            return False

        if self._state["dragging"] and self._rectangles["current"]:
            current_pos = self.view.mapToScene(event.pos())
            if self._drag_info["handle"] == "move" and isinstance(self._drag_info["start"], QPointF):
                delta = current_pos - self._drag_info["start"]
                self._drag_info["start"] = current_pos
                self._rectangles["current"].translate(int(delta.x()), int(delta.y()))
            else:
                handle = self._drag_info["handle"] if isinstance(self._drag_info["handle"], str) else None
                self.resize_crop_rect_from_anchor(handle, current_pos, photo)
            self.constrain_crop_rect(photo)
            self.view.viewport().update()  # type: ignore[union-attr]
            event.accept()
            return True

        # Update cursor based on handle under mouse
        handle = self.get_handle_at(event.pos())
        self.update_cursor_for_handle(handle)
        event.accept()
        return True

    def apply_crop(self, photo: QGraphicsPixmapItem) -> QPixmap:
        """
        Apply the crop rectangle to the image and return the cropped pixmap.

        Args:
            photo (QGraphicsPixmapItem): The photo to crop

        Returns:
            QPixmap: The cropped image
        """
        if not self._rectangles["saved"] or not photo or not photo.pixmap():
            return photo.pixmap() if photo and photo.pixmap() else QPixmap()

        # Extract the portion of the image defined by the crop rectangle
        original_pixmap = photo.pixmap()

        # Ensure crop rectangle is valid and within bounds
        crop_rect = self._rectangles["saved"].intersected(
            QRect(0, 0, original_pixmap.width(), original_pixmap.height())
        )

        # Only crop if we have a valid rectangle
        if crop_rect.isValid() and crop_rect.width() > 0 and crop_rect.height() > 0:
            cropped_pixmap = original_pixmap.copy(crop_rect)
            return cropped_pixmap

        # Return original if crop isn't valid
        return original_pixmap
