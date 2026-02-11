"""Tests for the application tracking module."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from email_opportunity_pipeline.tracking.models import (
    ApplicationStatus,
    FinalOutcome,
    InterviewRecord,
    InterviewType,
    OfferDetails,
    StatusChange,
    TrackedApplication,
    TrackingSummary,
)
from email_opportunity_pipeline.tracking.tracker import ApplicationTracker
from email_opportunity_pipeline.tracking.report import (
    render_application_card,
    render_tracking_report,
    render_tracking_summary,
)
from email_opportunity_pipeline.correlation.models import (
    CorrelatedOpportunity,
    MatchSummary,
    OpportunityStage,
    ReplyOutcome,
    ReplySummary,
)
from email_opportunity_pipeline.io import read_tracking, write_tracking


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_correlated(
    job_id: str = "msg_001",
    job_title: str = "Senior Engineer",
    company: str = "Acme Corp",
    stage: OpportunityStage = OpportunityStage.REPLIED,
    score: float = 85.0,
    grade: str = "excellent",
) -> CorrelatedOpportunity:
    return CorrelatedOpportunity(
        job_id=job_id,
        job_title=job_title,
        company=company,
        recruiter_name="Jane Recruiter",
        recruiter_email="jane@acme.com",
        stage=stage,
        pipeline_complete=True,
        match=MatchSummary(
            overall_score=score,
            match_grade=grade,
            recommendation="strong_apply",
        ),
        reply=ReplySummary(
            to="jane@acme.com",
            subject="Re: Senior Engineer",
            status=ReplyOutcome.SENT,
        ),
        replied_at="2026-02-01T12:00:00+00:00",
    )


def _make_tracked(
    job_id: str = "msg_001",
    status: ApplicationStatus = ApplicationStatus.APPLIED,
) -> TrackedApplication:
    return TrackedApplication(
        job_id=job_id,
        job_title="Senior Engineer",
        company="Acme Corp",
        status=status,
        match_score=85.0,
        match_grade="excellent",
        applied_at="2026-02-01T12:00:00+00:00",
        last_updated_at="2026-02-01T12:00:00+00:00",
    )


# ============================================================================
# Model tests
# ============================================================================

class TestApplicationStatus:
    def test_values(self):
        assert ApplicationStatus.APPLIED.value == "applied"
        assert ApplicationStatus.INTERVIEWING.value == "interviewing"
        assert ApplicationStatus.OFFERED.value == "offered"
        assert ApplicationStatus.CLOSED.value == "closed"

    def test_from_string(self):
        assert ApplicationStatus("applied") == ApplicationStatus.APPLIED


class TestFinalOutcome:
    def test_values(self):
        assert FinalOutcome.ACCEPTED.value == "accepted"
        assert FinalOutcome.DECLINED.value == "declined"
        assert FinalOutcome.REJECTED.value == "rejected"
        assert FinalOutcome.WITHDRAWN.value == "withdrawn"
        assert FinalOutcome.GHOSTED.value == "ghosted"


class TestInterviewRecord:
    def test_round_trip(self):
        record = InterviewRecord(
            interview_type=InterviewType.TECHNICAL,
            scheduled_at="2026-02-15T10:00:00",
            completed=True,
            interviewer_name="John",
            interviewer_title="Staff Engineer",
            notes="Went well",
            round_number=2,
            created_at="2026-02-10T09:00:00",
        )
        d = record.to_dict()
        restored = InterviewRecord.from_dict(d)
        assert restored.interview_type == InterviewType.TECHNICAL
        assert restored.completed is True
        assert restored.interviewer_name == "John"
        assert restored.round_number == 2

    def test_defaults(self):
        record = InterviewRecord.from_dict({})
        assert record.interview_type == InterviewType.OTHER
        assert record.completed is False
        assert record.round_number == 1

    def test_unknown_type_fallback(self):
        record = InterviewRecord.from_dict({"interview_type": "unknown_type"})
        assert record.interview_type == InterviewType.OTHER


class TestOfferDetails:
    def test_round_trip(self):
        offer = OfferDetails(
            salary="150k USD",
            equity="0.1%",
            bonus="10k",
            start_date="2026-03-01",
            notes="Great offer",
        )
        d = offer.to_dict()
        restored = OfferDetails.from_dict(d)
        assert restored.salary == "150k USD"
        assert restored.equity == "0.1%"
        assert restored.notes == "Great offer"

    def test_defaults(self):
        offer = OfferDetails.from_dict({})
        assert offer.salary is None
        assert offer.equity is None


class TestStatusChange:
    def test_round_trip(self):
        sc = StatusChange(
            from_status="applied",
            to_status="interviewing",
            timestamp="2026-02-10T09:00:00",
            note="Phone screen scheduled",
        )
        d = sc.to_dict()
        restored = StatusChange.from_dict(d)
        assert restored.from_status == "applied"
        assert restored.to_status == "interviewing"
        assert restored.note == "Phone screen scheduled"


class TestTrackedApplication:
    def test_minimal_round_trip(self):
        app = TrackedApplication(job_id="msg_001")
        d = app.to_dict()
        restored = TrackedApplication.from_dict(d)
        assert restored.job_id == "msg_001"
        assert restored.status == ApplicationStatus.APPLIED
        assert restored.is_active is True

    def test_full_round_trip(self):
        app = TrackedApplication(
            job_id="msg_002",
            job_title="Staff Engineer",
            company="BigCo",
            recruiter_name="Alice",
            recruiter_email="alice@bigco.com",
            status=ApplicationStatus.CLOSED,
            final_outcome=FinalOutcome.ACCEPTED,
            match_score=92.0,
            match_grade="excellent",
            interviews=[
                InterviewRecord(
                    interview_type=InterviewType.PHONE_SCREEN,
                    completed=True,
                    round_number=1,
                ),
                InterviewRecord(
                    interview_type=InterviewType.TECHNICAL,
                    completed=True,
                    round_number=2,
                ),
            ],
            offer=OfferDetails(salary="200k", equity="0.5%"),
            notes=["Great company", "Loved the team"],
            status_history=[
                StatusChange(from_status="applied", to_status="interviewing", timestamp="t1"),
                StatusChange(from_status="interviewing", to_status="offered", timestamp="t2"),
                StatusChange(from_status="offered", to_status="closed", timestamp="t3"),
            ],
            applied_at="2026-01-01",
            last_updated_at="2026-02-10",
            closed_at="2026-02-10",
        )
        d = app.to_dict()
        restored = TrackedApplication.from_dict(d)
        assert restored.job_id == "msg_002"
        assert restored.status == ApplicationStatus.CLOSED
        assert restored.final_outcome == FinalOutcome.ACCEPTED
        assert restored.is_active is False
        assert len(restored.interviews) == 2
        assert restored.offer.salary == "200k"
        assert len(restored.notes) == 2
        assert len(restored.status_history) == 3

    def test_is_active(self):
        app = _make_tracked(status=ApplicationStatus.INTERVIEWING)
        assert app.is_active is True
        app.status = ApplicationStatus.CLOSED
        assert app.is_active is False

    def test_unknown_status_fallback(self):
        app = TrackedApplication.from_dict({"job_id": "x", "status": "unknown_status"})
        assert app.status == ApplicationStatus.APPLIED

    def test_unknown_outcome_ignored(self):
        app = TrackedApplication.from_dict({"job_id": "x", "final_outcome": "not_real"})
        assert app.final_outcome is None


class TestTrackingSummary:
    def test_round_trip(self):
        summary = TrackingSummary(
            total_tracked=5,
            by_status={"applied": 2, "interviewing": 3},
            by_outcome={"accepted": 1},
            active_count=4,
            total_interviews=6,
            offers_received=1,
            avg_match_score=82.5,
            top_companies=[{"company": "Acme", "count": 2}],
            generated_at="2026-02-10",
        )
        d = summary.to_dict()
        restored = TrackingSummary.from_dict(d)
        assert restored.total_tracked == 5
        assert restored.active_count == 4
        assert restored.avg_match_score == 82.5

    def test_defaults(self):
        summary = TrackingSummary.from_dict({})
        assert summary.total_tracked == 0
        assert summary.avg_match_score == 0.0


# ============================================================================
# Tracker engine tests
# ============================================================================

class TestApplicationTracker:
    def test_empty_tracker(self):
        tracker = ApplicationTracker()
        assert tracker.get_all() == []
        summary = tracker.build_summary()
        assert summary.total_tracked == 0

    def test_init_from_correlation(self):
        tracker = ApplicationTracker()
        correlated = [
            _make_correlated("msg_001", "Engineer", "Acme"),
            _make_correlated("msg_002", "Manager", "BigCo"),
        ]
        count = tracker.init_from_correlation(correlated)
        assert count == 2
        apps = tracker.get_all()
        assert len(apps) == 2
        assert all(a.status == ApplicationStatus.APPLIED for a in apps)

    def test_init_from_correlation_skips_below_min_stage(self):
        tracker = ApplicationTracker()
        correlated = [
            _make_correlated("msg_001", stage=OpportunityStage.REPLIED),
            _make_correlated("msg_002", stage=OpportunityStage.MATCHED),
        ]
        count = tracker.init_from_correlation(correlated)
        assert count == 1  # only the REPLIED one

    def test_init_idempotent(self):
        tracker = ApplicationTracker()
        correlated = [_make_correlated("msg_001")]
        tracker.init_from_correlation(correlated)
        # Running again should not create duplicates
        count = tracker.init_from_correlation(correlated)
        assert count == 0
        assert len(tracker.get_all()) == 1

    def test_load_existing(self):
        tracker = ApplicationTracker()
        existing = [_make_tracked("msg_001"), _make_tracked("msg_002")]
        tracker.load_existing(existing)
        assert len(tracker.get_all()) == 2

    def test_load_existing_no_duplicate_with_init(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001")])
        correlated = [_make_correlated("msg_001")]
        count = tracker.init_from_correlation(correlated)
        assert count == 0  # already tracked
        assert len(tracker.get_all()) == 1

    def test_update_status(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001")])
        app = tracker.update_status("msg_001", ApplicationStatus.INTERVIEWING, note="Phone screen")
        assert app.status == ApplicationStatus.INTERVIEWING
        assert len(app.status_history) == 1
        assert app.status_history[0].to_status == "interviewing"
        assert app.status_history[0].note == "Phone screen"

    def test_update_status_to_closed_sets_closed_at(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001")])
        app = tracker.update_status("msg_001", ApplicationStatus.CLOSED)
        assert app.closed_at is not None

    def test_set_outcome(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001")])
        app = tracker.set_outcome("msg_001", FinalOutcome.ACCEPTED, note="Hooray!")
        assert app.final_outcome == FinalOutcome.ACCEPTED
        assert app.status == ApplicationStatus.CLOSED
        assert app.closed_at is not None

    def test_add_interview_auto_promotes(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001", status=ApplicationStatus.APPLIED)])
        record = InterviewRecord(interview_type=InterviewType.PHONE_SCREEN)
        app = tracker.add_interview("msg_001", record)
        assert app.status == ApplicationStatus.INTERVIEWING
        assert len(app.interviews) == 1

    def test_add_interview_no_downgrade(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001", status=ApplicationStatus.OFFERED)])
        record = InterviewRecord(interview_type=InterviewType.TECHNICAL)
        app = tracker.add_interview("msg_001", record)
        assert app.status == ApplicationStatus.OFFERED  # should not change
        assert len(app.interviews) == 1

    def test_set_offer_auto_promotes(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001", status=ApplicationStatus.INTERVIEWING)])
        offer = OfferDetails(salary="150k USD")
        app = tracker.set_offer("msg_001", offer)
        assert app.status == ApplicationStatus.OFFERED
        assert app.offer.salary == "150k USD"

    def test_add_note(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001")])
        app = tracker.add_note("msg_001", "Following up next week")
        assert "Following up next week" in app.notes
        assert app.last_updated_at is not None

    def test_build_summary(self):
        tracker = ApplicationTracker()
        tracker.load_existing([
            _make_tracked("msg_001", status=ApplicationStatus.APPLIED),
            _make_tracked("msg_002", status=ApplicationStatus.INTERVIEWING),
            _make_tracked("msg_003", status=ApplicationStatus.OFFERED),
        ])
        # Add an interview and offer to specific apps
        tracker.add_interview(
            "msg_002",
            InterviewRecord(interview_type=InterviewType.TECHNICAL),
        )
        tracker.set_offer("msg_003", OfferDetails(salary="120k"))

        summary = tracker.build_summary()
        assert summary.total_tracked == 3
        assert summary.active_count == 3  # none are CLOSED
        assert summary.total_interviews == 1
        assert summary.offers_received == 1
        assert summary.avg_match_score == 85.0

    def test_unknown_job_id_raises(self):
        tracker = ApplicationTracker()
        with pytest.raises(KeyError):
            tracker.update_status("nonexistent", ApplicationStatus.INTERVIEWING)

    def test_get_application(self):
        tracker = ApplicationTracker()
        tracker.load_existing([_make_tracked("msg_001")])
        assert tracker.get_application("msg_001") is not None
        assert tracker.get_application("nonexistent") is None


# ============================================================================
# Report tests
# ============================================================================

class TestTrackingReport:
    def test_summary_report_contains_sections(self):
        apps = [
            _make_tracked("msg_001", status=ApplicationStatus.APPLIED),
            _make_tracked("msg_002", status=ApplicationStatus.INTERVIEWING),
        ]
        summary = TrackingSummary(
            total_tracked=2,
            by_status={"applied": 1, "interviewing": 1},
            active_count=2,
        )
        md = render_tracking_summary(summary, apps)
        assert "# Application Tracking Report" in md
        assert "Executive Summary" in md
        assert "All Applications" in md
        assert "Acme Corp" in md

    def test_application_card_rendering(self):
        app = _make_tracked("msg_001")
        app.interviews = [
            InterviewRecord(
                interview_type=InterviewType.TECHNICAL,
                scheduled_at="2026-02-15",
                completed=True,
                interviewer_name="John",
                notes="Great discussion",
            ),
        ]
        app.offer = OfferDetails(salary="150k USD")
        app.notes = ["Looking good"]
        md = render_application_card(app)
        assert "Senior Engineer" in md
        assert "Acme Corp" in md
        assert "Technical" in md
        assert "150k USD" in md
        assert "Looking good" in md

    def test_full_report_includes_cards(self):
        apps = [_make_tracked("msg_001")]
        summary = TrackingSummary(total_tracked=1, active_count=1)
        md = render_tracking_report(summary, apps, include_cards=True)
        assert "Detailed Application Cards" in md
        assert "Senior Engineer" in md

    def test_card_minimal_data(self):
        app = TrackedApplication(job_id="x")
        md = render_application_card(app)
        assert "Unknown Role" in md
        assert "Unknown Company" in md


# ============================================================================
# I/O tests
# ============================================================================

class TestTrackingIO:
    def test_write_and_read_round_trip(self, tmp_path):
        apps = [
            _make_tracked("msg_001"),
            _make_tracked("msg_002", status=ApplicationStatus.INTERVIEWING),
        ]
        summary = TrackingSummary(total_tracked=2, active_count=2)

        path = tmp_path / "tracking.json"
        write_tracking(path, apps, summary)

        restored_apps, restored_summary = read_tracking(path)
        assert len(restored_apps) == 2
        assert restored_apps[0].job_id == "msg_001"
        assert restored_apps[1].status == ApplicationStatus.INTERVIEWING
        assert restored_summary.total_tracked == 2

    def test_write_empty(self, tmp_path):
        path = tmp_path / "tracking.json"
        summary = TrackingSummary()
        write_tracking(path, [], summary)

        restored_apps, restored_summary = read_tracking(path)
        assert len(restored_apps) == 0
        assert restored_summary.total_tracked == 0

    def test_json_structure(self, tmp_path):
        apps = [_make_tracked("msg_001")]
        summary = TrackingSummary(total_tracked=1)
        path = tmp_path / "tracking.json"
        write_tracking(path, apps, summary)

        raw = json.loads(path.read_text(encoding="utf-8"))
        assert "created_at_utc" in raw
        assert raw["count"] == 1
        assert "summary" in raw
        assert "tracked_applications" in raw
        assert raw["tracked_applications"][0]["job_id"] == "msg_001"
