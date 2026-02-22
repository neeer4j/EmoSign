"""
Keras Trainer — Train TF/Keras MLP (static) and LSTM (dynamic) models

Reads collected landmark data (CSV from DataCollector), normalizes with
LandmarkNormalizer (63 features), and trains the Keras models.

Also provides a train_from_landmarks() convenience method that takes
raw landmark arrays + labels directly (for use from Training Page).
"""
import os
import pickle
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

from config import (
    KERAS_STATIC_MODEL_PATH,
    KERAS_STATIC_LABELS_PATH,
    KERAS_DYNAMIC_MODEL_PATH,
    KERAS_DYNAMIC_LABELS_PATH,
    KERAS_FEATURE_COUNT,
    DYNAMIC_SEQUENCE_LENGTH,
    DATA_DIR,
)
from detector.landmark_normalizer import LandmarkNormalizer


class KerasTrainer:
    """Train and save Keras MLP/LSTM models for gesture classification."""

    def __init__(self):
        self.label_encoder = LabelEncoder()
        self.accuracy = 0.0
        self._normalizer = LandmarkNormalizer()

    # ==================================================================
    # Static MLP training
    # ==================================================================

    def train_static(
        self,
        features: np.ndarray,
        labels: list,
        epochs: int = 50,
        batch_size: int = 32,
        test_size: float = 0.2,
    ) -> float:
        """Train the Keras MLP on pre-normalized 63-feature vectors.

        Args:
            features: (N, 63) array of normalized landmark features.
            labels: list of N string labels.
            epochs: training epochs.
            batch_size: batch size.
            test_size: fraction for test split.

        Returns:
            Accuracy on test set.
        """
        from ml.keras_static_classifier import build_static_model

        y = self.label_encoder.fit_transform(labels)
        num_classes = len(self.label_encoder.classes_)

        X_train, X_test, y_train, y_test = train_test_split(
            features, y, test_size=test_size, random_state=42, stratify=y,
        )

        model = build_static_model(
            input_size=features.shape[1], num_classes=num_classes
        )
        model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            verbose=0,
        )

        loss, acc = model.evaluate(X_test, y_test, verbose=0)
        self.accuracy = float(acc)

        # Save
        model.save(KERAS_STATIC_MODEL_PATH)
        with open(KERAS_STATIC_LABELS_PATH, "wb") as f:
            pickle.dump(self.label_encoder, f)

        self._model = model
        return self.accuracy

    def train_static_from_landmarks(
        self,
        landmarks_list: list,
        labels: list,
        **kwargs,
    ) -> float:
        """Train static model from raw landmarks (21 × 3 per sample).

        Normalizes each sample with LandmarkNormalizer → 63 features.
        """
        features = []
        valid_labels = []
        for lm, lbl in zip(landmarks_list, labels):
            feat = self._normalizer.normalize(lm)
            if feat is not None:
                features.append(feat)
                valid_labels.append(lbl)

        if not features:
            return 0.0

        X = np.stack(features, axis=0)
        return self.train_static(X, valid_labels, **kwargs)

    # ==================================================================
    # Dynamic LSTM training
    # ==================================================================

    def train_dynamic(
        self,
        sequences: np.ndarray,
        labels: list,
        epochs: int = 50,
        batch_size: int = 16,
        test_size: float = 0.2,
    ) -> float:
        """Train the Keras LSTM on sequences of 63-feature vectors.

        Args:
            sequences: (N, seq_len, 63) array.
            labels: list of N string labels.

        Returns:
            Accuracy on test set.
        """
        from ml.keras_dynamic_classifier import build_dynamic_model

        y = self.label_encoder.fit_transform(labels)
        num_classes = len(self.label_encoder.classes_)
        seq_len = sequences.shape[1]

        X_train, X_test, y_train, y_test = train_test_split(
            sequences, y, test_size=test_size, random_state=42, stratify=y,
        )

        model = build_dynamic_model(
            input_size=sequences.shape[2],
            sequence_length=seq_len,
            num_classes=num_classes,
        )
        model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            verbose=0,
        )

        loss, acc = model.evaluate(X_test, y_test, verbose=0)
        self.accuracy = float(acc)

        # Save
        model.save(KERAS_DYNAMIC_MODEL_PATH)
        with open(KERAS_DYNAMIC_LABELS_PATH, "wb") as f:
            pickle.dump(self.label_encoder, f)

        self._model = model
        return self.accuracy

    # ==================================================================
    # Utilities
    # ==================================================================

    def get_classes(self) -> list:
        return self.label_encoder.classes_.tolist()

    def get_training_summary(self) -> dict:
        return {
            "accuracy": self.accuracy,
            "classes": self.get_classes(),
            "n_classes": len(self.get_classes()),
        }
