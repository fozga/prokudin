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
Unit tests for src.ui.handlers.autosave module.

Tests session persistence: saving channel paths, slider values, and crop state to JSON.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


from src.ui.handlers.autosave import (
    save_autosave,
    restore_autosave,
    clear_autosave,
    _autosave_path,
)


@pytest.fixture
def mock_main_window(tmp_path: Path) -> MagicMock:
    """Create a mock MainWindow with required attributes for autosave testing."""
    main_window = MagicMock()
    main_window.config_dir = str(tmp_path)

    # State: channel paths
    main_window.state = MagicMock()
    main_window.state.channel_paths = [None, None, None]

    # Controllers: sliders for each channel
    main_window.controllers = []
    for _ in range(3):
        ctrl = MagicMock()
        ctrl.sliders = {
            "brightness": MagicMock(value=MagicMock(return_value=10)),
            "contrast": MagicMock(value=MagicMock(return_value=20)),
            "intensity": MagicMock(value=MagicMock(return_value=95)),
        }
        ctrl.text_inputs = {
            "brightness": MagicMock(),
            "contrast": MagicMock(),
            "intensity": MagicMock(),
        }
        main_window.controllers.append(ctrl)

    # Viewer: crop rect
    main_window.viewer = MagicMock()

    # Service: aligned channels
    main_window.svc = MagicMock()
    main_window.svc.aligned = [None, None, None]

    # Status handler
    main_window.status_handler = MagicMock()
    main_window.status_handler.MEDIUM_TIMEOUT = "medium"

    return main_window


