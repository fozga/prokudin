# Alignment Algorithm Robustness Test Campaign

## Prokudin — `src/core/align.py`

---

## Document Purpose and Audience

This document defines a complete, multi-layer test campaign for the channel-alignment subsystem of the Prokudin application (`src/core/align.py`). It is written to be directly actionable: a developer or an automated test-generation agent should be able to read this document and produce concrete `pytest` test modules, fixtures, and assertions without needing additional design decisions.

The campaign is triggered by three linked GitHub issues:

- **Feature request** — the current alignment pipeline has no degrees-of-freedom control, no sanity checking of extreme transformations, no multi-method fallback, and no status-bar reporting of what alignment actually did.
- **Issue "6a" (Infrastructure)** — no synthetic fixture layer exists to construct images with a known ground-truth transform, decompose affine matrices, or assert closeness between aligned channels.
- **Issue "Correctness"** — no tests verify that the *recovered* transform matches the *known* transform within tolerance; existing tests only check that the function does not crash.
- **Issue "Adversarial / failure modes"** — no tests exercise `AlignmentError`, degenerate geometry, featureless images, or partial-failure isolation between channels.

This document assumes that **some of the required functionality does not yet exist** (degrees-of-freedom selection, sanity-check thresholds, multi-method fallback, status-bar reporting). Test cases for these areas are written as **target-state specifications** — they define the expected behavior of the *improved* system and will fail against the current implementation until the corresponding feature/bugfix work lands. This is intentional and should not be treated as a defect in the test design.

---

## 1. Testing Strategy

### 1.1 Guiding Principles

1. **Ground truth first.** Every correctness test must be built around a synthetic image with a precisely known applied transformation. No test may assert correctness against an image whose "correct" alignment is itself unknown or subjective.
2. **Isolate the geometry from the algorithm.** Test infrastructure (fixture generation, matrix decomposition, closeness assertions) must be implemented and unit-tested *before* any alignment-correctness test is written, because every correctness and robustness test depends on it.
3. **Fail loudly, never silently.** A wrong alignment that is silently accepted into the composite image is treated as a more severe defect than a raised exception. Test design must actively try to make the algorithm fail in a *detectable* way (raise `AlignmentError` or flag low confidence) rather than merely avoiding crashes.
4. **Test the full spectrum from clean to adversarial.** Categories range from trivial (identity transform) to pathological (featureless images, degenerate keypoint geometry, extreme shifts). Each category has an explicitly documented expected outcome — success within tolerance, or a specific, well-formed error.
5. **Separate "what changed" from "how well it matches."** Every test case distinguishes between *parameter recovery* (does the decomposed matrix match the ground truth transform parameters within tolerance) and *pixel fidelity* (does the warped image actually align visually with the reference channel, measured via MAE/SSIM). Both must be checked; passing one without the other indicates a partial bug (e.g., correct parameters but wrong application order).
6. **Regression safety net.** Once the multi-method fallback and DOF-restriction features are implemented, this suite doubles as the primary regression gate — any future change to `align.py` must keep all correctness and adversarial tests green.
7. **Deterministic and CI-friendly.** All synthetic fixtures must be deterministic (seeded RNG) so that CI runs are reproducible and failures are not flaky.

### 1.2 Test Pyramid for Alignment

```
                    ┌─────────────────────────┐
                    │   System / E2E (few)    │   Full workflow: load 3 real-ish
                    │                         │   channels → align → save
                    └─────────────────────────┘
                  ┌───────────────────────────────┐
                  │   Integration (moderate)      │   align_images() + status bar
                  │                                │   + DOF config + fallback chain
                  └───────────────────────────────┘
              ┌───────────────────────────────────────┐
              │        Unit / Correctness (many)      │   Parameter recovery,
              │                                        │   pixel fidelity, DOF
              │                                        │   restriction, thresholds
              └───────────────────────────────────────┘
          ┌───────────────────────────────────────────────┐
          │   Adversarial / Failure Mode (many)            │   AlignmentError paths,
          │                                                  │   degenerate geometry,
          │                                                  │   featureless input
          └───────────────────────────────────────────────┘
      ┌───────────────────────────────────────────────────────┐
      │        Infrastructure / Fixture Unit Tests (few)       │   Fixtures themselves
      │                                                          │   must be verified
      └───────────────────────────────────────────────────────┘
```

Infrastructure tests sit at the foundation because every other layer depends on their correctness. If `make_transformed_channel` or `decompose_affine_matrix` has a bug, all correctness tests built on top of it are meaningless.

### 1.3 Scope Boundaries

**In scope:**
- `align_images()` and all code paths reachable from it in `src/core/align.py`
- `AlignmentError` and its usage contract
- Proposed new features: DOF selection, sanity-check thresholds, multi-method fallback, status-bar summary reporting
- Supporting fixture/helper infrastructure needed to write the above tests

**Out of scope (covered elsewhere / referenced only):**
- UI-level status bar rendering (covered by UI/handler tests, not this document)
- Crop, presets, autosave — unaffected by alignment internals
- Performance/timing benchmarks beyond basic sanity bounds (tracked separately under non-functional requirements)

---

## 2. Test Areas Overview

| # | Area | Goal | Depends on |
|---|------|------|-------------|
| A | Fixture & Helper Infrastructure | Provide reliable ground-truth image generation and comparison primitives | — |
| B | Parameter Recovery Correctness | Verify recovered transform matches known ground truth within tolerance | A |
| C | Pixel Fidelity Correctness | Verify the *applied* warp visually aligns channels, not just the matrix | A, B |
| D | Output Invariants | Verify value range, dtype, shape, and reference-channel immutability | A |
| E | Adversarial / Failure Modes | Verify `AlignmentError` is raised correctly and informatively on bad input | A |
| F | Degrees-of-Freedom (DOF) Restriction | Verify user-selectable DOF modes constrain the transform as specified | A, B |
| G | Extreme-Transformation Sanity Check | Verify out-of-bounds transforms are rejected or flagged, not silently applied | A, B |
| H | Multi-Method Fallback Pipeline | Verify cascade behavior across primary/secondary/tertiary methods and final no-op fallback | A, E, G |
| I | Status/Confidence Reporting | Verify the reported method, parameters, and confidence/warning match what was actually computed | H |
| J | Partial-Failure Isolation | Verify a failure on one channel does not corrupt or block another | A, E |
| K | Integration / Full-Pipeline Regression | Verify the end-to-end `align_images()` contract across representative real-world-like scenarios | B–J |

