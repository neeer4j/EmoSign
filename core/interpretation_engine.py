"""
Sign Language Interpretation Engine - Main orchestrator for gesture interpretation

This is the main entry point for sign language interpretation, coordinating:
- Gesture recognition (from camera/video input)
- Temporal sequence buffering
- Sentence mapping
- Text output generation
- Text-to-sign reverse communication

Design Principles:
- Modular architecture with clear component separation
- Supports both live camera and uploaded video input
- Sentence-level output via manual stop or inactivity timeout
- Bidirectional communication (Sign→Text and Text→Sign)
- Extensible vocabulary without UI changes

SCOPE & LIMITATIONS:
This system uses a constrained vocabulary approach for reliable communication.
It is NOT a full ASL linguistic translator - it provides practical, real-time
sentence-level communication within a controlled set of gestures and phrases.
This is explicitly designed as a college major project demonstration.
"""
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any, Tuple
from enum import Enum
from queue import Queue, Empty

from .gesture_dictionary import (
    GestureDictionary, GestureDefinition, SentenceMapping,
    GestureCategory, get_dictionary
)
from .sequence_buffer import (
    TemporalSequenceBuffer, SequenceBufferConfig,
    DetectedGesture, GestureState
)
from .sentence_mapper import (
    SentenceMapper, TextToSignMapper,
    SentenceResult, OutputType
)


class EngineMode(Enum):
    """Operating modes for the interpretation engine."""
    IDLE = "idle"              # Not processing
    LIVE_CAMERA = "camera"     # Live camera input
    VIDEO_FILE = "video"       # Uploaded video input
    TEXT_TO_SIGN = "text"      # Reverse translation mode


class TranslationTrigger(Enum):
    """What triggered the translation."""
    MANUAL = "manual"          # User pressed Stop/Translate
    TIMEOUT = "timeout"        # Inactivity timeout reached
    VIDEO_END = "video_end"    # Video playback completed
    AUTO = "auto"              # Automatic (sentence mode)


@dataclass
class EngineConfig:
    """Configuration for the interpretation engine.
    
    Attributes:
        stability_frames: Frames needed to confirm a gesture
        min_confidence: Minimum confidence to accept detection
        inactivity_timeout: Seconds of no gestures before auto-translate
        enable_auto_translate: Whether to auto-translate on timeout
        enable_partial_hints: Show partial match hints during input
    """
    stability_frames: int = 5
    min_confidence: float = 0.5
    inactivity_timeout: float = 2.5
    enable_auto_translate: bool = True
    enable_partial_hints: bool = True
    max_sequence_length: int = 50
    duplicate_filter_frames: int = 8


@dataclass
class EngineState:
    """Current state of the interpretation engine."""
    mode: EngineMode = EngineMode.IDLE
    is_active: bool = False
    
    # Current recognition state
    current_gesture: Optional[str] = None
    current_confidence: float = 0.0
    gesture_state: GestureState = GestureState.IDLE
    
    # Sequence state
    sequence_length: int = 0
    preview_text: str = ""
    
    # Timing
    start_time: float = 0.0
    time_since_last_gesture: float = 0.0
    
    # Stats
    frames_processed: int = 0
    gestures_recognized: int = 0


@dataclass
class TranslationOutput:
    """Final translation output.
    
    Attributes:
        text: The translated English text
        output_type: How the translation was generated
        trigger: What caused the translation
        gesture_count: Number of gestures in sequence
        word_count: Number of words in output
        confidence: Average confidence
        matched_sentence: Predefined sentence if matched
        gesture_breakdown: Interpretation of each gesture
        duration: Time from start to translation
    """
    text: str
    output_type: OutputType
    trigger: TranslationTrigger
    gesture_count: int = 0
    word_count: int = 0
    confidence: float = 0.0
    matched_sentence: Optional[SentenceMapping] = None
    gesture_breakdown: List[Tuple[str, str]] = field(default_factory=list)
    duration: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'output_type': self.output_type.value,
            'trigger': self.trigger.value,
            'gesture_count': self.gesture_count,
            'word_count': self.word_count,
            'confidence': self.confidence,
            'matched_sentence_id': self.matched_sentence.id if self.matched_sentence else None,
            'duration': self.duration
        }


