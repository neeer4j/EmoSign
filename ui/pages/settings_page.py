"""
Settings Page - Clean, Modern Application Settings

Provides settings for:
- Appearance (Theme, Accent Color)
- Voice output configuration
- Language selection
- Accessibility options
- Detection settings
- Export preferences
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSlider, QCheckBox, QComboBox,
    QSpinBox, QGridLayout, QSizePolicy
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
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 20px;")
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
        self.content_layout.setSpacing(12)
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
    """Modern application settings page."""
    
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
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(24)
        
        # ========== HEADER ==========
        header, _ = make_page_header("⚙️ Settings", back_signal=self.back_requested)
        layout.addLayout(header)
        
        # ========== SCROLLABLE CONTENT ==========
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
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
        
        # ========== VOICE OUTPUT CARD ==========
        voice_card = SettingCard("Voice Output", "🔊")
        
        # Enable voice
        self.voice_enabled_check = QCheckBox()
        self.voice_enabled_check.setChecked(True)
        self.voice_enabled_check.stateChanged.connect(self._on_voice_settings_changed)
        voice_card.add_row("Enable Voice", self.voice_enabled_check, "Speak translations aloud")
        
        # Voice speed
        speed_widget = QWidget()
        speed_layout = QHBoxLayout(speed_widget)
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_layout.setSpacing(12)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(300)
        self.speed_slider.setValue(150)
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.valueChanged.connect(self._on_voice_settings_changed)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("150")
        self.speed_label.setFixedWidth(40)
        self.speed_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        speed_layout.addWidget(self.speed_label)
        
        voice_card.add_row("Speech Speed", speed_widget, "Words per minute (50-300)")
        
        # Volume
        volume_widget = QWidget()
        volume_layout = QHBoxLayout(volume_widget)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(12)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self._on_voice_settings_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("80%")
        self.volume_label.setFixedWidth(40)
        self.volume_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        volume_layout.addWidget(self.volume_label)
        
        voice_card.add_row("Volume", volume_widget, "Voice output volume")
        
        # Voice gender
        self.voice_gender_combo = QComboBox()
        self.voice_gender_combo.addItems(["Female", "Male"])
        voice_card.add_row("Voice", self.voice_gender_combo, "Preferred voice type")
        
        # Auto-speak mode
        self.auto_speak_combo = QComboBox()
        self.auto_speak_combo.addItems(["Per Sentence", "Per Word", "Manual Only"])
        voice_card.add_row("Auto-Speak", self.auto_speak_combo, "When to automatically speak")
        
        content_layout.addWidget(voice_card)
        
        # ========== LANGUAGE CARD ==========
        lang_card = SettingCard("Language", "🌍")
        
        self.sign_lang_combo = QComboBox()
        self.sign_lang_combo.addItems([
            "🇺🇸 American Sign Language (ASL)"
        ])
        self.sign_lang_combo.setEnabled(False)  # Only ASL supported
        lang_card.add_row("Sign Language", self.sign_lang_combo, "Currently only ASL is supported")
        
        content_layout.addWidget(lang_card)
        
        # ========== DETECTION CARD ==========
        detect_card = SettingCard("Detection", "🎯")
        
        # Two-hand mode
        self.two_hand_check = QCheckBox()
        self.two_hand_check.setChecked(True)
        detect_card.add_row("Two-Hand Mode", self.two_hand_check, "Detect signs using both hands")
        
        # Confidence threshold
        self.confidence_spin = QSpinBox()
        self.confidence_spin.setMinimum(30)
        self.confidence_spin.setMaximum(95)
        self.confidence_spin.setValue(55)
        self.confidence_spin.setSuffix("%")
        self.confidence_spin.setFixedWidth(100)
        detect_card.add_row("Confidence", self.confidence_spin, "Minimum confidence to accept detection")
        
        # Autocorrect
        self.autocorrect_check = QCheckBox()
        self.autocorrect_check.setChecked(True)
        detect_card.add_row("Autocorrect", self.autocorrect_check, "Auto-fix common signing errors")
        
        # Word prediction
        self.prediction_check = QCheckBox()
        self.prediction_check.setChecked(True)
        detect_card.add_row("Word Prediction", self.prediction_check, "Suggest next words")
        
        content_layout.addWidget(detect_card)
        
        # ========== ACCESSIBILITY CARD ==========
        access_card = SettingCard("Accessibility", "♿")
        
        self.high_contrast_check = QCheckBox()
        access_card.add_row("High Contrast", self.high_contrast_check, "Increase color contrast")
        
        self.large_text_check = QCheckBox()
        access_card.add_row("Large Text", self.large_text_check, "Use larger font sizes")
        
        self.reduce_motion_check = QCheckBox()
        access_card.add_row("Reduce Motion", self.reduce_motion_check, "Minimize animations")
        
        content_layout.addWidget(access_card)
        
        # ========== EXPORT CARD ==========
        export_card = SettingCard("Export", "📤")
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["TXT", "CSV", "JSON", "PDF", "HTML", "SRT"])
        export_card.add_row("Default Format", self.export_format_combo, "Default export format")
        
        self.timestamps_check = QCheckBox()
        self.timestamps_check.setChecked(True)
        export_card.add_row("Timestamps", self.timestamps_check, "Include timestamps")
        
        content_layout.addWidget(export_card)
        
        # ========== SAVE BUTTON ==========
        content_layout.addSpacing(16)
        
        save_btn = QPushButton("💾  Save Settings")
        save_btn.setObjectName("primary")
        save_btn.setFixedHeight(50)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        content_layout.addWidget(save_btn)
        
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
            'voice_enabled': self.voice_enabled_check.isChecked(),
            'voice_speed': self.speed_slider.value(),
            'voice_volume': self.volume_slider.value(),
            'voice_gender': self.voice_gender_combo.currentText().lower(),
            'auto_speak': self.auto_speak_combo.currentText(),
            'sign_language': 'asl',
            'two_hand_mode': self.two_hand_check.isChecked(),
            'confidence': self.confidence_spin.value(),
            'autocorrect': self.autocorrect_check.isChecked(),
            'prediction': self.prediction_check.isChecked(),
            'high_contrast': self.high_contrast_check.isChecked(),
            'large_text': self.large_text_check.isChecked(),
            'reduce_motion': self.reduce_motion_check.isChecked(),
            'export_format': self.export_format_combo.currentText(),
            'timestamps': self.timestamps_check.isChecked(),
        }
        
        # Save to config file
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "user_settings.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")
        
        # Emit signals for active settings
        self.detection_settings_changed.emit({
            'confidence_threshold': self.confidence_spin.value() / 100,
            'autocorrect': self.autocorrect_check.isChecked(),
            'word_prediction': self.prediction_check.isChecked(),
            'two_hand_mode': self.two_hand_check.isChecked()
        })
        
        self.accessibility_changed.emit({
            'high_contrast': self.high_contrast_check.isChecked(),
            'large_text': self.large_text_check.isChecked(),
            'reduce_motion': self.reduce_motion_check.isChecked()
        })
        
        # Show confirmation
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully!")
    
    def _on_theme_changed(self, theme_text: str):
        """Handle theme change."""
        theme = "dark" if "Dark" in theme_text else "light"
        ThemeManager.set_theme(theme)
        self.theme_changed.emit(theme)
        for btn in self.color_buttons:
            btn._update_style()
    
    def _on_accent_changed(self, accent_key: str):
        """Handle accent color change."""
        for btn in self.color_buttons:
            btn.setChecked(btn.color_key == accent_key)
        ThemeManager.set_accent(accent_key)
        self.accent_changed.emit(accent_key)
    
    def _on_voice_settings_changed(self):
        """Handle voice settings change."""
        self.speed_label.setText(str(self.speed_slider.value()))
        self.volume_label.setText(f"{self.volume_slider.value()}%")
        self.voice_settings_changed.emit({
            'enabled': self.voice_enabled_check.isChecked(),
            'speed': self.speed_slider.value(),
            'volume': self.volume_slider.value() / 100,
            'gender': self.voice_gender_combo.currentText().lower(),
            'auto_speak': self.auto_speak_combo.currentText()
        })
    
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
            
            self.voice_enabled_check.setChecked(settings.get('voice_enabled', True))
            self.speed_slider.setValue(settings.get('voice_speed', 150))
            self.volume_slider.setValue(settings.get('voice_volume', 80))
            
            gender = settings.get('voice_gender', 'female').title()
            if gender in ["Male", "Female"]:
                self.voice_gender_combo.setCurrentText(gender)
            
            auto_speak = settings.get('auto_speak', 'Per Sentence')
            if auto_speak in ["Per Sentence", "Per Word", "Manual Only"]:
                self.auto_speak_combo.setCurrentText(auto_speak)
            
            self.two_hand_check.setChecked(settings.get('two_hand_mode', True))
            self.confidence_spin.setValue(settings.get('confidence', 55))
            self.autocorrect_check.setChecked(settings.get('autocorrect', True))
            self.prediction_check.setChecked(settings.get('prediction', True))
            
            self.high_contrast_check.setChecked(settings.get('high_contrast', False))
            self.large_text_check.setChecked(settings.get('large_text', False))
            self.reduce_motion_check.setChecked(settings.get('reduce_motion', False))
            
            export_fmt = settings.get('export_format', 'TXT')
            if export_fmt in ["TXT", "CSV", "JSON", "PDF", "HTML", "SRT"]:
                self.export_format_combo.setCurrentText(export_fmt)
            
            self.timestamps_check.setChecked(settings.get('timestamps', True))
            
        except Exception as e:
            print(f"Failed to load settings: {e}")

