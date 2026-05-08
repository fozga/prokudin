"""Unit tests for src.ui.widgets.grid_types module.

Tests grid type constants are defined correctly.
"""

import pytest

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
    GRID_TYPE_NONE,
)


class TestGridTypeConstants:
    """Test suite for grid type constants."""

    def test_none_constant(self) -> None:
        """Test GRID_TYPE_NONE is defined."""
        assert GRID_TYPE_NONE == "none"

    def test_3x3_constant(self) -> None:
        """Test GRID_TYPE_3X3 is defined."""
        assert GRID_TYPE_3X3 == "3x3"

    def test_golden_ratio_constant(self) -> None:
        """Test GRID_TYPE_GOLDEN_RATIO is defined."""
        assert GRID_TYPE_GOLDEN_RATIO == "golden_ratio"

    def test_diagonal_constants(self) -> None:
        """Test all diagonal grid type constants are defined."""
        assert GRID_TYPE_DIAGONAL_1_1 == "diagonal_1_1"
        assert GRID_TYPE_DIAGONAL_2_3 == "diagonal_2_3"
        assert GRID_TYPE_DIAGONAL_3_2 == "diagonal_3_2"
        assert GRID_TYPE_DIAGONAL_3_4 == "diagonal_3_4"
        assert GRID_TYPE_DIAGONAL_4_3 == "diagonal_4_3"
        assert GRID_TYPE_DIAGONAL_THIRDS_V == "diagonal_thirds_v"
        assert GRID_TYPE_DIAGONAL_THIRDS_H == "diagonal_thirds_h"
        assert GRID_TYPE_DIAGONAL_GOLDEN_V == "diagonal_golden_v"
        assert GRID_TYPE_DIAGONAL_GOLDEN_H == "diagonal_golden_h"

    def test_no_duplicate_values(self) -> None:
        """Test all grid type constants have unique values."""
        constants = [
            GRID_TYPE_NONE,
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
        ]
        assert len(constants) == len(set(constants))
