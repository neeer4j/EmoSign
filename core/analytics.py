"""
Analytics Module - Usage statistics and learning progress tracking

Provides:
- Usage analytics (most used signs, session stats)
- Learning progress tracking with gamification
- Achievement badges and milestones
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from enum import Enum

from config import BASE_DIR
from core.practice_scheduler import PracticeScheduler


class AchievementCategory(Enum):
    """Categories of achievements."""
    PRACTICE = "practice"
    VOCABULARY = "vocabulary"
    STREAK = "streak"
    ACCURACY = "accuracy"
    SPECIAL = "special"


@dataclass
class Achievement:
    """An achievement/badge definition."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    icon: str
    requirement: int  # Value needed to unlock
    points: int = 10


@dataclass
class UserStats:
    """User statistics."""
    user_id: str
    total_translations: int = 0
    total_signs_detected: int = 0
    total_words_formed: int = 0
    total_sentences: int = 0
    total_sessions: int = 0
    total_practice_time: float = 0.0  # in minutes
    
    # Sign usage
    sign_counts: Dict[str, int] = field(default_factory=dict)
    
    # Accuracy tracking
    correct_predictions: int = 0
    total_predictions: int = 0
    
    # Streaks
    current_streak: int = 0
    longest_streak: int = 0
    last_active_date: Optional[str] = None
    
    # Learning progress
    signs_learned: List[str] = field(default_factory=list)
    signs_mastered: List[str] = field(default_factory=list)  # >90% accuracy
    
    # Achievements
    unlocked_achievements: List[str] = field(default_factory=list)
    achievement_dates: Dict[str, str] = field(default_factory=dict)
    total_points: int = 0
    
    # Session history
    session_dates: List[str] = field(default_factory=list)

    # Spaced-repetition review state
    review_schedule: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Quiz tracking
    quiz_history: List[Dict[str, Any]] = field(default_factory=list)
    quiz_topic_performance: Dict[str, Dict[str, int]] = field(default_factory=dict)


# Define all achievements
ACHIEVEMENTS: Dict[str, Achievement] = {
    # Practice achievements
    "first_sign": Achievement(
        "first_sign", "First Sign", "Detect your first sign",
        AchievementCategory.PRACTICE, "👶", 1, 5
    ),
    "practice_10": Achievement(
        "practice_10", "Getting Started", "Detect 10 signs",
        AchievementCategory.PRACTICE, "🌱", 10, 10
    ),
    "practice_50": Achievement(
        "practice_50", "Regular Signer", "Detect 50 signs",
        AchievementCategory.PRACTICE, "✋", 50, 25
    ),
    "practice_100": Achievement(
        "practice_100", "Dedicated Learner", "Detect 100 signs",
        AchievementCategory.PRACTICE, "🔥", 100, 50
    ),
    "practice_500": Achievement(
        "practice_500", "Sign Expert", "Detect 500 signs",
        AchievementCategory.PRACTICE, "⭐", 500, 100
    ),
    "practice_1000": Achievement(
        "practice_1000", "Master Signer", "Detect 1000 signs",
        AchievementCategory.PRACTICE, "👑", 1000, 200
    ),
    
    # Vocabulary achievements
    "alphabet_complete": Achievement(
        "alphabet_complete", "ABC Master", "Learn all 26 letters",
        AchievementCategory.VOCABULARY, "🔤", 26, 100
    ),
    "words_10": Achievement(
        "words_10", "Word Builder", "Form 10 words",
        AchievementCategory.VOCABULARY, "📝", 10, 25
    ),
    "words_50": Achievement(
        "words_50", "Vocabulary Builder", "Form 50 words",
        AchievementCategory.VOCABULARY, "📚", 50, 75
    ),
    "first_sentence": Achievement(
        "first_sentence", "Sentence Maker", "Complete your first sentence",
        AchievementCategory.VOCABULARY, "💬", 1, 30
    ),
    
    # Streak achievements
    "streak_3": Achievement(
        "streak_3", "3 Day Streak", "Practice 3 days in a row",
        AchievementCategory.STREAK, "🔥", 3, 30
    ),
    "streak_7": Achievement(
        "streak_7", "Week Warrior", "Practice 7 days in a row",
        AchievementCategory.STREAK, "📅", 7, 70
    ),
    "streak_30": Achievement(
        "streak_30", "Monthly Master", "Practice 30 days in a row",
        AchievementCategory.STREAK, "🏆", 30, 300
    ),
    
    # Accuracy achievements
    "accuracy_80": Achievement(
        "accuracy_80", "Sharp Eye", "Maintain 80% accuracy",
        AchievementCategory.ACCURACY, "🎯", 80, 50
    ),
    "accuracy_95": Achievement(
        "accuracy_95", "Perfect Form", "Maintain 95% accuracy",
        AchievementCategory.ACCURACY, "💎", 95, 150
    ),
    
    # Special achievements
    "speed_demon": Achievement(
        "speed_demon", "Speed Demon", "Sign 10 letters in under 30 seconds",
        AchievementCategory.SPECIAL, "⚡", 1, 50
    ),
    "night_owl": Achievement(
        "night_owl", "Night Owl", "Practice after midnight",
        AchievementCategory.SPECIAL, "🦉", 1, 20
    ),
    "early_bird": Achievement(
        "early_bird", "Early Bird", "Practice before 6 AM",
        AchievementCategory.SPECIAL, "🐦", 1, 20
    ),
}


