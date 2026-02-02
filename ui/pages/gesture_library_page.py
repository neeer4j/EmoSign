"""
Gesture Library Page - Visual dictionary of all available signs

Provides a searchable reference of all signs with:
- Visual demonstrations
- Hand shape descriptions
- Search and filtering
- Category organization
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QLineEdit,
    QComboBox, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS


class SignCard(QFrame):
    """A card displaying information about a sign."""
    
    clicked = Signal(str)  # sign_id
    
    def __init__(self, sign_id: str, text: str, category: str,
                 description: str = "", emoji: str = "", is_dynamic: bool = False,
                 parent=None):
        super().__init__(parent)
        self.sign_id = sign_id
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(180, 200)
        self._setup_ui(text, category, description, emoji, is_dynamic)
    
    def _setup_ui(self, text, category, description, emoji, is_dynamic):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Category badge
        badge = QLabel(category.title())
        badge_colors = {
            'letter': COLORS['primary'],
            'number': COLORS['accent'],
            'word': COLORS['success'],
            'phrase': COLORS['warning'],
        }
        badge_color = badge_colors.get(category.lower(), COLORS['text_muted'])
        badge.setStyleSheet(f"""
            background-color: {badge_color}30;
            color: {badge_color};
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
        """)
        badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(badge, alignment=Qt.AlignCenter)
        
        # Main display (emoji or text)
        if emoji:
            display = QLabel(emoji)
            display.setStyleSheet("font-size: 48px; background: transparent;")
        else:
            display = QLabel(text)
            display.setStyleSheet(f"""
                font-size: 48px;
                font-weight: 700;
                color: {COLORS['primary']};
                background: transparent;
            """)
        display.setAlignment(Qt.AlignCenter)
        layout.addWidget(display)
        
        # Text label
        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        # Dynamic indicator
        if is_dynamic:
            dynamic_label = QLabel("🔄 Motion")
            dynamic_label.setStyleSheet(f"""
                color: {COLORS['accent']};
                font-size: 11px;
                background: transparent;
            """)
            dynamic_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(dynamic_label)
        
        layout.addStretch()
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.sign_id)


class SignDetailPanel(QFrame):
    """Panel showing detailed information about a sign."""
    
    close_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedWidth(350)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        self.title_label = QLabel("Sign Details")
        self.title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(self.title_label)
        header.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']};
                border: none;
                border-radius: 16px;
                color: {COLORS['text_secondary']};
            }}
            QPushButton:hover {{
                background: {COLORS['bg_card_hover']};
            }}
        """)
        close_btn.clicked.connect(self.close_requested.emit)
        header.addWidget(close_btn)
        
        layout.addLayout(header)
        
        # Sign display
        self.sign_display = QLabel("A")
        self.sign_display.setStyleSheet(f"""
            font-size: 80px;
            font-weight: 700;
            color: {COLORS['primary']};
            background: {COLORS['bg_input']};
            border-radius: 16px;
            padding: 24px;
        """)
        self.sign_display.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sign_display)
        
        # Description
        self.description_label = QLabel("Hand shape description")
        self.description_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # Hand position section
        position_title = QLabel("📍 Hand Position")
        position_title.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        layout.addWidget(position_title)
        
        self.position_label = QLabel("Position details...")
        self.position_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.position_label.setWordWrap(True)
        layout.addWidget(self.position_label)
        
        # Tips section
        tips_title = QLabel("💡 Tips")
        tips_title.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        layout.addWidget(tips_title)
        
        self.tips_label = QLabel("Tips for signing...")
        self.tips_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.tips_label.setWordWrap(True)
        layout.addWidget(self.tips_label)
        
        layout.addStretch()
        
        # Practice button
        practice_btn = QPushButton("Practice This Sign")
        practice_btn.setObjectName("primaryButton")
        layout.addWidget(practice_btn)
    
    def show_sign(self, sign_data: dict):
        """Display information for a specific sign."""
        self.title_label.setText(sign_data.get('text', 'Sign'))
        
        display_text = sign_data.get('emoji', sign_data.get('text', '?'))
        self.sign_display.setText(display_text)
        
        self.description_label.setText(sign_data.get('description', 'No description available.'))
        self.position_label.setText(sign_data.get('position', 'Hold your hand in front of you.'))
        self.tips_label.setText(sign_data.get('tips', 'Practice slowly and clearly.'))


