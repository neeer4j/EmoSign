"""
EmoSign - Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Camera Settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# MediaPipe Settings
MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.5

# Video-specific settings (lower threshold for compressed video content)
VIDEO_DETECTION_CONFIDENCE = 0.5

# Model Settings
MODEL_PATH = os.path.join(MODELS_DIR, "gesture_model.pkl")
LABELS_PATH = os.path.join(MODELS_DIR, "labels.pkl")

# Neural Network Model Settings
STATIC_MODEL_PATH = os.path.join(MODELS_DIR, "static_ffn_model.pth")
STATIC_LABELS_PATH = os.path.join(MODELS_DIR, "static_labels.pkl")
DYNAMIC_MODEL_PATH = os.path.join(MODELS_DIR, "dynamic_lstm_model.pth")
DYNAMIC_LABELS_PATH = os.path.join(MODELS_DIR, "dynamic_labels.pkl")

# Dual Model Manager Settings
MOVEMENT_THRESHOLD = 0.02           # Normalized max-landmark displacement threshold
MOVEMENT_FRAMES_REQUIRED = 3        # Consecutive frames exceeding threshold to trigger dynamic
DYNAMIC_SEQUENCE_LENGTH = 30         # Number of frames buffered for LSTM
FULL_FEATURE_COUNT = 87             # All features from FeatureExtractor (63 coords + 24 derived)

# Keras Pipeline Settings
KERAS_STATIC_MODEL_PATH = os.path.join(MODELS_DIR, "keras_static_mlp.keras")
KERAS_STATIC_LABELS_PATH = os.path.join(MODELS_DIR, "keras_static_labels.pkl")
KERAS_DYNAMIC_MODEL_PATH = os.path.join(MODELS_DIR, "keras_dynamic_lstm.keras")
KERAS_DYNAMIC_LABELS_PATH = os.path.join(MODELS_DIR, "keras_dynamic_labels.pkl")
KERAS_FEATURE_COUNT = 63            # 21 landmarks × 3 coords (normalized)
SMOOTHING_WINDOW = 5                # Majority-vote window for prediction smoothing
MIN_PREDICTION_CONFIDENCE = 0.75    # Suppress predictions below this threshold

# ASL Alphabet Labels
ASL_LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# UI Colors (Dark Theme)
COLORS = {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "success": "#00d26a",
    "warning": "#ffc107",
}

# ============================================================
# CORE PIPELINE SETTINGS (Redesigned Sign Language Processing)
# ============================================================

# Temporal Aggregation Settings
TEMPORAL_WINDOW_SIZE = 15        # Frames to consider for voting/smoothing
STABILITY_THRESHOLD = 3          # Consecutive frames for stable recognition
TRANSITION_FRAMES = 3            # Tolerance frames during gesture transition

# Translation Settings (Sentence Mode)
TRANSLATION_TIME_WINDOW = 3.0    # Seconds of inactivity before auto-translate
WORD_TIMEOUT = 1.5               # Seconds of inactivity to finalize a word
LETTER_DEBOUNCE_TIME = 0.8       # Minimum time between same letter
CONFIDENCE_THRESHOLD = 0.45      # Minimum confidence for gesture acceptance
GESTURE_COOLDOWN_MS = 1500       # (legacy) Cooldown bar duration
CAPTURE_WINDOW_MS = 2500         # Capture window duration (ms) — bar fills, then majority vote

# Translation Modes
TRANSLATION_MODE_INSTANT = "instant"      # Output each gesture immediately
TRANSLATION_MODE_SENTENCE = "sentence"    # Accumulate and output sentences
TRANSLATION_MODE_WORD = "word"            # Output complete words

# Default translation mode
DEFAULT_TRANSLATION_MODE = TRANSLATION_MODE_SENTENCE

# Gesture Recognition Settings
ENABLE_WORD_RECOGNITION = True   # Try to recognize word patterns from letters
ENABLE_DYNAMIC_GESTURES = True   # Enable motion-based gesture recognition
ENABLE_HEURISTICS = True         # Use geometric heuristics for reliable detection

# Text-to-Sign Settings
SIGN_DISPLAY_DURATION = 1.5      # Seconds to display each word sign
LETTER_DISPLAY_DURATION = 0.5    # Seconds to display each letter
FINGERSPELL_SPEED = 0.4          # Seconds per letter when fingerspelling

# ============================================================
# VIDEO PROCESSING SETTINGS
# ============================================================

SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
DEFAULT_PLAYBACK_SPEED = 1.0
VIDEO_FAST_MODE_INTERVAL = 10    # ms between frames in fast mode
VIDEO_NORMAL_INTERVAL = 33       # ms between frames (~30 FPS)

# Video-specific processing
VIDEO_AUTO_TRANSLATE_ON_END = True  # Auto-translate when video ends

# ============================================================
# TWO-HAND GESTURE SUPPORT
# ============================================================
MAX_HANDS = 2                    # Support two-handed gestures
ENABLE_TWO_HAND_GESTURES = True  # Enable two-handed sign recognition
TWO_HAND_COORDINATION_THRESHOLD = 0.3  # Max time diff between hand detections

# ============================================================
# VOICE OUTPUT SETTINGS (Text-to-Speech)
# ============================================================
VOICE_ENABLED = True             # Enable voice output
VOICE_ENGINE = "pyttsx3"         # TTS engine: pyttsx3, gtts
VOICE_RATE = 150                 # Speech rate (words per minute)
VOICE_VOLUME = 0.8               # Volume (0.0 to 1.0)
VOICE_AUTO_SPEAK_WORDS = True    # Auto-speak detected words
VOICE_AUTO_SPEAK_SENTENCES = True  # Auto-speak completed sentences
VOICE_SPEAK_LETTERS = False      # Speak individual letters

# ============================================================
# MULTI-LANGUAGE SUPPORT
# ============================================================
DEFAULT_SIGN_LANGUAGE = "asl"    # Default sign language (asl, bsl, isl, etc.)
SUPPORTED_SIGN_LANGUAGES = ["asl", "bsl", "isl", "lsf", "dgs", "auslan"]

# ============================================================
# AUTOCORRECT SETTINGS
# ============================================================
AUTOCORRECT_ENABLED = True       # Enable spell correction
AUTOCORRECT_MIN_CONFIDENCE = 0.6  # Minimum confidence for auto-correction
PREDICTION_ENABLED = True        # Enable word/phrase prediction

# ============================================================
# ANALYTICS & GAMIFICATION
# ============================================================
ANALYTICS_ENABLED = True         # Track usage analytics
ACHIEVEMENTS_ENABLED = True      # Enable achievement system
STREAK_TRACKING = True           # Track daily practice streaks

# ============================================================
# ACCESSIBILITY SETTINGS
# ============================================================
HIGH_CONTRAST_MODE = False       # High contrast for visibility
LARGE_TEXT_MODE = False          # Larger font sizes
REDUCE_MOTION = False            # Minimize animations
SCREEN_READER_SUPPORT = True     # Optimize for screen readers

# ============================================================
# THEME SETTINGS
# ============================================================
CURRENT_THEME = "dark"           # Current theme: dark, light
UI_SCALE = 1.0                   # UI scaling factor (1.0 = 100%)

# ============================================================
# EXPORT SETTINGS
# ============================================================
DEFAULT_EXPORT_FORMAT = "txt"    # Default export format
EXPORT_INCLUDE_TIMESTAMPS = True
EXPORT_INCLUDE_CONFIDENCE = False
EXPORT_OUTPUT_DIR = os.path.join(BASE_DIR, "exports")
