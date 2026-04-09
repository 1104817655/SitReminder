from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any

from .config import CONFIG_DIR


STATS_PATH = CONFIG_DIR / "stats.json"


@dataclass
class DailyStats:
    day: str
    reminder_count: int = 0
    rest_count: int = 0
    snooze_count: int = 0
    skip_count: int = 0
    deferred_count: int = 0
    idle_reset_count: int = 0

    @classmethod
    def from_dict(cls, day: str, raw: dict[str, Any]) -> "DailyStats":
        return cls(
            day=day,
            reminder_count=_to_non_negative_int(raw.get("reminder_count", 0)),
            rest_count=_to_non_negative_int(raw.get("rest_count", 0)),
            snooze_count=_to_non_negative_int(raw.get("snooze_count", 0)),
            skip_count=_to_non_negative_int(raw.get("skip_count", 0)),
            deferred_count=_to_non_negative_int(raw.get("deferred_count", 0)),
            idle_reset_count=_to_non_negative_int(raw.get("idle_reset_count", 0)),
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "reminder_count": self.reminder_count,
            "rest_count": self.rest_count,
            "snooze_count": self.snooze_count,
            "skip_count": self.skip_count,
            "deferred_count": self.deferred_count,
            "idle_reset_count": self.idle_reset_count,
        }


class StatsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or STATS_PATH
        self._days: dict[str, DailyStats] = {}
        self._load()

    def increment(self, field: str, amount: int = 1, on_date: date | None = None) -> None:
        if amount <= 0:
            return
        if field not in {
            "reminder_count",
            "rest_count",
            "snooze_count",
            "skip_count",
            "deferred_count",
            "idle_reset_count",
        }:
            return

        key = (on_date or date.today()).isoformat()
        stats = self._days.get(key)
        if stats is None:
            stats = DailyStats(day=key)
            self._days[key] = stats

        current = getattr(stats, field)
        setattr(stats, field, current + amount)
        self._save()

    def get_daily(self, on_date: date | None = None) -> DailyStats:
        key = (on_date or date.today()).isoformat()
        return self._days.get(key, DailyStats(day=key))

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        raw_days = raw.get("days", {})
        if not isinstance(raw_days, dict):
            return

        for day, payload in raw_days.items():
            if not isinstance(day, str) or not isinstance(payload, dict):
                continue
            self._days[day] = DailyStats.from_dict(day, payload)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "days": {day: stats.to_dict() for day, stats in self._days.items()},
        }
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


def _to_non_negative_int(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return n if n >= 0 else 0