class AnalyticsManager:
    """Manages usage analytics and learning progress.
    
    Features:
    - Track sign usage statistics
    - Calculate learning progress
    - Manage achievements and badges
    - Provide insights and recommendations
    """
    
    ANALYTICS_DIR = os.path.join(BASE_DIR, "analytics")
    
    def __init__(self):
        os.makedirs(self.ANALYTICS_DIR, exist_ok=True)
        self._user_stats: Dict[str, UserStats] = {}
        self._session_start: Optional[datetime] = None
    
    def get_user_stats(self, user_id: str) -> UserStats:
        """Get or load user statistics."""
        if user_id not in self._user_stats:
            filepath = os.path.join(self.ANALYTICS_DIR, f"{user_id}_stats.json")
            if os.path.exists(filepath):
                self._user_stats[user_id] = self._load_stats(filepath)
            else:
                self._user_stats[user_id] = UserStats(user_id=user_id)
        return self._user_stats[user_id]
    
    def _load_stats(self, filepath: str) -> UserStats:
        """Load stats from file."""
        import dataclasses
        # Derive user_id from filename so errors still return a usable object
        base = os.path.splitext(os.path.basename(filepath))[0]
        file_user_id = base[:-len('_stats')] if base.endswith('_stats') else base
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            # Filter to known fields so schema changes never cause a TypeError
            known = {f.name for f in dataclasses.fields(UserStats)}
            filtered = {k: v for k, v in data.items() if k in known}
            return UserStats(**filtered)
        except Exception as e:
            print(f"Error loading stats: {e}")
            return UserStats(user_id=file_user_id)
    
    def save_stats(self, user_id: str):
        """Save user stats to file."""
        if user_id not in self._user_stats:
            return
        
        stats = self._user_stats[user_id]
        filepath = os.path.join(self.ANALYTICS_DIR, f"{user_id}_stats.json")
        
        data = {
            'user_id': stats.user_id,
            'total_translations': stats.total_translations,
            'total_signs_detected': stats.total_signs_detected,
            'total_words_formed': stats.total_words_formed,
            'total_sentences': stats.total_sentences,
            'total_sessions': stats.total_sessions,
            'total_practice_time': stats.total_practice_time,
            'sign_counts': stats.sign_counts,
            'correct_predictions': stats.correct_predictions,
            'total_predictions': stats.total_predictions,
            'current_streak': stats.current_streak,
            'longest_streak': stats.longest_streak,
            'last_active_date': stats.last_active_date,
            'signs_learned': stats.signs_learned,
            'signs_mastered': stats.signs_mastered,
            'unlocked_achievements': stats.unlocked_achievements,
            'achievement_dates': stats.achievement_dates,
            'total_points': stats.total_points,
            'session_dates': stats.session_dates,
            'review_schedule': stats.review_schedule,
            'quiz_history': stats.quiz_history,
            'quiz_topic_performance': stats.quiz_topic_performance,
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def start_session(self, user_id: str):
        """Start a new practice session."""
        self._session_start = datetime.now()
        stats = self.get_user_stats(user_id)
        stats.total_sessions += 1
        
        # Update streak
        today = datetime.now().strftime("%Y-%m-%d")
        if stats.last_active_date:
            last_date = datetime.strptime(stats.last_active_date, "%Y-%m-%d")
            days_diff = (datetime.now() - last_date).days
            
            if days_diff == 1:
                stats.current_streak += 1
            elif days_diff > 1:
                stats.current_streak = 1
            # Same day - no change to streak
        else:
            stats.current_streak = 1
        
        stats.longest_streak = max(stats.longest_streak, stats.current_streak)
        stats.last_active_date = today
        
        if today not in stats.session_dates:
            stats.session_dates.append(today)
        
        # Check time-based achievements
        # early_bird: 4 AM – 6 AM  |  night_owl: midnight – 4 AM  (no overlap)
        hour = datetime.now().hour
        if 4 <= hour < 6:
            self._check_achievement(user_id, "early_bird", 1)
        elif hour < 4:   # 0, 1, 2, 3
            self._check_achievement(user_id, "night_owl", 1)
        
        self._check_streak_achievements(user_id)
    
    def end_session(self, user_id: str):
        """End the current session."""
        if self._session_start:
            duration = (datetime.now() - self._session_start).total_seconds() / 60
            stats = self.get_user_stats(user_id)
            stats.total_practice_time += duration
            self._session_start = None
            self.save_stats(user_id)
    
    def record_sign(self, user_id: str, sign: str, confidence: float = 0.0,
                    was_correct: bool = True):
        """Record a detected sign."""
        stats = self.get_user_stats(user_id)
        
        stats.total_signs_detected += 1
        stats.sign_counts[sign] = stats.sign_counts.get(sign, 0) + 1
        
        if was_correct:
            stats.correct_predictions += 1
        stats.total_predictions += 1
        
        # Track learned signs
        if sign not in stats.signs_learned:
            stats.signs_learned.append(sign)
        
        # Check achievements
        self._check_achievement(user_id, "first_sign", 1)
        self._check_achievement(user_id, "practice_10", stats.total_signs_detected)
        self._check_achievement(user_id, "practice_50", stats.total_signs_detected)
        self._check_achievement(user_id, "practice_100", stats.total_signs_detected)
        self._check_achievement(user_id, "practice_500", stats.total_signs_detected)
        self._check_achievement(user_id, "practice_1000", stats.total_signs_detected)
        
        # Check alphabet completion
        letters_learned = len([s for s in stats.signs_learned if len(s) == 1 and s.isalpha()])
        self._check_achievement(user_id, "alphabet_complete", letters_learned)
        
        # Check accuracy achievements
        if stats.total_predictions > 10:
            accuracy = (stats.correct_predictions / stats.total_predictions) * 100
            self._check_achievement(user_id, "accuracy_80", int(accuracy))
            self._check_achievement(user_id, "accuracy_95", int(accuracy))
    
    def record_word(self, user_id: str, word: str):
        """Record a formed word."""
        stats = self.get_user_stats(user_id)
        stats.total_words_formed += 1
        
        self._check_achievement(user_id, "words_10", stats.total_words_formed)
        self._check_achievement(user_id, "words_50", stats.total_words_formed)
    
    def record_sentence(self, user_id: str, sentence: str):
        """Record a completed sentence."""
        stats = self.get_user_stats(user_id)
        stats.total_sentences += 1
        stats.total_translations += 1
        
        self._check_achievement(user_id, "first_sentence", 1)
    
    def _check_achievement(self, user_id: str, achievement_id: str, value: int):
        """Check and unlock achievement if requirements met."""
        stats = self.get_user_stats(user_id)
        
        if achievement_id in stats.unlocked_achievements:
            return  # Already unlocked
        
        achievement = ACHIEVEMENTS.get(achievement_id)
        if not achievement:
            return
        
        if value >= achievement.requirement:
            stats.unlocked_achievements.append(achievement_id)
            stats.achievement_dates[achievement_id] = datetime.now().isoformat()
            stats.total_points += achievement.points
            print(f"🏆 Achievement Unlocked: {achievement.name}")
    
    def _check_streak_achievements(self, user_id: str):
        """Check streak-based achievements."""
        stats = self.get_user_stats(user_id)
        self._check_achievement(user_id, "streak_3", stats.current_streak)
        self._check_achievement(user_id, "streak_7", stats.current_streak)
        self._check_achievement(user_id, "streak_30", stats.current_streak)
    
    def get_most_used_signs(self, user_id: str, n: int = 10) -> List[tuple]:
        """Get the most frequently used signs."""
        stats = self.get_user_stats(user_id)
        return Counter(stats.sign_counts).most_common(n)
    
    def get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning progress."""
        stats = self.get_user_stats(user_id)
        
        total_letters = 26
        letters_learned = len([s for s in stats.signs_learned if len(s) == 1 and s.isalpha()])
        
        accuracy = 0
        if stats.total_predictions > 0:
            accuracy = (stats.correct_predictions / stats.total_predictions) * 100
        
        return {
            'signs_learned': len(stats.signs_learned),
            'letters_learned': letters_learned,
            'letters_progress': (letters_learned / total_letters) * 100,
            'total_practice_time': stats.total_practice_time,
            'accuracy': accuracy,
            'current_streak': stats.current_streak,
            'longest_streak': stats.longest_streak,
            'total_signs_detected': stats.total_signs_detected,
            'total_words': stats.total_words_formed,
            'total_sentences': stats.total_sentences,
            'achievements_unlocked': len(stats.unlocked_achievements),
            'total_achievements': len(ACHIEVEMENTS),
            'total_points': stats.total_points,
        }
    
    def get_achievements(self, user_id: str) -> Dict[str, Any]:
        """Get all achievements with unlock status."""
        stats = self.get_user_stats(user_id)
        
        achievements = []
        for aid, achievement in ACHIEVEMENTS.items():
            achievements.append({
                'id': aid,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'category': achievement.category.value,
                'points': achievement.points,
                'unlocked': aid in stats.unlocked_achievements,
                'unlocked_date': stats.achievement_dates.get(aid)
            })
        
        return {
            'achievements': achievements,
            'unlocked_count': len(stats.unlocked_achievements),
            'total_count': len(ACHIEVEMENTS),
            'total_points': stats.total_points
        }
    
    def get_recommendations(self, user_id: str) -> List[str]:
        """Get personalized learning recommendations."""
        stats = self.get_user_stats(user_id)
        recommendations = []

        scheduler = PracticeScheduler(stats.review_schedule)
        schedule_summary = scheduler.summary(stats.sign_counts.keys())
        if schedule_summary['due_items'] > 0:
            recommendations.append(
                f"You have {schedule_summary['due_items']} review sign(s) due now."
            )
        
        # Check which letters haven't been practiced
        all_letters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        practiced = set(s for s in stats.sign_counts.keys() if len(s) == 1 and s.isalpha())
        unpracticed = all_letters - practiced
        
        if unpracticed:
            letters = ', '.join(sorted(list(unpracticed)[:5]))
            recommendations.append(f"Try practicing these letters: {letters}")
        
        # Check for low-practice letters
        if stats.sign_counts:
            low_count = [s for s, c in stats.sign_counts.items() 
                        if c < 5 and len(s) == 1 and s.isalpha()]
            if low_count:
                recommendations.append(f"Keep practicing: {', '.join(low_count[:5])}")
        
        # Streak reminder
        if stats.current_streak > 0:
            recommendations.append(f"Keep your {stats.current_streak}-day streak going!")
        else:
            recommendations.append("Start a practice streak today!")
        
        # Next achievement hint
        next_achievements = [
            a for a in ACHIEVEMENTS.values() 
            if a.id not in stats.unlocked_achievements
        ]
        if next_achievements:
            closest = min(next_achievements, key=lambda a: a.requirement)
            recommendations.append(f"Next achievement: {closest.name} - {closest.description}")
        
        return recommendations

    def get_due_review_items(self, user_id: str, item_ids: List[str], limit: int = 12) -> List[str]:
        """Return prioritized due/new items for a review session."""
        stats = self.get_user_stats(user_id)
        scheduler = PracticeScheduler(stats.review_schedule)
        return scheduler.due_items(item_ids, limit=limit)

    def get_review_summary(self, user_id: str, item_ids: List[str]) -> Dict[str, int]:
        """Return review scheduling summary for UI labels."""
        stats = self.get_user_stats(user_id)
        scheduler = PracticeScheduler(stats.review_schedule)
        return scheduler.summary(item_ids)

    def record_review_result(self, user_id: str, item_id: str, correct: bool) -> Dict[str, Any]:
        """Update spaced-repetition state for one practiced item."""
        stats = self.get_user_stats(user_id)
        scheduler = PracticeScheduler(stats.review_schedule)
        result = scheduler.record_result(item_id, correct)
        stats.review_schedule = scheduler.export_state()
        return result

    def record_quiz_session(
        self,
        user_id: str,
        total_questions: int,
        correct_answers: int,
        score: int,
        verdict: str,
        topic_stats: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> Dict[str, Any]:
        """Record a completed quiz session and aggregate topic performance."""
        stats = self.get_user_stats(user_id)
        total_questions = max(0, int(total_questions))
        correct_answers = max(0, min(int(correct_answers), total_questions if total_questions else int(correct_answers)))
        accuracy = (correct_answers / total_questions * 100.0) if total_questions > 0 else 0.0

        entry = {
            'timestamp': datetime.now().isoformat(),
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'wrong_answers': max(0, total_questions - correct_answers),
            'score': int(score),
            'accuracy': round(accuracy, 2),
            'verdict': verdict,
        }
        stats.quiz_history.append(entry)
        stats.quiz_history = stats.quiz_history[-100:]

        if topic_stats:
            for topic, perf in topic_stats.items():
                attempts = int(perf.get('attempts', 0) or 0)
                correct = int(perf.get('correct', 0) or 0)
                if attempts <= 0:
                    continue
                topic_key = str(topic)
                agg = stats.quiz_topic_performance.setdefault(topic_key, {'attempts': 0, 'correct': 0})
                agg['attempts'] = int(agg.get('attempts', 0)) + attempts
                agg['correct'] = int(agg.get('correct', 0)) + max(0, min(correct, attempts))

        return entry

    def get_quiz_insights(self, user_id: str, history_limit: int = 12) -> Dict[str, Any]:
        """Return quiz history and aggregate weakness insights."""
        stats = self.get_user_stats(user_id)
        history = list(stats.quiz_history or [])
        recent_history = history[-max(1, int(history_limit)):] if history else []

        total_sessions = len(history)
        avg_accuracy = 0.0
        best_accuracy = 0.0
        if history:
            accuracies = [float(item.get('accuracy', 0.0) or 0.0) for item in history]
            avg_accuracy = sum(accuracies) / len(accuracies)
            best_accuracy = max(accuracies)

        topic_rows = []
        for topic, perf in (stats.quiz_topic_performance or {}).items():
            attempts = int(perf.get('attempts', 0) or 0)
            correct = int(perf.get('correct', 0) or 0)
            if attempts <= 0:
                continue
            accuracy = (correct / attempts) * 100.0
            topic_rows.append({
                'topic': topic,
                'attempts': attempts,
                'correct': correct,
                'accuracy': round(accuracy, 2),
            })

        topic_rows.sort(key=lambda item: (item['accuracy'], item['attempts']))
        weak_topics = topic_rows[:3]

        latest_verdict = "-"
        if history:
            latest_verdict = str(history[-1].get('verdict', '-') or '-')

        return {
            'total_sessions': total_sessions,
            'average_accuracy': round(avg_accuracy, 2),
            'best_accuracy': round(best_accuracy, 2),
            'latest_verdict': latest_verdict,
            'weak_topics': weak_topics,
            'history': list(reversed(recent_history)),
        }


# Singleton instance
analytics = AnalyticsManager()
