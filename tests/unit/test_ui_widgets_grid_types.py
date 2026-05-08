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
Unit tests for src.ui.widgets.grid_types module.

Tests grid type constant definitions.
"""

import pytest

import src.ui.widgets.grid_types as grid_types


class TestGridTypeConstants:
    """Tests for grid type constant definitions."""

    def test_grid_type_none_exists(self) -> None:
        """Verify GRID_TYPE_NONE constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_NONE")

    def test_grid_type_none_value(self) -> None:
        """Verify GRID_TYPE_NONE equals 'none'."""
        assert grid_types.GRID_TYPE_NONE == "none"

    def test_grid_type_3x3_exists(self) -> None:
        """Verify GRID_TYPE_3X3 constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_3X3")

    def test_grid_type_3x3_value(self) -> None:
        """Verify GRID_TYPE_3X3 equals '3x3'."""
        assert grid_types.GRID_TYPE_3X3 == "3x3"

    def test_grid_type_golden_ratio_exists(self) -> None:
        """Verify GRID_TYPE_GOLDEN_RATIO constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_GOLDEN_RATIO")

    def test_grid_type_golden_ratio_value(self) -> None:
        """Verify GRID_TYPE_GOLDEN_RATIO equals 'golden_ratio'."""
        assert grid_types.GRID_TYPE_GOLDEN_RATIO == "golden_ratio"

    def test_grid_type_diagonal_1_1_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_1_1 constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_1_1")

    def test_grid_type_diagonal_1_1_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_1_1 equals 'diagonal_1_1'."""
        assert grid_types.GRID_TYPE_DIAGONAL_1_1 == "diagonal_1_1"

    def test_grid_type_diagonal_2_3_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_2_3 constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_2_3")

    def test_grid_type_diagonal_2_3_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_2_3 equals 'diagonal_2_3'."""
        assert grid_types.GRID_TYPE_DIAGONAL_2_3 == "diagonal_2_3"

    def test_grid_type_diagonal_3_2_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_3_2 constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_3_2")

    def test_grid_type_diagonal_3_2_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_3_2 equals 'diagonal_3_2'."""
        assert grid_types.GRID_TYPE_DIAGONAL_3_2 == "diagonal_3_2"

    def test_grid_type_diagonal_3_4_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_3_4 constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_3_4")

    def test_grid_type_diagonal_3_4_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_3_4 equals 'diagonal_3_4'."""
        assert grid_types.GRID_TYPE_DIAGONAL_3_4 == "diagonal_3_4"

    def test_grid_type_diagonal_4_3_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_4_3 constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_4_3")

    def test_grid_type_diagonal_4_3_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_4_3 equals 'diagonal_4_3'."""
        assert grid_types.GRID_TYPE_DIAGONAL_4_3 == "diagonal_4_3"

    def test_grid_type_diagonal_thirds_v_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_THIRDS_V constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_THIRDS_V")

    def test_grid_type_diagonal_thirds_v_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_THIRDS_V equals 'diagonal_thirds_v'."""
        assert grid_types.GRID_TYPE_DIAGONAL_THIRDS_V == "diagonal_thirds_v"

    def test_grid_type_diagonal_thirds_h_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_THIRDS_H constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_THIRDS_H")

    def test_grid_type_diagonal_thirds_h_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_THIRDS_H equals 'diagonal_thirds_h'."""
        assert grid_types.GRID_TYPE_DIAGONAL_THIRDS_H == "diagonal_thirds_h"

    def test_grid_type_diagonal_golden_v_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_GOLDEN_V constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_GOLDEN_V")

    def test_grid_type_diagonal_golden_v_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_GOLDEN_V equals 'diagonal_golden_v'."""
        assert grid_types.GRID_TYPE_DIAGONAL_GOLDEN_V == "diagonal_golden_v"

    def test_grid_type_diagonal_golden_h_exists(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_GOLDEN_H constant is defined."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_GOLDEN_H")

    def test_grid_type_diagonal_golden_h_value(self) -> None:
        """Verify GRID_TYPE_DIAGONAL_GOLDEN_H equals 'diagonal_golden_h'."""
        assert grid_types.GRID_TYPE_DIAGONAL_GOLDEN_H == "diagonal_golden_h"

    def test_all_constants_are_strings(self) -> None:
        """Verify all grid type constants are strings."""
        constants = [
            grid_types.GRID_TYPE_NONE,
            grid_types.GRID_TYPE_3X3,
            grid_types.GRID_TYPE_GOLDEN_RATIO,
            grid_types.GRID_TYPE_DIAGONAL_1_1,
            grid_types.GRID_TYPE_DIAGONAL_2_3,
            grid_types.GRID_TYPE_DIAGONAL_3_2,
            grid_types.GRID_TYPE_DIAGONAL_3_4,
            grid_types.GRID_TYPE_DIAGONAL_4_3,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_V,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_H,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_V,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_H,
        ]
        for const in constants:
            assert isinstance(const, str)

    def test_all_constants_non_empty(self) -> None:
        """Verify all grid type constants are non-empty strings."""
        constants = [
            grid_types.GRID_TYPE_NONE,
            grid_types.GRID_TYPE_3X3,
            grid_types.GRID_TYPE_GOLDEN_RATIO,
            grid_types.GRID_TYPE_DIAGONAL_1_1,
            grid_types.GRID_TYPE_DIAGONAL_2_3,
            grid_types.GRID_TYPE_DIAGONAL_3_2,
            grid_types.GRID_TYPE_DIAGONAL_3_4,
            grid_types.GRID_TYPE_DIAGONAL_4_3,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_V,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_H,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_V,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_H,
        ]
        for const in constants:
            assert len(const) > 0

    def test_no_duplicate_values(self) -> None:
        """Verify no duplicate values among grid type constants."""
        constants = [
            grid_types.GRID_TYPE_NONE,
            grid_types.GRID_TYPE_3X3,
            grid_types.GRID_TYPE_GOLDEN_RATIO,
            grid_types.GRID_TYPE_DIAGONAL_1_1,
            grid_types.GRID_TYPE_DIAGONAL_2_3,
            grid_types.GRID_TYPE_DIAGONAL_3_2,
            grid_types.GRID_TYPE_DIAGONAL_3_4,
            grid_types.GRID_TYPE_DIAGONAL_4_3,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_V,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_H,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_V,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_H,
        ]
        assert len(constants) == len(set(constants))

    def test_expected_constant_count(self) -> None:
        """Verify exactly 12 grid type constants are defined."""
        constants = [
            grid_types.GRID_TYPE_NONE,
            grid_types.GRID_TYPE_3X3,
            grid_types.GRID_TYPE_GOLDEN_RATIO,
            grid_types.GRID_TYPE_DIAGONAL_1_1,
            grid_types.GRID_TYPE_DIAGONAL_2_3,
            grid_types.GRID_TYPE_DIAGONAL_3_2,
            grid_types.GRID_TYPE_DIAGONAL_3_4,
            grid_types.GRID_TYPE_DIAGONAL_4_3,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_V,
            grid_types.GRID_TYPE_DIAGONAL_THIRDS_H,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_V,
            grid_types.GRID_TYPE_DIAGONAL_GOLDEN_H,
        ]
        assert len(constants) == 12
