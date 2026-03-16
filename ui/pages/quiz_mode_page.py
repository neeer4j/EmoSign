"""
Quiz Mode - richer sign learning quiz with optional camera verification.
"""
import glob
import os
import random
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

from ui.styles import COLORS
from ui.page_header import make_page_header
from ui.pages.tutorial_page import SIGN_GUIDE

try:
    from core.analytics import analytics
except Exception:
    analytics = None


class QuizModePage(QWidget):
    """Multiple-choice quiz with optional camera verification."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._quiz_items = self._build_quiz_items()
        self._item_by_id = {
            item["item_id"]: item for item in self._quiz_items if item.get("item_id")
        }
        self._score = 0
        self._correct_answers = 0
        self._attempts = 0
        self._streak = 0
        self._target_rounds = 10
        self._quiz_finished = False
        self._session_saved = False
        self._session_topic_stats = {}
        self._current_item = None
        self._thumb_cache = {}
        self._recent_correct_categories = deque(maxlen=3)
        self._hint_used = False
        self._user_id = "guest"
        self._review_queue = deque()
        self._ref_video_timer = QTimer(self)
        self._ref_video_timer.timeout.connect(self._update_reference_video_frame)
        self._ref_video_cap = None
        self._ref_video_path = None
        self._camera_widget = None
        self._setup_ui()
        self._start_new_quiz()

    def _build_quiz_items(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
        items = []

        # Alphabet image cards
        alpha_dir = os.path.join(base_dir, "alphabets")
        for path in sorted(glob.glob(os.path.join(alpha_dir, "*"))):
            if not os.path.isfile(path):
                continue
            stem = os.path.splitext(os.path.basename(path))[0]
            key = stem[0].upper() if stem else ""
            if len(key) == 1 and key.isalpha():
                guide = SIGN_GUIDE.get(key, {})
                items.append({
                    "item_id": f"alphabet:{key}",
                    "answer": key,
                    "display": key,
                    "category": "Alphabet",
                    "image_path": path,
                    "video_path": None,
                    "hint": guide.get("imagine", ""),
                    "camera_target": key,
                })

        # Number image cards
        num_dir = os.path.join(base_dir, "numbers")
        for path in sorted(glob.glob(os.path.join(num_dir, "*"))):
            if not os.path.isfile(path):
                continue
            stem = os.path.splitext(os.path.basename(path))[0]
            digit = stem[0] if stem else ""
            if len(digit) == 1 and digit.isdigit():
                items.append({
                    "item_id": f"number:{digit}",
                    "answer": digit,
                    "display": digit,
                    "category": "Number",
                    "image_path": path,
                    "video_path": None,
                    "hint": f"This is number sign {digit}.",
                    "camera_target": None,
                })

        # Gesture video cards (play clip in reference panel)
        gesture_dir = os.path.join(base_dir, "gestures")
        for path in sorted(glob.glob(os.path.join(gesture_dir, "*.mp4"))):
            if not os.path.isfile(path):
                continue
            stem = os.path.splitext(os.path.basename(path))[0]
            normalized_stem = stem.strip().lower()
            display = stem.upper()
            if len(display) == 1 and display.isalpha():
                display = f"{display} (Gesture)"
            items.append({
                "item_id": f"gesture:{normalized_stem}",
                "answer": display,
                "display": display,
                "category": "Gesture",
                "image_path": None,
                "video_path": path,
                "hint": f"Common gesture: {stem.replace('_', ' ')}.",
                "camera_target": None,
            })

        return items

    def _video_thumbnail(self, video_path: str) -> QPixmap:
        cached = self._thumb_cache.get(video_path)
        if cached is not None:
            return cached

        pixmap = QPixmap()
        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            ok, frame = cap.read()
            tries = 0
            while ok and frame is not None and tries < 20:
                # Skip black/blank intro frames
                if float(frame.mean()) > 10.0:
                    break
                ok, frame = cap.read()
                tries += 1
            cap.release()
            if ok and frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                qimg = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
                pixmap = QPixmap.fromImage(qimg)
        except Exception:
            pixmap = QPixmap()

        self._thumb_cache[video_path] = pixmap
        return pixmap

    def _stop_reference_video(self):
        if self._ref_video_timer.isActive():
            self._ref_video_timer.stop()
        if self._ref_video_cap is not None:
            try:
                self._ref_video_cap.release()
            except Exception:
                pass
        self._ref_video_cap = None
        self._ref_video_path = None

    def _start_reference_video(self, video_path: str):
        self._stop_reference_video()
        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False

            fps = cap.get(cv2.CAP_PROP_FPS)
            if not fps or fps <= 1:
                fps = 24
            interval = max(25, int(1000 / fps))

            self._ref_video_cap = cap
            self._ref_video_path = video_path
            self._ref_video_timer.start(interval)
            self._update_reference_video_frame()
            return True
        except Exception:
            self._stop_reference_video()
            return False

    def _update_reference_video_frame(self):
        if self._ref_video_cap is None:
            return
        try:
            import cv2

            ok, frame = self._ref_video_cap.read()
            if not ok or frame is None:
                self._ref_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._ref_video_cap.read()
                if not ok or frame is None:
                    return

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            qimg = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            pixmap = QPixmap.fromImage(qimg)
            scaled = pixmap.scaled(
                self.reference_image.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.reference_image.setPixmap(scaled)
            self.reference_image.setText("")
            self.reference_image.setAlignment(Qt.AlignCenter)
        except Exception:
            self._stop_reference_video()

    def _set_reference_image(self, item: dict):
        self._stop_reference_video()
        pixmap = QPixmap()
        if item.get("image_path"):
            pixmap = QPixmap(item["image_path"])
        elif item.get("video_path"):
            if self._start_reference_video(item["video_path"]):
                return
            pixmap = self._video_thumbnail(item["video_path"])

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.reference_image.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.reference_image.setPixmap(scaled)
            self.reference_image.setText("")
            self.reference_image.setAlignment(Qt.AlignCenter)
        else:
            self.reference_image.setPixmap(QPixmap())
            self.reference_image.setText("Preview unavailable for this sign")
            self.reference_image.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_item:
            self._set_reference_image(self._current_item)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        header, _ = make_page_header("❓ Quiz Mode")
        root.addLayout(header)

        self.subtitle = QLabel("Practice recall first. Use camera verification only when you need confidence check.")
        self.subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        root.addWidget(self.subtitle)

        settings_row = QFrame()
        settings_row.setStyleSheet(f"background: transparent;")
        settings_layout = QHBoxLayout(settings_row)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(10)

        rounds_lbl = QLabel("Questions")
        rounds_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 700;")
        settings_layout.addWidget(rounds_lbl)

        self.round_count_combo = QComboBox()
        for count in (5, 10, 15, 20, 25, 30):
            self.round_count_combo.addItem(str(count), count)
        default_idx = self.round_count_combo.findData(self._target_rounds)
        self.round_count_combo.setCurrentIndex(default_idx if default_idx >= 0 else 1)
        self.round_count_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 6px 10px;
                font-weight: 700;
                min-width: 86px;
            }}
        """)
        settings_layout.addWidget(self.round_count_combo)

        self.start_new_btn = QPushButton("🔁 Start New Quiz")
        self.start_new_btn.setCursor(Qt.PointingHandCursor)
        self.start_new_btn.clicked.connect(self._start_new_quiz)
        self.start_new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_card_hover']};
            }}
        """)
        settings_layout.addWidget(self.start_new_btn)
        settings_layout.addStretch()
        root.addWidget(settings_row)

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

        self.score_label = QLabel("Score: 0 pts")
        self.accuracy_label = QLabel("Accuracy: 0%")
        self.streak_label = QLabel("Streak: 0")
        self.review_due_label = QLabel("Review Due: -")
        for lbl in (self.score_label, self.accuracy_label, self.streak_label, self.review_due_label):
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
                border: none;
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
                border: none;
                border-radius: 12px;
            }}
        """)
        ql = QVBoxLayout(self.question_card)
        ql.setContentsMargins(20, 20, 20, 20)
        ql.setSpacing(10)

        self.prompt = QLabel("")
        self.prompt.setWordWrap(True)
        self.prompt.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 15px; font-weight: 600;")

        self.reference_image = QLabel("Loading reference...")
        self.reference_image.setMinimumHeight(230)
        self.reference_image.setStyleSheet(f"""
            QLabel {{
                background: {COLORS['bg_input']};
                border: none;
                border-radius: 10px;
                color: {COLORS['text_muted']};
                font-size: 12px;
            }}
        """)
        self.reference_image.setAlignment(Qt.AlignCenter)

        self.hint = QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")

        self.feedback = QLabel("")
        self.feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: 600;")

        ql.addWidget(self.prompt)
        ql.addWidget(self.reference_image)
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
                    border: none;
                    border-radius: 8px;
                    padding: 10px 14px;
                    text-align: left;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_card_hover']};
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
        self.next_btn.clicked.connect(self._handle_next_action)
        for btn in (self.hint_btn, self.next_btn):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_card_hover']};
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

        self.expected_label = QLabel("Target Answer: -")
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
        body.addWidget(verify_frame, 2)

        root.addLayout(body, 1)

    def _start_camera(self):
        if not self._current_item or not self._current_item.get("camera_target"):
            self.verify_feedback.setText("ℹ️ Camera verify is enabled only for alphabet cards in this quiz")
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
        if not label or not self._current_item:
            return
        target = self._current_item.get("camera_target")
        if not target:
            return
        guess = label.upper().strip()
        if guess == target:
            self.verify_feedback.setText(f"✅ Verified by camera: {guess} ({confidence:.0%})")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; font-weight: 700;")
        else:
            self.verify_feedback.setText(f"Try again: saw {guess}, expected {target}")
            self.verify_feedback.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px; font-weight: 700;")

    def _show_hint(self):
        if not self._current_item:
            return
        self._hint_used = True
        category = self._current_item.get("category", "Sign")
        item_hint = self._current_item.get("hint", "Focus on finger shape and palm orientation.")
        self.hint.setText(f"Category: {category} • 💡 Hint: {item_hint}")
        self.feedback.setText("Hint revealed. Choose the best matching option.")
        self.feedback.setStyleSheet(f"color: {COLORS['accent']}; font-size: 13px; font-weight: 700;")

    def _update_stats(self):
        accuracy = int((self._correct_answers / self._attempts) * 100) if self._attempts else 0
        self.score_label.setText(f"Score: {self._score} pts")
        self.accuracy_label.setText(f"Accuracy: {accuracy}%")
        self.streak_label.setText(f"Streak: {self._streak}")
        self.progress.setValue(min(self._attempts, self._target_rounds))

        due_count = len(self._review_queue)
        if analytics:
            try:
                summary = analytics.get_review_summary(self._user_id, list(self._item_by_id.keys()))
                due_count = int(summary.get("due_items", due_count))
            except Exception:
                pass
        self.review_due_label.setText(f"Review Due: {due_count}")

    def update_user(self, user_id: str):
        """Set active user for personalized review scheduling."""
        self._user_id = user_id or "guest"
        self._refresh_review_queue()
        self._update_stats()

    def _refresh_review_queue(self):
        self._review_queue.clear()
        if not analytics:
            return
        try:
            due_items = analytics.get_due_review_items(
                self._user_id,
                list(self._item_by_id.keys()),
                limit=24,
            )
        except Exception:
            due_items = []

        for item_id in due_items:
            if item_id in self._item_by_id:
                self._review_queue.append(item_id)

    def _handle_next_action(self):
        if self._quiz_finished:
            self._start_new_quiz()
            return
        self._next_question()

    def _set_verdict(self, accuracy: int) -> str:
        if accuracy >= 90:
            return "Excellent"
        if accuracy >= 75:
            return "Strong"
        if accuracy >= 60:
            return "Fair"
        return "Needs More Practice"

    def _start_new_quiz(self):
        selected_rounds = self.round_count_combo.currentData() if hasattr(self, "round_count_combo") else self._target_rounds
        try:
            self._target_rounds = max(1, int(selected_rounds))
        except Exception:
            self._target_rounds = 10

        self._score = 0
        self._correct_answers = 0
        self._attempts = 0
        self._streak = 0
        self._quiz_finished = False
        self._session_saved = False
        self._session_topic_stats = {}
        self._recent_correct_categories.clear()
        self._hint_used = False
        self.progress.setRange(0, self._target_rounds)
        self.progress.setValue(0)
        self.progress.setFormat("Round %v / %m")
        self._refresh_review_queue()
        self._update_stats()

        self.next_btn.setText("Next Question")
        self.next_btn.setEnabled(False)
        self.hint_btn.setEnabled(True)

        self.prompt.setText("Starting quiz...")
        self.feedback.setText("")
        self.expected_label.setText("Target Answer: Hidden")
        self.verify_feedback.setText("Verification idle")
        self.verify_feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")

        for btn in self.option_buttons:
            btn.setEnabled(True)

        self._next_question()

    def _finish_quiz(self):
        if self._quiz_finished:
            return

        self._quiz_finished = True
        accuracy = int((self._correct_answers / self._attempts) * 100) if self._attempts else 0
        verdict = self._set_verdict(accuracy)

        self.prompt.setText("🎉 Quiz complete")
        self.hint.setText(
            f"Final: {self._correct_answers}/{self._target_rounds} correct • Accuracy {accuracy}%"
        )
        self.feedback.setText(
            f"Verdict: {verdict} • Score {self._score} pts. Select a question count and start a new quiz anytime."
        )
        self.feedback.setStyleSheet(f"color: {COLORS['success']}; font-size: 13px; font-weight: 700;")
        self.expected_label.setText("Target Answer: Quiz ended")
        self.verify_feedback.setText("Quiz finished")
        self.verify_feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")

        if self._camera_widget and self._camera_widget.is_running:
            self._stop_camera()

        self.start_cam_btn.setEnabled(False)
        self.stop_cam_btn.setEnabled(False)
        self.hint_btn.setEnabled(False)
        self.next_btn.setText("Start New Quiz")
        self.next_btn.setEnabled(True)

        for btn in self.option_buttons:
            btn.setEnabled(False)

        if analytics and not self._session_saved:
            try:
                analytics.record_quiz_session(
                    self._user_id,
                    self._target_rounds,
                    self._correct_answers,
                    self._score,
                    verdict,
                    topic_stats=self._session_topic_stats,
                )
                analytics.save_stats(self._user_id)
                self._session_saved = True
            except Exception:
                pass

        self._update_stats()

    def _next_question(self):
        if len(self._quiz_items) < 4:
            self.prompt.setText("Not enough sign data to generate quiz.")
            return

        if self._attempts >= self._target_rounds:
            self._finish_quiz()
            return

        if not self._review_queue:
            self._refresh_review_queue()

        self._current_item = None
        if self._review_queue:
            while self._review_queue and self._current_item is None:
                next_id = self._review_queue.popleft()
                self._current_item = self._item_by_id.get(next_id)

        if self._current_item is None:
            self._current_item = random.choice(self._quiz_items)

        self._hint_used = False
        self.prompt.setText("Which sign matches this reference image?")
        self.hint.setText(f"Category: {self._current_item['category']} • Tap Hint if needed")
        self._set_reference_image(self._current_item)

        self.feedback.setText("")
        self.feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: 600;")
        self.expected_label.setText("Target Answer: Hidden")
        self.verify_feedback.setText("Verification idle")
        self.verify_feedback.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")
        self.hint_btn.setEnabled(True)
        self.next_btn.setEnabled(False)

        supports_camera = bool(self._current_item.get("camera_target"))
        if self._camera_widget and self._camera_widget.is_running:
            self._stop_camera()
        self.start_cam_btn.setEnabled(supports_camera)
        self.stop_cam_btn.setEnabled(False)
        if not supports_camera:
            self.verify_feedback.setText("Camera verify disabled for this category")

        choices = {self._current_item["answer"]}
        while len(choices) < 4:
            choices.add(random.choice(self._quiz_items)["answer"])

        shuffled = list(choices)
        random.shuffle(shuffled)
        for btn, choice in zip(self.option_buttons, shuffled):
            btn.setText(choice)
            btn.setEnabled(True)

    def _submit_answer(self, answer: str):
        if not self._current_item:
            return

        self._attempts += 1
        self.expected_label.setText(f"Target Answer: {self._current_item['display']} (revealed)")
        is_correct = answer == self._current_item["answer"]
        category = self._current_item.get("category", "General")
        bucket = self._session_topic_stats.setdefault(category, {"attempts": 0, "correct": 0})
        bucket["attempts"] += 1

        if is_correct:
            self._correct_answers += 1
            self._streak += 1
            bonus = 0
            self._score += 1
            bucket["correct"] += 1

            self._recent_correct_categories.append(category)
            if len(self._recent_correct_categories) == 3 and len(set(self._recent_correct_categories)) == 3:
                bonus = 2
                self._score += bonus

            if bonus:
                self.feedback.setText(
                    f"✅ Correct! {self._current_item['display']} (+1) • 🔥 Category Combo Bonus +{bonus}"
                )
            else:
                self.feedback.setText(f"✅ Correct! The answer is {self._current_item['display']}.")
            self.feedback.setStyleSheet(f"color: {COLORS['success']}; font-size: 13px; font-weight: 700;")
        else:
            self._streak = 0
            self._recent_correct_categories.clear()
            self.feedback.setText(f"❌ Not quite. Correct answer: {self._current_item['display']}.")
            self.feedback.setStyleSheet(f"color: {COLORS['danger']}; font-size: 13px; font-weight: 700;")

        if analytics and self._current_item.get("item_id"):
            try:
                analytics.record_review_result(
                    self._user_id,
                    self._current_item["item_id"],
                    is_correct,
                )
                analytics.save_stats(self._user_id)
            except Exception:
                pass

        if not is_correct and self._current_item.get("item_id"):
            self._review_queue.append(self._current_item["item_id"])

        if not self._hint_used:
            self.hint.setText(f"Category: {self._current_item['category']}")

        self._update_stats()

        for btn in self.option_buttons:
            btn.setEnabled(False)

        self.hint_btn.setEnabled(False)
        if self._attempts >= self._target_rounds:
            self._finish_quiz()
        else:
            self.next_btn.setEnabled(True)

    def hideEvent(self, event):
        self._stop_reference_video()
        self._stop_camera()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._stop_reference_video()
        self._stop_camera()
        super().closeEvent(event)
