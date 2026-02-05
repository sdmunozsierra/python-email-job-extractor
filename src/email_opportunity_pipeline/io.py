from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, TYPE_CHECKING

from .models import EmailMessage

if TYPE_CHECKING:
    from .matching.models import Resume, MatchResult


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
