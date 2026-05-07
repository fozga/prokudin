# Service Layer Refactor — Migration Plan

## 1. File Inventory

| File | Action | What changes |
|------|--------|--------------|
| `src/core/image_processing.py` | **Modified** | Remove `convert_to_qimage` function and `from PyQt5.QtGui import QImage` import; module becomes Qt-free. |
| `src/core/__init__.py` | Unchanged | No changes needed. |
| `src/core/align.py` | Unchanged | Already Qt-free; no changes. |
| `src/services/__init__.py` | **Created** | New package init with GPL header and docstring. |
| `src/services/processor.py` | **Created** | `ChannelAdjustments` dataclass and `ImageProcessorService` class — owns all image-array state and exposes pure-Python methods. |
| `src/ui/__init__.py` | **Created** | New package init with GPL header and docstring. |
| `src/ui/qt_utils.py` | **Created** | `convert_to_qimage` moved here from `core/image_processing.py`. |
| `src/ui/main_window.py` | **Moved** from `src/main_window.py` | Add `self.svc = ImageProcessorService()` to `__init__`. Update all relative imports from `.handlers.` → `.ui.handlers.`, `.widgets.` → `.ui.widgets.`, etc. Convert `QRect` to plain tuple before passing to `svc`. |
| `src/ui/app_state.py` | **Moved** from `src/app_state.py` | Update relative import of `DefaultState`. Contains only UI-specific state (`crop_rect: QRect`, `crop_mode`, `show_combined`, `current_channel`, `grid_settings_dialog`). Image arrays removed (now owned by `svc`). |
| `src/ui/default_state.py` | **Moved** from `src/default_state.py` | No content changes; only file location changes. |
| `src/ui/handlers/__init__.py` | **Moved** from `src/handlers/__init__.py` | No content changes. |
| `src/ui/handlers/channels.py` | **Moved** from `src/handlers/channels.py` | Delegates image storage and alignment to `svc`. Reads slider values from controllers (Qt), calls `svc.adjust_channel()`, receives `np.ndarray` back, updates previews. `_process_channel_image` becomes a thin bridge that calls `svc.load_channel_from_array()`. |
| `src/ui/handlers/display.py` | **Moved** from `src/handlers/display.py` | Calls `svc.get_combined(crop=...)` and `svc.get_channel(idx, crop=...)` instead of doing array slicing inline. Uses `qt_utils.convert_to_qimage` instead of `core.image_processing.convert_to_qimage`. Converts saved crop `QRect` to tuple before passing to `svc`. |
| `src/ui/handlers/image_loading.py` | **Moved** from `src/handlers/image_loading.py` | No content changes; only import paths update. |
| `src/ui/handlers/image_saving.py` | **Moved** from `src/handlers/image_saving.py` | `apply_crop` helper changes to accept `tuple[int,int,int,int] | None` instead of `QRect`. Conversion from `QRect` → tuple happens at the call-site in `save_image_with_dialog`. `_create_combined_image` and `_save_cropped_images` accept plain tuple crop. |
| `src/ui/handlers/keyboard.py` | **Moved** from `src/handlers/keyboard.py` | No content changes beyond import path updates. |
| `src/ui/handlers/autosave.py` | **Moved** from `src/handlers/autosave.py` | Reads channel paths from `svc` (or `state.channel_paths`). `QRect` construction from JSON stays here (UI layer). Import paths update. Saves slider values from controllers, crop rect from viewer — schema unchanged. |
| `src/ui/handlers/presets.py` | **Moved** from `src/handlers/presets.py` | No content changes beyond import path updates. |
| `src/ui/widgets/__init__.py` | **Moved** from `src/widgets/__init__.py` | No content changes. |
| `src/ui/widgets/channel_controller.py` | **Moved** from `src/widgets/channel_controller.py` | No content changes; only import paths change if any relative imports exist. |
| `src/ui/widgets/crop_handler.py` | **Moved** from `src/widgets/crop_handler.py` | No content changes. |
| `src/ui/widgets/grid_overlay.py` | **Moved** from `src/widgets/grid_overlay.py` | No content changes. |
| `src/ui/widgets/grid_settings_dialog.py` | **Moved** from `src/widgets/grid_settings_dialog.py` | No content changes. |
| `src/ui/widgets/grid_types.py` | **Moved** from `src/widgets/grid_types.py` | No content changes. |
| `src/ui/widgets/image_viewer.py` | **Moved** from `src/widgets/image_viewer.py` | No content changes. |
| `src/ui/widgets/preset_panel.py` | **Moved** from `src/widgets/preset_panel.py` | No content changes. |
| `src/ui/widgets/sliders.py` | **Moved** from `src/widgets/sliders.py` | No content changes. |
| `src/ui/widgets/status_bar.py` | **Moved** from `src/widgets/status_bar.py` | No content changes. |
| `src/__init__.py` | **Modified** | Stays as package root; no changes needed. |
| `src/main.py` | **Modified** | Import changes from `.main_window` → `.ui.main_window`. |
| `src/main_window.py` | **Deleted** | Moved to `src/ui/main_window.py`. |
| `src/app_state.py` | **Deleted** | Moved to `src/ui/app_state.py`. |
| `src/default_state.py` | **Deleted** | Moved to `src/ui/default_state.py`. |
| `src/handlers/` (entire dir) | **Deleted** | All files moved to `src/ui/handlers/`. |
| `src/widgets/` (entire dir) | **Deleted** | All files moved to `src/ui/widgets/`. |

