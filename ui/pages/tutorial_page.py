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
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QObject
from PySide6.QtGui import QFont, QColor, QPixmap, QImage
import cv2

import os
import glob

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
        'fingers': [1, 1, 3, 3, 3],
        'do_this': [
            '1️⃣  Touch your THUMB tip to your INDEX fingertip (makes a small circle)',
            '2️⃣  Stick the other 3 fingers (middle, ring, pinky) STRAIGHT UP',
            '3️⃣  Keep those 3 fingers straight and slightly apart',
        ],
    },
    'G': {
        'emoji': '👉',
        'imagine': 'Like a finger gun pointing sideways →',
        'fingers': [2, 2, 0, 0, 0],
        'direction': 'side',
        'do_this': [
            '1️⃣  Point your INDEX finger SIDEWAYS → (not up!)',
            '2️⃣  Extend your THUMB parallel above it (like a finger gun)',
            '3️⃣  Curl the other 3 fingers into your palm',
        ],
    },
    'H': {
        'emoji': '✌️',
        'imagine': 'Like a peace sign, but pointing sideways →',
        'fingers': [0, 2, 2, 0, 0],
        'direction': 'side',
        'do_this': [
            '1️⃣  Extend INDEX + MIDDLE fingers SIDEWAYS → (not up!)',
            '2️⃣  Keep them together (touching side by side)',
            '3️⃣  Curl ring, pinky, and tuck thumb underneath',
        ],
    },
    'I': {
        'emoji': '🤙',
        'imagine': 'Like a fist, but your PINKY sticks up alone',
        'fingers': [0, 0, 0, 0, 3],
        'do_this': [
            '1️⃣  Make a fist with your thumb across the front',
            '2️⃣  Stick ONLY your PINKY finger straight up',
            '3️⃣  Keep all other fingers curled tight',
        ],
    },
    'J': {
        'emoji': '🤙',
        'imagine': 'Start like "I" (pinky up), then draw a J in the air',
        'fingers': [0, 0, 0, 0, 3],
        'do_this': [
            '1️⃣  Start in the letter I position (fist with pinky up)',
            '2️⃣  Move your hand DOWN ↓ then CURVE it toward you ↩',
            '3️⃣  Your pinky traces the shape of the letter J!',
        ],
        'motion': '↓↩ Move hand down, then curve inward — drawing a J with your pinky',
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
        'imagine': 'Like the letter K, but your hand points DOWNWARD ↓',
        'fingers': [2, 3, 3, 0, 0],
        'direction': 'down',
        'do_this': [
            '1️⃣  Make the letter K (V shape + thumb wedged between)',
            '2️⃣  Now rotate your whole hand to point DOWNWARD ↓',
            '3️⃣  Index + middle should point toward the ground',
        ],
    },
    'Q': {
        'emoji': '👇',
        'imagine': 'Like the letter G, but your hand points DOWNWARD ↓',
        'fingers': [2, 2, 0, 0, 0],
        'direction': 'down',
        'do_this': [
            '1️⃣  Make the letter G (index + thumb pointing)',
            '2️⃣  Now rotate your whole hand to point DOWNWARD ↓',
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
        'imagine': 'A tight fist — thumb wraps across the FRONT',
        'fingers': [1, 0, 0, 0, 0],
        'do_this': [
            '1️⃣  Make a tight FIST (all fingers curled in)',
            '2️⃣  Wrap your thumb across the FRONT of your fingers',
            '3️⃣  Thumb tip sits near your ring/pinky knuckles',
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
        'imagine': 'Two fingers up and pressed TOGETHER — like a closed peace sign',
        'fingers': [0, 3, 3, 0, 0],
        'do_this': [
            '1️⃣  Hold INDEX + MIDDLE fingers straight UP ↑',
            '2️⃣  Keep them pressed TOGETHER (touching each other)',
            '3️⃣  Curl ring + pinky down, tuck thumb across palm',
        ],
    },
    'V': {
        'emoji': '✌️',
        'imagine': 'Peace sign / Victory sign — fingers SPREAD!',
        'fingers': [0, 3, 3, 0, 0],
        'do_this': [
            '1️⃣  Hold INDEX + MIDDLE fingers straight UP ↑',
            '2️⃣  SPREAD them APART (making a V / peace shape)',
            '3️⃣  Curl ring + pinky down, tuck thumb across palm',
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
# Looping reference video player (used for J, Z motion demos)
# ─────────────────────────────────────────────────────────────

class _RefVideoLooper(QObject):
    """Loops a short video clip into a QLabel at the given display size."""

    def __init__(self, path: str, label, w: int = 260, h: int = 200, parent=None):
        super().__init__(parent)
        self._label = label
        self._w = w
        self._h = h
        self._cap = cv2.VideoCapture(path)
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 25.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._timer.start(int(1000 / fps))

    def _next_frame(self):
        ok, frame = self._cap.read()
        if not ok:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        if ok:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            fh, fw = frame.shape[:2]
            scale = min(self._w / fw, self._h / fh)
            nw, nh = max(1, int(fw * scale)), max(1, int(fh * scale))
            frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
            img = QImage(frame.data, nw, nh, nw * 3, QImage.Format_RGB888)
            self._label.setPixmap(QPixmap.fromImage(img))

    def stop(self):
        self._timer.stop()
        if self._cap.isOpened():
            self._cap.release()

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass


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
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # ── Row 1: emoji + letter + analogy (single compact header) ──
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self._emoji_lbl = QLabel()
        self._emoji_lbl.setStyleSheet("font-size: 32px; background: transparent;")
        self._emoji_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._emoji_lbl.setFixedWidth(40)
        header_row.addWidget(self._emoji_lbl)

        self._letter_lbl = QLabel()
        self._letter_lbl.setStyleSheet(f"""
            font-size: 40px; font-weight: 900;
            color: {COLORS['primary']}; background: transparent;
        """)
        self._letter_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._letter_lbl.setFixedWidth(48)
        header_row.addWidget(self._letter_lbl)

        self._imagine_lbl = QLabel()
        self._imagine_lbl.setWordWrap(True)
        self._imagine_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._imagine_lbl.setStyleSheet(f"""
            font-size: 12px; font-weight: 600;
            color: {COLORS['text_primary']};
            background: {COLORS['primary']}15;
            padding: 5px 10px;
            border-radius: 8px;
        """)
        header_row.addWidget(self._imagine_lbl, 1)
        layout.addLayout(header_row)

        # ── Row 2: Finger bars (left) | Reference photo (right) ──
        media_row = QHBoxLayout()
        media_row.setSpacing(8)

        # Left — animated finger-position bars
        hand_frame = QFrame()
        hand_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border-radius: 10px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        hand_vbox = QVBoxLayout(hand_frame)
        hand_vbox.setContentsMargins(4, 4, 4, 2)
        hand_vbox.setSpacing(2)
        hand_title = QLabel("🖐 Finger Positions")
        hand_title.setAlignment(Qt.AlignCenter)
        hand_title.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['text_muted']}; background: transparent;")
        hand_vbox.addWidget(hand_title)
        self._hand = AnimatedHandWidget()
        self._hand._desc_label.hide()  # desc shown in header
        self._hand.setMinimumHeight(140)
        self._hand.setMaximumHeight(220)
        hand_vbox.addWidget(self._hand)
        media_row.addWidget(hand_frame, 1)

        # Right — reference photo
        self._ref_img_frame = QFrame()
        self._ref_img_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['bg_card']}, stop:1 {COLORS['bg_input']});
                border-radius: 10px;
                border: 1.5px solid {COLORS['primary']}50;
            }}
        """)
        ref_vbox = QVBoxLayout(self._ref_img_frame)
        ref_vbox.setContentsMargins(4, 4, 4, 4)
        ref_vbox.setSpacing(2)
        ref_vbox.setAlignment(Qt.AlignCenter)
        ref_title = QLabel("📸 Reference")
        ref_title.setAlignment(Qt.AlignCenter)
        ref_title.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {COLORS['primary']}; background: transparent;")
        ref_vbox.addWidget(ref_title)
        self._ref_img_label = QLabel()
        self._ref_img_label.setAlignment(Qt.AlignCenter)
        self._ref_img_label.setMinimumHeight(140)
        self._ref_img_label.setMaximumHeight(220)
        self._ref_img_label.setStyleSheet("background: transparent;")
        self._ref_img_label.setScaledContents(False)
        ref_vbox.addWidget(self._ref_img_label)
        self._ref_video_looper = None
        media_row.addWidget(self._ref_img_frame, 1)

        layout.addLayout(media_row)

        # ── Row 3: Step-by-step instructions ──
        self._steps_container = QVBoxLayout()
        self._steps_container.setSpacing(3)
        self._step_labels = []
        for _ in range(3):
            step = QLabel()
            step.setWordWrap(True)
            step.setStyleSheet(f"""
                font-size: 11px;
                color: {COLORS['text_primary']};
                background: {COLORS['bg_card']};
                padding: 4px 10px;
                border-radius: 7px;
                border-left: 3px solid {COLORS['primary']};
            """)
            self._steps_container.addWidget(step)
            self._step_labels.append(step)
        layout.addLayout(self._steps_container)

        # ── Row 4: Motion hint (J, Z only) ──
        self._motion_lbl = QLabel()
        self._motion_lbl.setAlignment(Qt.AlignCenter)
        self._motion_lbl.setWordWrap(True)
        self._motion_lbl.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: white;
            background: {COLORS['primary']};
            padding: 5px 10px;
            border-radius: 8px;
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

        # Load reference image — images live in assets/alphabets/
        self._load_ref_image(self.letter, 'alphabets')

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

    def _load_ref_image(self, name: str, folder: str):
        """Load a reference image or looping video from assets/<folder>/."""
        # Stop any previous video looper
        if self._ref_video_looper is not None:
            self._ref_video_looper.stop()
            self._ref_video_looper = None

        assets_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), 'assets')
        # Search priority: requested folder first, then fallbacks
        search_folders = [folder]
        for fb in ('alphabets', 'numbers', 'asl_hands'):
            if fb != folder:
                search_folders.append(fb)

        VIDEO_EXTS = {'.mp4', '.webm', '.avi', '.mov'}
        IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif', '.tif', '.tiff', '.svg'}

        video_matches = []
        image_matches = []
        seen = set()
        for sf in search_folders:
            base = os.path.join(assets_root, sf)
            for pat in [f'{name}.*', f'{name.lower()}.*', f'{name.upper()}.*']:
                for m in glob.glob(os.path.join(base, pat)):
                    if m in seen:
                        continue
                    seen.add(m)
                    ext = os.path.splitext(m)[1].lower()
                    if ext in VIDEO_EXTS:
                        video_matches.append(m)
                    elif ext in IMAGE_EXTS:
                        image_matches.append(m)

        # Prefer video (looping motion demo) over static image
        if video_matches:
            self._ref_img_label.clear()
            self._ref_video_looper = _RefVideoLooper(
                video_matches[0], self._ref_img_label, 260, 200, self)
            self._ref_img_frame.show()
            return

        if image_matches:
            pixmap = QPixmap(image_matches[0])
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    260, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._ref_img_label.setPixmap(scaled)
                self._ref_img_frame.show()
                return

        # Nothing found — hide the frame
        self._ref_img_label.clear()
        self._ref_img_frame.hide()

    def cleanup(self):
        if self._ref_video_looper is not None:
            self._ref_video_looper.stop()
            self._ref_video_looper = None
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
        self.setFixedHeight(150)
        self._setup_ui(title, description, icon, progress)

    def _setup_ui(self, title, description, icon, progress):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Icon and title row
        header = QHBoxLayout()

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 26px; background: transparent;")
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; background: transparent;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(progress)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Progress text
        self.progress_text = QLabel(f"{progress}% Complete")
        self.progress_text.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; background: transparent;")
        layout.addWidget(self.progress_text)

    def update_progress(self, progress: int):
        """Update progress display."""
        self.progress_bar.setValue(progress)
        self.progress_text.setText(f"{progress}% Complete")

    def mousePressEvent(self, event):
        self.clicked.emit(self.lesson_id)


# ─────────────────────────────────────────────────────────────
# AlphabetLesson — the main interactive A-Z lesson
# Now uses SignCard (bar chart + analogies + steps) instead of
# ASCII art and technical descriptions.
# Includes live camera practice panel in a single-screen layout.
# ─────────────────────────────────────────────────────────────

class AlphabetLesson(QWidget):
    """Interactive alphabet learning lesson with beginner-friendly visuals
    and integrated camera practice — all on a single screen (no scrolling)."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_letter_index = 0
        self.letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.completed_letters = set()
        self._hold_count = 0
        self._target_hold_frames = 20  # ~0.7s at 30fps (slightly faster than 1s)
        self._auto_advance_timer = QTimer(self)
        self._auto_advance_timer.setSingleShot(True)
        self._auto_advance_timer.timeout.connect(self._next_letter)
        self._camera_widget = None  # Lazy-loaded
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # ── Header (compact) ──
        header = QHBoxLayout()
        header.setSpacing(12)

        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondaryButton")
        back_btn.setMinimumWidth(80)
        back_btn.clicked.connect(self._on_back)
        header.addWidget(back_btn)

        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.setMinimumWidth(80)
        reset_btn.clicked.connect(self._reset_tutorial)
        header.addWidget(reset_btn)

        title = QLabel("🔤 ASL Alphabet")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)

        # Progress bar inline
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(26)
        self.progress_bar.setValue(1)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background-color: {COLORS['bg_input']}; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {COLORS['primary']}; border-radius: 4px; }}
        """)
        header.addWidget(self.progress_bar)

        self.progress_text = QLabel("1/26")
        self.progress_text.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        header.addWidget(self.progress_text)

        header.addStretch()

        # Letter indicator
        self.letter_indicator = QLabel("A")
        self.letter_indicator.setStyleSheet(f"""
            font-size: 20px; font-weight: bold;
            color: {COLORS['primary']};
            background: {COLORS['primary']}20;
            padding: 4px 10px; border-radius: 6px;
        """)
        header.addWidget(self.letter_indicator)

        layout.addLayout(header)

        # ── Main content: 3 columns (no scroll) ──
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # === LEFT COLUMN: SignCard (no scroll — compact layout fits) ===
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_panel.setFixedWidth(400)
        left_inner = QVBoxLayout(left_panel)
        left_inner.setContentsMargins(6, 6, 6, 6)
        left_inner.setSpacing(0)

        self.sign_card = SignCard()
        left_inner.addWidget(self.sign_card)

        content_layout.addWidget(left_panel)

        # === MIDDLE COLUMN: Tips (compact) ===
        mid_panel = QFrame()
        mid_panel.setObjectName("card")
        mid_layout = QVBoxLayout(mid_panel)
        mid_layout.setContentsMargins(10, 10, 10, 10)
        mid_layout.setSpacing(8)

        # Similar letters
        similar_title = QLabel("🔍 Similar Letters")
        similar_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_primary']}; background: transparent;")
        mid_layout.addWidget(similar_title)

        self.similar_label = QLabel()
        self.similar_label.setStyleSheet(f"""
            font-size: 11px; color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']}; padding: 8px; border-radius: 8px;
        """)
        self.similar_label.setWordWrap(True)
        mid_layout.addWidget(self.similar_label)

        # Common mistakes
        mistakes_title = QLabel("⚠️ Common Mistakes")
        mistakes_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['warning']}; background: transparent;")
        mid_layout.addWidget(mistakes_title)

        self.mistakes_label = QLabel()
        self.mistakes_label.setStyleSheet(f"""
            font-size: 11px; color: {COLORS['text_muted']};
            background: {COLORS['warning']}15; padding: 8px; border-radius: 8px;
        """)
        self.mistakes_label.setWordWrap(True)
        mid_layout.addWidget(self.mistakes_label)

        # Description
        desc_title = QLabel("📝 Description")
        desc_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_primary']}; background: transparent;")
        mid_layout.addWidget(desc_title)

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(f"""
            font-size: 11px; color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']}; padding: 8px; border-radius: 8px;
        """)
        self.desc_label.setWordWrap(True)
        mid_layout.addWidget(self.desc_label)

        mid_layout.addStretch()
        content_layout.addWidget(mid_panel, 1)

        # === RIGHT COLUMN: Camera Practice ===
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_panel.setMinimumWidth(460)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(6)

        cam_title = QLabel("📷 Practice with Camera")
        cam_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']}; background: transparent;")
        right_layout.addWidget(cam_title)

        # Camera container (placeholder until started)
        self.camera_container = QFrame()
        self.camera_container.setStyleSheet(f"""
            background: #000;
            border-radius: 10px;
            min-height: 340px;
        """)
        self.camera_container.setMinimumHeight(360)
        cam_inner = QVBoxLayout(self.camera_container)
        cam_inner.setContentsMargins(0, 0, 0, 0)

        self.camera_placeholder = QLabel("Click 'Start Camera' to practice")
        self.camera_placeholder.setAlignment(Qt.AlignCenter)
        self.camera_placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        cam_inner.addWidget(self.camera_placeholder)

        right_layout.addWidget(self.camera_container)

        # Feedback label (shows if letter is correct)
        self.feedback_label = QLabel("👆 Show the letter to camera")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setStyleSheet(f"""
            font-size: 14px; font-weight: 600;
            color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']};
            padding: 10px; border-radius: 8px;
        """)
        right_layout.addWidget(self.feedback_label)

        # Camera control buttons
        cam_btns = QHBoxLayout()
        self.start_cam_btn = QPushButton("▶ Start Camera")
        self.start_cam_btn.setObjectName("primaryButton")
        self.start_cam_btn.clicked.connect(self._start_camera)
        cam_btns.addWidget(self.start_cam_btn)

        self.stop_cam_btn = QPushButton("⏹ Stop")
        self.stop_cam_btn.setObjectName("secondaryButton")
        self.stop_cam_btn.clicked.connect(self._stop_camera)
        self.stop_cam_btn.setEnabled(False)
        cam_btns.addWidget(self.stop_cam_btn)

        right_layout.addLayout(cam_btns)
        right_layout.addStretch()

        content_layout.addWidget(right_panel)

        layout.addLayout(content_layout, 1)

        # ── Navigation bar ──
        nav_frame = QFrame()
        nav_frame.setObjectName("alphabetNavFrame")
        nav_frame.setStyleSheet(f"""
            QFrame#alphabetNavFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        nav_frame_layout = QVBoxLayout(nav_frame)
        nav_frame_layout.setContentsMargins(12, 8, 12, 10)
        nav_frame_layout.setSpacing(6)

        # Top row: Prev / title / Next
        nav_top = QHBoxLayout()
        nav_top.setSpacing(8)

        self.prev_btn = QPushButton("◀  Previous Letter")
        self.prev_btn.setMinimumWidth(130)
        self.prev_btn.setFixedHeight(36)
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 13px; font-weight: 600;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary']};
                color: white;
                border-color: {COLORS['primary']};
            }}
            QPushButton:disabled {{
                opacity: 0.4;
                color: {COLORS['text_muted']};
            }}
        """)
        self.prev_btn.clicked.connect(self._prev_letter)
        nav_top.addWidget(self.prev_btn)

        nav_top.addStretch()

        nav_title = QLabel("📍 Jump to Letter")
        nav_title.setAlignment(Qt.AlignCenter)
        nav_title.setStyleSheet(f"""
            font-size: 13px; font-weight: 700;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        nav_top.addWidget(nav_title)

        nav_top.addStretch()

        self.next_btn = QPushButton("Next Letter  ▶")
        self.next_btn.setMinimumWidth(130)
        self.next_btn.setFixedHeight(36)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px; font-weight: 700;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        self.next_btn.clicked.connect(self._next_letter)
        nav_top.addWidget(self.next_btn)

        nav_frame_layout.addLayout(nav_top)

        # Bottom row: Quick-jump letter grid (two rows of 13)
        letter_grid_widget = QWidget()
        letter_grid = QGridLayout(letter_grid_widget)
        letter_grid.setSpacing(4)
        letter_grid.setContentsMargins(0, 0, 0, 0)
        self.nav_buttons = []
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, letter in enumerate(alphabet):
            btn = QPushButton(letter)
            btn.setFixedSize(38, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"Jump to letter {letter}")
            btn.clicked.connect(lambda checked, idx=i: self._jump_to_letter(idx))
            row = 0 if i < 13 else 1
            col = i if i < 13 else i - 13
            letter_grid.addWidget(btn, row, col, Qt.AlignCenter)
            self.nav_buttons.append(btn)

        nav_frame_layout.addWidget(letter_grid_widget, 0, Qt.AlignCenter)
        layout.addWidget(nav_frame)
        # Initialize display
        self._update_display()

    def _on_back(self):
        """Clean up and go back."""
        self._stop_camera()
        self.back_requested.emit()

    def _reset_tutorial(self):
        """Reset all progress."""
        self.completed_letters.clear()
        self.current_letter_index = 0
        self._hold_count = 0
        self._auto_advance_timer.stop()
        self._update_display()

    def _start_camera(self):
        """Start the camera for practice."""
        try:
            from ui.camera_widget import CameraWidget
        except ImportError:
            self.feedback_label.setText("❌ Camera not available")
            return

        if self._camera_widget is None:
            self._camera_widget = CameraWidget()
            self._camera_widget.setMinimumSize(440, 340)
            self._camera_widget.video_label.setMinimumSize(440, 340)
            # Lower threshold for tutorial practice (easier to trigger)
            self._camera_widget.heuristic_threshold = 0.35
            
            # Connect heuristic gesture signal for feedback
            self._camera_widget.heuristic_gesture_detected.connect(self._on_gesture_detected)

            # Replace placeholder with camera
            self.camera_placeholder.hide()
            self.camera_container.layout().addWidget(self._camera_widget)

        if self._camera_widget.start():
            self.start_cam_btn.setEnabled(False)
            self.stop_cam_btn.setEnabled(True)
            self.feedback_label.setText("👀 Show the letter to the camera...")
            self.feedback_label.setStyleSheet(f"""
                font-size: 14px; font-weight: 600;
                color: {COLORS['text_secondary']};
                background: {COLORS['bg_input']};
                padding: 10px; border-radius: 8px;
            """)
        else:
            self.feedback_label.setText("❌ Could not start camera")

    def _stop_camera(self):
        """Stop the camera."""
        if self._camera_widget:
            self._camera_widget.stop()
        self.start_cam_btn.setEnabled(True)
        self.stop_cam_btn.setEnabled(False)
        self.feedback_label.setText("👆 Click Start to practice")
        self.feedback_label.setStyleSheet(f"""
            font-size: 14px; font-weight: 600;
            color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']};
            padding: 10px; border-radius: 8px;
        """)

    def _on_gesture_detected(self, gesture_name: str, confidence: float):
        """Handle gesture detection from camera."""
        current_letter = self.letters[self.current_letter_index]
        detected = gesture_name.upper()

        # If already auto-advancing, ignore new gestures
        if self._auto_advance_timer.isActive():
            return

        if detected == current_letter:
            self._hold_count += 1
            
            # Progress bar for holding logic
            progress = min(1.0, self._hold_count / self._target_hold_frames)
            
            if self._hold_count >= self._target_hold_frames:
                # Confirmed!
                if current_letter not in self.completed_letters:
                    self.completed_letters.add(current_letter)
                    self._update_display()
                    
                    self.feedback_label.setText(f"✅ Perfect! '{current_letter}' confirmed.")
                    self.feedback_label.setStyleSheet(f"""
                        font-size: 16px; font-weight: 700;
                        color: white;
                        background: {COLORS['success']};
                        padding: 12px; border-radius: 8px;
                    """)
                    
                    # Auto advance
                    self._auto_advance_timer.start(1500)
            else:
                # Holding feedback - visual bar
                scaling = int(progress * 10)
                bars = "█" * scaling + "░" * (10 - scaling)
                self.feedback_label.setText(f"Hold steady... {bars}")
                self.feedback_label.setStyleSheet(f"""
                    font-size: 14px; font-weight: 600;
                    color: {COLORS['primary']};
                    background: {COLORS['primary']}20;
                    padding: 10px; border-radius: 8px;
                    border: 1px solid {COLORS['primary']};
                """)
        else:
            self._hold_count = 0
            # Wrong gesture
            self.feedback_label.setText(f"🔄 Detected '{detected}' — try '{current_letter}'")
            self.feedback_label.setStyleSheet(f"""
                font-size: 14px; font-weight: 600;
                color: {COLORS['warning']};
                background: {COLORS['warning']}20;
                padding: 10px; border-radius: 8px;
            """)

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

        # Update Quick Jump Buttons
        if hasattr(self, 'nav_buttons'):
            for i, btn in enumerate(self.nav_buttons):
                char = self.letters[i]
                if i == self.current_letter_index:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {COLORS['primary']};
                            color: white;
                            border: 2px solid {COLORS['primary_light']};
                            border-radius: 4px;
                            font-size: 13px; font-weight: bold;
                            padding: 0px;
                            min-width: 36px;
                            min-height: 28px;
                        }}
                    """)
                elif char in self.completed_letters:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {COLORS['success']}30;
                            color: {COLORS['success']};
                            border: 2px solid {COLORS['success']};
                            border-radius: 4px;
                            font-size: 13px; font-weight: bold;
                            padding: 0px;
                            min-width: 36px;
                            min-height: 28px;
                        }}
                        QPushButton:hover {{
                            background: {COLORS['success']}50;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {COLORS['bg_card']};
                            color: {COLORS['text_primary']};
                            border: 1px solid {COLORS['border_light']};
                            border-radius: 4px;
                            font-size: 13px; font-weight: bold;
                            padding: 0px;
                            min-width: 36px;
                            min-height: 28px;
                        }}
                        QPushButton:hover {{
                            background: {COLORS['primary']}30;
                            color: {COLORS['primary_light']};
                            border-color: {COLORS['primary']};
                        }}
                    """)

        # Nav buttons
        self.prev_btn.setEnabled(self.current_letter_index > 0)
        # Next button: show checkmark on last letter
        if self.current_letter_index == 25:
            self.next_btn.setText("All Done  ✓")
            self.next_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['success']};
                    color: white;
                    border: none; border-radius: 8px;
                    font-size: 13px; font-weight: 700;
                    padding: 4px 14px;
                }}
                QPushButton:hover {{
                    background: {COLORS['success']}dd;
                }}
            """)
        else:
            self.next_btn.setText("Next Letter  ▶")
            self.next_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px; font-weight: 700;
                    padding: 4px 14px;
                }}
                QPushButton:hover {{
                    background: {COLORS['primary_hover']};
                }}
            """)

        # Reset feedback when changing letters
        if self._camera_widget and self._camera_widget.is_running:
            self.feedback_label.setText(f"👀 Now try signing '{letter}'")
            self.feedback_label.setStyleSheet(f"""
                font-size: 14px; font-weight: 600;
                color: {COLORS['text_secondary']};
                background: {COLORS['bg_input']};
                padding: 10px; border-radius: 8px;
            """)

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
        self._hold_count = 0
        self._update_display()

    def showEvent(self, event):
        """Auto-start camera when lesson is shown."""
        super().showEvent(event)
        self._start_camera()

    def hideEvent(self, event):
        """Stop camera when lesson is hidden."""
        super().hideEvent(event)
        self._stop_camera()


