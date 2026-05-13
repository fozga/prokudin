# Image Saving

## Contract

The image saving feature exports the current alignment result to disk as:

1. One **combined colour image** built from the aligned grayscale channels, and
2. Up to three **per-channel colour images** built from the aligned RGB channels
   (`_ir`, `_vis`, `_uv` suffixes).

Saving is only possible when at least one aligned channel exists. The save
operation never crashes the application: all I/O errors are caught and reported
as error messages; the caller receives a `(success: bool, message: str)` tuple.

> **Important:** The combined image is built from `aligned[]` (grayscale) and
> does **not** include brightness/contrast or intensity adjustments from
> `processed[]`. Image saving reflects alignment only, not the adjustment state.

---

## Entry Point

### `save_image_with_dialog(main_window) -> tuple[bool, str]`
`src/ui/handlers/image_saving.py`

User-facing entry point called when the **Save** button is clicked.

High-level behaviour:

1. Guard: if no aligned channels exist (`svc.has_aligned_channels()` is `False`),
   saving is refused and `(False, "No images to save")` is returned.
2. A modal `QFileDialog` asks the user for a base file name and format.
3. A crop rectangle is resolved from the current viewer state.
4. Individual aligned RGB channels, if present, are saved as
   `<base>_ir.<ext>`, `<base>_vis.<ext>`, `<base>_uv.<ext>`.
5. A combined RGB image (from aligned grayscale channels) is saved as
   `<base>.<ext>`.
6. A summary `(success, message)` is returned, indicating whether all images
   were written successfully.

---

## File Dialog and Format Resolution

### Filters

The file dialog uses the following filter string:

```text
"JPEG (*.jpg);;TIFF (*.tif);;PNG (*.png);;All Files (*)"
```

The initial directory is the default for the platform; there is no custom
starting path. The dialog returns two values:

- `filepath`: absolute path chosen by the user (may or may not include an extension)
- `selected_filter`: the filter string that was active when the user clicked Save

### Extension handling — `_get_file_path_info()`

`_get_file_path_info(main_window, file_filters)` normalises the output path and
file format:

1. If `filepath` is empty, the user cancelled — `(None, None)` is returned and
   the caller reports "Save operation cancelled".
2. If `filepath` has no extension, the first extension from `selected_filter`
   is extracted (e.g. `jpg` from `"JPEG (*.jpg)"`) and appended to the path.
3. `file_format` is the lowercased extension without the dot (e.g. `"jpg"`).

The function returns `(filepath, file_format)` or `(filepath, None)` if no
extension could be determined from either the path or the filter.

---

## Crop Resolution

Before saving, the handler computes an optional crop rectangle in image-space
coordinates:

```python
saved_crop_rect = main_window.viewer.get_saved_crop_rect()

crop_rect = None if main_window.state.crop_mode else (
    (saved_crop_rect.left(),
     saved_crop_rect.top(),
     saved_crop_rect.width(),
     saved_crop_rect.height())
    if saved_crop_rect
    else None
)
```

Rules:

- If **crop mode is active**, the working crop is still being edited and is **not**
  applied; `crop_rect` is `None`.
- If crop mode is inactive and a saved crop rect exists, `crop_rect` is a
  4-tuple `(x, y, width, height)` in pixel coordinates.
- If no crop rect exists, `crop_rect` is `None` and images are saved uncropped.

Cropping is performed by `apply_crop(image, crop_rect)`, which clamps the crop
rectangle to image bounds and returns an empty array if the input is empty.

---

## Per-Channel Image Saving

### `_save_cropped_images()`

```python
_save_cropped_images(
    images: Sequence[Optional[np.ndarray]],
    filepath: str,
    channel_names: list[str],
    crop_rect: tuple[int,int,int,int] | None,
    file_format: str,
) -> list[tuple[bool, str]]
```

For each non-`None` entry in `images` (typically `svc.aligned_rgb`):

1. Apply `apply_crop(img, crop_rect)` if a crop rect is provided.
2. Compute `channel_path` by inserting `_<channel_name>` before the extension:
   - Base path: `/path/to/output.png`
   - IR path: `/path/to/output_ir.png`
   - VIS path: `/path/to/output_vis.png`
   - UV path: `/path/to/output_uv.png`
3. Call `save_image(img_to_save, channel_path, file_format, is_bgr=True)`.

The `channel_names` used by `save_image_with_dialog()` are fixed:

| Channel index | Name | Suffix |
|---|---|---|
| 0 | Red spectral slot | `_ir` |
| 1 | Green spectral slot | `_vis` |
| 2 | Blue spectral slot | `_uv` |

