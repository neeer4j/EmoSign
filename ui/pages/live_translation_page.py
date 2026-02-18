"""
Live Translation Page - Simplified Unified Translation

Real-time sign language detection with:
- Automatic detection of letters, words, and sentences
- No mode selection needed - the engine figures it out
- Predefined vocabulary for reliable communication
- Camera and video input support
- Text-to-sign reverse communication

ARCHITECTURE:
    Camera/Video → Gesture Recognition → SimpleTranslationEngine → Translation
    Text Input → TextToSignMapper → SignVisualizer → Display

Uses SimpleTranslationEngine which:
- Auto-detects if input is letter/word/sentence
- Uses only predefined gestures for reliability
- No modes - just works
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy, QTextEdit,
    QProgressBar, QTabWidget, QStackedWidget, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS
from ui.page_header import make_page_header
from ui.camera_widget import CameraWidget
from ui.video_player_widget import VideoPlayerWidget
from ui.sign_visualizer import SignVisualizerWidget
from ml.classifier import Classifier

# Simple unified translation engine
from core.simple_engine import (
    SimpleTranslationEngine, TranslationResult as SimpleResult,
    OutputType, GestureEvent, WORD_GESTURES
)

# Legacy imports for compatibility (needed for some callback types)
try:
    from core.interpretation_engine import (
        SignLanguageEngine, EngineConfig, EngineMode,
        TranslationTrigger, TranslationOutput
    )
    from core.sequence_buffer import DetectedGesture, GestureState
    from core.sentence_mapper import SentenceMapping
    from core.gesture_dictionary import GestureCategory
except ImportError:
    pass  # These are optional now

# Legacy imports for compatibility
from core.pipeline import SignLanguagePipeline, PipelineMode, PipelineConfig
from core.gesture_sequence import GestureType, RecognizedGesture, TranslationResult
from core.text_to_sign import TextToSignTranslator

import config


class TranslationDisplay(QFrame):
    """Display for showing current translation with live preview."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📝 Translation")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        
        # Status indicator
        self.status_label = QLabel("⏸️ Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        header.addWidget(self.status_label)
        
        layout.addLayout(header)
        
        # Main translation text
        self.translation_text = QLabel("Start signing to translate...")
        self.translation_text.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            padding: 16px;
            background-color: {COLORS['bg_input']};
            border-radius: 10px;
            min-height: 60px;
        """)
        self.translation_text.setWordWrap(True)
        self.translation_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.translation_text)
        
        # Preview (buffer) text
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            padding: 8px 12px;
        """)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
        # Statistics row
        stats_row = QHBoxLayout()
        
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        stats_row.addWidget(self.word_count_label)
        
        self.gesture_count_label = QLabel("Gestures: 0")
        self.gesture_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        stats_row.addWidget(self.gesture_count_label)
        
        self.confidence_label = QLabel("Confidence: --")
        self.confidence_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        stats_row.addWidget(self.confidence_label)
        
        stats_row.addStretch()
        layout.addLayout(stats_row)
    
    def set_translation(self, text: str):
        """Set the main translation text."""
        if text:
            self.translation_text.setText(text)
        else:
            self.translation_text.setText("Start signing to translate...")
    
    def set_preview(self, preview: str):
        """Set the preview/buffer text."""
        if preview and preview != "(waiting...)":
            self.preview_label.setText(f"📦 Building: {preview}")
            self.preview_label.show()
        else:
            self.preview_label.hide()
    
    def set_statistics(self, words: int, gestures: int, confidence: float):
        """Update statistics display."""
        self.word_count_label.setText(f"Words: {words}")
        self.gesture_count_label.setText(f"Gestures: {gestures}")
        if confidence > 0:
            self.confidence_label.setText(f"Confidence: {confidence:.0%}")
        else:
            self.confidence_label.setText("Confidence: --")
    
    def set_status(self, status: str, is_active: bool = False):
        """Set status indicator."""
        if is_active:
            self.status_label.setText(f"🔴 {status}")
            self.status_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        else:
            self.status_label.setText(f"⏸️ {status}")
            self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
    
    def clear(self):
        """Clear the display."""
        self.set_translation("")
        self.set_preview("")
        self.set_statistics(0, 0, 0)
        self.set_status("Ready")


