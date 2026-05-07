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

"""Mutable application state dataclass for the Prokudin main window."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    import numpy as np
    from PyQt5.QtCore import QRect

    from .widgets.grid_settings_dialog import GridSettingsDialog

from .default_state import DefaultState


@dataclass
class AppState:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Centralised mutable state owned by MainWindow.

    All fields are initialised to their default values on construction.
    Call reset() to restore defaults after a session ends.
    """

    original_images: List[Optional[np.ndarray]] = field(default_factory=lambda: [None, None, None])
    aligned: List[Optional[np.ndarray]] = field(default_factory=lambda: [None, None, None])
    processed: List[Optional[np.ndarray]] = field(default_factory=lambda: [None, None, None])
    original_rgb_images: List[Optional[np.ndarray]] = field(default_factory=lambda: [None, None, None])
    aligned_rgb: List[Optional[np.ndarray]] = field(default_factory=lambda: [None, None, None])
    channel_paths: List[Optional[str]] = field(default_factory=lambda: [None, None, None])
    show_combined: bool = DefaultState.SHOW_COMBINED
    current_channel: int = DefaultState.CURRENT_CHANNEL
    crop_mode: bool = DefaultState.CROP_MODE
    crop_rect: Optional[QRect] = None
    crop_ratio: Optional[Tuple[int, int]] = None
    grid_settings_dialog: Optional[GridSettingsDialog] = None

    def reset(self) -> None:
        """Restore every field to its default value."""
        self.original_images = [None, None, None]
        self.aligned = [None, None, None]
        self.processed = [None, None, None]
        self.original_rgb_images = [None, None, None]
        self.aligned_rgb = [None, None, None]
        self.channel_paths = [None, None, None]
        self.show_combined = DefaultState.SHOW_COMBINED
        self.current_channel = DefaultState.CURRENT_CHANNEL
        self.crop_mode = DefaultState.CROP_MODE
        self.crop_rect = None
        self.crop_ratio = None
        self.grid_settings_dialog = None
