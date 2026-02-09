"""
Face Detector Module - MediaPipe Tasks API for Emotion Detection

Detects facial expressions/emotions to add context to sign language translation.
Uses facial landmark analysis to classify emotions.
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.request import urlretrieve

from config import MODELS_DIR


class Emotion(Enum):
    """Detected emotion categories."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    SURPRISED = "surprised"
    ANGRY = "angry"


@dataclass
class EmotionResult:
    """Result of emotion detection."""
    emotion: Emotion
    confidence: float
    landmarks_detected: bool


class FaceDetector:
    """MediaPipe FaceLandmarker wrapper for emotion detection.
    
    Uses facial landmark positions to estimate emotional state
    based on eyebrow position, mouth shape, and eye openness.
    """
    
    # Face landmark model URL
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    MODEL_NAME = "face_landmarker.task"
    
    def __init__(self):
        """Initialize face detector with MediaPipe FaceLandmarker."""
        self.model_path = os.path.join(MODELS_DIR, self.MODEL_NAME)
        
        # Download model if not exists
        if not os.path.exists(self.model_path):
            print(f"Downloading face landmarker model...")
            try:
                urlretrieve(self.MODEL_URL, self.model_path)
                print(f"Downloaded to: {self.model_path}")
            except Exception as e:
                print(f"Warning: Could not download face model: {e}")
                self.detector = None
                self.results = None
                return
        
        # Create face landmarker
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=True  # Enable blendshapes for emotion
            )
            self.detector = vision.FaceLandmarker.create_from_options(options)
        except Exception as e:
            print(f"Warning: Could not create face detector: {e}")
            self.detector = None
        
        self.results = None
        self._frame_height = 480
        self._frame_width = 640
        
        # Landmark indices for emotion detection (478 landmarks)
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.LEFT_EYEBROW_INDICES = [70, 63, 105, 66, 107]
        self.RIGHT_EYEBROW_INDICES = [336, 296, 334, 293, 300]
        self.NOSE_TIP = 1
    
    def process(self, frame_rgb: np.ndarray) -> Optional[EmotionResult]:
        """Process RGB frame to detect face and emotion.
        
        Args:
            frame_rgb: RGB image frame (numpy array)
            
        Returns:
            EmotionResult with detected emotion, or None if no face
        """
        if self.detector is None:
            return EmotionResult(Emotion.NEUTRAL, 0.0, False)
        
        self._frame_height, self._frame_width = frame_rgb.shape[:2]
        
        # Convert to MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Detect face
        try:
            self.results = self.detector.detect(mp_image)
        except Exception as e:
            return EmotionResult(Emotion.NEUTRAL, 0.0, False)
        
        if not self.results.face_landmarks:
            return EmotionResult(Emotion.NEUTRAL, 0.0, False)
        
        # Analyze emotion from landmarks and blendshapes
        emotion, confidence = self._analyze_emotion()
        
        return EmotionResult(emotion, confidence, True)
    
    def _analyze_emotion(self) -> Tuple[Emotion, float]:
        """Analyze facial landmarks and blendshapes to determine emotion."""
        if not self.results or not self.results.face_landmarks:
            return Emotion.NEUTRAL, 0.0
        
        # Use blendshapes if available (more accurate)
        if self.results.face_blendshapes and len(self.results.face_blendshapes) > 0:
            return self._analyze_blendshapes(self.results.face_blendshapes[0])
        
        # Fallback to landmark analysis
        return self._analyze_landmarks(self.results.face_landmarks[0])
    
    def _analyze_blendshapes(self, blendshapes) -> Tuple[Emotion, float]:
        """Analyze face blendshapes for emotion detection.
        
        Uses compound signals from multiple blendshapes for each emotion
        rather than relying on a single feature.  Thresholds are tuned for
        real-world webcam usage where subtle expressions matter.
        """
        # Convert blendshapes to dict for easier access
        bs_dict = {bs.category_name: bs.score for bs in blendshapes}
        
        # --- Extract all relevant blendshape values ---
        # Smile
        smile_L = bs_dict.get('mouthSmileLeft', 0)
        smile_R = bs_dict.get('mouthSmileRight', 0)
        smile = (smile_L + smile_R) / 2
        
        # Cheek raise (accompanies genuine smiles)
        cheek_squint_L = bs_dict.get('cheekSquintLeft', 0)
        cheek_squint_R = bs_dict.get('cheekSquintRight', 0)
        cheek_squint = (cheek_squint_L + cheek_squint_R) / 2
        
        # Frown / lip corner depressor
        frown_L = bs_dict.get('mouthFrownLeft', 0)
        frown_R = bs_dict.get('mouthFrownRight', 0)
        frown = (frown_L + frown_R) / 2
        
        # Brow movements
        brow_inner_up = bs_dict.get('browInnerUp', 0)
        brow_down_L = bs_dict.get('browDownLeft', 0)
        brow_down_R = bs_dict.get('browDownRight', 0)
        brow_down = (brow_down_L + brow_down_R) / 2
        brow_outer_up_L = bs_dict.get('browOuterUpLeft', 0)
        brow_outer_up_R = bs_dict.get('browOuterUpRight', 0)
        brow_outer_up = (brow_outer_up_L + brow_outer_up_R) / 2
        
        # Jaw / mouth opening
        jaw_open = bs_dict.get('jawOpen', 0)
        mouth_close = bs_dict.get('mouthClose', 0)
        
        # Nose sneer (wrinkled nose — anger)
        nose_sneer_L = bs_dict.get('noseSneerLeft', 0)
        nose_sneer_R = bs_dict.get('noseSneerRight', 0)
        nose_sneer = (nose_sneer_L + nose_sneer_R) / 2
        
        # Eye squint (anger / disgust)
        eye_squint_L = bs_dict.get('eyeSquintLeft', 0)
        eye_squint_R = bs_dict.get('eyeSquintRight', 0)
        eye_squint = (eye_squint_L + eye_squint_R) / 2
        
        # Lip press (anger / tension)
        mouth_press_L = bs_dict.get('mouthPressLeft', 0)
        mouth_press_R = bs_dict.get('mouthPressRight', 0)
        mouth_press = (mouth_press_L + mouth_press_R) / 2
        
        # Mouth lower-down & upper-up for exaggerated sad
        mouth_lower_down_L = bs_dict.get('mouthLowerDownLeft', 0)
        mouth_lower_down_R = bs_dict.get('mouthLowerDownRight', 0)
        mouth_lower_down = (mouth_lower_down_L + mouth_lower_down_R) / 2
        
        # Lip stretch (can accompany grimace / sadness)
        mouth_stretch_L = bs_dict.get('mouthStretchLeft', 0)
        mouth_stretch_R = bs_dict.get('mouthStretchRight', 0)
        mouth_stretch = (mouth_stretch_L + mouth_stretch_R) / 2
        
        # Eye wide (surprise)
        eye_wide_L = bs_dict.get('eyeWideLeft', 0)
        eye_wide_R = bs_dict.get('eyeWideRight', 0)
        eye_wide = (eye_wide_L + eye_wide_R) / 2
        
        # --- Compute per-emotion scores using compound signals ---
        scores = {}
        
        # ── HAPPY ──
        # Primary: smile.  Boosted by cheek squint (genuine Duchenne smile).
        # Requires noticeable smile to trigger.
        happy_score = 0
        if smile > 0.15:  # Threshold: must actually be smiling
            happy_score = smile * 1.5 + cheek_squint * 0.4
        scores[Emotion.HAPPY] = max(0, happy_score)
        
        # ── SAD ──
        # Primary signal: inner brow raise ("puppy dog eyes") — this is the most
        # reliable indicator of sadness.  Mouth frown is secondary.
        # Also look for droopy/pout expression.
        sad_score = 0
        # Inner brow raise is the KEY sad indicator
        if brow_inner_up > 0.1:
            sad_score += brow_inner_up * 2.0
        # Mouth frown adds to it (but is unreliable alone)
        sad_score += frown * 2.5
        # Mouth corners pulled down
        sad_score += mouth_lower_down * 0.6
        # Penalize if smiling (not sad)
        sad_score -= smile * 1.0
        # Penalize if brow is furrowed down (that's angry, not sad)
        sad_score -= brow_down * 0.5
        scores[Emotion.SAD] = max(0, sad_score)
        
        # ── ANGRY ──
        # Require MULTIPLE anger signals to fire — don't trigger on single cues.
        # This prevents neutral faces with slightly furrowed brows from reading as angry.
        angry_signals = 0
        angry_score = 0
        
        # Count how many anger signals are present
        if brow_down > 0.15:
            angry_signals += 1
            angry_score += brow_down * 1.0
        if nose_sneer > 0.1:
            angry_signals += 1
            angry_score += nose_sneer * 1.2
        if eye_squint > 0.2:
            angry_signals += 1
            angry_score += eye_squint * 0.5
        if mouth_press > 0.15:
            angry_signals += 1
            angry_score += mouth_press * 0.5
        
        # Only count as angry if at least 2 signals are present
        if angry_signals < 2:
            angry_score = angry_score * 0.3  # Heavily dampen single-signal anger
        
        # Penalize if smiling or inner brow raised (not angry)
        angry_score -= smile * 0.8
        angry_score -= brow_inner_up * 0.4
        scores[Emotion.ANGRY] = max(0, angry_score)
        
        # ── SURPRISED ──
        # Primary: brow raise + jaw open + eyes wide.
        surprised_score = 0
        if brow_inner_up > 0.15 or brow_outer_up > 0.15:
            surprised_score += (brow_inner_up + brow_outer_up) * 0.8
        if jaw_open > 0.15:
            surprised_score += jaw_open * 1.0
        if eye_wide > 0.1:
            surprised_score += eye_wide * 0.8
        scores[Emotion.SURPRISED] = max(0, surprised_score)
        
        # ── NEUTRAL ──
        # Neutral is the default when no strong emotion signals are present.
        # Calculate total "expression intensity" — if low, it's neutral.
        expression_intensity = (
            smile * 1.5 
            + frown * 2.0 
            + brow_down * 1.2 
            + brow_inner_up * 1.5
            + jaw_open * 0.8 
            + nose_sneer * 1.5 
            + eye_squint * 0.6 
            + mouth_press * 0.6
        )
        
        # Neutral score is high when expression intensity is low
        # Use a sigmoid-like falloff so neutral stays strong until expressions get noticeable
        if expression_intensity < 0.25:
            neutral_score = 0.6  # Strong neutral for very relaxed face
        elif expression_intensity < 0.4:
            neutral_score = 0.4  # Moderate neutral
        elif expression_intensity < 0.6:
            neutral_score = 0.2  # Weak neutral
        else:
            neutral_score = 0.05  # Very weak — some emotion is happening
        
        scores[Emotion.NEUTRAL] = neutral_score
        
        # Get highest scoring emotion
        best_emotion = max(scores, key=scores.get)
        confidence = min(1.0, max(0.1, scores[best_emotion]))
        
        # If the winning score is extremely low, default to neutral
        if scores[best_emotion] < 0.1:
            return Emotion.NEUTRAL, 0.5
        
        return best_emotion, confidence
    
    def _analyze_landmarks(self, landmarks) -> Tuple[Emotion, float]:
        """Fallback: Analyze landmarks for emotion (less accurate than blendshapes)."""
        try:
            # Mouth height (jaw open)
            top_lip = landmarks[13]
            bottom_lip = landmarks[14]
            mouth_height = abs(top_lip.y - bottom_lip.y)
            
            # Mouth corners vs center-bottom  (smile vs frown)
            left_corner = landmarks[61]
            right_corner = landmarks[291]
            center_bottom = landmarks[17]
            
            corner_avg_y = (left_corner.y + right_corner.y) / 2
            # Positive  → corners lower than center  → smile
            # Negative  → corners higher than center → frown
            mouth_curve = center_bottom.y - corner_avg_y
            
            # Eyebrow height relative to eye center
            left_brow_top = landmarks[105]
            left_eye_center = landmarks[159]
            right_brow_top = landmarks[334]
            right_eye_center = landmarks[386]
            
            left_brow_dist  = left_eye_center.y - left_brow_top.y
            right_brow_dist = right_eye_center.y - right_brow_top.y
            avg_brow_dist = (left_brow_dist + right_brow_dist) / 2
            
            # Inner brow points for furrowing
            left_inner_brow  = landmarks[66]
            right_inner_brow = landmarks[296]
            inner_brow_dist  = abs(left_inner_brow.x - right_inner_brow.x)
            
            # Happy: mouth corners up
            if mouth_curve > 0.015:
                return Emotion.HAPPY, min(0.9, 0.5 + mouth_curve * 10)
            
            # Surprised: mouth open wide + brows raised
            if mouth_height > 0.04 and avg_brow_dist > 0.06:
                return Emotion.SURPRISED, 0.7
            
            # Angry: brows furrowed (close together) + mouth not smiling
            if inner_brow_dist < 0.035 and mouth_curve < 0.005:
                return Emotion.ANGRY, 0.6
            
            # Sad: mouth corners down OR brows raised with no smile
            if mouth_curve < -0.008:
                return Emotion.SAD, min(0.8, 0.5 + abs(mouth_curve) * 12)
            
            # Mild sad: flat mouth + slightly raised inner brows
            if avg_brow_dist > 0.055 and mouth_curve < 0.005 and mouth_height < 0.02:
                return Emotion.SAD, 0.5
            
            return Emotion.NEUTRAL, 0.5
        except Exception:
            return Emotion.NEUTRAL, 0.5
    
    def draw_landmarks(self, frame_bgr: np.ndarray, 
                       show_mesh: bool = False,
                       show_emotion: bool = True,
                       emotion_result: Optional[EmotionResult] = None) -> np.ndarray:
        """Draw face landmarks and emotion on frame."""
        if self.results is None or not self.results.face_landmarks:
            return frame_bgr
        
        h, w = frame_bgr.shape[:2]
        
        # Draw face landmarks (simplified - just contour)
        for face_landmarks in self.results.face_landmarks:
            # Draw face oval
            face_oval_indices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 
                                397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                                172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
            
            points = []
            for idx in face_oval_indices:
                if idx < len(face_landmarks):
                    lm = face_landmarks[idx]
                    px = int(lm.x * w)
                    py = int(lm.y * h)
                    points.append((px, py))
            
            # Draw oval
            if len(points) > 2:
                for i in range(len(points) - 1):
                    cv2.line(frame_bgr, points[i], points[i+1], (0, 255, 255), 1)
                cv2.line(frame_bgr, points[-1], points[0], (0, 255, 255), 1)
        
        # Draw emotion text
        if show_emotion and emotion_result and emotion_result.landmarks_detected:
            emotion_text = f"{emotion_result.emotion.value.capitalize()}"
            confidence_text = f"{emotion_result.confidence:.0%}"
            
            # Emotion colors
            emotion_colors = {
                Emotion.NEUTRAL: (200, 200, 200),
                Emotion.HAPPY: (0, 255, 100),
                Emotion.SAD: (255, 100, 100),
                Emotion.SURPRISED: (0, 200, 255),
                Emotion.ANGRY: (0, 0, 255)
            }
            color = emotion_colors.get(emotion_result.emotion, (255, 255, 255))
            
            # Draw background box
            cv2.rectangle(frame_bgr, (10, 10), (180, 60), (0, 0, 0), -1)
            cv2.rectangle(frame_bgr, (10, 10), (180, 60), color, 2)
            
            # Draw text
            cv2.putText(frame_bgr, f"{emotion_text}", (20, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame_bgr, confidence_text, (20, 52),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        return frame_bgr
    
    def has_face(self) -> bool:
        """Check if a face was detected in the last frame."""
        return (self.results is not None and 
                self.results.face_landmarks is not None and
                len(self.results.face_landmarks) > 0)
    
    def release(self):
        """Release resources."""
        if self.detector:
            self.detector.close()
