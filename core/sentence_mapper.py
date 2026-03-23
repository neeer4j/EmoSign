"""
Sentence Mapper - Maps gesture sequences to English sentences

This module handles:
- Matching gesture sequences to predefined sentence mappings
- Falling back to fingerspelling for unmatched sequences
- Building readable English output from recognized gestures
- Providing partial match suggestions

Design Principles:
- Predefined mappings take priority over raw output
- Graceful fallback to fingerspelling
- Clear separation between recognition and mapping
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum

from .gesture_dictionary import (
    GestureDictionary, GestureDefinition, SentenceMapping,
    GestureCategory, get_dictionary
)
from .sequence_buffer import DetectedGesture


class OutputType(Enum):
    """Type of sentence output."""
    PREDEFINED = "predefined"      # Matched a predefined sentence
    FINGERSPELLED = "fingerspelled"  # Built from letters
    MIXED = "mixed"                # Combination of words and letters
    EMPTY = "empty"


@dataclass
class SentenceResult:
    """Result of sentence mapping.
    
    Attributes:
        text: The final English text output
        output_type: How the output was generated
        matched_mapping: The predefined mapping if matched
        gesture_count: Number of gestures processed
        word_count: Number of words in output
        confidence: Average confidence of gestures
        breakdown: How each gesture was interpreted
    """
    text: str
    output_type: OutputType
    matched_mapping: Optional[SentenceMapping] = None
    gesture_count: int = 0
    word_count: int = 0
    confidence: float = 0.0
    breakdown: List[Tuple[str, str]] = field(default_factory=list)  # (gesture_id, interpretation)
    
    @property
    def is_empty(self) -> bool:
        return self.output_type == OutputType.EMPTY or not self.text
    
    def __str__(self):
        return self.text


class SentenceMapper:
    """Maps gesture sequences to English sentences.
    
    This mapper:
    1. Checks if the sequence matches any predefined sentence
    2. Falls back to intelligent fingerspelling/word combination
    3. Provides partial match suggestions during input
    
    Usage:
        mapper = SentenceMapper()
        
        # Map a sequence
        result = mapper.map_sequence([gesture1, gesture2, ...])
        print(result.text)
        
        # Get partial matches (for UI hints)
        hints = mapper.get_partial_matches(partial_sequence)
    """
    
    def __init__(self, dictionary: Optional[GestureDictionary] = None):
        self.dictionary = dictionary or get_dictionary()
        
        # Abbreviation expansions for common patterns
        self._abbreviations = {
            'TY': 'Thank you',
            'TYS': 'Thank you so much',
            'NP': 'No problem',
            'PLZ': 'Please',
            'PLS': 'Please',
            'ILY': 'I love you',
            'OMG': 'Oh my god',
            'BTW': 'By the way',
            'IDK': "I don't know",
            'NVM': 'Never mind',
            'HI': 'Hi',
            'BYE': 'Bye',
            'OK': 'OK',
            'YES': 'Yes',
            'NO': 'No',
        }
    
    def map_sequence(self, gestures: List[DetectedGesture]) -> SentenceResult:
        """Map a gesture sequence to English text.
        
        Args:
            gestures: List of detected gestures in order
            
        Returns:
            SentenceResult with the English text and metadata
        """
        if not gestures:
            return SentenceResult(
                text="",
                output_type=OutputType.EMPTY,
                gesture_count=0,
                word_count=0
            )
        
        # Extract gesture IDs
        gesture_ids = [g.gesture_id for g in gestures]
        
        # Calculate average confidence
        avg_confidence = sum(g.confidence for g in gestures) / len(gestures)
        
        # Try to find a predefined sentence match
        mapping = self.dictionary.find_sentence(gesture_ids)
        
        if mapping:
            return SentenceResult(
                text=mapping.english_sentence,
                output_type=OutputType.PREDEFINED,
                matched_mapping=mapping,
                gesture_count=len(gestures),
                word_count=len(mapping.english_sentence.split()),
                confidence=avg_confidence,
                breakdown=[(g.gesture_id, "→ " + mapping.english_sentence) for g in gestures]
            )
        
        # No predefined match - build from individual gestures
        return self._build_from_gestures(gestures, avg_confidence)
    
    def _build_from_gestures(
        self,
        gestures: List[DetectedGesture],
        avg_confidence: float
    ) -> SentenceResult:
        """Build sentence from individual gestures."""
        parts = []
        breakdown = []
        current_word = []
        has_letters = False
        has_words = False
        
        for gesture in gestures:
            gid = gesture.gesture_id
            
            # Handle control gestures
            if gid == "CTRL_SPACE" or gid == "SPACE":
                if current_word:
                    word = self._finalize_word(current_word)
                    if word:
                        parts.append(word)
                    current_word = []
                continue
            
            if gid == "CTRL_BACKSPACE":
                # Delete last character or word
                if current_word:
                    current_word.pop()
                elif parts:
                    parts.pop()
                continue
            
            # Get gesture definition
            gesture_def = self.dictionary.get_gesture(gid)
            
            if gesture_def:
                if gesture_def.category == GestureCategory.LETTER:
                    # Single letter - add to current word buffer
                    letter = gesture_def.symbol
                    current_word.append(letter)
                    breakdown.append((gid, f"letter '{letter}'"))
                    has_letters = True
                    
                elif gesture_def.category == GestureCategory.NUMBER:
                    # Number - add to current word buffer
                    num = gesture_def.symbol
                    current_word.append(num)
                    breakdown.append((gid, f"number '{num}'"))
                    
                elif gesture_def.category in [GestureCategory.WORD, GestureCategory.COMPOUND]:
                    # Word-level sign - finalize any pending letters first
                    if current_word:
                        word = self._finalize_word(current_word)
                        if word:
                            parts.append(word)
                        current_word = []
                    
                    # Add the word
                    word_text = self._get_word_text(gesture_def)
                    parts.append(word_text)
                    breakdown.append((gid, f"word '{word_text}'"))
                    has_words = True
            else:
                # Unknown gesture - treat as raw letter if single char
                if len(gid) == 1:
                    current_word.append(gid)
                    breakdown.append((gid, f"letter '{gid}'"))
                    has_letters = True
                elif gid.startswith("LETTER_"):
                    letter = gid[7:]
                    current_word.append(letter)
                    breakdown.append((gid, f"letter '{letter}'"))
                    has_letters = True
                elif gid.startswith("WORD_"):
                    word = gid[5:].replace("_", " ").title()
                    if current_word:
                        finalized = self._finalize_word(current_word)
                        if finalized:
                            parts.append(finalized)
                        current_word = []
                    parts.append(word)
                    breakdown.append((gid, f"word '{word}'"))
                    has_words = True
        
        # Finalize any remaining letters
        if current_word:
            word = self._finalize_word(current_word)
            if word:
                parts.append(word)
        
        # Build final text
        text = " ".join(parts)
        text = self._clean_sentence(text)
        
        # Determine output type
        if has_letters and has_words:
            output_type = OutputType.MIXED
        elif has_letters:
            output_type = OutputType.FINGERSPELLED
        elif has_words:
            output_type = OutputType.MIXED
        else:
            output_type = OutputType.EMPTY
        
        return SentenceResult(
            text=text,
            output_type=output_type,
            gesture_count=len(gestures),
            word_count=len(text.split()) if text else 0,
            confidence=avg_confidence,
            breakdown=breakdown
        )
    
    def _finalize_word(self, letters: List[str]) -> str:
        """Finalize a word from accumulated letters."""
        if not letters:
            return ""
        
        raw_word = "".join(letters).upper()
        
        # Check for abbreviation
        if raw_word in self._abbreviations:
            return self._abbreviations[raw_word]
        
        # Check dictionary for word pattern
        word_match = self.dictionary.find_sentence([raw_word])
        if word_match:
            return word_match.english_sentence.rstrip('.!?')
        
        # Return as-is (capitalized appropriately)
        return raw_word.capitalize()
    
    def _get_word_text(self, gesture_def: GestureDefinition) -> str:
        """Get display text for a word-level gesture."""
        # Use symbol if it's readable
        symbol = gesture_def.symbol
        
        # Clean up symbol (remove underscores, proper case)
        text = symbol.replace("_", " ").title()
        
        return text
    
    def _clean_sentence(self, text: str) -> str:
        """Clean up the final sentence text."""
        if not text:
            return ""
        
        # Basic cleanup
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    def get_partial_matches(
        self,
        gestures: List[DetectedGesture]
    ) -> List[SentenceMapping]:
        """Get possible sentence completions for a partial sequence.
        
        Useful for showing hints to the user about what sentences
        they might be signing.
        """
        gesture_ids = [g.gesture_id for g in gestures]
        return self.dictionary.find_partial_matches(gesture_ids)
    
    def get_preview(self, gestures: List[DetectedGesture]) -> str:
        """Get a preview of the current gesture sequence.
        
        Shows what has been recognized so far, without final formatting.
        """
        if not gestures:
            return ""
        
        parts = []
        for gesture in gestures:
            gid = gesture.gesture_id
            
            gesture_def = self.dictionary.get_gesture(gid)
            
            if gesture_def:
                if gesture_def.category == GestureCategory.LETTER:
                    parts.append(gesture_def.symbol.lower())
                elif gesture_def.category == GestureCategory.NUMBER:
                    parts.append(gesture_def.symbol)
                elif gesture_def.category == GestureCategory.CONTROL:
                    if gid == "CTRL_SPACE":
                        parts.append(" ")
                else:
                    parts.append(f"[{gesture_def.symbol}]")
            else:
                parts.append(gid)
        
        return "".join(parts)
    
    def get_word_gestures(self) -> List[GestureDefinition]:
        """Get all available word-level gestures."""
        return self.dictionary.get_all_word_gestures()
    
    def get_all_sentences(self, category: Optional[str] = None) -> List[SentenceMapping]:
        """Get all predefined sentences, optionally by category."""
        return self.dictionary.get_all_sentences(category)


class TextToSignMapper:
    """Maps English text to gesture sequences for bidirectional communication.
    
    This allows non-signing users to enter text and see the corresponding
    sign representation.
    
    Usage:
        mapper = TextToSignMapper()
        result = mapper.map_text("Hello, how are you?")
        for gesture in result.gestures:
            display_gesture(gesture)
    """
    
    @dataclass
    class Result:
        """Result of text-to-sign mapping."""
        original_text: str
        gestures: List[GestureDefinition]
        matched_sentence: Optional[SentenceMapping] = None
        is_fingerspelled: bool = False
        display_text: str = ""
    
    def __init__(self, dictionary: Optional[GestureDictionary] = None):
        self.dictionary = dictionary or get_dictionary()
    
    def map_text(self, text: str) -> 'TextToSignMapper.Result':
        """Map text to a gesture sequence.
        
        Args:
            text: English text to convert
            
        Returns:
            Result with gesture sequence for display
        """
        if not text:
            return self.Result(
                original_text="",
                gestures=[],
                display_text=""
            )
        
        # Try exact sentence match first
        sentence_match = self.dictionary.text_to_gestures(text)
        
        if sentence_match:
            sentence, gestures = sentence_match
            return self.Result(
                original_text=text,
                gestures=gestures,
                matched_sentence=sentence,
                is_fingerspelled=False,
                display_text=" → ".join(g.symbol for g in gestures)
            )
        
        # Fall back to fingerspelling
        gestures = self._fingerspell(text)
        
        return self.Result(
            original_text=text,
            gestures=gestures,
            is_fingerspelled=True,
            display_text=" ".join(g.symbol for g in gestures)
        )
    
    def _fingerspell(self, text: str) -> List[GestureDefinition]:
        """Convert text to fingerspelled letters."""
        gestures = []
        
        for char in text.upper():
            if char.isalpha():
                gesture = self.dictionary.get_gesture(f"LETTER_{char}")
                if gesture:
                    gestures.append(gesture)
            elif char.isdigit():
                gesture = self.dictionary.get_gesture(f"NUMBER_{char}")
                if gesture:
                    gestures.append(gesture)
            elif char == ' ':
                gesture = self.dictionary.get_gesture("CTRL_SPACE")
                if gesture:
                    gestures.append(gesture)
        
        return gestures
    
    def get_available_sentences(self) -> List[SentenceMapping]:
        """Get all sentences that can be converted to signs."""
        return [
            s for s in self.dictionary.get_all_sentences()
            if s.bidirectional
        ]