Each area is expanded into detailed test cases in Sections 4–14.

---

## 3. Test Infrastructure Design (Area A)

This section specifies the fixtures and helpers required by Issue 6a. All correctness, adversarial, and integration tests in this document assume these exist and behave as specified here. If the current repository lacks any of them, they must be implemented as a prerequisite deliverable of this campaign — they are test code, not production code, and can live under `tests/fixtures/` or `tests/conftest.py`.

### 3.1 `make_transformed_channel(base_image, tx, ty, angle_deg, scale, border_value=0)`

**Purpose:** Produce a synthetic "warped" channel image by applying a *known* affine transform to a base image, together with the exact ground-truth transformation matrix used.

**Signature contract:**
```python
def make_transformed_channel(
    base_image: np.ndarray,
    tx: float = 0.0,
    ty: float = 0.0,
    angle_deg: float = 0.0,
    scale: float = 1.0,
    border_value: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns (warped_image, ground_truth_matrix) where ground_truth_matrix
    is the 2x3 affine matrix used to produce warped_image from base_image,
    expressed in the same convention that align_images() is expected to
    recover (rotation/scale about image center, then translation).
    """
```

**Behavioral requirements:**
- Rotation and scale shall be applied about the image center (not the origin), matching the convention used by `cv2.getRotationMatrix2D` and expected by `estimateAffinePartial2D`.
- The function must compose the matrix analytically (not by chaining multiple `warpAffine` calls) to avoid compounding interpolation error, then apply a single `cv2.warpAffine` call with the composed matrix.
- Border pixels introduced by the transform must be filled with `border_value` (default black/0), matching the alignment pipeline's own border-filling contract.
- Must support pure translation, pure rotation, pure scale, and arbitrary combinations, each independently parameterizable and independently settable to zero/identity.
- Must accept and correctly transform images of arbitrary size, including non-square images, without introducing off-by-one center errors.

**Infrastructure test cases (IT):**

| ID | Description | Assertion |
|----|--------------|-----------|
| IT-A1 | Identity transform (tx=0, ty=0, angle=0, scale=1) | Output image is pixel-identical to input; matrix equals identity `[[1,0,0],[0,1,0]]` |
| IT-A2 | Pure translation (tx=10, ty=-5) | Output image shifted by exactly (10,-5) in the flat interior region (verified via cross-correlation peak); matrix translation components equal (10,-5) within floating point tolerance |
| IT-A3 | Pure rotation (angle=5°) around center | Center pixel unchanged (within 1px); corner pixels displaced consistently with a 5° rotation about center |
| IT-A4 | Pure scale (scale=1.1) | Image content scaled up around center; matrix diagonal terms reflect scale ×cos/sin decomposition consistent with 1.1 |
| IT-A5 | Combined transform reproducibility | Calling the function twice with identical parameters and the same base image produces bit-identical output (determinism check) |
| IT-A6 | Non-square image support | Base image 300×150; transform applied without exception; output shape matches input shape |

### 3.2 `decompose_affine_matrix(matrix)`

**Purpose:** Decompose a 2×3 affine matrix into `(tx, ty, angle_deg, scale)` for human-readable comparison against ground truth, assuming a *partial affine* model (rotation + uniform scale + translation, no shear).

**Signature contract:**
```python
def decompose_affine_matrix(matrix: np.ndarray) -> tuple[float, float, float, float]:
    """
    Returns (tx, ty, angle_deg, scale) decomposed from a 2x3 partial-affine
    matrix of the form:
        [[ s*cos(a), -s*sin(a), tx],
         [ s*sin(a),  s*cos(a), ty]]
    angle_deg is normalized to (-180, 180].
    """
```

**Behavioral requirements:**
- Must correctly recover `scale = sqrt(m00^2 + m10^2)`.
- Must correctly recover `angle_deg = degrees(atan2(m10, m00))`.
- Must correctly recover `tx = m02`, `ty = m12` directly.
- Must handle negative scale / degenerate matrices without raising (should return `NaN` or raise a clearly-documented exception — pick one and test it explicitly, see IT-A9).

**Infrastructure test cases (IT):**

| ID | Description | Assertion |
|----|--------------|-----------|
| IT-A7 | Decompose identity matrix | Returns (0, 0, 0, 1.0) exactly |
| IT-A8 | Round-trip: construct known matrix analytically for (tx=12, ty=-7, angle=8°, scale=1.03), decompose it | Recovered tuple matches input within 1e-6 absolute tolerance |
| IT-A9 | Decompose a degenerate all-zero matrix | Documented behavior occurs (either raises `ValueError` with descriptive message, or returns scale=0 with angle=NaN) — pick and assert one contract |
| IT-A10 | Angle normalization at boundary (angle_deg=180 vs -180) | Returned angle is normalized consistently to the documented range on both sides of the boundary |

### 3.3 Feature-Rich Base Image Fixtures

Extend the existing checkerboard+noise fixture with the following **parametrized variants**, each returned as an `np.ndarray` of dtype `uint8`:

