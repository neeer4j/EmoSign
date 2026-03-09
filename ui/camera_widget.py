"""
Camera Widget - Display webcam feed with landmarks and gesture tracking
"""
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from collections import Counter

from detector.camera import Camera
from detector.hand_tracker import HandTracker
from detector.features import FeatureExtractor
from detector.dynamic_gestures import DynamicGestureTracker
from detector.face_detector import FaceDetector, Emotion
from ml.heuristic_classifier import HeuristicClassifier
from ml.gesture_pipeline import GesturePipeline


class CameraWidget(QFrame):
    """Widget to display camera feed with hand tracking overlay."""
    
    # Signals
    features_ready = Signal(object)           # Emitted when features are extracted
    hand_detected = Signal(bool)              # Emitted when hand detection status changes
    fps_updated = Signal(float)               # Emitted with current FPS
    dynamic_gesture_detected = Signal(str, float)  # Emitted when dynamic gesture detected (name, confidence)
    emotion_detected = Signal(str, float)     # Emitted with detected emotion (name, confidence)
    heuristic_gesture_detected = Signal(str, float)  # Reliable gesture from geometry
    nn_gesture_detected = Signal(str, float, str)    # (label, confidence, model_used) from dual NN
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cameraFrame")
        
        # Components
        self.camera = Camera()
        self.hand_tracker = HandTracker()
        self.feature_extractor = FeatureExtractor()
        self.dynamic_tracker = DynamicGestureTracker(buffer_size=40, fps=20)
        self.face_detector = FaceDetector()
        self.heuristic_classifier = HeuristicClassifier()
        self.gesture_pipeline = GesturePipeline()
        self._pipeline_status = self.gesture_pipeline.load()
        
        # State
        self.is_running = False
        self._last_hand_detected = False
        self._last_emotion = None
        self._emotion_buffer = []          # rolling window for smoothing
        self._emotion_buffer_size = 8      # vote over last N frames (increased for stability)
        self.dynamic_gestures_enabled = True  # Toggle for dynamic gesture recognition
        self.emotion_detection_enabled = True  # Toggle for emotion detection
        self.heuristic_threshold = 0.5        # Confidence threshold for heuristic classifier
        self._frame_count = 0                 # Frame counter for throttling
        self._emotion_skip_frames = 5         # Run emotion detection every Nth frame (reduced load)
        self._ml_skip_frames = 2              # Run heavy ML pipeline every Nth frame
        
        # Setup UI
        self._setup_ui()
        
        # Timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background-color: #000000; border-radius: 12px;")
        self.video_label.setText("Camera Off")
        
        layout.addWidget(self.video_label)
    
    def start(self) -> bool:
        """Start camera capture."""
        if self.is_running:
            return True
        
        if not self.camera.start():
            self.video_label.setText("❌ Camera Error\nCould not access webcam")
            return False
        
        self.is_running = True
        self.dynamic_tracker.clear()  # Reset dynamic gesture tracker
        self.timer.start(50)  # ~20 FPS — less CPU load, still smooth enough for signing
        return True
    
    def stop(self):
        """Stop camera capture."""
        self.timer.stop()
        self.camera.stop()
        self.is_running = False
        self.video_label.setText("Camera Off")
        self.video_label.setPixmap(QPixmap())
        self.dynamic_tracker.clear()
    
    def set_dynamic_gestures_enabled(self, enabled: bool):
        """Enable or disable dynamic gesture recognition."""
        self.dynamic_gestures_enabled = enabled
        if not enabled:
            self.dynamic_tracker.clear()
    
    def _update_frame(self):
        """Process and display new frame."""
        success, frame_bgr, frame_rgb = self.camera.read()
        
        if not success:
            return
        
        self._frame_count += 1
        
        # Process with MediaPipe Hand Tracker
        self.hand_tracker.process(frame_rgb)
        
        # Check hand detection
        hand_detected = self.hand_tracker.has_hand()
        if hand_detected != self._last_hand_detected:
            self.hand_detected.emit(hand_detected)
            self._last_hand_detected = hand_detected
        
        # Get landmarks
        landmarks = None
        if hand_detected:
            landmarks = self.hand_tracker.get_landmarks()
            
            # Extract features for ML-based gesture recognition (every frame)
            features = self.feature_extractor.extract(landmarks)
            self.features_ready.emit(features)

            # Heavy ML classifiers run every _ml_skip_frames to reduce CPU load.
            # Dynamic gesture tracking still runs every frame for smooth trajectory.
            if self._frame_count % self._ml_skip_frames == 0:
                # Heuristic gesture detection
                heuristic_label, heuristic_conf = self.heuristic_classifier.predict(landmarks)
                if heuristic_label and heuristic_conf >= self.heuristic_threshold:
                    self.heuristic_gesture_detected.emit(heuristic_label, heuristic_conf)

                # Unified pipeline: Keras MLP/LSTM + heuristic fallback + smoothing
                pipe_label, pipe_conf, model_used = self.gesture_pipeline.process_frame(landmarks)

                if pipe_label and pipe_conf > 0.0:
                    self.nn_gesture_detected.emit(pipe_label, pipe_conf, model_used)
        
        # Dynamic gesture tracking (runs even when hand disappears to finalize gestures)
        if self.dynamic_gestures_enabled:
            gesture_name, confidence = self.dynamic_tracker.update(landmarks)
            if gesture_name is not None and confidence > 0.6:
                self.dynamic_gesture_detected.emit(gesture_name, confidence)
        
        # Face/Emotion detection with temporal smoothing (throttled for performance)
        emotion_result = None
        if self.emotion_detection_enabled and (self._frame_count % self._emotion_skip_frames == 0):
            emotion_result = self.face_detector.process(frame_rgb)
            if emotion_result and emotion_result.landmarks_detected:
                # Add to rolling buffer
                self._emotion_buffer.append(emotion_result.emotion)
                if len(self._emotion_buffer) > self._emotion_buffer_size:
                    self._emotion_buffer.pop(0)
                
                # Majority vote over the buffer
                counts = Counter(self._emotion_buffer)
                smoothed_emotion = counts.most_common(1)[0][0]
                
                if smoothed_emotion != self._last_emotion:
                    self._last_emotion = smoothed_emotion
                    self.emotion_detected.emit(
                        smoothed_emotion.value, 
                        emotion_result.confidence
                    )
        
        # Draw landmarks and tracking visualization on frame
        frame_bgr = self.hand_tracker.draw_landmarks(frame_bgr)
        frame_bgr = self._draw_tracking_overlay(frame_bgr)
        
        # Draw face emotion overlay
        if self.emotion_detection_enabled and emotion_result:
            frame_bgr = self.face_detector.draw_landmarks(
                frame_bgr, 
                show_mesh=False, 
                show_emotion=True,
                emotion_result=emotion_result
            )
        
        # Convert to QImage and display
        self._display_frame(frame_bgr)
        
        # Emit FPS
        self.fps_updated.emit(self.camera.get_fps())
    
    def _draw_tracking_overlay(self, frame):
        """Draw dynamic gesture tracking visualization.

        - Z is drawn with the index finger  → show fingertip_buffer (landmark 8)
        - J is drawn with the pinky finger  → show pinky_buffer     (landmark 20)
        We pick whichever tip has covered more total distance recently,
        so the right trail lights up automatically.
        """
        if not self.dynamic_gestures_enabled:
            return frame

        def _trail_length(buf):
            if len(buf) < 2:
                return 0.0
            pts = list(buf)
            return sum(
                float(np.linalg.norm(np.array(pts[i][:2]) - np.array(pts[i-1][:2])))
                for i in range(1, len(pts))
            )

        # Pick the buffer whose tip has moved more — that's the active drawing finger
        index_len = _trail_length(self.dynamic_tracker.fingertip_buffer)
        pinky_len  = _trail_length(self.dynamic_tracker.pinky_buffer)
        traj_buffer = (
            self.dynamic_tracker.pinky_buffer
            if pinky_len > index_len
            else self.dynamic_tracker.fingertip_buffer
        )

        if len(traj_buffer) > 1:
            positions = list(traj_buffer)
            h, w = frame.shape[:2]
            pts = np.array(
                [[int(p[0] * w), int(p[1] * h)] for p in positions],
                dtype=np.int32
            )
            npts = len(pts)
            for i in range(1, npts):
                alpha = i / npts  # 0 = old (faded), 1 = newest (bright)
                # Cyan → green gradient with increasing width
                blue  = int(255 * (1 - alpha))   # high at start, low at end
                green = int(200 + 55 * alpha)     # always present
                red   = 0
                color = (blue, green, red)
                thickness = max(1, int(1 + 4 * alpha))  # 1px old → 5px newest
                cv2.line(frame,
                         (pts[i-1][0], pts[i-1][1]),
                         (pts[i][0],   pts[i][1]),
                         color, thickness, cv2.LINE_AA)

        state = self.dynamic_tracker.state.value
        if state == "tracking":
            cv2.putText(frame, "TRACKING GESTURE...", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return frame
    
    def _display_frame(self, frame_bgr):
        """Convert and display frame on label."""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        
        # Create QImage
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale to fit label while maintaining aspect ratio
        # Use FastTransformation for performance on low-end systems
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
    
    def is_active(self) -> bool:
        """Check if camera is active."""
        return self.is_running
    
    def set_emotion_detection_enabled(self, enabled: bool):
        """Enable or disable emotion detection."""
        self.emotion_detection_enabled = enabled
        self._last_emotion = None
    
    def release(self):
        """Clean up resources."""
        self.stop()
        self.hand_tracker.release()
        self.face_detector.release()
