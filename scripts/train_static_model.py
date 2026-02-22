"""
Train the Static FFN gesture classifier on single-frame landmarks.

Reads all CSV files from data/ and trains a feedforward neural network
on the full 87-feature set (normalised coords + derived features).
Regenerates data if needed to ensure feature count matches.

Usage:
    python train_static_model.py
    python train_static_model.py --regen   # force regenerate data first
"""
import sys
import os
import pickle

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import STATIC_MODEL_PATH, STATIC_LABELS_PATH, FULL_FEATURE_COUNT
from ml.static_classifier import StaticFFN
from ml.data_collector import DataCollector


def train(
    epochs: int = 200,
    batch_size: int = 64,
    lr: float = 1e-3,
    test_size: float = 0.2,
    regen: bool = False,
):
    # Regenerate data if requested
    if regen:
        print("Regenerating training data with 87 features...")
        from generate_enhanced_data import generate_enhanced_dataset
        generate_enhanced_dataset(samples_per_letter=400)
        print()

    print("Loading training data...")
    features, labels = DataCollector.load_all_data()

    if features is None:
        print("ERROR: No training data found in data/ directory!")
        print("Run: python generate_enhanced_data.py")
        return

    actual_feat_count = features.shape[1]
    print(f"Loaded {len(labels)} samples, {actual_feat_count} features per sample")
    print(f"Classes: {sorted(set(labels))}")

    # Ensure feature count matches FULL_FEATURE_COUNT (87)
    if actual_feat_count < FULL_FEATURE_COUNT:
        print(f"WARNING: Data has {actual_feat_count} features but model expects {FULL_FEATURE_COUNT}.")
        print("Regenerating data with current FeatureExtractor (87 features)...")
        from generate_enhanced_data import generate_enhanced_dataset
        generate_enhanced_dataset(samples_per_letter=400)
        features, labels = DataCollector.load_all_data()
        actual_feat_count = features.shape[1]
        print(f"Reloaded: {len(labels)} samples, {actual_feat_count} features")

    if actual_feat_count > FULL_FEATURE_COUNT:
        features = features[:, :FULL_FEATURE_COUNT]
    elif actual_feat_count < FULL_FEATURE_COUNT:
        pad = np.zeros(
            (features.shape[0], FULL_FEATURE_COUNT - actual_feat_count),
            dtype=np.float32,
        )
        features = np.concatenate([features, pad], axis=1)

    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(labels)
    num_classes = len(le.classes_)
    print(f"Number of classes: {num_classes}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        features, y, test_size=test_size, random_state=42, stratify=y
    )

    # Convert to tensors
    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.long)

    train_ds = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    # Build model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = StaticFFN(input_size=FULL_FEATURE_COUNT, num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    print(f"\nTraining on {device} for {epochs} epochs...")
    print(f"Model params: {sum(p.numel() for p in model.parameters()):,}")

    best_acc = 0.0
    best_state = None
    patience = 30
    no_improve = 0

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item() * xb.size(0)
        scheduler.step()

        # Evaluate
        model.eval()
        with torch.no_grad():
            logits = model(X_test_t.to(device))
            preds = logits.argmax(dim=1).cpu()
            acc = (preds == y_test_t).float().mean().item()

        avg_loss = total_loss / len(train_ds)
        if epoch % 20 == 0 or epoch == 1 or epoch == epochs:
            current_lr = scheduler.get_last_lr()[0]
            print(f"  Epoch {epoch:3d}  loss={avg_loss:.4f}  test_acc={acc:.1%}  lr={current_lr:.2e}")

        if acc > best_acc:
            best_acc = acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1

        if no_improve >= patience:
            print(f"  Early stopping at epoch {epoch} (no improvement for {patience} epochs)")
            break

    print(f"\nBest test accuracy: {best_acc:.1%}")

    # Save model
    torch.save(best_state, STATIC_MODEL_PATH)
    with open(STATIC_LABELS_PATH, "wb") as f:
        pickle.dump(le, f)

    print(f"Model saved to {STATIC_MODEL_PATH}")
    print(f"Labels saved to {STATIC_LABELS_PATH}")
    print(f"Classes: {', '.join(le.classes_)}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--regen", action="store_true", help="Force regenerate training data")
    parser.add_argument("--epochs", type=int, default=200)
    args = parser.parse_args()
    train(epochs=args.epochs, regen=args.regen)
