"""
Main Window - Application shell with navigation
Premium multi-page application with sidebar navigation

Enhanced with:
- Voice output support
- Multi-language support
- Tutorial and gesture library pages
- Settings and analytics pages
- Conversation mode
- Theme switching (dark/light)
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QMessageBox, QFrame, QStackedWidget,
    QPushButton, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import DARK_THEME, LIGHT_THEME, COLORS, ICONS, ThemeManager
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.live_translation_page import LiveTranslationPage
from ui.pages.history_page import HistoryPage
from ui.pages.profile_page import ProfilePage
from ui.pages.admin_page import AdminPage

# New feature pages
from ui.pages.tutorial_page import TutorialPage
from ui.pages.settings_page import SettingsPage
from ui.pages.analytics_page import AnalyticsPage
from ui.pages.conversation_page import ConversationPage
from ui.pages.training_page import TrainingPage
from ui.pages.game_page import GamePage

from ml.classifier import Classifier
from ml.data_collector import DataCollector
from ml.trainer import Trainer

# Import new core features
try:
    from core.voice_output import voice_output
except ImportError:
    voice_output = None

try:
    from core.analytics import analytics
except ImportError:
    analytics = None

# Import database service if available
try:
    from backend.services.db import db as database_service
except ImportError:
    database_service = None


class TrainerThread(QThread):
    """Background thread for model training."""
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.trainer = Trainer()
    
    def run(self):
        try:
            self.progress.emit(10, "Loading training data...")
            features, labels = DataCollector.load_all_data()
            if features is None or len(features) == 0:
                self.error.emit("No training data found.")
                return
            self.progress.emit(30, f"Training on {len(labels)} samples...")
            accuracy = self.trainer.train(features, labels)
            self.progress.emit(70, "Saving model...")
            self.trainer.save()
            self.progress.emit(100, "Done")
            self.finished.emit(self.trainer.get_training_summary())
        except Exception as e:
            self.error.emit(str(e))


class NavButton(QPushButton):
    """Navigation sidebar button."""
    
    def __init__(self, icon, text, parent=None):
        super().__init__(f"{icon}  {text}", parent)
        self.setObjectName("navButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)


class Sidebar(QFrame):
    """Navigation sidebar."""
    
    navigate = Signal(str)  # page name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self._current_button = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)
        
        # Logo/Brand
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(12)
        
        import os, sys
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(project_root, "assets", "emosign.png")
        logo = QLabel()
        logo.setStyleSheet("background: transparent;")
        from PySide6.QtGui import QPixmap
        pm = QPixmap(logo_path)
        if not pm.isNull():
            logo.setPixmap(pm.scaledToHeight(40, Qt.SmoothTransformation))
        else:
            logo.setText("EmoSign")
            logo.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;")
        
        brand_layout.addWidget(logo)
        brand_layout.addStretch()
        
        layout.addLayout(brand_layout)
        layout.addSpacing(32)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("dashboard", "🏠", "Dashboard"),
            ("live", "🔴", "Live Translation"),
            ("conversation", "💬", "Conversation"),
            ("history", "📜", "History"),
        ]
        
        for page_id, icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, p=page_id: self._on_nav_click(p))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)
        
        # Divider
        divider1 = QLabel("LEARN")
        divider1.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            background: transparent;
            padding-top: 16px;
            padding-bottom: 4px;
        """)
        layout.addWidget(divider1)
        
        learn_items = [
            ("tutorial", "📚", "Tutorials"),
            ("training", "🎯", "Train Gestures"),
            ("game", "🎮", "Sign Game"),
        ]
        
        for page_id, icon, text in learn_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, p=page_id: self._on_nav_click(p))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)
        
        # Divider
        divider2 = QLabel("ACCOUNT")
        divider2.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            background: transparent;
            padding-top: 16px;
            padding-bottom: 4px;
        """)
        layout.addWidget(divider2)
        
        account_items = [
            ("analytics", "📊", "Analytics"),
            ("profile", "👤", "Profile"),
            ("settings", "⚙️", "Settings"),
        ]
        
        for page_id, icon, text in account_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, p=page_id: self._on_nav_click(p))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)
            
        # Admin Button (Special case)
        self.admin_btn = NavButton("🛡️", "Admin Panel")
        self.admin_btn.clicked.connect(lambda: self._on_nav_click("admin"))
        self.admin_btn.hide() # Hidden by default
        self.nav_buttons["admin"] = self.admin_btn
        layout.addWidget(self.admin_btn)
        
        layout.addStretch()
        
        # Theme toggle button
        self.theme_btn = QPushButton("🌙 Dark")
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                color: {COLORS['text_secondary']};
                padding: 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_card']};
            }}
        """)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)
        
        layout.addSpacing(8)
        
        # Version info
        version_label = QLabel("v3.0.0")
        version_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 12px;
            background: transparent;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
    
    def _on_nav_click(self, page_id):
        self.navigate.emit(page_id)
    
    def _toggle_theme(self):
        """Toggle between dark and light theme."""
        new_theme = ThemeManager.toggle_theme()
        if new_theme == "light":
            self.theme_btn.setText("☀️ Light")
        else:
            self.theme_btn.setText("🌙 Dark")
        self.theme_changed.emit(new_theme)
    
    theme_changed = Signal(str)
    
    def set_active(self, page_id):
        """Set the active navigation button."""
        for btn_id, btn in self.nav_buttons.items():
            btn.setChecked(btn_id == page_id)
            
    def show_admin_link(self, show=True):
        if show:
            self.admin_btn.show()
        else:
            self.admin_btn.hide()


