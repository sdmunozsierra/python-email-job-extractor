"""
Markdown report rendering for application tracking.

Generates user-friendly reports showing the post-reply lifecycle of each
application: status, interviews, offers, notes, and a full audit trail.
"""
from __future__ import annotations

from typing import List

from .models import (
    ApplicationStatus,
    FinalOutcome,
    TrackedApplication,
    TrackingSummary,
)


# ---------------------------------------------------------------------------
# Status / outcome icons
# ---------------------------------------------------------------------------

_STATUS_ICON = {
    ApplicationStatus.APPLIED: "\U0001f4e4",       # 📤
    ApplicationStatus.INTERVIEWING: "\U0001f5e3",   # 🗣️
    ApplicationStatus.OFFERED: "\U0001f4b0",        # 💰
    ApplicationStatus.CLOSED: "\U0001f3c1",         # 🏁
}

_OUTCOME_ICON = {
    FinalOutcome.ACCEPTED: "\U0001f389",   # 🎉
    FinalOutcome.DECLINED: "\U0001f6ab",   # 🚫
    FinalOutcome.REJECTED: "\u274c",       # ❌
    FinalOutcome.WITHDRAWN: "\u21a9\ufe0f", # ↩️
    FinalOutcome.GHOSTED: "\U0001f47b",    # 👻
}

_OUTCOME_LABEL = {
    "accepted": "Accepted",
    "declined": "Declined",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
    "ghosted": "Ghosted",
}


