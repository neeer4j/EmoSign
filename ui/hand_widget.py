"""
Animated Hand Widget for ASL Letter Visualization  (v5 — finger status bars)

Instead of a QPainter-drawn hand (which looks unrecognizable), this uses
clean, styled QWidget bars for each finger — tall = up, short = down.
Think of it like a simple equalizer showing finger positions.

People can instantly understand: "oh, these fingers are up, these are down"
without trying to parse a distorted drawing.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

from ui.styles import COLORS


# ═══════════════════════════════════════════════════════════════
#  Finger state data for every ASL letter
#  Each entry: {finger: state}
#  States: 'up', 'down', 'bent', 'spread', 'touch'
# ═══════════════════════════════════════════════════════════════

_FINGER_NAMES = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']

# Visual representation: bar height fraction (1.0 = fully up, 0.0 = fully down)
# Plus a color hint
# direction: 'up' (default), 'side' (pointing sideways), 'down' (pointing down)
# motion: optional movement note for J, Z
ASL_FINGER_STATES = {
    'A': {'heights': [0.4, 0.0, 0.0, 0.0, 0.0], 'desc': 'Fist with thumb resting on the side', 'direction': 'up'},
    'B': {'heights': [0.0, 1.0, 1.0, 1.0, 1.0], 'desc': 'Flat hand, thumb tucked across palm', 'direction': 'up'},
    'C': {'heights': [0.6, 0.6, 0.6, 0.6, 0.6], 'desc': 'Curved hand like holding a cup', 'direction': 'up'},
    'D': {'heights': [0.3, 1.0, 0.0, 0.0, 0.0], 'desc': 'Index up, thumb + others make circle', 'direction': 'up'},
    'E': {'heights': [0.0, 0.2, 0.2, 0.2, 0.2], 'desc': 'All fingers curled, thumb tucked under', 'direction': 'up'},
    'F': {'heights': [0.3, 0.3, 1.0, 1.0, 1.0], 'desc': 'Thumb + index circle, 3 fingers up', 'direction': 'up'},
    'G': {'heights': [0.7, 0.7, 0.0, 0.0, 0.0], 'desc': 'Index + thumb point SIDEWAYS →', 'direction': 'side'},
    'H': {'heights': [0.0, 0.7, 0.7, 0.0, 0.0], 'desc': 'Index + middle point SIDEWAYS →', 'direction': 'side'},
    'I': {'heights': [0.0, 0.0, 0.0, 0.0, 1.0], 'desc': 'Pinky up, rest in fist', 'direction': 'up'},
    'J': {'heights': [0.0, 0.0, 0.0, 0.0, 1.0], 'desc': 'Like I + draw J curve downward', 'direction': 'up', 'motion': '↓↩ Draw J with pinky'},
    'K': {'heights': [0.5, 1.0, 1.0, 0.0, 0.0], 'desc': 'V shape + thumb wedged between', 'direction': 'up'},
    'L': {'heights': [1.0, 1.0, 0.0, 0.0, 0.0], 'desc': 'Thumb + index make L shape (90°)', 'direction': 'up'},
    'M': {'heights': [0.0, 0.2, 0.2, 0.2, 0.0], 'desc': 'Three fingers folded over thumb', 'direction': 'up'},
    'N': {'heights': [0.0, 0.2, 0.2, 0.0, 0.0], 'desc': 'Two fingers folded over thumb', 'direction': 'up'},
    'O': {'heights': [0.5, 0.4, 0.4, 0.4, 0.4], 'desc': 'All fingertips touch thumb — circle', 'direction': 'up'},
    'P': {'heights': [0.5, 1.0, 1.0, 0.0, 0.0], 'desc': 'Like K but pointing DOWN ↓', 'direction': 'down'},
    'Q': {'heights': [0.7, 0.7, 0.0, 0.0, 0.0], 'desc': 'Like G but pointing DOWN ↓', 'direction': 'down'},
    'R': {'heights': [0.0, 1.0, 1.0, 0.0, 0.0], 'desc': 'Index crossed over middle', 'direction': 'up'},
    'S': {'heights': [0.4, 0.0, 0.0, 0.0, 0.0], 'desc': 'Tight fist, thumb across front', 'direction': 'up'},
    'T': {'heights': [0.3, 0.1, 0.0, 0.0, 0.0], 'desc': 'Thumb peeking between index + middle', 'direction': 'up'},
    'U': {'heights': [0.0, 1.0, 1.0, 0.0, 0.0], 'desc': 'Index + middle up TOGETHER', 'direction': 'up'},
    'V': {'heights': [0.0, 1.0, 1.0, 0.0, 0.0], 'desc': 'Index + middle SPREAD apart (peace)', 'direction': 'up'},
    'W': {'heights': [0.0, 1.0, 1.0, 1.0, 0.0], 'desc': 'Three fingers up and spread', 'direction': 'up'},
    'X': {'heights': [0.0, 0.5, 0.0, 0.0, 0.0], 'desc': 'Index bent into a hook', 'direction': 'up'},
    'Y': {'heights': [1.0, 0.0, 0.0, 0.0, 1.0], 'desc': 'Thumb + pinky out (hang loose 🤙)', 'direction': 'up'},
    'Z': {'heights': [0.0, 1.0, 0.0, 0.0, 0.0], 'desc': 'Index up, draw Z in the air', 'direction': 'up', 'motion': '→↙→ Draw Z in air'},
}

# Colors for the bars
_BAR_UP_COLOR   = COLORS['primary']       # bright when finger is up
_BAR_DOWN_COLOR = COLORS['border']        # dim when finger is down
_BAR_MID_COLOR  = COLORS['accent']        # medium for bent/curved


# ═══════════════════════════════════════════════════════════════
#  AnimatedHandWidget — the clean finger-status-bar visualization
# ═══════════════════════════════════════════════════════════════

class AnimatedHandWidget(QWidget):
    """Shows finger positions as animated vertical bars — instantly readable.
    
    Each of the 5 fingers is shown as a labeled bar:
    - Tall bar = finger up
    - Short bar = finger down/curled
    - Medium bar = bent/curved
    
    Bars animate smoothly when switching letters.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._current_heights = [0.0, 0.0, 0.0, 0.0, 0.0]
        self._target_heights  = [0.0, 0.0, 0.0, 0.0, 0.0]
        self._anim_t = 1.0
        self._current_letter = ''

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Description label
        self._desc_label = QLabel("Show a letter to see finger positions")
        self._desc_label.setAlignment(Qt.AlignCenter)
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_secondary']};
            background: transparent;
            padding: 2px 4px;
        """)
        main_layout.addWidget(self._desc_label)

        # Bars container
        bars_frame = QFrame()
        bars_frame.setStyleSheet("background: transparent;")
        bars_layout = QHBoxLayout(bars_frame)
        bars_layout.setContentsMargins(4, 4, 4, 2)
        bars_layout.setSpacing(4)

        self._bar_widgets = []
        self._bar_labels = []
        self._status_labels = []

        for i, name in enumerate(_FINGER_NAMES):
            finger_col = QVBoxLayout()
            finger_col.setSpacing(3)
            finger_col.setAlignment(Qt.AlignBottom)

            # Status emoji
            status_lbl = QLabel("✊")
            status_lbl.setAlignment(Qt.AlignCenter)
            status_lbl.setStyleSheet("font-size: 13px; background: transparent;")
            finger_col.addWidget(status_lbl)
            self._status_labels.append(status_lbl)

            # The bar itself
            bar = QFrame()
            bar.setFixedWidth(22)
            bar.setFixedHeight(8)  # start small
            bar.setStyleSheet(f"""
                background: {_BAR_DOWN_COLOR};
                border-radius: 6px;
            """)
            finger_col.addWidget(bar, alignment=Qt.AlignCenter)
            self._bar_widgets.append(bar)

            # Finger name
            name_lbl = QLabel(name[:3])  # Thu, Ind, Mid, Rin, Pin
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(f"""
                font-size: 9px; font-weight: 700;
                color: {COLORS['text_muted']};
                background: transparent;
            """)
            finger_col.addWidget(name_lbl)
            self._bar_labels.append(name_lbl)

            bars_layout.addLayout(finger_col)

        main_layout.addWidget(bars_frame)

        # Direction / motion indicator
        self._direction_label = QLabel("")
        self._direction_label.setAlignment(Qt.AlignCenter)
        self._direction_label.setWordWrap(True)
        self._direction_label.setStyleSheet(f"""
            font-size: 11px; font-weight: 700;
            color: {COLORS.get('accent', '#ff9800')};
            background: transparent;
            padding: 2px 4px;
        """)
        self._direction_label.hide()
        main_layout.addWidget(self._direction_label)

        # Animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._tick)

    def set_letter(self, letter: str):
        """Animate to a new letter's finger positions."""
        letter = letter.upper()
        data = ASL_FINGER_STATES.get(letter)
        if not data:
            return
        self._current_letter = letter
        self._target_heights = list(data['heights'])
        self._desc_label.setText(data['desc'])

        # Show direction / motion hint
        direction = data.get('direction', 'up')
        motion = data.get('motion', '')
        hints = []
        if direction == 'side':
            hints.append('→ Hand points SIDEWAYS')
        elif direction == 'down':
            hints.append('↓ Hand points DOWNWARD')
        if motion:
            hints.append(f'🔄 {motion}')
        if hints:
            self._direction_label.setText('  ·  '.join(hints))
            self._direction_label.show()
        else:
            self._direction_label.hide()

        self._anim_t = 0.0
        self._anim_timer.start()

    def cleanup(self):
        self._anim_timer.stop()

    def _tick(self):
        self._anim_t += 0.06
        if self._anim_t >= 1.0:
            self._anim_t = 1.0
            self._anim_timer.stop()
            self._current_heights = list(self._target_heights)
        else:
            t = self._anim_t * self._anim_t * (3.0 - 2.0 * self._anim_t)
            for i in range(5):
                self._current_heights[i] = (
                    self._current_heights[i] * (1 - t) + self._target_heights[i] * t
                )
        self._update_bars()

    def _update_bars(self):
        max_h = 60  # max bar height in pixels (reduced from 80 for compact layout)
        # Get direction from current letter data
        data = ASL_FINGER_STATES.get(self._current_letter, {})
        direction = data.get('direction', 'up')

        for i, h in enumerate(self._current_heights):
            bar_h = max(8, int(h * max_h))
            self._bar_widgets[i].setFixedHeight(bar_h)

            # Color based on height
            if h >= 0.7:
                color = _BAR_UP_COLOR
                # Direction-aware emoji for extended fingers
                if direction == 'down':
                    emoji = "👇"
                elif direction == 'side':
                    emoji = "👉"
                else:
                    emoji = "☝️"
            elif h >= 0.3:
                color = _BAR_MID_COLOR
                if direction == 'down':
                    emoji = "👇"
                elif direction == 'side':
                    emoji = "👉"
                else:
                    emoji = "👆"
            else:
                color = _BAR_DOWN_COLOR
                emoji = "✊"

            self._bar_widgets[i].setStyleSheet(f"""
                background: {color};
                border-radius: 6px;
            """)
            self._status_labels[i].setText(emoji)

