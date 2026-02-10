from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, TYPE_CHECKING

from .models import EmailMessage

if TYPE_CHECKING:
    from .matching.models import Resume, MatchResult
    from .reply.models import EmailDraft, QuestionnaireConfig, ReplyResult


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def write_messages(path: str | Path, messages: Iterable[EmailMessage]) -> None:
    data = [m.to_dict() for m in messages]
    payload = {
        "fetched_at_utc": _utc_now_iso(),
        "count": len(data),
        "messages": data,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_messages(path: str | Path) -> List[EmailMessage]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    messages = raw.get("messages", []) or []
    return [EmailMessage.from_dict(m) for m in messages]


def write_opportunities(path: str | Path, opportunities: List[Dict[str, Any]]) -> None:
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(opportunities),
        "opportunities": opportunities,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_opportunities(path: str | Path) -> List[Dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw.get("opportunities", []) or []


# Resume I/O

def read_resume(path: str | Path) -> "Resume":
    """
    Read a resume file (JSON or Markdown).
    
    Args:
        path: Path to the resume file
        
    Returns:
        Resume object
    """
    from .matching.resume_parser import parse_resume_file
    return parse_resume_file(path)


def write_resume(path: str | Path, resume: "Resume") -> None:
    """
    Write a resume to a JSON file.
    
    Args:
        path: Output path
        resume: Resume object
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        "resume": resume.to_dict(),
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# Match Result I/O

def write_match_results(
    path: str | Path,
    results: List["MatchResult"],
    resume_id: str | None = None,
) -> None:
    """
    Write match results to a JSON file.
    
    Args:
        path: Output path
        results: List of MatchResult objects
        resume_id: Optional resume identifier
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        "resume_id": resume_id,
        "count": len(results),
        "match_results": [r.to_dict() for r in results],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_match_results(path: str | Path) -> List["MatchResult"]:
    """
    Read match results from a JSON file.
    
    Args:
        path: Path to the match results file
        
    Returns:
        List of MatchResult objects
    """
    from .matching.models import MatchResult
    
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    results_data = raw.get("match_results", []) or []
    return [MatchResult.from_dict(r) for r in results_data]


def write_single_match_result(path: str | Path, result: "MatchResult") -> None:
    """
    Write a single match result to a JSON file.
    
    Args:
        path: Output path
        result: MatchResult object
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        **result.to_dict(),
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# Job Analysis I/O

def write_job_analyses(
    path: str | Path,
    analyses: List[Dict[str, Any]],
) -> None:
    """
    Write job analyses to a JSON file.
    
    Args:
        path: Output path
        analyses: List of job analysis dictionaries
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(analyses),
        "analyses": analyses,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_job_analyses(path: str | Path) -> List[Dict[str, Any]]:
    """
    Read job analyses from a JSON file.
    
    Args:
        path: Path to the analyses file
        
    Returns:
        List of job analysis dictionaries
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw.get("analyses", []) or []


# Tailoring I/O

def write_tailoring_report(
    path: str | Path,
    report_data: Dict[str, Any],
) -> None:
    """
    Write a tailoring report to a JSON file.

    Args:
        path: Output path
        report_data: Tailoring report dict (from TailoringReport.to_dict())
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        **report_data,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_tailoring_results(
    path: str | Path,
    results: List[Dict[str, Any]],
) -> None:
    """
    Write batch tailoring results to a JSON file.

    Args:
        path: Output path
        results: List of tailoring result dicts
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(results),
        "tailoring_results": results,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# =========================================================================
# Recruiter Reply I/O
# =========================================================================

def read_questionnaire(path: str | Path) -> "QuestionnaireConfig":
    """Read a questionnaire config from a JSON file.

    Args:
        path: Path to the questionnaire JSON file.

    Returns:
        QuestionnaireConfig object.
    """
    from .reply.models import QuestionnaireConfig

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return QuestionnaireConfig.from_dict(raw)


def write_questionnaire(path: str | Path, config: "QuestionnaireConfig") -> None:
    """Write a questionnaire config to a JSON file.

    Args:
        path: Output path.
        config: QuestionnaireConfig to serialise.
    """
    Path(path).write_text(
        json.dumps(config.to_dict(), indent=2),
        encoding="utf-8",
    )


def write_drafts(path: str | Path, drafts: List["EmailDraft"]) -> None:
    """Write a list of email drafts to a JSON file.

    Args:
        path: Output path.
        drafts: List of EmailDraft objects.
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(drafts),
        "drafts": [d.to_dict() for d in drafts],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_drafts(path: str | Path) -> List["EmailDraft"]:
    """Read email drafts from a JSON file.

    Args:
        path: Path to the drafts JSON file.

    Returns:
        List of EmailDraft objects.
    """
    from .reply.models import EmailDraft

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    drafts_data = raw.get("drafts", []) or []
    return [EmailDraft.from_dict(d) for d in drafts_data]


def write_reply_results(
    path: str | Path,
    results: List["ReplyResult"],
) -> None:
    """Write reply results (sent or dry-run) to a JSON file.

    Args:
        path: Output path.
        results: List of ReplyResult objects.
    """
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(results),
        "reply_results": [r.to_dict() for r in results],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_reply_results(path: str | Path) -> List["ReplyResult"]:
    """Read reply results from a JSON file.

    Args:
        path: Path to the reply results JSON file.

    Returns:
        List of ReplyResult objects.
    """
    from .reply.models import ReplyResult

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    results_data = raw.get("reply_results", []) or []
    return [ReplyResult.from_dict(r) for r in results_data]


# =========================================================================
# Correlation I/O
# =========================================================================

def write_correlation(
    path: str | Path,
    correlated: List[Any],
    summary: Any,
) -> None:
    """Write correlation results to a JSON file.

    Args:
        path: Output path.
        correlated: List of CorrelatedOpportunity objects (or dicts).
        summary: CorrelationSummary object (or dict).
    """
    items = [
        c.to_dict() if hasattr(c, "to_dict") else c for c in correlated
    ]
    summary_dict = summary.to_dict() if hasattr(summary, "to_dict") else summary
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(items),
        "summary": summary_dict,
        "correlated_opportunities": items,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_correlation(path: str | Path) -> Tuple[List[Any], Any]:
    """Read correlation results from a JSON file.

    Args:
        path: Path to the correlation JSON file.

    Returns:
        Tuple of (list of CorrelatedOpportunity, CorrelationSummary).
    """
    from .correlation.models import CorrelatedOpportunity, CorrelationSummary

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items_data = raw.get("correlated_opportunities", []) or []
    summary_data = raw.get("summary", {}) or {}

    correlated = [CorrelatedOpportunity.from_dict(d) for d in items_data]
    summary = CorrelationSummary.from_dict(summary_data)
    return correlated, summary


def read_tailoring_results(path: str | Path) -> List[Dict[str, Any]]:
    """Read tailoring results from a JSON file.

    Args:
        path: Path to the tailoring results JSON file.

    Returns:
        List of tailoring result dicts.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw.get("tailoring_results", []) or []


# =========================================================================
# Tracking I/O
# =========================================================================

def write_tracking(
    path: str | Path,
    applications: List[Any],
    summary: Any,
) -> None:
    """Write application tracking data to a JSON file.

    Args:
        path: Output path.
        applications: List of TrackedApplication objects (or dicts).
        summary: TrackingSummary object (or dict).
    """
    items = [
        a.to_dict() if hasattr(a, "to_dict") else a for a in applications
    ]
    summary_dict = summary.to_dict() if hasattr(summary, "to_dict") else summary
    payload = {
        "created_at_utc": _utc_now_iso(),
        "count": len(items),
        "summary": summary_dict,
        "tracked_applications": items,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_tracking(path: str | Path) -> Tuple[List[Any], Any]:
    """Read application tracking data from a JSON file.

    Args:
        path: Path to the tracking JSON file.

    Returns:
        Tuple of (list of TrackedApplication, TrackingSummary).
    """
    from .tracking.models import TrackedApplication, TrackingSummary

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items_data = raw.get("tracked_applications", []) or []
    summary_data = raw.get("summary", {}) or {}

    applications = [TrackedApplication.from_dict(d) for d in items_data]
    summary = TrackingSummary.from_dict(summary_data)
    return applications, summary