`is_bgr=True` indicates that the input is in **RGB** but must be converted to
OpenCV's BGR order before writing.

---

## Combined Image Saving

### `_create_combined_image()`

```python
_create_combined_image(
    aligned_images: Sequence[Optional[np.ndarray]],
    crop_rect: tuple[int,int,int,int] | None,
) -> Optional[np.ndarray]
```

This helper builds a combined RGB image for saving using aligned grayscale
channels:

1. If all channels are `None`, returns `None` — nothing to save.
2. Finds the first non-`None` channel to infer the output shape.
3. Crops non-`None` channels **before** filling missing ones with zeros so that
   the placeholder zeros use the post-crop shape.
4. For any `None` channel, substitutes a zero array of shape `out_shape`.
5. Returns `cv2.merge([channels[2], channels[1], channels[0]])`, i.e. B, G, R
   in OpenCV order.

`save_image_with_dialog()` then calls:

```python
combined = _create_combined_image(main_window.svc.aligned, crop_rect)
if combined is not None:
    success, message = save_image(combined, filepath, file_format, is_bgr=False)
```

Here `is_bgr=False` indicates that `combined` is already in BGR order and does
not need colour channel swapping.

---

## Low-Level Save Function

### `save_image(image, filepath=None, file_format=None, is_bgr=False)`

Single helper that wraps `cv2.imwrite` and normalises errors.

Behaviour:

1. If `image` is `None` or empty (`image.size == 0`), returns
   `(False, "No image data to save")`.
2. If `filepath` is `None`, returns
   `(False, "No filepath provided")`.
3. If `file_format` is `None`, attempts to infer it from the filepath extension;
   if this fails, returns
   `(False, "No file extension provided and no format specified")`.
4. If `is_bgr` is `True` and the image has 3 channels, converts from RGB to BGR
   via `cv2.cvtColor(image, cv2.COLOR_RGB2BGR)`.
5. Writes the image using format-specific options:

   | Format | Condition | cv2 call |
   |---|---|---|
   | JPEG | `file_format in {"jpg", "jpeg"}` | `cv2.imwrite(path, img, [IMWRITE_JPEG_QUALITY, 95])` |
   | PNG | `file_format == "png"` | `cv2.imwrite(path, img, [IMWRITE_PNG_COMPRESSION, 9])` |
   | TIFF | `file_format in {"tif", "tiff"}` | `cv2.imwrite(path, img)` |
   | Other | any other extension | `cv2.imwrite(path, img)` |

6. Returns `(True, filepath)` if `cv2.imwrite` reports success, otherwise
   `(False, f"Failed to save image to {filepath}")`.
7. Catches `FileNotFoundError` and `PermissionError` and returns
   `(False, f"Error saving image: {e}")`.

---

## Summary Result

`save_image_with_dialog()` aggregates results from per-channel and combined
saves into a single `(success, message)` pair:

```python
success_count = sum(1 for success, _ in results if success)

if success_count == 0:
    return False, "Failed to save any images"
if success_count < len(results):
    return True, f"Saved {success_count} out of {len(results)} images"
return True, f"Successfully saved all images to {os.path.dirname(filepath)}"
```

This ensures the caller always receives a clear textual summary:

- "Failed to save any images" — hard failure
- "Saved N out of M images" — partial success
- "Successfully saved all images to <dir>" — full success

---

## Preconditions and UI State

- `main_window.svc.has_aligned_channels()` must be `True` to enable the Save
  button. This guarantees that at least one of `svc.aligned` or `svc.aligned_rgb`
  contains non-`None` entries.
- If `crop_mode` is active, the current (editable) crop rectangle is **not**
  applied. The user must accept the crop to have it reflected in saved images.
- The file dialog may be cancelled by the user at any time, resulting in
  `(False, "Save operation cancelled")`.

---

## Interactions with Other Features

| Feature | Relationship |
|---|---|
| **Alignment** | Uses `svc.aligned` and `svc.aligned_rgb` directly. Save is disabled when alignment has never succeeded. |
| **Adjustments** | Ignored — brightness/contrast and intensity do not affect the saved combined image or per-channel exports. |
| **Crop** | Saved images are cropped to the saved crop rectangle if crop mode is inactive. Crop state is read from `ImageViewer` and `AppState.crop_mode`. |
| **Autosave** | Does not write anything to autosave; only reads the crop rectangle which may have been restored earlier. |
| **Presets** | Save does not depend on presets; however, users typically adjust sliders via presets before saving. |
