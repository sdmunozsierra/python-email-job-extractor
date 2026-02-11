"""
Data models for job-application tracking.

Extends the pipeline beyond the REPLIED stage to track the full hiring
lifecycle: application sent, interviews, offers, and final outcomes.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Status and outcome enums
# ---------------------------------------------------------------------------

class ApplicationStatus(enum.Enum):
    """Post-reply application lifecycle stages."""

    APPLIED = "applied"             # Application sent, waiting for response
    INTERVIEWING = "interviewing"   # At least one interview scheduled/completed
    OFFERED = "offered"             # Offer received
    CLOSED = "closed"               # Final outcome reached


class FinalOutcome(enum.Enum):
    """Terminal outcomes for a closed application."""

    ACCEPTED = "accepted"
    DECLINED = "declined"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    GHOSTED = "ghosted"


class InterviewType(enum.Enum):
    """Common interview types."""

    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    HIRING_MANAGER = "hiring_manager"
    PANEL = "panel"
    ONSITE = "onsite"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Interview record
# ---------------------------------------------------------------------------

@dataclass
class InterviewRecord:
    """Records a single interview event."""

    interview_type: InterviewType = InterviewType.OTHER
    scheduled_at: Optional[str] = None
    completed: bool = False
    interviewer_name: Optional[str] = None
    interviewer_title: Optional[str] = None
    notes: Optional[str] = None
    round_number: int = 1
    created_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interview_type": self.interview_type.value,
            "scheduled_at": self.scheduled_at,
            "completed": self.completed,
            "interviewer_name": self.interviewer_name,
            "interviewer_title": self.interviewer_title,
            "notes": self.notes,
            "round_number": self.round_number,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewRecord":
        type_str = data.get("interview_type", "other")
        try:
            interview_type = InterviewType(type_str)
        except ValueError:
            interview_type = InterviewType.OTHER

        return cls(
            interview_type=interview_type,
            scheduled_at=data.get("scheduled_at"),
            completed=data.get("completed", False),
            interviewer_name=data.get("interviewer_name"),
            interviewer_title=data.get("interviewer_title"),
            notes=data.get("notes"),
            round_number=data.get("round_number", 1),
            created_at=data.get("created_at"),
        )


# ---------------------------------------------------------------------------
# Offer details
# ---------------------------------------------------------------------------

@dataclass
class OfferDetails:
    """Captures an offer from a company."""

    salary: Optional[str] = None
    equity: Optional[str] = None
    bonus: Optional[str] = None
    benefits_notes: Optional[str] = None
    start_date: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None
    received_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "salary": self.salary,
            "equity": self.equity,
            "bonus": self.bonus,
            "benefits_notes": self.benefits_notes,
            "start_date": self.start_date,
            "expiry_date": self.expiry_date,
            "notes": self.notes,
            "received_at": self.received_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OfferDetails":
        return cls(
            salary=data.get("salary"),
            equity=data.get("equity"),
            bonus=data.get("bonus"),
            benefits_notes=data.get("benefits_notes"),
            start_date=data.get("start_date"),
            expiry_date=data.get("expiry_date"),
            notes=data.get("notes"),
            received_at=data.get("received_at"),
        )


# ---------------------------------------------------------------------------
# Status change (audit trail entry)
# ---------------------------------------------------------------------------

@dataclass
class StatusChange:
    """An audit-log entry recording a status transition."""

    from_status: str = ""
    to_status: str = ""
    timestamp: str = ""
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_status": self.from_status,
            "to_status": self.to_status,
            "timestamp": self.timestamp,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusChange":
        return cls(
            from_status=data.get("from_status", ""),
            to_status=data.get("to_status", ""),
            timestamp=data.get("timestamp", ""),
            note=data.get("note"),
        )


# ---------------------------------------------------------------------------
# Core: Tracked Application
# ---------------------------------------------------------------------------

@dataclass
class TrackedApplication:
    """A single job application being tracked through the hiring process.

    Links back to the pipeline's correlation data by ``job_id`` and adds
    mutable status, interview records, offer details, notes, and a full
    status-change audit trail.
    """

    # --- Identity (carried from correlation) ---
    job_id: str = ""
    job_title: str = ""
    company: str = ""
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None

    # --- Current status ---
    status: ApplicationStatus = ApplicationStatus.APPLIED
    final_outcome: Optional[FinalOutcome] = None

    # --- Match context (snapshot) ---
    match_score: Optional[float] = None
    match_grade: Optional[str] = None

    # --- Sub-records ---
    interviews: List[InterviewRecord] = field(default_factory=list)
    offer: Optional[OfferDetails] = None

    # --- User notes ---
    notes: List[str] = field(default_factory=list)

    # --- Audit trail ---
    status_history: List[StatusChange] = field(default_factory=list)

    # --- Timestamps ---
    applied_at: Optional[str] = None
    last_updated_at: Optional[str] = None
    closed_at: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """True unless the application has reached a final outcome."""
        return self.status != ApplicationStatus.CLOSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company": self.company,
            "recruiter_name": self.recruiter_name,
            "recruiter_email": self.recruiter_email,
            "status": self.status.value,
            "final_outcome": self.final_outcome.value if self.final_outcome else None,
            "match_score": self.match_score,
            "match_grade": self.match_grade,
            "interviews": [i.to_dict() for i in self.interviews],
            "offer": self.offer.to_dict() if self.offer else None,
            "notes": list(self.notes),
            "status_history": [s.to_dict() for s in self.status_history],
            "applied_at": self.applied_at,
            "last_updated_at": self.last_updated_at,
            "closed_at": self.closed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackedApplication":
        status_str = data.get("status", "applied")
        try:
            status = ApplicationStatus(status_str)
        except ValueError:
            status = ApplicationStatus.APPLIED

        outcome_str = data.get("final_outcome")
        final_outcome = None
        if outcome_str:
            try:
                final_outcome = FinalOutcome(outcome_str)
            except ValueError:
                pass

        interviews = [
            InterviewRecord.from_dict(i)
            for i in (data.get("interviews") or [])
        ]
        offer_data = data.get("offer")
        offer = OfferDetails.from_dict(offer_data) if offer_data else None

        history = [
            StatusChange.from_dict(s)
            for s in (data.get("status_history") or [])
        ]

        return cls(
            job_id=data.get("job_id", ""),
            job_title=data.get("job_title", ""),
            company=data.get("company", ""),
            recruiter_name=data.get("recruiter_name"),
            recruiter_email=data.get("recruiter_email"),
            status=status,
            final_outcome=final_outcome,
            match_score=data.get("match_score"),
            match_grade=data.get("match_grade"),
            interviews=interviews,
            offer=offer,
            notes=data.get("notes", []) or [],
            status_history=history,
            applied_at=data.get("applied_at"),
            last_updated_at=data.get("last_updated_at"),
            closed_at=data.get("closed_at"),
        )


# ---------------------------------------------------------------------------
# Tracking Summary (aggregate statistics)
# ---------------------------------------------------------------------------

@dataclass
class TrackingSummary:
    """Aggregate statistics across all tracked applications."""

    total_tracked: int = 0

    # Status breakdown
    by_status: Dict[str, int] = field(default_factory=dict)
    by_outcome: Dict[str, int] = field(default_factory=dict)
    active_count: int = 0

    # Activity
    total_interviews: int = 0
    offers_received: int = 0

    # Match context
    avg_match_score: float = 0.0

    # Top companies
    top_companies: List[Dict[str, Any]] = field(default_factory=list)

    # Timestamp
    generated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tracked": self.total_tracked,
            "by_status": dict(self.by_status),
            "by_outcome": dict(self.by_outcome),
            "active_count": self.active_count,
            "total_interviews": self.total_interviews,
            "offers_received": self.offers_received,
            "avg_match_score": round(self.avg_match_score, 1),
            "top_companies": self.top_companies,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackingSummary":
        return cls(
            total_tracked=data.get("total_tracked", 0),
            by_status=data.get("by_status", {}),
            by_outcome=data.get("by_outcome", {}),
            active_count=data.get("active_count", 0),
            total_interviews=data.get("total_interviews", 0),
            offers_received=data.get("offers_received", 0),
            avg_match_score=data.get("avg_match_score", 0.0),
            top_companies=data.get("top_companies", []),
            generated_at=data.get("generated_at"),
        )
