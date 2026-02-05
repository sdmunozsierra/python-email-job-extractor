from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


def _parse_window_value(window: str) -> timedelta:
    match = re.fullmatch(r"(?P<value>\d+)(?P<unit>[mhd])", window.strip().lower())
    if not match:
        raise ValueError("window must look like 30m, 6h, or 2d")

    value = int(match.group("value"))
    unit = match.group("unit")
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    return timedelta(days=value)


def parse_window(window: str, now: Optional[datetime] = None) -> TimeWindow:
    now = now or datetime.now(tz=timezone.utc)
    delta = _parse_window_value(window)
    return TimeWindow(start=now - delta, end=now)


def to_gmail_query(window: TimeWindow) -> str:
    duration = window.duration
    total_minutes = int(duration.total_seconds() // 60)
    if total_minutes < 60:
        return f"newer_than:{total_minutes}m"
    total_hours = total_minutes // 60
    if total_hours < 24 and total_minutes % 60 == 0:
        return f"newer_than:{total_hours}h"
    total_days = max(1, total_hours // 24)
    return f"newer_than:{total_days}d"
