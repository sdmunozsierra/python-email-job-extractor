"""Shared helpers for loading pipeline artifacts into Streamlit session state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _read_json(path: Path) -> Any:
    """Read a JSON file and return its parsed content."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_messages(path: Path) -> List[Dict[str, Any]]:
    """Load raw email messages from a messages JSON file."""
    data = _read_json(path)
    if data is None:
        return []
    return data.get("messages", [])


def load_opportunities(path: Path) -> List[Dict[str, Any]]:
    """Load extracted opportunities from an opportunities JSON file."""
    data = _read_json(path)
    if data is None:
        return []
    return data.get("opportunities", [])


def load_match_results(path: Path) -> List[Dict[str, Any]]:
    """Load match results from a match_results JSON file."""
    data = _read_json(path)
    if data is None:
        return []
    return data.get("match_results", [])


def load_analytics(path: Path) -> Optional[Dict[str, Any]]:
    """Load analytics data."""
    return _read_json(path)


def load_drafts(path: Path) -> List[Dict[str, Any]]:
    """Load email drafts."""
    data = _read_json(path)
    if data is None:
        return []
    return data.get("drafts", [])


def load_reply_results(path: Path) -> List[Dict[str, Any]]:
    """Load reply results."""
    data = _read_json(path)
    if data is None:
        return []
    return data.get("reply_results", [])


def load_tailoring_results(path: Path) -> List[Dict[str, Any]]:
    """Load tailoring results."""
    data = _read_json(path)
    if data is None:
        return []
    return data.get("tailoring_results", [])


def load_correlation(path: Path) -> Dict[str, Any]:
    """Load correlation data."""
    data = _read_json(path)
    if data is None:
        return {}
    return data


def load_tracking(path: Path) -> Dict[str, Any]:
    """Load application tracking data."""
    data = _read_json(path)
    if data is None:
        return {}
    return data


def discover_artifacts(work_dir: Path, out_dir: Path) -> Dict[str, Path]:
    """Discover available pipeline artifacts from standard directory layout.

    Returns a dict mapping artifact name to its path (only includes
    artifacts that actually exist on disk).
    """
    candidates = {
        "messages": work_dir / "messages.json",
        "filtered": work_dir / "filtered.json",
        "opportunities": work_dir / "opportunities.json",
        "job_analyses": work_dir / "job_analyses.json",
        "analytics": work_dir / "analytics.json",
        "analytics_report": work_dir / "analytics_report.txt",
        "match_results": out_dir / "matches" / "match_results.json",
        "match_summary": out_dir / "matches" / "match_summary.md",
        "tailoring_results": out_dir / "tailored" / "tailoring_results.json",
        "tailoring_summary": out_dir / "tailored" / "tailoring_summary.md",
        "drafts": out_dir / "replies" / "drafts.json",
        "drafts_preview": out_dir / "replies" / "drafts_preview.md",
        "reply_results": out_dir / "replies" / "reply_results.json",
        "reply_report": out_dir / "replies" / "reply_report.md",
        "correlation": out_dir / "correlation" / "correlation.json",
        "correlation_summary": out_dir / "correlation" / "correlation_summary.md",
        "tracking": out_dir / "tracking" / "tracking.json",
        "tracking_summary": out_dir / "tracking" / "tracking_summary.md",
    }
    return {name: path for name, path in candidates.items() if path.exists()}
