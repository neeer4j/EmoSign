"""
Enhanced ASL Training Data Generator

Creates training data for ASL letters A-Z with distinctive hand configurations
that more closely match actual ASL fingerspelling patterns.

Includes proper finger-over-thumb positioning for N, M, T, S, E
using Z-depth encoding.
"""
import os
import sys
import csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def generate_hand_template():
    """Generate base hand landmark positions (21 landmarks)."""
    # MediaPipe hand landmarks layout:
    # 0: Wrist
    # 1-4: Thumb (CMC, MCP, IP, TIP)
    # 5-8: Index (MCP, PIP, DIP, TIP)
    # 9-12: Middle (MCP, PIP, DIP, TIP)
    # 13-16: Ring (MCP, PIP, DIP, TIP)
    # 17-20: Pinky (MCP, PIP, DIP, TIP)
    
    landmarks = np.zeros((21, 3), dtype=np.float32)
    
    # Wrist
    landmarks[0] = [0.5, 0.8, 0]
    
    # Palm base positions (MCPs)
    landmarks[1] = [0.35, 0.7, 0]   # Thumb CMC
    landmarks[5] = [0.35, 0.55, 0]  # Index MCP
    landmarks[9] = [0.45, 0.5, 0]   # Middle MCP
    landmarks[13] = [0.55, 0.55, 0] # Ring MCP
    landmarks[17] = [0.65, 0.62, 0] # Pinky MCP
    
    return landmarks


