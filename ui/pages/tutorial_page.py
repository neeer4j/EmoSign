"""
Tutorial Page - Interactive ASL Learning Guide

Provides step-by-step tutorials for learning ASL:
- Alphabet lessons with visual hand demonstrations
- Common words and phrases with descriptions
- Practice mode with real-time feedback
- Progress tracking and achievements
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QProgressBar, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS


# Complete ASL alphabet learning data
ASL_LESSON_DATA = {
    'A': {
        'name': 'Letter A',
        'description': 'Fist with thumb resting on the side',
        'detailed_steps': [
            '1. Make a fist with your dominant hand',
            '2. Keep all fingers curled tightly into your palm',
            '3. Rest your thumb against the SIDE of your index finger',
            '4. Do NOT tuck thumb inside fist or point it up',
            '5. Palm should face forward or slightly sideways'
        ],
        'common_mistakes': [
            'Thumb pointing up (that\'s a different sign)',
            'Thumb tucked inside fist (that\'s S)'
        ],
        'emoji': '✊',
        'ascii_art': '''
     ╔═══╗
     ║███║
     ║███╠═╗ ← Thumb on side
     ║███║ ║
     ║███╠═╝
     ╚═══╝'''
    },
    'B': {
        'name': 'Letter B',
        'description': 'Flat hand with fingers together, thumb tucked',
        'detailed_steps': [
            '1. Hold hand flat with palm facing forward',
            '2. Extend all four fingers straight up',
            '3. Press fingers together (no gaps)',
            '4. Fold thumb across your palm',
            '5. Thumb tip should touch your palm'
        ],
        'common_mistakes': [
            'Fingers spread apart',
            'Thumb sticking out to the side'
        ],
        'emoji': '🖐️',
        'ascii_art': '''
     │ │ │ │
     │ │ │ │ ← Fingers straight
     ╔═══════╗
     ║ ═══   ║ ← Thumb across palm
     ╚═══════╝'''
    },
    'C': {
        'name': 'Letter C',
        'description': 'Curved hand like holding a cup',
        'detailed_steps': [
            '1. Curve your hand as if holding a can',
            '2. Keep fingers together in the curve',
            '3. Thumb curves opposite to fingers',
            '4. Hand should form a "C" shape when viewed from side',
            '5. Imagine grasping a tennis ball'
        ],
        'common_mistakes': [
            'Fingers too straight',
            'Thumb touching fingers (that\'s O)'
        ],
        'emoji': '🤏',
        'ascii_art': '''
       ╭───╮
      ╱     ╲
     │       │ ← Open C shape
     │       │
      ╲     ╱
       ╰───╯'''
    },
    'D': {
        'name': 'Letter D',
        'description': 'Index finger up, others form circle with thumb',
        'detailed_steps': [
            '1. Point your index finger straight up',
            '2. Touch middle, ring, and pinky fingertips to thumb tip',
            '3. This creates a circle below the index finger',
            '4. The circle should be round, not pinched',
            '5. Index finger stays pointing up'
        ],
        'common_mistakes': [
            'Other fingers not forming proper circle',
            'Index finger bent'
        ],
        'emoji': '☝️',
        'ascii_art': '''
        │ ← Index pointing up
        │
     ╭──┴──╮
     │  ◯  │ ← Circle with thumb
     ╰─────╯'''
    },
    'E': {
        'name': 'Letter E',
        'description': 'Fingers curled with thumb tucked under',
        'detailed_steps': [
            '1. Curl all fingertips down to touch your palm',
            '2. Tuck your thumb UNDER your fingers',
            '3. Fingertips should be visible from the front',
            '4. It looks like a relaxed fist',
            '5. Palm faces outward'
        ],
        'common_mistakes': [
            'Thumb on top (that\'s S)',
            'Fingers not curled enough'
        ],
        'emoji': '✊',
        'ascii_art': '''
     ╭───────╮
     │ ╭───╮ │
     │ │░░░│ │ ← Fingers curled
     │ ╰═══╯ │ ← Thumb under
     ╚═══════╝'''
    },
    'F': {
        'name': 'Letter F',
        'description': 'OK sign with three fingers extended up',
        'detailed_steps': [
            '1. Touch index fingertip to thumb tip (like OK)',
            '2. This forms a small circle',
            '3. Extend middle, ring, and pinky fingers UP',
            '4. Spread these three fingers slightly',
            '5. Palm faces outward'
        ],
        'common_mistakes': [
            'Three fingers not extended',
            'Circle not formed properly'
        ],
        'emoji': '👌',
        'ascii_art': '''
     │ │ │ ← 3 fingers extended
     │ │ │
     ╭─┴─┴─╮
     │ ◯   │ ← OK circle
     ╰─────╯'''
    },
    'G': {
        'name': 'Letter G',
        'description': 'Pointing hand held horizontally',
        'detailed_steps': [
            '1. Point with index finger SIDEWAYS (horizontal)',
            '2. Extend thumb parallel to index, slightly apart',
            '3. Curl other fingers into palm',
            '4. Like pointing to something beside you',
            '5. Keep hand level, not tilted'
        ],
        'common_mistakes': [
            'Pointing up instead of sideways',
            'Thumb not extended'
        ],
        'emoji': '👉',
        'ascii_art': '''
     ═══════► Index
     ═══════► Thumb
     ╔═════╗
     ║░░░░░║ ← Others tucked
     ╚═════╝'''
    },
    'H': {
        'name': 'Letter H',
        'description': 'Two fingers extended horizontally',
        'detailed_steps': [
            '1. Extend index and middle fingers together',
            '2. Point them SIDEWAYS (horizontal)',
            '3. Keep fingers pressed together',
            '4. Curl other fingers into palm',
            '5. Like G but with two fingers'
        ],
        'common_mistakes': [
            'Fingers pointing up (that\'s U or V)',
            'Fingers spread apart'
        ],
        'emoji': '✌️',
        'ascii_art': '''
     ═══════► Index
     ═══════► Middle
     ╔═════╗
     ║░░░░░║ ← Others tucked
     ╚═════╝'''
    },
    'I': {
        'name': 'Letter I',
        'description': 'Pinky finger extended, others closed',
        'detailed_steps': [
            '1. Make a loose fist',
            '2. Extend ONLY your pinky finger straight up',
            '3. Thumb wraps across front of fingers',
            '4. Keep pinky straight, not bent',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Other fingers extended',
            'Pinky bent'
        ],
        'emoji': '🤙',
        'ascii_art': '''
              │ ← Pinky up
     ╔════════╗
     ║░░░░░░░░║
     ║░░░░░░░░║
     ╚════════╝'''
    },
    'J': {
        'name': 'Letter J',
        'description': 'Pinky traces J shape in the air (MOTION)',
        'detailed_steps': [
            '1. Start in I position (pinky up)',
            '2. Draw a "J" curve in the air with your pinky',
            '3. Move down, then curve toward your body',
            '4. The MOVEMENT is the sign, not just the hand shape',
            '5. End with pinky pointing inward'
        ],
        'common_mistakes': [
            'Forgetting the motion (J requires movement!)',
            'Wrong direction of curve'
        ],
        'emoji': '☝️',
        'ascii_art': '''
     │ ← Start (I position)
     │
     │
     ╰──╮ Curve down
        │ and in
     ←──╯'''
    },
    'K': {
        'name': 'Letter K',
        'description': 'Peace sign with thumb between fingers',
        'detailed_steps': [
            '1. Extend index and middle fingers in a V',
            '2. Place thumb BETWEEN these two fingers',
            '3. Thumb should touch the middle of both fingers',
            '4. Curl ring and pinky fingers',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Thumb not touching both fingers',
            'Thumb on outside (that\'s V)'
        ],
        'emoji': '✌️',
        'ascii_art': '''
     ╲     ╱ ← V shape
      ╲   ╱
       ╲ ╱
     ═══╳═══ ← Thumb between
        │
     ╔══╧══╗'''
    },
    'L': {
        'name': 'Letter L',
        'description': 'L shape with thumb and index finger',
        'detailed_steps': [
            '1. Extend thumb straight out to the side',
            '2. Point index finger straight up',
            '3. This forms a 90-degree angle (L shape)',
            '4. Curl other fingers into palm',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Angle not 90 degrees',
            'Other fingers not curled'
        ],
        'emoji': '👆',
        'ascii_art': '''
        │ ← Index up
        │
     ╔══╧══╗
     ║     ║
     ╚═════╬═══► Thumb out
           │'''
    },
    'M': {
        'name': 'Letter M',
        'description': 'Three fingers over thumb',
        'detailed_steps': [
            '1. Tuck thumb under your fingers',
            '2. Fold index, middle, and ring fingers OVER the thumb',
            '3. Pinky is also tucked',
            '4. You should see THREE bumps (knuckles) on top',
            '5. This is similar to N but with three fingers'
        ],
        'common_mistakes': [
            'Only two fingers over thumb (that\'s N)',
            'Thumb visible from front'
        ],
        'emoji': '✊',
        'ascii_art': '''
     ╭─┬─┬─╮
     │ │ │ │ ← 3 knuckle bumps
     ╞═╧═╧═╡
     ║░░░░░║ ← Thumb under
     ╚═════╝'''
    },
    'N': {
        'name': 'Letter N',
        'description': 'Two fingers over thumb',
        'detailed_steps': [
            '1. Tuck thumb under your fingers',
            '2. Fold ONLY index and middle fingers over thumb',
            '3. Ring and pinky are tucked alongside',
            '4. You should see TWO bumps (knuckles) on top',
            '5. Similar to M but with only two fingers'
        ],
        'common_mistakes': [
            'Three fingers over (that\'s M)',
            'Thumb visible from front'
        ],
        'emoji': '✊',
        'ascii_art': '''
     ╭─┬─╮
     │ │ │  ← 2 knuckle bumps
     ╞═╧═╡
     ║░░░║  ← Thumb under
     ╚═══╝'''
    },
    'O': {
        'name': 'Letter O',
        'description': 'Fingers form O/circle shape',
        'detailed_steps': [
            '1. Curve all your fingers together',
            '2. Touch ALL fingertips to your thumb tip',
            '3. This forms a complete circle/O shape',
            '4. Like gently holding a small ball',
            '5. Palm faces to the side'
        ],
        'common_mistakes': [
            'Not all fingers touching thumb',
            'Circle too open (that\'s C)'
        ],
        'emoji': '👌',
        'ascii_art': '''
       ╭───╮
      ╱     ╲
     │   ◯   │ ← Closed circle
      ╲     ╱
       ╰───╯'''
    },
    'P': {
        'name': 'Letter P',
        'description': 'K shape pointing downward',
        'detailed_steps': [
            '1. Make the K handshape',
            '2. Rotate your hand to point DOWNWARD',
            '3. Middle finger points toward the ground',
            '4. Thumb still between index and middle',
            '5. It\'s just K but upside down'
        ],
        'common_mistakes': [
            'Not pointing down',
            'Wrong hand shape (should match K)'
        ],
        'emoji': '👇',
        'ascii_art': '''
     ╔═════╗
        │
     ═══╳═══ ← Thumb between
       ╱ ╲
      ╱   ╲
     ▼     ▼ ← Points down'''
    },
    'Q': {
        'name': 'Letter Q',
        'description': 'G shape pointing downward',
        'detailed_steps': [
            '1. Make the G handshape',
            '2. Rotate your hand to point DOWNWARD',
            '3. Index finger and thumb point to the ground',
            '4. Like pinching something below you',
            '5. It\'s just G but upside down'
        ],
        'common_mistakes': [
            'Not pointing down',
            'Wrong hand shape (should match G)'
        ],
        'emoji': '👇',
        'ascii_art': '''
     ╔═════╗
     ║░░░░░║
     ╚══╤══╝
        │
        │
        ▼ ← Points down'''
    },
    'R': {
        'name': 'Letter R',
        'description': 'Index and middle fingers crossed',
        'detailed_steps': [
            '1. Extend index and middle fingers',
            '2. CROSS index finger OVER middle finger',
            '3. Like crossing fingers for good luck',
            '4. Other fingers curled into palm',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Middle finger over index (wrong direction)',
            'Fingers not actually crossing'
        ],
        'emoji': '🤞',
        'ascii_art': '''
        ╲│
         ╳ ← Crossed
        │╱
     ╔══╧══╗
     ║░░░░░║
     ╚═════╝'''
    },
    'S': {
        'name': 'Letter S',
        'description': 'Fist with thumb across front',
        'detailed_steps': [
            '1. Make a tight fist',
            '2. Wrap thumb ACROSS the front of your fingers',
            '3. Thumb crosses over the first knuckles',
            '4. Thumb tip near the pinky side',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Thumb on side (that\'s A)',
            'Thumb tucked inside'
        ],
        'emoji': '✊',
        'ascii_art': '''
     ╔═══════╗
     ║░░░░░░░║
     ╠═══════╣ ← Thumb across
     ║░░░░░░░║
     ╚═══════╝'''
    },
    'T': {
        'name': 'Letter T',
        'description': 'Fist with thumb between index and middle',
        'detailed_steps': [
            '1. Make a fist',
            '2. Tuck thumb BETWEEN index and middle fingers',
            '3. Thumb tip should peek out between them',
            '4. Like hiding your thumb between fingers',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Thumb not between fingers',
            'Thumb not visible between them'
        ],
        'emoji': '✊',
        'ascii_art': '''
     ╔═══════╗
     ║░░╔═╗░░║ ← Thumb peeking
     ║░░║▲║░░║
     ║░░╚═╝░░║
     ╚═══════╝'''
    },
    'U': {
        'name': 'Letter U',
        'description': 'Two fingers up and TOGETHER',
        'detailed_steps': [
            '1. Extend index and middle fingers UP',
            '2. Keep them pressed TOGETHER (touching)',
            '3. Curl other fingers and thumb',
            '4. Fingers point straight up',
            '5. This is different from V (spread)'
        ],
        'common_mistakes': [
            'Fingers spread apart (that\'s V)',
            'Fingers pointing sideways (that\'s H)'
        ],
        'emoji': '✌️',
        'ascii_art': '''
     │ │
     │ │ ← Together
     │ │
     ╔═╧═╗
     ║░░░║
     ╚═══╝'''
    },
    'V': {
        'name': 'Letter V',
        'description': 'Peace sign (two fingers SPREAD)',
        'detailed_steps': [
            '1. Extend index and middle fingers UP',
            '2. SPREAD them apart in a V shape',
            '3. Clear gap between the fingers',
            '4. Classic "peace sign"',
            '5. This is different from U (together)'
        ],
        'common_mistakes': [
            'Fingers together (that\'s U)',
            'Thumb not tucked'
        ],
        'emoji': '✌️',
        'ascii_art': '''
     ╲   ╱
      ╲ ╱  ← Spread apart
       V
     ╔═╧═╗
     ║░░░║
     ╚═══╝'''
    },
    'W': {
        'name': 'Letter W',
        'description': 'Three fingers extended and spread',
        'detailed_steps': [
            '1. Extend index, middle, and ring fingers UP',
            '2. SPREAD all three fingers apart',
            '3. Clear gaps between each finger',
            '4. Thumb holds pinky down',
            '5. Like showing number "3"'
        ],
        'common_mistakes': [
            'Fingers not spread',
            'Only two fingers (that\'s V)'
        ],
        'emoji': '🖖',
        'ascii_art': '''
     ╲ │ ╱
      ╲│╱  ← 3 spread fingers
     ╔═╧═╗
     ║░░░║
     ╚═══╝'''
    },
    'X': {
        'name': 'Letter X',
        'description': 'Hooked/bent index finger',
        'detailed_steps': [
            '1. Make a fist',
            '2. Extend only your index finger',
            '3. BEND index finger at both knuckles',
            '4. It should look like a hook',
            '5. Like a crooked finger'
        ],
        'common_mistakes': [
            'Index finger straight (that\'s D)',
            'Other fingers extended'
        ],
        'emoji': '☝️',
        'ascii_art': '''
     ╭───╮
     │   │
     ╰───┤ ← Hooked index
     ╔═══╗
     ║░░░║
     ╚═══╝'''
    },
    'Y': {
        'name': 'Letter Y',
        'description': 'Hang loose - thumb and pinky out',
        'detailed_steps': [
            '1. Curl middle three fingers into palm',
            '2. Extend thumb OUT to one side',
            '3. Extend pinky OUT to the other side',
            '4. Classic "hang loose" or shaka sign',
            '5. Spread thumb and pinky wide'
        ],
        'common_mistakes': [
            'Middle fingers not curled',
            'Thumb or pinky not extended'
        ],
        'emoji': '🤙',
        'ascii_art': '''
               │ ← Pinky
     ╔═════════╗
     ║░░░░░░░░░║
     ╚═════════╝
     │ ← Thumb'''
    },
    'Z': {
        'name': 'Letter Z',
        'description': 'Index finger draws Z in air (MOTION)',
        'detailed_steps': [
            '1. Point with index finger',
            '2. Draw the letter Z in the air:',
            '   - Line across to the right',
            '   - Diagonal down-left',
            '   - Line across to the right',
            '3. The MOVEMENT is the sign!'
        ],
        'common_mistakes': [
            'Forgetting the motion (Z requires movement!)',
            'Drawing Z backwards'
        ],
        'emoji': '👆',
        'ascii_art': '''
     ━━━━━━►  Step 1: across
           ╲
            ╲ Step 2: diagonal
     ━━━━━━►  Step 3: across
     
     Draw Z in the air!'''
    },
}


class LessonCard(QFrame):
    """A card representing a lesson."""
    
    clicked = Signal(str)  # lesson_id
    
    def __init__(self, lesson_id: str, title: str, description: str,
                 icon: str, progress: int = 0, parent=None):
        super().__init__(parent)
        self.lesson_id = lesson_id
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(160)
        self._setup_ui(title, description, icon, progress)
    
    def _setup_ui(self, title, description, icon, progress):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Icon and title row
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setValue(progress)
        progress_bar.setFixedHeight(6)
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(progress_bar)
        
        # Progress text
        progress_text = QLabel(f"{progress}% Complete")
        progress_text.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent;")
        layout.addWidget(progress_text)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.lesson_id)


class AlphabetLesson(QWidget):
    """Interactive alphabet learning lesson with visual demonstrations."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_letter_index = 0
        self.letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back to Lessons")
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)
        
        title = QLabel("🔤 Learn the ASL Alphabet")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        # Letter indicator
        self.letter_indicator = QLabel("A")
        self.letter_indicator.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['primary']};
            background: {COLORS['primary']}20;
            padding: 4px 12px;
            border-radius: 8px;
        """)
        header.addWidget(self.letter_indicator)
        
        layout.addLayout(header)
        
        # Progress bar
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(26)
        self.progress_bar.setValue(1)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 4px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_text = QLabel("1/26")
        self.progress_text.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        progress_layout.addWidget(self.progress_text)
        
        layout.addLayout(progress_layout)
        
        # Main content - scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Left side: Letter display and ASCII art
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignCenter)
        left_layout.setSpacing(16)
        
        # Large letter
        self.letter_label = QLabel("A")
        self.letter_label.setStyleSheet(f"""
            font-size: 100px;
            font-weight: 700;
            color: {COLORS['primary']};
            background: transparent;
        """)
        self.letter_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.letter_label)
        
        # Emoji representation
        self.emoji_label = QLabel("✊")
        self.emoji_label.setStyleSheet("font-size: 48px; background: transparent;")
        self.emoji_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.emoji_label)
        
        # ASCII art display
        self.ascii_frame = QFrame()
        self.ascii_frame.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            border-radius: 12px;
            padding: 12px;
        """)
        ascii_layout = QVBoxLayout(self.ascii_frame)
        
        self.ascii_label = QLabel()
        self.ascii_label.setStyleSheet(f"""
            font-family: Consolas, 'Courier New', monospace;
            font-size: 13px;
            color: {COLORS['primary']};
            background: transparent;
        """)
        self.ascii_label.setAlignment(Qt.AlignCenter)
        ascii_layout.addWidget(self.ascii_label)
        
        left_layout.addWidget(self.ascii_frame)
        
        # Brief description
        self.brief_desc = QLabel("Fist with thumb on side")
        self.brief_desc.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_secondary']};
            background: transparent;
            text-align: center;
        """)
        self.brief_desc.setAlignment(Qt.AlignCenter)
        self.brief_desc.setWordWrap(True)
        left_layout.addWidget(self.brief_desc)
        
        content_layout.addWidget(left_panel)
        
        # Right side: Instructions
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)
        
        # Steps title
        steps_title = QLabel("📝 How to Sign This Letter")
        steps_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        right_layout.addWidget(steps_title)
        
        # Step-by-step instructions
        self.steps_label = QLabel()
        self.steps_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            background: transparent;
            line-height: 1.8;
        """)
        self.steps_label.setWordWrap(True)
        right_layout.addWidget(self.steps_label)
        
        # Common mistakes
        mistakes_title = QLabel("⚠️ Common Mistakes to Avoid")
        mistakes_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['warning']};
            background: transparent;
            margin-top: 12px;
        """)
        right_layout.addWidget(mistakes_title)
        
        self.mistakes_label = QLabel()
        self.mistakes_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_muted']};
            background: {COLORS['warning']}15;
            padding: 12px;
            border-radius: 8px;
        """)
        self.mistakes_label.setWordWrap(True)
        right_layout.addWidget(self.mistakes_label)
        
        # Practice tip
        practice_frame = QFrame()
        practice_frame.setStyleSheet(f"""
            background: {COLORS['primary']}15;
            border-radius: 8px;
            padding: 8px;
        """)
        practice_layout = QVBoxLayout(practice_frame)
        
        practice_title = QLabel("💡 Practice Tip")
        practice_title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['primary']};
            background: transparent;
        """)
        practice_layout.addWidget(practice_title)
        
        practice_text = QLabel("Try signing this letter in the Live Translation page to see if the camera recognizes it!")
        practice_text.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        practice_text.setWordWrap(True)
        practice_layout.addWidget(practice_text)
        
        right_layout.addWidget(practice_frame)
        right_layout.addStretch()
        
        content_layout.addWidget(right_panel, 1)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll, 1)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("← Previous Letter")
        self.prev_btn.setObjectName("secondaryButton")
        self.prev_btn.clicked.connect(self._prev_letter)
        nav_layout.addWidget(self.prev_btn)
        
        nav_layout.addStretch()
        
        # Quick jump
        quick_jump = QLabel("Quick jump:")
        quick_jump.setStyleSheet(f"color: {COLORS['text_muted']};")
        nav_layout.addWidget(quick_jump)
        
        # Letter buttons for quick navigation
        for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            btn = QPushButton(letter)
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_input']};
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {COLORS['primary']};
                    color: {COLORS['text_primary']};
                }}
            """)
            btn.clicked.connect(lambda checked, idx=i: self._jump_to_letter(idx))
            nav_layout.addWidget(btn)
        
        nav_layout.addStretch()
        
        self.next_btn = QPushButton("Next Letter →")
        self.next_btn.setObjectName("primaryButton")
        self.next_btn.clicked.connect(self._next_letter)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Initialize display
        self._update_display()
    
    def _update_display(self):
        """Update the display for the current letter."""
        letter = self.letters[self.current_letter_index]
        data = ASL_LESSON_DATA.get(letter, {})
        
        # Update letter display
        self.letter_label.setText(letter)
        self.letter_indicator.setText(f"{letter} - {data.get('name', letter)}")
        self.emoji_label.setText(data.get('emoji', '✋'))
        
        # Update ASCII art
        self.ascii_label.setText(data.get('ascii_art', ''))
        
        # Update description
        self.brief_desc.setText(data.get('description', ''))
        
        # Update steps
        steps = data.get('detailed_steps', [])
        self.steps_label.setText('\n'.join(steps))
        
        # Update mistakes
        mistakes = data.get('common_mistakes', [])
        mistakes_text = '\n'.join([f"• {m}" for m in mistakes])
        self.mistakes_label.setText(mistakes_text)
        
        # Update progress
        self.progress_bar.setValue(self.current_letter_index + 1)
        self.progress_text.setText(f"{self.current_letter_index + 1}/26")
        
        # Update navigation buttons
        self.prev_btn.setEnabled(self.current_letter_index > 0)
        self.next_btn.setText("Complete ✓" if self.current_letter_index == 25 else "Next Letter →")
    
    def _prev_letter(self):
        if self.current_letter_index > 0:
            self.current_letter_index -= 1
            self._update_display()
    
    def _next_letter(self):
        if self.current_letter_index < 25:
            self.current_letter_index += 1
            self._update_display()
        else:
            # Completed!
            self.back_requested.emit()
    
    def _jump_to_letter(self, index: int):
        self.current_letter_index = index
        self._update_display()


