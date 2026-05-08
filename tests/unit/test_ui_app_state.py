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
    """Tests for AppState default initialization."""

    def test_default_channel_paths(self) -> None:
        """Verify channel_paths defaults to list of 3 None values."""
        state = AppState()
        assert state.channel_paths == [None, None, None]
        assert len(state.channel_paths) == 3

    def test_channel_paths_is_mutable_list(self) -> None:
        """Verify channel_paths is a mutable list that can be modified."""
        state = AppState()
        state.channel_paths[0] = "/path/to/red.tif"
        assert state.channel_paths[0] == "/path/to/red.tif"
        assert state.channel_paths[1] is None
        assert state.channel_paths[2] is None

    def test_default_show_combined(self) -> None:
        """Verify show_combined defaults to DefaultState.SHOW_COMBINED."""
        state = AppState()
        assert state.show_combined is DefaultState.SHOW_COMBINED
        assert state.show_combined is True

    def test_show_combined_is_boolean(self) -> None:
        """Verify show_combined is a boolean type."""
        state = AppState()
        assert isinstance(state.show_combined, bool)

    def test_default_current_channel(self) -> None:
        """Verify current_channel defaults to DefaultState.CURRENT_CHANNEL."""
        state = AppState()
        assert state.current_channel == DefaultState.CURRENT_CHANNEL
        assert state.current_channel == 0

    def test_current_channel_is_integer(self) -> None:
        """Verify current_channel is an integer type."""
        state = AppState()
        assert isinstance(state.current_channel, int)

    def test_default_crop_mode(self) -> None:
        """Verify crop_mode defaults to DefaultState.CROP_MODE."""
        state = AppState()
        assert state.crop_mode is DefaultState.CROP_MODE
        assert state.crop_mode is False

    def test_crop_mode_is_boolean(self) -> None:
        """Verify crop_mode is a boolean type."""
        state = AppState()
        assert isinstance(state.crop_mode, bool)

    def test_default_crop_rect(self) -> None:
        """Verify crop_rect defaults to None."""
        state = AppState()
        assert state.crop_rect is None

    def test_default_crop_ratio(self) -> None:
        """Verify crop_ratio defaults to None."""
        state = AppState()
        assert state.crop_ratio is None

    def test_default_grid_settings_dialog(self) -> None:
        """Verify grid_settings_dialog defaults to None."""
        state = AppState()
        assert state.grid_settings_dialog is None

    def test_custom_initialization(self) -> None:
        """Verify AppState can be initialized with custom values."""
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
            crop_rect=None,
            crop_ratio=(16, 9),
            grid_settings_dialog=None,
        )
        assert state.channel_paths == ["/red.tif", "/green.tif", "/blue.tif"]
        assert state.show_combined is False
        assert state.current_channel == 2
        assert state.crop_mode is True
        assert state.crop_ratio == (16, 9)


class TestAppStateReset:
    """Tests for AppState reset() method."""

    def test_reset_channel_paths(self) -> None:
        """Verify reset() clears all channel paths."""
        state = AppState()
        state.channel_paths = ["/red.tif", "/green.tif", "/blue.tif"]
        state.reset()
        assert state.channel_paths == [None, None, None]

    def test_reset_show_combined(self) -> None:
        """Verify reset() restores show_combined to default."""
        state = AppState()
        state.show_combined = False
        state.reset()
        assert state.show_combined is DefaultState.SHOW_COMBINED
        assert state.show_combined is True

    def test_reset_current_channel(self) -> None:
        """Verify reset() restores current_channel to default."""
        state = AppState()
        state.current_channel = 2
        state.reset()
        assert state.current_channel == DefaultState.CURRENT_CHANNEL
        assert state.current_channel == 0

    def test_reset_crop_mode(self) -> None:
        """Verify reset() restores crop_mode to default."""
        state = AppState()
        state.crop_mode = True
        state.reset()
        assert state.crop_mode is DefaultState.CROP_MODE
        assert state.crop_mode is False

    def test_reset_crop_rect(self) -> None:
        """Verify reset() clears crop_rect."""
        state = AppState()
        state.crop_rect = object()  # Simulate QRect
        state.reset()
        assert state.crop_rect is None

    def test_reset_crop_ratio(self) -> None:
        """Verify reset() clears crop_ratio."""
        state = AppState()
        state.crop_ratio = (16, 9)
        state.reset()
        assert state.crop_ratio is None

    def test_reset_grid_settings_dialog(self) -> None:
        """Verify reset() clears grid_settings_dialog."""
        state = AppState()
        state.grid_settings_dialog = object()  # Simulate GridSettingsDialog
        state.reset()
        assert state.grid_settings_dialog is None

    def test_reset_all_fields_together(self) -> None:
        """Verify reset() restores all fields simultaneously."""
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=1,
            crop_mode=True,
            crop_rect=object(),
            crop_ratio=(16, 9),
            grid_settings_dialog=object(),
        )
        state.reset()
        assert state.channel_paths == [None, None, None]
        assert state.show_combined is True
        assert state.current_channel == 0
        assert state.crop_mode is False
        assert state.crop_rect is None
        assert state.crop_ratio is None
        assert state.grid_settings_dialog is None

    def test_reset_idempotent(self) -> None:
        """Verify reset() is idempotent (calling twice has same effect)."""
        state = AppState(
            channel_paths=["/red.tif", "/green.tif", "/blue.tif"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
        )
        state.reset()
        state_after_first = AppState()
        state.reset()
        state_after_second = AppState()
        assert state.channel_paths == state_after_first.channel_paths
        assert state.show_combined == state_after_first.show_combined
        assert state.current_channel == state_after_first.current_channel
        assert state.crop_mode == state_after_first.crop_mode

    def test_reset_multiple_times(self) -> None:
        """Verify reset() can be called multiple times."""
        state = AppState()
        for _ in range(5):
            state.show_combined = False
            state.current_channel = 2
            state.crop_mode = True
            state.reset()
            assert state.show_combined is True
            assert state.current_channel == 0
            assert state.crop_mode is False


class TestAppStateMutability:
    """Tests for AppState field mutability and independence."""

    def test_independent_channel_paths_instances(self) -> None:
        """Verify different AppState instances have independent channel_paths."""
        state1 = AppState()
        state2 = AppState()
        state1.channel_paths[0] = "/path1.tif"
        assert state2.channel_paths[0] is None

    def test_channel_paths_all_indices_mutable(self) -> None:
        """Verify all indices of channel_paths are independently mutable."""
        state = AppState()
        state.channel_paths[0] = "/red.tif"
        state.channel_paths[1] = "/green.tif"
        state.channel_paths[2] = "/blue.tif"
        assert state.channel_paths == ["/red.tif", "/green.tif", "/blue.tif"]

    def test_modifying_one_field_independent(self) -> None:
        """Verify modifying one field doesn't affect others."""
        state = AppState()
        state.show_combined = False
        assert state.current_channel == 0  # Unchanged
        assert state.crop_mode is False  # Unchanged

    def test_reset_preserves_type_on_all_fields(self) -> None:
        """Verify reset() maintains correct types for all fields."""
        state = AppState(
            channel_paths=["a", "b", "c"],
            show_combined=False,
            current_channel=2,
            crop_mode=True,
        )
        state.reset()
        assert isinstance(state.channel_paths, list)
        assert all(v is None for v in state.channel_paths)
        assert isinstance(state.show_combined, bool)
        assert isinstance(state.current_channel, int)
        assert isinstance(state.crop_mode, bool)
