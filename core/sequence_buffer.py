"""
Temporal Sequence Buffer - Gesture sequence accumulation with deduplication

This module handles:
- Accumulating recognized gestures over time
- Filtering duplicate consecutive detections (noise reduction)
- Maintaining a sliding window of recent gestures
- Detecting gesture boundaries (pauses between distinct gestures)

Design Principles:
- Gestures are only added when they represent a distinct sign
- Consecutive frames with the same gesture are collapsed
- A "gesture boundary" (brief pause or hand removal) allows the same gesture again
"""
import time
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Tuple
from collections import deque
from enum import Enum


class GestureState(Enum):
    """Current state of gesture detection."""
    IDLE = "idle"                    # No hand detected
    DETECTING = "detecting"          # Hand present, building detection
    STABLE = "stable"                # Gesture is stable, held
    TRANSITIONING = "transitioning"  # Moving between gestures


@dataclass
class DetectedGesture:
    """A single detected gesture with metadata.
    
    Attributes:
        gesture_id: Canonical gesture identifier
        raw_label: Original label from detector
        confidence: Detection confidence (0-1)
        timestamp: When gesture was finalized
        duration: How long gesture was held
        frame_count: Number of frames this gesture was seen
        is_word_level: Whether this is a word-level sign
    """
    gesture_id: str
    raw_label: str
    confidence: float
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0
    frame_count: int = 1
    is_word_level: bool = False
    
    def __str__(self):
        return f"{self.gesture_id}({self.confidence:.0%})"


@dataclass
class SequenceBufferConfig:
    """Configuration for the sequence buffer.
    
    Attributes:
        stability_frames: Frames needed to confirm a gesture (reduces flickering)
        min_confidence: Minimum confidence to accept a gesture
        gesture_timeout: Seconds of inactivity to trigger gesture boundary
        max_sequence_length: Maximum gestures to keep in buffer
        duplicate_filter_frames: Frames to wait before allowing same gesture again
    """
    stability_frames: int = 5
    min_confidence: float = 0.5
    gesture_timeout: float = 1.5
    max_sequence_length: int = 50
    duplicate_filter_frames: int = 8