**Total: 4 files created, 20 files moved, 4 files modified in-place, 1 file deleted (main_window.py original), 2 directories deleted.**

## 2. Handler-by-Handler Delegation Map

### `ui/handlers/channels.py`

| Function | What delegates to `svc` | What stays as Qt glue |
|----------|------------------------|-----------------------|
| `_process_channel_image` | Calls `svc.load_channel_from_array(idx, rgb_array)` which stores RGB, converts to gray, triggers alignment, and runs initial adjustments. Returns nothing — `svc` holds the arrays internally. | Status messages via `main_window.status_handler`, calls `update_channel_preview` and `update_main_display` (both Qt). |
| `load_channel` | Nothing directly — calls `_process_channel_image` which delegates. | Opens `QFileDialog` via `load_raw_image()`, stores `file_path` in `state.channel_paths`. |
| `load_channel_from_path` | Same as above via `_process_channel_image`. | Status messages. |
| `adjust_channel` | Calls `svc.adjust_channel(idx, brightness, contrast, intensity)`. | Reads slider values from `main_window.controllers[idx].sliders` (Qt widgets), calls `update_channel_preview` and `update_main_display`. |
| `update_channel_preview` | Calls `svc.get_channel_preview(idx)` to get `np.ndarray`. | Sets the array on the controller widget's `processed_image` and calls `controller.update_preview()`. |
| `show_single_channel` | Nothing. | Sets `state.show_combined = False`, `state.current_channel = idx`, calls `update_main_display`. |

### `ui/handlers/display.py`

| Function | What delegates to `svc` | What stays as Qt glue |
|----------|------------------------|-----------------------|
| `update_main_display` | Nothing directly. | Routes to `show_combined_image` or `show_single_channel_image`; updates scene rect. |
| `show_combined_image` | Calls `svc.get_combined(crop=crop_tuple)` which returns `np.ndarray` (HxWx3). Intensities are read from controllers and passed to `svc`. | Converts crop `QRect` → tuple. Calls `qt_utils.convert_to_qimage()`, wraps in `QPixmap`, calls `viewer.set_image()`. |
| `show_single_channel_image` | Calls `svc.get_channel(idx, crop=crop_tuple)` which returns `np.ndarray` (HxW grayscale). | Same QRect→tuple conversion, `convert_to_qimage`, `QPixmap`, `viewer.set_image()`. |

### `ui/handlers/image_saving.py`

| Function | What delegates to `svc` | What stays as Qt glue |
|----------|------------------------|-----------------------|
| `apply_crop` | Becomes a pure-Python function: accepts `tuple[int,int,int,int] | None` instead of `QRect`. No `svc` needed — it's a utility. | N/A (no longer uses Qt types). |
| `save_image_with_dialog` | Could call `svc.export(path, crop)` but currently the logic is fine as-is since it uses `cv2.imwrite`. The main change is converting `QRect` to tuple at call-site. | `QFileDialog` for path selection, `QRect` → tuple conversion. |
| `_save_cropped_images` | Accepts `tuple | None` for crop instead of `QRect`. | None — already pure Python/cv2. |
| `_create_combined_image` | Accepts `tuple | None` for crop. | None — already pure Python/cv2. |

### `ui/handlers/autosave.py`

| Function | What delegates to `svc` | What stays as Qt glue |
|----------|------------------------|-----------------------|
| `save_autosave` | Reads `state.channel_paths` (list of strings — not image data). | Reads slider values from controllers, reads crop rect from viewer, serializes to JSON. All Qt. |
| `restore_autosave` | Calls `load_channel_from_path` which delegates to `svc`. | Constructs `QRect` from JSON, sets sliders, blocks signals. |
| `clear_autosave` | Nothing. | Deletes file. |

### `ui/handlers/keyboard.py`

| Function | What delegates to `svc` | What stays as Qt glue |
|----------|------------------------|-----------------------|
| `handle_key_press` | Nothing. | Sets `state.show_combined` and `state.current_channel`, calls `update_main_display`. Pure Qt event handling. |