class GestureLibraryPage(QWidget):
    """Gesture library and reference page."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._signs_data = self._load_signs_data()
        self._setup_ui()
    
    def _load_signs_data(self) -> list:
        """Load all available signs data."""
        signs = []
        
        # Letters A-Z
        letter_descriptions = {
            'A': {'desc': 'Fist with thumb to side', 'pos': 'Fist facing forward', 'tips': 'Keep thumb parallel to fingers'},
            'B': {'desc': 'Flat hand, fingers together', 'pos': 'Palm facing out', 'tips': 'Keep fingers straight'},
            'C': {'desc': 'Curved hand like holding cup', 'pos': 'Side view', 'tips': 'Make a smooth curve'},
            'D': {'desc': 'Index up, others touch thumb', 'pos': 'Palm facing out', 'tips': 'Form a circle with other fingers'},
            'E': {'desc': 'Fingers curled over thumb', 'pos': 'Palm facing out', 'tips': 'Tuck thumb under fingers'},
            'F': {'desc': 'OK sign, 3 fingers up', 'pos': 'Palm facing out', 'tips': 'Touch index to thumb'},
            'G': {'desc': 'Pointing hand horizontal', 'pos': 'Side view', 'tips': 'Point to the side'},
            'H': {'desc': 'Two fingers out horizontal', 'pos': 'Side view', 'tips': 'Index and middle together'},
            'I': {'desc': 'Pinky finger up only', 'pos': 'Palm facing out', 'tips': 'Keep other fingers in fist'},
            'J': {'desc': 'Pinky draws J shape', 'pos': 'Moving downward', 'tips': 'Trace J in the air'},
            'K': {'desc': 'Peace sign with thumb', 'pos': 'Palm facing out', 'tips': 'Thumb between fingers'},
            'L': {'desc': 'L shape with thumb and index', 'pos': 'Palm facing out', 'tips': 'Make a right angle'},
            'M': {'desc': 'Three fingers over thumb', 'pos': 'Palm facing down', 'tips': 'Thumb under 3 fingers'},
            'N': {'desc': 'Two fingers over thumb', 'pos': 'Palm facing down', 'tips': 'Thumb under 2 fingers'},
            'O': {'desc': 'Fingers form O shape', 'pos': 'Side view', 'tips': 'Touch all fingers to thumb'},
            'P': {'desc': 'K shape pointing down', 'pos': 'Pointing downward', 'tips': 'Like K but inverted'},
            'Q': {'desc': 'G shape pointing down', 'pos': 'Pointing downward', 'tips': 'Like G but inverted'},
            'R': {'desc': 'Crossed index and middle', 'pos': 'Palm facing out', 'tips': 'Cross the fingers'},
            'S': {'desc': 'Fist with thumb over fingers', 'pos': 'Palm facing out', 'tips': 'Thumb across front'},
            'T': {'desc': 'Thumb between fingers', 'pos': 'Palm facing left', 'tips': 'Index over thumb'},
            'U': {'desc': 'Two fingers up together', 'pos': 'Palm facing out', 'tips': 'Fingers together'},
            'V': {'desc': 'Peace sign', 'pos': 'Palm facing out', 'tips': 'Fingers spread apart'},
            'W': {'desc': 'Three fingers up spread', 'pos': 'Palm facing out', 'tips': 'Like V plus middle'},
            'X': {'desc': 'Hooked index finger', 'pos': 'Palm facing left', 'tips': 'Curl the index'},
            'Y': {'desc': 'Hang loose (thumb + pinky)', 'pos': 'Palm facing out', 'tips': 'Shaka sign'},
            'Z': {'desc': 'Index draws Z in air', 'pos': 'Moving', 'tips': 'Draw the letter Z'},
        }
        
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            info = letter_descriptions.get(letter, {})
            signs.append({
                'id': f'letter_{letter}',
                'text': letter,
                'category': 'letter',
                'emoji': '',
                'is_dynamic': letter in ['J', 'Z'],
                'description': info.get('desc', ''),
                'position': info.get('pos', ''),
                'tips': info.get('tips', '')
            })
        
        # Numbers
        for i in range(10):
            signs.append({
                'id': f'number_{i}',
                'text': str(i),
                'category': 'number',
                'emoji': ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣'][i],
                'is_dynamic': False,
                'description': f'The number {i}',
                'position': 'Palm facing out',
                'tips': f'Show {i} fingers'
            })
        
        # Common words
        words = [
            {'id': 'word_hello', 'text': 'Hello', 'emoji': '👋', 'is_dynamic': True,
             'description': 'Wave your hand', 'position': 'Hand near face', 'tips': 'Natural waving motion'},
            {'id': 'word_thanks', 'text': 'Thank You', 'emoji': '🙏', 'is_dynamic': True,
             'description': 'Touch chin and move forward', 'position': 'Start at chin', 'tips': 'Move hand outward'},
            {'id': 'word_please', 'text': 'Please', 'emoji': '🙏', 'is_dynamic': True,
             'description': 'Circular motion on chest', 'position': 'Flat hand on chest', 'tips': 'Clockwise circle'},
            {'id': 'word_yes', 'text': 'Yes', 'emoji': '✅', 'is_dynamic': True,
             'description': 'Nod fist up and down', 'position': 'Fist at chin level', 'tips': 'Like head nodding'},
            {'id': 'word_no', 'text': 'No', 'emoji': '❌', 'is_dynamic': True,
             'description': 'Pinch fingers together', 'position': 'Index and middle to thumb', 'tips': 'Quick snap motion'},
            {'id': 'word_sorry', 'text': 'Sorry', 'emoji': '🙇', 'is_dynamic': True,
             'description': 'Fist circles on chest', 'position': 'Fist on chest', 'tips': 'Circular motion'},
            {'id': 'word_love', 'text': 'I Love You', 'emoji': '🤟', 'is_dynamic': False,
             'description': 'ILY hand shape', 'position': 'Palm out', 'tips': 'Thumb, index, pinky extended'},
            {'id': 'word_help', 'text': 'Help', 'emoji': '🆘', 'is_dynamic': True,
             'description': 'Thumbs up on palm, lift', 'position': 'Fist on flat palm', 'tips': 'Lift upward'},
        ]
        
        for word in words:
            word['category'] = 'word'
            signs.append(word)
        
        return signs
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Main content
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)
        
        title = QLabel("📖 Sign Library")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        main_layout.addLayout(header)
        
        # Search and filter bar
        filter_bar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search signs...")
        self.search_input.setObjectName("input")
        self.search_input.textChanged.connect(self._filter_signs)
        filter_bar.addWidget(self.search_input)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All Categories", "Letters", "Numbers", "Words", "Phrases"])
        self.category_combo.setObjectName("input")
        self.category_combo.currentTextChanged.connect(self._filter_signs)
        filter_bar.addWidget(self.category_combo)
        
        main_layout.addLayout(filter_bar)
        
        # Signs grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        
        self._populate_grid()
        
        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll)
        
        layout.addWidget(main_content, stretch=1)
        
        # Detail panel (hidden by default)
        self.detail_panel = SignDetailPanel()
        self.detail_panel.close_requested.connect(self._hide_detail_panel)
        self.detail_panel.hide()
        layout.addWidget(self.detail_panel)
    
    def _populate_grid(self, signs: list = None):
        """Populate the grid with sign cards."""
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        signs = signs or self._signs_data
        
        for i, sign in enumerate(signs):
            card = SignCard(
                sign['id'],
                sign['text'],
                sign['category'],
                sign.get('description', ''),
                sign.get('emoji', ''),
                sign.get('is_dynamic', False)
            )
            card.clicked.connect(self._show_sign_detail)
            self.grid_layout.addWidget(card, i // 5, i % 5)
    
    def _filter_signs(self):
        """Filter signs based on search and category."""
        search_text = self.search_input.text().lower()
        category = self.category_combo.currentText().lower()
        
        filtered = []
        for sign in self._signs_data:
            # Category filter
            if category != "all categories":
                if category == "letters" and sign['category'] != 'letter':
                    continue
                elif category == "numbers" and sign['category'] != 'number':
                    continue
                elif category == "words" and sign['category'] != 'word':
                    continue
                elif category == "phrases" and sign['category'] != 'phrase':
                    continue
            
            # Search filter
            if search_text:
                if search_text not in sign['text'].lower():
                    if search_text not in sign.get('description', '').lower():
                        continue
            
            filtered.append(sign)
        
        self._populate_grid(filtered)
    
    def _show_sign_detail(self, sign_id: str):
        """Show detail panel for a sign."""
        for sign in self._signs_data:
            if sign['id'] == sign_id:
                self.detail_panel.show_sign(sign)
                self.detail_panel.show()
                break
    
    def _hide_detail_panel(self):
        """Hide the detail panel."""
        self.detail_panel.hide()
