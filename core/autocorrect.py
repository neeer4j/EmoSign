"""
Autocorrect Module - Fingerspelling Word Correction

Provides spell-checking and word suggestions for fingerspelled text,
helping to correct common signing errors and misdetections.
"""
import os
import re
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import Counter


@dataclass
class CorrectionSuggestion:
    """A spelling correction suggestion."""
    original: str
    suggestion: str
    confidence: float
    distance: int  # Edit distance


class SpellCorrector:
    """Spell correction for fingerspelled words.
    
    Uses a combination of:
    - Common word dictionary
    - Edit distance matching
    - Phonetic similarity
    - Context-aware predictions
    """
    
    def __init__(self):
        self._word_freq: Dict[str, int] = {}
        self._common_words: Set[str] = set()
        self._load_dictionary()
        
        # Common letter confusion patterns in sign language
        self._confusion_matrix = {
            'A': ['S', 'E', 'M', 'N', 'T'],
            'B': ['D', 'F'],
            'C': ['O', 'G'],
            'D': ['F', 'K', 'B'],
            'E': ['A', 'S', 'O'],
            'F': ['D', 'B'],
            'G': ['H', 'Q'],
            'H': ['G', 'U', 'R'],
            'I': ['Y', 'J'],
            'J': ['I', 'Z'],
            'K': ['P', 'V', 'D'],
            'L': ['G'],
            'M': ['N', 'A', 'S'],
            'N': ['M', 'A', 'S', 'T'],
            'O': ['C', 'E'],
            'P': ['K', 'Q'],
            'Q': ['P', 'G'],
            'R': ['U', 'H'],
            'S': ['A', 'E', 'M', 'N', 'T'],
            'T': ['N', 'A', 'S'],
            'U': ['R', 'H', 'V'],
            'V': ['U', 'K'],
            'W': ['3'],  # Often confused with number 3
            'X': ['T'],
            'Y': ['I'],
            'Z': ['J'],
        }
    
    def _load_dictionary(self):
        """Load common English words dictionary."""
        # Most common English words with frequencies
        common_words = """
        the be to of and a in that have i it for not on with he as you do at
        this but his by from they we say her she or an will my one all would
        there their what so up out if about who get which go me when make can
        like time no just him know take people into year your good some could
        them see other than then now look only come its over think also back
        after use two how our work first well way even new want because any
        these give day most us hello goodbye yes no please thank you sorry
        help love friend family name what where when why how who okay good
        bad happy sad angry hungry thirsty tired sick hurt need want like
        stop go come here there now today tomorrow yesterday morning afternoon
        evening night water food eat drink more less big small hot cold
        beautiful nice welcome understand learn teach school work home
        """.split()
        
        for i, word in enumerate(common_words):
            word = word.upper()
            self._common_words.add(word)
            # Higher frequency for more common words
            self._word_freq[word] = len(common_words) - i
        
        # Add alphabet as valid "words" for single letter detection
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self._word_freq[letter] = 1
    
    def add_word(self, word: str, frequency: int = 10):
        """Add a custom word to the dictionary."""
        word = word.upper()
        self._common_words.add(word)
        self._word_freq[word] = frequency
    
    def add_words(self, words: List[str]):
        """Add multiple words to the dictionary."""
        for word in words:
            self.add_word(word)
    
    def is_valid_word(self, word: str) -> bool:
        """Check if a word is in the dictionary."""
        return word.upper() in self._common_words
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance."""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _sign_language_distance(self, s1: str, s2: str) -> float:
        """Calculate distance accounting for sign language confusion patterns."""
        s1, s2 = s1.upper(), s2.upper()
        
        if len(s1) != len(s2):
            # Use regular edit distance for different lengths
            return self._edit_distance(s1, s2)
        
        distance = 0.0
        for c1, c2 in zip(s1, s2):
            if c1 == c2:
                continue
            elif c2 in self._confusion_matrix.get(c1, []):
                # Common confusion - less penalty
                distance += 0.5
            else:
                distance += 1.0
        
        return distance
    
    def get_suggestions(self, word: str, max_suggestions: int = 5, 
                       max_distance: int = 2) -> List[CorrectionSuggestion]:
        """Get spelling suggestions for a word.
        
        Args:
            word: The word to check
            max_suggestions: Maximum number of suggestions
            max_distance: Maximum edit distance for suggestions
            
        Returns:
            List of correction suggestions sorted by confidence
        """
        word = word.upper()
        
        # If word is valid, return it with high confidence
        if self.is_valid_word(word):
            return [CorrectionSuggestion(word, word, 1.0, 0)]
        
        suggestions = []
        
        for dict_word in self._common_words:
            # Skip if length difference is too large
            if abs(len(dict_word) - len(word)) > max_distance:
                continue
            
            # Calculate sign-language aware distance
            sl_dist = self._sign_language_distance(word, dict_word)
            
            if sl_dist <= max_distance:
                # Calculate confidence based on distance and word frequency
                base_confidence = 1.0 - (sl_dist / (len(word) + 1))
                freq_boost = min(self._word_freq.get(dict_word, 1) / 100, 0.2)
                confidence = min(base_confidence + freq_boost, 0.99)
                
                suggestions.append(CorrectionSuggestion(
                    original=word,
                    suggestion=dict_word,
                    confidence=confidence,
                    distance=int(sl_dist)
                ))
        
        # Sort by confidence (descending)
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        return suggestions[:max_suggestions]
    
    def correct(self, word: str) -> Tuple[str, float]:
        """Get the best correction for a word.
        
        Returns:
            Tuple of (corrected_word, confidence)
        """
        suggestions = self.get_suggestions(word, max_suggestions=1)
        if suggestions:
            return suggestions[0].suggestion, suggestions[0].confidence
        return word.upper(), 0.0
    
    def correct_sentence(self, text: str) -> Tuple[str, List[CorrectionSuggestion]]:
        """Correct all words in a sentence.
        
        Returns:
            Tuple of (corrected_text, list_of_corrections_made)
        """
        words = text.split()
        corrected_words = []
        corrections = []
        
        for word in words:
            if word.upper() in self._common_words:
                corrected_words.append(word)
            else:
                suggestion = self.get_suggestions(word, max_suggestions=1)
                if suggestion and suggestion[0].confidence > 0.5:
                    corrected_words.append(suggestion[0].suggestion)
                    corrections.append(suggestion[0])
                else:
                    corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections


class ContextPredictor:
    """Predicts likely next words based on context.
    
    Uses n-gram models and common phrase patterns.
    """
    
    def __init__(self):
        # Common word pairs (bigrams)
        self._bigrams: Dict[str, List[Tuple[str, float]]] = {
            'HELLO': [('THERE', 0.3), ('FRIEND', 0.2), ('MY', 0.2)],
            'THANK': [('YOU', 0.9)],
            'HOW': [('ARE', 0.5), ('DO', 0.2), ('MUCH', 0.1)],
            'ARE': [('YOU', 0.5)],
            'I': [('AM', 0.3), ('LOVE', 0.2), ('WANT', 0.2), ('NEED', 0.1)],
            'MY': [('NAME', 0.3), ('FRIEND', 0.1)],
            'GOOD': [('MORNING', 0.3), ('AFTERNOON', 0.2), ('NIGHT', 0.2)],
            'NICE': [('TO', 0.4), ('MEET', 0.2)],
            'TO': [('MEET', 0.2), ('YOU', 0.2)],
            'WHAT': [('IS', 0.3), ('ARE', 0.2), ('DO', 0.1)],
            'WHERE': [('IS', 0.3), ('ARE', 0.2)],
            'PLEASE': [('HELP', 0.2)],
            'CAN': [('YOU', 0.4), ('I', 0.3)],
        }
        
        # Common phrases
        self._phrases = [
            ['HELLO', 'HOW', 'ARE', 'YOU'],
            ['MY', 'NAME', 'IS'],
            ['NICE', 'TO', 'MEET', 'YOU'],
            ['THANK', 'YOU', 'VERY', 'MUCH'],
            ['GOOD', 'MORNING'],
            ['GOOD', 'AFTERNOON'],
            ['GOOD', 'NIGHT'],
            ['I', 'LOVE', 'YOU'],
            ['PLEASE', 'HELP', 'ME'],
            ['I', 'AM', 'SORRY'],
        ]
    
    def predict_next(self, words: List[str], n: int = 3) -> List[Tuple[str, float]]:
        """Predict likely next words based on previous words.
        
        Args:
            words: List of previous words
            n: Number of predictions to return
            
        Returns:
            List of (word, probability) tuples
        """
        if not words:
            return []
        
        last_word = words[-1].upper()
        predictions = []
        
        # Check bigrams
        if last_word in self._bigrams:
            predictions.extend(self._bigrams[last_word])
        
        # Check phrase patterns
        for phrase in self._phrases:
            words_upper = [w.upper() for w in words]
            for i in range(len(phrase) - 1):
                if phrase[:i+1] == words_upper[-(i+1):]:
                    if i + 1 < len(phrase):
                        next_word = phrase[i + 1]
                        # Add if not already in predictions
                        if not any(p[0] == next_word for p in predictions):
                            predictions.append((next_word, 0.4))
        
        # Sort by probability and return top n
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:n]
    
    def complete_phrase(self, partial: str) -> List[Tuple[str, float]]:
        """Suggest phrase completions based on partial input."""
        partial_words = partial.upper().split()
        if not partial_words:
            return []
        
        completions = []
        for phrase in self._phrases:
            # Check if partial matches beginning of phrase
            if len(partial_words) <= len(phrase):
                if phrase[:len(partial_words)] == partial_words:
                    remaining = ' '.join(phrase[len(partial_words):])
                    if remaining:
                        completions.append((remaining, 0.5))
        
        return completions


class AutocorrectManager:
    """Main manager combining spell correction and prediction."""
    
    def __init__(self):
        self.corrector = SpellCorrector()
        self.predictor = ContextPredictor()
        
        # Settings
        self.auto_correct_enabled = True
        self.prediction_enabled = True
        self.min_confidence = 0.6
    
    def process_input(self, text: str) -> Dict:
        """Process input text and return corrections and predictions.
        
        Returns:
            Dict with:
                - corrected: The corrected text
                - corrections: List of corrections made
                - predictions: Predicted next words
                - completions: Phrase completions
        """
        result = {
            'original': text,
            'corrected': text,
            'corrections': [],
            'predictions': [],
            'completions': []
        }
        
        if not text:
            return result
        
        # Auto-correct
        if self.auto_correct_enabled:
            corrected, corrections = self.corrector.correct_sentence(text)
            result['corrected'] = corrected
            result['corrections'] = [
                {'from': c.original, 'to': c.suggestion, 'confidence': c.confidence}
                for c in corrections if c.confidence >= self.min_confidence
            ]
        
        # Predictions
        if self.prediction_enabled:
            words = result['corrected'].split()
            predictions = self.predictor.predict_next(words)
            result['predictions'] = [
                {'word': p[0], 'probability': p[1]} for p in predictions
            ]
            
            completions = self.predictor.complete_phrase(result['corrected'])
            result['completions'] = [
                {'text': c[0], 'probability': c[1]} for c in completions
            ]
        
        return result


# Singleton instance
autocorrect = AutocorrectManager()
