"""
Static Gesture Classifier - Feedforward Neural Network

Classifies static ASL gestures from single-frame MediaPipe landmarks using
the full 87-feature set from FeatureExtractor (63 normalised coords + 24
derived features including z-depth, finger distances, curl angles, orientation).
"""
import os
import pickle
import numpy as np

import torch
import torch.nn as nn

from config import STATIC_MODEL_PATH, STATIC_LABELS_PATH, FULL_FEATURE_COUNT
from detector.features import FeatureExtractor


class StaticFFN(nn.Module):
    """Feedforward neural network for static gesture classification.

    Architecture: deeper network with residual-style skip connections
    for better gradient flow across 26+ classes.
    """

    def __init__(self, input_size: int = FULL_FEATURE_COUNT, num_classes: int = 26):
        super().__init__()
        self.input_proj = nn.Linear(input_size, 512)
        self.bn0 = nn.BatchNorm1d(512)

        # Block 1
        self.fc1 = nn.Linear(512, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.drop1 = nn.Dropout(0.3)

        # Block 2
        self.fc2 = nn.Linear(512, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.drop2 = nn.Dropout(0.25)

        # Block 3
        self.fc3 = nn.Linear(256, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.drop3 = nn.Dropout(0.2)

        # Head
        self.fc4 = nn.Linear(128, 64)
        self.head = nn.Linear(64, num_classes)

        # Skip projection (512 → 256) for residual
        self.skip_proj = nn.Linear(512, 256)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input projection
        x = torch.relu(self.bn0(self.input_proj(x)))

        # Block 1 (with residual)
        identity = x
        x = self.drop1(torch.relu(self.bn1(self.fc1(x))))
        x = x + identity  # residual

        # Block 2 (with skip from 512→256)
        skip = self.skip_proj(x)
        x = self.drop2(torch.relu(self.bn2(self.fc2(x))))
        x = x + skip  # residual

        # Block 3
        x = self.drop3(torch.relu(self.bn3(self.fc3(x))))

        # Head
        x = torch.relu(self.fc4(x))
        return self.head(x)


class StaticGestureClassifier:
    """Wrapper that loads a trained StaticFFN and runs real-time inference
    using the full FeatureExtractor (87 features)."""

    def __init__(self):
        self.model: StaticFFN | None = None
        self.label_encoder = None
        self.is_loaded = False
        self.device = torch.device("cpu")
        self._feature_extractor = FeatureExtractor()

    def load(
        self,
        model_path: str | None = None,
        labels_path: str | None = None,
    ) -> bool:
        """Load trained model weights and label encoder."""
        model_path = model_path or STATIC_MODEL_PATH
        labels_path = labels_path or STATIC_LABELS_PATH

        if not os.path.exists(model_path) or not os.path.exists(labels_path):
            return False

        try:
            with open(labels_path, "rb") as f:
                self.label_encoder = pickle.load(f)

            num_classes = len(self.label_encoder.classes_)
            self.model = StaticFFN(
                input_size=FULL_FEATURE_COUNT, num_classes=num_classes
            )
            state = torch.load(model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            self.model.eval()
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"[StaticClassifier] Error loading model: {e}")
            return False

    @torch.no_grad()
    def predict(self, landmarks) -> tuple:
        """Predict static gesture from a single frame of landmarks.

        Uses FeatureExtractor.extract() for the full 87-feature set including
        z-depth differences, thumb-finger distances, curl angles, and orientation.

        Args:
            landmarks: list of 21 (x, y, z) tuples.

        Returns:
            (label: str | None, confidence: float)
        """
        if not self.is_loaded:
            return None, 0.0

        features = self._feature_extractor.extract(landmarks)
        if features is None:
            return None, 0.0

        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        logits = self.model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0)

        confidence, idx = probs.max(dim=0)
        label = self.label_encoder.inverse_transform([idx.item()])[0]
        return label, float(confidence)

    @torch.no_grad()
    def predict_from_features(self, features: np.ndarray) -> tuple:
        """Predict from pre-extracted feature vector (87 features)."""
        if not self.is_loaded or features is None:
            return None, 0.0

        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        logits = self.model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0)

        confidence, idx = probs.max(dim=0)
        label = self.label_encoder.inverse_transform([idx.item()])[0]
        return label, float(confidence)

    def predict_top_n(self, landmarks, n: int = 3) -> list:
        """Return top-n predictions as list of (label, confidence)."""
        if not self.is_loaded:
            return []

        features = self._feature_extractor.extract(landmarks)
        if features is None:
            return []
        return self._predict_top_n_from_features(features, n)

    @torch.no_grad()
    def _predict_top_n_from_features(self, features: np.ndarray, n: int = 3) -> list:
        """Return top-n predictions from a pre-extracted feature vector."""
        if not self.is_loaded or features is None:
            return []

        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        logits = self.model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0)

        topk = torch.topk(probs, min(n, len(probs)))
        results = []
        for score, idx in zip(topk.values, topk.indices):
            label = self.label_encoder.inverse_transform([idx.item()])[0]
            results.append((label, float(score)))
        return results

    def get_classes(self) -> list:
        if self.label_encoder is None:
            return []
        return self.label_encoder.classes_.tolist()
