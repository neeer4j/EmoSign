"""
Login Page - Premium Professional Design
Stunning split-panel layout with animated neural network background
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFrame, QGraphicsDropShadowEffect,
    QSpacerItem, QSizePolicy
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
            self.dx = random.uniform(-0.5, 0.5)
            self.dy = random.uniform(-0.5, 0.5)
            self.max_w = max_w
            self.max_h = max_h
            self.size = random.uniform(2, 5)
            
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
            
        # Network animation timer (60 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._update_network)
        self.anim_timer.start(16)
        
    def _init_nodes(self):
        self.nodes = [
            self.Node(
                random.uniform(0, self.width()),
                random.uniform(0, self.height()),
                self.width(), self.height()
            ) for _ in range(60) # Number of nodes
        ]
            
    def resizeEvent(self, event):
        self._init_nodes()
        super().resizeEvent(event)
            
    def _update_network(self):
        for node in self.nodes:
            node.update()
        self._phase += 0.02
        self.update()

    def _load_images(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assets_dir = os.path.join(base_dir, "assets")
        
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        excluded_files = {"icon.png", "emosign.png"}
        if os.path.exists(assets_dir):
            for f in sorted(os.listdir(assets_dir)):
                if f.lower() in excluded_files:
                    continue
                if os.path.splitext(f)[1].lower() in valid_exts:
                    pm = QPixmap(os.path.join(assets_dir, f))
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
        
        # 1. Draw Background Image Slideshow
        if self.pixmaps:
            def draw_bg(pm, opacity):
                if opacity <= 0: return
                scaled = pm.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                x = (self.width() - scaled.width()) // 2
                y = (self.height() - scaled.height()) // 2
                painter.setOpacity(opacity)
                painter.drawPixmap(x, y, scaled)
            
            draw_bg(self.pixmaps[self.current_idx], 1.0)
            if self._fade > 0:
                draw_bg(self.pixmaps[self.next_idx], self._fade)
        else:
            painter.fillRect(self.rect(), QColor("#0a0a0f" if ThemeManager.is_dark() else "#e2e8f0"))
            
        # 2. Dark/Light Overlay
        painter.setOpacity(0.85 if ThemeManager.is_dark() else 0.92)
        painter.fillRect(self.rect(), QColor('#080810' if ThemeManager.is_dark() else '#f0f4f8'))
        
        # 3. Draw Neural Network Overlay
        painter.setOpacity(1.0)
        pen = QPen(QColor(139, 92, 246, 50)) # Purple lines
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(6, 182, 212, 100))) # Cyan nodes
        
        # Draw connections
        for i, node1 in enumerate(self.nodes):
            # Draw node
            painter.drawEllipse(QPointF(node1.x, node1.y), node1.size, node1.size)
            
            # Connect to nearby nodes
            for node2 in self.nodes[i+1:]:
                dist = math.hypot(node1.x - node2.x, node1.y - node2.y)
                if dist < 150:
                    alpha = int((1 - dist/150) * 100) # Fade out with distance
                    pen.setColor(QColor(139, 92, 246, alpha))
                    painter.setPen(pen)
                    painter.drawLine(QPointF(node1.x, node1.y), QPointF(node2.x, node2.y))


class PremiumInput(QLineEdit):
    """Premium styled input with animated border."""
    
    def __init__(self, placeholder="", icon="", is_password=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.icon = icon
        
        if is_password:
            self.setEchoMode(QLineEdit.Password)
        
        is_dark = ThemeManager.is_dark()
        bg_color = 'rgba(255, 255, 255, 0.03)' if is_dark else 'rgba(0, 0, 0, 0.04)'
        border_color = 'rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0, 0, 0, 0.15)'
        text_color = '#ffffff' if is_dark else '#0f172a'
        focus_border = 'rgba(139, 92, 246, 0.6)'
        focus_bg = 'rgba(255, 255, 255, 0.05)' if is_dark else 'rgba(0, 0, 0, 0.02)'
        placeholder_color = 'rgba(255, 255, 255, 0.35)' if is_dark else 'rgba(0, 0, 0, 0.4)'
        
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 14px;
                padding: 18px 20px;
                padding-left: {50 if icon else 20}px;
                color: {text_color};
                font-size: 15px;
                font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
                font-weight: 400;
            }}
            QLineEdit:focus {{
                border: 1px solid {focus_border};
                background-color: {focus_bg};
            }}
            QLineEdit::placeholder {{
                color: {placeholder_color};
            }}
        """)
        self.setMinimumHeight(58)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.icon:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.TextAntialiasing)
            icon_color = QColor(255, 255, 255, 100) if ThemeManager.is_dark() else QColor(0, 0, 0, 100)
            painter.setPen(icon_color)
            painter.setFont(QFont("Segoe UI Emoji", 14))
            painter.drawText(18, 38, self.icon)


