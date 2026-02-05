"""
Gesture Library Page - Visual ASL Sign Reference Guide

Provides visual demonstrations of ASL signs with:
- Video-based demonstrations for each letter
- Detailed descriptions of how to form each sign
- Common words and phrases
- Searchable reference
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QStackedWidget,
    QLineEdit, QTabWidget, QSizePolicy, QGraphicsDropShadowEffect,
    QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

import json
import os

from ui.styles import COLORS

# Load video timestamps
SIGN_TIMESTAMPS = {}
SIGN_VIDEO_PATH = ""
_timestamps_file = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "asl_hands", "sign_timestamps.json")
if os.path.exists(_timestamps_file):
    with open(_timestamps_file, 'r') as f:
        _data = json.load(f)
        SIGN_TIMESTAMPS = _data.get("signs", {})
        SIGN_VIDEO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "asl_hands", _data.get("video_file", ""))


# ASL Alphabet data with visual descriptions and hand shape instructions
ASL_ALPHABET_DATA = {
    'A': {
        'description': 'Fist with thumb resting on the side',
        'hand_shape': 'closed_fist_thumb_side',
        'detailed': '''Form a fist with your dominant hand. 
Your thumb should rest against the side of your index finger, 
not tucked in or sticking up.
        
Key Points:
• All fingers curled into palm
• Thumb rests on side of hand (near index finger)
• Palm faces forward or slightly to the side''',
        'tips': 'Keep your wrist straight, don\'t bend it.',
        'similar': ['S', 'E', 'T'],
        'emoji': '✊',
        'ascii': '''
    ╔═══╗
    ║███║
    ║███╠═╗
    ║███║ ║← Thumb
    ║███╠═╝
    ╚═══╝
    Fist'''
    },
    'B': {
        'description': 'Flat hand with fingers together, thumb tucked',
        'hand_shape': 'flat_hand',
        'detailed': '''Hold your hand flat with all four fingers 
extended straight up and pressed together.
Tuck your thumb across your palm.

Key Points:
• Fingers straight and together
• Thumb tucked across palm
• Palm faces forward''',
        'tips': 'Keep fingers pressed together tightly.',
        'similar': ['D', 'F'],
        'emoji': '🖐️',
        'ascii': '''
    │ │ │ │
    │ │ │ │
    ╔═══════╗
    ║ ═══   ║← Thumb tucked
    ╚═══════╝
    Flat hand'''
    },
    'C': {
        'description': 'Curved hand like holding a cup',
        'hand_shape': 'curved_c',
        'detailed': '''Curve your hand as if you're holding a 
can or small cup. Fingers and thumb form a 'C' shape.

Key Points:
• Fingers together in a curve
• Thumb curves opposite to fingers
• Opening faces sideways
• Hand forms letter C shape''',
        'tips': 'Imagine holding a tennis ball.',
        'similar': ['O', 'E'],
        'emoji': '🤏',
        'ascii': '''
      ╭───╮
     ╱     ╲
    │       │
    │       │
     ╲     ╱
      ╰───╯
    C shape'''
    },
    'D': {
        'description': 'Index finger up, others touch thumb',
        'hand_shape': 'index_up_circle',
        'detailed': '''Point your index finger straight up.
Touch the tips of your middle, ring, and pinky fingers 
to the tip of your thumb, forming a circle.

Key Points:
• Index finger straight up
• Other three fingers form circle with thumb
• Like making "OK" but with index up''',
        'tips': 'The circle should be round, not pinched.',
        'similar': ['F', 'I'],
        'emoji': '☝️',
        'ascii': '''
       │
       │  Index
    ╭──┴──╮
    │  ◯  │← Circle
    ╰─────╯
    '''
    },
    'E': {
        'description': 'Fingers curled over thumb',
        'hand_shape': 'curled_fist',
        'detailed': '''Curl all your fingertips down to touch 
your palm, with your thumb tucked under your fingers.

Key Points:
• All fingertips touch palm
• Thumb tucked in under fingers
• Like a relaxed fist
• Palm faces outward''',
        'tips': 'Fingertips should be visible from front.',
        'similar': ['A', 'S'],
        'emoji': '✊',
        'ascii': '''
    ╭───────╮
    │ ╭───╮ │
    │ │░░░│ │ ← Fingers curled
    │ ╰═══╯ │ ← Thumb under
    ╰───────╯
    '''
    },
    'F': {
        'description': 'OK sign with three fingers extended up',
        'hand_shape': 'ok_sign_extended',
        'detailed': '''Make an "OK" sign by touching your index 
finger to your thumb. Extend your middle, ring, 
and pinky fingers straight up.

Key Points:
• Thumb and index finger form a circle
• Other three fingers extended up
• Three fingers spread slightly
• Palm faces outward''',
        'tips': 'Keep the circle round, not pinched.',
        'similar': ['D', 'W'],
        'emoji': '👌',
        'ascii': '''
    │ │ │
    │ │ │  ← 3 fingers up
    ╭─┴─┴─╮
    │ ◯   │← Thumb + index circle
    ╰─────╯
    '''
    },
    'G': {
        'description': 'Pointing hand, horizontal position',
        'hand_shape': 'pointing_horizontal',
        'detailed': '''Point with your index finger and thumb, 
held horizontally (pointing to the side).
Other fingers are curled into palm.

Key Points:
• Index finger points sideways
• Thumb parallel to index, slightly apart
• Like a horizontal gun shape
• Other fingers tucked''',
        'tips': 'Keep hand level, don\'t tilt up or down.',
        'similar': ['Q', 'H'],
        'emoji': '👉',
        'ascii': '''
    ═══════►  Index
    ═══════►  Thumb
    ╔═════╗
    ║░░░░░║  ← Others tucked
    ╚═════╝
    '''
    },
    'H': {
        'description': 'Two fingers out, held horizontally',
        'hand_shape': 'two_fingers_horizontal',
        'detailed': '''Extend your index and middle fingers 
together, held horizontally (pointing to the side).
Thumb may rest on other curled fingers.

Key Points:
• Index and middle together horizontally
• Fingers point to the side
• Palm faces down or away
• Like G but with two fingers''',
        'tips': 'Keep the two fingers pressed together.',
        'similar': ['G', 'U', 'N'],
        'emoji': '✌️',
        'ascii': '''
    ═══════►  Index
    ═══════►  Middle
    ╔═════╗
    ║░░░░░║  ← Others tucked
    ╚═════╝
    '''
    },
    'I': {
        'description': 'Pinky finger extended, others closed',
        'hand_shape': 'pinky_up',
        'detailed': '''Make a fist with your pinky finger 
extended straight up. Thumb rests on the 
front of your curled fingers.

Key Points:
• Pinky extended straight up
• Other fingers in loose fist
• Thumb wraps across front
• Palm faces forward''',
        'tips': 'Keep pinky straight, not bent.',
        'similar': ['J', 'Y'],
        'emoji': '🤙',
        'ascii': '''
             │
             │ ← Pinky
    ╔═══════╗
    ║░░░░░░░║
    ║░░░░░░░║
    ╚═══════╝
    '''
    },
    'J': {
        'description': 'Pinky draws J shape in air',
        'hand_shape': 'pinky_draws_j',
        'detailed': '''Start with I (pinky up), then draw a 
small J shape in the air by moving your pinky 
down and curving toward your body.

Key Points:
• Start in I position (pinky up)
• Trace J curve downward
• End with pinky pointing inward
• Motion is the key part''',
        'tips': 'This is a motion sign - movement matters!',
        'similar': ['I', 'Z'],
        'emoji': '☝️→',
        'ascii': '''
    │
    │ ← Start
    │
    ╰──╮
       │
    ←──╯ ← End
    '''
    },
    'K': {
        'description': 'Peace sign with thumb between fingers',
        'hand_shape': 'k_shape',
        'detailed': '''Extend index and middle fingers in a V.
Place your thumb between and touching the 
middle of both fingers.

Key Points:
• Index and middle in V shape
• Thumb touches middle of both
• Ring and pinky curled
• Palm faces forward''',
        'tips': 'Thumb should touch both fingers.',
        'similar': ['V', 'P'],
        'emoji': '✌️',
        'ascii': '''
    ╲     ╱
     ╲   ╱
      ╲ ╱
    ═══╳═══ ← Thumb between
       │
    ╔══╧══╗
    ╚═════╝
    '''
    },
    'L': {
        'description': 'L shape with thumb and index finger',
        'hand_shape': 'l_shape',
        'detailed': '''Extend your thumb out to the side and 
your index finger straight up, forming 
an "L" shape. Other fingers are curled.

Key Points:
• Index finger points up
• Thumb points to the side
• Forms 90-degree angle
• Palm faces forward''',
        'tips': 'Keep the L shape clear - 90 degree angle.',
        'similar': ['G', 'D'],
        'emoji': '👆',
        'ascii': '''
       │
       │  ← Index up
    ╔══╧══╗
    ║     ║
    ╚═════╬═══► Thumb out
          │
    '''
    },
    'M': {
        'description': 'Three fingers over thumb',
        'hand_shape': 'three_over_thumb',
        'detailed': '''Tuck your thumb under your index, middle, 
and ring fingers. Pinky is also tucked.
The three finger knuckles are visible.

Key Points:
• Thumb hidden under first 3 fingers
• Index, middle, ring over thumb
• Pinky tucked alongside
• Shows three bumps''',
        'tips': 'You should see three "bumps" on top.',
        'similar': ['N', 'S', 'T'],
        'emoji': '✊',
        'ascii': '''
    ╭─┬─┬─╮
    │ │ │ │  ← 3 bumps visible
    ╞═╧═╧═╡
    ║░░░░░║  ← Thumb under
    ╚═════╝
    '''
    },
    'N': {
        'description': 'Two fingers over thumb',
        'hand_shape': 'two_over_thumb',
        'detailed': '''Tuck your thumb under your index and 
middle fingers. Ring and pinky are also tucked.
Two finger knuckles are visible.

Key Points:
• Thumb hidden under first 2 fingers
• Index and middle over thumb
• Ring and pinky tucked
• Shows two bumps''',
        'tips': 'Similar to M but with only two bumps.',
        'similar': ['M', 'S', 'T'],
        'emoji': '✊',
        'ascii': '''
    ╭─┬─╮
    │ │ │    ← 2 bumps visible
    ╞═╧═╡
    ║░░░║    ← Thumb under
    ╚═══╝
    '''
    },
    'O': {
        'description': 'Fingers form O/circle shape',
        'hand_shape': 'o_circle',
        'detailed': '''Curve all your fingers and thumb 
together to form an "O" shape.
All fingertips touch the thumb tip.

Key Points:
• All fingertips touch thumb
• Forms circular opening
• Like grasping a small ball
• Palm faces to the side''',
        'tips': 'Make the O as round as possible.',
        'similar': ['C', 'E'],
        'emoji': '👌',
        'ascii': '''
      ╭───╮
     ╱     ╲
    │   ◯   │  ← Circle opening
     ╲     ╱
      ╰───╯
    '''
    },
    'P': {
        'description': 'K shape pointing downward',
        'hand_shape': 'k_pointing_down',
        'detailed': '''Make the K handshape, then point it 
downward (middle finger toward the ground).
Looks like an inverted K.

Key Points:
• Same handshape as K
• Pointed downward
• Index and middle in V
• Thumb touches middle fingers''',
        'tips': 'It\'s just K rotated down.',
        'similar': ['K', 'Q'],
        'emoji': '👇',
        'ascii': '''
    ╔═════╗
       │
    ═══╳═══ ← Thumb between
      ╱ ╲
     ╱   ╲
    ▼     ▼  ← Points down
    '''
    },
    'Q': {
        'description': 'G shape pointing downward',
        'hand_shape': 'g_pointing_down',
        'detailed': '''Make the G handshape, then point it 
downward. Index finger and thumb point 
toward the ground.

Key Points:
• Same handshape as G
• Pointed downward
• Index and thumb extend down
• Like picking up something small''',
        'tips': 'It\'s just G rotated down.',
        'similar': ['G', 'P'],
        'emoji': '👇',
        'ascii': '''
    ╔═════╗
    ║░░░░░║
    ╚══╤══╝
       │
       │
       ▼  ← Points down
    '''
    },
    'R': {
        'description': 'Crossed index and middle fingers',
        'hand_shape': 'crossed_fingers',
        'detailed': '''Cross your index finger over your 
middle finger (like crossing fingers for luck).
Other fingers are tucked.

Key Points:
• Index crosses over middle
• Middle behind index
• Fingers point up
• "Good luck" position''',
        'tips': 'Index goes in FRONT of middle.',
        'similar': ['U', 'V'],
        'emoji': '🤞',
        'ascii': '''
       ╲│
        ╳  ← Crossed
       │╱
    ╔══╧══╗
    ║░░░░░║
    ╚═════╝
    '''
    },
    'S': {
        'description': 'Fist with thumb across front of fingers',
        'hand_shape': 'fist_thumb_front',
        'detailed': '''Make a fist with your thumb wrapped 
across the front of your fingers 
(across the first knuckles).

Key Points:
• Tight fist
• Thumb crosses in front
• Thumb tip near pinky side
• Palm faces forward''',
        'tips': 'Thumb goes ACROSS front, not side like A.',
        'similar': ['A', 'E', 'T'],
        'emoji': '✊',
        'ascii': '''
    ╔═══════╗
    ║░░░░░░░║
    ╠═══════╣ ← Thumb across
    ║░░░░░░░║
    ╚═══════╝
    '''
    },
    'T': {
        'description': 'Fist with thumb between index and middle',
        'hand_shape': 'thumb_between',
        'detailed': '''Make a fist with your thumb tucked 
between your index and middle fingers.
Thumb tip pokes out slightly.

Key Points:
• Fingers curled in fist
• Thumb between index and middle
• Thumb tip visible between them
• Like peeking thumb''',
        'tips': 'Thumb tip should show between the fingers.',
        'similar': ['S', 'N', 'M'],
        'emoji': '✊',
        'ascii': '''
    ╔═══════╗
    ║░░╔═╗░░║ ← Thumb between
    ║░░║▲║░░║
    ║░░╚═╝░░║
    ╚═══════╝
    '''
    },
    'U': {
        'description': 'Two fingers up together (not spread)',
        'hand_shape': 'two_up_together',
        'detailed': '''Extend your index and middle fingers 
straight up and pressed together.
Other fingers and thumb tucked.

Key Points:
• Index and middle up together
• Fingers touching/parallel
• Not spread like V
• Palm faces forward''',
        'tips': 'Fingers must be TOGETHER, not spread.',
        'similar': ['H', 'V', 'N'],
        'emoji': '✌️',
        'ascii': '''
    │ │
    │ │  ← Together
    │ │
    ╔═╧═╗
    ║░░░║
    ╚═══╝
    '''
    },
    'V': {
        'description': 'Peace sign (two fingers spread)',
        'hand_shape': 'peace_sign',
        'detailed': '''Extend your index and middle fingers 
in a V shape (spread apart).
Other fingers and thumb tucked.

Key Points:
• Index and middle spread in V
• Clear gap between fingers
• Classic "peace" sign
• Palm faces forward''',
        'tips': 'Make a clear V - spread the fingers.',
        'similar': ['U', 'K', 'R'],
        'emoji': '✌️',
        'ascii': '''
    ╲   ╱
     ╲ ╱
      V   ← Spread apart
    ╔═╧═╗
    ║░░░║
    ╚═══╝
    '''
    },
    'W': {
        'description': 'Three fingers extended and spread',
        'hand_shape': 'three_up_spread',
        'detailed': '''Extend your index, middle, and ring 
fingers, spreading them apart.
Pinky and thumb tucked.

Key Points:
• Three fingers up and spread
• Clear gaps between fingers
• Thumb holds pinky down
• Like "3" hand signal''',
        'tips': 'Spread all three fingers clearly.',
        'similar': ['F', 'V'],
        'emoji': '🖖',
        'ascii': '''
    ╲ │ ╱
     ╲│╱  ← 3 spread
    ╔═╧═╗
    ║░░░║
    ╚═══╝
    '''
    },
    'X': {
        'description': 'Hooked/bent index finger',
        'hand_shape': 'hooked_index',
        'detailed': '''Make a fist and extend only your index 
finger in a hook shape (bent at the knuckle).
Like a hook or crooked finger.

Key Points:
• Index finger bent in hook
• Other fingers in fist
• Thumb wrapped around
• Hook faces sideways''',
        'tips': 'Bend at both knuckles to make a hook.',
        'similar': ['G', 'D'],
        'emoji': '☝️',
        'ascii': '''
    ╭───╮
    │   │
    ╰───┤← Hooked
    ╔═══╗
    ║░░░║
    ╚═══╝
    '''
    },
    'Y': {
        'description': 'Hang loose - thumb and pinky extended',
        'hand_shape': 'shaka',
        'detailed': '''Extend your thumb and pinky outward 
while keeping other fingers curled in.
The classic "hang loose" or shaka sign.

Key Points:
• Thumb out to one side
• Pinky out to other side
• Middle three fingers curled
• Palm can face any direction''',
        'tips': 'Spread thumb and pinky wide apart.',
        'similar': ['I', 'L'],
        'emoji': '🤙',
        'ascii': '''
              │← Pinky
    ╔═════════╗
    ║░░░░░░░░░║
    ╚═════════╝
    │← Thumb
    '''
    },
    'Z': {
        'description': 'Index finger draws Z in air',
        'hand_shape': 'draw_z',
        'detailed': '''Point with your index finger and draw 
the letter Z in the air:
diagonal down-left, across right, diagonal down-left.

Key Points:
• Start with pointing hand
• Draw Z shape in the air
• Motion is the key part
• Like writing Z''',
        'tips': 'This is a motion sign - trace Z clearly!',
        'similar': ['J'],
        'emoji': '👆→',
        'ascii': '''
    ━━━━━━►
          ╲
           ╲
    ━━━━━━►
    Draw Z in air
    '''
    },
}

# Common words with their sign descriptions
ASL_WORDS_DATA = {
    'HELLO': {
        'type': 'greeting',
        'description': 'Open hand salute from forehead outward',
        'detailed': 'Hold flat hand near forehead, palm out, move hand outward like a salute wave.',
        'emoji': '👋'
    },
    'THANK YOU': {
        'type': 'courtesy',
        'description': 'Flat hand from chin moving forward',
        'detailed': 'Touch flat hand to chin/lips, move hand forward and down. Similar to blowing a kiss motion.',
        'emoji': '🙏'
    },
    'PLEASE': {
        'type': 'courtesy',
        'description': 'Flat hand circles on chest',
        'detailed': 'Place flat hand on chest and rub in a circular motion.',
        'emoji': '🙏'
    },
    'YES': {
        'type': 'response',
        'description': 'Fist nods like a head nodding',
        'detailed': 'Make a fist (S hand) and nod it up and down, like your hand is nodding "yes".',
        'emoji': '✅'
    },
    'NO': {
        'type': 'response',
        'description': 'Index and middle tap thumb',
        'detailed': 'Extend index and middle finger, tap them against thumb (like fingers saying "no").',
        'emoji': '❌'
    },
    'HELP': {
        'type': 'request',
        'description': 'Fist on flat palm, lift up together',
        'detailed': 'Place closed fist on flat palm of other hand. Lift both hands up together.',
        'emoji': '🆘'
    },
    'SORRY': {
        'type': 'courtesy',
        'description': 'Fist circles on chest',
        'detailed': 'Make a fist (A or S hand), place on chest, move in a circular rubbing motion.',
        'emoji': '😔'
    },
    'I LOVE YOU': {
        'type': 'expression',
        'description': 'Thumb, index, and pinky extended',
        'detailed': 'Extend thumb, index finger, and pinky. Middle and ring fingers are down. Combines I, L, and Y.',
        'emoji': '🤟'
    },
    'GOOD': {
        'type': 'description',
        'description': 'Flat hand from chin forward',
        'detailed': 'Touch flat hand to chin/lips, bring forward and down to land on other palm.',
        'emoji': '👍'
    },
    'BAD': {
        'type': 'description', 
        'description': 'Flat hand from chin, flip down',
        'detailed': 'Touch flat hand to chin, then flip hand so palm faces down.',
        'emoji': '👎'
    },
    'WATER': {
        'type': 'noun',
        'description': 'W hand taps chin',
        'detailed': 'Make W hand shape (3 fingers extended), tap index finger on chin twice.',
        'emoji': '💧'
    },
    'FOOD': {
        'type': 'noun',
        'description': 'Bunched fingers tap mouth',
        'detailed': 'Bunch all fingertips together, tap to lips/mouth repeatedly.',
        'emoji': '🍽️'
    },
}


class SignVideoPlayer(QFrame):
    """Widget for playing sign video segments based on timestamps."""
    
    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self.timestamps = SIGN_TIMESTAMPS.get(letter, {})
        self.start_time = self.timestamps.get('start', 0) * 1000  # Convert to ms
        self.end_time = self.timestamps.get('end', 0) * 1000  # Convert to ms
        self._loop_enabled = True
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(320, 240)
        self.video_widget.setStyleSheet(f"""
            background-color: #000000;
            border-radius: 8px;
        """)
        layout.addWidget(self.video_widget)
        
        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Position check timer for looping within segment
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._check_position)
        self.position_timer.setInterval(50)  # Check every 50ms
        
        # Control buttons
        controls = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        self.play_btn.clicked.connect(self._toggle_play)
        controls.addWidget(self.play_btn)
        
        self.loop_btn = QPushButton("🔁 Loop: On")
        self.loop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                padding: 8px 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        self.loop_btn.clicked.connect(self._toggle_loop)
        controls.addWidget(self.loop_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Load video if timestamps exist
        if self.timestamps and os.path.exists(SIGN_VIDEO_PATH):
            self.media_player.setSource(QUrl.fromLocalFile(SIGN_VIDEO_PATH))
            self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        else:
            no_video_label = QLabel("📹 No video available for this letter")
            no_video_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 20px;")
            no_video_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_video_label)
    
    def _on_media_status_changed(self, status):
        """Handle media status changes."""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Seek to start position and auto-play
            self.media_player.setPosition(int(self.start_time))
            self.media_player.play()
            self.position_timer.start()
            self.play_btn.setText("⏸ Pause")
    
    def _check_position(self):
        """Check if we've reached the end of the segment."""
        current = self.media_player.position()
        if current >= self.end_time:
            if self._loop_enabled:
                self.media_player.setPosition(int(self.start_time))
            else:
                self.media_player.pause()
                self.play_btn.setText("▶ Play")
    
    def _toggle_play(self):
        """Toggle play/pause."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.position_timer.stop()
            self.play_btn.setText("▶ Play")
        else:
            # Ensure we're within segment bounds
            current = self.media_player.position()
            if current < self.start_time or current >= self.end_time:
                self.media_player.setPosition(int(self.start_time))
            self.media_player.play()
            self.position_timer.start()
            self.play_btn.setText("⏸ Pause")
    
    def _toggle_loop(self):
        """Toggle loop mode."""
        self._loop_enabled = not self._loop_enabled
        self.loop_btn.setText(f"🔁 Loop: {'On' if self._loop_enabled else 'Off'}")
    
    def cleanup(self):
        """Stop playback and cleanup resources."""
        self.position_timer.stop()
        self.media_player.stop()


class HandShapeWidget(QFrame):
    """Widget showing the hand shape for a sign with video and description."""
    
    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self.data = ASL_ALPHABET_DATA.get(letter, {})
        self.video_player = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Letter display with emoji
        header = QHBoxLayout()
        
        letter_label = QLabel(self.letter)
        letter_label.setStyleSheet(f"""
            font-size: 64px;
            font-weight: bold;
            color: {COLORS['primary']};
            background: transparent;
        """)
        header.addWidget(letter_label)
        
        emoji_label = QLabel(self.data.get('emoji', ''))
        emoji_label.setStyleSheet("font-size: 48px; background: transparent;")
        header.addWidget(emoji_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Brief description
        desc = QLabel(self.data.get('description', ''))
        desc.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Video player for this letter (if timestamp exists)
        if self.letter in SIGN_TIMESTAMPS:
            video_frame = QFrame()
            video_frame.setStyleSheet(f"""
                background-color: {COLORS['bg_input']};
                border-radius: 8px;
                padding: 8px;
            """)
            video_layout = QVBoxLayout(video_frame)
            
            video_title = QLabel("📹 Video Demonstration")
            video_title.setStyleSheet(f"""
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['text_primary']};
                background: transparent;
            """)
            video_layout.addWidget(video_title)
            
            self.video_player = SignVideoPlayer(self.letter)
            video_layout.addWidget(self.video_player)
            
            layout.addWidget(video_frame)
        else:
            # Fallback to ASCII art if no video timestamp
            ascii_art = self.data.get('ascii', '')
            if ascii_art:
                art_frame = QFrame()
                art_frame.setStyleSheet(f"""
                    background-color: {COLORS['bg_input']};
                    border-radius: 8px;
                    padding: 8px;
                """)
                art_layout = QVBoxLayout(art_frame)
                
                art_label = QLabel(ascii_art)
                art_label.setStyleSheet(f"""
                    font-family: Consolas, 'Courier New', monospace;
                    font-size: 14px;
                    color: {COLORS['primary']};
                    background: transparent;
                """)
                art_label.setAlignment(Qt.AlignCenter)
                art_layout.addWidget(art_label)
                
                layout.addWidget(art_frame)
        
        # Detailed instructions
        detailed = QLabel(self.data.get('detailed', ''))
        detailed.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            line-height: 1.5;
            background: transparent;
        """)
        detailed.setWordWrap(True)
        layout.addWidget(detailed)
        
        # Tips
        tips = self.data.get('tips', '')
        if tips:
            tips_label = QLabel(f"💡 Tip: {tips}")
            tips_label.setStyleSheet(f"""
                font-size: 13px;
                color: {COLORS['accent']};
                background-color: {COLORS['accent']}20;
                padding: 8px 12px;
                border-radius: 6px;
            """)
            tips_label.setWordWrap(True)
            layout.addWidget(tips_label)
        
        # Similar signs
        similar = self.data.get('similar', [])
        if similar:
            similar_text = ", ".join(similar)
            similar_label = QLabel(f"⚠️ Similar to: {similar_text}")
            similar_label.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS['warning']};
                background: transparent;
            """)
            layout.addWidget(similar_label)
        
        layout.addStretch()


class SignCard(QFrame):
    """A clickable card for a letter in the alphabet grid."""
    
    clicked = Signal(str)
    
    def __init__(self, letter: str, parent=None):
        super().__init__(parent)
        self.letter = letter
        self.setObjectName("signCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(80, 100)
        self._setup_ui()
        self._apply_style(False)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Emoji
        data = ASL_ALPHABET_DATA.get(self.letter, {})
        emoji = data.get('emoji', '✋')
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 24px; background: transparent;")
        emoji_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(emoji_label)
        
        # Letter
        letter_label = QLabel(self.letter)
        letter_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        letter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(letter_label)
        
        # Brief description
        desc = data.get('description', '')[:20]
        desc_label = QLabel(desc + "..." if len(data.get('description', '')) > 20 else desc)
        desc_label.setStyleSheet(f"""
            font-size: 9px;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
    
    def _apply_style(self, selected: bool):
        if selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['primary']};
                    border-radius: 12px;
                    border: 2px solid {COLORS['primary']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border-radius: 12px;
                    border: 2px solid transparent;
                }}
                QFrame:hover {{
                    background-color: {COLORS['bg_hover']};
                    border: 2px solid {COLORS['primary']}40;
                }}
            """)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.letter)


class WordCard(QFrame):
    """A card showing a common word/phrase."""
    
    def __init__(self, word: str, data: dict, parent=None):
        super().__init__(parent)
        self.word = word
        self.data = data
        self.setObjectName("wordCard")
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with emoji and word
        header = QHBoxLayout()
        
        emoji = QLabel(self.data.get('emoji', '👋'))
        emoji.setStyleSheet("font-size: 28px; background: transparent;")
        header.addWidget(emoji)
        
        word_label = QLabel(self.word)
        word_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header.addWidget(word_label)
        header.addStretch()
        
        type_label = QLabel(self.data.get('type', '').title())
        type_label.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['primary']};
            background-color: {COLORS['primary']}20;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        header.addWidget(type_label)
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel(self.data.get('description', ''))
        desc.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Detailed
        detailed = QLabel(self.data.get('detailed', ''))
        detailed.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        detailed.setWordWrap(True)
        layout.addWidget(detailed)


class GestureLibraryPage(QWidget):
    """Main sign library page with searchable reference."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_letter = None
        self._letter_cards = {}
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
        
        title = QLabel("📖 Sign Library")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['text_primary']};")
        header.addWidget(title)
        
        header.addStretch()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search signs...")
        self.search_box.setFixedWidth(200)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
            }}
        """)
        self.search_box.textChanged.connect(self._filter_signs)
        header.addWidget(self.search_box)
        
        layout.addLayout(header)
        
        # Tabs for Alphabet / Words
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_secondary']};
                padding: 10px 20px;
                margin-right: 4px;
                border-radius: 8px 8px 0 0;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['text_primary']};
            }}
        """)
        
        # Alphabet tab
        alphabet_tab = self._create_alphabet_tab()
        self.tabs.addTab(alphabet_tab, "🔤 Alphabet (A-Z)")
        
        # Common words tab
        words_tab = self._create_words_tab()
        self.tabs.addTab(words_tab, "💬 Common Words")
        
        layout.addWidget(self.tabs)
    
    def _create_alphabet_tab(self) -> QWidget:
        """Create the alphabet reference tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)
        
        # Left: Letter grid
        grid_container = QWidget()
        grid_container.setFixedWidth(380)
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        grid_title = QLabel("Select a letter to see how to sign it:")
        grid_title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        grid_layout.addWidget(grid_title)
        
        # Letter grid
        grid_scroll = QScrollArea()
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setFrameShape(QFrame.NoFrame)
        grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        grid_content = QWidget()
        self.letter_grid = QGridLayout(grid_content)
        self.letter_grid.setSpacing(8)
        
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, letter in enumerate(letters):
            card = SignCard(letter)
            card.clicked.connect(self._on_letter_selected)
            self._letter_cards[letter] = card
            self.letter_grid.addWidget(card, i // 5, i % 5)
        
        grid_scroll.setWidget(grid_content)
        grid_layout.addWidget(grid_scroll)
        
        layout.addWidget(grid_container)
        
        # Right: Detail view
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.NoFrame)
        self.detail_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg_card']};
                border-radius: 12px;
            }}
        """)
        
        # Default: show instruction
        self.detail_container = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_container)
        
        placeholder = QLabel("👈 Select a letter from the left\nto see how to form the sign")
        placeholder.setStyleSheet(f"""
            font-size: 18px;
            color: {COLORS['text_muted']};
            padding: 40px;
        """)
        placeholder.setAlignment(Qt.AlignCenter)
        self.detail_layout.addWidget(placeholder)
        
        self.detail_scroll.setWidget(self.detail_container)
        layout.addWidget(self.detail_scroll, 1)
        
        return widget
    
    def _create_words_tab(self) -> QWidget:
        """Create the common words reference tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 16, 0, 0)
        
        info = QLabel("Common ASL words and phrases with descriptions of how to sign them:")
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; margin-bottom: 8px;")
        layout.addWidget(info)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # Group by type
        types = {}
        for word, data in ASL_WORDS_DATA.items():
            word_type = data.get('type', 'other')
            if word_type not in types:
                types[word_type] = []
            types[word_type].append((word, data))
        
        for word_type, words in types.items():
            # Type header
            type_label = QLabel(f"📌 {word_type.title()}")
            type_label.setStyleSheet(f"""
                font-size: 16px;
                font-weight: 600;
                color: {COLORS['text_primary']};
                margin-top: 16px;
            """)
            scroll_layout.addWidget(type_label)
            
            # Word cards
            for word, data in words:
                card = WordCard(word, data)
                scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _on_letter_selected(self, letter: str):
        """Handle letter selection."""
        # Update card styles
        for l, card in self._letter_cards.items():
            card._apply_style(l == letter)
        
        self._selected_letter = letter
        
        # Show detail
        # Clear old content - cleanup video players first
        while self.detail_layout.count():
            child = self.detail_layout.takeAt(0)
            if child.widget():
                # Check if it's a HandShapeWidget with a video player
                widget = child.widget()
                if hasattr(widget, 'video_player') and widget.video_player:
                    widget.video_player.cleanup()
                widget.deleteLater()
        
        # Add new detail widget
        detail_widget = HandShapeWidget(letter)
        self.detail_layout.addWidget(detail_widget)
    
    def _filter_signs(self, query: str):
        """Filter signs based on search query."""
        query = query.upper().strip()
        
        for letter, card in self._letter_cards.items():
            if not query:
                card.show()
            else:
                # Search in letter and description
                data = ASL_ALPHABET_DATA.get(letter, {})
                desc = data.get('description', '').upper()
                if query in letter or query in desc:
                    card.show()
                else:
                    card.hide()
