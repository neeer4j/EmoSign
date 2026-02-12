"""
Game Page - Gamified Sign Language Learning

Falling letters/numbers that the player must sign correctly before they
reach the bottom.  Uses the existing CameraWidget + Classifier pipeline.

DIFFICULTY LEVELS:
    Easy   - One letter at a time, very slow. Anyone can play.
    Medium - Multiple letters, moderate pace.
    Hard   - Fast falling letters!
    Expert - Small words to spell out (not fast).
"""

import math
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QRectF
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath
)

from ui.styles import COLORS, ICONS
from ui.camera_widget import CameraWidget
from ml.classifier import Classifier

# Reuse tutorial data for hint feature
from ui.pages.tutorial_page import SIGN_GUIDE, SignCard


# ---------------------------------------------------------------------------
# Difficulty presets
# ---------------------------------------------------------------------------

DIFFICULTY_PRESETS = {
    "easy": {
        "name": "Easy",
        "emoji": "🌱",
        "description": "One letter at a time, nice and slow",
        "fall_speed": 30,
        "spawn_interval_ms": 6000,
        "spawn_min_ms": 4000,
        "max_items": 1,
        "speed_increment": 3,
        "use_words": False,
    },
    "medium": {
        "name": "Medium",
        "emoji": "⚡",
        "description": "Multiple letters, moderate pace",
        "fall_speed": 60,
        "spawn_interval_ms": 2800,
        "spawn_min_ms": 1600,
        "max_items": 3,
        "speed_increment": 8,
        "use_words": False,
    },
    "hard": {
        "name": "Hard",
        "emoji": "🔥",
        "description": "Speedy letters — test your reflexes!",
        "fall_speed": 130,
        "spawn_interval_ms": 1200,
        "spawn_min_ms": 600,
        "max_items": 5,
        "speed_increment": 18,
        "use_words": False,
    },
    "expert": {
        "name": "Expert",
        "emoji": "🏆",
        "description": "Spell small words letter by letter",
        "fall_speed": 38,
        "spawn_interval_ms": 6000,
        "spawn_min_ms": 3500,
        "max_items": 2,
        "speed_increment": 3,
        "use_words": True,
    },
}

WORD_POOL = [
    "HI", "NO", "OK", "UP", "GO", "YES", "BYE", "CAT", "DOG",
    "SUN", "HAT", "CUP", "RED", "BIG", "RUN", "FUN", "WIN",
    "TOP", "HOT", "ICE", "BOX", "KEY", "MAP", "PEN",
]


# ---------------------------------------------------------------------------
# Falling item data
# ---------------------------------------------------------------------------

class FallingItem:
    """Represents a single character or word falling down the game canvas."""

    __slots__ = ("char", "x", "y", "speed", "width", "height",
                 "is_alive", "opacity", "glow_phase",
                 "word", "word_index")

    def __init__(self, char: str, x: float, speed: float, word: str = ""):
        self.char = char.upper()
        self.x = x
        self.y = -60.0  # start above the visible area
        self.speed = speed
        self.height = 56
        self.is_alive = True
        self.opacity = 1.0
        self.glow_phase = random.uniform(0, 6.28)

        # Word mode
        self.word = word.upper() if word else self.char
        self.word_index = 0  # index of current letter the player must sign
        self.width = max(56, len(self.word) * 52 + 8)

    @property
    def current_letter(self) -> str:
        """The letter the player needs to sign next."""
        if self.word_index < len(self.word):
            return self.word[self.word_index]
        return ""

    @property
    def is_word(self) -> bool:
        return len(self.word) > 1

    def advance_letter(self) -> bool:
        """Move to next letter in word. Returns True if word complete."""
        self.word_index += 1
        return self.word_index >= len(self.word)


# ---------------------------------------------------------------------------
# Game canvas – custom-painted game area
# ---------------------------------------------------------------------------