class SignLanguageEngine:
    """Main interpretation engine for sign language communication.
    
    This engine orchestrates the entire interpretation pipeline:
    1. Receives gesture predictions from camera/video processing
    2. Buffers gestures with temporal deduplication
    3. Maps gesture sequences to English sentences
    4. Provides real-time preview and partial match hints
    5. Outputs final translation on manual stop or timeout
    
    Usage:
        engine = SignLanguageEngine()
        
        # Start for live camera
        engine.start(EngineMode.LIVE_CAMERA)
        
        # Process frames (called by camera/video widget)
        engine.process_gesture("HELLO", 0.95, is_word_level=True)
        engine.process_gesture("A", 0.88)  # Letter
        
        # Get preview
        print(engine.get_preview())
        
        # Translate (manual trigger)
        result = engine.translate()
        print(result.text)
        
        # Or wait for auto-translate on timeout
        engine.check_timeout()  # Call periodically
    
    Bidirectional:
        # Text to sign
        result = engine.text_to_sign("Hello, how are you?")
        for gesture in result.gestures:
            display(gesture)
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """Initialize the interpretation engine.
        
        Args:
            config: Engine configuration (uses defaults if None)
        """
        self.config = config or EngineConfig()
        
        # Core components
        self.dictionary = get_dictionary()
        
        buffer_config = SequenceBufferConfig(
            stability_frames=self.config.stability_frames,
            min_confidence=self.config.min_confidence,
            gesture_timeout=self.config.inactivity_timeout,
            max_sequence_length=self.config.max_sequence_length,
            duplicate_filter_frames=self.config.duplicate_filter_frames
        )
        self.buffer = TemporalSequenceBuffer(buffer_config)
        
        self.sentence_mapper = SentenceMapper(self.dictionary)
        self.text_to_sign_mapper = TextToSignMapper(self.dictionary)
        
        # State
        self._state = EngineState()
        self._start_time: float = 0.0
        self._frames_processed: int = 0
        
        # Callbacks
        self._on_gesture_recognized: Optional[Callable[[DetectedGesture], None]] = None
        self._on_preview_updated: Optional[Callable[[str, List[SentenceMapping]], None]] = None
        self._on_translation_complete: Optional[Callable[[TranslationOutput], None]] = None
        self._on_state_changed: Optional[Callable[[EngineState], None]] = None
        
        # Setup internal callbacks
        self.buffer.set_on_gesture_added(self._handle_gesture_added)
        self.buffer.set_on_sequence_updated(self._handle_sequence_updated)
    
    # === Callback Setters ===
    
    def set_on_gesture_recognized(self, callback: Callable[[DetectedGesture], None]):
        """Set callback for when a gesture is confirmed."""
        self._on_gesture_recognized = callback
    
    def set_on_preview_updated(self, callback: Callable[[str, List[SentenceMapping]], None]):
        """Set callback for preview updates (text, partial matches)."""
        self._on_preview_updated = callback
    
    def set_on_translation_complete(self, callback: Callable[[TranslationOutput], None]):
        """Set callback for translation completion."""
        self._on_translation_complete = callback
    
    def set_on_state_changed(self, callback: Callable[[EngineState], None]):
        """Set callback for state changes."""
        self._on_state_changed = callback
    
    # === Control Methods ===
    
    def start(self, mode: EngineMode = EngineMode.LIVE_CAMERA):
        """Start the interpretation engine.
        
        Args:
            mode: Operating mode (camera, video, or text-to-sign)
        """
        self.clear()
        self._state.mode = mode
        self._state.is_active = True
        self._state.start_time = time.time()
        self._start_time = time.time()
        self._frames_processed = 0
        
        self._notify_state_change()
    
    def stop(self):
        """Stop the engine without translating."""
        self._state.is_active = False
        self._state.mode = EngineMode.IDLE
        self._notify_state_change()
    
    def translate(self, trigger: TranslationTrigger = TranslationTrigger.MANUAL) -> TranslationOutput:
        """Finalize and translate the current gesture sequence.
        
        Args:
            trigger: What triggered this translation
            
        Returns:
            TranslationOutput with the English text and metadata
        """
        # Force finalize any pending gesture
        self.buffer.force_finalize()
        
        # Get the gesture sequence
        gestures = self.buffer.get_sequence()
        
        # Map to sentence
        result = self.sentence_mapper.map_sequence(gestures)
        
        # Build output
        output = TranslationOutput(
            text=result.text,
            output_type=result.output_type,
            trigger=trigger,
            gesture_count=result.gesture_count,
            word_count=result.word_count,
            confidence=result.confidence,
            matched_sentence=result.matched_mapping,
            gesture_breakdown=result.breakdown,
            duration=time.time() - self._start_time if self._start_time > 0 else 0
        )
        
        # Notify
        if self._on_translation_complete:
            self._on_translation_complete(output)
        
        # Clear buffer after translation
        self.buffer.clear()
        
        # Update state
        self._state.sequence_length = 0
        self._state.preview_text = ""
        self._state.gestures_recognized = 0
        
        return output
    
    def clear(self):
        """Clear all accumulated gestures."""
        self.buffer.clear()
        self._state = EngineState()
        self._start_time = 0.0
        self._frames_processed = 0
    
    # === Gesture Processing ===
    
    def process_gesture(
        self,
        gesture_label: Optional[str],
        confidence: float,
        is_word_level: bool = False,
        timestamp: Optional[float] = None
    ) -> Optional[DetectedGesture]:
        """Process a gesture prediction from the recognizer.
        
        This is the main entry point for gesture input. Call this for each
        frame where a gesture is detected.
        
        Args:
            gesture_label: Detected gesture (None if no hand)
            confidence: Detection confidence (0-1)
            is_word_level: Whether this is a word-level sign
            timestamp: Frame timestamp (uses current time if None)
            
        Returns:
            DetectedGesture if a new gesture was confirmed
        """
        if not self._state.is_active:
            return None
        
        self._frames_processed += 1
        self._state.frames_processed = self._frames_processed
        
        # Update current gesture state
        self._state.current_gesture = gesture_label
        self._state.current_confidence = confidence
        
        # Normalize the gesture label using dictionary
        normalized_label = None
        if gesture_label:
            normalized_label = self.dictionary.normalize_gesture(gesture_label)
            if not normalized_label:
                normalized_label = gesture_label.upper()
            
            # Check if it's word-level
            gesture_def = self.dictionary.get_gesture(normalized_label)
            if gesture_def:
                is_word_level = gesture_def.category in [
                    GestureCategory.WORD, 
                    GestureCategory.COMPOUND
                ]
        
        # Process through buffer
        result = self.buffer.process_frame(
            gesture_label=normalized_label,
            confidence=confidence,
            is_word_level=is_word_level,
            timestamp=timestamp
        )
        
        # Update state
        self._state.gesture_state = self.buffer.get_state()
        self._state.time_since_last_gesture = self.buffer.get_time_since_last_gesture()
        
        return result
    
    def mark_no_hand(self):
        """Mark that no hand is detected (allows same gesture again)."""
        self.buffer.mark_no_hand()
        self._state.gesture_state = GestureState.IDLE
    
    def insert_space(self):
        """Insert a word boundary."""
        self.buffer.insert_space()
    
    def delete_last(self):
        """Delete the last gesture."""
        self.buffer.delete_last()
        self._update_preview()
    
    # === Query Methods ===
    
    def get_preview(self) -> str:
        """Get preview text of current gesture sequence."""
        gestures = self.buffer.get_sequence()
        return self.sentence_mapper.get_preview(gestures)
    
    def get_partial_matches(self) -> List[SentenceMapping]:
        """Get sentences that match the current partial sequence."""
        if not self.config.enable_partial_hints:
            return []
        gestures = self.buffer.get_sequence()
        return self.sentence_mapper.get_partial_matches(gestures)
    
    def get_sequence(self) -> List[DetectedGesture]:
        """Get the current gesture sequence."""
        return self.buffer.get_sequence()
    
    def get_state(self) -> EngineState:
        """Get current engine state."""
        self._state.sequence_length = len(self.buffer.get_sequence())
        self._state.preview_text = self.get_preview()
        self._state.time_since_last_gesture = self.buffer.get_time_since_last_gesture()
        return self._state
    
    def is_inactive(self) -> bool:
        """Check if engine is inactive (no gestures for timeout period)."""
        return self.buffer.is_inactive(self.config.inactivity_timeout)
    
    def check_timeout(self) -> Optional[TranslationOutput]:
        """Check for inactivity timeout and auto-translate if needed.
        
        Call this periodically (e.g., every 500ms) to enable auto-translation.
        
        Returns:
            TranslationOutput if auto-translated, None otherwise
        """
        if not self._state.is_active:
            return None
        
        if not self.config.enable_auto_translate:
            return None
        
        # Only auto-translate if we have gestures and are inactive
        if len(self.buffer.get_sequence()) > 0 and self.is_inactive():
            return self.translate(TranslationTrigger.TIMEOUT)
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        buffer_stats = self.buffer.get_statistics()
        return {
            'mode': self._state.mode.value,
            'is_active': self._state.is_active,
            'frames_processed': self._frames_processed,
            'gestures_recognized': self._state.gestures_recognized,
            'sequence_length': buffer_stats['sequence_length'],
            'time_since_last_gesture': buffer_stats['time_since_last'],
            'is_inactive': buffer_stats['is_inactive'],
            'buffer_state': buffer_stats['state']
        }
    
    # === Text-to-Sign (Reverse Direction) ===
    
    def text_to_sign(self, text: str) -> TextToSignMapper.Result:
        """Convert text to sign language representation.
        
        Args:
            text: English text to convert
            
        Returns:
            Result with gesture sequence for display
        """
        return self.text_to_sign_mapper.map_text(text)
    
    def get_available_sentences(self) -> List[SentenceMapping]:
        """Get all predefined sentences (for text-to-sign suggestions)."""
        return self.sentence_mapper.get_all_sentences()
    
    def get_word_gestures(self) -> List[GestureDefinition]:
        """Get all word-level gestures."""
        return self.sentence_mapper.get_word_gestures()
    
    # === Internal Callbacks ===
    
    def _handle_gesture_added(self, gesture: DetectedGesture):
        """Handle when a gesture is added to the sequence."""
        self._state.gestures_recognized += 1
        
        if self._on_gesture_recognized:
            self._on_gesture_recognized(gesture)
        
        self._update_preview()
        self._notify_state_change()
    
    def _handle_sequence_updated(self, sequence: List[DetectedGesture]):
        """Handle sequence update."""
        self._update_preview()
    
    def _update_preview(self):
        """Update preview and partial matches."""
        preview = self.get_preview()
        partial_matches = self.get_partial_matches()
        
        self._state.preview_text = preview
        self._state.sequence_length = len(self.buffer.get_sequence())
        
        if self._on_preview_updated:
            self._on_preview_updated(preview, partial_matches)
    
    def _notify_state_change(self):
        """Notify about state change."""
        if self._on_state_changed:
            self._on_state_changed(self.get_state())


# === Vocabulary Information ===

def get_vocabulary_info() -> Dict:
    """Get information about the available vocabulary.
    
    Returns dictionary with:
    - stats: Counts of gestures and sentences
    - word_gestures: List of word-level signs
    - sentence_categories: Available sentence categories
    - limitations: Explicit scope acknowledgment
    """
    dictionary = get_dictionary()
    stats = dictionary.get_vocabulary_stats()
    
    return {
        'stats': stats,
        'word_gestures': [
            {
                'id': g.id,
                'symbol': g.symbol,
                'description': g.description,
                'emoji': g.emoji,
                'is_dynamic': g.is_dynamic
            }
            for g in dictionary.get_all_word_gestures()
        ],
        'sentence_categories': list(set(
            s.category for s in dictionary.get_all_sentences()
        )),
        'limitations': {
            'scope': 'Constrained vocabulary for practical communication',
            'not_full_asl': True,
            'grammar': 'English word order, not ASL grammar',
            'dynamic_gestures': 'Limited motion tracking support',
            'purpose': 'College major project demonstration'
        }
    }


def get_supported_sentences(category: Optional[str] = None) -> List[Dict]:
    """Get list of supported predefined sentences.
    
    Args:
        category: Optional filter by category (greeting, question, etc.)
        
    Returns:
        List of sentence info dictionaries
    """
    dictionary = get_dictionary()
    sentences = dictionary.get_all_sentences(category)
    
    return [
        {
            'id': s.id,
            'gesture_sequence': s.gesture_sequence,
            'english': s.english_sentence,
            'category': s.category,
            'notes': s.notes
        }
        for s in sentences
    ]
