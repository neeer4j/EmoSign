# Machine Learning Framework Usage Report

This document clarifies the machine learning frameworks, loading procedures, and inference logic currently active in the application.

### 1. Active Framework for Inference
The app currently uses **TensorFlow / Keras** for all neural-network-based predictions at runtime. 
**scikit-learn** is used only for post-processing (decoding numeric indices back to letter labels).

### 2. Model Loading
- **File:** [keras_static_classifier.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/keras_static_classifier.py)
- **Function:** `KerasStaticClassifier.load()`
- **Loading Implementation:**
```python
def load(self, model_path=None, labels_path=None):
    # ...
    self.model = tf.keras.models.load_model(model_path) # Exact load call
    with open(labels_path, "rb") as f:
        self.label_encoder = pickle.load(f) # Scikit-learn LabelEncoder
```

### 3. Inference Execution (.predict)
- **File:** [keras_static_classifier.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/keras_static_classifier.py)
- **Function:** `KerasStaticClassifier.predict_from_features()`
- **Inference Implementation:**
```python
def predict_from_features(self, features):
    # ...
    # TensorFlow/Keras inference call
    probs = self.model.predict(features.reshape(1, -1), verbose=0)[0]
    
    idx = int(np.argmax(probs))
    # Label decoding via scikit-learn
    label = self.label_encoder.inverse_transform([idx])[0]
    return label, float(probs[idx])
```

### 4. ML-Related Imports across the Project
The following frameworks are imported in various parts of the codebase:
- **`tensorflow` / `keras`**: Primary inference engine ([ml/gesture_pipeline.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/gesture_pipeline.py), [ml/keras_static_classifier.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/keras_static_classifier.py), [ml/keras_dynamic_classifier.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/keras_dynamic_classifier.py)).
- **`sklearn` (scikit-learn)**: Used for label encoding/decoding during inference ([ml/keras_static_classifier.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/keras_static_classifier.py)) and for the legacy RandomForest trainer ([ml/trainer.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/trainer.py)).
- **`torch` (PyTorch)**: Imported in the legacy [ml/static_classifier.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/static_classifier.py) and [ml/dynamic_classifier.py](file:///c:/NEERAJVENU/PROJECTS/signlanguage/ml/dynamic_classifier.py) files.

### 5. Unused Frameworks (Inactive)
- **PyTorch (torch)**: Although installed, PyTorch is **NOT used** in the current runtime inference pipeline. All UI components (`camera_widget`, `video_player_widget`) have been migrated to the `GesturePipeline`, which uses the new Keras-based classifiers.

### 6. Model File Format
The system loads models in the **`.keras`** (TensorFlow/Keras SavedModel format) and **`.pkl`** (Python Pickle for LabelEncoder) formats.
- **Model:** `models/keras_static_mlp.keras`
- **Labels:** `models/keras_static_labels.pkl`

---

### Final Statement
**"The app currently uses TensorFlow / Keras for inference."**
