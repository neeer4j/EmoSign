"""
ASL Number Data Generator (0-9)

Generates synthetic landmark data for ASL numbers 0-9 and appends
them to data/asl_enhanced_data.csv so the Keras MLP can recognise digits.

ASL number hand shapes:
  0 - All fingers curved into O (like letter O)
  1 - Index extended up, others folded, thumb out
  2 - Index + middle extended (V / peace sign)
  3 - Thumb + index + middle extended
  4 - Four fingers extended (index/middle/ring/pinky), thumb folded
  5 - Open hand, all 5 fingers extended
  6 - Pinky + thumb touch, index/middle/ring extended
  7 - Ring + thumb touch, index/middle/pinky extended
  8 - Middle + thumb touch, index/ring/pinky extended
  9 - Index + thumb form a loop (like F), others folded
"""
import os
import sys
import csv
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import DATA_DIR

CSV_PATH = os.path.join(DATA_DIR, "asl_enhanced_data.csv")
SAMPLES_PER_DIGIT = 200


# ---------------------------------------------------------------------------
# Landmark template (matches generate_enhanced_data.py exactly)
# ---------------------------------------------------------------------------

def _hand_template():
    lm = np.zeros((21, 3), dtype=np.float32)
    lm[0]  = [0.5, 0.8, 0]    # Wrist
    lm[1]  = [0.35, 0.7, 0]   # Thumb CMC
    lm[5]  = [0.35, 0.55, 0]  # Index  MCP
    lm[9]  = [0.45, 0.5, 0]   # Middle MCP
    lm[13] = [0.55, 0.55, 0]  # Ring   MCP
    lm[17] = [0.65, 0.62, 0]  # Pinky  MCP
    return lm


# map finger index → (MCP, PIP, DIP, TIP)
_FINGER_JOINTS = {
    0: (1, 2, 3, 4),     # Thumb
    1: (5, 6, 7, 8),     # Index
    2: (9, 10, 11, 12),  # Middle
    3: (13, 14, 15, 16), # Ring
    4: (17, 18, 19, 20), # Pinky
}

_FINGER_DIR = {
    0: np.array([-0.10, -0.15, 0.0]),   # Thumb
    1: np.array([0.0,   -0.15, 0.0]),   # Index
    2: np.array([0.0,   -0.15, 0.0]),   # Middle
    3: np.array([0.0,   -0.15, 0.0]),   # Ring
    4: np.array([0.0,   -0.15, 0.0]),   # Pinky
}


def _set(lm, finger, state, var=0.03):
    mcp, pip, dip, tip = _FINGER_JOINTS[finger]
    d = _FINGER_DIR[finger]
    n = np.random.randn(3) * var

    if state == 'extended':
        lm[pip] = lm[mcp] + d + n
        lm[dip] = lm[pip] + d * 0.8 + n * 0.5
        lm[tip] = lm[dip] + d * 0.6 + n * 0.3

    elif state == 'folded':
        fd = np.array([0.05, 0.1, 0.02])
        lm[pip] = lm[mcp] + d * 0.2 + n
        lm[dip] = lm[pip] + fd + n * 0.5
        lm[tip] = lm[dip] + fd * 0.5 + n * 0.3

    elif state == 'curved':
        lm[pip] = lm[mcp] + d * 0.6 + n
        lm[dip] = lm[pip] + d * 0.4 + np.array([0.03, 0.02, 0]) + n * 0.5
        lm[tip] = lm[dip] + d * 0.2 + np.array([0.05, 0.03, 0]) + n * 0.3

    elif state == 'bent':
        lm[pip] = lm[mcp] + d * 0.5 + n
        bd = np.array([0.1, 0.05, 0.05])
        lm[dip] = lm[pip] + bd + n * 0.5
        lm[tip] = lm[dip] + bd * 0.7 + n * 0.3

    elif state == 'o_curl':
        # Rounded shape for 0
        lm[pip] = lm[mcp] + d * 0.4 + n
        lm[dip] = lm[pip] + np.array([0.06, 0.04, 0]) + n * 0.5
        lm[tip] = lm[dip] + np.array([0.07, 0.02, 0]) + n * 0.3

    elif state == 'touch_thumb':
        # Fingertip rests near thumb tip (pinch / touch)
        lm[pip] = lm[mcp] + d * 0.3 + n
        lm[dip] = lm[pip] + np.array([0.02, 0.06, -0.02]) + n * 0.5
        lm[tip] = lm[dip] + np.array([0.01, 0.04, -0.03]) + n * 0.3

    elif state == 'thumb_out':
        # Thumb clearly side-extended
        lm[2] = lm[1] + np.array([-0.12, -0.05, 0]) + n
        lm[3] = lm[2] + np.array([-0.10, -0.04, 0]) + n * 0.6
        lm[4] = lm[3] + np.array([-0.08, -0.03, 0]) + n * 0.3

    return lm


