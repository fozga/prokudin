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


def _get_grid_type_constants() -> list[str]:
    """Dynamically discover all GRID_TYPE_* constants from the module."""
    return [
        getattr(grid_types, attr)
        for attr in dir(grid_types)
        if attr.startswith("GRID_TYPE_") and isinstance(getattr(grid_types, attr), str)
    ]


class TestGridTypeConstants:
    """
    Test Design Specification: Grid type constants with dynamic discovery
    Module under test: src/ui/widgets/grid_types.py

    Contract:
        Verifies grid type constants are properly defined in the module.
        Tests check for existence, correct string values, all being strings,
        non-empty, and uniqueness. Uses dynamic discovery via dir() and getattr()
        to verify all GRID_TYPE_* constants (name prefix filtering).
        Comprehensive structural validation without hardcoding constant names.

    Equivalence partitions:
        EP1  GRID_TYPE_NONE exists and is correct  → constant defined
        EP2  GRID_TYPE_3X3 exists and is correct   → constant defined
        EP3  GRID_TYPE_GOLDEN_RATIO exists         → constant defined
        EP4  GRID_TYPE_DIAGONAL_* variants         → each defined with correct value
        EP5  All constants are strings             → dynamic discovery confirms type
        EP6  All constants non-empty               → len > 0 verified
        EP7  All constants unique values           → no duplicates
        EP8  At least one constant defined         → module is populated

    Boundary values:
        BV1  Minimum constant count > 0 (at least 1)
        BV2  All constants are string type
        BV3  Empty string would be invalid (len > 0 check)

    Exclusions:
        - Constant value semantics (just structural checks)
        - Module import paths (assumes module is importable)
        - Rendering/visualization behavior

    Constraints:
        - Dynamic discovery requires GRID_TYPE_* naming convention
        - Relies on dir() and getattr() introspection
        - Must import src.ui.widgets.grid_types module
        - No external dependencies beyond standard Python introspection
    """

    def test_grid_type_none_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_NONE, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_NONE")

    def test_grid_type_none_value(self) -> None:
        """Given GRID_TYPE_NONE constant, when accessed, then value is 'none'."""
        assert grid_types.GRID_TYPE_NONE == "none"

    def test_grid_type_3x3_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_3X3, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_3X3")

    def test_grid_type_3x3_value(self) -> None:
        """Given GRID_TYPE_3X3 constant, when accessed, then value is '3x3'."""
        assert grid_types.GRID_TYPE_3X3 == "3x3"

    def test_grid_type_golden_ratio_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_GOLDEN_RATIO, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_GOLDEN_RATIO")

    def test_grid_type_golden_ratio_value(self) -> None:
        """Given GRID_TYPE_GOLDEN_RATIO constant, when accessed, then value is 'golden_ratio'."""
        assert grid_types.GRID_TYPE_GOLDEN_RATIO == "golden_ratio"

    def test_grid_type_diagonal_1_1_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_1_1, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_1_1")

    def test_grid_type_diagonal_1_1_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_1_1 constant, when accessed, then value is 'diagonal_1_1'."""
        assert grid_types.GRID_TYPE_DIAGONAL_1_1 == "diagonal_1_1"

    def test_grid_type_diagonal_2_3_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_2_3, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_2_3")

    def test_grid_type_diagonal_2_3_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_2_3 constant, when accessed, then value is 'diagonal_2_3'."""
        assert grid_types.GRID_TYPE_DIAGONAL_2_3 == "diagonal_2_3"

    def test_grid_type_diagonal_3_2_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_3_2, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_3_2")

    def test_grid_type_diagonal_3_2_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_3_2 constant, when accessed, then value is 'diagonal_3_2'."""
        assert grid_types.GRID_TYPE_DIAGONAL_3_2 == "diagonal_3_2"

    def test_grid_type_diagonal_3_4_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_3_4, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_3_4")

    def test_grid_type_diagonal_3_4_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_3_4 constant, when accessed, then value is 'diagonal_3_4'."""
        assert grid_types.GRID_TYPE_DIAGONAL_3_4 == "diagonal_3_4"

    def test_grid_type_diagonal_4_3_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_4_3, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_4_3")

    def test_grid_type_diagonal_4_3_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_4_3 constant, when accessed, then value is 'diagonal_4_3'."""
        assert grid_types.GRID_TYPE_DIAGONAL_4_3 == "diagonal_4_3"

    def test_grid_type_diagonal_thirds_v_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_THIRDS_V, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_THIRDS_V")

    def test_grid_type_diagonal_thirds_v_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_THIRDS_V constant, when accessed, then value is 'diagonal_thirds_v'."""
        assert grid_types.GRID_TYPE_DIAGONAL_THIRDS_V == "diagonal_thirds_v"

    def test_grid_type_diagonal_thirds_h_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_THIRDS_H, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_THIRDS_H")

    def test_grid_type_diagonal_thirds_h_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_THIRDS_H constant, when accessed, then value is 'diagonal_thirds_h'."""
        assert grid_types.GRID_TYPE_DIAGONAL_THIRDS_H == "diagonal_thirds_h"

    def test_grid_type_diagonal_golden_v_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_GOLDEN_V, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_GOLDEN_V")

    def test_grid_type_diagonal_golden_v_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_GOLDEN_V constant, when accessed, then value is 'diagonal_golden_v'."""
        assert grid_types.GRID_TYPE_DIAGONAL_GOLDEN_V == "diagonal_golden_v"

    def test_grid_type_diagonal_golden_h_exists(self) -> None:
        """Given the grid_types module, when checking for GRID_TYPE_DIAGONAL_GOLDEN_H, then attribute exists."""
        assert hasattr(grid_types, "GRID_TYPE_DIAGONAL_GOLDEN_H")

    def test_grid_type_diagonal_golden_h_value(self) -> None:
        """Given GRID_TYPE_DIAGONAL_GOLDEN_H constant, when accessed, then value is 'diagonal_golden_h'."""
        assert grid_types.GRID_TYPE_DIAGONAL_GOLDEN_H == "diagonal_golden_h"

    def test_all_constants_are_strings(self) -> None:
        """Given grid type constants discovered dynamically, when checked, then all are strings."""
        # Arrange
        constants = _get_grid_type_constants()

        # Act & Assert
        assert len(constants) > 0
        for const in constants:
            assert isinstance(const, str)

    def test_all_constants_non_empty(self) -> None:
        """Given grid type constants discovered dynamically, when checked, then all are non-empty strings."""
        # Arrange
        constants = _get_grid_type_constants()

        # Act & Assert
        assert len(constants) > 0
        for const in constants:
            assert len(const) > 0

    def test_no_duplicate_values(self) -> None:
        """Given grid type constants discovered dynamically, when checked, then no duplicate values exist."""
        # Arrange
        constants = _get_grid_type_constants()

        # Act & Assert
        assert len(constants) > 0
        assert len(constants) == len(set(constants))

    def test_expected_constant_count(self) -> None:
        """Given grid type constants discovered dynamically, when checked, then at least one is defined."""
        constants = _get_grid_type_constants()
        assert len(constants) > 0
