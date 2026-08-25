"""Synthetic alignment tests for shared alignment fixtures and algorithm adapters."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from tests.fixtures.align_synthetic import (
    AlignmentAlgorithm,
    AlignmentRunResult,
    assert_channels_close,
    base_image_flat,  # noqa: F401
    base_image_large,  # noqa: F401
    base_image_repetitive,  # noqa: F401
    base_image_small,  # noqa: F401
    base_image_sparse_features,  # noqa: F401
    decompose_affine_matrix,
    make_transformed_channel,
    run_alignment_with_algorithms,
)
from src.core.align import align_images

pytestmark = pytest.mark.skip_coverage_enforcement


@pytest.fixture
def align_algorithm_orb() -> AlignmentAlgorithm:
    """Default adapter for the current ORB alignment implementation."""
    return AlignmentAlgorithm(name="orb", align=align_images)


def _expected_translation(base_image: np.ndarray, tx: int, ty: int, border_value: int = 0) -> np.ndarray:
    """Create the expected integer-translation result with constant borders."""
    height, width = base_image.shape
    translated = np.full((height, width), border_value, dtype=base_image.dtype)

    src_x0 = max(0, -tx)
    src_x1 = min(width, width - tx)
    src_y0 = max(0, -ty)
    src_y1 = min(height, height - ty)

    dst_x0 = max(0, tx)
    dst_x1 = dst_x0 + (src_x1 - src_x0)
    dst_y0 = max(0, ty)
    dst_y1 = dst_y0 + (src_y1 - src_y0)

    translated[dst_y0:dst_y1, dst_x0:dst_x1] = base_image[src_y0:src_y1, src_x0:src_x1]
    return translated


class TestSyntheticTransformHelper:
    """
    Test Design Specification: make_transformed_channel()
    Module under test: tests/fixtures/align_synthetic.py

    Contract:
        Applies a known affine transform (rotation/scale around image center,
        then translation) to a grayscale image via one cv2.warpAffine call,
        and returns both transformed image and the exact 2x3 matrix used.

    Equivalence partitions:
        EP1  Identity transform                      -> identical output + identity matrix
        EP2  Pure translation                        -> deterministic shift and tx/ty matrix terms
        EP3  Pure rotation around center             -> center remains approximately stable
        EP4  Pure uniform scale                      -> matrix decomposes to expected scale
        EP5  Combined transform deterministic replay -> bit-identical outputs across runs
        EP6  Non-square image                        -> output shape preserved

    Boundary values:
        BV1  tx=0, ty=0, angle=0, scale=1
        BV2  Positive and negative integer translations
        BV3  Non-square dimensions (300x150)

    Exclusions:
        - Color (3D) images are not supported by this helper.
        - Perspective transforms are out of scope.

    Constraints:
        - Uses cv2.getRotationMatrix2D center convention.
        - Uses cv2.BORDER_CONSTANT fill with configurable border_value.
    """

    def test_identity_transform_returns_identical_image_and_identity_matrix(
        self, base_image_large: np.ndarray
    ) -> None:
        """Given identity parameters, when transforming, then output equals input and matrix is identity."""
        # Arrange
        base = base_image_large

        # Act
        warped, matrix = make_transformed_channel(base, tx=0.0, ty=0.0, angle_deg=0.0, scale=1.0)

        # Assert
        np.testing.assert_array_equal(warped, base)
        np.testing.assert_allclose(matrix, np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]), atol=1e-12)

    def test_pure_translation_matches_expected_pixel_shift_and_matrix_terms(
        self, base_image_large: np.ndarray
    ) -> None:
        """Given integer translation only, when transforming, then shifted image and matrix tx/ty match exactly."""
        # Arrange
        tx, ty = 10, -5
        base = base_image_large
        expected = _expected_translation(base, tx=tx, ty=ty, border_value=0)

        # Act
        warped, matrix = make_transformed_channel(base, tx=tx, ty=ty, angle_deg=0.0, scale=1.0)

        # Assert
        np.testing.assert_array_equal(warped, expected)
        assert matrix[0, 2] == pytest.approx(10.0)
        assert matrix[1, 2] == pytest.approx(-5.0)

    def test_pure_rotation_preserves_center_pixel_with_small_tolerance(
        self, base_image_large: np.ndarray
    ) -> None:
        """Given pure rotation around center, when transforming, then the affine matrix keeps the center coordinate fixed."""
        # Arrange
        base = base_image_large
        center_x = (base.shape[1] - 1) / 2.0
        center_y = (base.shape[0] - 1) / 2.0
        center_h = np.array([center_x, center_y, 1.0], dtype=np.float64)

        # Act
        _, matrix = make_transformed_channel(base, angle_deg=5.0)
        transformed_center = matrix @ center_h

        # Assert
        assert transformed_center[0] == pytest.approx(center_x, abs=1e-6)
        assert transformed_center[1] == pytest.approx(center_y, abs=1e-6)

    def test_pure_scale_decomposes_to_expected_scale(self, base_image_large: np.ndarray) -> None:
        """Given pure scale, when matrix is decomposed, then recovered scale matches the requested factor."""
        # Arrange
        requested_scale = 1.1

        # Act
        _, matrix = make_transformed_channel(base_image_large, scale=requested_scale)

        # Assert
        tx, ty, angle_deg, scale = decompose_affine_matrix(matrix)
        assert tx == pytest.approx(matrix[0, 2])
        assert ty == pytest.approx(matrix[1, 2])
        assert angle_deg == pytest.approx(0.0, abs=1e-7)
        assert scale == pytest.approx(requested_scale, abs=1e-7)

    def test_combined_transform_is_deterministic_for_repeated_calls(
        self, base_image_large: np.ndarray
    ) -> None:
        """Given fixed inputs, when called twice, then warped output and matrix are bit-identical."""
        # Arrange
        params = {"tx": 7.0, "ty": -3.0, "angle_deg": 1.7, "scale": 0.98}

        # Act
        warped_1, matrix_1 = make_transformed_channel(base_image_large, **params)
        warped_2, matrix_2 = make_transformed_channel(base_image_large, **params)

        # Assert
        np.testing.assert_array_equal(warped_1, warped_2)
        np.testing.assert_array_equal(matrix_1, matrix_2)

    def test_non_square_input_preserves_shape(self) -> None:
        """Given a non-square image, when transformed, then output shape matches input shape."""
        # Arrange
        base = np.full((300, 150), 127, dtype=np.uint8)
        base[40:80, 20:60] = 220

        # Act
        warped, _ = make_transformed_channel(base, tx=3.0, ty=4.0, angle_deg=2.0, scale=1.02)

        # Assert
        assert warped.shape == base.shape


class TestAffineDecompositionHelper:
    """
    Test Design Specification: decompose_affine_matrix()
    Module under test: tests/fixtures/align_synthetic.py

    Contract:
        Decomposes a partial-affine 2x3 matrix
        [[s*cos(a), -s*sin(a), tx], [s*sin(a), s*cos(a), ty]]
        into scalar components (tx, ty, angle_deg, scale), with angle normalized
        to (-180, 180], and raises ValueError on degenerate zero-scale matrices.

    Equivalence partitions:
        EP1  Identity matrix                    -> (0, 0, 0, 1)
        EP2  Valid partial-affine matrix        -> round-trip recovery within tolerance
        EP3  Degenerate zero-scale matrix       -> ValueError
        EP4  Angle boundary around +-180        -> normalized to documented interval

    Boundary values:
        BV1  scale = 1
        BV2  scale = 0
        BV3  angle = 180 and angle = -180

    Exclusions:
        - Shear decomposition is out of scope.
        - Perspective transforms are out of scope.

    Constraints:
        - Input must be shape (2, 3).
    """

    def test_decompose_identity_matrix_returns_expected_components(self) -> None:
        """Given an identity affine matrix, when decomposed, then tx/ty/angle/scale are identity values."""
        # Arrange
        matrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)

        # Act
        tx, ty, angle_deg, scale = decompose_affine_matrix(matrix)

        # Assert
        assert tx == pytest.approx(0.0)
        assert ty == pytest.approx(0.0)
        assert angle_deg == pytest.approx(0.0)
        assert scale == pytest.approx(1.0)

    def test_decompose_round_trip_recovers_known_parameters(self) -> None:
        """Given a known analytic partial-affine matrix, when decomposed, then original parameters are recovered."""
        # Arrange
        tx_true, ty_true, angle_true_deg, scale_true = 12.0, -7.0, 8.0, 1.03
        angle_rad = np.deg2rad(angle_true_deg)
        matrix = np.array(
            [
                [scale_true * np.cos(angle_rad), -scale_true * np.sin(angle_rad), tx_true],
                [scale_true * np.sin(angle_rad), scale_true * np.cos(angle_rad), ty_true],
            ],
            dtype=np.float64,
        )

        # Act
        tx, ty, angle_deg, scale = decompose_affine_matrix(matrix)

        # Assert
        assert tx == pytest.approx(tx_true, abs=1e-6)
        assert ty == pytest.approx(ty_true, abs=1e-6)
        assert angle_deg == pytest.approx(angle_true_deg, abs=1e-6)
        assert scale == pytest.approx(scale_true, abs=1e-6)

    def test_decompose_zero_matrix_raises_value_error(self) -> None:
        """Given a degenerate all-zero matrix, when decomposed, then a documented ValueError is raised."""
        # Arrange
        matrix = np.zeros((2, 3), dtype=np.float64)

        # Act / Assert
        with pytest.raises(ValueError, match="scale is zero"):
            decompose_affine_matrix(matrix)

    @pytest.mark.parametrize(
        "angle_deg",
        [
            180.0,  # BV3: positive boundary
            -180.0,  # BV3: negative boundary
        ],
        ids=["angle_180", "angle_minus_180"],
    )
    def test_angle_boundary_normalizes_to_documented_range(self, angle_deg: float) -> None:
        """Given angle at +-180 degrees, when decomposed, then result is normalized consistently to 180."""
        # Arrange
        angle_rad = np.deg2rad(angle_deg)
        matrix = np.array(
            [
                [np.cos(angle_rad), -np.sin(angle_rad), 0.0],
                [np.sin(angle_rad), np.cos(angle_rad), 0.0],
            ],
            dtype=np.float64,
        )

        # Act
        _, _, normalized_angle, _ = decompose_affine_matrix(matrix)

        # Assert
        assert normalized_angle == pytest.approx(180.0)


class TestSyntheticBaseImageFixtures:
    """
    Test Design Specification: base image fixtures
    Module under test: tests/fixtures/align_synthetic.py

    Contract:
        Supplies deterministic grayscale fixture variants for alignment testing:
        large feature-rich, small feature-rich, flat featureless, repetitive,
        and sparse-feature images.

    Equivalence partitions:
        EP1  Flat fixture                      -> zero ORB keypoints
        EP2  Large fixture                     -> high ORB keypoint count
        EP3  Repetitive fixture                -> strong periodic self-similarity

    Boundary values:
        BV1  Flat texture (no local contrast gradients)
        BV2  Keypoint richness threshold >= 500 for large image
        BV3  One-period roll for periodicity checks

    Exclusions:
        - Exact keypoint coordinates are not asserted.
        - ORB descriptor values are not asserted.

    Constraints:
        - ORB behavior can vary slightly by OpenCV version.
    """

    def test_flat_fixture_has_zero_orb_keypoints(self, base_image_flat: np.ndarray) -> None:
        """Given the flat fixture, when ORB detects features, then zero keypoints are returned."""
        # Arrange
        orb = cv2.ORB_create(1000)

        # Act
        keypoints, _ = orb.detectAndCompute(base_image_flat, None)

        # Assert
        assert len(keypoints) == 0

    def test_large_fixture_has_minimum_orb_keypoint_count(self, base_image_large: np.ndarray) -> None:
        """Given the large feature-rich fixture, when ORB detects features, then at least 500 keypoints are found."""
        # Arrange
        orb = cv2.ORB_create(1000)

        # Act
        keypoints, _ = orb.detectAndCompute(base_image_large, None)

        # Assert
        assert len(keypoints) >= 500

    def test_repetitive_fixture_has_high_periodic_self_similarity(
        self, base_image_repetitive: np.ndarray
    ) -> None:
        """Given repetitive texture fixture, when rolled by one period, then normalized similarity remains high."""
        # Arrange
        rolled = np.roll(base_image_repetitive, shift=16, axis=1)
        a = base_image_repetitive.astype(np.float32).ravel()
        b = rolled.astype(np.float32).ravel()

        # Act
        similarity = float(np.corrcoef(a, b)[0, 1])

        # Assert
        assert similarity > 0.9


class TestChannelsCloseAssertionHelper:
    """
    Test Design Specification: assert_channels_close()
    Module under test: tests/fixtures/align_synthetic.py

    Contract:
        Computes MAE between aligned and reference images, defaulting to
        5-percent border exclusion, and raises AssertionError with diagnostics
        when MAE exceeds a threshold.

    Equivalence partitions:
        EP1  Identical arrays                  -> pass (MAE=0)
        EP2  Small deterministic difference    -> pass if threshold is above MAE
        EP3  Difference above threshold        -> fail with informative message
        EP4  Differences confined to border    -> pass with default border exclusion
        EP5  Same border-only difference       -> fail when full image region is forced

    Boundary values:
        BV1  max_mae equals observed MAE
        BV2  max_mae just below observed MAE
        BV3  Border-only modifications

    Exclusions:
        - Multi-channel arrays are out of scope.

    Constraints:
        - Expects same shape inputs.
    """

    def test_identical_images_pass_with_zero_error(self, base_image_small: np.ndarray) -> None:
        """Given identical arrays, when compared, then assertion helper passes."""
        # Arrange
        aligned = base_image_small.copy()
        reference = base_image_small.copy()

        # Act
        assert_channels_close(aligned, reference, max_mae=0.0)

        # Assert
        assert True

    def test_small_offset_passes_when_threshold_exceeds_mae(self) -> None:
        """Given a known MAE offset, when threshold is above it, then assertion helper passes."""
        # Arrange
        reference = np.full((32, 32), 100, dtype=np.uint8)
        aligned = np.full((32, 32), 103, dtype=np.uint8)

        # Act
        assert_channels_close(aligned, reference, max_mae=3.1, region=(slice(0, 32), slice(0, 32)))

        # Assert
        assert True

    def test_small_offset_fails_when_threshold_is_below_mae(self) -> None:
        """Given a known MAE offset, when threshold is below it, then assertion helper raises AssertionError."""
        # Arrange
        reference = np.full((32, 32), 100, dtype=np.uint8)
        aligned = np.full((32, 32), 103, dtype=np.uint8)

        # Act / Assert
        with pytest.raises(AssertionError, match="mae="):
            assert_channels_close(aligned, reference, max_mae=2.9, region=(slice(0, 32), slice(0, 32)))

    def test_border_only_difference_passes_with_default_border_exclusion(self) -> None:
        """Given border-only differences, when using default comparison region, then assertion helper passes."""
        # Arrange
        reference = np.full((100, 100), 120, dtype=np.uint8)
        aligned = reference.copy()
        aligned[:5, :] = 0
        aligned[-5:, :] = 0
        aligned[:, :5] = 0
        aligned[:, -5:] = 0

        # Act
        assert_channels_close(aligned, reference, max_mae=1.0)

        # Assert
        assert True

    def test_border_only_difference_fails_when_full_region_is_used(self) -> None:
        """Given border-only differences, when full image is compared, then assertion helper raises AssertionError."""
        # Arrange
        reference = np.full((100, 100), 120, dtype=np.uint8)
        aligned = reference.copy()
        aligned[:5, :] = 0
        aligned[-5:, :] = 0
        aligned[:, :5] = 0
        aligned[:, -5:] = 0

        # Act / Assert
        with pytest.raises(AssertionError):
            assert_channels_close(aligned, reference, max_mae=1.0, region=(slice(0, 100), slice(0, 100)))


class TestAlignmentAlgorithmInterface:
    """
    Test Design Specification: run_alignment_with_algorithms()
    Module under test: tests/fixtures/align_synthetic.py

    Contract:
        Provides a pluggable interface for synthetic alignment tests so a test
        can execute one algorithm directly or a chain of algorithms in
        fallback order. Returns the aligned outputs and the algorithm name used.

    Equivalence partitions:
        EP1  Single successful algorithm           -> returns result with selected name
        EP2  First fails, second succeeds          -> fallback selects second algorithm
        EP3  All algorithms fail                   -> raises the last error
        EP4  Empty algorithm list                  -> ValueError

    Boundary values:
        BV1  Exactly one algorithm in the list
        BV2  Two algorithms with first failing
        BV3  Zero algorithms

    Exclusions:
        - Confidence scoring and diagnostics are out of scope here.
        - Method-specific transform quality is tested elsewhere.

    Constraints:
        - Algorithm adapter must follow AlignmentCallable signature.
        - Input arrays are passed through unchanged to the selected algorithm.
    """

    def test_single_algorithm_adapter_uses_orb_implementation(
        self,
        align_algorithm_orb: AlignmentAlgorithm,
        base_image_large: np.ndarray,
    ) -> None:
        """Given one algorithm adapter, when executed, then that algorithm is used and outputs contain three channels."""
        # Arrange
        grayscale_images = [base_image_large.copy(), base_image_large.copy(), base_image_large.copy()]
        rgb_base = np.stack([base_image_large] * 3, axis=2)
        rgb_images = [rgb_base.copy(), rgb_base.copy(), rgb_base.copy()]

        # Act
        result = run_alignment_with_algorithms([align_algorithm_orb], grayscale_images, rgb_images)

        # Assert
        assert isinstance(result, AlignmentRunResult)
        assert result.algorithm_name == "orb"
        assert len(result.aligned_grayscale) == 3
        assert len(result.aligned_rgb) == 3

    def test_fallback_chain_uses_second_algorithm_when_first_fails(self) -> None:
        """Given two algorithms with the first failing, when executed, then the second algorithm result is returned."""
        # Arrange
        grayscale_images = [np.full((8, 8), 11, dtype=np.uint8) for _ in range(3)]
        rgb_images = [np.stack([img] * 3, axis=2) for img in grayscale_images]

        def failing_algorithm(
            grayscale: list[np.ndarray], rgb: list[np.ndarray]
        ) -> tuple[list[np.ndarray], list[np.ndarray]]:
            raise RuntimeError("primary failed")

        def identity_algorithm(
            grayscale: list[np.ndarray], rgb: list[np.ndarray]
        ) -> tuple[list[np.ndarray], list[np.ndarray]]:
            return [img.copy() for img in grayscale], [img.copy() for img in rgb]

        algorithms = [
            AlignmentAlgorithm(name="primary", align=failing_algorithm),
            AlignmentAlgorithm(name="secondary", align=identity_algorithm),
        ]

        # Act
        result = run_alignment_with_algorithms(algorithms, grayscale_images, rgb_images)

        # Assert
        assert result.algorithm_name == "secondary"
        np.testing.assert_array_equal(result.aligned_grayscale[0], grayscale_images[0])
        np.testing.assert_array_equal(result.aligned_rgb[0], rgb_images[0])

    def test_all_failing_algorithms_raise_the_last_error(self) -> None:
        """Given all algorithms failing, when executed, then the final algorithm exception is re-raised."""
        # Arrange
        grayscale_images = [np.full((8, 8), 11, dtype=np.uint8) for _ in range(3)]
        rgb_images = [np.stack([img] * 3, axis=2) for img in grayscale_images]

        def fail_first(
            grayscale: list[np.ndarray], rgb: list[np.ndarray]
        ) -> tuple[list[np.ndarray], list[np.ndarray]]:
            raise RuntimeError("first failure")

        def fail_second(
            grayscale: list[np.ndarray], rgb: list[np.ndarray]
        ) -> tuple[list[np.ndarray], list[np.ndarray]]:
            raise ValueError("second failure")

        algorithms = [
            AlignmentAlgorithm(name="first", align=fail_first),
            AlignmentAlgorithm(name="second", align=fail_second),
        ]

        # Act / Assert
        with pytest.raises(ValueError, match="second failure"):
            run_alignment_with_algorithms(algorithms, grayscale_images, rgb_images)

    def test_empty_algorithm_list_raises_value_error(self) -> None:
        """Given no algorithms, when executed, then ValueError is raised."""
        # Arrange
        grayscale_images = [np.full((8, 8), 11, dtype=np.uint8) for _ in range(3)]
        rgb_images = [np.stack([img] * 3, axis=2) for img in grayscale_images]

        # Act / Assert
        with pytest.raises(ValueError, match="At least one alignment algorithm"):
            run_alignment_with_algorithms([], grayscale_images, rgb_images)
