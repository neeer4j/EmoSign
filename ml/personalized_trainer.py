"""
Personalized Training Module - User-specific model calibration

Allows users to train the model on their own signing style,
improving accuracy for individual users.
"""
import os
import json
import pickle
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict

from config import BASE_DIR, MODELS_DIR


@dataclass
class UserCalibrationData:
    """Calibration data for a specific user."""
    user_id: str
    samples_per_gesture: Dict[str, int] = field(default_factory=dict)
    total_samples: int = 0
    calibration_date: Optional[datetime] = None
    accuracy_improvement: float = 0.0
    
    # Per-gesture confidence adjustments
    confidence_adjustments: Dict[str, float] = field(default_factory=dict)
    
    # Feature mean/std for normalization
    feature_means: Optional[np.ndarray] = None
    feature_stds: Optional[np.ndarray] = None


@dataclass
class CalibrationSession:
    """A calibration training session."""
    session_id: str
    user_id: str
    gesture_label: str
    samples: List[np.ndarray] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    completed: bool = False


class PersonalizedTrainer:
    """Manages personalized model training for individual users.
    
    Features:
    - Collect user-specific gesture samples
    - Fine-tune model on user's signing style
    - Adjust confidence thresholds per user
    - Track calibration progress
    """
    
    CALIBRATION_DIR = os.path.join(BASE_DIR, "user_calibration")
    SAMPLES_PER_GESTURE = 10
    
    def __init__(self):
        os.makedirs(self.CALIBRATION_DIR, exist_ok=True)
        
        self._current_session: Optional[CalibrationSession] = None
        self._user_data: Dict[str, UserCalibrationData] = {}
        
        # Gestures to calibrate (can be customized)
        self.calibration_gestures = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    
    def get_user_data(self, user_id: str) -> UserCalibrationData:
        """Get or create calibration data for a user."""
        if user_id not in self._user_data:
            # Try to load from file
            filepath = os.path.join(self.CALIBRATION_DIR, f"{user_id}_calibration.json")
            if os.path.exists(filepath):
                self._user_data[user_id] = self._load_user_data(filepath)
            else:
                self._user_data[user_id] = UserCalibrationData(user_id=user_id)
        
        return self._user_data[user_id]
    
    def _load_user_data(self, filepath: str) -> UserCalibrationData:
        """Load user calibration data from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            user_data = UserCalibrationData(
                user_id=data['user_id'],
                samples_per_gesture=data.get('samples_per_gesture', {}),
                total_samples=data.get('total_samples', 0),
                accuracy_improvement=data.get('accuracy_improvement', 0.0),
                confidence_adjustments=data.get('confidence_adjustments', {})
            )
            
            if data.get('calibration_date'):
                user_data.calibration_date = datetime.fromisoformat(data['calibration_date'])
            
            # Load feature arrays if they exist
            feature_path = filepath.replace('.json', '_features.npz')
            if os.path.exists(feature_path):
                arrays = np.load(feature_path)
                user_data.feature_means = arrays.get('means')
                user_data.feature_stds = arrays.get('stds')
            
            return user_data
        except Exception as e:
            print(f"Error loading user calibration: {e}")
            return UserCalibrationData(user_id="unknown")
    
    def save_user_data(self, user_id: str):
        """Save user calibration data to file."""
        if user_id not in self._user_data:
            return
        
        user_data = self._user_data[user_id]
        filepath = os.path.join(self.CALIBRATION_DIR, f"{user_id}_calibration.json")
        
        data = {
            'user_id': user_data.user_id,
            'samples_per_gesture': user_data.samples_per_gesture,
            'total_samples': user_data.total_samples,
            'calibration_date': user_data.calibration_date.isoformat() if user_data.calibration_date else None,
            'accuracy_improvement': user_data.accuracy_improvement,
            'confidence_adjustments': user_data.confidence_adjustments
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save feature arrays separately
        if user_data.feature_means is not None:
            feature_path = filepath.replace('.json', '_features.npz')
            np.savez(feature_path, 
                    means=user_data.feature_means,
                    stds=user_data.feature_stds)
    
    def start_calibration_session(self, user_id: str, gesture_label: str) -> CalibrationSession:
        """Start a new calibration session for a specific gesture."""
        session = CalibrationSession(
            session_id=f"{user_id}_{gesture_label}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=user_id,
            gesture_label=gesture_label.upper()
        )
        self._current_session = session
        return session
    
    def add_sample(self, features: np.ndarray) -> int:
        """Add a feature sample to the current calibration session.
        
        Returns:
            Number of samples collected so far
        """
        if self._current_session is None:
            return 0
        
        self._current_session.samples.append(features.copy())
        return len(self._current_session.samples)
    
    def complete_calibration_session(self) -> Dict[str, Any]:
        """Complete the current calibration session and update user data.
        
        Returns:
            Session summary
        """
        if self._current_session is None:
            return {'success': False, 'error': 'No active session'}
        
        session = self._current_session
        user_data = self.get_user_data(session.user_id)
        
        # Update counts
        gesture = session.gesture_label
        current_count = user_data.samples_per_gesture.get(gesture, 0)
        user_data.samples_per_gesture[gesture] = current_count + len(session.samples)
        user_data.total_samples += len(session.samples)
        user_data.calibration_date = datetime.now()
        
        # Calculate feature statistics for this gesture
        if session.samples:
            samples_array = np.array(session.samples)
            gesture_mean = np.mean(samples_array, axis=0)
            gesture_std = np.std(samples_array, axis=0)
            
            # Save gesture-specific samples
            self._save_gesture_samples(session.user_id, gesture, samples_array)
        
        session.completed = True
        self._current_session = None
        
        # Save updated user data
        self.save_user_data(session.user_id)
        
        return {
            'success': True,
            'gesture': gesture,
            'samples_collected': len(session.samples),
            'total_for_gesture': user_data.samples_per_gesture[gesture]
        }
    
    def _save_gesture_samples(self, user_id: str, gesture: str, samples: np.ndarray):
        """Save gesture samples to file."""
        filepath = os.path.join(
            self.CALIBRATION_DIR, 
            f"{user_id}_samples_{gesture}.npy"
        )
        
        # Append to existing samples if any
        if os.path.exists(filepath):
            existing = np.load(filepath)
            samples = np.vstack([existing, samples])
        
        np.save(filepath, samples)
    
    def get_calibration_progress(self, user_id: str) -> Dict[str, Any]:
        """Get calibration progress for a user."""
        user_data = self.get_user_data(user_id)
        
        total_gestures = len(self.calibration_gestures)
        calibrated_gestures = sum(
            1 for g in self.calibration_gestures 
            if user_data.samples_per_gesture.get(g, 0) >= self.SAMPLES_PER_GESTURE
        )
        
        return {
            'user_id': user_id,
            'total_samples': user_data.total_samples,
            'gestures_calibrated': calibrated_gestures,
            'total_gestures': total_gestures,
            'progress_percent': (calibrated_gestures / total_gestures) * 100,
            'samples_per_gesture': user_data.samples_per_gesture,
            'required_per_gesture': self.SAMPLES_PER_GESTURE,
            'last_calibration': user_data.calibration_date,
            'accuracy_improvement': user_data.accuracy_improvement
        }
    
    def get_confidence_adjustment(self, user_id: str, gesture: str) -> float:
        """Get confidence adjustment for a specific gesture.
        
        Returns:
            Adjustment factor (1.0 = no adjustment)
        """
        user_data = self.get_user_data(user_id)
        return user_data.confidence_adjustments.get(gesture.upper(), 1.0)
    
    def train_personalized_model(self, user_id: str, base_model=None) -> Dict[str, Any]:
        """Train a personalized model using user's calibration data.
        
        Args:
            user_id: User ID
            base_model: Optional base model to fine-tune
            
        Returns:
            Training results
        """
        user_data = self.get_user_data(user_id)
        
        # Collect all user samples
        all_features = []
        all_labels = []
        
        for gesture in self.calibration_gestures:
            filepath = os.path.join(
                self.CALIBRATION_DIR,
                f"{user_id}_samples_{gesture}.npy"
            )
            
            if os.path.exists(filepath):
                samples = np.load(filepath)
                all_features.extend(samples)
                all_labels.extend([gesture] * len(samples))
        
        if not all_features:
            return {'success': False, 'error': 'No calibration data found'}
        
        X = np.array(all_features)
        y = np.array(all_labels)
        
        # Calculate user-specific feature normalization
        user_data.feature_means = np.mean(X, axis=0)
        user_data.feature_stds = np.std(X, axis=0) + 1e-8
        
        # Train or fine-tune model
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import cross_val_score
            from sklearn.preprocessing import LabelEncoder
            
            # Normalize features
            X_normalized = (X - user_data.feature_means) / user_data.feature_stds
            
            # Encode labels
            le = LabelEncoder()
            y_encoded = le.fit_transform(y)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Cross-validation
            scores = cross_val_score(model, X_normalized, y_encoded, cv=min(5, len(set(y))))
            accuracy = scores.mean()
            
            # Fit final model
            model.fit(X_normalized, y_encoded)
            
            # Save personalized model
            model_path = os.path.join(
                self.CALIBRATION_DIR,
                f"{user_id}_model.pkl"
            )
            with open(model_path, 'wb') as f:
                pickle.dump({'model': model, 'label_encoder': le}, f)
            
            user_data.accuracy_improvement = accuracy
            self.save_user_data(user_id)
            
            return {
                'success': True,
                'accuracy': accuracy,
                'samples_used': len(X),
                'gestures_trained': len(set(y)),
                'model_path': model_path
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def load_personalized_model(self, user_id: str):
        """Load a user's personalized model."""
        model_path = os.path.join(
            self.CALIBRATION_DIR,
            f"{user_id}_model.pkl"
        )
        
        if not os.path.exists(model_path):
            return None
        
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
            return data['model'], data['label_encoder']
        except Exception as e:
            print(f"Error loading personalized model: {e}")
            return None
    
    def reset_calibration(self, user_id: str):
        """Reset all calibration data for a user."""
        # Remove files
        for f in os.listdir(self.CALIBRATION_DIR):
            if f.startswith(f"{user_id}_"):
                os.remove(os.path.join(self.CALIBRATION_DIR, f))
        
        # Clear from memory
        if user_id in self._user_data:
            del self._user_data[user_id]


# Singleton instance
personalized_trainer = PersonalizedTrainer()