def _trunc(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def render_tracking_summary(
    summary: TrackingSummary,
    applications: List[TrackedApplication],
) -> str:
    """Render a Markdown summary of all tracked applications."""
    lines: List[str] = []

    lines.append("# Application Tracking Report")
    lines.append("")
    if summary.generated_at:
        lines.append(f"**Generated:** {summary.generated_at}")
    lines.append("")

    # ---- Executive summary ----
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Tracked | {summary.total_tracked} |")
    lines.append(f"| Active | {summary.active_count} |")
    lines.append(f"| Total Interviews | {summary.total_interviews} |")
    lines.append(f"| Offers Received | {summary.offers_received} |")
    if summary.avg_match_score > 0:
        lines.append(f"| Avg Match Score | {summary.avg_match_score:.1f} |")
    lines.append("")

    # ---- Status distribution ----
    if summary.by_status:
        lines.append("## Status Distribution")
        lines.append("")
        lines.append("| Status | Count |")
        lines.append("|--------|-------|")
        for status_name in ["applied", "interviewing", "offered", "closed"]:
            count = summary.by_status.get(status_name, 0)
            if count:
                try:
                    icon = _STATUS_ICON.get(ApplicationStatus(status_name), "")
                except ValueError:
                    icon = ""
                lines.append(f"| {icon} {status_name.title()} | {count} |")
        lines.append("")

    # ---- Outcome distribution ----
    if summary.by_outcome:
        lines.append("## Outcomes")
        lines.append("")
        lines.append("| Outcome | Count |")
        lines.append("|---------|-------|")
        for outcome_name in ["accepted", "declined", "rejected", "withdrawn", "ghosted"]:
            count = summary.by_outcome.get(outcome_name, 0)
            if count:
                try:
                    icon = _OUTCOME_ICON.get(FinalOutcome(outcome_name), "")
                except ValueError:
                    icon = ""
                label = _OUTCOME_LABEL.get(outcome_name, outcome_name.title())
                lines.append(f"| {icon} {label} | {count} |")
        lines.append("")

    # ---- All applications table ----
    lines.append("## All Applications")
    lines.append("")
    lines.append(
        "| # | Company | Job Title | Status | Outcome | Score | Interviews | Updated |"
    )
    lines.append(
        "|---|---------|-----------|--------|---------|-------|------------|---------|"
    )

    for i, app in enumerate(applications, 1):
        company = _trunc(app.company, 25) if app.company else "--"
        title = _trunc(app.job_title, 30) if app.job_title else "--"
        status_icon = _STATUS_ICON.get(app.status, "")
        status = f"{status_icon} {app.status.value.title()}"

        if app.final_outcome:
            out_icon = _OUTCOME_ICON.get(app.final_outcome, "")
            outcome = f"{out_icon} {app.final_outcome.value.title()}"
        else:
            outcome = "--"

        score = f"{app.match_score:.0f}" if app.match_score is not None else "--"
        interviews = str(len(app.interviews))
        updated = app.last_updated_at[:10] if app.last_updated_at else "--"

        lines.append(
            f"| {i} | {company} | {title} | {status} | {outcome} | {score} | {interviews} | {updated} |"
        )
    lines.append("")

    # ---- Top companies ----
    if summary.top_companies:
        lines.append("## Top Companies")
        lines.append("")
        lines.append("| Company | Applications |")
        lines.append("|---------|-------------|")
        for item in summary.top_companies[:10]:
            lines.append(f"| {item['company']} | {item['count']} |")
        lines.append("")

    lines.append("---")
    lines.append("*Report generated by email-pipeline track*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual application card
# ---------------------------------------------------------------------------

def render_application_card(app: TrackedApplication) -> str:
    """Render a detailed Markdown card for a single tracked application."""
    lines: List[str] = []

    status_icon = _STATUS_ICON.get(app.status, "")
    lines.append(f"# {app.job_title or 'Unknown Role'} at {app.company or 'Unknown Company'}")
    lines.append("")
    lines.append(f"**Status:** {status_icon} {app.status.value.title()}")

    if app.final_outcome:
        out_icon = _OUTCOME_ICON.get(app.final_outcome, "")
        lines.append(f"**Outcome:** {out_icon} {app.final_outcome.value.title()}")

    if app.match_score is not None:
        lines.append(f"**Match Score:** {app.match_score:.0f} / 100 ({app.match_grade or 'N/A'})")

    lines.append(f"**Job ID:** `{app.job_id}`")
    lines.append("")

    # ---- Contact ----
    if app.recruiter_name or app.recruiter_email:
        lines.append("## Contact")
        lines.append("")
        if app.recruiter_name:
            lines.append(f"- **Recruiter:** {app.recruiter_name}")
        if app.recruiter_email:
            lines.append(f"- **Email:** {app.recruiter_email}")
        lines.append("")

    # ---- Interviews ----
    if app.interviews:
        lines.append("## Interviews")
        lines.append("")
        for i, iv in enumerate(app.interviews, 1):
            status = "completed" if iv.completed else "scheduled"
            lines.append(f"### Round {iv.round_number or i}: {iv.interview_type.value.replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"- **Status:** {status.title()}")
            if iv.scheduled_at:
                lines.append(f"- **Scheduled:** {iv.scheduled_at}")
            if iv.interviewer_name:
                interviewer = iv.interviewer_name
                if iv.interviewer_title:
                    interviewer += f" ({iv.interviewer_title})"
                lines.append(f"- **Interviewer:** {interviewer}")
            if iv.notes:
                lines.append(f"- **Notes:** {iv.notes}")
            lines.append("")

    # ---- Offer ----
    if app.offer:
        lines.append("## Offer Details")
        lines.append("")
        if app.offer.salary:
            lines.append(f"- **Salary:** {app.offer.salary}")
        if app.offer.equity:
            lines.append(f"- **Equity:** {app.offer.equity}")
        if app.offer.bonus:
            lines.append(f"- **Bonus:** {app.offer.bonus}")
        if app.offer.benefits_notes:
            lines.append(f"- **Benefits:** {app.offer.benefits_notes}")
        if app.offer.start_date:
            lines.append(f"- **Start Date:** {app.offer.start_date}")
        if app.offer.expiry_date:
            lines.append(f"- **Deadline:** {app.offer.expiry_date}")
        if app.offer.received_at:
            lines.append(f"- **Received:** {app.offer.received_at}")
        if app.offer.notes:
            lines.append(f"- **Notes:** {app.offer.notes}")
        lines.append("")

    # ---- Notes ----
    if app.notes:
        lines.append("## Notes")
        lines.append("")
        for note in app.notes:
            lines.append(f"- {note}")
        lines.append("")

    # ---- Status History ----
    if app.status_history:
        lines.append("## Status History")
        lines.append("")
        lines.append("| Timestamp | From | To | Note |")
        lines.append("|-----------|------|----|------|")
        for sc in app.status_history:
            ts = sc.timestamp[:19] if sc.timestamp else "--"
            note = _trunc(sc.note, 50) if sc.note else "--"
            lines.append(
                f"| {ts} | {sc.from_status} | {sc.to_status} | {note} |"
            )
        lines.append("")

    # ---- Timeline ----
    lines.append("## Timeline")
    lines.append("")
    events = [
        ("Applied", app.applied_at),
        ("Last Updated", app.last_updated_at),
        ("Closed", app.closed_at),
    ]
    for label, ts in events:
        if ts:
            lines.append(f"- **{label}:** {ts}")
    if not any(ts for _, ts in events):
        lines.append("- No timeline events recorded")
    lines.append("")

    lines.append("---")
    lines.append(f"*Job ID: `{app.job_id}`*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Batch rendering
# ---------------------------------------------------------------------------

def render_tracking_report(
    summary: TrackingSummary,
    applications: List[TrackedApplication],
    include_cards: bool = False,
) -> str:
    """Render the full tracking report: summary + optional detailed cards."""
    parts = [render_tracking_summary(summary, applications)]

    if include_cards and applications:
        parts.append("\n---\n")
        parts.append("# Detailed Application Cards\n")
        for app in applications:
            parts.append(render_application_card(app))
            parts.append("\n---\n")

    return "\n".join(parts)
