"""
Spaced-repetition scheduler for sign practice.

This module keeps a lightweight per-item state and prioritizes:
- overdue items,
- historically weak items,
- and newly introduced items.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ReviewItemState:
    """Stored review state for one item."""

    ease: float = 2.3
    interval_days: int = 0
    repetitions: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    due_date: str = ""
    last_review_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ease": round(float(self.ease), 3),
            "interval_days": int(self.interval_days),
            "repetitions": int(self.repetitions),
            "correct_count": int(self.correct_count),
            "wrong_count": int(self.wrong_count),
            "due_date": self.due_date,
            "last_review_date": self.last_review_date,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewItemState":
        return cls(
            ease=float(data.get("ease", 2.3)),
            interval_days=int(data.get("interval_days", 0)),
            repetitions=int(data.get("repetitions", 0)),
            correct_count=int(data.get("correct_count", 0)),
            wrong_count=int(data.get("wrong_count", 0)),
            due_date=str(data.get("due_date", "") or ""),
            last_review_date=str(data.get("last_review_date", "") or ""),
        )


class PracticeScheduler:
    """Simple adaptive scheduler for sign-learning reviews."""

    def __init__(self, state: Optional[Dict[str, Dict[str, Any]]] = None):
        self._items: Dict[str, ReviewItemState] = {}
        raw_state = state or {}
        for item_id, item_state in raw_state.items():
            if isinstance(item_state, dict):
                self._items[item_id] = ReviewItemState.from_dict(item_state)

    @staticmethod
    def _today() -> date:
        return date.today()

    @staticmethod
    def _parse_date(value: str) -> Optional[date]:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except Exception:
            return None

    def export_state(self) -> Dict[str, Dict[str, Any]]:
        return {item_id: state.to_dict() for item_id, state in self._items.items()}

    def _ensure(self, item_id: str) -> ReviewItemState:
        state = self._items.get(item_id)
        if state is None:
            state = ReviewItemState(due_date=self._today().isoformat())
            self._items[item_id] = state
        return state

    def record_result(self, item_id: str, correct: bool) -> Dict[str, Any]:
        """Update one item using a lightweight SM-2 style rule set."""
        state = self._ensure(item_id)
        today = self._today()

        if correct:
            state.correct_count += 1
            state.repetitions += 1
            if state.repetitions == 1:
                state.interval_days = 1
            elif state.repetitions == 2:
                state.interval_days = 3
            else:
                state.interval_days = max(1, int(round(state.interval_days * state.ease)))
            state.ease = min(2.9, state.ease + 0.05)
            next_due = today + timedelta(days=state.interval_days)
        else:
            state.wrong_count += 1
            state.repetitions = 0
            state.interval_days = 0
            state.ease = max(1.3, state.ease - 0.2)
            next_due = today

        state.last_review_date = today.isoformat()
        state.due_date = next_due.isoformat()

        return {
            "item_id": item_id,
            "correct": correct,
            "due_date": state.due_date,
            "interval_days": state.interval_days,
            "ease": round(state.ease, 2),
        }

    def due_items(self, item_ids: Iterable[str], limit: int = 12) -> List[str]:
        """Return prioritized list of due/new items."""
        today = self._today()
        scored: List[tuple] = []

        for item_id in item_ids:
            state = self._items.get(item_id)
            if state is None:
                scored.append((0, 0, 0, item_id))
                continue

            due_date = self._parse_date(state.due_date) or today
            overdue_days = max((today - due_date).days, 0)
            attempts = state.correct_count + state.wrong_count
            miss_ratio = (state.wrong_count / attempts) if attempts > 0 else 0.0

            if overdue_days > 0 or due_date <= today:
                scored.append((2, overdue_days, miss_ratio, item_id))
            elif attempts < 2:
                scored.append((1, 0, miss_ratio, item_id))

        scored.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
        ordered = [item_id for *_rest, item_id in scored]
        return ordered[: max(1, int(limit))]

    def summary(self, item_ids: Iterable[str]) -> Dict[str, int]:
        """Basic summary counts for dashboard labels."""
        today = self._today()
        total = 0
        due = 0
        tracked = 0
        weak = 0

        for item_id in item_ids:
            total += 1
            state = self._items.get(item_id)
            if state is None:
                continue
            tracked += 1

            due_date = self._parse_date(state.due_date) or today
            if due_date <= today:
                due += 1

            attempts = state.correct_count + state.wrong_count
            if attempts >= 4 and state.wrong_count / attempts >= 0.4:
                weak += 1

        return {
            "total_items": total,
            "tracked_items": tracked,
            "due_items": due,
            "weak_items": weak,
        }