# ─────────────────────────────────────────────────────────────
# Lightweight looping video player for gesture demo clips
# ─────────────────────────────────────────────────────────────

class _SignVideoPlayer(QFrame):
    """Minimal looping video player embedded in tutorial cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._playing = False
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #000;
                border-radius: 10px;
                border: 1.5px solid rgba(255,255,255,0.08);
            }
        """)
        self.setFixedHeight(190)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._lbl = QLabel()
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setStyleSheet("background: transparent;")
        layout.addWidget(self._lbl, 1)

        # Minimal controls row
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(6, 0, 6, 4)

        self._status_lbl = QLabel("🎬 Demo")
        self._status_lbl.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 10px; background: transparent;")
        ctrl.addWidget(self._status_lbl)
        ctrl.addStretch()

        self._play_btn = QPushButton("⏸")
        self._play_btn.setFixedSize(26, 22)
        self._play_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.30); }
        """)
        self._play_btn.clicked.connect(self._toggle)
        ctrl.addWidget(self._play_btn)
        layout.addLayout(ctrl)

    # ------------------------------------------------------------------

    def load(self, path: str):
        """Load *path* and auto-play.  Pass empty string to hide."""
        self._stop_cap()
        if path and os.path.exists(path):
            self._cap = cv2.VideoCapture(path)
            if self._cap.isOpened():
                fps = self._cap.get(cv2.CAP_PROP_FPS) or 24
                self._timer.start(max(16, int(1000 / fps)))
                self._playing = True
                self._play_btn.setText("⏸")
                self._status_lbl.setText("🎬 Demo")
                self.show()
                return
        # No valid video
        self._cap = None
        self.hide()

    def cleanup(self):
        self._stop_cap()

    # ------------------------------------------------------------------

    def _next_frame(self):
        if not self._cap or not self._playing:
            return
        ret, frame = self._cap.read()
        if not ret:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
            if not ret:
                return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        qi = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qi).scaled(
            self._lbl.width() or 310, 175,
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self._lbl.setPixmap(pix)

    def _toggle(self):
        if self._playing:
            self._playing = False
            self._timer.stop()
            self._play_btn.setText("▶")
        else:
            if self._cap:
                self._playing = True
                fps = self._cap.get(cv2.CAP_PROP_FPS) or 24
                self._timer.start(max(16, int(1000 / fps)))
                self._play_btn.setText("⏸")

    def _stop_cap(self):
        self._timer.stop()
        self._playing = False
        if self._cap:
            self._cap.release()
            self._cap = None


# ─────────────────────────────────────────────────────────────
# Generic phrase / word lesson — reusable for all non-alphabet
# lessons: Numbers, Greetings, Basics, Questions, etc.
# ─────────────────────────────────────────────────────────────

class _PhraseLesson(QWidget):
    """A reusable lesson widget that shows a list of items with
    emoji, name, description, detailed steps, and a spelling helper
    that shows each letter with the SignCard.

    Subclasses just set TITLE, ICON, and DATA.
    """

    back_requested = Signal()

    TITLE = ""
    ICON  = ""
    DATA  = []   # list of dicts: {name, emoji, desc, steps, tip?}
    ASSETS_FOLDER = ""  # subclasses set e.g. 'numbers', 'alphabets'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = 0
        self._camera_widget = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)

        title = QLabel(f"{self.ICON} {self.TITLE}")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()

        self._indicator = QLabel()
        self._indicator.setStyleSheet(f"""
            font-size: 12px; font-weight: 600;
            color: {COLORS['primary']};
            background: {COLORS['primary']}20;
            padding: 3px 10px; border-radius: 6px;
        """)
        header.addWidget(self._indicator)
        layout.addLayout(header)

        # Progress (compact)
        prog_row = QHBoxLayout()
        self._prog_bar = QProgressBar()
        self._prog_bar.setMaximum(max(len(self.DATA), 1))
        self._prog_bar.setFixedHeight(5)
        self._prog_bar.setTextVisible(False)
        self._prog_bar.setStyleSheet(f"""
            QProgressBar {{ background: {COLORS['bg_input']}; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {COLORS['primary']}; border-radius: 2px; }}
        """)
        prog_row.addWidget(self._prog_bar)
        self._prog_lbl = QLabel()
        self._prog_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        prog_row.addWidget(self._prog_lbl)
        layout.addLayout(prog_row)

        # Two-column layout (no scroll)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # LEFT: Info + Steps
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 10, 12, 10)
        left_layout.setSpacing(4)

        top = QHBoxLayout()
        self._emoji = QLabel()
        self._emoji.setStyleSheet("font-size: 32px; background: transparent;")
        top.addWidget(self._emoji)
        self._name = QLabel()
        self._name.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {COLORS['text_primary']}; background: transparent;")
        top.addWidget(self._name)
        top.addStretch()
        left_layout.addLayout(top)

        self._desc = QLabel()
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet(f"""
            font-size: 12px; color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']}; padding: 6px 10px; border-radius: 8px;
        """)
        left_layout.addWidget(self._desc)

        self._step_labels = []
        for _ in range(6):
            s = QLabel()
            s.setWordWrap(True)
            s.setStyleSheet(f"""
                font-size: 11px; color: {COLORS['text_primary']};
                background: {COLORS['bg_card']};
                padding: 4px 8px; border-radius: 6px;
                border-left: 3px solid {COLORS['primary']};
            """)
            left_layout.addWidget(s)
            self._step_labels.append(s)

        self._tip = QLabel()
        self._tip.setWordWrap(True)
        self._tip.setStyleSheet(f"""
            font-size: 11px; font-weight: 600; color: {COLORS['primary']};
            background: {COLORS['primary']}12; padding: 6px 10px; border-radius: 6px;
        """)
        left_layout.addWidget(self._tip)
        left_layout.addStretch()
        content_layout.addWidget(left_panel, 1)

        # RIGHT: Reference photo + Spelling + SignCard
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_panel.setFixedWidth(340)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(6)

        # ── Video demo player (shown when a gesture video is available) ──
        self._video_player = _SignVideoPlayer()
        right_layout.addWidget(self._video_player)
        self._video_player.hide()  # hidden until a video is loaded

        # Reference photo at the top of right panel — always clearly visible
        self._ref_img_frame = QFrame()
        self._ref_img_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['bg_card']}, stop:1 {COLORS['bg_input']});
                border-radius: 14px;
                border: 1.5px solid {COLORS['primary']}50;
            }}
        """)
        ref_inner = QVBoxLayout(self._ref_img_frame)
        ref_inner.setContentsMargins(8, 8, 8, 8)
        ref_inner.setSpacing(4)
        ref_inner.setAlignment(Qt.AlignCenter)
        ref_title = QLabel("📸  Reference Photo")
        ref_title.setAlignment(Qt.AlignCenter)
        ref_title.setStyleSheet(f"""
            font-size: 12px; font-weight: 700;
            color: {COLORS['primary']}; background: transparent;
        """)
        ref_inner.addWidget(ref_title)
        self._phrase_ref_img = QLabel()
        self._phrase_ref_img.setAlignment(Qt.AlignCenter)
        self._phrase_ref_img.setFixedHeight(160)
        self._phrase_ref_img.setStyleSheet("background: transparent;")
        self._phrase_ref_img.setScaledContents(False)
        ref_inner.addWidget(self._phrase_ref_img)
        right_layout.addWidget(self._ref_img_frame)
        self._ref_img_frame.hide()  # shown when an image is found

        spell_title = QLabel("🔤 Finger-Spell It")
        spell_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_primary']}; background: transparent;")
        right_layout.addWidget(spell_title)

        self._spell_desc = QLabel()
        self._spell_desc.setStyleSheet(f"font-size: 10px; color: {COLORS['text_muted']}; background: transparent;")
        self._spell_desc.setWordWrap(True)
        right_layout.addWidget(self._spell_desc)

        self._letter_btn_container = QWidget()
        self._letter_btn_layout = QHBoxLayout(self._letter_btn_container)
        self._letter_btn_layout.setContentsMargins(0, 0, 0, 0)
        self._letter_btn_layout.setSpacing(3)
        right_layout.addWidget(self._letter_btn_container)

        self._sign_card = SignCard("")
        right_layout.addWidget(self._sign_card)
        right_layout.addStretch()
        content_layout.addWidget(right_panel)

        # CAMERA COLUMN: Live practice camera
        cam_panel = QFrame()
        cam_panel.setObjectName("card")
        cam_panel.setMinimumWidth(380)
        cam_layout = QVBoxLayout(cam_panel)
        cam_layout.setContentsMargins(10, 10, 10, 10)
        cam_layout.setSpacing(6)

        cam_title = QLabel("📷 Practice with Camera")
        cam_title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {COLORS['primary']}; background: transparent;")
        cam_layout.addWidget(cam_title)

        self._cam_container = QFrame()
        self._cam_container.setStyleSheet(f"""
            background: #000;
            border-radius: 10px;
            min-height: 280px;
        """)
        self._cam_container.setMinimumHeight(300)
        cam_inner = QVBoxLayout(self._cam_container)
        cam_inner.setContentsMargins(0, 0, 0, 0)

        self._cam_placeholder = QLabel("Camera loading...")
        self._cam_placeholder.setAlignment(Qt.AlignCenter)
        self._cam_placeholder.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        cam_inner.addWidget(self._cam_placeholder)

        cam_layout.addWidget(self._cam_container)

        self._cam_feedback = QLabel("👆 Show the sign to practice")
        self._cam_feedback.setAlignment(Qt.AlignCenter)
        self._cam_feedback.setStyleSheet(f"""
            font-size: 13px; font-weight: 600;
            color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']};
            padding: 8px; border-radius: 8px;
        """)
        cam_layout.addWidget(self._cam_feedback)
        cam_layout.addStretch()

        content_layout.addWidget(cam_panel)

        layout.addLayout(content_layout, 1)

        # Navigation bar
        nav_frame = QFrame()
        nav_frame.setObjectName("phraseNavFrame")
        nav_frame.setStyleSheet(f"""
            QFrame#phraseNavFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        nav_inner = QHBoxLayout(nav_frame)
        nav_inner.setContentsMargins(12, 8, 12, 8)

        self._prev_btn = QPushButton("◀  Previous")
        self._prev_btn.setMinimumWidth(120)
        self._prev_btn.setFixedHeight(36)
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 13px; font-weight: 600;
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary']};
                color: white;
                border-color: {COLORS['primary']};
            }}
            QPushButton:disabled {{
                opacity: 0.4;
                color: {COLORS['text_muted']};
            }}
        """)
        self._prev_btn.clicked.connect(self._prev)
        nav_inner.addWidget(self._prev_btn)

        nav_inner.addStretch()

        self._nav_indicator = QLabel()
        self._nav_indicator.setAlignment(Qt.AlignCenter)
        self._nav_indicator.setStyleSheet(f"""
            font-size: 13px; font-weight: 700;
            color: {COLORS['text_secondary']};
            background: {COLORS['bg_input']};
            padding: 4px 16px;
            border-radius: 8px;
        """)
        nav_inner.addWidget(self._nav_indicator)

        nav_inner.addStretch()

        self._next_btn = QPushButton("Next  ▶")
        self._next_btn.setMinimumWidth(120)
        self._next_btn.setFixedHeight(36)
        self._next_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px; font-weight: 700;
                padding: 4px 16px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        self._next_btn.clicked.connect(self._next)
        nav_inner.addWidget(self._next_btn)

        layout.addWidget(nav_frame)

        # Item jump buttons row (for quick navigation between items)
        self._item_jump_frame = QFrame()
        self._item_jump_frame.setObjectName("itemJumpFrame")
        self._item_jump_frame.setStyleSheet(f"""
            QFrame#itemJumpFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        jump_layout = QVBoxLayout(self._item_jump_frame)
        jump_layout.setContentsMargins(10, 6, 10, 8)
        jump_layout.setSpacing(4)

        jump_title = QLabel("📍 Jump to Item")
        jump_title.setAlignment(Qt.AlignCenter)
        jump_title.setStyleSheet(f"""
            font-size: 11px; font-weight: 600;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        jump_layout.addWidget(jump_title)

        self._item_btn_container = QWidget()
        self._item_btn_row = QHBoxLayout(self._item_btn_container)
        self._item_btn_row.setContentsMargins(0, 0, 0, 0)
        self._item_btn_row.setSpacing(4)
        self._item_jump_btns = []

        for idx, item in enumerate(self.DATA):
            label = item.get('name', str(idx))
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.setMinimumWidth(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"Jump to {label}")
            btn.clicked.connect(lambda checked, i=idx: self._jump_to_item(i))
            self._item_btn_row.addWidget(btn)
            self._item_jump_btns.append(btn)
        self._item_btn_row.addStretch()

        jump_layout.addWidget(self._item_btn_container, 0, Qt.AlignCenter)

        if len(self.DATA) > 1:
            layout.addWidget(self._item_jump_frame)

        self._refresh()

    def _refresh(self):
        if not self.DATA:
            return
        d = self.DATA[self._current]
        self._emoji.setText(d.get('emoji', ''))
        self._name.setText(d['name'])
        self._desc.setText(d.get('desc', ''))
        self._indicator.setText(f"{self._current + 1}/{len(self.DATA)}")
        self._prog_bar.setValue(self._current + 1)
        self._prog_lbl.setText(f"{self._current + 1}/{len(self.DATA)}")

        steps = d.get('steps', [])
        for i, lbl in enumerate(self._step_labels):
            if i < len(steps):
                lbl.setText(steps[i])
                lbl.show()
            else:
                lbl.hide()

        tip = d.get('tip', '')
        if tip:
            self._tip.setText(f"💡 {tip}")
            self._tip.show()
        else:
            self._tip.hide()

        # Load reference image if available
        self._load_phrase_ref_image(d['name'])

        # Load gesture demo video if available
        self._video_player.load(self._find_gesture_video(d['name']))

        # Spelling buttons
        # Clear old buttons
        while self._letter_btn_layout.count():
            item = self._letter_btn_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        spell_word = d['name'].upper()
        letters_only = [c for c in spell_word if c.isalpha()]
        self._spell_desc.setText(f'Tap a letter to see its sign — spell "{d["name"]}"')
        for ch in spell_word:
            if ch.isalpha():
                btn = QPushButton(ch)
                btn.setFixedSize(28, 28)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {COLORS['bg_input']};
                        color: {COLORS['text_primary']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 5px; font-size: 11px; font-weight: 700;
                    }}
                    QPushButton:hover {{
                        background: {COLORS['primary']}; color: white;
                    }}
                """)
                btn.clicked.connect(lambda checked, c=ch: self._sign_card.set_letter(c))
                self._letter_btn_layout.addWidget(btn)
            else:
                spacer = QLabel("  ")
                spacer.setStyleSheet("background: transparent; font-size: 14px;")
                self._letter_btn_layout.addWidget(spacer)
        self._letter_btn_layout.addStretch()

        # Show first letter by default
        if letters_only:
            self._sign_card.set_letter(letters_only[0])

        self._prev_btn.setEnabled(self._current > 0)
        if self._current >= len(self.DATA) - 1:
            self._next_btn.setText("Complete  ✓")
            self._next_btn.setMinimumWidth(130)
            self._next_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['success']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px; font-weight: 700;
                    padding: 4px 18px;
                }}
                QPushButton:hover {{
                    background: {COLORS['success']}dd;
                }}
            """)
        else:
            self._next_btn.setText("Next  ▶")
            self._next_btn.setMinimumWidth(120)
            self._next_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px; font-weight: 700;
                    padding: 4px 16px;
                }}
                QPushButton:hover {{
                    background: {COLORS['primary_hover']};
                }}
            """)

        # Update nav indicator
        if hasattr(self, '_nav_indicator'):
            self._nav_indicator.setText(f"Step {self._current + 1} of {len(self.DATA)}")

        # Update item jump buttons
        if hasattr(self, '_item_jump_btns'):
            for idx, btn in enumerate(self._item_jump_btns):
                if idx == self._current:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {COLORS['primary']};
                            color: white;
                            border: 2px solid {COLORS['primary_light']};
                            border-radius: 6px;
                            font-size: 12px; font-weight: bold;
                            padding: 2px 8px;
                            min-height: 24px;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {COLORS['bg_card']};
                            color: {COLORS['text_primary']};
                            border: 1px solid {COLORS['border_light']};
                            border-radius: 6px;
                            font-size: 12px; font-weight: bold;
                            padding: 2px 8px;
                            min-height: 24px;
                        }}
                        QPushButton:hover {{
                            background: {COLORS['primary']}30;
                            color: {COLORS['primary_light']};
                            border-color: {COLORS['primary']};
                        }}
                    """)

    def _load_phrase_ref_image(self, name: str):
        """Load a reference image from assets/<ASSETS_FOLDER>/ (and fallback folders) for the given item name."""
        assets_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), 'assets')
        search_folders = [self.ASSETS_FOLDER] if self.ASSETS_FOLDER else []
        for fb in ('asl_hands', 'numbers', 'alphabets'):
            if fb not in search_folders:
                search_folders.append(fb)
        all_matches = []
        seen = set()
        for sf in search_folders:
            base = os.path.join(assets_root, sf)
            for pat in [f'{name}.*', f'{name.lower()}.*', f'{name.upper()}.*']:
                for m in glob.glob(os.path.join(base, pat)):
                    if m not in seen:
                        seen.add(m)
                        all_matches.append(m)
        if all_matches:
            pixmap = QPixmap(all_matches[0])
            if not pixmap.isNull():
                # Scale to fit the fixed 160px tall display
                scaled = pixmap.scaled(
                    320, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._phrase_ref_img.setPixmap(scaled)
                self._ref_img_frame.show()
                return
        self._phrase_ref_img.clear()
        self._ref_img_frame.hide()

    def _find_gesture_video(self, name: str) -> str:
        """Return path to assets/gestures/<name>.mp4 if it exists, else ''."""
        gestures_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'assets', 'gestures',
        )
        for variant in [
            name.lower().replace(' ', ''),
            name.lower().replace(' ', '_'),
            name.lower(),
        ]:
            p = os.path.join(gestures_dir, f'{variant}.mp4')
            if os.path.exists(p):
                return p
        return ''

    def _prev(self):
        if self._current > 0:
            self._current -= 1
            self._refresh()

    def _next(self):
        if self._current < len(self.DATA) - 1:
            self._current += 1
            self._refresh()
        else:
            self.back_requested.emit()

    def _jump_to_item(self, index: int):
        """Jump to a specific item in the lesson."""
        if 0 <= index < len(self.DATA):
            self._current = index
            self._refresh()

    def cleanup(self):
        self._sign_card.cleanup()
        self._video_player.cleanup()
        self._stop_phrase_camera()

    def _start_phrase_camera(self):
        """Start the camera for practice."""
        try:
            from ui.camera_widget import CameraWidget
        except ImportError:
            return

        if self._camera_widget is None:
            self._camera_widget = CameraWidget()
            self._camera_widget.setMinimumSize(360, 280)
            self._camera_widget.video_label.setMinimumSize(360, 280)
            self._camera_widget.heuristic_threshold = 0.35

            self._cam_placeholder.hide()
            self._cam_container.layout().addWidget(self._camera_widget)

        self._camera_widget.start()
        self._cam_feedback.setText("👀 Show the sign to the camera...")

    def _stop_phrase_camera(self):
        """Stop the camera."""
        if self._camera_widget:
            self._camera_widget.stop()

    def showEvent(self, event):
        """Auto-start camera and video demo when lesson is shown."""
        super().showEvent(event)
        self._start_phrase_camera()
        if self.DATA:
            self._video_player.load(self._find_gesture_video(self.DATA[self._current]['name']))

    def hideEvent(self, event):
        """Stop camera when lesson is hidden."""
        super().hideEvent(event)
        self._video_player.cleanup()
        self._stop_phrase_camera()


