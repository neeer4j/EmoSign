"""
Training Page - Train the app to recognize gestures

This page allows users to:
1. Select a predefined gesture from the vocabulary
2. Create custom gestures with any name
3. Show that gesture to the camera
4. Capture training samples
5. Train the model with collected data
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QProgressBar, QComboBox, QStackedWidget, QMessageBox,
    QListWidget, QListWidgetItem, QSplitter, QSpinBox,
    QLineEdit, QInputDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS
from ui.page_header import make_page_header
from ui.camera_widget import CameraWidget
from ml.data_collector import DataCollector
from ml.trainer import Trainer
from ml.classifier import Classifier
from ml.keras_trainer import KerasTrainer
from detector.landmark_normalizer import LandmarkNormalizer
from core.simple_engine import (
    get_trainable_gestures, LETTERS, WORD_GESTURES,
    add_custom_gesture, remove_custom_gesture, load_custom_gestures
)

import os
import config


class GestureSelector(QFrame):
    """Widget for selecting a gesture to train."""
    
    gesture_selected = Signal(str, str)  # (gesture_id, display_name)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()
        self._load_gestures()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("📝 Select Gesture to Train")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        # Category filter
        cat_row = QHBoxLayout()
        cat_label = QLabel("Category:")
        cat_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Letters", "Numbers", "Words", "Custom"])
        self.category_combo.currentTextChanged.connect(self._filter_gestures)
        self.category_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 120px;
            }}
        """)
        cat_row.addWidget(cat_label)
        cat_row.addWidget(self.category_combo)
        cat_row.addStretch()
        layout.addLayout(cat_row)
        
        # Gesture list
        self.gesture_list = QListWidget()
        self.gesture_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        self.gesture_list.itemClicked.connect(self._on_gesture_clicked)
        layout.addWidget(self.gesture_list, 1)
        
        # Selected indicator
        self.selected_label = QLabel("Selected: None")
        self.selected_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        layout.addWidget(self.selected_label)
        
        # ── Custom Gesture Section ──
        custom_frame = QFrame()
        custom_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        custom_layout = QVBoxLayout(custom_frame)
        custom_layout.setContentsMargins(12, 10, 12, 10)
        custom_layout.setSpacing(8)
        
        custom_title = QLabel("✨ Custom Gestures")
        custom_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['primary']};")
        custom_layout.addWidget(custom_title)
        
        # Input row: text field + add button
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        
        self.custom_name_input = QLineEdit()
        self.custom_name_input.setPlaceholderText("Enter gesture name...")
        self.custom_name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        self.custom_name_input.returnPressed.connect(self._add_custom_gesture)
        input_row.addWidget(self.custom_name_input, 1)
        
        self.add_custom_btn = QPushButton("+ Add")
        self.add_custom_btn.setCursor(Qt.PointingHandCursor)
        self.add_custom_btn.setFixedHeight(36)
        self.add_custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self.add_custom_btn.clicked.connect(self._add_custom_gesture)
        input_row.addWidget(self.add_custom_btn)
        
        custom_layout.addLayout(input_row)
        
        # Delete button (for selected custom gesture)
        self.delete_custom_btn = QPushButton("🗑 Delete Selected Custom Gesture")
        self.delete_custom_btn.setCursor(Qt.PointingHandCursor)
        self.delete_custom_btn.setFixedHeight(32)
        self.delete_custom_btn.setVisible(False)
        self.delete_custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
            }}
        """)
        self.delete_custom_btn.clicked.connect(self._delete_custom_gesture)
        custom_layout.addWidget(self.delete_custom_btn)
        
        layout.addWidget(custom_frame)
    
    def _load_gestures(self):
        """Load trainable gestures."""
        self.all_gestures = get_trainable_gestures()
        self._filter_gestures("All")
    
    def _filter_gestures(self, category: str):
        """Filter gestures by category."""
        self.gesture_list.clear()
        
        category_map = {
            "All": None,
            "Letters": "letter",
            "Numbers": "number", 
            "Words": "word",
            "Custom": "custom"
        }
        filter_cat = category_map.get(category)
        
        for gesture_id, display_name, cat in self.all_gestures:
            if filter_cat is None or cat == filter_cat:
                prefix = "🎨 " if cat == "custom" else ""
                item = QListWidgetItem(f"{prefix}{display_name} ({gesture_id})")
                item.setData(Qt.UserRole, (gesture_id, display_name))
                item.setData(Qt.UserRole + 1, cat)  # Store category
                self.gesture_list.addItem(item)
    
    def _on_gesture_clicked(self, item: QListWidgetItem):
        gesture_id, display_name = item.data(Qt.UserRole)
        cat = item.data(Qt.UserRole + 1)
        self.selected_label.setText(f"Selected: {display_name} ({gesture_id})")
        self.gesture_selected.emit(gesture_id, display_name)
        # Show delete button only for custom gestures
        self.delete_custom_btn.setVisible(cat == "custom")
    
    def _add_custom_gesture(self):
        """Add a new custom gesture from the input field."""
        name = self.custom_name_input.text().strip()
        if not name:
            return
        
        try:
            gesture_id, display_name = add_custom_gesture(name)
            self.custom_name_input.clear()
            
            # Reload the gesture list
            self._load_gestures()
            
            # Switch to Custom category to show the new gesture
            self.category_combo.setCurrentText("Custom")
            
            # Auto-select the newly added gesture
            for i in range(self.gesture_list.count()):
                item = self.gesture_list.item(i)
                gid, _ = item.data(Qt.UserRole)
                if gid == gesture_id:
                    self.gesture_list.setCurrentItem(item)
                    self._on_gesture_clicked(item)
                    break
                    
        except ValueError as e:
            QMessageBox.warning(
                self.window() if self.window() else self,
                "Cannot Add Gesture",
                str(e)
            )
    
    def _delete_custom_gesture(self):
        """Delete the currently selected custom gesture."""
        item = self.gesture_list.currentItem()
        if not item:
            return
        
        cat = item.data(Qt.UserRole + 1)
        if cat != "custom":
            return
        
        gesture_id, display_name = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self.window() if self.window() else self,
            "Delete Custom Gesture",
            f"Delete custom gesture '{display_name}'?\n\n"
            "This removes the gesture definition. Training data for it "
            "will remain but won't be associated with this name.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            remove_custom_gesture(gesture_id)
            self._load_gestures()
            self.selected_label.setText("Selected: None")
            self.delete_custom_btn.setVisible(False)
    
    def get_selected(self):
        """Get currently selected gesture."""
        item = self.gesture_list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None, None


class TrainingControls(QFrame):
    """Widget for training controls and sample collection."""
    
    capture_requested = Signal()
    train_requested = Signal()
    clear_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._current_gesture = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Gesture display + instructions in a horizontal row
        gesture_row = QHBoxLayout()
        gesture_row.setSpacing(16)

        self.gesture_display = QLabel("?")
        self.gesture_display.setAlignment(Qt.AlignCenter)
        self.gesture_display.setFixedSize(80, 80)
        self.gesture_display.setStyleSheet(f"""
            font-size: 48px;
            font-weight: bold;
            color: {COLORS['primary']};
            background-color: {COLORS['bg_input']};
            border-radius: 14px;
        """)
        gesture_row.addWidget(self.gesture_display)

        self.instructions = QLabel("Select a gesture, then hold it in front of the camera")
        self.instructions.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.instructions.setWordWrap(True)
        self.instructions.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        gesture_row.addWidget(self.instructions, 1)

        layout.addLayout(gesture_row)
        
        # Stats Row (Samples config + count)
        stats_row = QHBoxLayout()
        
        # Config side
        config_container = QHBoxLayout()
        config_container.setSpacing(8)
        samples_label = QLabel("Samples per capture:")
        samples_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(10, 100)
        self.samples_spin.setValue(30)
        self.samples_spin.setFixedSize(70, 36)
        self.samples_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
        """)
        config_container.addWidget(samples_label)
        config_container.addWidget(self.samples_spin)
        
        # Count side
        self.sample_count_label = QLabel("Collected: 0")
        self.sample_count_label.setStyleSheet(f"""
            color: {COLORS['primary']}; 
            font-weight: bold; 
            font-size: 14px;
            background: {COLORS['bg_input']};
            padding: 6px 12px;
            border-radius: 6px;
        """)
        
        stats_row.addLayout(config_container)
        stats_row.addStretch()
        stats_row.addWidget(self.sample_count_label)
        layout.addLayout(stats_row)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
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
        layout.addWidget(self.progress_bar)
        
        layout.addSpacing(10)
        
        # Mode toggle: Static vs Dynamic
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Static (Single Frame)", "Dynamic (Motion Clip)"])
        self.mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 180px;
            }}
        """)
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        layout.addSpacing(6)
        
        # Action Buttons (Capture & Clear)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.capture_btn = QPushButton("📸 Capture Samples")
        self.capture_btn.setCursor(Qt.PointingHandCursor)
        self.capture_btn.setFixedHeight(44)
        self.capture_btn.setStyleSheet(self._button_style(primary=True))
        self.capture_btn.clicked.connect(self.capture_requested.emit)
        self.capture_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setFixedSize(80, 44)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
            }}
        """)
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        
        btn_layout.addWidget(self.capture_btn, 1) # Expand
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        
        layout.addSpacing(20)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(line)
        
        layout.addSpacing(20)
        
        # Train button (prominent)
        self.train_btn = QPushButton("🧠 Train Model")
        self.train_btn.setCursor(Qt.PointingHandCursor)
        self.train_btn.setFixedHeight(50)
        self.train_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: #0ea566;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.train_btn.clicked.connect(self.train_requested.emit)
        self.train_btn.setEnabled(False)
        layout.addWidget(self.train_btn)
        
        layout.addStretch()
    
    def _button_style(self, primary=False) -> str:
        if primary:
            return f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary_hover']};
                }}
                QPushButton:disabled {{
                    background-color: {COLORS['bg_panel']};
                    color: {COLORS['text_muted']};
                }}
            """
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """
    
    def set_gesture(self, gesture_id: str, display_name: str):
        """Set the current gesture to train."""
        self._current_gesture = gesture_id
        self.gesture_display.setText(display_name)
        is_dynamic = display_name.upper() in ('J', 'Z')
        if is_dynamic:
            self.mode_combo.setCurrentIndex(1)  # Auto-select Dynamic mode
            self.instructions.setText(f"Perform the '{display_name}' motion in front of the camera")
        else:
            self.mode_combo.setCurrentIndex(0)
            self.instructions.setText(f"Hold the '{display_name}' gesture in front of the camera")
        self.capture_btn.setEnabled(True)
    
    def update_sample_count(self, count: int, total: int = 0):
        """Update sample count display."""
        self.sample_count_label.setText(f"Samples collected: {count}")
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(count)
        self.train_btn.setEnabled(count >= 50)  # Need at least 50 samples
    
    def set_capturing(self, capturing: bool):
        """Set capturing state."""
        if capturing:
            self.capture_btn.setText("⏹️ Stop")
            self.capture_btn.setStyleSheet(self._button_style())
        else:
            self.capture_btn.setText("📸 Capture Samples")
            self.capture_btn.setStyleSheet(self._button_style(primary=True))
    
    def get_samples_per_capture(self) -> int:
        return self.samples_spin.value()
    
    def is_dynamic_mode(self) -> bool:
        return self.mode_combo.currentIndex() == 1