class MainWindow(QMainWindow):
    """Main application window with multi-page navigation."""
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.db = database_service
        self.classifier = Classifier()
        self.data_collector = DataCollector()
        self.trainer_thread = None
        
        # State
        self.user = None
        self.model_loaded = self.classifier.load()
        
        self._setup_ui()
        self._connect_signals()
        
        # Start with login page
        self._show_login()
    
    def _setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("EmoSign v2.0.0")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(DARK_THEME)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar (hidden initially)
        self.sidebar = Sidebar()
        self.sidebar.hide()
        self.main_layout.addWidget(self.sidebar)
        
        # Page container
        self.page_stack = QStackedWidget()
        self.main_layout.addWidget(self.page_stack)
        
        # Create pages
        self._create_pages()
        
        # Load saved settings
        self.settings_page.load_saved_settings()
        
        # Start analytics session if available
        if analytics and self.user:
            analytics.start_session(self.user.get('id', 'guest'))
    
    def _create_pages(self):
        """Create all application pages."""
        # Login page
        self.login_page = LoginPage(self.db)
        self.page_stack.addWidget(self.login_page)
        
        # Dashboard
        self.dashboard_page = DashboardPage(self.user, self.db)
        self.page_stack.addWidget(self.dashboard_page)
        
        # Live translation
        self.live_page = LiveTranslationPage(self.classifier, self.db, self.user)
        self.page_stack.addWidget(self.live_page)
        
        # Conversation mode
        self.conversation_page = ConversationPage()
        self.page_stack.addWidget(self.conversation_page)
        
        # History
        self.history_page = HistoryPage(self.db, self.user)
        self.page_stack.addWidget(self.history_page)
        
        # Tutorial page
        self.tutorial_page = TutorialPage()
        self.page_stack.addWidget(self.tutorial_page)
        
        # Training page for predefined gestures
        self.training_page = TrainingPage()
        self.page_stack.addWidget(self.training_page)
        
        # Game page
        self.game_page = GamePage(self.classifier)
        self.page_stack.addWidget(self.game_page)
        
        # Analytics page
        self.analytics_page = AnalyticsPage()
        self.page_stack.addWidget(self.analytics_page)
        
        # Profile
        self.profile_page = ProfilePage(self.user, self.db)
        self.page_stack.addWidget(self.profile_page)
        
        # Settings page
        self.settings_page = SettingsPage()
        self.page_stack.addWidget(self.settings_page)
        
        # Admin Page
        self.admin_page = AdminPage(self.db)
        self.page_stack.addWidget(self.admin_page)
    
    def _connect_signals(self):
        """Connect all signals."""
        # Login signals
        self.login_page.login_successful.connect(self._on_login)
        self.login_page.signup_successful.connect(self._on_login)
        
        # Sidebar navigation
        self.sidebar.navigate.connect(self._navigate_to)
        
        # Sidebar theme change
        self.sidebar.theme_changed.connect(self._apply_theme)
        
        # Dashboard navigation
        self.dashboard_page.navigate_to_live.connect(lambda: self._navigate_to("live"))
        self.dashboard_page.navigate_to_history.connect(lambda: self._navigate_to("history"))
        self.dashboard_page.navigate_to_profile.connect(lambda: self._navigate_to("profile"))
        self.dashboard_page.navigate_to_training.connect(lambda: self._navigate_to("training"))
        
        # Page back buttons
        self.live_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.history_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.profile_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.tutorial_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.training_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.game_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.analytics_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.settings_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.conversation_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        
        # Training page signals
        self.training_page.model_trained.connect(self._on_model_trained)
        
        # Live page translation events
        self.live_page.translation_made.connect(self._save_translation)
        self.live_page.translation_made.connect(self._on_translation_made)
        
        # Settings signals
        self.settings_page.theme_changed.connect(self._apply_theme)
        self.settings_page.accent_changed.connect(self._apply_accent)
        self.settings_page.voice_settings_changed.connect(self._apply_voice_settings)
        self.settings_page.accessibility_changed.connect(self._apply_accessibility)
        self.settings_page.detection_settings_changed.connect(self._apply_detection_settings)
        
        # Profile signals
        self.profile_page.logout_requested.connect(self._on_logout)
        self.profile_page.settings_section.navigate_to_settings.connect(lambda: self._navigate_to("settings"))
    
    def _apply_theme(self, theme: str):
        """Apply theme to the application."""
        ThemeManager.set_theme(theme)
        self.setStyleSheet(ThemeManager.get_theme())
        # Recreate pages so inline styles pick up new COLORS
        self._rebuild_pages()
    
    def _apply_accent(self, accent: str):
        """Apply accent color to the application."""
        ThemeManager.set_accent(accent)
        self.setStyleSheet(ThemeManager.get_theme())
        self._rebuild_pages()

    def _rebuild_pages(self):
        """Destroy and recreate all pages so inline styles use current COLORS."""
        # Remember current state
        saved_user = self.user
        current_page = self.page_stack.currentWidget()
        current_page_name = None
        # Map widget to page name
        page_map = {
            'dashboard_page': 'dashboard', 'live_page': 'live',
            'conversation_page': 'conversation', 'history_page': 'history',
            'tutorial_page': 'tutorial', 'training_page': 'training',
            'game_page': 'game', 'analytics_page': 'analytics',
            'profile_page': 'profile', 'settings_page': 'settings',
            'admin_page': 'admin', 'login_page': 'login',
        }
        for attr, name in page_map.items():
            if hasattr(self, attr) and getattr(self, attr) is current_page:
                current_page_name = name
                break

        # Cleanup active cameras/resources
        try:
            self.live_page.cleanup()
        except Exception:
            pass
        try:
            self.game_page.cleanup()
        except Exception:
            pass

        # Remove all pages from stack
        while self.page_stack.count() > 0:
            w = self.page_stack.widget(0)
            self.page_stack.removeWidget(w)
            w.deleteLater()

        # Rebuild sidebar
        old_sidebar = self.sidebar
        self.sidebar = Sidebar()
        self.main_layout.replaceWidget(old_sidebar, self.sidebar)
        old_sidebar.deleteLater()
        self.sidebar.navigate.connect(self._navigate_to)
        self.sidebar.theme_changed.connect(self._apply_theme)
        # Update theme button text
        if not ThemeManager.is_dark():
            self.sidebar.theme_btn.setText("☀️ Light")

        # Recreate pages
        self._create_pages()
        self.settings_page.load_saved_settings()
        self._connect_signals()

        # Restore user
        if saved_user:
            self.user = saved_user
            self.dashboard_page.update_user(saved_user)
            self.live_page.user = saved_user
            self.history_page.update_user(saved_user)
            self.profile_page.update_user(saved_user)
            self.analytics_page.update_user(saved_user.get('id', 'guest'))
            is_admin = saved_user.get("email") == "admin"
            self.sidebar.show_admin_link(is_admin)
            self.sidebar.show()

            # Navigate back to same page
            if current_page_name and current_page_name != 'login':
                self._navigate_to(current_page_name)
        else:
            self._show_login()
    
    def _apply_voice_settings(self, settings: dict):
        """Apply voice output settings."""
        if voice_output:
            voice_output.set_enabled(settings.get('enabled', True))
            voice_output.set_rate(settings.get('speed', 150))
            voice_output.set_volume(settings.get('volume', 0.8))
    
    def _apply_accessibility(self, settings: dict):
        """Apply accessibility settings."""
        # Get current font size base
        base_size = 14
        
        # Apply large text if enabled
        if settings.get('large_text', False):
            base_size = 18
        
        # Apply high contrast if enabled (modify colors)
        if settings.get('high_contrast', False):
            # Create high contrast stylesheet addition
            high_contrast_style = """
                QLabel { color: #ffffff !important; }
                QPushButton { color: #ffffff !important; border: 2px solid #ffffff !important; }
            """
            current_style = self.styleSheet()
            if "high_contrast_style" not in current_style:
                self.setStyleSheet(current_style + high_contrast_style)
        else:
            # Remove high contrast styles
            self.setStyleSheet(ThemeManager.get_theme())
        
        # Store settings for later use
        self._accessibility_settings = settings
    
    def _apply_detection_settings(self, settings: dict):
        """Apply detection settings to the pipeline."""
        # Update confidence threshold
        if hasattr(self.live_page, 'pipeline') and self.live_page.pipeline:
            pipeline = self.live_page.pipeline
            if hasattr(pipeline, 'config'):
                pipeline.config.min_confidence = settings.get('confidence_threshold', 0.55)
        
        # Store settings for use across the app
        self._detection_settings = settings
    
    def _on_translation_made(self, label, confidence, gesture_type):
        """Handle translation events for analytics and voice."""
        # Record in analytics
        if analytics and self.user:
            user_id = self.user.get('id', 'guest')
            analytics.record_sign(user_id, label, confidence)
            analytics.save_stats(user_id)
        
        # Speak the translation
        if voice_output and voice_output.config.enabled:
            voice_output.speak_word(label)
    
    def _show_login(self):
        """Show login page."""
        self.sidebar.hide()
        self.page_stack.setCurrentWidget(self.login_page)

    
    @Slot(dict)
    def _on_login(self, user_data):
        """Handle successful login."""
        self.user = user_data
        
        # Update all pages with user data
        self.dashboard_page.update_user(user_data)
        self.live_page.user = user_data
        self.history_page.update_user(user_data)
        self.profile_page.update_user(user_data)
        self.analytics_page.update_user(user_data.get('id', 'guest'))
        
        # Check if admin
        is_admin = user_data.get("email") == "admin"
        self.sidebar.show_admin_link(is_admin)
        
        # Show main app
        self.sidebar.show()
        if is_admin:
             self._navigate_to("admin")
        else:
             self._navigate_to("dashboard")
        
        # Start analytics session
        if analytics:
            analytics.start_session(user_data.get('id', 'guest'))
        
        # Clear login form
        self.login_page.clear_form()
    
    def _on_logout(self):
        """Handle logout."""
        # End analytics session
        if analytics and self.user:
            analytics.end_session(self.user.get('id', 'guest'))
        
        self.user = None
        
        # Stop any active camera
        self.live_page.stop_camera()
        
        # Clear user data from all pages
        self.live_page.user = None
        self.dashboard_page.update_user({})
        self.history_page.update_user({})
        self.profile_page.update_user({})
        
        # Hide admin link
        self.sidebar.show_admin_link(False)
        
        # Clear the login form for fresh state
        self.login_page.clear_form()
        
        # Show login
        self._show_login()
    
    def _navigate_to(self, page_id):
        """Navigate to a page."""
        self.sidebar.set_active(page_id)
        
        if page_id == "dashboard":
            self.dashboard_page.refresh_stats()
            self.page_stack.setCurrentWidget(self.dashboard_page)
        elif page_id == "live":
            self.page_stack.setCurrentWidget(self.live_page)
        elif page_id == "conversation":
            self.page_stack.setCurrentWidget(self.conversation_page)
        elif page_id == "history":
            self.history_page.refresh()
            self.page_stack.setCurrentWidget(self.history_page)
        elif page_id == "tutorial":
            self.page_stack.setCurrentWidget(self.tutorial_page)
        elif page_id == "training":
            self.page_stack.setCurrentWidget(self.training_page)
        elif page_id == "game":
            self.page_stack.setCurrentWidget(self.game_page)
        elif page_id == "analytics":
            if self.user:
                self.analytics_page.update_user(self.user.get('id', 'guest'))
            self.analytics_page.refresh()
            self.page_stack.setCurrentWidget(self.analytics_page)
        elif page_id == "profile":
            self.profile_page.refresh()
            self.page_stack.setCurrentWidget(self.profile_page)
        elif page_id == "settings":
            self.page_stack.setCurrentWidget(self.settings_page)
        elif page_id == "admin":
            self.admin_page.refresh_all()
            self.page_stack.setCurrentWidget(self.admin_page)
    
    @Slot(str, float, str)
    def _save_translation(self, label, confidence, gesture_type):
        """Save translation to database."""
        if not self.db or not self.user or self.user.get("guest"):
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self.db.save_translation(
                    self.user.get("id", ""),
                    label,
                    confidence,
                    gesture_type
                )
            )
            loop.close()
        except Exception as e:
            print(f"Failed to save translation: {e}")
    
    def _start_training(self):
        """Start model training."""
        if self.trainer_thread and self.trainer_thread.isRunning():
            QMessageBox.warning(self, "Training", "Training is already in progress.")
            return
        
        reply = QMessageBox.question(
            self, "Train Model",
            "Start training a new model with collected data?\n\nThis may take a few minutes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.trainer_thread = TrainerThread()
        self.trainer_thread.progress.connect(self._on_training_progress)
        self.trainer_thread.finished.connect(self._on_training_done)
        self.trainer_thread.error.connect(self._on_training_error)
        self.trainer_thread.start()
    
    @Slot(int, str)
    def _on_training_progress(self, percent, message):
        """Handle training progress updates."""
        # Could show a progress dialog here
        print(f"Training: {percent}% - {message}")
    
    @Slot(dict)
    def _on_training_done(self, summary):
        """Handle training completion."""
        self.model_loaded = self.classifier.load()
        QMessageBox.information(
            self, "Training Complete",
            f"Model trained successfully!\n\nAccuracy: {summary['accuracy']:.1%}"
        )
    
    @Slot(float)
    def _on_model_trained(self, accuracy: float):
        """Handle model trained from training page."""
        # Reload classifier to pick up new model
        self.model_loaded = self.classifier.load()
        print(f"Model updated after training. Accuracy: {accuracy:.1%}")
    
    @Slot(str)
    def _on_training_error(self, error):
        """Handle training error."""
        QMessageBox.critical(self, "Training Error", f"Training failed:\n{error}")
    
    def closeEvent(self, event):
        """Handle window close."""
        # Stop camera
        self.live_page.cleanup()
        self.game_page.cleanup()
        
        # Stop training thread
        if self.trainer_thread and self.trainer_thread.isRunning():
            self.trainer_thread.quit()
            self.trainer_thread.wait()
        
        event.accept()
