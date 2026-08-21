# Copyright (C) 2025 fozga
#
# This file is part of Prokudin.
#
# Prokudin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prokudin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prokudin.  If not, see <https://www.gnu.org/licenses/>.

"""
Image alignment utilities for RGB channel processing.

Aligns green and blue channels to the red channel using a cascaded pipeline:
1. ORB feature matching with the requested degrees of freedom (DOF).
2. Phase correlation (translation only) if ORB fails or fails the sanity check.
3. Unmodified passthrough if all methods fail.

Sanity checks reject transforms with rotation > SANITY_MAX_ROTATION_DEG or scale
outside [SANITY_MIN_SCALE, SANITY_MAX_SCALE].
"""

import enum
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2  # type: ignore
import numpy as np

# ---------------------------------------------------------------------------
# Public constants – sanity thresholds
# ---------------------------------------------------------------------------

SANITY_MAX_ROTATION_DEG: float = 5.0
SANITY_MIN_SCALE: float = 0.8
SANITY_MAX_SCALE: float = 1.2

# Minimum ORB feature matches for a reliable transform estimate
_MIN_ORB_MATCHES: int = 50


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class AlignmentDOF(enum.Enum):
    """Degrees of freedom permitted during alignment.

    Controls how many geometric parameters are optimised when registering
    channels to the red reference.

    Values
    ------
    TRANSLATION
        Only horizontal and vertical shift (2 DOF).  Rotation and scale are
        forced to 0° and 1.0 respectively.
    TRANSLATION_ROTATION
        Shift plus in-plane rotation (3 DOF).  Scale is forced to 1.0.
    TRANSLATION_ROTATION_SCALE
        Shift, rotation, and uniform scale (4 DOF).  This is the default and
        matches the behaviour of ``estimateAffinePartial2D``.
    FULL_AFFINE
        Full six-parameter affine transform including shear and non-uniform
        scale (6 DOF).  Uses ``estimateAffine2D``.
    """

    TRANSLATION = "translation"
    TRANSLATION_ROTATION = "translation_rotation"
    TRANSLATION_ROTATION_SCALE = "translation_rotation_scale"
    FULL_AFFINE = "full_affine"


@dataclass
class TransformParams:
    """Geometric parameters extracted from a 2×3 affine matrix.

    All values are for a single channel relative to the red reference.
    The red channel always has the identity transform (all zeros / scale 1).

    Attributes
    ----------
    translation_x : float
        Horizontal displacement in pixels (positive = right).
    translation_y : float
        Vertical displacement in pixels (positive = down).
    rotation_deg : float
        Counter-clockwise rotation in degrees.
    scale : float
        Uniform scale factor (1.0 = no change).
    """

    translation_x: float = 0.0
    translation_y: float = 0.0
    rotation_deg: float = 0.0
    scale: float = 1.0


@dataclass
class AlignmentResult:
    """Full output of the alignment pipeline.

    Attributes
    ----------
    aligned_grayscale : list of np.ndarray
        Three aligned grayscale images [R, G, B].
    aligned_rgb : list of np.ndarray
        Three aligned RGB images [R, G, B].
    method_used : str
        Human-readable name of the method that produced the final result
        (e.g. ``"ORB"``, ``"phase correlation"``, ``"unaligned"``).
    channel_params : list of TransformParams
        Per-channel transform parameters in [R, G, B] order.
        The red channel entry is always the identity.
    fallback_triggered : bool
        ``True`` when ORB failed and a fallback method was used.
    warning : str or None
        Optional human-readable warning (e.g. sanity check failure reason).
    """

    aligned_grayscale: List[np.ndarray]
    aligned_rgb: List[np.ndarray]
    method_used: str
    channel_params: List[TransformParams] = field(default_factory=lambda: [TransformParams() for _ in range(3)])
    fallback_triggered: bool = False
    warning: Optional[str] = None


# ---------------------------------------------------------------------------
# Public exceptions
# ---------------------------------------------------------------------------


