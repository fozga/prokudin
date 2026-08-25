"""Synthetic fixtures and helpers for alignment robustness tests."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, Sequence

import cv2
import numpy as np
import pytest


class AlignmentCallable(Protocol):
    """Callable protocol for pluggable alignment implementations."""

    def __call__(
        self, grayscale_images: list[np.ndarray], rgb_images: list[np.ndarray]
    ) -> tuple[list[np.ndarray], list[np.ndarray]]:
        """Return aligned grayscale and RGB image lists."""


@dataclass(frozen=True)
class AlignmentAlgorithm:
    """Named algorithm adapter used by synthetic alignment tests."""

    name: str
    align: AlignmentCallable


@dataclass(frozen=True)
class AlignmentRunResult:
    """Alignment outputs plus the algorithm name that produced them."""

    algorithm_name: str
    aligned_grayscale: list[np.ndarray]
    aligned_rgb: list[np.ndarray]


def run_alignment_with_algorithms(
    algorithms: Sequence[AlignmentAlgorithm],
    grayscale_images: list[np.ndarray],
    rgb_images: list[np.ndarray],
) -> AlignmentRunResult:
    """Run algorithms in order and return first successful result."""
    if len(algorithms) == 0:
        raise ValueError("At least one alignment algorithm is required")

    last_error: Exception | None = None
    for algorithm in algorithms:
        try:
            aligned_grayscale, aligned_rgb = algorithm.align(grayscale_images, rgb_images)
            return AlignmentRunResult(
                algorithm_name=algorithm.name,
                aligned_grayscale=aligned_grayscale,
                aligned_rgb=aligned_rgb,
            )
        except Exception as exc:  # pragma: no cover - failure path exercised by tests
            last_error = exc

    assert last_error is not None
    raise last_error


def _checkerboard(height: int, width: int, square_size: int, low: int, high: int) -> np.ndarray:
    """Create a deterministic checkerboard image."""
    yy, xx = np.indices((height, width))
    pattern = ((yy // square_size) + (xx // square_size)) % 2
    return np.where(pattern == 0, high, low).astype(np.uint8)


def make_transformed_channel(
    base_image: np.ndarray,
    tx: float = 0.0,
    ty: float = 0.0,
    angle_deg: float = 0.0,
    scale: float = 1.0,
    border_value: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply a known center-based affine transform and return image plus matrix."""
    if base_image.ndim != 2:
        raise ValueError("base_image must be a 2D grayscale array")

    height, width = base_image.shape
    center = ((width - 1) / 2.0, (height - 1) / 2.0)

    matrix = cv2.getRotationMatrix2D(center, angle_deg, scale).astype(np.float64)
    matrix[0, 2] += float(tx)
    matrix[1, 2] += float(ty)

    warped = cv2.warpAffine(
        base_image,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=int(border_value),
    )
    return warped, matrix


def decompose_affine_matrix(matrix: np.ndarray) -> tuple[float, float, float, float]:
    """Decompose a 2x3 partial affine matrix into tx, ty, angle_deg, scale."""
    if matrix.shape != (2, 3):
        raise ValueError(f"Expected matrix shape (2, 3), got {matrix.shape}")

    m00 = float(matrix[0, 0])
    m10 = float(matrix[1, 0])
    tx = float(matrix[0, 2])
    ty = float(matrix[1, 2])

    scale = float(np.sqrt((m00 * m00) + (m10 * m10)))
    if np.isclose(scale, 0.0):
        raise ValueError("Degenerate affine matrix: scale is zero")

    angle_deg = float(np.degrees(np.arctan2(m10, m00)))
    angle_deg = ((angle_deg + 180.0) % 360.0) - 180.0
    if np.isclose(angle_deg, -180.0):
        angle_deg = 180.0

    return tx, ty, angle_deg, scale