class TrainingStats(QFrame):
    """Widget showing training statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        title = QLabel("📊 Training Statistics")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)
        
        self.labels_trained = QLabel("Gestures trained: 0")
        self.total_samples = QLabel("Total samples: 0")
        self.model_accuracy = QLabel("Model accuracy: --")
        self.last_trained = QLabel("Last trained: Never")
        
        for i, label in enumerate([self.labels_trained, self.total_samples, 
                                   self.model_accuracy, self.last_trained]):
            label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px;")
            stats_layout.addWidget(label, i, 0)
        
        layout.addLayout(stats_layout)
        
        # Label distribution
        self.distribution_label = QLabel("Sample distribution:")
        self.distribution_label.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-top: 8px;")
        layout.addWidget(self.distribution_label)
        
        self.distribution_list = QListWidget()
        self.distribution_list.setMaximumHeight(150)
        self.distribution_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.distribution_list)
        
        layout.addStretch()
    
    def update_stats(self, label_counts: dict, accuracy: float = 0.0):
        """Update statistics display."""
        total = sum(label_counts.values())
        num_labels = len(label_counts)
        
        self.labels_trained.setText(f"Gestures trained: {num_labels}")
        self.total_samples.setText(f"Total samples: {total}")
        
        if accuracy > 0:
            self.model_accuracy.setText(f"Model accuracy: {accuracy:.1%}")
        
        # Update distribution
        self.distribution_list.clear()
        for label, count in sorted(label_counts.items()):
            self.distribution_list.addItem(f"{label}: {count} samples")
    
    def set_trained(self, accuracy: float):
        """Mark as trained with accuracy."""
        self.model_accuracy.setText(f"Model accuracy: {accuracy:.1%}")
        from datetime import datetime
        self.last_trained.setText(f"Last trained: {datetime.now().strftime('%H:%M:%S')}")


class TrainingPage(QWidget):
    """Page for training gesture recognition.
    
    Allows users to:
    1. Select predefined gestures from the vocabulary
    2. Create and manage custom gestures with any name
    3. Capture training samples for each gesture
    4. Train/retrain the model
    """
    
    back_requested = Signal()
    model_trained = Signal(float)  # Emits accuracy
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Components
        self.data_collector = DataCollector()
        self.trainer = Trainer()
        self.classifier = Classifier()
        self.keras_trainer = KerasTrainer()
        self._normalizer = LandmarkNormalizer()
        
        # State
        self._is_capturing = False
        self._current_gesture = None
        self._capture_count = 0
        self._target_count = 30
        
        # Dynamic recording state
        self._dynamic_sequences = []   # list of (label, [30 frames of landmarks])
        self._current_sequence = []     # current 30-frame recording buffer
        self._is_recording_dynamic = False
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        
        # Header
        header, _ = make_page_header("🎓 Train Gestures")
        main_layout.addLayout(header)
        
        # Info banner
        info = QLabel("📌 Train the app to recognize your hand gestures. Select a gesture or create a custom one, hold it steadily, and capture samples.")
        info.setWordWrap(True)
        info.setStyleSheet(f"""
            background-color: {COLORS['bg_card']};
            color: {COLORS['text_secondary']};
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 4px solid {COLORS['primary']};
        """)
        main_layout.addWidget(info)
        
        # Main content - splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Gesture selector
        self.gesture_selector = GestureSelector()
        splitter.addWidget(self.gesture_selector)
        
        # Center: Camera and controls
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)
        
        self.camera_widget = CameraWidget()
        self.camera_widget.setMinimumSize(480, 360)
        center_layout.addWidget(self.camera_widget)
        
        self.training_controls = TrainingControls()
        center_layout.addWidget(self.training_controls)
        
        splitter.addWidget(center_widget)
        
        # Right: Stats
        self.training_stats = TrainingStats()
        splitter.addWidget(self.training_stats)
        
        splitter.setSizes([250, 500, 250])
        main_layout.addWidget(splitter, 1)
    
    def _connect_signals(self):
        self.gesture_selector.gesture_selected.connect(self._on_gesture_selected)
        self.training_controls.capture_requested.connect(self._toggle_capture)
        self.training_controls.train_requested.connect(self._train_model)
        self.training_controls.clear_requested.connect(self._clear_data)
        self.camera_widget.features_ready.connect(self._on_features)
    
    @Slot(str, str)
    def _on_gesture_selected(self, gesture_id: str, display_name: str):
        """Handle gesture selection."""
        self._current_gesture = gesture_id
        self.training_controls.set_gesture(gesture_id, display_name)
        self.data_collector.set_label(gesture_id)
    
    def _toggle_capture(self):
        """Toggle sample capture."""
        if self._is_capturing:
            self._stop_capture()
        else:
            self._start_capture()
    
    def _start_capture(self):
        """Start capturing samples."""
        if not self._current_gesture:
            return
        
        if not self.camera_widget.is_running:
            self.camera_widget.start()
        
        self._is_capturing = True
        self._capture_count = 0
        self._target_count = self.training_controls.get_samples_per_capture()
        
        # Check if dynamic mode
        if self.training_controls.is_dynamic_mode():
            self._is_recording_dynamic = True
            self._current_sequence = []
            self.training_controls.instructions.setText(
                f"🎬 Recording motion clip... perform the gesture NOW"
            )
            self.training_controls.progress_bar.setMaximum(30)  # 30 frames
            self.training_controls.progress_bar.setValue(0)
        else:
            self._is_recording_dynamic = False
            self.training_controls.progress_bar.setMaximum(self._target_count)
            self.training_controls.progress_bar.setValue(0)
        
        self.training_controls.set_capturing(True)
    
    def _stop_capture(self):
        """Stop capturing samples."""
        self._is_capturing = False
        self.training_controls.set_capturing(False)
        
        # If dynamic recording was active, save the sequence
        if self._is_recording_dynamic and len(self._current_sequence) >= 10:
            self._dynamic_sequences.append(
                (self._current_gesture, list(self._current_sequence))
            )
            seq_count = len(self._dynamic_sequences)
            self.training_controls.instructions.setText(
                f"✅ Motion clip recorded! ({seq_count} clips total)"
            )
        self._is_recording_dynamic = False
        self._current_sequence = []
        
        # Update stats
        counts = self.data_collector.get_label_counts()
        # Add dynamic sequence counts
        for label, _ in self._dynamic_sequences:
            counts[label] = counts.get(label, 0)
        if self._dynamic_sequences:
            dyn_labels = set(l for l, _ in self._dynamic_sequences)
            for dl in dyn_labels:
                dc = sum(1 for l, _ in self._dynamic_sequences if l == dl)
                counts[f"{dl} (motion)"] = dc
        
        self.training_stats.update_stats(counts)
        self.training_controls.update_sample_count(
            self.data_collector.get_sample_count()
        )
        # Enable training if we have enough static OR dynamic data
        total = self.data_collector.get_sample_count() + len(self._dynamic_sequences) * 30
        self.training_controls.train_btn.setEnabled(total >= 50)
    
    @Slot(object)
    def _on_features(self, features):
        """Handle features from camera (both static and dynamic modes)."""
        if not self._is_capturing or features is None:
            return
        
        if self._is_recording_dynamic:
            # Dynamic mode: grab raw landmarks for sequence recording
            landmarks = self.camera_widget.hand_tracker.get_landmarks()
            if landmarks is not None:
                self._current_sequence.append(landmarks)
                self.training_controls.progress_bar.setValue(len(self._current_sequence))
                # Auto-stop at 30 frames
                if len(self._current_sequence) >= 30:
                    self._stop_capture()
            return
        
        # Static mode: add sample
        if self.data_collector.add_sample(features):
            self._capture_count += 1
            self.training_controls.progress_bar.setValue(self._capture_count)
            
            if self._capture_count >= self._target_count:
                self._stop_capture()
    
    def _train_model(self):
        """Train the model with collected data."""
        total_samples = self.data_collector.get_sample_count()
        total_dynamic = len(self._dynamic_sequences)
        
        if total_samples < 50 and total_dynamic < 5:
            QMessageBox.warning(
                self, 
                "Not Enough Data",
                f"Need at least 50 static samples or 5 dynamic clips.\n"
                f"Currently have {total_samples} static, {total_dynamic} dynamic."
            )
            return
        
        # Check for existing training data
        existing_data = self._load_existing_data()
        
        # Combine with collected samples
        all_features = []
        all_labels = []
        
        # Add existing data
        if existing_data:
            features, labels = existing_data
            all_features.extend(features)
            all_labels.extend(labels)
        
        # Add new samples
        for sample in self.data_collector.samples:
            all_features.append(sample['features'])
            all_labels.append(sample['label'])
        
        import numpy as np
        
        # Train
        self.training_controls.setEnabled(False)
        self.training_controls.instructions.setText("Training models... please wait")
        
        try:
            results = []
            
            # --- 1. Train sklearn (legacy) ---
            if len(all_features) >= 100:
                features_array = np.array(all_features, dtype=np.float32)
                accuracy = self.trainer.train(features_array, all_labels)
                self.trainer.save()
                self.data_collector.save()
                self.classifier.load()
                results.append(f"sklearn: {accuracy:.1%}")
            
            # --- 2. Train Keras MLP (static, 63 features) ---
            if len(all_features) >= 100:
                features_array = np.array(all_features, dtype=np.float32)
                # Extract first 63 features (coordinates only)
                keras_features = features_array[:, :63]
                keras_acc = self.keras_trainer.train_static(
                    keras_features, all_labels, epochs=50, batch_size=32
                )
                results.append(f"Keras MLP: {keras_acc:.1%}")
                accuracy = keras_acc  # Use Keras accuracy as primary
            else:
                accuracy = 0.0
            
            # --- 3. Train Keras LSTM (dynamic sequences) ---
            if len(self._dynamic_sequences) >= 5:
                dyn_features = []
                dyn_labels = []
                for label, seq in self._dynamic_sequences:
                    normed = self._normalizer.normalize_sequence(seq)
                    if normed is not None:
                        # Pad/truncate to 30 frames
                        if normed.shape[0] < 30:
                            pad = np.zeros((30 - normed.shape[0], 63), dtype=np.float32)
                            normed = np.concatenate([pad, normed], axis=0)
                        elif normed.shape[0] > 30:
                            normed = normed[-30:]
                        dyn_features.append(normed)
                        dyn_labels.append(label)
                
                if len(dyn_features) >= 5:
                    dyn_array = np.stack(dyn_features, axis=0)
                    lstm_acc = self.keras_trainer.train_dynamic(
                        dyn_array, dyn_labels, epochs=50, batch_size=8
                    )
                    results.append(f"Keras LSTM: {lstm_acc:.1%}")
            
            # Update UI
            if accuracy > 0:
                self.training_stats.set_trained(accuracy)
            self.training_controls.instructions.setText(
                f"✅ Training complete! {' | '.join(results)}"
            )
            
            # Emit signal
            if accuracy > 0:
                self.model_trained.emit(accuracy)
            
            msg_parts = ["Models trained successfully!\n"]
            for r in results:
                msg_parts.append(f"  • {r}")
            if self._dynamic_sequences:
                msg_parts.append(f"\nDynamic clips: {len(self._dynamic_sequences)}")
            msg_parts.append(f"Static samples: {len(all_labels)}")
            
            QMessageBox.information(
                self,
                "Training Complete",
                "\n".join(msg_parts)
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Training Error",
                f"Error during training:\n{str(e)}"
            )
        finally:
            self.training_controls.setEnabled(True)
    
    def _load_existing_data(self):
        """Load existing training data from CSV files."""
        import glob
        import csv
        import numpy as np
        
        data_files = glob.glob(os.path.join(config.DATA_DIR, "*.csv"))
        if not data_files:
            return None
        
        all_features = []
        all_labels = []
        
        for filepath in data_files:
            try:
                with open(filepath, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        label = row.get('label', '')
                        if not label:
                            continue
                        
                        features = []
                        # Dynamically detect feature count from columns
                        i = 0
                        while f'f{i}' in row:
                            try:
                                features.append(float(row[f'f{i}']))
                            except ValueError:
                                break
                            i += 1
                        
                        if len(features) > 0:
                            all_features.append(features)
                            all_labels.append(label)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                continue
        
        if all_features:
            return np.array(all_features, dtype=np.float32), all_labels
        return None
    
    def _clear_data(self):
        """Clear collected data."""
        reply = QMessageBox.question(
            self,
            "Clear Data",
            "Clear all collected samples? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_collector.clear()
            self.training_stats.update_stats({})
            self.training_controls.update_sample_count(0)
            self.training_controls.progress_bar.setValue(0)
    
    def showEvent(self, event):
        """Start camera when page is shown."""
        super().showEvent(event)
        self.camera_widget.start()
        
        # Update stats
        counts = self.data_collector.get_label_counts()
        self.training_stats.update_stats(counts)
    
    def hideEvent(self, event):
        """Stop camera when page is hidden."""
        super().hideEvent(event)
        if self._is_capturing:
            self._stop_capture()
        self.camera_widget.stop()
    
    def cleanup(self):
        """Clean up resources."""
        if self._is_capturing:
            self._stop_capture()
        self.camera_widget.stop()
