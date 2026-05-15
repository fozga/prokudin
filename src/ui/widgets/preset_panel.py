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
Supports renaming and deleting presets via right-click context menu.
"""

import json
import os
import re

from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

THUMBNAIL_W = 120
THUMBNAIL_H = 80


class PresetItem(QFrame):
    """A clickable widget showing a preset's thumbnail and name."""

    clicked = pyqtSignal(dict)
    rename_requested = pyqtSignal(dict, str)
    delete_requested = pyqtSignal(dict)

    def __init__(
        self, preset_data: dict, thumbnail_path: str, is_protected: bool = False, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.preset_data = preset_data
        self.thumbnail_path = thumbnail_path
        self.is_protected = is_protected
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

    def contextMenuEvent(self, event: QEvent | None) -> None:  # pylint: disable=invalid-name
        """Show context menu on right-click with rename and delete options."""
        menu = QMenu(self)

        if not self.is_protected:
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(self._handle_rename)
            menu.addSeparator()

        if not self.is_protected:
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(self._handle_delete)

        if event and isinstance(event, QContextMenuEvent):
            menu.exec_(event.globalPos())
        else:
            menu.exec_(self.cursor().pos())

    def _handle_rename(self) -> None:
        """Open rename dialog and emit rename_requested signal."""
        current_name = self.preset_data.get("name", "Unnamed")
        new_name, ok = QInputDialog.getText(self, "Rename Preset", "New name:", text=current_name)

        if not ok:
            return

        new_name = new_name.strip()
        if not new_name:
            QMessageBox.warning(self, "Invalid Name", "Preset name cannot be empty.")
            return

        if new_name == current_name:
            return

        self.rename_requested.emit(self.preset_data, new_name)

    def _handle_delete(self) -> None:
        """Emit delete_requested signal."""
        self.delete_requested.emit(self.preset_data)


class PresetPanel(QWidget):
    """
    Left-sidebar panel with a scrollable list of presets and a save button.

    Signals:
        preset_selected: Emitted when user clicks a preset item, carries preset data dict.
        save_requested:  Emitted when user clicks "Save Preset".
        preset_renamed:  Emitted when a preset is successfully renamed.
        preset_deleted:  Emitted when a preset is successfully deleted.
    """

    preset_selected = pyqtSignal(dict)
    save_requested = pyqtSignal()
    preset_renamed = pyqtSignal(str, str)
    preset_deleted = pyqtSignal(str)

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

        self.save_btn = QPushButton("Save Preset")
        self.save_btn.clicked.connect(self.save_requested.emit)
        layout.addWidget(self.save_btn)

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
            widget.rename_requested.connect(self._handle_rename_preset)
            widget.delete_requested.connect(self._handle_delete_preset)
            self._list_layout.insertWidget(self._list_layout.count() - 1, widget)

    def _handle_rename_preset(self, preset_data: dict, new_name: str) -> None:
        """Handle preset rename by updating the JSON file."""
        old_name = preset_data.get("name", "")
        if not new_name or not new_name.strip():
            QMessageBox.warning(self, "Invalid Name", "Preset name cannot be empty.")
            return

        new_name = new_name.strip()

        if not self._is_valid_preset_name(new_name):
            error_msg = (
                "Preset name contains invalid characters.\n"
                "Only alphanumeric, spaces, hyphens, and underscores are allowed."
            )
            QMessageBox.warning(self, "Invalid Name", error_msg)
            return

        safe_old_name = re.sub(r"[^\w\s-]", "", old_name).strip().replace(" ", "_")
        safe_new_name = re.sub(r"[^\w\s-]", "", new_name).strip().replace(" ", "_")

        if safe_old_name == safe_new_name and old_name == new_name:
            return

        if self._preset_exists(new_name):
            QMessageBox.warning(self, "Duplicate Name", f"A preset named '{new_name}' already exists.")
            return

        old_json_path = os.path.join(self.presets_dir, f"{safe_old_name}.json")
        new_json_path = os.path.join(self.presets_dir, f"{safe_new_name}.json")
        old_thumb_path = os.path.join(self.presets_dir, f"{safe_old_name}.png")
        new_thumb_path = os.path.join(self.presets_dir, f"{safe_new_name}.png")

        try:
            if os.path.exists(old_json_path):
                preset_data["name"] = new_name
                with open(new_json_path, "w", encoding="utf-8") as f:
                    json.dump(preset_data, f, indent=2)
                os.remove(old_json_path)

                if os.path.exists(old_thumb_path):
                    os.rename(old_thumb_path, new_thumb_path)

                self.preset_renamed.emit(old_name, new_name)
                self.reload_presets()
        except OSError as e:
            QMessageBox.critical(self, "Rename Error", f"Failed to rename preset: {e}")

    def _handle_delete_preset(self, preset_data: dict) -> None:
        """Handle preset deletion by removing the JSON and thumbnail files."""
        preset_name = preset_data.get("name", "Unnamed")
        safe_name = re.sub(r"[^\w\s-]", "", preset_name).strip().replace(" ", "_")

        json_path = os.path.join(self.presets_dir, f"{safe_name}.json")
        thumb_path = os.path.join(self.presets_dir, f"{safe_name}.png")

        try:
            if os.path.exists(json_path):
                os.remove(json_path)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)

            self.preset_deleted.emit(preset_name)
            self.reload_presets()
        except OSError as e:
            QMessageBox.critical(self, "Delete Error", f"Failed to delete preset: {e}")

    @staticmethod
    def _is_valid_preset_name(name: str) -> bool:
        """Check if a preset name contains only valid characters."""
        return bool(re.match(r"^[\w\s\-]+$", name))

    def _preset_exists(self, name: str) -> bool:
        """Check if a preset with the given name already exists."""
        if not os.path.isdir(self.presets_dir):
            return False

        for existing_preset in self._get_preset_names():
            if existing_preset.lower() == name.lower():
                return True
        return False

    def _get_preset_names(self) -> list[str]:
        """Get list of all preset names from the presets directory."""
        names: list[str] = []
        if not os.path.isdir(self.presets_dir):
            return names

        for fname in os.listdir(self.presets_dir):
            if not fname.endswith(".json"):
                continue
            json_path = os.path.join(self.presets_dir, fname)
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "name" in data:
                        names.append(data["name"])
            except (json.JSONDecodeError, OSError):
                continue
        return names