# ─── Numbers ────────────────────────────────────────────────

class NumbersLesson(_PhraseLesson):
    TITLE = "Numbers 0-9"
    ICON  = "🔢"
    ASSETS_FOLDER = "numbers"
    DATA  = [
        {
            'name': '0', 'emoji': '👌',
            'desc': 'All fingers form an O shape — same hand shape as the letter O.',
            'steps': [
                '1️⃣  Curve all your fingers together',
                '2️⃣  Touch ALL fingertips to your thumb tip (makes a circle)',
                '3️⃣  Your hand looks like a round O — that\'s zero!',
            ],
            'tip': 'This is identical to the letter O in ASL!',
        },
        {
            'name': '1', 'emoji': '☝️',
            'desc': 'Index finger pointing straight up — everything else closed.',
            'steps': [
                '1️⃣  Make a fist',
                '2️⃣  Extend ONLY your index finger straight up',
                '3️⃣  Thumb wraps across other fingers — done!',
            ],
        },
        {
            'name': '2', 'emoji': '✌️',
            'desc': 'Peace/victory sign — index and middle fingers up and apart.',
            'steps': [
                '1️⃣  Make a fist',
                '2️⃣  Extend index + middle fingers UP',
                '3️⃣  Spread them apart in a V shape',
            ],
            'tip': 'Same as the letter V in ASL!',
        },
        {
            'name': '3', 'emoji': '🤟',
            'desc': 'Thumb, index, and middle finger all extended.',
            'steps': [
                '1️⃣  Extend your THUMB out to the side',
                '2️⃣  Extend INDEX + MIDDLE fingers straight up',
                '3️⃣  Curl ring + pinky down',
            ],
            'tip': 'This looks like an "OK" but with the thumb out too.',
        },
        {
            'name': '4', 'emoji': '🖐️',
            'desc': 'Four fingers up, thumb tucked across the palm.',
            'steps': [
                '1️⃣  Hold up all 4 fingers (index through pinky)',
                '2️⃣  Spread them slightly apart',
                '3️⃣  Fold your thumb DOWN across your palm',
            ],
            'tip': 'Same as the letter B but with fingers spread!',
        },
        {
            'name': '5', 'emoji': '🖐️',
            'desc': 'All five fingers wide open — the full "high five" hand.',
            'steps': [
                '1️⃣  Spread ALL five fingers wide open',
                '2️⃣  Include your thumb — stick it out to the side',
                '3️⃣  Like you\'re giving a high five — nice and wide!',
            ],
        },
        {
            'name': '6', 'emoji': '🤙',
            'desc': 'Pinky touches thumb; index, middle, ring stay up.',
            'steps': [
                '1️⃣  Hold index, middle, and ring fingers UP',
                '2️⃣  Bring your PINKY down to touch your THUMB tip',
                '3️⃣  They should form a small circle at the bottom',
            ],
            'tip': 'Think of "hang loose" 🤙 but upright with 3 fingers up.',
        },
        {
            'name': '7', 'emoji': '🖐️',
            'desc': 'Ring finger touches thumb; index, middle, pinky stay up.',
            'steps': [
                '1️⃣  Hold index, middle, and pinky fingers UP',
                '2️⃣  Bring your RING finger down to touch your THUMB tip',
                '3️⃣  The ring finger + thumb make a small circle',
            ],
        },
        {
            'name': '8', 'emoji': '🖐️',
            'desc': 'Middle finger touches thumb; index, ring, pinky stay up.',
            'steps': [
                '1️⃣  Hold index, ring, and pinky fingers UP',
                '2️⃣  Bring your MIDDLE finger down to touch your THUMB tip',
                '3️⃣  The middle finger + thumb make a small circle',
            ],
        },
        {
            'name': '9', 'emoji': '👌',
            'desc': 'Index finger touches thumb (OK sign); middle, ring, pinky stay up.',
            'steps': [
                '1️⃣  Touch your INDEX fingertip to your THUMB tip',
                '2️⃣  This forms the "OK" circle',
                '3️⃣  Extend middle, ring, and pinky UP',
            ],
            'tip': 'Same as the letter F in ASL!',
        },
    ]


