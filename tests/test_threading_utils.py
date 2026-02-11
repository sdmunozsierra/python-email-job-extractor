"""Tests for email_opportunity_pipeline.threading_utils."""

from __future__ import annotations

from email_opportunity_pipeline.threading_utils import (
    ThreadSummary,
    build_thread_summaries,
    group_messages_by_thread,
    sort_threads_by_latest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_msg(
    *,
    message_id: str = "msg1",
    thread_id: str = "thread1",
    subject: str = "Hello",
    from_: str = "alice@example.com",
    date: str = "2024-01-01",
    internal_date_ms: int = 1704067200000,
    snippet: str = "preview text",
    labels: list | None = None,
    attachments: list | None = None,
    body_text: str = "",
    body_html: str = "",
) -> dict:
    return {
        "message_id": message_id,
        "thread_id": thread_id,
        "internal_date_ms": internal_date_ms,
        "headers": {
            "subject": subject,
            "from": from_,
            "to": "bob@example.com",
            "date": date,
        },
        "snippet": snippet,
        "body": {"text": body_text, "html": body_html},
        "labels": labels or [],
        "attachments": attachments or [],
    }


# ---------------------------------------------------------------------------
# group_messages_by_thread
# ---------------------------------------------------------------------------

class TestGroupMessagesByThread:
    def test_groups_by_thread_id(self):
        msgs = [
            _make_msg(message_id="m1", thread_id="t1"),
            _make_msg(message_id="m2", thread_id="t2"),
            _make_msg(message_id="m3", thread_id="t1"),
        ]
        threads = group_messages_by_thread(msgs)
        assert len(threads) == 2
        assert len(threads["t1"]) == 2
        assert len(threads["t2"]) == 1

    def test_sorts_within_thread_by_date(self):
        msgs = [
            _make_msg(message_id="m2", thread_id="t1", internal_date_ms=2000),
            _make_msg(message_id="m1", thread_id="t1", internal_date_ms=1000),
        ]
        threads = group_messages_by_thread(msgs)
        assert threads["t1"][0]["message_id"] == "m1"
        assert threads["t1"][1]["message_id"] == "m2"

    def test_empty_thread_id_uses_message_id(self):
        msgs = [
            _make_msg(message_id="m1", thread_id=""),
            _make_msg(message_id="m2", thread_id=""),
        ]
        threads = group_messages_by_thread(msgs)
        # Each gets its own group
        assert len(threads) == 2
        assert "m1" in threads
        assert "m2" in threads

    def test_deduplicates_within_thread(self):
        msgs = [
            _make_msg(message_id="m1", thread_id="t1"),
            _make_msg(message_id="m1", thread_id="t1"),  # duplicate
        ]
        threads = group_messages_by_thread(msgs)
        assert len(threads["t1"]) == 1

    def test_empty_input(self):
        threads = group_messages_by_thread([])
        assert threads == {}

    def test_missing_fields(self):
        msgs = [{"message_id": "m1"}]
        threads = group_messages_by_thread(msgs)
        assert len(threads) == 1
        assert "m1" in threads


# ---------------------------------------------------------------------------
# sort_threads_by_latest
# ---------------------------------------------------------------------------

class TestSortThreadsByLatest:
    def test_newest_first_by_default(self):
        threads = {
            "old": [_make_msg(thread_id="old", internal_date_ms=1000)],
            "new": [_make_msg(thread_id="new", internal_date_ms=9000)],
            "mid": [_make_msg(thread_id="mid", internal_date_ms=5000)],
        }
        sorted_t = sort_threads_by_latest(threads)
        assert [tid for tid, _ in sorted_t] == ["new", "mid", "old"]

    def test_oldest_first(self):
        threads = {
            "old": [_make_msg(thread_id="old", internal_date_ms=1000)],
            "new": [_make_msg(thread_id="new", internal_date_ms=9000)],
        }
        sorted_t = sort_threads_by_latest(threads, reverse=False)
        assert sorted_t[0][0] == "old"

    def test_uses_latest_message_in_thread(self):
        threads = {
            "t1": [
                _make_msg(message_id="m1", thread_id="t1", internal_date_ms=100),
                _make_msg(message_id="m2", thread_id="t1", internal_date_ms=9000),
            ],
            "t2": [
                _make_msg(message_id="m3", thread_id="t2", internal_date_ms=5000),
            ],
        }
        sorted_t = sort_threads_by_latest(threads)
        assert sorted_t[0][0] == "t1"  # Latest msg at 9000


# ---------------------------------------------------------------------------
# ThreadSummary
# ---------------------------------------------------------------------------

class TestThreadSummary:
    def test_from_thread_basic(self):
        msgs = [
            _make_msg(
                message_id="m1", thread_id="t1",
                subject="Job Offer", from_="alice@co.com",
                date="2024-01-01", internal_date_ms=1000,
                snippet="Hello world",
            ),
            _make_msg(
                message_id="m2", thread_id="t1",
                subject="Re: Job Offer", from_="bob@co.com",
                date="2024-01-02", internal_date_ms=2000,
            ),
        ]
        summary = ThreadSummary.from_thread("t1", msgs)
        assert summary.thread_id == "t1"
        assert summary.subject == "Job Offer"
        assert summary.message_count == 2
        assert len(summary.participants) == 2
        assert "alice@co.com" in summary.participants
        assert "bob@co.com" in summary.participants
        assert summary.latest_date == "2024-01-02"
        assert summary.latest_date_ms == 2000
        assert summary.earliest_snippet == "Hello world"
        assert summary.message_ids == ["m1", "m2"]

    def test_from_thread_empty(self):
        summary = ThreadSummary.from_thread("empty", [])
        assert summary.thread_id == "empty"
        assert summary.message_count == 0
        assert summary.participants == []

    def test_from_thread_deduplicates_participants(self):
        msgs = [
            _make_msg(message_id="m1", from_="alice@co.com"),
            _make_msg(message_id="m2", from_="alice@co.com"),
        ]
        summary = ThreadSummary.from_thread("t1", msgs)
        assert len(summary.participants) == 1

    def test_from_thread_collects_labels(self):
        msgs = [
            _make_msg(message_id="m1", labels=["INBOX", "UNREAD"]),
            _make_msg(message_id="m2", labels=["INBOX", "IMPORTANT"]),
        ]
        summary = ThreadSummary.from_thread("t1", msgs)
        assert set(summary.labels) == {"INBOX", "UNREAD", "IMPORTANT"}

    def test_from_thread_detects_attachments(self):
        msgs = [
            _make_msg(message_id="m1", attachments=[]),
            _make_msg(message_id="m2", attachments=[{"filename": "resume.pdf", "size": 1024}]),
        ]
        summary = ThreadSummary.from_thread("t1", msgs)
        assert summary.has_attachments is True

    def test_from_thread_no_attachments(self):
        msgs = [_make_msg(message_id="m1")]
        summary = ThreadSummary.from_thread("t1", msgs)
        assert summary.has_attachments is False

    def test_to_dict_roundtrip(self):
        msgs = [
            _make_msg(message_id="m1", thread_id="t1", labels=["INBOX"]),
        ]
        summary = ThreadSummary.from_thread("t1", msgs)
        d = summary.to_dict()
        assert d["thread_id"] == "t1"
        assert d["message_count"] == 1
        assert isinstance(d["participants"], list)
        assert isinstance(d["labels"], list)
        assert isinstance(d["message_ids"], list)


# ---------------------------------------------------------------------------
# build_thread_summaries
# ---------------------------------------------------------------------------

class TestBuildThreadSummaries:
    def test_sorts_newest_first(self):
        threads = {
            "old": [_make_msg(message_id="m1", thread_id="old", internal_date_ms=1000)],
            "new": [_make_msg(message_id="m2", thread_id="new", internal_date_ms=9000)],
        }
        summaries = build_thread_summaries(threads)
        assert summaries[0].thread_id == "new"
        assert summaries[1].thread_id == "old"

    def test_empty_threads(self):
        summaries = build_thread_summaries({})
        assert summaries == []


# ---------------------------------------------------------------------------
# EmailHeaders in_reply_to / references fields
# ---------------------------------------------------------------------------

class TestEmailHeadersThreadingFields:
    def test_new_fields_default_empty(self):
        from email_opportunity_pipeline.models import EmailHeaders

        h = EmailHeaders()
        assert h.in_reply_to == ""
        assert h.references == ""

    def test_new_fields_to_dict(self):
        from email_opportunity_pipeline.models import EmailHeaders

        h = EmailHeaders(
            from_="a@b.com",
            in_reply_to="<abc@mail.com>",
            references="<abc@mail.com> <def@mail.com>",
        )
        d = h.to_dict()
        assert d["in_reply_to"] == "<abc@mail.com>"
        assert d["references"] == "<abc@mail.com> <def@mail.com>"

    def test_new_fields_from_dict(self):
        from email_opportunity_pipeline.models import EmailHeaders

        d = {
            "from": "sender@co.com",
            "in_reply_to": "<reply-id@co.com>",
            "references": "<ref1@co.com>",
        }
        h = EmailHeaders.from_dict(d)
        assert h.in_reply_to == "<reply-id@co.com>"
        assert h.references == "<ref1@co.com>"

    def test_missing_new_fields_default(self):
        from email_opportunity_pipeline.models import EmailHeaders

        # Simulates loading an old messages.json without the new fields
        d = {"from": "sender@co.com", "subject": "test"}
        h = EmailHeaders.from_dict(d)
        assert h.in_reply_to == ""
        assert h.references == ""
