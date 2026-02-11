"""
Markdown report rendering for job-opportunity correlation.

Generates user-friendly reports showing the complete lifecycle of each
opportunity: source email, extracted data, match score, tailored resume,
and reply status -- all in a single unified view.
"""
from __future__ import annotations

from typing import List, Optional

from .models import (
    CorrelatedOpportunity,
    CorrelationSummary,
    OpportunityStage,
    ReplyOutcome,
)


# ---------------------------------------------------------------------------
# Stage / status icons
# ---------------------------------------------------------------------------

_STAGE_ICON = {
    OpportunityStage.FETCHED: "📬",
    OpportunityStage.FILTERED: "🔍",
    OpportunityStage.EXTRACTED: "📋",
    OpportunityStage.ANALYZED: "🧪",
    OpportunityStage.MATCHED: "🎯",
    OpportunityStage.TAILORED: "✂️",
    OpportunityStage.COMPOSED: "✉️",
    OpportunityStage.REPLIED: "✅",
    # Post-reply tracking stages
    OpportunityStage.APPLIED: "📤",
    OpportunityStage.INTERVIEWING: "🗣️",
    OpportunityStage.OFFERED: "💰",
    OpportunityStage.CLOSED: "🏁",
}

_REPLY_ICON = {
    ReplyOutcome.NOT_STARTED: "⬜",
    ReplyOutcome.DRAFTED: "📝",
    ReplyOutcome.DRY_RUN: "👀",
    ReplyOutcome.SENT: "✅",
    ReplyOutcome.FAILED: "❌",
}

_GRADE_EMOJI = {
    "excellent": "🟢",
    "good": "🔵",
    "fair": "🟡",
    "poor": "🟠",
    "unqualified": "🔴",
}

_RECOMMENDATION_LABEL = {
    "strong_apply": "Strong Apply",
    "apply": "Apply",
    "consider": "Consider",
    "skip": "Skip",
    "not_recommended": "Not Recommended",
}


