"""
Settings Page - Application Appearance Settings

Provides settings for:
- Appearance (Theme, Accent Color)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import os
from datetime import datetime

from ui.styles import COLORS, ACCENT_PRESETS, ThemeManager
from ui.page_header import make_page_header

try:
    from ui.pages.profile_page import (
        ChangePasswordDialog,
        HelpSupportDialog,
    )
except Exception:
    ChangePasswordDialog = None
    HelpSupportDialog = None

try:
    from core.export_manager import ExportManager, ExportFormat, TranslationRecord
    EXPORT_AVAILABLE = True
except Exception:
    EXPORT_AVAILABLE = False


class ColorButton(QPushButton):
    """A circular button for selecting accent colors."""
    
    color_selected = Signal(str)
    
    def __init__(self, color_key: str, color_hex: str, parent=None):
        super().__init__(parent)
        self.color_key = color_key
        self.color_hex = color_hex
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self._update_style()
        self.clicked.connect(self._on_clicked)
    
    def _update_style(self):
        checked_border = "#ffffff" if ThemeManager.is_dark() else "#0f172a"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_hex};
                border: 3px solid transparent;
                border-radius: 20px;
            }}
            QPushButton:hover {{
                border-color: rgba(255, 255, 255, 0.5);
            }}
            QPushButton:checked {{
                border-color: {checked_border};
            }}
        """)
    
    def _on_clicked(self):
        self.color_selected.emit(self.color_key)


