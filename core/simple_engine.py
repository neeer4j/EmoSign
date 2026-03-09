"""
Simple Translation Engine - Unified gesture recognition and translation

This engine replaces the complex multi-mode pipeline with a simple, reliable system:
- Auto-detects whether input is a single letter, word, or sentence
- Uses ONLY predefined gestures/commands for reliability
- No separate modes - just works

PREDEFINED VOCABULARY:
- Letters A-Z (fingerspelling)
- Numbers 0-9
- Word gestures: HELLO, GOODBYE, THANK_YOU, PLEASE, YES, NO, HELP, etc.
- Sentence mappings: Common phrases recognized from gesture sequences
"""
import time
import json
import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Callable
from enum import Enum
from collections import deque

from config import DATA_DIR

# Path for custom gesture definitions
CUSTOM_GESTURES_PATH = os.path.join(DATA_DIR, "custom_gestures.json")


class OutputType(Enum):
    """Type of translation output."""
    LETTER = "letter"           # Single letter
    WORD = "word"               # Single word gesture
    FINGERSPELLED = "fingerspelled"  # Word from letters
    SENTENCE = "sentence"       # Predefined sentence from gesture sequence


@dataclass
class GestureEvent:
    """A detected gesture event."""
    gesture: str              # Gesture name/label
    confidence: float         # Detection confidence
    timestamp: float          # When detected
    is_word_level: bool = False  # True for word gestures like HELLO


@dataclass
class TranslationResult:
    """Result of translation."""
    text: str                           # Translated text
    output_type: OutputType             # How it was generated
    gestures: List[str] = field(default_factory=list)  # Gesture sequence
    confidence: float = 0.0             # Average confidence
    is_complete: bool = True            # Whether translation is final
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'type': self.output_type.value,
            'gestures': self.gestures,
            'confidence': self.confidence
        }


# =============================================================================
# PREDEFINED VOCABULARY
# =============================================================================

# Letters that can be fingerspelled
LETTERS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Numbers
NUMBERS = set("0123456789")

# Word-level gestures (single gesture = word)
WORD_GESTURES = {
    "HELLO": "Hello",
    "GOODBYE": "Goodbye", 
    "THANK_YOU": "Thank you",
    "PLEASE": "Please",
    "YES": "Yes",
    "NO": "No",
    "HELP": "Help",
    "SORRY": "Sorry",
    "LOVE": "Love",
    "FRIEND": "Friend",
    "FAMILY": "Family",
    "GOOD": "Good",
    "BAD": "Bad",
    "OK": "Okay",
    "STOP": "Stop",
    "GO": "Go",
    "WANT": "Want",
    "NEED": "Need",
    "LIKE": "Like",
    "UNDERSTAND": "Understand",
    "WATER": "Water",
    "FOOD": "Food",
    "HOME": "Home",
    "WORK": "Work",
    "SCHOOL": "School",
    "I": "I",
    "YOU": "You",
    "WE": "We",
    "THEY": "They",
    "HOW": "How",
    "WHAT": "What",
    "WHERE": "Where",
    "WHEN": "When",
    "WHY": "Why",
    "WHO": "Who",
    # --- Dynamic gestures ---
    "WAVE": "Hello (wave)",
    # CIRCLE intentionally omitted until detection is more reliable
}

