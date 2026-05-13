# Alignment – Flow

This document describes the control and data flow for aligning the three channels
in Prokudin. For alignment semantics and parameters see
`specs/features/ALIGNMENT.md`.

---

## Legend

- **Handler** — function in `src/ui/handlers/`.
- **Service** — methods of `ImageProcessorService` in `src/services/processor.py`.
- **Core** — pure functions in `src/core/align.py`.
- **UI** — Qt widgets (no heavy logic).

---

## Alignment Trigger

Alignment is triggered from `_process_channel_image()` in `channels.py` whenever
all three channels have been loaded into the service.

### Flow

```text
_process_channel_image(main_window, channel_idx, rgb_image)
    │
    ├──► svc.load_channel_from_array(channel_idx, rgb_image)
    │       original_rgb_images[idx] = rgb
    │       original_images[idx]     = cvtColor(rgb, GRAY)
    │       processed[idx]           = grayscale copy
    │
    │       all 3 channels present?
    │           YES → _perform_alignment()
    │           NO  → return (no alignment yet)
    │
    └──► (post-alignment display update handled separately)
```

---

## Service-Level Alignment – `_perform_alignment()`

`ImageProcessorService._perform_alignment()` orchestrates calls into the core
alignment routine and updates its own arrays.

### Flow

```text
_perform_alignment()
    │
    ├── ensure all 3 original_images[i] are not None
    │
    ├── grayscale_list = [original_images[0], original_images[1], original_images[2]]
    │   rgb_list        = [original_rgb_images[0], original_rgb_images[1], original_rgb_images[2]]
    │
    ├── aligned_gray, aligned_rgb = align_images(grayscale_list, rgb_list)
    │       (call into src/core/align.py)
    │
    ├── aligned[0..2]      = aligned_gray[0..2]
    ├── aligned_rgb[0..2]  = aligned_rgb[0..2]
    ├── processed[0..2]    = copies of aligned_gray[0..2]
    │
    └── for i in 0..2:
            _update_processed_image(i)
```

If `align_images()` raises `AlignmentError`, `_perform_alignment()` lets the
exception propagate to the caller. The caller is responsible for notifying the
user and leaving `aligned` as `[None, None, None]`.

---

## Core Alignment – `align_images()`

`align_images()` in `src/core/align.py` performs all heavy computation. It takes
three grayscale images and three RGB images as input and returns aligned
versions of both.

### Input validation

```text
align_images(grayscale_images, rgb_images)
    │
    ├── assert len(grayscale_images) == 3
    ├── assert len(rgb_images) == 3
    ├── for each img in grayscale_images:
    │       ensure img is a 2D uint8 array
    ├── for each img in rgb_images:
    │       ensure img is a 3D uint8 array with 3 channels
    │
    └── reference_size = grayscale_images[0].shape  # (H₀, W₀)
```

If any input is missing or has incompatible shape/dtype, `ValueError` is raised.

### ORB keypoint detection

```text
# Create ORB detector
orb = cv2.ORB_create(nfeatures=1000)

for i in 0..2:
    keypoints[i], descriptors[i] = orb.detectAndCompute(grayscale_images[i], mask=None)
```

- `keypoints[i]` — list of keypoint objects for channel `i`.
- `descriptors[i]` — NumPy array of binary descriptors or `None` if no
  keypoints were found.

### Feature matching

```text
matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

for i in {1, 2}:  # Green and Blue
    if descriptors[0] is None or descriptors[i] is None:
        raise AlignmentError("No descriptors for matching")

    matches = matcher.match(descriptors[0], descriptors[i])

    if len(matches) < 50:
        raise AlignmentError(f"Insufficient matches ({len(matches)}/50)")
```

Matches describe correspondences between points in Red (index 0) and the
current channel `i`.

### Affine transform estimation

```text
src_pts = np.float32([ keypoints[i][m.trainIdx].pt for m in matches ]).reshape(-1, 1, 2)
DST_pts = np.float32([ keypoints[0][m.queryIdx].pt for m in matches ]).reshape(-1, 1, 2)

matrix, inliers = cv2.estimateAffinePartial2D(src_pts, DST_pts)

if matrix is None:
    raise AlignmentError(f"Failed to estimate transformation for channel {i}")
```

- `estimateAffinePartial2D` uses a robust estimator (RANSAC) internally.
- The resulting `matrix` is 2×3: rotation + uniform scale + translation.

### Image warping

```text
H₀, W₀ = grayscale_images[0].shape
output_size = (W₀, H₀)

aligned_gray = [None, None, None]
aligned_rgb  = [None, None, None]

# Red channel — no warp
aligned_gray[0] = grayscale_images[0].copy()
aligned_rgb[0]  = rgb_images[0].copy()

# Green and Blue channels — warped
for i in {1, 2}:
    aligned_gray[i] = cv2.warpAffine(grayscale_images[i], matrix_i, output_size)
    aligned_rgb[i]  = cv2.warpAffine(rgb_images[i],       matrix_i, output_size)
```

Each channel `i` has its own transform `matrix_i`. Areas mapped outside the
image bounds are filled with zeros (black).

### Output

`align_images()` returns `(aligned_gray, aligned_rgb)` with:

- `aligned_gray[i]` — aligned grayscale H₀×W₀ `uint8` arrays.
- `aligned_rgb[i]` — aligned RGB H₀×W₀×3 `uint8` arrays.

The service writes these into its `aligned` and `aligned_rgb` fields and uses
copies to initialise `processed`.

---

## Error Propagation and User Feedback

### AlignmentError

If `align_images()` raises `AlignmentError`, the call stack is:

```text
_process_channel_image()
    → svc.load_channel_from_array()
        → _perform_alignment()
            → align_images()  # raises AlignmentError
```

`channels.py` catches `AlignmentError` and:

- Writes an error message to the status bar, e.g.
  "Alignment failed: Insufficient matches (34/50)".
- Leaves `svc.aligned` and `svc.aligned_rgb` as `[None, None, None]`.
- Calls `update_channel_preview()` only for the newly loaded channel.
- Does **not** update the combined main display.

Subsequent loads of any channel will re-trigger `_perform_alignment()` and may
succeed if the new data contains more usable features.

### Non-fatal conditions

Some situations do not raise an exception but still prevent useful alignment:

- ORB finds zero keypoints in Green or Blue: `descriptors[i] is None`.
- All descriptors are identical (e.g. flat regions): matching produces too few
  distinct matches.

In these cases, `AlignmentError` is raised with an explanatory message and
handled as above.

---

## Interaction with Display and Save Flows

Once `_perform_alignment()` completes successfully:

1. `_update_processed_image(i)` is called for each channel `i` to apply current
   brightness/contrast to the aligned grayscale arrays.
2. `update_channel_preview()` is called to refresh the three channel thumbnails.
3. `update_main_display()` is called to show either the combined or single-channel
   view based on `AppState.show_combined`.
4. `update_save_button_state()` enables the Save button because
   `svc.has_aligned_channels()` and `svc.has_processed_channels()` both return
   `True`.

The **image saving** flow reads directly from `aligned` and `aligned_rgb` to
write files to disk; see `specs/features/IMAGE_SAVING.md` and
`specs/flows/CHANNEL_LOADING_FLOW.md` for details.
