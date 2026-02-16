"""
PySide6 Styles - Premium Professional Theme System
Modern, user-friendly design with multiple accent colors
"""

# ==================== ACCENT COLOR PRESETS ====================
ACCENT_PRESETS = {
    'teal': {
        'name': 'Teal',
        'primary': '#14b8a6',
        'primary_hover': '#0d9488',
        'primary_light': '#2dd4bf',
        'primary_glow': 'rgba(20, 184, 166, 0.3)',
        'gradient_start': '#14b8a6',
        'gradient_end': '#0d9488',
    },
    'blue': {
        'name': 'Ocean Blue',
        'primary': '#3b82f6',
        'primary_hover': '#2563eb',
        'primary_light': '#60a5fa',
        'primary_glow': 'rgba(59, 130, 246, 0.3)',
        'gradient_start': '#3b82f6',
        'gradient_end': '#2563eb',
    },
    'purple': {
        'name': 'Purple',
        'primary': '#8b5cf6',
        'primary_hover': '#7c3aed',
        'primary_light': '#a78bfa',
        'primary_glow': 'rgba(139, 92, 246, 0.3)',
        'gradient_start': '#8b5cf6',
        'gradient_end': '#7c3aed',
    },
    'pink': {
        'name': 'Pink',
        'primary': '#ec4899',
        'primary_hover': '#db2777',
        'primary_light': '#f472b6',
        'primary_glow': 'rgba(236, 72, 153, 0.3)',
        'gradient_start': '#ec4899',
        'gradient_end': '#db2777',
    },
    'orange': {
        'name': 'Sunset Orange',
        'primary': '#f97316',
        'primary_hover': '#ea580c',
        'primary_light': '#fb923c',
        'primary_glow': 'rgba(249, 115, 22, 0.3)',
        'gradient_start': '#f97316',
        'gradient_end': '#ea580c',
    },
    'green': {
        'name': 'Emerald',
        'primary': '#10b981',
        'primary_hover': '#059669',
        'primary_light': '#34d399',
        'primary_glow': 'rgba(16, 185, 129, 0.3)',
        'gradient_start': '#10b981',
        'gradient_end': '#059669',
    },
    'red': {
        'name': 'Ruby Red',
        'primary': '#ef4444',
        'primary_hover': '#dc2626',
        'primary_light': '#f87171',
        'primary_glow': 'rgba(239, 68, 68, 0.3)',
        'gradient_start': '#ef4444',
        'gradient_end': '#dc2626',
    },
    'indigo': {
        'name': 'Indigo',
        'primary': '#6366f1',
        'primary_hover': '#4f46e5',
        'primary_light': '#818cf8',
        'primary_glow': 'rgba(99, 102, 241, 0.3)',
        'gradient_start': '#6366f1',
        'gradient_end': '#4f46e5',
    },
}

# Default accent
_current_accent = 'teal'

def get_accent_colors():
    """Get current accent color palette."""
    return ACCENT_PRESETS.get(_current_accent, ACCENT_PRESETS['teal'])

def set_accent_color(accent_name: str):
    """Set the accent color theme."""
    global _current_accent
    if accent_name in ACCENT_PRESETS:
        _current_accent = accent_name

def get_accent_name() -> str:
    """Get current accent name."""
    return _current_accent

# ==================== COLOR PALETTE ====================
# Premium dark theme with vibrant accents
def _build_colors(accent='teal'):
    """Build color palette with specified accent."""
    acc = ACCENT_PRESETS.get(accent, ACCENT_PRESETS['teal'])
    return {
        # Backgrounds - Dark charcoal with subtle cool undertone
        'bg_app': '#12121a',
        'bg_panel': '#16161e',
        'bg_card': '#1a1a24',
        'bg_card_hover': '#22222e',
        'bg_hover': '#22222e',
        'bg_input': '#131319',
        'bg_sidebar': '#0e0e14',
        'bg_dark': '#0a0a10',
        'bg_secondary': '#16161e',
        
        # Primary - From accent
        'primary': acc['primary'],
        'primary_hover': acc['primary_hover'],
        'primary_light': acc['primary_light'],
        'primary_glow': acc['primary_glow'],
        
        # Accent - Cyan/Teal
        'accent': '#06b6d4',
        'accent_hover': '#0891b2',
        'accent_light': '#22d3ee',
        
        # Semantic Colors
        'success': '#10b981',
        'success_bg': 'rgba(16, 185, 129, 0.1)',
        'warning': '#f59e0b',
        'warning_bg': 'rgba(245, 158, 11, 0.1)',
        'danger': '#ef4444',
        'danger_bg': 'rgba(239, 68, 68, 0.1)',
        
        # Text
        'text_primary': '#e8e8f0',
        'text_secondary': '#8888a0',
        'text_muted': '#555568',
        'text_disabled': '#3a3a4a',
        
        # Borders & Dividers
        'border': '#262630',
        'border_light': '#303040',
        'divider': '#1e1e28',
        
        # Gradients
        'gradient_start': acc['gradient_start'],
        'gradient_end': acc['gradient_end'],
    }

