"""
Shared page header builder for consistent header layout across all pages.

Usage:
    from ui.page_header import make_page_header

    header, back_btn = make_page_header("🎮 Sign Language Game")
    main_layout.addLayout(header)
"""
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal

from ui.styles import COLORS


def make_page_header(title_text: str, back_signal=None, back_callback=None):
    """Create a standardized page header with title.

    Args:
        title_text: Title text (can include emoji prefix like "🎮 Game").
        back_signal: Unused (kept for backwards compatibility).
        back_callback: Unused (kept for backwards compatibility).

    Returns:
        (QHBoxLayout, None) — the header row and None (back button removed).
    """
    header = QHBoxLayout()
    header.setSpacing(12)
    header.setContentsMargins(0, 0, 0, 8)

    # Title — consistent style
    title = QLabel(title_text)
    title.setObjectName("pageTitle")

    header.addWidget(title)
    header.addStretch()

    return header, None
