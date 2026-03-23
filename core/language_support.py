"""
Multi-Language Support - Sign Language Vocabulary for Multiple Languages

Supports multiple sign languages:
- ASL (American Sign Language)
- BSL (British Sign Language)
- ISL (Indian Sign Language)
- LSF (French Sign Language)
- DGS (German Sign Language)
- Auslan (Australian Sign Language)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class SignLanguageType(Enum):
    """Supported sign languages."""
    ASL = "asl"       # American Sign Language
    BSL = "bsl"       # British Sign Language
    ISL = "isl"       # Indian Sign Language
    LSF = "lsf"       # French Sign Language
    DGS = "dgs"       # German Sign Language
    AUSLAN = "auslan" # Australian Sign Language


@dataclass
class LanguageInfo:
    """Information about a sign language."""
    code: SignLanguageType
    name: str
    native_name: str
    country: str
    flag_emoji: str
    alphabet_count: int
    has_two_hand_alphabet: bool
    description: str
    
    # Recognition model info
    model_available: bool = False
    model_path: Optional[str] = None


# Sign language definitions
SUPPORTED_LANGUAGES: Dict[SignLanguageType, LanguageInfo] = {
    SignLanguageType.ASL: LanguageInfo(
        code=SignLanguageType.ASL,
        name="American Sign Language",
        native_name="ASL",
        country="United States",
        flag_emoji="🇺🇸",
        alphabet_count=26,
        has_two_hand_alphabet=False,
        description="The primary sign language used in the US and English-speaking Canada.",
        model_available=True
    ),
    SignLanguageType.BSL: LanguageInfo(
        code=SignLanguageType.BSL,
        name="British Sign Language",
        native_name="BSL",
        country="United Kingdom",
        flag_emoji="🇬🇧",
        alphabet_count=26,
        has_two_hand_alphabet=True,
        description="The sign language used in the United Kingdom. Uses two-handed fingerspelling.",
        model_available=False
    ),
    SignLanguageType.ISL: LanguageInfo(
        code=SignLanguageType.ISL,
        name="Indian Sign Language",
        native_name="भारतीय सांकेतिक भाषा",
        country="India",
        flag_emoji="🇮🇳",
        alphabet_count=36,  # Devanagari-based
        has_two_hand_alphabet=False,
        description="Sign language used in India. Can represent both English and Devanagari scripts.",
        model_available=False
    ),
    SignLanguageType.LSF: LanguageInfo(
        code=SignLanguageType.LSF,
        name="French Sign Language",
        native_name="Langue des Signes Française",
        country="France",
        flag_emoji="🇫🇷",
        alphabet_count=26,
        has_two_hand_alphabet=False,
        description="Sign language used in France. Historical parent of ASL.",
        model_available=False
    ),
    SignLanguageType.DGS: LanguageInfo(
        code=SignLanguageType.DGS,
        name="German Sign Language",
        native_name="Deutsche Gebärdensprache",
        country="Germany",
        flag_emoji="🇩🇪",
        alphabet_count=30,  # Includes umlauts
        has_two_hand_alphabet=False,
        description="Sign language used in Germany and Luxembourg.",
        model_available=False
    ),
    SignLanguageType.AUSLAN: LanguageInfo(
        code=SignLanguageType.AUSLAN,
        name="Australian Sign Language",
        native_name="Auslan",
        country="Australia",
        flag_emoji="🇦🇺",
        alphabet_count=26,
        has_two_hand_alphabet=True,
        description="Sign language used in Australia. Related to BSL.",
        model_available=False
    ),
}


@dataclass
class LanguageVocabulary:
    """Vocabulary for a specific sign language."""
    language: SignLanguageType
    
    # Alphabet mappings
    alphabet: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Numbers
    numbers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Common words/phrases
    words: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Dynamic gestures
    dynamic_gestures: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class MultiLanguageManager:
    """Manages multiple sign language vocabularies.
    
    Features:
    - Switch between different sign languages
    - Language-specific vocabulary lookup
    - Cross-language sign comparison
    - Model loading for different languages
    """
    
    _instance: Optional['MultiLanguageManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._current_language = SignLanguageType.ASL
        self._vocabularies: Dict[SignLanguageType, LanguageVocabulary] = {}
        self._load_default_vocabularies()
    
    def _load_default_vocabularies(self):
        """Load default vocabularies for all supported languages."""
        # ASL Vocabulary (fully implemented)
        asl_vocab = LanguageVocabulary(language=SignLanguageType.ASL)
        
        # ASL Alphabet (single hand)
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            asl_vocab.alphabet[letter] = {
                "gesture_label": letter,
                "is_dynamic": letter in ['J', 'Z'],
                "hand_shape": self._get_asl_hand_shape(letter),
                "description": f"ASL letter {letter}"
            }
        
        # ASL Numbers
        for i in range(10):
            asl_vocab.numbers[str(i)] = {
                "gesture_label": str(i),
                "description": f"Number {i}"
            }
        
        # ASL Common words
        asl_vocab.words = {
            "hello": {"gesture_label": "hello", "is_dynamic": True, "emoji": "👋"},
            "thank you": {"gesture_label": "thank_you", "emoji": "🙏"},
            "please": {"gesture_label": "please", "emoji": "🙏"},
            "yes": {"gesture_label": "yes", "is_dynamic": True},
            "no": {"gesture_label": "no", "is_dynamic": True},
            "sorry": {"gesture_label": "sorry", "emoji": "🙇"},
            "help": {"gesture_label": "help"},
            "love": {"gesture_label": "love", "emoji": "❤️"},
            "friend": {"gesture_label": "friend"},
            "family": {"gesture_label": "family"},
        }
        
        self._vocabularies[SignLanguageType.ASL] = asl_vocab
        
        # BSL Vocabulary (placeholder - two-handed alphabet)
        bsl_vocab = LanguageVocabulary(language=SignLanguageType.BSL)
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            bsl_vocab.alphabet[letter] = {
                "gesture_label": f"BSL_{letter}",
                "is_dynamic": False,
                "two_handed": True,
                "description": f"BSL letter {letter} (two-handed)"
            }
        self._vocabularies[SignLanguageType.BSL] = bsl_vocab
        
        # ISL Vocabulary (placeholder)
        isl_vocab = LanguageVocabulary(language=SignLanguageType.ISL)
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            isl_vocab.alphabet[letter] = {
                "gesture_label": f"ISL_{letter}",
                "description": f"ISL letter {letter}"
            }
        self._vocabularies[SignLanguageType.ISL] = isl_vocab
    
    def _get_asl_hand_shape(self, letter: str) -> str:
        """Get ASL hand shape description for a letter."""
        shapes = {
            'A': 'Fist with thumb to side',
            'B': 'Flat hand, fingers together, thumb across palm',
            'C': 'Curved hand like holding a cup',
            'D': 'Index finger up, other fingers touch thumb',
            'E': 'Fingers curled, thumb across fingers',
            'F': 'OK sign, 3 fingers up',
            'G': 'Pointing hand horizontal',
            'H': 'Index and middle finger out horizontal',
            'I': 'Pinky up, other fingers in fist',
            'J': 'Pinky draws J shape (dynamic)',
            'K': 'Index and middle up, thumb between',
            'L': 'L shape with thumb and index',
            'M': 'Three fingers over thumb',
            'N': 'Two fingers over thumb',
            'O': 'Fingers and thumb form O',
            'P': 'K shape pointing down',
            'Q': 'G shape pointing down',
            'R': 'Crossed fingers',
            'S': 'Fist with thumb over fingers',
            'T': 'Thumb between index and middle',
            'U': 'Index and middle up together',
            'V': 'Peace sign',
            'W': 'Three fingers up',
            'X': 'Hooked index finger',
            'Y': 'Thumb and pinky out (hang loose)',
            'Z': 'Index finger draws Z (dynamic)',
        }
        return shapes.get(letter, "")
    
    @property
    def current_language(self) -> SignLanguageType:
        """Get current sign language."""
        return self._current_language
    
    @property
    def current_language_info(self) -> LanguageInfo:
        """Get info about current language."""
        return SUPPORTED_LANGUAGES[self._current_language]
    
    def set_language(self, language: SignLanguageType) -> bool:
        """Switch to a different sign language.
        
        Returns True if switch was successful.
        """
        if language not in SUPPORTED_LANGUAGES:
            return False
        
        self._current_language = language
        print(f"✅ Switched to {SUPPORTED_LANGUAGES[language].name}")
        return True
    
    def get_vocabulary(self, language: SignLanguageType = None) -> LanguageVocabulary:
        """Get vocabulary for a language."""
        lang = language or self._current_language
        return self._vocabularies.get(lang, LanguageVocabulary(language=lang))
    
    def get_available_languages(self) -> List[LanguageInfo]:
        """Get list of available languages."""
        return list(SUPPORTED_LANGUAGES.values())
    
    def get_language_info(self, language: SignLanguageType) -> Optional[LanguageInfo]:
        """Get info about a specific language."""
        return SUPPORTED_LANGUAGES.get(language)
    
    def translate_gesture(self, gesture_label: str, 
                         from_lang: SignLanguageType = None,
                         to_lang: SignLanguageType = None) -> Optional[str]:
        """Translate a gesture between languages (if mapping exists)."""
        # For now, return the same label (cross-language translation not implemented)
        return gesture_label
    
    def is_model_available(self, language: SignLanguageType = None) -> bool:
        """Check if ML model is available for a language."""
        lang = language or self._current_language
        return SUPPORTED_LANGUAGES[lang].model_available


# Singleton instance
language_manager = MultiLanguageManager()