### `ui/handlers/presets.py`

| Function | What delegates to `svc` | What stays as Qt glue |
|----------|------------------------|-----------------------|
| `save_preset` | Nothing. | Reads slider values, writes JSON, saves thumbnail `QPixmap`. |
| `apply_preset` | Nothing — calls `adjust_channel` which delegates. | Sets slider values, blocks signals. |

## 3. Risks and Ambiguities

### 3.1 QRect Leakage into Non-UI Code

**Risk:** `QRect` currently flows into `image_saving.py:apply_crop()` and `display.py` array slicing. The crop handler and image viewer store crop rectangles as `QRect`.

**Mitigation:** The `QRect` → `tuple[int,int,int,int]` conversion happens exactly at these boundaries:
- `display.py:show_combined_image` — convert `viewer.get_saved_crop_rect()` to tuple before passing to `svc.get_combined(crop=...)`
- `display.py:show_single_channel_image` — same pattern
- `image_saving.py:save_image_with_dialog` — convert crop rect to tuple before passing to `_save_cropped_images` / `_create_combined_image`
- `main_window.py:apply_crop` — convert crop rect to tuple if/when passing to `svc`

The `ImageViewer` and `CropHandler` widgets keep `QRect` internally — this is correct since they're UI widgets.

### 3.2 AppState Split

**Risk:** `AppState` currently holds both image arrays (`original_images`, `aligned`, `processed`, `original_rgb_images`, `aligned_rgb`) and UI state (`crop_mode`, `crop_rect`, `show_combined`, etc.). Moving image arrays to `svc` while keeping UI state in `AppState` requires careful coordination.

**Mitigation:** After the refactor, `AppState` retains only:
- `channel_paths: list[str | None]` — needed for autosave serialization
- `show_combined: bool`
- `current_channel: int`
- `crop_mode: bool`
- `crop_rect: QRect | None`
- `crop_ratio: tuple[int, int] | None`
- `grid_settings_dialog: GridSettingsDialog | None`

The service owns `original_gray`, `original_rgb`, `aligned_gray`, `aligned_rgb`, `processed`, and per-channel adjustments. The `MainWindow` accesses image data exclusively through `self.svc`.

### 3.3 Circular Import Risk

**Risk:** `services/processor.py` imports from `core/`. `ui/handlers/` imports from both `services/` and `core/`. `ui/main_window.py` imports from `ui/handlers/`, `ui/widgets/`, and `services/`. No cycle here — the dependency graph is: `core ← services ← ui`.

**Mitigation:** Maintain strict one-way imports: `core` never imports from `services` or `ui`; `services` never imports from `ui`. The `TYPE_CHECKING` guard for `MainWindow` in handlers uses forward references only.

### 3.4 Autosave JSON Schema Compatibility

**Risk:** The autosave JSON schema stores `channel_paths`, slider values, and crop rect. Moving image arrays to `svc` doesn't affect the schema since it never stored arrays — only paths and slider values.

**Mitigation:** Schema stays identical:
```json
{
  "version": 1,
  "channels": { "red": { "path": "...", "brightness": 0, "contrast": 0, "intensity": 100 }, ... },
  "crop": { "x": 0, "y": 0, "width": 100, "height": 100 }
}
```
`channel_paths` remains on `AppState` (or could move to `svc`). Slider values are read from Qt controllers. Crop rect is read from the viewer widget. No change.

### 3.5 `channel_controller.py:_set_preview` Walks the Widget Tree for Crop Rect

**Risk:** `ChannelController._set_preview()` (line 300-313) walks up the parent widget tree with `parent.viewer.get_saved_crop_rect()` to apply on-the-fly cropping. This returns a `QRect`. Since `channel_controller.py` lives under `ui/widgets/` (Qt territory), this is acceptable.

**Mitigation:** No change needed — this code stays in the Qt layer. It uses `QRect` internally for a purely UI concern (preview thumbnail cropping).

### 3.6 `main_window.py:toggle_crop_mode` Creates Default QRect from Image Shape

**Risk:** Lines 392-402 access `self.state.processed[i].shape` to compute a default crop rectangle. After the refactor, `processed` arrays live in `svc`.

**Mitigation:** Add a `svc.get_image_dimensions() -> tuple[int, int] | None` method or use `svc.get_channel(i)` to inspect shape. The crop rect construction (`QRect(x, y, w, h)`) stays in `main_window.py` since it's UI code.

### 3.7 `main_window.py:update_save_button_state` Checks `state.aligned` and `state.processed`

**Risk:** Lines 791-797 check `any(img is not None for img in self.state.aligned)` and similar for `processed`. After the refactor, these arrays live in `svc`.

