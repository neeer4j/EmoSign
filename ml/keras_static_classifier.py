"""
Keras Static Classifier — MLP for single-frame ASL letter classification

Architecture (per user spec):
    Dense(128, ReLU) → Dense(128, ReLU) → Dropout(0.3) → Dense(26, Softmax)

Input : 63 features from LandmarkNormalizer
Output: (label, confidence)
"""
import os
import pickle
import numpy as np
from typing import Optional, Tuple, List

from detector.landmark_normalizer import LandmarkNormalizer, LANDMARK_FEATURE_COUNT

# TF imported lazily to avoid slow startup when not needed
_tf = None
_keras = None


def _ensure_tf():
    """Lazy-load TensorFlow/Keras."""
    global _tf, _keras
    if _tf is None:
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")  # suppress TF logs
        import tensorflow as tf
        _tf = tf
        _keras = tf.keras


def build_static_model(
    input_size: int = LANDMARK_FEATURE_COUNT,
    num_classes: int = 26,
) -> "tf.keras.Model":
    """Build the Keras MLP model for static letter classification.

    Architecture:
        Dense(128, ReLU) → Dense(128, ReLU) → Dropout(0.3) → Dense(num_classes, Softmax)
    """
    _ensure_tf()
    model = _keras.Sequential([
        _keras.layers.Input(shape=(input_size,)),
        _keras.layers.Dense(128, activation="relu"),
        _keras.layers.Dense(128, activation="relu"),
        _keras.layers.Dropout(0.3),
        _keras.layers.Dense(num_classes, activation="softmax"),
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


class KerasStaticClassifier:
    """Wrapper that loads a trained Keras MLP and runs real-time inference.

    Public API mirrors StaticGestureClassifier so it can be used as a
    drop-in replacement.
    """

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.is_loaded = False
        self._normalizer = LandmarkNormalizer()

    # ------------------------------------------------------------------
    # Loading / Saving
    # ------------------------------------------------------------------

    def load(
        self,
        model_path: Optional[str] = None,
        labels_path: Optional[str] = None,
    ) -> bool:
        """Load a trained Keras model + label encoder from disk."""
        from config import KERAS_STATIC_MODEL_PATH, KERAS_STATIC_LABELS_PATH

        model_path = model_path or KERAS_STATIC_MODEL_PATH
        labels_path = labels_path or KERAS_STATIC_LABELS_PATH

        if not os.path.exists(model_path) or not os.path.exists(labels_path):
            return False

        try:
            _ensure_tf()
            self.model = _keras.models.load_model(model_path)

            with open(labels_path, "rb") as f:
                self.label_encoder = pickle.load(f)

            self.is_loaded = True
            return True
        except Exception as e:
            print(f"[KerasStaticClassifier] Error loading model: {e}")
            return False

    def save(self, model_path: str, labels_path: str) -> bool:
        """Save current model + label encoder to disk."""
        if self.model is None or self.label_encoder is None:
            return False
        try:
            self.model.save(model_path)
            with open(labels_path, "wb") as f:
                pickle.dump(self.label_encoder, f)
            return True
        except Exception as e:
            print(f"[KerasStaticClassifier] Error saving model: {e}")
            return False

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, landmarks) -> Tuple[Optional[str], float]:
        """Predict static gesture from raw landmarks (21 × 3).

        Returns:
            (label, confidence) or (None, 0.0)
        """
        features = self._normalizer.normalize(landmarks)
        return self.predict_from_features(features)

    def predict_from_features(
        self, features: Optional[np.ndarray]
    ) -> Tuple[Optional[str], float]:
        """Predict from a pre-normalized 63-feature vector."""
        if not self.is_loaded or features is None:
            return None, 0.0

        x = features.reshape(1, -1)
        probs = self.model.predict(x, verbose=0)[0]

        idx = int(np.argmax(probs))
        confidence = float(probs[idx])
        label = self.label_encoder.inverse_transform([idx])[0]
        return label, confidence

    def predict_top_n(
        self, landmarks, n: int = 3
    ) -> List[Tuple[str, float]]:
        """Return top-n predictions as list of (label, confidence)."""
        features = self._normalizer.normalize(landmarks)
        return self._predict_top_n_from_features(features, n)

    def _predict_top_n_from_features(
        self, features: Optional[np.ndarray], n: int = 3
    ) -> List[Tuple[str, float]]:
        """Return top-n from pre-normalized features."""
        if not self.is_loaded or features is None:
            return []

        x = features.reshape(1, -1)
        probs = self.model.predict(x, verbose=0)[0]

        top_idx = np.argsort(probs)[::-1][:n]
        results = []
        for idx in top_idx:
            label = self.label_encoder.inverse_transform([idx])[0]
            results.append((label, float(probs[idx])))
        return results

    def get_classes(self) -> list:
        if self.label_encoder is None:
            return []
        return self.label_encoder.classes_.tolist()