def set_finger_state(landmarks, finger_idx, state, variation=0.03):
    """
    Set finger state: 'extended', 'bent', 'curved', 'folded', 'tucked'
    
    finger_idx: 0=thumb, 1=index, 2=middle, 3=ring, 4=pinky
    
    States:
    - extended: finger straight up
    - bent: finger bent at 90 degrees
    - curved: gentle curve
    - folded: fully folded into palm
    - tucked: finger curled with tip positioned over/near the thumb area (for N, M)
    """
    # Finger joint indices
    if finger_idx == 0:  # Thumb
        mcp, pip, dip, tip = 1, 2, 3, 4
        direction = np.array([-0.1, -0.15, 0])
    else:
        mcp = 1 + finger_idx * 4
        pip = mcp + 1
        dip = mcp + 2
        tip = mcp + 3
        direction = np.array([0, -0.15, 0])
    
    # Add variation
    noise = np.random.randn(3) * variation
    
    if state == 'extended':
        landmarks[pip] = landmarks[mcp] + direction + noise
        landmarks[dip] = landmarks[pip] + direction * 0.8 + noise * 0.5
        landmarks[tip] = landmarks[dip] + direction * 0.6 + noise * 0.3
    elif state == 'bent':
        # Finger bent at 90 degrees
        landmarks[pip] = landmarks[mcp] + direction * 0.5 + noise
        bend_dir = np.array([0.1, 0.05, 0.05])
        landmarks[dip] = landmarks[pip] + bend_dir + noise * 0.5
        landmarks[tip] = landmarks[dip] + bend_dir * 0.7 + noise * 0.3
    elif state == 'curved':
        # Gentle curve
        landmarks[pip] = landmarks[mcp] + direction * 0.6 + noise
        landmarks[dip] = landmarks[pip] + direction * 0.4 + np.array([0.03, 0.02, 0]) + noise * 0.5
        landmarks[tip] = landmarks[dip] + direction * 0.2 + np.array([0.05, 0.03, 0]) + noise * 0.3
    elif state == 'folded':
        # Fully folded into palm
        fold_dir = np.array([0.05, 0.1, 0.02])
        landmarks[pip] = landmarks[mcp] + direction * 0.2 + noise
        landmarks[dip] = landmarks[pip] + fold_dir + noise * 0.5
        landmarks[tip] = landmarks[dip] + fold_dir * 0.5 + noise * 0.3
    elif state == 'tucked':
        # Finger curled with tip near/over the thumb tip area
        # The tip has a NEGATIVE Z offset (closer to camera = in front of thumb)
        landmarks[pip] = landmarks[mcp] + direction * 0.3 + noise
        # Tip curves down and forward (toward camera, over thumb)
        tuck_dir = np.array([0.03, 0.08, -0.04])  # negative Z = in front
        landmarks[dip] = landmarks[pip] + tuck_dir + noise * 0.5
        landmarks[tip] = landmarks[dip] + tuck_dir * 0.6 + noise * 0.3
        # Position tip near where thumb would be
        landmarks[tip][2] -= 0.02  # Extra forward (over thumb)
    elif state == 'curled_down':
        # All fingertips curled DOWN tightly toward palm (for E)
        # Key: tips must end up NEAR palm center, FAR from thumb
        landmarks[pip] = landmarks[mcp] + direction * 0.25 + noise
        # Strong downward curl toward palm
        curl_dir = np.array([0.0, 0.14, 0.03])
        landmarks[dip] = landmarks[pip] + curl_dir + noise * 0.5
        # Tip curls back under, ending near the MCP base
        tuck_back = np.array([-0.01, 0.06, 0.04])
        landmarks[tip] = landmarks[dip] + tuck_back + noise * 0.3
    elif state == 'o_curl':
        # Finger curls inward so tip converges near the thumb/index meeting
        # point. Used for O shape where all fingertips form a tight circle.
        landmarks[pip] = landmarks[mcp] + direction * 0.35 + noise
        # DIP curls inward toward palm center
        curl_in = np.array([-0.02, 0.06, -0.01])
        landmarks[dip] = landmarks[pip] + curl_in + noise * 0.5
        # Tip converges further inward — will be repositioned by O adjustment
        landmarks[tip] = landmarks[dip] + curl_in * 0.8 + noise * 0.3
    elif state == 'across':
        # Thumb across front of fingers (for S) - thumb sweeps far right, clearly in front
        landmarks[pip] = landmarks[mcp] + np.array([0.08, -0.04, -0.05]) + noise
        landmarks[dip] = landmarks[pip] + np.array([0.10, 0.0, -0.04]) + noise * 0.5
        landmarks[tip] = landmarks[dip] + np.array([0.08, 0.02, -0.03]) + noise * 0.3
    elif state == 'between':
        # Thumb tucked between index and middle (for T) - thumb pokes UP between fingers
        landmarks[pip] = landmarks[mcp] + np.array([0.06, -0.08, -0.01]) + noise
        landmarks[dip] = landmarks[pip] + np.array([0.04, -0.06, -0.06]) + noise * 0.5
        landmarks[tip] = landmarks[dip] + np.array([0.02, -0.04, -0.06]) + noise * 0.3
    elif state == 'under':
        # Thumb tucked under fingers (for N, M)
        # The thumb tip is behind (positive Z) the fingertips
        landmarks[pip] = landmarks[mcp] + np.array([0.04, -0.04, 0.02]) + noise
        landmarks[dip] = landmarks[pip] + np.array([0.05, 0.0, 0.02]) + noise * 0.5
        landmarks[tip] = landmarks[dip] + np.array([0.03, 0.03, 0.02]) + noise * 0.3
    elif state == 'side':
        # Thumb beside the fist (for A) - pointing upward, beside fingers
        landmarks[pip] = landmarks[mcp] + np.array([-0.08, -0.1, 0]) + noise
        landmarks[dip] = landmarks[pip] + np.array([-0.05, -0.08, 0]) + noise * 0.5
        landmarks[tip] = landmarks[dip] + np.array([-0.03, -0.06, 0]) + noise * 0.3
    
    return landmarks


