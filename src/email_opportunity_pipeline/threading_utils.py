"""Utilities for grouping email messages into conversation threads."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class ThreadSummary:
    """Lightweight computed view of a conversation thread for list display."""

    thread_id: str = ""
    subject: str = ""
    participants: List[str] = field(default_factory=list)
    message_count: int = 0
    latest_date: str = ""
    latest_date_ms: int = 0
    earliest_snippet: str = ""
    labels: List[str] = field(default_factory=list)
    has_attachments: bool = False
    message_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "subject": self.subject,
            "participants": list(self.participants),
            "message_count": self.message_count,
            "latest_date": self.latest_date,
            "latest_date_ms": self.latest_date_ms,
            "earliest_snippet": self.earliest_snippet,
            "labels": list(self.labels),
            "has_attachments": self.has_attachments,
            "message_ids": list(self.message_ids),
        }

    @classmethod
    def from_thread(cls, thread_id: str, messages: List[Dict[str, Any]]) -> "ThreadSummary":
        """Build a summary from a list of message dicts belonging to the same thread."""
        if not messages:
            return cls(thread_id=thread_id)

        # Collect unique participants (senders)
        participants: List[str] = []
        seen_participants: set = set()
        all_labels: set = set()
        has_attachments = False
        message_ids: List[str] = []

        for msg in messages:
            mid = msg.get("message_id", "")
            if mid:
                message_ids.append(mid)

            sender = (msg.get("headers") or {}).get("from", "")
            if sender and sender not in seen_participants:
                participants.append(sender)
                seen_participants.add(sender)

            for label in msg.get("labels", []):
                all_labels.add(label)

            if msg.get("attachments"):
                has_attachments = True

        # Earliest message (first in sorted order) provides subject
        earliest = messages[0]
        subject = (earliest.get("headers") or {}).get("subject", "(no subject)")
        earliest_snippet = earliest.get("snippet", "")

        # Latest message provides date
        latest = messages[-1]
        latest_date = (latest.get("headers") or {}).get("date", "")
        latest_date_ms = latest.get("internal_date_ms") or 0

        return cls(
            thread_id=thread_id,
            subject=subject,
            participants=participants,
            message_count=len(messages),
            latest_date=latest_date,
            latest_date_ms=latest_date_ms,
            earliest_snippet=earliest_snippet,
            labels=sorted(all_labels),
            has_attachments=has_attachments,
            message_ids=message_ids,
        )


def group_messages_by_thread(
    messages: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group a flat list of message dicts by ``thread_id``.

    Messages within each thread are sorted by ``internal_date_ms`` ascending
    (oldest first, like a conversation).

    Messages with an empty or missing ``thread_id`` are each placed in their
    own singleton group keyed by ``message_id``.

    Duplicate messages (same ``message_id``) within a thread are deduplicated.
    """
    threads: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    seen_ids: Dict[str, set] = defaultdict(set)

    for msg in messages:
        tid = msg.get("thread_id", "") or msg.get("message_id", "unknown")
        mid = msg.get("message_id", "")

        # Deduplicate within thread
        if mid and mid in seen_ids[tid]:
            continue
        if mid:
            seen_ids[tid].add(mid)

        threads[tid].append(msg)

    # Sort messages within each thread by date (oldest first)
    for tid in threads:
        threads[tid].sort(key=lambda m: m.get("internal_date_ms") or 0)

    return dict(threads)


def sort_threads_by_latest(
    threads: Dict[str, List[Dict[str, Any]]],
    *,
    reverse: bool = True,
) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """Return threads sorted by their latest message date (newest first by default)."""

    def _latest_date_ms(msgs: List[Dict[str, Any]]) -> int:
        return max((m.get("internal_date_ms") or 0) for m in msgs) if msgs else 0

    return sorted(threads.items(), key=lambda kv: _latest_date_ms(kv[1]), reverse=reverse)


def build_thread_summaries(
    threads: Dict[str, List[Dict[str, Any]]],
) -> List[ThreadSummary]:
    """Build lightweight summaries for all threads, sorted newest first."""
    summaries = [ThreadSummary.from_thread(tid, msgs) for tid, msgs in threads.items()]
    summaries.sort(key=lambda s: s.latest_date_ms, reverse=True)
    return summaries
