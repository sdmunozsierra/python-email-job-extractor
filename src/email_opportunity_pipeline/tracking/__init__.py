"""
Application tracking module.

Extends the pipeline beyond the REPLIED stage to track the full hiring
lifecycle -- from application sent through interviews, offers, and final
outcomes (accepted, declined, rejected, withdrawn, ghosted).

Quick start (Python API)::

    from email_opportunity_pipeline.tracking import (
        ApplicationTracker,
        render_tracking_report,
    )

    tracker = ApplicationTracker()
    tracker.init_from_correlation(correlated_opportunities)
    tracker.update_status(job_id, ApplicationStatus.INTERVIEWING)

    summary = tracker.build_summary()
    print(render_tracking_report(summary, tracker.get_all()))

CLI::

    email-pipeline track --out-dir output --out output/tracking
    email-pipeline track-update --tracking-file output/tracking/tracking.json \\
        --job-id <id> --action status --status interviewing
"""

__all__ = [
    "ApplicationStatus",
    "ApplicationTracker",
    "FinalOutcome",
    "InterviewRecord",
    "InterviewType",
    "OfferDetails",
    "StatusChange",
    "TrackedApplication",
    "TrackingSummary",
    "render_application_card",
    "render_tracking_report",
    "render_tracking_summary",
]

from .models import (
    ApplicationStatus,
    FinalOutcome,
    InterviewRecord,
    InterviewType,
    OfferDetails,
    StatusChange,
    TrackedApplication,
    TrackingSummary,
)
from .report import (
    render_application_card,
    render_tracking_report,
    render_tracking_summary,
)
from .tracker import ApplicationTracker