# Default colors (will be regenerated when accent changes)
COLORS = _build_colors('teal')

# ==================== PREMIUM DARK THEME ====================
DARK_THEME = """
/* ========== GLOBAL RESET & BASE ========== */
QWidget {
    background-color: #12121a;
    color: #e8e8f0;
    font-family: 'Nunito', 'Segoe UI', 'SF Pro Display', sans-serif;
    font-size: 14px;
    selection-background-color: #8b5cf6;
    selection-color: white;
}

QMainWindow {
    background-color: #12121a;
}

/* ========== TYPOGRAPHY ========== */
QLabel {
    color: #e8e8f0;
    border: none;
    background: transparent;
}

QLabel#appTitle {
    font-size: 28px;
    font-weight: 700;
    color: #e8e8f0;
    letter-spacing: -0.5px;
}

QLabel#title {
    font-size: 24px;
    font-weight: 700;
    color: #e8e8f0;
    letter-spacing: -0.5px;
}

QLabel#pageTitle {
    font-size: 20px;
    font-weight: 600;
    color: #e8e8f0;
}

QLabel#subtitle {
    font-size: 14px;
    color: #8888a0;
    font-weight: 500;
}

QLabel#sectionTitle {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #555568;
    letter-spacing: 1.5px;
}

QLabel#prediction {
    font-size: 96px;
    font-weight: 800;
    color: #8b5cf6;
}

QLabel#predictionSmall {
    font-size: 48px;
    font-weight: 700;
    color: #8b5cf6;
}

QLabel#confidence {
    font-size: 18px;
    font-weight: 600;
    color: #10b981;
}

QLabel#status {
    color: #8888a0;
    font-size: 13px;
}

QLabel#errorText {
    color: #ef4444;
    font-size: 13px;
}

QLabel#successText {
    color: #10b981;
    font-size: 13px;
}

QLabel#welcomeText {
    font-size: 32px;
    font-weight: 700;
    color: #e8e8f0;
}

QLabel#statsNumber {
    font-size: 36px;
    font-weight: 700;
    color: #8b5cf6;
}

QLabel#statsLabel {
    font-size: 12px;
    font-weight: 600;
    color: #555568;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ========== CARDS & FRAMES ========== */
QFrame#card {
    background-color: #16161e;
    border: 1px solid #262630;
    border-radius: 14px;
}

QFrame#cardHover {
    background-color: #16161e;
    border: 1px solid #262630;
    border-radius: 14px;
}

QFrame#cardHover:hover {
    background-color: #1a1a24;
    border-color: #303040;
}

QFrame#highlightCard {
    background-color: #16161e;
    border: 1px solid #8b5cf6;
    border-radius: 14px;
}

QFrame#cameraView {
    background-color: #0a0a10;
    border-radius: 14px;
    border: 1px solid #262630;
}

QFrame#sidebar {
    background-color: #0e0e14;
    border-right: 1px solid #1e1e28;
}

QFrame#divider {
    background-color: #262630;
    max-height: 1px;
    min-height: 1px;
}

/* ========== BUTTONS - MODERN STYLE ========== */
QPushButton {
    background-color: #16161e;
    border: 1px solid #262630;
    border-radius: 10px;
    color: #e8e8f0;
    padding: 12px 20px;
    font-weight: 600;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #1e1e28;
    border-color: #303040;
}

QPushButton:pressed {
    background-color: #0e0e14;
}

QPushButton:disabled {
    background-color: #0e0e14;
    color: #3a3a4a;
    border-color: #1e1e28;
}

/* Primary Button - Gradient style */
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #7c3aed);
    border: none;
    color: white;
    padding: 14px 28px;
    font-weight: 600;
}

QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #6d28d9);
}

QPushButton#primary:pressed {
    background: #6d28d9;
}

QPushButton#primary:disabled {
    background: #262630;
    color: #555568;
}

/* Secondary Button */
QPushButton#secondary {
    background-color: transparent;
    border: 2px solid #8b5cf6;
    color: #8b5cf6;
}

QPushButton#secondary:hover {
    background-color: rgba(139, 92, 246, 0.1);
    border-color: #a78bfa;
    color: #a78bfa;
}

/* Accent Button - Cyan */
QPushButton#accent {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #06b6d4, stop:1 #0891b2);
    border: none;
    color: white;
}

QPushButton#accent:hover {
    background: #0891b2;
}

/* Success Button */
QPushButton#success {
    background-color: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

QPushButton#success:hover {
    background-color: rgba(16, 185, 129, 0.2);
    border-color: #10b981;
}

/* Danger Button */
QPushButton#danger {
    background-color: rgba(239, 68, 68, 0.12);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.25);
}

QPushButton#danger:hover {
    background-color: rgba(239, 68, 68, 0.2);
    border-color: #ef4444;
}

/* Ghost Button - Minimal */
QPushButton#ghost {
    background: transparent;
    border: none;
    color: #8888a0;
    padding: 8px 12px;
}

QPushButton#ghost:hover {
    color: #e8e8f0;
    background: rgba(255, 255, 255, 0.04);
}

/* Nav Button - Sidebar navigation */
QPushButton#navButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    color: #8888a0;
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
    font-size: 13px;
}

QPushButton#navButton:hover {
    background: rgba(139, 92, 246, 0.08);
    color: #e8e8f0;
}

QPushButton#navButton:checked {
    background: rgba(139, 92, 246, 0.10);
    color: #8b5cf6;
    border-left: 3px solid #8b5cf6;
    font-weight: 600;
}

/* Icon Button - Round */
QPushButton#iconButton {
    background: #16161e;
    border: 1px solid #262630;
    border-radius: 12px;
    padding: 12px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
}

QPushButton#iconButton:hover {
    background: #1e1e28;
    border-color: #8b5cf6;
}

/* Toggle Buttons */
QPushButton:checked {
    background: rgba(139, 92, 246, 0.12);
    border-color: #8b5cf6;
    color: #8b5cf6;
}

/* ========== INPUTS ========== */
QLineEdit {
    background-color: #131319;
    border: 1px solid #262630;
    border-radius: 10px;
    color: #e8e8f0;
    padding: 12px 16px;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #8b5cf6;
    background-color: #16161e;
}

QLineEdit:hover {
    border-color: #303040;
}

QLineEdit::placeholder {
    color: #555568;
}

QLineEdit#searchInput {
    background-color: #16161e;
    border-radius: 24px;
    padding-left: 44px;
}

QTextEdit {
    background-color: #131319;
    border: 1px solid #262630;
    border-radius: 10px;
    color: #e8e8f0;
    padding: 12px;
}

QTextEdit:focus {
    border-color: #8b5cf6;
}

QComboBox {
    background-color: #131319;
    border: 1px solid #262630;
    border-radius: 10px;
    padding: 10px 16px;
    color: #e8e8f0;
    font-size: 14px;
}

QComboBox:hover {
    border-color: #303040;
}

QComboBox:focus {
    border-color: #8b5cf6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 12px;
}

QComboBox QAbstractItemView {
    background-color: #16161e;
    border: 1px solid #262630;
    border-radius: 8px;
    selection-background-color: #8b5cf6;
    padding: 4px;
}

/* ========== PROGRESS BAR ========== */
QProgressBar {
    background-color: #131319;
    border: none;
    border-radius: 8px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #06b6d4);
    border-radius: 8px;
}

/* ========== SCROLLBAR - Minimal ========== */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}

QScrollBar::handle:vertical {
    background: #262630;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #303040;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px 4px;
}

QScrollBar::handle:horizontal {
    background: #262630;
    border-radius: 4px;
    min-width: 40px;
}

/* ========== STATUS PILLS ========== */
QLabel#statusPill {
    background-color: #16161e;
    border: 1px solid #262630;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusPillSuccess {
    background-color: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #10b981;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusPillWarning {
    background-color: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.25);
    color: #f59e0b;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusPillDanger {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.25);
    color: #ef4444;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

/* ========== TOOLTIPS ========== */
QToolTip {
    background-color: #1a1a24;
    border: 1px solid #262630;
    border-radius: 8px;
    color: #e8e8f0;
    padding: 8px 12px;
    font-size: 13px;
}

/* ========== LIST WIDGETS ========== */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    background-color: #16161e;
    border: 1px solid #262630;
    border-radius: 10px;
    padding: 14px;
    margin: 3px 0px;
}

QListWidget::item:hover {
    background-color: #1a1a24;
    border-color: #303040;
}

QListWidget::item:selected {
    background-color: rgba(139, 92, 246, 0.12);
    border-color: #8b5cf6;
}

/* ========== TABLE WIDGET ========== */
QTableWidget {
    background-color: #16161e;
    border: 1px solid #262630;
    border-radius: 10px;
    gridline-color: #262630;
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #1e1e28;
}

QTableWidget::item:selected {
    background-color: rgba(139, 92, 246, 0.12);
}

QHeaderView::section {
    background-color: #0e0e14;
    color: #555568;
    border: none;
    padding: 12px 16px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ========== MESSAGE BOX ========== */
QMessageBox {
    background-color: #16161e;
}

QMessageBox QLabel {
    color: #e8e8f0;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ========== ANIMATIONS HELPER CLASSES ========== */
QFrame#glowCard {
    background-color: #16161e;
    border: 2px solid #8b5cf6;
    border-radius: 14px;
}
"""

