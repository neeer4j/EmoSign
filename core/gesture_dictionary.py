"""
Gesture Dictionary - Extensible definitions for gestures and sentences

This module provides a centralized, extensible dictionary of:
- Recognized gestures (letters, numbers, word-level signs)
- Predefined sentence mappings (gesture sequences → English sentences)
- Text-to-sign reverse mappings

Design Principles:
- All definitions are data-driven (easily add new gestures/sentences)
- Clear separation between gesture recognition and semantic meaning
- Explicit scope acknowledgment (controlled vocabulary, not full ASL)

LIMITATIONS ACKNOWLEDGMENT:
This system uses a constrained vocabulary approach for reliable communication.
It does NOT attempt full ASL grammar recognition or linguistic translation.
The goal is practical, real-time communication within defined boundaries.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import json
import os


class GestureCategory(Enum):
    """Categories of recognized gestures."""
    LETTER = "letter"           # A-Z fingerspelling
    NUMBER = "number"           # 0-9
    WORD = "word"               # Word-level signs (HELLO, THANK_YOU, etc.)
    CONTROL = "control"         # Space, backspace, enter
    COMPOUND = "compound"       # Multi-sign concepts


@dataclass
class GestureDefinition:
    """Definition of a single recognizable gesture.
    
    Attributes:
        id: Unique identifier (e.g., "LETTER_A", "WORD_HELLO")
        symbol: Display symbol/text (e.g., "A", "👋 Hello")
        category: Type of gesture
        aliases: Alternative detection labels that map to this gesture
        is_dynamic: Whether gesture requires motion detection
        description: Human-readable description of how to perform
        hand_shape: Description of hand configuration
        movement: Description of required movement (if dynamic)
    """
    id: str
    symbol: str
    category: GestureCategory
    aliases: List[str] = field(default_factory=list)
    is_dynamic: bool = False
    description: str = ""
    hand_shape: str = ""
    movement: str = ""
    emoji: str = ""
    
    def matches(self, label: str) -> bool:
        """Check if a detected label matches this gesture."""
        label_upper = label.upper()
        if self.id.upper() == label_upper:
            return True
        if self.symbol.upper() == label_upper:
            return True
        return any(alias.upper() == label_upper for alias in self.aliases)


@dataclass 
class SentenceMapping:
    """Maps a gesture sequence to a predefined English sentence.
    
    Attributes:
        id: Unique identifier for this mapping
        gesture_sequence: Ordered list of gesture IDs that trigger this sentence
        english_sentence: The English sentence output
        category: Semantic category (greeting, question, response, etc.)
        notes: Usage notes or context
        bidirectional: Whether this can be used for text-to-sign
    """
    id: str
    gesture_sequence: List[str]
    english_sentence: str
    category: str = "general"
    notes: str = ""
    bidirectional: bool = True
    
    def matches_sequence(self, sequence: List[str]) -> bool:
        """Check if a gesture sequence matches this mapping."""
        if len(sequence) != len(self.gesture_sequence):
            return False
        return all(
            seq.upper() == expected.upper() 
            for seq, expected in zip(sequence, self.gesture_sequence)
        )
    
    def starts_with(self, partial_sequence: List[str]) -> bool:
        """Check if this mapping starts with the given partial sequence."""
        if len(partial_sequence) > len(self.gesture_sequence):
            return False
        return all(
            seq.upper() == expected.upper()
            for seq, expected in zip(partial_sequence, self.gesture_sequence)
        )


class GestureDictionary:
    """Central dictionary of all gestures and sentence mappings.
    
    This class provides:
    - Registration and lookup of gesture definitions
    - Predefined sentence mappings for common phrases
    - Text-to-sign reverse lookup
    - Extensibility for adding new gestures/sentences
    
    Usage:
        dictionary = GestureDictionary()
        
        # Look up a gesture
        gesture = dictionary.get_gesture("A")
        
        # Find sentence for gesture sequence
        sentence = dictionary.find_sentence(["HELLO", "YOU", "OK"])
        
        # Reverse: text to gesture sequence
        gestures = dictionary.text_to_gestures("Hello, how are you?")
    """
    
    def __init__(self):
        self._gestures: Dict[str, GestureDefinition] = {}
        self._alias_map: Dict[str, str] = {}  # alias -> gesture_id
        self._sentences: Dict[str, SentenceMapping] = {}
        self._text_to_sentence: Dict[str, str] = {}  # normalized text -> sentence_id
        
        self._load_default_gestures()
        self._load_default_sentences()
    
    def _load_default_gestures(self):
        """Load built-in gesture definitions."""
        
        # === LETTERS A-Z ===
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            is_dynamic = letter in ['J', 'Z']  # J and Z require motion
            self.register_gesture(GestureDefinition(
                id=f"LETTER_{letter}",
                symbol=letter,
                category=GestureCategory.LETTER,
                aliases=[letter, letter.lower()],
                is_dynamic=is_dynamic,
                description=f"ASL letter {letter}"
            ))
        
        # === NUMBERS 0-9 ===
        number_words = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 
                        'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE']
        for i, word in enumerate(number_words):
            self.register_gesture(GestureDefinition(
                id=f"NUMBER_{i}",
                symbol=str(i),
                category=GestureCategory.NUMBER,
                aliases=[str(i), word, word.lower()],
                description=f"Number {i}"
            ))
        
        # === WORD-LEVEL SIGNS ===
        # These are the core vocabulary for sentence-level communication
        word_signs = [
            # Greetings
            GestureDefinition(
                id="WORD_HELLO",
                symbol="HELLO",
                category=GestureCategory.WORD,
                aliases=["hello", "hi", "wave", "WAVE"],
                is_dynamic=True,
                description="Open hand wave near forehead",
                hand_shape="Open palm, fingers together",
                movement="Wave side to side",
                emoji="👋"
            ),
            GestureDefinition(
                id="WORD_GOODBYE",
                symbol="GOODBYE",
                category=GestureCategory.WORD,
                aliases=["goodbye", "bye", "BYE"],
                is_dynamic=True,
                description="Open hand wave",
                emoji="👋"
            ),
            
            # Pronouns
            GestureDefinition(
                id="WORD_I",
                symbol="I",
                category=GestureCategory.WORD,
                aliases=["me", "I_POINT", "SELF"],
                description="Point to self (chest)",
                hand_shape="Index finger pointing",
                emoji="👆"
            ),
            GestureDefinition(
                id="WORD_YOU",
                symbol="YOU",
                category=GestureCategory.WORD,
                aliases=["you", "YOU_POINT"],
                description="Point forward to other person",
                hand_shape="Index finger pointing forward",
                emoji="👉"
            ),
            GestureDefinition(
                id="WORD_WE",
                symbol="WE",
                category=GestureCategory.WORD,
                aliases=["we", "us"],
                description="Point between self and other",
                emoji="👥"
            ),
            
            # Common responses
            GestureDefinition(
                id="WORD_YES",
                symbol="YES",
                category=GestureCategory.WORD,
                aliases=["yes", "thumbs_up", "THUMBS_UP", "OK", "ok"],
                description="Fist nodding (like a head nod)",
                hand_shape="Closed fist",
                movement="Nod up and down",
                emoji="👍"
            ),
            GestureDefinition(
                id="WORD_NO",
                symbol="NO",
                category=GestureCategory.WORD,
                aliases=["no", "thumbs_down", "THUMBS_DOWN"],
                description="Index and middle finger tap thumb",
                emoji="👎"
            ),
            
            # Courtesy
            GestureDefinition(
                id="WORD_PLEASE",
                symbol="PLEASE",
                category=GestureCategory.WORD,
                aliases=["please", "pls"],
                is_dynamic=True,
                description="Flat hand circles on chest",
                hand_shape="Open palm on chest",
                movement="Circular motion",
                emoji="🙏"
            ),
            GestureDefinition(
                id="WORD_THANK_YOU",
                symbol="THANK_YOU",
                category=GestureCategory.WORD,
                aliases=["thank_you", "thanks", "THANKS", "thankyou"],
                is_dynamic=True,
                description="Flat hand from chin forward",
                hand_shape="Flat hand at chin",
                movement="Move forward and down",
                emoji="🙏"
            ),
            GestureDefinition(
                id="WORD_SORRY",
                symbol="SORRY",
                category=GestureCategory.WORD,
                aliases=["sorry", "apologize"],
                is_dynamic=True,
                description="Fist circles on chest",
                hand_shape="Closed fist on chest",
                movement="Circular motion",
                emoji="🙇"
            ),
            
            # Questions
            GestureDefinition(
                id="WORD_WHAT",
                symbol="WHAT",
                category=GestureCategory.WORD,
                aliases=["what", "WHAT_QUESTION"],
                description="Palms up, shake slightly",
                hand_shape="Open palms facing up",
                movement="Small shake",
                emoji="❓"
            ),
            GestureDefinition(
                id="WORD_WHERE",
                symbol="WHERE",
                category=GestureCategory.WORD,
                aliases=["where"],
                description="Index finger wags side to side",
                hand_shape="Pointing index",
                movement="Wag side to side",
                emoji="📍"
            ),
            GestureDefinition(
                id="WORD_HOW",
                symbol="HOW",
                category=GestureCategory.WORD,
                aliases=["how"],
                description="Backs of hands together, roll forward",
                emoji="🤔"
            ),
            GestureDefinition(
                id="WORD_WHY",
                symbol="WHY",
                category=GestureCategory.WORD,
                aliases=["why"],
                description="Touch forehead, pull away to Y handshape",
                emoji="❔"
            ),
            GestureDefinition(
                id="WORD_WHEN",
                symbol="WHEN",
                category=GestureCategory.WORD,
                aliases=["when"],
                description="Index fingers circle each other",
                emoji="🕐"
            ),
            
            # Common verbs
            GestureDefinition(
                id="WORD_WANT",
                symbol="WANT",
                category=GestureCategory.WORD,
                aliases=["want", "need"],
                is_dynamic=True,
                description="Claw hands pull toward body",
                emoji="🙋"
            ),
            GestureDefinition(
                id="WORD_HELP",
                symbol="HELP",
                category=GestureCategory.WORD,
                aliases=["help", "assist"],
                is_dynamic=True,
                description="Thumbs-up on flat palm, lift up",
                emoji="🆘"
            ),
            GestureDefinition(
                id="WORD_STOP",
                symbol="STOP",
                category=GestureCategory.WORD,
                aliases=["stop", "STOP_HAND", "halt"],
                description="Flat hand chops into other palm",
                hand_shape="Flat hand (stop gesture)",
                emoji="✋"
            ),
            GestureDefinition(
                id="WORD_GO",
                symbol="GO",
                category=GestureCategory.WORD,
                aliases=["go", "leave"],
                is_dynamic=True,
                description="Index fingers point and move forward",
                emoji="🚶"
            ),
            GestureDefinition(
                id="WORD_COME",
                symbol="COME",
                category=GestureCategory.WORD,
                aliases=["come", "come_here"],
                is_dynamic=True,
                description="Beckoning motion with index finger",
                emoji="🫴"
            ),
            GestureDefinition(
                id="WORD_LIKE",
                symbol="LIKE",
                category=GestureCategory.WORD,
                aliases=["like", "enjoy"],
                description="Middle finger and thumb pull from chest",
                emoji="❤️"
            ),
            GestureDefinition(
                id="WORD_LOVE",
                symbol="LOVE",
                category=GestureCategory.WORD,
                aliases=["love", "heart"],
                description="Cross arms over chest",
                emoji="❤️"
            ),
            GestureDefinition(
                id="WORD_UNDERSTAND",
                symbol="UNDERSTAND",
                category=GestureCategory.WORD,
                aliases=["understand", "get_it"],
                is_dynamic=True,
                description="Index finger flicks up near forehead",
                emoji="💡"
            ),
            GestureDefinition(
                id="WORD_KNOW",
                symbol="KNOW",
                category=GestureCategory.WORD,
                aliases=["know"],
                description="Fingertips tap forehead",
                emoji="🧠"
            ),
            GestureDefinition(
                id="WORD_DONT_KNOW",
                symbol="DONT_KNOW",
                category=GestureCategory.WORD,
                aliases=["dont_know", "idk", "dunno"],
                is_dynamic=True,
                description="Fingertips at forehead, flick away",
                emoji="🤷"
            ),
            GestureDefinition(
                id="WORD_WAIT",
                symbol="WAIT",
                category=GestureCategory.WORD,
                aliases=["wait", "hold_on"],
                description="Wiggle fingers of both hands",
                emoji="⏳"
            ),
            
            # Common nouns
            GestureDefinition(
                id="WORD_NAME",
                symbol="NAME",
                category=GestureCategory.WORD,
                aliases=["name", "called"],
                description="H-hands tap each other",
                emoji="📛"
            ),
            GestureDefinition(
                id="WORD_WATER",
                symbol="WATER",
                category=GestureCategory.WORD,
                aliases=["water", "drink"],
                description="W-hand taps chin",
                emoji="💧"
            ),
            GestureDefinition(
                id="WORD_FOOD",
                symbol="FOOD",
                category=GestureCategory.WORD,
                aliases=["food", "eat", "hungry"],
                description="Flat O to mouth",
                emoji="🍽️"
            ),
            GestureDefinition(
                id="WORD_BATHROOM",
                symbol="BATHROOM",
                category=GestureCategory.WORD,
                aliases=["bathroom", "toilet", "restroom"],
                description="T-hand shakes",
                emoji="🚻"
            ),
            GestureDefinition(
                id="WORD_HOME",
                symbol="HOME",
                category=GestureCategory.WORD,
                aliases=["home", "house"],
                description="Flat O at cheek moves to chin",
                emoji="🏠"
            ),
            GestureDefinition(
                id="WORD_WORK",
                symbol="WORK",
                category=GestureCategory.WORD,
                aliases=["work", "job"],
                is_dynamic=True,
                description="Fists tap on top of each other",
                emoji="💼"
            ),
            
            # Adjectives/States
            GestureDefinition(
                id="WORD_GOOD",
                symbol="GOOD",
                category=GestureCategory.WORD,
                aliases=["good", "fine", "well"],
                description="Flat hand from chin forward",
                emoji="👍"
            ),
            GestureDefinition(
                id="WORD_BAD",
                symbol="BAD",
                category=GestureCategory.WORD,
                aliases=["bad", "wrong"],
                description="Flat hand from chin, turn down",
                emoji="👎"
            ),
            GestureDefinition(
                id="WORD_HAPPY",
                symbol="HAPPY",
                category=GestureCategory.WORD,
                aliases=["happy", "glad"],
                is_dynamic=True,
                description="Flat hands brush up on chest",
                emoji="😊"
            ),
            GestureDefinition(
                id="WORD_SAD",
                symbol="SAD",
                category=GestureCategory.WORD,
                aliases=["sad", "unhappy"],
                is_dynamic=True,
                description="Open hands move down face",
                emoji="😢"
            ),
            GestureDefinition(
                id="WORD_TIRED",
                symbol="TIRED",
                category=GestureCategory.WORD,
                aliases=["tired", "exhausted"],
                description="Bent hands drop on chest",
                emoji="😴"
            ),
            GestureDefinition(
                id="WORD_SICK",
                symbol="SICK",
                category=GestureCategory.WORD,
                aliases=["sick", "ill"],
                description="Middle fingers on forehead and stomach",
                emoji="🤒"
            ),
            
            # Time
            GestureDefinition(
                id="WORD_NOW",
                symbol="NOW",
                category=GestureCategory.WORD,
                aliases=["now", "today"],
                description="Y-hands drop in front of body",
                emoji="📅"
            ),
            GestureDefinition(
                id="WORD_LATER",
                symbol="LATER",
                category=GestureCategory.WORD,
                aliases=["later", "after"],
                is_dynamic=True,
                description="L-hand twists forward",
                emoji="🕐"
            ),
            GestureDefinition(
                id="WORD_BEFORE",
                symbol="BEFORE",
                category=GestureCategory.WORD,
                aliases=["before", "ago"],
                description="Hand moves backward",
                emoji="⏪"
            ),
            
            # Special compound
            GestureDefinition(
                id="WORD_I_LOVE_YOU",
                symbol="I_LOVE_YOU",
                category=GestureCategory.COMPOUND,
                aliases=["i_love_you", "ily", "ILY"],
                description="ILY handshape (thumb, index, pinky extended)",
                hand_shape="Thumb, index, and pinky extended",
                emoji="🤟"
            ),
        ]
        
        for gesture in word_signs:
            self.register_gesture(gesture)
        
        # === CONTROL GESTURES ===
        controls = [
            GestureDefinition(
                id="CTRL_SPACE",
                symbol=" ",
                category=GestureCategory.CONTROL,
                aliases=["space", "SPACE", "_", "pause"],
                description="Word separator"
            ),
            GestureDefinition(
                id="CTRL_BACKSPACE",
                symbol="⌫",
                category=GestureCategory.CONTROL,
                aliases=["backspace", "delete", "back"],
                description="Delete last"
            ),
        ]
        
        for ctrl in controls:
            self.register_gesture(ctrl)
    
    def _load_default_sentences(self):
        """Load predefined gesture sequence → sentence mappings."""
        
        # These are the core sentence mappings for practical communication
        sentences = [
            # === GREETINGS ===
            SentenceMapping(
                id="GREET_HELLO_HOW_ARE_YOU",
                gesture_sequence=["HELLO", "YOU", "HOW"],
                english_sentence="Hello, how are you?",
                category="greeting"
            ),
            SentenceMapping(
                id="GREET_HELLO_HOW_ARE_YOU_2",
                gesture_sequence=["HELLO", "HOW", "YOU"],
                english_sentence="Hello, how are you?",
                category="greeting"
            ),
            SentenceMapping(
                id="GREET_SIMPLE_HELLO",
                gesture_sequence=["HELLO"],
                english_sentence="Hello!",
                category="greeting"
            ),
            SentenceMapping(
                id="GREET_GOODBYE",
                gesture_sequence=["GOODBYE"],
                english_sentence="Goodbye!",
                category="greeting"
            ),
            SentenceMapping(
                id="GREET_NICE_MEET_YOU",
                gesture_sequence=["GOOD", "MEET", "YOU"],
                english_sentence="Nice to meet you.",
                category="greeting"
            ),
            SentenceMapping(
                id="GREET_GOOD_MORNING",
                gesture_sequence=["GOOD", "MORNING"],
                english_sentence="Good morning!",
                category="greeting"
            ),
            
            # === RESPONSES ===
            SentenceMapping(
                id="RESP_I_GOOD",
                gesture_sequence=["I", "GOOD"],
                english_sentence="I'm good.",
                category="response"
            ),
            SentenceMapping(
                id="RESP_I_FINE",
                gesture_sequence=["I", "FINE"],
                english_sentence="I'm fine.",
                category="response"
            ),
            SentenceMapping(
                id="RESP_I_OK",
                gesture_sequence=["I", "OK"],
                english_sentence="I'm okay.",
                category="response"
            ),
            SentenceMapping(
                id="RESP_YES",
                gesture_sequence=["YES"],
                english_sentence="Yes.",
                category="response"
            ),
            SentenceMapping(
                id="RESP_NO",
                gesture_sequence=["NO"],
                english_sentence="No.",
                category="response"
            ),
            SentenceMapping(
                id="RESP_THANK_YOU",
                gesture_sequence=["THANK_YOU"],
                english_sentence="Thank you!",
                category="response"
            ),
            SentenceMapping(
                id="RESP_YOURE_WELCOME",
                gesture_sequence=["YOU", "WELCOME"],
                english_sentence="You're welcome.",
                category="response"
            ),
            SentenceMapping(
                id="RESP_SORRY",
                gesture_sequence=["SORRY"],
                english_sentence="I'm sorry.",
                category="response"
            ),
            SentenceMapping(
                id="RESP_NO_PROBLEM",
                gesture_sequence=["NO", "PROBLEM"],
                english_sentence="No problem.",
                category="response"
            ),
            
            # === QUESTIONS ===
            SentenceMapping(
                id="Q_WHAT_YOUR_NAME",
                gesture_sequence=["WHAT", "YOUR", "NAME"],
                english_sentence="What is your name?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WHAT_YOUR_NAME_2",
                gesture_sequence=["YOUR", "NAME", "WHAT"],
                english_sentence="What is your name?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WHERE_BATHROOM",
                gesture_sequence=["WHERE", "BATHROOM"],
                english_sentence="Where is the bathroom?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WHERE_BATHROOM_2",
                gesture_sequence=["BATHROOM", "WHERE"],
                english_sentence="Where is the bathroom?",
                category="question"
            ),
            SentenceMapping(
                id="Q_UNDERSTAND",
                gesture_sequence=["YOU", "UNDERSTAND"],
                english_sentence="Do you understand?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WHAT_TIME",
                gesture_sequence=["WHAT", "TIME"],
                english_sentence="What time is it?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WANT_HELP",
                gesture_sequence=["YOU", "WANT", "HELP"],
                english_sentence="Do you want help?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WHAT_WANT",
                gesture_sequence=["YOU", "WANT", "WHAT"],
                english_sentence="What do you want?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WHERE_GO",
                gesture_sequence=["WHERE", "GO"],
                english_sentence="Where are you going?",
                category="question"
            ),
            SentenceMapping(
                id="Q_WHERE_FROM",
                gesture_sequence=["YOU", "WHERE", "FROM"],
                english_sentence="Where are you from?",
                category="question"
            ),
            
            # === REQUESTS ===
            SentenceMapping(
                id="REQ_HELP_ME",
                gesture_sequence=["HELP", "I"],
                english_sentence="Please help me.",
                category="request"
            ),
            SentenceMapping(
                id="REQ_HELP_ME_2",
                gesture_sequence=["I", "NEED", "HELP"],
                english_sentence="I need help.",
                category="request"
            ),
            SentenceMapping(
                id="REQ_WAIT",
                gesture_sequence=["WAIT", "PLEASE"],
                english_sentence="Please wait.",
                category="request"
            ),
            SentenceMapping(
                id="REQ_WAIT_2",
                gesture_sequence=["PLEASE", "WAIT"],
                english_sentence="Please wait.",
                category="request"
            ),
            SentenceMapping(
                id="REQ_COME_HERE",
                gesture_sequence=["COME", "HERE"],
                english_sentence="Come here, please.",
                category="request"
            ),
            SentenceMapping(
                id="REQ_STOP",
                gesture_sequence=["STOP"],
                english_sentence="Stop!",
                category="request"
            ),
            SentenceMapping(
                id="REQ_SLOW_DOWN",
                gesture_sequence=["SLOW", "PLEASE"],
                english_sentence="Please slow down.",
                category="request"
            ),
            SentenceMapping(
                id="REQ_REPEAT",
                gesture_sequence=["AGAIN", "PLEASE"],
                english_sentence="Please repeat that.",
                category="request"
            ),
            
            # === STATEMENTS ===
            SentenceMapping(
                id="STMT_MY_NAME",
                gesture_sequence=["MY", "NAME"],
                english_sentence="My name is...",
                category="statement",
                notes="Follow with fingerspelled name"
            ),
            SentenceMapping(
                id="STMT_I_UNDERSTAND",
                gesture_sequence=["I", "UNDERSTAND"],
                english_sentence="I understand.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_DONT_UNDERSTAND",
                gesture_sequence=["I", "DONT_KNOW"],
                english_sentence="I don't understand.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_KNOW",
                gesture_sequence=["I", "KNOW"],
                english_sentence="I know.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_DONT_KNOW",
                gesture_sequence=["I", "KNOW", "NO"],
                english_sentence="I don't know.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_WANT",
                gesture_sequence=["I", "WANT"],
                english_sentence="I want...",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_NEED",
                gesture_sequence=["I", "NEED"],
                english_sentence="I need...",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_LIKE",
                gesture_sequence=["I", "LIKE"],
                english_sentence="I like...",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_LOVE_YOU",
                gesture_sequence=["I", "LOVE", "YOU"],
                english_sentence="I love you.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_ILY",
                gesture_sequence=["I_LOVE_YOU"],
                english_sentence="I love you.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_HAPPY",
                gesture_sequence=["I", "HAPPY"],
                english_sentence="I'm happy.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_SAD",
                gesture_sequence=["I", "SAD"],
                english_sentence="I'm sad.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_TIRED",
                gesture_sequence=["I", "TIRED"],
                english_sentence="I'm tired.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_HUNGRY",
                gesture_sequence=["I", "HUNGRY"],
                english_sentence="I'm hungry.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_I_GO_HOME",
                gesture_sequence=["I", "GO", "HOME"],
                english_sentence="I'm going home.",
                category="statement"
            ),
            SentenceMapping(
                id="STMT_SEE_LATER",
                gesture_sequence=["SEE", "YOU", "LATER"],
                english_sentence="See you later.",
                category="statement"
            ),
            
            # === EMERGENCY/IMPORTANT ===
            SentenceMapping(
                id="EMERG_HELP",
                gesture_sequence=["HELP"],
                english_sentence="I need help!",
                category="emergency"
            ),
            SentenceMapping(
                id="EMERG_SICK",
                gesture_sequence=["I", "SICK"],
                english_sentence="I'm sick.",
                category="emergency"
            ),
            SentenceMapping(
                id="EMERG_CALL",
                gesture_sequence=["CALL", "HELP"],
                english_sentence="Call for help!",
                category="emergency"
            ),
        ]
        
        for sentence in sentences:
            self.register_sentence(sentence)
    
    # === Public API ===
    
    def register_gesture(self, gesture: GestureDefinition):
        """Register a new gesture definition."""
        self._gestures[gesture.id.upper()] = gesture
        
        # Map all aliases
        for alias in gesture.aliases:
            self._alias_map[alias.upper()] = gesture.id.upper()
        
        # Also map the symbol
        self._alias_map[gesture.symbol.upper()] = gesture.id.upper()
    
    def register_sentence(self, sentence: SentenceMapping):
        """Register a new sentence mapping."""
        self._sentences[sentence.id] = sentence
        
        # Map normalized text for reverse lookup
        normalized = sentence.english_sentence.lower().strip().rstrip('.!?')
        self._text_to_sentence[normalized] = sentence.id
    
    def get_gesture(self, label: str) -> Optional[GestureDefinition]:
        """Look up gesture by ID, symbol, or alias."""
        upper = label.upper()
        
        # Direct lookup
        if upper in self._gestures:
            return self._gestures[upper]
        
        # Alias lookup
        if upper in self._alias_map:
            gesture_id = self._alias_map[upper]
            return self._gestures.get(gesture_id)
        
        return None
    
    def normalize_gesture(self, label: str) -> Optional[str]:
        """Convert any gesture label to its canonical ID."""
        upper = label.upper()
        
        if upper in self._gestures:
            return upper
        
        if upper in self._alias_map:
            return self._alias_map[upper]
        
        # Check if it's a letter
        if len(label) == 1 and label.isalpha():
            return f"LETTER_{label.upper()}"
        
        # Check if it's a number
        if label.isdigit():
            return f"NUMBER_{label}"
        
        return None
    
    def find_sentence(self, gesture_sequence: List[str]) -> Optional[SentenceMapping]:
        """Find a sentence mapping for a gesture sequence."""
        # Normalize the sequence
        normalized = []
        for g in gesture_sequence:
            norm = self.normalize_gesture(g)
            if norm:
                # Strip prefix for matching (WORD_HELLO -> HELLO)
                if norm.startswith("WORD_"):
                    normalized.append(norm[5:])
                elif norm.startswith("LETTER_"):
                    normalized.append(norm[7:])
                elif norm.startswith("NUMBER_"):
                    normalized.append(norm[7:])
                else:
                    normalized.append(norm)
            else:
                normalized.append(g.upper())
        
        # Find best match
        for sentence in self._sentences.values():
            if sentence.matches_sequence(normalized):
                return sentence
        
        return None
    
    def find_partial_matches(self, partial_sequence: List[str]) -> List[SentenceMapping]:
        """Find sentences that start with the given partial sequence."""
        normalized = []
        for g in partial_sequence:
            norm = self.normalize_gesture(g)
            if norm and norm.startswith("WORD_"):
                normalized.append(norm[5:])
            elif norm:
                normalized.append(norm)
            else:
                normalized.append(g.upper())
        
        matches = []
        for sentence in self._sentences.values():
            if sentence.starts_with(normalized):
                matches.append(sentence)
        
        return matches
    
    def text_to_gestures(self, text: str) -> Optional[Tuple[SentenceMapping, List[GestureDefinition]]]:
        """Convert text to gesture sequence for text-to-sign.
        
        Returns:
            Tuple of (SentenceMapping, list of GestureDefinition) or None
        """
        normalized = text.lower().strip().rstrip('.!?')
        
        # Look for exact sentence match
        if normalized in self._text_to_sentence:
            sentence_id = self._text_to_sentence[normalized]
            sentence = self._sentences[sentence_id]
            
            # Get gesture definitions
            gestures = []
            for gesture_name in sentence.gesture_sequence:
                gesture = self.get_gesture(gesture_name) or self.get_gesture(f"WORD_{gesture_name}")
                if gesture:
                    gestures.append(gesture)
            
            return (sentence, gestures)
        
        return None
    
    def get_all_sentences(self, category: Optional[str] = None) -> List[SentenceMapping]:
        """Get all sentence mappings, optionally filtered by category."""
        if category:
            return [s for s in self._sentences.values() if s.category == category]
        return list(self._sentences.values())
    
    def get_all_word_gestures(self) -> List[GestureDefinition]:
        """Get all word-level gestures (not letters/numbers)."""
        return [
            g for g in self._gestures.values()
            if g.category in [GestureCategory.WORD, GestureCategory.COMPOUND]
        ]
    
    def get_vocabulary_stats(self) -> Dict:
        """Get statistics about the vocabulary."""
        categories = {}
        for g in self._gestures.values():
            cat = g.category.value
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_gestures': len(self._gestures),
            'total_sentences': len(self._sentences),
            'by_category': categories,
            'sentence_categories': list(set(s.category for s in self._sentences.values()))
        }
    
    # === Persistence ===
    
    def export_to_json(self) -> Dict:
        """Export dictionary to JSON-serializable format."""
        return {
            'gestures': {
                gid: {
                    'symbol': g.symbol,
                    'category': g.category.value,
                    'aliases': g.aliases,
                    'is_dynamic': g.is_dynamic,
                    'description': g.description,
                    'emoji': g.emoji
                }
                for gid, g in self._gestures.items()
            },
            'sentences': {
                sid: {
                    'gesture_sequence': s.gesture_sequence,
                    'english_sentence': s.english_sentence,
                    'category': s.category,
                    'notes': s.notes
                }
                for sid, s in self._sentences.items()
            }
        }
    
    def save_custom(self, filepath: str):
        """Save custom additions to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.export_to_json(), f, indent=2)
    
    def load_custom(self, filepath: str):
        """Load custom gestures/sentences from a JSON file."""
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Load custom gestures
        for gid, gdata in data.get('gestures', {}).items():
            gesture = GestureDefinition(
                id=gid,
                symbol=gdata['symbol'],
                category=GestureCategory(gdata['category']),
                aliases=gdata.get('aliases', []),
                is_dynamic=gdata.get('is_dynamic', False),
                description=gdata.get('description', ''),
                emoji=gdata.get('emoji', '')
            )
            self.register_gesture(gesture)
        
        # Load custom sentences
        for sid, sdata in data.get('sentences', {}).items():
            sentence = SentenceMapping(
                id=sid,
                gesture_sequence=sdata['gesture_sequence'],
                english_sentence=sdata['english_sentence'],
                category=sdata.get('category', 'custom'),
                notes=sdata.get('notes', '')
            )
            self.register_sentence(sentence)


# Singleton instance
_dictionary_instance: Optional[GestureDictionary] = None

def get_dictionary() -> GestureDictionary:
    """Get the global gesture dictionary instance."""
    global _dictionary_instance
    if _dictionary_instance is None:
        _dictionary_instance = GestureDictionary()
    return _dictionary_instance
