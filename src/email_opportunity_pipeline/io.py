from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .models import EmailMessage


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def write_messages(path: str | Path, messages: Iterable[EmailMessage]) -> None:
    data = [m.to_dict() for m in messages]
    payload = {
        "fetched_at_utc": _utc_now_iso(),
        "count": len(data),
        "messages": data,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_messages(path: str | Path) -> List[EmailMessage]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    messages = raw.get("messages", []) or []
    return [EmailMessage.from_dict(m) for m in messages]


def write_opportunities(path: str | Path, opportunities: List[Dict[str, Any]]) -> None:
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(opportunities),
        "opportunities": opportunities,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_opportunities(path: str | Path) -> List[Dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw.get("opportunities", []) or []
