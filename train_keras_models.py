"""
Train Keras MLP for static ASL letters using existing landmark data.

Reads the existing asl_enhanced_data.csv, extracts the first 63 features
(which are wrist-relative, palm-scaled coordinates — identical to
LandmarkNormalizer output), and trains the Keras MLP.

Usage:
    python train_keras_models.py
"""
import os
import sys
import csv
import pickle
import numpy as np
from collections import Counter
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DATA_DIR,
    KERAS_STATIC_MODEL_PATH,
    KERAS_STATIC_LABELS_PATH,
    KERAS_FEATURE_COUNT,
)


def load_csv_data(filepath, feature_count=63):
    """Load training data from CSV, extracting coordinate features only."""
    features = []
    labels = []

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = next(reader)  # skip header

        for row in reader:
            label = row[0]
            # Take only the first 63 features (normalized x,y,z coordinates)
            feat = [float(x) for x in row[1 : feature_count + 1]]
            features.append(feat)
            labels.append(label)

    return np.array(features, dtype=np.float32), labels


def train_static_model():
    """Train the Keras MLP on static ASL letter data."""
    # Suppress TF logging
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    import tensorflow as tf

    csv_path = os.path.join(DATA_DIR, "asl_enhanced_data.csv")
    if not os.path.exists(csv_path):
        print(f"ERROR: Training data not found at {csv_path}")
        return

    print("=" * 60)
    print("  Keras Static MLP Training — ASL Letters")
    print("=" * 60)

    # 1. Load data
    print(f"\n[1/5] Loading data from {csv_path}...")
    X, y_str = load_csv_data(csv_path, KERAS_FEATURE_COUNT)
    print(f"      Loaded {len(X)} samples, {KERAS_FEATURE_COUNT} features each")

    # Class distribution
    dist = Counter(y_str)
    print(f"      Classes: {len(dist)}")
    for cls in sorted(dist.keys()):
        print(f"        {cls}: {dist[cls]} samples")

    # 2. Encode labels
    print("\n[2/5] Encoding labels...")
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_str)
    num_classes = len(label_encoder.classes_)
    print(f"      {num_classes} classes: {label_encoder.classes_.tolist()}")

    # 3. Split
    print("\n[3/5] Splitting train/test (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"      Train: {len(X_train)}, Test: {len(X_test)}")

    # 4. Build and train model
    print("\n[4/5] Building Keras MLP...")
    print("      Architecture: Dense(128,ReLU) → Dense(128,ReLU) → Dropout(0.3) → Dense(26,Softmax)")

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(KERAS_FEATURE_COUNT,)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    print("\n      Training (50 epochs)...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=50,
        batch_size=32,
        verbose=1,
    )

    # 5. Evaluate
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n[5/5] Results:")
    print(f"      Test Accuracy:  {acc * 100:.2f}%")
    print(f"      Test Loss:     {loss:.4f}")

    # Training history summary
    train_acc = history.history["accuracy"][-1]
    val_acc = history.history["val_accuracy"][-1]
    print(f"      Train Accuracy: {train_acc * 100:.2f}%")
    print(f"      Val Accuracy:   {val_acc * 100:.2f}%")

    # Save
    print(f"\n      Saving model to {KERAS_STATIC_MODEL_PATH}...")
    model.save(KERAS_STATIC_MODEL_PATH)
    with open(KERAS_STATIC_LABELS_PATH, "wb") as f:
        pickle.dump(label_encoder, f)
    print(f"      Saving labels to {KERAS_STATIC_LABELS_PATH}...")

    print("\n" + "=" * 60)
    print("  Training complete!")
    print("=" * 60)

    return acc


if __name__ == "__main__":
    train_static_model()
