"""
Feature Extraction Module - Convert landmarks to ML features

Enhanced feature set for improved accuracy:
- Normalized coordinates (63 features)
- Finger tip to MCP distances (5 features)  
- Thumb to fingertip distances (4 features)
- Fingertip Z-depth relative to thumb (4 features)
- Fingertip to palm center distances (5 features)
"""
import numpy as np


class FeatureExtractor:
    """Extract normalized features from hand landmarks for ML classification."""
    
    # Landmark indices
    FINGER_TIPS = [4, 8, 12, 16, 20]      # Thumb, Index, Middle, Ring, Pinky tips
    FINGER_MCPS = [2, 5, 9, 13, 17]       # MCP joints (knuckles)
    FINGER_PIPS = [3, 6, 10, 14, 18]      # PIP joints (middle of finger)
    FINGER_DIPS = [3, 7, 11, 15, 19]      # DIP joints
    PALM_CENTER = 9                        # Middle finger MCP as palm reference
    WRIST = 0
    THUMB_TIP = 4
    
    @staticmethod
    def extract(landmarks) -> np.ndarray:
        """Extract feature vector from landmarks.
        
        Features include:
        - Normalized x, y, z coordinates (relative to wrist) - 63 features
        - Finger tip to MCP distances - 5 features
        - Thumb tip to each fingertip distance - 4 features
        - Z-depth difference (thumb Z - fingertip Z) - 4 features
        - Fingertip to palm center distances - 5 features
        
        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe
            
        Returns:
            numpy array of features (81 features)
        """
        if landmarks is None or len(landmarks) != 21:
            return None
        
        landmarks = np.array(landmarks)
        
        # Normalize relative to wrist (landmark 0)
        wrist = landmarks[0]
        normalized = landmarks - wrist
        
        # Scale normalization - use distance from wrist to middle finger MCP
        scale = np.linalg.norm(landmarks[9] - landmarks[0])
        if scale > 0:
            normalized = normalized / scale
        
        # 1. Flatten to 1D feature vector (63 features: 21 * 3)
        features = normalized.flatten()
        
        # 2. Finger tip to MCP distances (5 features)
        finger_tips = [4, 8, 12, 16, 20]
        finger_mcps = [2, 5, 9, 13, 17]
        
        tip_mcp_distances = []
        for tip, mcp in zip(finger_tips, finger_mcps):
            dist = np.linalg.norm(landmarks[tip] - landmarks[mcp])
            tip_mcp_distances.append(dist / scale if scale > 0 else 0)
        
        # 3. Thumb tip to each non-thumb fingertip distance (4 features)
        # Critical for distinguishing N, M, T from A, S
        thumb_tip = landmarks[4]
        thumb_to_finger_dists = []
        for tip_idx in [8, 12, 16, 20]:  # Index, Middle, Ring, Pinky tips
            dist = np.linalg.norm(thumb_tip - landmarks[tip_idx])
            thumb_to_finger_dists.append(dist / scale if scale > 0 else 0)
        
        # 4. Z-depth differences: thumb Z minus fingertip Z (4 features)
        # Positive value = finger is in front of (over) thumb
        # This is the key feature for detecting fingers draped over thumb
        z_depth_diffs = []
        for tip_idx in [8, 12, 16, 20]:
            z_diff = landmarks[4][2] - landmarks[tip_idx][2]
            z_depth_diffs.append(z_diff / scale if scale > 0 else 0)
        
        # 5. Fingertip to palm center distances (5 features)
        # Indicates how curled each finger is toward the palm
        palm_center = landmarks[9]  # Middle MCP
        palm_distances = []
        for tip_idx in finger_tips:
            dist = np.linalg.norm(landmarks[tip_idx] - palm_center)
            palm_distances.append(dist / scale if scale > 0 else 0)
        
        # Combine all features: 63 + 5 + 4 + 4 + 5 = 81
        features = np.concatenate([
            features,
            np.array(tip_mcp_distances),
            np.array(thumb_to_finger_dists),
            np.array(z_depth_diffs),
            np.array(palm_distances),
        ])
        
        return features.astype(np.float32)
    
    @staticmethod
    def get_feature_count() -> int:
        """Return the total number of features."""
        return 81  # 63 coords + 5 tip-MCP + 4 thumb-finger + 4 z-depth + 5 palm