class AlignmentError(Exception):
    """Raised when all alignment methods fail for a channel."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_transform_params(matrix: np.ndarray) -> TransformParams:
    """Extract human-readable parameters from a 2×3 affine matrix.

    For a partial-affine matrix of the form
    ``[[a, -b, tx], [b, a, ty]]`` the uniform scale is
    ``sqrt(a**2 + b**2)`` and rotation is ``atan2(b, a)``.

    For a full-affine matrix the scale estimate uses the geometric mean of
    the two axis scales and rotation is taken from the first column.

    Args:
        matrix: 2×3 float32 affine matrix.

    Returns:
        TransformParams with extracted values.
    """
    a, b = float(matrix[0, 0]), float(matrix[1, 0])
    tx = float(matrix[0, 2])
    ty = float(matrix[1, 2])

    scale = math.sqrt(a * a + b * b)
    rotation_deg = math.degrees(math.atan2(b, a))

    return TransformParams(
        translation_x=tx,
        translation_y=ty,
        rotation_deg=rotation_deg,
        scale=scale,
    )


def _check_sanity(params: TransformParams) -> Optional[str]:
    """Return a warning string if the transform exceeds reasonable bounds, else None.

    A transform is considered unreasonable when:
    - |rotation| > SANITY_MAX_ROTATION_DEG, or
    - scale < SANITY_MIN_SCALE, or
    - scale > SANITY_MAX_SCALE.

    Args:
        params: Transform parameters to validate.

    Returns:
        A descriptive warning string, or ``None`` if the transform is sane.
    """
    if abs(params.rotation_deg) > SANITY_MAX_ROTATION_DEG:
        return f"rotation {params.rotation_deg:.1f}° exceeds ±{SANITY_MAX_ROTATION_DEG}°"
    if params.scale < SANITY_MIN_SCALE or params.scale > SANITY_MAX_SCALE:
        return f"scale {params.scale:.3f} outside [{SANITY_MIN_SCALE}, {SANITY_MAX_SCALE}]"
    return None


def _restrict_matrix_to_dof(matrix: np.ndarray, dof: AlignmentDOF) -> np.ndarray:
    """Return a new matrix restricted to the given degrees of freedom.

    ``TRANSLATION_ROTATION_SCALE`` and ``FULL_AFFINE`` are passed through
    unchanged (the estimation step already uses the appropriate model).
    ``TRANSLATION`` and ``TRANSLATION_ROTATION`` rebuild the matrix from the
    extracted parameters, zeroing out the components outside the DOF.

    Args:
        matrix: 2×3 float32 affine matrix from OpenCV estimation.
        dof: Target degrees of freedom.

    Returns:
        A 2×3 float32 matrix restricted to ``dof``.
    """
    if dof in (AlignmentDOF.TRANSLATION_ROTATION_SCALE, AlignmentDOF.FULL_AFFINE):
        return matrix

    params = _extract_transform_params(matrix)
    tx, ty = params.translation_x, params.translation_y

    if dof == AlignmentDOF.TRANSLATION:
        return np.array([[1.0, 0.0, tx], [0.0, 1.0, ty]], dtype=np.float32)

    # TRANSLATION_ROTATION: scale forced to 1.0
    angle_rad = math.radians(params.rotation_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return np.array([[cos_a, -sin_a, tx], [sin_a, cos_a, ty]], dtype=np.float32)


def _translation_matrix(dx: float, dy: float) -> np.ndarray:
    """Build a 2×3 affine matrix for a pure translation.

    Args:
        dx: Horizontal displacement in pixels.
        dy: Vertical displacement in pixels.

    Returns:
        2×3 float32 translation matrix.
    """
    return np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float32)


# ---------------------------------------------------------------------------
# Per-method alignment functions
# ---------------------------------------------------------------------------


def _estimate_orb_matrices(
    grayscale_images: List[np.ndarray],
    dof: AlignmentDOF,
) -> List[Optional[np.ndarray]]:
    """Estimate per-channel affine matrices using ORB feature matching.

    Attempts to align channels 1 (Green) and 2 (Blue) to channel 0 (Red).
    Channel 0 always receives ``None`` (identity is applied by the caller).

    Args:
        grayscale_images: Three grayscale images [R, G, B].
        dof: Degrees of freedom to apply after estimation.

    Returns:
        List of three matrices (or ``None`` for the red channel or any channel
        that could not be matched).

    Raises:
        AlignmentError: If feature matching produces too few matches or the
            transform estimator returns ``None`` for any channel.
    """
    orb = cv2.ORB_create(1000)  # type: ignore[attr-defined]  # pylint: disable=E1101
    keypoints = []
    descriptors = []

    for img in grayscale_images:
        kp, des = orb.detectAndCompute(img, None)
        keypoints.append(kp)
        descriptors.append(des)

    matrices: List[Optional[np.ndarray]] = [None, None, None]

    for i in range(1, 3):
        if descriptors[0] is None or descriptors[i] is None or descriptors[0].size == 0 or descriptors[i].size == 0:
            # No features: leave matrix as None (caller keeps channel unchanged)
            continue

        matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(  # pylint: disable=E1101
            descriptors[0], descriptors[i]
        )

        if len(matches) < _MIN_ORB_MATCHES:
            raise AlignmentError(f"Insufficient matches ({len(matches)}/{_MIN_ORB_MATCHES})")

        src_pts = np.array([keypoints[i][m.trainIdx].pt for m in matches], dtype=np.float32).reshape((-1, 1, 2))
        dst_pts = np.array([keypoints[0][m.queryIdx].pt for m in matches], dtype=np.float32).reshape((-1, 1, 2))

        if dof == AlignmentDOF.FULL_AFFINE:
            matrix, _ = cv2.estimateAffine2D(src_pts, dst_pts)  # pylint: disable=E1101
        else:
            matrix, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts)  # pylint: disable=E1101

        if matrix is None:
            raise AlignmentError(f"Failed to estimate transformation for channel {i}")

        matrices[i] = _restrict_matrix_to_dof(matrix.astype(np.float32), dof)

    return matrices


def _estimate_phase_matrices(
    grayscale_images: List[np.ndarray],
) -> List[Optional[np.ndarray]]:
    """Estimate per-channel translation matrices using phase correlation.

    Phase correlation is more robust than feature matching for images with
    few texture features, but only estimates translation (2 DOF).

    Args:
        grayscale_images: Three grayscale images [R, G, B].

    Returns:
        List of three matrices. Channel 0 is always ``None``.
    """
    ref = grayscale_images[0].astype(np.float32)
    matrices: List[Optional[np.ndarray]] = [None, None, None]

    for i in range(1, 3):
        src = grayscale_images[i].astype(np.float32)
        (dx, dy), _response = cv2.phaseCorrelate(ref, src)  # pylint: disable=E1101
        matrices[i] = _translation_matrix(-dx, -dy)

    return matrices


def _apply_matrices(
    grayscale_images: List[np.ndarray],
    rgb_images: List[np.ndarray],
    matrices: List[Optional[np.ndarray]],
) -> Tuple[List[np.ndarray], List[np.ndarray], List[TransformParams]]:
    """Warp images using the provided matrices and extract transform parameters.

    Channel 0 is always copied unchanged.  For channels 1 and 2 a ``None``
    matrix results in an unchanged copy (identity fallback).

    Args:
        grayscale_images: Three source grayscale images.
        rgb_images: Three source RGB images.
        matrices: Per-channel 2×3 affine matrices (``None`` = identity).

    Returns:
        Tuple of (aligned_grayscale, aligned_rgb, channel_params).
    """
    out_size = (grayscale_images[0].shape[1], grayscale_images[0].shape[0])
    aligned_gray = [img.copy() for img in grayscale_images]
    aligned_rgb = [img.copy() for img in rgb_images]
    params = [TransformParams() for _ in range(3)]

    for i in range(1, 3):
        mat = matrices[i]
        if mat is None:
            continue
        aligned_gray[i] = cv2.warpAffine(grayscale_images[i], mat, out_size)  # pylint: disable=E1101
        aligned_rgb[i] = cv2.warpAffine(  # pylint: disable=E1101
            rgb_images[i], mat, (rgb_images[0].shape[1], rgb_images[0].shape[0])
        )
        params[i] = _extract_transform_params(mat)

    return aligned_gray, aligned_rgb, params


# ---------------------------------------------------------------------------
# Public API
def _sanity_check_orb_matrices(
    orb_matrices: List[Optional[np.ndarray]],
) -> Optional[str]:
    """Return a failure string if any channel's ORB matrix fails the sanity check.

    Args:
        orb_matrices: Per-channel matrices from :func:`_estimate_orb_matrices`.

    Returns:
        A human-readable failure string, or ``None`` if all channels are sane.
    """
    sanity_warnings: List[str] = []
    for i in range(1, 3):
        mat = orb_matrices[i]
        if mat is not None:
            p = _extract_transform_params(mat)
            warn = _check_sanity(p)
            if warn is not None:
                ch = ("Green", "Blue")[i - 1]
                sanity_warnings.append(f"{ch}: {warn}")
    return ("sanity check failed: " + "; ".join(sanity_warnings)) if sanity_warnings else None


# ---------------------------------------------------------------------------


def align_images_with_result(  # pylint: disable=too-many-locals
    grayscale_images: List[np.ndarray],
    rgb_images: List[np.ndarray],
    dof: AlignmentDOF = AlignmentDOF.TRANSLATION_ROTATION_SCALE,
) -> AlignmentResult:
    """Align channels using a cascaded pipeline with sanity checks.

    Pipeline
    --------
    1. ORB feature matching with the requested ``dof``.
    2. Per-channel sanity check on rotation and scale.
    3. If ORB fails or any channel fails the sanity check, retry with phase
       correlation (translation-only).
    4. If phase correlation also fails, return unmodified images.

    Args:
        grayscale_images: Three grayscale images [R, G, B].
        rgb_images: Three RGB images [R, G, B].
        dof: Degrees of freedom for the ORB step.

    Returns:
        AlignmentResult containing aligned images, per-channel transform
        parameters, the method name used, and any warnings.
    """
    # --- Step 1: ORB ---
    orb_failure: Optional[str] = None
    try:
        orb_matrices = _estimate_orb_matrices(grayscale_images, dof)
        # Sanity check each estimated transform
        sanity_warnings: List[str] = []
        for i in range(1, 3):
            mat = orb_matrices[i]
            if mat is not None:
                p = _extract_transform_params(mat)
                warn = _check_sanity(p)
                if warn is not None:
                    ch = ("Green", "Blue")[i - 1]
                    sanity_warnings.append(f"{ch}: {warn}")
        if sanity_warnings:
            orb_failure = "sanity check failed: " + "; ".join(sanity_warnings)
        else:
            aligned_gray, aligned_rgb, ch_params = _apply_matrices(grayscale_images, rgb_images, orb_matrices)
            return AlignmentResult(
                aligned_grayscale=aligned_gray,
                aligned_rgb=aligned_rgb,
                method_used="ORB",
                channel_params=ch_params,
                fallback_triggered=False,
                warning=None,
            )
    except AlignmentError as exc:
        orb_failure = str(exc)

    # --- Step 2: Phase correlation fallback ---
    phase_failure: Optional[str] = None
    try:
        phase_matrices = _estimate_phase_matrices(grayscale_images)
        aligned_gray, aligned_rgb, ch_params = _apply_matrices(grayscale_images, rgb_images, phase_matrices)
        return AlignmentResult(
            aligned_grayscale=aligned_gray,
            aligned_rgb=aligned_rgb,
            method_used="phase correlation",
            channel_params=ch_params,
            fallback_triggered=True,
            warning=f"ORB failed ({orb_failure}); used phase correlation fallback",
        )
    except Exception as exc:  # pylint: disable=broad-except
        phase_failure = str(exc)

    # --- Step 3: Unaligned passthrough ---
    identity_params = [TransformParams() for _ in range(3)]
    return AlignmentResult(
        aligned_grayscale=[img.copy() for img in grayscale_images],
        aligned_rgb=[img.copy() for img in rgb_images],
        method_used="unaligned",
        channel_params=identity_params,
        fallback_triggered=True,
        warning=(f"All alignment methods failed. ORB: {orb_failure}; " f"phase correlation: {phase_failure}"),
    )


def align_images(
    grayscale_images: List[np.ndarray],
    rgb_images: List[np.ndarray],
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """Align channels using the default pipeline (backward-compatible wrapper).

    Calls :func:`align_images_with_result` with
    ``AlignmentDOF.TRANSLATION_ROTATION_SCALE`` and returns only the image
    arrays.  Use :func:`align_images_with_result` directly when you need the
    method name, per-channel parameters, or fallback/warning information.

    Args:
        grayscale_images: Three grayscale images [R, G, B].
        rgb_images: Three RGB images [R, G, B].

    Returns:
        Tuple of (aligned_grayscale, aligned_rgb).

    Raises:
        AlignmentError: If all alignment methods fail.

    Cross-references:
        - handlers.channels.load_channel
    """
    result = align_images_with_result(grayscale_images, rgb_images)
    if result.method_used == "unaligned" and result.fallback_triggered:
        raise AlignmentError(result.warning or "All alignment methods failed")
    return result.aligned_grayscale, result.aligned_rgb