@pytest.fixture
def base_image_large() -> np.ndarray:
    """Feature-rich 512x512 image with checkerboard, noise, and asymmetric blobs."""
    image = _checkerboard(512, 512, square_size=32, low=45, high=210).astype(np.int16)
    rng = np.random.default_rng(12345)
    noise = rng.normal(loc=0.0, scale=5.0, size=image.shape)
    image = image + noise.astype(np.int16)

    for center, radius, value in [
        ((89, 137), 14, 25),
        ((411, 93), 18, 240),
        ((147, 398), 12, 15),
        ((362, 333), 20, 235),
        ((259, 211), 10, 120),
    ]:
        cv2.circle(image, center, radius, int(value), thickness=-1)

    return np.clip(image, 0, 255).astype(np.uint8)


@pytest.fixture
def base_image_small() -> np.ndarray:
    """Feature-rich but compact 64x64 image for small-image edge cases."""
    image = _checkerboard(64, 64, square_size=8, low=55, high=200).astype(np.int16)
    rng = np.random.default_rng(2026)
    noise = rng.normal(loc=0.0, scale=2.0, size=image.shape)
    image = image + noise.astype(np.int16)

    cv2.circle(image, (14, 19), 4, 12, thickness=-1)
    cv2.circle(image, (49, 41), 5, 244, thickness=-1)

    return np.clip(image, 0, 255).astype(np.uint8)


@pytest.fixture
def base_image_flat() -> np.ndarray:
    """Uniform 256x256 featureless image for failure-mode tests."""
    return np.full((256, 256), 128, dtype=np.uint8)


@pytest.fixture
def base_image_repetitive() -> np.ndarray:
    """Highly periodic 256x256 dot-grid image for ambiguous-match tests."""
    image = np.full((256, 256), 128, dtype=np.uint8)
    period = 16
    for y in range(0, 256, period):
        for x in range(0, 256, period):
            cv2.circle(image, (x + 4, y + 4), 2, 220, thickness=-1)
            cv2.circle(image, (x + 12, y + 12), 2, 36, thickness=-1)
    return image


@pytest.fixture
def base_image_sparse_features() -> np.ndarray:
    """Mostly flat 256x256 image with only a few marks near one corner."""
    image = np.full((256, 256), 124, dtype=np.uint8)
    cv2.circle(image, (20, 24), 3, 240, thickness=-1)
    cv2.circle(image, (30, 18), 2, 20, thickness=-1)
    cv2.rectangle(image, (12, 34), (16, 38), 235, thickness=-1)
    cv2.line(image, (26, 30), (34, 36), 30, thickness=1)
    return image


def assert_channels_close(
    aligned: np.ndarray,
    reference: np.ndarray,
    max_mae: float,
    region: Optional[tuple[slice, slice]] = None,
) -> None:
    """Assert that two images are close under MAE, with border exclusion by default."""
    if aligned.shape != reference.shape:
        raise AssertionError(
            f"Shape mismatch: aligned.shape={aligned.shape}, reference.shape={reference.shape}"
        )

    if region is None:
        margin_y = max(1, int(round(aligned.shape[0] * 0.05)))
        margin_x = max(1, int(round(aligned.shape[1] * 0.05)))
        region = (
            slice(margin_y, aligned.shape[0] - margin_y),
            slice(margin_x, aligned.shape[1] - margin_x),
        )

    aligned_roi = aligned[region]
    reference_roi = reference[region]
    mae = float(np.mean(np.abs(aligned_roi.astype(np.float32) - reference_roi.astype(np.float32))))

    if mae <= float(max_mae):
        return

    diff = cv2.absdiff(aligned.astype(np.uint8), reference.astype(np.uint8))
    diff_path = Path(tempfile.mkdtemp(prefix="align-diff-")) / "diff.png"
    heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
    cv2.imwrite(str(diff_path), heatmap)

    raise AssertionError(
        "MAE comparison failed: "
        f"mae={mae:.4f} > max_mae={max_mae:.4f}; "
        f"aligned.shape={aligned.shape}; reference.shape={reference.shape}; "
        f"region=({region[0].start}:{region[0].stop}, {region[1].start}:{region[1].stop}); "
        f"diff_image={diff_path}"
    )
