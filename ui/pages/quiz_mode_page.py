"""
Quiz Mode - richer sign learning quiz with optional camera verification.
"""
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar
)
from PySide6.QtCore import Qt

from ui.styles import COLORS
from ui.page_header import make_page_header
from ui.pages.tutorial_page import SIGN_GUIDE


class QuizModePage(QWidget):
    """Multiple-choice quiz with optional camera verification."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._letters = sorted([
            key for key in SIGN_GUIDE.keys()
            if len(key) == 1 and key.isalpha()
        ])
        self._score = 0
        self._attempts = 0
        self._streak = 0
        self._target_rounds = 10
        self._current_answer = None
        self._camera_widget = None
        self._setup_ui()
        self._next_question()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        header, _ = make_page_header("❓ Quiz Mode")
        root.addLayout(header)

        self.subtitle = QLabel("Practice recall first. Use camera verification only when you need confidence check.")
        self.subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        root.addWidget(self.subtitle)

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

        self.score_label = QLabel("Score: 0/0")
        self.accuracy_label = QLabel("Accuracy: 0%")
        self.streak_label = QLabel("Streak: 0")
        for lbl in (self.score_label, self.accuracy_label, self.streak_label):
            lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 700;")
            stats_layout.addWidget(lbl)
        stats_layout.addStretch()
        root.addWidget(stats_frame)

        self.progress = QProgressBar()
        self.progress.setRange(0, self._target_rounds)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("Round %v / %m")
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                font-size: 11px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {COLORS['primary']};
                border-radius: 8px;
            }}
        """)
        root.addWidget(self.progress)

        body = QHBoxLayout()
        body.setSpacing(16)

        self.question_card = QFrame()
        self.question_card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        ql = QVBoxLayout(self.question_card)
        ql.setContentsMargins(20, 20, 20, 20)
        ql.setSpacing(10)

        self.prompt = QLabel("")
        self.prompt.setWordWrap(True)
        self.prompt.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: 600;")

        self.hint = QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")

        self.feedback = QLabel("")
        self.feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: 600;")

        ql.addWidget(self.prompt)
        ql.addWidget(self.hint)
        ql.addWidget(self.feedback)

        self.option_buttons = []
        for _ in range(4):
            btn = QPushButton("")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, b=btn: self._submit_answer(b.text()))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    padding: 10px 14px;
                    text-align: left;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['primary']}77;
                }}
            """)
            ql.addWidget(btn)
            self.option_buttons.append(btn)

        controls = QHBoxLayout()
        self.hint_btn = QPushButton("💡 Hint")
        self.hint_btn.setCursor(Qt.PointingHandCursor)
        self.hint_btn.clicked.connect(self._show_hint)
        self.next_btn = QPushButton("Next Question")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self._next_question)
        for btn in (self.hint_btn, self.next_btn):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['accent']}88;
                }}
            """)
        controls.addWidget(self.hint_btn)
        controls.addStretch()
        controls.addWidget(self.next_btn)
        ql.addLayout(controls)
        body.addWidget(self.question_card, 3)

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

        self.expected_label = QLabel("Target Answer: -")
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
        self.camera_placeholder = QLabel("Start camera to verify your signed answer")
        self.camera_placeholder.setAlignment(Qt.AlignCenter)
        self.camera_placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        cam_layout.addWidget(self.camera_placeholder)
        verify_layout.addWidget(self.camera_container)

        self.verify_feedback = QLabel("Verification idle")
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
        body.addWidget(verify_frame, 2)

        root.addLayout(body, 1)

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
            self.verify_feedback.setText("👀 Show your answer sign to verify")
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
        if not label or not self._current_answer:
            return
        guess = label.upper().strip()
        if guess == self._current_answer:
            self.verify_feedback.setText(f"✅ Verified by camera: {guess} ({confidence:.0%})")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: 700;")
        else:
            self.verify_feedback.setText(f"Try again: saw {guess}, expected {self._current_answer}")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px; font-weight: 700;")

    def _show_hint(self):
        if not self._current_answer:
            return
        info = SIGN_GUIDE.get(self._current_answer, {})
        steps = info.get("do_this", [])
        extra = steps[1] if len(steps) > 1 else "Keep hand shape stable and clear."
        self.feedback.setText(f"💡 Hint: {extra}")
        self.feedback.setStyleSheet(f"color: {COLORS['accent']}; font-size: 13px; font-weight: 700;")

    def _update_stats(self):
        accuracy = int((self._score / self._attempts) * 100) if self._attempts else 0
        self.score_label.setText(f"Score: {self._score}/{self._attempts}")
        self.accuracy_label.setText(f"Accuracy: {accuracy}%")
        self.streak_label.setText(f"Streak: {self._streak}")
        self.progress.setValue(min(self._attempts, self._target_rounds))

    def _next_question(self):
        if len(self._letters) < 4:
            self.prompt.setText("Not enough sign data to generate quiz.")
            return

        self._current_answer = random.choice(self._letters)
        info = SIGN_GUIDE.get(self._current_answer, {})

        clue = info.get("imagine", "")
        step = ""
        do_this = info.get("do_this", [])
        if do_this:
            step = do_this[0]

        self.prompt.setText("Which letter matches this clue?")
        self.hint.setText(f"{clue}\n{step}")
        self.feedback.setText("")
        self.feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: 600;")
        self.expected_label.setText(f"Target Answer: {self._current_answer}")
        self.verify_feedback.setText("Verification idle")
        self.verify_feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")

        choices = {self._current_answer}
        while len(choices) < 4:
            choices.add(random.choice(self._letters))

        shuffled = list(choices)
        random.shuffle(shuffled)
        for btn, choice in zip(self.option_buttons, shuffled):
            btn.setText(choice)
            btn.setEnabled(True)

    def _submit_answer(self, answer: str):
        if not self._current_answer:
            return

        self._attempts += 1
        if answer == self._current_answer:
            self._score += 1
            self._streak += 1
            self.feedback.setText(f"✅ Correct! The answer is {self._current_answer}.")
            self.feedback.setStyleSheet(f"color: {COLORS['success']}; font-size: 13px; font-weight: 700;")
        else:
            self._streak = 0
            self.feedback.setText(f"❌ Not quite. Correct answer: {self._current_answer}.")
            self.feedback.setStyleSheet(f"color: {COLORS['danger']}; font-size: 13px; font-weight: 700;")

        self._update_stats()

        for btn in self.option_buttons:
            btn.setEnabled(False)

    def hideEvent(self, event):
        self._stop_camera()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)
