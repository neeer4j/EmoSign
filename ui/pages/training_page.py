"""
Training Page - Train the app to recognize predefined gestures

This page allows users to:
1. Select a predefined gesture from the vocabulary
2. Show that gesture to the camera
3. Capture training samples
4. Train the model with collected data

Only predefined gestures can be trained - this ensures reliability
and a constrained, working vocabulary.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QProgressBar, QComboBox, QStackedWidget, QMessageBox,
    QListWidget, QListWidgetItem, QSplitter, QSpinBox
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS
from ui.page_header import make_page_header
from ui.camera_widget import CameraWidget
from ml.data_collector import DataCollector
from ml.trainer import Trainer
from ml.classifier import Classifier
from core.simple_engine import get_trainable_gestures, LETTERS, WORD_GESTURES

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
        self.category_combo.addItems(["All", "Letters", "Numbers", "Words"])
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
            "Words": "word"
        }
        filter_cat = category_map.get(category)
        
        for gesture_id, display_name, cat in self.all_gestures:
            if filter_cat is None or cat == filter_cat:
                item = QListWidgetItem(f"{display_name} ({gesture_id})")
                item.setData(Qt.UserRole, (gesture_id, display_name))
                self.gesture_list.addItem(item)
    
    def _on_gesture_clicked(self, item: QListWidgetItem):
        gesture_id, display_name = item.data(Qt.UserRole)
        self.selected_label.setText(f"Selected: {display_name} ({gesture_id})")
        self.gesture_selected.emit(gesture_id, display_name)
    
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
        
        # Current gesture display
        self.gesture_display = QLabel("?")
        self.gesture_display.setAlignment(Qt.AlignCenter)
        self.gesture_display.setStyleSheet(f"""
            font-size: 72px;
            font-weight: bold;
            color: {COLORS['primary']};
            background-color: {COLORS['bg_input']};
            border-radius: 16px;
            padding: 24px;
            min-height: 100px;
        """)
        layout.addWidget(self.gesture_display)
        
        # Instructions
        self.instructions = QLabel("Select a gesture, then hold it in front of the camera")
        self.instructions.setAlignment(Qt.AlignCenter)
        self.instructions.setWordWrap(True)
        self.instructions.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        layout.addWidget(self.instructions)
        
        # Sample count settings
        settings_row = QHBoxLayout()
        samples_label = QLabel("Samples per capture:")
        samples_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        
        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(10, 100)
        self.samples_spin.setValue(30)
        self.samples_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                min-width: 80px;
            }}
        """)
        
        settings_row.addWidget(samples_label)
        settings_row.addWidget(self.samples_spin)
        settings_row.addStretch()
        layout.addLayout(settings_row)
        
        # Sample count display
        self.sample_count_label = QLabel("Samples collected: 0")
        self.sample_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        layout.addWidget(self.sample_count_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_input']};
                border-radius: 6px;
                height: 20px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.capture_btn = QPushButton("📸 Capture Samples")
        self.capture_btn.setStyleSheet(self._button_style(primary=True))
        self.capture_btn.clicked.connect(self.capture_requested.emit)
        self.capture_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setStyleSheet(self._button_style())
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        
        btn_layout.addWidget(self.capture_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        
        # Train button (prominent)
        self.train_btn = QPushButton("🧠 Train Model")
        self.train_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 16px 32px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0ea566;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_panel']};
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
    2. Capture training samples for each gesture
    3. Train/retrain the model
    """
    
    back_requested = Signal()
    model_trained = Signal(float)  # Emits accuracy
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Components
        self.data_collector = DataCollector()
        self.trainer = Trainer()
        self.classifier = Classifier()
        
        # State
        self._is_capturing = False
        self._current_gesture = None
        self._capture_count = 0
        self._target_count = 30
        
        # Capture timer
        self._capture_timer = QTimer()
        self._capture_timer.timeout.connect(self._capture_sample)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        
        # Header
        header, _ = make_page_header("🎓 Train Gestures", back_signal=self.back_requested)
        main_layout.addLayout(header)
        
        # Info banner
        info = QLabel("📌 Train the app to recognize your hand gestures. Select a gesture, hold it steadily, and capture samples.")
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
        
        self.training_controls.set_capturing(True)
        self.training_controls.progress_bar.setMaximum(self._target_count)
        self.training_controls.progress_bar.setValue(0)
        
        # Capture every 100ms
        self._capture_timer.start(100)
    
    def _stop_capture(self):
        """Stop capturing samples."""
        self._is_capturing = False
        self._capture_timer.stop()
        self.training_controls.set_capturing(False)
        
        # Update stats
        counts = self.data_collector.get_label_counts()
        self.training_stats.update_stats(counts)
        self.training_controls.update_sample_count(
            self.data_collector.get_sample_count()
        )
    
    @Slot(object)
    def _on_features(self, features):
        """Handle features from camera."""
        if not self._is_capturing or features is None:
            return
        
        # Add sample
        if self.data_collector.add_sample(features):
            self._capture_count += 1
            self.training_controls.progress_bar.setValue(self._capture_count)
            
            if self._capture_count >= self._target_count:
                self._stop_capture()
    
    def _capture_sample(self):
        """Timer callback for capture - features are handled by _on_features."""
        pass
    
    def _train_model(self):
        """Train the model with collected data."""
        total_samples = self.data_collector.get_sample_count()
        if total_samples < 50:
            QMessageBox.warning(
                self, 
                "Not Enough Data",
                f"Need at least 50 samples to train. Currently have {total_samples}."
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
        
        if len(all_features) < 100:
            QMessageBox.warning(
                self,
                "Need More Data",
                f"Need at least 100 total samples. Have {len(all_features)}.\n"
                "Collect more samples or combine with existing data."
            )
            return
        
        # Convert to numpy
        import numpy as np
        features_array = np.array(all_features, dtype=np.float32)
        
        # Train
        self.training_controls.setEnabled(False)
        self.training_controls.instructions.setText("Training model... please wait")
        
        try:
            accuracy = self.trainer.train(features_array, all_labels)
            self.trainer.save()
            
            # Save training data
            self.data_collector.save()
            
            # Reload classifier
            self.classifier.load()
            
            # Update UI
            self.training_stats.set_trained(accuracy)
            self.training_controls.instructions.setText(
                f"✅ Model trained! Accuracy: {accuracy:.1%}"
            )
            
            # Emit signal
            self.model_trained.emit(accuracy)
            
            QMessageBox.information(
                self,
                "Training Complete",
                f"Model trained successfully!\n\n"
                f"Accuracy: {accuracy:.1%}\n"
                f"Classes: {len(self.trainer.get_classes())}\n"
                f"Total samples: {len(all_labels)}"
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
