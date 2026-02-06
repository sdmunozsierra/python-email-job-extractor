"""
Tests for email recipient override and CC/BCC audit features.

Covers:
- EmailDraft model: cc, bcc, original_to fields + serialisation round-trip
- _apply_overrides helper: recipient override logic
- _build_mime_message: CC/BCC headers in MIME output
- GmailSender.send / send_batch: override_to, cc, bcc plumbing
- Report rendering: display of CC/BCC and original_to
"""
from __future__ import annotations

import email
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

from email_opportunity_pipeline.reply.models import (
    EmailDraft,
    ReplyResult,
    ReplyStatus,
)
from email_opportunity_pipeline.reply.sender import (
    GmailSender,
    _apply_overrides,
    _build_mime_message,
)
from email_opportunity_pipeline.reply.report import (
    render_batch_preview,
    render_draft_preview,
    render_send_report,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_draft(
    to: str = "recruiter@acme.com",
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    original_to: Optional[str] = None,
) -> EmailDraft:
    """Create a minimal EmailDraft for testing."""
    return EmailDraft(
        to=to,
        subject="Re: Senior Engineer at Acme",
        body_text="Thanks for reaching out!",
        cc=cc or [],
        bcc=bcc or [],
        original_to=original_to,
        job_id="msg123",
        job_title="Senior Engineer",
        company="Acme Corp",
        match_score=85.0,
        match_grade="excellent",
        recruiter_name="Jane Recruiter",
    )


# ===========================================================================
# EmailDraft model tests
# ===========================================================================

class TestEmailDraftCcBccFields:
    """Test that cc, bcc, and original_to are properly stored and serialised."""

    def test_defaults_are_empty(self):
        draft = EmailDraft(to="x@y.com", subject="Hi", body_text="Hello")
        assert draft.cc == []
        assert draft.bcc == []
        assert draft.original_to is None

    def test_fields_populated(self):
        draft = _make_draft(
            cc=["manager@acme.com"],
            bcc=["audit@acme.com", "compliance@acme.com"],
            original_to="original@acme.com",
        )
        assert draft.cc == ["manager@acme.com"]
        assert draft.bcc == ["audit@acme.com", "compliance@acme.com"]
        assert draft.original_to == "original@acme.com"

    def test_to_dict_includes_new_fields(self):
        draft = _make_draft(
            cc=["a@b.com"],
            bcc=["c@d.com"],
            original_to="orig@b.com",
        )
        d = draft.to_dict()
        assert d["cc"] == ["a@b.com"]
        assert d["bcc"] == ["c@d.com"]
        assert d["original_to"] == "orig@b.com"

    def test_to_dict_empty_new_fields(self):
        draft = _make_draft()
        d = draft.to_dict()
        assert d["cc"] == []
        assert d["bcc"] == []
        assert d["original_to"] is None

    def test_from_dict_round_trip(self):
        original = _make_draft(
            cc=["manager@acme.com", "lead@acme.com"],
            bcc=["audit@acme.com"],
            original_to="recruiter@original.com",
        )
        d = original.to_dict()
        restored = EmailDraft.from_dict(d)

        assert restored.to == original.to
        assert restored.cc == original.cc
        assert restored.bcc == original.bcc
        assert restored.original_to == original.original_to
        assert restored.subject == original.subject
        assert restored.body_text == original.body_text

    def test_from_dict_missing_new_fields_uses_defaults(self):
        """Backwards compatibility: old JSON without cc/bcc/original_to."""
        data = {
            "to": "x@y.com",
            "subject": "Hi",
            "body_text": "Hello",
        }
        draft = EmailDraft.from_dict(data)
        assert draft.cc == []
        assert draft.bcc == []
        assert draft.original_to is None


# ===========================================================================
# _apply_overrides tests
# ===========================================================================

class TestApplyOverrides:
    """Test the _apply_overrides helper function."""

    def test_no_overrides(self):
        draft = _make_draft(to="recruiter@acme.com")
        result = _apply_overrides(draft)
        assert result.to == "recruiter@acme.com"
        assert result.original_to is None
        assert result.cc == []
        assert result.bcc == []

    def test_override_to(self):
        draft = _make_draft(to="recruiter@acme.com")
        result = _apply_overrides(draft, override_to="test@mymail.com")
        assert result.to == "test@mymail.com"
        assert result.original_to == "recruiter@acme.com"

    def test_override_to_same_address_no_change(self):
        draft = _make_draft(to="recruiter@acme.com")
        result = _apply_overrides(draft, override_to="recruiter@acme.com")
        assert result.to == "recruiter@acme.com"
        assert result.original_to is None  # not changed

    def test_override_to_none(self):
        draft = _make_draft(to="recruiter@acme.com")
        result = _apply_overrides(draft, override_to=None)
        assert result.to == "recruiter@acme.com"
        assert result.original_to is None

    def test_add_cc(self):
        draft = _make_draft()
        result = _apply_overrides(draft, cc=["manager@acme.com"])
        assert result.cc == ["manager@acme.com"]

    def test_add_bcc(self):
        draft = _make_draft()
        result = _apply_overrides(draft, bcc=["audit@acme.com"])
        assert result.bcc == ["audit@acme.com"]

    def test_merge_cc_deduplicates(self):
        draft = _make_draft(cc=["existing@acme.com"])
        result = _apply_overrides(
            draft,
            cc=["existing@acme.com", "new@acme.com"],
        )
        assert result.cc == ["existing@acme.com", "new@acme.com"]

    def test_merge_bcc_deduplicates(self):
        draft = _make_draft(bcc=["existing@acme.com"])
        result = _apply_overrides(
            draft,
            bcc=["existing@acme.com", "new@acme.com"],
        )
        assert result.bcc == ["existing@acme.com", "new@acme.com"]

    def test_all_overrides_combined(self):
        draft = _make_draft(to="recruiter@acme.com")
        result = _apply_overrides(
            draft,
            override_to="test@mymail.com",
            cc=["manager@acme.com"],
            bcc=["audit@acme.com", "compliance@acme.com"],
        )
        assert result.to == "test@mymail.com"
        assert result.original_to == "recruiter@acme.com"
        assert result.cc == ["manager@acme.com"]
        assert result.bcc == ["audit@acme.com", "compliance@acme.com"]


# ===========================================================================
# _build_mime_message tests
# ===========================================================================

class TestBuildMimeMessage:
    """Test MIME message construction with CC/BCC headers."""

    def test_no_cc_bcc(self):
        draft = _make_draft()
        msg = _build_mime_message(draft, "me@gmail.com")
        assert msg["To"] == "recruiter@acme.com"
        assert msg["Cc"] is None
        assert msg["Bcc"] is None

    def test_cc_header(self):
        draft = _make_draft(cc=["manager@acme.com", "lead@acme.com"])
        msg = _build_mime_message(draft, "me@gmail.com")
        assert msg["Cc"] == "manager@acme.com, lead@acme.com"

    def test_bcc_header(self):
        draft = _make_draft(bcc=["audit@acme.com"])
        msg = _build_mime_message(draft, "me@gmail.com")
        assert msg["Bcc"] == "audit@acme.com"

    def test_cc_and_bcc_together(self):
        draft = _make_draft(
            cc=["manager@acme.com"],
            bcc=["audit@acme.com", "compliance@acme.com"],
        )
        msg = _build_mime_message(draft, "me@gmail.com")
        assert msg["Cc"] == "manager@acme.com"
        assert msg["Bcc"] == "audit@acme.com, compliance@acme.com"

    def test_overridden_to_in_mime(self):
        """When to is overridden, the MIME To: header should show the new address."""
        draft = _make_draft(
            to="test@mymail.com",
            original_to="recruiter@acme.com",
        )
        msg = _build_mime_message(draft, "me@gmail.com")
        assert msg["To"] == "test@mymail.com"

    def test_mime_message_is_valid(self):
        """Full MIME message with all features should parse correctly."""
        draft = _make_draft(
            cc=["cc1@example.com", "cc2@example.com"],
            bcc=["bcc@example.com"],
        )
        msg = _build_mime_message(draft, "sender@gmail.com")

        # Convert to bytes and parse back
        raw = msg.as_bytes()
        parsed = email.message_from_bytes(raw)

        assert parsed["To"] == "recruiter@acme.com"
        assert parsed["From"] == "sender@gmail.com"
        assert "cc1@example.com" in parsed["Cc"]
        assert "cc2@example.com" in parsed["Cc"]
        assert parsed["Bcc"] == "bcc@example.com"
        assert parsed["Subject"] == "Re: Senior Engineer at Acme"


# ===========================================================================
# GmailSender.send / send_batch tests
# ===========================================================================

class TestGmailSenderOverrides:
    """Test that GmailSender passes overrides through correctly."""

    def test_send_dry_run_with_override_to(self):
        sender = GmailSender()
        draft = _make_draft(to="recruiter@acme.com")

        result = sender.send(
            draft,
            dry_run=True,
            override_to="test@mymail.com",
        )

        assert result.status == ReplyStatus.DRY_RUN
        assert result.draft.to == "test@mymail.com"
        assert result.draft.original_to == "recruiter@acme.com"

    def test_send_dry_run_with_cc_bcc(self):
        sender = GmailSender()
        draft = _make_draft()

        result = sender.send(
            draft,
            dry_run=True,
            cc=["cc@acme.com"],
            bcc=["bcc@acme.com"],
        )

        assert result.status == ReplyStatus.DRY_RUN
        assert result.draft.cc == ["cc@acme.com"]
        assert result.draft.bcc == ["bcc@acme.com"]

    def test_send_dry_run_all_overrides(self):
        sender = GmailSender()
        draft = _make_draft(to="recruiter@acme.com")

        result = sender.send(
            draft,
            dry_run=True,
            override_to="test@mymail.com",
            cc=["manager@acme.com"],
            bcc=["audit@acme.com"],
        )

        assert result.status == ReplyStatus.DRY_RUN
        assert result.draft.to == "test@mymail.com"
        assert result.draft.original_to == "recruiter@acme.com"
        assert result.draft.cc == ["manager@acme.com"]
        assert result.draft.bcc == ["audit@acme.com"]

    def test_send_batch_passes_overrides(self):
        sender = GmailSender()
        drafts = [
            _make_draft(to="recruiter1@acme.com"),
            _make_draft(to="recruiter2@bigco.com"),
        ]

        results = sender.send_batch(
            drafts,
            dry_run=True,
            override_to="test@mymail.com",
            cc=["manager@mymail.com"],
            bcc=["audit@mymail.com"],
        )

        assert len(results) == 2
        for result in results:
            assert result.status == ReplyStatus.DRY_RUN
            assert result.draft.to == "test@mymail.com"
            assert result.draft.cc == ["manager@mymail.com"]
            assert result.draft.bcc == ["audit@mymail.com"]

        # original_to should be different for each
        assert results[0].draft.original_to == "recruiter1@acme.com"
        assert results[1].draft.original_to == "recruiter2@bigco.com"

    def test_send_batch_no_overrides(self):
        sender = GmailSender()
        drafts = [_make_draft(to="recruiter@acme.com")]

        results = sender.send_batch(drafts, dry_run=True)

        assert len(results) == 1
        assert results[0].draft.to == "recruiter@acme.com"
        assert results[0].draft.original_to is None
        assert results[0].draft.cc == []
        assert results[0].draft.bcc == []


# ===========================================================================
# Report rendering tests
# ===========================================================================

class TestReportRendering:
    """Test that reports display CC/BCC/original_to correctly."""

    def test_draft_preview_no_overrides(self):
        draft = _make_draft()
        md = render_draft_preview(draft)
        assert "**To:** recruiter@acme.com" in md
        assert "Original To" not in md
        assert "**CC:**" not in md
        assert "**BCC:**" not in md

    def test_draft_preview_with_override(self):
        draft = _make_draft(
            to="test@mymail.com",
            original_to="recruiter@acme.com",
        )
        md = render_draft_preview(draft)
        assert "**To:** test@mymail.com" in md
        assert "**Original To:** recruiter@acme.com" in md
        assert "overridden" in md.lower()

    def test_draft_preview_with_cc_bcc(self):
        draft = _make_draft(
            cc=["manager@acme.com"],
            bcc=["audit@acme.com", "compliance@acme.com"],
        )
        md = render_draft_preview(draft)
        assert "**CC:** manager@acme.com" in md
        assert "**BCC:** audit@acme.com, compliance@acme.com" in md

    def test_batch_preview_shows_override_indicator(self):
        drafts = [
            _make_draft(to="test@mymail.com", original_to="recruiter@acme.com"),
        ]
        md = render_batch_preview(drafts)
        assert "Recipient Override Active" in md
        assert "was" in md  # table shows original

    def test_batch_preview_no_override(self):
        drafts = [_make_draft()]
        md = render_batch_preview(drafts)
        assert "Recipient Override Active" not in md

    def test_batch_preview_individual_sections_show_cc_bcc(self):
        drafts = [
            _make_draft(
                cc=["cc@example.com"],
                bcc=["bcc@example.com"],
            ),
        ]
        md = render_batch_preview(drafts)
        assert "**CC:** cc@example.com" in md
        assert "**BCC:** bcc@example.com" in md

    def test_send_report_shows_override_and_cc_bcc(self):
        draft = _make_draft(
            to="test@mymail.com",
            original_to="recruiter@acme.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        result = ReplyResult(draft=draft, status=ReplyStatus.DRY_RUN)
        md = render_send_report([result])
        assert "**To:** test@mymail.com" in md
        assert "**Original To:** recruiter@acme.com" in md
        assert "**CC:** cc@example.com" in md
        assert "**BCC:** bcc@example.com" in md


# ===========================================================================
# Serialisation round-trip through IO layer
# ===========================================================================

class TestIODraftRoundTrip:
    """Test that drafts with cc/bcc/original_to survive write/read."""

    def test_write_read_drafts_preserves_new_fields(self, tmp_path):
        from email_opportunity_pipeline.io import write_drafts, read_drafts

        original = _make_draft(
            to="test@mymail.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            original_to="recruiter@acme.com",
        )

        path = tmp_path / "drafts.json"
        write_drafts(path, [original])
        restored_list = read_drafts(path)

        assert len(restored_list) == 1
        restored = restored_list[0]
        assert restored.to == "test@mymail.com"
        assert restored.cc == ["cc@example.com"]
        assert restored.bcc == ["bcc@example.com"]
        assert restored.original_to == "recruiter@acme.com"

    def test_write_read_reply_results_preserves_new_fields(self, tmp_path):
        from email_opportunity_pipeline.io import write_reply_results, read_reply_results

        draft = _make_draft(
            to="test@mymail.com",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            original_to="recruiter@acme.com",
        )
        result = ReplyResult(draft=draft, status=ReplyStatus.DRY_RUN)

        path = tmp_path / "reply_results.json"
        write_reply_results(path, [result])
        restored_list = read_reply_results(path)

        assert len(restored_list) == 1
        r = restored_list[0]
        assert r.draft.to == "test@mymail.com"
        assert r.draft.cc == ["cc@example.com"]
        assert r.draft.bcc == ["bcc@example.com"]
        assert r.draft.original_to == "recruiter@acme.com"
