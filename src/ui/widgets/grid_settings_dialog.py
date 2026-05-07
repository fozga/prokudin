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
Grid settings dialog for selecting grid type and line width.
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from .grid_types import (
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


class GridSettingsDialog(QFrame):
    """
    Overlay panel for configuring grid overlay settings.

    Provides a list of grid types and controls for adjusting grid line width.
    """

    # Signals
    grid_type_changed = pyqtSignal(str)  # Emits grid type name
    line_width_changed = pyqtSignal(int)  # Emits new line width

    MIN_LINE_WIDTH = 1
    MAX_LINE_WIDTH = 10

    # Grid type definitions: (display_name, internal_value)
    GRID_TYPES = [
        ("None", GRID_TYPE_NONE),
        ("3x3 Grid", GRID_TYPE_3X3),
        ("Golden Ratio", GRID_TYPE_GOLDEN_RATIO),
        ("Diagonal 1:1", GRID_TYPE_DIAGONAL_1_1),
        ("Diagonal 2:3", GRID_TYPE_DIAGONAL_2_3),
        ("Diagonal 3:2", GRID_TYPE_DIAGONAL_3_2),
        ("Diagonal 3:4", GRID_TYPE_DIAGONAL_3_4),
        ("Diagonal 4:3", GRID_TYPE_DIAGONAL_4_3),
        ("Diagonal + Thirds V", GRID_TYPE_DIAGONAL_THIRDS_V),
        ("Diagonal + Thirds H", GRID_TYPE_DIAGONAL_THIRDS_H),
        ("Diagonal + Golden V", GRID_TYPE_DIAGONAL_GOLDEN_V),
        ("Diagonal + Golden H", GRID_TYPE_DIAGONAL_GOLDEN_H),
        # Future grid types can be added here:
    ]

    def __init__(
        self, current_width: int = 4, current_grid_type: str = GRID_TYPE_3X3, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the grid settings overlay.

        Args:
            current_width: Current line width in pixels.
            current_grid_type: Currently selected grid type.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)  # type: ignore[arg-type]
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self._current_width = current_width
        self._current_grid_type = current_grid_type
        self._init_ui()

    def _init_ui(self) -> None:
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Line width control at the top
        width_layout = QHBoxLayout()
        width_layout.setSpacing(5)

        width_label = QLabel("Line Width:")
        width_layout.addWidget(width_label)

        # Decrease button
        self.decrease_btn = QPushButton("-")
        self.decrease_btn.setFixedWidth(30)
        self.decrease_btn.clicked.connect(self._decrease_width)
        width_layout.addWidget(self.decrease_btn)

        # Width display
        self.width_display = QLabel(str(self._current_width))
        self.width_display.setFixedWidth(30)
        self.width_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.width_display.setStyleSheet("QLabel { background-color: white; border: 1px solid gray; padding: 2px; }")
        width_layout.addWidget(self.width_display)

        # Increase button
        self.increase_btn = QPushButton("+")
        self.increase_btn.setFixedWidth(30)
        self.increase_btn.clicked.connect(self._increase_width)
        width_layout.addWidget(self.increase_btn)

        width_layout.addStretch()
        main_layout.addLayout(width_layout)

        # Grid type list
        grid_label = QLabel("Grid Type:")
        main_layout.addWidget(grid_label)

        self.grid_list = QListWidget()

        # Populate grid types from GRID_TYPES definition
        for display_name, _ in self.GRID_TYPES:
            self.grid_list.addItem(display_name)

        # Set current selection based on grid type value
        current_index = self._get_grid_type_index(self._current_grid_type)
        if current_index >= 0:
            self.grid_list.setCurrentRow(current_index)

        self.grid_list.currentRowChanged.connect(self._on_grid_type_changed)
        main_layout.addWidget(self.grid_list)

        # Set dialog size
        self.setFixedSize(200, 200)

        self._update_button_states()

    def _decrease_width(self) -> None:
        """Decrease line width by 1."""
        if self._current_width > self.MIN_LINE_WIDTH:
            self._current_width -= 1
            self._update_width_display()
            self.line_width_changed.emit(self._current_width)

    def _increase_width(self) -> None:
        """Increase line width by 1."""
        if self._current_width < self.MAX_LINE_WIDTH:
            self._current_width += 1
            self._update_width_display()
            self.line_width_changed.emit(self._current_width)

    def _update_width_display(self) -> None:
        """Update the width display label and button states."""
        self.width_display.setText(str(self._current_width))
        self._update_button_states()

    def _update_button_states(self) -> None:
        """Enable/disable buttons based on current width."""
        self.decrease_btn.setEnabled(self._current_width > self.MIN_LINE_WIDTH)
        self.increase_btn.setEnabled(self._current_width < self.MAX_LINE_WIDTH)

    def _get_grid_type_index(self, grid_type: str) -> int:
        """
        Get the list index for a given grid type value.

        Args:
            grid_type: The grid type value to find.

        Returns:
            int: The index in GRID_TYPES, or -1 if not found.
        """
        for index, (_, value) in enumerate(self.GRID_TYPES):
            if value == grid_type:
                return index
        return -1

    def _get_grid_type_value(self, index: int) -> str:
        """
        Get the grid type value for a given list index.

        Args:
            index: The index in the grid type list.

        Returns:
            str: The grid type value, or GRID_TYPE_NONE if index is invalid.
        """
        if 0 <= index < len(self.GRID_TYPES):
            return self.GRID_TYPES[index][1]
        return GRID_TYPE_NONE

    def _on_grid_type_changed(self, row: int) -> None:
        """
        Handle grid type selection change.

        Args:
            row: The selected row index in the list widget.
        """
        grid_type = self._get_grid_type_value(row)
        self._current_grid_type = grid_type
        self.grid_type_changed.emit(grid_type)

    def get_current_grid_type(self) -> str:
        """
        Get the currently selected grid type.

        Returns:
            str: The current grid type (e.g., GridType.NONE or GridType.GRID_3X3).
        """
        return self._current_grid_type

    def get_current_line_width(self) -> int:
        """
        Get the current line width.

        Returns:
            int: The current line width in pixels.
        """
        return self._current_width
