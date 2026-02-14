"""
Login Page - Premium Professional Design
Stunning centered glassmorphism card with animated neural network background
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFrame, QGraphicsDropShadowEffect,
    QSpacerItem, QSizePolicy, QGraphicsBlurEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, Property, QRectF, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QPen, QPixmap, QPainterPath
import math
import random
import os

from ui.styles import COLORS, ThemeManager


class NeuralNetworkBackground(QWidget):
    """Animated background with neural network nodes and connections overlaying images."""
    
    class Node:
        def __init__(self, x, y, max_w, max_h):
            self.x = x
            self.y = y
            self.dx = random.uniform(-0.3, 0.3)
            self.dy = random.uniform(-0.3, 0.3)
            self.max_w = max_w
            self.max_h = max_h
            self.size = random.uniform(2, 4.5)
            
        def update(self):
            self.x += self.dx
            self.y += self.dy
            
            # Bounce off edges
            if self.x < 0 or self.x > self.max_w: self.dx *= -1
            if self.y < 0 or self.y > self.max_h: self.dy *= -1
            
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []
        self._phase = 0.0
        
        # Image slideshow state
        self.pixmaps = []
        self.current_idx = 0
        self.next_idx = 1
        self._fade = 0.0
        
        # Load images
        self._load_images()
        
        # Animations
        self.fade_anim = QPropertyAnimation(self, b"fade")
        self.fade_anim.setDuration(2000)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.finished.connect(self._on_fade_finished)
        
        # Slideshow timer
        if len(self.pixmaps) > 1:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._next_slide)
            self.timer.start(8000)
            
        # Network animation timer (~30 FPS for smoothness without CPU burn)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_network)
        self.anim_timer.start(33)
        
    def _init_nodes(self):
        self.nodes = [
            self.Node(
                random.uniform(0, self.width()),
                random.uniform(0, self.height()),
                self.width(), self.height()
            ) for _ in range(50)  # Number of nodes
        ]
            
    def resizeEvent(self, event):
        self._init_nodes()
        super().resizeEvent(event)
            
    def _update_network(self):
        for node in self.nodes:
            node.update()
        self._phase += 0.015
        self.update()

    def _load_images(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        slide_dir = os.path.join(base_dir, "assets", "slidepic")
        
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        if os.path.exists(slide_dir):
            for f in sorted(os.listdir(slide_dir)):
                if os.path.splitext(f)[1].lower() in valid_exts:
                    pm = QPixmap(os.path.join(slide_dir, f))
                    if not pm.isNull():
                        self.pixmaps.append(pm)
                        
    def _next_slide(self):
        self.next_idx = (self.current_idx + 1) % len(self.pixmaps)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
    def _on_fade_finished(self):
        self.current_idx = self.next_idx
        self._fade = 0.0
        self.update()
    
    def get_fade(self): return self._fade
    def set_fade(self, val): self._fade = val; self.update()
    fade = Property(float, get_fade, set_fade)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        w, h = self.width(), self.height()
        is_dark = ThemeManager.is_dark()
        
        # 1. Draw Background Image Slideshow
        if self.pixmaps:
            def draw_bg(pm, opacity):
                if opacity <= 0: return
                scaled = pm.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x = (w - scaled.width()) // 2
                y = (h - scaled.height()) // 2
                painter.setOpacity(opacity)
                painter.drawPixmap(x, y, scaled)
            
            draw_bg(self.pixmaps[self.current_idx], 1.0)
            if self._fade > 0:
                draw_bg(self.pixmaps[self.next_idx], self._fade)
        else:
            painter.fillRect(self.rect(), QColor("#0a0a0f" if is_dark else "#e2e8f0"))
            
        # 2. Dark/Light Overlay with gradient
        painter.setOpacity(1.0)
        overlay = QLinearGradient(0, 0, w, h)
        if is_dark:
            overlay.setColorAt(0.0, QColor(8, 8, 16, 225))
            overlay.setColorAt(0.5, QColor(10, 10, 20, 210))
            overlay.setColorAt(1.0, QColor(15, 12, 30, 230))
        else:
            overlay.setColorAt(0.0, QColor(240, 244, 248, 235))
            overlay.setColorAt(0.5, QColor(248, 250, 252, 230))
            overlay.setColorAt(1.0, QColor(240, 244, 248, 240))
        painter.fillRect(self.rect(), overlay)
        
        # 3. Subtle radial glow at center
        painter.setOpacity(0.08 if is_dark else 0.04)
        glow = QLinearGradient(w * 0.3, h * 0.3, w * 0.7, h * 0.7)
        glow.setColorAt(0.0, QColor(139, 92, 246))
        glow.setColorAt(1.0, QColor(6, 182, 212))
        painter.fillRect(self.rect(), glow)
        
        # 4. Draw Neural Network Overlay
        painter.setOpacity(1.0)
        node_color = QColor(139, 92, 246, 80) if is_dark else QColor(139, 92, 246, 50)
        line_alpha_base = 80 if is_dark else 40
        
        painter.setBrush(QBrush(node_color))
        
        # Draw connections first (behind nodes)
        for i, node1 in enumerate(self.nodes):
            for node2 in self.nodes[i+1:]:
                dist = math.hypot(node1.x - node2.x, node1.y - node2.y)
                if dist < 140:
                    alpha = int((1 - dist/140) * line_alpha_base)
                    pen = QPen(QColor(139, 92, 246, alpha))
                    pen.setWidthF(0.8)
                    painter.setPen(pen)
                    painter.drawLine(QPointF(node1.x, node1.y), QPointF(node2.x, node2.y))
        
        # Draw nodes on top
        painter.setPen(Qt.NoPen)
        for node in self.nodes:
            # Soft glow around each node
            glow_color = QColor(139, 92, 246, 20)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QPointF(node.x, node.y), node.size * 3, node.size * 3)
            
            # Solid node
            painter.setBrush(QBrush(node_color))
            painter.drawEllipse(QPointF(node.x, node.y), node.size, node.size)


class PremiumInput(QLineEdit):
    """Premium styled input with floating label feel."""
    
    def __init__(self, placeholder="", icon="", is_password=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.icon = icon
        
        if is_password:
            self.setEchoMode(QLineEdit.Password)
        
        is_dark = ThemeManager.is_dark()
        bg_color = 'rgba(255, 255, 255, 0.04)' if is_dark else 'rgba(255, 255, 255, 0.7)'
        border_color = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.08)'
        text_color = '#f1f5f9' if is_dark else '#1e293b'
        focus_border = 'rgba(139, 92, 246, 0.5)'
        focus_bg = 'rgba(139, 92, 246, 0.06)' if is_dark else 'rgba(139, 92, 246, 0.04)'
        placeholder_color = 'rgba(255, 255, 255, 0.3)' if is_dark else 'rgba(0, 0, 0, 0.35)'
        
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_color};
                border: 1.5px solid transparent;
                border-radius: 12px;
                padding: 16px 20px;
                padding-left: {48 if icon else 20}px;
                color: {text_color};
                font-size: 14px;
                font-family: 'Nunito', 'Segoe UI', sans-serif;
                font-weight: 500;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {focus_border};
                background-color: {focus_bg};
            }}
            QLineEdit::placeholder {{
                color: {placeholder_color};
            }}
        """)
        self.setMinimumHeight(52)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.icon:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.TextAntialiasing)
            icon_color = QColor(255, 255, 255, 80) if ThemeManager.is_dark() else QColor(0, 0, 0, 80)
            painter.setPen(icon_color)
            painter.setFont(QFont("Segoe UI Emoji", 13))
            painter.drawText(16, 34, self.icon)