class GameCanvas(QWidget):
    """Custom-painted widget that renders the falling items."""

    item_reached_bottom = Signal(str)  # character/word that was missed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: list[FallingItem] = []
        self.setMinimumSize(500, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # visual helpers
        self._match_flash = 0.0
        self._match_char = ""
        self._particles: list[dict] = []
        self._time = 0.0

    # -- public API ----------------------------------------------------------

    def add_item(self, item: FallingItem):
        self.items.append(item)

    def alive_count(self) -> int:
        return sum(1 for i in self.items if i.is_alive)

    def tick(self, dt: float):
        """Advance physics by *dt* seconds."""
        self._time += dt

        new_items = []
        for item in self.items:
            if not item.is_alive:
                continue
            item.y += item.speed * dt
            item.glow_phase += dt * 3.0

            if item.y > self.height():
                self.item_reached_bottom.emit(item.word)
            else:
                new_items.append(item)
        self.items = new_items

        if self._match_flash > 0:
            self._match_flash -= dt * 3.0

        new_particles = []
        for p in self._particles:
            p["life"] -= dt * 2.0
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 200 * dt
            if p["life"] > 0:
                new_particles.append(p)
        self._particles = new_particles

        self.update()

    def consume_letter_match(self, char: str):
        """Try matching a letter against the lowest item.

        Returns:
            "full"    – item fully consumed (single letter or last letter of word)
            "partial" – matched a letter in a word, more to go
            None      – no match
        """
        upper = char.upper()
        # Find the lowest alive item whose current_letter matches
        best = None
        for item in self.items:
            if item.is_alive and item.current_letter == upper:
                if best is None or item.y > best.y:
                    best = item
        if best is None:
            return None

        if best.is_word:
            completed = best.advance_letter()
            if completed:
                self._spawn_particles(best)
                best.is_alive = False
                self._match_flash = 1.0
                self._match_char = best.word
                return "full"
            else:
                # partial match — small particle burst
                letter_x = best.x + best.word_index * 52
                for _ in range(5):
                    self._particles.append({
                        "x": letter_x, "y": best.y + 28,
                        "vx": random.uniform(-80, 80),
                        "vy": random.uniform(-120, -30),
                        "life": 0.6,
                        "color": random.choice(["#10b981", "#2dd4bf"])
                    })
                return "partial"
        else:
            # Single character
            self._spawn_particles(best)
            best.is_alive = False
            self._match_flash = 1.0
            self._match_char = upper
            return "full"

    def _spawn_particles(self, item: FallingItem):
        cx = item.x + item.width / 2
        cy = item.y + item.height / 2
        for _ in range(12):
            self._particles.append({
                "x": cx, "y": cy,
                "vx": random.uniform(-180, 180),
                "vy": random.uniform(-250, -50),
                "life": 1.0,
                "color": random.choice(["#10b981", "#2dd4bf", "#8b5cf6", "#06b6d4"])
            })

    def clear_items(self):
        self.items.clear()
        self._particles.clear()
        self._match_flash = 0.0
        self.update()

    # -- painting ------------------------------------------------------------

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0.0, QColor("#0a0a14"))
        bg.setColorAt(1.0, QColor("#12121e"))
        p.fillRect(0, 0, w, h, bg)

        # Grid
        p.setPen(QPen(QColor(255, 255, 255, 8), 1))
        for gx in range(0, w, 60):
            p.drawLine(gx, 0, gx, h)
        for gy in range(0, h, 60):
            p.drawLine(0, gy, w, gy)

        # Danger zone
        danger_grad = QLinearGradient(0, h - 60, 0, h)
        danger_grad.setColorAt(0.0, QColor(239, 68, 68, 0))
        danger_grad.setColorAt(1.0, QColor(239, 68, 68, 40))
        p.fillRect(0, h - 60, w, 60, danger_grad)
        p.setPen(QPen(QColor(239, 68, 68, 80), 2, Qt.DashLine))
        p.drawLine(0, h - 60, w, h - 60)

        # Items
        for item in self.items:
            if not item.is_alive:
                continue
            if item.is_word:
                self._draw_word_item(p, item)
            else:
                self._draw_single_item(p, item)

        # Match flash
        if self._match_flash > 0:
            flash_alpha = int(self._match_flash * 30)
            p.fillRect(0, 0, w, h, QColor(16, 185, 129, flash_alpha))
            p.setPen(QPen(QColor(16, 185, 129, int(self._match_flash * 200))))
            font = QFont("Segoe UI", 48, QFont.Bold)
            p.setFont(font)
            p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, f"✓ {self._match_char}")

        # Particles
        for par in self._particles:
            alpha = int(par["life"] * 255)
            color = QColor(par["color"])
            color.setAlpha(alpha)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(color))
            size = 4 + par["life"] * 6
            p.drawEllipse(int(par["x"] - size / 2), int(par["y"] - size / 2),
                          int(size), int(size))

        p.end()

    def _draw_single_item(self, p: QPainter, item: FallingItem):
        """Draw a single falling character tile."""
        x, y = int(item.x), int(item.y)
        tw, th = 56, item.height

        glow_intensity = 0.5 + 0.5 * math.sin(item.glow_phase)

        # Glow
        glow_color = QColor("#8b5cf6")
        glow_color.setAlpha(int(40 * glow_intensity))
        glow = QRadialGradient(x + tw / 2, y + th / 2, tw)
        glow.setColorAt(0.0, glow_color)
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(x - 10, y - 10, tw + 20, th + 20)

        # Tile
        path = QPainterPath()
        path.addRoundedRect(QRectF(x, y, tw, th), 12, 12)
        tile_bg = QLinearGradient(x, y, x, y + th)
        tile_bg.setColorAt(0.0, QColor("#1e1e2e"))
        tile_bg.setColorAt(1.0, QColor("#16161e"))
        p.fillPath(path, QBrush(tile_bg))

        border_color = QColor("#8b5cf6")
        border_color.setAlpha(int(120 + 80 * glow_intensity))
        p.setPen(QPen(border_color, 2))
        p.drawPath(path)

        p.setPen(QPen(QColor("#f8fafc")))
        font = QFont("Segoe UI", 22, QFont.Bold)
        p.setFont(font)
        p.drawText(QRectF(x, y, tw, th), Qt.AlignCenter, item.char)

    def _draw_word_item(self, p: QPainter, item: FallingItem):
        """Draw a falling word as a row of letter tiles."""
        base_x, y = int(item.x), int(item.y)
        th = item.height
        tile_w = 48
        gap = 4
        glow_intensity = 0.5 + 0.5 * math.sin(item.glow_phase)

        for i, letter in enumerate(item.word):
            lx = base_x + i * (tile_w + gap)
            rect = QRectF(lx, y, tile_w, th)
            path = QPainterPath()
            path.addRoundedRect(rect, 10, 10)

            if i < item.word_index:
                # Already signed — green tile
                bg = QLinearGradient(lx, y, lx, y + th)
                bg.setColorAt(0.0, QColor("#065f46"))
                bg.setColorAt(1.0, QColor("#064e3b"))
                p.fillPath(path, QBrush(bg))
                p.setPen(QPen(QColor("#10b981"), 2))
                p.drawPath(path)
                # Checkmark
                p.setPen(QPen(QColor("#10b981")))
                font = QFont("Segoe UI", 18, QFont.Bold)
                p.setFont(font)
                p.drawText(rect, Qt.AlignCenter, "✓")
            elif i == item.word_index:
                # Current target — bright pulsing
                glow_c = QColor("#f59e0b")
                glow_c.setAlpha(int(50 * glow_intensity))
                glow_r = QRadialGradient(lx + tile_w / 2, y + th / 2, tile_w)
                glow_r.setColorAt(0.0, glow_c)
                glow_r.setColorAt(1.0, QColor(0, 0, 0, 0))
                p.setBrush(QBrush(glow_r))
                p.setPen(Qt.NoPen)
                p.drawEllipse(lx - 6, y - 6, tile_w + 12, th + 12)

                bg = QLinearGradient(lx, y, lx, y + th)
                bg.setColorAt(0.0, QColor("#2e1e0e"))
                bg.setColorAt(1.0, QColor("#1e160e"))
                p.fillPath(path, QBrush(bg))
                border_c = QColor("#f59e0b")
                border_c.setAlpha(int(180 + 75 * glow_intensity))
                p.setPen(QPen(border_c, 2.5))
                p.drawPath(path)
                p.setPen(QPen(QColor("#fbbf24")))
                font = QFont("Segoe UI", 22, QFont.Bold)
                p.setFont(font)
                p.drawText(rect, Qt.AlignCenter, letter)
            else:
                # Upcoming — dim tile
                bg = QLinearGradient(lx, y, lx, y + th)
                bg.setColorAt(0.0, QColor("#1a1a2a"))
                bg.setColorAt(1.0, QColor("#141420"))
                p.fillPath(path, QBrush(bg))
                p.setPen(QPen(QColor(100, 100, 130, 80), 1.5))
                p.drawPath(path)
                p.setPen(QPen(QColor(160, 160, 180, 120)))
                font = QFont("Segoe UI", 18)
                p.setFont(font)
                p.drawText(rect, Qt.AlignCenter, letter)