# ─── Greetings ──────────────────────────────────────────────

class GreetingsLesson(_PhraseLesson):
    TITLE = "Greetings"
    ICON  = "👋"
    DATA  = [
        {
            'name': 'Hello', 'emoji': '👋',
            'desc': 'A flat-hand salute that moves away from your forehead.',
            'steps': [
                '1️⃣  Hold your dominant hand flat (fingers together, like a salute)',
                '2️⃣  Bring the fingertips to your forehead (near your temple)',
                '3️⃣  Move your hand forward and slightly outward — like a friendly wave!',
            ],
            'tip': 'This is the same motion as a casual military salute.',
        },
        {
            'name': 'Goodbye', 'emoji': '👋',
            'desc': 'Open your hand and wave — just like a regular goodbye wave!',
            'steps': [
                '1️⃣  Open your hand with all fingers spread',
                '2️⃣  Face your palm toward the other person',
                '3️⃣  Wave your hand back and forth — bye-bye!',
            ],
        },
        {
            'name': 'Nice to meet you', 'emoji': '🤝',
            'desc': 'A 3-part phrase: NICE + MEET + YOU.',
            'steps': [
                '1️⃣  NICE: Slide your dominant flat hand across your other flat palm (like brushing crumbs off)',
                '2️⃣  MEET: Both index fingers point up and come together, meeting in the middle',
                '3️⃣  YOU: Point your index finger at the other person',
            ],
            'tip': 'Practice each part separately, then combine them smoothly.',
        },
        {
            'name': 'Good morning', 'emoji': '🌅',
            'desc': 'GOOD + MORNING: flat hand from chin forward, then arm rises like the sun.',
            'steps': [
                '1️⃣  GOOD: Touch your chin with a flat hand, then move it forward and down onto your other palm',
                '2️⃣  MORNING: Place your non-dominant hand flat (horizon), rest your dominant elbow on it',
                '3️⃣  Raise your dominant flat hand upward — like the sun rising over the horizon!',
            ],
        },
        {
            'name': 'Good night', 'emoji': '🌙',
            'desc': 'GOOD + NIGHT: flat hand from chin, then hand bends down like the sun setting.',
            'steps': [
                '1️⃣  GOOD: Same as above — flat hand from chin to palm',
                '2️⃣  NIGHT: Hold non-dominant arm flat (horizon)',
                '3️⃣  Bend your dominant hand downward over it — like the sun going down',
            ],
        },
        {
            'name': 'How are you', 'emoji': '😊',
            'desc': 'HOW + YOU: bent hands move outward, then point at the person.',
            'steps': [
                '1️⃣  HOW: Hold both fists knuckles-together, then roll them forward and open your fingers',
                '2️⃣  YOU: Point your index finger at the other person',
                '3️⃣  Add a questioning facial expression (raised eyebrows)!',
            ],
            'tip': 'In ASL, facial expressions are part of the grammar — raise your eyebrows for questions!',
        },
    ]


