"""
Analytics Page - Usage statistics and learning progress visualization

Displays:
- Usage analytics (most used signs, session stats)
- Learning progress with charts
- Achievements and badges
- Recommendations
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QProgressBar,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS

# Try to import analytics
try:
    from core.analytics import analytics, ACHIEVEMENTS
except ImportError:
    analytics = None
    ACHIEVEMENTS = {}


class StatCard(QFrame):
    """A card displaying a single statistic."""
    
    def __init__(self, title: str, value: str, icon: str, 
                 color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(120)
        
        color = color or COLORS['primary']
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 28px; background: transparent;")
        layout.addWidget(icon_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {color};
            background: transparent;
        """)
        layout.addWidget(value_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: transparent;")
        layout.addWidget(title_label)


class AchievementBadge(QFrame):
    """A badge representing an achievement."""
    
    def __init__(self, icon: str, name: str, description: str,
                 unlocked: bool = False, points: int = 0, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 160)
        
        bg_color = COLORS['bg_card'] if unlocked else COLORS['bg_input']
        opacity = "1" if unlocked else "0.5"
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 12px;
                border: 2px solid {COLORS['primary'] if unlocked else COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 40px; 
            background: transparent;
            opacity: {opacity};
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {COLORS['text_primary'] if unlocked else COLORS['text_muted']};
            background: transparent;
        """)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Points
        if unlocked:
            points_label = QLabel(f"+{points} pts")
            points_label.setStyleSheet(f"""
                color: {COLORS['success']};
                font-size: 11px;
                font-weight: 600;
                background: transparent;
            """)
            points_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(points_label)
        else:
            desc_label = QLabel(description)
            desc_label.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                font-size: 10px;
                background: transparent;
            """)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)


