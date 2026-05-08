"""Unit tests for src.ui.app_state module.

Tests AppState dataclass and state reset functionality.
"""

import pytest

from src.ui.app_state import AppState
from src.ui.default_state import DefaultState


class TestAppState:
    """Test suite for AppState dataclass."""

    def test_default_channel_paths(self) -> None:
        """Test channel_paths defaults to [None, None, None]."""
        state = AppState()
        assert state.channel_paths == [None, None, None]
        assert len(state.channel_paths) == 3

    def test_default_show_combined(self) -> None:
        """Test show_combined defaults to DefaultState.SHOW_COMBINED."""
        state = AppState()
        assert state.show_combined is DefaultState.SHOW_COMBINED

    def test_default_current_channel(self) -> None:
        """Test current_channel defaults to DefaultState.CURRENT_CHANNEL."""
        state = AppState()
        assert state.current_channel == DefaultState.CURRENT_CHANNEL

    def test_default_crop_mode(self) -> None:
        """Test crop_mode defaults to DefaultState.CROP_MODE."""
        state = AppState()
        assert state.crop_mode is DefaultState.CROP_MODE

    def test_default_crop_rect(self) -> None:
        """Test crop_rect defaults to None."""
        state = AppState()
        assert state.crop_rect is None

    def test_default_crop_ratio(self) -> None:
        """Test crop_ratio defaults to None."""
        state = AppState()
        assert state.crop_ratio is None

    def test_reset_channel_paths(self) -> None:
        """Test reset() restores channel_paths to [None, None, None]."""
        state = AppState()
        state.channel_paths = ["path1", "path2", "path3"]
        state.reset()
        assert state.channel_paths == [None, None, None]

    def test_reset_show_combined(self) -> None:
        """Test reset() restores show_combined to default."""
        state = AppState()
        state.show_combined = not DefaultState.SHOW_COMBINED
        state.reset()
        assert state.show_combined is DefaultState.SHOW_COMBINED

    def test_reset_current_channel(self) -> None:
        """Test reset() restores current_channel to default."""
        state = AppState()
        state.current_channel = 2
        state.reset()
        assert state.current_channel == DefaultState.CURRENT_CHANNEL

    def test_reset_crop_mode(self) -> None:
        """Test reset() restores crop_mode to default."""
        state = AppState()
        state.crop_mode = True
        state.reset()
        assert state.crop_mode is DefaultState.CROP_MODE

    def test_reset_crop_rect(self) -> None:
        """Test reset() clears crop_rect."""
        state = AppState()
        state.crop_rect = object()  # Mock QRect
        state.reset()
        assert state.crop_rect is None

    def test_reset_crop_ratio(self) -> None:
        """Test reset() clears crop_ratio."""
        state = AppState()
        state.crop_ratio = (16, 9)
        state.reset()
        assert state.crop_ratio is None

    def test_reset_all_fields(self) -> None:
        """Test reset() restores all fields at once."""
        state = AppState()
        # Modify all fields
        state.channel_paths = ["a", "b", "c"]
        state.show_combined = False
        state.current_channel = 2
        state.crop_mode = True
        state.crop_rect = object()
        state.crop_ratio = (4, 3)
        # Reset and verify all are restored
        state.reset()
        assert state.channel_paths == [None, None, None]
        assert state.show_combined is DefaultState.SHOW_COMBINED
        assert state.current_channel == DefaultState.CURRENT_CHANNEL
        assert state.crop_mode is DefaultState.CROP_MODE
        assert state.crop_rect is None
        assert state.crop_ratio is None