# ─── Basic Words ─────────────────────────────────────────────

class BasicsLesson(_PhraseLesson):
    TITLE = "Basic Words"
    ICON  = "💬"
    DATA  = [
        {
            'name': 'Yes', 'emoji': '✅',
            'desc': 'Make a fist and nod it up and down — like your hand is nodding "yes"!',
            'steps': [
                '1️⃣  Make a fist (like the letter S)',
                '2️⃣  Bend your wrist DOWN, then UP repeatedly',
                '3️⃣  It looks like your fist is nodding — yes, yes, yes!',
            ],
        },
        {
            'name': 'No', 'emoji': '❌',
            'desc': 'Snap your index + middle finger against your thumb — like a tiny mouth saying "no".',
            'steps': [
                '1️⃣  Extend your index + middle fingers (and thumb)',
                '2️⃣  Bring them together to your thumb quickly, like a snap',
                '3️⃣  Do it once or twice — like a little beak closing shut',
            ],
        },
        {
            'name': 'Please', 'emoji': '🙏',
            'desc': 'Flat hand circles on your chest — like rubbing your heart.',
            'steps': [
                '1️⃣  Place your flat hand on the center of your chest',
                '2️⃣  Move it in a circular motion (clockwise)',
                '3️⃣  Keep a polite facial expression!',
            ],
            'tip': 'The circular motion is important — it shows sincerity.',
        },
        {
            'name': 'Thank you', 'emoji': '🙏',
            'desc': 'Flat hand touches chin, then moves forward — like blowing a kiss of thanks.',
            'steps': [
                '1️⃣  Touch your chin (or lips) with your flat fingertips',
                '2️⃣  Move your hand forward and slightly down, away from your face',
                '3️⃣  Like you\'re sending a "thank you" out to the person',
            ],
        },
        {
            'name': 'Sorry', 'emoji': '😔',
            'desc': 'Make a fist and rub it in a circle on your chest.',
            'steps': [
                '1️⃣  Make a fist (letter A shape — thumb on the side)',
                '2️⃣  Place it on the center of your chest',
                '3️⃣  Rub in a circular motion — shows you feel regret',
            ],
            'tip': 'Use a sincere facial expression — it matters in ASL!',
        },
        {
            'name': 'Excuse me', 'emoji': '🤚',
            'desc': 'Brush your non-dominant flat hand with your dominant fingertips.',
            'steps': [
                '1️⃣  Hold your non-dominant hand flat, palm up',
                '2️⃣  Place your dominant fingertips on it',
                '3️⃣  Brush your fingertips across the palm twice — like gently sweeping',
            ],
        },
    ]


