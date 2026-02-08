"""
Tutorial Page - Interactive ASL Learning Guide

Provides step-by-step tutorials for learning ASL:
- Alphabet lessons with beginner-friendly visual finger diagrams
- Bar chart finger positions (tall=up, short=down, color-coded)
- Everyday analogies anyone can understand
- 3 dead-simple steps written for a 10-year-old
- Numbers, common words and phrases
- Progress tracking
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QProgressBar, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS
from ui.hand_widget import AnimatedHandWidget


# ─────────────────────────────────────────────────────────────
# Legacy ASL data — kept for backward-compat (conversation page
# still reads detailed_steps + common_mistakes from here)
# ─────────────────────────────────────────────────────────────
ASL_LESSON_DATA = {
    'A': {
        'name': 'Letter A',
        'description': 'Fist with thumb resting on the side',
        'detailed_steps': [
            '1. Make a fist with all fingers curled in',
            '2. Rest your thumb on the SIDE of your fist',
            '3. Thumb should touch the middle segment of your index finger',
            '4. Do NOT place thumb on top of fingers',
            '5. Palm faces forward, toward the viewer'
        ],
        'common_mistakes': [
            'Thumb on top of fist (that\'s S)',
            'Thumb tucked inside fist'
        ],
        'emoji': '✊',
    },
    'B': {
        'name': 'Letter B',
        'description': 'Flat hand with fingers up, thumb tucked',
        'detailed_steps': [
            '1. Hold your hand up with all 4 fingers pointing straight up',
            '2. Keep all fingers together (touching side by side)',
            '3. Fold your thumb DOWN across your palm',
            '4. Thumb tip should touch the base of your fingers',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Thumb sticking out (tuck it in!)',
            'Fingers spread apart'
        ],
        'emoji': '🖐️',
    },
    'C': {
        'name': 'Letter C',
        'description': 'Curved hand forming C shape',
        'detailed_steps': [
            '1. Curve all your fingers together',
            '2. Curve your thumb to face your fingers',
            '3. Leave a gap between thumb and fingers',
            '4. Your hand should look like a sideways C',
            '5. Like holding a can or cup'
        ],
        'common_mistakes': [
            'Hand too flat (not curved enough)',
            'Fingers touching thumb (that\'s O)'
        ],
        'emoji': '🤏',
    },
    'D': {
        'name': 'Letter D',
        'description': 'Index finger up, others make circle with thumb',
        'detailed_steps': [
            '1. Point your INDEX finger straight up',
            '2. Curl middle, ring, and pinky fingers down',
            '3. Touch thumb tip to the curled middle finger',
            '4. This creates a circle with thumb and other fingers',
            '5. Index stays pointing straight up'
        ],
        'common_mistakes': [
            'Forgetting to make the circle with thumb',
            'Other fingers not curled enough'
        ],
        'emoji': '☝️',
    },
    'E': {
        'name': 'Letter E',
        'description': 'All fingers curled down, thumb tucked under',
        'detailed_steps': [
            '1. Curl all four fingers down toward your palm',
            '2. Tuck your thumb UNDER the curled fingers',
            '3. Fingertips should almost touch your palm',
            '4. Hand should look like a rounded bump',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'Thumb on side (that\'s A)',
            'Fingers too tight (relax them slightly)'
        ],
        'emoji': '✊',
    },
    'F': {
        'name': 'Letter F',
        'description': 'OK sign - thumb and index touch, others up',
        'detailed_steps': [
            '1. Touch your THUMB tip to your INDEX fingertip',
            '2. This creates a small circle (like OK sign)',
            '3. Extend middle, ring, and pinky fingers UP',
            '4. Keep those 3 fingers straight and slightly apart',
            '5. Palm faces forward'
        ],
        'common_mistakes': [
            'All fingers together (that\'s O)',
            'Circle too big or too small'
        ],
        'emoji': '👌',
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
    },
}


# ─────────────────────────────────────────────────────────────
# Beginner-friendly sign guide — the CANONICAL source.
# Used by both Tutorial and Conversation pages.
# ─────────────────────────────────────────────────────────────
# 'imagine': an everyday analogy anyone can understand
# 'fingers': [thumb, index, middle, ring, pinky]
#   3 = fully extended  → tall green bar
#   2 = partially out   → medium orange bar
#   1 = slightly bent   → short yellow bar
#   0 = fully closed    → tiny gray bar
# 'do_this': 3 dead-simple steps written for a 10-year-old
# 'motion': optional movement instruction (J, Z)
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


# ─────────────────────────────────────────────────────────────
# SignCard widget — reusable finger bar-chart + analogy + steps
# ─────────────────────────────────────────────────────────────

class SignCard(QFrame):
    """A beginner-friendly sign instruction card with animated hand.

    Designed for people with ZERO sign language knowledge:
    - Big emoji + letter at top
    - "Imagine..." everyday analogy
    - ANIMATED realistic hand showing the exact finger positions
    - 3 simple numbered steps a child could follow
    - Motion animation for J, Z (hand moves on screen)
    """

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

    # ── build ──
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)

        # Row 1 — big emoji + letter
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

        # Row 2 — "Imagine..." analogy
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

        # Row 3 — ANIMATED HAND (replaces bar chart)
        hand_frame = QFrame()
        hand_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border-radius: 14px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        hand_inner = QVBoxLayout(hand_frame)
        hand_inner.setContentsMargins(8, 8, 8, 8)

        self._hand = AnimatedHandWidget()
        self._hand.setFixedHeight(220)
        hand_inner.addWidget(self._hand)

        layout.addWidget(hand_frame)

        # Row 4 — step-by-step cards
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

        # Row 5 — motion indicator (J, Z)
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

    # ── public API ──
    def set_letter(self, letter: str):
        self.letter = letter.upper()
        self._update()

    def _update(self):
        info = SIGN_GUIDE.get(self.letter)
        if not info:
            self._emoji_lbl.setText("❓")
            self._letter_lbl.setText(self.letter)
            self._imagine_lbl.setText(f"No guide available for '{self.letter}'")
            for s in self._step_labels:
                s.hide()
            self._motion_lbl.hide()
            return

        self._emoji_lbl.setText(info['emoji'])
        self._letter_lbl.setText(self.letter)
        self._imagine_lbl.setText(f'💡 {info["imagine"]}')

        # Animate hand to the letter pose
        self._hand.set_letter(self.letter)

        # Steps
        steps = info.get('do_this', [])
        for j, lbl in enumerate(self._step_labels):
            if j < len(steps):
                lbl.setText(steps[j])
                lbl.show()
            else:
                lbl.hide()

        # Motion text
        motion = info.get('motion')
        if motion:
            self._motion_lbl.setText(f'🔄 MOVEMENT:  {motion}')
            self._motion_lbl.show()
        else:
            self._motion_lbl.hide()

    def cleanup(self):
        self._hand.cleanup()


# ─────────────────────────────────────────────────────────────
# LessonCard — a card on the main lesson-list page
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# AlphabetLesson — the main interactive A-Z lesson
# Now uses SignCard (bar chart + analogies + steps) instead of
# ASCII art and technical descriptions.
# ─────────────────────────────────────────────────────────────

class AlphabetLesson(QWidget):
    """Interactive alphabet learning lesson with beginner-friendly visuals."""

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

        # ── Header ──
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

        # ── Progress bar ──
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

        # ── Main content (scrollable) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # --- Left panel: SignCard (the beginner-friendly visual) ---
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_panel.setFixedWidth(380)
        left_inner = QVBoxLayout(left_panel)
        left_inner.setContentsMargins(8, 8, 8, 8)

        self.sign_card = SignCard()
        left_inner.addWidget(self.sign_card)
        left_inner.addStretch()

        content_layout.addWidget(left_panel)

        # --- Right panel: Detailed info + common mistakes + tips ---
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)

        # "Similar letters" helper
        similar_title = QLabel("🔍 Watch Out — Similar Letters")
        similar_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        right_layout.addWidget(similar_title)

        self.similar_label = QLabel()
        self.similar_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']};
            padding: 12px;
            border-radius: 10px;
        """)
        self.similar_label.setWordWrap(True)
        right_layout.addWidget(self.similar_label)

        # Common mistakes
        mistakes_title = QLabel("⚠️ Common Mistakes to Avoid")
        mistakes_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['warning']};
            background: transparent;
            margin-top: 8px;
        """)
        right_layout.addWidget(mistakes_title)

        self.mistakes_label = QLabel()
        self.mistakes_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_muted']};
            background: {COLORS['warning']}15;
            padding: 12px;
            border-radius: 10px;
        """)
        self.mistakes_label.setWordWrap(True)
        right_layout.addWidget(self.mistakes_label)

        # Quick description
        desc_title = QLabel("📝 Quick Description")
        desc_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
            margin-top: 8px;
        """)
        right_layout.addWidget(desc_title)

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']};
            padding: 12px;
            border-radius: 10px;
        """)
        self.desc_label.setWordWrap(True)
        right_layout.addWidget(self.desc_label)

        # Practice tip
        practice_frame = QFrame()
        practice_frame.setStyleSheet(f"""
            background: {COLORS['primary']}15;
            border-radius: 10px;
            padding: 8px;
            margin-top: 8px;
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

        practice_text = QLabel(
            "Try signing this letter in the Live Translation page "
            "to see if the camera recognizes it!"
        )
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

        # ── Navigation buttons ──
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

    # ── Similar-letter map (common confusions) ──
    SIMILAR_MAP = {
        'A': 'S has thumb across the front · E has all fingers curled with thumb under',
        'B': '5 (number) is the same but with thumb out · Flat-B has thumb tucked',
        'C': 'O has fingers touching thumb (closed circle) · C stays open',
        'D': '1 (number) has index up but NO circle · D makes a circle with remaining fingers',
        'E': 'A has thumb on the side · S has thumb across the front',
        'F': '9 (number) looks the same! · F/9 = thumb+index circle, 3 fingers up',
        'G': 'L has thumb and index at 90° (vertical) · G points sideways',
        'H': 'U has two fingers UP · H has two fingers SIDEWAYS',
        'I': 'J starts like I then adds a motion · Y has both thumb AND pinky out',
        'J': 'I is the same hand shape but with NO motion',
        'K': 'V has NO thumb between fingers · K has thumb wedged in',
        'L': 'G points sideways · L points up (makes an L shape)',
        'M': 'N has only TWO fingers over thumb · M has THREE',
        'N': 'M has THREE fingers over thumb · N has only TWO',
        'O': 'C is an open curve · O is a closed circle (all fingers touch thumb)',
        'P': 'K is the same hand shape · P just points it downward',
        'Q': 'G is the same hand shape · Q just points it downward',
        'R': 'U has two fingers together · R has them crossed',
        'S': 'A has thumb on the side · S has thumb across the front',
        'T': 'N has fingers over thumb · T has thumb poking between fingers',
        'U': 'V has fingers SPREAD apart · U has them TOGETHER',
        'V': 'U has fingers TOGETHER · V has them SPREAD',
        'W': '6 (number) looks similar · W = 3 fingers spread up',
        'X': 'D has index straight up · X has index HOOKED/bent',
        'Y': 'I has ONLY pinky up · Y has both thumb AND pinky out',
        'Z': 'J also has motion · Z traces a Z shape · J traces a J curve',
    }

    def _update_display(self):
        """Update the display for the current letter."""
        letter = self.letters[self.current_letter_index]
        guide = SIGN_GUIDE.get(letter, {})
        lesson = ASL_LESSON_DATA.get(letter, {})

        # Update SignCard (left panel)
        self.sign_card.set_letter(letter)

        # Letter indicator
        self.letter_indicator.setText(f"{letter} — {lesson.get('name', letter)}")

        # Similar letters
        similar = self.SIMILAR_MAP.get(letter, '')
        self.similar_label.setText(similar if similar else 'No common confusions.')

        # Common mistakes
        mistakes = lesson.get('common_mistakes', [])
        mistakes_text = '\n'.join([f"❌  {m}" for m in mistakes])
        self.mistakes_label.setText(mistakes_text if mistakes_text else 'None — you got this!')

        # Description
        self.desc_label.setText(lesson.get('description', ''))

        # Progress
        self.progress_bar.setValue(self.current_letter_index + 1)
        self.progress_text.setText(f"{self.current_letter_index + 1}/26")

        # Nav buttons
        self.prev_btn.setEnabled(self.current_letter_index > 0)
        self.next_btn.setText(
            "Complete ✓" if self.current_letter_index == 25 else "Next Letter →"
        )

    def _prev_letter(self):
        if self.current_letter_index > 0:
            self.current_letter_index -= 1
            self._update_display()

    def _next_letter(self):
        if self.current_letter_index < 25:
            self.current_letter_index += 1
            self._update_display()
        else:
            self.back_requested.emit()

    def _jump_to_letter(self, index: int):
        self.current_letter_index = index
        self._update_display()


# ─────────────────────────────────────────────────────────────
# NumbersLesson
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# TutorialPage — top-level page with lesson list + stacked views
# ─────────────────────────────────────────────────────────────

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
            "Learn American Sign Language through interactive lessons with "
            "easy-to-understand visual guides. Each letter shows you a simple "
            "bar chart of finger positions, everyday analogies, and 3 dead-simple "
            "steps — designed so anyone can follow along, even with zero sign "
            "language experience!"
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
        beginner_label = QLabel("🌱 Beginner — Start Here")
        beginner_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};")
        scroll_layout.addWidget(beginner_label)

        lessons_grid = QGridLayout()
        lessons_grid.setSpacing(16)

        lessons = [
            ("alphabet", "The ASL Alphabet",
             "Learn A-Z with bar-chart finger guides, everyday analogies, and 3 simple steps per letter",
             "🔤", 0),
            ("numbers", "Numbers 0-9",
             "Count from zero to nine in ASL", "🔢", 0),
            ("greetings", "Greetings",
             "Hello, goodbye, nice to meet you", "👋", 0),
            ("basics", "Basic Words",
             "Yes, no, please, thank you, sorry", "💬", 0),
        ]

        for i, (lid, ttl, desc, icon, progress) in enumerate(lessons):
            card = LessonCard(lid, ttl, desc, icon, progress)
            card.clicked.connect(self._open_lesson)
            lessons_grid.addWidget(card, i // 2, i % 2)

        scroll_layout.addLayout(lessons_grid)

        # Intermediate lessons
        inter_label = QLabel("📈 Intermediate")
        inter_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};")
        scroll_layout.addWidget(inter_label)

        inter_lessons = [
            ("questions", "Question Words",
             "What, where, when, why, how, who", "❓", 0),
            ("emotions", "Emotions",
             "Happy, sad, angry, scared, excited", "😊", 0),
            ("family", "Family",
             "Mom, dad, sister, brother, baby", "👨‍👩‍👧‍👦", 0),
            ("actions", "Common Actions",
             "Go, stop, help, want, need, like", "🏃", 0),
        ]

        inter_grid = QGridLayout()
        inter_grid.setSpacing(16)

        for i, (lid, ttl, desc, icon, progress) in enumerate(inter_lessons):
            card = LessonCard(lid, ttl, desc, icon, progress)
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
            "• Use the Live Translation feature to check your signs",
            "• Pay attention to hand orientation — it matters!",
            "• Some letters (J, Z) require motion — practice the movement",
            "• Learn similar letters together (M/N, U/V, A/S/E) to spot differences",
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

    def _show_lesson_list(self):
        """Return to the lesson list."""
        self.stack.setCurrentWidget(self.lesson_list)