**Mitigation:** Add `svc.has_aligned_channels() -> bool` and `svc.has_processed_channels() -> bool` (or a single `svc.is_ready_to_export() -> bool`).

### 3.8 Preset Thumbnail Saving Uses `QPixmap`

**Risk:** `presets.py:save_preset` (line 71-80) saves a thumbnail from `main_window.viewer.photo.pixmap()`. This is pure Qt and stays in the UI layer.

**Mitigation:** No change needed.

## 4. Commit Sequence

Each commit leaves the app in a fully working state with all CI checks passing.

### Commit 1: Create `src/services/` package with `ImageProcessorService`
- Create `src/services/__init__.py`
- Create `src/services/processor.py` with `ChannelAdjustments` dataclass and `ImageProcessorService` class
- Service imports only from `src/core/` (align, image_processing)
- All methods fully typed, docstrings for interrogate, GPL headers
- **App still works** — nothing uses the service yet; it's dead code that CI can lint

### Commit 2: Move `convert_to_qimage` from `core/` to new `src/ui/qt_utils.py`
- Create `src/ui/__init__.py` and `src/ui/qt_utils.py`
- Move `convert_to_qimage` function to `qt_utils.py`
- Remove `convert_to_qimage` and `QImage` import from `core/image_processing.py`
- Update the two existing callers (`handlers/display.py` imports from `ui.qt_utils` instead of `core.image_processing`)
- **App still works** — only import paths changed for `convert_to_qimage`

### Commit 3: Move `handlers/` under `src/ui/handlers/`
- `git mv src/handlers/ src/ui/handlers/`
- Update all imports in `main_window.py` from `.handlers.` → `.ui.handlers.`
- Update internal cross-imports within handlers (e.g., `from .display import` stays the same since they move together)
- **App still works** — pure file-move with import path updates

### Commit 4: Move `widgets/` under `src/ui/widgets/`
- `git mv src/widgets/ src/ui/widgets/`
- Update all imports in `main_window.py` from `.widgets.` → `.ui.widgets.`
- Update any cross-references between handlers and widgets
- **App still works** — pure file-move with import path updates

### Commit 5: Move `main_window.py`, `app_state.py`, `default_state.py` under `src/ui/`
- `git mv src/main_window.py src/ui/main_window.py`
- `git mv src/app_state.py src/ui/app_state.py`
- `git mv src/default_state.py src/ui/default_state.py`
- Update `src/main.py` to import from `.ui.main_window`
- Update all relative imports within the moved files (handlers now use `from ..app_state` instead of `from ...app_state`, etc.)
- Fix `app_state.py` relative import of `DefaultState`
- **App still works** — pure file-move with import path updates

### Commit 6: Wire `ImageProcessorService` into `MainWindow` and slim down handlers
- Add `self.svc = ImageProcessorService()` to `MainWindow.__init__`
- Refactor `handlers/channels.py`:
  - `_process_channel_image` → delegates to `svc.load_channel_from_array(idx, rgb)`
  - `adjust_channel` → reads slider values, calls `svc.adjust_channel(idx, b, c, i)`
  - `update_channel_preview` → calls `svc.get_channel_preview(idx)`
- Refactor `handlers/display.py`:
  - `show_combined_image` → converts crop `QRect` to tuple, calls `svc.get_combined(crop, intensities)`
  - `show_single_channel_image` → converts crop `QRect` to tuple, calls `svc.get_channel(idx, crop)`
- Refactor `handlers/image_saving.py`:
  - `apply_crop` → accepts `tuple | None` instead of `QRect`
  - Call-sites convert `QRect` → tuple before calling
  - `save_image_with_dialog` reads aligned/aligned_rgb from `svc`
- Refactor `main_window.py`:
  - `toggle_crop_mode` — query `svc` for processed image shapes
  - `apply_crop` — keep crop rect logic in Qt, but use `svc.has_processed_channels()`
  - `update_save_button_state` — use `svc.is_ready_to_export()`
  - `_update_mode_from_state` — use `svc` to count loaded channels
- Strip image arrays from `AppState` (keep only `channel_paths` and UI-only fields)
- Update `autosave.py` to read image state from `svc` where needed
- **App still works** — functionally identical, but image state now lives in `svc`

### Commit 7: Final cleanup and CI verification
- Run `black` and `isort` on all files
- Run full CI suite locally: `interrogate`, `mypy`, `flake8`, `pylint`
- Fix any remaining lint issues (unused imports after moves, missing docstrings)
- Verify autosave round-trip (save → quit → relaunch → restore)
- Verify preset save/load still works
- Verify crop workflow still works
- Add any missing GPL headers

## Invariants (Claude must verify after every commit)
- [ ] `grep -r "PyQt5" src/core/ src/services/` returns empty
- [ ] `python src/main.py` launches without errors
- [ ] All CI checks pass locally