class NumbersLesson(QWidget):
    """Numbers 0-9 learning lesson."""
    
    back_requested = Signal()
    
    NUMBERS_DATA = {
        '0': {'desc': 'All fingers form O shape (same as letter O)', 'emoji': '👌'},
        '1': {'desc': 'Index finger pointing up', 'emoji': '☝️'},
        '2': {'desc': 'Peace sign (index and middle up, spread)', 'emoji': '✌️'},
        '3': {'desc': 'Thumb, index, and middle up', 'emoji': '🤟'},
        '4': {'desc': 'Four fingers up, thumb tucked', 'emoji': '🖐️'},
        '5': {'desc': 'All five fingers spread open', 'emoji': '🖐️'},
        '6': {'desc': 'Pinky and thumb touching, others up', 'emoji': '🤙'},
        '7': {'desc': 'Ring finger and thumb touching, others up', 'emoji': '🖐️'},
        '8': {'desc': 'Middle finger and thumb touching, others up', 'emoji': '🖐️'},
        '9': {'desc': 'Index and thumb touching, others up', 'emoji': '👌'},
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("← Back to Lessons")
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)
        
        title = QLabel("🔢 Numbers 0-9")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Numbers grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)
        grid.setSpacing(16)
        
        for i, (num, data) in enumerate(self.NUMBERS_DATA.items()):
            card = QFrame()
            card.setObjectName("card")
            card.setFixedHeight(150)
            card_layout = QVBoxLayout(card)
            card_layout.setAlignment(Qt.AlignCenter)
            
            emoji = QLabel(data['emoji'])
            emoji.setStyleSheet("font-size: 36px; background: transparent;")
            emoji.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(emoji)
            
            num_label = QLabel(num)
            num_label.setStyleSheet(f"""
                font-size: 48px;
                font-weight: bold;
                color: {COLORS['primary']};
                background: transparent;
            """)
            num_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(num_label)
            
            desc = QLabel(data['desc'])
            desc.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS['text_secondary']};
                background: transparent;
            """)
            desc.setAlignment(Qt.AlignCenter)
            desc.setWordWrap(True)
            card_layout.addWidget(desc)
            
            grid.addWidget(card, i // 5, i % 5)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)


class TutorialPage(QWidget):
    """Main tutorial and learning page."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
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
        
        title = QLabel("📚 Learn Sign Language")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Stacked widget for lessons
        self.stack = QStackedWidget()
        
        # Main lesson list
        self.lesson_list = self._create_lesson_list()
        self.stack.addWidget(self.lesson_list)
        
        # Alphabet lesson
        self.alphabet_lesson = AlphabetLesson()
        self.alphabet_lesson.back_requested.connect(self._show_lesson_list)
        self.stack.addWidget(self.alphabet_lesson)
        
        # Numbers lesson
        self.numbers_lesson = NumbersLesson()
        self.numbers_lesson.back_requested.connect(self._show_lesson_list)
        self.stack.addWidget(self.numbers_lesson)
        
        layout.addWidget(self.stack)
    
    def _create_lesson_list(self) -> QWidget:
        """Create the main lesson list."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Welcome message
        welcome = QFrame()
        welcome.setObjectName("card")
        welcome_layout = QVBoxLayout(welcome)
        
        welcome_title = QLabel("👋 Welcome to ASL Learning!")
        welcome_title.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {COLORS['text_primary']};")
        welcome_layout.addWidget(welcome_title)
        
        welcome_text = QLabel(
            "Learn American Sign Language through interactive lessons with visual demonstrations. "
            "Each lesson shows you exactly how to form each sign with step-by-step instructions. "
            "Start with the alphabet and work your way up to common phrases!"
        )
        welcome_text.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.5;")
        welcome_text.setWordWrap(True)
        welcome_layout.addWidget(welcome_text)
        
        layout.addWidget(welcome)
        
        # Lesson categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # Beginner lessons
        beginner_label = QLabel("🌱 Beginner - Start Here")
        beginner_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};")
        scroll_layout.addWidget(beginner_label)
        
        lessons_grid = QGridLayout()
        lessons_grid.setSpacing(16)
        
        lessons = [
            ("alphabet", "The ASL Alphabet", "Learn A-Z fingerspelling with visual guides for each letter", "🔤", 0),
            ("numbers", "Numbers 0-9", "Count from zero to nine in ASL", "🔢", 0),
            ("greetings", "Greetings", "Hello, goodbye, nice to meet you", "👋", 0),
            ("basics", "Basic Words", "Yes, no, please, thank you, sorry", "💬", 0),
        ]
        
        for i, (lid, title, desc, icon, progress) in enumerate(lessons):
            card = LessonCard(lid, title, desc, icon, progress)
            card.clicked.connect(self._open_lesson)
            lessons_grid.addWidget(card, i // 2, i % 2)
        
        scroll_layout.addLayout(lessons_grid)
        
        # Intermediate lessons
        inter_label = QLabel("📈 Intermediate")
        inter_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};")
        scroll_layout.addWidget(inter_label)
        
        inter_lessons = [
            ("questions", "Question Words", "What, where, when, why, how, who", "❓", 0),
            ("emotions", "Emotions", "Happy, sad, angry, scared, excited", "😊", 0),
            ("family", "Family", "Mom, dad, sister, brother, baby", "👨‍👩‍👧‍👦", 0),
            ("actions", "Common Actions", "Go, stop, help, want, need, like", "🏃", 0),
        ]
        
        inter_grid = QGridLayout()
        inter_grid.setSpacing(16)
        
        for i, (lid, title, desc, icon, progress) in enumerate(inter_lessons):
            card = LessonCard(lid, title, desc, icon, progress)
            card.clicked.connect(self._open_lesson)
            inter_grid.addWidget(card, i // 2, i % 2)
        
        scroll_layout.addLayout(inter_grid)
        
        # Tips section
        tips_frame = QFrame()
        tips_frame.setObjectName("card")
        tips_layout = QVBoxLayout(tips_frame)
        
        tips_title = QLabel("💡 Learning Tips")
        tips_title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['primary']};")
        tips_layout.addWidget(tips_title)
        
        tips = [
            "• Practice each sign multiple times until it feels natural",
            "• Use the Live Translation feature to check if your signs are recognized",
            "• Pay attention to hand orientation - it matters!",
            "• Some letters (J, Z) require motion - practice the movement",
            "• Learn similar letters together (M/N, U/V, A/S/E) to spot differences"
        ]
        tips_text = QLabel('\n'.join(tips))
        tips_text.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.6;")
        tips_text.setWordWrap(True)
        tips_layout.addWidget(tips_text)
        
        scroll_layout.addWidget(tips_frame)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _open_lesson(self, lesson_id: str):
        """Open a specific lesson."""
        if lesson_id == "alphabet":
            self.alphabet_lesson.current_letter_index = 0
            self.alphabet_lesson._update_display()
            self.stack.setCurrentWidget(self.alphabet_lesson)
        elif lesson_id == "numbers":
            self.stack.setCurrentWidget(self.numbers_lesson)
        # Other lessons would be added here
    
    def _show_lesson_list(self):
        """Return to the lesson list."""
        self.stack.setCurrentWidget(self.lesson_list)