# ─── Question Words ─────────────────────────────────────────

class QuestionsLesson(_PhraseLesson):
    TITLE = "Question Words"
    ICON  = "❓"
    DATA  = [
        {
            'name': 'What', 'emoji': '❓',
            'desc': 'Index finger slides down across your other open palm.',
            'steps': [
                '1️⃣  Hold your non-dominant hand flat, palm up',
                '2️⃣  Point your dominant index finger down',
                '3️⃣  Slide it across the open palm from one side to the other',
            ],
            'tip': 'Furrow your eyebrows for WH- questions (what, where, who, etc.).',
        },
        {
            'name': 'Where', 'emoji': '📍',
            'desc': 'Point your index finger and wave it side to side.',
            'steps': [
                '1️⃣  Point your index finger up (like number 1)',
                '2️⃣  Wave it side to side — left, right, left',
                '3️⃣  Furrow your eyebrows with a questioning look',
            ],
        },
        {
            'name': 'When', 'emoji': '⏰',
            'desc': 'Circle your index finger around your other index finger, then land on it.',
            'steps': [
                '1️⃣  Hold your non-dominant index finger up (like a pole)',
                '2️⃣  Circle your dominant index finger around it',
                '3️⃣  Land your dominant index finger on top of the other one',
            ],
        },
        {
            'name': 'Why', 'emoji': '🤔',
            'desc': 'Touch your forehead, then form a Y hand shape moving outward.',
            'steps': [
                '1️⃣  Touch your forehead with your middle fingertip',
                '2️⃣  Pull your hand away while shifting to a Y shape (thumb + pinky out)',
                '3️⃣  The motion goes: forehead → outward + Y hand',
            ],
        },
        {
            'name': 'How', 'emoji': '🔧',
            'desc': 'Both fists roll forward and open up.',
            'steps': [
                '1️⃣  Hold both hands in fists, knuckles touching each other',
                '2️⃣  Roll them forward (away from you)',
                '3️⃣  As they roll, open your fingers — like unfolding something',
            ],
        },
        {
            'name': 'Who', 'emoji': '🧑',
            'desc': 'Circle your index finger around your puckered lips.',
            'steps': [
                '1️⃣  Pucker your lips slightly',
                '2️⃣  Point your index finger at your lips',
                '3️⃣  Circle it around your mouth area — like asking "who?"',
            ],
            'tip': 'Pucker your lips — this is part of the ASL grammar for "who".',
        },
    ]


