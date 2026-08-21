# Adjustments

## Contract

The adjustments feature provides per-channel, non-destructive brightness, contrast,
and intensity controls. Each control operates on a single grayscale channel's aligned
image and produces an updated entry in `ImageProcessorService.processed[]`. Changes
are reflected immediately in the channel preview thumbnail and the main display.
Adjustments are non-destructive: `processed[i]` is always recomputed from
`aligned[i]` — the aligned base is never modified. Resetting a slider to zero
produces output identical to the original aligned image.

---

## Controls

Each of the three `ChannelController` widgets exposes three sliders:

| Control | Range | Default | Unit | Scope |
|---|---|---|---|---|
| Brightness | −100 … 100 | 0 | additive pixel value | Per-channel grayscale |
| Contrast | −100 … 100 | 0 | percentage multiplier | Per-channel grayscale |
| Intensity | 0 … 100 | 100 | percentage multiplier | Applied only in `combine_channels()` |

Brightness and contrast operate on the grayscale `processed[]` array.
Intensity is stored as a slider value but applied later, only when
`combine_channels()` builds the RGB output — it scales each channel's contribution
to the combined image independently of `processed[]`.

---

## Formulas

### Brightness and contrast — `apply_adjustments()`
`src/core/image_processing.py`

\[
output = clip((input - 128) * (1 + contrast / 100) + 128 + brightness, 0, 255)
\]

Computation steps:

```
img_f = aligned[idx].astype(float32)
img_f = (img_f - 128) * (1 + contrast / 100) + 128 + brightness
processed[idx] = clip(img_f, 0, 255).astype(uint8)
```

Neutral values (brightness=0, contrast=0) produce output identical to the input.

### Intensity — `combine_channels()`
`src/core/image_processing.py`

\[
\text{combined}[:,:,i] = \operatorname{clip}\!\left(\text{processed}[i] \times \frac{\text{intensity}_i}{100},\ 0,\ 255\right)
\]

Intensity=100 (default) leaves the channel unchanged. Intensity=0 suppresses the
channel entirely. Intensity=200 would double channel brightness — but the current
slider maximum is 100, so the range in practice is [0 %, 100 %].

---

## Adjustment Pipeline

```
User moves slider
    │
    ▼
ChannelController.sliders["brightness" | "contrast"].valueChanged
    │  emits value_changed signal
    ▼
MainWindow slot → adjust_channel(main_window, channel_idx)   [channels.py]
    │
    ├──► status: "Processing image, please wait…"
    │
    ├──► brightness = controllers[idx].sliders["brightness"].value()
    │    contrast   = controllers[idx].sliders["contrast"].value()
    │
    ├──► svc.adjust_channel(idx, brightness, contrast)        [processor.py]
    │       adjustments[idx] = ChannelAdjustments(brightness, contrast)
    │       _update_processed_image(idx)
    │           base = aligned[idx]
    │           processed[idx] = apply_adjustments(base, brightness, contrast)
    │
    ├──► update_channel_preview(main_window, idx)
    │       controller.processed_image = svc.get_channel_preview(idx)
    │       controller.update_preview()   → 160×120 thumbnail
    │
    ├──► update_main_display(main_window)
    │       show_combined or show_single_channel
    │
    └──► status: ""  (cleared)
```

Intensity slider changes follow the same path — `value_changed` is emitted,
`adjust_channel` is called — but intensity only takes effect inside
`get_combined()` / `show_combined_image()`, not in `_update_processed_image()`.

---

## Non-Destructiveness

`processed[i]` is always recomputed from `aligned[i]`, never from a previous
`processed[i]`. This means:

- Adjusting the same channel multiple times does not accumulate errors.
- Resetting brightness and contrast to 0 restores `processed[i]` to an exact copy
  of `aligned[i]`.
- Reloading a channel re-runs alignment and resets `processed[i]` to the new
  aligned result before current slider values are re-applied.

---

## Slider Interaction Details

### Dual input — slider + text field

Each slider is paired with a `QLineEdit` text field. Changes in either widget
synchronise the other:

- Slider move → `_update_text_from_slider()` updates the text field
  (with `blockSignals` to prevent recursion).
- Text edit → `_update_slider_from_text()` clamps the entered value to the slider
  range and sets the slider.

### Double-click to reset

`ResetSlider` (a `QSlider` subclass) emits a `doubleClicked` signal on double-click.
`ChannelController._reset_slider_to_default()` handles this signal and restores the
slider and text field to the `DefaultState` default value (0 for brightness and
contrast, 100 for intensity).

### Signal blocking during batch updates

When `restore_autosave()` or `apply_preset()` sets multiple sliders programmatically,
`ChannelController.blockSignals(True)` is called before the first slider and
`blockSignals(False)` after the last. This prevents `value_changed` from firing for
each individual slider change. A single `adjust_channel()` call per channel is made
explicitly after signals are unblocked.

---

## Interactions with Other Features

| Feature | Relationship |
|---|---|
| **Alignment** | `_update_processed_image()` is called for all channels immediately after alignment, applying the current slider values to the freshly aligned arrays. |
| **Display** | Every `adjust_channel()` call ends with `update_main_display()`, keeping the viewer in sync. |
| **Autosave** | Slider values are serialised to `autosave.json` by `save_autosave()` (reads from widget state directly). Restored by `restore_autosave()` using `blockSignals`. |
| **Presets** | `save_preset()` reads current slider values. `apply_preset()` writes slider values and calls `adjust_channel()` per channel. |
| **Image Saving** | The combined image saved by `save_image_with_dialog()` is built from `aligned[]` directly (grayscale merge), **not** from `processed[]`. Brightness and contrast adjustments are therefore not reflected in the saved output. Intensity is also not applied. See `DATA_FLOW.md` Stage 7b. |

---

## Constraints

- Adjustments apply to grayscale data only. The original colour information in
  `aligned_rgb[]` is never modified by brightness or contrast changes.
- There is no per-pixel mask or selection — adjustments always affect the entire
  channel.
- Brightness and contrast adjustments operate in `float32` internally, then clip
  back to `uint8`. Repeated adjustment–save–reload cycles would accumulate
  quantisation loss, but this does not occur in normal use because `processed[]`
  is always derived from `aligned[]`.
- The intensity slider maximum is 100 (100 %) in the UI, meaning channels cannot
  be amplified beyond their adjusted value — only attenuated. The underlying
  `combine_channels()` accepts values up to 200.