# ==================== LIGHT THEME ====================
def _build_light_colors(accent='teal'):
    """Build light color palette with specified accent."""
    acc = ACCENT_PRESETS.get(accent, ACCENT_PRESETS['teal'])
    return {
        # Backgrounds - Clean whites and grays
        'bg_app': '#f8fafc',
        'bg_panel': '#ffffff',
        'bg_card': '#ffffff',
        'bg_card_hover': '#f1f5f9',
        'bg_hover': '#f1f5f9',
        'bg_input': '#f1f5f9',
        'bg_sidebar': '#ffffff',
        'bg_dark': '#e2e8f0',
        'bg_secondary': '#f8fafc',
        
        # Primary - From accent (slightly darker for light mode)
        'primary': acc['primary_hover'],
        'primary_hover': acc['primary'],
        'primary_light': acc['primary_light'],
        'primary_glow': acc['primary_glow'].replace('0.3', '0.15'),
        
        # Accent
        'accent': '#0891b2',
        'accent_hover': '#0e7490',
        'accent_light': '#06b6d4',
        
        # Semantic Colors
        'success': '#059669',
        'success_bg': 'rgba(5, 150, 105, 0.1)',
        'warning': '#d97706',
        'warning_bg': 'rgba(217, 119, 6, 0.1)',
        'danger': '#dc2626',
        'danger_bg': 'rgba(220, 38, 38, 0.1)',
        
        # Text
        'text_primary': '#0f172a',
        'text_secondary': '#475569',
        'text_muted': '#64748b',
        'text_disabled': '#94a3b8',
        
        # Borders & Dividers
        'border': 'transparent',
        'border_light': 'transparent',
        'divider': '#e2e8f0',
        
        # Gradients
        'gradient_start': acc['gradient_start'],
        'gradient_end': acc['gradient_end'],
    }

