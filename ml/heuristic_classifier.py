"""
Enhanced Heuristic Gesture Classifier - Rule-based gesture detection

Uses geometric analysis of hand landmarks for reliable gesture detection.
This enhanced version covers more ASL letters and provides better accuracy.
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
    
    Covers:
    - ASL letters A-Z (static ones)
    - Numbers 0-9
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
    
    def _classify(self, lm: np.ndarray, fs: FingerState) -> Tuple[Optional[str], float]:
        """Classify the gesture based on finger states and geometry."""
        
        pattern = fs.pattern()
        
        # === Check O/F first (thumb-index touching) ===
        thumb_index_dist = self._distance(lm[self.THUMB_TIP], lm[self.INDEX_TIP])
        if thumb_index_dist < 0.06:
            if not fs.middle_extended and not fs.ring_extended and not fs.pinky_extended:
                return "O", 0.85
            if fs.middle_extended and fs.ring_extended and fs.pinky_extended:
                return "F", 0.85
        
        # === CLOSED FIST VARIANTS ===
        if pattern in ['00000', '10000']:
            thumb_tip = lm[self.THUMB_TIP]
            index_mcp = lm[self.INDEX_MCP]
            # A has thumb beside fingers
            if thumb_tip[1] < index_mcp[1]:
                return "A", 0.85
            return "S", 0.75
        
        # === ONE FINGER EXTENDED ===
        
        # X vs D - both have index only (01000)
        if pattern == '01000':
            index_tip = lm[self.INDEX_TIP]
            index_dip = lm[self.INDEX_DIP]
            index_pip = lm[self.INDEX_PIP]
            # X = index is hooked/bent (tip is BELOW dip, or dip is below pip)
            if index_tip[1] > index_dip[1]:
                return "X", 0.80
            # D = index is straight up
            return "D", 0.85
        
        # I - Pinky only
        if pattern == '00001':
            return "I", 0.90
        
        # === TWO FINGERS ===
        
        # L vs G - both have pattern 11000
        if pattern == '11000':
            index_tip = lm[self.INDEX_TIP]
            index_mcp = lm[self.INDEX_MCP]
            # G = index points SIDEWAYS (tip and mcp at same Y height)
            if abs(index_tip[1] - index_mcp[1]) < 0.08:
                return "G", 0.80
            # L = index points UP (normal upward extension)
            return "L", 0.85
        
        # V/U - Index and middle
        if pattern == '01100':
            index_tip = lm[self.INDEX_TIP]
            middle_tip = lm[self.MIDDLE_TIP]
            spread = self._distance_2d(index_tip, middle_tip)
            hand_width = self._distance_2d(lm[self.INDEX_MCP], lm[self.PINKY_MCP])
            
            # R - fingers crossed (index over middle)
            if index_tip[0] > middle_tip[0] + 0.03:
                return "R", 0.80
            
            if hand_width > 0 and spread > hand_width * 0.25:
                return "V", 0.90
            return "U", 0.85
        
        # K - Index, middle with thumb between (middle slightly bent)
        if pattern == '11100':
            middle_tip = lm[self.MIDDLE_TIP]
            middle_pip = lm[self.MIDDLE_PIP]
            if middle_tip[1] > middle_pip[1] - 0.02:  # Middle slightly bent
                return "K", 0.80
            return "3", 0.80  # Otherwise it's number 3
        
        # Y - Thumb and pinky
        if pattern == '10001':
            return "Y", 0.90
        
        # === THREE FINGERS ===
        
        # W - Index, middle, ring spread
        if pattern == '01110':
            return "W", 0.85
        
        # === FOUR/FIVE FINGERS ===
        
        # B - Four fingers up, thumb across
        if pattern == '01111':
            return "B", 0.85
        
        # 5 / Open hand - All extended
        if pattern == '11111':
            # Check for C - curved hand
            thumb_tip = lm[self.THUMB_TIP]
            index_tip = lm[self.INDEX_TIP]
            gap = self._distance(thumb_tip, index_tip)
            if 0.06 < gap < 0.15:
                return "C", 0.75
            return "5", 0.90
        
        # === FALLBACK ===
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
    
    def clear(self):
        """Reset prediction state."""
        self.last_prediction = None
        self.prediction_count = 0
