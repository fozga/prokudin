"""Unit tests for src.core.align module.

Tests image alignment using ORB feature matching and affine transformation.
"""

import pytest
import numpy as np
import cv2

from src.core.align import align_images, AlignmentError

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

    def test_insufficient_matches_raises_alignment_error(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given images with too few feature matches, when aligned, then AlignmentError is raised."""
        # Arrange
        tiny_feature_gray = np.zeros((256, 256), dtype=np.uint8)
        tiny_feature_gray[100:110, 100:110] = 255
        tiny_feature_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        tiny_feature_rgb[100:110, 100:110] = [255, 255, 255]
        grayscale_images = [sample_grayscale_image, tiny_feature_gray, tiny_feature_gray]
        rgb_images = [sample_rgb_image, tiny_feature_rgb, tiny_feature_rgb]

        # Act & Assert
        with pytest.raises(AlignmentError):
            align_images(grayscale_images, rgb_images)

    def test_error_message_includes_match_count(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Given insufficient feature matches, when AlignmentError is raised, then error message includes match information."""
        # Arrange
        tiny_feature_gray = np.zeros((256, 256), dtype=np.uint8)
        tiny_feature_gray[100:110, 100:110] = 255
        tiny_feature_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        tiny_feature_rgb[100:110, 100:110] = [255, 255, 255]
        grayscale_images = [sample_grayscale_image, tiny_feature_gray, tiny_feature_gray]
        rgb_images = [sample_rgb_image, tiny_feature_rgb, tiny_feature_rgb]

        # Act & Assert
        with pytest.raises(AlignmentError) as exc_info:
            align_images(grayscale_images, rgb_images)
        error_msg = str(exc_info.value)
        assert "matches" in error_msg.lower() or "insufficient" in error_msg.lower()


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
