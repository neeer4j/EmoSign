# Sign Language Detection Pipeline — Technical Details

### 1. Inference Model & Framework
**Framework:** TensorFlow / Keras (MLP for static, LSTM for dynamic).
The system uses the `GesturePipeline` orchestrator which routes frames based on movement.

**Inference Code:**
```python
# From ml/gesture_pipeline.py
def process_frame(self, landmarks):
    # 1. Normalize landmarks (63 features)
    # 2. Check displacement (movement detection)
    # 3. Predict using KerasStaticClassifier (MLP) or KerasDynamicClassifier (LSTM)
    # 4. Apply majority-vote smoothing
    # 5. Apply 0.75 confidence filter
    
    lm = np.array(landmarks, dtype=np.float32)
    # ...
    if is_buffering:
        label, conf = self.dynamic_classifier.predict(self._landmark_buffer)
    else:
        label, conf = self.static_classifier.predict(landmarks)
```

### 2. Landmark Normalization
**Yes**, landmark normalization is applied to ensure translation and scale invariance. The exact same function is used during both training and inference.

**Normalization Function:**
```python
# From detector/landmark_normalizer.py
def normalize(landmarks):
    lm = np.array(landmarks, dtype=np.float32)
    # 1. Translate relative to wrist (landmark 0)
    wrist = lm[0]
    lm = lm - wrist
    # 2. Scale by palm size (wrist to middle-MCP distance)
    scale = np.linalg.norm(lm[9])
    if scale < 1e-6: scale = 1.0
    lm = lm / scale
    # 3. Flatten to 63 features (21 landmarks x 3 coords)
    return lm.flatten()
```

### 3. Training Data Distribution
The `asl_enhanced_data.csv` contains **600 samples per class** for each letter of the alphabet (A-Z).
Total dataset size: 15,600 samples.

### 4. Dynamic Letters (J, Z)
Letters **J** and **Z** are trained as **sequence-based models** using a 2-layer LSTM (64 hidden units).
- **Sequence Length:** 30 frames.
- **Routing:** Triggers automatically when landmark displacement exceeds `MOVEMENT_THRESHOLD`.

### 5. Prediction Smoothing
**Yes**, smoothing is implemented using a **5-frame majority vote** (rolling window).
A prediction must appear in the majority of the last 5 frames and maintain a consistency score to be accepted.

### 6. Confidence Threshold
**Yes**, a confidence filter is applied via `MIN_PREDICTION_CONFIDENCE = 0.75`.
Predictions with a probability lower than 75% are suppressed to prevent flickering and false positives.

### 7. Accuracy
The system architecture is redesigned for Keras. Legacy PyTorch models achieved **>98% training/validation accuracy**. The new Keras MLP/LSTM models are initialized for training with the 63-feature normalized dataset.

### 8. Multi-Hand Support
**Current Status:** Single-hand detection for classification.
While `MAX_HANDS = 2` is enabled in configuration and `HandTracker` detects both, the `GesturePipeline` currently extracts landmarks from the **first detected hand** (index 0) for inference to maximize performance on low-end systems.
