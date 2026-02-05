from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


def _bullets(items: List[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def _pay_str(pay: Dict) -> str:
    if not pay:
        return "(not provided)"
    mn, mx = pay.get("min"), pay.get("max")
    cur, unit = pay.get("currency"), pay.get("unit")
    notes = pay.get("notes")
    if mn is None and mx is None:
        return notes or "(not provided)"
    rng = f"{mn if mn is not None else ''}-{mx if mx is not None else ''}".strip("-")
    tail = " ".join([x for x in [cur, f"/ {unit}" if unit else None] if x])
    return (rng + (" " + tail if tail else "")).strip() or (notes or "(not provided)")


def _yaml_list(items: List[str], indent: int = 0) -> str:
    pad = " " * indent
    if not items:
        return f"{pad}- (none)"
    return "\n".join([f"{pad}- {item}" for item in items])


def _needs_clarification(job: Dict) -> List[str]:
    missing = set(job.get("missing_fields", []) or [])
    needs: List[str] = []
    if "locations" in missing:
        needs.append("location")
    if "mandatory_skills" in missing:
        needs.append("skills")
    if not job.get("apply_link"):
        needs.append("apply_link")

    for option in job.get("engagement_options", []) or []:
        pay = option.get("pay", {}) or {}
        if pay.get("min") is None and pay.get("max") is None:
            needs.append("salary_range")
            break

    return sorted(set(needs))


def _frontmatter(job: Dict) -> str:
    source = job.get("source_email", {}) or {}
    created_at = datetime.now(tz=timezone.utc).isoformat()
    engagement_types = [opt.get("type") for opt in job.get("engagement_options", []) or [] if opt.get("type")]
    needs = _needs_clarification(job)

    lines = [
        "---",
        f'opportunity_id: "{source.get("message_id")}"',
        f'source_message_id: "{source.get("message_id")}"',
        f'thread_id: "{source.get("thread_id") or ""}"',
        'status: "new"',
        f'created_at: "{created_at}"',
        "tags:",
        _yaml_list(["job-opportunity"], indent=2),
        "engagement_types:",
        _yaml_list(engagement_types, indent=2),
        "needs_clarification:",
        _yaml_list(needs, indent=2),
        "---",
        "",
    ]
    return "\n".join(lines)


def render_markdown(job: Dict) -> str:
    source = job.get("source_email", {}) or {}
    title = job.get("job_title") or "Job opportunity"

    lines: List[str] = []
    lines.append(_frontmatter(job))
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Company:** {job.get('company') or '(unknown)'}  ")
    lines.append(
        f"**Recruiter:** {job.get('recruiter_name') or '(unknown)'}"
        f" ({job.get('recruiter_company') or '(unknown)'})  "
    )
    lines.append(
        f"**Contact:** {job.get('recruiter_email') or '(unknown)'}"
        f" | {job.get('recruiter_phone') or '(unknown)'}  "
    )
    lines.append(f"**Socials:** {', '.join(job.get('social_links') or []) or '(none)'}  ")
    lines.append("")

    lines.append("## Summary")
    lines.append(f"- **Locations:** {', '.join(job.get('locations') or []) or '(unknown)'}")
    lines.append(f"- **Remote:** {job.get('remote')} | **Hybrid:** {job.get('hybrid')}")
    if job.get("summary"):
        lines.append(f"- **Notes:** {job.get('summary')}")
    lines.append(f"- **Apply link:** {job.get('apply_link') or '(not provided)'}")
    lines.append(f"- **Confidence:** {job.get('confidence')}")
    lines.append("")

    lines.append("## Engagement options")
    for idx, option in enumerate(job.get("engagement_options", []) or [], start=1):
        lines.append(f"### Option {idx}: {option.get('type')}")
        if option.get("duration"):
            lines.append(f"- **Duration:** {option.get('duration')}")
        lines.append(f"- **Pay:** {_pay_str(option.get('pay') or {})}")
        if option.get("benefits_notes"):
            lines.append(f"- **Benefits/Notes:** {option.get('benefits_notes')}")
        lines.append(f"- **Constraints:**\n{_bullets(option.get('constraints') or [])}")
        if len(job.get("engagement_options", []) or []) > 1:
            lines.append(
                "- **Differences vs other option(s):**\n"
                f"{_bullets(option.get('differences_vs_other_options') or [])}"
            )
        lines.append(f"- **Evidence:**\n{_bullets(option.get('evidence') or [])}")
        lines.append("")

    lines.append("## Hard requirements")
    lines.append(_bullets(job.get("hard_requirements") or []))
    lines.append("")
    lines.append("## Mandatory skills")
    lines.append(_bullets(job.get("mandatory_skills") or []))
    lines.append("")
    lines.append("## Preferred skills")
    lines.append(_bullets(job.get("preferred_skills") or []))
    lines.append("")
    lines.append("## Responsibilities")
    lines.append(_bullets(job.get("responsibilities") or []))
    lines.append("")
    lines.append("## Qualifications")
    lines.append(_bullets(job.get("qualifications") or []))
    lines.append("")
    lines.append("## Evidence (from email)")
    lines.append(_bullets(job.get("evidence") or []))
    lines.append("")
    lines.append("## Source")
    lines.append(f"- **Message-ID:** {source.get('message_id')}")
    lines.append(f"- **Subject:** {source.get('subject')}")
    lines.append(f"- **From:** {source.get('from')}")
    lines.append(f"- **Date:** {source.get('date')}")
    lines.append("")
    lines.append("## Missing fields")
    lines.append(_bullets(job.get("missing_fields") or []))

    return "\n".join(lines).strip() + "\n"
