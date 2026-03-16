"""
Analytics Page — Premium usage statistics and learning progress.

Displays:
- Usage analytics (most used signs, session stats)
- Learning progress with visual indicators
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


class AnalyticsPage(QWidget):
    """Analytics and progress page — premium design."""

    back_requested = Signal()

    def __init__(self, user_id: str = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id or "guest"
        self.main_layout = None
        self.scroll_area = None
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Scrollable content area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent; border: none;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        self.main_layout.addWidget(self.scroll_area)

        self._build_content()

    def _build_content(self):
        """Build the content area with current data."""
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        progress = {}
        if analytics:
            progress = analytics.get_learning_progress(self.user_id)

        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(16)

        title = QLabel("📊 Analytics & Progress")
        title.setStyleSheet(f"""
            font-size: 20px; font-weight: 800;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_card_hover']};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn, alignment=Qt.AlignVCenter)
        layout.addWidget(header)

        summary = QFrame()
        summary.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)
        summary_layout = QGridLayout(summary)
        summary_layout.setContentsMargins(16, 14, 16, 14)
        summary_layout.setHorizontalSpacing(12)
        summary_layout.setVerticalSpacing(10)

        stats_meta = [
            ("Total Signs", str(progress.get('total_signs_detected', 0))),
            ("Words Formed", str(progress.get('total_words', 0))),
            ("Current Streak", str(progress.get('current_streak', 0))),
            ("Practice Time", f"{progress.get('total_practice_time', 0):.0f}m"),
            ("Alphabet", f"{progress.get('letters_learned', 0)}/26"),
            ("Accuracy", f"{progress.get('accuracy', 0):.0f}%"),
        ]

        for i, (label, value) in enumerate(stats_meta):
            tile = QFrame()
            tile.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_input']};
                    border: none;
                    border-radius: 10px;
                }}
            """)
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(12, 10, 12, 10)
            tl.setSpacing(3)

            title_lbl = QLabel(label)
            title_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
            value_lbl = QLabel(value)
            value_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 19px; font-weight: 800; background: transparent;")

            tl.addWidget(title_lbl)
            tl.addWidget(value_lbl)

            row = i // 3
            col = i % 3
            summary_layout.addWidget(tile, row, col)

        layout.addWidget(summary)

        section_title = QLabel("Most Used Signs")
        section_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text_primary']};")
        layout.addWidget(section_title)

        usage_frame = QFrame()
        usage_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 14px;
            }}
        """)
        usage_layout = QVBoxLayout(usage_frame)
        usage_layout.setContentsMargins(24, 20, 24, 20)
        usage_layout.setSpacing(12)

        most_used = []
        if analytics:
            most_used = analytics.get_most_used_signs(self.user_id, 5)

        if most_used:
            max_count = most_used[0][1] if most_used else 1
            for sign, count in most_used:
                row = QHBoxLayout()
                row.setSpacing(12)

                sign_label = QLabel(sign)
                sign_label.setStyleSheet(f"""
                    font-size: 18px; font-weight: 700;
                    color: {COLORS['text_primary']};
                    background: transparent;
                    min-width: 30px;
                """)
                row.addWidget(sign_label)

                bar = QProgressBar()
                bar.setMaximum(max_count)
                bar.setValue(count)
                bar.setTextVisible(False)
                bar.setFixedHeight(10)
                bar.setStyleSheet(f"""
                    QProgressBar {{
                        background: {COLORS['bg_input']};
                        border-radius: 5px;
                        border: none;
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                        border-radius: 5px;
                    }}
                """)
                row.addWidget(bar, stretch=1)

                count_label = QLabel(str(count))
                count_label.setStyleSheet(f"""
                    color: {COLORS['text_muted']};
                    font-size: 12px; font-weight: 600;
                    min-width: 30px; background: transparent;
                """)
                count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                row.addWidget(count_label)

                usage_layout.addLayout(row)
        else:
            empty = QLabel("No usage data yet — start signing! ✋")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 24px; font-size: 13px;")
            empty.setAlignment(Qt.AlignCenter)
            usage_layout.addWidget(empty)

        layout.addWidget(usage_frame)

        points = QLabel(f"⭐ Total Points: {progress.get('total_points', 0)}")
        points.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {COLORS['warning']};")
        layout.addWidget(points)

        sec_label4 = QLabel("Recommendations")
        sec_label4.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['text_primary']};")
        layout.addWidget(sec_label4)

        rec_frame = QFrame()
        rec_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 14px;
            }}
        """)
        rec_layout = QVBoxLayout(rec_frame)
        rec_layout.setContentsMargins(24, 20, 24, 20)
        rec_layout.setSpacing(8)

        recommendations = []
        if analytics:
            recommendations = analytics.get_recommendations(self.user_id)

        if not recommendations:
            recommendations = [
                "Start practicing to get personalized recommendations!",
                "Try learning the alphabet first — go to Tutorials.",
                "Practice daily to build a streak!"
            ]

        for rec in recommendations:
            rec_item = QLabel(f"•  {rec}")
            rec_item.setStyleSheet(f"""
                color: {COLORS['text_secondary']};
                font-size: 13px;
                padding: 4px 0;
                background: transparent;
            """)
            rec_item.setWordWrap(True)
            rec_layout.addWidget(rec_item)

        layout.addWidget(rec_frame)

        layout.addStretch()
        self.scroll_area.setWidget(content)

    def update_user(self, user_id: str):
        """Update the user and refresh data."""
        self.user_id = user_id
        self.refresh()

    def refresh(self):
        """Refresh analytics data by rebuilding the content."""
        old_widget = self.scroll_area.widget()
        if old_widget:
            old_widget.deleteLater()
        self._build_content()
