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

"""Widget tests for src/ui/widgets/channel_controller.py."""

from unittest.mock import MagicMock

import numpy as np
import pytest
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QWidget
from pytestqt.plugin import QtBot

from src.ui.widgets.channel_controller import ChannelController


@pytest.mark.widget
class TestChannelControllerInit:
    """
    Test Design Specification: ChannelController — Initialization
    Module under test: src/ui/widgets/channel_controller.py

    Widget base class: QGroupBox

    Contract:
        ChannelController is a QGroupBox that encapsulates three ResetSliders
        (brightness, contrast, intensity), three QLineEdit text inputs, a load
        QPushButton, and a QLabel preview. On construction it reads default values
        from DefaultState.get_slider_defaults() and populates sliders/text inputs
        accordingly. The widget title is set to "<channel_name>.capitalize() channel".
        processed_image starts as None.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - No service or file IO mocking needed for init tests.

    What is tested:
        - Widget title matches the capitalised channel name.
        - channel_name and color attributes are stored correctly.
        - processed_image is None after construction.
        - sliders dict contains exactly brightness, contrast, intensity keys.
        - text_inputs dict contains exactly brightness, contrast, intensity keys.
        - Each slider is initialised with the correct default value from DefaultState.
        - Each text input reflects the matching default value string.
        - Slider ranges are correct (brightness/contrast: [-100,100], intensity: [0,100]).
        - btn_load label contains the correct abbreviated channel name.

    What is NOT tested:
        - Visual appearance, font sizes, colours.
        - Layout geometry or pixel positions.

    Equivalence partitions:
        EP1  channel_name = "red"   → abbreviation "IR", title "Red channel"
        EP2  channel_name = "green" → abbreviation "VIS", title "Green channel"
        EP3  channel_name = "blue"  → abbreviation "UV", title "Blue channel"
        EP4  channel_name = "xyz"   → abbreviation "xyz" (first 3 chars fallback)

    Boundary values:
        BV1  brightness default = 0  (mid-range)
        BV2  contrast default = 0    (mid-range)
        BV3  intensity default = 100 (maximum of [0, 100] range)

    Mocking strategy:
        None — ChannelController has no external service dependencies at init.

    Constraints:
        - No widget.show() required for init assertions.
    """

    def test_title_is_capitalised_channel_name(self, qtbot: QtBot) -> None:
        """
        Given channel_name="red",
        When ChannelController is constructed,
        Then the group box title is "Red channel".
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert widget.title() == "Red channel"

    def test_channel_name_stored(self, qtbot: QtBot) -> None:
        """
        Given channel_name="green",
        When ChannelController is constructed,
        Then widget.channel_name is "green".
        """
        # Arrange / Act
        widget = ChannelController("green", Qt.green)
        qtbot.addWidget(widget)
        # Assert
        assert widget.channel_name == "green"

    def test_color_stored(self, qtbot: QtBot) -> None:
        """
        Given color=Qt.blue,
        When ChannelController is constructed,
        Then widget.color is Qt.blue.
        """
        # Arrange / Act
        widget = ChannelController("blue", Qt.blue)
        qtbot.addWidget(widget)
        # Assert
        assert widget.color == Qt.blue

    def test_processed_image_is_none(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed ChannelController,
        When no image has been loaded,
        Then processed_image is None.
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert widget.processed_image is None

    def test_sliders_keys(self, qtbot: QtBot) -> None:
        """
        Given a constructed ChannelController,
        When inspecting the sliders dict,
        Then it contains exactly brightness, contrast, and intensity.
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert set(widget.sliders.keys()) == {"brightness", "contrast", "intensity"}

    def test_text_inputs_keys(self, qtbot: QtBot) -> None:
        """
        Given a constructed ChannelController,
        When inspecting the text_inputs dict,
        Then it contains exactly brightness, contrast, and intensity.
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert set(widget.text_inputs.keys()) == {"brightness", "contrast", "intensity"}

    @pytest.mark.parametrize(
        "name, expected_default",
        [
            ("brightness", 0),    # BV1: mid-range default
            ("contrast", 0),      # BV2: mid-range default
            ("intensity", 100),   # BV3: at maximum of [0,100]
        ],
        ids=["brightness", "contrast", "intensity"],
    )
    def test_slider_default_value(self, qtbot: QtBot, name: str, expected_default: int) -> None:
        """
        Given a constructed ChannelController,
        When reading the initial slider value for <name>,
        Then it equals the DefaultState default.
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert widget.sliders[name].value() == expected_default

    @pytest.mark.parametrize(
        "name, expected_default",
        [
            ("brightness", "0"),    # BV1
            ("contrast", "0"),      # BV2
            ("intensity", "100"),   # BV3
        ],
        ids=["brightness", "contrast", "intensity"],
    )
    def test_text_input_default_value(self, qtbot: QtBot, name: str, expected_default: str) -> None:
        """
        Given a constructed ChannelController,
        When reading the initial text_input text for <name>,
        Then it equals the string representation of the DefaultState default.
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert widget.text_inputs[name].text() == expected_default

    @pytest.mark.parametrize(
        "name, expected_min, expected_max",
        [
            ("brightness", -100, 100),  # EP: brightness range
            ("contrast", -100, 100),    # EP: contrast range
            ("intensity", 0, 100),      # EP: intensity range (no negatives)
        ],
        ids=["brightness", "contrast", "intensity"],
    )
    def test_slider_range(self, qtbot: QtBot, name: str, expected_min: int, expected_max: int) -> None:
        """
        Given a constructed ChannelController,
        When reading slider minimum and maximum for <name>,
        Then they match the configured range.
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert widget.sliders[name].minimum() == expected_min
        assert widget.sliders[name].maximum() == expected_max

    @pytest.mark.parametrize(
        "channel_name, expected_abbrev",
        [
            ("red", "IR"),    # EP1
            ("green", "VIS"), # EP2
            ("blue", "UV"),   # EP3
            ("xyz", "xyz"),   # EP4: fallback to first 3 chars
        ],
        ids=["red", "green", "blue", "unknown"],
    )
    def test_btn_load_label_abbreviation(self, qtbot: QtBot, channel_name: str, expected_abbrev: str) -> None:
        """
        Given channel_name,
        When ChannelController is constructed,
        Then btn_load text contains the expected abbreviation.
        """
        # Arrange / Act
        widget = ChannelController(channel_name, Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert expected_abbrev in widget.btn_load.text()


@pytest.mark.widget
class TestChannelControllerSliderTextSync:
    """
    Test Design Specification: ChannelController — Slider/Text Synchronisation
    Module under test: src/ui/widgets/channel_controller.py

    Widget base class: QGroupBox

    Contract:
        When a slider value changes, _update_text_from_slider updates the linked
        QLineEdit and emits value_changed. When a QLineEdit editingFinished signal
        fires, _update_slider_from_text parses the text, clamps it to [min, max],
        updates both slider and text field, and emits value_changed. Invalid text
        (non-numeric, empty) restores the previous slider value without emitting.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.

    What is tested:
        - Changing slider value updates the linked text input.
        - Changing slider value emits value_changed signal.
        - Valid text input within range updates the slider.
        - Valid text at minimum boundary sets slider to minimum.
        - Valid text at maximum boundary sets slider to maximum.
        - Text below minimum is clamped to minimum.
        - Text above maximum is clamped to maximum.
        - Non-numeric text restores the previous slider value.
        - Empty text restores the previous slider value.
        - Text update emits value_changed signal.

    What is NOT tested:
        - Visual cursor position in text field.
        - Focus / blur events.

    Equivalence partitions:
        EP1  text is valid integer in range → slider updated, text shows clamped value
        EP2  text below minimum            → slider clamped to minimum
        EP3  text above maximum            → slider clamped to maximum
        EP4  text equals minimum           → slider set to minimum exactly
        EP5  text equals maximum           → slider set to maximum exactly
        EP6  non-numeric text              → slider unchanged, text restored
        EP7  empty text                    → slider unchanged, text restored

    Boundary values:
        BV1  brightness text = "-100" → slider = -100 (minimum)
        BV2  brightness text = "100"  → slider = 100  (maximum)
        BV3  brightness text = "-101" → slider clamped to -100
        BV4  brightness text = "101"  → slider clamped to 100

    Mocking strategy:
        None — testing internal synchronisation logic only.

    Constraints:
        - No widget.show() required.
    """

    def test_slider_change_updates_text(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with brightness slider at default 0,
        When the brightness slider value is set to 50,
        Then the brightness text input shows "50".
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Act
        widget.sliders["brightness"].setValue(50)
        # Assert
        assert widget.text_inputs["brightness"].text() == "50"

    def test_slider_change_emits_value_changed(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController at default state,
        When the brightness slider value changes,
        Then the value_changed signal is emitted.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Act + Assert
        with qtbot.waitSignal(widget.value_changed, timeout=1000):
            widget.sliders["brightness"].setValue(10)

    def test_valid_text_updates_slider(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with brightness slider at default 0,
        When the user enters "42" in the brightness text input and fires editingFinished,
        Then the brightness slider value is 42.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        text_input = widget.text_inputs["brightness"]
        # Act
        text_input.setText("42")
        text_input.editingFinished.emit()
        # Assert
        assert widget.sliders["brightness"].value() == 42

    def test_valid_text_emits_value_changed(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController at default state,
        When the user enters "42" in the brightness text input and fires editingFinished,
        Then the value_changed signal is emitted.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        text_input = widget.text_inputs["brightness"]
        text_input.setText("42")
        # Act + Assert
        with qtbot.waitSignal(widget.value_changed, timeout=1000):
            text_input.editingFinished.emit()

    @pytest.mark.parametrize(
        "text, expected_value",
        [
            ("50", 50),      # EP1: valid within range
            ("-999", -100),  # EP2+BV3: below minimum, clamped to -100
            ("999", 100),    # EP3+BV4: above maximum, clamped to 100
            ("-100", -100),  # EP4+BV1: exactly at minimum
            ("100", 100),    # EP5+BV2: exactly at maximum
        ],
        ids=["valid", "below_min", "above_max", "at_min", "at_max"],
    )
    def test_text_input_clamping_on_brightness(self, qtbot: QtBot, text: str, expected_value: int) -> None:
        """
        Given a ChannelController with brightness range [-100, 100],
        When the user enters <text> and fires editingFinished,
        Then the slider is set to <expected_value>.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        text_input = widget.text_inputs["brightness"]
        # Act
        text_input.setText(text)
        text_input.editingFinished.emit()
        # Assert
        assert widget.sliders["brightness"].value() == expected_value

    def test_text_input_shows_clamped_value_below_min(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with brightness slider at 0,
        When the user enters "-999" and fires editingFinished,
        Then the text input displays "-100" (the clamped minimum).
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        text_input = widget.text_inputs["brightness"]
        # Act
        text_input.setText("-999")
        text_input.editingFinished.emit()
        # Assert
        assert text_input.text() == "-100"

    def test_text_input_shows_clamped_value_above_max(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with brightness slider at 0,
        When the user enters "999" and fires editingFinished,
        Then the text input displays "100" (the clamped maximum).
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        text_input = widget.text_inputs["brightness"]
        # Act
        text_input.setText("999")
        text_input.editingFinished.emit()
        # Assert
        assert text_input.text() == "100"

    def test_non_numeric_text_restores_previous_value(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with brightness slider at 30,
        When the user enters "abc" and fires editingFinished,
        Then the slider stays at 30 and the text field is restored to "30".
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(30)
        text_input = widget.text_inputs["brightness"]
        # Act
        text_input.setText("abc")
        text_input.editingFinished.emit()
        # Assert
        assert widget.sliders["brightness"].value() == 30
        assert text_input.text() == "30"

    def test_empty_text_restores_previous_value(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with brightness slider at 30,
        When the user clears the text field and fires editingFinished,
        Then the slider stays at 30 and the text field is restored to "30".
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(30)
        text_input = widget.text_inputs["brightness"]
        # Act
        text_input.setText("")
        text_input.editingFinished.emit()
        # Assert
        assert widget.sliders["brightness"].value() == 30
        assert text_input.text() == "30"

    def test_intensity_slider_minimum_is_zero(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with intensity range [0, 100],
        When the user enters "-50" in the intensity text input and fires editingFinished,
        Then the slider is clamped to 0 and the text input shows "0".
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        text_input = widget.text_inputs["intensity"]
        # Act
        text_input.setText("-50")
        text_input.editingFinished.emit()
        # Assert
        assert widget.sliders["intensity"].value() == 0
        assert text_input.text() == "0"


@pytest.mark.widget
class TestChannelControllerReset:
    """
    Test Design Specification: ChannelController — Reset Behaviour
    Module under test: src/ui/widgets/channel_controller.py

    Widget base class: QGroupBox

    Contract:
        _reset_slider_to_default(name) resets a single slider and its text input
        to the DefaultState default and emits value_changed. reset_all_sliders()
        resets all three sliders and emits value_changed once after all resets.
        Double-clicking a ResetSlider invokes _reset_slider_to_default via the
        doubleClicked signal.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.

    What is tested:
        - _reset_slider_to_default resets the named slider to its default.
        - _reset_slider_to_default updates the linked text input.
        - _reset_slider_to_default emits value_changed.
        - reset_all_sliders restores all three sliders to defaults.
        - reset_all_sliders emits value_changed.
        - Slider doubleClicked signal triggers _reset_slider_to_default.

    What is NOT tested:
        - Pixel-level double-click event routing (requires visible widget and OS
          event loop; tested via signal instead).

    Equivalence partitions:
        EP1  slider currently at non-default value → reset brings it back to default
        EP2  slider already at default             → reset is a no-op (value unchanged)

    Boundary values:
        BV1  brightness reset = 0   (default)
        BV2  intensity reset = 100  (default at maximum)

    Mocking strategy:
        None.

    Constraints:
        - No widget.show() required.
    """

    def test_reset_slider_to_default_restores_value(self, qtbot: QtBot) -> None:
        """
        Given brightness slider moved to 75,
        When _reset_slider_to_default("brightness") is called,
        Then the brightness slider value is 0 (the default).
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(75)
        # Act
        widget._reset_slider_to_default("brightness")
        # Assert
        assert widget.sliders["brightness"].value() == 0  # BV1

    def test_reset_slider_to_default_updates_text(self, qtbot: QtBot) -> None:
        """
        Given brightness slider moved to 75,
        When _reset_slider_to_default("brightness") is called,
        Then the brightness text input shows "0".
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(75)
        # Act
        widget._reset_slider_to_default("brightness")
        # Assert
        assert widget.text_inputs["brightness"].text() == "0"

    def test_reset_slider_to_default_emits_value_changed(self, qtbot: QtBot) -> None:
        """
        Given brightness slider at 75,
        When _reset_slider_to_default("brightness") is called,
        Then the value_changed signal is emitted.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(75)
        # Act + Assert
        with qtbot.waitSignal(widget.value_changed, timeout=1000):
            widget._reset_slider_to_default("brightness")

    def test_reset_intensity_default_is_100(self, qtbot: QtBot) -> None:
        """
        Given intensity slider moved to 50,
        When _reset_slider_to_default("intensity") is called,
        Then the intensity slider value is 100 (the default). (BV2)
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["intensity"].setValue(50)
        # Act
        widget._reset_slider_to_default("intensity")
        # Assert
        assert widget.sliders["intensity"].value() == 100  # BV2

    def test_reset_slider_already_at_default_is_noop(self, qtbot: QtBot) -> None:
        """
        Given brightness slider already at 0 (default),
        When _reset_slider_to_default("brightness") is called,
        Then the brightness slider value is still 0. (EP2)
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Act
        widget._reset_slider_to_default("brightness")
        # Assert
        assert widget.sliders["brightness"].value() == 0

    def test_reset_all_sliders_restores_brightness(self, qtbot: QtBot) -> None:
        """
        Given brightness slider moved to 80,
        When reset_all_sliders() is called,
        Then the brightness slider value is 0.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(80)
        # Act
        widget.reset_all_sliders()
        # Assert
        assert widget.sliders["brightness"].value() == 0

    def test_reset_all_sliders_restores_contrast(self, qtbot: QtBot) -> None:
        """
        Given contrast slider moved to -60,
        When reset_all_sliders() is called,
        Then the contrast slider value is 0.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["contrast"].setValue(-60)
        # Act
        widget.reset_all_sliders()
        # Assert
        assert widget.sliders["contrast"].value() == 0

    def test_reset_all_sliders_restores_intensity(self, qtbot: QtBot) -> None:
        """
        Given intensity slider moved to 20,
        When reset_all_sliders() is called,
        Then the intensity slider value is 100.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["intensity"].setValue(20)
        # Act
        widget.reset_all_sliders()
        # Assert
        assert widget.sliders["intensity"].value() == 100

    def test_reset_all_sliders_emits_value_changed(self, qtbot: QtBot) -> None:
        """
        Given all sliders at non-default values,
        When reset_all_sliders() is called,
        Then the value_changed signal is emitted.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(50)
        # Act + Assert
        with qtbot.waitSignal(widget.value_changed, timeout=1000):
            widget.reset_all_sliders()

    def test_double_clicked_signal_resets_slider(self, qtbot: QtBot) -> None:
        """
        Given brightness slider moved to 60,
        When the slider's doubleClicked signal is emitted,
        Then the brightness slider resets to 0.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(60)
        # Act
        widget.sliders["brightness"].doubleClicked.emit()
        # Assert
        assert widget.sliders["brightness"].value() == 0

    def test_reset_slider_to_default_with_invalid_name_is_noop(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController at default state,
        When _reset_slider_to_default("nonexistent") is called with a name not in sliders,
        Then no exception is raised and all sliders remain at their defaults.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Act
        widget._reset_slider_to_default("nonexistent")
        # Assert — no crash; existing sliders unchanged
        assert widget.sliders["brightness"].value() == 0

    def test_reset_all_sliders_skips_missing_default(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with the "brightness" key removed from default_values
        (simulating a defensive guard that is normally unreachable),
        When reset_all_sliders() is called,
        Then no exception is raised, contrast is reset, and brightness slider is unchanged.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.sliders["brightness"].setValue(50)
        widget.sliders["contrast"].setValue(-50)
        del widget.default_values["brightness"]
        # Act
        widget.reset_all_sliders()
        # Assert — contrast is reset; brightness slider left unchanged (no key to reset to)
        assert widget.sliders["contrast"].value() == 0
        assert widget.sliders["brightness"].value() == 50


@pytest.mark.widget
class TestChannelControllerPreview:
    """
    Test Design Specification: ChannelController — Image Preview
    Module under test: src/ui/widgets/channel_controller.py

    Widget base class: QGroupBox

    Contract:
        clear_image() sets processed_image to None and restores the placeholder
        preview (a 120×160 gray numpy array converted to QPixmap). update_preview()
        renders processed_image if set, or falls back to the placeholder. The
        preview label always holds a QPixmap after construction.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - numpy arrays used for processed_image; no file IO.

    What is tested:
        - After construction the preview_label has a pixmap (placeholder set).
        - clear_image() sets processed_image to None.
        - clear_image() updates the preview_label pixmap (placeholder reinstated).
        - update_preview() with processed_image=None shows placeholder (no crash).
        - update_preview() with a valid grayscale numpy array updates the label.
        - _set_preview() with a grayscale array does not raise.
        - _set_preview() with a wide image (width-constrained aspect) does not raise.
        - _set_preview() with a tall image (height-constrained aspect) does not raise.

    What is NOT tested:
        - Pixel-level pixmap content — test that the label has a non-null pixmap
          only, not the rendered image data.
        - Crop rect path (requires a parent widget hierarchy with a viewer — not
          tested here because it is integration-level behaviour).
        - Animations, visual transitions.

    Equivalence partitions:
        EP1  processed_image is None    → placeholder rendered (no crash)
        EP2  processed_image is a valid grayscale array → image rendered (no crash)

    Boundary values:
        BV1  image shape = (120, 160) → exactly matches preview label size
        BV2  wide image (320, 40)     → width-constrained resize path
        BV3  tall image (40, 320)     → height-constrained resize path

    Mocking strategy:
        None — _set_preview uses cv2 and QImage internally; only absence of crash
        and non-null pixmap are asserted.

    Constraints:
        - No widget.show() required.

    Exclusions:
        - Parent-traversal crop path in _set_preview() (lines 300-313) is covered
          by TestChannelControllerPreviewCrop using a mock parent QWidget.
    """

    def test_preview_label_has_pixmap_after_init(self, qtbot: QtBot) -> None:
        """
        Given a freshly constructed ChannelController,
        When inspecting preview_label,
        Then it has a non-null pixmap (placeholder was set).
        """
        # Arrange / Act
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_clear_image_sets_processed_image_to_none(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with processed_image set to a numpy array,
        When clear_image() is called,
        Then processed_image is None.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.processed_image = np.zeros((120, 160), dtype=np.uint8)
        # Act
        widget.clear_image()
        # Assert
        assert widget.processed_image is None

    def test_clear_image_restores_pixmap(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with a processed image,
        When clear_image() is called,
        Then the preview_label still has a non-null pixmap (placeholder).
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.processed_image = np.zeros((120, 160), dtype=np.uint8)
        # Act
        widget.clear_image()
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_update_preview_with_none_image_does_not_crash(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with processed_image=None,
        When update_preview() is called,
        Then no exception is raised and preview_label has a pixmap.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        assert widget.processed_image is None
        # Act
        widget.update_preview()
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_update_preview_with_valid_array_does_not_crash(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with a valid grayscale numpy array as processed_image,
        When update_preview() is called,
        Then no exception is raised and preview_label has a pixmap.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        widget.processed_image = np.full((120, 160), 128, dtype=np.uint8)
        # Act
        widget.update_preview()
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_set_preview_with_standard_image(self, qtbot: QtBot) -> None:
        """
        Given a grayscale image of exactly (120, 160),
        When _set_preview() is called,
        Then the preview_label has a non-null pixmap. (BV1)
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        img = np.full((120, 160), 200, dtype=np.uint8)
        # Act
        widget._set_preview(img)
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_set_preview_with_wide_image(self, qtbot: QtBot) -> None:
        """
        Given a wide grayscale image (40 rows × 320 cols) that triggers width-constrained
        resize path (aspect > 160/120),
        When _set_preview() is called,
        Then the preview_label has a non-null pixmap. (BV2)
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        img = np.full((40, 320), 100, dtype=np.uint8)  # aspect = 8.0 > 160/120 ≈ 1.33
        # Act
        widget._set_preview(img)
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_set_preview_with_tall_image(self, qtbot: QtBot) -> None:
        """
        Given a tall grayscale image (320 rows × 40 cols) that triggers height-constrained
        resize path (aspect <= 160/120),
        When _set_preview() is called,
        Then the preview_label has a non-null pixmap. (BV3)
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        img = np.full((320, 40), 100, dtype=np.uint8)  # aspect = 0.125 < 1.33
        # Act
        widget._set_preview(img)
        # Assert
        assert not widget.preview_label.pixmap().isNull()


@pytest.mark.widget
class TestChannelControllerPreviewClick:
    """
    Test Design Specification: ChannelController — Preview Label Click Signal
    Module under test: src/ui/widgets/channel_controller.py

    Widget base class: QGroupBox

    Contract:
        When the preview_label is clicked, the preview_clicked signal is emitted.
        The event filter installed on the preview label translates mouse press
        events into signal emissions.

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.

    What is tested:
        - preview_clicked signal is defined.
        - Clicking the preview label emits preview_clicked exactly once.

    What is NOT tested:
        - Visual appearance of the preview label.
        - Mouse event coordinates or cursor positioning.

    Equivalence partitions:
        EP1  preview label is clicked → preview_clicked signal emitted

    Boundary values:
        None (binary condition — clicked or not).

    Mocking strategy:
        None — testing signal emission only.

    Constraints:
        - Widget need not be shown() to emit signals.
        - qtbot.mouseClick requires the widget to be registered with qtbot.addWidget.
    """

    def test_preview_clicked_emitted_on_label_click(self, qtbot: QtBot) -> None:
        """
        Given a ChannelController with a preview label,
        When the preview label is clicked via qtbot.mouseClick,
        Then the preview_clicked signal is emitted.
        """
        # Arrange
        widget = ChannelController("red", Qt.red)
        qtbot.addWidget(widget)
        # Act + Assert
        with qtbot.waitSignal(widget.preview_clicked, timeout=1000):
            qtbot.mouseClick(widget.preview_label, Qt.LeftButton)

    """
    Test Design Specification: ChannelController — _set_preview crop path
    Module under test: src/ui/widgets/channel_controller.py

    Widget base class: QGroupBox

    Contract:
        _set_preview() traverses the parent hierarchy looking for a widget with a
        viewer attribute that has get_saved_crop_rect(). When found, it optionally
        applies a crop rectangle to the preview before resizing. The traversal stops
        with break after the first matching ancestor (or reaching None).

        Branches:
        A. No parent (self.parent() is None)         → while loop never entered (covered elsewhere)
        B. Parent present but no viewer attr         → parent = parent.parent(); loop re-evaluates
        C. Parent has viewer, get_saved_crop_rect returns None → crop skipped, break
        D. Parent has viewer, valid crop_rect, crop_mode=True  → crop skipped, break
        E. Parent has viewer, valid crop_rect, crop_mode=False, valid intersection → crop applied, break
        F. Parent has viewer, valid crop_rect, crop_mode=False, empty intersection  → crop skipped, break

    Infrastructure:
        - Requires qtbot fixture (QApplication, widget cleanup).
        - Requires QT_QPA_PLATFORM=offscreen.
        - parent QWidget created in-process; viewer replaced with MagicMock.

    What is tested:
        - Branch B: parent without viewer traverses to next ancestor (None) — no crash.
        - Branch C: saved_crop_rect=None → no crop, preview rendered without error.
        - Branch D: saved_crop_rect valid but crop_mode=True → no crop, preview rendered.
        - Branch E: valid crop rect within image → crop applied, preview rendered.
        - Branch F: crop rect entirely outside image (empty intersection) → no crop, no crash.

    What is NOT tested:
        - Pixel-level content of the cropped pixmap — only non-null pixmap is asserted.

    Equivalence partitions:
        EP1  No viewer on parent          → traverse and exit
        EP2  Crop rect = None             → skip crop
        EP3  crop_mode = True             → skip crop
        EP4  Valid intersecting crop rect → apply crop
        EP5  Non-intersecting crop rect   → skip crop (invalid intersection)

    Boundary values:
        BV1  crop_rect fully inside image (10, 10, 100, 80) → valid intersection
        BV2  crop_rect fully outside image (200, 200, 50, 50) → empty intersection

    Mocking strategy:
        - viewer attribute set directly on a plain QWidget parent.
        - viewer.get_saved_crop_rect replaced with MagicMock returning QRect or None.

    Constraints:
        - ChannelController constructed with parent= so self.parent() is non-None.
        - No widget.show() required.
    """

    def test_parent_without_viewer_traverses_to_none(self, qtbot: QtBot) -> None:
        """
        Given a parent QWidget with no viewer attribute,
        When _set_preview() is called,
        Then the loop traverses to parent.parent() (None) and exits without error. (EP1)
        """
        # Arrange
        parent = QWidget()
        qtbot.addWidget(parent)
        widget = ChannelController("red", Qt.red, parent=parent)
        # no viewer attr on parent → hits line 313: parent = parent.parent()
        img = np.full((60, 80), 128, dtype=np.uint8)
        # Act
        widget._set_preview(img)
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_crop_rect_none_skips_crop(self, qtbot: QtBot) -> None:
        """
        Given a parent with a viewer whose get_saved_crop_rect returns None,
        When _set_preview() is called,
        Then no crop is applied and the preview is rendered without error. (EP2, Branch C)
        """
        # Arrange
        parent = QWidget()
        qtbot.addWidget(parent)
        mock_viewer = MagicMock()
        mock_viewer.get_saved_crop_rect.return_value = None
        parent.viewer = mock_viewer  # type: ignore[attr-defined]
        parent.crop_mode = False  # type: ignore[attr-defined]
        widget = ChannelController("red", Qt.red, parent=parent)
        img = np.full((120, 160), 100, dtype=np.uint8)
        # Act
        widget._set_preview(img)
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_crop_mode_true_skips_crop(self, qtbot: QtBot) -> None:
        """
        Given a parent with a viewer returning a valid QRect but crop_mode=True,
        When _set_preview() is called,
        Then the crop is skipped and the preview is rendered without error. (EP3, Branch D)

        The explicit crop_mode=True assignment (not relying on getattr default) ensures
        this test exercises Branch D. The assertion that get_saved_crop_rect was called
        confirms the code reached the crop-decision point and chose to skip.
        """
        # Arrange
        parent = QWidget()
        qtbot.addWidget(parent)
        mock_viewer = MagicMock()
        mock_viewer.get_saved_crop_rect.return_value = QRect(10, 10, 100, 80)
        parent.viewer = mock_viewer  # type: ignore[attr-defined]
        parent.crop_mode = True  # type: ignore[attr-defined]
        widget = ChannelController("red", Qt.red, parent=parent)
        mock_viewer.get_saved_crop_rect.reset_mock()  # clear calls made during __init__
        img = np.full((120, 160), 100, dtype=np.uint8)
        # Act
        widget._set_preview(img)
        # Assert — crop decision point reached but crop skipped
        mock_viewer.get_saved_crop_rect.assert_called_once()
        assert not widget.preview_label.pixmap().isNull()

    def test_valid_crop_rect_applies_crop(self, qtbot: QtBot) -> None:
        """
        Given a parent with a viewer returning a QRect that intersects the image,
        When _set_preview() is called with crop_mode=False,
        Then the image is cropped and the preview is rendered without error. (EP4, BV1, Branch E)
        """
        # Arrange
        parent = QWidget()
        qtbot.addWidget(parent)
        mock_viewer = MagicMock()
        mock_viewer.get_saved_crop_rect.return_value = QRect(10, 10, 100, 80)  # BV1: fully inside
        parent.viewer = mock_viewer  # type: ignore[attr-defined]
        parent.crop_mode = False  # type: ignore[attr-defined]
        widget = ChannelController("red", Qt.red, parent=parent)
        img = np.full((120, 160), 200, dtype=np.uint8)
        # Act
        widget._set_preview(img)
        # Assert
        assert not widget.preview_label.pixmap().isNull()

    def test_nonintersecting_crop_rect_skips_crop(self, qtbot: QtBot) -> None:
        """
        Given a parent with a viewer returning a QRect entirely outside the image bounds,
        When _set_preview() is called with crop_mode=False,
        Then the intersection is empty, crop is skipped, and preview is rendered. (EP5, BV2, Branch F)
        """
        # Arrange
        parent = QWidget()
        qtbot.addWidget(parent)
        mock_viewer = MagicMock()
        mock_viewer.get_saved_crop_rect.return_value = QRect(200, 200, 50, 50)  # BV2: outside 160×120
        parent.viewer = mock_viewer  # type: ignore[attr-defined]
        parent.crop_mode = False  # type: ignore[attr-defined]
        widget = ChannelController("red", Qt.red, parent=parent)
        img = np.full((120, 160), 50, dtype=np.uint8)
        # Act
        widget._set_preview(img)
        # Assert
        assert not widget.preview_label.pixmap().isNull()