LIGHT_COLORS = _build_light_colors('teal')

def _generate_light_theme(accent='teal'):
    """Generate light theme CSS with accent color."""
    acc = ACCENT_PRESETS.get(accent, ACCENT_PRESETS['teal'])
    primary = acc['primary_hover']
    primary_light = acc['primary']
    
    return f"""
/* ========== LIGHT THEME - COMPREHENSIVE ========== */
QWidget {{
    background-color: #f8fafc;
    color: #0f172a;
    font-family: 'Nunito', 'Segoe UI', 'SF Pro Display', sans-serif;
    font-size: 14px;
    selection-background-color: {primary};
    selection-color: white;
}}

QMainWindow {{
    background-color: #f8fafc;
}}

/* ========== TYPOGRAPHY ========== */
QLabel {{
    color: #0f172a;
    border: none;
    background: transparent;
}}

QLabel#appTitle, QLabel#title {{
    font-size: 28px;
    font-weight: 700;
    color: #0f172a;
}}

QLabel#pageTitle {{
    font-size: 20px;
    font-weight: 600;
    color: #0f172a;
}}

QLabel#subtitle {{
    font-size: 14px;
    color: #475569;
    font-weight: 500;
}}

QLabel#sectionTitle {{
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
    letter-spacing: 1.5px;
}}

QLabel#prediction {{
    font-size: 96px;
    font-weight: 800;
    color: {primary};
}}

QLabel#predictionSmall {{
    font-size: 48px;
    font-weight: 700;
    color: {primary};
}}

QLabel#confidence {{
    font-size: 18px;
    font-weight: 600;
    color: #059669;
}}

QLabel#statsNumber {{
    font-size: 36px;
    font-weight: 700;
    color: {primary};
}}

QLabel#statsLabel {{
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
}}

QLabel#welcomeText {{
    font-size: 32px;
    font-weight: 700;
    color: #0f172a;
}}

/* ========== CARDS & FRAMES ========== */
QFrame {{
    background-color: transparent;
}}

QFrame#card {{
    background-color: #ffffff;
    border: none;
    border-radius: 16px;
}}

QFrame#cardHover {{
    background-color: #ffffff;
    border: none;
    border-radius: 16px;
}}

QFrame#cardHover:hover {{
    background-color: #f1f5f9;
    border: none;
}}

QFrame#highlightCard {{
    background-color: #ffffff;
    border: 2px solid {primary};
    border-radius: 16px;
}}

QFrame#cameraView {{
    background-color: #1e293b;
    border-radius: 16px;
    border: none;
}}

QFrame#sidebar {{
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}}

QFrame#divider {{
    background-color: #e2e8f0;
    max-height: 1px;
    min-height: 1px;
}}

/* ========== BUTTONS ========== */
QPushButton {{
    background-color: #f1f5f9;
    border: none;
    border-radius: 10px;
    color: #0f172a;
    padding: 12px 20px;
    font-weight: 600;
    font-size: 14px;
}}

QPushButton:hover {{
    background-color: #e2e8f0;
    border: none;
}}

QPushButton:pressed {{
    background-color: #e2e8f0;
}}

QPushButton:disabled {{
    background-color: #f8fafc;
    color: #94a3b8;
    border: none;
}}

QPushButton#primary, QPushButton#primaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {primary_light}, stop:1 {primary});
    border: none;
    color: white;
    padding: 14px 28px;
}}

QPushButton#primary:hover, QPushButton#primaryButton:hover {{
    background: {primary};
}}

QPushButton#secondary, QPushButton#secondaryButton {{
    background-color: transparent;
    border: 2px solid {primary};
    color: {primary};
}}

QPushButton#secondary:hover, QPushButton#secondaryButton:hover {{
    background-color: {acc['primary_glow'].replace('0.3', '0.1')};
}}

QPushButton#success {{
    background-color: rgba(5, 150, 105, 0.1);
    color: #059669;
    border: 1px solid rgba(5, 150, 105, 0.3);
}}

QPushButton#danger {{
    background-color: rgba(220, 38, 38, 0.1);
    color: #dc2626;
    border: 1px solid rgba(220, 38, 38, 0.3);
}}

QPushButton#ghost {{
    background: transparent;
    border: none;
    color: #475569;
}}

QPushButton#ghost:hover {{
    color: #0f172a;
    background: rgba(0, 0, 0, 0.05);
}}

QPushButton#navButton {{
    background: transparent;
    border: none;
    border-radius: 8px;
    color: #475569;
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
    font-size: 13px;
}}

QPushButton#navButton:hover {{
    background: #f1f5f9;
    color: #0f172a;
}}

QPushButton#navButton:checked {{
    background: {acc['primary_glow'].replace('0.3', '0.1')};
    color: {primary};
    border-left: 3px solid {primary};
    font-weight: 600;
}}

QPushButton#iconButton {{
    background: #f1f5f9;
    border: none;
    border-radius: 12px;
    padding: 12px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
}}

QPushButton#iconButton:hover {{
    background: #e2e8f0;
    border: none;
}}

/* ========== INPUTS ========== */
QLineEdit {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    color: #0f172a;
    padding: 12px 16px;
    font-size: 14px;
}}

QLineEdit:hover {{
    border-color: #cbd5e1;
}}

QLineEdit:focus {{
    border-color: {primary};
    border-width: 2px;
}}

QLineEdit:disabled {{
    background-color: #f8fafc;
    color: #94a3b8;
}}

QTextEdit {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    color: #0f172a;
    padding: 12px;
}}

QTextEdit:focus {{
    border-color: {primary};
    border-width: 2px;
}}

/* ========== COMBO BOX ========== */
QComboBox {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    color: #0f172a;
    padding: 10px 16px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: #cbd5e1;
}}

QComboBox:focus {{
    border-color: {primary};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 12px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #64748b;
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    color: #0f172a;
    selection-background-color: {acc['primary_glow'].replace('0.3', '0.15')};
    selection-color: {primary};
    padding: 4px;
}}

/* ========== SLIDERS ========== */
QSlider::groove:horizontal {{
    background-color: #e2e8f0;
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {primary};
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {primary_light};
}}

QSlider::sub-page:horizontal {{
    background-color: {primary};
    border-radius: 3px;
}}

/* ========== CHECKBOXES ========== */
QCheckBox {{
    color: #0f172a;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid #cbd5e1;
    border-radius: 4px;
    background-color: #ffffff;
}}

QCheckBox::indicator:hover {{
    border-color: {primary};
}}

QCheckBox::indicator:checked {{
    background-color: {primary};
    border-color: {primary};
}}

/* ========== SPINBOX ========== */
QSpinBox {{
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    color: #0f172a;
    padding: 8px 12px;
}}

QSpinBox:focus {{
    border-color: {primary};
}}

/* ========== PROGRESS BAR ========== */
QProgressBar {{
    background-color: #e2e8f0;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #0f172a;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {primary_light}, stop:1 {primary});
    border-radius: 4px;
}}

/* ========== SCROLL AREA ========== */
QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: #f1f5f9;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: #cbd5e1;
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #94a3b8;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background-color: #f1f5f9;
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background-color: #cbd5e1;
    border-radius: 5px;
    min-width: 30px;
}}

/* ========== TAB WIDGET ========== */
QTabWidget::pane {{
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background-color: #ffffff;
}}

QTabBar::tab {{
    background-color: #f1f5f9;
    color: #475569;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: #ffffff;
    color: {primary};
    border-bottom: 2px solid {primary};
}}

QTabBar::tab:hover:!selected {{
    background-color: #e2e8f0;
}}

/* ========== GROUP BOX ========== */
QGroupBox {{
    font-weight: 600;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    color: #0f172a;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}}

/* ========== TOOLTIPS ========== */
QToolTip {{
    background-color: #1e293b;
    color: #f8fafc;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
}}
"""