class TemporalSequenceBuffer:
    """Manages temporal accumulation of gestures with deduplication.
    
    This buffer receives raw frame-by-frame gesture predictions and:
    1. Filters out low-confidence detections
    2. Requires stability (N consecutive frames) before accepting
    3. Deduplicates consecutive identical gestures
    4. Tracks timing for gesture boundaries
    5. Maintains ordered sequence for sentence mapping
    
    Usage:
        buffer = TemporalSequenceBuffer()
        
        # In frame loop:
        result = buffer.process_frame("A", 0.85, timestamp)
        if result:
            print(f"Gesture confirmed: {result.gesture_id}")
        
        # Get accumulated sequence:
        sequence = buffer.get_sequence()
        
        # Clear after translation:
        buffer.clear()
    """
    
    def __init__(self, config: Optional[SequenceBufferConfig] = None):
        self.config = config or SequenceBufferConfig()
        
        # Accumulated gesture sequence
        self._sequence: List[DetectedGesture] = []
        
        # Current detection state
        self._state = GestureState.IDLE
        self._current_gesture: Optional[str] = None
        self._current_confidence_sum: float = 0.0
        self._current_frame_count: int = 0
        self._current_start_time: float = 0.0
        
        # Timing
        self._last_gesture_time: float = 0.0
        self._last_frame_time: float = 0.0
        self._no_hand_frames: int = 0
        
        # Duplicate filtering
        self._last_added_gesture: Optional[str] = None
        self._frames_since_last_add: int = 0
        
        # Callbacks
        self._on_gesture_added: Optional[Callable[[DetectedGesture], None]] = None
        self._on_sequence_updated: Optional[Callable[[List[DetectedGesture]], None]] = None
    
    def set_on_gesture_added(self, callback: Callable[[DetectedGesture], None]):
        """Set callback for when a gesture is added to sequence."""
        self._on_gesture_added = callback
    
    def set_on_sequence_updated(self, callback: Callable[[List[DetectedGesture]], None]):
        """Set callback for sequence updates."""
        self._on_sequence_updated = callback
    
    def process_frame(
        self,
        gesture_label: Optional[str],
        confidence: float,
        is_word_level: bool = False,
        timestamp: Optional[float] = None
    ) -> Optional[DetectedGesture]:
        """Process a single frame's gesture prediction.
        
        Args:
            gesture_label: Detected gesture (None if no hand)
            confidence: Detection confidence
            is_word_level: Whether this is a word-level sign
            timestamp: Frame timestamp (uses current time if None)
            
        Returns:
            DetectedGesture if a new gesture was confirmed and added, else None
        """
        current_time = timestamp or time.time()
        self._last_frame_time = current_time
        self._frames_since_last_add += 1
        
        # Handle no detection
        if gesture_label is None or confidence < self.config.min_confidence:
            return self._handle_no_detection(current_time)
        
        # Normalize label
        label = gesture_label.upper()
        
        # Check if this is a new gesture or continuation
        if label == self._current_gesture:
            # Same gesture - accumulate stability
            return self._handle_same_gesture(label, confidence, current_time, is_word_level)
        else:
            # Different gesture - handle transition
            return self._handle_new_gesture(label, confidence, current_time, is_word_level)
    
    def _handle_no_detection(self, current_time: float) -> Optional[DetectedGesture]:
        """Handle frame with no valid gesture detected."""
        self._no_hand_frames += 1
        
        # If we were detecting something, finalize it if stable enough
        if self._state in [GestureState.DETECTING, GestureState.STABLE]:
            if self._current_frame_count >= self.config.stability_frames:
                result = self._finalize_current_gesture(current_time)
                self._reset_detection()
                return result
            else:
                # Not stable enough, discard
                self._reset_detection()
        
        # Mark as idle after enough no-hand frames
        if self._no_hand_frames > 3:
            self._state = GestureState.IDLE
            # Allow same gesture to be added again after hand removal
            if self._no_hand_frames > self.config.duplicate_filter_frames:
                self._last_added_gesture = None
        
        return None
    
    def _handle_same_gesture(
        self,
        label: str,
        confidence: float,
        current_time: float,
        is_word_level: bool
    ) -> Optional[DetectedGesture]:
        """Handle frame with same gesture as current."""
        self._no_hand_frames = 0
        self._current_frame_count += 1
        self._current_confidence_sum += confidence
        self._state = GestureState.STABLE if self._current_frame_count >= self.config.stability_frames else GestureState.DETECTING
        
        # Don't immediately add - wait for gesture to complete (hand removal or new gesture)
        return None
    
    def _handle_new_gesture(
        self,
        label: str,
        confidence: float,
        current_time: float,
        is_word_level: bool
    ) -> Optional[DetectedGesture]:
        """Handle transition to a new gesture."""
        self._no_hand_frames = 0
        result = None
        
        # Finalize previous gesture if it was stable
        if self._state in [GestureState.DETECTING, GestureState.STABLE]:
            if self._current_frame_count >= self.config.stability_frames:
                result = self._finalize_current_gesture(current_time)
        
        # Start detecting new gesture
        self._current_gesture = label
        self._current_confidence_sum = confidence
        self._current_frame_count = 1
        self._current_start_time = current_time
        self._state = GestureState.DETECTING
        
        return result
    
    def _finalize_current_gesture(self, current_time: float) -> Optional[DetectedGesture]:
        """Finalize and add current gesture to sequence."""
        if not self._current_gesture:
            return None
        
        # Check for duplicate filtering
        if (self._current_gesture == self._last_added_gesture and 
            self._frames_since_last_add < self.config.duplicate_filter_frames):
            return None
        
        # Calculate average confidence
        avg_confidence = self._current_confidence_sum / max(1, self._current_frame_count)
        
        # Create gesture record
        gesture = DetectedGesture(
            gesture_id=self._current_gesture,
            raw_label=self._current_gesture,
            confidence=avg_confidence,
            timestamp=current_time,
            duration=current_time - self._current_start_time,
            frame_count=self._current_frame_count,
            is_word_level=self._is_word_level_gesture(self._current_gesture)
        )
        
        # Add to sequence
        self._add_to_sequence(gesture)
        
        # Update tracking
        self._last_added_gesture = self._current_gesture
        self._frames_since_last_add = 0
        self._last_gesture_time = current_time
        
        return gesture
    
    def _add_to_sequence(self, gesture: DetectedGesture):
        """Add gesture to the sequence buffer."""
        self._sequence.append(gesture)
        
        # Trim if too long
        if len(self._sequence) > self.config.max_sequence_length:
            self._sequence = self._sequence[-self.config.max_sequence_length:]
        
        # Callbacks
        if self._on_gesture_added:
            self._on_gesture_added(gesture)
        if self._on_sequence_updated:
            self._on_sequence_updated(self._sequence.copy())
    
    def _reset_detection(self):
        """Reset current detection state."""
        self._current_gesture = None
        self._current_confidence_sum = 0.0
        self._current_frame_count = 0
        self._current_start_time = 0.0
        self._state = GestureState.IDLE
    
    def _is_word_level_gesture(self, gesture_id: str) -> bool:
        """Check if gesture is word-level (not a letter/number)."""
        # Word-level gestures don't start with LETTER_ or NUMBER_
        upper = gesture_id.upper()
        return not (upper.startswith("LETTER_") or 
                   upper.startswith("NUMBER_") or 
                   (len(upper) == 1 and upper.isalpha()) or
                   upper.isdigit())
    
    def force_finalize(self) -> Optional[DetectedGesture]:
        """Force finalize any pending gesture (called on stop/translate)."""
        if self._state in [GestureState.DETECTING, GestureState.STABLE]:
            if self._current_frame_count >= self.config.stability_frames // 2:  # Lower threshold for force
                result = self._finalize_current_gesture(time.time())
                self._reset_detection()
                return result
            self._reset_detection()
        return None
    
    def mark_no_hand(self):
        """Mark that hand was removed (allows same gesture again)."""
        self._no_hand_frames = self.config.duplicate_filter_frames + 1
        self._last_added_gesture = None
        if self._state == GestureState.STABLE:
            self.force_finalize()
        self._state = GestureState.IDLE
    
    def get_sequence(self) -> List[DetectedGesture]:
        """Get the current gesture sequence."""
        return self._sequence.copy()
    
    def get_sequence_ids(self) -> List[str]:
        """Get just the gesture IDs from the sequence."""
        return [g.gesture_id for g in self._sequence]
    
    def get_last_gesture(self) -> Optional[DetectedGesture]:
        """Get the most recently added gesture."""
        return self._sequence[-1] if self._sequence else None
    
    def get_time_since_last_gesture(self) -> float:
        """Get seconds since last gesture was added."""
        if self._last_gesture_time == 0:
            return float('inf')
        return time.time() - self._last_gesture_time
    
    def is_inactive(self, timeout: Optional[float] = None) -> bool:
        """Check if buffer is inactive (no gestures for timeout period)."""
        timeout = timeout or self.config.gesture_timeout
        return self.get_time_since_last_gesture() > timeout
    
    def delete_last(self) -> Optional[DetectedGesture]:
        """Delete and return the last gesture in sequence."""
        if self._sequence:
            return self._sequence.pop()
        return None
    
    def insert_space(self):
        """Insert a word boundary marker."""
        space_gesture = DetectedGesture(
            gesture_id="CTRL_SPACE",
            raw_label="SPACE",
            confidence=1.0,
            timestamp=time.time(),
            is_word_level=False
        )
        self._add_to_sequence(space_gesture)
    
    def clear(self):
        """Clear the sequence buffer."""
        self._sequence.clear()
        self._reset_detection()
        self._last_gesture_time = 0.0
        self._last_added_gesture = None
        self._frames_since_last_add = 0
    
    def get_state(self) -> GestureState:
        """Get current detection state."""
        return self._state
    
    def get_statistics(self) -> dict:
        """Get buffer statistics."""
        return {
            'sequence_length': len(self._sequence),
            'state': self._state.value,
            'current_gesture': self._current_gesture,
            'current_stability': self._current_frame_count,
            'time_since_last': self.get_time_since_last_gesture(),
            'is_inactive': self.is_inactive()
        }
