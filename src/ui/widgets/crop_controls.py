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
Crop controls widget for the image viewer.
Provides aspect ratio selection and accept/cancel crop buttons.
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget


class CropControlsWidget(QWidget):
    """
    Widget containing crop controls (ratio selector and accept/cancel buttons).

    Signals:
        ratio_changed: Emitted when aspect ratio is changed. Payload is
            tuple[int, int] for a ratio or None for "Free" (unconstrained).
        accept_requested: Emitted when "Accept Crop" button is clicked.
        cancel_requested: Emitted when "Cancel Crop" button is clicked.
    """

    ratio_changed = pyqtSignal(object)  # tuple[int, int] | None
    accept_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize crop controls widget."""
        super().__init__(parent)
        self._ratio_options = [
            ("Free", None),
            ("16:9", (16, 9)),
            ("3:2", (3, 2)),
            ("4:3", (4, 3)),
            ("5:4", (5, 4)),
            ("1:1", (1, 1)),
            ("4:5", (4, 5)),
            ("3:4", (3, 4)),
            ("2:3", (2, 3)),
            ("9:16", (9, 16)),
        ]
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self._ratio_combo = QComboBox()
        self._ratio_combo.addItems([label for label, _ in self._ratio_options])
        self._ratio_combo.currentIndexChanged.connect(self._on_ratio_changed)

        self._accept_btn = QPushButton("Accept Crop")
        self._accept_btn.clicked.connect(self.accept_requested.emit)

        self._cancel_btn = QPushButton("Cancel Crop")
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)

        layout.addWidget(self._ratio_combo)
        layout.addWidget(self._accept_btn)
        layout.addWidget(self._cancel_btn)

        self.setLayout(layout)

    def _on_ratio_changed(self) -> None:
        """Handle aspect ratio combo box change."""
        ratio = self.get_selected_ratio()
        self.ratio_changed.emit(ratio)

    def get_selected_ratio(self) -> Optional[tuple[int, int]]:
        """Return the currently selected aspect ratio or None for 'Free'."""
        index = self._ratio_combo.currentIndex()
        if 0 <= index < len(self._ratio_options):
            return self._ratio_options[index][1]
        return None

    def set_enabled(self, enabled: bool) -> None:
        """Show or hide the entire widget."""
        self.setVisible(enabled)

    def reset(self) -> None:
        """Reset the ratio combo box to 'Free' (index 0)."""
        self._ratio_combo.setCurrentIndex(0)