| Fixture name | Size | Content | Purpose |
|--------------|------|---------|---------|
| `base_image_large` | 512×512 | Checkerboard (32px squares) + Gaussian noise (σ=5) + a handful of distinct circular blobs at asymmetric positions | Sub-pixel accuracy testing; enough unique local features for robust ORB matching |
| `base_image_small` | 64×64 | Checkerboard (8px squares) + light noise | Boundary/edge-case testing where ORB has very few candidate keypoints |
| `base_image_flat` | 256×256 | Uniform grey value (128) with **zero** texture | Featureless failure-mode testing — must guarantee zero usable keypoints |
| `base_image_repetitive` | 256×256 | Regular grid pattern (e.g., brick-wall or evenly spaced dots), fully periodic, no unique landmarks | Ambiguous-match / aliasing failure-mode testing |
| `base_image_sparse_features` | 256×256 | Mostly flat with only 3–4 small distinguishing marks near one corner | Testing the boundary between "enough" and "not enough" matches (near the 50-match threshold) |

**Infrastructure test cases (IT):**

| ID | Description | Assertion |
|----|--------------|-----------|
| IT-A11 | `base_image_flat` has zero ORB keypoints | `cv2.ORB_create().detectAndCompute(base_image_flat, None)` returns an empty keypoint list |
| IT-A12 | `base_image_large` has ≥ 500 ORB keypoints | Guarantees the "rich features" fixture actually is rich; prevents silent fixture regressions |
| IT-A13 | `base_image_repetitive` produces high symmetric self-similarity | Autocorrelation of the image with itself shifted by one period exceeds a defined similarity threshold, confirming the periodicity property used for ambiguous-match tests |

### 3.4 `assert_channels_close(aligned, reference, max_mae, region=None)`

**Purpose:** Centralize pixel-fidelity comparison logic with clear failure diagnostics.

**Signature contract:**
```python
def assert_channels_close(
    aligned: np.ndarray,
    reference: np.ndarray,
    max_mae: float,
    region: tuple[slice, slice] | None = None,
) -> None:
    """
    Computes Mean Absolute Error between `aligned` and `reference`
    (optionally restricted to `region`, to exclude border-fill artifacts),
    and raises AssertionError with the actual MAE, max_mae threshold, and
    a saved diff-image path if the comparison fails.
    """
```

**Behavioral requirements:**
- Must default to excluding a configurable border margin (e.g., 5% of image width/height) from the MAE computation, since warped border regions are filled with black and would artificially inflate error near edges.
- Must raise with a message that includes: computed MAE, threshold used, image shapes, and (optionally) write a diff heatmap PNG to a temp directory referenced in the failure message for manual inspection.
- Must support an optional `region` parameter to allow scoping the comparison to the guaranteed-content region only (useful for extreme-shift tests where much of the image is legitimately black).

**Infrastructure test cases (IT):**

| ID | Description | Assertion |
|----|--------------|-----------|
| IT-A14 | Two identical images | `assert_channels_close` passes with MAE = 0 |
| IT-A15 | Two images differing by a small deterministic offset | Passes when `max_mae` is set above the known deterministic offset, fails when set below it |
| IT-A16 | Border-exclusion behavior | An image pair identical except in the outer 5% border passes when border exclusion is active, fails when it is disabled |

---

## 4. Parameter Recovery Correctness (Area B)

**Objective:** For each canonical transform type, verify that `align_images()` recovers a transformation matrix whose decomposed parameters match the known ground truth within defined tolerances.

**Common test structure:**
1. Take `base_image_large` as the ground-truth R (reference) channel.
2. Apply a known transform via `make_transformed_channel` to produce synthetic G and/or B channels.
3. Call `align_images(r, g, b)` (or the actual function signature).
4. Decompose the returned per-channel transformation matrices via `decompose_affine_matrix`.
5. Compare decomposed parameters against the *inverse* of the applied ground-truth transform (since alignment recovers the transform mapping the warped channel back onto the reference) within tolerance.

**Tolerances (baseline, to be tuned once initial runs establish empirical variance):**

| Parameter | Tolerance |
|-----------|-----------|
| Translation (tx, ty) | ± 2 px |
| Rotation angle | ± 0.3° (small angles), ± 0.5° (rotation ≥ 2°, due to apparent-translation coupling) |
| Scale | ± 0.02 |

### 4.1 Translation-Only Tests

| ID | Ground truth applied | Channels affected | Expected recovered params | Notes |
|----|----------------------|--------------------|----------------------------|-------|
| B-T1 | tx=+10px, ty=0 | G only | tx≈-10±2, ty≈0±2, angle≈0±0.3°, scale≈1±0.02 | Positive-X direction |
| B-T2 | tx=-10px, ty=0 | G only | tx≈+10±2, ty≈0±2, angle≈0±0.3°, scale≈1±0.02 | Negative-X direction |
| B-T3 | tx=0, ty=+10px | G only | tx≈0±2, ty≈-10±2, angle≈0±0.3°, scale≈1±0.02 | Positive-Y direction |
| B-T4 | tx=0, ty=-10px | G only | tx≈0±2, ty≈+10±2, angle≈0±0.3°, scale≈1±0.02 | Negative-Y direction |
| B-T5 | tx=+8px, ty=+8px | G only | tx≈-8±2, ty≈-8±2 | Diagonal shift |
| B-T6 | tx=+10px, ty=+5px | Both G and B (independently, different magnitudes for B: tx=-6, ty=+3) | Each channel recovers its own independent transform correctly | Confirms channels are aligned independently, not coupled |
| B-T7 | tx=+1px, ty=+1px | G only | Recovery within tolerance | Sub-pixel-scale minimal translation; establishes lower sensitivity bound |

### 4.2 Rotation-Only Tests

| ID | Ground truth applied | Expected recovered params | Notes |
|----|----------------------|----------------------------|-------|
| B-R1 | angle=+2° | angle≈-2°±0.5°, scale≈1±0.02, |tx|,|ty| ≤ 3px (apparent translation from off-center rotation) | Small positive rotation |
| B-R2 | angle=-2° | angle≈+2°±0.5° | Small negative rotation |
| B-R3 | angle=+0.5° | angle≈-0.5°±0.3° | Very small angle — lower sensitivity bound |
| B-R4 | angle=+4.5° | angle≈-4.5°±0.5° | Near the eventual sanity-check boundary (see Area G) but still valid |
| B-R5 | angle=+2°, applied to both G and B independently at different angles (G: +2°, B: -1.5°) | Each channel recovers its own angle independently | Cross-channel independence check |