# Gesture sequences that map to complete sentences
SENTENCE_MAPPINGS = [
    # Greetings
    (["HELLO"], "Hello!"),
    (["HELLO", "YOU"], "Hello, how are you?"),
    (["HELLO", "YOU", "HOW"], "Hello, how are you?"),
    (["GOODBYE"], "Goodbye!"),
    (["THANK_YOU"], "Thank you!"),
    (["YES", "THANK_YOU"], "Yes, thank you!"),
    (["NO", "THANK_YOU"], "No, thank you."),
    (["PLEASE", "HELP"], "Please help me."),
    (["HELP", "ME"], "Help me!"),
    (["I", "LOVE", "YOU"], "I love you."),
    (["I", "UNDERSTAND"], "I understand."),
    (["I", "NO", "UNDERSTAND"], "I don't understand."),
    (["SORRY"], "I'm sorry."),
    (["I", "SORRY"], "I'm sorry."),
    (["OK"], "Okay!"),
    (["GOOD"], "Good!"),
    (["GOOD", "YOU"], "How are you?"),
    (["I", "GOOD"], "I'm good."),
    (["I", "WANT", "WATER"], "I want water."),
    (["I", "WANT", "FOOD"], "I want food."),
    (["I", "WANT", "HELP"], "I want help."),
    (["I", "NEED", "HELP"], "I need help."),
    (["I", "GO", "HOME"], "I'm going home."),
    (["I", "GO", "WORK"], "I'm going to work."),
    (["I", "GO", "SCHOOL"], "I'm going to school."),
    (["WHAT", "YOU", "WANT"], "What do you want?"),
    (["WHERE", "YOU", "GO"], "Where are you going?"),
    (["HOW", "YOU"], "How are you?"),
    (["WHO", "YOU"], "Who are you?"),
    (["WHAT", "YOU", "NEED"], "What do you need?"),
    (["PLEASE", "STOP"], "Please stop."),
    (["STOP"], "Stop!"),
    (["YES"], "Yes."),
    (["NO"], "No."),
    (["FAMILY", "GOOD"], "My family is good."),
    (["FRIEND", "GOOD"], "My friend is good."),
    (["YOU", "GOOD"], "Are you okay?"),
    (["LIKE", "YOU"], "I like you."),
]