# ─── Emotions ───────────────────────────────────────────────

class EmotionsLesson(_PhraseLesson):
    TITLE = "Emotions"
    ICON  = "😊"
    DATA  = [
        {
            'name': 'Happy', 'emoji': '😄',
            'desc': 'Flat hand brushes UP your chest repeatedly — happiness rises!',
            'steps': [
                '1️⃣  Place your flat hand on your chest',
                '2️⃣  Brush it UPWARD with a quick, light motion',
                '3️⃣  Repeat twice — the upward motion shows happiness rising!',
            ],
            'tip': 'Smile while signing — facial expressions are essential!',
        },
        {
            'name': 'Sad', 'emoji': '😢',
            'desc': 'Both open hands slide DOWN your face — like tears falling.',
            'steps': [
                '1️⃣  Hold both hands open in front of your face, palms facing inward',
                '2️⃣  Move them DOWNWARD slowly',
                '3️⃣  Make a sad facial expression — drooping face, frown',
            ],
        },
        {
            'name': 'Angry', 'emoji': '😡',
            'desc': 'Claw hand pulls away from your face — frustration bursting out!',
            'steps': [
                '1️⃣  Hold your hand in a "claw" shape (fingers spread and bent) near your face',
                '2️⃣  Pull it sharply AWAY from your face',
                '3️⃣  Show an angry expression — it\'s crucial for this sign!',
            ],
        },
        {
            'name': 'Scared', 'emoji': '😨',
            'desc': 'Both fists open suddenly in front of your chest — like getting startled!',
            'steps': [
                '1️⃣  Hold both fists near your chest',
                '2️⃣  Suddenly OPEN both hands (spread fingers wide)',
                '3️⃣  Move them slightly forward — like a flinch reaction',
            ],
            'tip': 'Widen your eyes and look startled — the expression sells it!',
        },
        {
            'name': 'Excited', 'emoji': '🤩',
            'desc': 'Both middle fingers brush UP on your chest alternately — energy!',
            'steps': [
                '1️⃣  Bend both middle fingers (others tucked)',
                '2️⃣  Place them on your chest',
                '3️⃣  Brush them upward in alternating circles — showing building excitement!',
            ],
        },
        {
            'name': 'Love', 'emoji': '❤️',
            'desc': 'Cross both fists (or hands) over your heart.',
            'steps': [
                '1️⃣  Make fists with both hands',
                '2️⃣  Cross your arms over your chest (like a hug)',
                '3️⃣  Press them against your heart — showing love!',
            ],
            'tip': 'You can also sign I-L-Y (I Love You): thumb + index + pinky out at once 🤟',
        },
    ]


# ─── Family ─────────────────────────────────────────────────

class FamilyLesson(_PhraseLesson):
    TITLE = "Family"
    ICON  = "👨‍👩‍👧‍👦"
    DATA  = [
        {
            'name': 'Mom', 'emoji': '👩',
            'desc': 'Thumb taps your chin — the CHIN area = female signs in ASL.',
            'steps': [
                '1️⃣  Open your hand with fingers spread (number 5 shape)',
                '2️⃣  Tap your THUMB against your CHIN',
                '3️⃣  Tap twice — that\'s mom!',
            ],
            'tip': 'In ASL, female family signs are near the CHIN, male ones near the FOREHEAD.',
        },
        {
            'name': 'Dad', 'emoji': '👨',
            'desc': 'Thumb taps your forehead — the FOREHEAD area = male signs in ASL.',
            'steps': [
                '1️⃣  Open your hand with fingers spread (number 5 shape)',
                '2️⃣  Tap your THUMB against your FOREHEAD',
                '3️⃣  Tap twice — that\'s dad!',
            ],
        },
        {
            'name': 'Sister', 'emoji': '👧',
            'desc': 'GIRL + SAME: thumb along chin, then both index fingers side by side.',
            'steps': [
                '1️⃣  GIRL: Trace your thumb along your jawline (chin area)',
                '2️⃣  SAME: Hold both hands as fists with index fingers pointing out',
                '3️⃣  Bring them together side by side — "same" = sibling, chin = girl → sister!',
            ],
        },
        {
            'name': 'Brother', 'emoji': '👦',
            'desc': 'BOY + SAME: thumb along forehead, then both index fingers side by side.',
            'steps': [
                '1️⃣  BOY: Pretend to grab a baseball cap brim at your forehead',
                '2️⃣  SAME: Hold both fists with index fingers pointing out',
                '3️⃣  Bring them together side by side — forehead = boy, same = sibling → brother!',
            ],
        },
        {
            'name': 'Baby', 'emoji': '👶',
            'desc': 'Rock your arms like you\'re cradling a baby.',
            'steps': [
                '1️⃣  Place one arm on top of the other (like holding a baby)',
                '2️⃣  Rock your arms gently side to side',
                '3️⃣  Just like rocking a real baby to sleep!',
            ],
        },
        {
            'name': 'Family', 'emoji': '👨‍👩‍👧‍👦',
            'desc': 'Both hands make F shapes and circle around to meet — a family circle!',
            'steps': [
                '1️⃣  Both hands make the letter F (thumb + index circle, 3 fingers up)',
                '2️⃣  Start with them touching in front of you',
                '3️⃣  Circle them outward and around until the pinkies touch — a complete family circle!',
            ],
        },
    ]


# ─── Common Actions ─────────────────────────────────────────