def _score_bar(score: float, width: int = 20) -> str:
    """Render a small text-based progress bar for a score 0-100."""
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _trunc(text: str, max_len: int = 60) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def render_correlation_summary(
    summary: CorrelationSummary,
    correlated: List[CorrelatedOpportunity],
) -> str:
    """Render a Markdown summary of all correlated opportunities."""
    lines: List[str] = []

    # Header
    lines.append("# Job Opportunity Correlation Report")
    lines.append("")
    if summary.resume_name:
        lines.append(f"**Candidate:** {summary.resume_name}")
    if summary.resume_file:
        lines.append(f"**Resume:** `{summary.resume_file}`")
    if summary.generated_at:
        lines.append(f"**Generated:** {summary.generated_at}")
    lines.append("")

    # ---- Executive summary ----
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Opportunities | {summary.total_opportunities} |")
    lines.append(f"| Matched | {summary.matched_count} |")
    lines.append(f"| Tailored Resumes | {summary.tailored_count} |")
    lines.append(f"| .docx Generated | {summary.docx_generated} |")
    replies_total = (
        summary.replies_sent + summary.replies_dry_run
        + summary.replies_drafted + summary.replies_failed
    )
    lines.append(f"| Replies (total) | {replies_total} |")
    lines.append(f"| Replies Sent | {summary.replies_sent} |")
    lines.append(f"| Pipeline Complete | {summary.pipeline_complete_count} |")
    lines.append("")

    # ---- Match statistics ----
    if summary.matched_count > 0:
        lines.append("## Match Statistics")
        lines.append("")
        lines.append(f"- **Average Score:** {summary.avg_match_score:.1f} / 100")
        lines.append(f"- **Highest Score:** {summary.max_match_score:.1f} / 100")
        lines.append(f"- **Lowest Score:** {summary.min_match_score:.1f} / 100")
        lines.append("")

        # Grade distribution
        if summary.by_grade:
            lines.append("### Grade Distribution")
            lines.append("")
            lines.append("| Grade | Count |")
            lines.append("|-------|-------|")
            for grade in ["excellent", "good", "fair", "poor", "unqualified"]:
                count = summary.by_grade.get(grade, 0)
                if count:
                    emoji = _GRADE_EMOJI.get(grade, "")
                    lines.append(f"| {emoji} {grade.title()} | {count} |")
            lines.append("")

        # Recommendation distribution
        if summary.by_recommendation:
            lines.append("### Recommendations")
            lines.append("")
            lines.append("| Recommendation | Count |")
            lines.append("|----------------|-------|")
            for rec in ["strong_apply", "apply", "consider", "skip", "not_recommended"]:
                count = summary.by_recommendation.get(rec, 0)
                if count:
                    label = _RECOMMENDATION_LABEL.get(rec, rec)
                    lines.append(f"| {label} | {count} |")
            lines.append("")

    # ---- Pipeline stage distribution ----
    if summary.by_stage:
        lines.append("## Pipeline Progress")
        lines.append("")
        lines.append("| Stage | Count |")
        lines.append("|-------|-------|")
        stage_order = [
            "fetched", "filtered", "extracted", "analyzed",
            "matched", "tailored", "composed", "replied",
            "applied", "interviewing", "offered", "closed",
        ]
        for stage_name in stage_order:
            count = summary.by_stage.get(stage_name, 0)
            if count:
                try:
                    icon = _STAGE_ICON.get(OpportunityStage(stage_name), "")
                except ValueError:
                    icon = ""
                lines.append(f"| {icon} {stage_name.title()} | {count} |")
        lines.append("")

    # ---- Quick-reference table ----
    lines.append("## All Opportunities")
    lines.append("")
    lines.append(
        "| # | Score | Grade | Company | Job Title | Stage | Reply |"
    )
    lines.append(
        "|---|-------|-------|---------|-----------|-------|-------|"
    )

    for i, c in enumerate(correlated, 1):
        score = f"{c.match.overall_score:.0f}" if c.match else "--"
        grade = c.match.match_grade.title() if c.match and c.match.match_grade else "--"
        grade_emoji = _GRADE_EMOJI.get(c.match.match_grade, "") if c.match else ""
        company = _trunc(c.company, 25) if c.company else "--"
        title = _trunc(c.job_title, 30) if c.job_title else "--"
        stage_icon = _STAGE_ICON.get(c.stage, "")
        reply_icon = _REPLY_ICON.get(c.reply.status, "⬜") if c.reply else "⬜"
        lines.append(
            f"| {i} | {score} | {grade_emoji} {grade} | {company} | {title} | {stage_icon} {c.stage.value.title()} | {reply_icon} |"
        )
    lines.append("")

    # ---- Top companies ----
    if summary.top_companies:
        lines.append("## Top Companies")
        lines.append("")
        lines.append("| Company | Opportunities |")
        lines.append("|---------|---------------|")
        for item in summary.top_companies[:10]:
            lines.append(f"| {item['company']} | {item['count']} |")
        lines.append("")

    # ---- Footer ----
    lines.append("---")
    lines.append("*Report generated by email-pipeline correlate*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual opportunity card
# ---------------------------------------------------------------------------

def render_opportunity_card(c: CorrelatedOpportunity) -> str:
    """Render a detailed Markdown card for a single correlated opportunity."""
    lines: List[str] = []

    stage_icon = _STAGE_ICON.get(c.stage, "")
    lines.append(f"# {c.job_title or 'Unknown Role'} at {c.company or 'Unknown Company'}")
    lines.append("")
    lines.append(f"**Stage:** {stage_icon} {c.stage.value.title()}")
    if c.pipeline_complete:
        lines.append("**Pipeline:** Complete")
    lines.append(f"**Job ID:** `{c.job_id}`")
    lines.append("")

    # ---- Contact ----
    lines.append("## Contact")
    lines.append("")
    if c.recruiter_name:
        lines.append(f"- **Recruiter:** {c.recruiter_name}")
    if c.recruiter_email:
        lines.append(f"- **Email:** {c.recruiter_email}")
    if c.locations:
        lines.append(f"- **Locations:** {', '.join(c.locations)}")
    if c.remote is not None:
        lines.append(f"- **Remote:** {'Yes' if c.remote else 'No'}")
    if c.hybrid is not None:
        lines.append(f"- **Hybrid:** {'Yes' if c.hybrid else 'No'}")
    lines.append("")

    # ---- Source Email ----
    if c.email:
        lines.append("## Source Email")
        lines.append("")
        lines.append(f"- **From:** {c.email.from_address}")
        lines.append(f"- **Subject:** {c.email.subject}")
        lines.append(f"- **Date:** {c.email.date}")
        if c.email.has_attachments:
            lines.append(f"- **Attachments:** Yes")
        if c.email.snippet:
            lines.append(f"- **Preview:** {_trunc(c.email.snippet, 150)}")
        lines.append("")

    # ---- Match Result ----
    if c.match:
        m = c.match
        grade_emoji = _GRADE_EMOJI.get(m.match_grade, "")
        rec_label = _RECOMMENDATION_LABEL.get(m.recommendation, m.recommendation)

        lines.append("## Match Result")
        lines.append("")
        lines.append(f"**Overall Score:** {m.overall_score:.0f} / 100  {_score_bar(m.overall_score)}")
        lines.append(f"**Grade:** {grade_emoji} {m.match_grade.title()}")
        lines.append(f"**Recommendation:** {rec_label}")
        lines.append("")

        # Category breakdown
        lines.append("### Score Breakdown")
        lines.append("")
        lines.append("| Category | Score | Bar |")
        lines.append("|----------|-------|-----|")
        for label, score in [
            ("Skills (35%)", m.skills_score),
            ("Experience (30%)", m.experience_score),
            ("Education (15%)", m.education_score),
            ("Location (10%)", m.location_score),
            ("Culture Fit (10%)", m.culture_fit_score),
        ]:
            lines.append(f"| {label} | {score:.0f} | {_score_bar(score, 15)} |")
        lines.append("")

        # Skills breakdown
        if m.mandatory_skills_total > 0 or m.preferred_skills_total > 0:
            lines.append("### Skills Analysis")
            lines.append("")
            lines.append(f"- **Mandatory:** {m.mandatory_skills_met}/{m.mandatory_skills_total} met")
            lines.append(f"- **Preferred:** {m.preferred_skills_met}/{m.preferred_skills_total} met")
            if m.missing_skills:
                lines.append(f"- **Missing:** {', '.join(m.missing_skills)}")
            lines.append("")

        # Strengths & concerns
        if m.top_strengths:
            lines.append("### Strengths")
            lines.append("")
            for s in m.top_strengths:
                lines.append(f"- {s}")
            lines.append("")

        if m.top_concerns:
            lines.append("### Concerns")
            lines.append("")
            for concern in m.top_concerns:
                lines.append(f"- {concern}")
            lines.append("")

    # ---- Tailoring ----
    if c.tailoring:
        lines.append("## Tailored Resume")
        lines.append("")
        lines.append(f"- **Total Changes:** {c.tailoring.total_changes}")
        if c.tailoring.changes_by_category:
            parts = [
                f"{cat}: {count}"
                for cat, count in c.tailoring.changes_by_category.items()
            ]
            lines.append(f"- **By Category:** {', '.join(parts)}")
        if c.tailoring.docx_path:
            lines.append(f"- **Document:** `{c.tailoring.docx_path}`")
        lines.append("")

    # ---- Reply ----
    if c.reply:
        reply_icon = _REPLY_ICON.get(c.reply.status, "")
        lines.append("## Reply Status")
        lines.append("")
        lines.append(f"- **Status:** {reply_icon} {c.reply.status.value.replace('_', ' ').title()}")
        lines.append(f"- **To:** {c.reply.to}")
        lines.append(f"- **Subject:** {c.reply.subject}")
        if c.reply.has_attachments:
            lines.append(f"- **Attachments:** {c.reply.attachment_count}")
        if c.reply.gmail_message_id:
            lines.append(f"- **Gmail ID:** `{c.reply.gmail_message_id}`")
        if c.reply.error:
            lines.append(f"- **Error:** {c.reply.error}")
        if c.reply.body_preview:
            lines.append("")
            lines.append("**Email Preview:**")
            lines.append("")
            lines.append(f"> {c.reply.body_preview.replace(chr(10), chr(10) + '> ')}")
        lines.append("")

    # ---- Timeline ----
    lines.append("## Timeline")
    lines.append("")
    events = [
        ("Email Received", c.email_received_at),
        ("Matched", c.matched_at),
        ("Resume Tailored", c.tailored_at),
        ("Reply Sent", c.replied_at),
    ]
    for label, ts in events:
        if ts:
            lines.append(f"- **{label}:** {ts}")
    if not any(ts for _, ts in events):
        lines.append("- No timeline events recorded")
    lines.append("")

    # ---- Footer ----
    lines.append("---")
    lines.append(f"*Job ID: `{c.job_id}`*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Batch rendering
# ---------------------------------------------------------------------------

def render_correlation_report(
    summary: CorrelationSummary,
    correlated: List[CorrelatedOpportunity],
    include_cards: bool = False,
) -> str:
    """Render the full correlation report: summary + optional detailed cards.

    When *include_cards* is ``True``, individual opportunity cards are
    appended after the summary for a single-file comprehensive report.
    """
    parts = [render_correlation_summary(summary, correlated)]

    if include_cards and correlated:
        parts.append("\n---\n")
        parts.append("# Detailed Opportunity Cards\n")
        for c in correlated:
            parts.append(render_opportunity_card(c))
            parts.append("\n---\n")

    return "\n".join(parts)