class SimpleTranslationEngine:
    """Simple, reliable translation engine with auto-detection.
    
    No modes to select - the engine figures out what you're signing:
    1. Recognizes word-level gestures (HELLO, THANK_YOU, etc.)
    2. Tries to match gesture sequences to predefined sentences
    3. Falls back to fingerspelling for unknown sequences
    
    Usage:
        engine = SimpleTranslationEngine()
        engine.start()
        
        # Feed gestures as they're detected
        engine.add_gesture("HELLO", 0.95)
        engine.add_gesture("H", 0.88)  # Letter
        
        # Get current translation (updates in real-time)
        result = engine.get_translation()
        
        # Or finalize when done
        result = engine.finalize()
    """
    
    def __init__(self, 
                 inactivity_timeout: float = 2.0,
                 stability_frames: int = 3,
                 min_confidence: float = 0.5):
        """Initialize the engine.
        
        Args:
            inactivity_timeout: Seconds of no input before auto-finalizing
            stability_frames: Consecutive detections needed to confirm gesture
            min_confidence: Minimum confidence to accept a gesture
        """
        self.inactivity_timeout = inactivity_timeout
        self.stability_frames = stability_frames
        self.min_confidence = min_confidence
        
        # State
        self._is_active = False
        self._gesture_buffer: List[GestureEvent] = []
        self._pending_gesture: Optional[str] = None
        self._pending_count: int = 0
        self._pending_confidence: float = 0.0
        self._last_gesture_time: float = 0.0
        self._start_time: float = 0.0
        
        # Duplicate filtering: a gesture registers ONCE and cannot repeat
        # until a DIFFERENT gesture is confirmed (or hand is removed).
        self._last_confirmed_gesture: Optional[str] = None
        self._gesture_is_held: bool = False  # True once confirmed, blocks repeats
        
        # Callbacks
        self._on_gesture_confirmed: Optional[Callable[[str, float], None]] = None
        self._on_translation_updated: Optional[Callable[[TranslationResult], None]] = None
    
    def set_on_gesture_confirmed(self, callback: Callable[[str, float], None]):
        """Set callback for when a gesture is confirmed."""
        self._on_gesture_confirmed = callback
    
    def set_on_translation_updated(self, callback: Callable[[TranslationResult], None]):
        """Set callback for translation updates."""
        self._on_translation_updated = callback
    
    def start(self):
        """Start the engine."""
        self.clear()
        self._is_active = True
        self._start_time = time.time()
    
    def stop(self):
        """Stop the engine."""
        self._is_active = False
    
    def clear(self):
        """Clear all state."""
        self._gesture_buffer.clear()
        self._pending_gesture = None
        self._pending_count = 0
        self._pending_confidence = 0.0
        self._last_gesture_time = 0.0
        self._last_confirmed_gesture = None
        self._gesture_is_held = False
    
    def reset_held(self):
        """Call when hand is removed from view.
        
        This allows the SAME gesture to be recognized again
        when the hand re-enters (since the user clearly lifted their hand).
        """
        self._gesture_is_held = False
        self._pending_gesture = None
        self._pending_count = 0

    def undo_last(self) -> bool:
        """Remove the most recently confirmed gesture from the buffer.

        Useful for a Delete/Backspace button in the UI.  Returns True if
        a gesture was removed, False if the buffer was already empty.
        After removal the translation callbacks are NOT automatically
        re-fired — call get_translation() and update the display yourself.
        """
        if not self._gesture_buffer:
            return False
        self._gesture_buffer.pop()
        # Reset the hold-lock to the new last gesture (or None)
        if self._gesture_buffer:
            self._last_confirmed_gesture = self._gesture_buffer[-1].gesture
        else:
            self._last_confirmed_gesture = None
            self._gesture_is_held = False
        return True
    
    def force_confirm(self, gesture: str, confidence: float):
        """Directly confirm a gesture, bypassing stability checking.
        
        Used by the capture-window approach where voting is done externally.
        The gesture is added straight to the buffer without requiring
        consecutive stable frames.
        """
        if not self._is_active:
            return
        gesture = gesture.upper().strip()
        self._confirm_gesture(gesture, confidence)
    
    def add_gesture(self, gesture: str, confidence: float) -> bool:
        """Add a detected gesture to the buffer.
        
        Gestures need to be confirmed through stability checking
        before being added to the translation buffer.
        
        Args:
            gesture: Gesture label (letter, number, or word gesture)
            confidence: Detection confidence (0-1)
            
        Returns:
            True if gesture was confirmed and added
        """
        if not self._is_active:
            return False
        
        if confidence < self.min_confidence:
            return False
        
        gesture = gesture.upper().strip()
        
        # ── Hold-blocking: if user is STILL showing the same gesture,
        #    don't add it again. They must show something DIFFERENT first
        #    (or remove their hand via reset_held).
        if self._gesture_is_held and gesture == self._last_confirmed_gesture:
            # Same gesture still being held — ignore
            return False
        
        # If a different gesture is coming in, release the hold-lock
        if gesture != self._last_confirmed_gesture:
            self._gesture_is_held = False
        
        # Stability checking: require N consecutive same-gesture frames
        if gesture == self._pending_gesture:
            self._pending_count += 1
            self._pending_confidence = max(self._pending_confidence, confidence)
        else:
            self._pending_gesture = gesture
            self._pending_count = 1
            self._pending_confidence = confidence
        
        # Check if gesture is stable enough to confirm
        if self._pending_count >= self.stability_frames:
            # Confirm this gesture
            self._confirm_gesture(gesture, self._pending_confidence)
            self._pending_gesture = None
            self._pending_count = 0
            
            # Lock: block this gesture from repeating until a different one appears
            self._last_confirmed_gesture = gesture
            self._gesture_is_held = True
            return True
        
        return False
    
    def _confirm_gesture(self, gesture: str, confidence: float):
        """Add a confirmed gesture to the buffer."""
        current_time = time.time()
        
        # Determine if this is a word-level gesture
        is_word = gesture in WORD_GESTURES or gesture.startswith("WORD_")
        
        # Clean up gesture name
        if gesture.startswith("WORD_"):
            gesture = gesture[5:]  # Remove WORD_ prefix
        
        event = GestureEvent(
            gesture=gesture,
            confidence=confidence,
            timestamp=current_time,
            is_word_level=is_word
        )
        
        self._gesture_buffer.append(event)
        self._last_gesture_time = current_time
        
        # Notify callback
        if self._on_gesture_confirmed:
            self._on_gesture_confirmed(gesture, confidence)
        
        # Update translation
        self._update_translation()
    
    def _update_translation(self):
        """Update and notify translation based on current buffer."""
        result = self.get_translation()
        if self._on_translation_updated and result:
            self._on_translation_updated(result)
    
    def check_timeout(self) -> bool:
        """Check if inactivity timeout has been reached.
        
        Returns:
            True if timeout reached and buffer has content
        """
        if not self._gesture_buffer:
            return False
        
        time_since_last = time.time() - self._last_gesture_time
        return time_since_last >= self.inactivity_timeout
    
    def get_translation(self) -> Optional[TranslationResult]:
        """Get current translation (preview).
        
        Returns the best translation for the current gesture buffer.
        """
        if not self._gesture_buffer:
            return None
        
        gestures = [e.gesture for e in self._gesture_buffer]
        avg_confidence = sum(e.confidence for e in self._gesture_buffer) / len(self._gesture_buffer)
        
        # Try to match a predefined sentence
        sentence_result = self._try_sentence_match(gestures)
        if sentence_result:
            return TranslationResult(
                text=sentence_result,
                output_type=OutputType.SENTENCE,
                gestures=gestures,
                confidence=avg_confidence,
                is_complete=True
            )
        
        # Check if all gestures are word-level
        all_words = all(e.is_word_level for e in self._gesture_buffer)
        if all_words and len(gestures) == 1:
            word = WORD_GESTURES.get(gestures[0], gestures[0])
            return TranslationResult(
                text=word,
                output_type=OutputType.WORD,
                gestures=gestures,
                confidence=avg_confidence,
                is_complete=True
            )
        
        # Check if all letters - fingerspelling
        all_letters = all(g in LETTERS or g in NUMBERS for g in gestures)
        if all_letters:
            text = ''.join(gestures)
            return TranslationResult(
                text=text,
                output_type=OutputType.FINGERSPELLED,
                gestures=gestures,
                confidence=avg_confidence,
                is_complete=True
            )
        
        # Mixed content - try to interpret
        return self._interpret_mixed(gestures, avg_confidence)
    
    def _try_sentence_match(self, gestures: List[str]) -> Optional[str]:
        """Try to match gesture sequence to a predefined sentence."""
        for pattern, sentence in SENTENCE_MAPPINGS:
            if len(pattern) == len(gestures):
                if all(p == g or (p.startswith("*") and g) for p, g in zip(pattern, gestures)):
                    return sentence
        return None
    
    def _try_partial_match(self, gestures: List[str]) -> List[Tuple[List[str], str]]:
        """Get sentences that start with the current gesture sequence."""
        matches = []
        for pattern, sentence in SENTENCE_MAPPINGS:
            if len(pattern) > len(gestures):
                if all(p == g for p, g in zip(pattern[:len(gestures)], gestures)):
                    matches.append((pattern, sentence))
        return matches
    
    def _interpret_mixed(self, gestures: List[str], confidence: float) -> TranslationResult:
        """Interpret a mixed sequence of words and letters."""
        result_parts = []
        letter_buffer = []
        
        for g in gestures:
            if g in WORD_GESTURES:
                # Flush letter buffer
                if letter_buffer:
                    result_parts.append(''.join(letter_buffer))
                    letter_buffer = []
                # Add word
                result_parts.append(WORD_GESTURES[g])
            elif g in LETTERS or g in NUMBERS:
                letter_buffer.append(g)
            else:
                # Unknown gesture - try as word
                if letter_buffer:
                    result_parts.append(''.join(letter_buffer))
                    letter_buffer = []
                result_parts.append(g)
        
        # Flush remaining letters
        if letter_buffer:
            result_parts.append(''.join(letter_buffer))
        
        text = ' '.join(result_parts)
        return TranslationResult(
            text=text,
            output_type=OutputType.FINGERSPELLED,
            gestures=gestures,
            confidence=confidence,
            is_complete=True
        )
    
    def finalize(self) -> Optional[TranslationResult]:
        """Finalize and return the translation.
        
        Returns the final translation WITHOUT clearing the buffer.
        Call clear() explicitly afterwards if you want to reset.
        """
        return self.get_translation()
    
    def get_preview(self) -> str:
        """Get a preview of current gestures."""
        if not self._gesture_buffer:
            return ""
        return " ".join(e.gesture for e in self._gesture_buffer)
    
    def get_partial_matches(self) -> List[str]:
        """Get possible sentence completions for current sequence."""
        if not self._gesture_buffer:
            return []
        gestures = [e.gesture for e in self._gesture_buffer]
        matches = self._try_partial_match(gestures)
        return [sentence for _, sentence in matches[:3]]  # Top 3 hints
    
    def get_gesture_count(self) -> int:
        """Get number of gestures in buffer."""
        return len(self._gesture_buffer)
    
    def is_active(self) -> bool:
        """Check if engine is active."""
        return self._is_active


