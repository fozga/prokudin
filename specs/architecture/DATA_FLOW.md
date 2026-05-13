# Data Flow

## Overview

This document traces every transformation that image data undergoes in Prokudin,
from the moment a RAW file is selected to the moment a colour image is written to
disk. Each stage identifies the responsible module, the array type at that point,
and any branching conditions.

---

## Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1 – RAW DECODE                                               │
│  Module: src/ui/handlers/image_loading.py                           │
│                                                                     │
│  ARW file on disk                                                   │
│      │                                                              │
│      ▼  rawpy.imread(path)                                          │
│  rawpy RawPy object                                                 │
│      │                                                              │
│      ▼  raw.postprocess(use_camera_wb=True,                         │
│                         no_auto_bright=True,                        │
│                         output_bps=8)                               │
│  np.ndarray  shape: H × W × 3   dtype: uint8   colour: RGB         │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2 – CHANNEL INTAKE                                           │
│  Module: src/services/processor.py → load_channel_from_array()      │
│                                                                     │
│  Stored as:                                                         │
│    original_rgb_images[idx]  = rgb_array          (H × W × 3)      │
│    original_images[idx]      = grayscale_array    (H × W)          │
│    processed[idx]            = grayscale_copy     (H × W)          │
│                                                                     │
│  Grayscale conversion:                                              │
│    cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)                      │
│                                                                     │
│  Condition: if all three channels are loaded → proceed to Stage 3   │
│             otherwise → Stage 5 (single-channel preview only)       │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ all 3 channels present
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3 – ALIGNMENT                                                │
│  Module: src/core/align.py → align_images()                         │
│                                                                     │
│  Input:  grayscale_images[3]   each H × W uint8                     │
│          rgb_images[3]         each H × W × 3 uint8                 │
│                                                                     │
│  For each channel i in {1 (Green), 2 (Blue)}:                       │
│    1. ORB.detectAndCompute(grayscale[i])    → keypoints, descriptors│
│    2. BFMatcher(NORM_HAMMING, crossCheck)                           │
│       .match(descriptors[0], descriptors[i])  → matches             │
│    3. len(matches) < 50  →  raise AlignmentError                    │
│    4. estimateAffinePartial2D(src_pts, dst_pts)  → 2×3 matrix       │
│    5. matrix is None  →  raise AlignmentError                       │
│    6. warpAffine(grayscale[i], matrix, (W₀, H₀))                    │
│    7. warpAffine(rgb[i],       matrix, (W₀, H₀))                    │
│                                                                     │
│  Red channel (index 0) is the reference — never warped.             │
│                                                                     │
│  Output stored in ImageProcessorService:                            │
│    aligned[0..2]      aligned grayscale    H₀ × W₀ uint8           │
│    aligned_rgb[0..2]  aligned RGB          H₀ × W₀ × 3 uint8       │
│    processed[0..2]    = copies of aligned  H₀ × W₀ uint8           │
│                                                                     │
│  On AlignmentError: error propagates to handler → status bar msg.  │
│    aligned remains [None, None, None].                              │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4 – BRIGHTNESS / CONTRAST ADJUSTMENT                         │
│  Module: src/core/image_processing.py → apply_adjustments()         │
│          src/services/processor.py  → _update_processed_image()     │
│                                                                     │
│  Triggered by:                                                      │
│    a) Immediately after alignment (with default b=0, c=0)           │
│    b) Slider change → adjust_channel(idx, brightness, contrast)     │
│                                                                     │
│  Formula:                                                           │
│    img_f = aligned[idx].astype(float32)                             │
│    img_f = img_f × (1 + contrast / 100) + brightness               │
│    processed[idx] = clip(img_f, 0, 255).astype(uint8)               │
│                                                                     │
│  Input:  aligned[idx]     H × W uint8                               │
│  Output: processed[idx]   H × W uint8                               │
│                                                                     │
│  Note: adjustment is always applied to aligned[], never to          │
│  processed[]. Re-adjusting the same channel replaces processed[]    │
│  with a fresh result. Non-destructive by design.                    │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                       ┌──────────────┴──────────────┐
                       │                             │
                       ▼                             ▼
            ┌──────────────────┐         ┌───────────────────────┐
            │  STAGE 5a        │         │  STAGE 5b             │
            │  SINGLE-CHANNEL  │         │  CHANNEL COMBINE      │
            │  PREVIEW         │         │                       │
            │                  │         │  Module:              │
            │  get_channel(idx)│         │  image_processing.py  │
            │  → processed[idx]│         │  → combine_channels() │
            │    (copy)        │         │                       │
            │  H × W uint8     │         │  Input:               │
            │                  │         │    processed[0..2]    │
            │  np.stack×3      │         │    each H × W uint8   │
            │  → H × W × 3     │         │    intensities[0..2]  │
            │  (fake RGB for   │         │    each ∈ [0, 200]    │
            │   display)       │         │                       │
            └────────┬─────────┘         │  Formula per pixel:   │
                     │                   │    out[:,:,i] =       │
                     │                   │      processed[i]     │
                     │                   │      × (intensity/100)│
                     │                   │    clip to [0, 255]   │
                     │                   │                       │
                     │                   │  Output:              │
                     │                   │    H × W × 3 uint8    │
                     │                   │    colour: RGB        │
                     │                   │                       │
                     │                   │  Returns None if any  │
                     │                   │  channel is missing.  │
                     └──────────┬────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 6 – OPTIONAL CROP                                            │
