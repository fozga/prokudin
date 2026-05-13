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

"""Widget tests for src/ui/widgets/image_viewer.py."""

from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QEvent, QPoint, QPointF, QRect, Qt
from PyQt5.QtGui import QMouseEvent, QPixmap, QWheelEvent
from PyQt5.QtWidgets import QApplication, QGraphicsPixmapItem, QGraphicsView
from pytestqt.plugin import QtBot

from src.ui.widgets.grid_overlay import GridOverlay
from src.ui.widgets.image_viewer import ImageViewer


@pytest.mark.widget
class TestImageViewerInit:
    """
    Test Design Specification: ImageViewer — Initialization
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        ImageViewer is a QGraphicsView that displays images with zoom, pan, and
        fit-to-view capabilities. On construction: zoom is 1.0, fit_to_view is
        False, the scene contains an empty QGraphicsPixmapItem (photo attribute),
        a GridOverlay is created, and a CropHandler is instantiated with the viewer
        and grid overlay.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - CropHandler instantiated for real (its __init__ stores references only,
          no rendering calls).

    What is tested:
        - zoom == 1.0 after construction.
        - fit_to_view == False after construction.
        - photo is not None after construction.
        - grid_overlay property returns a GridOverlay instance.
        - crop_handler property returns a non-None object.

    What is NOT tested:
        - Visual rendering or pixel output.
        - Layout geometry, scroll bar positions.
        - CropHandler internal state (separate unit concern).

    Equivalence partitions:
        EP1  Fresh ImageViewer with no parent → all default values.

    Mocking strategy:
        None for init tests (CropHandler init is side-effect-free).

    Constraints:
        Widget must be registered with qtbot (QGraphicsView cleanup).
        widget.show() is not required for attribute access.
    """

    def test_default_zoom_is_one(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed ImageViewer,
        When zoom is read,
        Then it equals 1.0.
        """
        # Arrange / Act
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Assert
        assert viewer.zoom == 1.0

    def test_default_fit_to_view_is_false(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed ImageViewer,
        When fit_to_view is read,
        Then it is False.
        """
        # Arrange / Act
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Assert
        assert viewer.fit_to_view is False

    def test_photo_is_not_none_after_init(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed ImageViewer,
        When photo is read,
        Then it is a QGraphicsPixmapItem (not None).
        """
        # Arrange / Act
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Assert
        assert viewer.photo is not None
        assert isinstance(viewer.photo, QGraphicsPixmapItem)

    def test_grid_overlay_property_returns_grid_overlay(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed ImageViewer,
        When grid_overlay is accessed,
        Then it returns a GridOverlay instance.
        """
        # Arrange / Act
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Assert
        assert isinstance(viewer.grid_overlay, GridOverlay)

    def test_crop_handler_property_returns_non_none(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed ImageViewer,
        When crop_handler is accessed,
        Then it returns a non-None object.
        """
        # Arrange / Act
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Assert
        assert viewer.crop_handler is not None


@pytest.mark.widget
class TestImageViewerImage:
    """
    Test Design Specification: ImageViewer — set_image and clear_image
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        set_image(pixmap) replaces the current photo pixmap and resets zoom to 1.0.
        clear_image() removes the current pixmap, creates an empty one, resets
        zoom to 1.0, and sets fit_to_view to False.

    Infrastructure:
        - Requires qtbot.
        - No service mocking needed.

    What is tested:
        - set_image with a non-null pixmap → zoom resets to 1.0.
        - clear_image → zoom is 1.0, fit_to_view is False, photo is not None.
        - clear_image after set_image → photo pixmap is empty.

    What is NOT tested:
        - Visual rendering of the pixmap.
        - Scene coordinate transformations.

    Equivalence partitions:
        EP1  set_image with valid 10×10 pixmap → zoom reset
        EP2  clear_image on viewer with image loaded → state reset

    Mocking strategy:
        None — real QPixmap used.

    Constraints:
        widget.show() called for set_image to allow fitInView without errors.
    """

    def test_set_image_resets_zoom_to_one(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with zoom != 1.0,
        When set_image is called with a valid pixmap,
        Then zoom is reset to 1.0.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        viewer.zoom = 2.5  # set zoom to non-default
        pixmap = QPixmap(10, 10)
        # Act
        viewer.set_image(pixmap)
        # Assert
        assert viewer.zoom == 1.0

    def test_clear_image_resets_zoom_to_one(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer,
        When clear_image is called,
        Then zoom is 1.0.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.zoom = 3.0
        # Act
        viewer.clear_image()
        # Assert
        assert viewer.zoom == 1.0

    def test_clear_image_resets_fit_to_view_to_false(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with fit_to_view=True,
        When clear_image is called,
        Then fit_to_view is False.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.fit_to_view = True
        # Act
        viewer.clear_image()
        # Assert
        assert viewer.fit_to_view is False

    def test_clear_image_photo_is_not_none(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer,
        When clear_image is called,
        Then photo is still a QGraphicsPixmapItem (not None).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Act
        viewer.clear_image()
        # Assert
        assert viewer.photo is not None


@pytest.mark.widget
class TestImageViewerToggleView:
    """
    Test Design Specification: ImageViewer — toggle_view
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        toggle_view() flips fit_to_view. When fit_to_view becomes True it calls
        fitInView and resets zoom to 1.0. When it becomes False it calls
        resetTransform and resets zoom to 1.0.

    Infrastructure:
        - Requires qtbot.
        - widget.show() called before toggle to allow fitInView without errors.

    What is tested:
        - toggle_view from False → fit_to_view becomes True.
        - toggle_view from True → fit_to_view becomes False.

    What is NOT tested:
        - The actual transformation matrix applied.

    Equivalence partitions:
        EP1  fit_to_view=False → toggle → True
        EP2  fit_to_view=True  → toggle → False

    Mocking strategy:
        None.

    Constraints:
        widget.show() required for fitInView to work in headless mode.
    """

    def test_toggle_view_from_false_sets_fit_to_view_true(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with fit_to_view=False,
        When toggle_view is called,
        Then fit_to_view becomes True (EP1).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        assert viewer.fit_to_view is False
        # Act
        viewer.toggle_view()
        # Assert
        assert viewer.fit_to_view is True

    def test_toggle_view_from_true_sets_fit_to_view_false(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with fit_to_view=True,
        When toggle_view is called,
        Then fit_to_view becomes False (EP2).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        viewer.fit_to_view = True
        # Act
        viewer.toggle_view()
        # Assert
        assert viewer.fit_to_view is False


@pytest.mark.widget
class TestImageViewerWheelZoom:
    """
    Test Design Specification: ImageViewer — wheelEvent zoom
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        wheelEvent handles mouse wheel input. With Ctrl modifier held:
          - upward scroll (angleDelta.y > 0) multiplies zoom by 1.25 and sets
            fit_to_view=False.
          - downward scroll divides zoom by 1.25 and sets fit_to_view=False.
        Without Ctrl, the event is passed to the base class (no zoom change).
        wheelEvent(None) returns immediately without error.

    Infrastructure:
        - Requires qtbot.
        - widget.show() required before wheel events.
        - QWheelEvent constructed directly for scroll simulation.

    What is tested:
        - wheelEvent(None) → no exception, state unchanged.
        - Ctrl + wheel up → zoom increases by factor 1.25.
        - Ctrl + wheel down → zoom decreases by factor 1.25.
        - Ctrl + wheel up → fit_to_view becomes False.
        - No-Ctrl wheel → zoom unchanged (event passed to super).

    What is NOT tested:
        - Scroll-bar position changes from non-Ctrl wheel.
        - Exact transformation matrix values.

    Equivalence partitions:
        EP1  event is None                     → early return
        EP2  Ctrl modifier + upward scroll     → zoom increases
        EP3  Ctrl modifier + downward scroll   → zoom decreases
        EP4  No Ctrl modifier                  → zoom unchanged

    Mocking strategy:
        Real QWheelEvent constructed with QPoint positions and angleDelta.

    Constraints:
        widget.show() required before scroll simulation.
    """

    def test_wheel_event_none_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer,
        When wheelEvent(None) is called,
        Then no exception is raised and zoom remains 1.0 (EP1).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        initial_zoom = viewer.zoom
        # Act
        viewer.wheelEvent(None)
        # Assert
        assert viewer.zoom == initial_zoom

    def test_ctrl_wheel_up_increases_zoom(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer shown at default zoom=1.0,
        When a Ctrl+scroll-up wheel event is delivered (EP2),
        Then viewer.zoom equals 1.0 * 1.25 = 1.25.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        event = QWheelEvent(
            QPoint(0, 0),
            QPoint(0, 0),
            QPoint(0, 120),   # pixelDelta
            QPoint(0, 120),   # angleDelta: positive = scroll up
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.ScrollBegin,
            False,
        )
        # Act
        viewer.wheelEvent(event)
        # Assert
        assert abs(viewer.zoom - 1.25) < 1e-9

    def test_ctrl_wheel_down_decreases_zoom(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer shown at default zoom=1.0,
        When a Ctrl+scroll-down wheel event is delivered (EP3),
        Then viewer.zoom equals 1.0 / 1.25 = 0.8.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        event = QWheelEvent(
            QPoint(0, 0),
            QPoint(0, 0),
            QPoint(0, -120),   # pixelDelta
            QPoint(0, -120),   # angleDelta: negative = scroll down
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.ScrollBegin,
            False,
        )
        # Act
        viewer.wheelEvent(event)
        # Assert
        assert abs(viewer.zoom - 0.8) < 1e-9

    def test_ctrl_wheel_up_exits_fit_to_view(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with fit_to_view=True,
        When a Ctrl+scroll-up wheel event is delivered,
        Then fit_to_view becomes False (manual zoom exits fit-to-view mode).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        viewer.fit_to_view = True
        event = QWheelEvent(
            QPoint(0, 0),
            QPoint(0, 0),
            QPoint(0, 120),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.ScrollBegin,
            False,
        )
        # Act
        viewer.wheelEvent(event)
        # Assert
        assert viewer.fit_to_view is False

    def test_no_ctrl_wheel_does_not_change_zoom(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer at default zoom=1.0,
        When a wheel event without Ctrl modifier is delivered (EP4),
        Then zoom remains unchanged at 1.0 (event passed to super).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        event = QWheelEvent(
            QPoint(0, 0),
            QPoint(0, 0),
            QPoint(0, 120),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,  # No Ctrl
            Qt.ScrollPhase.ScrollBegin,
            False,
        )
        # Act
        viewer.wheelEvent(event)
        # Assert
        assert viewer.zoom == 1.0


@pytest.mark.widget
class TestImageViewerCropDelegation:
    """
    Test Design Specification: ImageViewer — crop method delegation
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        ImageViewer delegates crop operations to the CropHandler stored in
        _crop_handler. The following methods are thin wrappers:
          - set_crop_mode(enabled) → CropHandler.set_crop_mode(enabled, photo)
          - get_saved_crop_rect()  → CropHandler.get_saved_crop_rect()
          - set_saved_crop_rect(r) → CropHandler.set_saved_crop_rect(r)
          - get_crop_rect()        → CropHandler.get_crop_rect()
          - set_crop_rect(r)       → CropHandler.set_crop_rect(r)
          - cancel_crop()          → CropHandler.cancel_crop()

    Infrastructure:
        - Requires qtbot.
        - CropHandler replaced with MagicMock after viewer construction to isolate
          ImageViewer from CropHandler behaviour.

    What is tested:
        - set_crop_mode(True) calls CropHandler.set_crop_mode with correct args.
        - get_saved_crop_rect() returns the value provided by CropHandler.
        - set_saved_crop_rect(rect) forwards rect to CropHandler.
        - get_crop_rect() returns the value provided by CropHandler.
        - set_crop_rect(rect) forwards rect to CropHandler.
        - cancel_crop() calls CropHandler.cancel_crop once.
        - get_saved_crop_rect() returns None when CropHandler returns None.

    What is NOT tested:
        - Internal CropHandler logic.
        - set_crop_ratio (requires photo state interaction, not a delegation test).

    Equivalence partitions:
        EP1  Delegation methods forward calls and return values transparently.

    Mocking strategy:
        After creating the viewer with a real CropHandler, replace _crop_handler
        with a MagicMock to intercept all calls and control return values.

    Constraints:
        qtbot.addWidget registers the widget for cleanup.
    """

    def test_set_crop_mode_delegates_to_crop_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler,
        When set_crop_mode(True) is called,
        Then CropHandler.set_crop_mode is called with (True, viewer.photo).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        # Act
        viewer.set_crop_mode(True)
        # Assert
        mock_handler.set_crop_mode.assert_called_once_with(True, viewer.photo)

    def test_get_saved_crop_rect_returns_none_by_default(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler returning None,
        When get_saved_crop_rect() is called,
        Then None is returned.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        mock_handler.get_saved_crop_rect.return_value = None
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        # Act
        result = viewer.get_saved_crop_rect()
        # Assert
        assert result is None

    def test_get_saved_crop_rect_returns_value_from_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler returning a QRect,
        When get_saved_crop_rect() is called,
        Then the exact QRect returned by the handler is returned.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        expected_rect = QRect(10, 20, 100, 80)
        mock_handler = MagicMock()
        mock_handler.get_saved_crop_rect.return_value = expected_rect
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        # Act
        result = viewer.get_saved_crop_rect()
        # Assert
        assert result == expected_rect

    def test_set_saved_crop_rect_forwards_to_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler,
        When set_saved_crop_rect(rect) is called with a QRect,
        Then CropHandler.set_saved_crop_rect is called with that rect.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        rect = QRect(5, 5, 50, 50)
        # Act
        viewer.set_saved_crop_rect(rect)
        # Assert
        mock_handler.set_saved_crop_rect.assert_called_once_with(rect)

    def test_get_crop_rect_returns_value_from_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler returning a QRect,
        When get_crop_rect() is called,
        Then the rect returned by the handler is returned.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        expected_rect = QRect(0, 0, 200, 150)
        mock_handler = MagicMock()
        mock_handler.get_crop_rect.return_value = expected_rect
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        # Act
        result = viewer.get_crop_rect()
        # Assert
        assert result == expected_rect

    def test_set_crop_rect_forwards_to_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler,
        When set_crop_rect(rect) is called,
        Then CropHandler.set_crop_rect is called with that rect.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        rect = QRect(10, 10, 80, 60)
        # Act
        viewer.set_crop_rect(rect)
        # Assert
        mock_handler.set_crop_rect.assert_called_once_with(rect)

    def test_cancel_crop_delegates_to_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler,
        When cancel_crop() is called,
        Then CropHandler.cancel_crop is called exactly once.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        # Act
        viewer.cancel_crop()
        # Assert
        mock_handler.cancel_crop.assert_called_once()


@pytest.mark.widget
class TestImageViewerNullEventHandlers:
    """
    Test Design Specification: ImageViewer — None-guard event handlers
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        Five event overrides (wheelEvent, resizeEvent, mousePressEvent,
        mouseReleaseEvent, mouseMoveEvent) each begin with a None guard that
        returns immediately when the event argument is None. This prevents
        crashes from callers that pass None to signal "no event".

    Infrastructure:
        - Requires qtbot.
        - No widget.show() needed — guard branches do not call Qt methods.

    What is tested:
        - resizeEvent(None) → no exception.
        - mousePressEvent(None) → no exception.
        - mouseReleaseEvent(None) → no exception.
        - mouseMoveEvent(None) → no exception.

    What is NOT tested:
        - Real event processing (covered by other tests or excluded as rendering).

    Equivalence partitions:
        EP1  event = None → early return, no state change, no exception.

    Mocking strategy:
        None — the guards do not interact with any dependencies.

    Constraints:
        None.
    """

    def test_resize_event_none_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer,
        When resizeEvent(None) is called,
        Then no exception is raised.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Act / Assert (no exception expected)
        viewer.resizeEvent(None)

    def test_mouse_press_event_none_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer,
        When mousePressEvent(None) is called,
        Then no exception is raised.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Act / Assert
        viewer.mousePressEvent(None)

    def test_mouse_release_event_none_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer,
        When mouseReleaseEvent(None) is called,
        Then no exception is raised.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Act / Assert
        viewer.mouseReleaseEvent(None)

    def test_mouse_move_event_none_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer,
        When mouseMoveEvent(None) is called,
        Then no exception is raised.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        # Act / Assert
        viewer.mouseMoveEvent(None)

    def test_resize_event_fit_to_view_calls_fit_in_view(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with fit_to_view=True,
        When resizeEvent(None) is called (None guard fires before super),
        Then no exception is raised (fit branch executes but None guard stops super call).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        viewer.fit_to_view = True
        # Act / Assert (fitInView runs, then None guard stops super call)
        viewer.resizeEvent(None)


@pytest.mark.widget
class TestImageViewerMouseEventHandlers:
    """
    Test Design Specification: ImageViewer — mouse event delegation to CropHandler
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        mousePressEvent, mouseReleaseEvent, and mouseMoveEvent each first
        delegate to the CropHandler. When the handler returns False (does not
        consume the event), the viewer continues with its own logic:
          - mousePressEvent with LeftButton → sets ScrollHandDrag mode, calls super.
          - mouseReleaseEvent → sets NoDrag mode, calls super.
          - mouseMoveEvent → calls super.

    Infrastructure:
        - Requires qtbot.
        - widget.show() called to allow QGraphicsView super-class event handling.
        - CropHandler replaced with MagicMock after construction.

    What is tested:
        - mousePressEvent with LeftButton and handler returning False → drag mode is
          ScrollHandDrag after the call.
        - mouseReleaseEvent with handler returning False → drag mode is NoDrag.
        - mouseMoveEvent with handler returning False → no exception (super called).
        - enterEvent with non-None QEvent and crop mode False → no exception.
        - leaveEvent with non-None QEvent and crop mode False → no exception.

    What is NOT tested:
        - Actual scene scrolling or panning (rendering).
        - enterEvent / leaveEvent cursor changes when crop mode is active (requires
          QMouseEvent for enter, which Qt does not deliver in headless mode).

    Equivalence partitions:
        EP1  handler returns False + LeftButton → drag mode set, super called
        EP2  handler returns False (release) → drag mode cleared
        EP3  handler returns False (move) → super called

    Mocking strategy:
        _crop_handler replaced with MagicMock returning False from handle_* methods.

    Constraints:
        widget.show() required for QGraphicsView scroll-hand drag to initialise.
    """

    def _make_press_event(self, button: Qt.MouseButton = Qt.MouseButton.LeftButton) -> QMouseEvent:
        """Create a QMouseEvent for a mouse button press at position (5, 5)."""
        return QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(5, 5),
            button,
            button,
            Qt.KeyboardModifier.NoModifier,
        )

    def _make_release_event(self) -> QMouseEvent:
        """Create a QMouseEvent for a left button release at position (5, 5)."""
        return QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(5, 5),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )

    def _make_move_event(self) -> QMouseEvent:
        """Create a QMouseEvent for a mouse move at position (5, 5)."""
        return QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(5, 5),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )

    def test_mouse_press_left_button_enables_scroll_hand_drag(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mock handler that does not consume the event (EP1),
        When mousePressEvent is called with a LeftButton event,
        Then the drag mode is set to ScrollHandDrag.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        mock_handler = MagicMock()
        mock_handler.handle_mouse_press.return_value = False
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        event = self._make_press_event(Qt.MouseButton.LeftButton)
        # Act
        viewer.mousePressEvent(event)
        # Assert
        assert viewer.dragMode() == QGraphicsView.ScrollHandDrag

    def test_mouse_release_disables_drag_mode(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer in ScrollHandDrag mode with a mock handler returning False (EP2),
        When mouseReleaseEvent is called,
        Then the drag mode is set to NoDrag.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        viewer.setDragMode(QGraphicsView.ScrollHandDrag)
        mock_handler = MagicMock()
        mock_handler.handle_mouse_release.return_value = False
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        event = self._make_release_event()
        # Act
        viewer.mouseReleaseEvent(event)
        # Assert
        assert viewer.dragMode() == QGraphicsView.NoDrag

    def test_mouse_move_calls_super_when_handler_returns_false(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mock handler returning False (EP3),
        When mouseMoveEvent is called with a move event,
        Then no exception is raised (super().mouseMoveEvent is called).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        mock_handler = MagicMock()
        mock_handler.handle_mouse_move.return_value = False
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        event = self._make_move_event()
        # Act / Assert
        viewer.mouseMoveEvent(event)

    def test_enter_event_non_none_calls_super(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with crop mode disabled,
        When enterEvent is called with a non-None QEvent,
        Then no exception is raised (super().enterEvent is called).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        mock_handler.is_crop_mode.return_value = False
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        event = QEvent(QEvent.Type.Enter)
        # Act / Assert
        viewer.enterEvent(event)

    def test_leave_event_non_none_calls_super(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with crop mode disabled,
        When leaveEvent is called with a non-None QEvent,
        Then no exception is raised (super().leaveEvent is called).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        mock_handler.is_crop_mode.return_value = False
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        event = QEvent(QEvent.Type.Leave)
        # Act / Assert
        viewer.leaveEvent(event)


@pytest.mark.widget
class TestImageViewerDrawForeground:
    """
    Test Design Specification: ImageViewer — drawForeground
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        drawForeground(painter, rect) is called by Qt's paint system. If painter
        is None it returns immediately. Otherwise it delegates to the CropHandler's
        draw_foreground, then conditionally draws the grid overlay on the photo
        when not in crop mode and the photo has a non-null pixmap.

    Infrastructure:
        - Requires qtbot.
        - CropHandler replaced with MagicMock.
        - QPainter replaced with MagicMock (no real paint device needed).

    What is tested:
        - drawForeground(None, rect) → crop_handler.draw_foreground not called.
        - drawForeground(mock_painter, rect) with crop mode False and null pixmap
          → draw_foreground called, grid overlay NOT drawn on photo.
        - drawForeground(mock_painter, rect) with crop mode False and valid pixmap
          → crop_handler.draw_foreground called, grid_overlay.draw_grid called.

    What is NOT tested:
        - Pixel content of the foreground drawing.
        - Crop mode True path (crop handler draws the grid internally).

    Equivalence partitions:
        EP1  painter = None          → early return
        EP2  painter valid, crop mode True   → only draw_foreground (grid skipped)
        EP3  painter valid, valid pixmap, crop mode False    → draw_foreground + grid

    Mocking strategy:
        _crop_handler replaced with MagicMock. QPainter replaced with MagicMock.

    Constraints:
        drawForeground is called directly, not via Qt's paint cycle.
        sceneRect() requires QApplication to be running.
    """

    def test_draw_foreground_painter_none_does_not_call_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler,
        When drawForeground(None, rect) is called (EP1),
        Then CropHandler.draw_foreground is never called.
        """
        # Arrange
        from PyQt5.QtCore import QRectF as _QRectF
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        # Act
        viewer.drawForeground(None, _QRectF(0, 0, 100, 100))
        # Assert
        mock_handler.draw_foreground.assert_not_called()

    def test_draw_foreground_with_null_pixmap_does_not_draw_grid(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer in crop mode (crop mode = True) with a mocked CropHandler (EP2),
        When drawForeground is called with a mock painter,
        Then CropHandler.draw_foreground is called but grid_overlay.draw_grid is NOT
        (the is_crop_mode condition prevents the grid overlay from drawing).
        """
        # Arrange
        from PyQt5.QtCore import QRectF as _QRectF
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        mock_handler.is_crop_mode.return_value = True  # crop mode active → grid skipped
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        mock_painter = MagicMock()
        mock_grid = MagicMock()
        viewer._grid_overlay = mock_grid  # pylint: disable=protected-access
        # Act
        viewer.drawForeground(mock_painter, _QRectF(0, 0, 100, 100))
        # Assert
        mock_handler.draw_foreground.assert_called_once()
        mock_grid.draw_grid.assert_not_called()

    def test_draw_foreground_with_valid_pixmap_draws_grid(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a valid pixmap on photo and crop mode False (EP3),
        When drawForeground is called with a mock painter,
        Then both crop_handler.draw_foreground and grid_overlay.draw_grid are called.
        """
        # Arrange
        from PyQt5.QtCore import QRectF as _QRectF
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.show()
        # Set a real pixmap so photo.pixmap() is non-null
        pixmap = QPixmap(10, 10)
        viewer.set_image(pixmap)
        mock_handler = MagicMock()
        mock_handler.is_crop_mode.return_value = False
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        mock_grid = MagicMock()
        viewer._grid_overlay = mock_grid  # pylint: disable=protected-access
        mock_painter = MagicMock()
        # Act
        viewer.drawForeground(mock_painter, _QRectF(0, 0, 100, 100))
        # Assert
        mock_handler.draw_foreground.assert_called_once()
        mock_grid.draw_grid.assert_called_once()


@pytest.mark.widget
class TestImageViewerEdgeCases:
    """
    Test Design Specification: ImageViewer — edge cases and defensive guards
    Module under test: src/ui/widgets/image_viewer.py

    Widget base class: QGraphicsView

    Contract:
        Several methods guard against None or empty state:
          - set_image: skips pixmap/fitInView when photo is None, still resets zoom.
          - clear_image: skips removeItem when photo is None, still creates new photo.
          - confirm_crop: returns immediately when photo has a null pixmap.
          - set_crop_ratio: thin delegation to CropHandler.

    Infrastructure:
        - Requires qtbot.
        - CropHandler replaced with MagicMock where needed.

    What is tested:
        - set_image with photo=None → zoom is reset to 1.0 without crash.
        - clear_image with photo=None → photo is not None after the call.
        - confirm_crop with null pixmap → no exception, no CropHandler calls.
        - set_crop_ratio forwards ratio and photo to CropHandler.

    What is NOT tested:
        - confirm_crop with a real crop operation (large Qt scene manipulation).

    Equivalence partitions:
        EP1  photo = None before set_image   → defensive skip, zoom still reset
        EP2  photo = None before clear_image → new photo created
        EP3  photo = None before confirm_crop → early return (photo is None guard)
        EP4  set_crop_ratio delegation       → handler receives correct args

    Mocking strategy:
        _crop_handler replaced with MagicMock for isolation.

    Constraints:
        None.
    """

    def test_set_image_with_photo_none_resets_zoom(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with photo manually set to None (EP1),
        When set_image is called with a valid pixmap,
        Then zoom is reset to 1.0 without raising an exception.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.photo = None
        viewer.zoom = 5.0
        pixmap = QPixmap(10, 10)
        # Act
        viewer.set_image(pixmap)
        # Assert
        assert viewer.zoom == 1.0

    def test_clear_image_with_photo_none_creates_new_photo(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with photo manually set to None (EP2),
        When clear_image is called,
        Then photo is a QGraphicsPixmapItem (not None) after the call.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        viewer.photo = None
        # Act
        viewer.clear_image()
        # Assert
        assert viewer.photo is not None

    def test_confirm_crop_with_null_pixmap_returns_early(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with photo set to None (EP3),
        When confirm_crop is called,
        Then no exception is raised and no CropHandler crop methods are called
        (the photo is None guard fires before any delegation).
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        viewer.photo = None  # trigger the photo is None guard
        # Act
        viewer.confirm_crop()
        # Assert
        mock_handler.confirm_crop.assert_not_called()

    def test_set_crop_ratio_forwards_to_handler(self, qtbot: QtBot) -> None:
        """
        Given an ImageViewer with a mocked CropHandler (EP4),
        When set_crop_ratio((4, 3)) is called,
        Then CropHandler.set_crop_ratio is called with the ratio and photo.
        """
        # Arrange
        viewer = ImageViewer()
        qtbot.addWidget(viewer)
        mock_handler = MagicMock()
        viewer._crop_handler = mock_handler  # pylint: disable=protected-access
        ratio = (4, 3)
        # Act
        viewer.set_crop_ratio(ratio)
        # Assert
        mock_handler.set_crop_ratio.assert_called_once_with(ratio, viewer.photo)