# =============================================================================
# PREDEFINED GESTURE REGISTRY
# =============================================================================

def get_all_predefined_gestures() -> Dict[str, str]:
    """Get all predefined gestures with descriptions."""
    gestures = {}
    
    # Letters
    for letter in LETTERS:
        gestures[letter] = f"Letter {letter}"
    
    # Numbers
    for num in NUMBERS:
        gestures[num] = f"Number {num}"
    
    # Word gestures
    for gesture, word in WORD_GESTURES.items():
        gestures[gesture] = f"Word: {word}"
    
    return gestures


def load_custom_gestures() -> Dict[str, str]:
    """Load custom gestures from JSON file.
    
    Returns:
        Dict mapping gesture_id -> display_name
    """
    if not os.path.exists(CUSTOM_GESTURES_PATH):
        return {}
    try:
        with open(CUSTOM_GESTURES_PATH, 'r') as f:
            data = json.load(f)
        return data.get('gestures', {})
    except Exception:
        return {}


def save_custom_gestures(gestures: Dict[str, str]):
    """Save custom gestures to JSON file.
    
    Args:
        gestures: Dict mapping gesture_id -> display_name
    """
    os.makedirs(os.path.dirname(CUSTOM_GESTURES_PATH), exist_ok=True)
    with open(CUSTOM_GESTURES_PATH, 'w') as f:
        json.dump({'gestures': gestures}, f, indent=2)


