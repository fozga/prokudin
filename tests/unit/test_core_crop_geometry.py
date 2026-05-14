"""Unit tests for src.core.crop_geometry module.

Tests pure geometry logic: clamping, ratio adjustment, corner/edge resizing,
and anchor point calculation. No Qt dependency.
"""

import pytest

from src.core.crop_geometry import (
    EdgeConstraints,
    EdgeResizeContext,
    Point,
    Rect,
    ResizeParameters,
    adjust_dimensions_to_ratio,
    apply_horizontal_bounds_constraints,
    apply_vertical_bounds_constraints,
    clamp_point_to_bounds,
    clamp_rect_to_bounds,
    edge_resize_free_aspect,
    get_anchor_point,
    get_horizontal_constraints,
    get_vertical_constraints,
    resize_bottom_left,
    resize_bottom_right,
    resize_top_left,
    resize_top_right,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def unit_bounds() -> Rect:
    """1000×800 image bounds at origin."""
    return Rect(0, 0, 1000, 800)


@pytest.fixture
def center_rect() -> Rect:
    """200×150 rectangle centred in a 1000×800 image (left=400, top=325)."""
    return Rect(400, 325, 200, 150)


# ---------------------------------------------------------------------------
# TestRect
# ---------------------------------------------------------------------------


class TestRect:
    """
    Test Design Specification: Rect dataclass
    Module under test: src/core/crop_geometry.py

    Contract:
        Stores (left, top, width, height) as integer fields and exposes four
        computed properties: right = left + width, bottom = top + height,
        center_x = left + width / 2, center_y = top + height / 2.

    Equivalence partitions:
        EP1  Zero-size rectangle        → right == left, bottom == top
        EP2  Typical positive rectangle → all properties correct
        EP3  Negative left/top          → off-screen rect; properties still correct

    Boundary values:
        BV1  width=0, height=0   (zero-size)
        BV2  left=0, top=0       (origin-anchored)

    Exclusions:
        - Equality comparisons between Rect instances (dataclass __eq__ is standard)
        - Mutation of fields after construction

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_right_is_left_plus_width(self) -> None:
        """Given Rect(10, 20, 100, 50), when right is accessed, then it equals 109 (inclusive)."""
        # Arrange
        r = Rect(10, 20, 100, 50)
        # Act
        result = r.right
        # Assert
        assert result == 109

    def test_bottom_is_top_plus_height(self) -> None:
        """Given Rect(10, 20, 100, 50), when bottom is accessed, then it equals 69 (inclusive)."""
        # Arrange
        r = Rect(10, 20, 100, 50)
        # Act
        result = r.bottom
        # Assert
        assert result == 69

    def test_center_x(self) -> None:
        """Given Rect(10, 0, 100, 0), when center_x is accessed, then it equals 59.5."""
        # Arrange
        r = Rect(10, 0, 100, 0)
        # Act
        result = r.center_x
        # Assert
        assert result == 59.5

    def test_center_y(self) -> None:
        """Given Rect(0, 20, 0, 80), when center_y is accessed, then it equals 59.5."""
        # Arrange
        r = Rect(0, 20, 0, 80)
        # Act
        result = r.center_y
        # Assert
        assert result == 59.5

    def test_zero_size_rect(self) -> None:
        """Given Rect with zero width and height (BV1), when right/bottom accessed, then they equal left-1/top-1."""
        # Arrange
        r = Rect(5, 7, 0, 0)
        # Act / Assert
        assert r.right == 4
        assert r.bottom == 6

    def test_origin_anchored_rect(self) -> None:
        """Given Rect(0, 0, 100, 80) at origin (BV2), when right/bottom accessed, then they equal width-1/height-1."""
        # Arrange
        r = Rect(0, 0, 100, 80)
        # Act / Assert
        assert r.right == 99
        assert r.bottom == 79

    def test_negative_left_top_properties_correct(self) -> None:
        """Given Rect(-50, -30, 100, 80) with negative origin (EP3), when properties accessed, then correct."""
        # Arrange
        r = Rect(-50, -30, 100, 80)
        # Act / Assert
        assert r.right == 49
        assert r.bottom == 49


# ---------------------------------------------------------------------------
# TestClampPointToBounds
# ---------------------------------------------------------------------------


class TestClampPointToBounds:
    """
    Test Design Specification: clamp_point_to_bounds()
    Module under test: src/core/crop_geometry.py

    Contract:
        Clamp point coordinates so that x ∈ [bounds.left, bounds.right] and
        y ∈ [bounds.top, bounds.bottom]. Returns a new Point; does not mutate
        the input. Coordinates are truncated to int before clamping.

    Equivalence partitions:
        EP1  Point inside bounds            → returned unchanged
        EP2  x < bounds.left               → x clamped to bounds.left
        EP3  x > bounds.right              → x clamped to bounds.right
        EP4  y < bounds.top                → y clamped to bounds.top
        EP5  y > bounds.bottom             → y clamped to bounds.bottom
        EP6  Both axes outside bounds      → both axes clamped independently

    Boundary values:
        BV1  Point exactly at bounds.left  → unchanged
        BV2  Point exactly at bounds.right → unchanged
        BV3  Point exactly at bounds.top   → unchanged
        BV4  Point exactly at bounds.bottom → unchanged

    Exclusions:
        - NaN / inf floating-point inputs (caller guarantees finite values)
        - Sub-pixel fractional precision beyond integer truncation

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_point_inside_bounds_unchanged(self, unit_bounds: Rect) -> None:
        """Given point (500, 400) inside 1000×800 bounds, when clamped, then returned unchanged."""
        # Arrange
        point = Point(500.0, 400.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.x == 500.0
        assert result.y == 400.0

    def test_x_below_left_clamped(self, unit_bounds: Rect) -> None:
        """Given point with x=-5 (left of bounds), when clamped, then x is set to bounds.left=0."""
        # Arrange
        point = Point(-5.0, 400.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.x == 0.0

    def test_x_above_right_clamped(self, unit_bounds: Rect) -> None:
        """Given point with x=1100 (right of bounds), when clamped, then x is set to bounds.right=999."""
        # Arrange
        point = Point(1100.0, 400.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.x == 999.0

    def test_y_above_top_clamped(self, unit_bounds: Rect) -> None:
        """Given point with y=-10 (above bounds), when clamped, then y is set to bounds.top=0."""
        # Arrange
        point = Point(500.0, -10.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.y == 0.0

    def test_y_below_bottom_clamped(self, unit_bounds: Rect) -> None:
        """Given point with y=900 (below bounds), when clamped, then y is set to bounds.bottom=799."""
        # Arrange
        point = Point(500.0, 900.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.y == 799.0

    def test_both_axes_out_of_bounds(self, unit_bounds: Rect) -> None:
        """Given point (-100, 900) with both axes out of bounds (EP6), when clamped, then both are clamped."""
        # Arrange
        point = Point(-100.0, 900.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.x == 0.0
        assert result.y == 799.0

    def test_point_at_left_boundary_unchanged(self, unit_bounds: Rect) -> None:
        """Given point exactly at bounds.left=0 (BV1), when clamped, then x remains 0."""
        # Arrange
        point = Point(0.0, 400.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.x == 0.0

    def test_point_at_right_boundary_unchanged(self, unit_bounds: Rect) -> None:
        """Given point exactly at bounds.right=999 (BV2), when clamped, then x remains 999."""
        # Arrange
        point = Point(999.0, 400.0)
        # Act
        result = clamp_point_to_bounds(point, unit_bounds)
        # Assert
        assert result.x == 999.0


# ---------------------------------------------------------------------------
# TestClampRectToBounds
# ---------------------------------------------------------------------------


class TestClampRectToBounds:
    """
    Test Design Specification: clamp_rect_to_bounds()
    Module under test: src/core/crop_geometry.py

    Contract:
        Returns the intersection of rect and bounds with non-negative dimensions.
        If the rect lies entirely outside bounds on one axis, the width or height
        for that axis becomes 0. The complementary axis is unaffected.

    Equivalence partitions:
        EP1  Rect fully inside bounds         → returned unchanged
        EP2  Rect partially outside left      → left clipped to bounds.left
        EP3  Rect partially outside right     → right clipped to bounds.right
        EP4  Rect partially outside top       → top clipped to bounds.top
        EP5  Rect partially outside bottom    → bottom clipped to bounds.bottom
        EP6  Rect entirely outside bounds (x) → width=0 on the overlapping axis

    Boundary values:
        BV1  Rect right edge exactly equals bounds.right → unchanged
        BV2  Rect left edge 1px outside bounds.left      → width trimmed by 1

    Exclusions:
        - Rects with negative width or height (invalid; not produced by this module)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_rect_inside_bounds_unchanged(self, unit_bounds: Rect) -> None:
        """Given rect fully inside bounds (EP1), when clamped, then returned unchanged."""
        # Arrange
        r = Rect(100, 100, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result == r

    def test_rect_clipped_at_left(self, unit_bounds: Rect) -> None:
        """Given rect extending 50px left of bounds (EP2), when clamped, then left=0 and width reduced by 50."""
        # Arrange
        r = Rect(-50, 100, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result.left == 0
        assert result.width == 150  # 200 - 50

    def test_rect_clipped_at_right(self, unit_bounds: Rect) -> None:
        """Given rect extending 50px right of bounds (EP3), when clamped, then right=999 and width=100."""
        # Arrange
        r = Rect(900, 100, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result.right == 999
        assert result.width == 100

    def test_rect_clipped_at_top(self, unit_bounds: Rect) -> None:
        """Given rect extending 30px above bounds (EP4), when clamped, then top=0 and height reduced by 30."""
        # Arrange
        r = Rect(100, -30, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result.top == 0
        assert result.height == 120  # 150 - 30

    def test_rect_clipped_at_bottom(self, unit_bounds: Rect) -> None:
        """Given rect extending 50px below bounds (EP5), when clamped, then bottom=799 and height=100."""
        # Arrange
        r = Rect(100, 700, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result.bottom == 799
        assert result.height == 100

    def test_rect_entirely_outside_x_returns_zero_width(self, unit_bounds: Rect) -> None:
        """Given rect entirely to the right of bounds (EP6), when clamped, then width=0."""
        # Arrange
        r = Rect(1100, 100, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result.width == 0

    def test_rect_touching_right_boundary_unchanged(self, unit_bounds: Rect) -> None:
        """Given rect whose right edge exactly equals bounds.right (BV1), when clamped, then unchanged."""
        # Arrange
        r = Rect(800, 100, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result == r

    def test_rect_one_pixel_outside_left_trimmed(self, unit_bounds: Rect) -> None:
        """Given rect with left=-1 exactly 1px outside bounds (BV2), when clamped, then width reduced by 1."""
        # Arrange
        r = Rect(-1, 100, 200, 150)
        # Act
        result = clamp_rect_to_bounds(r, unit_bounds)
        # Assert
        assert result.left == 0
        assert result.width == 199  # 200 - 1


# ---------------------------------------------------------------------------
# TestAdjustDimensionsToRatio
# ---------------------------------------------------------------------------


class TestAdjustDimensionsToRatio:
    """
    Test Design Specification: adjust_dimensions_to_ratio()
    Module under test: src/core/crop_geometry.py

    Contract:
        Adjusts (width, height) to satisfy width / height == ratio_w / ratio_h by
        shrinking whichever dimension exceeds the ratio. Then computes moving-corner
        coordinates relative to fixed_point for the given corner name.
        Returns (width, height, moving_x, moving_y).
        Formula: if width / target_ratio > height → width = int(height * target_ratio)
                 else                             → height = int(width / target_ratio)

    Equivalence partitions:
        EP1  width / target_ratio > height → height stays, width shrunk to match
        EP2  width / target_ratio <= height → width stays, height shrunk to match
        EP3  corner="top_left"    → moving = (fixed_x - width, fixed_y - height)
        EP4  corner="top_right"   → moving = (fixed_x + width, fixed_y - height)
        EP5  corner="bottom_left" → moving = (fixed_x - width, fixed_y + height)
        EP6  corner="bottom_right"→ moving = (fixed_x + width, fixed_y + height)

    Boundary values:
        BV1  Square ratio (1:1)      → width may equal height
        BV2  Wide ratio (16:9)       → width much larger than height
        BV3  Tall ratio (9:16)       → height much larger than width

    Exclusions:
        - Zero ratio values (division by zero; caller validates)
        - Floating-point rounding at extreme aspect ratios beyond typical crop use

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    @pytest.mark.parametrize(
        "dims, ratio, expected_w, expected_h",
        [
            ((200, 100), (1, 1), 100, 100),   # EP1+BV1: 200/1=200>100 → width=int(100*1)=100, square ratio
            ((100, 200), (1, 1), 100, 100),   # EP2+BV1: 100/1=100<=200 → height=int(100/1)=100, square ratio
            ((160, 100), (16, 9), 160, 90),   # EP2+BV2: 160/1.78=90<=100 → height=int(160/1.78)=90, wide ratio
            ((50, 200), (16, 9), 50, 28),     # EP2+BV2: 50/1.78=28<=200 → height=int(50/1.78)=28, wide ratio
            ((200, 100), (9, 16), 56, 100),   # EP1+BV3: 200/0.56=357>100 → width=int(100*0.5625)=56, tall ratio
        ],
        ids=[
            "square_width_limiting",
            "square_height_limiting",
            "wide_height_limiting",
            "wide_height_limiting_small",
            "tall_width_limiting",
        ],
    )
    def test_dimensions_adjusted_to_ratio(
        self, dims: tuple[int, int], ratio: tuple[int, int], expected_w: int, expected_h: int
    ) -> None:
        """Given dimensions and ratio, when adjusted, then output satisfies the ratio."""
        # Arrange  (parameters supplied by pytest.mark.parametrize)
        # Act
        w, h, _, _ = adjust_dimensions_to_ratio(dims, (0, 0), "bottom_right", ratio)
        # Assert
        assert w == expected_w
        assert h == expected_h

    @pytest.mark.parametrize(
        "corner, fixed, expected_mx, expected_my",
        [
            ("top_left", (500, 400), 400, 300),      # EP3: top_left → moving = (fixed_x - w, fixed_y - h)
            ("top_right", (400, 400), 500, 300),     # EP4: top_right → moving = (fixed_x + w, fixed_y - h)
            ("bottom_left", (500, 300), 400, 400),   # EP5: bottom_left → moving = (fixed_x - w, fixed_y + h)
            ("bottom_right", (400, 300), 500, 400),  # EP6: bottom_right → moving = (fixed_x + w, fixed_y + h)
        ],
        ids=["top_left", "top_right", "bottom_left", "bottom_right"],
    )
    def test_moving_corner_position(
        self, corner: str, fixed: tuple[int, int], expected_mx: int, expected_my: int
    ) -> None:
        """Given 100×100 with 1:1 ratio and named corner, when adjusted, then moving point is correct."""
        # Arrange  (parameters supplied by pytest.mark.parametrize)
        # Act
        _, _, mx, my = adjust_dimensions_to_ratio((100, 100), fixed, corner, (1, 1))
        # Assert
        assert mx == expected_mx
        assert my == expected_my

    def test_output_satisfies_ratio(self) -> None:
        """Given arbitrary dims (300, 200) and 4:3 ratio, when adjusted, then width/height ≈ 4/3."""
        # Arrange
        dims = (300, 200)
        # Act
        w, h, _, _ = adjust_dimensions_to_ratio(dims, (0, 0), "bottom_right", (4, 3))
        # Assert
        assert abs(w / h - 4 / 3) < 0.01


# ---------------------------------------------------------------------------
# TestResizeTopLeft
# ---------------------------------------------------------------------------


class TestResizeTopLeft:
    """
    Test Design Specification: resize_top_left()
    Module under test: src/core/crop_geometry.py

    Contract:
        Compute new Rect when the top-left handle is dragged to the mouse position.
        Fixed edges are the original right and bottom. The moving left and top edges
        are constrained to be at least 10px from their respective fixed edges.
        Result is clamped to the image bounds. If ratio is provided, dimensions
        are adjusted to maintain it.

    Equivalence partitions:
        EP1  Free aspect, normal drag     → correct rect from fixed_right/bottom
        EP2  Drag past fixed corner       → minimum 10px separation on width
        EP3  Drag past fixed corner (y)   → minimum 10px separation on height
        EP4  With ratio constraint        → dimensions satisfy ratio
        EP5  Result extends beyond bounds → clamped to image bounds

    Boundary values:
        BV1  Mouse at (fixed_right - 10, any) → width == 10 exactly
        BV2  Mouse at (bounds.left, any)      → result.left == bounds.left

    Exclusions:
        - Negative bounds or bounds with zero area (invalid configuration)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_normal_drag_free_aspect(self, unit_bounds: Rect) -> None:
        """Given mouse at (300, 200), fixed_right=600, fixed_bottom=500 (EP1), when dragged, then correct rect."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_left(Point(300.0, 200.0), fe, unit_bounds)
        # Assert
        assert result.left == 300
        assert result.top == 200
        assert result.right == 599  # inclusive: 300 + 300 - 1
        assert result.bottom == 499  # inclusive: 200 + 300 - 1

    def test_minimum_width_enforced(self, unit_bounds: Rect) -> None:
        """Given mouse x past fixed_right (EP2), when dragged, then width is at least 10px."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_left(Point(595.0, 200.0), fe, unit_bounds)
        # Assert
        assert result.width >= 10

    def test_minimum_height_enforced(self, unit_bounds: Rect) -> None:
        """Given mouse y past fixed_bottom (EP3), when dragged, then height is at least 10px."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_left(Point(300.0, 495.0), fe, unit_bounds)
        # Assert
        assert result.height >= 10

    def test_ratio_constraint_maintained(self, unit_bounds: Rect) -> None:
        """Given 1:1 ratio (EP4), when dragged, then width == height."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_left(Point(300.0, 200.0), fe, unit_bounds, ratio=(1, 1))
        # Assert
        assert result.width == result.height

    def test_result_clamped_to_bounds(self, unit_bounds: Rect) -> None:
        """Given mouse outside image bounds (EP5), when dragged, then result is clamped to bounds."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_left(Point(-100.0, -100.0), fe, unit_bounds)
        # Assert
        assert result.left >= unit_bounds.left
        assert result.top >= unit_bounds.top

    def test_width_exactly_ten_at_minimum_boundary(self, unit_bounds: Rect) -> None:
        """Given mouse at fixed_right - 10 (BV1), when dragged, then width == 10."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_left(Point(590.0, 200.0), fe, unit_bounds)
        # Assert
        assert result.width == 10

    def test_left_at_bounds_left(self, unit_bounds: Rect) -> None:
        """Given mouse at bounds.left=0 (BV2), when dragged, then result.left == 0."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_left(Point(0.0, 200.0), fe, unit_bounds)
        # Assert
        assert result.left == unit_bounds.left


# ---------------------------------------------------------------------------
# TestResizeTopRight
# ---------------------------------------------------------------------------


class TestResizeTopRight:
    """
    Test Design Specification: resize_top_right()
    Module under test: src/core/crop_geometry.py

    Contract:
        Compute new Rect when the top-right handle is dragged. Fixed edges are
        the original left and bottom. The moving right is constrained to be at
        least fixed_left + 10. The moving top is constrained to be at least 10px
        above fixed_bottom. Result is clamped to bounds.

    Equivalence partitions:
        EP1  Normal drag free aspect  → correct rect
        EP2  Minimum width enforced   → right >= fixed_left + 10
        EP3  With ratio               → dimensions satisfy ratio

    Boundary values:
        BV1  Mouse x = fixed_left + 10 → width == 10 exactly

    Exclusions:
        - Negative bounds or bounds with zero area (invalid configuration)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_normal_drag_free_aspect(self, unit_bounds: Rect) -> None:
        """Given mouse at (700, 200), fixed_left=400, fixed_bottom=500 (EP1), when dragged, then correct rect."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_right(Point(700.0, 200.0), fe, unit_bounds)
        # Assert
        assert result.left == 400
        assert result.top == 200
        assert result.right == 699  # inclusive: 400 + 300 - 1
        assert result.bottom == 499  # inclusive: 200 + 300 - 1

    def test_minimum_width_enforced(self, unit_bounds: Rect) -> None:
        """Given mouse x less than fixed_left + 10 (EP2), when dragged, then width is at least 10px."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_right(Point(405.0, 200.0), fe, unit_bounds)
        # Assert
        assert result.width >= 10

    def test_ratio_constraint_maintained(self, unit_bounds: Rect) -> None:
        """Given 1:1 ratio (EP3), when dragged, then width == height."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_right(Point(700.0, 200.0), fe, unit_bounds, ratio=(1, 1))
        # Assert
        assert result.width == result.height

    def test_width_exactly_ten_at_minimum_boundary(self, unit_bounds: Rect) -> None:
        """Given mouse at fixed_left + 10 = 410 (BV1), when dragged, then width == 10."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_top_right(Point(410.0, 200.0), fe, unit_bounds)
        # Assert
        assert result.width == 10


# ---------------------------------------------------------------------------
# TestResizeBottomLeft
# ---------------------------------------------------------------------------


class TestResizeBottomLeft:
    """
    Test Design Specification: resize_bottom_left()
    Module under test: src/core/crop_geometry.py

    Contract:
        Compute new Rect when the bottom-left handle is dragged. Fixed edges are
        the original right and top. The moving left is constrained to be at least
        10px from fixed_right. The moving bottom is constrained to be at least
        fixed_top + 10. Result is clamped to bounds.

    Equivalence partitions:
        EP1  Normal drag free aspect  → correct rect
        EP2  Minimum dimensions       → width >= 10
        EP3  With ratio               → dimensions satisfy ratio

    Boundary values:
        BV1  Mouse x = fixed_right - 10 → width == 10 exactly

    Exclusions:
        - Negative bounds or bounds with zero area (invalid configuration)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_normal_drag_free_aspect(self, unit_bounds: Rect) -> None:
        """Given mouse at (300, 500), fixed_right=600, fixed_top=300 (EP1), when dragged, then correct rect."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_left(Point(300.0, 500.0), fe, unit_bounds)
        # Assert
        assert result.left == 300
        assert result.top == 300
        assert result.right == 599  # inclusive: 300 + 300 - 1
        assert result.bottom == 499  # inclusive: 300 + 200 - 1

    def test_minimum_width_enforced(self, unit_bounds: Rect) -> None:
        """Given mouse x past fixed_right (EP2), when dragged, then width is at least 10px."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_left(Point(595.0, 500.0), fe, unit_bounds)
        # Assert
        assert result.width >= 10

    def test_ratio_constraint_maintained(self, unit_bounds: Rect) -> None:
        """Given 1:1 ratio (EP3), when dragged, then width == height."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_left(Point(300.0, 500.0), fe, unit_bounds, ratio=(1, 1))
        # Assert
        assert result.width == result.height

    def test_width_exactly_ten_at_minimum_boundary(self, unit_bounds: Rect) -> None:
        """Given mouse at fixed_right - 10 = 590 (BV1), when dragged, then width == 10."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_left(Point(590.0, 500.0), fe, unit_bounds)
        # Assert
        assert result.width == 10


# ---------------------------------------------------------------------------
# TestResizeBottomRight
# ---------------------------------------------------------------------------


class TestResizeBottomRight:
    """
    Test Design Specification: resize_bottom_right()
    Module under test: src/core/crop_geometry.py

    Contract:
        Compute new Rect when the bottom-right handle is dragged. Fixed edges are
        the original left and top. The moving right is constrained to be at least
        fixed_left + 10. The moving bottom is constrained to be at least
        fixed_top + 10. Result is clamped to bounds.

    Equivalence partitions:
        EP1  Normal drag free aspect  → correct rect
        EP2  Minimum dimensions       → width >= 10
        EP3  With ratio               → dimensions satisfy ratio

    Boundary values:
        BV1  Mouse x = fixed_left + 10 → width == 10 exactly

    Exclusions:
        - Negative bounds or bounds with zero area (invalid configuration)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_normal_drag_free_aspect(self, unit_bounds: Rect) -> None:
        """Given mouse at (700, 500), fixed_left=400, fixed_top=300 (EP1), when dragged, then correct rect."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_right(Point(700.0, 500.0), fe, unit_bounds)
        # Assert
        assert result.left == 400
        assert result.top == 300
        assert result.right == 699  # inclusive: 400 + 300 - 1
        assert result.bottom == 499  # inclusive: 300 + 200 - 1

    def test_minimum_width_enforced(self, unit_bounds: Rect) -> None:
        """Given mouse x less than fixed_left + 10 (EP2), when dragged, then width is at least 10px."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_right(Point(405.0, 500.0), fe, unit_bounds)
        # Assert
        assert result.width >= 10

    def test_ratio_constraint_maintained(self, unit_bounds: Rect) -> None:
        """Given 1:1 ratio (EP3), when dragged, then width == height."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_right(Point(700.0, 500.0), fe, unit_bounds, ratio=(1, 1))
        # Assert
        assert result.width == result.height

    def test_width_exactly_ten_at_minimum_boundary(self, unit_bounds: Rect) -> None:
        """Given mouse at fixed_left + 10 = 410 (BV1), when dragged, then width == 10."""
        # Arrange
        fe = {"right": 600, "bottom": 500, "left": 400, "top": 300}
        # Act
        result = resize_bottom_right(Point(410.0, 500.0), fe, unit_bounds)
        # Assert
        assert result.width == 10


# ---------------------------------------------------------------------------
# TestEdgeResizeFreeAspect
# ---------------------------------------------------------------------------


class TestEdgeResizeFreeAspect:
    """
    Test Design Specification: edge_resize_free_aspect()
    Module under test: src/core/crop_geometry.py

    Contract:
        Move a single edge of the rectangle to the mouse position. The opposite
        edge is unchanged. The minimum distance between moving and opposite edge
        is 10px. The resulting edge is clamped to image bounds.

    Equivalence partitions:
        EP1  Left handle dragged left    → left edge moves, right unchanged
        EP2  Right handle dragged right  → right edge moves, left unchanged
        EP3  Top handle dragged up       → top edge moves, bottom unchanged
        EP4  Bottom handle dragged down  → bottom edge moves, top unchanged
        EP5  Drag past opposite edge     → minimum 10px separation enforced
        EP6  Drag outside image bounds   → edge clamped to bounds

    Boundary values:
        BV1  Mouse exactly at opposite_edge - 10 → minimum width = 10 after clamp
        BV2  Mouse exactly at bounds edge        → result edge == bounds edge

    Exclusions:
        - Unknown handle names (behaviour undefined; caller must supply valid handles)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_left_handle_moves_left_edge(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given left handle and mouse at x=300 (EP1), when resized, then left=300, right unchanged."""
        # Arrange
        ctx = EdgeResizeContext("left", Point(300.0, 400.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.left == 300
        assert result.right == center_rect.right

    def test_right_handle_moves_right_edge(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given right handle and mouse at x=700 (EP2), when resized, then right=700, left unchanged."""
        # Arrange
        ctx = EdgeResizeContext("right", Point(700.0, 400.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.right == 700
        assert result.left == center_rect.left

    def test_top_handle_moves_top_edge(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given top handle and mouse at y=200 (EP3), when resized, then top=200, bottom unchanged."""
        # Arrange
        ctx = EdgeResizeContext("top", Point(500.0, 200.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.top == 200
        assert result.bottom == center_rect.bottom

    def test_bottom_handle_moves_bottom_edge(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given bottom handle and mouse at y=600 (EP4), when resized, then bottom=600, top unchanged."""
        # Arrange
        ctx = EdgeResizeContext("bottom", Point(500.0, 600.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.bottom == 600
        assert result.top == center_rect.top

    def test_left_drag_past_right_clamped_to_minimum(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given left handle dragged past right edge (EP5), when resized, then minimum 10px width maintained."""
        # Arrange
        ctx = EdgeResizeContext("left", Point(center_rect.right + 50.0, 400.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.width >= 10

    def test_right_drag_outside_bounds_clamped(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given right handle dragged beyond image bounds (EP6), when resized, then right == bounds.right."""
        # Arrange
        ctx = EdgeResizeContext("right", Point(1200.0, 400.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.right == unit_bounds.right

    def test_top_drag_outside_bounds_clamped(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given top handle dragged above image (EP6), when resized, then top == bounds.top."""
        # Arrange
        ctx = EdgeResizeContext("top", Point(500.0, -100.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.top == unit_bounds.top

    def test_right_edge_exactly_at_bounds(self, unit_bounds: Rect, center_rect: Rect) -> None:
        """Given right handle at mouse x = bounds.right (BV2), when resized, then right == bounds.right exactly."""
        # Arrange
        ctx = EdgeResizeContext("right", Point(float(unit_bounds.right), 400.0), center_rect, unit_bounds)
        # Act
        result = edge_resize_free_aspect(ctx)
        # Assert
        assert result.right == unit_bounds.right


# ---------------------------------------------------------------------------
# TestGetHorizontalConstraints
# ---------------------------------------------------------------------------


class TestGetHorizontalConstraints:
    """
    Test Design Specification: get_horizontal_constraints()
    Module under test: src/core/crop_geometry.py

    Contract:
        For a left/right edge drag with fixed aspect ratio, compute EdgeConstraints
        by deriving height from width (for left drag: width = fixed_right - new_left)
        or width from position (for right drag: width = new_right - fixed_left).
        Height = round(width / target_ratio). Rectangle is centred vertically at
        center_point. Minimum width of 10px is enforced.

    Equivalence partitions:
        EP1  Left handle → fixed_right stays, width = fixed_right - new_left
        EP2  Right handle → fixed_left stays, width = new_right - fixed_left

    Boundary values:
        BV1  Mouse x = fixed_right - 10 (left handle, minimum width = 10)
        BV2  Mouse x = fixed_left + 10  (right handle, minimum width = 10)

    Exclusions:
        - target_ratio = 0 (division by zero; caller validates)
        - Handles other than "left"/"right" (handled by get_vertical_constraints)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_left_handle_computes_correct_constraints(self, center_rect: Rect) -> None:
        """Given left handle at x=350, 16:9 ratio (EP1), when constraints computed, then width and ratio correct."""
        # Arrange
        params = ResizeParameters(
            handle="left",
            mouse=Point(350.0, 0.0),
            rect=center_rect,
            target_ratio=16 / 9,
            center_point=int(center_rect.center_y),
        )
        # Act
        c = get_horizontal_constraints(params)
        # Assert
        assert c.right == center_rect.right + 1  # Exclusive edge in constraints
        assert c.left == 350
        assert c.width == center_rect.right + 1 - 350
        assert abs(c.width / c.height - 16 / 9) < 0.01

    def test_right_handle_computes_correct_constraints(self, center_rect: Rect) -> None:
        """Given right handle at x=650, 4:3 ratio (EP2), when constraints computed, then width and ratio correct."""
        # Arrange
        params = ResizeParameters(
            handle="right",
            mouse=Point(650.0, 0.0),
            rect=center_rect,
            target_ratio=4 / 3,
            center_point=int(center_rect.center_y),
        )
        # Act
        c = get_horizontal_constraints(params)
        # Assert
        assert c.left == center_rect.left
        assert c.right == 650
        assert abs(c.width / c.height - 4 / 3) < 0.01

    def test_constraints_vertically_centred(self, center_rect: Rect) -> None:
        """Given left handle with center_y=400, when constraints computed, then vertical center matches."""
        # Arrange
        center_y = 400
        params = ResizeParameters(
            handle="left",
            mouse=Point(350.0, 0.0),
            rect=center_rect,
            target_ratio=1.0,
            center_point=center_y,
        )
        # Act
        c = get_horizontal_constraints(params)
        # Assert
        computed_center_y = (c.top + c.bottom) / 2
        assert abs(computed_center_y - center_y) <= 1  # integer rounding tolerance

    def test_left_handle_minimum_width_at_boundary(self, center_rect: Rect) -> None:
        """Given left handle at exclusive_right - 10 (BV1), when computed, then width == 10."""
        # Arrange
        params = ResizeParameters(
            handle="left",
            mouse=Point(float(center_rect.right + 1 - 10), 0.0),  # exclusive_right - 10
            rect=center_rect,
            target_ratio=1.0,
            center_point=int(center_rect.center_y),
        )
        # Act
        c = get_horizontal_constraints(params)
        # Assert
        assert c.width == 10

    def test_right_handle_minimum_width_at_boundary(self, center_rect: Rect) -> None:
        """Given right handle at fixed_left + 10 (BV2), when computed, then width == 10."""
        # Arrange
        params = ResizeParameters(
            handle="right",
            mouse=Point(float(center_rect.left + 10), 0.0),
            rect=center_rect,
            target_ratio=1.0,
            center_point=int(center_rect.center_y),
        )
        # Act
        c = get_horizontal_constraints(params)
        # Assert
        assert c.width == 10


# ---------------------------------------------------------------------------
# TestGetVerticalConstraints
# ---------------------------------------------------------------------------


class TestGetVerticalConstraints:
    """
    Test Design Specification: get_vertical_constraints()
    Module under test: src/core/crop_geometry.py

    Contract:
        For a top/bottom edge drag with fixed aspect ratio, compute EdgeConstraints
        by deriving width from height (height = fixed_bottom - new_top for top handle;
        height = new_bottom - fixed_top for bottom handle). Width = round(height *
        target_ratio). Rectangle is centred horizontally at center_point.

    Equivalence partitions:
        EP1  Top handle    → fixed_bottom stays, height = fixed_bottom - new_top
        EP2  Bottom handle → fixed_top stays, height = new_bottom - fixed_top

    Boundary values:
        BV1  Mouse y = fixed_bottom - 10 (top handle, minimum height = 10)

    Exclusions:
        - target_ratio = 0 (division by zero; caller validates)
        - Handles other than "top"/"bottom" (handled by get_horizontal_constraints)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_top_handle_computes_correct_constraints(self, center_rect: Rect) -> None:
        """Given top handle at y=250, 1:1 ratio (EP1), when computed, then height correct and width==height."""
        # Arrange
        params = ResizeParameters(
            handle="top",
            mouse=Point(0.0, 250.0),
            rect=center_rect,
            target_ratio=1.0,
            center_point=int(center_rect.center_x),
        )
        # Act
        c = get_vertical_constraints(params)
        # Assert
        assert c.bottom == center_rect.bottom + 1  # Exclusive edge in constraints
        assert c.top == 250
        assert c.width == c.height

    def test_bottom_handle_computes_correct_constraints(self, center_rect: Rect) -> None:
        """Given bottom handle at y=600, 4:3 ratio (EP2), when computed, then height and ratio correct."""
        # Arrange
        params = ResizeParameters(
            handle="bottom",
            mouse=Point(0.0, 600.0),
            rect=center_rect,
            target_ratio=4 / 3,
            center_point=int(center_rect.center_x),
        )
        # Act
        c = get_vertical_constraints(params)
        # Assert
        assert c.top == center_rect.top
        assert c.bottom == 600
        assert abs(c.width / c.height - 4 / 3) < 0.01

    def test_top_handle_minimum_height_at_boundary(self, center_rect: Rect) -> None:
        """Given top handle at exclusive_bottom - 10 (BV1), when computed, then height == 10."""
        # Arrange
        params = ResizeParameters(
            handle="top",
            mouse=Point(0.0, float(center_rect.bottom + 1 - 10)),  # exclusive_bottom - 10
            rect=center_rect,
            target_ratio=1.0,
            center_point=int(center_rect.center_x),
        )
        # Act
        c = get_vertical_constraints(params)
        # Assert
        assert c.height == 10


# ---------------------------------------------------------------------------
# TestApplyHorizontalBoundsConstraints
# ---------------------------------------------------------------------------


class TestApplyHorizontalBoundsConstraints:
    """
    Test Design Specification: apply_horizontal_bounds_constraints()
    Module under test: src/core/crop_geometry.py

    Contract:
        Given EdgeConstraints from a horizontal resize and image bounds, clamp
        the resulting rectangle so all edges remain within bounds while preserving
        aspect ratio. Checks are applied in order: left, then top, then bottom.

    Equivalence partitions:
        EP1  All edges within bounds         → result equals constraints unchanged
        EP2  Left edge outside bounds        → left clamped, width/height recalculated
        EP3  Top edge outside bounds         → top clamped, height/width recalculated
        EP4  Bottom edge outside bounds      → bottom clamped, height/width recalculated

    Boundary values:
        BV1  left == bounds.left exactly     → unchanged (on boundary)
        BV2  bottom == bounds.bottom exactly → unchanged (on boundary)

    Exclusions:
        - Right edge out of bounds (handled by caller via the edge argument)
        - Simultaneous left+top violations (left checked first; subsequent checks use updated values)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_no_violations_returns_unchanged(self, unit_bounds: Rect) -> None:
        """Given constraints all inside 1000×800 bounds (EP1), when applied, then result equals input."""
        # Arrange
        c = EdgeConstraints(left=100, top=100, right=300, bottom=200, width=200, height=100)
        # Act
        result = apply_horizontal_bounds_constraints(c, unit_bounds, "left", 2.0)
        # Assert
        assert result.left == 100
        assert result.top == 100
        assert result.width == 200
        assert result.height == 100

    def test_left_out_of_bounds_clamped(self, unit_bounds: Rect) -> None:
        """Given left=-50 outside bounds (EP2), when applied with left edge, then result.left >= 0."""
        # Arrange
        c = EdgeConstraints(left=-50, top=100, right=200, bottom=200, width=250, height=100)
        # Act
        result = apply_horizontal_bounds_constraints(c, unit_bounds, "left", 2.5)
        # Assert
        assert result.left >= unit_bounds.left

    def test_top_out_of_bounds_clamped(self, unit_bounds: Rect) -> None:
        """Given top=-20 outside bounds (EP3), when applied, then result.top >= 0."""
        # Arrange
        c = EdgeConstraints(left=100, top=-20, right=300, bottom=80, width=200, height=100)
        # Act
        result = apply_horizontal_bounds_constraints(c, unit_bounds, "right", 2.0)
        # Assert
        assert result.top >= unit_bounds.top

    def test_bottom_out_of_bounds_clamped(self, unit_bounds: Rect) -> None:
        """Given bottom=850 outside 800px bounds (EP4), when applied, then result.bottom <= 800."""
        # Arrange
        c = EdgeConstraints(left=100, top=750, right=300, bottom=850, width=200, height=100)
        # Act
        result = apply_horizontal_bounds_constraints(c, unit_bounds, "right", 2.0)
        # Assert
        assert result.bottom <= unit_bounds.bottom

    def test_left_exactly_at_bounds_unchanged(self, unit_bounds: Rect) -> None:
        """Given left=0 exactly at bounds.left (BV1), when applied, then left remains 0."""
        # Arrange
        c = EdgeConstraints(left=0, top=100, right=200, bottom=200, width=200, height=100)
        # Act
        result = apply_horizontal_bounds_constraints(c, unit_bounds, "left", 2.0)
        # Assert
        assert result.left == 0


# ---------------------------------------------------------------------------
# TestApplyVerticalBoundsConstraints
# ---------------------------------------------------------------------------


class TestApplyVerticalBoundsConstraints:
    """
    Test Design Specification: apply_vertical_bounds_constraints()
    Module under test: src/core/crop_geometry.py

    Contract:
        Given EdgeConstraints from a vertical resize and image bounds, clamp the
        resulting rectangle so all edges remain within bounds while preserving
        aspect ratio. Checks are applied in order: top (top-edge only), left, right.

    Equivalence partitions:
        EP1  All edges within bounds         → result equals constraints unchanged
        EP2  Top edge outside bounds         → top clamped and height recalculated (top-edge drag only)
        EP3  Left edge outside bounds        → left clamped, width recalculated
        EP4  Right edge outside bounds       → right clamped, width recalculated

    Boundary values:
        BV1  top == bounds.top exactly and edge="top" → unchanged (on boundary)
        BV2  right == bounds.right exactly            → unchanged (on boundary)

    Exclusions:
        - top out of bounds with edge="bottom" (this condition is intentionally skipped per algorithm)
        - Simultaneous left+right violations (left checked first)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    def test_no_violations_returns_unchanged(self, unit_bounds: Rect) -> None:
        """Given constraints all inside bounds (EP1), when applied, then result equals constraints."""
        # Arrange
        c = EdgeConstraints(left=100, top=100, right=300, bottom=300, width=200, height=200)
        # Act
        result = apply_vertical_bounds_constraints(c, unit_bounds, "bottom", 1.0)
        # Assert
        assert result.left == 100
        assert result.top == 100

    def test_top_out_of_bounds_clamped_for_top_edge(self, unit_bounds: Rect) -> None:
        """Given top=-30 with top edge (EP2), when applied, then result.top >= 0."""
        # Arrange
        c = EdgeConstraints(left=100, top=-30, right=300, bottom=200, width=200, height=230)
        # Act
        result = apply_vertical_bounds_constraints(c, unit_bounds, "top", 1.0)
        # Assert
        assert result.top >= unit_bounds.top

    def test_left_out_of_bounds_clamped(self, unit_bounds: Rect) -> None:
        """Given left=-50 outside bounds (EP3), when applied, then result.left >= 0."""
        # Arrange
        c = EdgeConstraints(left=-50, top=100, right=200, bottom=300, width=250, height=200)
        # Act
        result = apply_vertical_bounds_constraints(c, unit_bounds, "bottom", 1.25)
        # Assert
        assert result.left >= unit_bounds.left

    def test_right_out_of_bounds_clamped(self, unit_bounds: Rect) -> None:
        """Given right=1100 outside bounds (EP4), when applied, then result.right <= 1000."""
        # Arrange
        c = EdgeConstraints(left=900, top=100, right=1100, bottom=300, width=200, height=200)
        # Act
        result = apply_vertical_bounds_constraints(c, unit_bounds, "bottom", 1.0)
        # Assert
        assert result.right <= unit_bounds.right

    def test_right_exactly_at_bounds_unchanged(self, unit_bounds: Rect) -> None:
        """Given right=1000 exactly at bounds.right (BV2), when applied, then right remains 1000."""
        # Arrange
        c = EdgeConstraints(left=800, top=100, right=1000, bottom=300, width=200, height=200)
        # Act
        result = apply_vertical_bounds_constraints(c, unit_bounds, "bottom", 1.0)
        # Assert
        assert result.right == unit_bounds.right


# ---------------------------------------------------------------------------
# TestGetAnchorPoint
# ---------------------------------------------------------------------------


class TestGetAnchorPoint:
    """
    Test Design Specification: get_anchor_point()
    Module under test: src/core/crop_geometry.py

    Contract:
        Return the fixed anchor Point opposite the dragged handle on a rectangle.
        Corner handles anchor to the diagonally opposite corner. Edge handles
        anchor to the midpoint of the opposite edge. An unknown handle returns the
        rect centre. None rect returns Point(0, 0).

    Equivalence partitions:
        EP1   "top_left"    → (rect.right, rect.bottom)
        EP2   "top_right"   → (rect.left, rect.bottom)
        EP3   "bottom_left" → (rect.right, rect.top)
        EP4   "bottom_right"→ (rect.left, rect.top)
        EP5   "left"        → (rect.left, center_y)
        EP6   "right"       → (rect.right, center_y)
        EP7   "top"         → (center_x, rect.top)
        EP8   "bottom"      → (center_x, rect.bottom)
        EP9   unknown handle → (center_x, center_y)
        EP10  None rect      → (0, 0)

    Boundary values:
        BV1  Rect with zero width and height → center_x == left, center_y == top

    Exclusions:
        - Empty string handle (treated as unknown; same as EP9)

    Constraints:
        - No external dependencies; pure arithmetic only.
        - No mocking required.
    """

    @pytest.fixture
    def sample_rect(self) -> Rect:
        """200×100 rectangle at (100, 50)."""
        return Rect(100, 50, 200, 100)

    @pytest.mark.parametrize(
        "handle, expected_x, expected_y",
        [
            ("top_left", 299, 149),     # EP1: opposite corner = (right=299, bottom=149)
            ("top_right", 100, 149),    # EP2: opposite corner = (left=100, bottom=149)
            ("bottom_left", 299, 50),   # EP3: opposite corner = (right=299, top=50)
            ("bottom_right", 100, 50),  # EP4: opposite corner = (left=100, top=50)
        ],
        ids=["top_left", "top_right", "bottom_left", "bottom_right"],
    )
    def test_corner_handle_anchor_is_opposite_corner(
        self, sample_rect: Rect, handle: str, expected_x: int, expected_y: int
    ) -> None:
        """Given corner handle, when anchor computed, then it is the diagonally opposite corner."""
        # Arrange  (parameters supplied by pytest.mark.parametrize)
        # Act
        pt = get_anchor_point(handle, sample_rect)
        # Assert
        assert pt.x == expected_x
        assert pt.y == expected_y

    def test_left_handle_anchor(self, sample_rect: Rect) -> None:
        """Given 'left' handle (EP5), when anchor computed, then x=rect.left and y=center_y."""
        # Arrange  (fixture)
        # Act
        pt = get_anchor_point("left", sample_rect)
        # Assert
        assert pt.x == sample_rect.left
        assert pt.y == sample_rect.center_y

    def test_right_handle_anchor(self, sample_rect: Rect) -> None:
        """Given 'right' handle (EP6), when anchor computed, then x=rect.right and y=center_y."""
        # Arrange  (fixture)
        # Act
        pt = get_anchor_point("right", sample_rect)
        # Assert
        assert pt.x == sample_rect.right
        assert pt.y == sample_rect.center_y

    def test_top_handle_anchor(self, sample_rect: Rect) -> None:
        """Given 'top' handle (EP7), when anchor computed, then x=center_x and y=rect.top."""
        # Arrange  (fixture)
        # Act
        pt = get_anchor_point("top", sample_rect)
        # Assert
        assert pt.x == sample_rect.center_x
        assert pt.y == sample_rect.top

    def test_bottom_handle_anchor(self, sample_rect: Rect) -> None:
        """Given 'bottom' handle (EP8), when anchor computed, then x=center_x and y=rect.bottom."""
        # Arrange  (fixture)
        # Act
        pt = get_anchor_point("bottom", sample_rect)
        # Assert
        assert pt.x == sample_rect.center_x
        assert pt.y == sample_rect.bottom

    def test_unknown_handle_returns_center(self, sample_rect: Rect) -> None:
        """Given unknown handle 'move' (EP9), when anchor computed, then returns rect centre."""
        # Arrange  (fixture)
        # Act
        pt = get_anchor_point("move", sample_rect)
        # Assert
        assert pt.x == sample_rect.center_x
        assert pt.y == sample_rect.center_y

    def test_none_rect_returns_origin(self) -> None:
        """Given None rect (EP10), when anchor computed, then (0, 0) is returned."""
        # Arrange  (no rect)
        # Act
        pt = get_anchor_point("top_left", None)
        # Assert
        assert pt.x == 0.0
        assert pt.y == 0.0

    def test_zero_size_rect_anchor_equals_position(self) -> None:
        """Given zero-size rect (BV1), when top_left anchor computed, then x=r.right and y=r.bottom."""
        # Arrange
        r = Rect(200, 150, 0, 0)
        # Act
        pt = get_anchor_point("top_left", r)
        # Assert
        assert pt.x == r.right  # right = left + 0 - 1
        assert pt.y == r.bottom # bottom = top + 0 - 1
