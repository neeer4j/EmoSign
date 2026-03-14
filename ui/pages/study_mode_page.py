"""
Self Study Mode - rich learning page with optional camera verification.
"""
import random

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
        self._letters = sorted([
            key for key in SIGN_GUIDE.keys()
            if len(key) == 1 and key.isalpha()
        ])
        self._index = 0
        self._visited = set()
        self._show_steps = True
        self._camera_widget = None
        self._setup_ui()
        self._refresh_card()

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
                border: 1px solid {COLORS['border']};
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
                border: 1px solid {COLORS['border']};
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
                    border: 1px solid {COLORS['border']};
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
                border: 1px solid {COLORS['border']};
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
                border: 1px dashed {COLORS['border']};
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
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    padding: 7px 10px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['accent']}77;
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
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['primary']}77;
                }}
            """)

        controls.addWidget(self.prev_btn)
        controls.addWidget(self.shuffle_btn)
        controls.addWidget(self.reveal_btn)
        controls.addStretch()
        controls.addWidget(self.next_btn)
        root.addLayout(controls)

    def _start_camera(self):
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
        target = self._letters[self._index] if self._letters else ""
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
        total = len(self._letters) if self._letters else 1
        seen = len(self._visited)
        coverage = int((seen / total) * 100)
        motion_signs = len([k for k in self._letters if SIGN_GUIDE.get(k, {}).get("motion")])
        self.cards_seen_label.setText(f"Cards Seen: {seen}")
        self.coverage_label.setText(f"Coverage: {coverage}%")
        self.motion_label.setText(f"Motion Signs: {motion_signs}")

    def _refresh_card(self):
        if not self._letters:
            self.title.setText("No signs available")
            self.imagine.setText("")
            self.steps.setText("")
            self.meta.setText("")
            self.expected_label.setText("Target: -")
            return

        letter = self._letters[self._index]
        self._visited.add(letter)
        guide = SIGN_GUIDE.get(letter, {})

        emoji = guide.get("emoji", "✋")
        self.title.setText(f"{emoji}  {letter}")
        self.imagine.setText(guide.get("imagine", ""))
        self.expected_label.setText(f"Target: {letter}")

        do_this = guide.get("do_this", [])[:3]
        if self._show_steps:
            self.steps.setText("\n".join(do_this) if do_this else "No instructions available.")
        else:
            self.steps.setText("Think first: how would you shape your hand for this sign?")

        fingers = guide.get("fingers", [0, 0, 0, 0, 0])
        names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        for idx, name in enumerate(names):
            self._finger_bars[name].setValue(int(fingers[idx]) if idx < len(fingers) else 0)

        motion = guide.get("motion")
        motion_text = f" • Motion: {motion}" if motion else ""
        self.meta.setText(f"Card {self._index + 1}/{len(self._letters)}{motion_text}")
        self._update_metrics()

    def _prev(self):
        if not self._letters:
            return
        self._index = (self._index - 1) % len(self._letters)
        self._refresh_card()

    def _next(self):
        if not self._letters:
            return
        self._index = (self._index + 1) % len(self._letters)
        self._refresh_card()

    def _shuffle(self):
        if not self._letters:
            return
        self._index = random.randint(0, len(self._letters) - 1)
        self._refresh_card()

    def hideEvent(self, event):
        self._stop_camera()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)
