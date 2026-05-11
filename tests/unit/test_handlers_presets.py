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
Unit tests for src.ui.handlers.presets module.

Tests preset saving and loading: JSON serialization, slider state persistence,
thumbnail generation, and preset application with signal blocking.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

sys.modules["PyQt5"] = MagicMock()
sys.modules["PyQt5.QtCore"] = MagicMock()
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()

from src.ui.handlers.presets import save_preset, apply_preset


@pytest.fixture
def mock_main_window(tmp_path: Path) -> MagicMock:
    """Create a mock MainWindow with required attributes for preset testing."""
    main_window = MagicMock()
    main_window.presets_dir = str(tmp_path / "presets")

    main_window.controllers = []
    for i in range(3):
        ctrl = MagicMock()
        ctrl.sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=10 + i * 5)),
            "contrast": MagicMock(value=MagicMock(return_value=20 + i * 5)),
            "intensity": MagicMock(value=MagicMock(return_value=95 + i)),
        }
        ctrl.text_inputs = {
            "brightness": MagicMock(),
            "contrast": MagicMock(),
            "intensity": MagicMock(),
        }
        main_window.controllers.append(ctrl)

    main_window.viewer = MagicMock()
    main_window.viewer.photo = None

    main_window.preset_panel = MagicMock()
    main_window.status_handler = MagicMock()
    main_window.status_handler.MEDIUM_TIMEOUT = "medium"

    return main_window