# ---------------------------------------------------------------------------
# Hand shape definitions for digits 0-9
# ---------------------------------------------------------------------------

def _create_digit(digit, variation=0.03):
    lm = _hand_template()

    # Thumb base position (needed before _set calls)
    lm[2] = lm[1] + np.array([-0.06, -0.04, 0])
    lm[3] = lm[2] + np.array([-0.04, -0.03, 0])
    lm[4] = lm[3] + np.array([-0.03, -0.02, 0])

    if digit == '0':
        # O shape — all fingers gently curled, thumb meets index tip
        _set(lm, 0, 'o_curl', variation)
        _set(lm, 1, 'o_curl', variation)
        _set(lm, 2, 'o_curl', variation)
        _set(lm, 3, 'o_curl', variation)
        _set(lm, 4, 'o_curl', variation)

    elif digit == '1':
        # Index pointing up, thumb out, others folded
        _set(lm, 0, 'thumb_out', variation)
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'folded', variation)
        _set(lm, 3, 'folded', variation)
        _set(lm, 4, 'folded', variation)

    elif digit == '2':
        # V sign — index + middle extended, others folded
        _set(lm, 0, 'folded', variation)
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'extended', variation)
        _set(lm, 3, 'folded', variation)
        _set(lm, 4, 'folded', variation)

    elif digit == '3':
        # Thumb + index + middle extended
        _set(lm, 0, 'thumb_out', variation)
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'extended', variation)
        _set(lm, 3, 'folded', variation)
        _set(lm, 4, 'folded', variation)

    elif digit == '4':
        # Four fingers extended (no thumb)
        _set(lm, 0, 'folded', variation)
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'extended', variation)
        _set(lm, 3, 'extended', variation)
        _set(lm, 4, 'extended', variation)

    elif digit == '5':
        # Open hand — all 5 fingers extended
        _set(lm, 0, 'thumb_out', variation)
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'extended', variation)
        _set(lm, 3, 'extended', variation)
        _set(lm, 4, 'extended', variation)

    elif digit == '6':
        # Pinky + thumb touching; index/middle/ring extended
        _set(lm, 0, 'touch_thumb', variation)   # thumb bends toward pinky
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'extended', variation)
        _set(lm, 3, 'extended', variation)
        _set(lm, 4, 'touch_thumb', variation)    # pinky bends toward thumb

    elif digit == '7':
        # Ring + thumb touching; index/middle/pinky extended
        _set(lm, 0, 'touch_thumb', variation)
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'extended', variation)
        _set(lm, 3, 'touch_thumb', variation)    # ring bends toward thumb
        _set(lm, 4, 'extended', variation)

    elif digit == '8':
        # Middle + thumb touching; index/ring/pinky extended
        _set(lm, 0, 'touch_thumb', variation)
        _set(lm, 1, 'extended', variation)
        _set(lm, 2, 'touch_thumb', variation)    # middle bends toward thumb
        _set(lm, 3, 'extended', variation)
        _set(lm, 4, 'extended', variation)

    elif digit == '9':
        # Index + thumb form a loop (like F), others folded
        _set(lm, 0, 'touch_thumb', variation)
        _set(lm, 1, 'touch_thumb', variation)    # index bends toward thumb
        _set(lm, 2, 'folded', variation)
        _set(lm, 3, 'folded', variation)
        _set(lm, 4, 'folded', variation)

    return lm