class GradientButton(QPushButton):
    """Premium gradient button with hover effects."""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(52)
        
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #7c3aed, stop:0.5 #8b5cf6, stop:1 #a855f7);
                color: white;
                font-weight: 700;
                font-size: 15px;
                font-family: 'Nunito', 'Segoe UI', sans-serif;
                border-radius: 12px;
                border: none;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #6d28d9, stop:0.5 #7c3aed, stop:1 #9333ea);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #5b21b6, stop:0.5 #6d28d9, stop:1 #7c3aed);
            }
            QPushButton:disabled {
                background: rgba(139, 92, 246, 0.3);
                color: rgba(255, 255, 255, 0.4);
            }
        """)
        
        # Subtle glow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(139, 92, 246, 80))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)


class LoginPage(QWidget):
    """Premium Professional Login Page with centered glassmorphism card."""
    
    login_successful = Signal(dict)
    signup_successful = Signal(dict)
    
    def __init__(self, db_service=None, parent=None):
        super().__init__(parent)
        self.db = db_service
        self.is_login_mode = True
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        # Background: Image Slideshow + Neural Network Overlay
        self.bg = NeuralNetworkBackground(self)
        self.bg.setGeometry(0, 0, 3000, 2000)
        self.bg.lower()
        
        # Main overlay layout — centers the card
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        is_dark = ThemeManager.is_dark()
        
        # === LEFT PANEL — Branding === 
        left_panel = QFrame()
        left_panel.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(80, 80, 60, 80)
        left_layout.setAlignment(Qt.AlignCenter)
        
        text_color = '#f1f5f9' if is_dark else '#0f172a'
        subtext_color = 'rgba(255, 255, 255, 0.6)' if is_dark else 'rgba(15, 23, 42, 0.55)'
        accent_color = '#a78bfa'
        
        # App icon/logo area
        logo_container = QHBoxLayout()
        logo_container.setSpacing(14)
        
        logo_label = QLabel()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "assets", "newlogo.png")
        
        # Load and scale logo
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Colorize logic for visibility
                target_color = QColor('white') if is_dark else QColor('#0f172a')
                
                # Create a colorized version
                img = pixmap.toImage()
                result = QPixmap(pixmap.size())
                result.fill(Qt.transparent)
                painter = QPainter(result)
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                painter.drawPixmap(0, 0, pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(result.rect(), target_color)
                painter.end()
                
                scaled = result.scaledToHeight(64, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled)
                logo_label.setStyleSheet("background: transparent; border: none;")
        
        # Fallback text if no logo
        if logo_label.pixmap().isNull():
             logo_label.setText("EMOSIGN")
             logo_label.setStyleSheet(f"""
                font-size: 24px;
                font-weight: 800;
                color: {accent_color};
                letter-spacing: 4px;
                background: transparent;
                border: none;
            """)

        logo_container.addWidget(logo_label)
        logo_container.addStretch()
        
        # Big headline
        headline = QLabel("Bridging\nCommunication\nBarriers")
        headline.setStyleSheet(f"""
            font-size: 48px;
            font-weight: 800;
            color: {text_color};
            line-height: 1.1;
            background: transparent;
            letter-spacing: -1px;
        """)
        
        tagline = QLabel("Real-time sign language detection & emotion\nanalysis powered by AI")
        tagline.setStyleSheet(f"""
            font-size: 16px;
            color: {subtext_color};
            background: transparent;
            line-height: 1.6;
            margin-top: 16px;
        """)
        
        # Feature pills
        pills_layout = QHBoxLayout()
        pills_layout.setSpacing(10)
        
        pill_items = ["ASL A-Z", "Emotion AI", "Real-time"]
        pill_bg = 'rgba(139, 92, 246, 0.12)' if is_dark else 'rgba(139, 92, 246, 0.08)'
        pill_border = 'rgba(139, 92, 246, 0.2)' if is_dark else 'rgba(139, 92, 246, 0.15)'
        
        for pill_text in pill_items:
            pill = QLabel(pill_text)
            pill.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 600;
                color: {accent_color};
                background: {pill_bg};
                border: 1px solid {pill_border};
                border-radius: 16px;
                padding: 6px 14px;
            """)
            pill.setAlignment(Qt.AlignCenter)
            pills_layout.addWidget(pill)
        pills_layout.addStretch()
        
        left_layout.addStretch(2)
        left_layout.addLayout(logo_container)
        left_layout.addSpacing(24)
        left_layout.addWidget(headline)
        left_layout.addWidget(tagline)
        left_layout.addSpacing(28)
        left_layout.addLayout(pills_layout)
        left_layout.addStretch(3)
        
        # === RIGHT PANEL — Glass Card ===
        right_panel = QFrame()
        right_panel.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 60, 80, 60)
        right_layout.setAlignment(Qt.AlignCenter)
        
        # The glass card
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)
        
        card_bg = 'rgba(15, 15, 25, 0.65)' if is_dark else 'rgba(255, 255, 255, 0.8)'
        card_border = 'rgba(255, 255, 255, 0.06)' if is_dark else 'rgba(0, 0, 0, 0.06)'
        
        card.setStyleSheet(f"""
            #loginCard {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 24px;
            }}
        """)
        
        # Card shadow for depth
        card_shadow = QGraphicsDropShadowEffect(card)
        card_shadow.setBlurRadius(60)
        card_shadow.setColor(QColor(0, 0, 0, 80) if is_dark else QColor(0, 0, 0, 30))
        card_shadow.setOffset(0, 12)
        card.setGraphicsEffect(card_shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 44, 40, 40)
        card_layout.setSpacing(0)
        
        # Form header
        self.header_title = QLabel("Welcome back")
        self.header_title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {text_color};
            background: transparent;
            border: none;
        """)
        
        self.header_subtitle = QLabel("Sign in to continue")
        self.header_subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {subtext_color};
            background: transparent;
            margin-top: 6px;
            border: none;
        """)
        
        card_layout.addWidget(self.header_title)
        card_layout.addWidget(self.header_subtitle)
        card_layout.addSpacing(32)
        
        # Form inputs
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        
        self.email_input = PremiumInput("Email Address", "📧")
        self.password_input = PremiumInput("Password", "🔒", is_password=True)
        self.confirm_input = PremiumInput("Confirm Password", "🔒", is_password=True)
        self.confirm_input.hide()
        
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.confirm_input)
        
        card_layout.addLayout(form_layout)
        
        # Messages
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            color: #f87171; background: rgba(248, 113, 113, 0.08);
            font-size: 13px; padding: 8px 12px; border-radius: 8px; margin-top: 8px;
            border: none;
        """)
        self.error_label.hide()
        
        self.success_label = QLabel()
        self.success_label.setStyleSheet("""
            color: #34d399; background: rgba(52, 211, 153, 0.08);
            font-size: 13px; padding: 8px 12px; border-radius: 8px; margin-top: 8px;
            border: none;
        """)
        self.success_label.hide()
        
        card_layout.addWidget(self.error_label)
        card_layout.addWidget(self.success_label)
        card_layout.addSpacing(24)
        
        # Submit button
        self.submit_btn = GradientButton("Sign In")
        card_layout.addWidget(self.submit_btn)
        
        card_layout.addSpacing(20)
        
        # Divider
        divider_layout = QHBoxLayout()
        line_color = 'rgba(255,255,255,0.06)' if is_dark else 'rgba(0,0,0,0.06)'
        or_color = 'rgba(255,255,255,0.25)' if is_dark else 'rgba(0,0,0,0.25)'
        
        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setStyleSheet(f"background: {line_color};")
        
        or_label = QLabel("OR")
        or_label.setStyleSheet(f"""
            color: {or_color}; font-size: 11px; padding: 0 12px;
            font-weight: 700; letter-spacing: 1px; background: transparent;
            border: none;
        """)
        
        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet(f"background: {line_color};")
        
        divider_layout.addWidget(line1)
        divider_layout.addWidget(or_label)
        divider_layout.addWidget(line2)
        card_layout.addLayout(divider_layout)
        
        card_layout.addSpacing(20)
        
        # Guest button
        self.skip_btn = QPushButton("Continue as Guest")
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setMinimumHeight(48)
        guest_bg = 'rgba(255, 255, 255, 0.04)' if is_dark else 'rgba(0, 0, 0, 0.03)'
        guest_color = 'rgba(255, 255, 255, 0.55)' if is_dark else 'rgba(0, 0, 0, 0.5)'
        guest_border = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.08)'
        guest_hover_bg = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'
        guest_hover_color = '#f1f5f9' if is_dark else '#1e293b'
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: {guest_bg};
                color: {guest_color};
                font-size: 13px;
                font-weight: 600;
                font-family: 'Nunito', 'Segoe UI', sans-serif;
                border: 1px solid transparent;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background: {guest_hover_bg};
                color: {guest_hover_color};
            }}
        """)
        card_layout.addWidget(self.skip_btn)
        
        # Toggle mode
        card_layout.addSpacing(24)
        toggle_container = QHBoxLayout()
        toggle_text_color = 'rgba(255,255,255,0.4)' if is_dark else 'rgba(0,0,0,0.4)'
        toggle_text = QLabel("Don't have an account?")
        toggle_text.setStyleSheet(f"color: {toggle_text_color}; font-size: 13px; background: transparent; border: none;")
        
        self.toggle_btn = QPushButton("Create Account")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #a78bfa; font-weight: 700;
                font-size: 13px; border: none;
                font-family: 'Nunito', 'Segoe UI', sans-serif;
            }
            QPushButton:hover { color: #c4b5fd; }
        """)
        
        toggle_container.addStretch()
        toggle_container.addWidget(toggle_text)
        toggle_container.addWidget(self.toggle_btn)
        toggle_container.addStretch()
        
        card_layout.addLayout(toggle_container)
        
        right_layout.addWidget(card)
        
        # Add panels
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 0)
    
    def resizeEvent(self, event):
        self.bg.setGeometry(self.rect())
        super().resizeEvent(event)
    
    def _connect_signals(self):
        self.submit_btn.clicked.connect(self._handle_submit)
        self.toggle_btn.clicked.connect(self._toggle_mode)
        self.skip_btn.clicked.connect(self._skip_login)
        self.email_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self._handle_submit)
        self.confirm_input.returnPressed.connect(self._handle_submit)
    
    def _toggle_mode(self):
        self.is_login_mode = not self.is_login_mode
        self._clear_messages()
        
        if self.is_login_mode:
            self.header_title.setText("Welcome back")
            self.header_subtitle.setText("Sign in to continue")
            self.submit_btn.setText("Sign In")
            self.toggle_btn.setText("Create Account")
            self.toggle_btn.parent().findChildren(QLabel)[0].setText("Don't have an account?") if self.toggle_btn.parent() else None
            self.confirm_input.hide()
        else:
            self.header_title.setText("Create Account")
            self.header_subtitle.setText("Start your EmoSign journey")
            self.submit_btn.setText("Sign Up")
            self.toggle_btn.setText("Sign In")
            self.toggle_btn.parent().findChildren(QLabel)[0].setText("Already have an account?") if self.toggle_btn.parent() else None
            self.confirm_input.show()
    
    def _handle_submit(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self._show_error("Please fill in all fields")
            return
        
        if not self.is_login_mode:
            if len(password) < 6:
                self._show_error("Password must be at least 6 characters")
                return
            if password != self.confirm_input.text():
                self._show_error("Passwords do not match")
                return
        
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Processing...")
        
        if self.db:
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                if self.is_login_mode:
                    res = loop.run_until_complete(self.db.sign_in(email, password))
                else:
                    res = loop.run_until_complete(self.db.sign_up(email, password))
                
                if "error" in res:
                    self._show_error(res["error"])
                    self.submit_btn.setEnabled(True)
                    self.submit_btn.setText("Sign In" if self.is_login_mode else "Sign Up")
                else:
                    self._show_success("Success! Redirecting...")
                    QTimer.singleShot(800, lambda: self._complete_auth(res.get("user")))
            except Exception as e:
                self._show_error(str(e))
                self.submit_btn.setEnabled(True)
                self.submit_btn.setText("Sign In" if self.is_login_mode else "Sign Up")
            finally:
                loop.close()
        else:
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Sign In" if self.is_login_mode else "Sign Up")
            self._complete_auth({"id": "offline", "email": email})
    
    def _complete_auth(self, user):
        if self.is_login_mode:
            self.login_successful.emit(user)
        else:
            self.signup_successful.emit(user)
    
    def _skip_login(self):
        self.login_successful.emit({"id": "guest", "email": "Guest", "guest": True})
    
    def _show_error(self, msg):
        self.error_label.setText(f"⚠️ {msg}")
        self.error_label.show()
        self.success_label.hide()
    
    def _show_success(self, msg):
        self.success_label.setText(f"✓ {msg}")
        self.success_label.show()
        self.error_label.hide()
    
    def _clear_messages(self):
        self.error_label.hide()
        self.success_label.hide()
    
    def clear_form(self):
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self._clear_messages()
        self.submit_btn.setEnabled(True)
