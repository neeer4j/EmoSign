"""
Conversation Mode - Two-way communication support

Enables back-and-forth conversations between:
- Sign language users (signing to text)
- Non-signers (typing/speaking to sign visualization)

Features:
- Conversation thread display
- Turn-based communication
- Clear finger-status diagram for each ASL letter
- Animated letter-by-letter playback
- Quick responses
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QTextEdit,
    QSizePolicy, QGraphicsDropShadowEffect, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS
from ui.pages.tutorial_page import ASL_LESSON_DATA


# ─── Beginner-friendly sign data for each ASL letter ───
# 'imagine': an everyday analogy anyone can understand
# 'fingers': [thumb, index, middle, ring, pinky]
#   3 = fully extended (tall green bar)
#   2 = partially out / sideways (medium orange bar)
#   1 = slightly bent / hooked (short yellow bar)
#   0 = fully closed / curled in (tiny gray bar)
# 'do_this': 3 dead-simple steps written for a 10 year old
# 'motion': optional movement instruction
SIGN_GUIDE = {
    'A': {
        'emoji': '✊',
        'imagine': 'Like making a fist to knock on a door',
        'fingers': [2, 0, 0, 0, 0],
        'do_this': [
            '1️⃣  Close all your fingers into a tight fist',
            '2️⃣  Rest your thumb on the SIDE of your fist (not on top)',
            '3️⃣  Face your fist forward — done!',
        ],
    },
    'B': {
        'emoji': '🖐️',
        'imagine': 'Like a flat "stop" hand — all fingers straight up',
        'fingers': [0, 3, 3, 3, 3],
        'do_this': [
            '1️⃣  Hold your hand up with ALL 4 fingers pointing straight up',
            '2️⃣  Keep fingers together (touching side by side)',
            '3️⃣  Fold your thumb down across your palm',
        ],
    },
    'C': {
        'emoji': '🤏',
        'imagine': 'Like holding a cup or a tennis ball — hand curved',
        'fingers': [2, 2, 2, 2, 2],
        'do_this': [
            '1️⃣  Curve all your fingers like you\'re grabbing a cup',
            '2️⃣  Curve your thumb too — it should face your fingers',
            '3️⃣  Your hand should look like the letter C from the side',
        ],
    },
    'D': {
        'emoji': '☝️',
        'imagine': 'Like pointing up — but the other fingers make an "O"',
        'fingers': [1, 3, 0, 0, 0],
        'do_this': [
            '1️⃣  Point your INDEX finger straight up',
            '2️⃣  Curl middle, ring, and pinky fingers down',
            '3️⃣  Touch your thumb tip to the curled fingers (makes a circle)',
        ],
    },
    'E': {
        'emoji': '✊',
        'imagine': 'Like a soft fist — fingers curled, thumb tucked below',
        'fingers': [0, 0, 0, 0, 0],
        'do_this': [
            '1️⃣  Curl ALL your fingers down (like a loose fist)',
            '2️⃣  Tuck your thumb UNDER your curled fingers',
            '3️⃣  Fingertips should almost touch your palm',
        ],
    },
    'F': {
        'emoji': '👌',
        'imagine': 'Like the "OK" sign — thumb and index make a circle',
        'fingers': [1, 0, 3, 3, 3],
        'do_this': [
            '1️⃣  Touch your THUMB tip to your INDEX fingertip (makes a circle)',
            '2️⃣  Stick the other 3 fingers (middle, ring, pinky) STRAIGHT UP',
            '3️⃣  Keep those 3 fingers spread slightly apart',
        ],
    },
    'G': {
        'emoji': '👉',
        'imagine': 'Like a finger gun pointing sideways',
        'fingers': [2, 2, 0, 0, 0],
        'do_this': [
            '1️⃣  Point your INDEX finger SIDEWAYS (to the left)',
            '2️⃣  Extend your thumb parallel above it (like a finger gun)',
            '3️⃣  Curl the other 3 fingers into your palm',
        ],
    },
    'H': {
        'emoji': '✌️',
        'imagine': 'Like a peace sign, but pointing sideways',
        'fingers': [0, 2, 2, 0, 0],
        'do_this': [
            '1️⃣  Extend INDEX + MIDDLE fingers SIDEWAYS (pointing left)',
            '2️⃣  Keep them together (touching side by side)',
            '3️⃣  Curl ring, pinky, and tuck thumb underneath',
        ],
    },
    'I': {
        'emoji': '🤙',
        'imagine': 'Like a fist, but your PINKY sticks up alone',
        'fingers': [0, 0, 0, 0, 3],
        'do_this': [
            '1️⃣  Make a fist',
            '2️⃣  Stick ONLY your PINKY finger straight up',
            '3️⃣  Thumb wraps across the front of your fist',
        ],
    },
    'J': {
        'emoji': '🤙',
        'imagine': 'Start like "I" (pinky up), then draw a J in the air',
        'fingers': [0, 0, 0, 0, 3],
        'do_this': [
            '1️⃣  Make the letter I (fist with pinky up)',
            '2️⃣  Move your hand DOWN, then CURVE it toward you',
            '3️⃣  Your pinky traces the shape of the letter J!',
        ],
        'motion': '↓ Move hand down, then curve inward — drawing a J with your pinky',
    },
    'K': {
        'emoji': '✌️',
        'imagine': 'Like a peace/V sign, but thumb is wedged between the fingers',
        'fingers': [2, 3, 3, 0, 0],
        'do_this': [
            '1️⃣  Hold INDEX + MIDDLE fingers up in a V shape',
            '2️⃣  Wedge your THUMB between those two fingers',
            '3️⃣  Curl ring + pinky into your palm',
        ],
    },
    'L': {
        'emoji': '👆',
        'imagine': 'Make an "L" shape — like a right angle with your hand',
        'fingers': [2, 3, 0, 0, 0],
        'do_this': [
            '1️⃣  Point your INDEX finger straight UP',
            '2️⃣  Stick your THUMB straight OUT to the side',
            '3️⃣  These two fingers make an L shape (90° angle)!',
        ],
    },
    'M': {
        'emoji': '✊',
        'imagine': 'Like a fist, but three fingers fold OVER the thumb',
        'fingers': [0, 0, 0, 0, 0],
        'do_this': [
            '1️⃣  Tuck your THUMB into your palm',
            '2️⃣  Fold INDEX, MIDDLE, and RING fingers over the thumb',
            '3️⃣  Your thumb peeks out under your pinky',
        ],
    },
    'N': {
        'emoji': '✊',
        'imagine': 'Like M, but only TWO fingers fold over the thumb',
        'fingers': [0, 0, 0, 0, 0],
        'do_this': [
            '1️⃣  Tuck your THUMB into your palm',
            '2️⃣  Fold only INDEX and MIDDLE fingers over the thumb',
            '3️⃣  Your thumb peeks out between middle and ring fingers',
        ],
    },
    'O': {
        'emoji': '👌',
        'imagine': 'Make a circle — like your mouth when you say "Oh!"',
        'fingers': [1, 1, 1, 1, 1],
        'do_this': [
            '1️⃣  Touch ALL your fingertips to your thumb tip',
            '2️⃣  This makes a round O shape',
            '3️⃣  Keep it nice and round, not flat',
        ],
    },
    'P': {
        'emoji': '👇',
        'imagine': 'Like the letter K, but pointing downward',
        'fingers': [2, 2, 2, 0, 0],
        'do_this': [
            '1️⃣  Make the letter K (V + thumb between)',
            '2️⃣  Now tilt your whole hand DOWNWARD',
            '3️⃣  Your fingers should point toward the ground',
        ],
    },
    'Q': {
        'emoji': '👇',
        'imagine': 'Like the letter G, but pointing downward',
        'fingers': [2, 2, 0, 0, 0],
        'do_this': [
            '1️⃣  Make the letter G (index + thumb pointing)',
            '2️⃣  Now point your whole hand DOWNWARD',
            '3️⃣  Thumb + index point toward the ground',
        ],
    },
    'R': {
        'emoji': '🤞',
        'imagine': 'Cross your fingers — like wishing for good luck!',
        'fingers': [0, 3, 3, 0, 0],
        'do_this': [
            '1️⃣  Hold up INDEX + MIDDLE fingers',
            '2️⃣  CROSS your index finger over your middle finger',
            '3️⃣  Like you\'re crossing fingers for good luck!',
        ],
    },
    'S': {
        'emoji': '✊',
        'imagine': 'A tight fist — thumb wraps across the front',
        'fingers': [2, 0, 0, 0, 0],
        'do_this': [
            '1️⃣  Make a tight FIST',
            '2️⃣  Wrap your thumb across the FRONT of your fingers',
            '3️⃣  Thumb sits on top of index + middle fingers',
        ],
    },
    'T': {
        'emoji': '✊',
        'imagine': 'Like a fist, but thumb peeks between index and middle',
        'fingers': [1, 0, 0, 0, 0],
        'do_this': [
            '1️⃣  Make a FIST',
            '2️⃣  Poke your THUMB between index and middle fingers',
            '3️⃣  Just the tip of the thumb should peek through',
        ],
    },
    'U': {
        'emoji': '✌️',
        'imagine': 'Two fingers up and TOGETHER — like a peace sign but closed',
        'fingers': [0, 3, 3, 0, 0],
        'do_this': [
            '1️⃣  Hold INDEX + MIDDLE fingers straight UP',
            '2️⃣  Keep them TOGETHER (touching each other)',
            '3️⃣  Curl ring + pinky down, tuck thumb',
        ],
    },
    'V': {
        'emoji': '✌️',
        'imagine': 'Peace sign / Victory sign!',
        'fingers': [0, 3, 3, 0, 0],
        'do_this': [
            '1️⃣  Hold INDEX + MIDDLE fingers straight UP',
            '2️⃣  Spread them APART (making a V shape)',
            '3️⃣  Curl ring + pinky down, tuck thumb',
        ],
    },
    'W': {
        'emoji': '🖖',
        'imagine': 'Like showing the number 3 with your hand',
        'fingers': [0, 3, 3, 3, 0],
        'do_this': [
            '1️⃣  Hold INDEX + MIDDLE + RING fingers UP',
            '2️⃣  Spread them apart from each other',
            '3️⃣  Curl your PINKY down, tuck thumb over it',
        ],
    },
    'X': {
        'emoji': '☝️',
        'imagine': 'Point your index up, then bend it into a hook',
        'fingers': [0, 1, 0, 0, 0],
        'do_this': [
            '1️⃣  Make a fist',
            '2️⃣  Raise your INDEX finger but BEND/HOOK it',
            '3️⃣  It should look like a hook or claw',
        ],
    },
    'Y': {
        'emoji': '🤙',
        'imagine': 'Hang loose / Shaka! Thumb and pinky out — surfer wave!',
        'fingers': [3, 0, 0, 0, 3],
        'do_this': [
            '1️⃣  Make a fist with your middle 3 fingers',
            '2️⃣  Stick your THUMB out to one side',
            '3️⃣  Stick your PINKY out to the other side — 🤙 hang loose!',
        ],
    },
    'Z': {
        'emoji': '👆',
        'imagine': 'Point your index finger and draw the letter Z in the air',
        'fingers': [0, 3, 0, 0, 0],
        'do_this': [
            '1️⃣  Point your INDEX finger straight up',
            '2️⃣  Draw a Z in the air: go RIGHT → then diagonal DOWN-LEFT ↙ → then RIGHT again →',
            '3️⃣  It\'s like writing a Z with your fingertip!',
        ],
        'motion': '→ ↙ →  Draw the letter Z in the air with your index finger',
    },
}


class MessageBubble(QFrame):
    """A chat message bubble."""
    
    def __init__(self, text: str, is_user: bool, timestamp: str = "",
                 message_type: str = "text", parent=None):
        super().__init__(parent)
        
        # Styling based on sender
        if is_user:
            bg_color = COLORS['primary']
            text_color = "#ffffff"
            align = Qt.AlignRight
            margin = "0 0 0 60px"
        else:
            bg_color = COLORS['bg_card']
            text_color = COLORS['text_primary']
            align = Qt.AlignLeft
            margin = "0 60px 0 0"
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 16px;
                margin: {margin};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Message type indicator
        if message_type == "sign":
            type_label = QLabel("✋ Signed")
            type_label.setStyleSheet(f"color: {text_color}; font-size: 10px; opacity: 0.7;")
            layout.addWidget(type_label)
        elif message_type == "voice":
            type_label = QLabel("🎤 Spoken")
            type_label.setStyleSheet(f"color: {text_color}; font-size: 10px; opacity: 0.7;")
            layout.addWidget(type_label)
        
        # Message text
        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 15px;
            background: transparent;
        """)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        # Timestamp
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(f"color: {text_color}; font-size: 10px; opacity: 0.6;")
            time_label.setAlignment(Qt.AlignRight)
            layout.addWidget(time_label)


