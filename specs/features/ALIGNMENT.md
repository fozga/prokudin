# Alignment

## Contract

The alignment feature automatically registers the Green and Blue channels to the Red
channel using ORB feature matching and an affine warp transformation. Alignment is
triggered exactly once — when the third channel is loaded into
`ImageProcessorService`. The Red channel is the fixed spatial reference; only Green
and Blue are transformed. The same transformation matrix is applied to both the
grayscale working copy and the original RGB array for each channel, ensuring that
all downstream operations (adjustments, combine, save) operate on geometrically
consistent data.

If alignment cannot be computed (too few visual features, degenerate geometry),
`AlignmentError` is raised and the aligned arrays remain `None`. The application
remains usable with unaligned channels, but `get_combined()` will return `None`
and the Save button remains disabled.

---

## Algorithm

### Feature detection

```
ORB detector — nfeatures=1000
    ↓
For each of the 3 grayscale channels:
    keypoints[i], descriptors[i] = ORB.detectAndCompute(grayscale[i], mask=None)
```

ORB (Oriented FAST and Rotated BRIEF) is chosen for its speed and licence-free
status. The 1000-feature limit balances matching accuracy against processing time
on typical film-plate scans.

### Feature matching

```
For i in {1 (Green), 2 (Blue)}:
    matches = BFMatcher(NORM_HAMMING, crossCheck=True)
                .match(descriptors[0], descriptors[i])

    len(matches) < 50  →  raise AlignmentError(
        f"Insufficient matches ({len(matches)}/50)")
```

Brute-force matching with Hamming distance is used because ORB descriptors are
binary. `crossCheck=True` enforces mutual consistency: a match is accepted only
if descriptor A is the best match for B **and** B is the best match for A. This
eliminates the need for a ratio test and reduces false positives.

The 50-match threshold guards against images that share too little overlapping
content or that contain too few texture features (e.g. blank or uniformly grey
areas).

### Transform estimation

```
src_pts = [keypoints[i][m.trainIdx].pt  for m in matches]  # channel i points
dst_pts = [keypoints[0][m.queryIdx].pt  for m in matches]  # Red channel points

matrix, inlier_mask = cv2.estimateAffinePartial2D(
    src_pts.reshape(-1, 1, 2),
    dst_pts.reshape(-1, 1, 2)
)

matrix is None  →  raise AlignmentError(
    f"Failed to estimate transformation for channel {i}")
```

`estimateAffinePartial2D` estimates a **partial affine transform** (4 degrees of
freedom: rotation, uniform scale, translation x, translation y). Shear and
non-uniform scaling are not modelled, which is appropriate for Prokudin-Gorsky
plates where the camera did not move between exposures — only small registration
offsets are expected.

RANSAC is used internally by `estimateAffinePartial2D` to reject outlier matches.

### Warp application

```
output_size = (grayscale[0].shape[1], grayscale[0].shape[0])  # (W₀, H₀)

aligned_grayscale[i] = cv2.warpAffine(grayscale[i], matrix, output_size)
aligned_rgb[i]       = cv2.warpAffine(rgb[i],       matrix, output_size)
```

The output dimensions are fixed to those of the Red channel. Areas that map outside
the image boundary after warping are filled with zeros (black). The same matrix is
applied to the grayscale and RGB copies so that all representations remain
pixel-accurate with each other.

Red (index 0) is copied directly:

```
aligned_grayscale[0] = grayscale[0].copy()
aligned_rgb[0]       = rgb[0].copy()
```

---

## Trigger Conditions

| Condition | Alignment runs? |
|---|---|
| First or second channel loaded | No |
| Third channel loaded (any slot) | Yes — all three channels are aligned |
| Channel reloaded after all three exist | Yes — alignment re-runs for all channels |
| `adjust_channel()` called | No — alignment result is reused |
| Application restored from autosave | Yes — channels are reloaded from paths, alignment re-runs |

There is no cached alignment result on disk. Every application start that restores
a session re-runs the full alignment pipeline.

---

## Parameters

| Parameter | Value | Location | Rationale |
|---|---|---|---|
| ORB `nfeatures` | 1000 | `align.py` line with `ORB_create` | Balances accuracy and speed for typical scan resolution |
| Minimum matches | 50 | `align.py` constant `min_matches` | Below this, transform estimation is unreliable |
| Matcher type | BFMatcher, NORM_HAMMING, crossCheck=True | `align.py` | Appropriate for binary ORB descriptors |
| Transform type | Partial affine (rotation + scale + translation) | `estimateAffinePartial2D` | 4 DOF sufficient for plate registration |
| Border fill | 0 (black) | `warpAffine` default | Areas outside the warped source become black |

---

## Output

After successful alignment, `ImageProcessorService` contains:

| Field | Content |
|---|---|
| `aligned[0]` | Red channel grayscale — unchanged copy of `original_images[0]` |
| `aligned[1]` | Green channel grayscale warped to match Red |
| `aligned[2]` | Blue channel grayscale warped to match Red |
| `aligned_rgb[0]` | Red channel RGB — unchanged copy of `original_rgb_images[0]` |
| `aligned_rgb[1]` | Green channel RGB warped with the same matrix as `aligned[1]` |
| `aligned_rgb[2]` | Blue channel RGB warped with the same matrix as `aligned[2]` |
| `processed[0..2]` | Copies of `aligned[0..2]`, ready for adjustment |

All arrays share the same spatial dimensions: `H₀ × W₀` (the dimensions of the
Red channel).

---

## Error Handling

| Error | Condition | Effect |
|---|---|---|
| `AlignmentError("Insufficient matches …")` | `len(matches) < 50` for channel G or B | `aligned` stays `[None, None, None]`. Error propagates to handler → status bar message. |
| `AlignmentError("Failed to estimate transformation …")` | `estimateAffinePartial2D` returns `None` | Same as above. |
| `descriptors[i] is None` or `descriptors[i].size == 0` | ORB found no keypoints in a channel | The match step is skipped for that channel; `aligned[i]` remains `None`. No exception is raised — effectively the same outcome as insufficient matches. |

When alignment fails, `svc.has_aligned_channels()` returns `False`, the main
display shows nothing new, and the Save button remains disabled. The user may
reload any channel to retry alignment.

---

## Interactions with Other Features

| Feature | Relationship |
|---|---|
| **Channel Loading** | Alignment is triggered by the third `load_channel_from_array()` call. |
| **Adjustments** | `_update_processed_image()` is called for all channels immediately after successful alignment, applying the current (or default) brightness and contrast values. |
| **Display** | `update_channel_preview()` and `update_main_display()` are called after alignment to refresh all views. |
| **Image Saving** | `save_image_with_dialog()` reads from `aligned[]` and `aligned_rgb[]` directly, bypassing `processed[]`. |
| **Autosave** | Alignment re-runs on session restore. Only file paths are persisted — not alignment results. |

---

## Constraints and Known Limitations

- Alignment is global (whole-image). It does not handle images where different
  regions have different offsets (e.g. images with foreground motion between
  exposures).
- The model assumes the three plates are captured from the same position with no
  perspective change. Large perspective differences will cause poor alignment.
- Uniform or near-uniform images (plain backgrounds, solid colours) produce fewer
  than 50 ORB matches and raise `AlignmentError`. These images cannot be aligned
  automatically.
- There is no user-facing control to adjust alignment parameters (e.g. minimum
  matches, transform type) in the current implementation.
- Alignment always uses Red as the reference. It is not possible to designate a
  different channel as the reference without modifying `align.py`.
