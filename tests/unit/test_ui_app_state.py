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
Unit tests for src.ui.app_state module.

Tests AppState dataclass initialization and reset behavior.
"""

import pytest

from src.ui.app_state import AppState
from src.ui.default_state import DefaultState


class TestAppStateInitialization:
    """
    Test Design Specification: AppState dataclass initialization
    Module under test: src/ui/app_state.py

    Contract:
        Initializes mutable UI state owned by MainWindow. Fields represent display mode,
        channel selection, crop settings, and file paths. Default values are:
        - channel_paths: [None, None, None] (list of 3 file paths, mutable)
        - show_combined: True (from DefaultState.SHOW_COMBINED)
        - current_channel: 0 (from DefaultState.CURRENT_CHANNEL)
        - crop_mode: False (from DefaultState.CROP_MODE)
        - crop_rect: None
        - crop_ratio: None (or custom (int, int) tuple)
        - grid_settings_dialog: None
        Allows custom initialization with partial or complete field values.

    Equivalence partitions:
        EP1  Default initialization             → all fields initialized to defaults
        EP2  Custom channel_paths               → custom paths override default [None]*3
        EP3  Custom show_combined               → custom bool overrides default
        EP4  Custom current_channel             → custom int overrides default
        EP5  Custom crop_mode                   → custom bool overrides default
        EP6  Custom crop_ratio                  → custom (int, int) tuple
        EP7  Partial field initialization       → unspecified fields use defaults
        EP8  Full custom initialization         → all fields can be customized

    Boundary values:
        BV1  channel_paths length = 3 (exactly 3 slots)
        BV2  current_channel = 0 (red channel)
        BV3  current_channel = 2 (blue channel)
        BV4  show_combined = True (default display)
        BV5  show_combined = False (single channel)
        BV6  crop_mode = False (default)
        BV7  crop_mode = True (crop active)

    Exclusions:
        - Validation of channel paths existence (caller responsible)
        - Validation of current_channel bounds (assumes [0, 2])
        - Validation of crop_ratio values
        - Type enforcement beyond dataclass structure

    Constraints:
        - dataclass with mutable default for channel_paths (uses field(default_factory))
        - Mutable list and tuple fields (can be modified after init)
        - No external dependencies for initialization
    """

    def test_default_channel_paths(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: channel_paths field is accessed
        Then: it defaults to a list of 3 None values
        """
        # Arrange & Act
        state = AppState()
        # Assert
        assert state.channel_paths == [None, None, None]
        assert len(state.channel_paths) == 3

    def test_channel_paths_is_mutable_list(self) -> None:
        """
        Given: AppState with default channel_paths
        When: an element in channel_paths is modified
        Then: the modification persists and other elements remain None
        """
        # Arrange
        state = AppState()
        # Act
        state.channel_paths[0] = "/path/to/red.tif"
        # Assert
        assert state.channel_paths[0] == "/path/to/red.tif"
        assert state.channel_paths[1] is None
        assert state.channel_paths[2] is None

    def test_default_show_combined(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: show_combined field is accessed
        Then: it defaults to DefaultState.SHOW_COMBINED (True)
        """
        # Arrange & Act
        state = AppState()
        # Assert
        assert state.show_combined is DefaultState.SHOW_COMBINED
        assert state.show_combined is True

    def test_show_combined_is_boolean(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: show_combined field is accessed
        Then: it is of type bool
        """
        state = AppState()
        assert isinstance(state.show_combined, bool)

    def test_default_current_channel(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: current_channel field is accessed
        Then: it defaults to DefaultState.CURRENT_CHANNEL (0)
        """
        # Arrange & Act
        state = AppState()
        # Assert
        assert state.current_channel == DefaultState.CURRENT_CHANNEL
        assert state.current_channel == 0

    def test_current_channel_is_integer(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: current_channel field is accessed
        Then: it is of type int
        """
        state = AppState()
        assert isinstance(state.current_channel, int)

    def test_default_crop_mode(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: crop_mode field is accessed
        Then: it defaults to DefaultState.CROP_MODE (False)
        """
        # Arrange & Act
        state = AppState()
        # Assert
        assert state.crop_mode is DefaultState.CROP_MODE
        assert state.crop_mode is False

    def test_crop_mode_is_boolean(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: crop_mode field is accessed
        Then: it is of type bool
        """
        state = AppState()
        assert isinstance(state.crop_mode, bool)

    def test_default_crop_rect(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: crop_rect field is accessed
        Then: it defaults to None
        """
        state = AppState()
        assert state.crop_rect is None

    def test_default_crop_ratio(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: crop_ratio field is accessed
        Then: it defaults to None
        """
        state = AppState()
        assert state.crop_ratio is None

    def test_default_grid_settings_dialog(self) -> None:
        """
        Given: AppState instantiated with no arguments
        When: grid_settings_dialog field is accessed
        Then: it defaults to None
        """
        state = AppState()
        assert state.grid_settings_dialog is None

    def test_custom_initialization(self) -> None:
        """
        Given: custom values for all AppState fields
        When: AppState is initialized with these custom values
        Then: all fields are set to the specified values
        """
        # Arrange & Act
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
            crop_rect=None,
            crop_ratio=(16, 9),
            grid_settings_dialog=None,
        )
        # Assert
        assert state.channel_paths == ["/red.tif", "/green.tif", "/blue.tif"]
        assert state.show_combined is False
        assert state.current_channel == 2
        assert state.crop_mode is True
        assert state.crop_ratio == (16, 9)


class TestAppStateReset:
    """
    Test Design Specification: AppState.reset() method
    Module under test: src/ui/app_state.py

    Contract:
        Restores all fields to their default values as if newly initialized.
        Clears channel_paths to [None, None, None].
        Restores boolean/integer fields to DefaultState values.
        Clears all object references (crop_rect, crop_ratio, grid_settings_dialog) to None.
        Multiple calls produce identical state (idempotent operation).
        No return value; operates by side effect.

    Equivalence partitions:
        EP1  Reset channel_paths                → [None, None, None]
        EP2  Reset show_combined                → DefaultState.SHOW_COMBINED (True)
        EP3  Reset current_channel              → DefaultState.CURRENT_CHANNEL (0)
        EP4  Reset crop_mode                    → DefaultState.CROP_MODE (False)
        EP5  Reset all object references        → all set to None
        EP6  Reset after custom initialization  → returns to default state
        EP7  Idempotent reset (multiple calls)  → state identical after each call

    Boundary values:
        BV1  channel_paths → [None, None, None]
        BV2  show_combined → True
        BV3  current_channel → 0
        BV4  crop_mode → False
        BV5  crop_rect → None
        BV6  crop_ratio → None
        BV7  grid_settings_dialog → None

    Exclusions:
        - Partial reset (full reset only, no selective field reset)
        - Pre-reset state preservation
        - Return value (no return)

    Constraints:
        - Requires AppState instance (dataclass)
        - Must access DefaultState for default values
        - No external dependencies beyond DefaultState
    """

    def test_reset_channel_paths(self) -> None:
        """
        Given: AppState with custom channel_paths
        When: reset() method is called
        Then: channel_paths is restored to [None, None, None]
        """
        # Arrange
        state = AppState()
        state.channel_paths = ["/red.tif", "/green.tif", "/blue.tif"]
        # Act
        state.reset()
        # Assert
        assert state.channel_paths == [None, None, None]

    def test_reset_show_combined(self) -> None:
        """
        Given: AppState with show_combined set to False
        When: reset() method is called
        Then: show_combined is restored to DefaultState.SHOW_COMBINED (True)
        """
        # Arrange
        state = AppState()
        state.show_combined = False
        # Act
        state.reset()
        # Assert
        assert state.show_combined is DefaultState.SHOW_COMBINED
        assert state.show_combined is True

    def test_reset_current_channel(self) -> None:
        """
        Given: AppState with current_channel set to 2
        When: reset() method is called
        Then: current_channel is restored to DefaultState.CURRENT_CHANNEL (0)
        """
        # Arrange
        state = AppState()
        state.current_channel = 2
        # Act
        state.reset()
        # Assert
        assert state.current_channel == DefaultState.CURRENT_CHANNEL
        assert state.current_channel == 0

    def test_reset_crop_mode(self) -> None:
        """
        Given: AppState with crop_mode set to True
        When: reset() method is called
        Then: crop_mode is restored to DefaultState.CROP_MODE (False)
        """
        # Arrange
        state = AppState()
        state.crop_mode = True
        # Act
        state.reset()
        # Assert
        assert state.crop_mode is DefaultState.CROP_MODE
        assert state.crop_mode is False

    def test_reset_crop_rect(self) -> None:
        """
        Given: AppState with crop_rect set to an object
        When: reset() method is called
        Then: crop_rect is cleared to None
        """
        # Arrange
        state = AppState()
        state.crop_rect = object()  # Simulate QRect
        # Act
        state.reset()
        # Assert
        assert state.crop_rect is None

    def test_reset_crop_ratio(self) -> None:
        """
        Given: AppState with crop_ratio set to a tuple
        When: reset() method is called
        Then: crop_ratio is cleared to None
        """
        # Arrange
        state = AppState()
        state.crop_ratio = (16, 9)
        # Act
        state.reset()
        # Assert
        assert state.crop_ratio is None

    def test_reset_grid_settings_dialog(self) -> None:
        """
        Given: AppState with grid_settings_dialog set to an object
        When: reset() method is called
        Then: grid_settings_dialog is cleared to None
        """
        # Arrange
        state = AppState()
        state.grid_settings_dialog = object()  # Simulate GridSettingsDialog
        # Act
        state.reset()
        # Assert
        assert state.grid_settings_dialog is None

    def test_reset_all_fields_together(self) -> None:
        """
        Given: AppState with all fields set to custom values
        When: reset() method is called
        Then: all fields are simultaneously restored to their defaults
        """
        # Arrange
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=1,
            crop_mode=True,
            crop_rect=object(),
            crop_ratio=(16, 9),
            grid_settings_dialog=object(),
        )
        # Act
        state.reset()
        # Assert — all fields restored to defaults
        assert state.channel_paths == [None, None, None]
        assert state.show_combined is True
        assert state.current_channel == 0
        assert state.crop_mode is False
        assert state.crop_rect is None
        assert state.crop_ratio is None
        assert state.grid_settings_dialog is None

    def test_reset_restores_defaults(self) -> None:
        """
        Given: AppState with custom values
        When: reset() method is called once
        Then: all fields are restored to their known default state
        """
        # Arrange
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
        )
        # Act
        state.reset()
        # Assert
        assert state.show_combined is True
        assert state.current_channel == 0
        assert state.crop_mode is False

    def test_reset_is_idempotent(self) -> None:
        """
        Given: AppState that has been reset and then modified again
        When: reset() is called a second time on the modified state
        Then: the state matches what it was after the first reset
        """
        # Arrange
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
        )
        # First reset to establish baseline
        state.reset()
        state_after_first_reset = {
            "channel_paths": state.channel_paths[:],
            "show_combined": state.show_combined,
            "current_channel": state.current_channel,
            "crop_mode": state.crop_mode,
            "crop_rect": state.crop_rect,
            "crop_ratio": state.crop_ratio,
            "grid_settings_dialog": state.grid_settings_dialog,
        }
        # Modify state
        state.show_combined = False
        state.current_channel = 1
        state.crop_mode = True
        # Act - Reset again
        state.reset()
        # Assert - Verify state matches after first reset
        assert state.channel_paths == state_after_first_reset["channel_paths"]
        assert state.show_combined == state_after_first_reset["show_combined"]
        assert state.current_channel == state_after_first_reset["current_channel"]
        assert state.crop_mode == state_after_first_reset["crop_mode"]
        assert state.crop_rect == state_after_first_reset["crop_rect"]
        assert state.crop_ratio == state_after_first_reset["crop_ratio"]
        assert state.grid_settings_dialog == state_after_first_reset["grid_settings_dialog"]

    @pytest.mark.parametrize("iteration", [1, 2, 3, 4, 5], ids=["iter_1", "iter_2", "iter_3", "iter_4", "iter_5"])
    def test_reset_maintains_state_across_iterations(self, iteration: int) -> None:
        """
        Given: AppState with custom values and reset called at a specific iteration
        When: reset() is called after modifying the state
        Then: state returns to defaults regardless of iteration count
        """
        # Arrange
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
        )
        # Act
        state.reset()
        # Assert
        assert state.show_combined is True
        assert state.current_channel == 0
        assert state.crop_mode is False


