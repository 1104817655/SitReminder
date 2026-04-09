from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from typing import Any

APP_NAME = "SitReminder"


def _default_config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


CONFIG_DIR = _default_config_dir()
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    enabled: bool = True
    autostart: bool = False
    enable_sound: bool = True

    reminder_mode: str = "smart"

    reminder_interval_minutes: int = 60
    pre_reminder_minutes: int = 2
    pre_reminder_use_popup: bool = False
    pre_reminder_popup_seconds: int = 10
    rest_duration_minutes: int = 3
    cycle_work_minutes: int = 60
    cycle_rest_minutes: int = 5

    snooze_options_minutes: list[int] = field(default_factory=lambda: [5, 10, 15])
    default_snooze_minutes: int = 10
    max_consecutive_snoozes: int = 3

    idle_reset_minutes: int = 5

    work_start: str = "09:00"
    work_end: str = "18:00"
    lunch_start: str = "12:00"
    lunch_end: str = "13:30"

    meeting_process_keywords: list[str] = field(
        default_factory=lambda: ["teams", "zoom", "webex", "lark", "dingtalk", "腾讯会议"]
    )

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_PATH.exists():
            return cls()

        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError):
            return cls()

        cfg = cls()
        cfg._apply_dict(raw)
        cfg._normalize()
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "autostart": self.autostart,
            "enable_sound": self.enable_sound,
            "reminder_mode": self.reminder_mode,
            "reminder_interval_minutes": self.reminder_interval_minutes,
            "pre_reminder_minutes": self.pre_reminder_minutes,
            "pre_reminder_use_popup": self.pre_reminder_use_popup,
            "pre_reminder_popup_seconds": self.pre_reminder_popup_seconds,
            "rest_duration_minutes": self.rest_duration_minutes,
            "cycle_work_minutes": self.cycle_work_minutes,
            "cycle_rest_minutes": self.cycle_rest_minutes,
            "snooze_options_minutes": self.snooze_options_minutes,
            "default_snooze_minutes": self.default_snooze_minutes,
            "max_consecutive_snoozes": self.max_consecutive_snoozes,
            "idle_reset_minutes": self.idle_reset_minutes,
            "work_start": self.work_start,
            "work_end": self.work_end,
            "lunch_start": self.lunch_start,
            "lunch_end": self.lunch_end,
            "meeting_process_keywords": self.meeting_process_keywords,
        }

    def _apply_dict(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _normalize(self) -> None:
        if self.reminder_mode not in {"smart", "cycle"}:
            self.reminder_mode = "smart"

        self.reminder_interval_minutes = _clamp_int(self.reminder_interval_minutes, 15, 240)
        self.pre_reminder_minutes = _clamp_int(self.pre_reminder_minutes, 0, 30)
        self.pre_reminder_popup_seconds = _clamp_int(self.pre_reminder_popup_seconds, 3, 60)
        self.rest_duration_minutes = _clamp_int(self.rest_duration_minutes, 1, 60)
        self.cycle_work_minutes = _clamp_int(self.cycle_work_minutes, 15, 240)
        self.cycle_rest_minutes = _clamp_int(self.cycle_rest_minutes, 1, 60)

        if not isinstance(self.snooze_options_minutes, list):
            self.snooze_options_minutes = [5, 10, 15]
        self.snooze_options_minutes = sorted(
            {max(1, min(240, int(v))) for v in self.snooze_options_minutes if _is_int_like(v)}
        )
        if not self.snooze_options_minutes:
            self.snooze_options_minutes = [5, 10, 15]

        self.default_snooze_minutes = _clamp_int(self.default_snooze_minutes, 1, 240)
        if self.default_snooze_minutes not in self.snooze_options_minutes:
            self.default_snooze_minutes = self.snooze_options_minutes[0]

        self.max_consecutive_snoozes = _clamp_int(self.max_consecutive_snoozes, 1, 20)
        self.idle_reset_minutes = _clamp_int(self.idle_reset_minutes, 1, 180)

        self.work_start = _normalize_hhmm(self.work_start, "09:00")
        self.work_end = _normalize_hhmm(self.work_end, "18:00")
        self.lunch_start = _normalize_hhmm(self.lunch_start, "12:00")
        self.lunch_end = _normalize_hhmm(self.lunch_end, "13:30")

        if not isinstance(self.meeting_process_keywords, list):
            self.meeting_process_keywords = ["teams", "zoom"]
        self.meeting_process_keywords = [str(v).strip().lower() for v in self.meeting_process_keywords if str(v).strip()]



def _clamp_int(value: Any, low: int, high: int) -> int:
    if not _is_int_like(value):
        return low
    return max(low, min(high, int(value)))



def _is_int_like(value: Any) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False



def _normalize_hhmm(value: str, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    parts = value.strip().split(":")
    if len(parts) != 2:
        return fallback
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return fallback
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return fallback
    return f"{hour:02d}:{minute:02d}"