### 4.3 Scale-Only Tests

| ID | Ground truth applied | Expected recovered params | Notes |
|----|----------------------|----------------------------|-------|
| B-S1 | scale=0.95 | scale≈1.0526±0.02 (inverse), tx/ty≈0±2, angle≈0±0.3° | Slight shrink |
| B-S2 | scale=1.05 | scale≈0.9524±0.02 (inverse) | Slight growth |
| B-S3 | scale=0.98 | scale recovered within tolerance | Near-identity scale, lower sensitivity bound |
| B-S4 | scale=1.15 | scale recovered within tolerance, but flagged as approaching sanity-check boundary once Area G is implemented | Documents interaction between B and G test areas |

### 4.4 Combined Transform Tests

| ID | Ground truth applied | Expected recovered params | Notes |
|----|----------------------|----------------------------|-------|
| B-C1 | tx=+8, ty=-6, angle=+1.5°, scale=0.98 | All four components recovered within their respective tolerances (inverse-transformed) | Primary "realistic" combined case |
| B-C2 | tx=-5, ty=+12, angle=-3°, scale=1.03 | All four components recovered within tolerance | Different sign combination |
| B-C3 | G: tx=+8,ty=-6,angle=+1.5°,scale=0.98; B: tx=-3,ty=+4,angle=-1°,scale=1.01 | Each channel independently recovers its own combined transform | Realistic dual-channel misalignment scenario mirroring real ARW captures |
| B-C4 | Repeat B-C1 with `base_image_small` (64×64) instead of large | Recovery within *relaxed* tolerance (±4px, ±1°, ±0.05 scale) documented explicitly as the small-image tolerance profile | Establishes expected accuracy degradation on small images |

### 4.5 Pixel Fidelity Cross-Checks (Area C, paired with each B-case)

For every test case in 4.1–4.4, in addition to parameter-recovery assertions, add:

| ID pattern | Assertion |
|------------|-----------|
| `<B-ID>-fidelity` | After alignment, `assert_channels_close(aligned_gray[channel_idx], reference_gray, max_mae=5.0, region=interior_region)` passes, confirming the warp was physically applied and correct — not just numerically computed. |
| `<B-ID>-range` | All pixel values in `aligned_gray[channel_idx]` and `aligned_rgb[channel_idx]` lie within [0, 255] inclusive; dtype matches the documented contract (e.g., `uint8`). |
| `<B-ID>-red-unchanged` | `np.array_equal(aligned_gray[0], grayscale_images[0])` and `np.array_equal(aligned_rgb[0], rgb_images[0])` — the reference channel is never mutated, regardless of transform applied to G/B. |

---

## 5. Output Invariants (Area D)

These are cross-cutting invariants that must hold for **every** successful alignment call, independent of the specific transform. They should be implemented as a shared assertion helper invoked at the end of every Area B/C/F/G/H test, plus a small number of dedicated tests below.

| ID | Description | Assertion |
|----|--------------|-----------|
| D-1 | Output dimensions match reference | `aligned_gray[i].shape == grayscale_images[0].shape` for all `i` |
| D-2 | Output dtype consistency | All output arrays have the same dtype as input arrays (no unintended float64 promotion left unconverted) |
| D-3 | No NaN/Inf in output | `np.isfinite(aligned_gray[i]).all()` for all channels |
| D-4 | RGB and grayscale transforms are consistent | The same transformation matrix, when applied independently to the RGB and grayscale representations of a channel, produces geometrically consistent results (cross-correlation peak between the two aligned outputs, converted to same colorspace, exceeds a high similarity threshold) |
| D-5 | Idempotency of already-aligned input | Running `align_images()` a second time on already-aligned output (which should now have near-zero relative transform) recovers a near-identity transform (tx,ty≈0, angle≈0, scale≈1) within tight tolerance |
| D-6 | Border fill value | Pixels in regions exposed by the warp (previously outside original image bounds) are exactly 0 (black), not interpolated garbage or arbitrary values |

---

## 6. Adversarial / Failure Mode Tests (Area E)

**Objective:** Every input that *should* fail must fail cleanly via `AlignmentError` with an informative message, never via an unhandled exception, a silent wrong answer, or a hang.

### 6.1 Featureless and Insufficient-Feature Inputs

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| E-1 | Three copies of `base_image_flat` (uniform grey) as R, G, B | `AlignmentError` raised. Message should indicate zero or near-zero keypoints/matches found. |
| E-2 | R = `base_image_large`, G = `base_image_flat`, B = `base_image_large` (mixed) | `AlignmentError` raised specifically for channel G; message identifies channel index 1 |
| E-3 | Constructed image where ORB finds keypoints but cross-checked matches < 50 (using `base_image_sparse_features` with heavy transform) | `AlignmentError` raised with message including the actual match count (e.g., "23 matches found, minimum 50 required") |
| E-4 | Match count exactly at threshold boundary (49 vs 50 vs 51) — constructed via controlled sparse feature density | Verify the boundary condition explicitly: 49 → error, 50 → behavior is explicitly documented (inclusive or exclusive) and tested, 51 → success |

### 6.2 Extreme Geometric Inputs

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| E-5 | Translation of 130px applied to a 256×256 `base_image_large`-equivalent (>50% of image width) | Documented expected outcome: EITHER successful alignment within relaxed tolerance (if ORB matches survive the shift) OR clean `AlignmentError`. The test must assert exactly one of these two behaviors and treat the other as a failure — pin down and document the actual contract. |
| E-6 | Translation of 200px on a 256×256 image (>75% of width, minimal remaining overlap) | `AlignmentError` expected (insufficient overlap to find matches); if alignment unexpectedly succeeds, treat this as a discovered edge case requiring explicit documentation, not a silent pass |
| E-7 | Rotation of 90° applied | Given the eventual sanity-check feature (Area G), this should be *rejected* by the threshold check even if ORB could technically find a transform; document interaction between E-area and G-area tests |
| E-8 | Scale factor of 0.1 (extreme shrink) or 10.0 (extreme growth) | `AlignmentError` or sanity-check rejection (post Area G implementation); pre-Area-G baseline behavior must still be captured as a documented "known gap" test marked `xfail` with a reference to the feature issue |

