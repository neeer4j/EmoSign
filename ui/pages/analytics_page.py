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
        layout.setSpacing(20)

        # ── Get Data ──────────────────────────────────────────────
        progress = {}
        if analytics:
            progress = analytics.get_learning_progress(self.user_id)

        # ── HEADER ────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary']}15, stop:1 {COLORS['accent']}10);
                border: none;
                border-radius: 16px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 22, 28, 22)
        header_layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("📊 Analytics & Progress")
        title.setStyleSheet(f"""
            font-size: 24px; font-weight: 800;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        subtitle = QLabel("Track your sign language learning journey")
        subtitle.setStyleSheet(f"""
            font-size: 13px; color: {COLORS['text_muted']};
            background: transparent;
        """)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col, 1)

        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn, alignment=Qt.AlignVCenter)
        layout.addWidget(header)

        # ── STATS ROW ─────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)

        stats_meta = [
            ("✋", "Total Signs", str(progress.get('total_signs_detected', 0)), COLORS['primary']),
            ("📝", "Words Formed", str(progress.get('total_words', 0)), COLORS['accent']),
            ("🔥", "Day Streak", f"{progress.get('current_streak', 0)}", COLORS['warning']),
            ("⏱️", "Practice Time", f"{progress.get('total_practice_time', 0):.0f}m", COLORS['success']),
        ]

        for icon, label, value, color in stats_meta:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_card']};
                    border: none;
                    border-radius: 14px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 16, 18, 16)
            cl.setSpacing(8)

            top = QHBoxLayout()
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 18px; background: transparent;")
            tl = QLabel(label.upper())
            tl.setStyleSheet(f"""
                font-size: 10px; font-weight: 700;
                color: {COLORS['text_muted']};
                letter-spacing: 1px; background: transparent;
            """)
            top.addWidget(ic)
            top.addWidget(tl)
            top.addStretch()
            cl.addLayout(top)

            vl = QLabel(value)
            vl.setStyleSheet(f"""
                font-size: 26px; font-weight: 800;
                color: {color};
                background: transparent;
            """)
            cl.addWidget(vl)
            stats_row.addWidget(card, 1)

        layout.addLayout(stats_row)

        # ── LEARNING PROGRESS ─────────────────────────────────────
        sec_label = QLabel("🎯  LEARNING PROGRESS")
        sec_label.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {COLORS['text_muted']};
            letter-spacing: 1.5px; padding-top: 4px;
        """)
        layout.addWidget(sec_label)

        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 14px;
            }}
        """)
        pf_layout = QHBoxLayout(progress_frame)
        pf_layout.setContentsMargins(24, 24, 24, 24)
        pf_layout.setSpacing(24)

        letters = progress.get('letters_learned', 0)
        accuracy = progress.get('accuracy', 0)
        achievements_count = progress.get('achievements_unlocked', 0)
        total_achievements = progress.get('total_achievements', len(ACHIEVEMENTS))

        rings_data = [
            (letters, 26, "Alphabet", COLORS['primary']),
            (int(accuracy), 100, "Accuracy", COLORS['success']),
            (achievements_count, max(total_achievements, 1), "Achievements", COLORS['warning']),
        ]

        for value, max_val, label, color in rings_data:
            pct = int((value / max_val) * 100) if max_val > 0 else 0
            ring_w = QFrame()
            ring_w.setStyleSheet("background: transparent; border: none;")
            ring_w.setFixedWidth(120)
            rl = QVBoxLayout(ring_w)
            rl.setAlignment(Qt.AlignCenter)
            rl.setSpacing(8)

            circle = QLabel(f"{pct}%")
            circle.setStyleSheet(f"""
                font-size: 22px; font-weight: 700;
                color: {color};
                background: {COLORS['bg_input']};
                border: 4px solid {color};
                border-radius: 40px;
                min-width: 80px; min-height: 80px;
                max-width: 80px; max-height: 80px;
            """)
            circle.setAlignment(Qt.AlignCenter)
            rl.addWidget(circle, alignment=Qt.AlignCenter)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; background: transparent;")
            lbl.setAlignment(Qt.AlignCenter)
            rl.addWidget(lbl)

            val_lbl = QLabel(f"{value}/{max_val}")
            val_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
            val_lbl.setAlignment(Qt.AlignCenter)
            rl.addWidget(val_lbl)

            pf_layout.addWidget(ring_w)

        pf_layout.addStretch()
        layout.addWidget(progress_frame)

        # ── MOST USED SIGNS ───────────────────────────────────────
        sec_label2 = QLabel("📊  MOST USED SIGNS")
        sec_label2.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {COLORS['text_muted']};
            letter-spacing: 1.5px; padding-top: 4px;
        """)
        layout.addWidget(sec_label2)

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

        # ── ACHIEVEMENTS ──────────────────────────────────────────
        ach_header = QHBoxLayout()
        sec_label3 = QLabel("🏆  ACHIEVEMENTS")
        sec_label3.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {COLORS['text_muted']};
            letter-spacing: 1.5px; padding-top: 4px;
        """)
        ach_header.addWidget(sec_label3)
        ach_header.addStretch()

        pts = QLabel(f"⭐ {progress.get('total_points', 0)} pts")
        pts.setStyleSheet(f"""
            font-size: 13px; font-weight: 700;
            color: {COLORS['warning']};
            background: transparent;
        """)
        ach_header.addWidget(pts)
        layout.addLayout(ach_header)

        badges_frame = QFrame()
        badges_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 14px;
            }}
        """)
        badges_grid = QGridLayout(badges_frame)
        badges_grid.setContentsMargins(16, 16, 16, 16)
        badges_grid.setSpacing(12)

        achievements_data = {}
        if analytics:
            achievements_data = analytics.get_achievements(self.user_id)

        achievement_list = achievements_data.get('achievements', [])
        if not achievement_list:
            achievement_list = [
                {'icon': '👶', 'name': 'First Sign', 'description': 'Detect your first sign', 'unlocked': False, 'points': 5},
                {'icon': '🌱', 'name': 'Getting Started', 'description': 'Detect 10 signs', 'unlocked': False, 'points': 10},
                {'icon': '✋', 'name': 'Regular Signer', 'description': 'Detect 50 signs', 'unlocked': False, 'points': 25},
                {'icon': '🔥', 'name': 'Dedicated', 'description': 'Detect 100 signs', 'unlocked': False, 'points': 50},
                {'icon': '🔤', 'name': 'ABC Master', 'description': 'Learn all 26 letters', 'unlocked': False, 'points': 100},
                {'icon': '📅', 'name': 'Week Warrior', 'description': '7-day streak', 'unlocked': False, 'points': 70},
            ]

        for i, ach in enumerate(achievement_list[:12]):
            unlocked = ach.get('unlocked', False)
            badge = QFrame()
            badge.setFixedHeight(110)
            badge.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_card_hover'] if unlocked else COLORS['bg_input']};
                    border: none;
                    border-radius: 12px;
                }}
            """)
            bl = QVBoxLayout(badge)
            bl.setContentsMargins(10, 10, 10, 10)
            bl.setSpacing(4)
            bl.setAlignment(Qt.AlignCenter)

            icon_lbl = QLabel(ach.get('icon', '🏆'))
            icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")
            icon_lbl.setAlignment(Qt.AlignCenter)
            bl.addWidget(icon_lbl)

            name_lbl = QLabel(ach.get('name', 'Achievement'))
            name_lbl.setStyleSheet(f"""
                font-size: 11px; font-weight: 600;
                color: {COLORS['text_primary'] if unlocked else COLORS['text_muted']};
                background: transparent;
            """)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setWordWrap(True)
            bl.addWidget(name_lbl)

            if unlocked:
                pts_lbl = QLabel(f"+{ach.get('points', 0)}")
                pts_lbl.setStyleSheet(f"color: {COLORS['success']}; font-size: 10px; font-weight: 700; background: transparent;")
                pts_lbl.setAlignment(Qt.AlignCenter)
                bl.addWidget(pts_lbl)

            badges_grid.addWidget(badge, i // 6, i % 6)

        layout.addWidget(badges_frame)

        # ── RECOMMENDATIONS ───────────────────────────────────────
        sec_label4 = QLabel("💡  RECOMMENDATIONS")
        sec_label4.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {COLORS['text_muted']};
            letter-spacing: 1.5px; padding-top: 4px;
        """)
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
