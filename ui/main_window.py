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
from ui.pages.admin_page import AdminPage

# New feature pages
from ui.pages.tutorial_page import TutorialPage
from ui.pages.settings_page import SettingsPage
from ui.pages.analytics_page import AnalyticsPage
from ui.pages.conversation_page import ConversationPage
from ui.pages.training_page import TrainingPage
from ui.pages.game_page import GamePage
from ui.pages.study_mode_page import StudyModePage
from ui.pages.quiz_mode_page import QuizModePage
from ui.pages.features_page import FeaturesPage

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
        self.setMinimumHeight(40)


class Sidebar(QFrame):
    """Navigation sidebar."""
    
    navigate = Signal(str)  # page name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._current_button = None
        self._admin_mode = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)
        
        # Logo/Brand
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)
        brand_layout.setContentsMargins(8, 0, 8, 0)
        
        import os, sys
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(project_root, "assets", "emosign.png")
        logo = QLabel()
        logo.setStyleSheet("background: transparent;")
        from PySide6.QtGui import QPixmap
        pm = QPixmap(logo_path)
        if not pm.isNull():
            logo.setPixmap(pm.scaledToHeight(36, Qt.SmoothTransformation))
        else:
            logo.setText("EmoSign")
            logo.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;")
        
        brand_layout.addWidget(logo)
        brand_layout.addStretch()
        
        layout.addLayout(brand_layout)

        self.mode_badge = QLabel("ADMIN VIEW")
        self.mode_badge.setAlignment(Qt.AlignCenter)
        self.mode_badge.hide()
        self.mode_badge.setStyleSheet("""
            color: #fef2f2;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.4px;
            background: #991b1b;
            border-radius: 8px;
            padding: 4px 8px;
            margin: 2px 8px;
        """)
        layout.addWidget(self.mode_badge)

        layout.addSpacing(24)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("dashboard", "🏠", "Learning Hub"),
            ("live", "🔴", "Practice Lab"),
            ("conversation", "💬", "Conversation Drill"),
            ("history", "📜", "Practice History"),
        ]
        
        for page_id, icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, p=page_id: self._on_nav_click(p))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)
        
        # Divider
        layout.addSpacing(8)
        self.divider1 = QLabel("LEARN")
        self.divider1.setObjectName("sidebarDivider")
        self.divider1.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
            background: transparent;
            padding: 8px 8px 4px 8px;
        """)
        layout.addWidget(self.divider1)
        
        learn_items = [
            ("tutorial", "📚", "Tutorials"),
            ("study", "🧾", "Self Study"),
            ("quiz", "❓", "Quiz Mode"),
            ("game", "🎮", "Sign Game"),
        ]
        
        for page_id, icon, text in learn_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, p=page_id: self._on_nav_click(p))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)

        # Admin section
        self.admin_divider = QLabel("ADMIN")
        self.admin_divider.setObjectName("sidebarDivider")
        self.admin_divider.hide()
        self.admin_divider.setStyleSheet(f"""
            color: #ef4444;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.4px;
            background: transparent;
            padding: 8px 8px 4px 8px;
        """)
        layout.addWidget(self.admin_divider)

        # Admin-only training button
        self.training_btn = NavButton("🎯", "Train Gestures")
        self.training_btn.clicked.connect(lambda: self._on_nav_click("training"))
        self.training_btn.hide()
        self.nav_buttons["training"] = self.training_btn
        layout.addWidget(self.training_btn)
        
        # Divider
        layout.addSpacing(8)
        self.divider2 = QLabel("ACCOUNT")
        self.divider2.setObjectName("sidebarDivider")
        self.divider2.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
            background: transparent;
            padding: 8px 8px 4px 8px;
        """)
        layout.addWidget(self.divider2)
        
        account_items = [
            ("analytics", "📊", "Analytics"),
            ("settings", "⚙️", "Settings"),
            ("features", "✨", "Features"),
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
        
        layout.addSpacing(6)
        
        app_label = QLabel("EmoSign")
        app_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            background: transparent;
        """)
        app_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_label)
    
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
        self.set_admin_mode(show)

    def show_training_link(self, show=True):
        if self._admin_mode:
            self.training_btn.setVisible(show)
        else:
            self.training_btn.hide()

    def set_admin_mode(self, enabled=True):
        """Toggle between regular-user navigation and admin-exclusive navigation."""
        self._admin_mode = bool(enabled)
        regular_pages = [
            "dashboard", "live", "conversation", "history",
            "tutorial", "study", "quiz", "game",
            "analytics", "settings", "features"
        ]

        for page_id in regular_pages:
            btn = self.nav_buttons.get(page_id)
            if btn:
                btn.setVisible(not self._admin_mode)

        self.divider1.setVisible(not self._admin_mode)
        self.divider2.setVisible(not self._admin_mode)
        self.mode_badge.setVisible(self._admin_mode)

        self.admin_divider.setVisible(self._admin_mode)
        self.training_btn.setVisible(self._admin_mode)
        self.admin_btn.setVisible(self._admin_mode)


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

    def _is_admin_user(self, user_data=None) -> bool:
        """Return True if the provided/current user has admin access."""
        user = user_data if user_data is not None else self.user
        if not user:
            return False
        if user.get("is_admin") is True:
            return True
        if str(user.get("role", "")).lower() == "admin":
            return True
        identity = str(user.get("username") or user.get("email") or "").strip().lower()
        return identity == "admin"
    
    def _setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("EmoSign")
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

        # Camera-free study mode
        self.study_page = StudyModePage()
        self.page_stack.addWidget(self.study_page)

        # Camera-free quiz mode
        self.quiz_page = QuizModePage()
        if self.user:
            self.quiz_page.update_user(self.user.get('id', 'guest'))
        self.page_stack.addWidget(self.quiz_page)
        
        # Training page for predefined gestures
        self.training_page = TrainingPage()
        self.training_page.set_admin_access(self._is_admin_user())
        self.page_stack.addWidget(self.training_page)
        
        # Game page
        self.game_page = GamePage(self.classifier)
        self.page_stack.addWidget(self.game_page)
        
        # Analytics page
        self.analytics_page = AnalyticsPage()
        self.page_stack.addWidget(self.analytics_page)
        
        # Settings page
        self.settings_page = SettingsPage(self.user, self.db)
        self.page_stack.addWidget(self.settings_page)

        # Features page
        self.features_page = FeaturesPage()
        self.page_stack.addWidget(self.features_page)
        
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
        
        # Dashboard navigation
        self.dashboard_page.navigate_to_live.connect(lambda: self._navigate_to("live"))
        self.dashboard_page.navigate_to_history.connect(lambda: self._navigate_to("history"))
        self.dashboard_page.navigate_to_profile.connect(lambda: self._navigate_to("settings"))
        self.dashboard_page.navigate_to_training.connect(lambda: self._navigate_to("training"))
        self.dashboard_page.navigate_to_tutorial.connect(lambda: self._navigate_to("tutorial"))
        self.dashboard_page.navigate_to_study.connect(lambda: self._navigate_to("study"))
        self.dashboard_page.navigate_to_quiz.connect(lambda: self._navigate_to("quiz"))
        self.dashboard_page.navigate_to_game.connect(lambda: self._navigate_to("game"))
        self.dashboard_page.navigate_to_analytics.connect(lambda: self._navigate_to("analytics"))
        
        # Page back buttons - REMOVED (Sidebar is the primary navigation)
        # self.live_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        # self.history_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        # self.tutorial_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        # self.training_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        # self.game_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        # self.analytics_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        # self.settings_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        # self.conversation_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        
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
        self.settings_page.logout_requested.connect(self._on_logout)
    
    def _apply_theme(self, theme: str):
        """Apply theme — deferred rebuild for responsive button animation."""
        ThemeManager.set_theme(theme)
        self.setStyleSheet(ThemeManager.get_theme())
        # Defer the full page rebuild so the button press animates first
        # 50ms delay prevents race condition with camera timer callbacks
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, self._rebuild_pages)
    
    def _apply_accent(self, accent: str):
        """Apply accent color to the application."""
        ThemeManager.set_accent(accent)
        self.setStyleSheet(ThemeManager.get_theme())
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._rebuild_pages)

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
            'tutorial_page': 'tutorial', 'study_page': 'study',
            'quiz_page': 'quiz', 'training_page': 'training',
            'game_page': 'game', 'analytics_page': 'analytics',
            'settings_page': 'settings', 'features_page': 'features',
            'admin_page': 'admin', 'login_page': 'login',
        }
        for attr, name in page_map.items():
            if hasattr(self, attr) and getattr(self, attr) is current_page:
                current_page_name = name
                break

        # Safely stop cameras BEFORE destroying pages (prevents crash)
        # Use stop() not cleanup()/release() to avoid destroying MediaPipe
        # resources while timer callbacks may still be pending
        for page_attr in ['live_page', 'game_page', 'training_page']:
            try:
                page = getattr(self, page_attr, None)
                if page and hasattr(page, 'camera_widget'):
                    page.camera_widget.stop()
                if page and hasattr(page, 'video_widget'):
                    page.video_widget.release()
            except Exception:
                pass
        # Stop tutorial camera if running
        try:
            if hasattr(self, 'tutorial_page') and hasattr(self.tutorial_page, 'alphabet_lesson'):
                lesson = self.tutorial_page.alphabet_lesson
                if hasattr(lesson, '_camera_widget') and lesson._camera_widget:
                    lesson._stop_camera()
        except Exception:
            pass
        # Stop timers on live pages
        try:
            if hasattr(self.live_page, '_auto_translate_timer'):
                self.live_page._auto_translate_timer.stop()
            if hasattr(self.live_page, '_check_timer'):
                self.live_page._check_timer.stop()
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
            self.settings_page.update_user(saved_user)
            self.analytics_page.update_user(saved_user.get('id', 'guest'))
            self.quiz_page.update_user(saved_user.get('id', 'guest'))
            is_admin = self._is_admin_user(saved_user)
            self.sidebar.set_admin_mode(is_admin)
            self.training_page.set_admin_access(is_admin)
            self.sidebar.show()

            # Navigate back to same page
            if current_page_name and current_page_name != 'login':
                if is_admin and current_page_name not in {'admin', 'training'}:
                    self._navigate_to('admin')
                else:
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
        self.settings_page.update_user(user_data)
        self.analytics_page.update_user(user_data.get('id', 'guest'))
        self.quiz_page.update_user(user_data.get('id', 'guest'))
        
        # Check if admin
        is_admin = self._is_admin_user(user_data)
        self.sidebar.set_admin_mode(is_admin)
        self.training_page.set_admin_access(is_admin)
        
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
        self.settings_page.update_user({})
        self.quiz_page.update_user('guest')
        
        # Hide admin link
        self.sidebar.set_admin_mode(False)
        self.training_page.set_admin_access(False)
        
        # Clear the login form for fresh state
        self.login_page.clear_form()
        
        # Show login
        self._show_login()
    
    def _navigate_to(self, page_id):
        """Navigate to a page."""
        if page_id == "profile":
            page_id = "settings"

        if self._is_admin_user() and page_id not in {"admin", "training"}:
            page_id = "admin"

        # Route guards
        if page_id in {"admin", "training"} and not self._is_admin_user():
            self.sidebar.set_active("dashboard")
            self.page_stack.setCurrentWidget(self.dashboard_page)
            QMessageBox.warning(self, "Access Denied", "This page is available to admin users only.")
            return

        self.sidebar.set_active(page_id)
        
        # Stop cameras on pages we're leaving to save resources
        self._stop_active_cameras(page_id)
        
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
        elif page_id == "study":
            self.page_stack.setCurrentWidget(self.study_page)
        elif page_id == "quiz":
            self.page_stack.setCurrentWidget(self.quiz_page)
        elif page_id == "training":
            self.page_stack.setCurrentWidget(self.training_page)
        elif page_id == "game":
            self.page_stack.setCurrentWidget(self.game_page)
        elif page_id == "analytics":
            if self.user:
                self.analytics_page.update_user(self.user.get('id', 'guest'))
            self.analytics_page.refresh()
            self.page_stack.setCurrentWidget(self.analytics_page)
        elif page_id == "settings":
            if self.user:
                self.settings_page.update_user(self.user)
            self.settings_page.refresh()
            self.page_stack.setCurrentWidget(self.settings_page)
        elif page_id == "features":
            self.page_stack.setCurrentWidget(self.features_page)
        elif page_id == "admin":
            self.admin_page.refresh_all()
            self.page_stack.setCurrentWidget(self.admin_page)

    def _stop_active_cameras(self, target_page_id: str):
        """Stop cameras on all pages except the target to free resources."""
        # Stop live page camera
        if target_page_id != "live":
            try:
                if hasattr(self, 'live_page'):
                    self.live_page.stop_camera()
            except Exception:
                pass
        # Stop game page camera
        if target_page_id != "game":
            try:
                if hasattr(self, 'game_page') and hasattr(self.game_page, 'camera_widget'):
                    self.game_page.camera_widget.stop()
            except Exception:
                pass
        # Stop tutorial page camera (AlphabetLesson has a _camera_widget)
        if target_page_id != "tutorial":
            try:
                if hasattr(self, 'tutorial_page') and hasattr(self.tutorial_page, 'alphabet_lesson'):
                    lesson = self.tutorial_page.alphabet_lesson
                    if hasattr(lesson, '_camera_widget') and lesson._camera_widget:
                        lesson._stop_camera()
            except Exception:
                pass
        # Stop training page camera
        if target_page_id != "training":
            try:
                if hasattr(self, 'training_page') and hasattr(self.training_page, 'camera_widget'):
                    self.training_page.camera_widget.stop()
            except Exception:
                pass
    
    @Slot(str, float, str)
    def _save_translation(self, label, confidence, gesture_type):
        """Save translation to database (non-blocking)."""
        if not self.db or not self.user or self.user.get("guest"):
            return
        
        # Run the async save on a background thread to avoid blocking the UI
        from threading import Thread
        def _bg_save():
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
            except (RuntimeError, Exception):
                pass  # Ignore errors from shutdown or DB issues
        
        Thread(target=_bg_save, daemon=True).start()
    
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