LIGHT_THEME = _generate_light_theme('teal')

# ==================== ICONS (Emoji based for now) ====================
ICONS = {
    'camera_on': '📹',
    'camera_off': '🎥',
    'start': '▶️',
    'stop': '⏹️',
    'record': '⏺️',
    'train': '🧠',
    'save': '💾',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'wave': '👋',
    'hand': '✋',
    'copy': '📋',
    'clear': '🗑️',
    'user': '👤',
    'logout': '🚪',
    'settings': '⚙️',
    'history': '📜',
    'dashboard': '📊',
    'home': '🏠',
    'live': '🔴',
    'profile': '👤',
    'email': '📧',
    'lock': '🔒',
    'eye': '👁️',
    'search': '🔍',
    'refresh': '🔄',
    'delete': '🗑️',
    'edit': '✏️',
    'info': 'ℹ️',
    'close': '✕',
    'menu': '☰',
    'back': '←',
    'forward': '→',
    'up': '↑',
    'down': '↓',
    'check': '✓',
    'star': '⭐',
    'fire': '🔥',
    'sparkle': '✨',
    # New icons for features
    'voice': '🔊',
    'mute': '🔇',
    'language': '🌍',
    'tutorial': '📚',
    'analytics': '📊',
    'achievement': '🏆',
    'streak': '🔥',
    'conversation': '💬',
    'export': '📤',
    'calibrate': '🎯',
    'accessibility': '♿',
    'theme': '🎨',
}

