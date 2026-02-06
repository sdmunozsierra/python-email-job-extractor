"""
Report renderer for the recruiter reply feature.

Generates Markdown reports summarising composed drafts and send results
so the user can review what was (or will be) sent.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from .models import EmailDraft, ReplyResult, ReplyStatus


def _status_icon(status: ReplyStatus) -> str:
    mapping = {
        ReplyStatus.DRAFT: "📝",
        ReplyStatus.DRY_RUN: "👁️",
        ReplyStatus.SENT: "✅",
        ReplyStatus.FAILED: "❌",
    }
    return mapping.get(status, "❓")


def _render_recipient_lines(draft: EmailDraft) -> List[str]:
    """Build Markdown lines showing To / CC / BCC (and original To if overridden)."""
    lines: List[str] = []
    lines.append(f"**To:** {draft.to}")
    if draft.original_to:
        lines.append(f"**Original To:** {draft.original_to} *(overridden)*")
    if draft.cc:
        lines.append(f"**CC:** {', '.join(draft.cc)}")
    if draft.bcc:
        lines.append(f"**BCC:** {', '.join(draft.bcc)}")
    return lines


def render_draft_preview(draft: EmailDraft) -> str:
    """Render a single email draft as a readable Markdown preview.

    This is the primary output of the ``--dry-run`` mode so the user
    can review the email before sending.
    """
    lines: List[str] = []

    lines.append(f"# Email Draft: {draft.job_title} at {draft.company}")
    lines.append("")
    lines.extend(_render_recipient_lines(draft))
    if draft.recruiter_name:
        lines.append(f"**Recruiter:** {draft.recruiter_name}")
    lines.append(f"**Subject:** {draft.subject}")

    if draft.match_score is not None:
        lines.append(f"**Match Score:** {draft.match_score:.0f}/100 ({draft.match_grade or 'N/A'})")

    if draft.attachment_paths:
        lines.append(f"**Attachments:** {len(draft.attachment_paths)}")
        for p in draft.attachment_paths:
            lines.append(f"  - `{p}`")

    if draft.in_reply_to:
        lines.append(f"**In-Reply-To:** `{draft.in_reply_to}`")
    if draft.thread_id:
        lines.append(f"**Thread ID:** `{draft.thread_id}`")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Email Body")
    lines.append("")
    lines.append(draft.body_text)
    lines.append("")
    lines.append("---")

    return "\n".join(lines)


def render_batch_preview(drafts: List[EmailDraft]) -> str:
    """Render a summary of all composed drafts (for batch dry-run)."""
    lines: List[str] = []

    lines.append("# Recruiter Reply Drafts")
    lines.append("")
    lines.append(f"**Total drafts:** {len(drafts)}")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    # Show global override/CC/BCC if all drafts share the same values
    any_overridden = any(d.original_to for d in drafts)
    if any_overridden:
        lines.append(f"**Recipient Override Active**")

    lines.append("")

    # Summary table
    lines.append("| # | Company | Role | To | Score | Attachments |")
    lines.append("|---|---------|------|----|-------|-------------|")

    for i, d in enumerate(drafts, 1):
        score = f"{d.match_score:.0f}" if d.match_score is not None else "N/A"
        att_count = len(d.attachment_paths)
        to_display = d.to[:30]
        if d.original_to:
            to_display = f"{d.to[:20]} *(was {d.original_to[:15]})*"
        lines.append(
            f"| {i} | {d.company[:20]} | {d.job_title[:30]} | "
            f"{to_display} | {score} | {att_count} |"
        )

    lines.append("")

    # Individual previews
    for i, d in enumerate(drafts, 1):
        lines.append(f"---")
        lines.append("")
        lines.append(f"## Draft {i}: {d.job_title} at {d.company}")
        lines.append("")
        lines.extend(_render_recipient_lines(d))
        lines.append(f"**Subject:** {d.subject}")
        lines.append("")
        lines.append("```")
        lines.append(d.body_text)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def render_send_report(results: List[ReplyResult]) -> str:
    """Render a report of send results (or dry-run results)."""
    lines: List[str] = []

    sent = sum(1 for r in results if r.status == ReplyStatus.SENT)
    dry = sum(1 for r in results if r.status == ReplyStatus.DRY_RUN)
    failed = sum(1 for r in results if r.status == ReplyStatus.FAILED)

    is_dry_run = dry > 0 and sent == 0

    title = "Recruiter Reply Report (DRY RUN)" if is_dry_run else "Recruiter Reply Report"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Total:** {len(results)}")
    if sent:
        lines.append(f"**Sent:** {sent}")
    if dry:
        lines.append(f"**Previewed (dry run):** {dry}")
    if failed:
        lines.append(f"**Failed:** {failed}")
    lines.append(f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Results table
    lines.append("| # | Status | Company | Role | To | Gmail ID |")
    lines.append("|---|--------|---------|------|----|----------|")

    for i, r in enumerate(results, 1):
        icon = _status_icon(r.status)
        d = r.draft
        gid = r.gmail_message_id or "-"
        lines.append(
            f"| {i} | {icon} {r.status.value} | {d.company[:20]} | "
            f"{d.job_title[:25]} | {d.to[:30]} | {gid[:12]} |"
        )

    lines.append("")

    # Errors section
    errors = [r for r in results if r.error]
    if errors:
        lines.append("## Errors")
        lines.append("")
        for r in errors:
            lines.append(f"- **{r.draft.company} / {r.draft.job_title}:** {r.error}")
        lines.append("")

    # Details
    lines.append("## Details")
    lines.append("")
    for i, r in enumerate(results, 1):
        d = r.draft
        icon = _status_icon(r.status)
        lines.append(f"### {i}. {icon} {d.job_title} at {d.company}")
        lines.extend(_render_recipient_lines(d))
        lines.append(f"**Subject:** {d.subject}")
        lines.append(f"**Status:** {r.status.value}")
        if r.gmail_message_id:
            lines.append(f"**Gmail Message ID:** `{r.gmail_message_id}`")
        if d.attachment_paths:
            lines.append(f"**Attachments:**")
            for p in d.attachment_paths:
                lines.append(f"  - `{p}`")
        lines.append("")
        lines.append("**Body:**")
        lines.append("```")
        lines.append(d.body_text)
        lines.append("```")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Report generated at: {datetime.now(timezone.utc).isoformat()}*")

    return "\n".join(lines)
