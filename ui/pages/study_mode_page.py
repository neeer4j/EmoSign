"""
Self Study Mode - rich learning page with optional camera verification.
"""
import glob
import os
import random
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt

from ui.styles import COLORS
from ui.page_header import make_page_header
from ui.pages.tutorial_page import SIGN_GUIDE


class StudyModePage(QWidget):
    """Self-study page using tutorial sign data with optional camera checks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = self._build_study_cards()
        self._index = 0
        self._visited = set()
        self._show_steps = True
        self._camera_widget = None
        self._setup_ui()
        self._refresh_card()

    def _normalize_key(self, text: str) -> str:
        return re.sub(r'[^a-z0-9]', '', (text or '').lower())

    def _display_name_from_stem(self, stem: str) -> str:
        pretty = stem.replace('_', ' ').replace('-', ' ')
        pretty = re.sub(r'\s+', ' ', pretty).strip()
        return pretty.title() if pretty else stem

    def _build_study_cards(self):
        cards = []

        # Alphabet cards from SIGN_GUIDE
        for key in sorted(k for k in SIGN_GUIDE.keys() if len(k) == 1 and k.isalpha()):
            guide = SIGN_GUIDE.get(key, {})
            cards.append({
                "id": f"alpha:{key}",
                "title": key,
                "emoji": guide.get("emoji", "✋"),
                "imagine": guide.get("imagine", ""),
                "steps": guide.get("do_this", [])[:3],
                "fingers": guide.get("fingers", [0, 0, 0, 0, 0]),
                "motion": guide.get("motion"),
                "camera_target": key,
                "category": "Alphabet",
            })

        # Gesture cards from assets/gestures
        assets_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
        gestures_dir = os.path.join(assets_root, "gestures")
        known = {self._normalize_key(c["title"]) for c in cards}

        if os.path.isdir(gestures_dir):
            seen = set()
            for ext in ("*.mp4", "*.webm", "*.avi", "*.mov", "*.mkv"):
                for path in glob.glob(os.path.join(gestures_dir, ext)):
                    if not os.path.isfile(path):
                        continue
                    stem = os.path.splitext(os.path.basename(path))[0]
                    title = self._display_name_from_stem(stem)
                    normalized = self._normalize_key(title)
                    if not normalized or normalized in known or normalized in seen:
                        continue
                    seen.add(normalized)
                    cards.append({
                        "id": f"gesture:{normalized}",
                        "title": title,
                        "emoji": "🤟",
                        "imagine": "Study this gesture by watching the demo and matching hand shape + motion.",
                        "steps": [
                            "1️⃣  Watch the full movement once from start to finish",
                            "2️⃣  Repeat slowly, matching hand direction and timing",
                            "3️⃣  Practice until the motion feels smooth and natural",
                        ],
                        "fingers": [0, 0, 0, 0, 0],
                        "motion": "Video-guided gesture",
                        "camera_target": None,
                        "category": "Gesture",
                    })

        return cards

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        header, _ = make_page_header("🧾 Self Study")
        root.addLayout(header)

        sub = QLabel("Learn visually first, then optionally verify with camera when you want.")
        sub.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        root.addWidget(sub)

        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(14, 10, 14, 10)
        stats_layout.setSpacing(16)

        self.cards_seen_label = QLabel("Cards Seen: 0")
        self.coverage_label = QLabel("Coverage: 0%")
        self.motion_label = QLabel("Motion Signs: 0")
        for lbl in (self.cards_seen_label, self.coverage_label, self.motion_label):
            lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 600;")
            stats_layout.addWidget(lbl)
        stats_layout.addStretch()
        root.addWidget(stats_frame)

        content = QHBoxLayout()
        content.setSpacing(16)

        self.card = QFrame()
        self.card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        self.title = QLabel("")
        self.title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 26px; font-weight: 700;")

        self.imagine = QLabel("")
        self.imagine.setWordWrap(True)
        self.imagine.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")

        self.steps = QLabel("")
        self.steps.setWordWrap(True)
        self.steps.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")

        pattern_title = QLabel("Finger Pattern")
        pattern_title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: 700;")

        self.pattern_grid = QGridLayout()
        self.pattern_grid.setHorizontalSpacing(10)
        self.pattern_grid.setVerticalSpacing(6)
        self._finger_bars = {}
        names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        for row, name in enumerate(names):
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
            bar = QProgressBar()
            bar.setRange(0, 3)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background: {COLORS['bg_input']};
                    border: none;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background: {COLORS['primary']};
                    border-radius: 4px;
                }}
            """)
            self.pattern_grid.addWidget(name_lbl, row, 0)
            self.pattern_grid.addWidget(bar, row, 1)
            self._finger_bars[name] = bar

        self.meta = QLabel("")
        self.meta.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")

        card_layout.addWidget(self.title)
        card_layout.addWidget(self.imagine)
        card_layout.addWidget(self.steps)
        card_layout.addWidget(pattern_title)
        card_layout.addLayout(self.pattern_grid)
        card_layout.addStretch()
        card_layout.addWidget(self.meta)
        content.addWidget(self.card, 3)

        verify_frame = QFrame()
        verify_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)
        verify_layout = QVBoxLayout(verify_frame)
        verify_layout.setContentsMargins(16, 16, 16, 16)
        verify_layout.setSpacing(10)

        verify_title = QLabel("📷 Optional Camera Verify")
        verify_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px; font-weight: 700;")
        verify_layout.addWidget(verify_title)

        self.expected_label = QLabel("Target: -")
        self.expected_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        verify_layout.addWidget(self.expected_label)

        self.camera_container = QFrame()
        self.camera_container.setMinimumHeight(250)
        self.camera_container.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_input']};
                border: none;
                border-radius: 10px;
            }}
        """)
        cam_layout = QVBoxLayout(self.camera_container)
        cam_layout.setContentsMargins(8, 8, 8, 8)
        self.camera_placeholder = QLabel("Start camera if you want to verify this sign")
        self.camera_placeholder.setAlignment(Qt.AlignCenter)
        self.camera_placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        cam_layout.addWidget(self.camera_placeholder)
        verify_layout.addWidget(self.camera_container)

        self.verify_feedback = QLabel("Waiting for verification")
        self.verify_feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")
        verify_layout.addWidget(self.verify_feedback)

        cam_buttons = QHBoxLayout()
        self.start_cam_btn = QPushButton("▶ Start Camera")
        self.stop_cam_btn = QPushButton("⏹ Stop")
        self.stop_cam_btn.setEnabled(False)
        self.start_cam_btn.clicked.connect(self._start_camera)
        self.stop_cam_btn.clicked.connect(self._stop_camera)
        for btn in (self.start_cam_btn, self.stop_cam_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 7px 10px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_card_hover']};
                }}
            """)
        cam_buttons.addWidget(self.start_cam_btn)
        cam_buttons.addWidget(self.stop_cam_btn)
        verify_layout.addLayout(cam_buttons)
        content.addWidget(verify_frame, 2)
        root.addLayout(content, 1)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self._prev)
        self.shuffle_btn = QPushButton("🔀 Shuffle")
        self.shuffle_btn.clicked.connect(self._shuffle)
        self.reveal_btn = QPushButton("🙈 Hide Steps")
        self.reveal_btn.clicked.connect(self._toggle_steps)
        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self._next)

        for btn in (self.prev_btn, self.shuffle_btn, self.reveal_btn, self.next_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_card_hover']};
                }}
            """)

        controls.addWidget(self.prev_btn)
        controls.addWidget(self.shuffle_btn)
        controls.addWidget(self.reveal_btn)
        controls.addStretch()
        controls.addWidget(self.next_btn)
        root.addLayout(controls)

    def _start_camera(self):
        if not self._cards:
            return
        current = self._cards[self._index]
        if not current.get("camera_target"):
            self.verify_feedback.setText("ℹ️ Camera verify is not used for gesture study cards")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px; font-weight: 700;")
            return

        try:
            from ui.camera_widget import CameraWidget
        except Exception:
            self.verify_feedback.setText("❌ Camera is not available in this environment")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; font-weight: 700;")
            return

        if self._camera_widget is None:
            self._camera_widget = CameraWidget()
            self._camera_widget.setMinimumSize(320, 220)
            self._camera_widget.video_label.setMinimumSize(320, 220)
            self._camera_widget.heuristic_threshold = 0.35
            self._camera_widget.heuristic_gesture_detected.connect(self._on_heuristic)
            self._camera_widget.nn_gesture_detected.connect(self._on_nn)
            self.camera_placeholder.hide()
            self.camera_container.layout().addWidget(self._camera_widget)

        if self._camera_widget.start():
            self.start_cam_btn.setEnabled(False)
            self.stop_cam_btn.setEnabled(True)
            self.verify_feedback.setText("👀 Show the target sign to verify")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600;")
        else:
            self.verify_feedback.setText("❌ Could not start camera")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; font-weight: 700;")

    def _stop_camera(self):
        if self._camera_widget:
            self._camera_widget.stop()
        self.start_cam_btn.setEnabled(True)
        self.stop_cam_btn.setEnabled(False)
        self.verify_feedback.setText("Camera stopped")
        self.verify_feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")

    def _on_heuristic(self, label: str, confidence: float):
        self._handle_prediction(label, confidence)

    def _on_nn(self, label: str, confidence: float, _model_used: str):
        self._handle_prediction(label, confidence)

    def _handle_prediction(self, label: str, confidence: float):
        if not label:
            return
        target = self._cards[self._index].get("camera_target", "") if self._cards else ""
        if not target:
            return
        guess = label.upper().strip()
        if guess == target:
            self.verify_feedback.setText(f"✅ Correct match: {guess} ({confidence:.0%})")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: 700;")
        else:
            self.verify_feedback.setText(f"Try again: saw {guess}, target is {target}")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px; font-weight: 700;")

    def _toggle_steps(self):
        self._show_steps = not self._show_steps
        self.reveal_btn.setText("🙈 Hide Steps" if self._show_steps else "👀 Show Steps")
        self._refresh_card()

    def _update_metrics(self):
        total = len(self._cards) if self._cards else 1
        seen = len(self._visited)
        coverage = int((seen / total) * 100)
        motion_signs = len([c for c in self._cards if c.get("motion")])
        self.cards_seen_label.setText(f"Cards Seen: {seen}")
        self.coverage_label.setText(f"Coverage: {coverage}%")
        self.motion_label.setText(f"Motion Signs: {motion_signs}")

    def _refresh_card(self):
        if not self._cards:
            self.title.setText("No signs available")
            self.imagine.setText("")
            self.steps.setText("")
            self.meta.setText("")
            self.expected_label.setText("Target: -")
            return

        card = self._cards[self._index]
        self._visited.add(card["id"])

        self.title.setText(f"{card.get('emoji', '✋')}  {card.get('title', '')}")
        self.imagine.setText(card.get("imagine", ""))
        cam_target = card.get("camera_target")
        self.expected_label.setText(f"Target: {cam_target}" if cam_target else "Target: Study Only")

        do_this = card.get("steps", [])[:3]
        if self._show_steps:
            self.steps.setText("\n".join(do_this) if do_this else "No instructions available.")
        else:
            self.steps.setText("Think first: how would you shape your hand for this sign?")

        fingers = card.get("fingers", [0, 0, 0, 0, 0])
        names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        for idx, name in enumerate(names):
            self._finger_bars[name].setValue(int(fingers[idx]) if idx < len(fingers) else 0)

        motion = card.get("motion")
        motion_text = f" • Motion: {motion}" if motion else ""
        self.meta.setText(f"Card {self._index + 1}/{len(self._cards)} • {card.get('category', 'General')}{motion_text}")

        self.start_cam_btn.setEnabled(bool(cam_target))
        self.stop_cam_btn.setEnabled(False)
        if not cam_target and self._camera_widget and self._camera_widget.is_running:
            self._stop_camera()
        elif not cam_target:
            self.verify_feedback.setText("ℹ️ Camera verify disabled for this card")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")

        self._update_metrics()

    def _prev(self):
        if not self._cards:
            return
        self._index = (self._index - 1) % len(self._cards)
        self._refresh_card()

    def _next(self):
        if not self._cards:
            return
        self._index = (self._index + 1) % len(self._cards)
        self._refresh_card()

    def _shuffle(self):
        if not self._cards:
            return
        self._index = random.randint(0, len(self._cards) - 1)
        self._refresh_card()

    def hideEvent(self, event):
        self._stop_camera()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)