class ActionsLesson(_PhraseLesson):
    TITLE = "Common Actions"
    ICON  = "🏃"
    DATA  = [
        {
            'name': 'Help', 'emoji': '🆘',
            'desc': 'Fist on flat palm, both rise together — one hand lifting the other.',
            'steps': [
                '1️⃣  Make a fist with your dominant hand (thumbs-up position)',
                '2️⃣  Place it on your non-dominant flat palm',
                '3️⃣  Lift BOTH hands up together — like boosting someone up!',
            ],
        },
        {
            'name': 'Want', 'emoji': '🤲',
            'desc': 'Both hands reach forward with spread bent fingers, then pull toward you.',
            'steps': [
                '1️⃣  Hold both hands out, palms up, fingers spread and slightly bent (claw shape)',
                '2️⃣  Pull both hands toward your body',
                '3️⃣  Like you\'re pulling something you want toward you!',
            ],
        },
        {
            'name': 'Need', 'emoji': '💪',
            'desc': 'Bent index finger (X shape) bends downward — firm and urgent.',
            'steps': [
                '1️⃣  Make an X hand shape (index finger hooked)',
                '2️⃣  Hold it in front of you',
                '3️⃣  Bend your wrist downward firmly — showing urgency/need',
            ],
        },
        {
            'name': 'Stop', 'emoji': '🛑',
            'desc': 'Flat hand chops down onto your other flat palm — a firm stop.',
            'steps': [
                '1️⃣  Hold your non-dominant hand flat, palm facing up',
                '2️⃣  Bring your dominant flat hand DOWN sharply',
                '3️⃣  Chop it onto the other palm — like a karate chop = STOP!',
            ],
        },
        {
            'name': 'Go', 'emoji': '🏃',
            'desc': 'Both index fingers point forward and flick outward — GO!',
            'steps': [
                '1️⃣  Point both index fingers forward',
                '2️⃣  Bend them slightly (like they\'re bent at the knuckle)',
                '3️⃣  Flick them forward — like launching something — GO!',
            ],
        },
        {
            'name': 'Like', 'emoji': '👍',
            'desc': 'Thumb and middle finger pull away from your chest — like pulling heartstrings.',
            'steps': [
                '1️⃣  Place your thumb and middle finger on your chest (others extended)',
                '2️⃣  Pull them forward, bringing thumb and middle together',
                '3️⃣  Like pulling a thread from your heart — you LIKE it!',
            ],
            'tip': 'The sign starts at your heart because "liking" is a feeling!',
        },
    ]


# ─────────────────────────────────────────────────────────────
# CommonSignsLesson — the 10 essential ASL signs
# ─────────────────────────────────────────────────────────────

class CommonSignsLesson(_PhraseLesson):
    """The only lesson available: 10 essential everyday ASL signs."""
    TITLE = "Essential Signs"
    ICON  = "🤟"
    ASSETS_FOLDER = "asl_hands"
    DATA  = [
        {
            'name': 'Hello', 'emoji': '👋',
            'desc': 'A flat-hand salute that starts at your forehead and moves forward.',
            'steps': [
                '1️⃣  Hold your dominant hand flat, fingers together',
                '2️⃣  Bring your fingertips to the side of your forehead, like a salute',
                '3️⃣  Move your hand forward and outward — like a friendly wave!',
            ],
            'tip': 'Same motion as a casual military salute.',
            'video_path': None,
        },
        {
            'name': 'Thank you', 'emoji': '🙏',
            'desc': 'Flat hand touches your chin, then moves forward — like sending gratitude.',
            'steps': [
                '1️⃣  Hold your dominant hand flat, fingers together',
                '2️⃣  Touch your fingertips lightly to your chin or lips',
                '3️⃣  Move your hand forward and slightly downward, away from your face',
            ],
            'tip': "Like blowing a kiss of thanks toward the person.",
            'video_path': None,
        },
        {
            'name': 'Please', 'emoji': '🙏',
            'desc': 'Flat hand rubbed in a circle on your chest — like polishing your heart.',
            'steps': [
                '1️⃣  Place your flat dominant hand on the center of your chest',
                '2️⃣  Move it in a slow clockwise circle',
                '3️⃣  Keep a warm, polite facial expression',
            ],
            'tip': "The circular motion shows sincerity — don't skip it!",
            'video_path': None,
        },
        {
            'name': 'I', 'emoji': '👆',
            'desc': 'Point your index finger at yourself — simple and direct.',
            'steps': [
                '1️⃣  Extend your dominant index finger',
                '2️⃣  Point it toward your own chest (not your face)',
                '3️⃣  A small, clear point — no movement needed',
            ],
            'tip': 'In ASL, pointing at yourself means "I" or "me".',
            'video_path': None,
        },
        {
            'name': 'Yes', 'emoji': '✅',
            'desc': 'A fist that nods up and down — like your hand is saying YES!',
            'steps': [
                '1️⃣  Make a fist (like the letter S)',
                '2️⃣  Hold your arm comfortably in front of you',
                '3️⃣  Bend your wrist down then up, once or twice — like nodding',
            ],
            'tip': 'Nod your head along — it reinforces the meaning!',
            'video_path': None,
        },
        {
            'name': 'No', 'emoji': '❌',
            'desc': 'Index and middle fingers snap to the thumb — like a tiny beak saying NO.',
            'steps': [
                '1️⃣  Extend your index finger, middle finger, and thumb',
                '2️⃣  Quickly snap your index + middle fingers DOWN to meet your thumb',
                '3️⃣  Do this once or twice — like a beak opening and closing',
            ],
            'tip': 'Shake your head slightly — it adds emphasis in ASL!',
            'video_path': None,
        },
        {
            'name': 'Help', 'emoji': '🆘',
            'desc': 'A thumbs-up on a flat palm, lifted upward — like someone being helped up.',
            'steps': [
                '1️⃣  Make a thumbs-up (A-hand) with your dominant hand',
                '2️⃣  Rest it on top of your non-dominant flat palm',
                '3️⃣  Lift both hands upward together — like raising someone up',
            ],
            'tip': 'This sign visually shows one person assisting another.',
            'video_path': None,
        },
        {
            'name': 'Fine', 'emoji': '👍',
            'desc': 'Open hand (5 handshape), thumb touches chest — showing everything is fine.',
            'steps': [
                '1️⃣  Spread all five fingers open (5-hand)',
                '2️⃣  Turn your palm so it faces to the side, toward your body',
                '3️⃣  Touch your thumb lightly to the center of your chest once',
            ],
            'tip': 'A gentle thumb-to-chest touch — light and confident.',
            'video_path': None,
        },
        {
            'name': 'Bathroom', 'emoji': '🚻',
            'desc': 'The letter T hand shakes side to side — a discreet way to ask.',
            'steps': [
                '1️⃣  Make a T handshape: tuck your thumb between your index and middle fingers into a fist',
                '2️⃣  Hold your fist up at about chest or shoulder level',
                '3️⃣  Shake it gently side to side (left–right) two or three times',
            ],
            'tip': 'T stands for Toilet — widely recognized across ASL users.',
            'video_path': None,
        },
        {
            'name': 'More', 'emoji': '➕',
            'desc': 'Both flat-O hands tap fingertips together — asking for more.',
            'steps': [
                '1️⃣  Bring all fingers and thumb of each hand together into a flat-O (like pinching)',
                '2️⃣  Hold both hands in front of you at chest height',
                '3️⃣  Tap the fingertips of both hands together two or three times',
            ],
            'tip': 'Think of two pinches coming together — clean and clear!',
            'video_path': None,
        },
    ]


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
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("📚 Learn Sign Language")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Stacked widget
        self.stack = QStackedWidget()

        # Main lesson list
        self.lesson_list = self._create_lesson_list()
        self.stack.addWidget(self.lesson_list)

        # The only lesson: 10 Essential Signs
        self.common_lesson = CommonSignsLesson()
        self.common_lesson.back_requested.connect(self._show_lesson_list)
        self.stack.addWidget(self.common_lesson)

        layout.addWidget(self.stack)

    def _create_lesson_list(self) -> QWidget:
        """Create the lesson home page."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Welcome banner
        welcome = QFrame()
        welcome.setObjectName("card")
        welcome_layout = QHBoxLayout(welcome)
        welcome_layout.setContentsMargins(20, 12, 20, 12)

        welcome_title = QLabel("👋 Welcome to ASL Learning!")
        welcome_title.setStyleSheet(f"font-size: 17px; font-weight: 600; color: {COLORS['text_primary']};")
        welcome_layout.addWidget(welcome_title)

        welcome_text = QLabel("Learn 10 essential everyday signs with visual guides and step-by-step instructions.")
        welcome_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        welcome_layout.addWidget(welcome_text, 1)

        layout.addWidget(welcome)

        # Single lesson card
        card = LessonCard(
            "common_signs",
            "Essential Signs",
            "Hello · Thank you · Please · I · Yes · No · Help · Fine · Bathroom · More",
            "🤟",
            0,
        )
        card.clicked.connect(self._open_lesson)
        self.lesson_cards = {"common_signs": card}

        card_row = QHBoxLayout()
        card_row.addWidget(card)
        card_row.addStretch()
        layout.addLayout(card_row)

        tips_lbl = QLabel("💡 Practice signs often · Use Live Translation to check · Pay attention to hand orientation")
        tips_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; padding: 6px 8px;")
        tips_lbl.setWordWrap(True)
        layout.addWidget(tips_lbl)

        layout.addStretch()
        return widget

    def _open_lesson(self, lesson_id: str):
        """Open a lesson."""
        if lesson_id == "common_signs":
            self.common_lesson._current = 0
            self.common_lesson._refresh()
            self.stack.setCurrentWidget(self.common_lesson)

    def get_progress(self, lesson_id: str) -> int:
        return 0

    def _show_lesson_list(self):
        """Return to the lesson list."""
        if hasattr(self, 'lesson_cards'):
            for lid, card in self.lesson_cards.items():
                card.update_progress(self.get_progress(lid))
        self.stack.setCurrentWidget(self.lesson_list)