class QuickReplyButton(QPushButton):
    """A quick reply button."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                color: {COLORS['text_primary']};
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_card_hover']};
                border-color: {COLORS['primary']};
            }}
        """)


class SignCard(QFrame):
    """A beginner-friendly sign instruction card.
    
    Designed for people with ZERO sign language knowledge:
    - Big emoji + letter at top
    - "Imagine..." everyday analogy (like "knocking on a door")
    - Visual bar chart of finger positions (tall=up, short=down)
    - Color-coded: green=open, orange=halfway, yellow=bent, gray=closed
    - 3 simple numbered steps a child could follow
    - Motion instruction for J, Z
    """

    FINGER_NAMES = ['👍\nThumb', '☝️\nIndex', '🖐️\nMiddle', '💍\nRing', '🤙\nPinky']
    # Bar heights for each level (0-3), colors, and simple labels
    BAR_CONFIG = {
        0: {'height': 14, 'color': '#78909C', 'label': 'Closed',  'bg': '#78909C'},
        1: {'height': 30, 'color': '#FFC107', 'label': 'Bent',    'bg': '#FFC107'},
        2: {'height': 50, 'color': '#FF9800', 'label': 'Halfway', 'bg': '#FF9800'},
        3: {'height': 70, 'color': '#4CAF50', 'label': 'Open',    'bg': '#4CAF50'},
    }

    def __init__(self, letter: str = '', parent=None):
        super().__init__(parent)
        self.letter = letter.upper()
        self.setObjectName("signCard")
        self.setStyleSheet(f"""
            QFrame#signCard {{
                background: {COLORS['bg_input']};
                border-radius: 16px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)

        # ── Row 1: Big emoji + letter ──
        top_row = QHBoxLayout()
        top_row.setAlignment(Qt.AlignCenter)
        self._emoji_lbl = QLabel()
        self._emoji_lbl.setStyleSheet("font-size: 52px; background: transparent;")
        self._emoji_lbl.setAlignment(Qt.AlignCenter)
        top_row.addWidget(self._emoji_lbl)
        self._letter_lbl = QLabel()
        self._letter_lbl.setStyleSheet(f"""
            font-size: 60px; font-weight: 900;
            color: {COLORS['primary']}; background: transparent;
        """)
        self._letter_lbl.setAlignment(Qt.AlignCenter)
        top_row.addWidget(self._letter_lbl)
        layout.addLayout(top_row)

        # ── Row 2: "Imagine..." analogy ──
        self._imagine_lbl = QLabel()
        self._imagine_lbl.setAlignment(Qt.AlignCenter)
        self._imagine_lbl.setWordWrap(True)
        self._imagine_lbl.setStyleSheet(f"""
            font-size: 16px; font-weight: 700;
            color: {COLORS['text_primary']};
            background: {COLORS['primary']}12;
            padding: 10px 16px;
            border-radius: 12px;
        """)
        layout.addWidget(self._imagine_lbl)

        # ── Row 3: Visual finger bars (bar-chart style) ──
        bar_frame = QFrame()
        bar_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border-radius: 14px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        bar_layout = QHBoxLayout(bar_frame)
        bar_layout.setContentsMargins(12, 14, 12, 10)
        bar_layout.setSpacing(8)

        self._bar_columns = []
        for i in range(5):
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

            # The bar itself (colored rectangle)
            bar = QFrame()
            bar.setFixedWidth(36)
            bar.setFixedHeight(14)
            bar.setStyleSheet(f"""
                background: #78909C;
                border-radius: 6px;
            """)
            col.addWidget(bar, alignment=Qt.AlignHCenter)

            # State label under the bar
            state_lbl = QLabel("Closed")
            state_lbl.setAlignment(Qt.AlignCenter)
            state_lbl.setStyleSheet(f"""
                font-size: 9px; font-weight: 800;
                color: #78909C; background: transparent;
            """)
            col.addWidget(state_lbl)

            # Finger name with emoji (below)
            name_lbl = QLabel(self.FINGER_NAMES[i])
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(f"""
                font-size: 10px; font-weight: 600;
                color: {COLORS['text_muted']}; background: transparent;
            """)
            col.addWidget(name_lbl)

            bar_layout.addLayout(col)
            self._bar_columns.append({'bar': bar, 'state_lbl': state_lbl})

        layout.addWidget(bar_frame)

        # ── Row 4: Legend (tiny, one line) ──
        legend = QLabel(
            '<span style="color:#4CAF50">🟩 Open</span> &nbsp; '
            '<span style="color:#FF9800">🟧 Halfway</span> &nbsp; '
            '<span style="color:#FFC107">🟨 Bent</span> &nbsp; '
            '<span style="color:#78909C">⬜ Closed</span>'
        )
        legend.setTextFormat(Qt.RichText)
        legend.setAlignment(Qt.AlignCenter)
        legend.setStyleSheet(f"font-size: 10px; color: {COLORS['text_muted']}; background: transparent;")
        layout.addWidget(legend)

        # ── Row 5: Step-by-step (numbered cards) ──
        self._steps_container = QVBoxLayout()
        self._steps_container.setSpacing(4)
        self._step_labels = []
        for _ in range(3):
            step = QLabel()
            step.setWordWrap(True)
            step.setStyleSheet(f"""
                font-size: 14px;
                color: {COLORS['text_primary']};
                background: {COLORS['bg_card']};
                padding: 8px 14px;
                border-radius: 10px;
                border-left: 4px solid {COLORS['primary']};
            """)
            self._steps_container.addWidget(step)
            self._step_labels.append(step)
        layout.addLayout(self._steps_container)

        # ── Row 6: Motion indicator (for J, Z) ──
        self._motion_lbl = QLabel()
        self._motion_lbl.setAlignment(Qt.AlignCenter)
        self._motion_lbl.setWordWrap(True)
        self._motion_lbl.setStyleSheet(f"""
            font-size: 15px; font-weight: 700;
            color: white;
            background: {COLORS['primary']};
            padding: 10px 16px;
            border-radius: 12px;
        """)
        self._motion_lbl.hide()
        layout.addWidget(self._motion_lbl)

        if self.letter:
            self._update()

    def set_letter(self, letter: str):
        self.letter = letter.upper()
        self._update()

    def _update(self):
        info = SIGN_GUIDE.get(self.letter)
        if not info:
            self._emoji_lbl.setText("❓")
            self._letter_lbl.setText(self.letter)
            self._imagine_lbl.setText(f"No guide available for '{self.letter}'")
            for col in self._bar_columns:
                col['bar'].setFixedHeight(14)
                col['bar'].setStyleSheet("background: #78909C; border-radius: 6px;")
                col['state_lbl'].setText("—")
            for s in self._step_labels:
                s.hide()
            self._motion_lbl.hide()
            return

        # Top
        self._emoji_lbl.setText(info['emoji'])
        self._letter_lbl.setText(self.letter)
        self._imagine_lbl.setText(f'💡 {info["imagine"]}')

        # Bars
        fingers = info['fingers']
        for i in range(5):
            level = fingers[i] if i < len(fingers) else 0
            cfg = self.BAR_CONFIG[level]
            self._bar_columns[i]['bar'].setFixedHeight(cfg['height'])
            self._bar_columns[i]['bar'].setStyleSheet(
                f"background: {cfg['bg']}; border-radius: 6px;"
            )
            self._bar_columns[i]['state_lbl'].setText(cfg['label'])
            self._bar_columns[i]['state_lbl'].setStyleSheet(
                f"font-size: 9px; font-weight: 800; color: {cfg['color']}; background: transparent;"
            )

        # Steps
        steps = info.get('do_this', [])
        for j, lbl in enumerate(self._step_labels):
            if j < len(steps):
                lbl.setText(steps[j])
                lbl.show()
            else:
                lbl.hide()

        # Motion
        motion = info.get('motion')
        if motion:
            self._motion_lbl.setText(f'🔄 MOVEMENT:  {motion}')
            self._motion_lbl.show()
        else:
            self._motion_lbl.hide()

    def cleanup(self):
        pass


class SignVisualizationBubble(QFrame):
    """A rich sign language visualization panel using a clear finger-status
    diagram instead of abstract hand drawings.
    
    Shows a finger diagram (5 columns: Thumb→Pinky) with state icons,
    a quick instruction, the word with active letter highlighted,
    detailed steps, and animated playback.
    """
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.original_text = text
        self.letters = [ch.upper() for ch in text if ch.isalpha()]
        self.word_chars = list(text)
        self.current_index = 0
        self._animation_timer = None
        self._is_playing = False
        
        self.setStyleSheet(f"""
            QFrame#signVizBubble {{
                background: {COLORS['bg_card']};
                border-radius: 20px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        self.setObjectName("signVizBubble")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 16)
        main_layout.setSpacing(12)
        
        # ── Header ──
        header = QHBoxLayout()
        badge = QLabel("🤟 Sign Language")
        badge.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: 13px; font-weight: 700;
            background: {COLORS['primary']}18;
            padding: 4px 12px; border-radius: 10px;
        """)
        header.addWidget(badge)
        header.addStretch()
        time_label = QLabel(QDateTime.currentDateTime().toString("hh:mm"))
        time_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        header.addWidget(time_label)
        main_layout.addLayout(header)
        
        # ── Word display ──
        self.word_display = QLabel()
        self.word_display.setAlignment(Qt.AlignCenter)
        self.word_display.setStyleSheet("background: transparent;")
        self.word_display.setTextFormat(Qt.RichText)
        self.word_display.setWordWrap(True)
        main_layout.addWidget(self.word_display)
        
        # ── Finger diagram (replaces hand drawing) ──
        self.sign_card = SignCard("")
        main_layout.addWidget(self.sign_card)
        
        # ── Step-by-step instructions ──
        self.steps_label = QLabel("")
        self.steps_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']};
            padding: 12px 14px;
            border-radius: 10px;
            line-height: 1.6;
        """)
        self.steps_label.setWordWrap(True)
        main_layout.addWidget(self.steps_label)
        
        # ── Common mistake / tip ──
        self.tip_label = QLabel("")
        self.tip_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['warning']};
            background: {COLORS['warning']}12;
            padding: 8px 12px;
            border-radius: 8px;
        """)
        self.tip_label.setWordWrap(True)
        main_layout.addWidget(self.tip_label)
        
        # ── Playback controls ──
        controls = QHBoxLayout()
        controls.setSpacing(8)
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']}; border: 1px solid {COLORS['border']};
                border-radius: 18px; font-size: 14px; color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{ background: {COLORS['bg_card_hover']}; }}
        """)
        self.prev_btn.clicked.connect(self._prev)
        controls.addWidget(self.prev_btn)
        
        self.play_btn = QPushButton("▶  Play")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']}; color: white; border: none;
                border-radius: 18px; padding: 8px 24px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """)
        self.play_btn.clicked.connect(self._toggle_playback)
        controls.addWidget(self.play_btn)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']}; border: 1px solid {COLORS['border']};
                border-radius: 18px; font-size: 14px; color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{ background: {COLORS['bg_card_hover']}; }}
        """)
        self.next_btn.clicked.connect(self._next)
        controls.addWidget(self.next_btn)
        
        controls.addSpacing(12)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; background: transparent;")
        controls.addWidget(self.progress_label)
        controls.addStretch()
        
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent;")
        controls.addWidget(speed_label)
        
        self._speed_ms = 1200
        for label, ms in [("Slow", 2000), ("Normal", 1200), ("Fast", 600)]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.PointingHandCursor)
            is_selected = (ms == self._speed_ms)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['primary'] if is_selected else COLORS['bg_input']};
                    color: {'white' if is_selected else COLORS['text_secondary']};
                    border: 1px solid {COLORS['primary'] if is_selected else COLORS['border']};
                    border-radius: 6px; padding: 2px 10px; font-size: 11px;
                }}
                QPushButton:hover {{ background: {COLORS['primary_hover'] if is_selected else COLORS['bg_card_hover']}; }}
            """)
            btn.clicked.connect(lambda checked, m=ms: self._set_speed(m))
            controls.addWidget(btn)
        
        main_layout.addLayout(controls)
        
        # Show first letter
        if self.letters:
            self._show_letter(0)
    
    def _build_word_html(self):
        """Build rich text showing the word with active letter highlighted."""
        html_parts = []
        letter_idx = 0
        for ch in self.word_chars:
            if ch == ' ':
                html_parts.append('&nbsp;&nbsp;&nbsp;')
            elif ch.isalpha():
                is_active = (letter_idx == self.current_index)
                if is_active:
                    html_parts.append(
                        f'<span style="color:{COLORS["primary"]}; font-size:28px; '
                        f'font-weight:900; background:{COLORS["primary"]}18; '
                        f'padding:2px 6px; border-radius:6px;">{ch.upper()}</span>'
                    )
                else:
                    done = letter_idx < self.current_index
                    color = COLORS['text_primary'] if done else COLORS['text_muted']
                    html_parts.append(
                        f'<span style="color:{color}; font-size:24px; '
                        f'font-weight:600; padding:2px 3px;">{ch.upper()}</span>'
                    )
                letter_idx += 1
            else:
                html_parts.append(f'<span style="color:{COLORS["text_muted"]}; font-size:24px;">{ch}</span>')
        return ''.join(html_parts)
    
    def _show_letter(self, index: int):
        """Display the sign for the letter at the given index."""
        if index < 0 or index >= len(self.letters):
            return
        self.current_index = index
        letter = self.letters[index]
        data = ASL_LESSON_DATA.get(letter, {})
        
        # Update sign card
        self.sign_card.set_letter(letter)
        
        # Update word highlight
        self.word_display.setText(self._build_word_html())
        
        # Update steps
        steps = data.get('detailed_steps', [])
        if steps:
            self.steps_label.setText('\n'.join(steps[:4]))
            self.steps_label.show()
        else:
            self.steps_label.hide()
        
        # Update tip
        mistakes = data.get('common_mistakes', [])
        if mistakes:
            self.tip_label.setText("⚠️ " + " • ".join(mistakes[:2]))
            self.tip_label.show()
        else:
            self.tip_label.hide()
        
        # Update progress
        self.progress_label.setText(f"{index + 1} / {len(self.letters)}")
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self.letters) - 1)
    
    def _prev(self):
        if self.current_index > 0:
            self._show_letter(self.current_index - 1)
    
    def _next(self):
        if self.current_index < len(self.letters) - 1:
            self._show_letter(self.current_index + 1)
    
    def _set_speed(self, ms: int):
        self._speed_ms = ms
    
    def _toggle_playback(self):
        if self._is_playing:
            self._stop_playback()
        else:
            self._start_playback()
    
    def _start_playback(self):
        self._is_playing = True
        self.play_btn.setText("⏸  Pause")
        if self.current_index >= len(self.letters) - 1:
            self.current_index = -1
        self._play_next()
    
    def _stop_playback(self):
        self._is_playing = False
        self.play_btn.setText("▶  Play")
        if self._animation_timer:
            self._animation_timer.stop()
    
    def _play_next(self):
        if not self._is_playing:
            return
        next_idx = self.current_index + 1
        if next_idx >= len(self.letters):
            self._stop_playback()
            self.progress_label.setText(f"✅ Done! ({len(self.letters)} signs)")
            return
        self._show_letter(next_idx)
        self._animation_timer = QTimer()
        self._animation_timer.setSingleShot(True)
        self._animation_timer.timeout.connect(self._play_next)
        self._animation_timer.start(self._speed_ms)
    
    def cleanup(self):
        if self._animation_timer:
            self._animation_timer.stop()
        self.sign_card.cleanup()


class ConversationWidget(QWidget):
    """Main conversation interface."""
    
    message_sent = Signal(str, str)  # message, type ('text', 'sign', 'voice')
    translation_requested = Signal(str)  # text to translate to sign
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, stretch=1)
        
        # Quick replies
        quick_replies_frame = QFrame()
        quick_replies_frame.setStyleSheet(f"background: {COLORS['bg_panel']};")
        quick_layout = QHBoxLayout(quick_replies_frame)
        quick_layout.setContentsMargins(16, 8, 16, 8)
        quick_layout.setSpacing(8)
        
        quick_replies = ["Hello!", "Thank you", "Yes", "No", "Help"]
        for reply in quick_replies:
            btn = QuickReplyButton(reply)
            btn.clicked.connect(lambda checked, r=reply: self._send_quick_reply(r))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        
        layout.addWidget(quick_replies_frame)
        
        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_panel']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(12)
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setObjectName("input")
        self.text_input.returnPressed.connect(self._send_text_message)
        input_layout.addWidget(self.text_input, stretch=1)
        
        # Send button
        send_btn = QPushButton("Send")
        send_btn.setObjectName("primaryButton")
        send_btn.clicked.connect(self._send_text_message)
        input_layout.addWidget(send_btn)
        
        # Show as sign button
        sign_btn = QPushButton("🤟")
        sign_btn.setToolTip("Show as sign")
        sign_btn.setFixedSize(40, 40)
        sign_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent']};
                border-radius: 20px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: {COLORS['accent_hover']};
            }}
        """)
        sign_btn.clicked.connect(self._request_sign_translation)
        input_layout.addWidget(sign_btn)
        
        layout.addWidget(input_frame)
    
    def add_message(self, text: str, is_user: bool, message_type: str = "text"):
        """Add a message to the conversation."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm")
        
        bubble = MessageBubble(text, is_user, timestamp, message_type)
        
        # Insert before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Store message
        self.messages.append({
            'text': text,
            'is_user': is_user,
            'type': message_type,
            'timestamp': timestamp
        })
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def add_signed_message(self, text: str):
        """Add a message that was signed by the user."""
        self.add_message(text, True, "sign")
    
    def add_response(self, text: str):
        """Add a response from the other party."""
        self.add_message(text, False, "text")
    
    def _send_text_message(self):
        """Send a typed text message."""
        text = self.text_input.text().strip()
        if text:
            self.add_message(text, True, "text")
            self.text_input.clear()
            self.message_sent.emit(text, "text")
    
    def _send_quick_reply(self, reply: str):
        """Send a quick reply."""
        self.add_message(reply, True, "text")
        self.message_sent.emit(reply, "text")
    
    def _request_sign_translation(self):
        """Request sign translation for current input."""
        text = self.text_input.text().strip()
        if text:
            # Add the user's message as a text bubble
            self.add_message(text, True, "text")
            
            # Add a sign visualization bubble as the response
            vis_bubble = SignVisualizationBubble(text)
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, vis_bubble)
            self.messages.append({
                'text': text,
                'is_user': False,
                'type': 'sign_visual',
                'timestamp': QDateTime.currentDateTime().toString("hh:mm")
            })
            
            self.text_input.clear()
            self.translation_requested.emit(text)
            QTimer.singleShot(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_conversation(self):
        """Clear all messages."""
        # Remove all message bubbles
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.messages = []


class ConversationPage(QWidget):
    """Full conversation mode page."""
    
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
        
        title = QLabel("💬 Conversation Mode")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self._clear_conversation)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # Instructions
        instructions = QFrame()
        instructions.setObjectName("card")
        inst_layout = QHBoxLayout(instructions)
        inst_layout.setContentsMargins(16, 12, 16, 12)
        
        inst_text = QLabel(
            "💡 Type a message and press the 🤟 button to see it as sign language. "
            "Each letter is shown with hand shapes, descriptions, and step-by-step instructions. "
            "Press ▶ Play to animate through the signs!"
        )
        inst_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        inst_text.setWordWrap(True)
        inst_layout.addWidget(inst_text)
        
        layout.addWidget(instructions)
        
        # Conversation widget (full width, no splitter)
        self.conversation = ConversationWidget()
        layout.addWidget(self.conversation, stretch=1)
        
        # Add welcome message
        self.conversation.add_response(
            "👋 Welcome to conversation mode! Type a message and press 🤟 to see it in sign language."
        )
    
    def on_sign_detected(self, text: str):
        """Handle detected sign translation."""
        self.conversation.add_signed_message(text)
    
    def _clear_conversation(self):
        """Clear the conversation."""
        self.conversation.clear_conversation()
        self.conversation.add_response("Conversation cleared. Start fresh!")
