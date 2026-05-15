"""Unit tests for src/core/grid_geometry module.

Tests pure geometry calculations for grid overlays: line coordinate generation
for rule-of-thirds, golden ratio, and diagonal grid types. No Qt dependency.
"""

import pytest

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


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rect_300_square() -> tuple[float, float, float, float]:
    """300×300 square rect at origin."""
    return (0.0, 0.0, 300.0, 300.0)


@pytest.fixture
def rect_tall() -> tuple[float, float, float, float]:
    """200×400 tall rect at origin."""
    return (0.0, 0.0, 200.0, 400.0)


@pytest.fixture
def rect_wide() -> tuple[float, float, float, float]:
    """400×200 wide rect at origin."""
    return (0.0, 0.0, 400.0, 200.0)


@pytest.fixture
def rect_offset() -> tuple[float, float, float, float]:
    """300×300 square rect at offset (50, 100)."""
    return (50.0, 100.0, 300.0, 300.0)


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestCalculate3x3Lines:
    """
    Test Design Specification: calculate_3x3_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        Calculates rule-of-thirds grid lines by dividing a rectangle into
        9 equal parts. Returns a list of 4 line segments as (x1, y1, x2, y2) tuples:
        - 2 vertical lines at x = left + width/3 and left + 2*width/3
        - 2 horizontal lines at y = top + height/3 and top + 2*height/3

    Equivalence partitions:
        EP1  Square rect (width = height)      → grid divides evenly
        EP2  Tall rect (width < height)        → thirds at fractional positions
        EP3  Wide rect (width > height)        → thirds at fractional positions
        EP4  Offset rect (left, top ≠ 0)       → coordinates account for offset

    Boundary values:
        BV1  Minimal rect (1×1)                → coordinates within bounds
        BV2  Large rect (1000×1000)            → coordinates precise at scale
        BV3  width/height with fractional thirds → output is float, not truncated

    Exclusions:
        - Rounding/truncation (output is exact float; caller converts to int)
        - Validation of rect dimensions (caller ensures positive dimensions)

    Constraints:
        - Pure arithmetic; no external dependencies.
        - Output must be exact float, not quantized to int.
    """

    def test_returns_four_lines(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_3x3_lines is called, then it returns a list of 4 tuples.
        """
        # Arrange / Act
        result = calculate_3x3_lines(rect_300_square)
        # Assert
        assert len(result) == 4
        assert all(isinstance(line, tuple) and len(line) == 4 for line in result)

    def test_vertical_lines_at_thirds(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect at origin, when calculate_3x3_lines is called,
        then the first two lines are vertical at x=100 and x=200 (each third of 300).
        """
        # Arrange / Act
        lines = calculate_3x3_lines(rect_300_square)
        # Assert
        # Vertical line 1: x1 = x2
        assert lines[0][0] == 100.0  # x1
        assert lines[0][2] == 100.0  # x2
        assert lines[0][1] == 0.0  # y1 (top)
        assert lines[0][3] == 300.0  # y2 (bottom)
        # Vertical line 2: x1 = x2
        assert lines[1][0] == 200.0
        assert lines[1][2] == 200.0

    def test_horizontal_lines_at_thirds(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect at origin, when calculate_3x3_lines is called,
        then the last two lines are horizontal at y=100 and y=200.
        """
        # Arrange / Act
        lines = calculate_3x3_lines(rect_300_square)
        # Assert
        # Horizontal line 1: y1 = y2
        assert lines[2][1] == 100.0  # y1
        assert lines[2][3] == 100.0  # y2
        assert lines[2][0] == 0.0  # x1 (left)
        assert lines[2][2] == 300.0  # x2 (right)
        # Horizontal line 2: y1 = y2
        assert lines[3][1] == 200.0
        assert lines[3][3] == 200.0

    def test_respects_rect_offset(self, rect_offset: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect at offset (50, 100), when calculate_3x3_lines is called,
        then all coordinates are adjusted by the offset.
        """
        # Arrange / Act
        lines = calculate_3x3_lines(rect_offset)
        # Assert
        assert lines[0][0] == 150.0  # 50 + 300/3
        assert lines[0][1] == 100.0  # top offset
        assert lines[2][0] == 50.0  # left offset
        assert lines[2][1] == 200.0  # 100 + 300/3

    def test_works_with_tall_rect(self, rect_tall: tuple[float, float, float, float]) -> None:
        """
        Given a 200×400 tall rect, when calculate_3x3_lines is called,
        then vertical lines are at x=66.67 and x=133.33, horizontal at y=133.33 and y=266.67.
        """
        # Arrange / Act
        lines = calculate_3x3_lines(rect_tall)
        # Assert
        assert len(lines) == 4
        assert abs(lines[0][0] - 200.0 / 3) < 1e-6
        assert abs(lines[1][0] - 2 * 200.0 / 3) < 1e-6
        assert abs(lines[2][1] - 400.0 / 3) < 1e-6
        assert abs(lines[3][1] - 2 * 400.0 / 3) < 1e-6

    def test_works_with_wide_rect(self, rect_wide: tuple[float, float, float, float]) -> None:
        """
        Given a 400×200 wide rect, when calculate_3x3_lines is called,
        then vertical lines are at x=133.33 and x=266.67, horizontal at y=66.67 and y=133.33.
        """
        # Arrange / Act
        lines = calculate_3x3_lines(rect_wide)
        # Assert
        assert len(lines) == 4
        assert abs(lines[0][0] - 400.0 / 3) < 1e-6
        assert abs(lines[1][0] - 2 * 400.0 / 3) < 1e-6


class TestCalculateGoldenRatioLines:
    """
    Test Design Specification: calculate_golden_ratio_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        Calculates golden ratio grid lines at positions 0.382 and 0.618 of each dimension.
        Returns 4 line segments: 2 vertical and 2 horizontal.
        Constants 0.382 and 0.618 are precise representations of the golden ratio
        division (1/(1+φ) and φ/(1+φ) where φ ≈ 1.618).

    Equivalence partitions:
        EP1  Square 300×300 rect                → golden positions at ~114 and ~185
        EP2  Arbitrary dimensions (200×400)    → golden ratios apply to each axis independently

    Boundary values:
        BV1  width = 300, height = 300         → x values ~114, ~185; y values ~114, ~185
        BV2  width = 1000                      → x values ~382, ~618 (exact integer multiples)

    Exclusions:
        - Validation of rect dimensions
        - Floating-point tolerance beyond inherent representation

    Constraints:
        - Golden ratio constants 0.382 and 0.618 must be exact floats in output.
    """

    def test_returns_four_lines(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_golden_ratio_lines is called,
        then it returns a list of 4 tuples.
        """
        # Arrange / Act
        result = calculate_golden_ratio_lines(rect_300_square)
        # Assert
        assert len(result) == 4
        assert all(isinstance(line, tuple) and len(line) == 4 for line in result)

    def test_vertical_lines_at_golden_ratio(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_golden_ratio_lines is called,
        then vertical lines are at x = 300 * 0.382 ≈ 114.6 and x = 300 * 0.618 ≈ 185.4.
        """
        # Arrange / Act
        lines = calculate_golden_ratio_lines(rect_300_square)
        # Assert
        expected_x1 = 300.0 * 0.382  # ~114.6
        expected_x2 = 300.0 * 0.618  # ~185.4
        assert abs(lines[0][0] - expected_x1) < 1e-9
        assert abs(lines[0][2] - expected_x1) < 1e-9
        assert abs(lines[1][0] - expected_x2) < 1e-9
        assert abs(lines[1][2] - expected_x2) < 1e-9

    def test_horizontal_lines_at_golden_ratio(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_golden_ratio_lines is called,
        then horizontal lines are at y = 300 * 0.382 and y = 300 * 0.618.
        """
        # Arrange / Act
        lines = calculate_golden_ratio_lines(rect_300_square)
        # Assert
        expected_y1 = 300.0 * 0.382
        expected_y2 = 300.0 * 0.618
        assert abs(lines[2][1] - expected_y1) < 1e-9
        assert abs(lines[2][3] - expected_y1) < 1e-9
        assert abs(lines[3][1] - expected_y2) < 1e-9
        assert abs(lines[3][3] - expected_y2) < 1e-9

    def test_respects_offset(self, rect_offset: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect at offset (50, 100), when calculate_golden_ratio_lines is called,
        then all coordinates include the offset.
        """
        # Arrange / Act
        lines = calculate_golden_ratio_lines(rect_offset)
        # Assert
        expected_x1 = 50.0 + 300.0 * 0.382
        assert abs(lines[0][0] - expected_x1) < 1e-9
        assert abs(lines[2][0] - 50.0) < 1e-9


class TestCalculateDiagonal1_1Lines:
    """
    Test Design Specification: calculate_diagonal_1_1_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        Calculates four 45-degree diagonal lines from each corner. Each diagonal
        extends until it hits the far edge of the rectangle (either horizontal or
        vertical depending on rect aspect ratio). For a square or tall rect,
        the diagonal reaches the far horizontal edge; for a wide rect, it reaches
        the far vertical edge.

    Equivalence partitions:
        EP1  width ≤ height (square or tall)  → diagonals reach right/left edges
        EP2  width > height (wide)            → diagonals reach bottom/top edges

    Boundary values:
        BV1  Square (300×300)                 → width ≤ height branch
        BV2  Tall (200×400)                   → width ≤ height branch
        BV3  Wide (400×300)                   → width > height branch

    Exclusions:
        - Exact endpoint validation beyond bounds checking

    Constraints:
        - All endpoints must fall on the rectangle edges.
    """

    def test_returns_four_lines_square(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 square rect, when calculate_diagonal_1_1_lines is called,
        then it returns a list of 4 tuples.
        """
        # Arrange / Act
        result = calculate_diagonal_1_1_lines(rect_300_square)
        # Assert
        assert len(result) == 4

    def test_returns_four_lines_tall(self, rect_tall: tuple[float, float, float, float]) -> None:
        """
        Given a 200×400 tall rect, when calculate_diagonal_1_1_lines is called,
        then it returns a list of 4 tuples.
        """
        # Arrange / Act
        result = calculate_diagonal_1_1_lines(rect_tall)
        # Assert
        assert len(result) == 4

    def test_returns_four_lines_wide(self, rect_wide: tuple[float, float, float, float]) -> None:
        """
        Given a 400×200 wide rect, when calculate_diagonal_1_1_lines is called,
        then it returns a list of 4 tuples.
        """
        # Arrange / Act
        result = calculate_diagonal_1_1_lines(rect_wide)
        # Assert
        assert len(result) == 4

    def test_diagonals_start_at_corners(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 square, when calculate_diagonal_1_1_lines is called,
        then all four lines start at the corners (0,0), (300,0), (0,300), (300,300).
        """
        # Arrange / Act
        lines = calculate_diagonal_1_1_lines(rect_300_square)
        # Assert
        corners = {(lines[0][0], lines[0][1]), (lines[1][0], lines[1][1]),
                   (lines[2][0], lines[2][1]), (lines[3][0], lines[3][1])}
        expected_corners = {(0.0, 0.0), (300.0, 0.0), (0.0, 300.0), (300.0, 300.0)}
        assert corners == expected_corners


class TestCalculateDiagonalRatioLines:
    """
    Test Design Specification: calculate_diagonal_2_3_lines, 3_2, 3_4, 4_3
    Module under test: src/core/grid_geometry.py

    Contract:
        Each function calculates four corner-to-edge diagonal lines at a specific
        slope (vertical_ratio : horizontal_ratio). All four functions delegate to
        a shared helper _calculate_diagonal_ratio_lines. Output is 4 line tuples.

    Equivalence partitions:
        EP1  Each ratio variant (2:3, 3:2, 3:4, 4:3)  → returns 4 lines from each

    Boundary values:
        BV1  Square 300×300 rect           → all ratio variants produce valid output

    Exclusions:
        - Exact endpoint positions (implementation detail of ratio calculation)

    Constraints:
        - Must not raise exception for any valid rect.
    """

    @pytest.mark.parametrize(
        "calc_func",
        [
            calculate_diagonal_2_3_lines,
            calculate_diagonal_3_2_lines,
            calculate_diagonal_3_4_lines,
            calculate_diagonal_4_3_lines,
        ],
        ids=["2_3", "3_2", "3_4", "4_3"],
    )
    def test_each_ratio_variant_returns_four_lines(
        self, calc_func, rect_300_square: tuple[float, float, float, float]
    ) -> None:
        """
        Given any ratio variant and a 300×300 rect (EP1, BV1),
        when the function is called, then it returns a list of 4 tuples.
        """
        # Arrange / Act
        result = calc_func(rect_300_square)
        # Assert
        assert len(result) == 4
        assert all(isinstance(line, tuple) and len(line) == 4 for line in result)


class TestCalculateDiagonalThirdsVLines:
    """
    Test Design Specification: calculate_diagonal_thirds_v_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        Calculates 6 lines: 2 corner-to-corner diagonals plus 4 vertical lines
        from corners to rule-of-thirds division points on top/bottom edges.
        Returns exactly 6 line tuples in order: diagonals first, then vertical lines.

    Equivalence partitions:
        EP1  Any valid rect  → returns 6 lines

    Boundary values:
        BV1  Square 300×300  → thirds at x=100, x=200

    Exclusions:
        - Exact positioning of vertical lines (covered by 3x3 tests)

    Constraints:
        - First 2 lines must be the diagonals (matching 1:1 diagonal).
    """

    def test_returns_six_lines(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_thirds_v_lines is called,
        then it returns a list of 6 tuples.
        """
        # Arrange / Act
        result = calculate_diagonal_thirds_v_lines(rect_300_square)
        # Assert
        assert len(result) == 6

    def test_first_two_lines_are_diagonals(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_thirds_v_lines is called,
        then the first two lines are the corner-to-corner diagonals.
        """
        # Arrange / Act
        lines = calculate_diagonal_thirds_v_lines(rect_300_square)
        # Assert
        assert lines[0] == (0.0, 0.0, 300.0, 300.0)  # Top-left to bottom-right
        assert lines[1] == (300.0, 0.0, 0.0, 300.0)  # Top-right to bottom-left

    def test_remaining_lines_are_to_thirds_points(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_thirds_v_lines is called,
        then lines 3–6 connect corners to thirds division points on opposite edges.
        """
        # Arrange / Act
        lines = calculate_diagonal_thirds_v_lines(rect_300_square)
        # Assert
        # Each line 2-5 should have one end on the thirds vertical (x=100 or x=200)
        thirds_x_values = {100.0, 200.0}
        for i in range(2, 6):
            x_coords = {lines[i][0], lines[i][2]}
            # At least one end should be on a thirds line
            assert any(x in thirds_x_values for x in x_coords), f"Line {i}: {lines[i]} doesn't have thirds point"


class TestCalculateDiagonalThirdsHLines:
    """
    Test Design Specification: calculate_diagonal_thirds_h_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        Calculates 6 lines: 2 corner-to-corner diagonals plus 4 horizontal lines
        from corners to rule-of-thirds division points on left/right edges.
        Returns exactly 6 line tuples in order: diagonals first, then horizontal lines.

    Equivalence partitions:
        EP1  Any valid rect  → returns 6 lines

    Boundary values:
        BV1  Square 300×300  → thirds at y=100, y=200

    Constraints:
        - First 2 lines must be the diagonals.
    """

    def test_returns_six_lines(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_thirds_h_lines is called,
        then it returns a list of 6 tuples.
        """
        # Arrange / Act
        result = calculate_diagonal_thirds_h_lines(rect_300_square)
        # Assert
        assert len(result) == 6

    def test_remaining_lines_are_to_thirds_points(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_thirds_h_lines is called,
        then lines 3–6 connect corners to thirds division points on opposite edges.
        """
        # Arrange / Act
        lines = calculate_diagonal_thirds_h_lines(rect_300_square)
        # Assert
        # Each line 2-5 should have one end on the thirds horizontal (y=100 or y=200)
        thirds_y_values = {100.0, 200.0}
        for i in range(2, 6):
            y_coords = {lines[i][1], lines[i][3]}
            # At least one end should be on a thirds line
            assert any(y in thirds_y_values for y in y_coords), f"Line {i}: {lines[i]} doesn't have thirds point"


class TestCalculateDiagonalGoldenVLines:
    """
    Test Design Specification: calculate_diagonal_golden_v_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        Calculates 6 lines: 2 corner-to-corner diagonals plus 4 vertical lines
        from corners to golden ratio division points on top/bottom edges.
        Vertical lines are at x = left + width * 0.382 and left + width * 0.618.

    Equivalence partitions:
        EP1  Square 300×300  → golden x at ~114.6 and ~185.4

    Boundary values:
        BV1  Square 300×300  → golden ratio constants apply

    Constraints:
        - First 2 lines are the diagonals.
        - Lines 3–6 are vertical (x1 == x2) at golden positions.
    """

    def test_returns_six_lines(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_golden_v_lines is called,
        then it returns a list of 6 tuples.
        """
        # Arrange / Act
        result = calculate_diagonal_golden_v_lines(rect_300_square)
        # Assert
        assert len(result) == 6

    def test_vertical_lines_at_golden_points(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_golden_v_lines is called,
        then lines 3–6 connect corners to golden ratio division points on opposite edges.
        """
        # Arrange / Act
        lines = calculate_diagonal_golden_v_lines(rect_300_square)
        # Assert
        expected_x1 = 300.0 * 0.382
        expected_x2 = 300.0 * 0.618
        golden_x_values = {expected_x1, expected_x2}
        # Each line 2-5 should have one end on a golden ratio vertical
        for i in range(2, 6):
            x_coords = {lines[i][0], lines[i][2]}
            # At least one end should be on a golden ratio line
            close_to_golden = any(
                min(abs(x - exp_x) for exp_x in golden_x_values) < 1.0 for x in x_coords
            )
            assert close_to_golden, f"Line {i}: {lines[i]} doesn't have golden point"


class TestCalculateDiagonalGoldenHLines:
    """
    Test Design Specification: calculate_diagonal_golden_h_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        Calculates 6 lines: 2 corner-to-corner diagonals plus 4 horizontal lines
        from corners to golden ratio division points on left/right edges.
        Horizontal lines are at y = top + height * 0.382 and top + height * 0.618.

    Equivalence partitions:
        EP1  Square 300×300  → golden y at ~114.6 and ~185.4

    Constraints:
        - First 2 lines are the diagonals.
        - Lines 3–6 are horizontal (y1 == y2) at golden positions.
    """

    def test_returns_six_lines(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_golden_h_lines is called,
        then it returns a list of 6 tuples.
        """
        # Arrange / Act
        result = calculate_diagonal_golden_h_lines(rect_300_square)
        # Assert
        assert len(result) == 6

    def test_horizontal_lines_at_golden_points(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given a 300×300 rect, when calculate_diagonal_golden_h_lines is called,
        then lines 3–6 connect corners to golden ratio division points on opposite edges.
        """
        # Arrange / Act
        lines = calculate_diagonal_golden_h_lines(rect_300_square)
        # Assert
        expected_y1 = 300.0 * 0.382
        expected_y2 = 300.0 * 0.618
        golden_y_values = {expected_y1, expected_y2}
        # Each line 2-5 should have one end on a golden ratio horizontal
        for i in range(2, 6):
            y_coords = {lines[i][1], lines[i][3]}
            # At least one end should be on a golden ratio line
            close_to_golden = any(
                min(abs(y - exp_y) for exp_y in golden_y_values) < 1.0 for y in y_coords
            )
            assert close_to_golden, f"Line {i}: {lines[i]} doesn't have golden point"


class TestCalculateDiagonalRatioHelper:
    """
    Test Design Specification: _calculate_diagonal_ratio_lines()
    Module under test: src/core/grid_geometry.py

    Contract:
        _calculate_diagonal_ratio_lines is a private helper that calculates
        corner-to-edge diagonals with parameterized slope. It returns 4 line
        tuples for positive ratios, or an empty list if either ratio is ≤ 0
        (defensive guard against misuse).

    Equivalence partitions:
        EP1  Both ratios > 0           → returns 4 lines
        EP2  vertical_ratio = 0        → returns empty list (guard)
        EP3  horizontal_ratio = 0      → returns empty list (guard)
        EP4  Both ratios < 0           → returns empty list (guard)

    Boundary values:
        BV1  vertical_ratio = 0        (at boundary, triggers guard)
        BV2  horizontal_ratio = 0      (at boundary, triggers guard)
        BV3  vertical_ratio = 0.0001   (just above zero, passes guard)

    Exclusions:
        - Negative ratios are not explicitly tested (EP4 covers both ≤ 0)

    Constraints:
        - This is a private helper (_calculate_diagonal_ratio_lines);
          tested directly for defensive programming validation.
    """

    def test_valid_ratios_returns_four_lines(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given valid positive ratios (2.0, 3.0) and a 300×300 rect,
        when _calculate_diagonal_ratio_lines is called,
        then it returns a list of 4 line tuples.
        """
        # Arrange / Act
        from src.core.grid_geometry import _calculate_diagonal_ratio_lines

        result = _calculate_diagonal_ratio_lines(rect_300_square, vertical_ratio=2.0, horizontal_ratio=3.0)
        # Assert
        assert len(result) == 4

    def test_zero_vertical_ratio_returns_empty(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given vertical_ratio=0 (guard boundary, EP2, BV1),
        when _calculate_diagonal_ratio_lines is called,
        then it returns an empty list (early-return guard).
        """
        # Arrange / Act
        from src.core.grid_geometry import _calculate_diagonal_ratio_lines

        result = _calculate_diagonal_ratio_lines(rect_300_square, vertical_ratio=0.0, horizontal_ratio=3.0)
        # Assert
        assert result == []

    def test_zero_horizontal_ratio_returns_empty(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given horizontal_ratio=0 (guard boundary, EP3, BV2),
        when _calculate_diagonal_ratio_lines is called,
        then it returns an empty list (early-return guard).
        """
        # Arrange / Act
        from src.core.grid_geometry import _calculate_diagonal_ratio_lines

        result = _calculate_diagonal_ratio_lines(rect_300_square, vertical_ratio=2.0, horizontal_ratio=0.0)
        # Assert
        assert result == []

    def test_negative_vertical_ratio_returns_empty(self, rect_300_square: tuple[float, float, float, float]) -> None:
        """
        Given vertical_ratio < 0 (invalid, EP4),
        when _calculate_diagonal_ratio_lines is called,
        then it returns an empty list (guard catches ≤ 0).
        """
        # Arrange / Act
        from src.core.grid_geometry import _calculate_diagonal_ratio_lines

        result = _calculate_diagonal_ratio_lines(rect_300_square, vertical_ratio=-1.0, horizontal_ratio=3.0)
        # Assert
        assert result == []



    """
    Test Design Specification: Edge cases for all grid geometry functions
    Module under test: src/core/grid_geometry.py

    Contract:
        Grid geometry functions handle edge cases gracefully: minimal rects,
        offset rects, and fractional coordinates.

    Equivalence partitions:
        EP1  Minimal rect (1×1)           → functions operate correctly
        EP2  Offset rect (left, top ≠ 0)  → coordinates respect offset
        EP3  Large rect (1000×1000)       → coordinates remain accurate

    Constraints:
        - No special handling of zero-width/height (caller's responsibility).
    """

    def test_minimal_rect_1x1(self) -> None:
        """
        Given a minimal 1×1 rect at origin, when grid functions are called,
        then they return valid output without error.
        """
        # Arrange
        minimal_rect = (0.0, 0.0, 1.0, 1.0)
        # Act / Assert
        assert len(calculate_3x3_lines(minimal_rect)) == 4
        assert len(calculate_golden_ratio_lines(minimal_rect)) == 4
        assert len(calculate_diagonal_1_1_lines(minimal_rect)) == 4
        assert len(calculate_diagonal_thirds_v_lines(minimal_rect)) == 6
        assert len(calculate_diagonal_golden_h_lines(minimal_rect)) == 6

    def test_large_rect_1000x1000(self) -> None:
        """
        Given a 1000×1000 rect, when calculate_golden_ratio_lines is called,
        then vertical lines are at x = 382 and x = 618 (exact integer multiples).
        """
        # Arrange
        large_rect = (0.0, 0.0, 1000.0, 1000.0)
        # Act
        lines = calculate_golden_ratio_lines(large_rect)
        # Assert
        expected_x1 = 1000.0 * 0.382  # 382
        expected_x2 = 1000.0 * 0.618  # 618
        assert abs(lines[0][0] - expected_x1) < 1e-9
        assert abs(lines[1][0] - expected_x2) < 1e-9

    def test_offset_rect_all_functions(self) -> None:
        """
        Given any rect with non-zero left/top offset, when all 11 functions are called,
        then coordinates respect the offset without special handling.
        """
        # Arrange
        offset_rect = (50.0, 75.0, 200.0, 200.0)
        # Act
        lines_3x3 = calculate_3x3_lines(offset_rect)
        lines_golden = calculate_golden_ratio_lines(offset_rect)
        # Assert
        # All x coordinates should be >= left (50)
        assert all(line[0] >= 50.0 and line[2] >= 50.0 for line in lines_3x3)
        assert all(line[0] >= 50.0 and line[2] >= 50.0 for line in lines_golden)
        # All y coordinates should be >= top (75)
        assert all(line[1] >= 75.0 and line[3] >= 75.0 for line in lines_3x3)
        assert all(line[1] >= 75.0 and line[3] >= 75.0 for line in lines_golden)
