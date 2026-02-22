"""
Gesture Pipeline — Unified orchestrator for sign language detection

Combines:
  • Movement detection    → routes to static MLP or dynamic LSTM
  • Keras static MLP      → single-frame letter classification
  • Keras dynamic LSTM    → sequence-based letter classification (J, Z)
  • Heuristic classifier  → rule-based fallback (always available)
  • Prediction smoothing  → majority vote over last N predictions
  • Confidence filter      → suppress predictions below threshold

This replaces DualModelManager as the main entry point called from
camera_widget.py and video_player_widget.py.
"""
from collections import deque, Counter
from typing import Optional, Tuple

import numpy as np

from config import (
    MOVEMENT_THRESHOLD,
    MOVEMENT_FRAMES_REQUIRED,
    DYNAMIC_SEQUENCE_LENGTH,
    SMOOTHING_WINDOW,
    MIN_PREDICTION_CONFIDENCE,
)
from ml.keras_static_classifier import KerasStaticClassifier
from ml.keras_dynamic_classifier import KerasDynamicClassifier
from ml.heuristic_classifier import HeuristicClassifier


class GesturePipeline:
    """Movement-aware, smoothing, confidence-filtered gesture pipeline.

    Usage::

        pipe = GesturePipeline()
        pipe.load()              # loads Keras models (if available)

        # Per frame (from camera):
        label, conf, model = pipe.process_frame(landmarks)
    """

    def __init__(
        self,
        movement_threshold: float = MOVEMENT_THRESHOLD,
        movement_frames_required: int = MOVEMENT_FRAMES_REQUIRED,
        sequence_length: int = DYNAMIC_SEQUENCE_LENGTH,
        smoothing_window: int = SMOOTHING_WINDOW,
        min_confidence: float = MIN_PREDICTION_CONFIDENCE,
    ):
        self.movement_threshold = movement_threshold
        self.movement_frames_required = movement_frames_required
        self.sequence_length = sequence_length
        self.min_confidence = min_confidence

        # --- Classifiers ---
        self.static_classifier = KerasStaticClassifier()
        self.dynamic_classifier = KerasDynamicClassifier()
        self.heuristic_classifier = HeuristicClassifier()

        # --- Model load status ---
        self._static_loaded = False
        self._dynamic_loaded = False

        # --- Movement detection state ---
        self._prev_landmarks: Optional[np.ndarray] = None
        self._motion_counter: int = 0
        self._is_buffering: bool = False
        self._landmark_buffer: deque = deque(maxlen=sequence_length)

        # --- Prediction smoothing ---
        self._prediction_buffer: deque = deque(maxlen=smoothing_window)
        self._confidence_buffer: deque = deque(maxlen=smoothing_window)

    # ==================================================================
    # Loading
    # ==================================================================

    def load(self) -> dict:
        """Load Keras models.  Returns dict with load status."""
        self._static_loaded = self.static_classifier.load()
        self._dynamic_loaded = self.dynamic_classifier.load()
        return {
            "static": self._static_loaded,
            "dynamic": self._dynamic_loaded,
        }

    @property
    def any_model_loaded(self) -> bool:
        return self._static_loaded or self._dynamic_loaded

    # ==================================================================
    # Movement Detection
    # ==================================================================

    def _compute_displacement(self, landmarks: np.ndarray) -> float:
        """Mean displacement of 21 landmarks vs previous frame, normalized."""
        if self._prev_landmarks is None:
            return 0.0

        diff = landmarks - self._prev_landmarks
        per_point = np.linalg.norm(diff, axis=1)  # (21,)

        # Normalize by palm scale (wrist → middle MCP)
        scale = np.linalg.norm(landmarks[9] - landmarks[0])
        if scale < 1e-6:
            scale = 1.0

        return float(np.mean(per_point) / scale)

    # ==================================================================
    # Smoothing
    # ==================================================================

    def _smooth_prediction(
        self, label: Optional[str], confidence: float
    ) -> Tuple[Optional[str], float]:
        """Apply majority-vote smoothing over last N predictions."""
        if label is None:
            return None, 0.0

        self._prediction_buffer.append(label)
        self._confidence_buffer.append(confidence)

        if len(self._prediction_buffer) < 2:
            return label, confidence

        counts = Counter(self._prediction_buffer)
        best_label, best_count = counts.most_common(1)[0]
        consistency = best_count / len(self._prediction_buffer)

        if consistency < 0.35:
            return None, 0.0

        # Average confidence for the winning label
        avg_conf = np.mean([
            c for l, c in zip(self._prediction_buffer, self._confidence_buffer)
            if l == best_label
        ])
        adjusted = float(min(avg_conf * consistency, 1.0))
        return best_label, adjusted

    # ==================================================================
    # Core Pipeline
    # ==================================================================

    def process_frame(
        self, landmarks
    ) -> Tuple[Optional[str], float, str]:
        """Process one frame and return the prediction.

        Args:
            landmarks: list of 21 (x, y, z) tuples from MediaPipe,
                       or None when hand is not detected.

        Returns:
            (label, confidence, model_used)
            model_used is 'keras_static', 'keras_dynamic', 'heuristic', or 'none'.
        """
        if landmarks is None or len(landmarks) != 21:
            self._on_hand_lost()
            return None, 0.0, "none"

        lm = np.array(landmarks, dtype=np.float32)
        displacement = self._compute_displacement(lm)
        self._prev_landmarks = lm.copy()

        # Always buffer for potential LSTM use
        self._landmark_buffer.append(landmarks)

        # --- Movement routing ---
        if displacement >= self.movement_threshold:
            self._motion_counter += 1
        else:
            # Motion just stopped — try dynamic prediction on buffer
            if self._is_buffering and self._dynamic_loaded:
                label, conf = self._try_dynamic_predict()
                if label is not None:
                    label, conf = self._smooth_prediction(label, conf)
                    if label and conf >= self.min_confidence:
                        self._reset_motion_state()
                        return label, conf, "keras_dynamic"
            self._motion_counter = 0
            self._is_buffering = False

        # Start buffering once motion threshold is sustained
        if self._motion_counter >= self.movement_frames_required:
            self._is_buffering = True

        # Full buffer → dynamic prediction
        if (
            self._is_buffering
            and self._dynamic_loaded
            and len(self._landmark_buffer) >= self.sequence_length
        ):
            label, conf = self.dynamic_classifier.predict(
                list(self._landmark_buffer)
            )
            if label is not None and conf > 0.0:
                label, conf = self._smooth_prediction(label, conf)
                if label and conf >= self.min_confidence:
                    self._reset_motion_state()
                    return label, conf, "keras_dynamic"

        # Still buffering → suppress static to avoid noise
        if self._is_buffering:
            return None, 0.0, "none"

        # --- Static classification ---
        # Try Keras MLP first, fall back to heuristic
        raw_label, raw_conf = None, 0.0
        model_used = "none"

        if self._static_loaded:
            raw_label, raw_conf = self.static_classifier.predict(landmarks)
            model_used = "keras_static"

        # Heuristic as fallback / augmentation
        h_label, h_conf = self.heuristic_classifier.predict(landmarks)

        # Prefer heuristic when it's confident and no Keras or Keras is weak
        if h_label and h_conf > 0.7:
            if raw_label is None or raw_conf < 0.5:
                raw_label, raw_conf = h_label, h_conf
                model_used = "heuristic"
            elif h_label == raw_label:
                # Both agree — boost confidence
                raw_conf = min(1.0, (raw_conf + h_conf) / 2 * 1.1)

        if raw_label is None:
            return None, 0.0, "none"

        # Smooth + filter
        label, conf = self._smooth_prediction(raw_label, raw_conf)
        if label is None or conf < self.min_confidence:
            return None, 0.0, "none"

        return label, conf, model_used

    # ==================================================================
    # Helpers
    # ==================================================================

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
        self._prediction_buffer.clear()
        self._confidence_buffer.clear()

    def clear_buffer(self):
        """Clear the smoothing buffers (alias for Classifier API)."""
        self._prediction_buffer.clear()
        self._confidence_buffer.clear()

    def get_status(self) -> dict:
        """Return current pipeline status for debugging/UI."""
        return {
            "static_loaded": self._static_loaded,
            "dynamic_loaded": self._dynamic_loaded,
            "motion_counter": self._motion_counter,
            "is_buffering": self._is_buffering,
            "buffer_size": len(self._landmark_buffer),
            "smoothing_size": len(self._prediction_buffer),
        }
