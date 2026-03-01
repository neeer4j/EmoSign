"""
Profile Page - User settings and account management
Premium profile view with stats and settings
"""
import os
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QMessageBox,
    QGraphicsDropShadowEffect, QDialog, QLineEdit,
    QFormLayout, QFileDialog, QTextEdit, QScrollArea,
    QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS
from ui.page_header import make_page_header

# Import export manager
try:
    from core.export_manager import ExportManager, ExportFormat, ExportConfig, TranslationRecord
    EXPORT_AVAILABLE = True
except ImportError:
    EXPORT_AVAILABLE = False


class ChangePasswordDialog(QDialog):
    """Dialog for changing password."""
    
    def __init__(self, db_service, user_id, parent=None):
        super().__init__(parent)
        self.db = db_service
        self.user_id = user_id
        self.setWindowTitle("Change Password")
        self.setFixedSize(400, 300)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_app']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton#cancel {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_secondary']};
            }}
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("🔑 Change Password")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setPlaceholderText("Enter current password")
        form.addRow("Current:", self.current_password)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("Enter new password (min 6 chars)")
        form.addRow("New:", self.new_password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("Confirm new password")
        form.addRow("Confirm:", self.confirm_password)
        
        layout.addLayout(form)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        buttons = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Update Password")
        save_btn.clicked.connect(self._save_password)
        
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)
    
    def _save_password(self):
        current = self.current_password.text()
        new_pass = self.new_password.text()
        confirm = self.confirm_password.text()
        
        if not current or not new_pass or not confirm:
            self.error_label.setText("All fields are required")
            return
        
        if len(new_pass) < 6:
            self.error_label.setText("Password must be at least 6 characters")
            return
        
        if new_pass != confirm:
            self.error_label.setText("Passwords do not match")
            return
        
        if self.db:
            try:
                result = self.db.change_password(self.user_id, current, new_pass)
                if result.get("success"):
                    QMessageBox.information(self, "Success", "Password updated successfully!")
                    self.accept()
                else:
                    self.error_label.setText(result.get("error", "Failed to update password"))
            except Exception as e:
                self.error_label.setText(f"Error: {str(e)}")
        else:
            self.error_label.setText("Database not available")


class NotificationSettingsDialog(QDialog):
    """Dialog for notification settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notification Settings")
        self.setFixedSize(400, 350)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_app']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QCheckBox {{
                color: {COLORS['text_primary']};
                font-size: 14px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {COLORS['border']};
                background: {COLORS['bg_input']};
            }}
            QCheckBox::indicator:checked {{
                background: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("🔔 Notification Settings")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        desc = QLabel("Choose which notifications you'd like to receive:")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(desc)
        
        layout.addSpacing(8)
        
        self.practice_reminder = QCheckBox("Daily practice reminders")
        self.practice_reminder.setChecked(True)
        layout.addWidget(self.practice_reminder)
        
        self.achievement_notify = QCheckBox("Achievement unlocked notifications")
        self.achievement_notify.setChecked(True)
        layout.addWidget(self.achievement_notify)
        
        self.streak_notify = QCheckBox("Streak milestone alerts")
        self.streak_notify.setChecked(True)
        layout.addWidget(self.streak_notify)
        
        self.tip_notify = QCheckBox("Tips and learning suggestions")
        self.tip_notify.setChecked(False)
        layout.addWidget(self.tip_notify)
        
        self.sound_enabled = QCheckBox("Enable notification sounds")
        self.sound_enabled.setChecked(True)
        layout.addWidget(self.sound_enabled)
        
        layout.addStretch()
        
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
            }}
        """)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)
    
    def _save_settings(self):
        settings = {
            "practice_reminder": self.practice_reminder.isChecked(),
            "achievement_notify": self.achievement_notify.isChecked(),
            "streak_notify": self.streak_notify.isChecked(),
            "tip_notify": self.tip_notify.isChecked(),
            "sound_enabled": self.sound_enabled.isChecked()
        }
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(config_dir, "notification_settings.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(self, "Saved", "Notification settings saved!")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save settings: {e}")