def _apply_letter_adjustments(landmarks, letter, noise_scale=0.01):
    """Apply letter-specific post-processing adjustments to make ambiguous
    letters distinguishable in feature space.

    Every letter gets adjustments — even ones that are already fairly unique —
    so the model learns the specific distinguishing cues rather than relying
    purely on random noise patterns.
    """
    rng_noise = lambda: np.random.randn(3) * noise_scale

    # ──────── A (fist, thumb on side, pointing up) ────────
    if letter == 'A':
        # Thumb clearly beside the fist, z=0, distinct from S (thumb in front)
        landmarks[4] += np.array([-0.04, -0.04, 0.0]) + rng_noise()
        landmarks[3] += np.array([-0.02, -0.02, 0.0]) + rng_noise()

    # ──────── B (4 fingers up, thumb folded tight across palm) ────────
    elif letter == 'B':
        landmarks[4] += np.array([0.06, 0.03, -0.03]) + rng_noise()  # thumb across palm
        # Pinky clearly extended (vs W which has pinky folded)
        landmarks[20] += np.array([0.0, -0.04, 0.0]) + rng_noise()
        landmarks[19] += np.array([0.0, -0.02, 0.0]) + rng_noise()

    # ──────── C (wide arc, thumb & fingers DON'T touch) ────────
    elif letter == 'C':
        landmarks[4] += np.array([-0.10, 0.03, 0.0]) + rng_noise()   # thumb far left/away
        landmarks[3] += np.array([-0.06, 0.02, 0.0]) + rng_noise()
        landmarks[8] += np.array([0.04, -0.04, 0.0]) + rng_noise()   # index tip away
        landmarks[12] += np.array([0.04, -0.02, 0.0]) + rng_noise()  # middle tip away
        landmarks[16] += np.array([0.04, 0.0, 0.0]) + rng_noise()    # ring tip away
        landmarks[20] += np.array([0.04, 0.02, 0.0]) + rng_noise()   # pinky tip away

    # ──────── D (index up, thumb touches middle) ────────
    elif letter == 'D':
        landmarks[4] = landmarks[12] + np.array([0.01, 0.01, -0.03]) + rng_noise()
        landmarks[8] += np.array([0.0, -0.04, 0.0]) + rng_noise()  # index clearly up

    # ──────── E (all fingers curled tightly into palm, thumb across front) ────────
    elif letter == 'E':
        # KEY vs O: fingertips curl DOWN into palm, NOT toward thumb tip.
        # Thumb is folded across the FRONT of the curled fingers.
        wrist = landmarks[0]
        palm_center = (landmarks[0] + landmarks[9]) / 2
        # Push all fingertips DOWN toward palm center (away from thumb)
        for tip_idx in [8, 12, 16, 20]:
            # Blend tip toward palm center
            landmarks[tip_idx] = 0.4 * landmarks[tip_idx] + 0.6 * palm_center + rng_noise() * 0.5
            # Push tips further down (high Y) and back (positive Z = away from camera)
            landmarks[tip_idx] += np.array([0.0, 0.04, 0.04]) + rng_noise() * 0.3
        # Thumb clearly in front: low Z (toward camera) and staying above the curled tips
        landmarks[4] += np.array([0.03, -0.02, -0.06]) + rng_noise()
        landmarks[3] += np.array([0.02, -0.01, -0.04]) + rng_noise()

    # ──────── F (thumb+index circle, other 3 extended) ────────
    elif letter == 'F':
        landmarks[4] = landmarks[8] + np.array([0.02, 0.02, -0.02]) + rng_noise()
        # 3 extended fingers spread slightly
        landmarks[12] += np.array([0.0, -0.02, 0.0]) + rng_noise()
        landmarks[16] += np.array([0.02, -0.01, 0.0]) + rng_noise()
        landmarks[20] += np.array([0.03, 0.0, 0.0]) + rng_noise()

    # ──────── G (sideways pointing, thumb+index to the left) ────────
    elif letter == 'G':
        for idx in [2, 3, 4]:  # thumb joints
            landmarks[idx] += np.array([-0.12, 0.10, 0.0]) + rng_noise()
        for idx in [6, 7, 8]:  # index joints
            landmarks[idx] += np.array([-0.14, 0.10, 0.0]) + rng_noise()
        # Thumb and index close together horizontally
        landmarks[4][1] = landmarks[8][1] + 0.02

    # ──────── H (index+middle horizontal, pointing to side) ────────
    elif letter == 'H':
        for idx in [6, 7, 8]:
            landmarks[idx] += np.array([-0.18, 0.14, 0.0]) + rng_noise()
        for idx in [10, 11, 12]:
            landmarks[idx] += np.array([-0.18, 0.14, 0.0]) + rng_noise()

    # ──────── I (pinky straight up, others folded) ────────
    elif letter == 'I':
        # Make pinky clearly straight and high
        landmarks[20] += np.array([0.0, -0.06, 0.0]) + rng_noise()
        landmarks[19] += np.array([0.0, -0.04, 0.0]) + rng_noise()
        landmarks[18] += np.array([0.0, -0.02, 0.0]) + rng_noise()
        # Thumb folded tight, z=0
        landmarks[4] += np.array([0.02, 0.02, 0.0]) + rng_noise()

    # ──────── J (like I but pinky is curving/angled — dynamic letter) ────────
    elif letter == 'J':
        # Pinky has a strong lateral curve + downward drop (tracing J motion)
        # Key distinction from I: pinky goes right and curves down, not straight up
        landmarks[20] += np.array([0.10, 0.06, 0.0]) + rng_noise()   # pinky tip far right & down
        landmarks[19] += np.array([0.06, 0.03, 0.0]) + rng_noise()
        landmarks[18] += np.array([0.02, 0.0, 0.0]) + rng_noise()
        # Thumb slightly different from I
        landmarks[4] += np.array([0.0, 0.05, 0.0]) + rng_noise()

    # ──────── K (thumb between extended index & middle) ────────
    elif letter == 'K':
        thumb_pos = (landmarks[8] + landmarks[12]) / 2
        landmarks[4] = thumb_pos + np.array([0.0, 0.03, -0.04]) + rng_noise()
        landmarks[3] = thumb_pos + np.array([0.0, 0.06, -0.02]) + rng_noise()
        landmarks[12] += np.array([0.04, 0.02, 0.0]) + rng_noise()  # middle angled

    # ──────── L (thumb perpendicular to index, clear L shape) ────────
    elif letter == 'L':
        landmarks[4] += np.array([-0.08, 0.0, 0.0]) + rng_noise()
        landmarks[3] += np.array([-0.05, 0.0, 0.0]) + rng_noise()
        landmarks[2] += np.array([-0.03, 0.0, 0.0]) + rng_noise()
        # Index clearly straight up
        landmarks[8] += np.array([0.0, -0.03, 0.0]) + rng_noise()

    # ──────── M (3 fingers tucked over thumb) — no extra adjustment needed ────────
    elif letter == 'M':
        pass  # finger states already unique enough

    # ──────── N (2 fingers tucked over thumb) — no extra adjustment needed ────────
    elif letter == 'N':
        pass

    # ──────── O (ALL fingertips converge to thumb = tight circle) ────────
    elif letter == 'O':
        # The key signature of O: ALL fingertips are very close to the thumb
        # tip, forming a tight circular opening. This is the #1 distinguishing
        # feature vs C (open arc) and vs W/Y (extended fingers).
        thumb_tip = landmarks[4].copy()
        # Move each fingertip to converge near thumb tip with small offsets
        for i, tip_idx in enumerate([8, 12, 16, 20]):
            # Each finger approaches from slightly different angle
            offset = np.array([
                0.02 + i * 0.015,    # slight rightward spread
                0.01 + i * 0.01,     # slight downward
                -0.01 + i * 0.005,   # slight z variation
            ])
            landmarks[tip_idx] = thumb_tip + offset + rng_noise()
            # Also curl the DIP joints inward
            dip_idx = tip_idx - 1
            landmarks[dip_idx] = (landmarks[tip_idx] + landmarks[tip_idx - 2]) / 2 + rng_noise()

    # ──────── P (like K but hand pointing down) ────────
    elif letter == 'P':
        # Index and middle both point strongly downward
        # Key distinction from L: both fingers go down, thumb too
        for idx in [6, 7, 8]:
            landmarks[idx] += np.array([-0.04, 0.16, 0.0]) + rng_noise()
        for idx in [10, 11, 12]:
            landmarks[idx] += np.array([-0.02, 0.12, 0.0]) + rng_noise()
        landmarks[4] += np.array([-0.02, 0.06, -0.04]) + rng_noise()
        landmarks[3] += np.array([-0.01, 0.04, -0.02]) + rng_noise()

    # ──────── Q (thumb+index pointing DOWN, distinct from G/L/A) ────────
    elif letter == 'Q':
        # Both thumb and index point strongly downward — much more than G
        for idx in [2, 3, 4]:
            landmarks[idx] += np.array([0.04, 0.20, 0.0]) + rng_noise()
        for idx in [6, 7, 8]:
            landmarks[idx] += np.array([0.04, 0.20, 0.0]) + rng_noise()
        # Thumb and index tips close together, pointing down
        landmarks[8] += np.array([0.02, 0.04, 0.0]) + rng_noise()
        landmarks[4] += np.array([-0.02, 0.04, 0.0]) + rng_noise()

    # ──────── R (index crossed over middle, z-depth) ────────
    elif letter == 'R':
        landmarks[8][2] -= 0.08    # index clearly in front
        landmarks[7][2] -= 0.05
        landmarks[12][2] += 0.04   # middle behind
        landmarks[11][2] += 0.02
        landmarks[8][0] += 0.06    # index crosses toward middle
        landmarks[12][0] -= 0.03

    # ──────── S (fist, thumb across FRONT of fingers) ────────
    elif letter == 'S':
        # Amplify thumb forward + rightward sweep
        landmarks[4] += np.array([0.04, 0.0, -0.06]) + rng_noise()  # further forward
        landmarks[3] += np.array([0.02, 0.0, -0.03]) + rng_noise()

    # ──────── T (thumb pokes UP between index & middle) ────────
    elif letter == 'T':
        # Thumb tip positioned between index & middle, pointing upward
        # Key distinction from S: thumb z much more negative, and positioned higher
        # Key distinction from A: thumb x centered between fingers, not to the side
        mid_pos = (landmarks[5] + landmarks[9]) / 2  # between index MCP & middle MCP
        landmarks[4] = mid_pos + np.array([0.0, -0.08, -0.10]) + rng_noise()
        landmarks[3] = mid_pos + np.array([0.0, -0.03, -0.06]) + rng_noise()
        landmarks[2] = mid_pos + np.array([-0.02, 0.02, -0.03]) + rng_noise()
        # Keep index folded extra tight (not extended like A which has thumb on side)
        landmarks[8] += np.array([0.02, 0.03, 0.0]) + rng_noise()

    # ──────── U (index+middle together, straight up, no spread) ────────
    elif letter == 'U':
        # Fingers touching, very close together
        landmarks[8] += np.array([0.015, -0.03, 0.0]) + rng_noise()
        landmarks[12] += np.array([-0.015, -0.03, 0.0]) + rng_noise()
        landmarks[7] += np.array([0.01, -0.01, 0.0]) + rng_noise()
        landmarks[11] += np.array([-0.01, -0.01, 0.0]) + rng_noise()
        # Both at same z-depth (unlike R)
        landmarks[8][2] += 0.0
        landmarks[12][2] += 0.0

    # ──────── V (index+middle spread apart, V shape) ────────
    elif letter == 'V':
        landmarks[8] += np.array([-0.08, -0.02, 0.0]) + rng_noise()
        landmarks[7] += np.array([-0.05, -0.01, 0.0]) + rng_noise()
        landmarks[12] += np.array([0.08, -0.02, 0.0]) + rng_noise()
        landmarks[11] += np.array([0.05, -0.01, 0.0]) + rng_noise()

    # ──────── W (3 fingers spread: index, middle, ring) ────────
    elif letter == 'W':
        landmarks[8] += np.array([-0.06, -0.01, 0.0]) + rng_noise()   # index left
        landmarks[12] += np.array([0.0, -0.02, 0.0]) + rng_noise()    # middle center
        landmarks[16] += np.array([0.06, -0.01, 0.0]) + rng_noise()   # ring right
        # Pinky clearly folded (vs B)
        landmarks[20] += np.array([0.02, 0.04, 0.0]) + rng_noise()

    # ──────── X (index finger hook/bent) ────────
    elif letter == 'X':
        # Index hook is already set by 'bent' state; make it tighter
        landmarks[8] += np.array([0.02, 0.03, 0.0]) + rng_noise()

    # ──────── Y (thumb + pinky extended, others folded) ────────
    elif letter == 'Y':
        # Thumb clearly extended out to the side
        landmarks[4] += np.array([-0.06, -0.04, 0.0]) + rng_noise()
        landmarks[3] += np.array([-0.04, -0.02, 0.0]) + rng_noise()
        # Pinky clearly up
        landmarks[20] += np.array([0.0, -0.06, 0.0]) + rng_noise()
        landmarks[19] += np.array([0.0, -0.03, 0.0]) + rng_noise()

    # ──────── Z (index pointing, dynamic letter) ────────
    elif letter == 'Z':
        # Slightly bent index (mid-trace of Z), distinct from D
        landmarks[8] += np.array([-0.03, 0.02, 0.0]) + rng_noise()
        landmarks[7] += np.array([-0.01, 0.01, 0.0]) + rng_noise()

    return landmarks