# ---------------------------------------------------------------------------
# Game HUD (score / lives / level)
# ---------------------------------------------------------------------------

class GameHUD(QFrame):
    """Heads-up display showing score, lives, and level."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(32)

        def _col(value_text, title_text, color):
            val = QLabel(value_text)
            val.setStyleSheet(f"font-size: 36px; font-weight: 800; color: {color}; background: transparent;")
            title = QLabel(title_text)
            title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;")
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(val, alignment=Qt.AlignCenter)
            col.addWidget(title, alignment=Qt.AlignCenter)
            layout.addLayout(col)
            return val

        self.score_label = _col("0", "SCORE", COLORS['primary'])
        self.lives_label = QLabel("❤️ ❤️ ❤️")
        self.lives_label.setStyleSheet("font-size: 24px; background: transparent;")
        lives_title = QLabel("LIVES")
        lives_title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;")
        lives_col = QVBoxLayout()
        lives_col.setSpacing(2)
        lives_col.addWidget(self.lives_label, alignment=Qt.AlignCenter)
        lives_col.addWidget(lives_title, alignment=Qt.AlignCenter)
        layout.addLayout(lives_col)

        self.level_label = _col("1", "LEVEL", COLORS['warning'])
        self.best_label = _col("0", "BEST", COLORS['success'])

    def update_hud(self, score: int, lives: int, level: int, best: int):
        self.score_label.setText(str(score))
        hearts = " ".join(["❤️"] * lives + ["🖤"] * (3 - lives))
        self.lives_label.setText(hearts)
        self.level_label.setText(str(level))
        self.best_label.setText(str(best))


# ---------------------------------------------------------------------------
# Difficulty selector
# ---------------------------------------------------------------------------

class DifficultySelector(QFrame):
    """Card-based difficulty picker shown before the game starts."""

    difficulty_chosen = Signal(str)  # emits preset key

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        outer.setSpacing(20)

        heading = QLabel("Choose Difficulty")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet(f"""
            font-size: 28px; font-weight: 800;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        outer.addWidget(heading)

        subtitle = QLabel("Pick a level that matches your skill — you can always change later!")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"""
            font-size: 14px; color: {COLORS['text_secondary']};
            background: transparent;
        """)
        outer.addWidget(subtitle)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        accent_map = {
            "easy": "#10b981",
            "medium": "#3b82f6",
            "hard": "#ef4444",
            "expert": "#f59e0b",
        }

        for key in ("easy", "medium", "hard", "expert"):
            preset = DIFFICULTY_PRESETS[key]
            accent = accent_map[key]
            card = self._make_card(key, preset, accent)
            cards_row.addWidget(card)

        outer.addLayout(cards_row)

    def _make_card(self, key: str, preset: dict, accent: str) -> QFrame:
        card = QFrame()
        card.setFixedWidth(180)
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {accent};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        emoji = QLabel(preset["emoji"])
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet("font-size: 42px; background: transparent;")
        layout.addWidget(emoji)

        name = QLabel(preset["name"])
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet(f"""
            font-size: 18px; font-weight: 800;
            color: {accent}; background: transparent;
        """)
        layout.addWidget(name)

        desc = QLabel(preset["description"])
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            font-size: 12px; color: {COLORS['text_secondary']};
            background: transparent;
        """)
        layout.addWidget(desc)

        layout.addSpacing(8)

        btn = QPushButton("Play")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 0;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        btn.clicked.connect(lambda checked=False, k=key: self.difficulty_chosen.emit(k))
        layout.addWidget(btn)

        return card


# ---------------------------------------------------------------------------
# Game-over overlay
# ---------------------------------------------------------------------------

class GameOverOverlay(QFrame):
    """Semi-transparent overlay shown on game over."""

    play_again = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(10, 10, 20, 0.85); border-radius: 0px;")
        self.hide()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        title = QLabel("GAME OVER")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 48px; font-weight: 900;
            color: #ef4444; letter-spacing: 4px;
            background: transparent;
        """)
        layout.addWidget(title)

        self.final_score_label = QLabel("Score: 0")
        self.final_score_label.setAlignment(Qt.AlignCenter)
        self.final_score_label.setStyleSheet("""
            font-size: 28px; font-weight: 700;
            color: #f8fafc; background: transparent;
        """)
        layout.addWidget(self.final_score_label)

        self.high_score_label = QLabel("")
        self.high_score_label.setAlignment(Qt.AlignCenter)
        self.high_score_label.setStyleSheet("""
            font-size: 16px; font-weight: 600;
            color: #10b981; background: transparent;
        """)
        layout.addWidget(self.high_score_label)

        layout.addSpacing(16)

        retry_btn = QPushButton("🔄  Play Again")
        retry_btn.setObjectName("primary")
        retry_btn.setMinimumWidth(200)
        retry_btn.setMinimumHeight(48)
        retry_btn.setCursor(Qt.PointingHandCursor)
        retry_btn.clicked.connect(self.play_again.emit)
        layout.addWidget(retry_btn, alignment=Qt.AlignCenter)

    def show_results(self, score: int, best: int, is_new_best: bool):
        self.final_score_label.setText(f"Score: {score}")
        if is_new_best:
            self.high_score_label.setText("🏆  NEW HIGH SCORE!")
        else:
            self.high_score_label.setText(f"Best: {best}")
        self.show()
        self.raise_()


