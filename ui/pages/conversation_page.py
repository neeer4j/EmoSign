"""
Conversation Mode — Two-way communication with persistent sign panel.

Layout: Chat messages on the left, sign visualization panel on the right.
The sign panel stays visible and updates when you send/type a message.
Quick replies both send a message AND show the sign for it.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QSizePolicy, QSplitter,
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS
from ui.page_header import make_page_header
from ui.pages.tutorial_page import SIGN_GUIDE, SignCard


# ═══════════════════════════════════════════════════════════════
#  Message Bubble
# ═══════════════════════════════════════════════════════════════

class MessageBubble(QFrame):
    """A simple chat message bubble."""

    def __init__(self, text: str, is_user: bool, timestamp: str = "",
                 message_type: str = "text", parent=None):
        super().__init__(parent)

        if is_user:
            bg = COLORS['primary']
            fg = "#ffffff"
            margin = "2px 0 2px 50px"
        else:
            bg = COLORS['bg_card']
            fg = COLORS['text_primary']
            margin = "2px 50px 2px 0"

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 14px;
                margin: {margin};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        # Type badge
        if message_type == "sign":
            badge = QLabel("✋ Signed")
            badge.setStyleSheet(f"color: {fg}; font-size: 10px; background: transparent;")
            layout.addWidget(badge)

        # Message text
        msg = QLabel(text)
        msg.setStyleSheet(f"color: {fg}; font-size: 14px; background: transparent;")
        msg.setWordWrap(True)
        layout.addWidget(msg)

        # Timestamp
        if timestamp:
            ts = QLabel(timestamp)
            ts.setStyleSheet(f"color: {fg}; font-size: 10px; opacity: 0.6; background: transparent;")
            ts.setAlignment(Qt.AlignRight)
            layout.addWidget(ts)


# ═══════════════════════════════════════════════════════════════
#  Sign Panel — persistent right-side panel
# ═══════════════════════════════════════════════════════════════

class SignPanel(QFrame):
    """Persistent panel that shows sign visualization for a word/phrase.

    Shows:  word with highlighted active letter  |  SignCard  |  playback controls
    Always visible on the right side of the conversation.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("signPanel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        self.setStyleSheet(f"""
            QFrame#signPanel {{
                background: {COLORS['bg_panel']};
                border-left: 1px solid {COLORS['border']};
                border-radius: 0;
            }}
        """)

        self.letters = []
        self.word_chars = []
        self.current_index = 0
        self._is_playing = False
        self._speed_ms = 1200
        self._animation_timer = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Panel title
        title = QLabel("🤟 Sign Viewer")
        title.setStyleSheet(f"""
            font-size: 16px; font-weight: 700;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        layout.addWidget(title)

        # Word display (highlighted letters)
        self.word_display = QLabel("Type something & press 🤟")
        self.word_display.setAlignment(Qt.AlignCenter)
        self.word_display.setWordWrap(True)
        self.word_display.setTextFormat(Qt.RichText)
        self.word_display.setStyleSheet(f"""
            background: {COLORS['bg_input']};
            border-radius: 10px;
            padding: 10px;
            font-size: 14px;
            color: {COLORS['text_muted']};
        """)
        layout.addWidget(self.word_display)

        # Sign card (scrollable area for it)
        self._card_scroll = QScrollArea()
        self._card_scroll.setWidgetResizable(True)
        self._card_scroll.setFrameShape(QFrame.NoFrame)
        self._card_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._card_scroll.setStyleSheet("background: transparent;")

        self.sign_card = SignCard("")
        self._card_scroll.setWidget(self.sign_card)
        layout.addWidget(self._card_scroll, stretch=1)

        # Playback controls — compact
        controls = QHBoxLayout()
        controls.setSpacing(6)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(self._ctrl_btn_style())
        self.prev_btn.clicked.connect(self._prev)
        controls.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']}; color: white; border: none;
                border-radius: 14px; padding: 6px 18px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """)
        self.play_btn.clicked.connect(self._toggle_playback)
        controls.addWidget(self.play_btn)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(self._ctrl_btn_style())
        self.next_btn.clicked.connect(self._next)
        controls.addWidget(self.next_btn)

        self.progress_lbl = QLabel("")
        self.progress_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent;")
        controls.addWidget(self.progress_lbl)
        controls.addStretch()

        layout.addLayout(controls)

        # Speed buttons
        speed_row = QHBoxLayout()
        speed_row.setSpacing(4)
        speed_lbl = QLabel("Speed:")
        speed_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        speed_row.addWidget(speed_lbl)
        for label, ms in [("Slow", 2000), ("Med", 1200), ("Fast", 600)]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setCursor(Qt.PointingHandCursor)
            sel = (ms == self._speed_ms)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['primary'] if sel else COLORS['bg_input']};
                    color: {'white' if sel else COLORS['text_secondary']};
                    border: 1px solid {COLORS['primary'] if sel else COLORS['border']};
                    border-radius: 5px; padding: 1px 8px; font-size: 10px;
                }}
            """)
            btn.clicked.connect(lambda checked, m=ms: self._set_speed(m))
            speed_row.addWidget(btn)
        speed_row.addStretch()
        layout.addLayout(speed_row)

        # Empty state
        self._empty = True

    def _ctrl_btn_style(self):
        return f"""
            QPushButton {{
                background: {COLORS['bg_input']}; border: 1px solid {COLORS['border']};
                border-radius: 16px; font-size: 12px; color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{ background: {COLORS['bg_card_hover']}; }}
        """

    def show_word(self, text: str):
        """Show sign visualization for a word/phrase."""
        self.letters = [ch.upper() for ch in text if ch.isalpha()]
        self.word_chars = list(text)
        self.current_index = 0
        self._empty = False
        self._stop_playback()
        if self.letters:
            self._show_letter(0)

    def _build_word_html(self):
        html = []
        li = 0
        for ch in self.word_chars:
            if ch == ' ':
                html.append('&nbsp;&nbsp;')
            elif ch.isalpha():
                active = (li == self.current_index)
                if active:
                    html.append(
                        f'<span style="color:{COLORS["primary"]}; font-size:22px; '
                        f'font-weight:900; background:{COLORS["primary"]}22; '
                        f'padding:1px 4px; border-radius:4px;">{ch.upper()}</span>'
                    )
                else:
                    done = li < self.current_index
                    c = COLORS['text_primary'] if done else COLORS['text_muted']
                    html.append(
                        f'<span style="color:{c}; font-size:18px; font-weight:600;">{ch.upper()}</span>'
                    )
                li += 1
            else:
                html.append(f'<span style="color:{COLORS["text_muted"]};">{ch}</span>')
        return ''.join(html)

    def _show_letter(self, idx):
        if idx < 0 or idx >= len(self.letters):
            return
        self.current_index = idx
        letter = self.letters[idx]
        self.sign_card.set_letter(letter)
        self.word_display.setText(self._build_word_html())
        self.progress_lbl.setText(f"{idx + 1}/{len(self.letters)}")
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < len(self.letters) - 1)

    def _prev(self):
        if self.current_index > 0:
            self._show_letter(self.current_index - 1)

    def _next(self):
        if self.current_index < len(self.letters) - 1:
            self._show_letter(self.current_index + 1)

    def _set_speed(self, ms):
        self._speed_ms = ms

    def _toggle_playback(self):
        if self._is_playing:
            self._stop_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        self._is_playing = True
        self.play_btn.setText("⏸ Pause")
        if self.current_index >= len(self.letters) - 1:
            self.current_index = -1
        self._play_next()

    def _stop_playback(self):
        self._is_playing = False
        self.play_btn.setText("▶ Play")
        if self._animation_timer:
            self._animation_timer.stop()

    def _play_next(self):
        if not self._is_playing:
            return
        ni = self.current_index + 1
        if ni >= len(self.letters):
            self._stop_playback()
            self.progress_lbl.setText("✅ Done!")
            return
        self._show_letter(ni)
        self._animation_timer = QTimer()
        self._animation_timer.setSingleShot(True)
        self._animation_timer.timeout.connect(self._play_next)
        self._animation_timer.start(self._speed_ms)

    def cleanup(self):
        self._stop_playback()
        self.sign_card.cleanup()


