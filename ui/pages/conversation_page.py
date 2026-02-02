"""
Conversation Mode - Two-way communication support

Enables back-and-forth conversations between:
- Sign language users (signing to text)
- Non-signers (typing/speaking to sign visualization)

Features:
- Conversation thread display
- Turn-based communication
- Message history
- Quick responses
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QTextEdit, QSplitter,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS


class MessageBubble(QFrame):
    """A chat message bubble."""
    
    def __init__(self, text: str, is_user: bool, timestamp: str = "",
                 message_type: str = "text", parent=None):
        super().__init__(parent)
        
        # Styling based on sender
        if is_user:
            bg_color = COLORS['primary']
            text_color = "#ffffff"
            align = Qt.AlignRight
            margin = "0 0 0 60px"
        else:
            bg_color = COLORS['bg_card']
            text_color = COLORS['text_primary']
            align = Qt.AlignLeft
            margin = "0 60px 0 0"
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 16px;
                margin: {margin};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Message type indicator
        if message_type == "sign":
            type_label = QLabel("✋ Signed")
            type_label.setStyleSheet(f"color: {text_color}; font-size: 10px; opacity: 0.7;")
            layout.addWidget(type_label)
        elif message_type == "voice":
            type_label = QLabel("🎤 Spoken")
            type_label.setStyleSheet(f"color: {text_color}; font-size: 10px; opacity: 0.7;")
            layout.addWidget(type_label)
        
        # Message text
        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 15px;
            background: transparent;
        """)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        # Timestamp
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(f"color: {text_color}; font-size: 10px; opacity: 0.6;")
            time_label.setAlignment(Qt.AlignRight)
            layout.addWidget(time_label)


class QuickReplyButton(QPushButton):
    """A quick reply button."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                color: {COLORS['text_primary']};
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_card_hover']};
                border-color: {COLORS['primary']};
            }}
        """)


class ConversationWidget(QWidget):
    """Main conversation interface."""
    
    message_sent = Signal(str, str)  # message, type ('text', 'sign', 'voice')
    translation_requested = Signal(str)  # text to translate to sign
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, stretch=1)
        
        # Quick replies
        quick_replies_frame = QFrame()
        quick_replies_frame.setStyleSheet(f"background: {COLORS['bg_panel']};")
        quick_layout = QHBoxLayout(quick_replies_frame)
        quick_layout.setContentsMargins(16, 8, 16, 8)
        quick_layout.setSpacing(8)
        
        quick_replies = ["Hello!", "Thank you", "Yes", "No", "Help"]
        for reply in quick_replies:
            btn = QuickReplyButton(reply)
            btn.clicked.connect(lambda checked, r=reply: self._send_quick_reply(r))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        
        layout.addWidget(quick_replies_frame)
        
        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_panel']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(12)
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setObjectName("input")
        self.text_input.returnPressed.connect(self._send_text_message)
        input_layout.addWidget(self.text_input, stretch=1)
        
        # Send button
        send_btn = QPushButton("Send")
        send_btn.setObjectName("primaryButton")
        send_btn.clicked.connect(self._send_text_message)
        input_layout.addWidget(send_btn)
        
        # Show as sign button
        sign_btn = QPushButton("🤟")
        sign_btn.setToolTip("Show as sign")
        sign_btn.setFixedSize(40, 40)
        sign_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent']};
                border-radius: 20px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: {COLORS['accent_hover']};
            }}
        """)
        sign_btn.clicked.connect(self._request_sign_translation)
        input_layout.addWidget(sign_btn)
        
        layout.addWidget(input_frame)
    
    def add_message(self, text: str, is_user: bool, message_type: str = "text"):
        """Add a message to the conversation."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm")
        
        bubble = MessageBubble(text, is_user, timestamp, message_type)
        
        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Store message
        self.messages.append({
            'text': text,
            'is_user': is_user,
            'type': message_type,
            'timestamp': timestamp
        })
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def add_signed_message(self, text: str):
        """Add a message that was signed by the user."""
        self.add_message(text, True, "sign")
    
    def add_response(self, text: str):
        """Add a response from the other party."""
        self.add_message(text, False, "text")
    
    def _send_text_message(self):
        """Send a typed text message."""
        text = self.text_input.text().strip()
        if text:
            self.add_message(text, True, "text")
            self.text_input.clear()
            self.message_sent.emit(text, "text")
    
    def _send_quick_reply(self, reply: str):
        """Send a quick reply."""
        self.add_message(reply, True, "text")
        self.message_sent.emit(reply, "text")
    
    def _request_sign_translation(self):
        """Request sign translation for current input."""
        text = self.text_input.text().strip()
        if text:
            self.translation_requested.emit(text)
            self.text_input.clear()
    
    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_conversation(self):
        """Clear all messages."""
        # Remove all message bubbles
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.messages = []


class ConversationPage(QWidget):
    """Full conversation mode page."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        title = QLabel("💬 Conversation Mode")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self._clear_conversation)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # Instructions
        instructions = QFrame()
        instructions.setObjectName("card")
        inst_layout = QHBoxLayout(instructions)
        inst_layout.setContentsMargins(16, 12, 16, 12)
        
        inst_text = QLabel(
            "💡 Sign to add messages, or type to communicate. "
            "Use the 🤟 button to show your message as signs."
        )
        inst_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        inst_text.setWordWrap(True)
        inst_layout.addWidget(inst_text)
        
        layout.addWidget(instructions)
        
        # Splitter for camera and chat
        splitter = QSplitter(Qt.Horizontal)
        
        # Camera/signing area placeholder
        camera_frame = QFrame()
        camera_frame.setObjectName("card")
        camera_frame.setMinimumWidth(400)
        camera_layout = QVBoxLayout(camera_frame)
        
        camera_title = QLabel("📷 Camera Feed")
        camera_title.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        camera_layout.addWidget(camera_title)
        
        camera_placeholder = QLabel("Camera preview will appear here")
        camera_placeholder.setStyleSheet(f"""
            background: {COLORS['bg_input']};
            color: {COLORS['text_muted']};
            border-radius: 8px;
            padding: 40px;
        """)
        camera_placeholder.setAlignment(Qt.AlignCenter)
        camera_layout.addWidget(camera_placeholder, stretch=1)
        
        # Status
        self.status_label = QLabel("Ready to detect signs")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        camera_layout.addWidget(self.status_label)
        
        splitter.addWidget(camera_frame)
        
        # Conversation widget
        self.conversation = ConversationWidget()
        splitter.addWidget(self.conversation)
        
        splitter.setSizes([400, 600])
        layout.addWidget(splitter, stretch=1)
        
        # Add welcome message
        self.conversation.add_response(
            "👋 Welcome to conversation mode! Start signing or type a message."
        )
    
    def on_sign_detected(self, text: str):
        """Handle detected sign translation."""
        self.conversation.add_signed_message(text)
        self.status_label.setText(f"Detected: {text}")
        self.status_label.setStyleSheet(f"color: {COLORS['success']};")
        
        # Reset status after delay
        QTimer.singleShot(2000, self._reset_status)
    
    def _reset_status(self):
        """Reset status label."""
        self.status_label.setText("Ready to detect signs")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
    
    def _clear_conversation(self):
        """Clear the conversation."""
        self.conversation.clear_conversation()
        self.conversation.add_response("Conversation cleared. Start fresh!")
