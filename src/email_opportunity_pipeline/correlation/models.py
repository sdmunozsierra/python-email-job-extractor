"""
Data models for job-opportunity correlation.

Provides a unified view that links every pipeline artifact (email, opportunity,
match result, tailored resume, reply draft, reply result) for each job
opportunity, making it easy to see the complete lifecycle at a glance.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Opportunity pipeline status
# ---------------------------------------------------------------------------

class OpportunityStage(enum.Enum):
    """How far an opportunity has progressed through the pipeline."""

    FETCHED = "fetched"
    FILTERED = "filtered"
    EXTRACTED = "extracted"
    ANALYZED = "analyzed"
    MATCHED = "matched"
    TAILORED = "tailored"
    COMPOSED = "composed"
    REPLIED = "replied"
    # Post-reply tracking stages
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    CLOSED = "closed"


class ReplyOutcome(enum.Enum):
    """Simplified reply state for the correlation view."""

    NOT_STARTED = "not_started"
    DRAFTED = "drafted"
    DRY_RUN = "dry_run"
    SENT = "sent"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Email summary (lightweight view of the source email)
# ---------------------------------------------------------------------------

@dataclass
class EmailSummary:
    """Lightweight summary of the source email for the correlation view."""

    message_id: str
    thread_id: str = ""
    subject: str = ""
    from_address: str = ""
    date: str = ""
    snippet: str = ""
    labels: List[str] = field(default_factory=list)
    has_attachments: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "from": self.from_address,
            "date": self.date,
            "snippet": self.snippet,
            "labels": list(self.labels),
            "has_attachments": self.has_attachments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailSummary":
        return cls(
            message_id=data.get("message_id", ""),
            thread_id=data.get("thread_id", ""),
            subject=data.get("subject", ""),
            from_address=data.get("from", ""),
            date=data.get("date", ""),
            snippet=data.get("snippet", ""),
            labels=data.get("labels", []) or [],
            has_attachments=data.get("has_attachments", False),
        )


# ---------------------------------------------------------------------------
# Match summary (lightweight view of the match result)
# ---------------------------------------------------------------------------

@dataclass
class MatchSummary:
    """Lightweight summary of match result for the correlation view."""

    overall_score: float = 0.0
    match_grade: str = ""
    recommendation: str = ""
    skills_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    location_score: float = 0.0
    culture_fit_score: float = 0.0
    mandatory_skills_met: int = 0
    mandatory_skills_total: int = 0
    preferred_skills_met: int = 0
    preferred_skills_total: int = 0
    top_strengths: List[str] = field(default_factory=list)
    top_concerns: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "match_grade": self.match_grade,
            "recommendation": self.recommendation,
            "skills_score": self.skills_score,
            "experience_score": self.experience_score,
            "education_score": self.education_score,
            "location_score": self.location_score,
            "culture_fit_score": self.culture_fit_score,
            "mandatory_skills_met": self.mandatory_skills_met,
            "mandatory_skills_total": self.mandatory_skills_total,
            "preferred_skills_met": self.preferred_skills_met,
            "preferred_skills_total": self.preferred_skills_total,
            "top_strengths": list(self.top_strengths),
            "top_concerns": list(self.top_concerns),
            "missing_skills": list(self.missing_skills),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchSummary":
        return cls(
            overall_score=data.get("overall_score", 0.0),
            match_grade=data.get("match_grade", ""),
            recommendation=data.get("recommendation", ""),
            skills_score=data.get("skills_score", 0.0),
            experience_score=data.get("experience_score", 0.0),
            education_score=data.get("education_score", 0.0),
            location_score=data.get("location_score", 0.0),
            culture_fit_score=data.get("culture_fit_score", 0.0),
            mandatory_skills_met=data.get("mandatory_skills_met", 0),
            mandatory_skills_total=data.get("mandatory_skills_total", 0),
            preferred_skills_met=data.get("preferred_skills_met", 0),
            preferred_skills_total=data.get("preferred_skills_total", 0),
            top_strengths=data.get("top_strengths", []) or [],
            top_concerns=data.get("top_concerns", []) or [],
            missing_skills=data.get("missing_skills", []) or [],
        )


# ---------------------------------------------------------------------------
# Tailoring summary
# ---------------------------------------------------------------------------

@dataclass
class TailoringSummary:
    """Lightweight summary of tailoring result for the correlation view."""

    total_changes: int = 0
    changes_by_category: Dict[str, int] = field(default_factory=dict)
    docx_path: Optional[str] = None
    resume_json_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_changes": self.total_changes,
            "changes_by_category": dict(self.changes_by_category),
            "docx_path": self.docx_path,
            "resume_json_path": self.resume_json_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TailoringSummary":
        return cls(
            total_changes=data.get("total_changes", 0),
            changes_by_category=data.get("changes_by_category", {}),
            docx_path=data.get("docx_path"),
            resume_json_path=data.get("resume_json_path"),
        )


# ---------------------------------------------------------------------------
# Reply summary
# ---------------------------------------------------------------------------

@dataclass
class ReplySummary:
    """Lightweight summary of the reply draft and send result."""

    to: str = ""
    subject: str = ""
    body_preview: str = ""
    has_attachments: bool = False
    attachment_count: int = 0
    status: ReplyOutcome = ReplyOutcome.NOT_STARTED
    gmail_message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "to": self.to,
            "subject": self.subject,
            "body_preview": self.body_preview,
            "has_attachments": self.has_attachments,
            "attachment_count": self.attachment_count,
            "status": self.status.value,
            "gmail_message_id": self.gmail_message_id,
            "error": self.error,
            "sent_at": self.sent_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReplySummary":
        status_str = data.get("status", "not_started")
        try:
            status = ReplyOutcome(status_str)
        except ValueError:
            status = ReplyOutcome.NOT_STARTED

        return cls(
            to=data.get("to", ""),
            subject=data.get("subject", ""),
            body_preview=data.get("body_preview", ""),
            has_attachments=data.get("has_attachments", False),
            attachment_count=data.get("attachment_count", 0),
            status=status,
            gmail_message_id=data.get("gmail_message_id"),
            error=data.get("error"),
            sent_at=data.get("sent_at"),
        )


# ---------------------------------------------------------------------------
# Core: Correlated Opportunity
# ---------------------------------------------------------------------------

@dataclass
class CorrelatedOpportunity:
    """A unified view of a single job opportunity across the entire pipeline.

    Links together the source email, extracted opportunity data, match result,
    tailored resume, and reply status so users can see the full lifecycle of
    each opportunity at a glance.
    """

    # --- Identity ---
    job_id: str  # message_id that ties everything together
    job_title: str = ""
    company: str = ""
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None

    # --- Pipeline progress ---
    stage: OpportunityStage = OpportunityStage.FETCHED
    pipeline_complete: bool = False

    # --- Location and work mode ---
    locations: List[str] = field(default_factory=list)
    remote: Optional[bool] = None
    hybrid: Optional[bool] = None

    # --- Linked artifacts ---
    email: Optional[EmailSummary] = None
    opportunity: Optional[Dict[str, Any]] = None  # raw opportunity dict
    match: Optional[MatchSummary] = None
    tailoring: Optional[TailoringSummary] = None
    reply: Optional[ReplySummary] = None

    # --- Timeline ---
    email_received_at: Optional[str] = None
    matched_at: Optional[str] = None
    tailored_at: Optional[str] = None
    replied_at: Optional[str] = None

    # --- File paths to related artifacts ---
    artifact_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company": self.company,
            "recruiter_name": self.recruiter_name,
            "recruiter_email": self.recruiter_email,
            "stage": self.stage.value,
            "pipeline_complete": self.pipeline_complete,
            "locations": list(self.locations),
            "remote": self.remote,
            "hybrid": self.hybrid,
            "email": self.email.to_dict() if self.email else None,
            "opportunity": self.opportunity,
            "match": self.match.to_dict() if self.match else None,
            "tailoring": self.tailoring.to_dict() if self.tailoring else None,
            "reply": self.reply.to_dict() if self.reply else None,
            "timeline": {
                "email_received_at": self.email_received_at,
                "matched_at": self.matched_at,
                "tailored_at": self.tailored_at,
                "replied_at": self.replied_at,
            },
            "artifact_paths": dict(self.artifact_paths),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrelatedOpportunity":
        stage_str = data.get("stage", "fetched")
        try:
            stage = OpportunityStage(stage_str)
        except ValueError:
            stage = OpportunityStage.FETCHED

        timeline = data.get("timeline", {}) or {}

        return cls(
            job_id=data.get("job_id", ""),
            job_title=data.get("job_title", ""),
            company=data.get("company", ""),
            recruiter_name=data.get("recruiter_name"),
            recruiter_email=data.get("recruiter_email"),
            stage=stage,
            pipeline_complete=data.get("pipeline_complete", False),
            locations=data.get("locations", []) or [],
            remote=data.get("remote"),
            hybrid=data.get("hybrid"),
            email=EmailSummary.from_dict(data["email"]) if data.get("email") else None,
            opportunity=data.get("opportunity"),
            match=MatchSummary.from_dict(data["match"]) if data.get("match") else None,
            tailoring=TailoringSummary.from_dict(data["tailoring"]) if data.get("tailoring") else None,
            reply=ReplySummary.from_dict(data["reply"]) if data.get("reply") else None,
            email_received_at=timeline.get("email_received_at"),
            matched_at=timeline.get("matched_at"),
            tailored_at=timeline.get("tailored_at"),
            replied_at=timeline.get("replied_at"),
            artifact_paths=data.get("artifact_paths", {}),
        )


# ---------------------------------------------------------------------------
# Correlation Summary (aggregate statistics)
# ---------------------------------------------------------------------------

@dataclass
class CorrelationSummary:
    """Aggregate statistics across all correlated opportunities."""

    total_opportunities: int = 0
    resume_name: Optional[str] = None
    resume_file: Optional[str] = None

    # Stage counts
    by_stage: Dict[str, int] = field(default_factory=dict)
    pipeline_complete_count: int = 0

    # Match statistics
    matched_count: int = 0
    avg_match_score: float = 0.0
    max_match_score: float = 0.0
    min_match_score: float = 0.0

    # Grade distribution
    by_grade: Dict[str, int] = field(default_factory=dict)

    # Recommendation distribution
    by_recommendation: Dict[str, int] = field(default_factory=dict)

    # Reply statistics
    replies_drafted: int = 0
    replies_sent: int = 0
    replies_failed: int = 0
    replies_dry_run: int = 0

    # Tailoring statistics
    tailored_count: int = 0
    total_tailoring_changes: int = 0
    docx_generated: int = 0

    # Top companies
    top_companies: List[Dict[str, Any]] = field(default_factory=list)

    # Timestamp
    generated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_opportunities": self.total_opportunities,
            "resume_name": self.resume_name,
            "resume_file": self.resume_file,
            "by_stage": dict(self.by_stage),
            "pipeline_complete_count": self.pipeline_complete_count,
            "match_statistics": {
                "matched_count": self.matched_count,
                "avg_score": round(self.avg_match_score, 1),
                "max_score": round(self.max_match_score, 1),
                "min_score": round(self.min_match_score, 1),
            },
            "by_grade": dict(self.by_grade),
            "by_recommendation": dict(self.by_recommendation),
            "reply_statistics": {
                "drafted": self.replies_drafted,
                "sent": self.replies_sent,
                "failed": self.replies_failed,
                "dry_run": self.replies_dry_run,
            },
            "tailoring_statistics": {
                "tailored_count": self.tailored_count,
                "total_changes": self.total_tailoring_changes,
                "docx_generated": self.docx_generated,
            },
            "top_companies": self.top_companies,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrelationSummary":
        match_stats = data.get("match_statistics", {})
        reply_stats = data.get("reply_statistics", {})
        tailor_stats = data.get("tailoring_statistics", {})

        return cls(
            total_opportunities=data.get("total_opportunities", 0),
            resume_name=data.get("resume_name"),
            resume_file=data.get("resume_file"),
            by_stage=data.get("by_stage", {}),
            pipeline_complete_count=data.get("pipeline_complete_count", 0),
            matched_count=match_stats.get("matched_count", 0),
            avg_match_score=match_stats.get("avg_score", 0.0),
            max_match_score=match_stats.get("max_score", 0.0),
            min_match_score=match_stats.get("min_score", 0.0),
            by_grade=data.get("by_grade", {}),
            by_recommendation=data.get("by_recommendation", {}),
            replies_drafted=reply_stats.get("drafted", 0),
            replies_sent=reply_stats.get("sent", 0),
            replies_failed=reply_stats.get("failed", 0),
            replies_dry_run=reply_stats.get("dry_run", 0),
            tailored_count=tailor_stats.get("tailored_count", 0),
            total_tailoring_changes=tailor_stats.get("total_changes", 0),
            docx_generated=tailor_stats.get("docx_generated", 0),
            top_companies=data.get("top_companies", []),
            generated_at=data.get("generated_at"),
        )