class ProgressRing(QFrame):
    """A circular progress indicator."""
    
    def __init__(self, value: int, max_value: int, label: str,
                 color: str = None, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 140)
        
        color = color or COLORS['primary']
        percentage = int((value / max_value) * 100) if max_value > 0 else 0
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        # Circle with percentage
        circle = QLabel(f"{percentage}%")
        circle.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {color};
            background: {COLORS['bg_input']};
            border: 4px solid {color};
            border-radius: 40px;
            min-width: 80px;
            min-height: 80px;
            max-width: 80px;
            max-height: 80px;
        """)
        circle.setAlignment(Qt.AlignCenter)
        layout.addWidget(circle, alignment=Qt.AlignCenter)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)


class AnalyticsPage(QWidget):
    """Analytics and progress page."""
    
    back_requested = Signal()
    
    def __init__(self, user_id: str = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id or "guest"
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
        
        title = QLabel("📊 Analytics & Progress")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        
        # ============ Overview Stats ============
        stats_section = QLabel("📈 Overview")
        stats_section.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLORS['text_primary']};")
        content_layout.addWidget(stats_section)
        
        stats_grid = QGridLayout()
        stats_grid.setSpacing(16)
        
        # Get stats from analytics
        progress = {}
        if analytics:
            progress = analytics.get_learning_progress(self.user_id)
        
        stats = [
            ("Total Signs", str(progress.get('total_signs_detected', 0)), "✋", COLORS['primary']),
            ("Words Formed", str(progress.get('total_words', 0)), "📝", COLORS['accent']),
            ("Current Streak", f"{progress.get('current_streak', 0)} days", "🔥", COLORS['warning']),
            ("Practice Time", f"{progress.get('total_practice_time', 0):.0f} min", "⏱️", COLORS['success']),
        ]
        
        for i, (title, value, icon, color) in enumerate(stats):
            card = StatCard(title, value, icon, color)
            stats_grid.addWidget(card, 0, i)
        
        content_layout.addLayout(stats_grid)
        
        # ============ Learning Progress ============
        progress_section = QLabel("🎯 Learning Progress")
        progress_section.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLORS['text_primary']};")
        content_layout.addWidget(progress_section)
        
        progress_frame = QFrame()
        progress_frame.setObjectName("card")
        progress_layout = QHBoxLayout(progress_frame)
        progress_layout.setContentsMargins(24, 24, 24, 24)
        progress_layout.setSpacing(32)
        
        # Progress rings
        letters = progress.get('letters_learned', 0)
        accuracy = progress.get('accuracy', 0)
        achievements = progress.get('achievements_unlocked', 0)
        total_achievements = progress.get('total_achievements', len(ACHIEVEMENTS))
        
        rings = [
            (letters, 26, "Alphabet", COLORS['primary']),
            (int(accuracy), 100, "Accuracy", COLORS['success']),
            (achievements, total_achievements, "Achievements", COLORS['warning']),
        ]
        
        for value, max_val, label, color in rings:
            ring = ProgressRing(value, max_val, label, color)
            progress_layout.addWidget(ring)
        
        progress_layout.addStretch()
        content_layout.addWidget(progress_frame)
        
        # ============ Most Used Signs ============
        usage_section = QLabel("📊 Most Used Signs")
        usage_section.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLORS['text_primary']};")
        content_layout.addWidget(usage_section)
        
        usage_frame = QFrame()
        usage_frame.setObjectName("card")
        usage_layout = QVBoxLayout(usage_frame)
        usage_layout.setContentsMargins(20, 16, 20, 16)
        
        # Get most used signs
        most_used = []
        if analytics:
            most_used = analytics.get_most_used_signs(self.user_id, 5)
        
        if most_used:
            max_count = most_used[0][1] if most_used else 1
            for sign, count in most_used:
                row = QHBoxLayout()
                
                sign_label = QLabel(sign)
                sign_label.setStyleSheet(f"""
                    font-size: 18px;
                    font-weight: 600;
                    color: {COLORS['text_primary']};
                    min-width: 40px;
                """)
                row.addWidget(sign_label)
                
                bar = QProgressBar()
                bar.setMaximum(max_count)
                bar.setValue(count)
                bar.setTextVisible(False)
                bar.setFixedHeight(12)
                bar.setStyleSheet(f"""
                    QProgressBar {{
                        background: {COLORS['bg_input']};
                        border-radius: 6px;
                    }}
                    QProgressBar::chunk {{
                        background: {COLORS['primary']};
                        border-radius: 6px;
                    }}
                """)
                row.addWidget(bar, stretch=1)
                
                count_label = QLabel(str(count))
                count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 40px;")
                count_label.setAlignment(Qt.AlignRight)
                row.addWidget(count_label)
                
                usage_layout.addLayout(row)
        else:
            empty_label = QLabel("No usage data yet. Start signing!")
            empty_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            usage_layout.addWidget(empty_label)
        
        content_layout.addWidget(usage_frame)
        
        # ============ Achievements ============
        achievements_section = QLabel("🏆 Achievements")
        achievements_section.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLORS['text_primary']};")
        content_layout.addWidget(achievements_section)
        
        # Points display
        points_label = QLabel(f"Total Points: {progress.get('total_points', 0)}")
        points_label.setStyleSheet(f"color: {COLORS['warning']}; font-weight: 600;")
        content_layout.addWidget(points_label)
        
        # Achievement badges
        badges_frame = QFrame()
        badges_layout = QGridLayout(badges_frame)
        badges_layout.setSpacing(12)
        
        achievements_data = {}
        if analytics:
            achievements_data = analytics.get_achievements(self.user_id)
        
        achievement_list = achievements_data.get('achievements', [])
        if not achievement_list:
            # Show placeholder achievements
            achievement_list = [
                {'icon': '👶', 'name': 'First Sign', 'description': 'Detect your first sign', 'unlocked': False, 'points': 5},
                {'icon': '🌱', 'name': 'Getting Started', 'description': 'Detect 10 signs', 'unlocked': False, 'points': 10},
                {'icon': '✋', 'name': 'Regular Signer', 'description': 'Detect 50 signs', 'unlocked': False, 'points': 25},
                {'icon': '🔥', 'name': 'Dedicated Learner', 'description': 'Detect 100 signs', 'unlocked': False, 'points': 50},
                {'icon': '🔤', 'name': 'ABC Master', 'description': 'Learn all 26 letters', 'unlocked': False, 'points': 100},
                {'icon': '📅', 'name': 'Week Warrior', 'description': '7-day streak', 'unlocked': False, 'points': 70},
            ]
        
        for i, achievement in enumerate(achievement_list[:12]):
            badge = AchievementBadge(
                achievement.get('icon', '🏆'),
                achievement.get('name', 'Achievement'),
                achievement.get('description', ''),
                achievement.get('unlocked', False),
                achievement.get('points', 10)
            )
            badges_layout.addWidget(badge, i // 6, i % 6)
        
        content_layout.addWidget(badges_frame)
        
        # ============ Recommendations ============
        rec_section = QLabel("💡 Recommendations")
        rec_section.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {COLORS['text_primary']};")
        content_layout.addWidget(rec_section)
        
        rec_frame = QFrame()
        rec_frame.setObjectName("card")
        rec_layout = QVBoxLayout(rec_frame)
        rec_layout.setContentsMargins(20, 16, 20, 16)
        
        recommendations = []
        if analytics:
            recommendations = analytics.get_recommendations(self.user_id)
        
        if not recommendations:
            recommendations = [
                "Start practicing to get personalized recommendations!",
                "Try learning the alphabet first.",
                "Practice daily to build a streak!"
            ]
        
        for rec in recommendations:
            rec_item = QLabel(f"• {rec}")
            rec_item.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px 0;")
            rec_item.setWordWrap(True)
            rec_layout.addWidget(rec_item)
        
        content_layout.addWidget(rec_frame)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def update_user(self, user_id: str):
        """Update the user and refresh data."""
        self.user_id = user_id
        # Would need to rebuild UI or refresh data
    
    def refresh(self):
        """Refresh analytics data."""
        # Rebuild the UI with fresh data
        pass
