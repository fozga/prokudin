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

# pylint: disable=too-few-public-methods

"""
Preset panel widget providing a scrollable list of saved presets with thumbnails.
Users can save current slider values as a named preset, and apply any preset by clicking it.
"""

import json
import os

from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

THUMBNAIL_W = 120
THUMBNAIL_H = 80


class PresetItem(QFrame):
    """A clickable widget showing a preset's thumbnail and name."""

    clicked = pyqtSignal(dict)

    def __init__(self, preset_data: dict, thumbnail_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.preset_data = preset_data
        self.setFrameShape(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)  # type: ignore[attr-defined]
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        thumb_label = QLabel()
        thumb_label.setFixedSize(THUMBNAIL_W, THUMBNAIL_H)
        thumb_label.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
        thumb_label.setStyleSheet("border: none; background-color: transparent;")
        if os.path.exists(thumbnail_path):
            pixmap = QPixmap(thumbnail_path).scaled(
                THUMBNAIL_W, THUMBNAIL_H, Qt.KeepAspectRatio, Qt.SmoothTransformation  # type: ignore[attr-defined]
            )
            thumb_label.setPixmap(pixmap)
        else:
            thumb_label.setText("No image")
        layout.addWidget(thumb_label, alignment=Qt.AlignCenter)  # type: ignore[attr-defined]

        name_label = QLabel(preset_data.get("name", "Unnamed"))
        name_label.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 10pt;")
        layout.addWidget(name_label)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # pylint: disable=invalid-name
        """Emit clicked signal when preset is clicked."""
        self.clicked.emit(self.preset_data)
        if event is None:
            return
        super().mousePressEvent(event)

    def enterEvent(self, event: QEvent | None) -> None:  # pylint: disable=invalid-name
        """Highlight preset on mouse enter."""
        self.setStyleSheet("QFrame { background-color: rgba(100, 150, 255, 0.15); }")
        if event is None:
            return
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent | None) -> None:  # pylint: disable=invalid-name
        """Remove highlight on mouse leave."""
        self.setStyleSheet("QFrame { background-color: transparent; }")
        if event is None:
            return
        super().leaveEvent(event)


class PresetPanel(QWidget):
    """
    Left-sidebar panel with a scrollable list of presets and a save button.

    Signals:
        preset_selected: Emitted when user clicks a preset item, carries preset data dict.
        save_requested:  Emitted when user clicks "Save Preset".
    """

    preset_selected = pyqtSignal(dict)
    save_requested = pyqtSignal()

    def __init__(self, presets_dir: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.presets_dir = presets_dir

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        title = QLabel("Presets")
        title.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)

        save_btn = QPushButton("Save Preset")
        save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(save_btn)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # type: ignore[attr-defined]

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(2, 2, 2, 2)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        layout.addWidget(self._scroll)

        self.setMinimumWidth(THUMBNAIL_W + 30)

        self.reload_presets()

    def reload_presets(self) -> None:
        """Clear and repopulate the list from the presets directory."""
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()  # type: ignore[union-attr]

        if not os.path.isdir(self.presets_dir):
            return

        for fname in sorted(os.listdir(self.presets_dir)):
            if not fname.endswith(".json"):
                continue
            json_path = os.path.join(self.presets_dir, fname)
            thumb_path = os.path.splitext(json_path)[0] + ".png"
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            widget = PresetItem(data, thumb_path)
            widget.clicked.connect(self.preset_selected.emit)
            self._list_layout.insertWidget(self._list_layout.count() - 1, widget)
