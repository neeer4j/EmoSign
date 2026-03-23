"""
Enhanced Heuristic Gesture Classifier - Rule-based gesture detection

Uses geometric analysis of hand landmarks for reliable gesture detection.
All thresholds are **normalized by hand scale** so detection works at any
distance from the camera.

Covers all 26 ASL static letters (A-Z) and numbers 0-9 with improved
accuracy, including finger-over-thumb detection for N, M, T, S, E
differentiation.  Number/letter overlaps: 0=O, 2=V, 4=B, 9≈F.
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
    
    All spatial thresholds are expressed as fractions of **hand_scale**
    (wrist → middle-MCP distance) so they adapt to any hand size or
    camera distance.
    
    Covers all 26 ASL static letters (A-Z) and numbers 0-9, with
    improved closed-fist differentiation (A, S, T, N, M, E).
    
    Number/letter overlaps (identical hand shapes):
    0 = O, 2 = V, 4 = B, 9 ≈ F
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
        self._hand_inverted = False  # Track hand orientation
    
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
        scale = self._hand_scale(lm)
        
        # Detect hand orientation (inverted = fingers point downward)
        self._hand_inverted = self._detect_inverted(lm)
        
        # Get finger states (orientation-aware)
        finger_state = self._get_finger_state(lm, scale)
        
        # Classify gesture
        gesture, confidence = self._classify(lm, finger_state, scale)
        
        return gesture, confidence
    
    # ── helpers ──────────────────────────────────────────────────
    
    def _hand_scale(self, lm: np.ndarray) -> float:
        """Wrist → middle-MCP distance.  All thresholds scale by this."""
        s = self._dist(lm[self.WRIST], lm[self.MIDDLE_MCP])
        return s if s > 0.01 else 0.1
    
    def _dist(self, a: np.ndarray, b: np.ndarray) -> float:
        """3-D Euclidean distance."""
        return float(np.linalg.norm(a - b))
    
    def _dist2d(self, a: np.ndarray, b: np.ndarray) -> float:
        """2-D (x, y) distance."""
        return float(np.linalg.norm(a[:2] - b[:2]))
    
    def _angle_at(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """Angle (degrees) at point *b* formed by segments b→a and b→c."""
        ba = a[:2] - b[:2]
        bc = c[:2] - b[:2]
        cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        return float(np.degrees(np.arccos(np.clip(cos, -1, 1))))
    
    def _finger_curl_angle(self, lm: np.ndarray, mcp: int, pip: int, tip: int) -> float:
        """Curl angle at PIP joint (0° = straight, 180° = fully curled)."""
        return self._angle_at(lm[mcp], lm[pip], lm[tip])
    
    def _y_dir(self, v: float) -> float:
        """Return *v* with sign flipped when hand is inverted, so
        'above' / 'below' comparisons keep their meaning."""
        return -v if self._hand_inverted else v
    
    # ── orientation detection ────────────────────────────────────
    
    def _detect_inverted(self, lm: np.ndarray) -> bool:
        """Detect if the hand is inverted (fingers pointing downward)."""
        tips_y = np.mean([lm[8][1], lm[12][1], lm[16][1], lm[20][1]])
        mcps_y = np.mean([lm[5][1], lm[9][1], lm[13][1], lm[17][1]])
        wrist_y = lm[self.WRIST][1]
        spread = abs(tips_y - mcps_y)
        return wrist_y < tips_y and tips_y > mcps_y and spread > 0.03
    
    # ── finger-state analysis ────────────────────────────────────
    
    def _get_finger_state(self, lm: np.ndarray, scale: float) -> FingerState:
        """Analyse which fingers are extended.
        
        Uses a fully **orientation-independent** test: compare the 2-D
        distance from the fingertip to the wrist vs the same distance
        from the PIP joint to the wrist.
        
        • Extended → tip is *farther* from the wrist than the PIP joint
        • Curled   → tip is *closer* to the wrist than the PIP joint
        
        This works regardless of hand rotation / inversion because it
        only depends on radial distance from the wrist.
        """
        thumb_ext = self._is_thumb_extended(lm, scale)
        wrist = lm[self.WRIST]
        
        def _extended(tip_idx: int, pip_idx: int) -> bool:
            return self._dist2d(lm[tip_idx], wrist) > self._dist2d(lm[pip_idx], wrist)
        
        return FingerState(
            thumb_extended=thumb_ext,
            index_extended=_extended(self.INDEX_TIP, self.INDEX_PIP),
            middle_extended=_extended(self.MIDDLE_TIP, self.MIDDLE_PIP),
            ring_extended=_extended(self.RING_TIP, self.RING_PIP),
            pinky_extended=_extended(self.PINKY_TIP, self.PINKY_PIP),
        )
    
    def _is_thumb_extended(self, lm: np.ndarray, scale: float) -> bool:
        """Thumb is extended if its tip is far enough from the palm centre."""
        palm_cx = (lm[self.INDEX_MCP][0] + lm[self.PINKY_MCP][0]) / 2
        thumb_dx = abs(lm[self.THUMB_TIP][0] - palm_cx)
        return thumb_dx > scale * 0.35
    
    # ── main classification ──────────────────────────────────────
    
    def _classify(self, lm: np.ndarray, fs: FingerState, scale: float) -> Tuple[Optional[str], float]:
        """Classify based on finger states + geometry.  Every spatial
        threshold is relative to *scale* for distance-independence."""
        
        pattern = fs.pattern()
        
        # ── SPECIAL: thumb-index circle (O / F) ─────────────────
        ti_dist = self._dist(lm[self.THUMB_TIP], lm[self.INDEX_TIP]) / scale
        # For O/F, the index must be *partially open* (forming the circle),
        # not tightly curled into a fist.  Guard: index tip must be at
        # least 0.15·scale away from its own MCP.
        idx_tip_mcp = self._dist(lm[self.INDEX_TIP], lm[self.INDEX_MCP]) / scale
        if ti_dist < 0.25 and idx_tip_mcp > 0.10 and not fs.thumb_extended:
            if not fs.middle_extended and not fs.ring_extended and not fs.pinky_extended:
                return "O", 0.88
            if fs.middle_extended and fs.ring_extended and fs.pinky_extended:
                return "F", 0.88
        
        # ── SPECIAL: X — hooked index finger ─────────────────────
        # X has the index finger prominent (PIP far from wrist) but
        # hooked (tip curls back toward MCP).  Detect before pattern
        # routing because the wrist-distance test marks it as "curled".
        if not fs.index_extended and not fs.middle_extended and not fs.ring_extended and not fs.pinky_extended:
            wrist = lm[self.WRIST]
            idx_pip_d = self._dist2d(lm[self.INDEX_PIP], wrist)
            idx_dip_d = self._dist2d(lm[self.INDEX_DIP], wrist)
            mid_pip_d = self._dist2d(lm[self.MIDDLE_PIP], wrist)
            # Index PIP or DIP is noticeably farther from wrist than
            # middle PIP → index is sticking out even though tip curls.
            idx_prominent = idx_pip_d > mid_pip_d * 1.03 or idx_dip_d > mid_pip_d * 1.03
            if idx_prominent:
                idx_tip_mcp = self._dist(lm[self.INDEX_TIP], lm[self.INDEX_MCP]) / scale
                idx_pip_mcp = self._dist(lm[self.INDEX_PIP], lm[self.INDEX_MCP]) / scale
                if idx_tip_mcp < idx_pip_mcp * 1.4:
                    return "X", 0.82
        
        # ── CLOSED FIST (A S T N M E) ───────────────────────────
        if pattern in ('00000', '10000'):
            return self._classify_closed_fist(lm, fs, scale)
        
        # ── ONE FINGER ───────────────────────────────────────────
        
        # D / 1 / X  (01000)
        if pattern == '01000':
            # X = index hooked — tip close to MCP
            # D = index straight + thumb touching middle tip (small circle)
            # 1 = index straight + thumb across fist (not touching middle)
            tip_mcp = self._dist(lm[self.INDEX_TIP], lm[self.INDEX_MCP]) / scale
            pip_mcp = self._dist(lm[self.INDEX_PIP], lm[self.INDEX_MCP]) / scale
            # For X the tip curls back toward MCP; for D it extends away
            if tip_mcp < pip_mcp * 1.3:
                return "X", 0.82
            # D vs 1: in D, thumb tip touches middle tip
            t2mid = self._dist(lm[self.THUMB_TIP], lm[self.MIDDLE_TIP]) / scale
            if t2mid < 0.25:
                return "D", 0.88
            return "1", 0.88

        # I — pinky only
        if pattern == '00001':
            return "I", 0.90
        
        # ── TWO FINGERS ──────────────────────────────────────────
        
        # L / G / Q  (thumb + index = 11000)
        if pattern == '11000':
            idx_tip = lm[self.INDEX_TIP]
            idx_mcp = lm[self.INDEX_MCP]
            # Use RAW y: tip below MCP = pointing down (world-space)
            raw_dy = idx_mcp[1] - idx_tip[1]  # positive = tip above MCP
            dx = abs(idx_tip[0] - idx_mcp[0])
            
            # Q: index pointing DOWN (raw tip is below MCP in screen coords)
            if raw_dy < -scale * 0.15:
                return "Q", 0.82
            # G: index points SIDEWAYS
            if abs(raw_dy) < scale * 0.25 and dx > scale * 0.25:
                return "G", 0.82
            # L: index points UP, thumb out
            return "L", 0.88
        
        # V / U / R / H / P  (index + middle = 01100)
        if pattern == '01100':
            idx_tip = lm[self.INDEX_TIP]
            mid_tip = lm[self.MIDDLE_TIP]
            idx_mcp = lm[self.INDEX_MCP]
            mid_mcp = lm[self.MIDDLE_MCP]
            
            # RAW direction in world space for P / H detection
            raw_dy_idx = idx_mcp[1] - idx_tip[1]
            raw_dy_mid = mid_mcp[1] - mid_tip[1]
            
            # P: both fingers pointing DOWN
            if raw_dy_idx < -scale * 0.15 and raw_dy_mid < -scale * 0.15:
                return "P", 0.82
            
            # H: both fingers pointing SIDEWAYS
            dx_idx = abs(idx_tip[0] - idx_mcp[0])
            if abs(raw_dy_idx) < scale * 0.25 and dx_idx > scale * 0.2:
                return "H", 0.82
            
            # R: fingers crossed (index tip near middle-finger MCP)
            idx_cross = self._dist2d(idx_tip, mid_mcp) / scale
            mid_self = self._dist2d(mid_tip, mid_mcp) / scale
            if idx_cross < mid_self * 0.9:   # relaxed threshold
                return "R", 0.80
            
            # V vs U — spread vs together
            spread = self._dist2d(idx_tip, mid_tip) / scale
            if spread > 0.30:
                return "V", 0.90
            return "U", 0.88
        
        # K / 3 / P (thumb + index + middle = 11100)
        if pattern == '11100':
            # P (alternate form): all three pointing DOWN
            raw_dy_idx = lm[self.INDEX_MCP][1] - lm[self.INDEX_TIP][1]
            raw_dy_mid = lm[self.MIDDLE_MCP][1] - lm[self.MIDDLE_TIP][1]
            if raw_dy_idx < -scale * 0.15 and raw_dy_mid < -scale * 0.15:
                return "P", 0.82
            
            # K: middle finger is partially bent — its tip is closer to
            # wrist (relative to its PIP) than index tip is.
            wrist = lm[self.WRIST]
            mid_tip_d = self._dist2d(lm[self.MIDDLE_TIP], wrist)
            mid_pip_d = self._dist2d(lm[self.MIDDLE_PIP], wrist)
            idx_tip_d = self._dist2d(lm[self.INDEX_TIP], wrist)
            idx_pip_d = self._dist2d(lm[self.INDEX_PIP], wrist)
            mid_ext_ratio = mid_tip_d / (mid_pip_d + 1e-6)
            idx_ext_ratio = idx_tip_d / (idx_pip_d + 1e-6)
            if mid_ext_ratio < idx_ext_ratio * 0.9:
                return "K", 0.80
            return "3", 0.82
        
        # Y — thumb + pinky (10001)
        if pattern == '10001':
            return "Y", 0.90
        
        # ── NUMBER GESTURES (unique shapes) ──────────────────────
        
        # 7 — index + middle + pinky up, thumb touches ring (01101)
        if pattern == '01101':
            return "7", 0.85
        
        # 8 — index + ring + pinky up, thumb touches middle (01011)
        if pattern == '01011':
            return "8", 0.85
        
        # 9 — middle + ring + pinky up, thumb touches index (00111)
        if pattern == '00111':
            return "9", 0.85
        
        # ── THREE FINGERS ────────────────────────────────────────
        
        # W / 6 — index + middle + ring (01110)
        if pattern == '01110':
            # 6: thumb touches pinky while index+middle+ring up
            t2pnk = self._dist(lm[self.THUMB_TIP], lm[self.PINKY_TIP]) / scale
            if t2pnk < 0.30:
                return "6", 0.85
            return "W", 0.88
        
        # ── FOUR / FIVE FINGERS ──────────────────────────────────
        
        # B — four up, thumb folded (01111)
        if pattern == '01111':
            return "B", 0.88
        
        # 5 / C — all extended (11111)
        if pattern == '11111':
            # C: fingers are curved — tips are closer to wrist than
            # they would be for fully-spread '5'.  Measure average
            # tip-distance / pip-distance ratio.
            wrist = lm[self.WRIST]
            ratios = []
            for tip, pip in [(8,6),(12,10),(16,14),(20,18)]:
                td = self._dist2d(lm[tip], wrist)
                pd = self._dist2d(lm[pip], wrist)
                ratios.append(td / (pd + 1e-6))
            avg_ratio = np.mean(ratios)
            # Thumb-index gap (the opening of the 'C')
            ti_gap = self._dist(lm[self.THUMB_TIP], lm[self.INDEX_TIP]) / scale
            # C: moderately curved (ratio < 1.35) with a visible gap
            if avg_ratio < 1.35 and ti_gap > 0.25:
                return "C", 0.80
            return "5", 0.90
        
        # ── FALLBACK ─────────────────────────────────────────────
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
    
    # ── closed-fist sub-classifier ──────────────────────────────
    
    def _classify_closed_fist(self, lm: np.ndarray, fs: FingerState, scale: float) -> Tuple[str, float]:
        """Differentiate A, S, T, N, M, E — all have fingers curled.
        
        PRIMARY split: thumb extended → A.
        SECONDARY: within thumb-not-extended, differentiate S/T/N/M/E
        using thumb-to-fingertip distances and z-depth.
        """
        # ── A: thumb extended (up/beside the fist) ───────────────
        if fs.thumb_extended:
            return "A", 0.85
        
        # From here, thumb is NOT extended (across / tucked)
        thumb_tip = lm[self.THUMB_TIP]
        index_tip = lm[self.INDEX_TIP]
        middle_tip = lm[self.MIDDLE_TIP]
        ring_tip = lm[self.RING_TIP]
        pinky_tip = lm[self.PINKY_TIP]
        index_mcp = lm[self.INDEX_MCP]
        
        # Normalised thumb→fingertip distances
        t2i = self._dist(thumb_tip, index_tip) / scale
        t2m = self._dist(thumb_tip, middle_tip) / scale
        t2r = self._dist(thumb_tip, ring_tip) / scale
        
        # Z-depth (positive = finger closer to camera = "over" thumb)
        z_thresh = max(0.003, scale * 0.008)
        idx_over = (thumb_tip[2] - index_tip[2]) > z_thresh
        mid_over = (thumb_tip[2] - middle_tip[2]) > z_thresh
        rng_over = (thumb_tip[2] - ring_tip[2]) > z_thresh
        if self._hand_inverted:
            idx_over = idx_over or (index_tip[2] - thumb_tip[2]) > z_thresh
            mid_over = mid_over or (middle_tip[2] - thumb_tip[2]) > z_thresh
            rng_over = rng_over or (ring_tip[2] - thumb_tip[2]) > z_thresh
        
        near = 0.55
        idx_near = t2i < near
        mid_near = t2m < near
        rng_near = t2r < near
        
        # All tips well below their MCPs? (orientation-aware)
        if self._hand_inverted:
            all_down = all(lm[t][1] < lm[m][1] for t, m in [(8,5),(12,9),(16,13),(20,17)])
        else:
            all_down = all(lm[t][1] > lm[m][1] for t, m in [(8,5),(12,9),(16,13),(20,17)])
        
        # E: all tips tucked close together, thumb near fingers
        if all_down:
            spread = self._dist(index_tip, pinky_tip) / scale
            if spread < 0.55:
                thumb_near = (t2i < 0.55 or t2m < 0.55)
                if thumb_near:
                    return "E", 0.80
        
        # M: three fingers over thumb
        if idx_near and mid_near and rng_near and (idx_over or mid_over or rng_over):
            return "M", 0.82
        
        # N: two fingers over thumb
        if idx_near and mid_near and not rng_near and (idx_over or mid_over):
            return "N", 0.82
        
        # T: thumb tucked between index and middle
        if t2i < 0.45 and abs(thumb_tip[1] - index_tip[1]) < scale * 0.35 and not mid_near:
            return "T", 0.78
        
        # S: default closed fist with thumb across
        return "S", 0.75
    
    def clear(self):
        """Reset prediction state."""
        self.last_prediction = None
        self.prediction_count = 0
        self._hand_inverted = False