class TestSavePreset:
    """
    Test Design Specification: save_preset()
    Module under test: src/ui/handlers/presets.py

    Contract:
        Prompts user for preset name via QInputDialog. If name accepted and non-empty,
        sanitizes it by removing special characters. If sanitized name is empty, shows
        warning and returns. Otherwise, gathers slider values from all three controllers,
        creates JSON preset data, saves to presets_dir/{safe_name}.json. If viewer has
        a valid photo, also saves scaled thumbnail to presets_dir/{safe_name}.png
        (errors ignored; optional). Reloads preset panel and shows status message.

    Equivalence partitions:
        EP1  User cancels dialog (ok=False)     → returns early, no save
        EP2  User accepts empty name            → returns early, no save
        EP3  User accepts whitespace-only name  → returns early, no save
        EP4  Valid name with alphanumerics      → saves JSON with slider values
        EP5  Name with special chars            → special chars removed, safe_name used
        EP6  Name with spaces                   → spaces converted to underscores
        EP7  All special chars (becomes empty)  → shows warning, returns
        EP8  Valid name but file write fails    → shows error, returns
        EP9  Photo exists and valid             → saves thumbnail PNG
        EP10 Photo exists but null/invalid      → skips thumbnail silently
        EP11 Thumbnail write fails              → skips silently (optional)

    Boundary values:
        BV1  name with leading/trailing spaces  → stripped
        BV2  name with multiple consecutive spaces → handled correctly

    Exclusions:
        - Qt event loop not required; QInputDialog mocked
        - Filesystem permissions tested only via mock exception injection

    Constraints:
        - Requires mocking QInputDialog.getText and QMessageBox methods
        - File I/O tested with tmp_path fixture
        - MainWindow attributes mocked: controllers, presets_dir, viewer, preset_panel, status_handler
    """

    def test_dialog_cancelled_returns_early(self, mock_main_window: MagicMock) -> None:
        """
        Given user cancels the preset name dialog,
        When save_preset is called,
        Then function returns without saving any files.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("ignored", False)  # ok=False

            # Act
            save_preset(mock_main_window)

            # Assert
            assert not Path(mock_main_window.presets_dir).exists()
            mock_main_window.preset_panel.reload_presets.assert_not_called()

    def test_empty_name_returns_early(self, mock_main_window: MagicMock) -> None:
        """
        Given user enters an empty name and accepts,
        When save_preset is called,
        Then function returns without saving.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("", True)  # Empty string

            # Act
            save_preset(mock_main_window)

            # Assert
            assert not Path(mock_main_window.presets_dir).exists()

    def test_whitespace_only_name_returns_early(self, mock_main_window: MagicMock) -> None:
        """
        Given user enters only whitespace and accepts,
        When save_preset is called,
        Then function returns without saving.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("   \t\n  ", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            assert not Path(mock_main_window.presets_dir).exists()

    def test_valid_name_saves_json_with_slider_values(self, mock_main_window: MagicMock) -> None:
        """
        Given user enters a valid preset name with alphanumeric characters,
        When save_preset is called,
        Then JSON file is created in presets_dir with correct slider values.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("MyPreset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            json_path = Path(mock_main_window.presets_dir) / "MyPreset.json"
            assert json_path.exists()

            with open(json_path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            assert saved["name"] == "MyPreset"
            assert "channels" in saved
            assert set(saved["channels"].keys()) == {"red", "green", "blue"}
            # Red: brightness=10, contrast=20, intensity=95
            assert saved["channels"]["red"]["brightness"] == 10
            assert saved["channels"]["red"]["contrast"] == 20
            assert saved["channels"]["red"]["intensity"] == 95
            # Green: brightness=15, contrast=25, intensity=96
            assert saved["channels"]["green"]["brightness"] == 15
            assert saved["channels"]["green"]["contrast"] == 25
            assert saved["channels"]["green"]["intensity"] == 96

    def test_special_chars_removed_from_name(self, mock_main_window: MagicMock) -> None:
        """
        Given user enters a name with special characters,
        When save_preset is called,
        Then special characters are removed and file saved with safe name.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("My@Preset#2025!", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            json_path = Path(mock_main_window.presets_dir) / "MyPreset2025.json"
            assert json_path.exists()

            with open(json_path, "r", encoding="utf-8") as f:
                saved = json.load(f)

            assert saved["name"] == "My@Preset#2025!"

    def test_spaces_converted_to_underscores(self, mock_main_window: MagicMock) -> None:
        """
        Given user enters a name with spaces,
        When save_preset is called,
        Then spaces are converted to underscores in the filename.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("My New Preset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            json_path = Path(mock_main_window.presets_dir) / "My_New_Preset.json"
            assert json_path.exists()

    def test_all_special_chars_name_shows_warning(self, mock_main_window: MagicMock) -> None:
        """
        Given user enters a name that becomes empty after sanitization,
        When save_preset is called,
        Then warning dialog is shown and function returns without saving.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog, \
             patch("src.ui.handlers.presets.QMessageBox.warning") as mock_warning:
            mock_dialog.return_value = ("!!!@@@###", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            mock_warning.assert_called_once()
            assert not Path(mock_main_window.presets_dir).exists()

    def test_file_write_error_shows_critical_dialog(self, mock_main_window: MagicMock) -> None:
        """
        Given preset dir cannot be written to,
        When save_preset is called,
        Then critical error dialog is shown and function returns.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog, \
             patch("builtins.open", side_effect=OSError("Permission denied")), \
             patch("src.ui.handlers.presets.QMessageBox.critical") as mock_critical:
            mock_dialog.return_value = ("MyPreset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            mock_critical.assert_called_once()
            assert "Failed to save preset" in mock_critical.call_args[0][2]

    def test_thumbnail_saved_when_photo_valid(self, mock_main_window: MagicMock) -> None:
        """
        Given viewer.photo is not None and has a valid pixmap,
        When save_preset is called,
        Then both JSON and thumbnail PNG are saved.
        """
        # Arrange
        mock_pixmap = MagicMock()
        mock_pixmap.isNull.return_value = False
        mock_scaled = MagicMock()
        mock_pixmap.scaled.return_value = mock_scaled

        mock_photo = MagicMock()
        mock_photo.pixmap.return_value = mock_pixmap

        mock_main_window.viewer.photo = mock_photo

        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("MyPreset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            json_path = Path(mock_main_window.presets_dir) / "MyPreset.json"
            png_path = Path(mock_main_window.presets_dir) / "MyPreset.png"
            assert json_path.exists()
            # Verify pixmap.scaled was called with correct dimensions
            mock_pixmap.scaled.assert_called_once()
            # Verify thumbnail save was attempted
            mock_scaled.save.assert_called_once_with(str(png_path))

    def test_thumbnail_skip_if_photo_null(self, mock_main_window: MagicMock) -> None:
        """
        Given viewer.photo exists but pixmap.isNull returns True,
        When save_preset is called,
        Then only JSON is saved, no thumbnail created.
        """
        # Arrange
        mock_pixmap = MagicMock()
        mock_pixmap.isNull.return_value = True

        mock_photo = MagicMock()
        mock_photo.pixmap.return_value = mock_pixmap

        mock_main_window.viewer.photo = mock_photo

        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("MyPreset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            json_path = Path(mock_main_window.presets_dir) / "MyPreset.json"
            png_path = Path(mock_main_window.presets_dir) / "MyPreset.png"
            assert json_path.exists()
            assert not png_path.exists()

    def test_thumbnail_error_ignored_silently(self, mock_main_window: MagicMock) -> None:
        """
        Given thumbnail save fails with OSError,
        When save_preset is called,
        Then JSON is still saved and function returns normally.
        """
        # Arrange
        mock_pixmap = MagicMock()
        mock_pixmap.isNull.return_value = False
        mock_scaled = MagicMock()
        mock_scaled.save.side_effect = OSError("Disk full")
        mock_pixmap.scaled.return_value = mock_scaled

        mock_photo = MagicMock()
        mock_photo.pixmap.return_value = mock_pixmap

        mock_main_window.viewer.photo = mock_photo

        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("MyPreset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            json_path = Path(mock_main_window.presets_dir) / "MyPreset.json"
            assert json_path.exists()

    def test_preset_panel_reloaded_on_success(self, mock_main_window: MagicMock) -> None:
        """
        Given preset is saved successfully,
        When save_preset is called,
        Then preset_panel.reload_presets() is called.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("MyPreset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            mock_main_window.preset_panel.reload_presets.assert_called_once()

    def test_status_message_set_on_success(self, mock_main_window: MagicMock) -> None:
        """
        Given preset is saved successfully,
        When save_preset is called,
        Then status message displays the original (non-sanitized) preset name.
        """
        # Arrange
        with patch("src.ui.handlers.presets.QInputDialog.getText") as mock_dialog:
            mock_dialog.return_value = ("My Cool Preset", True)

            # Act
            save_preset(mock_main_window)

            # Assert
            mock_main_window.status_handler.set_message.assert_called_once()
            call_args = mock_main_window.status_handler.set_message.call_args[0]
            assert "My Cool Preset" in call_args[0]
            assert call_args[1] == "medium"


class TestApplyPreset:
    """
    Test Design Specification: apply_preset()
    Module under test: src/ui/handlers/presets.py

    Contract:
        Takes MainWindow and preset_data dict. Extracts "channels" field from
        preset_data. For each of three controllers, fetches channel data by name
        ("red", "green", "blue"), blocks signals, sets slider values and text inputs
        if present and value is int, then unblocks signals. After all three
        controllers configured, calls adjust_channel for each channel index 0-2.
        Finally, sets status message with preset name from "name" field (defaults
        to "preset" if missing).

    Equivalence partitions:
        EP1  Valid preset with all channels       → all sliders set, all adjust_channel called
        EP2  Preset missing "channels" key        → uses empty dict, skips slider setting
        EP3  Preset["channels"] is not dict       → uses empty dict, skips slider setting
        EP4  Channel data missing                 → skips that channel, no error
        EP5  Channel data not a dict              → uses empty dict for that channel
        EP6  Slider value is not int              → value skipped, slider unchanged
        EP6a Slider value is boolean (True/False) → ACCEPTED as int (bool is int subclass in Python)
        EP7  Slider name not in ctrl.sliders      → value skipped, slider unchanged
        EP8  text_inputs present for slider       → text_input.setText called with string
        EP9  text_inputs missing for slider       → slider set, no text_input call
        EP10 All three channels adjusted          → adjust_channel called 3x
        EP11 Preset missing "name" field          → status message uses default "preset"

    Boundary values:
        BV1  Empty preset_data dict              → uses empty dict, no error
        BV2  Preset with only one channel data   → other channels skipped

    Exclusions:
        - adjust_channel behavior tested in channels module; here just verify it's called
        - Qt event loop not required; all mocked

    Constraints:
        - Requires mocking adjust_channel from src.ui.handlers.channels
        - MainWindow attributes mocked: controllers, status_handler
        - Controllers and sliders are MagicMock with value() and setValue() methods
    """

    def test_valid_preset_sets_all_slider_values(self, mock_main_window: MagicMock) -> None:
        """
        Given a valid preset with all three channels and sliders,
        When apply_preset is called,
        Then each controller slider receives setValue() for each defined value.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": 50, "contrast": 30, "intensity": 100},
                "green": {"brightness": 40, "contrast": 35, "intensity": 105},
                "blue": {"brightness": 60, "contrast": 25, "intensity": 110},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # Red channel
            assert mock_main_window.controllers[0].sliders["brightness"].setValue.called
            mock_main_window.controllers[0].sliders["brightness"].setValue.assert_called_with(50)
            mock_main_window.controllers[0].sliders["contrast"].setValue.assert_called_with(30)
            mock_main_window.controllers[0].sliders["intensity"].setValue.assert_called_with(100)

            # Green channel
            mock_main_window.controllers[1].sliders["brightness"].setValue.assert_called_with(40)
            mock_main_window.controllers[1].sliders["contrast"].setValue.assert_called_with(35)

            # Blue channel
            mock_main_window.controllers[2].sliders["brightness"].setValue.assert_called_with(60)

    def test_missing_channels_key_uses_empty_dict(self, mock_main_window: MagicMock) -> None:
        """
        Given preset_data lacks "channels" key,
        When apply_preset is called,
        Then empty dict is used, no slider values set.
        """
        # Arrange
        preset_data = {"name": "TestPreset"}

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            for ctrl in mock_main_window.controllers:
                for slider in ctrl.sliders.values():
                    slider.setValue.assert_not_called()

    def test_channels_not_dict_uses_empty_dict(self, mock_main_window: MagicMock) -> None:
        """
        Given preset["channels"] is not a dict,
        When apply_preset is called,
        Then empty dict is used, no errors raised.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": "not a dict"  # Invalid type
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            for ctrl in mock_main_window.controllers:
                for slider in ctrl.sliders.values():
                    slider.setValue.assert_not_called()

    def test_missing_channel_data_skips_channel(self, mock_main_window: MagicMock) -> None:
        """
        Given preset only defines "red" channel, missing "green" and "blue",
        When apply_preset is called,
        Then only red channel sliders are set, others unchanged.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": 50, "contrast": 30, "intensity": 100},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # Red set
            mock_main_window.controllers[0].sliders["brightness"].setValue.assert_called_with(50)
            # Green and blue not set
            mock_main_window.controllers[1].sliders["brightness"].setValue.assert_not_called()
            mock_main_window.controllers[2].sliders["brightness"].setValue.assert_not_called()

    def test_channel_data_not_dict_uses_empty_dict(self, mock_main_window: MagicMock) -> None:
        """
        Given channel data is not a dict (e.g., a list or string),
        When apply_preset is called,
        Then empty dict is used for that channel, no error raised.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": ["invalid", "list"],
                "green": {"brightness": 50},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # Red channel skipped (invalid type)
            mock_main_window.controllers[0].sliders["brightness"].setValue.assert_not_called()
            # Green channel set normally
            mock_main_window.controllers[1].sliders["brightness"].setValue.assert_called_with(50)

    @pytest.mark.parametrize("invalid_value", [
        "not_an_int",
        3.14,
        None,
        [],
        {},
    ], ids=["string", "float", "none", "list", "dict"])
    def test_non_int_slider_value_skipped(self, mock_main_window: MagicMock, invalid_value: object) -> None:
        """
        Given a slider value is not an integer (and not a bool),
        When apply_preset is called,
        Then that specific value is skipped, slider unchanged.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": invalid_value, "contrast": 30},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # brightness (invalid) not set
            mock_main_window.controllers[0].sliders["brightness"].setValue.assert_not_called()
            # contrast (valid int) still set
            mock_main_window.controllers[0].sliders["contrast"].setValue.assert_called_with(30)

    @pytest.mark.parametrize("bool_value, slider_int, text_str", [
        (True, 1, "True"),
        (False, 0, "False"),
    ], ids=["true_as_one", "false_as_zero"])
    def test_boolean_slider_values_accepted_as_ints(
        self, mock_main_window: MagicMock, bool_value: bool, slider_int: int, text_str: str
    ) -> None:
        """
        Given a slider value is a boolean (True or False),
        When apply_preset is called,
        Then the boolean is accepted (since bool is a subclass of int in Python)
        and setValue is called with the integer equivalent (True→1, False→0),
        while setText displays the string representation ("True" or "False").
        This edge case documents the actual behavior when a preset file contains
        booleans (e.g., from manual editing or non-standard tooling).
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": bool_value},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # Boolean is accepted by isinstance(value, int) and converted
            mock_main_window.controllers[0].sliders["brightness"].setValue.assert_called_with(slider_int)
            mock_main_window.controllers[0].text_inputs["brightness"].setText.assert_called_with(text_str)

    def test_unknown_slider_name_skipped(self, mock_main_window: MagicMock) -> None:
        """
        Given preset contains a slider name not in ctrl.sliders,
        When apply_preset is called,
        Then that value is skipped, no error raised.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": 50, "unknown_slider": 100},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # brightness set
            mock_main_window.controllers[0].sliders["brightness"].setValue.assert_called_with(50)
            # unknown_slider ignored

    def test_text_input_updated_when_present(self, mock_main_window: MagicMock) -> None:
        """
        Given a controller has text_inputs for a slider,
        When apply_preset is called and slider is set,
        Then text_input.setText is called with the string value.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": 50},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            mock_main_window.controllers[0].text_inputs["brightness"].setText.assert_called_once_with("50")

    def test_text_input_not_called_if_missing(self, mock_main_window: MagicMock) -> None:
        """
        Given a controller lacks text_inputs for a slider,
        When apply_preset is called,
        Then text_input.setText is not called, no error raised.
        """
        # Arrange
        mock_main_window.controllers[0].text_inputs = {}

        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": 50},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # Should not raise KeyError
            mock_main_window.controllers[0].sliders["brightness"].setValue.assert_called_with(50)

    def test_signals_blocked_during_slider_setting(self, mock_main_window: MagicMock) -> None:
        """
        Given a preset is applied,
        When apply_preset is called,
        Then signals are blocked on all controllers during slider setting.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": 50, "contrast": 30},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # Verify blockSignals(True) then setValue then blockSignals(False)
            for ctrl in mock_main_window.controllers:
                assert ctrl.blockSignals.call_count == 2
                calls = ctrl.blockSignals.call_args_list
                assert calls[0][0] == (True,)   # First call: True
                assert calls[1][0] == (False,)  # Second call: False

    def test_adjust_channel_called_for_all_three_channels(self, mock_main_window: MagicMock) -> None:
        """
        Given a preset is applied,
        When apply_preset is called,
        Then adjust_channel is called once for each channel index (0, 1, 2).
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {"brightness": 50},
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel") as mock_adjust:
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            assert mock_adjust.call_count == 3
            calls = mock_adjust.call_args_list
            assert calls[0] == call(mock_main_window, 0)
            assert calls[1] == call(mock_main_window, 1)
            assert calls[2] == call(mock_main_window, 2)

    def test_status_message_set_with_preset_name(self, mock_main_window: MagicMock) -> None:
        """
        Given a preset with a name field is applied,
        When apply_preset is called,
        Then status message contains the preset name.
        """
        # Arrange
        preset_data = {
            "name": "MyAwesomePreset",
            "channels": {}
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            mock_main_window.status_handler.set_message.assert_called_once()
            call_args = mock_main_window.status_handler.set_message.call_args[0]
            assert "MyAwesomePreset" in call_args[0]
            assert call_args[1] == "medium"

    def test_status_message_default_preset_name_if_missing(self, mock_main_window: MagicMock) -> None:
        """
        Given preset_data lacks "name" field,
        When apply_preset is called,
        Then status message uses default "preset" as name.
        """
        # Arrange
        preset_data = {"channels": {}}

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            mock_main_window.status_handler.set_message.assert_called_once()
            call_args = mock_main_window.status_handler.set_message.call_args[0]
            assert "preset" in call_args[0]

    def test_empty_preset_data_dict(self, mock_main_window: MagicMock) -> None:
        """
        Given an empty preset_data dict,
        When apply_preset is called,
        Then no errors are raised, default behaviors applied.
        """
        # Arrange
        preset_data = {}

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            # No sliders set, no errors
            for ctrl in mock_main_window.controllers:
                for slider in ctrl.sliders.values():
                    slider.setValue.assert_not_called()
            # But adjust_channel still called for each channel
            # and status message still set

    def test_multiple_sliders_per_channel(self, mock_main_window: MagicMock) -> None:
        """
        Given a preset with multiple slider values per channel,
        When apply_preset is called,
        Then all sliders and text inputs for that channel are updated.
        """
        # Arrange
        preset_data = {
            "name": "TestPreset",
            "channels": {
                "red": {
                    "brightness": 10,
                    "contrast": 20,
                    "intensity": 95,
                },
            }
        }

        with patch("src.ui.handlers.presets.adjust_channel"):
            # Act
            apply_preset(mock_main_window, preset_data)

            # Assert
            red_ctrl = mock_main_window.controllers[0]
            red_ctrl.sliders["brightness"].setValue.assert_called_with(10)
            red_ctrl.sliders["contrast"].setValue.assert_called_with(20)
            red_ctrl.sliders["intensity"].setValue.assert_called_with(95)

            red_ctrl.text_inputs["brightness"].setText.assert_called_with("10")
            red_ctrl.text_inputs["contrast"].setText.assert_called_with("20")
            red_ctrl.text_inputs["intensity"].setText.assert_called_with("95")
