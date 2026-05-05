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

"""Handlers for saving and applying image adjustment presets."""

from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QInputDialog, QMessageBox

if TYPE_CHECKING:
    from ..main_window import MainWindow

_CHANNEL_NAMES = ["red", "green", "blue"]
_SLIDER_NAMES = ["brightness", "contrast", "intensity"]


def save_preset(main_window: "MainWindow") -> None:
    """
    Show a name dialog, then save current slider values and a thumbnail to the presets folder.
    """
    name, ok = QInputDialog.getText(main_window, "Save Preset", "Preset name:")
    if not ok or not name.strip():
        return

    name = name.strip()
    safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    if not safe_name:
        QMessageBox.warning(main_window, "Invalid Name", "Please enter a valid preset name.")
        return

    channels: dict = {}
    for i, ctrl in enumerate(main_window.controllers):
        channels[_CHANNEL_NAMES[i]] = {s: ctrl.sliders[s].value() for s in _SLIDER_NAMES}

    preset_data = {"name": name, "channels": channels}

    os.makedirs(main_window.presets_dir, exist_ok=True)  # type: ignore[arg-type]
    json_path = os.path.join(main_window.presets_dir, f"{safe_name}.json")  # type: ignore[arg-type]

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(preset_data, f, indent=2)
    except OSError as e:
        QMessageBox.critical(main_window, "Save Error", f"Failed to save preset: {e}")
        return

    # Save thumbnail from current viewer content (optional)
    if main_window.viewer.photo is not None:
        pixmap = main_window.viewer.photo.pixmap()
        if pixmap and not pixmap.isNull():
            try:
                thumb = pixmap.scaled(
                    120, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation  # type: ignore[attr-defined]
                )
                thumb_path = os.path.join(main_window.presets_dir, f"{safe_name}.png")  # type: ignore[arg-type]
                thumb.save(thumb_path)
            except OSError:
                pass  # Thumbnail is optional; preset still works without it

    main_window.preset_panel.reload_presets()
    main_window.status_handler.set_message(f"Preset '{name}' saved", main_window.status_handler.MEDIUM_TIMEOUT)


def apply_preset(main_window: "MainWindow", preset_data: dict) -> None:
    """
    Apply a preset by setting all controller sliders and refreshing the display.
    Blocks controller signals while setting sliders so only one adjust_channel call fires per channel.
    """
    from .channels import adjust_channel  # pylint: disable=import-outside-toplevel

    channels = preset_data.get("channels", {})

    for i, ctrl in enumerate(main_window.controllers):
        ch_data = channels.get(_CHANNEL_NAMES[i], {})
        ctrl.blockSignals(True)
        for slider_name, value in ch_data.items():
            if slider_name in ctrl.sliders:
                slider = ctrl.sliders[slider_name]
                slider.setValue(value)
                if slider_name in ctrl.text_inputs:
                    ctrl.text_inputs[slider_name].setText(str(value))
        ctrl.blockSignals(False)

    for i in range(3):
        adjust_channel(main_window, i)

    name = preset_data.get("name", "preset")
    main_window.status_handler.set_message(f"Applied preset '{name}'", main_window.status_handler.MEDIUM_TIMEOUT)