# ═══════════════════════════════════════════════════════════════
#  ConversationWidget — chat area + input
# ═══════════════════════════════════════════════════════════════

class ConversationWidget(QWidget):
    """Chat area with messages, input, and quick replies."""

    sign_requested = Signal(str)  # emitted when user wants sign viz for text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Chat scroll area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet(f"background: {COLORS['bg_app']};")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, stretch=1)

        # Quick replies
        qr_frame = QFrame()
        qr_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_panel']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        qr_layout = QHBoxLayout(qr_frame)
        qr_layout.setContentsMargins(12, 6, 12, 6)
        qr_layout.setSpacing(6)

        for reply in ["Hello!", "Thank you", "Yes", "No", "Help", "Goodbye"]:
            btn = QPushButton(reply)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 14px;
                    color: {COLORS['text_primary']};
                    padding: 5px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {COLORS['primary']}22;
                    border-color: {COLORS['primary']};
                    color: {COLORS['primary']};
                }}
            """)
            btn.clicked.connect(lambda checked, r=reply: self._quick_reply(r))
            qr_layout.addWidget(btn)
        qr_layout.addStretch()
        layout.addWidget(qr_frame)

        # Input row
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_panel']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        inp_layout = QHBoxLayout(input_frame)
        inp_layout.setContentsMargins(12, 10, 12, 10)
        inp_layout.setSpacing(8)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message and press 🤟 to see signs...")
        self.text_input.setObjectName("input")
        self.text_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 18px;
                padding: 8px 16px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.text_input.returnPressed.connect(self._send_and_sign)
        inp_layout.addWidget(self.text_input, stretch=1)

        # Send + Show Sign (combined button)
        sign_send_btn = QPushButton("🤟 Send & Show")
        sign_send_btn.setCursor(Qt.PointingHandCursor)
        sign_send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white; border: none;
                border-radius: 18px;
                padding: 8px 20px;
                font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """)
        sign_send_btn.clicked.connect(self._send_and_sign)
        inp_layout.addWidget(sign_send_btn)

        layout.addWidget(input_frame)

    def add_message(self, text: str, is_user: bool, message_type: str = "text"):
        ts = QDateTime.currentDateTime().toString("hh:mm")
        bubble = MessageBubble(text, is_user, ts, message_type)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        self.messages.append({'text': text, 'is_user': is_user, 'type': message_type})
        QTimer.singleShot(80, self._scroll_to_bottom)

    def add_signed_message(self, text: str):
        self.add_message(text, True, "sign")
        self.sign_requested.emit(text)

    def _send_and_sign(self):
        """Send text message AND show it in sign panel."""
        text = self.text_input.text().strip()
        if text:
            self.add_message(text, True, "text")
            self.text_input.clear()
            self.sign_requested.emit(text)

    def _quick_reply(self, reply: str):
        """Quick reply — sends message AND shows sign."""
        self.add_message(reply, True, "text")
        self.sign_requested.emit(reply)

    def _scroll_to_bottom(self):
        sb = self.chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear_conversation(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.messages = []


# ═══════════════════════════════════════════════════════════════
#  ConversationPage — full page with split layout
# ═══════════════════════════════════════════════════════════════

class ConversationPage(QWidget):
    """Conversation mode page with chat + persistent sign panel."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Compact header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_panel']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(24, 10, 24, 10)

        header, _ = make_page_header("💬 Conversation Mode")

        hint = QLabel("Type a message → see it in sign language")
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        header.addWidget(hint)

        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setObjectName("ghost")
        clear_btn.clicked.connect(self._clear)
        header.addWidget(clear_btn)

        h_layout.addLayout(header)
        layout.addWidget(header_frame)

        # Main content: chat + sign panel side by side
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # Chat (left, takes most space)
        self.conversation = ConversationWidget()
        content.addWidget(self.conversation, stretch=3)

        # Sign panel (right, persistent)
        self.sign_panel = SignPanel()
        content.addWidget(self.sign_panel, stretch=2)

        # Connect chat → sign panel
        self.conversation.sign_requested.connect(self.sign_panel.show_word)

        content_widget = QWidget()
        content_widget.setLayout(content)
        layout.addWidget(content_widget, stretch=1)

        # Welcome message
        self.conversation.add_message(
            "👋 Type a message and press Send to see it in sign language on the right panel!",
            False, "text"
        )

    def on_sign_detected(self, text: str):
        self.conversation.add_signed_message(text)

    def _clear(self):
        self.conversation.clear_conversation()
        self.conversation.add_message("Conversation cleared. Start fresh!", False, "text")

