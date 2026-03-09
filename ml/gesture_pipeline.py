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

# Debug flag - set to True to see movement detection logs
DEBUG_MOVEMENT = False


# ==================================================================
# Z / J Trajectory Detector
# ==================================================================

class ZJDetector:
    """Movement-based detector for ASL Z and J.

    Z: hand in 'D' shape (only index finger extended) + significant movement
    J: hand in 'I' shape (only pinky finger extended) + significant movement

    • D held still  → static pipeline outputs 'D'  (ZJDetector stays silent)
    • D + big move  → ZJDetector fires 'Z' immediately
    • I held still  → static pipeline outputs 'I'  (ZJDetector stays silent)
    • I + big move  → ZJDetector fires 'J' immediately
    """

    # Frames the tip must move above MOTION_THRESHOLD before we fire
    MIN_MOTION_FRAMES = 12          # raised: needs a long, sustained stroke
    # Per-frame fingertip displacement (normalized by palm scale) to count as "moving"
    MOTION_THRESHOLD = 0.035        # raised: only track real motion, not jitter
    # Total accumulated displacement needed to confirm the gesture
    MIN_TOTAL_DISP = 0.40           # raised significantly: short strokes won't fire
    # Cooldown frames after firing — prevents immediate re-detection (~1 s @ 30 fps)
    COOLDOWN_FRAMES = 30            # raised: give time between detections

    def __init__(self):
        self._mode: Optional[str] = None      # 'Z', 'J', or None
        self._motion_frames: int = 0           # frames with tip displacement ≥ MOTION_THRESHOLD
        self._total_disp: float = 0.0          # cumulative normalised tip displacement
        self._prev_tip: Optional[np.ndarray] = None
        self._cooldown: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, landmarks) -> Tuple[Optional[str], float]:
        """Feed one frame of 21 MediaPipe (x,y,z) landmarks.

        Returns ``(label, confidence)`` as soon as Z or J is confirmed,
        else ``(None, 0.0)``.
        """
        if self._cooldown > 0:
            self._cooldown -= 1
            return None, 0.0

        if landmarks is None or len(landmarks) != 21:
            self._reset()
            return None, 0.0

        lm = np.array(landmarks, dtype=np.float32)
        mode = self._detect_mode(lm)

        if mode is None:
            # Hand shape changed — cancel any in-progress gesture
            self._reset()
            return None, 0.0

        if mode != self._mode:
            # Shape switched (e.g., D → I mid-air) — start fresh
            self._reset()
            self._mode = mode

        # Track the relevant fingertip: index (8) for Z, pinky (20) for J
        tip_idx = 8 if mode == 'Z' else 20
        tip = lm[tip_idx, :2].copy()

        # Normalise displacement by palm scale (wrist → middle MCP)
        scale = float(np.linalg.norm(lm[9, :2] - lm[0, :2]))
        if scale < 1e-6:
            scale = 1.0

        if self._prev_tip is not None:
            disp = float(np.linalg.norm(tip - self._prev_tip)) / scale
            if disp >= self.MOTION_THRESHOLD:
                self._motion_frames += 1
                self._total_disp += disp

        self._prev_tip = tip

        # Fire once enough sustained movement has accumulated
        if (self._motion_frames >= self.MIN_MOTION_FRAMES
                and self._total_disp >= self.MIN_TOTAL_DISP):
            label = mode
            self._reset()
            self._cooldown = self.COOLDOWN_FRAMES
            return label, 0.92

        return None, 0.0

    def clear(self):
        """Full reset including cooldown."""
        self._reset()
        self._cooldown = 0

    # ------------------------------------------------------------------
    # Hand-shape detection
    # ------------------------------------------------------------------

    def _detect_mode(self, lm: np.ndarray) -> Optional[str]:
        """Return 'Z' for D-shape (only index extended),
        'J' for I-shape (only pinky extended), else None."""
        wrist = lm[0]

        def _ext(tip_i: int, pip_i: int) -> bool:
            return (float(np.linalg.norm(lm[tip_i, :2] - wrist[:2])) >
                    float(np.linalg.norm(lm[pip_i, :2] - wrist[:2])))

        index_ext  = _ext(8,  6)
        middle_ext = _ext(12, 10)
        ring_ext   = _ext(16, 14)
        pinky_ext  = _ext(20, 18)

        if index_ext and not middle_ext and not ring_ext and not pinky_ext:
            return 'Z'
        if pinky_ext and not index_ext and not middle_ext and not ring_ext:
            return 'J'
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reset(self):
        self._mode = None
        self._motion_frames = 0
        self._total_disp = 0.0
        self._prev_tip = None


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

        # --- Z / J trajectory detector (always-on heuristic) ---
        self._zj_detector = ZJDetector()

        # --- Debug ---
        self._debug_frame_count: int = 0

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
        """Max displacement of any landmark vs previous frame, normalized.

        Uses np.max so that significant motion by ANY single landmark
        (e.g. index finger drawing Z) triggers dynamic routing, instead
        of being diluted by the 20 stationary landmarks.
        """
        if self._prev_landmarks is None:
            return 0.0

        diff = landmarks - self._prev_landmarks
        per_point = np.linalg.norm(diff, axis=1)  # (21,)

        # Normalize by palm scale (wrist → middle MCP)
        scale = np.linalg.norm(landmarks[9] - landmarks[0])
        if scale < 1e-6:
            scale = 1.0

        disp = float(np.max(per_point) / scale)
        if DEBUG_MOVEMENT and self._debug_frame_count % 10 == 0:
            print(f"[MOVE] disp={disp:.4f}")
        return disp

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
            model_used is 'keras_static', 'keras_dynamic', 'zj_heuristic', 'heuristic', or 'none'.
        """
        if landmarks is None or len(landmarks) != 21:
            self._on_hand_lost()
            return None, 0.0, "none"

        lm = np.array(landmarks, dtype=np.float32)
        displacement = self._compute_displacement(lm)
        self._prev_landmarks = lm.copy()

        # DEBUG: Print movement info
        if DEBUG_MOVEMENT and self._debug_frame_count % 10 == 0:
            print(f"[MOVE] disp={displacement:.4f} thresh={self.movement_threshold:.4f} "
                  f"motion_cnt={self._motion_counter}/{self.movement_frames_required} "
                  f"buffering={self._is_buffering} buf_len={len(self._landmark_buffer)}/{self.sequence_length} "
                  f"dynamic_loaded={self._dynamic_loaded}")
        self._debug_frame_count += 1

        # ------------------------------------------------------------------
        # Z / J trajectory detection — runs every frame, fires immediately
        # when a stroke pattern is confidently recognised.
        # This is a dedicated heuristic and does NOT depend on the LSTM.
        # ------------------------------------------------------------------
        zj_label, zj_conf = self._zj_detector.update(landmarks)
        if zj_label is not None and zj_conf >= self.min_confidence:
            if DEBUG_MOVEMENT:
                print(f"[ZJ] ✓ Detected: {zj_label} ({zj_conf:.1%})")
            # Reset motion state so we don't contaminate the next gesture
            self._reset_motion_state()
            return zj_label, zj_conf, "zj_heuristic"

        # Always buffer for potential LSTM use
        self._landmark_buffer.append(landmarks)

        # --- Movement routing ---
        if displacement >= self.movement_threshold:
            self._motion_counter += 1
        else:
            # Motion just stopped — try dynamic prediction on buffer
            if self._is_buffering and self._dynamic_loaded:
                if DEBUG_MOVEMENT:
                    print(f"[MOVE] Motion stopped! Trying dynamic predict on {len(self._landmark_buffer)} frames...")
                label, conf = self._try_dynamic_predict()
                if DEBUG_MOVEMENT:
                    print(f"[LSTM] Raw prediction: label={label}, conf={conf:.3f}")
                if label is not None:
                    label, conf = self._smooth_prediction(label, conf)
                    if DEBUG_MOVEMENT:
                        print(f"[LSTM] After smoothing: label={label}, conf={conf:.3f}, min_conf={self.min_confidence}")
                    if label and conf >= self.min_confidence:
                        if DEBUG_MOVEMENT:
                            print(f"[LSTM] ✓ RETURNING DYNAMIC: {label} ({conf:.1%})")
                        self._reset_motion_state()
                        return label, conf, "keras_dynamic"
            self._motion_counter = 0
            self._is_buffering = False
            # Clear stale landmark frames so ghost data from a previous gesture
            # does not contaminate the next LSTM run.
            self._landmark_buffer.clear()

        # Start buffering once motion threshold is sustained
        if self._motion_counter >= self.movement_frames_required:
            if not self._is_buffering and DEBUG_MOVEMENT:
                print(f"[MOVE] >>> BUFFERING STARTED! motion_counter={self._motion_counter}")
            self._is_buffering = True

        # Full buffer → dynamic prediction
        if (
            self._is_buffering
            and self._dynamic_loaded
            and len(self._landmark_buffer) >= self.sequence_length
        ):
            if DEBUG_MOVEMENT:
                print(f"[LSTM] Buffer full ({len(self._landmark_buffer)}), predicting...")
            label, conf = self.dynamic_classifier.predict(
                list(self._landmark_buffer)
            )
            if DEBUG_MOVEMENT:
                print(f"[LSTM] Full buffer prediction: label={label}, conf={conf:.3f}")
            if label is not None and conf > 0.0:
                label, conf = self._smooth_prediction(label, conf)
                if label and conf >= self.min_confidence:
                    if DEBUG_MOVEMENT:
                        print(f"[LSTM] ✓ RETURNING DYNAMIC (full buffer): {label} ({conf:.1%})")
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
        """Called when hand disappears from frame.

        If we were mid-gesture, attempt a final LSTM prediction on whatever
        was buffered before the hand left the frame, then clean up.
        """
        result = None, 0.0, "none"
        if self._is_buffering and self._dynamic_loaded:
            label, conf = self._try_dynamic_predict()
            if label is not None and conf >= self.min_confidence:
                label, conf = self._smooth_prediction(label, conf)
                if label and conf >= self.min_confidence:
                    result = label, conf, "keras_dynamic"
        self._prev_landmarks = None
        self._reset_motion_state()
        self._zj_detector.clear()   # discard partial Z/J trajectory on hand-loss
        # Return the result so callers can decide whether to surface it.
        # process_frame currently calls _on_hand_lost and ignores the return;
        # that's fine — the result is emitted by the NEXT call that gets the
        # smoothed buffer anyway.  What matters here is the cleanup above.
        return result

    def clear(self):
        """Reset all state."""
        self._prev_landmarks = None
        self._motion_counter = 0
        self._is_buffering = False
        self._landmark_buffer.clear()
        self._prediction_buffer.clear()
        self._confidence_buffer.clear()
        self._zj_detector.clear()

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
            "zj_mode": self._zj_detector._mode,
            "zj_motion_frames": self._zj_detector._motion_frames,
            "zj_total_disp": round(self._zj_detector._total_disp, 3),
        }
