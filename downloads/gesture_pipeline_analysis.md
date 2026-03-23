# Gesture Pipeline Movement Detection Analysis

## 1. Movement Detection Logic  
**File:** ml/gesture_pipeline.py (lines 97-112)

```python
def _compute_displacement(self, landmarks: np.ndarray) -> float:
    """Mean displacement of 21 landmarks vs previous frame, normalized."""
    if self._prev_landmarks is None:
        return 0.0

    diff = landmarks - self._prev_landmarks
    per_point = np.linalg.norm(diff, axis=1)  # (21,)

    # Normalize by palm scale (wrist → middle MCP)
    scale = np.linalg.norm(landmarks[9] - landmarks[0])
    if scale < 1e-6:
        scale = 1.0

    return float(np.mean(per_point) / scale)
```

**Movement is calculated using RAW landmarks** (MediaPipe coordinates 0-1), then **normalized by palm scale** (wrist to middle MCP distance).

---

## 2. Current Threshold Value  
**File:** config.py

```python
MOVEMENT_THRESHOLD = 0.015          # Normalized landmark displacement threshold
MOVEMENT_FRAMES_REQUIRED = 5        # Consecutive frames exceeding threshold to trigger dynamic
```

---

## 3. Routing Logic Summary  
**File:** ml/gesture_pipeline.py

1. Each frame: compute displacement from previous frame
2. If `displacement >= 0.015` for **5 consecutive frames** → start buffering
3. While buffering: **static predictions are suppressed** (returns "none")
4. When buffer reaches **30 frames** OR motion stops → call LSTM
5. LSTM prediction must meet `MIN_PREDICTION_CONFIDENCE = 0.75`
6. If LSTM fails/low-confidence → discard, reset, return to static mode

---

## 4. Debug Prints Added  
I added comprehensive debug logging to the pipeline. **Run the app and draw Z** — you'll see output like:

```
[MOVE] disp=0.0234 thresh=0.0150 motion_cnt=3/5 buffering=False buf_len=15/30 dynamic_loaded=True
[MOVE] >>> BUFFERING STARTED! motion_counter=5
[MOVE] Motion stopped! Trying dynamic predict on 25 frames...
[LSTM] Raw prediction: label=Z, conf=0.892
[LSTM] ✓ RETURNING DYNAMIC: Z (89.2%)
```

**Or if it's failing, you'll see WHY:**
- `dynamic_loaded=False` → model not loaded
- `motion_cnt` never reaches 5 → threshold too high
- `buffering` never starts → motion not sustained
- LSTM returns conf < 0.75 → prediction rejected

---

## 5. LSTM Model Status  
**Verified loaded:** ✓
```
Dynamic classes: ['Z']
Pipeline Status: {'static': True, 'dynamic': True}
```

---

## 6. Buffer Logic  
**File:** ml/gesture_pipeline.py

```python
self._landmark_buffer: deque = deque(maxlen=sequence_length)  # maxlen=30
```

Buffer is cleared in `_reset_motion_state()` after successful prediction:
```python
def _reset_motion_state(self):
    self._motion_counter = 0
    self._is_buffering = False
    self._landmark_buffer.clear()  # ← Cleared here
```

---

## 7. Training Script  
**File:** ml/keras_trainer.py

The trainer uses validation split and returns test accuracy:
```python
X_train, X_test, y_train, y_test = train_test_split(
    sequences, y, test_size=0.2, random_state=42, stratify=y,
)
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=50, ...)
loss, acc = model.evaluate(X_test, y_test, verbose=0)
```

---

## 🔍 ROOT CAUSE DIAGNOSIS

Based on my analysis, **the most likely issue is:**

### Threshold is likely TOO HIGH (0.015)

When you draw Z, the palm-normalized displacement may not reach 0.015 for 5 consecutive frames because:
1. MediaPipe coordinates are 0-1 (normalized to image)
2. Palm scale normalization further reduces the value
3. Fast movements may not sustain above threshold for 5 frames

### Recommended Fix:

Lower the threshold and reduce required frames:

```python
# In config.py
MOVEMENT_THRESHOLD = 0.008          # Was 0.015 (too high)
MOVEMENT_FRAMES_REQUIRED = 3        # Was 5 (too many)
```

Want me to apply this fix? Or run the app first with debug prints enabled to see the actual displacement values when you draw Z?
