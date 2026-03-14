"""
Dashboard Page - Main hub after login
Beautiful overview with stats and quick navigation
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS

# Import analytics for streak data
try:
    from core.analytics import analytics
except ImportError:
    analytics = None


class StatCard(QFrame):
    """Animated statistic card with icon and value."""
    
    def __init__(self, icon, value, label, color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.color = color or COLORS['primary']
        self._setup_ui(icon, value, label)
        self._setup_hover_effect()
    
    def _setup_ui(self, icon, value, label):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(44, 44)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color}15;
                border-radius: 12px;
                border: 1px solid {self.color}30;
            }}
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("statsNumber")
        self.value_label.setStyleSheet(f"color: {self.color};")
        
        # Label
        self.label_label = QLabel(label)
        self.label_label.setObjectName("statsLabel")
        
        layout.addWidget(icon_container)
        layout.addStretch()
        layout.addWidget(self.value_label)
        layout.addWidget(self.label_label)
    
    def _setup_hover_effect(self):
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(0)
        self.shadow.setColor(QColor(self.color))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
    
    def enterEvent(self, event):
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim.setDuration(200)
        self.anim.setStartValue(0)
        self.anim.setEndValue(30)
        self.anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim.setDuration(200)
        self.anim.setStartValue(30)
        self.anim.setEndValue(0)
        self.anim.start()
        super().leaveEvent(event)
    
    def update_value(self, value):
        self.value_label.setText(str(value))


class QuickActionCard(QFrame):
    """Large action card for main navigation."""
    
    clicked = Signal()
    
    def __init__(self, icon, title, description, color, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.color = color
        self._setup_ui(icon, title, description)
        self._apply_style()
    
    def _setup_ui(self, icon, title, description):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Icon (left side)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Content (middle)
        content = QVBoxLayout()
        content.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
            border: none;
        """)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_muted']};
            background: transparent;
            border: none;
        """)
        
        content.addWidget(title_label)
        content.addWidget(desc_label)
        layout.addLayout(content)
        
        layout.addStretch()
        
        # Arrow (right side)
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px; background: transparent; border: none;")
        layout.addWidget(arrow)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-left: 3px solid {self.color};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {self.color}60;
            }}
        """)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class DashboardPage(QWidget):
    """Main dashboard with overview and quick navigation."""
    
    # Navigation signals
    navigate_to_live = Signal()
    navigate_to_history = Signal()
    navigate_to_profile = Signal()
    navigate_to_training = Signal()
    navigate_to_tutorial = Signal()
    navigate_to_game = Signal()
    navigate_to_analytics = Signal()
    navigate_to_study = Signal()
    navigate_to_quiz = Signal()
    
    def __init__(self, user_data=None, db_service=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.db = db_service
        self._setup_ui()
        self._load_stats()
    
    def _setup_ui(self):
        """Setup dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)
        
        # === HEADER ===
        header = QHBoxLayout()
        
        # Welcome section
        welcome_box = QVBoxLayout()
        welcome_box.setSpacing(2)
        
        username = self._get_username()
        greeting = self._get_greeting()
        self._welcome_label = QLabel(f"{greeting}, {username}! 👋")
        self._welcome_label.setObjectName("welcomeText")
        
        subtitle = QLabel("Choose a learning mode and keep your streak alive.")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        
        welcome_box.addWidget(self._welcome_label)
        welcome_box.addWidget(subtitle)
        
        header.addLayout(welcome_box)
        header.addStretch()
        
        # Quick action buttons in header
        self._profile_btn = None
        if not self.user.get("guest"):
            self._profile_btn = QPushButton(f"👤 {username[:8]}")
            self._profile_btn.setObjectName("ghost")
            self._profile_btn.clicked.connect(self.navigate_to_profile.emit)
            header.addWidget(self._profile_btn)
        
        main_layout.addLayout(header)
        
        # === LEARNING STATS ROW ===
        stats_label = QLabel("📈 Learning Progress Snapshot")
        stats_label.setObjectName("sectionTitle")
        main_layout.addWidget(stats_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.signs_learned_card = StatCard("🔤", "0", "Signs Learned", COLORS['primary'])
        self.accuracy_card = StatCard("🎯", "0%", "Recognition Accuracy", COLORS['accent'])
        self.streak_card = StatCard("🔥", "0", "Day Streak", COLORS['warning'])
        self.points_card = StatCard("🏆", "0", "Learning Points", COLORS['success'])
        
        stats_layout.addWidget(self.signs_learned_card)
        stats_layout.addWidget(self.accuracy_card)
        stats_layout.addWidget(self.streak_card)
        stats_layout.addWidget(self.points_card)
        
        main_layout.addLayout(stats_layout)
        
        # === LEARNING MODES ===
        actions_label = QLabel("🎓 Learning Modes")
        actions_label.setObjectName("sectionTitle")
        main_layout.addWidget(actions_label)
        
        actions_layout = QGridLayout()
        actions_layout.setSpacing(16)
        
        # Guided lessons (no camera required)
        tutorial_card = QuickActionCard(
            "📚",
            "Guided Lessons",
            "Learn signs step-by-step with visual guidance",
            COLORS['primary']
        )
        tutorial_card.clicked.connect(self.navigate_to_tutorial.emit)

        # Self-study flashcards (no camera required)
        study_card = QuickActionCard(
            "🧾",
            "Self Study",
            "Review sign cards and finger patterns offline",
            COLORS['success']
        )
        study_card.clicked.connect(self.navigate_to_study.emit)

        # Quiz mode (no camera required)
        quiz_card = QuickActionCard(
            "❓",
            "Quiz Mode",
            "Test recall with multiple-choice drills",
            COLORS['warning']
        )
        quiz_card.clicked.connect(self.navigate_to_quiz.emit)

        # Practice lab (camera optional, lower confidence in weak conditions)
        practice_card = QuickActionCard(
            "🔴",
            "Practice Lab",
            "Use live recognition to rehearse signs",
            COLORS['accent']
        )
        practice_card.clicked.connect(self.navigate_to_live.emit)

        # Challenge mode
        game_card = QuickActionCard(
            "🎮",
            "Challenge Mode",
            "Boost speed and confidence with mini challenges",
            COLORS['success']
        )
        game_card.clicked.connect(self.navigate_to_game.emit)

        # Progress and goals
        progress_card = QuickActionCard(
            "📊",
            "Progress & Goals",
            "Track streaks, accuracy, and achievements",
            COLORS['warning']
        )
        progress_card.clicked.connect(self.navigate_to_analytics.emit)

        actions_layout.addWidget(tutorial_card, 0, 0)
        actions_layout.addWidget(study_card, 0, 1)
        actions_layout.addWidget(quiz_card, 1, 0)
        actions_layout.addWidget(practice_card, 1, 1)
        actions_layout.addWidget(game_card, 2, 0)
        actions_layout.addWidget(progress_card, 2, 1)
        
        main_layout.addLayout(actions_layout)
        
        # === TIPS SECTION ===
        tips_frame = QFrame()
        tips_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['warning_bg']};
                border: 1px solid {COLORS['warning']}30;
                border-radius: 10px;
            }}
        """)
        tips_layout = QHBoxLayout(tips_frame)
        tips_layout.setContentsMargins(14, 10, 14, 10)
        tips_layout.setSpacing(10)
        
        tip_icon = QLabel("💡")
        tip_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        
        tip_text = QLabel("Tip: Short daily sessions improve retention and streaks faster than long occasional sessions.")
        tip_text.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        
        tips_layout.addWidget(tip_icon)
        tips_layout.addWidget(tip_text)
        tips_layout.addStretch()
        
        main_layout.addWidget(tips_frame)
        main_layout.addStretch()
    
    def _get_username(self) -> str:
        """Derive display name from user data."""
        email = self.user.get("email", "") if self.user else ""
        raw = (
            (self.user or {}).get("username")
            or (self.user or {}).get("display_name")
            or (self.user or {}).get("name")
            or (email.split("@")[0] if "@" in email else email)
            or "User"
        )
        return raw.capitalize() if raw.islower() else raw

    def _get_greeting(self):
        """Get time-appropriate greeting."""
        from datetime import datetime
        hour = datetime.now().hour
        
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"
    
    def _load_stats(self):
        """Load user statistics with learning-first metrics."""
        if self.user.get("guest"):
            return
        
        try:
            user_id = self.user.get('id', 'guest')

            # Prefer analytics for learning platform stats
            if analytics:
                progress = analytics.get_learning_progress(user_id)
                self.signs_learned_card.update_value(progress.get('signs_learned', 0))
                self.accuracy_card.update_value(f"{progress.get('accuracy', 0):.0f}%")
                self.streak_card.update_value(progress.get('current_streak', 0))
                self.points_card.update_value(progress.get('total_points', 0))
                return

            # Fallback to DB translation stats if analytics is unavailable
            if self.db:
                import asyncio
                loop = asyncio.new_event_loop()
                stats = loop.run_until_complete(
                    self.db.get_translation_stats(self.user.get("id", ""))
                )
                loop.close()

                self.signs_learned_card.update_value(stats.get("unique_signs", 0))
                self.accuracy_card.update_value("0%")
                self.streak_card.update_value(0)
                self.points_card.update_value(stats.get("total", 0))
        except Exception as e:
            print(f"Failed to load stats: {e}")
    
    def update_user(self, user_data):
        """Update user data and refresh greeting + stats."""
        self.user = user_data
        username = self._get_username()
        self._welcome_label.setText(f"{self._get_greeting()}, {username}! 👋")
        if self._profile_btn is not None:
            self._profile_btn.setText(f"👤 {username[:8]}")
        self._load_stats()
    
    def refresh_stats(self):
        """Refresh statistics."""
        self._load_stats()