│  Module: src/services/processor.py (get_channel / get_combined)     │
│          src/ui/handlers/image_saving.py (apply_crop)               │
│                                                                     │
│  Applied when: saved_crop_rect is set AND crop_mode is False.       │
│  Skipped when: no saved crop, or crop_mode is True (interactive).   │
│                                                                     │
│  crop = (x, y, width, height)                                       │
│  result = image[y : y+h,  x : x+w]  .copy()                        │
│                                                                     │
│  Output dimensions: h × w (or h × w × 3 for combined)              │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                       ┌──────────────┴──────────────┐
                       │                             │
                       ▼                             ▼
            ┌──────────────────┐         ┌───────────────────────┐
            │  STAGE 7a        │         │  STAGE 7b             │
            │  DISPLAY         │         │  SAVE TO DISK         │
            │                  │         │                       │
            │  Module:         │         │  Module:              │
            │  qt_utils.py     │         │  image_saving.py      │
            │                  │         │                       │
            │  convert_to_     │         │  Combined image path: │
            │  qimage(array)   │         │    cv2.merge(         │
            │  → QImage        │         │      [B, G, R])       │
            │  → QPixmap       │         │    ← note: aligned[], │
            │  → ImageViewer   │         │      not processed[]  │
            │                  │         │                       │
            │  No colour space │         │  Per-channel paths:   │
            │  conversion.     │         │    aligned_rgb[i]     │
            │  RGB in = RGB    │         │    cropped, saved as  │
            │  displayed.      │         │    _ir / _vis / _uv   │
            │                  │         │                       │
            │                  │         │  cv2.imwrite()        │
            │                  │         │  formats: JPG/PNG/TIF │
            └──────────────────┘         └───────────────────────┘
```

---

## Array Types at Each Stage

| Stage | Variable | Shape | dtype | Colour space |
|---|---|---|---|---|
| After RAW decode | `rgb` | H × W × 3 | uint8 | RGB |
| After grayscale convert | `original_images[i]` | H × W | uint8 | Grayscale |
| After alignment (grayscale) | `aligned[i]` | H₀ × W₀ | uint8 | Grayscale |
| After alignment (colour) | `aligned_rgb[i]` | H₀ × W₀ × 3 | uint8 | RGB |
| After adjustment | `processed[i]` | H₀ × W₀ | uint8 | Grayscale |
| After combine | `combined` | H₀ × W₀ × 3 | uint8 | RGB |
| After crop | `cropped` | h × w (× 3) | uint8 | same as input |
| For display (QImage) | — | h × w × 3 | uint8 | RGB |
| For file save (combined) | — | h × w × 3 | uint8 | BGR (cv2) |
| For file save (channels) | — | h × w × 3 | uint8 | RGB → BGR |

> **Note:** `H₀` and `W₀` are the dimensions of the Red channel (index 0), which
> is the alignment reference. All other channels are warped to match this size.

---

## Important Behavioural Notes

### What `save_image_with_dialog` saves

The save operation writes **two kinds of output files** to the same directory:

1. **Combined colour image** (`<name>.png`) — built from `aligned[]` (grayscale)
   using `cv2.merge([B, G, R])`. This uses the raw aligned grayscale channels,
   **not** `processed[]`. Brightness/contrast adjustments are therefore **not**
   reflected in the saved combined image.
2. **Per-channel colour images** (`<name>_ir.png`, `<name>_vis.png`,
   `<name>_uv.png`) — built from `aligned_rgb[]` (the aligned RGB originals).

### Crop application during save vs display

| Context | Crop applied? | Source |
|---|---|---|
| Main display (combined) | Yes, if saved rect exists and `crop_mode` is False | `get_combined(crop=...)` |
| Main display (single channel) | Yes, if saved rect exists and `crop_mode` is False | `get_channel(idx, crop=...)` |
| Channel preview (small thumbnail) | No | `get_channel_preview(idx)` |
| Save to disk | Yes, if saved rect exists and `crop_mode` is False | `apply_crop(image, crop_rect)` in `image_saving.py` |
| Autosave JSON | Crop rect coordinates only (not the image) | `CropHandler.get_saved_crop_rect()` |

### ⚠ Issue #48 — `get_channel()` without crop returns internal reference

`get_channel(idx)` (no crop argument) currently returns `self.processed[idx]`
directly. Callers that modify the returned array corrupt the service's internal
state. Until issue #48 is fixed, `processed[]` must be treated as read-only by
all consumers. `get_channel(idx, crop=...)` is not affected — it returns a copy.

---

## Data Flow for Session Restore (Autosave)

At startup, `restore_autosave()` reconstructs in-memory state from the JSON file
without repeating the full pipeline from scratch:

```
autosave.json on disk
    │
    ▼  json.load()
dict { version, channels: { red/green/blue: { path, brightness,
                                              contrast, intensity } },
       crop: { x, y, width, height } }
    │
    ├──► for each channel with a valid path:
    │       load_raw_image_from_path(path)     ← rawpy decode (Stage 1)
    │       load_channel_from_array(idx, rgb)  ← Stages 2–4 run in full
    │
    ├──► set slider values (blockSignals=True, no re-processing triggered)
    │
    ├──► adjust_channel(idx) for each loaded channel  ← Stage 4 with
    │                                                    restored values
    │
    └──► set_saved_crop_rect(QRect(x, y, w, h))
         update_channel_preview() for each channel
         update_main_display()
```

The full alignment pipeline (Stage 3) runs again during restore. There is no
cache of aligned arrays on disk — only the source file paths are persisted.
