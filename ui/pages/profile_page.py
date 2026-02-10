"""
Profile Page - User settings and account management
Clean profile view with stats and logout
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
                background-color: {COLORS['bg_primary']};
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
                background-color: {COLORS['bg_primary']};
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
        # Save to config file
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
                background-color: {COLORS['bg_primary']};
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


class ProfileCard(QFrame):
    """User profile display card."""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Avatar circle
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(100, 100)
        avatar_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                border-radius: 50px;
            }}
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Get initials from email
        email = self.user.get("email", "User")
        initials = email[0].upper() if email else "U"
        
        initial_label = QLabel(initials)
        initial_label.setStyleSheet("""
            font-size: 40px;
            font-weight: 700;
            color: white;
            background: transparent;
        """)
        initial_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(initial_label)
        
        # Center the avatar
        avatar_container = QHBoxLayout()
        avatar_container.addStretch()
        avatar_container.addWidget(avatar_frame)
        avatar_container.addStretch()
        layout.addLayout(avatar_container)
        
        # User name
        name = email.split("@")[0].title() if "@" in email else email
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {COLORS['text_primary']};
        """)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        # Email
        email_label = QLabel(email)
        email_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
        """)
        email_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(email_label)
        
        # Account status badge
        if self.user.get("guest"):
            status = "Guest Account"
            status_color = COLORS['warning']
        elif self.user.get("offline"):
            status = "Offline Mode"
            status_color = COLORS['text_muted']
        else:
            status = "Verified Account"
            status_color = COLORS['success']
        
        status_badge = QLabel(f"• {status}")
        status_badge.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {status_color};
        """)
        status_badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_badge)
    
    def update_user(self, user_data):
        """Update user data."""
        self.user = user_data
        # Would need to refresh UI