# ---------------------------------------------------------------------------
# Feature extraction (must match detector/features.py exactly)
# ---------------------------------------------------------------------------

def _extract_features(lm):
    wrist = lm[0]
    norm = lm - wrist
    scale = np.linalg.norm(lm[9] - lm[0])
    if scale > 0:
        norm = norm / scale

    feats = norm.flatten().tolist()   # 63 features

    # Finger tip → MCP distances (5)
    tips  = [4, 8, 12, 16, 20]
    mcps  = [2, 5,  9, 13, 17]
    feats += [np.linalg.norm(lm[t] - lm[m]) / (scale or 1) for t, m in zip(tips, mcps)]

    # Thumb tip → each fingertip (4)
    thumb_tip = lm[4]
    feats += [np.linalg.norm(thumb_tip - lm[t]) / (scale or 1) for t in [8, 12, 16, 20]]

    # Z-depth thumb - fingertip (4)
    feats += [(lm[4][2] - lm[t][2]) / (scale or 1) for t in [8, 12, 16, 20]]

    # Fingertip → palm centre (5)
    palm = lm[9]
    feats += [np.linalg.norm(lm[t] - palm) / (scale or 1) for t in tips]

    # Hand orientation (1)
    avg_tip_y = np.mean([lm[t][1] for t in tips[1:]])
    avg_mcp_y = np.mean([lm[m][1] for m in [5, 9, 13, 17]])
    feats.append((avg_mcp_y - avg_tip_y) / (scale or 1))

    # Finger curl angles at PIP (5)
    pips = [3, 6, 10, 14, 18]
    for t, p, m in zip(tips, pips, mcps):
        v1 = lm[m] - lm[p]
        v2 = lm[t] - lm[p]
        cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        feats.append(float(np.arccos(np.clip(cos_a, -1, 1)) / np.pi))

    return feats   # 87 features total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_and_append():
    """Generate 0-9 samples and append to asl_enhanced_data.csv."""
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found — run generate_enhanced_data.py first.")
        sys.exit(1)

    # Check if numbers already in file
    with open(CSV_PATH) as f:
        existing_labels = {row.split(',')[0] for row in f if row.strip()}
    if '0' in existing_labels:
        print("Numbers 0-9 already present in training data. Removing old entries first...")
        # Re-read, filter out old number rows, rewrite
        with open(CSV_PATH) as f:
            rows = f.readlines()
        with open(CSV_PATH, 'w') as f:
            for row in rows:
                label = row.split(',')[0]
                if label not in set('0123456789'):
                    f.write(row)
        print("Old number rows removed.")

    print(f"Generating {SAMPLES_PER_DIGIT} samples per digit (0-9)...")
    np.random.seed(123)

    new_rows = []
    for digit in "0123456789":
        for i in range(SAMPLES_PER_DIGIT):
            if i < SAMPLES_PER_DIGIT * 0.4:
                var = 0.015 + np.random.rand() * 0.02
            elif i < SAMPLES_PER_DIGIT * 0.75:
                var = 0.03  + np.random.rand() * 0.03
            else:
                var = 0.05  + np.random.rand() * 0.035

            lm    = _create_digit(digit, var)
            feats = _extract_features(lm)
            new_rows.append([digit] + feats)

    with open(CSV_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        for row in new_rows:
            writer.writerow(row)

    total = len(new_rows)
    print(f"Appended {total} number samples to {CSV_PATH}")
    print("Now run:  python scripts/train_keras_models.py")


if __name__ == "__main__":
    generate_and_append()