def add_custom_gesture(gesture_name: str) -> Tuple[str, str]:
    """Add a new custom gesture.
    
    Args:
        gesture_name: Human-readable name for the gesture
        
    Returns:
        Tuple of (gesture_id, display_name)
        
    Raises:
        ValueError: If name conflicts with an existing gesture
    """
    gesture_id = gesture_name.upper().strip().replace(' ', '_')
    display_name = gesture_name.strip()
    
    if not gesture_id:
        raise ValueError("Gesture name cannot be empty.")
    
    # Check for conflicts with built-in gestures
    if gesture_id in LETTERS or gesture_id in NUMBERS:
        raise ValueError(f"'{gesture_name}' conflicts with a built-in letter/number.")
    if gesture_id in WORD_GESTURES:
        raise ValueError(f"'{gesture_name}' conflicts with a built-in word gesture.")
    
    # Load existing custom gestures
    custom = load_custom_gestures()
    if gesture_id in custom:
        raise ValueError(f"Custom gesture '{gesture_name}' already exists.")
    
    # Save
    custom[gesture_id] = display_name
    save_custom_gestures(custom)
    
    # Also register in WORD_GESTURES so the engine recognizes it
    WORD_GESTURES[gesture_id] = display_name
    
    return gesture_id, display_name


def remove_custom_gesture(gesture_id: str):
    """Remove a custom gesture.
    
    Args:
        gesture_id: ID of the gesture to remove
    """
    custom = load_custom_gestures()
    if gesture_id in custom:
        del custom[gesture_id]
        save_custom_gestures(custom)
        # Also remove from WORD_GESTURES if present
        WORD_GESTURES.pop(gesture_id, None)


def _register_custom_gestures():
    """Load and register all custom gestures into WORD_GESTURES at startup."""
    custom = load_custom_gestures()
    for gesture_id, display_name in custom.items():
        if gesture_id not in WORD_GESTURES:
            WORD_GESTURES[gesture_id] = display_name


# Register custom gestures when module loads
_register_custom_gestures()


def get_trainable_gestures() -> List[Tuple[str, str, str]]:
    """Get list of gestures that can be trained.
    
    Returns list of (gesture_id, display_name, category) tuples.
    """
    trainable = []
    
    # Letters
    for letter in sorted(LETTERS):
        trainable.append((letter, letter, "letter"))
    
    # Numbers
    for num in "0123456789":
        trainable.append((num, num, "number"))
    
    # Key word gestures
    priority_words = ["HELLO", "GOODBYE", "THANK_YOU", "PLEASE", "YES", "NO", 
                      "HELP", "SORRY", "I", "YOU", "GOOD", "OK", "STOP"]
    for gesture in priority_words:
        if gesture in WORD_GESTURES:
            trainable.append((gesture, WORD_GESTURES[gesture], "word"))
    
    # Custom gestures
    custom = load_custom_gestures()
    for gesture_id, display_name in sorted(custom.items()):
        trainable.append((gesture_id, display_name, "custom"))
    
    return trainable
