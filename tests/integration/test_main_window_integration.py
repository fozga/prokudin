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

"""Integration tests for src/ui/main_window.MainWindow."""

import json
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox
from pytestqt.plugin import QtBot

from src.ui.main_window import MainWindow

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

# 10×10 uniform-zero RGB array.  ORB finds no keypoints on a uniform image so
# alignment silently falls back to identity copies, avoiding AlignmentError.
_SYNTHETIC_RGB: np.ndarray = np.zeros((10, 10, 3), dtype=np.uint8)
_SYNTHETIC_GRAY: np.ndarray = np.zeros((10, 10), dtype=np.uint8)


def _make_fresh_window(
    config_dir: Path,
    presets_dir: Path,
    *,
    suppress_restore: bool = True,
) -> MainWindow:
    """Return a fully real MainWindow isolated to *config_dir*/*presets_dir*.

    When *suppress_restore* is True the autosave restore is patched out so the
    window opens with a blank slate.  Pass False to exercise the real
    restore path (used by ``TestAutosaveRoundTrip`` EP2 and EP3).
    """
    ctx = [
        patch("src.ui.main_window.get_presets_dir", return_value=str(presets_dir)),
        patch("src.ui.main_window.get_config_dir", return_value=str(config_dir)),
    ]
    if suppress_restore:
        ctx.append(patch("src.ui.main_window.restore_autosave"))

    with ExitStack() as stack:
        for p in ctx:
            stack.enter_context(p)
        return MainWindow()


