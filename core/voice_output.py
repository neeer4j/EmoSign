"""
Voice Output Module - Text-to-Speech for Sign Language Translations

Provides audio output for translated text, enabling better communication
with non-signers by speaking the detected signs aloud.
"""
import threading
import queue
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Try to import TTS engines
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("⚠️ pyttsx3 not installed. Voice output will be limited.")

try:
    from gtts import gTTS
    import io
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


class VoiceEngine(Enum):
    """Available TTS engines."""
    PYTTSX3 = "pyttsx3"      # Offline, fast
    GTTS = "gtts"            # Online, natural voice
    SYSTEM = "system"        # OS default


class VoiceGender(Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


@dataclass
class VoiceConfig:
    """Voice output configuration."""
    enabled: bool = True
    engine: VoiceEngine = VoiceEngine.PYTTSX3
    rate: int = 150          # Words per minute (50-300)
    volume: float = 1.0      # 0.0 to 1.0
    gender: VoiceGender = VoiceGender.FEMALE
    language: str = "en"     # Language code
    
    # Auto-speak settings
    auto_speak_words: bool = True
    auto_speak_sentences: bool = True
    speak_letters: bool = False  # Speak individual letters
    
    # Delays
    word_delay: float = 0.3  # Delay between words
    sentence_delay: float = 0.5  # Delay after sentences


class VoiceOutputManager:
    """Manages text-to-speech output for translations.
    
    Features:
    - Multiple TTS engine support (pyttsx3, gTTS)
    - Configurable voice settings (rate, volume, gender)
    - Background processing for non-blocking speech
    - Queue management for sequential speaking
    - Auto-speak for words and sentences
    """
    
    _instance: Optional['VoiceOutputManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.config = VoiceConfig()
        self._engine = None
        self._speech_queue = queue.Queue()
        self._worker_thread = None
        self._is_speaking = False
        self._stop_flag = False
        
        # Callbacks
        self._on_speech_start: Optional[Callable] = None
        self._on_speech_end: Optional[Callable] = None
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the TTS engine."""
        if self.config.engine == VoiceEngine.PYTTSX3 and PYTTSX3_AVAILABLE:
            try:
                self._engine = pyttsx3.init()
                self._apply_settings()
                print("✅ Voice output initialized (pyttsx3)")
                return True
            except Exception as e:
                print(f"⚠️ Failed to initialize pyttsx3: {e}")
        
        if self.config.engine == VoiceEngine.GTTS and GTTS_AVAILABLE:
            print("✅ Voice output initialized (gTTS - online)")
            return True
        
        print("⚠️ No TTS engine available")
        return False
    
    def _apply_settings(self):
        """Apply current settings to the engine."""
        if self._engine is None:
            return
        
        try:
            # Set rate
            self._engine.setProperty('rate', self.config.rate)
            
            # Set volume
            self._engine.setProperty('volume', self.config.volume)
            
            # Set voice (gender)
            voices = self._engine.getProperty('voices')
            if voices:
                for voice in voices:
                    voice_name = voice.name.lower()
                    if self.config.gender == VoiceGender.FEMALE:
                        if 'female' in voice_name or 'zira' in voice_name or 'woman' in voice_name:
                            self._engine.setProperty('voice', voice.id)
                            break
                    elif self.config.gender == VoiceGender.MALE:
                        if 'male' in voice_name or 'david' in voice_name or 'man' in voice_name:
                            self._engine.setProperty('voice', voice.id)
                            break
        except Exception as e:
            print(f"Warning: Could not apply voice settings: {e}")
    
    def set_config(self, config: VoiceConfig):
        """Update voice configuration."""
        self.config = config
        self._apply_settings()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable voice output."""
        self.config.enabled = enabled
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)."""
        self.config.rate = max(50, min(300, rate))
        self._apply_settings()
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.config.volume = max(0.0, min(1.0, volume))
        self._apply_settings()
    
    def speak(self, text: str, priority: bool = False, block: bool = False):
        """Speak text.
        
        Args:
            text: Text to speak
            priority: If True, clear queue and speak immediately
            block: If True, wait until speech completes
        """
        if not self.config.enabled or not text:
            return
        
        if priority:
            self.stop()
            self._clear_queue()
        
        if block:
            self._speak_sync(text)
        else:
            self._speech_queue.put(text)
            self._ensure_worker_running()
    
    def speak_word(self, word: str):
        """Speak a detected word."""
        if self.config.auto_speak_words:
            self.speak(word)
    
    def speak_sentence(self, sentence: str):
        """Speak a complete sentence."""
        if self.config.auto_speak_sentences:
            self.speak(sentence, priority=True)
    
    def speak_letter(self, letter: str):
        """Speak an individual letter."""
        if self.config.speak_letters:
            self.speak(letter)
    
    def _speak_sync(self, text: str):
        """Speak text synchronously."""
        if self._engine is None:
            return
        
        try:
            self._is_speaking = True
            if self._on_speech_start:
                self._on_speech_start(text)
            
            self._engine.say(text)
            self._engine.runAndWait()
            
            self._is_speaking = False
            if self._on_speech_end:
                self._on_speech_end(text)
        except Exception as e:
            print(f"Speech error: {e}")
            self._is_speaking = False
    
    def _worker_loop(self):
        """Background worker for processing speech queue."""
        while not self._stop_flag:
            try:
                text = self._speech_queue.get(timeout=0.5)
                if text is None:
                    break
                self._speak_sync(text)
                self._speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Speech worker error: {e}")
    
    def _ensure_worker_running(self):
        """Ensure background worker thread is running."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_flag = False
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name="VoiceOutputWorker"
            )
            self._worker_thread.start()
    
    def _clear_queue(self):
        """Clear the speech queue."""
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
    
    def stop(self):
        """Stop current speech."""
        if self._engine:
            try:
                self._engine.stop()
            except:
                pass
        self._is_speaking = False
    
    def shutdown(self):
        """Shutdown voice output manager."""
        self._stop_flag = True
        self._clear_queue()
        self._speech_queue.put(None)  # Signal worker to exit
        
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        
        if self._engine:
            try:
                self._engine.stop()
            except:
                pass
    
    @property
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking
    
    @property
    def is_available(self) -> bool:
        """Check if voice output is available."""
        return PYTTSX3_AVAILABLE or GTTS_AVAILABLE
    
    def get_available_voices(self) -> list:
        """Get list of available voices."""
        if self._engine is None:
            return []
        
        try:
            voices = self._engine.getProperty('voices')
            return [{"id": v.id, "name": v.name} for v in voices]
        except:
            return []
    
    def on_speech_start(self, callback: Callable):
        """Set callback for speech start event."""
        self._on_speech_start = callback
    
    def on_speech_end(self, callback: Callable):
        """Set callback for speech end event."""
        self._on_speech_end = callback


# Singleton instance
voice_output = VoiceOutputManager()
