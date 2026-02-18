"""
Train the Dynamic LSTM gesture classifier on sequences of landmark frames.

For dynamic gestures (J, Z, WAVE, etc.) we need temporal sequences of 30
frames.  This script supports two data sources:

  1. A pre-collected sequence dataset (CSV with columns: label, frame_idx,
     f0..fN  — grouped by sequence_id).
  2. **Synthetic generation**: Dynamic gestures (J, Z) get trajectory-
     augmented sequences; static letters get small jitter (labelled "STATIC").

Usage:
    python train_dynamic_model.py              # synthetic generation + train
    python train_dynamic_model.py --data FILE  # train from collected file
"""
import sys
import os
import pickle
import argparse

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DYNAMIC_MODEL_PATH,
    DYNAMIC_LABELS_PATH,
    DYNAMIC_SEQUENCE_LENGTH,
    FULL_FEATURE_COUNT,
    DATA_DIR,
)
from ml.dynamic_classifier import DynamicLSTM


# ───────────────────────────── data helpers ──────────────────────────────


def _generate_synthetic_sequences(
    n_per_class: int = 200,
    seq_len: int = DYNAMIC_SEQUENCE_LENGTH,
    feat_dim: int = FULL_FEATURE_COUNT,
) -> tuple:
    """Generate synthetic training sequences for dynamic gestures.

    Returns (X, labels) where X has shape (N, seq_len, feat_dim).
    """
    rng = np.random.default_rng(42)
    sequences = []
    labels = []

    # --- Dynamic gesture profiles ---
    dynamic_profiles = {
        "J": _profile_j,
        "Z": _profile_z,
    }

    for gesture_name, profile_fn in dynamic_profiles.items():
        for _ in range(n_per_class):
            seq = profile_fn(seq_len, feat_dim, rng)
            sequences.append(seq)
            labels.append(gesture_name)

    # --- Static gestures (as "STATIC" class so LSTM learns to reject) ---
    for _ in range(n_per_class):
        base = rng.standard_normal(feat_dim).astype(np.float32) * 0.3
        seq = np.tile(base, (seq_len, 1)) + rng.normal(0, 0.01, (seq_len, feat_dim)).astype(np.float32)
        sequences.append(seq)
        labels.append("STATIC")

    X = np.stack(sequences).astype(np.float32)
    return X, labels


def _profile_j(seq_len, feat_dim, rng) -> np.ndarray:
    """Simulate a J-draw trajectory embedded in landmark space."""
    seq = np.zeros((seq_len, feat_dim), dtype=np.float32)
    base = rng.standard_normal(feat_dim).astype(np.float32) * 0.2

    for t in range(seq_len):
        frac = t / max(seq_len - 1, 1)
        # J motion: down then curve left
        dx = -0.3 * max(0, frac - 0.5) + rng.normal(0, 0.01)
        dy = 0.4 * frac + rng.normal(0, 0.01)
        offset = np.zeros(feat_dim, dtype=np.float32)
        offset[0] = dx
        offset[1] = dy
        seq[t] = base + offset + rng.normal(0, 0.008, feat_dim).astype(np.float32)

    return seq


def _profile_z(seq_len, feat_dim, rng) -> np.ndarray:
    """Simulate a Z-draw trajectory."""
    seq = np.zeros((seq_len, feat_dim), dtype=np.float32)
    base = rng.standard_normal(feat_dim).astype(np.float32) * 0.2
    third = seq_len // 3

    for t in range(seq_len):
        offset = np.zeros(feat_dim, dtype=np.float32)
        if t < third:  # right
            offset[0] = 0.4 * (t / third)
        elif t < 2 * third:  # diagonal down-left
            local = (t - third) / third
            offset[0] = 0.4 - 0.8 * local
            offset[1] = 0.4 * local
        else:  # right again
            local = (t - 2 * third) / max(third, 1)
            offset[0] = -0.4 + 0.8 * local
            offset[1] = 0.4
        seq[t] = base + offset + rng.normal(0, 0.008, feat_dim).astype(np.float32)

    return seq


# ───────────────────────────── training ──────────────────────────────────


def train(
    X: np.ndarray,
    labels: list,
    epochs: int = 100,
    batch_size: int = 32,
    lr: float = 1e-3,
    test_size: float = 0.2,
):
    le = LabelEncoder()
    y = le.fit_transform(labels)
    num_classes = len(le.classes_)

    print(f"Samples: {X.shape[0]}, seq_len={X.shape[1]}, features={X.shape[2]}")
    print(f"Classes ({num_classes}): {', '.join(le.classes_)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.long)

    train_ds = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DynamicLSTM(
        input_size=X.shape[2], num_classes=num_classes
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    print(f"\nTraining on {device} for {epochs} epochs...")
    print(f"Model params: {sum(p.numel() for p in model.parameters()):,}")

    best_acc = 0.0
    best_state = None
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

        model.eval()
        with torch.no_grad():
            logits = model(X_test_t.to(device))
            preds = logits.argmax(dim=1).cpu()
            acc = (preds == y_test_t).float().mean().item()

        avg_loss = total_loss / len(train_ds)
        if epoch % 20 == 0 or epoch == 1 or epoch == epochs:
            print(f"  Epoch {epoch:3d}  loss={avg_loss:.4f}  test_acc={acc:.1%}")

        if acc > best_acc:
            best_acc = acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    print(f"\nBest test accuracy: {best_acc:.1%}")

    # Save
    torch.save(best_state, DYNAMIC_MODEL_PATH)
    with open(DYNAMIC_LABELS_PATH, "wb") as f:
        pickle.dump(le, f)

    print(f"Model saved to {DYNAMIC_MODEL_PATH}")
    print(f"Labels saved to {DYNAMIC_LABELS_PATH}")


# ───────────────────────────── main ──────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Train dynamic LSTM gesture model")
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to pre-collected sequence CSV. If omitted, uses synthetic data.",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--samples", type=int, default=300, help="Synthetic samples per class")
    args = parser.parse_args()

    if args.data and os.path.exists(args.data):
        print(f"Loading sequences from {args.data}...")
        import csv

        sequences_by_id = {}
        with open(args.data, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                sid = row[0]
                label = row[1]
                feats = [float(v) for v in row[2:]]
                if sid not in sequences_by_id:
                    sequences_by_id[sid] = {"label": label, "frames": []}
                sequences_by_id[sid]["frames"].append(feats)

        X_list, labels = [], []
        for sid, data in sequences_by_id.items():
            arr = np.array(data["frames"], dtype=np.float32)
            if arr.shape[0] < DYNAMIC_SEQUENCE_LENGTH:
                pad = np.zeros(
                    (DYNAMIC_SEQUENCE_LENGTH - arr.shape[0], arr.shape[1]),
                    dtype=np.float32,
                )
                arr = np.concatenate([pad, arr])
            elif arr.shape[0] > DYNAMIC_SEQUENCE_LENGTH:
                arr = arr[-DYNAMIC_SEQUENCE_LENGTH:]
            X_list.append(arr)
            labels.append(data["label"])

        X = np.stack(X_list)
        train(X, labels, epochs=args.epochs)
    else:
        print("Generating synthetic dynamic gesture sequences...")
        X, labels = _generate_synthetic_sequences(n_per_class=args.samples)
        train(X, labels, epochs=args.epochs)


if __name__ == "__main__":
    main()