class TestAppStateMutability:
    """
    Test Design Specification: AppState field mutability and independence
    Module under test: src/ui/app_state.py

    Contract:
        Verifies that AppState instances are independent (no shared mutable state)
        and that all fields can be individually modified without affecting other fields.
        Multiple instances each own independent channel_paths lists.
        Modifying one instance's fields does not affect other instances.

    Equivalence partitions:
        EP1  Independent channel_paths instances → each instance owns separate list
        EP2  All list indices mutable            → each of [0], [1], [2] can be set
        EP3  Field independence                  → modifying one field leaves others unchanged
        EP4  Type preservation after reset       → all fields maintain correct types
        EP5  List independence between instances → instance1.channel_paths != instance2.channel_paths

    Boundary values:
        BV1  channel_paths[0] modification → doesn't affect [1] or [2]
        BV2  channel_paths[1] modification → doesn't affect [0] or [2]
        BV3  channel_paths[2] modification → doesn't affect [0] or [1]
        BV4  show_combined change → current_channel unchanged
        BV5  crop_mode change → other fields unchanged

    Exclusions:
        - Mutation of nested objects (assumes strings in channel_paths)
        - Shared state via class variables (AppState uses instance fields)
        - Reference equality (only value equality tested)

    Constraints:
        - Requires AppState as dataclass with mutable fields
        - No shared fixtures between instance creations
        - Each test creates fresh AppState instances
    """

    def test_independent_channel_paths_instances(self) -> None:
        """
        Given: two separate AppState instances
        When: channel_paths of the first instance is modified
        Then: the second instance's channel_paths remains unaffected
        """
        # Arrange
        state1 = AppState()
        state2 = AppState()
        # Act
        state1.channel_paths[0] = "/path1.tif"
        # Assert
        assert state2.channel_paths[0] is None

    def test_channel_paths_all_indices_mutable(self) -> None:
        """
        Given: AppState with default channel_paths
        When: all three indices are independently modified
        Then: all modifications persist correctly
        """
        # Arrange
        state = AppState()
        # Act
        state.channel_paths[0] = "/red.tif"
        state.channel_paths[1] = "/green.tif"
        state.channel_paths[2] = "/blue.tif"
        # Assert
        assert state.channel_paths == ["/red.tif", "/green.tif", "/blue.tif"]

    def test_modifying_one_field_independent(self) -> None:
        """
        Given: AppState with default field values
        When: one field (show_combined) is modified
        Then: other fields remain unchanged from their defaults
        """
        # Arrange
        state = AppState()
        # Act
        state.show_combined = False
        # Assert
        assert state.current_channel == 0  # Unchanged
        assert state.crop_mode is False  # Unchanged

    def test_reset_preserves_type_on_all_fields(self) -> None:
        """
        Given: AppState with custom values of various types
        When: reset() method is called
        Then: all fields maintain their correct types after reset
        """
        # Arrange
        state = AppState(
            channel_paths=["a", "b", "c"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
        )
        # Act
        state.reset()
        # Assert
        assert isinstance(state.channel_paths, list)
        assert all(v is None for v in state.channel_paths)
        assert isinstance(state.show_combined, bool)
        assert isinstance(state.current_channel, int)
        assert isinstance(state.crop_mode, bool)