# ---------------------------------------------------------------------------
# TestSignalWiring
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSignalWiring:
    """
    Test Design Specification: MainWindow signal wiring (integration)
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        ``MainWindow.init_ui`` wires Qt signals to real handler functions via
        ``connect()``.  These tests verify that the connections are live end-to-
        end: a real user gesture (slider move, button click, preset emission)
        propagates through the real handler chain and produces observable state
        changes without any handler mocks.

    Infrastructure:
        - Requires the module-scoped ``real_window`` fixture from
          ``tests/integration/conftest.py`` (no handler mocks; only
          ``restore_autosave`` suppressed).
        - Requires QT_QPA_PLATFORM=offscreen.
        - ``qtbot`` used for ``waitSignal`` in EP1 and widget-cleanup in EP2/EP3.

    What is tested:
        EP1  Slider value_changed → adjust_channel → update_main_display
             propagates to a non-null viewer pixmap.
        EP2  Load button click → load_channel → svc.original_images[0] set
             (file dialog stubbed via patch).
        EP3  preset_panel.preset_selected emitted → apply_preset → controller
             sliders updated to preset values.

    What is NOT tested:
        - Visual appearance or rendered pixel values.
        - Signal disconnect behaviour.
        - Concurrent or threaded signal delivery.

    Mocking strategy:
        - EP1: no mocks; svc state seeded directly.
        - EP2: ``src.ui.handlers.channels.load_raw_image`` stubbed to return a
          synthetic array (bypasses the rawpy file-dialog path only).
        - EP3: no mocks; signal emitted directly on the real PresetPanel.

    Constraints:
        - ``real_window`` is module-scoped; state from these tests may carry
          into later test classes in the same module.  Tests are written so
          only additive state changes occur (no destructive resets).
    """

    def test_slider_value_changed_propagates_through_real_handler_to_display(
        self, real_window: MainWindow, qtbot: QtBot
    ) -> None:
        """
        Given channel 0 aligned and processed images seeded on svc and
        single-channel display mode active,
        When the brightness slider on controller 0 is incremented by one step,
        Then the value_changed signal is caught by the real adjust_channel
        handler and the viewer photo pixmap becomes non-null.
        """
        # Arrange
        real_window.svc.aligned[0] = _SYNTHETIC_GRAY.copy()
        real_window.svc.processed[0] = _SYNTHETIC_GRAY.copy()
        real_window.state.show_combined = False
        real_window.state.current_channel = 0

        brightness_slider = real_window.controllers[0].sliders["brightness"]
        new_value = brightness_slider.value() + 1

        # Act + Assert (waitSignal blocks until the emission completes)
        with qtbot.waitSignal(real_window.controllers[0].value_changed, timeout=1000):
            brightness_slider.setValue(new_value)

        # Assert: the full chain ran and the viewer now holds a real pixmap
        assert real_window.viewer.photo is not None
        assert not real_window.viewer.photo.pixmap().isNull()

    def test_load_button_click_wired_to_load_channel_sets_original_image(
        self, real_window: MainWindow, qtbot: QtBot
    ) -> None:
        """
        Given a stubbed file dialog that returns a synthetic RGB array for
        channel 0,
        When the channel 0 load button is clicked,
        Then svc.original_images[0] is set to a non-None value via the real
        load_channel signal wiring.
        """
        # Arrange
        with patch(
            "src.ui.handlers.channels.load_raw_image",
            return_value=(_SYNTHETIC_RGB.copy(), "/fake/ch0.arw", None),
        ):
            # Act
            real_window.controllers[0].btn_load.click()

        # Assert
        assert real_window.svc.original_images[0] is not None

    def test_preset_selected_signal_wired_to_apply_preset_updates_sliders(
        self, real_window: MainWindow, qtbot: QtBot
    ) -> None:
        """
        Given valid preset data specifying brightness=30 for the red channel,
        When preset_panel emits the preset_selected signal with that data,
        Then controller 0 brightness slider is updated to 30 via the real
        apply_preset signal wiring.
        """
        # Arrange
        preset_data = {
            "name": "integration-test-preset",
            "channels": {
                "red": {"brightness": 30, "contrast": 5, "intensity": 80},
                "green": {"brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"brightness": 0, "contrast": 0, "intensity": 100},
            },
        }

        # Act
        real_window.preset_panel.preset_selected.emit(preset_data)

        # Assert
        assert real_window.controllers[0].sliders["brightness"].value() == 30


# ---------------------------------------------------------------------------
# TestAutosaveRoundTrip
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAutosaveRoundTrip:
    """
    Test Design Specification: save_autosave / restore_autosave round-trip
    Module under test: src/ui/main_window.py  (via src/ui/handlers/autosave.py)

    Widget base class: QMainWindow

    Contract:
        ``save_autosave`` serialises channel paths and slider values to a JSON
        file under ``config_dir``.  ``restore_autosave`` (called during
        ``MainWindow.__init__``) reads the file and reconstructs slider state
        on a fresh instance.  ``reset_to_defaults`` removes the autosave file
        so subsequent instances start blank.

    Infrastructure:
        - Each test creates its own function-scoped ``MainWindow`` via
          ``_make_fresh_window`` to isolate filesystem I/O.
        - Requires ``qapp`` (session-scoped) and ``tmp_path`` (function-scoped)
          from pytest built-ins / conftest.
        - Requires QT_QPA_PLATFORM=offscreen.

    What is tested:
        EP1  save_autosave writes channel_paths[0] and brightness=42 to disk.
        EP2  A fresh MainWindow (restore NOT suppressed) reads the autosave and
             restores controller 0 brightness slider to 42.
        EP3  reset_to_defaults() removes the autosave file; a subsequent fresh
             instance starts with the default brightness (0).

    What is NOT tested:
        - Crop-rect round-trip (covered by separate crop-handler unit tests).
        - Corruption or partial-write recovery.
        - Concurrent access to the autosave file.

    Mocking strategy:
        - ``get_presets_dir`` and ``get_config_dir`` redirected to ``tmp_path``
          sub-dirs for full filesystem isolation.
        - ``restore_autosave`` suppressed during window construction in EP1
          (EP2 and EP3 intentionally do NOT suppress it).

    Constraints:
        - Image paths are set to non-existent fake strings so ``restore_autosave``
          skips the rawpy loading step while still restoring slider values.
        - ``QMessageBox.question`` is patched during ``window.close()`` to
          prevent the "save session?" dialog from blocking in headless mode.
    """

    def test_save_autosave_writes_channel_path_and_brightness_to_disk(
        self, qapp: QApplication, tmp_path: Path
    ) -> None:
        """
        Given a window with channel 0 path set to a fake path and brightness
        slider at 42,
        When save_autosave is called,
        Then the autosave JSON file exists on disk and contains the channel path
        and brightness=42 for the red channel.
        """
        # Arrange
        from src.ui.handlers.autosave import save_autosave

        config_dir = tmp_path / "config"
        presets_dir = tmp_path / "presets"
        config_dir.mkdir()
        presets_dir.mkdir()

        window = _make_fresh_window(config_dir, presets_dir, suppress_restore=True)
        window.state.channel_paths[0] = "/fake/red_channel.arw"
        window.controllers[0].sliders["brightness"].blockSignals(True)
        window.controllers[0].sliders["brightness"].setValue(42)
        window.controllers[0].sliders["brightness"].blockSignals(False)

        # Act
        save_autosave(window)

        # Assert
        autosave_file = config_dir / "autosave.json"
        assert autosave_file.exists()
        data = json.loads(autosave_file.read_text(encoding="utf-8"))
        assert data["channels"]["red"]["path"] == "/fake/red_channel.arw"
        assert data["channels"]["red"]["brightness"] == 42

        with patch("PyQt5.QtWidgets.QMessageBox.question", return_value=int(QMessageBox.No)):
            window.close()

    def test_restore_autosave_reconstructs_brightness_on_fresh_instance(
        self, qapp: QApplication, tmp_path: Path
    ) -> None:
        """
        Given an autosave JSON on disk with brightness=42 for the red channel,
        When a second MainWindow is constructed without suppressing
        restore_autosave,
        Then controller 0 brightness slider value equals 42.
        """
        # Arrange: write autosave JSON with known brightness value
        config_dir = tmp_path / "config"
        presets_dir = tmp_path / "presets"
        config_dir.mkdir()
        presets_dir.mkdir()

        autosave_data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 42, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        (config_dir / "autosave.json").write_text(
            json.dumps(autosave_data), encoding="utf-8"
        )

        # Act: construct window with real restore_autosave (NOT suppressed)
        window2 = _make_fresh_window(config_dir, presets_dir, suppress_restore=False)

        # Assert
        assert window2.controllers[0].sliders["brightness"].value() == 42

        with patch("PyQt5.QtWidgets.QMessageBox.question", return_value=int(QMessageBox.No)):
            window2.close()

    def test_reset_to_defaults_deletes_autosave_and_fresh_instance_starts_blank(
        self, qapp: QApplication, tmp_path: Path
    ) -> None:
        """
        Given a window that has an autosave JSON on disk with brightness=42,
        When reset_to_defaults is called on that window,
        Then the autosave file is deleted and a subsequently constructed
        MainWindow starts with the default brightness value of 0.
        """
        # Arrange: create window with a non-default autosave already on disk
        config_dir = tmp_path / "config"
        presets_dir = tmp_path / "presets"
        config_dir.mkdir()
        presets_dir.mkdir()

        autosave_data = {
            "version": 1,
            "channels": {
                "red": {"path": None, "brightness": 42, "contrast": 0, "intensity": 100},
                "green": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
                "blue": {"path": None, "brightness": 0, "contrast": 0, "intensity": 100},
            },
            "crop": None,
        }
        autosave_file = config_dir / "autosave.json"
        autosave_file.write_text(json.dumps(autosave_data), encoding="utf-8")

        # Window 1 restores the autosave on construction (brightness becomes 42)
        window1 = _make_fresh_window(config_dir, presets_dir, suppress_restore=False)

        # Act
        window1.reset_to_defaults()

        # Assert: autosave file removed
        assert not autosave_file.exists()

        # Assert: a fresh instance starts with default brightness (0)
        window3 = _make_fresh_window(config_dir, presets_dir, suppress_restore=False)
        assert window3.controllers[0].sliders["brightness"].value() == 0

        with patch("PyQt5.QtWidgets.QMessageBox.question", return_value=int(QMessageBox.No)):
            window1.close()
            window3.close()


# ---------------------------------------------------------------------------
# TestLoadDisplayPipeline
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestLoadDisplayPipeline:
    """
    Test Design Specification: load→align→process→display pipeline (integration)
    Module under test: src/ui/main_window.py

    Widget base class: QMainWindow

    Contract:
        Calling ``load_channel_from_path`` for all three channels triggers the
        full chain: rawpy loading → ``svc.load_channel_from_array`` → ORB
        alignment (falls back to identity for uniform images) → brightness/
        contrast processing → display update → save-button state update.
        After all channels are loaded the application is ready for cropping.

        Infrastructure:
                - Requires the module-scoped ``real_window`` fixture from
                    ``tests/integration/conftest.py``.
                - Requires QT_QPA_PLATFORM=offscreen.
                - ``src.ui.handlers.channels.load_raw_image_from_path`` is patched
                    to return a synthetic 10×10 RGB array, bypassing rawpy so real ARW
                    files are not required.

    What is tested:
        EP1  All three channels loaded → svc.has_processed_channels() is True
             and viewer photo pixmap is non-null.
        EP2  After all channels loaded → save_btn is enabled
             (update_save_button_state propagated via real service).
        EP3  After all channels loaded → entering crop mode sets state.crop_rect
             to a valid QRect with non-zero dimensions.

    What is NOT tested:
        - Actual image pixel correctness after processing.
        - Save-to-file pipeline (covered by image_saving unit tests).
        - Crop application and result (covered by crop handler tests).

    Mocking strategy:
        - ``src.ui.handlers.channels.load_raw_image_from_path`` patched
          to return ``(_SYNTHETIC_RGB, None)`` so ``load_channel_from_path``
          uses the stubbed loader instead of rawpy.

    Constraints:
        - Each test loads all three channels independently; no ordering
          dependency exists between EP1/EP2/EP3.
        - ``real_window.state.show_combined`` may be False from earlier
          TestSignalWiring tests; ``show_single_channel_image`` is used in
          that case, which still sets a non-null pixmap once a channel is loaded.
    """

    @staticmethod
    def _load_all_channels_with_stubbed_loader(real_window: MainWindow) -> None:
        """Load all three channels through the real path-based handler using a stubbed raw loader."""
        from src.ui.handlers.channels import load_channel_from_path

        with patch(
            "src.ui.handlers.channels.load_raw_image_from_path",
            return_value=(_SYNTHETIC_RGB.copy(), None),
        ):
            load_channel_from_path(real_window, 0, "/fake/red.arw")
            load_channel_from_path(real_window, 1, "/fake/green.arw")
            load_channel_from_path(real_window, 2, "/fake/blue.arw")

    def test_load_all_channels_results_in_processed_channels_and_non_null_pixmap(
        self, real_window: MainWindow, qtbot: QtBot
    ) -> None:
        """
        Given load_raw_image_from_path patched to return a 10×10 synthetic
        RGB array,
        When load_channel_from_path is called for all three channels,
        Then svc.has_processed_channels() returns True and viewer photo
        pixmap is non-null.
        """
        # Arrange

        # Act: load all three channels through the real handler chain
        self._load_all_channels_with_stubbed_loader(real_window)

        # Assert
        assert real_window.svc.has_processed_channels()
        assert real_window.viewer.photo is not None
        assert not real_window.viewer.photo.pixmap().isNull()

    def test_save_button_is_enabled_after_all_channels_loaded(
        self, real_window: MainWindow
    ) -> None:
        """
        Given all three channels have been loaded into svc (EP1 ran first),
        When update_save_button_state was propagated through the real service,
        Then save_btn.isEnabled() is True.
        """
        # Arrange
        self._load_all_channels_with_stubbed_loader(real_window)

        # Act      (state was set by real handler chain during Arrange)
        # Assert
        assert real_window.save_btn.isEnabled()

    def test_enter_crop_mode_sets_valid_crop_rect_after_channels_loaded(
        self, real_window: MainWindow
    ) -> None:
        """
        Given all three channels are loaded and the crop button is enabled,
        When toggle_crop_mode is called,
        Then state.crop_rect is a valid QRect with non-zero width and height.
        """
        # Arrange
        self._load_all_channels_with_stubbed_loader(real_window)

        # Ensure we start outside crop mode
        if real_window.state.crop_mode:
            real_window.cancel_crop()

        # Act
        real_window.toggle_crop_mode()

        # Assert
        assert real_window.state.crop_rect is not None
        assert real_window.state.crop_rect.isValid()
        assert real_window.state.crop_rect.width() > 0
        assert real_window.state.crop_rect.height() > 0

        # Cleanup: exit crop mode so the module fixture teardown is clean
        real_window.cancel_crop()
