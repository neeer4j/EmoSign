"""
Hand Tracker Module - MediaPipe Tasks API Integration

Supports both IMAGE mode (for live camera) and VIDEO mode (for uploaded videos).
VIDEO mode provides temporal consistency between frames for smoother tracking.
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import time

from config import MAX_HANDS, MIN_DETECTION_CONFIDENCE, MIN_TRACKING_CONFIDENCE, MODELS_DIR

# Hand connections for drawing (21 landmarks)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),      # Index
    (0, 9), (9, 10), (10, 11), (11, 12), # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17)            # Palm
]


class HandTracker:
    """MediaPipe HandLandmarker wrapper for hand detection and tracking.
    
    Supports two running modes:
    - IMAGE: For live camera feed (each frame processed independently)
    - VIDEO: For pre-recorded video files (temporal consistency between frames)
    """
    
    def __init__(self, use_video_mode: bool = False, detection_confidence: float = None):
        """Initialize hand tracker.
        
        Args:
            use_video_mode: If True, use VIDEO running mode for better temporal tracking.
                           If False, use IMAGE mode for live camera.
            detection_confidence: Override detection confidence (use lower values for video)
        """
        # Model path
        self.model_path = os.path.join(MODELS_DIR, "hand_landmarker.task")
        self.use_video_mode = use_video_mode
        
        # Check if model exists
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Hand landmarker model not found at {self.model_path}. "
                "Please download from: https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            )
        
        # Use provided confidence or default
        det_confidence = detection_confidence if detection_confidence else MIN_DETECTION_CONFIDENCE
        
        # Select running mode
        running_mode = vision.RunningMode.VIDEO if use_video_mode else vision.RunningMode.IMAGE
        
        # Create hand landmarker options
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=running_mode,
            num_hands=MAX_HANDS,
            min_hand_detection_confidence=det_confidence,
            min_hand_presence_confidence=0.6,   # reject fleeting detections
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE
        )
        
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.results = None
        self._frame_height = 480
        self._frame_width = 640
        
        # Timestamp tracking for VIDEO mode (in milliseconds)
        self._start_time = time.time() * 1000
        self._frame_count = 0

        # EMA landmark smoothing — reduces per-frame jitter
        # alpha=1.0 means no smoothing (raw), lower = smoother but more lag
        # 0.40 gives a good balance: smooth trail without noticeable input lag
        self._smoothing_alpha: float = 0.40
        self._smoothed_landmarks = None   # [(x, y, z), ...] or None
    
    def process(self, frame_rgb, timestamp_ms: int = None):
        """Process RGB frame to detect hands.
        
        Args:
            frame_rgb: RGB image frame (numpy array)
            timestamp_ms: Optional timestamp in milliseconds (required for VIDEO mode)
            
        Returns:
            Detection results
        """
        self._frame_height, self._frame_width = frame_rgb.shape[:2]
        
        # Convert numpy array to MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Detect hands using appropriate method based on running mode
        if self.use_video_mode:
            # VIDEO mode requires timestamps
            if timestamp_ms is None:
                # Auto-generate timestamp based on frame count
                self._frame_count += 1
                timestamp_ms = int(self._frame_count * (1000 / 30))  # Assume 30 FPS
            self.results = self.detector.detect_for_video(mp_image, timestamp_ms)
        else:
            # IMAGE mode - simple detection
            self.results = self.detector.detect(mp_image)

        # Reset smoothed landmarks when hand goes away so next detection starts fresh
        if not (self.results and self.results.hand_landmarks):
            self._smoothed_landmarks = None
        
        return self.results
    
    def get_landmarks(self):
        """Get hand landmarks from last processed frame.
        
        Returns:
            list: List of landmark coordinates [(x, y, z), ...] for first detected hand.
                  Returns None if no hand detected.
        """
        if self.results is None or not self.results.hand_landmarks:
            return None
        
        # Get first hand's landmarks
        hand_landmarks = self.results.hand_landmarks[0]
        
        raw = [(lm.x, lm.y, lm.z) for lm in hand_landmarks]

        # Apply EMA smoothing to reduce jitter
        if self._smoothed_landmarks is None:
            # First frame after detection — initialise with raw values
            self._smoothed_landmarks = raw
        else:
            a = self._smoothing_alpha
            smoothed = []
            for prev, curr in zip(self._smoothed_landmarks, raw):
                sx = a * curr[0] + (1 - a) * prev[0]
                sy = a * curr[1] + (1 - a) * prev[1]
                sz = a * curr[2] + (1 - a) * prev[2]
                smoothed.append((sx, sy, sz))
            self._smoothed_landmarks = smoothed

        return self._smoothed_landmarks
    
    def get_all_hands_landmarks(self):
        """Get landmarks for all detected hands.
        
        Returns:
            list: List of hands, each containing list of landmark coordinates.
                  Each hand: {'landmarks': [(x, y, z), ...], 'handedness': 'Left'/'Right'}
                  Returns empty list if no hands detected.
        """
        if self.results is None or not self.results.hand_landmarks:
            return []
        
        hands = []
        for i, hand_landmarks in enumerate(self.results.hand_landmarks):
            landmarks = []
            for lm in hand_landmarks:
                landmarks.append((lm.x, lm.y, lm.z))
            
            # Get handedness (Left/Right)
            handedness = 'Unknown'
            if self.results.handedness and i < len(self.results.handedness):
                handedness = self.results.handedness[i][0].category_name
            
            hands.append({
                'landmarks': landmarks,
                'handedness': handedness
            })
        
        return hands
    
    def get_hand_count(self):
        """Get number of detected hands.
        
        Returns:
            int: Number of hands detected (0, 1, or 2)
        """
        if self.results is None or not self.results.hand_landmarks:
            return 0
        return len(self.results.hand_landmarks)
    
    def draw_landmarks(self, frame_bgr):
        """Draw hand landmarks on frame.
        
        Args:
            frame_bgr: BGR image frame to draw on
            
        Returns:
            Frame with landmarks drawn
        """
        if self.results is None or not self.results.hand_landmarks:
            return frame_bgr
        
        h, w = frame_bgr.shape[:2]
        
        # Colors
        landmark_color = (0, 255, 0)  # Green
        connection_color = (255, 255, 255)  # White
        
        # Use smoothed coords for drawing if available (prevents jitter)
        use_smoothed = (
            self._smoothed_landmarks is not None
            and len(self._smoothed_landmarks) == 21
        )

        # Draw each hand
        for hand_idx, hand_landmarks in enumerate(self.results.hand_landmarks):
            # Use smoothed landmarks for the first (primary) hand,
            # raw for any additional hands
            if use_smoothed and hand_idx == 0:
                points = [
                    (int(lm[0] * w), int(lm[1] * h))
                    for lm in self._smoothed_landmarks
                ]
            else:
                points = [
                    (int(lm.x * w), int(lm.y * h))
                    for lm in hand_landmarks
                ]
            
            # Draw connections
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection
                if start_idx < len(points) and end_idx < len(points):
                    cv2.line(frame_bgr, points[start_idx], points[end_idx], 
                             connection_color, 2)
            
            # Draw landmarks
            for i, point in enumerate(points):
                # Fingertips are larger
                if i in [4, 8, 12, 16, 20]:
                    cv2.circle(frame_bgr, point, 8, (0, 0, 255), -1)  # Red
                else:
                    cv2.circle(frame_bgr, point, 5, landmark_color, -1)
        
        return frame_bgr
    
    def has_hand(self) -> bool:
        """Check if a hand was detected in the last frame."""
        return (self.results is not None and 
                self.results.hand_landmarks is not None and
                len(self.results.hand_landmarks) > 0)
    
    def reset_timestamp(self):
        """Reset timestamp counter. Call when loading a new video."""
        self._frame_count = 0
        self._start_time = time.time() * 1000
    
    def release(self):
        """Release resources."""
        if self.detector:
            self.detector.close()
