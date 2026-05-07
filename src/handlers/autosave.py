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

"""Autosave handler - persists session state (channel paths, sliders, crop) between app runs."""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

from PyQt5.QtCore import QRect

from .channels import adjust_channel, load_channel_from_path, update_channel_preview

if TYPE_CHECKING:
    from ..main_window import MainWindow

_AUTOSAVE_FILENAME = "autosave.json"
_CHANNEL_NAMES = ["red", "green", "blue"]
_SLIDER_NAMES = ["brightness", "contrast", "intensity"]


def _autosave_path(main_window: "MainWindow") -> str:
    """Return the absolute path to the autosave JSON file."""
    return os.path.join(main_window.config_dir, _AUTOSAVE_FILENAME)  # type: ignore[arg-type]


def save_autosave(main_window: "MainWindow") -> None:
    """Save current channel paths, slider values, and crop rect to the autosave file."""
    channels: dict = {}
    for i, name in enumerate(_CHANNEL_NAMES):
        ctrl = main_window.controllers[i]
        channels[name] = {
            "path": main_window.channel_paths[i],
            **{s: ctrl.sliders[s].value() for s in _SLIDER_NAMES},
        }

    saved_crop = main_window.viewer.get_saved_crop_rect() if main_window.viewer else None
    crop = None
    if saved_crop and saved_crop.isValid():
        crop = {"x": saved_crop.x(), "y": saved_crop.y(), "width": saved_crop.width(), "height": saved_crop.height()}

    data = {"version": 1, "channels": channels, "crop": crop}

    try:
        with open(_autosave_path(main_window), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        logging.warning("Autosave write failed: %s", e)


def restore_autosave(main_window: "MainWindow") -> None:  # pylint: disable=too-many-locals,too-many-branches
    """Load session state from the autosave file and restore channel images, sliders, and crop."""
    path = _autosave_path(main_window)
    if not os.path.exists(path):
        return

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    for i, name in enumerate(_CHANNEL_NAMES):
        ch_data = data.get("channels", {}).get(name, {})
        filepath = ch_data.get("path")
        if isinstance(filepath, str) and os.path.exists(filepath):
            load_channel_from_path(main_window, i, filepath)

    for i, name in enumerate(_CHANNEL_NAMES):
        ch_data = data.get("channels", {}).get(name, {})
        ctrl = main_window.controllers[i]
        ctrl.blockSignals(True)
        for slider_name in _SLIDER_NAMES:
            value = ch_data.get(slider_name)
            if isinstance(value, int) and slider_name in ctrl.sliders:
                ctrl.sliders[slider_name].setValue(value)
                if slider_name in ctrl.text_inputs:
                    ctrl.text_inputs[slider_name].setText(str(value))
        ctrl.blockSignals(False)

    for i in range(3):
        if main_window.aligned[i] is not None:
            adjust_channel(main_window, i)
        update_channel_preview(main_window, i)

    crop_data = data.get("crop")
    if isinstance(crop_data, dict):
        x = crop_data.get("x", 0)
        y = crop_data.get("y", 0)
        w = crop_data.get("width", 0)
        h = crop_data.get("height", 0)
        if all(isinstance(v, (int, float)) for v in [x, y, w, h]) and w > 0 and h > 0:
            crop_rect = QRect(int(x), int(y), int(w), int(h))
            main_window.viewer.set_saved_crop_rect(crop_rect)
            for i in range(3):
                update_channel_preview(main_window, i)

    main_window.update_save_button_state()
    main_window.status_handler.set_message("Session restored", main_window.status_handler.MEDIUM_TIMEOUT)


def clear_autosave(main_window: "MainWindow") -> None:
    """Remove the autosave file (called on app reset)."""
    try:
        os.remove(_autosave_path(main_window))
    except OSError:
        pass