### 6.3 Very Small Images

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| E-9 | `base_image_small` (64×64), feature-rich, small known transform (tx=3,ty=2,angle=1°) | Either successful alignment within relaxed tolerance, or clean `AlignmentError` — no unhandled OpenCV internal exceptions (e.g., assertion failures from `cv2`) |
| E-10 | `base_image_small` at 64×64 with an extreme transform (tx=40px, >60% of width) | Clean `AlignmentError`, not a crash |
| E-11 | Extremely small image, 16×16 | Documented minimum-size behavior: either a pre-flight size check raising a descriptive `AlignmentError`/`ValueError` before attempting ORB, or a graceful `AlignmentError` from ORB itself. No OpenCV low-level crash permitted. |

### 6.4 Repetitive / Ambiguous Texture

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| E-12 | Three `base_image_repetitive` copies with a known small transform applied to G/B | No crash. Documented outcome (success within tolerance, OR `AlignmentError` due to ambiguous matches, OR success with *wrong* but plausible transform recovered — if the latter, this must be explicitly flagged as a known limitation with a regression test asserting the current (possibly wrong) behavior stays stable until fixed) |
| E-13 | `base_image_repetitive` combined with a translation that is an exact multiple of the pattern period | Explicitly documents the periodicity-aliasing failure mode: recovered translation may plausibly be `true_tx mod period` rather than `true_tx`. Test asserts current documented behavior. |

### 6.5 Degenerate Matrix Estimation

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| E-14 | Construct matched keypoints that are synthetically forced to be exactly collinear (e.g., by mocking the matcher to return only collinear point pairs) so `cv2.estimateAffinePartial2D` returns `None` | `AlignmentError` raised with a message identifying the affected channel index and indicating matrix-estimation failure specifically (distinct message from "insufficient matches") |
| E-15 | Matched keypoints with near-zero spatial spread (all matches clustered in a tiny image region) | Either successful alignment (if RANSAC still resolves a valid matrix) or `AlignmentError`; both outcomes must avoid raising an uncaught `cv2.error` |

### 6.6 Error Message Content Quality

| ID | Description | Assertion |
|----|--------------|-----------|
| E-16 | For every `AlignmentError` raised across E-1 through E-15 | `str(exception)` is non-empty |
| E-17 | For match-count failures (E-1, E-3, E-4) | Exception message contains the actual numeric match count |
| E-18 | For channel-specific failures (E-2, E-14) | Exception message contains the channel index or name (e.g., "channel 1", "G channel", "VIS") |
| E-19 | For matrix-estimation failures (E-14) | Exception message text is distinguishable from insufficient-match message text (i.e., a caller/log reader can tell which failure mode occurred without inspecting stack traces) |

---

## 7. Partial-Failure Isolation (Area J)

**Objective:** A failure while processing one channel must not corrupt, block, or silently propagate incorrect data into another channel's processing.

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| J-1 | R valid, G triggers `AlignmentError` (e.g., `base_image_flat`), B valid with a known transform | If the implementation processes channels sequentially and raises on first failure: assert that no partial/corrupted state (e.g., a half-written `aligned_gray[1]`) is exposed — either the whole call raises before returning anything, or channel B's independent result is still computed. This exact contract must be pinned down and asserted explicitly, not assumed. |
| J-2 | R valid, G valid with known transform, B triggers `AlignmentError` | R channel output is verified unchanged (`np.array_equal` against original) even though the overall call raised |
| J-3 | Simulate the "future" multi-method fallback (Area H) with per-channel failure: G fails method A but succeeds via fallback method B, while B channel succeeds on method A directly | Both channels produce correct, independent results; success of one channel's fallback does not alter the primary-method result of the other channel |
| J-4 | Repeated calls: first call fails on G (raises `AlignmentError`), second call on the same object/state with a corrected G channel succeeds | Confirms no cached/stale failure state leaks between calls (relevant given the reload-triggers-realignment behavior documented in the functional requirements) |

---

## 8. Degrees-of-Freedom (DOF) Restriction (Area F) — Target-State Feature

**Objective:** Verify the requested DOF-selection feature once implemented. These tests define the acceptance criteria for that feature.

**Assumed API (to be finalized during implementation):**
```python
align_images(r, g, b, dof_mode: DOFMode = DOFMode.TRANSLATION_ROTATION_SCALE)
```
with `DOFMode` enum values: `TRANSLATION_ONLY`, `TRANSLATION_ROTATION`, `TRANSLATION_ROTATION_SCALE`, `FULL_AFFINE`.

