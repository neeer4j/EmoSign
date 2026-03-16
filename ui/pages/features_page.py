"""
Features Page - In-app guide to application capabilities.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from typing import List

from ui.styles import COLORS
from ui.page_header import make_page_header


class FeaturesPage(QWidget):
    """Shows what the app does and how to use each major feature."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _feature_card(self, title: str, subtitle: str, bullets: List[str]) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: 700;"
        )
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setWordWrap(True)
        subtitle_lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        layout.addWidget(subtitle_lbl)

        for bullet in bullets:
            b = QLabel(f"• {bullet}")
            b.setWordWrap(True)
            b.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 12px;"
            )
            layout.addWidget(b)

        return card

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        header, _ = make_page_header("✨ Features")
        root.addLayout(header)

        subtitle = QLabel(
            "Quick guide to what each mode does and how to use it effectively."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px;"
        )
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(0, 0, 8, 0)

        cards = [
            (
                "🔴 Practice Lab (Live Translation)",
                "Real-time sign recognition from camera.",
                [
                    "Show one clear sign at a time with good lighting.",
                    "Model outputs label + confidence and logs analytics.",
                    "Use this mode for free-form daily practice.",
                ],
            ),
            (
                "📚 Tutorials",
                "Step-by-step learning for alphabets and gestures.",
                [
                    "Learn handshape, finger positions, and movement cues.",
                    "Follow visual references and repeat for muscle memory.",
                ],
            ),
            (
                "🧾 Self Study + ❓ Quiz",
                "Visual-first learning and recall checks.",
                [
                    "Study mode shows references and cues.",
                    "Quiz mode asks image/video-based multiple-choice questions.",
                    "Hint reveals clue text; camera verify is available for alphabet cards.",
                ],
            ),
            (
                "🧠 Smart Practice Scheduler",
                "Spaced repetition adapts to your weak signs.",
                [
                    "Each quiz answer updates item difficulty and next due date.",
                    "Wrong answers are re-queued sooner for reinforcement.",
                    "Quiz prioritizes due/weak signs before random picks.",
                    "Use the Review Due metric in Quiz stats to track pending review.",
                ],
            ),
            (
                "🎮 Game + 🎯 Train Gestures",
                "Engagement and model personalization.",
                [
                    "Game mode offers practice with immediate feedback.",
                    "Admin training mode supports collecting/retraining gesture data.",
                ],
            ),
            (
                "📊 Analytics + ⚙️ Settings",
                "Progress tracking and account/app controls.",
                [
                    "Analytics summarizes streak, usage, and recommendations.",
                    "Settings now includes account actions + appearance in one place.",
                    "Manage theme, accent, password, notifications, export, and sign out.",
                ],
            ),
        ]

        for title, subtitle_text, bullets in cards:
            content_layout.addWidget(self._feature_card(title, subtitle_text, bullets))

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)
