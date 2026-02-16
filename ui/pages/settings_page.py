"""
Settings Page - Application Appearance Settings

Provides settings for:
- Appearance (Theme, Accent Color)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ACCENT_PRESETS, ThemeManager
from ui.page_header import make_page_header


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
    """Application settings page — Appearance only."""
    
    back_requested = Signal()
    theme_changed = Signal(str)
    accent_changed = Signal(str)
    voice_settings_changed = Signal(dict)
    language_changed = Signal(str)
    accessibility_changed = Signal(dict)
    detection_settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        import os
        
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

