"""
Resume Tailoring Report renderer.

Generates detailed Markdown reports documenting every change made
during tailoring -- primarily experience, skills, and certifications.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import (
    ChangeCategory,
    TailoredResume,
    TailoringChange,
    TailoringReport,
)


def _category_emoji(category: ChangeCategory) -> str:
    mapping = {
        ChangeCategory.SUMMARY: "📝",
        ChangeCategory.SKILLS: "🔧",
        ChangeCategory.EXPERIENCE: "💼",
        ChangeCategory.CERTIFICATIONS: "🏅",
        ChangeCategory.KEYWORDS: "🔑",
        ChangeCategory.EDUCATION: "🎓",
        ChangeCategory.PROJECTS: "📂",
    }
    return mapping.get(category, "📋")


def _grade_emoji(grade: str) -> str:
    mapping = {
        "excellent": "🟢",
        "good": "🟡",
        "fair": "🟠",
        "poor": "🔴",
        "unqualified": "⛔",
    }
    return mapping.get(grade, "❓")


def render_tailoring_report(report: TailoringReport) -> str:
    """Render a single tailoring report as Markdown.

    The report is structured by change category so reviewers can quickly
    see what was modified in experience, skills, and certifications.

    Args:
        report: TailoringReport to render.

    Returns:
        Formatted Markdown string.
    """
    lines: List[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f'job_id: "{report.job_id}"')
    lines.append(f'job_title: "{report.job_title}"')
    lines.append(f'company: "{report.company}"')
    lines.append(f"match_score: {report.match_score}")
    lines.append(f'match_grade: "{report.match_grade}"')
    lines.append(f"total_changes: {report.total_changes}")
    lines.append(f'timestamp: "{report.timestamp.isoformat() if report.timestamp else ""}"')
    lines.append("---")
    lines.append("")

    # Title
    lines.append(f"# Tailoring Report: {report.job_title} at {report.company}")
    lines.append("")

    # Overview
    lines.append("## Overview")
    lines.append("")
    lines.append(f"**Candidate:** {report.resume_name}")
    lines.append(f"**Match Score:** {report.match_score:.0f}/100 {_grade_emoji(report.match_grade)} {report.match_grade.title()}")
    lines.append(f"**Total Changes:** {report.total_changes}")
    lines.append("")

    # Category summary table
    by_cat = report.changes_by_category
    if by_cat:
        lines.append("### Changes by Category")
        lines.append("")
        lines.append("| Category | Changes |")
        lines.append("|----------|---------|")
        for cat in ChangeCategory:
            count = len(by_cat.get(cat, []))
            if count > 0:
                lines.append(f"| {_category_emoji(cat)} {cat.value.title()} | {count} |")
        lines.append("")

    # Detailed changes by category (experience, skills, certs are primary)
    _render_category_section(lines, by_cat, ChangeCategory.EXPERIENCE, "Experience Changes")
    _render_category_section(lines, by_cat, ChangeCategory.SKILLS, "Skills Changes")
    _render_category_section(lines, by_cat, ChangeCategory.CERTIFICATIONS, "Certification Changes")
    _render_category_section(lines, by_cat, ChangeCategory.SUMMARY, "Summary Changes")
    _render_category_section(lines, by_cat, ChangeCategory.KEYWORDS, "Keyword Analysis")
    _render_category_section(lines, by_cat, ChangeCategory.EDUCATION, "Education Changes")
    _render_category_section(lines, by_cat, ChangeCategory.PROJECTS, "Project Changes")

    # Footer
    lines.append("---")
    lines.append("")
    ts = report.timestamp.isoformat() if report.timestamp else "Unknown"
    lines.append(f"*Report generated at: {ts}*")

    return "\n".join(lines)


def _render_category_section(
    lines: List[str],
    by_cat: Dict[ChangeCategory, List[TailoringChange]],
    category: ChangeCategory,
    heading: str,
) -> None:
    """Render a section for a single change category."""
    changes = by_cat.get(category, [])
    if not changes:
        return

    emoji = _category_emoji(category)
    lines.append(f"## {emoji} {heading}")
    lines.append("")

    for i, change in enumerate(changes, 1):
        lines.append(f"### Change {i}: {change.description}")
        lines.append("")
        lines.append(f"**Reason:** {change.reason}")
        lines.append("")

        if change.before is not None:
            lines.append("**Before:**")
            lines.append(f"> {change.before}")
            lines.append("")

        if change.after is not None:
            lines.append("**After:**")
            lines.append(f"> {change.after}")
            lines.append("")

        if change.section_index is not None:
            lines.append(f"*Section index: {change.section_index}*")
        if change.field_name:
            lines.append(f"*Field: {change.field_name}*")
        lines.append("")


def render_tailoring_summary(tailored_resumes: List[TailoredResume]) -> str:
    """Render a summary report across multiple tailored resumes.

    Useful when tailoring the same resume for many job opportunities
    in a batch run.

    Args:
        tailored_resumes: List of TailoredResume objects.

    Returns:
        Formatted Markdown summary string.
    """
    lines: List[str] = []

    lines.append("# Resume Tailoring Summary")
    lines.append("")
    lines.append(f"**Total Jobs Tailored:** {len(tailored_resumes)}")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Summary table
    lines.append("## Tailored Resumes")
    lines.append("")
    lines.append("| # | Job Title | Company | Match | Changes | .docx |")
    lines.append("|---|-----------|---------|-------|---------|-------|")

    for i, tr in enumerate(tailored_resumes, 1):
        r = tr.report
        grade_em = _grade_emoji(r.match_grade)
        docx_status = "Yes" if tr.docx_path else "No"
        lines.append(
            f"| {i} | {r.job_title[:30]} | {r.company[:20]} | "
            f"{grade_em} {r.match_score:.0f} | {r.total_changes} | {docx_status} |"
        )

    lines.append("")

    # Aggregate stats
    total_changes = sum(tr.report.total_changes for tr in tailored_resumes)
    cat_totals: Dict[str, int] = {}
    for tr in tailored_resumes:
        for cat, changes in tr.report.changes_by_category.items():
            cat_totals[cat.value] = cat_totals.get(cat.value, 0) + len(changes)

    lines.append("## Aggregate Statistics")
    lines.append("")
    lines.append(f"**Total changes across all resumes:** {total_changes}")
    lines.append("")

    if cat_totals:
        lines.append("| Category | Total Changes |")
        lines.append("|----------|---------------|")
        for cat_name, count in sorted(cat_totals.items(), key=lambda x: -x[1]):
            lines.append(f"| {cat_name.title()} | {count} |")
        lines.append("")

    # Per-job detail snippets
    lines.append("## Per-Job Highlights")
    lines.append("")

    for i, tr in enumerate(tailored_resumes, 1):
        r = tr.report
        lines.append(f"### {i}. {r.job_title} at {r.company}")
        lines.append(f"Match: {r.match_score:.0f}/100 ({r.match_grade})")
        lines.append("")

        # Show first few changes as highlights
        for change in r.changes[:3]:
            lines.append(f"- {_category_emoji(change.category)} {change.description}")
        if r.total_changes > 3:
            lines.append(f"- ... and {r.total_changes - 3} more changes")
        lines.append("")

        if tr.docx_path:
            lines.append(f"Generated: `{tr.docx_path}`")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Summary generated at: {datetime.now(timezone.utc).isoformat()}*")

    return "\n".join(lines)