class TestAutosavePath:
    """
    Test Design Specification: _autosave_path()
    Module under test: src/ui/handlers/autosave.py

    Contract:
        Returns absolute path to autosave.json in the config directory.
        Takes MainWindow as argument. Returns string path.

    Equivalence partitions:
        EP1  Valid config_dir → returns joined path with autosave.json
        EP2  Different config_dir values → returns correct absolute path

    Boundary values:
        BV1  config_dir with trailing slash
        BV2  config_dir without trailing slash

    Exclusions:
        - File existence checks (just returns path string)
        - Path normalization

    Constraints:
        - Requires main_window.config_dir attribute
    """

    def test_returns_path_ending_with_autosave_json(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow with config_dir set
        When: _autosave_path is called
        Then: returns path string ending with 'autosave.json'."""
        # Act
        path = _autosave_path(mock_main_window)

        # Assert
        assert path.endswith("autosave.json")

    def test_uses_config_dir_from_main_window(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow with config_dir = '/tmp/foo'
        When: _autosave_path is called
        Then: returned path starts with that config_dir."""
        # Arrange
        mock_main_window.config_dir = "/tmp/foo"

        # Act
        path = _autosave_path(mock_main_window)

        # Assert
        assert path.startswith("/tmp/foo")


class TestSaveAutosave:
    """
    Test Design Specification: save_autosave()
    Module under test: src/ui/handlers/autosave.py

    Contract:
        Serializes current session state (channel paths, slider values, crop rect)
        to JSON file. Takes MainWindow reference. Returns None.
        Side effects: writes autosave.json with structure:
            {
              "version": 1,
              "channels": {
                "red": {"path": str or null, "brightness": int, "contrast": int, "intensity": int},
                "green": {...},
                "blue": {...}
              },
              "crop": null or {"x": int, "y": int, "width": int, "height": int}
            }
        Logs warning on write failure; silently continues.

    Equivalence partitions:
        EP1  No crop rect set → crop field is null
        EP2  Valid crop rect → crop field with x, y, width, height
        EP3  All channels with paths → all three channel paths stored
        EP4  Some channels with paths → paths stored as null for empty channels
        EP5  Slider values vary → correct values persisted per channel
        EP6  File write succeeds → JSON file created with valid JSON
        EP7  File write fails (OSError) → warning logged, function returns gracefully

    Boundary values:
        BV1  Empty/None crop rect (isValid returns False) → crop = null
        BV2  Valid crop rect → all fields populated
        BV3  slider value = 0 → stored as 0
        BV4  slider value = 100 → stored as 100

    Exclusions:
        - Slider value validation (assumes int from QSlider)
        - File permission verification (let OS exceptions bubble to logger)

    Constraints:
        - Requires mocking: main_window.controllers[i].sliders[name].value()
        - Requires mocking: main_window.viewer.get_saved_crop_rect()
        - MainWindow.state.channel_paths must be list of 3 slots
    """

    def test_writes_valid_json_file(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow with no crop set
        When: save_autosave is called
        Then: writes valid JSON to autosave.json."""
        # Arrange
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        assert autosave_file.exists()
        data = json.loads(autosave_file.read_text())
        assert isinstance(data, dict)
        assert "version" in data
        assert "channels" in data
        assert "crop" in data

    def test_saves_version_1(self, mock_main_window: MagicMock) -> None:
        """Given: save_autosave is called
        When: JSON is written
        Then: version field equals 1."""
        # Arrange
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = json.loads(autosave_file.read_text())
        assert data["version"] == 1

    def test_saves_all_three_channels(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow with three controllers
        When: save_autosave is called
        Then: channels dict contains 'red', 'green', 'blue' keys."""
        # Arrange
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = json.loads(autosave_file.read_text())
        assert "red" in data["channels"]
        assert "green" in data["channels"]
        assert "blue" in data["channels"]

    def test_saves_channel_paths(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow.state.channel_paths = ['/path/red.raw', None, '/path/blue.raw']
        When: save_autosave is called
        Then: JSON channels have correct path values."""
        # Arrange
        mock_main_window.state.channel_paths = ["/path/red.raw", None, "/path/blue.raw"]
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = json.loads(autosave_file.read_text())
        assert data["channels"]["red"]["path"] == "/path/red.raw"
        assert data["channels"]["green"]["path"] is None
        assert data["channels"]["blue"]["path"] == "/path/blue.raw"

    def test_saves_slider_values_for_each_channel(self, mock_main_window: MagicMock) -> None:
        """Given: Controllers with different slider values per channel
        When: save_autosave is called
        Then: brightness, contrast, intensity saved per channel."""
        # Arrange
        # Red: brightness=10, contrast=20, intensity=95 (from fixture)
        # Green: brightness=15, contrast=25, intensity=100
        mock_main_window.controllers[1].sliders["brightness"].value.return_value = 15
        mock_main_window.controllers[1].sliders["contrast"].value.return_value = 25
        mock_main_window.controllers[1].sliders["intensity"].value.return_value = 100

        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = json.loads(autosave_file.read_text())
        assert data["channels"]["red"]["brightness"] == 10
        assert data["channels"]["red"]["contrast"] == 20
        assert data["channels"]["red"]["intensity"] == 95
        assert data["channels"]["green"]["brightness"] == 15
        assert data["channels"]["green"]["contrast"] == 25
        assert data["channels"]["green"]["intensity"] == 100

    def test_saves_crop_rect_when_valid(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow.viewer has valid crop rect
        When: save_autosave is called
        Then: crop field contains x, y, width, height."""
        # Arrange
        mock_rect = MagicMock()
        mock_rect.isValid.return_value = True
        mock_rect.x.return_value = 10
        mock_rect.y.return_value = 20
        mock_rect.width.return_value = 100
        mock_rect.height.return_value = 80
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = json.loads(autosave_file.read_text())
        assert data["crop"] == {"x": 10, "y": 20, "width": 100, "height": 80}

    def test_saves_crop_null_when_invalid(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow.viewer.get_saved_crop_rect returns None
        When: save_autosave is called
        Then: crop field is null."""
        # Arrange
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = json.loads(autosave_file.read_text())
        assert data["crop"] is None

    def test_saves_crop_null_when_rect_not_valid(self, mock_main_window: MagicMock) -> None:
        """Given: MainWindow.viewer.get_saved_crop_rect returns a rect with isValid() = False
        When: save_autosave is called
        Then: crop field is null (non-None rect that fails isValid is treated as no crop)."""
        # Arrange
        mock_rect = MagicMock()
        mock_rect.isValid.return_value = False
        mock_main_window.viewer.get_saved_crop_rect.return_value = mock_rect

        # Act
        save_autosave(mock_main_window)

        # Assert
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = json.loads(autosave_file.read_text())
        assert data["crop"] is None

    def test_logs_warning_on_write_failure(self, mock_main_window: MagicMock) -> None:
        """Given: config_dir is not writable (raises OSError)
        When: save_autosave is called
        Then: OSError is caught and warning logged."""
        # Arrange
        mock_main_window.config_dir = "/nonexistent/path/that/cannot/exist"
        mock_main_window.viewer.get_saved_crop_rect.return_value = None

        # Act & Assert (should not raise)
        with patch("src.ui.handlers.autosave.logging.warning") as mock_warn:
            save_autosave(mock_main_window)
            mock_warn.assert_called_once()


class TestRestoreAutosave:
    """
    Test Design Specification: restore_autosave()
    Module under test: src/ui/handlers/autosave.py

    Contract:
        Loads session state from autosave.json and restores channel images,
        slider values, and crop rect. Takes MainWindow reference. Returns None.
        Side effects: loads channel images via load_channel_from_path(),
        updates slider values and text inputs, calls adjust_channel() for
        aligned channels, calls update_channel_preview() for all channels,
        sets crop rect on viewer, updates save button state, displays status message.
        Silently returns on missing/corrupt file.

    Equivalence partitions:
        EP1  File missing → returns without side effects
        EP2  File exists, valid JSON → restores all state
        EP3  Corrupt JSON (invalid syntax) → returns silently
        EP4  All three channels have valid paths → loads all three
        EP5  Some channels missing or invalid paths → loads valid, skips invalid
        EP6  Slider values present and valid → sets all sliders and text inputs
        EP7  Slider values missing or invalid type → skips gracefully
        EP8  Crop rect present and valid → sets crop on viewer, updates previews
        EP9  Crop rect missing or invalid (w=0 or h=0) → skipped
        EP10 Some channels aligned, some not → calls adjust_channel only for aligned

    Boundary values:
        BV1  crop width = 0 → skipped (invalid)
        BV2  crop height = 0 → skipped (invalid)
        BV3  crop width = 1, height = 1 → valid, accepted
        BV4  slider value = 0 → accepted
        BV5  slider value = 100 → accepted
        BV6  file path does not exist → load_channel_from_path not called

    Exclusions:
        - Actual file I/O (handled by save_autosave in integration)
        - Channel image loading details (mocked load_channel_from_path)
        - Signal blocking behavior (depends on Qt implementation)

    Constraints:
        - Requires mocking: load_channel_from_path(), adjust_channel(),
          update_channel_preview(), main_window.update_save_button_state()
        - MainWindow.svc.aligned must be list of 3 slots
        - File must be valid JSON (dict with 'channels', 'crop' keys)
    """

    def test_returns_if_file_missing(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json does not exist
        When: restore_autosave is called
        Then: returns without side effects."""
        # Arrange (no file created)

        # Act & Assert (should not raise)
        with patch("src.ui.handlers.autosave.load_channel_from_path") as mock_load:
            restore_autosave(mock_main_window)
            mock_load.assert_not_called()

    def test_returns_if_json_corrupt(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json contains invalid JSON
        When: restore_autosave is called
        Then: JSONDecodeError caught, returns silently."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        autosave_file.write_text("{ invalid json }")

        # Act & Assert (should not raise)
        with patch("src.ui.handlers.autosave.load_channel_from_path") as mock_load:
            restore_autosave(mock_main_window)
            mock_load.assert_not_called()

    def test_loads_channels_with_valid_paths(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json has valid channel paths that exist on disk
        When: restore_autosave is called
        Then: load_channel_from_path called for each valid path."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        test_file_1 = Path(mock_main_window.config_dir) / "test1.raw"
        test_file_2 = Path(mock_main_window.config_dir) / "test2.raw"
        test_file_1.touch()
        test_file_2.touch()

        data = {
            "version": 1,
            "channels": {
                "red": {"path": str(test_file_1), "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": str(test_file_2), "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path") as mock_load:
            restore_autosave(mock_main_window)

        # Assert
        assert mock_load.call_count == 2
        mock_load.assert_any_call(mock_main_window, 0, str(test_file_1))
        mock_load.assert_any_call(mock_main_window, 2, str(test_file_2))

    def test_skips_nonexistent_channel_paths(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json has paths that don't exist
        When: restore_autosave is called
        Then: load_channel_from_path not called for nonexistent paths."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": "/nonexistent/file.raw", "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": "/also/nonexistent.raw", "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path") as mock_load:
            restore_autosave(mock_main_window)

        # Assert
        mock_load.assert_not_called()

    def test_restores_slider_values(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json has slider values
        When: restore_autosave is called
        Then: setValue called for each slider with saved values."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 10, "contrast": 20, "intensity": 95},
                "green": {"path": None, "brightness": 15, "contrast": 25, "intensity": 100},
                "blue": {"path": None, "brightness": 5, "contrast": 10, "intensity": 90},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    restore_autosave(mock_main_window)

        # Assert
        # Red channel
        mock_main_window.controllers[0].sliders["brightness"].setValue.assert_called_with(10)
        mock_main_window.controllers[0].sliders["contrast"].setValue.assert_called_with(20)
        mock_main_window.controllers[0].sliders["intensity"].setValue.assert_called_with(95)

        # Green channel
        mock_main_window.controllers[1].sliders["brightness"].setValue.assert_called_with(15)
        mock_main_window.controllers[1].sliders["contrast"].setValue.assert_called_with(25)
        mock_main_window.controllers[1].sliders["intensity"].setValue.assert_called_with(100)

    def test_updates_text_inputs_with_slider_values(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json has slider values
        When: restore_autosave is called
        Then: setText called on text inputs to match slider values."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 10, "contrast": 20, "intensity": 95},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    restore_autosave(mock_main_window)

        # Assert
        mock_main_window.controllers[0].text_inputs["brightness"].setText.assert_called_with("10")
        mock_main_window.controllers[0].text_inputs["contrast"].setText.assert_called_with("20")
        mock_main_window.controllers[0].text_inputs["intensity"].setText.assert_called_with("95")

    def test_calls_adjust_channel_for_aligned_channels(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json exists and channels 0, 2 are aligned
        When: restore_autosave is called
        Then: adjust_channel called for channels 0 and 2."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        mock_main_window.svc.aligned = [np.zeros((100, 100)), None, np.zeros((100, 100))]
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel") as mock_adjust:
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    restore_autosave(mock_main_window)

        # Assert
        assert mock_adjust.call_count == 2
        mock_adjust.assert_any_call(mock_main_window, 0)
        mock_adjust.assert_any_call(mock_main_window, 2)

    def test_updates_previews_for_all_channels(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json exists
        When: restore_autosave is called
        Then: update_channel_preview called for all three channels."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview") as mock_update:
                    restore_autosave(mock_main_window)

        # Assert
        assert mock_update.call_count == 3

    def test_restores_valid_crop_rect(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json has valid crop rect
        When: restore_autosave is called
        Then: set_saved_crop_rect called with QRect of saved dimensions."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": {"x": 10, "y": 20, "width": 100, "height": 80},
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    with patch("src.ui.handlers.autosave.QRect") as mock_qrect:
                        restore_autosave(mock_main_window)

        # Assert
        mock_qrect.assert_called_once_with(10, 20, 100, 80)
        mock_main_window.viewer.set_saved_crop_rect.assert_called_once()

    def test_skips_invalid_crop_rect_with_zero_dimensions(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json has crop rect with width=0
        When: restore_autosave is called
        Then: set_saved_crop_rect not called."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": {"x": 10, "y": 20, "width": 0, "height": 80},
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    restore_autosave(mock_main_window)

        # Assert
        mock_main_window.viewer.set_saved_crop_rect.assert_not_called()

    def test_updates_save_button_state(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json exists
        When: restore_autosave is called
        Then: update_save_button_state called."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    restore_autosave(mock_main_window)

        # Assert
        mock_main_window.update_save_button_state.assert_called_once()

    def test_sets_status_message_on_restore(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json exists
        When: restore_autosave is called
        Then: status_handler.set_message called with 'Session restored'."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    restore_autosave(mock_main_window)

        # Assert
        mock_main_window.status_handler.set_message.assert_called_once()
        call_args = mock_main_window.status_handler.set_message.call_args[0]
        assert "Session restored" in call_args[0]

    def test_blocks_signals_during_slider_update(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json has slider values
        When: restore_autosave is called
        Then: blockSignals(True) called before updates, blockSignals(False) after."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 10, "contrast": 20, "intensity": 95},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file.write_text(json.dumps(data))

        # Act
        with patch("src.ui.handlers.autosave.load_channel_from_path"):
            with patch("src.ui.handlers.autosave.adjust_channel"):
                with patch("src.ui.handlers.autosave.update_channel_preview"):
                    restore_autosave(mock_main_window)

        # Assert
        assert mock_main_window.controllers[0].blockSignals.call_count >= 2


class TestClearAutosave:
    """
    Test Design Specification: clear_autosave()
    Module under test: src/ui/handlers.autosave.py

    Contract:
        Removes the autosave.json file from config directory.
        Takes MainWindow reference. Returns None.
        Silently continues if file doesn't exist or deletion fails.

    Equivalence partitions:
        EP1  File exists → removed successfully
        EP2  File missing → OSError caught, no error raised
        EP3  File not writable → OSError caught, no error raised

    Boundary values:
        BV1  File just created (should delete)
        BV2  File already missing (should not raise)

    Exclusions:
        - Permission verification
        - Actual file removal confirmation

    Constraints:
        - Requires os.path.exists() and os.remove() behavior
    """

    def test_removes_existing_autosave_file(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json exists in config_dir
        When: clear_autosave is called
        Then: file is deleted."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        autosave_file.write_text('{"version": 1}')
        assert autosave_file.exists()

        # Act
        clear_autosave(mock_main_window)

        # Assert
        assert not autosave_file.exists()

    def test_does_not_raise_if_file_missing(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json does not exist
        When: clear_autosave is called
        Then: no exception is raised."""
        # Arrange
        autosave_file = Path(mock_main_window.config_dir) / "autosave.json"
        assert not autosave_file.exists()

        # Act & Assert (should not raise)
        clear_autosave(mock_main_window)

    def test_silently_handles_permission_error(self, mock_main_window: MagicMock) -> None:
        """Given: autosave.json exists but cannot be removed (simulated)
        When: clear_autosave is called
        Then: OSError is caught and function returns gracefully."""
        # Arrange
        with patch("src.ui.handlers.autosave.os.remove") as mock_remove:
            mock_remove.side_effect = OSError("Permission denied")

        # Act & Assert (should not raise)
        clear_autosave(mock_main_window)
