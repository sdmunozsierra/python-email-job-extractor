"""
Application tracker engine.

Initialises tracked applications from correlation data and provides
mutation methods for status updates, interview recording, offer capture,
and free-form notes -- all with a full audit trail.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import (
    ApplicationStatus,
    FinalOutcome,
    InterviewRecord,
    OfferDetails,
    StatusChange,
    TrackedApplication,
    TrackingSummary,
)

if TYPE_CHECKING:
    from ..correlation.models import CorrelatedOpportunity, OpportunityStage


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApplicationTracker:
    """Manage the post-reply lifecycle of job applications.

    Usage::

        tracker = ApplicationTracker()
        tracker.init_from_correlation(correlated)   # bootstrap
        tracker.update_status(job_id, ApplicationStatus.INTERVIEWING)
        tracker.add_interview(job_id, InterviewRecord(...))
        tracker.set_offer(job_id, OfferDetails(salary="150k"))
        tracker.set_outcome(job_id, FinalOutcome.ACCEPTED)

        summary = tracker.build_summary()
    """

    def __init__(self) -> None:
        self._applications: Dict[str, TrackedApplication] = {}

    # ------------------------------------------------------------------
    # Data ingestion
    # ------------------------------------------------------------------

    def load_existing(self, applications: List[TrackedApplication]) -> None:
        """Load previously saved tracked applications."""
        for app in applications:
            if app.job_id:
                self._applications[app.job_id] = app

    def init_from_correlation(
        self,
        correlated: List["CorrelatedOpportunity"],
        min_stage: Optional["OpportunityStage"] = None,
    ) -> int:
        """Initialise tracking for correlated opportunities.

        Creates a :class:`TrackedApplication` for each opportunity that has
        reached at least *min_stage* (default: ``REPLIED``) and is not
        already tracked.

        Returns the number of newly initialised applications.
        """
        from ..correlation.models import OpportunityStage

        if min_stage is None:
            min_stage = OpportunityStage.REPLIED

        stage_order = list(OpportunityStage)
        min_idx = stage_order.index(min_stage)

        count = 0
        for c in correlated:
            if c.job_id in self._applications:
                continue
            try:
                c_idx = stage_order.index(c.stage)
            except ValueError:
                continue
            if c_idx < min_idx:
                continue

            now = _utc_now()
            applied_at = c.replied_at or now

            app = TrackedApplication(
                job_id=c.job_id,
                job_title=c.job_title,
                company=c.company,
                recruiter_name=c.recruiter_name,
                recruiter_email=c.recruiter_email,
                status=ApplicationStatus.APPLIED,
                match_score=c.match.overall_score if c.match else None,
                match_grade=c.match.match_grade if c.match else None,
                applied_at=applied_at,
                last_updated_at=now,
                status_history=[
                    StatusChange(
                        from_status=ApplicationStatus.APPLIED.value,
                        to_status=ApplicationStatus.APPLIED.value,
                        timestamp=now,
                        note="Initialised from correlation data",
                    ),
                ],
            )
            self._applications[c.job_id] = app
            count += 1

        return count

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def update_status(
        self,
        job_id: str,
        new_status: ApplicationStatus,
        note: Optional[str] = None,
    ) -> TrackedApplication:
        """Transition an application to a new status with audit trail."""
        app = self._get_or_raise(job_id)
        now = _utc_now()

        app.status_history.append(
            StatusChange(
                from_status=app.status.value,
                to_status=new_status.value,
                timestamp=now,
                note=note,
            )
        )
        app.status = new_status
        app.last_updated_at = now

        if new_status == ApplicationStatus.CLOSED:
            app.closed_at = now

        return app

    def set_outcome(
        self,
        job_id: str,
        outcome: FinalOutcome,
        note: Optional[str] = None,
    ) -> TrackedApplication:
        """Set the final outcome and close the application."""
        app = self._get_or_raise(job_id)
        app.final_outcome = outcome
        status_note = note or f"Outcome: {outcome.value}"
        self.update_status(job_id, ApplicationStatus.CLOSED, note=status_note)
        return app

    def add_interview(
        self,
        job_id: str,
        interview: InterviewRecord,
    ) -> TrackedApplication:
        """Record an interview.  Auto-promotes APPLIED to INTERVIEWING."""
        app = self._get_or_raise(job_id)
        now = _utc_now()

        if not interview.created_at:
            interview.created_at = now
        if not interview.round_number:
            interview.round_number = len(app.interviews) + 1

        app.interviews.append(interview)
        app.last_updated_at = now

        if app.status == ApplicationStatus.APPLIED:
            self.update_status(
                job_id,
                ApplicationStatus.INTERVIEWING,
                note=f"Interview added: {interview.interview_type.value}",
            )

        return app

    def set_offer(
        self,
        job_id: str,
        offer: OfferDetails,
    ) -> TrackedApplication:
        """Record an offer.  Auto-promotes to OFFERED."""
        app = self._get_or_raise(job_id)
        now = _utc_now()

        if not offer.received_at:
            offer.received_at = now

        app.offer = offer
        app.last_updated_at = now

        if app.status in (ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEWING):
            self.update_status(
                job_id,
                ApplicationStatus.OFFERED,
                note="Offer received",
            )

        return app

    def add_note(
        self,
        job_id: str,
        note: str,
    ) -> TrackedApplication:
        """Append a free-form note."""
        app = self._get_or_raise(job_id)
        app.notes.append(note)
        app.last_updated_at = _utc_now()
        return app

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_application(self, job_id: str) -> Optional[TrackedApplication]:
        """Return a tracked application or ``None``."""
        return self._applications.get(job_id)

    def get_all(self) -> List[TrackedApplication]:
        """Return all applications sorted by last_updated_at descending."""
        apps = list(self._applications.values())
        apps.sort(
            key=lambda a: a.last_updated_at or "",
            reverse=True,
        )
        return apps

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def build_summary(self) -> TrackingSummary:
        """Compute aggregate statistics across all tracked applications."""
        apps = self.get_all()

        status_counts: Dict[str, int] = defaultdict(int)
        outcome_counts: Dict[str, int] = defaultdict(int)
        company_counts: Dict[str, int] = defaultdict(int)
        scores: List[float] = []
        active = 0
        total_interviews = 0
        offers = 0

        for app in apps:
            status_counts[app.status.value] += 1

            if app.is_active:
                active += 1

            if app.final_outcome:
                outcome_counts[app.final_outcome.value] += 1

            if app.company:
                company_counts[app.company] += 1

            total_interviews += len(app.interviews)

            if app.offer:
                offers += 1

            if app.match_score is not None:
                scores.append(app.match_score)

        avg_score = sum(scores) / len(scores) if scores else 0.0

        sorted_companies = sorted(
            company_counts.items(), key=lambda x: x[1], reverse=True
        )
        top_companies = [
            {"company": name, "count": count}
            for name, count in sorted_companies[:10]
        ]

        return TrackingSummary(
            total_tracked=len(apps),
            by_status=dict(status_counts),
            by_outcome=dict(outcome_counts),
            active_count=active,
            total_interviews=total_interviews,
            offers_received=offers,
            avg_match_score=avg_score,
            top_companies=top_companies,
            generated_at=_utc_now(),
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_or_raise(self, job_id: str) -> TrackedApplication:
        app = self._applications.get(job_id)
        if app is None:
            raise KeyError(
                f"No tracked application with job_id={job_id!r}. "
                f"Known IDs: {list(self._applications.keys())[:5]}"
            )
        return app