class StatsRow(QFrame):
    """Row of user statistics."""
    
    def __init__(self, stats=None, parent=None):
        super().__init__(parent)
        self.stats = stats or {}
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)
        
        stats_data = [
            (str(self.stats.get("total", 0)), "Total\nTranslations"),
            (str(self.stats.get("unique_signs", 0)), "Unique\nSigns"),
            (str(self.stats.get("today", 0)), "Today's\nSessions"),
            ("0", "Day\nStreak"),
        ]
        
        for i, (value, label) in enumerate(stats_data):
            stat_layout = QVBoxLayout()
            stat_layout.setAlignment(Qt.AlignCenter)
            
            value_label = QLabel(value)
            value_label.setStyleSheet(f"""
                font-size: 28px;
                font-weight: 700;
                color: {COLORS['primary']};
            """)
            value_label.setAlignment(Qt.AlignCenter)
            
            label_label = QLabel(label)
            label_label.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS['text_muted']};
                text-align: center;
            """)
            label_label.setAlignment(Qt.AlignCenter)
            
            stat_layout.addWidget(value_label)
            stat_layout.addWidget(label_label)
            layout.addLayout(stat_layout)
            
            # Add divider between stats
            if i < len(stats_data) - 1:
                divider = QFrame()
                divider.setStyleSheet(f"background-color: {COLORS['border']}; max-width: 1px;")
                divider.setFixedWidth(1)
                layout.addWidget(divider)


class SettingsSection(QFrame):
    """Settings and actions section."""
    
    logout_requested = Signal()
    password_change_requested = Signal()
    navigate_to_settings = Signal()
    
    def __init__(self, db_service=None, user_data=None, parent=None):
        super().__init__(parent)
        self.db = db_service
        self.user = user_data or {}
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Section title
        title = QLabel("⚙️ Account Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Settings buttons - all functional now
        settings = [
            ("🔑", "Change Password", self._change_password),
            ("🔔", "Notifications", self._show_notifications),
            ("🎨", "Appearance", self._go_to_appearance),
            ("📤", "Export Data", self._export_data),
            ("❓", "Help & Support", self._show_help),
        ]
        
        for icon, text, action in settings:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("navButton")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 14px 16px;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(action)
            layout.addWidget(btn)
        
        layout.addSpacing(20)
        
        # Danger zone
        danger_title = QLabel("⚠️ Danger Zone")
        danger_title.setObjectName("sectionTitle")
        danger_title.setStyleSheet(f"color: {COLORS['danger']};")
        layout.addWidget(danger_title)
        
        logout_btn = QPushButton("🚪  Sign Out")
        logout_btn.setObjectName("danger")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout_btn)
    
    def _change_password(self):
        """Show change password dialog."""
        if self.user.get("guest") or self.user.get("offline"):
            QMessageBox.information(
                self, "Not Available",
                "Password change is not available in guest/offline mode."
            )
            return
        
        dialog = ChangePasswordDialog(self.db, self.user.get("id", ""), self)
        dialog.exec()
    
    def _show_notifications(self):
        """Show notification settings dialog."""
        dialog = NotificationSettingsDialog(self)
        dialog.exec()
    
    def _go_to_appearance(self):
        """Navigate to appearance/settings page."""
        self.navigate_to_settings.emit()
    
    def _export_data(self):
        """Export user data."""
        if not EXPORT_AVAILABLE:
            QMessageBox.warning(
                self, "Export Error",
                "Export functionality is not available."
            )
            return
        
        # Ask for export location
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Translation Data",
            os.path.expanduser("~/Documents/emosign_export.json"),
            "JSON Files (*.json);;CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            # Determine format from extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".csv":
                fmt = ExportFormat.CSV
            elif ext == ".txt":
                fmt = ExportFormat.TXT
            else:
                fmt = ExportFormat.JSON
            
            # Create export manager and export
            exporter = ExportManager(os.path.dirname(file_path))
            
            # Get user's translation history if db available
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
                QMessageBox.information(
                    self, "Export Complete",
                    f"Data exported successfully!\n\nFile: {result_path}"
                )
            else:
                QMessageBox.information(
                    self, "No Data",
                    "No translation data to export. Start using the app to generate data!"
                )
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export data: {e}")
    
    def _show_help(self):
        """Show help and support dialog."""
        dialog = HelpSupportDialog(self)
        dialog.exec()
    
    def update_user(self, user_data):
        """Update user data."""
        self.user = user_data


class ProfilePage(QWidget):
    """User profile and settings page."""
    
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
        """Setup profile page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 32)
        main_layout.setSpacing(24)
        
        # === HEADER ===
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self.back_requested.emit)
        
        title = QLabel("👤 Profile & Settings")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        main_layout.addLayout(header)
        
        # === CONTENT ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left column: Profile + Stats
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        self.profile_card = ProfileCard(self.user)
        self.stats_row = StatsRow(self._stats)
        
        left_column.addWidget(self.profile_card)
        left_column.addWidget(self.stats_row)
        left_column.addStretch()
        
        # Right column: Settings
        self.settings_section = SettingsSection(self.db, self.user)
        self.settings_section.logout_requested.connect(self._handle_logout)
        
        content_layout.addLayout(left_column, 1)
        content_layout.addWidget(self.settings_section, 1)
        
        main_layout.addLayout(content_layout)
        
        # === APP INFO ===
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(24, 16, 24, 16)
        
        app_name = QLabel("EmoSign")
        app_name.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        
        version = QLabel("v2.0.0")
        version.setStyleSheet(f"color: {COLORS['text_muted']};")
        
        made_with = QLabel("Made with ❤️ using Python, MediaPipe & scikit-learn")
        made_with.setStyleSheet(f"color: {COLORS['text_muted']};")
        
        info_layout.addWidget(app_name)
        info_layout.addWidget(version)
        info_layout.addStretch()
        info_layout.addWidget(made_with)
        
        main_layout.addWidget(info_frame)
    
    def _load_stats(self):
        """Load user statistics."""
        if not self.db or self.user.get("guest"):
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            self._stats = loop.run_until_complete(
                self.db.get_translation_stats(self.user.get("id", ""))
            )
            loop.close()
            
            # Update stats display
            self._update_stats_display()
        except Exception as e:
            print(f"Failed to load stats: {e}")
    
    def _update_stats_display(self):
        """Update the stats row with new data."""
        # Remove old stats row and rebuild with new data
        if hasattr(self, 'stats_row') and self.stats_row:
            self.stats_row.deleteLater()
        self.stats_row = StatsRow(self._stats)
        # Find the left column layout and insert the new stats row
        content_layout = self.centralWidget().layout() if hasattr(self, 'centralWidget') else None
        # Re-insert into the layout - find it by traversing
        main_layout = self.layout()
        if main_layout and main_layout.count() > 1:
            content_item = main_layout.itemAt(1)  # content_layout is second item
            if content_item and content_item.layout():
                left_col = content_item.layout().itemAt(0)
                if left_col and left_col.layout():
                    left_col.layout().insertWidget(1, self.stats_row)
    
    def _handle_logout(self):
        """Handle logout request."""
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
    
    def update_user(self, user_data):
        """Update user data."""
        self.user = user_data
        self.settings_section.user = user_data
        self._load_stats()
    
    def refresh(self):
        """Refresh profile data."""
        self._load_stats()
