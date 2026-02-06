"""
Data models for resume tailoring tracking and reporting.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ChangeCategory(enum.Enum):
    """Categories of resume changes."""

    SUMMARY = "summary"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    CERTIFICATIONS = "certifications"
    KEYWORDS = "keywords"
    EDUCATION = "education"
    PROJECTS = "projects"


@dataclass
class TailoringChange:
    """A single change made to the resume during tailoring.

    Captures what changed, why, and the before/after values so the user
    can review the diff.
    """

    category: ChangeCategory
    description: str
    reason: str
    before: Optional[str] = None
    after: Optional[str] = None
    section_index: Optional[int] = None  # e.g. experience[2]
    field_name: Optional[str] = None  # e.g. "achievements"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "description": self.description,
            "reason": self.reason,
            "before": self.before,
            "after": self.after,
            "section_index": self.section_index,
            "field_name": self.field_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TailoringChange":
        return cls(
            category=ChangeCategory(data.get("category", "skills")),
            description=data.get("description", ""),
            reason=data.get("reason", ""),
            before=data.get("before"),
            after=data.get("after"),
            section_index=data.get("section_index"),
            field_name=data.get("field_name"),
        )


@dataclass
class TailoringReport:
    """Complete report of all tailoring changes applied to a resume.

    Provides traceability: what was changed, why (match insight), and
    the category breakdown.
    """

    job_id: str
    job_title: str
    company: str
    resume_name: str
    match_score: float
    match_grade: str
    changes: List[TailoringChange] = field(default_factory=list)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    @property
    def total_changes(self) -> int:
        return len(self.changes)

    @property
    def changes_by_category(self) -> Dict[ChangeCategory, List[TailoringChange]]:
        grouped: Dict[ChangeCategory, List[TailoringChange]] = {}
        for change in self.changes:
            grouped.setdefault(change.category, []).append(change)
        return grouped

    @property
    def summary_changes(self) -> List[TailoringChange]:
        return [c for c in self.changes if c.category == ChangeCategory.SUMMARY]

    @property
    def skill_changes(self) -> List[TailoringChange]:
        return [c for c in self.changes if c.category == ChangeCategory.SKILLS]

    @property
    def experience_changes(self) -> List[TailoringChange]:
        return [c for c in self.changes if c.category == ChangeCategory.EXPERIENCE]

    @property
    def certification_changes(self) -> List[TailoringChange]:
        return [c for c in self.changes if c.category == ChangeCategory.CERTIFICATIONS]

    @property
    def keyword_changes(self) -> List[TailoringChange]:
        return [c for c in self.changes if c.category == ChangeCategory.KEYWORDS]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company": self.company,
            "resume_name": self.resume_name,
            "match_score": self.match_score,
            "match_grade": self.match_grade,
            "total_changes": self.total_changes,
            "changes_by_category": {
                cat.value: len(items)
                for cat, items in self.changes_by_category.items()
            },
            "changes": [c.to_dict() for c in self.changes],
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TailoringReport":
        timestamp = None
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass

        return cls(
            job_id=data.get("job_id", ""),
            job_title=data.get("job_title", ""),
            company=data.get("company", ""),
            resume_name=data.get("resume_name", ""),
            match_score=data.get("match_score", 0),
            match_grade=data.get("match_grade", ""),
            changes=[TailoringChange.from_dict(c) for c in data.get("changes", [])],
            timestamp=timestamp,
        )


@dataclass
class TailoredResume:
    """Result of resume tailoring: the modified resume data, the generated
    document path (if built), and the full tailoring report.
    """

    resume_data: Dict[str, Any]  # Modified resume JSON schema dict
    report: TailoringReport
    docx_path: Optional[Path] = None
    original_data: Optional[Dict[str, Any]] = None  # Snapshot before changes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resume_data": self.resume_data,
            "report": self.report.to_dict(),
            "docx_path": str(self.docx_path) if self.docx_path else None,
        }
