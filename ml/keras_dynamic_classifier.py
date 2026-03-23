"""
Keras Dynamic Classifier — LSTM for motion-based ASL letters (J, Z, etc.)

Architecture (per user spec):
    LSTM(64) → LSTM(64) → Dense(26, Softmax)

Input : sequence of 30 frames × 63 features from LandmarkNormalizer
Output: (label, confidence)
"""
import os
import pickle
import numpy as np
from typing import Optional, Tuple

from detector.landmark_normalizer import LandmarkNormalizer, LANDMARK_FEATURE_COUNT

# TF imported lazily
_tf = None
_keras = None


def _ensure_tf():
    """Lazy-load TensorFlow/Keras."""
    global _tf, _keras
    if _tf is None:
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
        import tensorflow as tf
        _tf = tf
        _keras = tf.keras


def build_dynamic_model(
    input_size: int = LANDMARK_FEATURE_COUNT,
    sequence_length: int = 30,
    num_classes: int = 26,
) -> "tf.keras.Model":
    """Build the Keras LSTM model for dynamic gesture classification.

    Architecture:
        LSTM(64) → LSTM(64) → Dense(num_classes, Softmax)
    """
    _ensure_tf()
    model = _keras.Sequential([
        _keras.layers.Input(shape=(sequence_length, input_size)),
        _keras.layers.LSTM(64, return_sequences=True),
        _keras.layers.LSTM(64),
        _keras.layers.Dense(num_classes, activation="softmax"),
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


class KerasDynamicClassifier:
    """Wrapper that loads a trained Keras LSTM and runs inference
    on buffered 30-frame landmark sequences.

    Public API mirrors DynamicGestureClassifier for drop-in use.
    """

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.is_loaded = False
        self._normalizer = LandmarkNormalizer()
        self.sequence_length = 30  # updated in load() from config

    # ------------------------------------------------------------------
    # Loading / Saving
    # ------------------------------------------------------------------

    def load(
        self,
        model_path: Optional[str] = None,
        labels_path: Optional[str] = None,
    ) -> bool:
        """Load a trained Keras LSTM model + label encoder."""
        from config import (
            KERAS_DYNAMIC_MODEL_PATH,
            KERAS_DYNAMIC_LABELS_PATH,
            DYNAMIC_SEQUENCE_LENGTH,
        )

        model_path = model_path or KERAS_DYNAMIC_MODEL_PATH
        labels_path = labels_path or KERAS_DYNAMIC_LABELS_PATH
        self.sequence_length = DYNAMIC_SEQUENCE_LENGTH

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
            print(f"[KerasDynamicClassifier] Error loading model: {e}")
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
            print(f"[KerasDynamicClassifier] Error saving model: {e}")
            return False

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, landmark_sequence) -> Tuple[Optional[str], float]:
        """Predict dynamic gesture from a buffered landmark sequence.

        Args:
            landmark_sequence: list of frames, each frame is 21 (x,y,z).

        Returns:
            (label, confidence) or (None, 0.0)
        """
        if not self.is_loaded:
            return None, 0.0

        features = self._normalizer.normalize_sequence(landmark_sequence)
        if features is None:
            return None, 0.0

        # Pad or truncate to expected sequence length
        if features.shape[0] < self.sequence_length:
            pad = np.zeros(
                (self.sequence_length - features.shape[0], features.shape[1]),
                dtype=np.float32,
            )
            features = np.concatenate([pad, features], axis=0)
        elif features.shape[0] > self.sequence_length:
            features = features[-self.sequence_length:]

        x = features.reshape(1, self.sequence_length, -1)
        probs = self.model.predict(x, verbose=0)[0]

        idx = int(np.argmax(probs))
        confidence = float(probs[idx])
        label = self.label_encoder.inverse_transform([idx])[0]
        return label, confidence

    def get_classes(self) -> list:
        if self.label_encoder is None:
            return []
        return self.label_encoder.classes_.tolist()