class SettingCard(QFrame):
    """A card containing related settings."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 24, 28, 24)
        self.main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 22px;")
            header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title_label)
        header.addStretch()
        
        self.main_layout.addLayout(header)
        
        # Content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(16)
        self.main_layout.addLayout(self.content_layout)
    
    def add_row(self, label: str, widget, description: str = ""):
        """Add a setting row with label and control widget."""
        row = QHBoxLayout()
        row.setSpacing(16)
        
        # Left side - labels
        left = QVBoxLayout()
        left.setSpacing(2)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']}; font-size: 14px;")
        left.addWidget(label_widget)
        
        if description:
            desc_widget = QLabel(description)
            desc_widget.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
            desc_widget.setWordWrap(True)
            left.addWidget(desc_widget)
        
        row.addLayout(left, 1)
        
        # Right side - control
        if isinstance(widget, QWidget):
            widget.setMinimumWidth(180)
            row.addWidget(widget)
        
        self.content_layout.addLayout(row)
    
    def add_widget(self, widget):
        """Add a custom widget to the content area."""
        self.content_layout.addWidget(widget)


class SettingsPage(QWidget):
    """Application settings page — account + appearance."""
    
    back_requested = Signal()
    theme_changed = Signal(str)
    accent_changed = Signal(str)
    voice_settings_changed = Signal(dict)
    language_changed = Signal(str)
    accessibility_changed = Signal(dict)
    detection_settings_changed = Signal(dict)
    logout_requested = Signal()
    
    def __init__(self, user_data=None, db_service=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.db = db_service
        self.color_buttons = []
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(28)
        
        # ========== HEADER ==========
        header, _ = make_page_header("⚙️ Settings")
        layout.addLayout(header)
        
        # ========== SCROLLABLE CONTENT ==========
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(28)
        content_layout.setContentsMargins(0, 0, 16, 0)
        
        # ========== ACCOUNT CARD ==========
        account_card = SettingCard("Account", "👤")

        self.user_name_label = QLabel("User")
        self.user_name_label.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {COLORS['text_primary']};"
        )
        account_card.add_widget(self.user_name_label)

        self.user_email_label = QLabel("-")
        self.user_email_label.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_secondary']};"
        )
        account_card.add_widget(self.user_email_label)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        for label, handler in [
            ("Change Password", self._change_password),
            ("Export Data", self._export_data),
            ("Help", self._show_help),
        ]:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_card_hover']};
                }}
            """)
            action_row.addWidget(btn)

        signout_btn = QPushButton("Sign Out")
        signout_btn.setCursor(Qt.PointingHandCursor)
        signout_btn.clicked.connect(self._handle_logout)
        signout_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']};
                color: {COLORS['danger']};
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']}20;
            }}
        """)
        action_row.addWidget(signout_btn)
        action_row.addStretch()
        account_card.content_layout.addLayout(action_row)

        content_layout.addWidget(account_card)

        # ========== APPEARANCE CARD ==========
        appearance_card = SettingCard("Appearance", "🎨")
        
        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Mode", "Light Mode"])
        self.theme_combo.setCurrentText("Dark Mode" if ThemeManager.is_dark() else "Light Mode")
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        appearance_card.add_row("Theme", self.theme_combo, "Switch between dark and light mode")
        
        # Accent color picker
        color_label = QLabel("Accent Color")
        color_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']}; font-size: 14px;")
        appearance_card.content_layout.addWidget(color_label)
        
        color_desc = QLabel("Choose your preferred accent color")
        color_desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        appearance_card.content_layout.addWidget(color_desc)
        
        color_grid = QHBoxLayout()
        color_grid.setSpacing(12)
        
        for key, preset in ACCENT_PRESETS.items():
            btn = ColorButton(key, preset['primary'])
            btn.setToolTip(preset['name'])
            btn.color_selected.connect(self._on_accent_changed)
            if key == ThemeManager.get_accent():
                btn.setChecked(True)
            self.color_buttons.append(btn)
            color_grid.addWidget(btn)
        
        color_grid.addStretch()
        appearance_card.content_layout.addLayout(color_grid)
        
        content_layout.addWidget(appearance_card)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.update_user(self.user)
    
    def _load_settings(self):
        """Load current settings."""
        current_accent = ThemeManager.get_accent()
        for btn in self.color_buttons:
            btn.setChecked(btn.color_key == current_accent)
    
    def _save_settings(self):
        """Save all settings and emit signals."""
        import json
        import os
        
        settings = {
            'theme': 'dark' if 'Dark' in self.theme_combo.currentText() else 'light',
            'accent': ThemeManager.get_accent(),
        }
        
        # Save to config file
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_settings.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")
    
    def _on_theme_changed(self, theme_text: str):
        """Handle theme change."""
        theme = "dark" if "Dark" in theme_text else "light"
        ThemeManager.set_theme(theme)
        self.theme_changed.emit(theme)
        for btn in self.color_buttons:
            btn._update_style()
        self._save_settings()
    
    def _on_accent_changed(self, accent_key: str):
        """Handle accent color change."""
        for btn in self.color_buttons:
            btn.setChecked(btn.color_key == accent_key)
        ThemeManager.set_accent(accent_key)
        self.accent_changed.emit(accent_key)
        self._save_settings()
    
    def refresh_theme(self):
        """Refresh the page with current theme colors."""
        pass
    
    def load_saved_settings(self):
        """Load previously saved settings from file."""
        import json
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_settings.json")
        
        if not os.path.exists(config_path):
            return
        
        try:
            with open(config_path, 'r') as f:
                settings = json.load(f)
            
            # Apply loaded settings
            if settings.get('theme') == 'light':
                self.theme_combo.setCurrentText("Light Mode")
            
            if settings.get('accent') and settings['accent'] in ACCENT_PRESETS:
                self._on_accent_changed(settings['accent'])
            
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def update_user(self, user_data):
        self.user = user_data or {}
        email = self.user.get("email", "")
        raw_name = (
            self.user.get("username")
            or self.user.get("display_name")
            or self.user.get("name")
            or (email.split("@")[0] if "@" in email else "User")
        )
        name = raw_name.capitalize() if isinstance(raw_name, str) and raw_name.islower() else str(raw_name)
        self.user_name_label.setText(name or "User")
        self.user_email_label.setText(email or "Guest / Offline")

    def refresh(self):
        self.update_user(self.user)

    def _handle_logout(self):
        reply = QMessageBox.question(
            self,
            "Sign Out",
            "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()

    def _change_password(self):
        if self.user.get("guest") or self.user.get("offline"):
            QMessageBox.information(self, "Not Available", "Password change is not available in guest/offline mode.")
            return
        if not ChangePasswordDialog:
            QMessageBox.warning(self, "Not Available", "Password dialog is unavailable.")
            return
        dialog = ChangePasswordDialog(self.db, self.user.get("id", ""), self)
        dialog.exec()

    def _show_help(self):
        if not HelpSupportDialog:
            QMessageBox.warning(self, "Not Available", "Help dialog is unavailable.")
            return
        dialog = HelpSupportDialog(self)
        dialog.exec()

    def _export_data(self):
        if not EXPORT_AVAILABLE:
            QMessageBox.warning(self, "Export Error", "Export functionality is not available.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Translation Data",
            os.path.expanduser("~/Documents/emosign_export.json"),
            "JSON Files (*.json);;CSV Files (*.csv);;Text Files (*.txt)",
        )
        if not file_path:
            return

        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".csv":
                fmt = ExportFormat.CSV
            elif ext == ".txt":
                fmt = ExportFormat.TXT
            else:
                fmt = ExportFormat.JSON

            exporter = ExportManager(os.path.dirname(file_path))
            translations = []
            if self.db and self.user.get("id"):
                try:
                    history = self.db.get_translation_history_sync(self.user.get("id"), 1000)
                    for item in history:
                        translations.append(
                            TranslationRecord(
                                text=item.get("sign_label", ""),
                                timestamp=datetime.fromisoformat(
                                    item.get("created_at", datetime.now().isoformat()).replace("Z", "")
                                ),
                                confidence=item.get("confidence", 0),
                                gesture_type=item.get("gesture_type", "static"),
                            )
                        )
                except Exception as e:
                    print(f"Failed to load translation history for export: {e}")

            if translations:
                result_path = exporter.export_translations(translations, fmt, os.path.basename(file_path))
                QMessageBox.information(self, "Export Complete", f"Data exported successfully!\n\nFile: {result_path}")
            else:
                QMessageBox.information(self, "No Data", "No translation data to export.")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export data: {e}")

