# Channel Loading

## Contract

The channel loading feature provides a single entry point for importing a Sony ARW
RAW file into one of the three colour slots (Red, Green, Blue). Loading a channel
stores the decoded RGB array in `ImageProcessorService` and, once all three channels
are present, automatically triggers image alignment. Errors at any stage are surfaced
as status bar messages — the application never raises an unhandled exception or shows
a modal error dialog for loading failures.

---

## Supported Input Format

| Property | Value |
|---|---|
| File format | Sony ARW (RAW) |
| Extension filter | `*.arw` |
| Decoder | `rawpy` (`libraw` backend) |
| Post-processing | `use_camera_wb=True`, `no_auto_bright=True`, `output_bps=8` |
| Output array | `H × W × 3`, `uint8`, colour space: RGB |

No other file formats are accepted. Passing a non-ARW file through the dialog is
prevented by the file filter, but if a file with an `.arw` extension contains
incompatible data, `rawpy` raises `LibRawFileUnsupportedError` or `LibRawIOError`,
which is caught and reported as a status bar error.

---

## Entry Points

There are two loading paths, both ultimately calling
`ImageProcessorService.load_channel_from_array()`:

### Interactive load — `load_channel(main_window, channel_idx)`
`src/ui/handlers/channels.py`

Called when the user clicks a **Load** button on a `ChannelController`. Opens a
`QFileDialog` filtered to `*.arw`. On success, stores the selected file path in
`AppState.channel_paths[channel_idx]` before calling the shared processing step.

### Path-based load — `load_channel_from_path(main_window, channel_idx, file_path)`
`src/ui/handlers/channels.py`

Called by `restore_autosave()` at startup to reload channels from persisted paths,
without opening a file dialog. Produces a per-channel status bar error if the file
no longer exists or cannot be decoded; other channels are unaffected.

---

## Processing Sequence

```
load_channel() or load_channel_from_path()
    │
    ▼
load_raw_image() / load_raw_image_from_path()     [image_loading.py]
    │  rawpy.imread(path).postprocess(...)
    │  → rgb_array (H × W × 3, uint8, RGB)
    │  error? → return (None, error_msg)
    │
    ▼
AppState.channel_paths[idx] = file_path
    │
    ▼
_process_channel_image(main_window, channel_idx, rgb_array)
    │
    ├──► svc.load_channel_from_array(idx, rgb_array)   [processor.py]
    │       original_rgb_images[idx] = rgb_array
    │       original_images[idx]     = cv2.cvtColor(rgb, GRAY)
    │       processed[idx]           = grayscale copy
    │
    │       all 3 channels loaded?
    │           YES → _perform_alignment()
    │                   aligned[0..2]     = aligned grayscale
    │                   aligned_rgb[0..2] = aligned RGB
    │                   processed[0..2]  = copies of aligned
    │                 → _update_processed_image(i) for each i
    │                   (applies current brightness/contrast)
    │           NO  → no alignment yet
    │
    ├──► has_aligned_channels()?
    │       YES → for each i: adjust_channel(main_window, i)
    │                          update_channel_preview(main_window, i)
    │             status: "All channels loaded successfully – Ready for editing!"
    │       NO  → update_channel_preview(main_window, idx) only
    │             status: "Successfully loaded image into <Name> channel"
    │
    ├──► update_main_display(main_window)
    │
    └──► update_save_button_state()
             svc.has_processed_channels()? → enable Save button
```

---

## Channel Index Convention

| Index | Colour slot | Load button label | Channel abbreviation |
|---|---|---|---|
| 0 | Red | Load IR | IR (infrared) |
| 1 | Green | Load VIS | VIS (visible) |
| 2 | Blue | Load UV | UV (ultraviolet) |

The abbreviations reflect the spectral sensitivity of the original glass plates used
in the Prokudin-Gorsky process, not standard RGB terminology.

---

## Reloading a Channel

Any of the three channels can be reloaded at any time. When a channel is reloaded:

- The new image replaces `original_images[idx]`, `original_rgb_images[idx]`, and
  `processed[idx]`.
- If all three channels are now present (including the newly loaded one), alignment
  runs again from scratch for all channels.
- Existing per-channel slider values are preserved; `_update_processed_image()` is
  called immediately to apply them to the newly aligned result.
- `AppState.channel_paths[idx]` is updated to the new path.

---

## Error Handling

| Error condition | Source | User-visible result |
|---|---|---|
| User dismisses the file dialog | `QFileDialog` | Silent — no status bar message. |
| File does not exist | `FileNotFoundError` in `rawpy` | Status bar error: "Error loading ARW file: …" |
| File exists but is not a valid ARW | `LibRawFileUnsupportedError` or `LibRawIOError` | Status bar error: "Error loading ARW file: …" |
| Permission denied | `PermissionError` | Status bar error: "Error loading ARW file: …" |
| Alignment fails after load | `AlignmentError` | `AlignmentError` propagates — status bar error from alignment handler. `aligned` remains `[None, None, None]`. |
| Session restore — file missing | `FileNotFoundError` | Status bar error per channel: "Failed to restore <Name> channel: …". Other channels load normally. |

---

## Interactions with Other Features

| Feature | Relationship |
|---|---|
| **Alignment** | Triggered automatically when the third channel is loaded. |
| **Adjustments** | `adjust_channel()` is called for all channels after successful alignment. |
| **Autosave** | `AppState.channel_paths[idx]` is written to `autosave.json` on the next debounce tick. |
| **Save button** | Enabled by `update_save_button_state()` once any processed channel exists. |
| **Channel preview** | `update_channel_preview()` updates the 160×120 thumbnail in the corresponding `ChannelController` after every load. |

---

## Constraints

- Only one channel can be loaded at a time (no batch import).
- The file dialog is modal; the main window is blocked while it is open.
- Alignment always uses the Red channel (index 0) as the fixed reference. Loading Red
  last re-runs alignment and may produce different results than loading it first, since
  Green and Blue are always warped to match whatever is currently in index 0 at the
  time alignment runs.