# ---------------------------------------------------------------------------
# Main GamePage widget
# ---------------------------------------------------------------------------

class GamePage(QWidget):
    """Gamified sign language learning page.

    Letters and numbers fall from the top; the player must sign them
    before they reach the bottom.
    """

    back_requested = Signal()

    TICK_INTERVAL_MS = 16   # ~60 fps
    MAX_LIVES = 3
    MATCHES_PER_LEVEL = 5

    ALL_CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

    def __init__(self, classifier: Classifier = None, parent=None):
        super().__init__(parent)
        self.classifier = classifier or Classifier()

        # Determine available characters from the trained model
        model_classes = self.classifier.get_classes()
        if model_classes:
            self._char_pool = [c.upper() for c in model_classes
                               if c.upper() in self.ALL_CHARS]
        else:
            self._char_pool = list(self.ALL_CHARS)
        if not self._char_pool:
            self._char_pool = list("ABCDEFGHIJ")

        # Filter WORD_POOL to only include words whose letters are all in _char_pool
        self._word_pool = [w for w in WORD_POOL
                           if all(ch in self._char_pool for ch in w)]
        if not self._word_pool:
            self._word_pool = ["HI", "NO", "GO"]  # fallback

        # State
        self._score = 0
        self._lives = self.MAX_LIVES
        self._level = 1
        self._best_score = 0
        self._matches_in_level = 0
        self._is_playing = False
        self._hints_enabled = False
        self._difficulty_key = "easy"
        self._preset = DIFFICULTY_PRESETS["easy"]
        self._last_prediction = ""
        self._last_prediction_confidence = 0.0

        # Timers
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(self.TICK_INTERVAL_MS)
        self._tick_timer.timeout.connect(self._tick)

        self._spawn_timer = QTimer(self)
        self._spawn_timer.timeout.connect(self._spawn_item)

        self._setup_ui()
        self._connect_signals()

    # ── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self._on_back)

        title = QLabel("🎮 Sign Language Game")
        title.setObjectName("pageTitle")

        self._prediction_pill = QLabel("Sign: --")
        self._prediction_pill.setObjectName("statusPill")

        # Hint toggle
        self._hint_btn = QPushButton("💡 Hints: OFF")
        self._hint_btn.setCursor(Qt.PointingHandCursor)
        self._hint_btn.setCheckable(True)
        self._hint_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:checked {{
                background-color: rgba(245, 158, 11, 0.15);
                color: #f59e0b; border-color: #f59e0b;
            }}
            QPushButton:hover {{ border-color: {COLORS['primary']}; }}
        """)
        self._hint_btn.clicked.connect(self._toggle_hints)

        # Difficulty badge (shows current difficulty during play)
        self._diff_badge = QLabel("")
        self._diff_badge.setStyleSheet(f"""
            font-size: 12px; font-weight: 700;
            color: {COLORS['text_muted']};
            background: transparent;
            padding: 4px 10px;
        """)

        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._diff_badge)
        header.addWidget(self._hint_btn)
        header.addWidget(self._prediction_pill)

        main_layout.addLayout(header)

        # HUD
        self.hud = GameHUD()
        main_layout.addWidget(self.hud)

        # Content — game canvas + camera side-by-side
        self._game_content = QWidget()
        content = QHBoxLayout(self._game_content)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(16)

        # Game canvas (left)
        self.canvas = GameCanvas()
        self.canvas.setStyleSheet("border-radius: 16px;")
        content.addWidget(self.canvas, 3)

        # Right panel: camera + prediction + hint
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        cam_label = QLabel("📷 Your Camera")
        cam_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px; font-weight: 700;
            letter-spacing: 1px; background: transparent;
        """)
        right_panel.addWidget(cam_label)

        self.camera_widget = CameraWidget()
        self.camera_widget.setMaximumHeight(300)
        self.camera_widget.setMinimumWidth(320)
        right_panel.addWidget(self.camera_widget)

        # Current prediction display
        pred_card = QFrame()
        pred_card.setObjectName("card")
        pred_layout = QVBoxLayout(pred_card)
        pred_layout.setAlignment(Qt.AlignCenter)

        self._pred_char_label = QLabel("?")
        self._pred_char_label.setAlignment(Qt.AlignCenter)
        self._pred_char_label.setStyleSheet(f"""
            font-size: 56px; font-weight: 900;
            color: {COLORS['primary']}; background: transparent;
        """)
        pred_title = QLabel("YOUR SIGN")
        pred_title.setAlignment(Qt.AlignCenter)
        pred_title.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 700; letter-spacing: 1px; background: transparent;")

        pred_layout.addWidget(self._pred_char_label)
        pred_layout.addWidget(pred_title)
        right_panel.addWidget(pred_card)

        # Hint panel
        self._hint_container = QFrame()
        self._hint_container.setObjectName("hintCard")
        self._hint_container.setStyleSheet(f"""
            QFrame#hintCard {{
                background: {COLORS['bg_card']};
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 14px;
            }}
        """)
        hint_layout = QVBoxLayout(self._hint_container)
        hint_layout.setContentsMargins(8, 8, 8, 8)
        hint_layout.setSpacing(4)

        hint_header = QLabel("💡 HINT")
        hint_header.setAlignment(Qt.AlignCenter)
        hint_header.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 700; letter-spacing: 1px; background: transparent;")
        hint_layout.addWidget(hint_header)

        self._hint_sign_card = None
        self._hint_card_placeholder = QVBoxLayout()
        hint_layout.addLayout(self._hint_card_placeholder)

        self._hint_container.hide()
        right_panel.addWidget(self._hint_container)

        right_panel.addStretch()
        content.addLayout(right_panel, 1)

        main_layout.addWidget(self._game_content, 1)

        # Difficulty selector (shown when not playing)
        self._difficulty_selector = DifficultySelector()
        main_layout.addWidget(self._difficulty_selector, 1)

        # Initially hide game content, show selector
        self._game_content.hide()
        self.hud.hide()
        self._diff_badge.hide()
        self._hint_btn.hide()
        self._prediction_pill.hide()

        # Game-over overlay
        self.game_over = GameOverOverlay(self)
        self.game_over.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.game_over.setGeometry(self.rect())

    # ── Signals ─────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.camera_widget.features_ready.connect(self._on_features)
        self.camera_widget.hand_detected.connect(self._on_hand_detected)
        self.camera_widget.heuristic_gesture_detected.connect(self._on_heuristic_gesture)
        self.canvas.item_reached_bottom.connect(self._on_item_missed)
        self.game_over.play_again.connect(self._restart_same_difficulty)
        self._difficulty_selector.difficulty_chosen.connect(self._start_game)

    # ── Game lifecycle ──────────────────────────────────────────────────────

    @Slot(str)
    def _start_game(self, difficulty_key: str):
        self._difficulty_key = difficulty_key
        self._preset = DIFFICULTY_PRESETS[difficulty_key]

        self._score = 0
        self._lives = self.MAX_LIVES
        self._level = 1
        self._matches_in_level = 0
        self._is_playing = True
        self._last_prediction = ""

        self.canvas.clear_items()
        self.game_over.hide()
        self._difficulty_selector.hide()
        self._game_content.show()
        self.hud.show()
        self._diff_badge.show()
        self._hint_btn.show()
        self._prediction_pill.show()
        self._diff_badge.setText(f"{self._preset['emoji']} {self._preset['name']}")

        self.hud.update_hud(self._score, self._lives, self._level, self._best_score)

        self.camera_widget.start()
        self.classifier.clear_buffer()

        self._spawn_timer.setInterval(self._preset["spawn_interval_ms"])
        self._spawn_timer.start()
        self._tick_timer.start()

        self._spawn_item()

    def _restart_same_difficulty(self):
        self._start_game(self._difficulty_key)

    def _end_game(self):
        self._is_playing = False
        self._tick_timer.stop()
        self._spawn_timer.stop()
        self.camera_widget.stop()

        is_new_best = self._score > self._best_score
        if is_new_best:
            self._best_score = self._score

        self.hud.update_hud(self._score, self._lives, self._level, self._best_score)
        self.game_over.show_results(self._score, self._best_score, is_new_best)

    def _on_back(self):
        if self._is_playing:
            self._end_game()
        self.camera_widget.stop()
        self._tick_timer.stop()
        self._spawn_timer.stop()
        self._game_content.hide()
        self.hud.hide()
        self._diff_badge.hide()
        self._hint_btn.hide()
        self._prediction_pill.hide()
        self._difficulty_selector.show()
        self.game_over.hide()
        self.canvas.clear_items()
        self.back_requested.emit()

    # ── Game loop ───────────────────────────────────────────────────────────

    def _tick(self):
        if not self._is_playing:
            return
        dt = self.TICK_INTERVAL_MS / 1000.0
        self.canvas.tick(dt)

    def _spawn_item(self):
        if not self._is_playing:
            return

        # Respect max_items constraint
        if self.canvas.alive_count() >= self._preset["max_items"]:
            return

        margin = 70
        max_x = max(self.canvas.width() - margin, margin + 1)
        speed = self._preset["fall_speed"] + self._preset["speed_increment"] * (self._level - 1)

        if self._preset["use_words"]:
            word = random.choice(self._word_pool)
            item_width = len(word) * 52 + 8
            safe_max_x = max(self.canvas.width() - item_width - 20, margin)
            x = random.randint(margin, max(margin, safe_max_x))
            self.canvas.add_item(FallingItem(word[0], float(x), speed, word=word))
        else:
            char = random.choice(self._char_pool)
            x = random.randint(margin, max_x)
            self.canvas.add_item(FallingItem(char, float(x), speed))

        self._update_hint_display()

    # ── ML callbacks ────────────────────────────────────────────────────────

    @Slot(object)
    def _on_features(self, features):
        if not self._is_playing or features is None:
            return
        if not self.classifier.is_loaded:
            return

        label, confidence = self.classifier.predict(features, use_smoothing=False)
        if label and confidence > 0.50:
            self._last_prediction = label.upper()
            self._last_prediction_confidence = confidence
            self._pred_char_label.setText(self._last_prediction)
            self._prediction_pill.setText(f"Sign: {self._last_prediction} ({confidence:.0%})")

            color = COLORS['success'] if confidence >= 0.7 else COLORS['primary']
            self._pred_char_label.setStyleSheet(f"""
                font-size: 56px; font-weight: 900;
                color: {color}; background: transparent;
            """)
            self._try_match(self._last_prediction)
        else:
            self._prediction_pill.setText("Sign: --")

    @Slot(str, float)
    def _on_heuristic_gesture(self, gesture: str, confidence: float):
        if not self._is_playing:
            return
        upper = gesture.upper()
        self._last_prediction = upper
        self._pred_char_label.setText(upper)
        self._prediction_pill.setText(f"Sign: {upper} ({confidence:.0%})")
        self._try_match(upper)

    @Slot(bool)
    def _on_hand_detected(self, detected: bool):
        if not detected:
            self._pred_char_label.setText("👋")
            self._pred_char_label.setStyleSheet(f"""
                font-size: 56px; font-weight: 900;
                color: {COLORS['text_muted']}; background: transparent;
            """)

    # ── Match logic ─────────────────────────────────────────────────────────

    def _try_match(self, char: str):
        result = self.canvas.consume_letter_match(char)
        if result == "full":
            self._score += 1
            self._matches_in_level += 1

            if self._matches_in_level >= self.MATCHES_PER_LEVEL:
                self._level += 1
                self._matches_in_level = 0
                current_interval = self._spawn_timer.interval()
                new_interval = max(self._preset["spawn_min_ms"],
                                   current_interval - 150)
                self._spawn_timer.setInterval(new_interval)

            self.hud.update_hud(self._score, self._lives, self._level, self._best_score)
            self._update_hint_display()
        elif result == "partial":
            # Letter matched in word but word not complete — update hint
            self._update_hint_display()

    def _on_item_missed(self, word: str):
        if not self._is_playing:
            return
        self._lives -= 1
        self.hud.update_hud(self._score, self._lives, self._level, self._best_score)
        if self._lives <= 0:
            self._end_game()
        else:
            self._update_hint_display()

    # ── Hints ───────────────────────────────────────────────────────────────

    def _toggle_hints(self):
        self._hints_enabled = self._hint_btn.isChecked()
        if self._hints_enabled:
            self._hint_btn.setText("💡 Hints: ON")
            self._hint_container.show()
            self._update_hint_display()
        else:
            self._hint_btn.setText("💡 Hints: OFF")
            self._hint_container.hide()

    def _get_lowest_item(self):
        best = None
        for item in self.canvas.items:
            if item.is_alive:
                if best is None or item.y > best.y:
                    best = item
        return best

    def _update_hint_display(self):
        if not self._hints_enabled:
            return

        lowest = self._get_lowest_item()
        target_char = lowest.current_letter if lowest else None

        # Skip rebuild if same character
        if self._hint_sign_card is not None:
            if target_char and getattr(self._hint_sign_card, 'letter', None) == target_char:
                return

        # Remove old card
        if self._hint_sign_card is not None:
            self._hint_card_placeholder.removeWidget(self._hint_sign_card)
            self._hint_sign_card.deleteLater()
            self._hint_sign_card = None

        if target_char and target_char in SIGN_GUIDE:
            self._hint_sign_card = SignCard(target_char)
            self._hint_sign_card.setMaximumHeight(350)
            self._hint_card_placeholder.addWidget(self._hint_sign_card)
        elif target_char:
            fallback = QLabel(f"Sign the character:\n{target_char}")
            fallback.setAlignment(Qt.AlignCenter)
            fallback.setStyleSheet(f"""
                font-size: 24px; font-weight: 700;
                color: {COLORS['text_primary']};
                background: transparent; padding: 20px;
            """)
            wrapper = QFrame()
            wrapper.letter = target_char
            wl = QVBoxLayout(wrapper)
            wl.addWidget(fallback)
            self._hint_sign_card = wrapper
            self._hint_card_placeholder.addWidget(self._hint_sign_card)

    # ── Cleanup ─────────────────────────────────────────────────────────────

    def cleanup(self):
        """Release resources."""
        self._tick_timer.stop()
        self._spawn_timer.stop()
        self.camera_widget.stop()
        self.camera_widget.release()