class GradientButton(QPushButton):
    """Premium gradient button with hover effects."""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(58)
        
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #8b5cf6, stop:0.5 #a855f7, stop:1 #ec4899);
                color: white;
                font-weight: 600;
                font-size: 15px;
                font-family: 'Segoe UI', sans-serif;
                border-radius: 14px;
                border: none;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #9b6cf6, stop:0.5 #b865f7, stop:1 #f458a3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #7c4ce6, stop:0.5 #9845e7, stop:1 #dc3889);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Add glow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(139, 92, 246, 100))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)


class LoginPage(QWidget):
    """Premium Professional Login Page with split-panel design."""
    
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
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === LEFT PANEL - Branding ===
        left_panel = QFrame()
        left_panel.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(60, 60, 60, 60)
        left_layout.setAlignment(Qt.AlignCenter)
        
        is_dark = ThemeManager.is_dark()
        text_color = 'white' if is_dark else '#0f172a'
        subtext_color = 'rgba(255, 255, 255, 0.7)' if is_dark else 'rgba(0, 0, 0, 0.6)'
        
        # App name (EmoSign)
        app_name = QLabel("EmoSign")
        app_name.setStyleSheet(f"""
            font-size: 56px;
            font-weight: 800;
            color: {text_color};
            letter-spacing: -2px;
            background: transparent;
        """)
        
        tagline = QLabel("Emotion & Sign Language Translator")
        tagline.setStyleSheet(f"""
            font-size: 18px;
            color: {subtext_color};
            background: transparent;
        """)
        
        # Feature highlights
        features_container = QFrame()
        features_container.setStyleSheet("background: transparent;")
        features_layout = QVBoxLayout(features_container)
        features_layout.setSpacing(20)
        features_layout.setContentsMargins(0, 50, 0, 0)
        
        features = [
            ("🖐️", "Hand Gesture Recognition", "ASL alphabet A-Z detection"),
            ("😊", "Emotion Detection", "Real-time facial analysis"),
            ("📹", "Video Processing", "Upload and translate videos"),
            ("💾", "Translation History", "Save and review translations"),
        ]
        
        for icon, title, desc in features:
            feature_row = QHBoxLayout()
            feature_row.setSpacing(16)
            
            icon_label = QLabel(icon)
            icon_bg = 'rgba(139, 92, 246, 0.15)' if is_dark else 'rgba(139, 92, 246, 0.1)'
            icon_border = 'rgba(139, 92, 246, 0.2)' if is_dark else 'rgba(139, 92, 246, 0.15)'
            icon_label.setStyleSheet(f"""
                font-size: 24px;
                background: {icon_bg};
                border-radius: 12px;
                padding: 10px;
                border: 1px solid {icon_border};
            """)
            icon_label.setFixedSize(54, 54)
            icon_label.setAlignment(Qt.AlignCenter)
            
            text_container = QVBoxLayout()
            text_container.setSpacing(2)
            
            title_label = QLabel(title)
            title_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {text_color}; background: transparent;")
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet(f"font-size: 13px; color: {subtext_color}; background: transparent;")
            
            text_container.addWidget(title_label)
            text_container.addWidget(desc_label)
            
            feature_row.addWidget(icon_label)
            feature_row.addLayout(text_container)
            feature_row.addStretch()
            
            features_layout.addLayout(feature_row)
        
        left_layout.addStretch()
        left_layout.addWidget(app_name, alignment=Qt.AlignLeft)
        left_layout.addWidget(tagline, alignment=Qt.AlignLeft)
        left_layout.addWidget(features_container)
        left_layout.addStretch()
        
        # === RIGHT PANEL - Login Form ===
        right_panel = QFrame()
        panel_bg = 'rgba(10, 10, 15, 0.7)' if is_dark else 'rgba(255, 255, 255, 0.85)'
        panel_border = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.1)'
        right_panel.setStyleSheet(f"""
            background: {panel_bg};
            border-left: 1px solid {panel_border};
        """)
        # Blur effect for glassmorphism
        blur = QGraphicsDropShadowEffect(right_panel)
        blur.setBlurRadius(0) 
        
        right_panel.setFixedWidth(500)
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(60, 60, 60, 60)
        right_layout.setSpacing(0)
        
        # Spacer
        right_layout.addStretch()
        
        # Form header
        self.header_title = QLabel("Welcome back")
        self.header_title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {text_color};
            background: transparent;
        """)
        
        self.header_subtitle = QLabel("Sign in to continue")
        self.header_subtitle.setStyleSheet(f"""
            font-size: 16px;
            color: {subtext_color};
            background: transparent;
            margin-top: 8px;
        """)
        
        right_layout.addWidget(self.header_title)
        right_layout.addWidget(self.header_subtitle)
        right_layout.addSpacing(40)
        
        # Form inputs
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        self.email_input = PremiumInput("Email Address", "📧")
        self.password_input = PremiumInput("Password", "🔒", is_password=True)
        self.confirm_input = PremiumInput("Confirm Password", "🔒", is_password=True)
        self.confirm_input.hide()
        
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.confirm_input)
        
        right_layout.addLayout(form_layout)
        
        # Messages
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            color: #ef4444; background: transparent; font-size: 13px; margin-top: 10px;
        """)
        self.error_label.hide()
        
        self.success_label = QLabel()
        self.success_label.setStyleSheet("color: #22c55e; background: transparent; margin-top: 10px;")
        self.success_label.hide()
        
        right_layout.addWidget(self.error_label)
        right_layout.addWidget(self.success_label)
        right_layout.addSpacing(30)
        
        # Submit button
        self.submit_btn = GradientButton("Sign In")
        right_layout.addWidget(self.submit_btn)
        
        right_layout.addSpacing(24)
        
        # Divider
        divider_layout = QHBoxLayout()
        line1 = QFrame()
        line1.setFixedHeight(1)
        line_color = 'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.1)'
        line1.setStyleSheet(f"background: {line_color};")
        or_color = 'rgba(255,255,255,0.3)' if is_dark else 'rgba(0,0,0,0.3)'
        or_label = QLabel("OR")
        or_label.setStyleSheet(f"color: {or_color}; font-size: 12px; padding: 0 10px; font-weight: 600;")
        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet(f"background: {line_color};")
        divider_layout.addWidget(line1)
        divider_layout.addWidget(or_label)
        divider_layout.addWidget(line2)
        right_layout.addLayout(divider_layout)
        
        right_layout.addSpacing(24)
        
        # Guest button
        self.skip_btn = QPushButton("Continue as Guest")
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setMinimumHeight(54)
        guest_bg = 'rgba(255, 255, 255, 0.03)' if is_dark else 'rgba(0, 0, 0, 0.04)'
        guest_color = 'rgba(255, 255, 255, 0.7)' if is_dark else 'rgba(0, 0, 0, 0.6)'
        guest_border = 'rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0, 0, 0, 0.1)'
        guest_hover_bg = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'
        guest_hover_color = 'white' if is_dark else '#0f172a'
        guest_hover_border = 'rgba(255, 255, 255, 0.2)' if is_dark else 'rgba(0, 0, 0, 0.2)'
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: {guest_bg};
                color: {guest_color};
                font-size: 14px;
                font-weight: 500;
                border: 1px solid {guest_border};
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: {guest_hover_bg};
                color: {guest_hover_color};
                border: 1px solid {guest_hover_border};
            }}
        """)
        right_layout.addWidget(self.skip_btn)
        
        # Toggle mode
        right_layout.addStretch()
        toggle_container = QHBoxLayout()
        toggle_text_color = 'rgba(255,255,255,0.5)' if is_dark else 'rgba(0,0,0,0.5)'
        toggle_text = QLabel("Don't have an account?")
        toggle_text.setStyleSheet(f"color: {toggle_text_color}; font-size: 14px;")
        
        self.toggle_btn = QPushButton("Create Account")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #a855f7; font-weight: 600; font-size: 14px; border: none;
            }
            QPushButton:hover { color: #d8b4fe; }
        """)
        
        toggle_container.addStretch()
        toggle_container.addWidget(toggle_text)
        toggle_container.addWidget(self.toggle_btn)
        toggle_container.addStretch()
        
        right_layout.addLayout(toggle_container)
        right_layout.addStretch()
        
        # Add panels
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel)
    
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
