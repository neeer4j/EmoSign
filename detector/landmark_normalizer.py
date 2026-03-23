"""
Landmark Normalizer — Wrist-relative, palm-scaled normalization

Produces exactly 63 features (21 landmarks × 3 coordinates):
  1. Translate all landmarks relative to wrist (landmark 0)
  2. Scale by distance from wrist to middle-finger MCP (landmark 9)
  3. Flatten to 1-D float32 array
"""
import numpy as np
from typing import Optional


LANDMARK_FEATURE_COUNT = 63  # 21 × 3


class LandmarkNormalizer:
    """Normalize hand landmarks for ML classification."""

    WRIST = 0
    MIDDLE_MCP = 9  # palm-scale reference

    @staticmethod
    def normalize(landmarks) -> Optional[np.ndarray]:
        """Normalize 21 hand landmarks to 63 features.

        Steps:
            1. Subtract wrist position  → translation invariant
            2. Divide by |wrist → middle MCP| → scale invariant
            3. Flatten to (63,)

        Args:
            landmarks: list/array of 21 (x, y, z) tuples from MediaPipe.

        Returns:
            np.float32 array of shape (63,), or None if input is invalid.
        """
        if landmarks is None or len(landmarks) != 21:
            return None

        lm = np.array(landmarks, dtype=np.float32)

        # 1. Translate relative to wrist
        wrist = lm[LandmarkNormalizer.WRIST]
        lm = lm - wrist

        # 2. Scale by palm size
        scale = np.linalg.norm(lm[LandmarkNormalizer.MIDDLE_MCP])
        if scale < 1e-6:
            scale = 1.0
        lm = lm / scale

        # 3. Flatten to 63 features
        return lm.flatten().astype(np.float32)

    @staticmethod
    def normalize_sequence(landmark_sequence) -> Optional[np.ndarray]:
        """Normalize a sequence of landmark frames.

        Args:
            landmark_sequence: list of frames, each frame is 21 (x,y,z).

        Returns:
            np.float32 array of shape (num_frames, 63), or None.
        """
        if not landmark_sequence:
            return None

        frames = []
        for lm in landmark_sequence:
            feat = LandmarkNormalizer.normalize(lm)
            if feat is None:
                return None
            frames.append(feat)

        return np.stack(frames, axis=0)