class CurrentGestureDisplay(QFrame):
    """Compact display for current gesture recognition with capture window.
    
    Capture-window approach (replaces cooldown):
    1. A time bar fills 0→100 % over CAPTURE_WINDOW_MS
    2. During the window every detected gesture is recorded as a *vote*
    3. When the bar completes the gesture with the most votes wins
    4. The confirmed gesture is shown briefly, then the next window starts
    """
    
    # Emitted when a capture window completes with a majority-vote winner
    capture_complete = Signal(str, float)   # gesture, confidence
    
    def __init__(self, capture_ms: int = 2500, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._capture_ms = capture_ms       # capture-window duration
        self._is_capturing = False
        self._capture_elapsed = 0
        self._tick_interval = 30            # timer tick (ms)
        self._vote_buffer: dict = {}        # gesture → vote count
        self._confidence_buffer: dict = {}  # gesture → max confidence
        self._show_delay = 600              # ms to show result before next window
        self._auto_continue = False         # auto-start next window?
        self._min_votes = 4                 # min votes to confirm (avoids noise)
        
        # Capture-window timer
        self._capture_timer = QTimer()
        self._capture_timer.setInterval(self._tick_interval)
        self._capture_timer.timeout.connect(self._tick_capture)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setAlignment(Qt.AlignCenter)
        
        # Current gesture
        self.gesture_label = QLabel("?")
        self.gesture_label.setAlignment(Qt.AlignCenter)
        self.gesture_label.setStyleSheet(f"""
            font-size: 52px;
            font-weight: bold;
            color: {COLORS['primary']};
            background: transparent;
        """)
        
        # Confidence bar
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setMaximum(100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setMaximumHeight(6)
        
        # Capture-window progress bar — fills 0→100 % during the window
        self.capture_bar = QProgressBar()
        self.capture_bar.setMaximum(100)
        self.capture_bar.setValue(0)
        self.capture_bar.setTextVisible(False)
        self.capture_bar.setMaximumHeight(8)
        self.capture_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                border-radius: 4px;
            }}
        """)
        self.capture_bar.hide()
        
        # Capture-window status label
        self.capture_label = QLabel("")
        self.capture_label.setAlignment(Qt.AlignCenter)
        self.capture_label.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: 11px;
            font-weight: 600;
            background: transparent;
        """)
        self.capture_label.hide()
        
        # Type label
        self.type_label = QLabel("Waiting...")
        self.type_label.setAlignment(Qt.AlignCenter)
        self.type_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        
        layout.addWidget(self.gesture_label)
        layout.addWidget(self.confidence_bar)
        layout.addSpacing(4)
        layout.addWidget(self.capture_bar)
        layout.addWidget(self.capture_label)
        layout.addWidget(self.type_label)
        
        # Glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(139, 92, 246, 100))
        glow.setOffset(0, 0)
        self.gesture_label.setGraphicsEffect(glow)
    
    # ── public API ──────────────────────────────────────────────
    
    def update_gesture(self, label: str, confidence: float, gesture_type: str = ""):
        """Update displayed gesture (used for real-time leader preview)."""
        self.gesture_label.setText(label)
        self.confidence_bar.setValue(int(confidence * 100))
        
        if gesture_type:
            self.type_label.setText(gesture_type.capitalize())
        
        if confidence >= 0.8:
            color = COLORS['success']
        elif confidence >= 0.6:
            color = COLORS['primary']
        else:
            color = COLORS['warning']
        
        self.gesture_label.setStyleSheet(f"""
            font-size: 52px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
    
    def start_capture_window(self):
        """Start a new capture window.
        
        The bar fills 0→100 %.  Call ``add_vote()`` during the window
        for each detected gesture.  When the window completes the
        gesture with the most votes is confirmed.
        """
        self._is_capturing = True
        self._capture_elapsed = 0
        self._vote_buffer.clear()
        self._confidence_buffer.clear()
        self.capture_bar.setValue(0)
        self.capture_bar.show()
        self.capture_label.setText("🎯 Show your gesture…")
        self.capture_label.show()
        self.gesture_label.setText("?")
        self.gesture_label.setStyleSheet(f"""
            font-size: 52px;
            font-weight: bold;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        self.type_label.setText("Capturing…")
        self._capture_timer.start()
    
    def add_vote(self, gesture: str, confidence: float):
        """Record a gesture vote during the active capture window.
        
        Call once per frame where a gesture was detected.  The gesture
        with the most votes wins when the window ends.
        """
        if not self._is_capturing:
            return
        gesture = gesture.upper().strip()
        self._vote_buffer[gesture] = self._vote_buffer.get(gesture, 0) + 1
        self._confidence_buffer[gesture] = max(
            self._confidence_buffer.get(gesture, 0), confidence
        )
        # Show the current leader in real-time for user feedback
        if self._vote_buffer:
            leader = max(self._vote_buffer, key=self._vote_buffer.get)
            leader_conf = self._confidence_buffer.get(leader, 0)
            total = sum(self._vote_buffer.values())
            pct = self._vote_buffer[leader] / total if total else 0
            self.update_gesture(leader, leader_conf, f"leading ({pct:.0%})")
    
    def set_auto_continue(self, enabled: bool):
        """Enable / disable auto-starting the next capture window."""
        self._auto_continue = enabled
    
    def is_capturing(self) -> bool:
        """Return True while a capture window is active."""
        return self._is_capturing
    
    def stop_capture(self):
        """Stop the capture window and timer."""
        self._capture_timer.stop()
        self._is_capturing = False
        self._auto_continue = False
        self.capture_bar.hide()
        self.capture_label.hide()
    
    def set_no_hand(self):
        """Set no-hand-detected state (only when NOT mid-capture)."""
        if not self._is_capturing:
            self.gesture_label.setText("👋")
            self.confidence_bar.setValue(0)
            self.type_label.setText("Show your hand")
            self.gesture_label.setStyleSheet(f"""
                font-size: 52px;
                font-weight: bold;
                color: {COLORS['text_muted']};
                background: transparent;
            """)
    
    def clear(self):
        """Clear display and stop any active capture."""
        self.stop_capture()
        self.set_no_hand()
    
    # ── internal ────────────────────────────────────────────────
    
    def _tick_capture(self):
        """Timer tick — advance progress bar and resolve when done."""
        self._capture_elapsed += self._tick_interval
        progress = min(100, int(self._capture_elapsed / self._capture_ms * 100))
        self.capture_bar.setValue(progress)
        
        remaining = max(0, self._capture_ms - self._capture_elapsed) / 1000
        if self._vote_buffer:
            leader = max(self._vote_buffer, key=self._vote_buffer.get)
            self.capture_label.setText(f"🎯 Capturing… {remaining:.1f}s")
        else:
            self.capture_label.setText(f"🎯 Show gesture… {remaining:.1f}s")
        
        if self._capture_elapsed >= self._capture_ms:
            self._capture_timer.stop()
            self._is_capturing = False
            self._resolve_capture()
    
    def _resolve_capture(self):
        """End-of-window: pick the majority-vote winner and emit signal."""
        total = sum(self._vote_buffer.values()) if self._vote_buffer else 0
        
        if not self._vote_buffer or total < self._min_votes:
            # Not enough votes — skip this window
            self.capture_label.setText("⚠ No gesture detected")
            self.capture_bar.hide()
            self.gesture_label.setText("—")
            self.type_label.setText("No detection")
            if self._auto_continue:
                QTimer.singleShot(self._show_delay, self._maybe_next_window)
            return
        
        # Majority vote
        winner = max(self._vote_buffer, key=self._vote_buffer.get)
        confidence = self._confidence_buffer.get(winner, 0.5)
        votes = self._vote_buffer[winner]
        
        # Show confirmed gesture
        self.update_gesture(winner, confidence, "✓ confirmed")
        self.capture_label.setText(f"✓ '{winner}' confirmed ({votes}/{total} votes)")
        self.capture_bar.setValue(100)
        
        # Notify listeners
        self.capture_complete.emit(winner, confidence)
        
        # Auto-start next window after a brief display pause
        if self._auto_continue:
            QTimer.singleShot(self._show_delay, self._maybe_next_window)
    
    def _maybe_next_window(self):
        """Start the next capture window if auto-continue is still on."""
        if self._auto_continue:
            self.start_capture_window()


class SourceSelector(QFrame):
    """Source selection tabs (camera/video)."""
    
    source_changed = Signal(str)  # 'camera' or 'video'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = "camera"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.camera_btn = QPushButton("📷 Camera")
        self.camera_btn.setCheckable(True)
        self.camera_btn.setChecked(True)
        self.camera_btn.clicked.connect(lambda: self._set_source("camera"))
        self._apply_tab_style(self.camera_btn, True)
        
        self.video_btn = QPushButton("🎬 Video File")
        self.video_btn.setCheckable(True)
        self.video_btn.clicked.connect(lambda: self._set_source("video"))
        self._apply_tab_style(self.video_btn, False)
        
        self.text_btn = QPushButton("📤 Text to Sign")
        self.text_btn.setCheckable(True)
        self.text_btn.clicked.connect(lambda: self._set_source("text"))
        self._apply_tab_style(self.text_btn, False)
        
        layout.addWidget(self.camera_btn)
        layout.addWidget(self.video_btn)
        layout.addWidget(self.text_btn)
        layout.addStretch()
    
    def _apply_tab_style(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px 8px 0 0;
                    padding: 12px 20px;
                    font-weight: bold;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_panel']};
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 8px 8px 0 0;
                    padding: 12px 20px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_card']};
                }}
            """)
    
    def _set_source(self, source: str):
        self._current = source
        self.camera_btn.setChecked(source == "camera")
        self.video_btn.setChecked(source == "video")
        self.text_btn.setChecked(source == "text")
        self._apply_tab_style(self.camera_btn, source == "camera")
        self._apply_tab_style(self.video_btn, source == "video")
        self._apply_tab_style(self.text_btn, source == "text")
        self.source_changed.emit(source)
    
    def get_source(self) -> str:
        return self._current


class LiveTranslationPage(QWidget):
    """Simplified live translation page with unified translation engine.
    
    Features:
    - Automatic detection of letters, words, and sentences
    - No mode selection needed - engine auto-detects
    - Predefined vocabulary for reliability
    - Camera and video input support
    - Text-to-sign reverse communication
    
    Uses SimpleTranslationEngine which:
    - Auto-detects if input is letter/word/sentence
    - Uses only predefined gestures for reliability
    - No modes to configure
    """
    
    back_requested = Signal()
    translation_made = Signal(str, float, str)  # text, confidence, type
    
    def __init__(self, classifier=None, db_service=None, user_data=None, parent=None):
        super().__init__(parent)
        self.classifier = classifier or Classifier()
        self.db = db_service
        self.user = user_data or {}
        
        # === SIMPLE TRANSLATION ENGINE ===
        self.engine = SimpleTranslationEngine(
            inactivity_timeout=getattr(config, 'TRANSLATION_TIME_WINDOW', 2.5),
            stability_frames=getattr(config, 'STABILITY_THRESHOLD', 5),
            min_confidence=getattr(config, 'CONFIDENCE_THRESHOLD', 0.5)
        )
        
        # Legacy pipeline for fallback
        self.pipeline = SignLanguagePipeline(PipelineConfig(
            aggregation_window=getattr(config, 'TEMPORAL_WINDOW_SIZE', 15),
            stability_threshold=getattr(config, 'STABILITY_THRESHOLD', 5),
            min_confidence=getattr(config, 'CONFIDENCE_THRESHOLD', 0.5),
            word_timeout=getattr(config, 'WORD_TIMEOUT', 1.5),
            sentence_timeout=getattr(config, 'TRANSLATION_TIME_WINDOW', 3.0)
        ))
        
        # Load classifier
        self._model_loaded = self.classifier.load()
        
        # State
        self._is_translating = False
        self._current_source = "camera"
        
        # Auto-check timer for timeout-based translation
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_timeout)
        self._check_timer.setInterval(500)
        
        self._setup_ui()
        self._connect_signals()
        self._setup_engine_callbacks()
    
    def _setup_ui(self):
        """Setup the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 12, 20, 12)
        main_layout.setSpacing(12)
        
        # === HEADER ===
        header, _ = make_page_header("🔴 Live Translation")
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setObjectName("statusPill")
        
        self.model_label = QLabel("✓ Model Ready" if self._model_loaded else "✗ No Model")
        self.model_label.setObjectName("statusPillSuccess" if self._model_loaded else "statusPillDanger")
        
        # Info label about auto-detection
        info_label = QLabel("🤖 Auto-detects letters, words & sentences")
        info_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            padding: 4px 12px;
            background-color: {COLORS['bg_card']};
            border-radius: 4px;
        """)
        
        header.addWidget(info_label)
        header.addWidget(self.fps_label)
        header.addWidget(self.model_label)
        
        main_layout.addLayout(header)
        
        # === SOURCE TABS ===
        self.source_selector = SourceSelector()
        main_layout.addWidget(self.source_selector)
        
        # === MAIN CONTENT ===
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Source widgets stack
        source_container = QFrame()
        source_container.setObjectName("sourceContainer")
        source_layout = QVBoxLayout(source_container)
        source_layout.setContentsMargins(4, 4, 4, 4)
        
        self.source_stack = QStackedWidget()
        
        # Camera widget
        self.camera_widget = CameraWidget()
        self.source_stack.addWidget(self.camera_widget)
        
        # Video widget
        self.video_widget = VideoPlayerWidget()
        self.source_stack.addWidget(self.video_widget)
        
        # Text-to-sign widget
        self.sign_visualizer = SignVisualizerWidget()
        self.source_stack.addWidget(self.sign_visualizer)
        
        source_layout.addWidget(self.source_stack)
        
        # Camera controls
        self.camera_controls = QFrame()
        cam_ctrl_layout = QHBoxLayout(self.camera_controls)
        
        self.start_btn = QPushButton("▶️ Start Translation")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._toggle_translation)
        
        self.stop_translate_btn = QPushButton("🛑 Stop & Translate")
        self.stop_translate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0ea566;
            }}
        """)
        self.stop_translate_btn.clicked.connect(self._stop_and_translate)
        self.stop_translate_btn.hide()
        
        cam_ctrl_layout.addStretch()
        cam_ctrl_layout.addWidget(self.start_btn)
        cam_ctrl_layout.addWidget(self.stop_translate_btn)
        cam_ctrl_layout.addStretch()
        
        source_layout.addWidget(self.camera_controls)
        
        content_splitter.addWidget(source_container)
        
        # Right: Results panel
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)
        
        # Current gesture display (with capture window)
        capture_ms = getattr(config, 'CAPTURE_WINDOW_MS', 1500)
        self.gesture_display = CurrentGestureDisplay(capture_ms=capture_ms)
        self.gesture_display.setMaximumHeight(200)
        right_layout.addWidget(self.gesture_display)
        
        # Translation display
        self.translation_display = TranslationDisplay()
        right_layout.addWidget(self.translation_display, 1)
        
        # Action buttons
        action_row = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setObjectName("ghost")
        self.copy_btn.clicked.connect(self._copy_translation)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setObjectName("ghost")
        self.clear_btn.clicked.connect(self._clear_translation)
        
        self.space_btn = QPushButton("␣ Space")
        self.space_btn.setObjectName("ghost")
        self.space_btn.clicked.connect(self._insert_space)
        
        self.delete_btn = QPushButton("⌫ Delete")
        self.delete_btn.setObjectName("ghost")
        self.delete_btn.clicked.connect(self._delete_last)
        
        action_row.addWidget(self.copy_btn)
        action_row.addWidget(self.clear_btn)
        action_row.addStretch()
        action_row.addWidget(self.space_btn)
        action_row.addWidget(self.delete_btn)
        
        right_layout.addLayout(action_row)
        
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([600, 400])
        
        main_layout.addWidget(content_splitter, 1)
    
    def _connect_signals(self):
        """Connect UI signals."""
        # Source selector
        self.source_selector.source_changed.connect(self._on_source_changed)
        
        # Camera widget
        self.camera_widget.features_ready.connect(self._on_features)
        self.camera_widget.hand_detected.connect(self._on_hand_detected)
        self.camera_widget.fps_updated.connect(
            lambda f: self.fps_label.setText(f"FPS: {f:.0f}")
        )
        self.camera_widget.heuristic_gesture_detected.connect(self._on_heuristic_gesture)
        self.camera_widget.dynamic_gesture_detected.connect(self._on_dynamic_gesture)
        
        # Capture-window completion → feed confirmed gesture to engine
        self.gesture_display.capture_complete.connect(self._on_capture_complete)
        
        # Video widget - connect same signals for video translation
        self.video_widget.features_ready.connect(self._on_video_features)
        self.video_widget.hand_detected.connect(self._on_hand_detected)
        self.video_widget.fps_updated.connect(
            lambda f: self.fps_label.setText(f"FPS: {f:.0f}")
        )
        self.video_widget.heuristic_gesture_detected.connect(self._on_video_heuristic_gesture)
        self.video_widget.dynamic_gesture_detected.connect(self._on_video_dynamic_gesture)
        self.video_widget.video_finished.connect(self._on_video_finished)
        self.video_widget.video_loaded.connect(self._on_video_loaded)
    
    def _setup_pipeline_callbacks(self):
        """Setup callbacks from the processing pipeline."""
        self.pipeline.set_on_gesture_recognized(self._on_gesture_recognized)
        self.pipeline.set_on_text_updated(self._on_text_updated)
        self.pipeline.set_on_translation_complete(self._on_translation_complete)
    
    def _setup_engine_callbacks(self):
        """Setup callbacks from the simple translation engine."""
        self.engine.set_on_gesture_confirmed(self._on_gesture_confirmed)
        self.engine.set_on_translation_updated(self._on_translation_updated)
    
    def _on_gesture_confirmed(self, gesture: str, confidence: float):
        """Handle gesture confirmation from SimpleTranslationEngine.
        
        Called by engine.force_confirm() or engine.add_gesture() when
        stability is reached.  The capture window handles timing, so
        we only update the preview here.
        """
        # Update preview with accumulated gestures
        result = self.engine.get_translation()
        if result:
            preview_text = " ".join(result.gestures)
            self.translation_display.set_preview(f"📝 {preview_text}")
    
    def _on_capture_complete(self, gesture: str, confidence: float):
        """Handle capture-window completion — feed confirmed gesture to engine."""
        # Directly confirm in engine (bypasses stability check; voting was
        # already done inside the capture window).
        self.engine.force_confirm(gesture, confidence)
    
    def _on_translation_updated(self, result: SimpleResult):
        """Handle translation update from SimpleTranslationEngine."""
        self.translation_display.set_translation(result.text)
        
        # Calculate statistics
        word_count = len(result.text.split()) if result.text else 0
        gesture_count = len(result.gestures)
        
        self.translation_display.set_statistics(
            word_count,
            gesture_count,
            result.confidence
        )
        
        # Show output type info
        type_info = {
            OutputType.LETTER: "📄 Letter detected",
            OutputType.WORD: "📖 Word gesture detected",
            OutputType.FINGERSPELLED: "✍️ Fingerspelling",
            OutputType.SENTENCE: "💬 Sentence matched"
        }
        self.translation_display.set_status(
            type_info.get(result.output_type, "Translating..."),
            is_active=not result.is_complete
        )
        
        # If complete, save to history
        if result.is_complete:
            self._save_translation_result(result)
    
    def _save_translation_result(self, result: SimpleResult):
        """Save translation result to history."""
        if not self.db or self.user.get("guest"):
            return
        
        self.translation_made.emit(
            result.text,
            result.confidence,
            result.output_type.value
        )
    
    # === Video-specific signal handlers ===
    
    @Slot(object)
    def _on_video_features(self, features):
        """Handle extracted features from video (always process when video loaded)."""
        # For video, we process as long as video is loaded, not just when "translating"
        if not self._model_loaded or features is None:
            return
        
        if not self.video_widget.is_loaded():
            return
        
        # Get ML prediction
        label, confidence = self.classifier.predict(features)
        
        if label and confidence > config.CONFIDENCE_THRESHOLD:
            # Feed to simple engine
            self.engine.add_gesture(label, confidence)
            
            # Update gesture display
            self.gesture_display.update_gesture(label, confidence, "video")
    
    @Slot(str, float)
    def _on_video_heuristic_gesture(self, gesture: str, confidence: float):
        """Handle heuristic gesture from video widget (always process)."""
        if not self.video_widget.is_loaded():
            return
        
        # Feed to simple engine
        self.engine.add_gesture(gesture, confidence)
        
        # Update gesture display
        self.gesture_display.update_gesture(gesture, confidence, "heuristic")
    
    @Slot(str, float)
    def _on_video_dynamic_gesture(self, gesture: str, confidence: float):
        """Handle dynamic gesture from video widget (always process)."""
        if not self.video_widget.is_loaded():
            return
        
        # Prefix with WORD_ for word-level gestures
        gesture_name = f"WORD_{gesture.upper()}" if not gesture.startswith("WORD_") else gesture
        self.engine.add_gesture(gesture_name, confidence)
        
        # Update gesture display
        self.gesture_display.update_gesture(f"✨{gesture}", confidence, "dynamic")
    
    # === Source Handling ===
    
    def _on_source_changed(self, source: str):
        """Handle source tab change."""
        self._current_source = source
        
        # Stop any ongoing translation
        if self._is_translating:
            self._stop_translation()
        
        # Switch stack
        if source == "camera":
            self.source_stack.setCurrentIndex(0)
            self.camera_controls.show()
            self.start_btn.setText("▶️ Start Translation")
        elif source == "video":
            self.source_stack.setCurrentIndex(1)
            # Show controls for video too - they control translation
            self.camera_controls.show()
            self.start_btn.setText("▶️ Enable Translation")
        else:  # text
            self.source_stack.setCurrentIndex(2)
            self.camera_controls.hide()
        
        # Stop other sources
        if source != "camera" and self.camera_widget.is_running:
            self.camera_widget.stop()
        if source != "video" and self.video_widget.is_active():
            self.video_widget.release()
    
    def _on_video_loaded(self, filename: str):
        """Handle video loaded - prepare for translation."""
        self.translation_display.set_status(f"Video loaded: {filename}")
        self.translation_display.clear()
        self.gesture_display.clear()
        self.pipeline.clear()
        self.engine.clear()
        # Auto-start engine for video
        self.engine.start()
    
    # === Translation Control ===
    
    def _toggle_translation(self):
        """Start or stop translation."""
        if self._is_translating:
            self._stop_translation()
        else:
            self._start_translation()
    
    def _start_translation(self):
        """Start translation."""
        self._is_translating = True
        
        # Start appropriate source
        if self._current_source == "camera":
            if not self.camera_widget.start():
                self._is_translating = False
                return
        elif self._current_source == "video":
            # For video, translation is enabled - video plays via its own controls
            if not self.video_widget.is_loaded():
                self._is_translating = False
                self.translation_display.set_status("Please load a video first")
                return
        
        # Start legacy pipeline for fallback
        mode = PipelineMode.LIVE_ACCUMULATE
        self.pipeline.start(mode)
        
        # Start simple translation engine
        self.engine.start()
        
        # Update UI
        if self._current_source == "camera":
            self.start_btn.setText("⏹️ Stop")
        else:
            self.start_btn.setText("⏹️ Disable Translation")
        self.start_btn.setObjectName("danger")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        
        # Always show stop & translate button
        self.stop_translate_btn.show()
        
        self.translation_display.set_status("Translating...", True)
        self._check_timer.start()
        
        # Start the first capture window (bar fills → votes → confirm)
        self.gesture_display.set_auto_continue(True)
        self.gesture_display.start_capture_window()
    
    def _stop_translation(self):
        """Stop translation without finalizing."""
        self._is_translating = False
        
        # Stop capture window
        self.gesture_display.stop_capture()
        
        # Stop sources
        if self._current_source == "camera":
            self.camera_widget.stop()
        
        # Stop both pipeline and engine
        self.pipeline.stop()
        self.engine.stop()
        
        # Update UI
        if self._current_source == "camera":
            self.start_btn.setText("▶️ Start Translation")
        else:
            self.start_btn.setText("▶️ Enable Translation")
        self.start_btn.setObjectName("primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        
        self.stop_translate_btn.hide()
        self.translation_display.set_status("Stopped")
        self._check_timer.stop()
    
    def _stop_and_translate(self):
        """Stop and finalize translation."""
        if not self._is_translating:
            return
        
        self._is_translating = False
        
        # Stop capture window
        self.gesture_display.stop_capture()
        
        # Get final translation from simple engine
        result = self.engine.finalize()
        self.engine.clear()   # explicit clear (finalize no longer auto-clears)
        self.engine.stop()
        
        if result and result.text:
            self._on_translation_updated(result)
        else:
            self.translation_display.set_status("No translation available")
        
        # Stop camera
        self.camera_widget.stop()
        
        # Update buttons
        self.start_btn.setText("▶️ Start Translation")
        self.start_btn.setObjectName("primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        
        self.stop_translate_btn.hide()
        self.translation_display.set_status("Complete")
        self._check_timer.stop()
    
    def _check_timeout(self):
        """Periodic update — with capture windows we never auto-clear.
        
        The capture window handles all timing.  This timer now only
        serves to refresh the translation display periodically.
        """
        if not self._is_translating:
            return
        
        # Just refresh the translation preview (no finalize / no clear)
        result = self.engine.get_translation()
        if result:
            self._on_translation_updated(result)
    
    # === Gesture Processing ===
    
    @Slot(object)
    def _on_features(self, features):
        """Handle extracted features from camera/video."""
        if not self._is_translating or not self._model_loaded or features is None:
            self._ml_handled_frame = False
            return
        
        # Use RAW prediction (no temporal smoothing) — the capture window
        # itself performs majority voting, so double-smoothing hurts accuracy.
        label, confidence = self.classifier.predict(features, use_smoothing=False)
        
        if label and confidence > config.CONFIDENCE_THRESHOLD:
            # Feed to capture-window vote buffer (NOT directly to engine)
            self.gesture_display.add_vote(label, confidence)
            self._ml_handled_frame = True  # Skip heuristic for this frame
        else:
            self._ml_handled_frame = False
    
    @Slot(str, float)
    def _on_heuristic_gesture(self, gesture: str, confidence: float):
        """Handle heuristic gesture detection from camera.
        
        Used as fallback when ML didn't produce a result this frame,
        or as supplementary vote when ML also voted (both count).
        """
        if not self._is_translating:
            return
        
        # Feed to capture-window vote buffer
        # Both ML and heuristic votes count — the majority wins
        self.gesture_display.add_vote(gesture, confidence)
    
    @Slot(str, float)
    def _on_dynamic_gesture(self, gesture: str, confidence: float):
        """Handle dynamic gesture detection from camera."""
        if not self._is_translating:
            return
        
        # Dynamic gestures are word-level - prefix with WORD_
        gesture_name = f"WORD_{gesture.upper()}" if not gesture.startswith("WORD_") else gesture
        # Feed to capture-window vote buffer
        self.gesture_display.add_vote(gesture_name, confidence)
    
    @Slot(bool)
    def _on_hand_detected(self, detected: bool):
        """Handle hand detection status."""
        if not detected:
            self.gesture_display.set_no_hand()
            if self._is_translating:
                # Allow same gesture to register again after hand re-enters
                self.engine.reset_held()
                self.pipeline.mark_no_hand()
    
    def _on_video_finished(self):
        """Handle video playback finished."""
        # Auto-translate when video ends
        result = self.engine.finalize()
        self.engine.clear()  # explicit clear after finalize
        if result and result.text:
            self._on_translation_updated(result)
        self.translation_display.set_status("Video complete")
    
    # === Pipeline Callbacks (legacy fallback) ===
    
    def _on_gesture_recognized(self, gesture: RecognizedGesture):
        """Handle gesture recognition from pipeline."""
        self.gesture_display.update_gesture(
            gesture.label,
            gesture.confidence,
            gesture.gesture_type.value
        )
    
    def _on_text_updated(self, text: str, preview: str):
        """Handle text update from pipeline."""
        self.translation_display.set_translation(text)
        self.translation_display.set_preview(preview)
        
        # Update statistics
        stats = self.pipeline.get_statistics()
        self.translation_display.set_statistics(
            stats.get('word_count', 0),
            stats.get('gesture_count', 0),
            0.0  # Will be set on completion
        )
    
    def _on_translation_complete(self, result: TranslationResult):
        """Handle translation completion."""
        self.translation_display.set_translation(result.text)
        self.translation_display.set_preview("")
        self.translation_display.set_statistics(
            result.word_count,
            result.gesture_count,
            result.confidence
        )
        
        self._save_translation(result)
    
    # === Actions ===
    
    def _copy_translation(self):
        """Copy translation to clipboard."""
        from PySide6.QtWidgets import QApplication
        text = self.translation_display.translation_text.text()
        if text and text != "Start signing to translate...":
            QApplication.clipboard().setText(text)
    
    def _clear_translation(self):
        """Clear current translation."""
        self.pipeline.clear()
        self.engine.clear()
        self.translation_display.clear()
        self.gesture_display.clear()
    
    def _insert_space(self):
        """Insert a word boundary."""
        # For simple engine, we don't need explicit space handling
        # The engine auto-detects word boundaries
        pass
    
    def _delete_last(self):
        """Delete last character/word."""
        # For simple engine, we can clear and restart
        # In future, implement proper deletion from buffer
        pass
    
    def _save_translation(self, result: TranslationResult):
        """Save translation to history."""
        if not self.db or self.user.get("guest"):
            return
        
        self.translation_made.emit(
            result.text,
            result.confidence,
            "sentence"
        )
    
    # === Lifecycle ===
    
    def stop_camera(self):
        """Stop the camera (called from main window on logout)."""
        if self._is_translating:
            self._stop_translation()
        self.camera_widget.stop()
    
    def cleanup(self):
        """Cleanup resources."""
        self._check_timer.stop()
        if self._is_translating:
            self._stop_translation()
        self.camera_widget.stop()
        self.video_widget.release()
        self.engine.stop()
