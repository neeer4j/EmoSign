"""
Tutorial Page - Interactive ASL Learning Guide

Provides step-by-step tutorials for learning ASL:
- Alphabet lessons
- Common words and phrases
- Practice mode with feedback
- Progress tracking
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QProgressBar, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS


class LessonCard(QFrame):
    """A card representing a lesson."""
    
    clicked = Signal(str)  # lesson_id
    
    def __init__(self, lesson_id: str, title: str, description: str,
                 icon: str, progress: int = 0, parent=None):
        super().__init__(parent)
        self.lesson_id = lesson_id
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(160)
        self._setup_ui(title, description, icon, progress)
    
    def _setup_ui(self, title, description, icon, progress):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Icon and title row
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setValue(progress)
        progress_bar.setFixedHeight(6)
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(progress_bar)
        
        # Progress text
        progress_text = QLabel(f"{progress}% Complete")
        progress_text.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent;")
        layout.addWidget(progress_text)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.lesson_id)


class AlphabetLesson(QWidget):
    """Interactive alphabet learning lesson."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_letter_index = 0
        self.letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)
        
        title = QLabel("🔤 Learn the Alphabet")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(26)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Main content
        content = QFrame()
        content.setObjectName("card")
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(24)
        
        # Current letter display
        self.letter_label = QLabel("A")
        self.letter_label.setStyleSheet(f"""
            font-size: 120px;
            font-weight: 700;
            color: {COLORS['primary']};
            background: transparent;
        """)
        self.letter_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.letter_label)
        
        # Hand shape description
        self.description_label = QLabel("Fist with thumb to side")
        self.description_label.setStyleSheet(f"""
            font-size: 18px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        self.description_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.description_label)
        
        # Instructions
        instruction = QLabel("Show this sign to your camera to continue")
        instruction.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        instruction.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(instruction)
        
        # Status
        self.status_label = QLabel("👋 Position your hand in front of the camera")
        self.status_label.setStyleSheet(f"""
            font-size: 16px;
            color: {COLORS['accent']};
            background: {COLORS['bg_input']};
            padding: 16px;
            border-radius: 8px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        layout.addWidget(content)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setObjectName("secondaryButton")
        self.prev_btn.clicked.connect(self._prev_letter)
        nav_layout.addWidget(self.prev_btn)
        
        nav_layout.addStretch()
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.setObjectName("primaryButton")
        self.next_btn.clicked.connect(self._next_letter)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        self._update_display()
    
    def _update_display(self):
        """Update the display for the current letter."""
        letter = self.letters[self.current_letter_index]
        self.letter_label.setText(letter)
        self.progress_bar.setValue(self.current_letter_index + 1)
        
        # Update description based on letter
        descriptions = {
            'A': 'Fist with thumb to side',
            'B': 'Flat hand, fingers together',
            'C': 'Curved hand like holding cup',
            'D': 'Index up, others touch thumb',
            'E': 'Fingers curled over thumb',
            'F': 'OK sign, 3 fingers up',
            'G': 'Pointing hand horizontal',
            'H': 'Two fingers out horizontal',
            'I': 'Pinky finger up only',
            'J': 'Pinky draws J shape',
            'K': 'Peace sign with thumb',
            'L': 'L shape with thumb and index',
            'M': 'Three fingers over thumb',
            'N': 'Two fingers over thumb',
            'O': 'Fingers form O shape',
            'P': 'K shape pointing down',
            'Q': 'G shape pointing down',
            'R': 'Crossed index and middle',
            'S': 'Fist with thumb over fingers',
            'T': 'Thumb between fingers',
            'U': 'Two fingers up together',
            'V': 'Peace sign',
            'W': 'Three fingers up spread',
            'X': 'Hooked index finger',
            'Y': 'Hang loose (thumb + pinky)',
            'Z': 'Index draws Z in air',
        }
        self.description_label.setText(descriptions.get(letter, ""))
        
        # Update navigation buttons
        self.prev_btn.setEnabled(self.current_letter_index > 0)
        self.next_btn.setText("Complete ✓" if self.current_letter_index == 25 else "Next →")
    
    def _prev_letter(self):
        if self.current_letter_index > 0:
            self.current_letter_index -= 1
            self._update_display()
    
    def _next_letter(self):
        if self.current_letter_index < 25:
            self.current_letter_index += 1
            self._update_display()
        else:
            self.back_requested.emit()
    
    def on_sign_detected(self, sign: str, confidence: float):
        """Handle when a sign is detected."""
        expected = self.letters[self.current_letter_index]
        if sign.upper() == expected and confidence > 0.7:
            self.status_label.setText(f"✅ Correct! You signed '{expected}'")
            self.status_label.setStyleSheet(f"""
                font-size: 16px;
                color: {COLORS['success']};
                background: {COLORS['success_bg']};
                padding: 16px;
                border-radius: 8px;
            """)
            # Auto-advance after delay
            QTimer.singleShot(1500, self._next_letter)
        else:
            self.status_label.setText(f"Detected: {sign} - Keep trying for {expected}")


class TutorialPage(QWidget):
    """Main tutorial and learning page."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)
        
        title = QLabel("📚 Learn Sign Language")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Stacked widget for lessons
        self.stack = QStackedWidget()
        
        # Main lesson list
        self.lesson_list = self._create_lesson_list()
        self.stack.addWidget(self.lesson_list)
        
        # Alphabet lesson
        self.alphabet_lesson = AlphabetLesson()
        self.alphabet_lesson.back_requested.connect(self._show_lesson_list)
        self.stack.addWidget(self.alphabet_lesson)
        
        layout.addWidget(self.stack)
    
    def _create_lesson_list(self) -> QWidget:
        """Create the main lesson list."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Welcome message
        welcome = QFrame()
        welcome.setObjectName("card")
        welcome_layout = QVBoxLayout(welcome)
        
        welcome_title = QLabel("👋 Welcome to ASL Learning!")
        welcome_title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {COLORS['text_primary']};")
        welcome_layout.addWidget(welcome_title)
        
        welcome_text = QLabel(
            "Learn American Sign Language through interactive lessons. "
            "Start with the alphabet and work your way up to common phrases."
        )
        welcome_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        welcome_text.setWordWrap(True)
        welcome_layout.addWidget(welcome_text)
        
        layout.addWidget(welcome)
        
        # Lesson categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # Beginner lessons
        beginner_label = QLabel("🌱 Beginner")
        beginner_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};")
        scroll_layout.addWidget(beginner_label)
        
        lessons_grid = QGridLayout()
        lessons_grid.setSpacing(16)
        
        lessons = [
            ("alphabet", "The Alphabet", "Learn A-Z fingerspelling", "🔤", 0),
            ("numbers", "Numbers 0-9", "Count from zero to nine", "🔢", 0),
            ("greetings", "Greetings", "Hello, goodbye, and more", "👋", 0),
            ("basics", "Basic Words", "Yes, no, please, thank you", "💬", 0),
        ]
        
        for i, (lid, title, desc, icon, progress) in enumerate(lessons):
            card = LessonCard(lid, title, desc, icon, progress)
            card.clicked.connect(self._open_lesson)
            lessons_grid.addWidget(card, i // 2, i % 2)
        
        scroll_layout.addLayout(lessons_grid)
        
        # Intermediate lessons
        inter_label = QLabel("📈 Intermediate")
        inter_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};")
        scroll_layout.addWidget(inter_label)
        
        inter_lessons = [
            ("questions", "Questions", "What, where, when, why, how", "❓", 0),
            ("emotions", "Emotions", "Happy, sad, angry, scared", "😊", 0),
            ("family", "Family", "Mom, dad, sister, brother", "👨‍👩‍👧‍👦", 0),
            ("actions", "Actions", "Go, stop, help, want", "🏃", 0),
        ]
        
        inter_grid = QGridLayout()
        inter_grid.setSpacing(16)
        
        for i, (lid, title, desc, icon, progress) in enumerate(inter_lessons):
            card = LessonCard(lid, title, desc, icon, progress)
            card.clicked.connect(self._open_lesson)
            inter_grid.addWidget(card, i // 2, i % 2)
        
        scroll_layout.addLayout(inter_grid)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _open_lesson(self, lesson_id: str):
        """Open a specific lesson."""
        if lesson_id == "alphabet":
            self.stack.setCurrentWidget(self.alphabet_lesson)
        # Add more lesson handlers as needed
    
    def _show_lesson_list(self):
        """Return to the lesson list."""
        self.stack.setCurrentWidget(self.lesson_list)