class HelpSupportDialog(QDialog):
    """Help and support dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help & Support")
        self.setFixedSize(500, 500)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_app']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QTextEdit {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                color: {COLORS['text_primary']};
                padding: 12px;
            }}
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("❓ Help & Support")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        help_content = QTextEdit()
        help_content.setReadOnly(True)
        help_content.setHtml(f"""
        <style>
            h3 {{ color: {COLORS['primary']}; margin-top: 16px; }}
            p {{ color: {COLORS['text_secondary']}; line-height: 1.6; }}
            ul {{ color: {COLORS['text_secondary']}; }}
        </style>
        <h3>🚀 Getting Started</h3>
        <p>Welcome to EmoSign! Here's how to get started:</p>
        <ul>
            <li>Go to <b>Live Translation</b> to start detecting signs</li>
            <li>Position your hand clearly in front of the camera</li>
            <li>Use good lighting for best results</li>
        </ul>
        
        <h3>📚 Learning ASL</h3>
        <p>Use the <b>Tutorials</b> page to learn ASL alphabet and common signs.</p>
        
        <h3>⚙️ Settings</h3>
        <p>Customize your experience in Settings:</p>
        <ul>
            <li><b>Theme:</b> Switch between dark and light mode</li>
            <li><b>Voice:</b> Enable text-to-speech for translations</li>
            <li><b>Detection:</b> Adjust confidence thresholds</li>
        </ul>
        
        <h3>🎯 Tips for Better Recognition</h3>
        <ul>
            <li>Use a plain background</li>
            <li>Ensure good, even lighting</li>
            <li>Keep your hand steady</li>
            <li>Face your palm towards the camera</li>
        </ul>
        
        <h3>📧 Contact Support</h3>
        <p>For additional help, please contact:<br>
        <b>Email:</b> support@emosign.app<br>
        <b>GitHub:</b> github.com/emosign/app</p>
        """)
        layout.addWidget(help_content)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
            }}
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class ProfilePage(QWidget):
    """User profile and settings page — premium design."""
    
    back_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, user_data=None, db_service=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.db = db_service
        self._stats = {}
        self._setup_ui()
        self._load_stats()
    
    def _setup_ui(self):
        """Build the profile page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(0)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent; border: none;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(20)
        
        # ── HERO CARD ─────────────────────────────────────────────
        hero = QFrame()
        hero.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary']}18, stop:1 {COLORS['accent']}10);
                border: none;
                border-radius: 16px;
            }}
        """)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(32, 28, 32, 28)
        hero_layout.setSpacing(24)
        
        # Avatar
        email = self.user.get("email", "")
        raw_name = (
            self.user.get("username")
            or self.user.get("display_name")
            or self.user.get("name")
            or (email.split("@")[0] if "@" in email else email)
            or "User"
        )
        username = raw_name.capitalize() if raw_name.islower() else raw_name
        initials = username[0].upper() if username else "U"
        
        avatar = QFrame()
        avatar.setFixedSize(80, 80)
        avatar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                border-radius: 40px;
            }}
        """)
        avatar_layout = QVBoxLayout(avatar)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        initial_label = QLabel(initials)
        initial_label.setStyleSheet("font-size: 32px; font-weight: 700; color: white; background: transparent;")
        initial_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(initial_label)
        hero_layout.addWidget(avatar)
        
        # User info column
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        
        name_label = QLabel(username)
        name_label.setStyleSheet(f"""
            font-size: 22px; font-weight: 700;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        info_col.addWidget(name_label)
        
        # Status badge
        if self.user.get("guest"):
            status_text, status_color = "Guest Account", COLORS['warning']
        elif self.user.get("offline"):
            status_text, status_color = "Offline Mode", COLORS['text_muted']
        else:
            status_text, status_color = "✓ Verified Account", COLORS['success']
        
        status = QLabel(status_text)
        status.setStyleSheet(f"""
            font-size: 12px; font-weight: 600;
            color: {status_color};
            background: transparent;
        """)
        info_col.addWidget(status)
        info_col.addStretch()
        hero_layout.addLayout(info_col, 1)
        
        # Sign out button in hero
        signout_btn = QPushButton("Sign Out")
        signout_btn.setCursor(Qt.PointingHandCursor)
        signout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']}50;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']}15;
                border-color: {COLORS['danger']};
            }}
        """)
        signout_btn.clicked.connect(self._handle_logout)
        hero_layout.addWidget(signout_btn, alignment=Qt.AlignVCenter)
        
        content_layout.addWidget(hero)
        
        # ── STATS ROW ─────────────────────────────────────────────
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 14px;
            }}
        """)
        stats_grid = QHBoxLayout(stats_frame)
        stats_grid.setContentsMargins(8, 8, 8, 8)
        stats_grid.setSpacing(0)
        
        stats_data = [
            ("📝", "0", "Total Translations", COLORS['primary']),
            ("✨", "0", "Unique Signs", COLORS['success']),
            ("📅", "0", "Today's Sessions", COLORS['accent']),
            ("🔥", "0", "Day Streak", "#f59e0b"),
        ]
        
        self._stat_value_labels = []
        
        for i, (icon, value, label, color) in enumerate(stats_data):
            stat_widget = QFrame()
            stat_widget.setStyleSheet(f"""
                QFrame {{
                    background: {color}08;
                    border-radius: 10px;
                    border: none;
                }}
            """)
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(16, 16, 16, 16)
            stat_layout.setSpacing(6)
            stat_layout.setAlignment(Qt.AlignCenter)
            
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
            icon_lbl.setAlignment(Qt.AlignCenter)
            stat_layout.addWidget(icon_lbl)
            
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"""
                font-size: 26px; font-weight: 800;
                color: {color};
                background: transparent;
            """)
            val_lbl.setAlignment(Qt.AlignCenter)
            stat_layout.addWidget(val_lbl)
            self._stat_value_labels.append(val_lbl)
            
            name_lbl = QLabel(label)
            name_lbl.setStyleSheet(f"""
                font-size: 11px; font-weight: 600;
                color: {COLORS['text_muted']};
                background: transparent;
            """)
            name_lbl.setAlignment(Qt.AlignCenter)
            stat_layout.addWidget(name_lbl)
            
            stats_grid.addWidget(stat_widget, 1)
        
        content_layout.addWidget(stats_frame)
        
        # ── SETTINGS GRID (2-column) ────────────────────────────
        settings_label = QLabel("⚙️  ACCOUNT SETTINGS")
        settings_label.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {COLORS['text_muted']};
            letter-spacing: 1.5px;
            padding-top: 8px;
        """)
        content_layout.addWidget(settings_label)
        
        grid = QGridLayout()
        grid.setSpacing(12)
        
        settings_items = [
            ("🔑", "Change Password", "Update your account password", self._change_password),
            ("🔔", "Notifications", "Manage alert preferences", self._show_notifications),
            ("🎨", "Appearance", "Theme and display settings", self._go_to_appearance),
            ("📤", "Export Data", "Download your translation history", self._export_data),
            ("❓", "Help & Support", "Get help and view guides", self._show_help),
        ]
        
        for i, (icon, title, desc, action) in enumerate(settings_items):
            card = QFrame()
            card.setCursor(Qt.PointingHandCursor)
            card.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_card']};
                    border: none;
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    background: {COLORS['bg_card_hover']};
                }}
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(14)
            
            icon_frame = QFrame()
            icon_frame.setFixedSize(40, 40)
            icon_frame.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['primary']}12;
                    border-radius: 10px;
                    border: none;
                }}
            """)
            icon_inner = QVBoxLayout(icon_frame)
            icon_inner.setContentsMargins(0, 0, 0, 0)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_inner.addWidget(icon_lbl)
            card_layout.addWidget(icon_frame)
            
            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"""
                font-size: 14px; font-weight: 600;
                color: {COLORS['text_primary']};
                background: transparent;
            """)
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"""
                font-size: 11px;
                color: {COLORS['text_muted']};
                background: transparent;
            """)
            text_col.addWidget(title_lbl)
            text_col.addWidget(desc_lbl)
            card_layout.addLayout(text_col, 1)
            
            arrow = QLabel("→")
            arrow.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; background: transparent;")
            card_layout.addWidget(arrow)
            
            # Make frame clickable via mouse event
            card.mousePressEvent = lambda e, a=action: a()
            
            row, col = divmod(i, 2)
            grid.addWidget(card, row, col)
        
        content_layout.addLayout(grid)
        
        # ── APP INFO FOOTER ───────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: none;
                border-radius: 12px;
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 14, 20, 14)
        
        app_lbl = QLabel("EmoSign")
        app_lbl.setStyleSheet(f"font-weight: 700; color: {COLORS['text_primary']}; background: transparent;")
        ver_lbl = QLabel("v2.0.0")
        ver_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent;")
        made_lbl = QLabel("Made with ❤️ using Python, MediaPipe & scikit-learn")
        made_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent;")
        
        footer_layout.addWidget(app_lbl)
        footer_layout.addWidget(ver_lbl)
        footer_layout.addStretch()
        footer_layout.addWidget(made_lbl)
        
        content_layout.addWidget(footer)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    # ── Data Loading ──────────────────────────────────────────────
    
    def _load_stats(self):
        """Load user statistics from database."""
        if not self.db or self.user.get("guest"):
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            self._stats = loop.run_until_complete(
                self.db.get_translation_stats(self.user.get("id", ""))
            )
            loop.close()
            self._update_stats_display()
        except Exception as e:
            print(f"Failed to load stats: {e}")
    
    def _update_stats_display(self):
        """Update stat value labels with loaded data."""
        if not hasattr(self, '_stat_value_labels') or len(self._stat_value_labels) < 4:
            return
        self._stat_value_labels[0].setText(str(self._stats.get("total", 0)))
        self._stat_value_labels[1].setText(str(self._stats.get("unique_signs", 0)))
        self._stat_value_labels[2].setText(str(self._stats.get("today", 0)))
        # Streak from analytics
        try:
            from core.analytics import analytics
            if analytics:
                user_id = self.user.get('id', 'guest')
                progress = analytics.get_learning_progress(user_id)
                self._stat_value_labels[3].setText(str(progress.get('current_streak', 0)))
        except ImportError:
            pass
    
    # ── Actions ───────────────────────────────────────────────────
    
    def _handle_logout(self):
        reply = QMessageBox.question(
            self, "Sign Out",
            "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.db:
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.db.sign_out())
                    loop.close()
                except Exception as e:
                    print(f"Sign out error: {e}")
            self.logout_requested.emit()
    
    def _change_password(self):
        if self.user.get("guest") or self.user.get("offline"):
            QMessageBox.information(self, "Not Available", "Password change is not available in guest/offline mode.")
            return
        dialog = ChangePasswordDialog(self.db, self.user.get("id", ""), self)
        dialog.exec()
    
    def _show_notifications(self):
        dialog = NotificationSettingsDialog(self)
        dialog.exec()
    
    def _go_to_appearance(self):
        # Navigate to settings page
        parent = self.parent()
        while parent:
            if hasattr(parent, 'navigate_to') and callable(parent.navigate_to):
                parent.navigate_to("settings")
                return
            parent = parent.parent()
    
    def _export_data(self):
        if not EXPORT_AVAILABLE:
            QMessageBox.warning(self, "Export Error", "Export functionality is not available.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Translation Data",
            os.path.expanduser("~/Documents/emosign_export.json"),
            "JSON Files (*.json);;CSV Files (*.csv);;Text Files (*.txt)"
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
                        translations.append(TranslationRecord(
                            text=item.get("sign_label", ""),
                            timestamp=datetime.fromisoformat(item.get("created_at", datetime.now().isoformat()).replace("Z", "")),
                            confidence=item.get("confidence", 0),
                            gesture_type=item.get("gesture_type", "static")
                        ))
                except Exception as e:
                    print(f"Failed to load translation history for export: {e}")
            
            if translations:
                result_path = exporter.export_translations(translations, fmt, os.path.basename(file_path))
                QMessageBox.information(self, "Export Complete", f"Data exported successfully!\n\nFile: {result_path}")
            else:
                QMessageBox.information(self, "No Data", "No translation data to export.")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export data: {e}")
    
    def _show_help(self):
        dialog = HelpSupportDialog(self)
        dialog.exec()
    
    # ── Public API ────────────────────────────────────────────────
    
    def update_user(self, user_data):
        self.user = user_data
        self._load_stats()
    
    def refresh(self):
        self._load_stats()
