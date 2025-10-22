from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Iterable

from ..deps import SettingsType, get_settings


@dataclass
class AttentionEvent:
    timestamp: datetime
    state: str


class AttentionTracker:
    def __init__(self, settings: SettingsType | None = None) -> None:
        self.settings = settings or get_settings()
        self.window = timedelta(seconds=self.settings.attention_window_seconds)
        self.events: Deque[AttentionEvent] = deque()

    def add_event(self, state: str, timestamp: datetime | None = None) -> None:
        ts = timestamp or datetime.utcnow()
        self.events.append(AttentionEvent(timestamp=ts, state=state))
        self._trim()

    def _trim(self) -> None:
        cutoff = datetime.utcnow() - self.window
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()

    def ratio(self, state: str) -> float:
        self._trim()
        if not self.events:
            return 0.0
        matches = sum(1 for event in self.events if event.state == state)
        return matches / len(self.events)

    def summary(self) -> dict[str, float]:
        self._trim()
        total = len(self.events)
        if total == 0:
            return {"focused_ratio": 0.0, "distracted_ratio": 0.0}
        focused = sum(1 for event in self.events if event.state == "focused") / total
        distracted = sum(1 for event in self.events if event.state == "distracted") / total
        return {"focused_ratio": focused, "distracted_ratio": distracted}


def summarize_events(events: Iterable[AttentionEvent]) -> dict[str, float]:
    tracker = AttentionTracker()
    for event in events:
        tracker.add_event(event.state, event.timestamp)
    return tracker.summary()
