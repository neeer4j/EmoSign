"""
Gesture Classifier - Real-time prediction with temporal smoothing

Delegates to the StaticFFN (PyTorch) model for inference.  Keeps the
same public API so all existing pages (live_translation, game, live,
training, main_window) work without changes.
"""
import numpy as np
import os
from collections import deque

from config import STATIC_MODEL_PATH, STATIC_LABELS_PATH
from ml.static_classifier import StaticGestureClassifier


class Classifier:
    """Wrapper around StaticGestureClassifier with temporal smoothing."""

    def __init__(self, smoothing_window: int = 5):
        self._backend = StaticGestureClassifier()
        self.is_loaded = False

        # Temporal smoothing buffer
        self.smoothing_window = smoothing_window
        self.prediction_buffer = deque(maxlen=smoothing_window)
        self.confidence_buffer = deque(maxlen=smoothing_window)

    def load(self, model_path: str = None, labels_path: str = None) -> bool:
        model_path = model_path or STATIC_MODEL_PATH
        labels_path = labels_path or STATIC_LABELS_PATH
        self.is_loaded = self._backend.load(model_path, labels_path)
        if self.is_loaded:
            self.clear_buffer()
        return self.is_loaded

    def clear_buffer(self):
        self.prediction_buffer.clear()
        self.confidence_buffer.clear()

    def predict(self, features: np.ndarray, use_smoothing: bool = True) -> tuple:
        """Predict from a pre-extracted 87-feature vector.

        Args:
            features: 87-element feature vector from FeatureExtractor
            use_smoothing: Whether to apply temporal majority-voting

        Returns:
            (label, confidence)
        """
        if not self.is_loaded or features is None:
            return None, 0.0

        raw_label, raw_confidence = self._backend.predict_from_features(features)
        if raw_label is None:
            return None, 0.0

        if not use_smoothing:
            return raw_label, raw_confidence

        # Temporal smoothing via majority voting
        self.prediction_buffer.append(raw_label)
        self.confidence_buffer.append(raw_confidence)

        if len(self.prediction_buffer) >= 2:
            label_counts = {}
            label_confidences = {}
            for label, conf in zip(self.prediction_buffer, self.confidence_buffer):
                if label not in label_counts:
                    label_counts[label] = 0
                    label_confidences[label] = []
                label_counts[label] += 1
                label_confidences[label].append(conf)

            best_label = max(label_counts, key=label_counts.get)
            avg_confidence = np.mean(label_confidences[best_label])
            consistency = label_counts[best_label] / len(self.prediction_buffer)

            if consistency < 0.35:
                return None, 0.0

            adjusted_confidence = avg_confidence * consistency
            return best_label, float(min(adjusted_confidence, 1.0))

        return raw_label, raw_confidence

    def predict_top_n(self, features: np.ndarray, n: int = 3) -> list:
        if not self.is_loaded or features is None:
            return []
        # predict_top_n on the backend expects landmarks, but we have
        # features — so use the model directly
        return self._backend._predict_top_n_from_features(features, n)

    def get_classes(self) -> list:
        return self._backend.get_classes()

    def model_exists(self) -> bool:
        return (
            os.path.exists(STATIC_MODEL_PATH)
            and os.path.exists(STATIC_LABELS_PATH)
        )
