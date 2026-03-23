"""
Dual Model Manager - Movement-aware gesture classification

Routes each frame to either the static FFN or dynamic LSTM classifier
based on hand landmark displacement between consecutive frames.

Logic:
  - Compute mean displacement of all 21 landmarks between the current
    and previous frame (normalised by palm scale).
  - If displacement < MOVEMENT_THRESHOLD for the last N frames, classify
    with the static FFN on the current single frame.
  - If displacement >= MOVEMENT_THRESHOLD for MOVEMENT_FRAMES_REQUIRED
    consecutive frames, buffer 30 frames and classify with the LSTM.
"""
from collections import deque
from typing import Optional, Tuple, List

import numpy as np

from config import (
    MOVEMENT_THRESHOLD,
    MOVEMENT_FRAMES_REQUIRED,
    DYNAMIC_SEQUENCE_LENGTH,
)
from ml.static_classifier import StaticGestureClassifier
from ml.dynamic_classifier import DynamicGestureClassifier


class DualModelManager:
    """Manages static/dynamic model switching based on hand motion."""

    def __init__(
        self,
        movement_threshold: float = MOVEMENT_THRESHOLD,
        movement_frames_required: int = MOVEMENT_FRAMES_REQUIRED,
        sequence_length: int = DYNAMIC_SEQUENCE_LENGTH,
    ):
        self.movement_threshold = movement_threshold
        self.movement_frames_required = movement_frames_required
        self.sequence_length = sequence_length

        # Classifiers
        self.static_classifier = StaticGestureClassifier()
        self.dynamic_classifier = DynamicGestureClassifier()

        # State
        self._prev_landmarks: Optional[np.ndarray] = None
        self._motion_counter: int = 0  # consecutive high-motion frames
        self._landmark_buffer: deque = deque(maxlen=sequence_length)
        self._is_buffering: bool = False
        self._static_loaded = False
        self._dynamic_loaded = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> dict:
        """Attempt to load both models.

        Returns dict with keys 'static' and 'dynamic' indicating load
        success for each.
        """
        self._static_loaded = self.static_classifier.load()
        self._dynamic_loaded = self.dynamic_classifier.load()
        return {
            "static": self._static_loaded,
            "dynamic": self._dynamic_loaded,
        }

    @property
    def any_model_loaded(self) -> bool:
        return self._static_loaded or self._dynamic_loaded

    # ------------------------------------------------------------------
    # Movement detection
    # ------------------------------------------------------------------

    def _compute_displacement(self, landmarks: np.ndarray) -> float:
        """Mean displacement of 21 landmarks vs previous frame, normalised."""
        if self._prev_landmarks is None:
            return 0.0

        diff = landmarks - self._prev_landmarks
        per_point = np.linalg.norm(diff, axis=1)  # (21,)

        # Normalise by palm scale (wrist to middle-MCP)
        scale = np.linalg.norm(landmarks[9] - landmarks[0])
        if scale < 1e-6:
            scale = 1.0

        return float(np.mean(per_point) / scale)

    # ------------------------------------------------------------------
    # Core prediction
    # ------------------------------------------------------------------

    def process_frame(
        self, landmarks
    ) -> Tuple[Optional[str], float, str]:
        """Process one frame and return the prediction.

        Args:
            landmarks: list of 21 (x, y, z) tuples from MediaPipe,
                       or None when hand is not detected.

        Returns:
            (label, confidence, model_used)
            model_used is one of 'static', 'dynamic', or 'none'.
        """
        if landmarks is None or len(landmarks) != 21:
            self._on_hand_lost()
            return None, 0.0, "none"

        lm = np.array(landmarks, dtype=np.float32)
        displacement = self._compute_displacement(lm)
        self._prev_landmarks = lm.copy()

        # Always buffer for potential LSTM use
        self._landmark_buffer.append(landmarks)

        # --- Motion routing ---
        if displacement >= self.movement_threshold:
            self._motion_counter += 1
        else:
            # If we were buffering but motion stopped, try to classify
            # the accumulated sequence before resetting
            if self._is_buffering and self._dynamic_loaded:
                label, conf = self._try_dynamic_predict()
                if label is not None:
                    self._reset_motion_state()
                    return label, conf, "dynamic"
            self._motion_counter = 0
            self._is_buffering = False

        # Start buffering once motion threshold is hit
        if self._motion_counter >= self.movement_frames_required:
            self._is_buffering = True

        # If we have a full buffer of motion frames, predict dynamically
        if (
            self._is_buffering
            and self._dynamic_loaded
            and len(self._landmark_buffer) >= self.sequence_length
        ):
            label, conf = self.dynamic_classifier.predict(
                list(self._landmark_buffer)
            )
            if label is not None and conf > 0.0:
                self._reset_motion_state()
                return label, conf, "dynamic"

        # Still buffering: don't return a static prediction to avoid noise
        if self._is_buffering:
            return None, 0.0, "none"

        # Static classification
        if self._static_loaded:
            label, conf = self.static_classifier.predict(landmarks)
            return label, conf, "static"

        return None, 0.0, "none"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _try_dynamic_predict(self) -> Tuple[Optional[str], float]:
        """Try to predict from whatever is in the buffer."""
        if len(self._landmark_buffer) < 10:
            return None, 0.0
        return self.dynamic_classifier.predict(list(self._landmark_buffer))

    def _reset_motion_state(self):
        self._motion_counter = 0
        self._is_buffering = False
        self._landmark_buffer.clear()

    def _on_hand_lost(self):
        """Called when hand disappears from frame."""
        # If we were buffering, try a final dynamic prediction
        if self._is_buffering and self._dynamic_loaded:
            self._try_dynamic_predict()
        self._prev_landmarks = None
        self._motion_counter = 0
        self._is_buffering = False

    def clear(self):
        """Reset all state."""
        self._prev_landmarks = None
        self._motion_counter = 0
        self._is_buffering = False
        self._landmark_buffer.clear()

    def get_status(self) -> dict:
        """Return current manager status for debugging/UI."""
        return {
            "static_loaded": self._static_loaded,
            "dynamic_loaded": self._dynamic_loaded,
            "motion_counter": self._motion_counter,
            "is_buffering": self._is_buffering,
            "buffer_size": len(self._landmark_buffer),
        }
