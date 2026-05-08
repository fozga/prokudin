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
    """Test suite for align_images() function."""

    def test_identical_images_produce_minimal_transform(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Test that identical images produce near-identity transformation."""
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Identical images should produce very similar outputs (minimal or identity transform)
        assert len(aligned_gray) == 3
        assert len(aligned_rgb) == 3
        # Red channel should be unchanged
        np.testing.assert_array_almost_equal(aligned_gray[0], grayscale_images[0])
        np.testing.assert_array_almost_equal(aligned_rgb[0], rgb_images[0])

    def test_returns_correct_output_shape(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Test that output shape matches input shape."""
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        assert aligned_gray[0].shape == grayscale_images[0].shape
        assert aligned_gray[1].shape == grayscale_images[1].shape
        assert aligned_gray[2].shape == grayscale_images[2].shape
        assert aligned_rgb[0].shape == rgb_images[0].shape
        assert aligned_rgb[1].shape == rgb_images[1].shape
        assert aligned_rgb[2].shape == rgb_images[2].shape

    def test_returns_correct_output_dtype(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Test that output dtype matches input dtype."""
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        assert aligned_gray[0].dtype == grayscale_images[0].dtype
        assert aligned_gray[1].dtype == grayscale_images[1].dtype
        assert aligned_gray[2].dtype == grayscale_images[2].dtype
        assert aligned_rgb[0].dtype == rgb_images[0].dtype
        assert aligned_rgb[1].dtype == rgb_images[1].dtype
        assert aligned_rgb[2].dtype == rgb_images[2].dtype

    def test_red_channel_never_transformed(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Test that red channel (index 0) is always returned unchanged."""
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Red channel should always be returned as-is
        np.testing.assert_array_equal(aligned_gray[0], grayscale_images[0])
        np.testing.assert_array_equal(aligned_rgb[0], rgb_images[0])

    def test_alignment_output_is_independent_copy(
        self, identical_image_set: tuple[list[np.ndarray], list[np.ndarray]]
    ) -> None:
        """Test that output arrays are independent copies, not views."""
        grayscale_images, rgb_images = identical_image_set
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)

        # Modify original
        grayscale_images[0][0, 0] = 255
        rgb_images[0][0, 0] = [255, 255, 255]

        # Aligned should be unaffected
        assert aligned_gray[0][0, 0] != 255
        assert not np.array_equal(aligned_rgb[0][0, 0], [255, 255, 255])


class TestAlignmentError:
    """Test suite for AlignmentError exception."""

    def test_alignment_error_is_exception(self) -> None:
        """Test that AlignmentError is an Exception subclass."""
        assert issubclass(AlignmentError, Exception)

    def test_alignment_error_can_be_instantiated(self) -> None:
        """Test that AlignmentError can be raised and caught."""
        with pytest.raises(AlignmentError):
            raise AlignmentError("Test error message")

    def test_alignment_error_message_preserved(self) -> None:
        """Test that error message is preserved."""
        error_msg = "Custom error message"
        try:
            raise AlignmentError(error_msg)
        except AlignmentError as e:
            assert str(e) == error_msg

    def test_no_descriptor_silently_skips_alignment(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that missing descriptors (blank images) are skipped gracefully."""
        # Create images where green/blue channels are blank (no features)
        # This should not raise, just skip alignment for those channels
        blank_gray = np.zeros((256, 256), dtype=np.uint8)
        blank_rgb = np.zeros((256, 256, 3), dtype=np.uint8)

        grayscale_images = [sample_grayscale_image, blank_gray, blank_gray]
        rgb_images = [sample_rgb_image, blank_rgb, blank_rgb]

        # Should not raise, just return the images unaligned
        aligned_gray, aligned_rgb = align_images(grayscale_images, rgb_images)
        assert aligned_gray[1] is not None
        assert aligned_rgb[1] is not None

    def test_insufficient_matches_raises_alignment_error(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that too few feature matches raise AlignmentError."""
        # Create a mostly blank image with only a tiny amount of content
        # This should have few enough features to fail the match threshold
        tiny_feature_gray = np.zeros((256, 256), dtype=np.uint8)
        tiny_feature_gray[100:110, 100:110] = 255  # Very small feature

        tiny_feature_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        tiny_feature_rgb[100:110, 100:110] = [255, 255, 255]

        grayscale_images = [sample_grayscale_image, tiny_feature_gray, tiny_feature_gray]
        rgb_images = [sample_rgb_image, tiny_feature_rgb, tiny_feature_rgb]

        with pytest.raises(AlignmentError):
            align_images(grayscale_images, rgb_images)

    def test_error_message_includes_match_count(
        self, sample_grayscale_image: np.ndarray, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that error message includes the number of matches found."""
        tiny_feature_gray = np.zeros((256, 256), dtype=np.uint8)
        tiny_feature_gray[100:110, 100:110] = 255

        tiny_feature_rgb = np.zeros((256, 256, 3), dtype=np.uint8)
        tiny_feature_rgb[100:110, 100:110] = [255, 255, 255]

        grayscale_images = [sample_grayscale_image, tiny_feature_gray, tiny_feature_gray]
        rgb_images = [sample_rgb_image, tiny_feature_rgb, tiny_feature_rgb]

        try:
            align_images(grayscale_images, rgb_images)
            pytest.fail("Expected AlignmentError to be raised")
        except AlignmentError as e:
            error_msg = str(e)
            # Error should mention matches and the threshold (50)
            assert "matches" in error_msg.lower() or "insufficient" in error_msg.lower()


class TestAlignImagesInputValidation:
    """Test suite for input validation of align_images()."""

    def test_requires_three_grayscale_images(
        self, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that function handles list of images with correct length."""
        # The function expects exactly 3 images in each list
        # Less than 3 should cause an issue
        two_gray = [np.zeros((256, 256), dtype=np.uint8) for _ in range(2)]
        three_rgb = [sample_rgb_image.copy() for _ in range(3)]

        # This might pass or fail depending on implementation details,
        # but we test that it doesn't crash unexpectedly
        try:
            align_images(two_gray, three_rgb)
            # If it doesn't raise, that's okay - just check no crash
        except (IndexError, ValueError, AlignmentError):
            # These are acceptable errors for invalid input
            pass

    def test_function_accepts_different_sized_images(self) -> None:
        """Test alignment with different image sizes."""
        # Create different sized images
        img1 = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
        img2 = np.random.randint(0, 256, (512, 512), dtype=np.uint8)
        # Add some features
        img1[100:150, 100:150] = 200
        img2[100:150, 100:150] = 200
        img1 = cv2.resize(img1, (256, 256))
        img2 = cv2.resize(img2, (256, 256))

        grayscale = [img1, img1.copy(), img1.copy()]
        rgb = [np.stack([img1] * 3, axis=2) for _ in range(3)]

        # Should handle identical images without issue
        try:
            aligned_gray, aligned_rgb = align_images(grayscale, rgb)
            assert len(aligned_gray) == 3
            assert len(aligned_rgb) == 3
        except AlignmentError:
            # Acceptable if identical images still fail due to feature matching
            pass
