"""
Dynamic Gesture Classifier - LSTM Neural Network

Classifies motion-based ASL gestures from sequences of 30 frames.
Each frame uses the full 87-feature FeatureExtractor output (63 normalised
coords + 24 derived features) for maximum discriminative power.
"""
import os
import pickle
import numpy as np

import torch
import torch.nn as nn

from config import (
    DYNAMIC_MODEL_PATH,
    DYNAMIC_LABELS_PATH,
    DYNAMIC_SEQUENCE_LENGTH,
    FULL_FEATURE_COUNT,
)
from detector.features import FeatureExtractor


class DynamicLSTM(nn.Module):
    """LSTM network for dynamic (motion-based) gesture classification."""

    def __init__(
        self,
        input_size: int = FULL_FEATURE_COUNT,
        hidden_size: int = 256,
        num_layers: int = 2,
        num_classes: int = 26,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: (batch, seq_len, input_size)

        Returns:
            logits: (batch, num_classes)
        """
        lstm_out, _ = self.lstm(x)  # (batch, seq, hidden)
        last_hidden = lstm_out[:, -1, :]  # (batch, hidden)
        return self.classifier(last_hidden)


class DynamicGestureClassifier:
    """Wrapper that loads a trained DynamicLSTM and runs real-time inference
    on buffered 30-frame landmark sequences using full 87-feature extraction."""

    def __init__(self):
        self.model: DynamicLSTM | None = None
        self.label_encoder = None
        self.is_loaded = False
        self.device = torch.device("cpu")
        self.sequence_length = DYNAMIC_SEQUENCE_LENGTH
        self._feature_extractor = FeatureExtractor()

    def load(
        self,
        model_path: str | None = None,
        labels_path: str | None = None,
    ) -> bool:
        """Load trained model weights and label encoder."""
        model_path = model_path or DYNAMIC_MODEL_PATH
        labels_path = labels_path or DYNAMIC_LABELS_PATH

        if not os.path.exists(model_path) or not os.path.exists(labels_path):
            return False

        try:
            with open(labels_path, "rb") as f:
                self.label_encoder = pickle.load(f)

            num_classes = len(self.label_encoder.classes_)
            self.model = DynamicLSTM(
                input_size=FULL_FEATURE_COUNT, num_classes=num_classes
            )
            state = torch.load(model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            self.model.eval()
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"[DynamicClassifier] Error loading model: {e}")
            return False

    def extract_sequence_features(self, landmark_sequence) -> np.ndarray | None:
        """Convert a sequence of raw landmarks into (seq_len, 87) feature array.

        Each frame is processed through FeatureExtractor.extract() to get the
        full 87-feature set (coords + distances + z-depth + curl angles + orientation).

        Args:
            landmark_sequence: list of frames, each frame is list of 21 (x,y,z).

        Returns:
            numpy float32 array of shape (seq_len, 87) or None.
        """
        if landmark_sequence is None or len(landmark_sequence) == 0:
            return None

        frames = []
        for lm in landmark_sequence:
            feat = self._feature_extractor.extract(lm)
            if feat is None:
                return None
            frames.append(feat)

        return np.stack(frames, axis=0)

    @torch.no_grad()
    def predict(self, landmark_sequence) -> tuple:
        """Predict dynamic gesture from a buffered landmark sequence.

        Args:
            landmark_sequence: list of 30 frames, each frame list of 21 (x,y,z).

        Returns:
            (label: str | None, confidence: float)
        """
        if not self.is_loaded:
            return None, 0.0

        features = self.extract_sequence_features(landmark_sequence)
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

        x = (
            torch.tensor(features, dtype=torch.float32)
            .unsqueeze(0)
            .to(self.device)
        )
        logits = self.model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0)

        confidence, idx = probs.max(dim=0)
        label = self.label_encoder.inverse_transform([idx.item()])[0]
        return label, float(confidence)

    def get_classes(self) -> list:
        if self.label_encoder is None:
            return []
        return self.label_encoder.classes_.tolist()
