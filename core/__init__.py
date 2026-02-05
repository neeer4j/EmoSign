"""
Core Sign Language Processing Module

REDESIGNED ARCHITECTURE (v2.0):

This module provides a practical, constrained-vocabulary sign language
interpretation system for real-time communication.

Key Components:
- GestureDictionary: Extensible definitions for gestures and sentences
- SequenceBuffer: Temporal gesture accumulation with deduplication  
- SentenceMapper: Maps gesture sequences to English sentences
- InterpretationEngine: Main orchestrator for interpretation
- SignVisualizer: Text-to-sign visualization

Architecture:
    Input (Camera/Video) 
           ↓
    Gesture Recognition (ML + Heuristics)
           ↓
    TemporalSequenceBuffer (deduplication, stability)
           ↓
    SentenceMapper (predefined mappings → English)
           ↓
    TranslationOutput

    Text Input → TextToSignMapper → SignVisualizer → Visual Output

SCOPE & LIMITATIONS:
- Constrained vocabulary for practical communication
- NOT a full ASL linguistic translator
- English word order (not ASL grammar)
- Explicit acknowledgment of limitations
"""

# === NEW MODULAR ARCHITECTURE ===
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
from .interpretation_engine import (
    SignLanguageEngine, EngineConfig, EngineState,
    EngineMode, TranslationTrigger, TranslationOutput,
    get_vocabulary_info, get_supported_sentences
)
from .sign_visualizer import (
    SignVisualizer, SignVisualization, SignStep
)

# === LEGACY COMPATIBILITY ===
from .pipeline import SignLanguagePipeline
from .temporal_aggregator import TemporalAggregator
from .sentence_constructor import SentenceConstructor
from .text_to_sign import TextToSignTranslator
from .sign_vocabulary import SignVocabulary
from .gesture_sequence import GestureSequence, GestureFrame

__all__ = [
    # New architecture
    'GestureDictionary',
    'GestureDefinition', 
    'SentenceMapping',
    'GestureCategory',
    'get_dictionary',
    'TemporalSequenceBuffer',
    'SequenceBufferConfig',
    'DetectedGesture',
    'GestureState',
    'SentenceMapper',
    'TextToSignMapper',
    'SentenceResult',
    'OutputType',
    'SignLanguageEngine',
    'EngineConfig',
    'EngineState',
    'EngineMode',
    'TranslationTrigger',
    'TranslationOutput',
    'get_vocabulary_info',
    'get_supported_sentences',
    'SignVisualizer',
    'SignVisualization',
    'SignStep',
    
    # Legacy compatibility
    'SignLanguagePipeline',
    'TemporalAggregator', 
    'SentenceConstructor',
    'TextToSignTranslator',
    'SignVocabulary',
    'GestureSequence',
    'GestureFrame',
]
