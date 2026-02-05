"""
Sign Visualizer - Display sign language representations for text-to-sign

This module provides visualization for the text-to-sign direction:
- Shows sequence of gestures for a given text
- Displays hand shape descriptions, movements
- Provides step-by-step sign instruction

Works with the interpretation engine to enable bidirectional communication.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Generator
import time

from .gesture_dictionary import (
    GestureDictionary, GestureDefinition, GestureCategory,
    get_dictionary
)
from .sentence_mapper import TextToSignMapper


@dataclass
class SignStep:
    """A single step in a sign sequence visualization.
    
    Attributes:
        gesture: The gesture definition
        display_text: What to show for this step
        instruction: How to perform this sign
        duration: Suggested display duration (seconds)
        is_fingerspell: Whether this is a fingerspelled letter
        animation_hint: Type of animation if applicable
    """
    gesture: GestureDefinition
    display_text: str
    instruction: str
    duration: float = 1.0
    is_fingerspell: bool = False
    animation_hint: str = ""  # "static", "wave", "circle", etc.
    
    @property
    def emoji(self) -> str:
        return self.gesture.emoji if self.gesture else ""
    
    @property
    def symbol(self) -> str:
        return self.gesture.symbol if self.gesture else ""


@dataclass
class SignVisualization:
    """Complete visualization for a text-to-sign translation.
    
    Attributes:
        original_text: The input English text
        steps: Ordered list of sign steps
        total_duration: Total suggested duration
        is_predefined: Whether matched a predefined sentence
        sentence_id: ID of matched sentence if predefined
    """
    original_text: str
    steps: List[SignStep] = field(default_factory=list)
    total_duration: float = 0.0
    is_predefined: bool = False
    sentence_id: Optional[str] = None
    
    def __len__(self):
        return len(self.steps)
    
    def __iter__(self):
        return iter(self.steps)
    
    @property
    def summary(self) -> str:
        """Get a text summary of the sign sequence."""
        return " → ".join(step.display_text for step in self.steps)


class SignVisualizer:
    """Creates visualizations for text-to-sign translations.
    
    This class takes text input and generates a step-by-step
    visualization of how to sign it.
    
    Usage:
        visualizer = SignVisualizer()
        vis = visualizer.create_visualization("Hello, how are you?")
        
        for step in vis:
            show_sign(step.display_text, step.instruction)
            wait(step.duration)
    """
    
    def __init__(self, dictionary: Optional[GestureDictionary] = None):
        self.dictionary = dictionary or get_dictionary()
        self.mapper = TextToSignMapper(self.dictionary)
        
        # Duration settings (seconds)
        self.word_sign_duration = 1.5
        self.letter_duration = 0.5
        self.space_duration = 0.3
    
    def create_visualization(self, text: str) -> SignVisualization:
        """Create a visualization for the given text.
        
        Args:
            text: English text to visualize as signs
            
        Returns:
            SignVisualization with step-by-step instructions
        """
        if not text:
            return SignVisualization(original_text="")
        
        # Get gesture sequence from mapper
        result = self.mapper.map_text(text)
        
        # Build visualization steps
        steps = []
        total_duration = 0.0
        
        for gesture in result.gestures:
            step = self._create_step(gesture)
            steps.append(step)
            total_duration += step.duration
        
        return SignVisualization(
            original_text=text,
            steps=steps,
            total_duration=total_duration,
            is_predefined=result.matched_sentence is not None,
            sentence_id=result.matched_sentence.id if result.matched_sentence else None
        )
    
    def _create_step(self, gesture: GestureDefinition) -> SignStep:
        """Create a visualization step for a gesture."""
        # Determine if fingerspelling
        is_fingerspell = gesture.category == GestureCategory.LETTER
        
        # Set duration based on type
        if gesture.category == GestureCategory.LETTER:
            duration = self.letter_duration
        elif gesture.category == GestureCategory.CONTROL:
            duration = self.space_duration
        else:
            duration = self.word_sign_duration
        
        # Build instruction
        instruction = self._build_instruction(gesture)
        
        # Determine animation hint
        animation_hint = "static"
        if gesture.is_dynamic:
            if "wave" in gesture.movement.lower():
                animation_hint = "wave"
            elif "circle" in gesture.movement.lower():
                animation_hint = "circle"
            elif "tap" in gesture.movement.lower():
                animation_hint = "tap"
            else:
                animation_hint = "dynamic"
        
        # Display text
        if gesture.category == GestureCategory.LETTER:
            display_text = gesture.symbol
        elif gesture.category == GestureCategory.CONTROL:
            display_text = "[SPACE]" if "SPACE" in gesture.id else gesture.symbol
        else:
            display_text = gesture.emoji + " " + gesture.symbol if gesture.emoji else gesture.symbol
        
        return SignStep(
            gesture=gesture,
            display_text=display_text,
            instruction=instruction,
            duration=duration,
            is_fingerspell=is_fingerspell,
            animation_hint=animation_hint
        )
    
    def _build_instruction(self, gesture: GestureDefinition) -> str:
        """Build human-readable instruction for a gesture."""
        parts = []
        
        # Add description
        if gesture.description:
            parts.append(gesture.description)
        
        # Add hand shape
        if gesture.hand_shape:
            parts.append(f"Hand: {gesture.hand_shape}")
        
        # Add movement
        if gesture.movement:
            parts.append(f"Movement: {gesture.movement}")
        
        if parts:
            return " | ".join(parts)
        
        # Fallback for letters
        if gesture.category == GestureCategory.LETTER:
            return f"Sign the letter '{gesture.symbol}'"
        elif gesture.category == GestureCategory.NUMBER:
            return f"Sign the number '{gesture.symbol}'"
        
        return f"Sign: {gesture.symbol}"
    
    def iterate_with_timing(
        self,
        visualization: SignVisualization
    ) -> Generator[SignStep, None, None]:
        """Iterate through steps with proper timing.
        
        This generator yields steps and waits the appropriate duration.
        Useful for automated playback.
        
        Usage:
            for step in visualizer.iterate_with_timing(vis):
                display(step)
        """
        for step in visualization.steps:
            yield step
            time.sleep(step.duration)
    
    def get_quick_signs(self) -> List[Dict]:
        """Get list of common phrases for quick text-to-sign.
        
        Returns frequently used sentences that can be quickly
        converted to sign demonstrations.
        """
        sentences = self.dictionary.get_all_sentences()
        
        # Prioritize common categories
        priority = ['greeting', 'response', 'question', 'request']
        
        quick_signs = []
        for category in priority:
            for sentence in sentences:
                if sentence.category == category and sentence.bidirectional:
                    quick_signs.append({
                        'text': sentence.english_sentence,
                        'category': category,
                        'gesture_count': len(sentence.gesture_sequence),
                        'gestures': sentence.gesture_sequence
                    })
        
        return quick_signs[:20]  # Top 20
    
    def get_alphabet_chart(self) -> List[Dict]:
        """Get fingerspelling alphabet for reference."""
        alphabet = []
        
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            gesture = self.dictionary.get_gesture(f"LETTER_{letter}")
            if gesture:
                alphabet.append({
                    'letter': letter,
                    'description': gesture.description,
                    'is_dynamic': gesture.is_dynamic,
                    'hand_shape': gesture.hand_shape
                })
        
        return alphabet
    
    def get_numbers_chart(self) -> List[Dict]:
        """Get number signs for reference."""
        numbers = []
        
        for i in range(10):
            gesture = self.dictionary.get_gesture(f"NUMBER_{i}")
            if gesture:
                numbers.append({
                    'number': str(i),
                    'description': gesture.description
                })
        
        return numbers
