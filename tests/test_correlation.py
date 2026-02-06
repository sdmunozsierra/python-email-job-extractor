"""
Tests for the job-opportunity correlation module.

Covers:
- Data models (serialization round-trip)
- OpportunityCorrelator (artifact linking, stage detection, filtering)
- Markdown report rendering
- I/O functions (write/read correlation)
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------

from email_opportunity_pipeline.correlation.models import (
    CorrelatedOpportunity,
    CorrelationSummary,
    EmailSummary,
    MatchSummary,
    OpportunityStage,
    ReplyOutcome,
    ReplySummary,
    TailoringSummary,
)
from email_opportunity_pipeline.correlation.correlator import (
    OpportunityCorrelator,
    _opp_job_id,
)
from email_opportunity_pipeline.correlation.report import (
    render_correlation_report,
    render_correlation_summary,
    render_opportunity_card,
)
from email_opportunity_pipeline.io import (
    write_correlation,
    read_correlation,
)
from email_opportunity_pipeline.models import (
    EmailHeaders,
    EmailMessage,
    Attachment,
    EmailSource,
)
from email_opportunity_pipeline.matching.models import (
    CategoryScore,
    ExperienceMatch,
    MatchInsights,
    MatchResult,
    SkillMatch,
)
from email_opportunity_pipeline.reply.models import (
    EmailDraft,
    ReplyResult,
    ReplyStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_email(msg_id: str, subject: str = "Test Job", from_: str = "recruiter@corp.com") -> EmailMessage:
    """Create a minimal EmailMessage for testing."""
    return EmailMessage(
        message_id=msg_id,
        thread_id=f"thread_{msg_id}",
        internal_date=datetime(2025, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
        headers=EmailHeaders(
            from_=from_,
            to="candidate@email.com",
            subject=subject,
            date="Sat, 01 Feb 2025 12:00:00 +0000",
            message_id=f"<{msg_id}@mail.corp.com>",
        ),
        snippet="This is a test job opportunity...",
        body_text="Full body of the email about a job opportunity.",
        body_html="<p>Full body</p>",
        labels=["INBOX", "UNREAD"],
        attachments=[
            Attachment(
                filename="job_description.pdf",
                mime_type="application/pdf",
                size=12345,
                attachment_id="att123",
            )
        ],
        source=EmailSource(provider="gmail", user_id="me"),
    )


def _make_opportunity(msg_id: str, title: str = "Senior Engineer", company: str = "Acme Corp") -> Dict[str, Any]:
    """Create a minimal opportunity dict for testing."""
    return {
        "job_title": title,
        "company": company,
        "recruiter_name": "Jane Recruiter",
        "recruiter_email": "jane@acme.com",
        "recruiter_phone": None,
        "recruiter_company": "Acme Corp",
        "social_links": [],
        "locations": ["San Francisco, CA"],
        "remote": True,
        "hybrid": False,
        "summary": "Exciting senior engineering role.",
        "hard_requirements": ["5+ years Python"],
        "mandatory_skills": ["Python", "AWS"],
        "preferred_skills": ["Kubernetes", "Go"],
        "responsibilities": ["Design systems"],
        "qualifications": ["BS in CS"],
        "engagement_options": [],
        "apply_link": "https://acme.com/apply",
        "source_email": {
            "message_id": msg_id,
            "thread_id": f"thread_{msg_id}",
            "subject": "Job: Senior Engineer",
            "from": "jane@acme.com",
            "date": "2025-02-01",
        },
        "evidence": [],
        "missing_fields": [],
        "confidence": 0.9,
    }


def _make_match_result(job_id: str, score: float = 85.0) -> MatchResult:
    """Create a minimal MatchResult for testing."""
    grade = "excellent" if score >= 85 else "good" if score >= 70 else "fair"
    rec = "strong_apply" if score >= 85 else "apply" if score >= 70 else "consider"

    return MatchResult(
        job_id=job_id,
        overall_score=score,
        match_grade=grade,
        recommendation=rec,
        skills_match=SkillMatch(
            score=80.0,
            mandatory_met=4,
            mandatory_total=5,
            preferred_met=2,
            preferred_total=3,
            matched_mandatory=["Python", "AWS", "Docker", "SQL"],
            missing_mandatory=["Terraform"],
            matched_preferred=["Go", "Kubernetes"],
            missing_preferred=["React"],
        ),
        experience_match=ExperienceMatch(
            score=90.0,
            years_required=5,
            years_candidate=7,
            role_relevance="high",
        ),
        education_score=CategoryScore(score=85.0, weight=0.15),
        location_score=CategoryScore(score=95.0, weight=0.10),
        culture_fit_score=CategoryScore(score=80.0, weight=0.10),
        insights=MatchInsights(
            strengths=["Strong Python background", "Cloud experience", "Leadership skills"],
            concerns=["Missing Terraform", "No React experience"],
            talking_points=["Led migration to microservices"],
        ),
        timestamp=datetime(2025, 2, 2, 10, 0, 0, tzinfo=timezone.utc),
        model_used="gpt-4o-mini",
    )


def _make_tailoring_result(job_id: str) -> Dict[str, Any]:
    """Create a minimal tailoring result dict for testing."""
    return {
        "resume_data": {"personal": {"name": "Alex"}},
        "report": {
            "job_id": job_id,
            "job_title": "Senior Engineer",
            "company": "Acme Corp",
            "resume_name": "Alex Johnson",
            "match_score": 85.0,
            "match_grade": "excellent",
            "total_changes": 7,
            "changes_by_category": {"summary": 1, "skills": 3, "experience": 2, "keywords": 1},
            "changes": [],
            "timestamp": "2025-02-03T10:00:00+00:00",
        },
        "docx_path": "output/tailored/tailored_resume_Acme_Corp_Senior_Engineer.docx",
    }


def _make_draft(job_id: str) -> EmailDraft:
    """Create a minimal EmailDraft for testing."""
    return EmailDraft(
        to="jane@acme.com",
        subject="Re: Job: Senior Engineer at Acme Corp",
        body_text="Dear Jane,\n\nThank you for reaching out about the Senior Engineer role. I am very interested.\n\nBest,\nAlex",
        job_id=job_id,
        job_title="Senior Engineer",
        company="Acme Corp",
        match_score=85.0,
        match_grade="excellent",
        recruiter_name="Jane Recruiter",
        attachment_paths=["output/tailored/resume.docx"],
    )


def _make_reply_result(job_id: str, status: ReplyStatus = ReplyStatus.DRY_RUN) -> ReplyResult:
    """Create a minimal ReplyResult for testing."""
    return ReplyResult(
        draft=_make_draft(job_id),
        status=status,
        gmail_message_id="gmail_msg_123" if status == ReplyStatus.SENT else None,
        timestamp=datetime(2025, 2, 4, 10, 0, 0, tzinfo=timezone.utc),
    )


# ===========================================================================
# Model Tests
# ===========================================================================

class TestEmailSummary:
    def test_round_trip(self):
        es = EmailSummary(
            message_id="msg1",
            thread_id="thread1",
            subject="Job Opportunity",
            from_address="recruiter@corp.com",
            date="2025-02-01",
            snippet="A great opportunity...",
            labels=["INBOX"],
            has_attachments=True,
        )
        d = es.to_dict()
        restored = EmailSummary.from_dict(d)
        assert restored.message_id == "msg1"
        assert restored.from_address == "recruiter@corp.com"
        assert restored.has_attachments is True

    def test_defaults(self):
        es = EmailSummary.from_dict({})
        assert es.message_id == ""
        assert es.labels == []
        assert es.has_attachments is False


class TestMatchSummary:
    def test_round_trip(self):
        ms = MatchSummary(
            overall_score=85.5,
            match_grade="excellent",
            recommendation="strong_apply",
            skills_score=80.0,
            top_strengths=["Python", "AWS"],
            missing_skills=["Terraform"],
        )
        d = ms.to_dict()
        restored = MatchSummary.from_dict(d)
        assert restored.overall_score == 85.5
        assert restored.match_grade == "excellent"
        assert len(restored.top_strengths) == 2
        assert restored.missing_skills == ["Terraform"]


class TestTailoringSummary:
    def test_round_trip(self):
        ts = TailoringSummary(
            total_changes=7,
            changes_by_category={"summary": 1, "skills": 3},
            docx_path="/path/to/resume.docx",
        )
        d = ts.to_dict()
        restored = TailoringSummary.from_dict(d)
        assert restored.total_changes == 7
        assert restored.docx_path == "/path/to/resume.docx"


class TestReplySummary:
    def test_round_trip(self):
        rs = ReplySummary(
            to="recruiter@corp.com",
            subject="Re: Job",
            body_preview="Thank you for reaching out...",
            status=ReplyOutcome.SENT,
            gmail_message_id="gmail123",
        )
        d = rs.to_dict()
        restored = ReplySummary.from_dict(d)
        assert restored.status == ReplyOutcome.SENT
        assert restored.gmail_message_id == "gmail123"

    def test_unknown_status_defaults(self):
        rs = ReplySummary.from_dict({"status": "unknown_status"})
        assert rs.status == ReplyOutcome.NOT_STARTED


class TestCorrelatedOpportunity:
    def test_round_trip_minimal(self):
        co = CorrelatedOpportunity(
            job_id="msg1",
            job_title="Senior Engineer",
            company="Acme Corp",
            stage=OpportunityStage.MATCHED,
        )
        d = co.to_dict()
        restored = CorrelatedOpportunity.from_dict(d)
        assert restored.job_id == "msg1"
        assert restored.stage == OpportunityStage.MATCHED
        assert restored.email is None
        assert restored.match is None

    def test_round_trip_full(self):
        co = CorrelatedOpportunity(
            job_id="msg1",
            job_title="Senior Engineer",
            company="Acme Corp",
            recruiter_name="Jane",
            recruiter_email="jane@acme.com",
            stage=OpportunityStage.REPLIED,
            pipeline_complete=True,
            locations=["SF", "NYC"],
            remote=True,
            hybrid=False,
            email=EmailSummary(message_id="msg1", subject="Job!"),
            match=MatchSummary(overall_score=90.0, match_grade="excellent"),
            tailoring=TailoringSummary(total_changes=5),
            reply=ReplySummary(to="jane@acme.com", status=ReplyOutcome.SENT),
            email_received_at="2025-02-01T12:00:00+00:00",
            matched_at="2025-02-02T10:00:00+00:00",
        )
        d = co.to_dict()
        restored = CorrelatedOpportunity.from_dict(d)
        assert restored.pipeline_complete is True
        assert restored.email.subject == "Job!"
        assert restored.match.overall_score == 90.0
        assert restored.tailoring.total_changes == 5
        assert restored.reply.status == ReplyOutcome.SENT
        assert restored.locations == ["SF", "NYC"]


class TestCorrelationSummary:
    def test_round_trip(self):
        cs = CorrelationSummary(
            total_opportunities=10,
            resume_name="Alex Johnson",
            matched_count=8,
            avg_match_score=75.5,
            max_match_score=95.0,
            min_match_score=55.0,
            by_grade={"excellent": 2, "good": 4, "fair": 2},
            by_recommendation={"strong_apply": 2, "apply": 4, "consider": 2},
            replies_sent=3,
            tailored_count=5,
            docx_generated=5,
        )
        d = cs.to_dict()
        restored = CorrelationSummary.from_dict(d)
        assert restored.total_opportunities == 10
        assert restored.resume_name == "Alex Johnson"
        assert restored.avg_match_score == 75.5
        assert restored.by_grade["excellent"] == 2


# ===========================================================================
# Correlator Tests
# ===========================================================================

class TestOpportunityCorrelator:
    def test_empty_correlator(self):
        correlator = OpportunityCorrelator()
        result = correlator.correlate()
        assert result == []

    def test_messages_only(self):
        correlator = OpportunityCorrelator()
        correlator.add_messages([_make_email("msg1"), _make_email("msg2")])
        result = correlator.correlate()
        assert len(result) == 2

        # All should be at FETCHED stage
        for c in result:
            assert c.stage == OpportunityStage.FETCHED
            assert c.email is not None
            assert c.match is None

    def test_opportunities_only(self):
        correlator = OpportunityCorrelator()
        correlator.add_opportunities([
            _make_opportunity("msg1"),
            _make_opportunity("msg2", "Staff Engineer", "BigCo"),
        ])
        result = correlator.correlate()
        assert len(result) == 2

        for c in result:
            assert c.stage == OpportunityStage.EXTRACTED
            assert c.opportunity is not None
            assert c.job_title != ""

    def test_full_pipeline_correlation(self):
        """Test correlating all artifact types for a single job."""
        correlator = OpportunityCorrelator()

        msg_id = "msg_full"
        correlator.add_messages([_make_email(msg_id)])
        correlator.add_opportunities([_make_opportunity(msg_id)])
        correlator.add_match_results([_make_match_result(msg_id)])
        correlator.add_tailoring_results([_make_tailoring_result(msg_id)])
        correlator.add_drafts([_make_draft(msg_id)])
        correlator.add_reply_results([_make_reply_result(msg_id, ReplyStatus.DRY_RUN)])

        result = correlator.correlate()
        assert len(result) == 1

        c = result[0]
        assert c.job_id == msg_id
        assert c.job_title == "Senior Engineer"
        assert c.company == "Acme Corp"
        assert c.stage == OpportunityStage.REPLIED
        assert c.pipeline_complete is True  # dry_run counts as complete

        # Email
        assert c.email is not None
        assert c.email.message_id == msg_id
        assert c.email.has_attachments is True
        assert "INBOX" in c.email.labels

        # Match
        assert c.match is not None
        assert c.match.overall_score == 85.0
        assert c.match.match_grade == "excellent"
        assert c.match.recommendation == "strong_apply"
        assert c.match.mandatory_skills_met == 4
        assert "Terraform" in c.match.missing_skills

        # Tailoring
        assert c.tailoring is not None
        assert c.tailoring.total_changes == 7
        assert c.tailoring.docx_path is not None

        # Reply
        assert c.reply is not None
        assert c.reply.status == ReplyOutcome.DRY_RUN
        assert c.reply.to == "jane@acme.com"

    def test_mixed_stages(self):
        """Test that each opportunity gets the correct stage."""
        correlator = OpportunityCorrelator()

        # msg1: only email
        correlator.add_messages([_make_email("msg1")])

        # msg2: email + opportunity
        correlator.add_messages([_make_email("msg2")])
        correlator.add_opportunities([_make_opportunity("msg2")])

        # msg3: email + opportunity + match
        correlator.add_messages([_make_email("msg3")])
        correlator.add_opportunities([_make_opportunity("msg3")])
        correlator.add_match_results([_make_match_result("msg3", 90.0)])

        # msg4: email + opportunity + match + tailoring
        correlator.add_messages([_make_email("msg4")])
        correlator.add_opportunities([_make_opportunity("msg4")])
        correlator.add_match_results([_make_match_result("msg4", 80.0)])
        correlator.add_tailoring_results([_make_tailoring_result("msg4")])

        result = correlator.correlate()
        assert len(result) == 4

        stages = {c.job_id: c.stage for c in result}
        assert stages["msg1"] == OpportunityStage.FETCHED
        assert stages["msg2"] == OpportunityStage.EXTRACTED
        assert stages["msg3"] == OpportunityStage.MATCHED
        assert stages["msg4"] == OpportunityStage.TAILORED

    def test_sorting_by_score(self):
        """Results should be sorted by match score descending."""
        correlator = OpportunityCorrelator()
        correlator.add_opportunities([
            _make_opportunity("msg1"),
            _make_opportunity("msg2"),
            _make_opportunity("msg3"),
        ])
        correlator.add_match_results([
            _make_match_result("msg1", 70.0),
            _make_match_result("msg2", 95.0),
            _make_match_result("msg3", 80.0),
        ])

        result = correlator.correlate()
        scores = [c.match.overall_score for c in result]
        assert scores == [95.0, 80.0, 70.0]

    def test_unmatched_after_matched(self):
        """Unmatched opportunities should come after matched ones."""
        correlator = OpportunityCorrelator()
        correlator.add_opportunities([
            _make_opportunity("msg_unmatched"),
            _make_opportunity("msg_matched"),
        ])
        correlator.add_match_results([_make_match_result("msg_matched", 75.0)])

        result = correlator.correlate()
        assert result[0].job_id == "msg_matched"
        assert result[1].job_id == "msg_unmatched"

    def test_reply_status_mapping(self):
        """Test that ReplyStatus maps correctly to ReplyOutcome."""
        for reply_status, expected_outcome in [
            (ReplyStatus.SENT, ReplyOutcome.SENT),
            (ReplyStatus.DRY_RUN, ReplyOutcome.DRY_RUN),
            (ReplyStatus.FAILED, ReplyOutcome.FAILED),
            (ReplyStatus.DRAFT, ReplyOutcome.DRAFTED),
        ]:
            correlator = OpportunityCorrelator()
            correlator.add_reply_results([
                _make_reply_result("msg1", reply_status),
            ])
            result = correlator.correlate()
            assert result[0].reply.status == expected_outcome

    def test_pipeline_complete_only_for_sent_or_dry_run(self):
        """Pipeline is only 'complete' when reply was sent or dry-run."""
        for status, expected_complete in [
            (ReplyStatus.SENT, True),
            (ReplyStatus.DRY_RUN, True),
            (ReplyStatus.FAILED, False),
            (ReplyStatus.DRAFT, False),
        ]:
            correlator = OpportunityCorrelator()
            correlator.add_reply_results([_make_reply_result("msg1", status)])
            result = correlator.correlate()
            assert result[0].pipeline_complete is expected_complete, \
                f"Expected pipeline_complete={expected_complete} for {status}"


class TestBuildSummary:
    def test_summary_statistics(self):
        correlator = OpportunityCorrelator()
        for i in range(5):
            msg_id = f"msg{i}"
            correlator.add_opportunities([_make_opportunity(msg_id, f"Role {i}", f"Company {i % 3}")])
            correlator.add_match_results([_make_match_result(msg_id, 60.0 + i * 10)])

        # Add tailoring for 3
        for i in range(3):
            correlator.add_tailoring_results([_make_tailoring_result(f"msg{i}")])

        # Add replies for 2
        correlator.add_reply_results([
            _make_reply_result("msg0", ReplyStatus.SENT),
            _make_reply_result("msg1", ReplyStatus.DRY_RUN),
        ])

        correlated = correlator.correlate()
        summary = correlator.build_summary(correlated, resume_name="Alex", resume_file="resume.json")

        assert summary.total_opportunities == 5
        assert summary.resume_name == "Alex"
        assert summary.matched_count == 5
        assert summary.avg_match_score == pytest.approx(80.0, abs=0.1)
        assert summary.max_match_score == 100.0
        assert summary.min_match_score == 60.0
        assert summary.tailored_count == 3
        assert summary.replies_sent == 1
        assert summary.replies_dry_run == 1
        assert len(summary.top_companies) > 0

    def test_empty_summary(self):
        correlator = OpportunityCorrelator()
        correlated = correlator.correlate()
        summary = correlator.build_summary(correlated)
        assert summary.total_opportunities == 0
        assert summary.matched_count == 0
        assert summary.avg_match_score == 0.0


# ===========================================================================
# Helper Tests
# ===========================================================================

class TestOppJobId:
    def test_normal(self):
        opp = {"source_email": {"message_id": "msg123"}}
        assert _opp_job_id(opp) == "msg123"

    def test_missing_source_email(self):
        assert _opp_job_id({}) == ""

    def test_missing_message_id(self):
        assert _opp_job_id({"source_email": {}}) == ""

    def test_non_dict_source(self):
        assert _opp_job_id({"source_email": "not_a_dict"}) == ""


# ===========================================================================
# Report Rendering Tests
# ===========================================================================

class TestReportRendering:
    def _setup_correlated(self) -> tuple:
        """Create a set of correlated opportunities for rendering tests."""
        correlator = OpportunityCorrelator()
        for i in range(3):
            msg_id = f"msg{i}"
            correlator.add_messages([_make_email(msg_id, f"Job {i}")])
            correlator.add_opportunities([_make_opportunity(msg_id, f"Engineer {i}", f"Corp {i}")])
            correlator.add_match_results([_make_match_result(msg_id, 70 + i * 10)])

        correlator.add_tailoring_results([_make_tailoring_result("msg2")])
        correlator.add_reply_results([_make_reply_result("msg2", ReplyStatus.DRY_RUN)])

        correlated = correlator.correlate()
        summary = correlator.build_summary(correlated, resume_name="Alex Johnson")
        return correlated, summary

    def test_summary_report_contains_key_sections(self):
        correlated, summary = self._setup_correlated()
        md = render_correlation_summary(summary, correlated)

        assert "# Job Opportunity Correlation Report" in md
        assert "## Executive Summary" in md
        assert "## Match Statistics" in md
        assert "## All Opportunities" in md
        assert "Alex Johnson" in md
        assert "Engineer" in md

    def test_summary_report_contains_all_opportunities(self):
        correlated, summary = self._setup_correlated()
        md = render_correlation_summary(summary, correlated)

        # Should have rows for all 3 opportunities
        for i in range(3):
            assert f"Corp {i}" in md

    def test_opportunity_card_rendering(self):
        correlator = OpportunityCorrelator()
        msg_id = "msg_card"
        correlator.add_messages([_make_email(msg_id)])
        correlator.add_opportunities([_make_opportunity(msg_id)])
        correlator.add_match_results([_make_match_result(msg_id)])
        correlator.add_tailoring_results([_make_tailoring_result(msg_id)])
        correlator.add_reply_results([_make_reply_result(msg_id, ReplyStatus.SENT)])

        correlated = correlator.correlate()
        card = render_opportunity_card(correlated[0])

        assert "# Senior Engineer at Acme Corp" in card
        assert "## Source Email" in card
        assert "## Match Result" in card
        assert "## Tailored Resume" in card
        assert "## Reply Status" in card
        assert "## Timeline" in card
        assert "85" in card  # match score
        assert "Terraform" in card  # missing skill
        assert "Strong Python" in card  # strength

    def test_full_report_includes_cards(self):
        correlated, summary = self._setup_correlated()
        report = render_correlation_report(summary, correlated, include_cards=True)

        assert "# Job Opportunity Correlation Report" in report
        assert "# Detailed Opportunity Cards" in report
        # Should contain individual opportunity headers
        for i in range(3):
            assert f"Corp {i}" in report

    def test_report_without_cards(self):
        correlated, summary = self._setup_correlated()
        report = render_correlation_report(summary, correlated, include_cards=False)

        assert "# Job Opportunity Correlation Report" in report
        assert "# Detailed Opportunity Cards" not in report

    def test_card_minimal_data(self):
        """Card should render even with minimal data."""
        c = CorrelatedOpportunity(job_id="min1")
        card = render_opportunity_card(c)
        assert "Unknown Role" in card
        assert "Unknown Company" in card
        assert "min1" in card


# ===========================================================================
# I/O Tests
# ===========================================================================

class TestCorrelationIO:
    def test_write_and_read_round_trip(self):
        correlator = OpportunityCorrelator()
        msg_id = "msg_io"
        correlator.add_opportunities([_make_opportunity(msg_id)])
        correlator.add_match_results([_make_match_result(msg_id)])

        correlated = correlator.correlate()
        summary = correlator.build_summary(correlated, resume_name="Alex")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "correlation.json"
            write_correlation(path, correlated, summary)

            # Verify file exists and is valid JSON
            raw = json.loads(path.read_text(encoding="utf-8"))
            assert raw["count"] == 1
            assert "summary" in raw
            assert "correlated_opportunities" in raw

            # Read back
            restored_correlated, restored_summary = read_correlation(path)
            assert len(restored_correlated) == 1
            assert restored_correlated[0].job_id == msg_id
            assert restored_correlated[0].match.overall_score == 85.0
            assert restored_summary.resume_name == "Alex"

    def test_write_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.json"
            summary = CorrelationSummary()
            write_correlation(path, [], summary)

            restored_correlated, restored_summary = read_correlation(path)
            assert restored_correlated == []
            assert restored_summary.total_opportunities == 0


# ===========================================================================
# Stage Determination Tests
# ===========================================================================

class TestStageDetermination:
    def test_all_stages(self):
        """Verify _determine_stage returns the correct furthest stage."""
        from email_opportunity_pipeline.correlation.correlator import OpportunityCorrelator

        # Use the static method directly
        det = OpportunityCorrelator._determine_stage

        assert det(None, None, None, None, None, None) == OpportunityStage.FETCHED
        assert det("email", None, None, None, None, None) == OpportunityStage.FETCHED
        assert det("email", {"opp": 1}, None, None, None, None) == OpportunityStage.EXTRACTED
        assert det("email", {"opp": 1}, "match", None, None, None) == OpportunityStage.MATCHED
        assert det("email", {"opp": 1}, "match", {"tail": 1}, None, None) == OpportunityStage.TAILORED
        assert det("email", {"opp": 1}, "match", {"tail": 1}, "draft", None) == OpportunityStage.COMPOSED
        assert det("email", {"opp": 1}, "match", {"tail": 1}, "draft", "reply") == OpportunityStage.REPLIED


# ===========================================================================
# Integration-style test with file outputs
# ===========================================================================

class TestCorrelationIntegration:
    def test_full_flow_with_file_output(self):
        """Simulate a full correlation flow: build, correlate, summarize, write."""
        correlator = OpportunityCorrelator()

        # Simulate 5 opportunities at various stages
        for i in range(5):
            msg_id = f"integration_msg{i}"
            correlator.add_messages([_make_email(msg_id, f"Job {i}")])
            correlator.add_opportunities([
                _make_opportunity(msg_id, f"Role {i}", f"Company {i}")
            ])

        # Match 3 of them
        for i in range(3):
            correlator.add_match_results([
                _make_match_result(f"integration_msg{i}", 60 + i * 15)
            ])

        # Tailor 2
        for i in range(2):
            correlator.add_tailoring_results([
                _make_tailoring_result(f"integration_msg{i}")
            ])

        # Reply to 1
        correlator.add_reply_results([
            _make_reply_result("integration_msg0", ReplyStatus.SENT)
        ])

        correlated = correlator.correlate()
        assert len(correlated) == 5

        summary = correlator.build_summary(
            correlated, resume_name="Test User", resume_file="test.json"
        )

        assert summary.total_opportunities == 5
        assert summary.matched_count == 3
        assert summary.tailored_count == 2
        assert summary.replies_sent == 1

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "correlation"
            out_dir.mkdir()

            # Write JSON
            json_path = out_dir / "correlation.json"
            write_correlation(json_path, correlated, summary)

            # Write summary report
            summary_md = render_correlation_summary(summary, correlated)
            (out_dir / "correlation_summary.md").write_text(summary_md)

            # Write individual cards
            cards_dir = out_dir / "opportunity_cards"
            cards_dir.mkdir()
            for c in correlated:
                card_md = render_opportunity_card(c)
                (cards_dir / f"{c.job_id}.md").write_text(card_md)

            # Verify all files exist
            assert json_path.exists()
            assert (out_dir / "correlation_summary.md").exists()
            assert len(list(cards_dir.iterdir())) == 5

            # Verify JSON is valid and complete
            raw = json.loads(json_path.read_text())
            assert raw["count"] == 5
            assert raw["summary"]["total_opportunities"] == 5

            # Verify summary markdown has content
            md_content = (out_dir / "correlation_summary.md").read_text()
            assert "Test User" in md_content
            assert "Company 0" in md_content
