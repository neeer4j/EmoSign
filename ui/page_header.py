"""
Shared page header builder for consistent header layout across all pages.

Usage:
    from ui.page_header import make_page_header

    header, back_btn = make_page_header("🎮 Sign Language Game", back_signal=self.back_requested)
    # Optionally add right-side widgets to header before adding to layout:
    header.addWidget(some_widget)
    main_layout.addLayout(header)
"""
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal

from ui.styles import COLORS


def make_page_header(title_text: str, back_signal=None, back_callback=None):
    """Create a standardized page header with back button and title.

    Args:
        title_text: Title text (can include emoji prefix like "🎮 Game").
        back_signal: A Signal to emit when back is clicked (preferred).
        back_callback: A callable for back button clicks (alternative).

    Returns:
        (QHBoxLayout, QPushButton) — the header row and the back button.
    """
    header = QHBoxLayout()
    header.setSpacing(12)

    # Back button — consistent across all pages
    back_btn = QPushButton("← Back")
    back_btn.setObjectName("ghost")
    back_btn.setCursor(Qt.PointingHandCursor)
    back_btn.setFixedHeight(36)
    if back_signal is not None:
        back_btn.clicked.connect(back_signal.emit)
    elif back_callback is not None:
        back_btn.clicked.connect(back_callback)

    # Title — consistent style
    title = QLabel(title_text)
    title.setObjectName("pageTitle")

    header.addWidget(back_btn)
    header.addWidget(title)
    header.addStretch()

    return header, back_btn
