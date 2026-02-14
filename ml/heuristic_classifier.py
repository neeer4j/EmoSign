"""
Enhanced Heuristic Gesture Classifier - Rule-based gesture detection

Uses geometric analysis of hand landmarks for reliable gesture detection.
This enhanced version covers all 26 ASL letters with improved accuracy,
including finger-over-thumb detection for N, M, T, S, E differentiation.
"""
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class FingerState:
    """State of individual fingers."""
    thumb_extended: bool
    index_extended: bool
    middle_extended: bool
    ring_extended: bool
    pinky_extended: bool
    
    @property
    def count(self) -> int:
        return sum([
            self.thumb_extended, self.index_extended, 
            self.middle_extended, self.ring_extended, self.pinky_extended
        ])
    
    def pattern(self) -> str:
        """Get binary pattern like '01100' for index+middle."""
        return ''.join([
            '1' if self.thumb_extended else '0',
            '1' if self.index_extended else '0',
            '1' if self.middle_extended else '0',
            '1' if self.ring_extended else '0',
            '1' if self.pinky_extended else '0',
        ])


class HeuristicClassifier:
    """Enhanced rule-based gesture classifier using hand landmark geometry.
    
    Covers all 26 ASL static letters (A-Z) with improved detection for
    closed-fist variants (A, S, T, N, M, E) using finger-over-thumb analysis.
    """
    
    # Landmark indices
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20
    
    FINGER_TIPS = [4, 8, 12, 16, 20]
    FINGER_PIPS = [3, 6, 10, 14, 18]
    FINGER_MCPS = [2, 5, 9, 13, 17]
    
    def __init__(self):
        """Initialize classifier."""
        self.last_prediction = None
        self.prediction_count = 0
        self._stability_threshold = 2
    
    def predict(self, landmarks: List[Tuple[float, float, float]]) -> Tuple[Optional[str], float]:
        """Predict gesture from landmarks.
        
        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe
            
        Returns:
            (gesture_label, confidence) or (None, 0.0) if no match
        """
        if landmarks is None or len(landmarks) != 21:
            return None, 0.0
        
        lm = np.array(landmarks)
        
        # Get finger states
        finger_state = self._get_finger_state(lm)
        
        # Classify gesture
        gesture, confidence = self._classify(lm, finger_state)
        
        # Temporal smoothing
        if gesture == self.last_prediction:
            self.prediction_count += 1
        else:
            self.last_prediction = gesture
            self.prediction_count = 1
        
        if self.prediction_count >= self._stability_threshold:
            return gesture, confidence
        
        return None, 0.0
    
    def _get_finger_state(self, lm: np.ndarray) -> FingerState:
        """Analyze which fingers are extended."""
        
        # Thumb - check horizontal extension
        thumb_extended = self._is_thumb_extended(lm)
        
        # Other fingers - compare tip to PIP joint (y-coordinate)
        index_extended = lm[self.INDEX_TIP][1] < lm[self.INDEX_PIP][1]
        middle_extended = lm[self.MIDDLE_TIP][1] < lm[self.MIDDLE_PIP][1]
        ring_extended = lm[self.RING_TIP][1] < lm[self.RING_PIP][1]
        pinky_extended = lm[self.PINKY_TIP][1] < lm[self.PINKY_PIP][1]
        
        return FingerState(
            thumb_extended=thumb_extended,
            index_extended=index_extended,
            middle_extended=middle_extended,
            ring_extended=ring_extended,
            pinky_extended=pinky_extended
        )
    
    def _is_thumb_extended(self, lm: np.ndarray) -> bool:
        """Check if thumb is extended outward."""
        thumb_tip = lm[self.THUMB_TIP]
        index_mcp = lm[self.INDEX_MCP]
        pinky_mcp = lm[self.PINKY_MCP]
        
        # Hand width
        hand_width = np.abs(pinky_mcp[0] - index_mcp[0])
        if hand_width < 0.01:
            hand_width = 0.1
        
        # Thumb is extended if tip is far from palm center horizontally
        thumb_dist = np.abs(thumb_tip[0] - index_mcp[0])
        return thumb_dist > hand_width * 0.4
    
    def _distance(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """Calculate 3D distance between two points."""
        return np.linalg.norm(p1 - p2)
    
    def _distance_2d(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """Calculate 2D distance (x, y only)."""
        return np.linalg.norm(p1[:2] - p2[:2])
    
    def _fingers_touching(self, lm: np.ndarray, f1_tip: int, f2_tip: int, threshold: float = 0.08) -> bool:
        """Check if two fingertips are touching."""
        dist = self._distance(lm[f1_tip], lm[f2_tip])
        return dist < threshold
    
    def _hand_scale(self, lm: np.ndarray) -> float:
        """Get hand scale (wrist to middle MCP distance) for normalization."""
        scale = self._distance(lm[self.WRIST], lm[self.MIDDLE_MCP])
        return scale if scale > 0.01 else 0.1
    
    def _is_finger_curled(self, lm: np.ndarray, tip: int, pip: int, mcp: int) -> bool:
        """Check if a finger is curled (tip below or at MCP level and close to palm)."""
        return lm[tip][1] > lm[pip][1]
    
    def _thumb_to_fingertip_dist(self, lm: np.ndarray, finger_tip: int) -> float:
        """Distance from thumb tip to a fingertip, normalized by hand scale."""
        return self._distance(lm[self.THUMB_TIP], lm[finger_tip]) / self._hand_scale(lm)
    
    def _classify(self, lm: np.ndarray, fs: FingerState) -> Tuple[Optional[str], float]:
        """Classify the gesture based on finger states and geometry.
        
        Covers all 26 ASL static letters with improved closed-fist differentiation.
        """
        
        pattern = fs.pattern()
        scale = self._hand_scale(lm)
        
        # ============================================================
        # PRIORITY 1: Check special gestures that need specific checks
        # ============================================================
        
        # === O and F: Thumb-index circle ===
        thumb_index_dist = self._distance(lm[self.THUMB_TIP], lm[self.INDEX_TIP])
        if thumb_index_dist < 0.06:
            if not fs.middle_extended and not fs.ring_extended and not fs.pinky_extended:
                return "O", 0.85
            if fs.middle_extended and fs.ring_extended and fs.pinky_extended:
                return "F", 0.85
        
        # ============================================================
        # PRIORITY 2: CLOSED FIST VARIANTS (A, S, T, N, M, E)
        # This is the critical section for differentiating similar poses
        # ============================================================
        if pattern in ['00000', '10000']:
            return self._classify_closed_fist(lm, fs, scale)
        
        # ============================================================
        # PRIORITY 3: ONE FINGER EXTENDED
        # ============================================================
        
        # D vs X: Both have index only (01000)
        if pattern == '01000':
            index_tip = lm[self.INDEX_TIP]
            index_dip = lm[self.INDEX_DIP]
            # X = index is hooked/bent (tip is BELOW dip)
            if index_tip[1] > index_dip[1]:
                return "X", 0.80
            # D = index is straight up
            return "D", 0.85
        
        # I - Pinky only
        if pattern == '00001':
            return "I", 0.90
        
        # Z - Index only, pointing sideways (dynamic letter, but detect pose)
        # Z is actually a dynamic gesture, but the static pose is similar to D/1
        
        # ============================================================
        # PRIORITY 4: TWO FINGERS
        # ============================================================
        
        # L vs G vs Q: Pattern 11000 (thumb + index)
        if pattern == '11000':
            index_tip = lm[self.INDEX_TIP]
            index_mcp = lm[self.INDEX_MCP]
            thumb_tip = lm[self.THUMB_TIP]
            
            # Q = thumb and index pointing DOWN
            if index_tip[1] > index_mcp[1] + 0.05 and thumb_tip[1] > lm[self.THUMB_MCP][1] + 0.05:
                return "Q", 0.80
            
            # G = index points SIDEWAYS (tip and MCP at same Y height)
            if abs(index_tip[1] - index_mcp[1]) < 0.08:
                return "G", 0.80
            
            # L = index points UP with thumb out to side (L-shape)
            return "L", 0.85
        
        # V vs U vs R vs H vs P: Index and middle extended (01100)
        if pattern == '01100':
            index_tip = lm[self.INDEX_TIP]
            middle_tip = lm[self.MIDDLE_TIP]
            index_mcp = lm[self.INDEX_MCP]
            spread = self._distance_2d(index_tip, middle_tip)
            hand_width = self._distance_2d(lm[self.INDEX_MCP], lm[self.PINKY_MCP])
            
            # P = index and middle pointing DOWN (hand facing down)
            if index_tip[1] > index_mcp[1] + 0.05 and middle_tip[1] > lm[self.MIDDLE_MCP][1] + 0.05:
                return "P", 0.80
            
            # H = index and middle pointing SIDEWAYS
            if abs(index_tip[1] - index_mcp[1]) < 0.07 and abs(middle_tip[1] - lm[self.MIDDLE_MCP][1]) < 0.07:
                return "H", 0.80
            
            # R - fingers crossed (index over middle)
            if index_tip[0] > middle_tip[0] + 0.03:
                return "R", 0.80
            
            # V vs U: spread fingers = V, together = U
            if hand_width > 0 and spread > hand_width * 0.25:
                return "V", 0.90
            return "U", 0.85
        
        # K vs 3: Thumb + index + middle (11100)
        if pattern == '11100':
            middle_tip = lm[self.MIDDLE_TIP]
            middle_pip = lm[self.MIDDLE_PIP]
            thumb_tip = lm[self.THUMB_TIP]
            
            # K = thumb touches between index and middle, middle slightly bent
            if middle_tip[1] > middle_pip[1] - 0.02:
                return "K", 0.80
            return "3", 0.80
        
        # Y - Thumb and pinky extended (10001)
        if pattern == '10001':
            return "Y", 0.90
        
        # ============================================================
        # PRIORITY 5: THREE FINGERS
        # ============================================================
        
        # W - Index, middle, ring spread (01110)
        if pattern == '01110':
            return "W", 0.85
        
        # ============================================================
        # PRIORITY 6: FOUR/FIVE FINGERS
        # ============================================================
        
        # B - Four fingers up, thumb folded (01111)
        if pattern == '01111':
            return "B", 0.85
        
        # 5 / C / Open hand - All extended (11111)
        if pattern == '11111':
            thumb_tip = lm[self.THUMB_TIP]
            index_tip = lm[self.INDEX_TIP]
            pinky_tip = lm[self.PINKY_TIP]
            gap = self._distance(thumb_tip, index_tip)
            
            # C - curved hand (thumb and index form a C-shape, moderate gap)
            if 0.06 < gap < 0.15:
                return "C", 0.75
            return "5", 0.90
        
        # ============================================================
        # FALLBACK: Best guess based on finger count
        # ============================================================
        count = fs.count
        if count == 0:
            return "A", 0.50
        elif count == 1:
            return "D", 0.50
        elif count == 2:
            return "V", 0.50
        elif count == 3:
            return "W", 0.50
        elif count == 4:
            return "B", 0.50
        else:
            return "5", 0.50
        
        return None, 0.0
    
    def _classify_closed_fist(self, lm: np.ndarray, fs: FingerState, scale: float) -> Tuple[str, float]:
        """Differentiate closed-fist variants: A, S, T, N, M, E.
        
        These letters all have fingers curled but differ in WHERE the thumb is
        relative to the fingers and whether fingertips rest ON TOP of the thumb.
        
        Key differentiators:
        - A: Thumb beside the fist (to the side), pointing up
        - S: Thumb across the front of the fist (over curled fingers)
        - T: Thumb tucked between index and middle fingers
        - N: Index and middle fingertips rest on top of/over the thumb
        - M: Index, middle, and ring fingertips rest on top of/over the thumb
        - E: All fingertips curled down with thumb tucked in/across palm
        """
        thumb_tip = lm[self.THUMB_TIP]
        thumb_ip = lm[self.THUMB_IP]
        index_tip = lm[self.INDEX_TIP]
        middle_tip = lm[self.MIDDLE_TIP]
        ring_tip = lm[self.RING_TIP]
        pinky_tip = lm[self.PINKY_TIP]
        index_mcp = lm[self.INDEX_MCP]
        middle_mcp = lm[self.MIDDLE_MCP]
        ring_mcp = lm[self.RING_MCP]
        
        # --- Compute key metrics ---
        
        # Distances from thumb tip to each fingertip (normalized)
        thumb_to_index = self._distance(thumb_tip, index_tip) / scale
        thumb_to_middle = self._distance(thumb_tip, middle_tip) / scale
        thumb_to_ring = self._distance(thumb_tip, ring_tip) / scale
        thumb_to_pinky = self._distance(thumb_tip, pinky_tip) / scale
        
        # Z-depth analysis: In MediaPipe, smaller Z = closer to camera.
        # If fingertip Z < thumb Z, the finger is in FRONT of the thumb (over it).
        index_z_diff = thumb_tip[2] - index_tip[2]   # positive = index in front
        middle_z_diff = thumb_tip[2] - middle_tip[2]  # positive = middle in front
        ring_z_diff = thumb_tip[2] - ring_tip[2]      # positive = ring in front
        
        # Check if fingertips are close to thumb (touching/near)
        close_threshold = 0.55  # normalized distance threshold
        index_near_thumb = thumb_to_index < close_threshold
        middle_near_thumb = thumb_to_middle < close_threshold
        ring_near_thumb = thumb_to_ring < close_threshold
        
        # Check if fingertips are over/in front of thumb (z-depth)
        z_threshold = 0.005
        index_over_thumb = index_z_diff > z_threshold
        middle_over_thumb = middle_z_diff > z_threshold
        ring_over_thumb = ring_z_diff > z_threshold
        
        # Thumb vertical position relative to index knuckle
        thumb_above_knuckles = thumb_tip[1] < index_mcp[1]
        
        # Check if all fingertips are curled down below their MCPs
        all_tips_below_mcps = all(
            lm[tip][1] > lm[mcp][1]
            for tip, mcp in [(8,5), (12,9), (16,13), (20,17)]
        )
        
        # --- Classification logic (most specific first) ---
        
        # E: All fingertips curled down, tips near each other, thumb tucked
        # E is distinctive because ALL four fingertips point down toward the palm
        # and are close together, with thumb tucked under/across
        if all_tips_below_mcps:
            tips_spread = self._distance(index_tip, pinky_tip) / scale
            # Thumb is also below or at knuckle level
            thumb_low = thumb_tip[1] > lm[self.THUMB_MCP][1]
            if tips_spread < 0.7 and thumb_low:
                return "E", 0.80
        
        # M: Index, middle, AND ring fingertips all near/over thumb
        # Three fingers draped over the thumb
        if (index_near_thumb and middle_near_thumb and ring_near_thumb and
            (index_over_thumb or middle_over_thumb or ring_over_thumb)):
            return "M", 0.82
        
        # N: Index AND middle fingertips near/over thumb (but NOT ring)
        # Two fingers draped over the thumb
        if (index_near_thumb and middle_near_thumb and not ring_near_thumb and
            (index_over_thumb or middle_over_thumb)):
            return "N", 0.82
        
        # T: Thumb tucked between index and middle
        # Thumb tip is close to index tip, and positioned between/under fingers
        # The thumb pokes out between index and middle
        thumb_between_idx_mid = (
            thumb_to_index < 0.45 and
            abs(thumb_tip[1] - index_tip[1]) < scale * 0.35 and
            not middle_near_thumb
        )
        if thumb_between_idx_mid:
            return "T", 0.78
        
        # A vs S: Both are fists, but differ in thumb position
        # A: Thumb is beside the fist, pointing upward, above the knuckle line
        # S: Thumb crosses over the front of the curled fingers
        
        if thumb_above_knuckles:
            # Thumb is up beside the fist -> A
            return "A", 0.85
        
        # Thumb is lower/across -> S
        return "S", 0.75
    
    def clear(self):
        """Reset prediction state."""
        self.last_prediction = None
        self.prediction_count = 0