| ID | DOF mode under test | Setup | Expected outcome |
|----|----------------------|-------|-------------------|
| F-1 | `TRANSLATION_ONLY` | Apply a combined transform (tx=10, ty=5, angle=3°, scale=1.05) to G | Recovered matrix has angle component forced to 0 and scale forced to 1, regardless of the true underlying rotation/scale; only tx/ty are estimated. Recovered tx/ty will *not* perfectly match ground truth (since rotation/scale are unmodeled) but should be the best-fit translation. |
| F-2 | `TRANSLATION_ROTATION` | Same combined transform as F-1 | Recovered matrix has scale forced to 1.0; tx, ty, angle are estimated (with residual error expected due to unmodeled scale) |
| F-3 | `TRANSLATION_ROTATION_SCALE` | Same combined transform as F-1 | Recovered matrix matches full ground truth within the Area B tolerances (this is the existing default `estimateAffinePartial2D` behavior) |
| F-4 | `FULL_AFFINE` | Apply a transform including shear (constructed directly as a general affine matrix, not expressible via `make_transformed_channel`'s rotation/scale-only parameterization — requires a shear-supporting fixture variant) | Recovered matrix includes non-trivial shear terms matching ground truth within tolerance; verify `TRANSLATION_ROTATION_SCALE` mode on the *same* sheared input produces a visibly worse fit (higher MAE) than `FULL_AFFINE` mode, proving the DOF restriction is actually being enforced and not ignored |
| F-5 | Invalid/unsupported DOF mode value passed | Raises a clear `ValueError`/`TypeError` at the API boundary rather than silently defaulting or crashing deep in OpenCV |
| F-6 | DOF mode restricts estimation but confidence/quality metric still reflects true residual error | When `TRANSLATION_ONLY` is used on data with real rotation, the reported confidence/quality indicator (Area I) is lower than when `TRANSLATION_ROTATION_SCALE` is used on the same data — proving the confidence metric is sensitive to model mismatch, not just to match count |

---

## 9. Extreme-Transformation Sanity Check (Area G) — Target-State Feature

**Objective:** Verify that once a transform is estimated, it is checked against configurable sanity bounds before being accepted, and rejected/flagged if it exceeds them — directly addressing the reported bug of "one channel ends up drastically scaled down or rotated by an extreme angle."

**Assumed configurable bounds (defaults per the feature request):**
- Rotation: reject if `|angle_deg| > 5.0`
- Scale: reject if `scale < 0.8 or scale > 1.2`
- (Recommended addition) Translation: reject if `|tx| > 0.5 * width` or `|ty| > 0.5 * height`

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| G-1 | Ground truth angle = 4.9° (just inside bound) | Transform accepted; recovered angle within Area B tolerance |
| G-2 | Ground truth angle = 5.1° (just outside bound) | Transform rejected by the sanity check — either raises `AlignmentError` with a message identifying "rotation out of bounds: 5.1° > 5.0° limit", or (per the fallback design in Area H) triggers fallback to method B, depending on final design decision. Both are acceptable *if explicitly documented*; the test must assert the actual chosen contract. |
| G-3 | Ground truth scale = 0.81 (just inside bound) | Transform accepted |
| G-4 | Ground truth scale = 0.75 (just outside bound, too small) | Transform rejected / triggers fallback, per G-2's documented contract |
| G-5 | Ground truth scale = 1.25 (just outside bound, too large) | Transform rejected / triggers fallback |
| G-6 | **Regression case directly reproducing the reported bug**: construct a scenario where ORB matching (due to ambiguous/repetitive content, e.g., `base_image_repetitive`) plausibly returns a wildly wrong matrix with scale=0.15 or angle=47° | The sanity check must catch and reject this specific pathological case — this is the direct regression test for the originating bug report and should be flagged as **P0 / must-pass** before this feature is considered complete |
| G-7 | Configurable bounds — construct the same near-boundary case (angle=6°) under two different configured limits (limit=5° → reject; limit=10° → accept) | Confirms bounds are actually configurable/parameterized, not hardcoded |
| G-8 | Combined transform where rotation is within bounds but scale is not (angle=2°, scale=1.5) | Rejected due to scale violation alone; message specifically cites scale, not rotation |
| G-9 | Sanity check applied independently per channel | G channel within bounds, B channel outside bounds → only B is rejected/flagged; G's valid result is unaffected | Directly reuses Area J isolation principle in the context of the new sanity-check feature |

---

## 10. Multi-Method Fallback Pipeline (Area H) — Target-State Feature

**Objective:** Verify the cascaded fallback strategy: primary method (feature-based/ORB) → secondary method (e.g., phase correlation) → tertiary method → final no-alignment overlay fallback, with each stage triggered only when the prior stage fails or fails its sanity check.

**Assumed API surface:**
```python
class AlignmentMethod(Enum):
    FEATURE_BASED = "orb"
    PHASE_CORRELATION = "phase_correlation"
    # extensible for future methods
    NONE = "no_alignment"

class AlignmentResult:
    matrix: np.ndarray
    method_used: AlignmentMethod
    confidence: float  # 0.0-1.0 or similar
    warnings: list[str]
```

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| H-1 | Clean, feature-rich input, moderate transform (well within sanity bounds) | `method_used == FEATURE_BASED`; no fallback triggered; confidence high |
| H-2 | Input where ORB fails outright (featureless, `base_image_flat`) | Cascade proceeds to `PHASE_CORRELATION`; if phase correlation succeeds within its own sanity bounds, `method_used == PHASE_CORRELATION` and a warning is present noting the fallback occurred |
| H-3 | Input where ORB succeeds but produces an out-of-bounds transform (per Area G, e.g., G-6's pathological case) | Cascade proceeds to the next method rather than accepting the bad ORB result; `method_used` reflects whichever method's result was ultimately accepted, and `warnings` explicitly states that the primary method's result was rejected and why |
| H-4 | Input where **both** ORB and phase correlation fail or produce out-of-bounds results | Cascade falls through to the tertiary method if one is implemented, or ultimately to `NONE` (unmodified overlay); `method_used == NONE`; `warnings` clearly states that no valid alignment could be found and the channels are being overlaid unmodified |
| H-5 | Full-fallback (`NONE`) case output invariants | When `method_used == NONE`, the returned matrix must be the identity matrix (no transform applied), and the resulting aligned arrays must equal the original unmodified input arrays exactly |
| H-6 | Fallback does not mask channel-independent success | G channel needs fallback to `PHASE_CORRELATION`, B channel succeeds on `FEATURE_BASED` directly | Each channel's `method_used` is reported and resolved independently; one channel's fallback path must not force the other channel onto the same path |
| H-7 | Cascade ordering is respected even when a later method would have produced a "better" (lower MAE) result | If `FEATURE_BASED` succeeds and passes the sanity check, it is used even if, hypothetically, `PHASE_CORRELATION` would have been marginally more accurate — the cascade should not run later methods once an earlier one is accepted (unless explicitly configured to always run all methods and pick the best; if that mode exists, test it as a separate configuration case) |
| H-8 | Confidence score ordering | Across H-1 through H-4, confidence should generally decrease along the fallback chain (`FEATURE_BASED` success > `PHASE_CORRELATION` fallback success > `NONE`), providing a monotonicity sanity check on the confidence metric itself |
| H-9 | Astrophotography-inspired quality-metric acceptance test | Borrowing from star-stacking software design: construct a case with a *marginal* quality primary result (e.g., match count just above the 50 threshold, transform just inside sanity bounds) and verify the system does not treat "technically passed the hard thresholds" as equivalent to "high confidence" — the confidence score for marginal cases should be measurably lower than for clean cases (H-1), even though both are "accepted" |

---

## 11. Status / Confidence Reporting (Area I) — Target-State Feature

**Objective:** Verify that the reported summary (destined for the status bar) accurately reflects what was actually computed — not a generic/static message.

Since UI rendering is out of scope, these tests target the **data contract** returned by the core alignment function (e.g., an `AlignmentResult` or equivalent structure/dict) that the UI layer would consume to build its status bar message.

| ID | Setup | Expected outcome |
|----|-------|-------------------|
| I-1 | Successful alignment via `FEATURE_BASED`, known transform (tx=10, ty=5, angle=2°, scale=1.02) applied to G | Result object reports `method_used=FEATURE_BASED` and numeric parameters for channel G matching the recovered (not ground-truth) values within Area B tolerance — i.e., the reported numbers must be the *actual* computed values, verified by cross-checking against `decompose_affine_matrix` applied independently to the same returned matrix |
| I-2 | Fallback scenario (H-2/H-3) | Result object's `warnings` list is non-empty and its content specifically names the fallback method used and the reason the primary method was rejected (not a generic "alignment may be inaccurate" string) |
| I-3 | Full no-alignment fallback (H-4/H-5) | Result object clearly flags this as the most severe case (e.g., `confidence == 0.0` or a dedicated `alignment_failed=True` flag), distinguishable programmatically from a low-but-nonzero-confidence success |
| I-4 | Per-channel reporting | For a 3-channel call where G uses `FEATURE_BASED` and B uses `PHASE_CORRELATION` fallback, the result structure reports method and parameters **per channel**, not a single aggregated value that would obscure which channel needed fallback |
| I-5 | Reported translation/rotation/scale units and sign convention | Explicitly documented and tested: translation reported in pixels (not normalized 0-1), rotation in degrees (not radians), and the sign convention (e.g., positive angle = counter-clockwise) is verified against a test case with an unambiguous, manually-verified expected sign |
| I-6 | Numeric formatting stability | Result parameters are plain Python floats (not numpy scalar types that could format unexpectedly in a UI string), avoiding a known class of "looks fine in code, renders oddly in UI" bugs |

---

## 12. Integration / Full-Pipeline Regression Tests (Area K)

**Objective:** Exercise `align_images()` as a whole, combining multiple areas together, to catch interaction bugs that isolated unit tests might miss.

| ID | Scenario | Assertion |
|----|----------|-----------|
| K-1 | "Golden path": three feature-rich channels, small realistic misalignment on both G and B independently, default DOF mode | Full success; per-channel parameters within tolerance; `method_used=FEATURE_BASED` for both; no warnings; output passes all Area D invariants |
| K-2 | "Bad channel" reload scenario | Simulate the documented reload-triggers-realignment behavior: first call with a bad G channel (`base_image_flat`) fails; caller reloads G with a valid feature-rich channel; second call succeeds fully, with R and B results unaffected/unchanged in content between calls |
| K-3 | "One good, one marginal, one bad" three-channel scenario | R valid, G marginal (near match-count threshold, succeeds with lower confidence), B triggers full fallback to `NONE` | Result object correctly attributes different outcomes to each of G and B, R is unaffected, and the overall call either raises with a clear multi-channel summary or returns a structure exposing all three outcomes (contract must be pinned and documented) |
| K-4 | Repeated realignment stability | Run `align_images()` three times in a row on the *same* unmodified input | All three runs produce bit-identical results (determinism is critical for the debounced-autosave and reload workflows already specified in the functional requirements) |
| K-5 | DOF mode + sanity check interaction | Use `TRANSLATION_ONLY` DOF mode on an input whose true transform includes a large rotation that would fail the sanity check under `TRANSLATION_ROTATION_SCALE` mode | Since `TRANSLATION_ONLY` never estimates rotation, the sanity check's rotation bound is inherently satisfied (rotation is fixed at 0); verify no spurious sanity-check rejection occurs purely because the *true* underlying data had a large rotation that the restricted DOF mode correctly ignores |
| K-6 | Full workflow smoke test with real-ish ARW-derived data (if sample ARW fixtures exist in the repo, e.g., under `tests/fixtures/samples/`) | Alignment completes successfully within a bounded time and produces a plausible confidence score; this is the closest proxy to real-world validation and should be run as part of the existing `FULL_WORKFLOW_TESTING` suite, cross-referenced here |

---

## 13. Test Data & Fixture Summary Table

| Fixture | Defined in | Used by areas |
|---------|-----------|----------------|
| `make_transformed_channel` | Area A (3.1) | B, C, D, F, G, H, I, K |
| `decompose_affine_matrix` | Area A (3.2) | B, F, G, I |
| `base_image_large` | Area A (3.3) | B, C, D, F, H, K |
| `base_image_small` | Area A (3.3) | E, K |
| `base_image_flat` | Area A (3.3) | E, H, J |
| `base_image_repetitive` | Area A (3.3) | E, G |
| `base_image_sparse_features` | Area A (3.3) | E |
| `assert_channels_close` | Area A (3.4) | C, D, G |

---

## 14. Traceability Matrix (Requirement → Test Area)

| Source requirement (from feature request / issues) | Test areas covering it |
|---|---|
| Degrees-of-freedom selection | F |
| Extreme transformation threshold / sanity check | G (including direct regression G-6 for the reported bug) |
| Multi-method fallback strategy | H |
| Status bar feedback (method, parameters, confidence/warning) | I |
| Shared fixture layer (`make_transformed_channel`, `decompose_affine_matrix`, base images, `assert_channels_close`) | A |
| Parameter-recovery correctness per transform type | B |
| Pixel-fidelity correctness | C |
| Output invariants (range, dtype, red-channel immutability) | D |
| `AlignmentError` on featureless/insufficient/degenerate input | E |
| No side effects on per-channel error | J |
| Full end-to-end regression | K |

---

## 15. Prioritization and Suggested Delivery Order

1. **P0 — Infrastructure (Area A).** Nothing else can be written or trusted without this.
2. **P0 — Adversarial baseline (Area E, sections 6.1–6.5) against the *current* implementation.** This documents today's actual failure behavior and prevents regressions while new features are built.
3. **P0 — Parameter recovery and pixel fidelity (Areas B, C, D) against the *current* implementation.** Establishes the correctness baseline for the existing single-method pipeline.
4. **P1 — Sanity-check tests (Area G), especially G-6, the direct regression test for the reported bug.** This is the highest-value new test because it directly encodes the originating complaint.
5. **P1 — DOF restriction tests (Area F).**
6. **P2 — Multi-method fallback tests (Area H) and status reporting tests (Area I).** These depend on the most new implementation work and should follow once the API surface is finalized.
7. **P2 — Partial-failure isolation (Area J) and full integration regression (Area K).**

Tests targeting not-yet-implemented behavior (most of F, G, H, I) should be added to the suite immediately, marked with `@pytest.mark.xfail(reason="pending implementation of <feature>", strict=True)` so that:
- They serve as an executable specification from day one.
- `strict=True` ensures that the moment the feature is implemented and the test starts passing, CI flags the `xfail` as unexpectedly passing — prompting the team to remove the marker and treat the test as a normal regression guard.

---

## 16. Appendix: Example Test Skeleton (Illustrative)

```python
import pytest
import numpy as np
from tests.fixtures.align_fixtures import (
    make_transformed_channel,
    decompose_affine_matrix,
    assert_channels_close,
)
from src.core.align import align_images, AlignmentError


class TestParameterRecoveryTranslation:
    """Area B.1 — Translation-only correctness tests."""

    @pytest.mark.parametrize(
        "tx,ty,test_id",
        [
            (10, 0, "B-T1-positive-x"),
            (-10, 0, "B-T2-negative-x"),
            (0, 10, "B-T3-positive-y"),
            (0, -10, "B-T4-negative-y"),
            (8, 8, "B-T5-diagonal"),
        ],
    )
    def test_translation_recovery(self, base_image_large, tx, ty, test_id):
        r = base_image_large
        g, ground_truth_matrix = make_transformed_channel(r, tx=tx, ty=ty)
        b = r.copy()

        result = align_images(r, g, b)

        recovered_tx, recovered_ty, recovered_angle, recovered_scale = (
            decompose_affine_matrix(result.aligned_gray_matrices[1])
        )

        assert abs(recovered_tx - (-tx)) <= 2.0, test_id
        assert abs(recovered_ty - (-ty)) <= 2.0, test_id
        assert abs(recovered_angle) <= 0.3, test_id
        assert abs(recovered_scale - 1.0) <= 0.02, test_id

        assert_channels_close(
            result.aligned_gray[1], result.aligned_gray[0], max_mae=5.0
        )
        assert np.array_equal(result.aligned_gray[0], r)


class TestAdversarialFeatureless:
    """Area E.1 — Featureless input failure modes."""

    def test_flat_image_raises_alignment_error(self, base_image_flat):
        with pytest.raises(AlignmentError) as exc_info:
            align_images(base_image_flat, base_image_flat, base_image_flat)
        assert str(exc_info.value)  # non-empty message

    def test_flat_channel_identifies_channel_index(
        self, base_image_large, base_image_flat
    ):
        with pytest.raises(AlignmentError) as exc_info:
            align_images(base_image_large, base_image_flat, base_image_large)
        assert "1" in str(exc_info.value) or "G" in str(exc_info.value)


@pytest.mark.xfail(reason="pending implementation of sanity-check thresholds", strict=True)
class TestSanityCheckThresholds:
    """Area G — direct regression test for the reported extreme-transform bug."""

    def test_extreme_scale_rejected(self, base_image_repetitive):
        # Constructs a scenario likely to produce a pathological ORB result
        # on ambiguous repetitive content; exact construction depends on
        # final ORB parameter tuning.
        r = base_image_repetitive
        g, _ = make_transformed_channel(r, tx=3, ty=2, angle_deg=1.0, scale=1.0)
        b = r.copy()

        # Once implemented, a wildly wrong transform must be rejected
        # rather than silently applied.
        result = align_images(r, g, b, sanity_check=True)
        assert result.method_used != "feature_based_unchecked"
```

---

## 17. Definition of Done for This Campaign

The alignment robustness test campaign is considered complete when:

- [ ] All Area A infrastructure fixtures and helpers are implemented and pass their own IT-A tests.
- [ ] All Area B, C, D tests pass against the current (pre-feature) implementation, establishing the correctness baseline.
- [ ] All Area E and J tests pass against the current implementation, establishing the adversarial baseline.
- [ ] Areas F, G, H, I tests exist as `xfail(strict=True)` specifications from day one.
- [ ] As DOF selection, sanity checking, fallback, and reporting features are implemented (per the linked feature request), their corresponding `xfail` markers are removed one at a time and the tests pass.
- [ ] G-6 (the direct regression test for the reported extreme-scale/rotation bug) passes and is documented as the canonical regression guard for this issue.
- [ ] The full suite runs deterministically in CI with no flaky failures across at least 10 consecutive runs.
- [ ] Test execution time for the full alignment suite remains within the project's existing CI time budget (to be measured once initial implementation lands; flag for optimization — e.g., via fixture caching — if it becomes a bottleneck).