def create_asl_letter(letter, variation=0.03):
    """Create hand landmarks for a specific ASL letter."""
    landmarks = generate_hand_template()
    
    # ASL letter configurations
    # Using specialized states for closed-fist variants
    configs = {
        'A': {'thumb': 'side',      'index': 'folded',     'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'B': {'thumb': 'folded',    'index': 'extended',   'middle': 'extended',  'ring': 'extended',  'pinky': 'extended'},
        'C': {'thumb': 'curved',    'index': 'curved',     'middle': 'curved',    'ring': 'curved',    'pinky': 'curved'},
        'D': {'thumb': 'bent',      'index': 'extended',   'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'E': {'thumb': 'folded',    'index': 'curled_down','middle': 'curled_down','ring': 'curled_down','pinky': 'curled_down'},
        'F': {'thumb': 'bent',      'index': 'bent',       'middle': 'extended',  'ring': 'extended',  'pinky': 'extended'},
        'G': {'thumb': 'extended',  'index': 'extended',   'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'H': {'thumb': 'folded',    'index': 'extended',   'middle': 'extended',  'ring': 'folded',    'pinky': 'folded'},
        'I': {'thumb': 'folded',    'index': 'folded',     'middle': 'folded',    'ring': 'folded',    'pinky': 'extended'},
        'J': {'thumb': 'folded',    'index': 'folded',     'middle': 'folded',    'ring': 'folded',    'pinky': 'curved'},
        'K': {'thumb': 'extended',  'index': 'extended',   'middle': 'extended',  'ring': 'folded',    'pinky': 'folded'},
        'L': {'thumb': 'extended',  'index': 'extended',   'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'M': {'thumb': 'under',     'index': 'tucked',     'middle': 'tucked',    'ring': 'tucked',    'pinky': 'folded'},
        'N': {'thumb': 'under',     'index': 'tucked',     'middle': 'tucked',    'ring': 'folded',    'pinky': 'folded'},
        'O': {'thumb': 'curved',    'index': 'o_curl',     'middle': 'o_curl',    'ring': 'o_curl',    'pinky': 'o_curl'},
        'P': {'thumb': 'extended',  'index': 'extended',   'middle': 'bent',      'ring': 'folded',    'pinky': 'folded'},
        'Q': {'thumb': 'extended',  'index': 'bent',       'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'R': {'thumb': 'folded',    'index': 'extended',   'middle': 'extended',  'ring': 'folded',    'pinky': 'folded'},
        'S': {'thumb': 'across',    'index': 'folded',     'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'T': {'thumb': 'between',   'index': 'folded',     'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'U': {'thumb': 'folded',    'index': 'extended',   'middle': 'extended',  'ring': 'folded',    'pinky': 'folded'},
        'V': {'thumb': 'folded',    'index': 'extended',   'middle': 'extended',  'ring': 'folded',    'pinky': 'folded'},
        'W': {'thumb': 'folded',    'index': 'extended',   'middle': 'extended',  'ring': 'extended',  'pinky': 'folded'},
        'X': {'thumb': 'folded',    'index': 'bent',       'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
        'Y': {'thumb': 'extended',  'index': 'folded',     'middle': 'folded',    'ring': 'folded',    'pinky': 'extended'},
        'Z': {'thumb': 'folded',    'index': 'extended',   'middle': 'folded',    'ring': 'folded',    'pinky': 'folded'},
    }
    
    config = configs.get(letter, {})
    finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
    
    for i, name in enumerate(finger_names):
        state = config.get(name, 'extended')
        landmarks = set_finger_state(landmarks, i, state, variation)
    
    # Apply letter-specific adjustments for disambiguation
    landmarks = _apply_letter_adjustments(landmarks, letter, noise_scale=variation * 0.3)
    
    return landmarks


def extract_features(landmarks):
    """Extract features matching features.py logic (87 features).
    
    Must stay perfectly in sync with detector/features.py FeatureExtractor.extract().
    """
    # Normalize relative to wrist
    wrist = landmarks[0]
    normalized = landmarks - wrist
    
    # Scale by middle finger base distance
    scale = np.linalg.norm(landmarks[9] - landmarks[0])
    if scale > 0:
        normalized = normalized / scale
    
    # 1. Normalized coordinates (63 features)
    features = normalized.flatten()
    
    # 2. Finger tip to MCP distances (5 features)
    finger_tips = [4, 8, 12, 16, 20]
    finger_mcps = [2, 5, 9, 13, 17]
    
    tip_mcp_distances = []
    for tip, mcp in zip(finger_tips, finger_mcps):
        dist = np.linalg.norm(landmarks[tip] - landmarks[mcp])
        tip_mcp_distances.append(dist / scale if scale > 0 else 0)
    
    # 3. Thumb tip to each non-thumb fingertip distance (4 features)
    thumb_tip = landmarks[4]
    thumb_to_finger_dists = []
    for tip_idx in [8, 12, 16, 20]:
        dist = np.linalg.norm(thumb_tip - landmarks[tip_idx])
        thumb_to_finger_dists.append(dist / scale if scale > 0 else 0)
    
    # 4. Z-depth differences: thumb Z minus fingertip Z (4 features)
    z_depth_diffs = []
    for tip_idx in [8, 12, 16, 20]:
        z_diff = landmarks[4][2] - landmarks[tip_idx][2]
        z_depth_diffs.append(z_diff / scale if scale > 0 else 0)
    
    # 5. Fingertip to palm center distances (5 features)
    palm_center = landmarks[9]
    palm_distances = []
    for tip_idx in finger_tips:
        dist = np.linalg.norm(landmarks[tip_idx] - palm_center)
        palm_distances.append(dist / scale if scale > 0 else 0)
    
    # 6. Hand orientation indicator (1 feature)
    avg_tip_y = np.mean([landmarks[8][1], landmarks[12][1], landmarks[16][1], landmarks[20][1]])
    avg_mcp_y = np.mean([landmarks[5][1], landmarks[9][1], landmarks[13][1], landmarks[17][1]])
    orientation = (avg_mcp_y - avg_tip_y) / scale if scale > 0 else 0
    
    # 7. Finger curl angles (5 features) — angle at PIP joint for each finger
    finger_pips = [3, 6, 10, 14, 18]
    curl_angles = []
    for tip, pip, mcp in zip(finger_tips, finger_pips, finger_mcps):
        v1 = landmarks[mcp] - landmarks[pip]
        v2 = landmarks[tip] - landmarks[pip]
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        cos_angle = np.clip(cos_angle, -1, 1)
        angle = np.arccos(cos_angle) / np.pi  # Normalize to [0, 1]
        curl_angles.append(angle)
    
    # Total: 63 + 5 + 4 + 4 + 5 + 1 + 5 = 87
    features = np.concatenate([
        features,
        np.array(tip_mcp_distances),
        np.array(thumb_to_finger_dists),
        np.array(z_depth_diffs),
        np.array(palm_distances),
        np.array([orientation]),
        np.array(curl_angles),
    ])
    return features.astype(np.float32)


def generate_enhanced_dataset(samples_per_letter=200):
    """Generate enhanced ASL dataset with distinctive patterns."""
    print(f"Generating enhanced ASL dataset ({samples_per_letter} samples per letter)...")
    
    samples = []
    labels = []
    
    np.random.seed(42)
    
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for i in range(samples_per_letter):
            # Use a WIDE range of noise levels to build robustness
            # Mix of low noise (clean) and high noise (stress) samples
            if i < samples_per_letter * 0.4:
                variation = 0.015 + np.random.rand() * 0.02     # low noise
            elif i < samples_per_letter * 0.75:
                variation = 0.03 + np.random.rand() * 0.03      # medium noise
            else:
                variation = 0.05 + np.random.rand() * 0.035     # high noise
            
            landmarks = create_asl_letter(letter, variation)
            features = extract_features(landmarks)
            
            samples.append(features)
            labels.append(letter)
    
    # Save to CSV
    output_path = os.path.join(DATA_DIR, "asl_enhanced_data.csv")
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ['label'] + [f'f{i}' for i in range(len(samples[0]))]
        writer.writerow(header)
        
        # Data
        for features, label in zip(samples, labels):
            row = [label] + features.tolist()
            writer.writerow(row)
    
    print(f"Generated {len(samples)} samples for {len(set(labels))} letters")
    print(f"Saved to: {output_path}")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate enhanced ASL training data")
    parser.add_argument("--samples", type=int, default=200, help="Samples per letter")
    
    args = parser.parse_args()
    
    generate_enhanced_dataset(args.samples)
    
    print("\nTo train the model, run:")
    print("  python train_model.py")
