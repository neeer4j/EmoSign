"""
Settings Page - Application settings and preferences

Provides settings for:
- Voice output configuration
- Theme (dark/light mode)
- Language selection
- Accessibility options
- Export preferences
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSlider, QCheckBox, QComboBox,
    QSpinBox, QGroupBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.styles import COLORS


class SettingRow(QFrame):
    """A row for a single setting."""
    
    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        text_layout.addWidget(title_label)
        
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Control widget placeholder
        self.control_layout = QHBoxLayout()
        layout.addLayout(self.control_layout)
    
    def add_control(self, widget):
        """Add a control widget to the row."""
        self.control_layout.addWidget(widget)


class SettingsPage(QWidget):
    """Application settings page."""
    
    back_requested = Signal()
    theme_changed = Signal(str)  # 'dark' or 'light'
    voice_settings_changed = Signal(dict)
    language_changed = Signal(str)
    accessibility_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()
    
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
        
        title = QLabel("⚙️ Settings")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        
        # ============ Appearance Section ============
        appearance_section = self._create_section("🎨 Appearance")
        
        # Theme toggle
        theme_row = SettingRow("Theme", "Switch between dark and light mode")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Mode", "Light Mode", "System Default"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_row.add_control(self.theme_combo)
        appearance_section.layout().addWidget(theme_row)
        
        # UI Scale
        scale_row = SettingRow("UI Scale", "Adjust the size of interface elements")
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["100%", "125%", "150%", "175%", "200%"])
        scale_row.add_control(self.scale_combo)
        appearance_section.layout().addWidget(scale_row)
        
        content_layout.addWidget(appearance_section)
        
        # ============ Voice Output Section ============
        voice_section = self._create_section("🔊 Voice Output")
        
        # Enable voice
        voice_enable_row = SettingRow("Enable Voice", "Speak translations aloud")
        self.voice_enabled_check = QCheckBox()
        self.voice_enabled_check.setChecked(True)
        self.voice_enabled_check.stateChanged.connect(self._on_voice_settings_changed)
        voice_enable_row.add_control(self.voice_enabled_check)
        voice_section.layout().addWidget(voice_enable_row)
        
        # Voice speed
        speed_row = SettingRow("Speech Speed", "Adjust how fast text is spoken")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(300)
        self.speed_slider.setValue(150)
        self.speed_slider.setFixedWidth(200)
        self.speed_slider.valueChanged.connect(self._on_voice_settings_changed)
        self.speed_label = QLabel("150 wpm")
        speed_row.add_control(self.speed_slider)
        speed_row.add_control(self.speed_label)
        voice_section.layout().addWidget(speed_row)
        
        # Voice volume
        volume_row = SettingRow("Volume", "Adjust voice output volume")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(200)
        self.volume_slider.valueChanged.connect(self._on_voice_settings_changed)
        self.volume_label = QLabel("80%")
        volume_row.add_control(self.volume_slider)
        volume_row.add_control(self.volume_label)
        voice_section.layout().addWidget(volume_row)
        
        # Auto-speak options
        auto_words_row = SettingRow("Auto-speak Words", "Automatically speak detected words")
        self.auto_words_check = QCheckBox()
        self.auto_words_check.setChecked(True)
        auto_words_row.add_control(self.auto_words_check)
        voice_section.layout().addWidget(auto_words_row)
        
        auto_sentences_row = SettingRow("Auto-speak Sentences", "Automatically speak completed sentences")
        self.auto_sentences_check = QCheckBox()
        self.auto_sentences_check.setChecked(True)
        auto_sentences_row.add_control(self.auto_sentences_check)
        voice_section.layout().addWidget(auto_sentences_row)
        
        content_layout.addWidget(voice_section)
        
        # ============ Language Section ============
        lang_section = self._create_section("🌍 Language")
        
        # Sign language selection
        sign_lang_row = SettingRow("Sign Language", "Select the sign language to recognize")
        self.sign_lang_combo = QComboBox()
        self.sign_lang_combo.addItems([
            "🇺🇸 American Sign Language (ASL)",
            "🇬🇧 British Sign Language (BSL)",
            "🇮🇳 Indian Sign Language (ISL)",
            "🇫🇷 French Sign Language (LSF)",
            "🇩🇪 German Sign Language (DGS)",
            "🇦🇺 Australian Sign Language (Auslan)"
        ])
        self.sign_lang_combo.currentTextChanged.connect(self._on_language_changed)
        sign_lang_row.add_control(self.sign_lang_combo)
        lang_section.layout().addWidget(sign_lang_row)
        
        content_layout.addWidget(lang_section)
        
        # ============ Accessibility Section ============
        access_section = self._create_section("♿ Accessibility")
        
        # High contrast
        contrast_row = SettingRow("High Contrast", "Increase color contrast for better visibility")
        self.high_contrast_check = QCheckBox()
        contrast_row.add_control(self.high_contrast_check)
        access_section.layout().addWidget(contrast_row)
        
        # Large text
        large_text_row = SettingRow("Large Text", "Use larger font sizes throughout the app")
        self.large_text_check = QCheckBox()
        large_text_row.add_control(self.large_text_check)
        access_section.layout().addWidget(large_text_row)
        
        # Reduce motion
        motion_row = SettingRow("Reduce Motion", "Minimize animations and transitions")
        self.reduce_motion_check = QCheckBox()
        motion_row.add_control(self.reduce_motion_check)
        access_section.layout().addWidget(motion_row)
        
        # Screen reader support
        reader_row = SettingRow("Screen Reader Support", "Optimize for screen readers")
        self.screen_reader_check = QCheckBox()
        reader_row.add_control(self.screen_reader_check)
        access_section.layout().addWidget(reader_row)
        
        content_layout.addWidget(access_section)
        
        # ============ Detection Section ============
        detect_section = self._create_section("🎯 Detection")
        
        # Two-hand mode
        two_hand_row = SettingRow("Two-Hand Mode", "Enable detection of two-handed signs")
        self.two_hand_check = QCheckBox()
        self.two_hand_check.setChecked(True)
        two_hand_row.add_control(self.two_hand_check)
        detect_section.layout().addWidget(two_hand_row)
        
        # Confidence threshold
        confidence_row = SettingRow("Confidence Threshold", "Minimum confidence to accept a detection")
        self.confidence_spin = QSpinBox()
        self.confidence_spin.setMinimum(30)
        self.confidence_spin.setMaximum(95)
        self.confidence_spin.setValue(55)
        self.confidence_spin.setSuffix("%")
        confidence_row.add_control(self.confidence_spin)
        detect_section.layout().addWidget(confidence_row)
        
        content_layout.addWidget(detect_section)
        
        # ============ Export Section ============
        export_section = self._create_section("📤 Export")
        
        # Default format
        format_row = SettingRow("Default Export Format", "Choose the default format for exports")
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["TXT", "CSV", "JSON", "PDF", "HTML"])
        format_row.add_control(self.export_format_combo)
        export_section.layout().addWidget(format_row)
        
        # Include timestamps
        timestamps_row = SettingRow("Include Timestamps", "Add timestamps to exported translations")
        self.timestamps_check = QCheckBox()
        self.timestamps_check.setChecked(True)
        timestamps_row.add_control(self.timestamps_check)
        export_section.layout().addWidget(timestamps_row)
        
        # Include confidence
        confidence_export_row = SettingRow("Include Confidence", "Add confidence scores to exports")
        self.confidence_export_check = QCheckBox()
        confidence_export_row.add_control(self.confidence_export_check)
        export_section.layout().addWidget(confidence_export_row)
        
        content_layout.addWidget(export_section)
        
        content_layout.addStretch()
        
        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_settings)
        content_layout.addWidget(save_btn)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def _create_section(self, title: str) -> QFrame:
        """Create a settings section."""
        section = QFrame()
        section.setObjectName("card")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(title_label)
        
        return section
    
    def _load_settings(self):
        """Load current settings."""
        # TODO: Load from config/storage
        pass
    
    def _save_settings(self):
        """Save all settings."""
        settings = {
            'theme': self.theme_combo.currentText(),
            'ui_scale': self.scale_combo.currentText(),
            'voice_enabled': self.voice_enabled_check.isChecked(),
            'voice_speed': self.speed_slider.value(),
            'voice_volume': self.volume_slider.value(),
            'auto_speak_words': self.auto_words_check.isChecked(),
            'auto_speak_sentences': self.auto_sentences_check.isChecked(),
            'sign_language': self.sign_lang_combo.currentText(),
            'high_contrast': self.high_contrast_check.isChecked(),
            'large_text': self.large_text_check.isChecked(),
            'reduce_motion': self.reduce_motion_check.isChecked(),
            'screen_reader': self.screen_reader_check.isChecked(),
            'two_hand_mode': self.two_hand_check.isChecked(),
            'confidence_threshold': self.confidence_spin.value(),
            'export_format': self.export_format_combo.currentText(),
            'export_timestamps': self.timestamps_check.isChecked(),
            'export_confidence': self.confidence_export_check.isChecked(),
        }
        
        # TODO: Save to config/storage
        print("Settings saved:", settings)
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        if "Dark" in theme:
            self.theme_changed.emit("dark")
        elif "Light" in theme:
            self.theme_changed.emit("light")
        else:
            self.theme_changed.emit("system")
    
    def _on_voice_settings_changed(self):
        """Handle voice settings change."""
        self.speed_label.setText(f"{self.speed_slider.value()} wpm")
        self.volume_label.setText(f"{self.volume_slider.value()}%")
        
        self.voice_settings_changed.emit({
            'enabled': self.voice_enabled_check.isChecked(),
            'speed': self.speed_slider.value(),
            'volume': self.volume_slider.value() / 100
        })
    
    def _on_language_changed(self, language: str):
        """Handle language change."""
        # Extract language code from selection
        if "ASL" in language:
            self.language_changed.emit("asl")
        elif "BSL" in language:
            self.language_changed.emit("bsl")
        elif "ISL" in language:
            self.language_changed.emit("isl")
        elif "LSF" in language:
            self.language_changed.emit("lsf")
        elif "DGS" in language:
            self.language_changed.emit("dgs")
        elif "Auslan" in language:
            self.language_changed.emit("auslan")