# ==================== THEME MANAGER ====================
class ThemeManager:
    """Manages application themes and accent colors."""
    
    _current_theme = "dark"
    _current_accent = "teal"
    
    @classmethod
    def get_theme(cls) -> str:
        """Get current theme stylesheet."""
        if cls._current_theme == "light":
            return _generate_light_theme(cls._current_accent)
        return cls._generate_dark_theme(cls._current_accent)
    
    @classmethod
    def _generate_dark_theme(cls, accent: str) -> str:
        """Generate dark theme with accent color."""
        acc = ACCENT_PRESETS.get(accent, ACCENT_PRESETS['teal'])
        primary = acc['primary']
        primary_hover = acc['primary_hover']
        primary_light = acc['primary_light']
        primary_glow = acc['primary_glow']
        
        # Return dark theme with dynamic accent colors
        return DARK_THEME.replace('#8b5cf6', primary).replace('#7c3aed', primary_hover).replace('#a78bfa', primary_light).replace('rgba(139, 92, 246, 0.3)', primary_glow).replace('rgba(139, 92, 246, 0.12)', primary_glow.replace('0.3', '0.12')).replace('rgba(139, 92, 246, 0.08)', primary_glow.replace('0.3', '0.08'))
    
    @classmethod
    def get_colors(cls) -> dict:
        """Get current theme colors."""
        if cls._current_theme == "light":
            return _build_light_colors(cls._current_accent)
        return _build_colors(cls._current_accent)
    
    @classmethod
    def set_theme(cls, theme: str):
        """Set the current theme."""
        cls._current_theme = theme if theme in ["dark", "light"] else "dark"
        # Update global COLORS dict in-place so all pages use correct colors
        global COLORS
        if cls._current_theme == "light":
            COLORS.update(_build_light_colors(cls._current_accent))
        else:
            COLORS.update(_build_colors(cls._current_accent))
    
    @classmethod
    def set_accent(cls, accent: str):
        """Set the accent color."""
        if accent in ACCENT_PRESETS:
            cls._current_accent = accent
            global COLORS, LIGHT_COLORS, _current_accent
            _current_accent = accent
            COLORS.update(_build_colors(accent))
            LIGHT_COLORS.update(_build_light_colors(accent))
    
    @classmethod
    def get_accent(cls) -> str:
        """Get current accent name."""
        return cls._current_accent
    
    @classmethod
    def get_accent_options(cls) -> list:
        """Get list of available accent colors."""
        return [(key, val['name']) for key, val in ACCENT_PRESETS.items()]
    
    @classmethod
    def toggle_theme(cls) -> str:
        """Toggle between dark and light theme."""
        cls._current_theme = "light" if cls._current_theme == "dark" else "dark"
        # Update global COLORS dict in-place
        global COLORS
        if cls._current_theme == "light":
            COLORS.update(_build_light_colors(cls._current_accent))
        else:
            COLORS.update(_build_colors(cls._current_accent))
        return cls._current_theme
    
    @classmethod
    def is_dark(cls) -> bool:
        """Check if current theme is dark."""
        return cls._current_theme == "dark"

# ==================== ANIMATION HELPERS ====================
def get_fade_in_style():
    """Returns stylesheet for fade-in effect (use with QPropertyAnimation)"""
    return """
        QWidget {
            background-color: rgba(0, 0, 0, 0);
        }
    """

def get_glow_effect_style(color='#8b5cf6'):
    """Returns stylesheet with glow effect"""
    return f"""
        QFrame {{
            border: 2px solid {color};
            background-color: rgba(139, 92, 246, 0.04);
        }}
    """

# ==================== ACCESSIBILITY HELPERS ====================
def get_high_contrast_adjustments() -> str:
    """Get high contrast mode adjustments."""
    return """
        QLabel { color: #ffffff; }
        QFrame#card { border-width: 2px; border-color: #ffffff; }
        QPushButton { border-width: 2px; }
    """

def get_large_text_adjustments() -> str:
    """Get large text mode adjustments."""
    return """
        QLabel { font-size: 16px; }
        QLabel#title { font-size: 28px; }
        QLabel#subtitle { font-size: 16px; }
        QPushButton { font-size: 16px; padding: 14px 24px; }
        QLineEdit { font-size: 16px; }
    """

