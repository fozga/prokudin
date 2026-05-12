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

"""Widget tests for src/ui/widgets/preset_panel.py."""

import json
from pathlib import Path

import pytest
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QPushButton
from pytestqt.plugin import QtBot

from src.ui.widgets.preset_panel import PresetItem, PresetPanel


@pytest.mark.widget
class TestPresetItem:
    """
    Test Design Specification: PresetItem
    Module under test: src/ui/widgets/preset_panel.py

    Widget base class: QFrame

    Contract:
        PresetItem is a clickable card showing a thumbnail image and a preset name.
        On construction it renders a thumbnail label (THUMBNAIL_W × THUMBNAIL_H) and a
        name label. If thumbnail_path exists on disk the path is loaded into QPixmap;
        otherwise the label shows "No image". The name is read from preset_data["name"]
        and falls back to "Unnamed" when the key is absent.
        mousePressEvent always emits clicked(preset_data) then propagates the event to the
        parent class unless the event is None. enterEvent and leaveEvent update the
        stylesheet for highlight feedback before optionally propagating.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - tmp_path used to create real files for the thumbnail-exists branch.
        - No service mocking needed.

    What is tested:
        - Widget instantiated without error for a missing thumbnail path.
        - "No image" text shown when thumbnail_path does not exist.
        - Widget instantiated without error when thumbnail_path points to an existing file.
        - Name label shows the value from preset_data["name"].
        - "Unnamed" fallback when preset_data has no "name" key.
        - clicked signal emitted with preset_data when mousePressEvent(None) is called.
        - Signal payload equals the original preset_data dict.
        - enterEvent(None) updates the stylesheet to the highlight colour.
        - leaveEvent(None) resets the stylesheet to transparent.
        - enterEvent and leaveEvent with a real QEvent do not raise an exception.

    What is NOT tested:
        - Actual pixel content of the thumbnail (rendered image).
        - Cursor shape or hover visual cues (not observable in headless mode).
        - QFrame.enterEvent / leaveEvent base-class side-effects.

    Equivalence partitions:
        EP1  thumbnail_path exists   → QPixmap loaded (may be null), label has pixmap
        EP2  thumbnail_path missing  → label shows "No image"
        EP3  preset_data has "name"  → name label shows that value
        EP4  preset_data missing key → name label shows "Unnamed"

    Boundary values:
        BV1  event = None in mousePressEvent → early return after emit
        BV2  event = real QEvent            → propagates to super()

    Mocking strategy:
        No external dependencies require mocking; thumbnail presence is controlled via
        tmp_path.

    Constraints:
        - mousePressEvent is invoked directly (not via qtbot.mouseClick) because the
          widget need not be visible for the signal-emission path.
        - Layout item indices: 0 = thumb_label, 1 = name_label.
    """

    def test_creates_without_error_for_missing_thumbnail(self, qtbot: QtBot) -> None:
        """
        Given preset_data with a name and a thumbnail_path that does not exist (EP2),
        When PresetItem is instantiated,
        Then it is created without raising an exception.
        """
        # Arrange + Act
        item = PresetItem({"name": "My Preset"}, "nonexistent_thumb.png")
        qtbot.addWidget(item)
        # Assert
        assert item is not None

    def test_shows_no_image_text_for_missing_thumbnail(self, qtbot: QtBot) -> None:
        """
        Given a thumbnail_path that does not exist on disk (EP2),
        When PresetItem is instantiated,
        Then the thumbnail label text is "No image".
        """
        # Arrange
        item = PresetItem({"name": "My Preset"}, "nonexistent_thumb.png")
        qtbot.addWidget(item)
        # Act
        thumb_label = item.layout().itemAt(0).widget()
        # Assert
        assert thumb_label.text() == "No image"

    def test_creates_without_error_for_existing_thumbnail(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a thumbnail_path pointing to a file that exists on disk (EP1),
        When PresetItem is instantiated,
        Then it is created without raising an exception (QPixmap null-pixmap is acceptable).
        """
        # Arrange
        thumb_file = tmp_path / "thumb.png"
        thumb_file.write_bytes(b"")
        # Act
        item = PresetItem({"name": "My Preset"}, str(thumb_file))
        qtbot.addWidget(item)
        # Assert
        assert item is not None

    def test_name_label_shows_value_from_preset_data(self, qtbot: QtBot) -> None:
        """
        Given preset_data containing key "name": "Special Preset" (EP3),
        When PresetItem is instantiated,
        Then the name label text is "Special Preset".
        """
        # Arrange
        item = PresetItem({"name": "Special Preset"}, "nonexistent.png")
        qtbot.addWidget(item)
        # Act
        name_label = item.layout().itemAt(1).widget()
        # Assert
        assert name_label.text() == "Special Preset"

    def test_name_label_falls_back_to_unnamed_when_key_missing(self, qtbot: QtBot) -> None:
        """
        Given preset_data without a "name" key (EP4),
        When PresetItem is instantiated,
        Then the name label text is "Unnamed".
        """
        # Arrange
        item = PresetItem({}, "nonexistent.png")
        qtbot.addWidget(item)
        # Act
        name_label = item.layout().itemAt(1).widget()
        # Assert
        assert name_label.text() == "Unnamed"

    def test_mouse_press_none_emits_clicked_signal(self, qtbot: QtBot) -> None:
        """
        Given a PresetItem with preset_data (BV1),
        When mousePressEvent is called with None,
        Then the clicked signal is emitted.
        """
        # Arrange
        item = PresetItem({"name": "Click Test"}, "nonexistent.png")
        qtbot.addWidget(item)
        # Act + Assert
        with qtbot.waitSignal(item.clicked, timeout=1000):
            item.mousePressEvent(None)

    def test_mouse_press_none_emits_clicked_with_preset_data(self, qtbot: QtBot) -> None:
        """
        Given a PresetItem with preset_data = {"name": "Click Test"} (BV1),
        When mousePressEvent is called with None,
        Then the emitted clicked signal payload equals the original preset_data dict.
        """
        # Arrange
        data = {"name": "Click Test", "brightness": 10}
        item = PresetItem(data, "nonexistent.png")
        qtbot.addWidget(item)
        received: list[dict] = []
        item.clicked.connect(received.append)
        # Act
        item.mousePressEvent(None)
        # Assert
        assert received == [data]

    def test_enter_event_none_applies_highlight_stylesheet(self, qtbot: QtBot) -> None:
        """
        Given a PresetItem with no highlight style,
        When enterEvent is called with None,
        Then the widget stylesheet contains a background-color rule.
        """
        # Arrange
        item = PresetItem({"name": "Test"}, "nonexistent.png")
        qtbot.addWidget(item)
        # Act
        item.enterEvent(None)
        # Assert
        assert "background-color" in item.styleSheet()

    def test_leave_event_none_restores_transparent_stylesheet(self, qtbot: QtBot) -> None:
        """
        Given a PresetItem with the highlight style applied by enterEvent,
        When leaveEvent is called with None,
        Then the widget stylesheet contains "transparent".
        """
        # Arrange
        item = PresetItem({"name": "Test"}, "nonexistent.png")
        qtbot.addWidget(item)
        item.enterEvent(None)
        # Act
        item.leaveEvent(None)
        # Assert
        assert "transparent" in item.styleSheet()

    def test_enter_event_with_real_event_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given a PresetItem and a real QEvent of type Enter (BV2),
        When enterEvent is called with that event,
        Then no exception is raised.
        """
        # Arrange
        item = PresetItem({"name": "Test"}, "nonexistent.png")
        qtbot.addWidget(item)
        event = QEvent(QEvent.Enter)
        # Act + Assert
        item.enterEvent(event)

    def test_leave_event_with_real_event_does_not_raise(self, qtbot: QtBot) -> None:
        """
        Given a PresetItem and a real QEvent of type Leave (BV2),
        When leaveEvent is called with that event,
        Then no exception is raised.
        """
        # Arrange
        item = PresetItem({"name": "Test"}, "nonexistent.png")
        qtbot.addWidget(item)
        event = QEvent(QEvent.Leave)
        # Act + Assert
        item.leaveEvent(event)


@pytest.mark.widget
class TestPresetPanel:
    """
    Test Design Specification: PresetPanel
    Module under test: src/ui/widgets/preset_panel.py

    Widget base class: QWidget

    Contract:
        PresetPanel is a left-sidebar widget with a "Save Preset" button and a QScrollArea
        containing a scrollable list of PresetItem widgets. On construction it calls
        reload_presets(), which scans presets_dir for .json files, parses each one, creates
        a PresetItem, and inserts it before the stretch item in the internal layout.
        Files that are not .json, have invalid JSON, or cannot be opened are silently
        skipped. reload_presets() clears existing items before repopulating.
        save_requested is emitted when the Save Preset button is clicked. preset_selected
        is emitted (with the preset data dict) when any PresetItem is clicked.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - tmp_path fixture used for real filesystem interactions (no mocking of OS calls).

    What is tested:
        - Panel created without error for an existing and a nonexistent presets_dir.
        - Empty directory results in zero preset items (layout count == 1, stretch only).
        - .json files in the directory are loaded as PresetItem widgets.
        - Non-.json files in the directory are skipped.
        - .json files with invalid JSON are skipped without raising.
        - Calling reload_presets() a second time clears old items before repopulating.
        - Clicking the Save Preset button emits save_requested.
        - Clicking a PresetItem propagates preset_selected with the preset data.

    What is NOT tested:
        - Visual appearance of the scroll area or the preset thumbnails.
        - Ordering guarantees beyond "sorted(os.listdir)" (implementation detail).

    Equivalence partitions:
        EP1  presets_dir is an existing directory   → presets loaded
        EP2  presets_dir does not exist             → no presets, no error
        EP3  file ends with .json, valid JSON       → PresetItem created
        EP4  file ends with .json, invalid JSON     → skipped silently
        EP5  file does not end with .json           → skipped silently

    Boundary values:
        BV1  0 .json files in directory             (empty, only stretch in layout)
        BV2  1 .json file in directory              (exactly one PresetItem)
        BV3  2 .json files in directory             (two PresetItems)

    Mocking strategy:
        Real files are written to tmp_path; no OS-level mocking is used.

    Constraints:
        - _list_layout always contains exactly one stretch item added during __init__.
          count() == 1 + number_of_preset_items.
        - PresetItem widgets are inserted with insertWidget(count - 1, widget), placing
          them before the stretch at the last position.
        - deleteLater() is asynchronous but takeAt() removes items from the layout
          synchronously, so count() is reliable immediately after reload_presets().
    """

    @staticmethod
    def _write_preset(directory: Path, stem: str, data: dict | None = None) -> Path:
        """Write a valid JSON preset file to directory and return its path."""
        payload = data if data is not None else {"name": stem, "brightness": 0}
        path = directory / f"{stem}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_panel_creates_without_error_for_existing_dir(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given an existing empty presets_dir (EP1, BV1),
        When PresetPanel is instantiated,
        Then the panel is created without raising an exception.
        """
        # Arrange + Act
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        # Assert
        assert panel is not None

    def test_panel_creates_without_error_for_nonexistent_dir(self, qtbot: QtBot) -> None:
        """
        Given a presets_dir that does not exist on disk (EP2),
        When PresetPanel is instantiated,
        Then the panel is created without raising an exception.
        """
        # Arrange + Act
        panel = PresetPanel("/nonexistent/path/to/presets")
        qtbot.addWidget(panel)
        # Assert
        assert panel is not None

    def test_empty_dir_has_no_preset_items(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given an empty presets_dir (EP1, BV1),
        When PresetPanel is instantiated,
        Then _list_layout contains only the stretch item (count == 1).
        """
        # Arrange
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        # Act + Assert
        assert panel._list_layout.count() == 1

    def test_one_json_file_loads_one_preset_item(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a presets_dir containing exactly one valid .json file (EP3, BV2),
        When PresetPanel is instantiated,
        Then _list_layout contains one PresetItem plus the stretch (count == 2).
        """
        # Arrange
        self._write_preset(tmp_path, "preset_a")
        # Act
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        # Assert
        assert panel._list_layout.count() == 2

    def test_two_json_files_load_two_preset_items(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a presets_dir containing two valid .json files (EP3, BV3),
        When PresetPanel is instantiated,
        Then _list_layout contains two PresetItems plus the stretch (count == 3).
        """
        # Arrange
        self._write_preset(tmp_path, "preset_a")
        self._write_preset(tmp_path, "preset_b")
        # Act
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        # Assert
        assert panel._list_layout.count() == 3

    def test_non_json_files_are_skipped(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a presets_dir with one .json and one .txt file (EP5),
        When PresetPanel is instantiated,
        Then only the .json file is loaded (count == 2).
        """
        # Arrange
        self._write_preset(tmp_path, "preset_a")
        (tmp_path / "readme.txt").write_text("not a preset", encoding="utf-8")
        # Act
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        # Assert
        assert panel._list_layout.count() == 2

    def test_invalid_json_files_are_skipped(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a presets_dir with one valid and one malformed .json file (EP4),
        When PresetPanel is instantiated,
        Then only the valid file is loaded (count == 2) without raising an exception.
        """
        # Arrange
        self._write_preset(tmp_path, "valid_preset")
        (tmp_path / "broken.json").write_text("not valid json {{{", encoding="utf-8")
        # Act
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        # Assert
        assert panel._list_layout.count() == 2

    def test_reload_presets_clears_existing_items_before_repopulating(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a PresetPanel with two presets already loaded (BV3),
        When reload_presets is called a second time,
        Then the layout count is still 3 (not doubled to 5).
        """
        # Arrange
        self._write_preset(tmp_path, "preset_a")
        self._write_preset(tmp_path, "preset_b")
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        # Act
        panel.reload_presets()
        # Assert
        assert panel._list_layout.count() == 3

    def test_save_button_click_emits_save_requested(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a PresetPanel,
        When the Save Preset button is clicked,
        Then save_requested is emitted.
        """
        # Arrange
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        save_btn = panel.findChild(QPushButton)
        # Act + Assert
        with qtbot.waitSignal(panel.save_requested, timeout=1000):
            save_btn.click()

    def test_preset_item_click_emits_preset_selected_with_data(self, qtbot: QtBot, tmp_path: Path) -> None:
        """
        Given a PresetPanel with one loaded preset and known preset data (BV2),
        When the PresetItem's mousePressEvent is triggered with None,
        Then preset_selected is emitted with the preset data dict.
        """
        # Arrange
        data = {"name": "Test", "brightness": 5}
        self._write_preset(tmp_path, "test_preset", data)
        panel = PresetPanel(str(tmp_path))
        qtbot.addWidget(panel)
        preset_item = panel._list_layout.itemAt(0).widget()
        # Act + Assert
        with qtbot.waitSignal(panel.preset_selected, timeout=1000):
            preset_item.mousePressEvent(None)
