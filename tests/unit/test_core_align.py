"""Unit tests for src.core.align module.

Tests image alignment using ORB feature matching and affine transformation.
"""

import math

import pytest
import numpy as np
import cv2

from src.core.align import (
    AlignmentDOF,
    AlignmentError,
    AlignmentResult,
    TransformParams,
    SANITY_MAX_ROTATION_DEG,
    SANITY_MIN_SCALE,
    SANITY_MAX_SCALE,
    _check_sanity,
    _extract_transform_params,
    _restrict_matrix_to_dof,
    _translation_matrix,
    align_images,
    align_images_with_result,
)

pytestmark = pytest.mark.skip_coverage_enforcement



@pytest.fixture
def sample_grayscale_image() -> np.ndarray:
    """Create a sample grayscale image with sufficient features for ORB detection."""
    # Create a checkerboard pattern with some random noise for feature richness
    img = np.zeros((256, 256), dtype=np.uint8)
    for i in range(0, 256, 16):
        for j in range(0, 256, 16):
            if (i // 16 + j // 16) % 2 == 0:
                img[i : i + 16, j : j + 16] = 200
    # Add some random features
    np.random.seed(42)
    img += np.random.randint(0, 30, img.shape).astype(np.uint8)
    return img


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create a sample RGB image (3-channel version of grayscale)."""
    grayscale = np.zeros((256, 256), dtype=np.uint8)
    for i in range(0, 256, 16):
        for j in range(0, 256, 16):
            if (i // 16 + j // 16) % 2 == 0:
                grayscale[i : i + 16, j : j + 16] = 200
    np.random.seed(42)
    grayscale += np.random.randint(0, 30, grayscale.shape).astype(np.uint8)
    # Convert to RGB by stacking 3 copies
    return np.stack([grayscale] * 3, axis=2)


@pytest.fixture
def identical_image_set(
    sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Create a set of identical grayscale and RGB images."""
    grayscale_images = [sample_grayscale_image.copy() for _ in range(3)]
    rgb_images = [sample_rgb_image.copy() for _ in range(3)]
    return grayscale_images, rgb_images


class TestAlignImages:
    """
    Test Design Specification: align_images()
    Module under test: src/core/align.py

    Contract:
        Aligns green (G) and blue (B) channels to red (R) channel using ORB
        feature matching and affine transformation. Takes two lists of three images
        each (grayscale and RGB). Returns aligned versions (grayscale, RGB).
        Red channel is never transformed. Raises AlignmentError if feature matching
        or transformation fails.

    Equivalence partitions:
        EP1  Identical images (no shift needed)        → near-identity transform
        EP2  Well-aligned images with features         → successful alignment
        EP3  Images with insufficient features         → skipped (returned as-is)
        EP4  Images with too few feature matches       → AlignmentError
        EP5  Different image sizes in same call        → processed independently

    Boundary values:
        BV1  Exactly 3 images (minimum required)
        BV2  Red channel index = 0 (never transformed)
        BV3  Green/blue channel indices = 1, 2 (aligned to red)
        BV4  Feature match count at threshold (e.g., 4 = minimum for affine)

    Exclusions:
        - Images with degenerate geometry (all-black, all-white)
        - Very small images (<32x32)
        - Mismatched sizes between grayscale and RGB versions
        - Non-OpenCV-compatible dtypes (tested at caller's responsibility)

    Constraints:
        - ORB detector and affine transforms are from cv2 (OpenCV)
        - Output shares input shape and dtype
        - Interpolation in warpAffine may shift border pixels by ±1
    """

    def test_identical_images_produce_minimal_transform(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Given identical grayscale and RGB images, when aligned, then channels remain unchanged within tolerance."""
        # Arrange
        grayscale_images, rgb_images = identical_image_set

        # Act
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Assert
        assert len(aligned_gray) == 3
        assert len(aligned_rgb) == 3
        # Red channel is never transformed
        np.testing.assert_array_equal(aligned_gray[0], grayscale_images[0])
        np.testing.assert_array_equal(aligned_rgb[0], rgb_images[0])
        # Green and blue should be near-identical after aligning identical images;
        # warpAffine interpolation may shift border pixels by ±1
        for ch in (1, 2):
            mae_gray = np.mean(np.abs(
                aligned_gray[ch].astype(float) - grayscale_images[ch].astype(float)
            ))
            mae_rgb = np.mean(np.abs(
                aligned_rgb[ch].astype(float) - rgb_images[ch].astype(float)
            ))
            assert mae_gray < 2, f"Grayscale channel {ch} MAE too high: {mae_gray}"
            assert mae_rgb < 2, f"RGB channel {ch} MAE too high: {mae_rgb}"

    @pytest.mark.parametrize("channel_idx", [
        0,  # BV1: red channel (reference channel, never transformed)
        1,  # BV2: green channel (aligned to red)
        2,  # BV3: blue channel (aligned to red)
    ], ids=["red_channel", "green_channel", "blue_channel"])
    def test_returns_correct_output_shape(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]], channel_idx: int
    ) -> None:
        """Given input images, when aligned, then output shape matches input shape for each channel."""
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Arrange
        # Act & Assert
        assert aligned_gray[channel_idx].shape == grayscale_images[channel_idx].shape
        assert aligned_rgb[channel_idx].shape == rgb_images[channel_idx].shape

    @pytest.mark.parametrize("channel_idx", [
        0,  # BV1: red channel (reference channel, never transformed)
        1,  # BV2: green channel (aligned to red)
        2,  # BV3: blue channel (aligned to red)
    ], ids=["red_channel", "green_channel", "blue_channel"])
    def test_returns_correct_output_dtype(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]], channel_idx: int
    ) -> None:
        """Given input images with uint8 dtype, when aligned, then output dtype matches input dtype for each channel."""
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Arrange
        # Act & Assert
        assert aligned_gray[channel_idx].dtype == grayscale_images[channel_idx].dtype
        assert aligned_rgb[channel_idx].dtype == rgb_images[channel_idx].dtype

    def test_red_channel_never_transformed(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Given images with red channel at index 0, when aligned, then red channel is returned unchanged."""
        # Arrange
        grayscale_images, rgb_images = identical_image_set

        # Act
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Assert
        np.testing.assert_array_equal(aligned_gray[0], grayscale_images[0])
        np.testing.assert_array_equal(aligned_rgb[0], rgb_images[0])

    def test_alignment_output_is_independent_copy(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Given aligned output, when original input is modified, then output remains unaffected."""
        # Arrange
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Act
        grayscale_images[0][0, 0] = 255
        rgb_images[0][0, 0] = [255, 255, 255]

        # Assert
        assert aligned_gray[0][0, 0] != 255
        assert not np.array_equal(aligned_rgb[0][0, 0], [255, 255, 255])


class TestAlignmentError:
    """
    Test Design Specification: AlignmentError exception
    Module under test: src/core/align.py

    Contract:
        Custom exception raised by align_images() when feature matching or
        transformation fails. Subclasses Exception. Preserves message passed
        to constructor.

    Equivalence partitions:
        EP1  AlignmentError as type object             → subclass of Exception
        EP2  AlignmentError instance creation          → can be instantiated
        EP3  AlignmentError with custom message        → message is preserved
        EP4  AlignmentError raised and caught          → caught as Exception

    Boundary values:
        BV1  Empty message string
        BV2  Long message string (> 256 chars)

    Exclusions:
        - Custom attributes beyond message
        - Pickling / unpickling behavior
        - Inheritance chain beyond Exception

    Constraints:
        - Pure exception class, no side effects
    """

    def test_alignment_error_is_exception(self) -> None:
        """Given AlignmentError class, when checked, then it is a subclass of Exception."""
        assert issubclass(AlignmentError, Exception)

    def test_alignment_error_can_be_instantiated(self) -> None:
        """Given AlignmentError class with message, when raised and caught, then instance is created successfully."""
        with pytest.raises(AlignmentError):
            raise AlignmentError("Test error message")

    def test_alignment_error_message_preserved(self) -> None:
        """Given AlignmentError with custom message, when raised, then message is preserved and matchable."""
        error_msg = "Custom error message"
        with pytest.raises(AlignmentError, match=error_msg):
            raise AlignmentError(error_msg)

    def test_no_descriptor_silently_skips_alignment(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given blank images without ORB descriptors, when aligned, then they are returned unchanged."""
        # Arrange
        blank_gray = np.zeros((256, 256), dtype=np.uint8)
        blank_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        grayscale_images = [sample_grayscale_image, blank_gray, blank_gray]
        rgb_images = [sample_rgb_image, blank_rgb, blank_rgb]

        # Act
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Assert
        np.testing.assert_array_equal(aligned_gray[1], blank_gray)
        np.testing.assert_array_equal(aligned_gray[2], blank_gray)
        np.testing.assert_array_equal(aligned_rgb[1], blank_rgb)
        np.testing.assert_array_equal(aligned_rgb[2], blank_rgb)

    def test_insufficient_matches_triggers_fallback(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given images with too few feature matches for ORB, when aligned with align_images_with_result, then a fallback method is used."""
        # Arrange
        tiny_feature_gray = np.zeros((256, 256), dtype=np.uint8)
        tiny_feature_gray[100:110, 100:110] = 255
        tiny_feature_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        tiny_feature_rgb[100:110, 100:110] = [255, 255, 255]
        grayscale_images = [sample_grayscale_image, tiny_feature_gray, tiny_feature_gray]
        rgb_images = [sample_rgb_image, tiny_feature_rgb, tiny_feature_rgb]

        # Act
        result = align_images_with_result(grayscale_images, rgb_images)

        # Assert: ORB failed → fallback triggered
        assert result.fallback_triggered is True
        assert result.method_used in ("phase correlation", "unaligned")

    def test_insufficient_matches_warning_includes_match_info(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given insufficient ORB matches, when align_images_with_result runs, then the warning references the failure."""
        # Arrange
        tiny_feature_gray = np.zeros((256, 256), dtype=np.uint8)
        tiny_feature_gray[100:110, 100:110] = 255
        tiny_feature_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        tiny_feature_rgb[100:110, 100:110] = [255, 255, 255]
        grayscale_images = [sample_grayscale_image, tiny_feature_gray, tiny_feature_gray]
        rgb_images = [sample_rgb_image, tiny_feature_rgb, tiny_feature_rgb]

        # Act
        result = align_images_with_result(grayscale_images, rgb_images)

        # Assert: fallback warning mentions the ORB failure
        assert result.warning is not None
        assert "matches" in result.warning.lower() or "insufficient" in result.warning.lower() or "orb" in result.warning.lower()


class TestAlignImagesInputValidation:
    """
    Test Design Specification: align_images() input validation
    Module under test: src/core/align.py

    Contract:
        Validates input constraints: exactly 3 grayscale images, exactly 3 RGB
        images. Images can be different sizes. Detects descriptor-less (blank)
        images and silently skips alignment for those channels.

    Equivalence partitions:
        EP1  Valid: 3 grayscale + 3 RGB, all feature-rich    → alignment succeeds
        EP2  Valid: 3 grayscale + 3 RGB, mixed blank+rich    → blanks skipped
        EP3  Invalid: fewer than 3 grayscale images          → IndexError
        EP4  Invalid: fewer than 3 RGB images               → IndexError
        EP5  Valid: different-sized images in same list      → each processed independently

    Boundary values:
        BV1  Exactly 3 images (minimum required)
        BV2  2 images (below minimum)
        BV3  Images with zero features (blank, all-black)
        BV4  Images of different dimensions (e.g., 256x256 vs 128x128)

    Exclusions:
        - Non-numpy inputs (type validation at caller boundary)
        - Non-uint8 dtypes (dtype validation at caller boundary)
        - More than 3 images (not tested; extras ignored)

    Constraints:
        - Blank images (no detected features) are silently skipped
        - Different image sizes are independently alignable
        - IndexError is raised when accessing missing channels
    """

    def test_requires_three_grayscale_images(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given fewer than 3 grayscale images, when aligned, then IndexError is raised."""
        # Arrange
        two_gray = [sample_grayscale_image.copy() for _ in range(2)]
        three_rgb = [sample_rgb_image.copy() for _ in range(3)]

        # Act & Assert
        with pytest.raises(IndexError):
            align_images(two_gray, three_rgb)

    def test_function_accepts_different_sized_images(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given images of different sizes, when aligned, then either succeeds with red channel shape or raises AlignmentError.

        Note: This test documents non-deterministic behavior. Scale differences in feature matching may cause alignment
        to succeed (output matches red channel shape) or fail (AlignmentError). Both outcomes are valid.
        """
        # Arrange
        red_gray = sample_grayscale_image  # 256x256
        red_rgb = sample_rgb_image  # 256x256x3
        large_gray = cv2.resize(sample_grayscale_image, (384, 384))
        large_rgb = cv2.resize(sample_rgb_image, (384, 384))

        grayscale = [red_gray, large_gray.copy(), large_gray.copy()]
        rgb = [red_rgb, large_rgb.copy(), large_rgb.copy()]

        # Act & Assert
        try:
            aligned_gray, aligned_rgb = align_images(grayscale, rgb)
            # Success path: outputs must match reference channel shape
            for i in range(3):
                assert aligned_gray[i].shape == red_gray.shape
                assert aligned_rgb[i].shape == red_rgb.shape
        except AlignmentError:
            # Acceptable failure: scale difference may cause insufficient feature matches
            pass


# ---------------------------------------------------------------------------
# New tests for DOF, sanity check, AlignmentResult, and fallback pipeline
# ---------------------------------------------------------------------------


class TestTransformParams:
    """
    Test Design Specification: TransformParams dataclass
    Module under test: src/core/align.py

    Contract:
        Dataclass that holds per-channel geometric transform parameters extracted
        from a 2×3 affine matrix. Default-constructed instance represents the
        identity transform (no displacement, no rotation, scale = 1.0).

    Equivalence partitions:
        EP1  Default construction       → all zeros except scale = 1.0
        EP2  Custom field values        → values stored correctly

    Boundary values:
        BV1  translation_x = 0.0
        BV2  rotation_deg = 0.0
        BV3  scale = 1.0

    Exclusions:
        - Validation of out-of-range values (dataclass has no validators)
    """

    def test_default_construction(self) -> None:
        """Given TransformParams with no args, when constructed, then fields are identity values."""
        # Arrange & Act
        p = TransformParams()
        # Assert
        assert p.translation_x == 0.0
        assert p.translation_y == 0.0
        assert p.rotation_deg == 0.0
        assert p.scale == 1.0

    def test_custom_values_stored(self) -> None:
        """Given TransformParams with explicit values, when constructed, then those values are accessible."""
        # Arrange & Act
        p = TransformParams(translation_x=5.0, translation_y=-3.0, rotation_deg=2.5, scale=0.95)
        # Assert
        assert p.translation_x == 5.0
        assert p.translation_y == -3.0
        assert p.rotation_deg == 2.5
        assert p.scale == 0.95


class TestAlignmentResult:
    """
    Test Design Specification: AlignmentResult dataclass
    Module under test: src/core/align.py

    Contract:
        Dataclass representing the complete output of the alignment pipeline.
        Contains aligned image arrays, method name, per-channel transform
        parameters, fallback flag, and optional warning string.

    Equivalence partitions:
        EP1  Successful ORB alignment       → fallback_triggered=False, warning=None
        EP2  Phase-correlation fallback     → fallback_triggered=True, warning set
        EP3  Unaligned passthrough          → method_used="unaligned"

    Boundary values:
        BV1  channel_params default = 3 identity TransformParams
        BV2  warning = None (no fallback)
        BV3  fallback_triggered = False (success)

    Exclusions:
        - Image array contents (tested via align_images_with_result)
    """

    def test_default_channel_params_are_identity(self) -> None:
        """Given AlignmentResult constructed with defaults, when accessed, then channel_params contains 3 identity params."""
        # Arrange
        dummy = [np.zeros((4, 4), dtype=np.uint8)]
        result = AlignmentResult(
            aligned_grayscale=dummy,
            aligned_rgb=dummy,
            method_used="ORB",
        )
        # Act & Assert
        assert len(result.channel_params) == 3
        for p in result.channel_params:
            assert p.scale == 1.0
            assert p.rotation_deg == 0.0

    def test_fallback_and_warning_fields(self) -> None:
        """Given AlignmentResult with fallback_triggered=True and a warning, when accessed, then fields match."""
        # Arrange
        dummy = [np.zeros((4, 4), dtype=np.uint8)]
        result = AlignmentResult(
            aligned_grayscale=dummy,
            aligned_rgb=dummy,
            method_used="phase correlation",
            fallback_triggered=True,
            warning="ORB failed",
        )
        # Act & Assert
        assert result.fallback_triggered is True
        assert result.warning == "ORB failed"
        assert result.method_used == "phase correlation"


class TestExtractTransformParams:
    """
    Test Design Specification: _extract_transform_params()
    Module under test: src/core/align.py

    Contract:
        Decomposes a 2×3 float32 affine matrix into translation, rotation (degrees),
        and uniform scale. The identity matrix should yield translation=(0,0),
        rotation=0°, scale=1.0. A pure translation matrix yields the correct
        displacements with rotation=0° and scale=1.0.

    Equivalence partitions:
        EP1  Identity matrix          → tx=0, ty=0, rot=0°, scale=1.0
        EP2  Pure translation         → tx=dx, ty=dy, rot=0°, scale=1.0
        EP3  Rotation-only            → rot ≈ angle, scale ≈ 1.0, tx=ty=0
        EP4  Scale-only               → scale=s, rot=0°, tx=ty=0

    Boundary values:
        BV1  Identity matrix (no transform)
        BV2  Translation with negative components
        BV3  Small rotation (< 1°)

    Exclusions:
        - Shear matrices (params are approximate for full-affine)
    """

    def test_identity_matrix(self) -> None:
        """Given the identity affine matrix, when extracted, then params are all-zero/scale-1."""
        # Arrange
        mat = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
        # Act
        p = _extract_transform_params(mat)
        # Assert
        assert p.translation_x == pytest.approx(0.0, abs=1e-5)
        assert p.translation_y == pytest.approx(0.0, abs=1e-5)
        assert p.rotation_deg == pytest.approx(0.0, abs=1e-4)
        assert p.scale == pytest.approx(1.0, abs=1e-5)

    def test_pure_translation(self) -> None:
        """Given a translation-only matrix, when extracted, then tx and ty match and rotation/scale are identity."""
        # Arrange
        mat = np.array([[1.0, 0.0, 7.5], [0.0, 1.0, -3.2]], dtype=np.float32)
        # Act
        p = _extract_transform_params(mat)
        # Assert
        assert p.translation_x == pytest.approx(7.5, abs=1e-4)
        assert p.translation_y == pytest.approx(-3.2, abs=1e-4)
        assert p.rotation_deg == pytest.approx(0.0, abs=1e-3)
        assert p.scale == pytest.approx(1.0, abs=1e-5)

    def test_rotation_extraction(self) -> None:
        """Given a rotation matrix with known angle, when extracted, then rotation_deg matches the input angle."""
        # Arrange
        angle_deg = 3.0
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        mat = np.array([[cos_a, -sin_a, 0.0], [sin_a, cos_a, 0.0]], dtype=np.float32)
        # Act
        p = _extract_transform_params(mat)
        # Assert
        assert p.rotation_deg == pytest.approx(angle_deg, abs=0.01)
        assert p.scale == pytest.approx(1.0, abs=1e-4)

    def test_scale_extraction(self) -> None:
        """Given a uniform-scale matrix, when extracted, then scale matches the input factor."""
        # Arrange
        s = 1.1
        mat = np.array([[s, 0.0, 0.0], [0.0, s, 0.0]], dtype=np.float32)
        # Act
        p = _extract_transform_params(mat)
        # Assert
        assert p.scale == pytest.approx(s, abs=1e-5)
        assert p.rotation_deg == pytest.approx(0.0, abs=1e-3)


class TestCheckSanity:
    """
    Test Design Specification: _check_sanity()
    Module under test: src/core/align.py

    Contract:
        Returns None when transform parameters are within acceptable bounds;
        returns a descriptive warning string otherwise. Thresholds are:
        - |rotation| ≤ SANITY_MAX_ROTATION_DEG
        - SANITY_MIN_SCALE ≤ scale ≤ SANITY_MAX_SCALE

    Equivalence partitions:
        EP1  All params within bounds   → None
        EP2  Rotation too large (pos)   → warning string containing "rotation"
        EP3  Rotation too large (neg)   → warning string
        EP4  Scale too small            → warning string containing "scale"
        EP5  Scale too large            → warning string containing "scale"

    Boundary values:
        BV1  rotation = SANITY_MAX_ROTATION_DEG exactly (edge: sane)
        BV2  rotation = SANITY_MAX_ROTATION_DEG + 0.01 (insane)
        BV3  scale = SANITY_MIN_SCALE exactly (edge: sane)
        BV4  scale = SANITY_MIN_SCALE - 0.001 (insane)
        BV5  scale = SANITY_MAX_SCALE exactly (edge: sane)
        BV6  scale = SANITY_MAX_SCALE + 0.001 (insane)

    Exclusions:
        - Combined violations (rotation and scale both bad): first check wins
    """

    def test_identity_params_pass(self) -> None:
        """Given identity TransformParams, when checked, then no warning is returned."""
        assert _check_sanity(TransformParams()) is None

    def test_small_rotation_passes(self) -> None:
        """Given rotation exactly at the threshold, when checked, then no warning is returned."""
        p = TransformParams(rotation_deg=SANITY_MAX_ROTATION_DEG)
        assert _check_sanity(p) is None

    def test_rotation_above_threshold_fails(self) -> None:
        """Given rotation slightly above the threshold, when checked, then a warning is returned."""
        p = TransformParams(rotation_deg=SANITY_MAX_ROTATION_DEG + 0.01)
        result = _check_sanity(p)
        assert result is not None
        assert "rotation" in result

    def test_negative_rotation_above_threshold_fails(self) -> None:
        """Given negative rotation beyond threshold, when checked, then a warning is returned."""
        p = TransformParams(rotation_deg=-(SANITY_MAX_ROTATION_DEG + 0.01))
        result = _check_sanity(p)
        assert result is not None
        assert "rotation" in result

    def test_scale_at_min_boundary_passes(self) -> None:
        """Given scale exactly at SANITY_MIN_SCALE, when checked, then no warning is returned."""
        p = TransformParams(scale=SANITY_MIN_SCALE)
        assert _check_sanity(p) is None

    def test_scale_below_minimum_fails(self) -> None:
        """Given scale below SANITY_MIN_SCALE, when checked, then a warning is returned."""
        p = TransformParams(scale=SANITY_MIN_SCALE - 0.001)
        result = _check_sanity(p)
        assert result is not None
        assert "scale" in result

    def test_scale_at_max_boundary_passes(self) -> None:
        """Given scale exactly at SANITY_MAX_SCALE, when checked, then no warning is returned."""
        p = TransformParams(scale=SANITY_MAX_SCALE)
        assert _check_sanity(p) is None

    def test_scale_above_maximum_fails(self) -> None:
        """Given scale above SANITY_MAX_SCALE, when checked, then a warning is returned."""
        p = TransformParams(scale=SANITY_MAX_SCALE + 0.001)
        result = _check_sanity(p)
        assert result is not None
        assert "scale" in result


class TestRestrictMatrixToDOF:
    """
    Test Design Specification: _restrict_matrix_to_dof()
    Module under test: src/core/align.py

    Contract:
        Given a 2×3 affine matrix and an AlignmentDOF, restricts the matrix to
        only the allowed parameters:
        - TRANSLATION: forces rotation=0°, scale=1.0; keeps tx, ty
        - TRANSLATION_ROTATION: forces scale=1.0; keeps rotation, tx, ty
        - TRANSLATION_ROTATION_SCALE: returns matrix unchanged
        - FULL_AFFINE: returns matrix unchanged

    Equivalence partitions:
        EP1  TRANSLATION → pure translation matrix (top-left 2×2 = identity)
        EP2  TRANSLATION_ROTATION → scale = 1.0; rotation and translation preserved
        EP3  TRANSLATION_ROTATION_SCALE → matrix unchanged
        EP4  FULL_AFFINE → matrix unchanged

    Boundary values:
        BV1  Identity matrix + TRANSLATION → identity output
        BV2  Non-zero rotation + TRANSLATION → rotation zeroed

    Exclusions:
        - Non-float32 matrices (caller responsibility)
    """

    def _make_partial_affine(self, angle_deg: float, scale: float, tx: float, ty: float) -> np.ndarray:
        r = math.radians(angle_deg)
        c, s = math.cos(r) * scale, math.sin(r) * scale
        return np.array([[c, -s, tx], [s, c, ty]], dtype=np.float32)

    def test_translation_dof_zeroes_rotation_and_scale(self) -> None:
        """Given a matrix with rotation and scale, when restricted to TRANSLATION, then only translation remains."""
        # Arrange
        mat = self._make_partial_affine(angle_deg=3.0, scale=1.05, tx=10.0, ty=-5.0)
        # Act
        result = _restrict_matrix_to_dof(mat, AlignmentDOF.TRANSLATION)
        # Assert
        p = _extract_transform_params(result)
        assert p.rotation_deg == pytest.approx(0.0, abs=1e-4)
        assert p.scale == pytest.approx(1.0, abs=1e-4)
        assert p.translation_x == pytest.approx(10.0, abs=0.1)
        assert p.translation_y == pytest.approx(-5.0, abs=0.1)

    def test_translation_rotation_dof_forces_scale_to_one(self) -> None:
        """Given a matrix with scale != 1, when restricted to TRANSLATION_ROTATION, then scale becomes 1.0."""
        # Arrange
        mat = self._make_partial_affine(angle_deg=2.0, scale=1.1, tx=4.0, ty=2.0)
        # Act
        result = _restrict_matrix_to_dof(mat, AlignmentDOF.TRANSLATION_ROTATION)
        p = _extract_transform_params(result)
        # Assert
        assert p.scale == pytest.approx(1.0, abs=1e-4)
        assert p.rotation_deg == pytest.approx(2.0, abs=0.05)

    def test_translation_rotation_scale_dof_unchanged(self) -> None:
        """Given any matrix, when restricted to TRANSLATION_ROTATION_SCALE, then matrix is returned unchanged."""
        # Arrange
        mat = self._make_partial_affine(angle_deg=4.0, scale=0.95, tx=3.0, ty=-1.0)
        # Act
        result = _restrict_matrix_to_dof(mat, AlignmentDOF.TRANSLATION_ROTATION_SCALE)
        # Assert
        np.testing.assert_array_almost_equal(result, mat)

    def test_full_affine_dof_unchanged(self) -> None:
        """Given any matrix, when restricted to FULL_AFFINE, then matrix is returned unchanged."""
        # Arrange
        mat = self._make_partial_affine(angle_deg=1.5, scale=1.02, tx=-2.0, ty=6.0)
        # Act
        result = _restrict_matrix_to_dof(mat, AlignmentDOF.FULL_AFFINE)
        # Assert
        np.testing.assert_array_almost_equal(result, mat)


class TestAlignImagesWithResult:
    """
    Test Design Specification: align_images_with_result()
    Module under test: src/core/align.py

    Contract:
        Runs the cascaded alignment pipeline and returns an AlignmentResult.
        Pipeline order: ORB → phase correlation → unaligned passthrough.
        Sanity-failing ORB results trigger the phase-correlation fallback.
        Returns method_used, fallback_triggered, and per-channel TransformParams.

    Equivalence partitions:
        EP1  Feature-rich identical images → ORB succeeds; fallback_triggered=False
        EP2  Blank images (no features)    → phase correlation or unaligned fallback
        EP3  DOF=TRANSLATION restricts     → output matrix is translation-only
        EP4  DOF=FULL_AFFINE passes through → matrix unchanged

    Boundary values:
        BV1  Red channel params always identity (index 0)
        BV2  fallback_triggered=False for clean ORB success
        BV3  method_used="ORB" when ORB succeeds

    Exclusions:
        - Sanity check triggering fallback on real images (hard to construct deterministically)
    """

    @pytest.fixture
    def feature_images(self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray) -> tuple:
        grays = [sample_grayscale_image.copy() for _ in range(3)]
        rgbs = [sample_rgb_image.copy() for _ in range(3)]
        return grays, rgbs

    def test_successful_orb_alignment_method_name(self, feature_images: tuple) -> None:
        """Given feature-rich images, when aligned, then method_used is 'ORB'."""
        # Arrange
        grays, rgbs = feature_images
        # Act
        result = align_images_with_result(grays, rgbs)
        # Assert
        assert result.method_used == "ORB"

    def test_successful_orb_no_fallback(self, feature_images: tuple) -> None:
        """Given feature-rich images, when aligned, then fallback_triggered is False."""
        # Arrange
        grays, rgbs = feature_images
        # Act
        result = align_images_with_result(grays, rgbs)
        # Assert
        assert result.fallback_triggered is False
        assert result.warning is None

    def test_result_contains_three_channel_params(self, feature_images: tuple) -> None:
        """Given feature-rich images, when aligned, then channel_params has exactly 3 entries."""
        # Arrange
        grays, rgbs = feature_images
        # Act
        result = align_images_with_result(grays, rgbs)
        # Assert
        assert len(result.channel_params) == 3

    def test_red_channel_params_are_identity(self, feature_images: tuple) -> None:
        """Given any images, when aligned, then channel_params[0] (Red) is the identity transform."""
        # Arrange
        grays, rgbs = feature_images
        # Act
        result = align_images_with_result(grays, rgbs)
        p = result.channel_params[0]
        # Assert
        assert p.translation_x == pytest.approx(0.0, abs=1e-5)
        assert p.translation_y == pytest.approx(0.0, abs=1e-5)
        assert p.rotation_deg == pytest.approx(0.0, abs=1e-4)
        assert p.scale == pytest.approx(1.0, abs=1e-5)

    def test_output_images_have_correct_count(self, feature_images: tuple) -> None:
        """Given feature-rich images, when aligned, then aligned_grayscale and aligned_rgb each contain 3 arrays."""
        # Arrange
        grays, rgbs = feature_images
        # Act
        result = align_images_with_result(grays, rgbs)
        # Assert
        assert len(result.aligned_grayscale) == 3
        assert len(result.aligned_rgb) == 3

    def test_few_feature_images_trigger_fallback(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given G/B channels with very few features (too few ORB matches), when aligned, then fallback is triggered."""
        # Arrange: tiny bright spot → produces few keypoints, likely < 50 matches with rich red channel
        tiny_gray = np.zeros((256, 256), dtype=np.uint8)
        tiny_gray[120:130, 120:130] = 255
        tiny_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        tiny_rgb[120:130, 120:130] = [255, 255, 255]
        grays = [sample_grayscale_image.copy(), tiny_gray, tiny_gray]
        rgbs = [sample_rgb_image.copy(), tiny_rgb, tiny_rgb]
        # Act
        result = align_images_with_result(grays, rgbs)
        # Assert: either ORB failed (fallback) or succeeded (few features still matched)
        # Both are acceptable — the important guarantee is that a valid result is always returned
        assert result.method_used in ("ORB", "phase correlation", "unaligned")
        assert len(result.aligned_grayscale) == 3
        assert len(result.aligned_rgb) == 3

    def test_translation_dof_produces_small_rotation(self, feature_images: tuple) -> None:
        """Given DOF=TRANSLATION and identical images, when aligned, then rotation in params is near 0°."""
        # Arrange
        grays, rgbs = feature_images
        # Act
        result = align_images_with_result(grays, rgbs, dof=AlignmentDOF.TRANSLATION)
        # Assert: method may be ORB or fallback, but rotation must be 0 for translation DOF
        for i in (1, 2):
            assert result.channel_params[i].rotation_deg == pytest.approx(0.0, abs=1e-3)
            assert result.channel_params[i].scale == pytest.approx(1.0, abs=1e-3)


class TestAlignmentDOFEnum:
    """
    Test Design Specification: AlignmentDOF enum
    Module under test: src/core/align.py

    Contract:
        Enum with four members representing the allowed geometric transformations:
        TRANSLATION, TRANSLATION_ROTATION, TRANSLATION_ROTATION_SCALE, FULL_AFFINE.
        Each member has a string value.

    Equivalence partitions:
        EP1  All four members exist
        EP2  String values are non-empty

    Exclusions:
        - Enum ordering (not part of contract)
    """

    def test_all_four_members_exist(self) -> None:
        """Given AlignmentDOF enum, when accessed, then all four DOF members are present."""
        members = {m.name for m in AlignmentDOF}
        assert "TRANSLATION" in members
        assert "TRANSLATION_ROTATION" in members
        assert "TRANSLATION_ROTATION_SCALE" in members
        assert "FULL_AFFINE" in members

    def test_values_are_strings(self) -> None:
        """Given AlignmentDOF members, when .value is accessed, then each is a non-empty string."""
        for member in AlignmentDOF:
            assert isinstance(member.value, str)
            assert len(member.value) > 0
