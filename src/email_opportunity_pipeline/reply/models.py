"""
Data models for the recruiter reply feature.

Covers questionnaire configuration, email drafts, and send results.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Questionnaire / user-preference models
# ---------------------------------------------------------------------------

class ReplyTone(enum.Enum):
    """Tone presets for LLM-generated replies."""

    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"
    CASUAL = "casual"
    CONCISE = "concise"


@dataclass
class QuestionnaireConfig:
    """User preferences for what to communicate in recruiter replies.

    This is serialisable to / from JSON so users can persist their
    preferences and re-use them across pipeline runs.

    Fields that are ``None`` or empty are *omitted* from the generated
    email -- the LLM composer only includes topics the user opted in to.
    """

    # --- Compensation ---
    salary_range: Optional[str] = None  # e.g. "$180,000 - $220,000 USD"
    salary_notes: Optional[str] = None  # extra context

    # --- Location / remote ---
    location_preference: Optional[str] = None
    relocation_notes: Optional[str] = None

    # --- Availability ---
    availability: Optional[str] = None  # e.g. "Available in 2 weeks"
    notice_period: Optional[str] = None

    # --- Visa / sponsorship ---
    visa_status: Optional[str] = None

    # --- Interview process ---
    interview_process_questions: List[str] = field(default_factory=list)

    # --- Custom free-form questions ---
    custom_questions: List[str] = field(default_factory=list)

    # --- Behavioural flags ---
    include_salary: bool = True
    include_location: bool = True
    include_interview_questions: bool = True
    include_availability: bool = True

    # --- Tone / style ---
    tone: ReplyTone = ReplyTone.PROFESSIONAL
    max_length_words: int = 300  # soft cap for the email body

    # --- Extra instructions the user can give to the LLM ---
    extra_instructions: Optional[str] = None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "salary_range": self.salary_range,
            "salary_notes": self.salary_notes,
            "location_preference": self.location_preference,
            "relocation_notes": self.relocation_notes,
            "availability": self.availability,
            "notice_period": self.notice_period,
            "visa_status": self.visa_status,
            "interview_process_questions": list(self.interview_process_questions),
            "custom_questions": list(self.custom_questions),
            "include_salary": self.include_salary,
            "include_location": self.include_location,
            "include_interview_questions": self.include_interview_questions,
            "include_availability": self.include_availability,
            "tone": self.tone.value,
            "max_length_words": self.max_length_words,
            "extra_instructions": self.extra_instructions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionnaireConfig":
        tone_str = data.get("tone", "professional")
        try:
            tone = ReplyTone(tone_str)
        except ValueError:
            tone = ReplyTone.PROFESSIONAL

        return cls(
            salary_range=data.get("salary_range"),
            salary_notes=data.get("salary_notes"),
            location_preference=data.get("location_preference"),
            relocation_notes=data.get("relocation_notes"),
            availability=data.get("availability"),
            notice_period=data.get("notice_period"),
            visa_status=data.get("visa_status"),
            interview_process_questions=data.get("interview_process_questions", []) or [],
            custom_questions=data.get("custom_questions", []) or [],
            include_salary=data.get("include_salary", True),
            include_location=data.get("include_location", True),
            include_interview_questions=data.get("include_interview_questions", True),
            include_availability=data.get("include_availability", True),
            tone=tone,
            max_length_words=data.get("max_length_words", 300),
            extra_instructions=data.get("extra_instructions"),
        )


# ---------------------------------------------------------------------------
# Email draft model
# ---------------------------------------------------------------------------

@dataclass
class EmailDraft:
    """A composed email draft ready for review or sending.

    May include file attachments (e.g. a tailored resume ``.docx``).
    """

    to: str
    subject: str
    body_text: str
    body_html: Optional[str] = None

    # Threading headers (for replying in the same Gmail conversation)
    in_reply_to: Optional[str] = None   # original Message-ID header
    references: Optional[str] = None    # References header chain
    thread_id: Optional[str] = None     # Gmail thread ID

    # Attachments (local file paths)
    attachment_paths: List[str] = field(default_factory=list)

    # Metadata for reporting
    job_id: str = ""
    job_title: str = ""
    company: str = ""
    match_score: Optional[float] = None
    match_grade: Optional[str] = None
    recruiter_name: Optional[str] = None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "to": self.to,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "in_reply_to": self.in_reply_to,
            "references": self.references,
            "thread_id": self.thread_id,
            "attachment_paths": list(self.attachment_paths),
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company": self.company,
            "match_score": self.match_score,
            "match_grade": self.match_grade,
            "recruiter_name": self.recruiter_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailDraft":
        return cls(
            to=data.get("to", ""),
            subject=data.get("subject", ""),
            body_text=data.get("body_text", ""),
            body_html=data.get("body_html"),
            in_reply_to=data.get("in_reply_to"),
            references=data.get("references"),
            thread_id=data.get("thread_id"),
            attachment_paths=data.get("attachment_paths", []) or [],
            job_id=data.get("job_id", ""),
            job_title=data.get("job_title", ""),
            company=data.get("company", ""),
            match_score=data.get("match_score"),
            match_grade=data.get("match_grade"),
            recruiter_name=data.get("recruiter_name"),
        )


# ---------------------------------------------------------------------------
# Reply result model
# ---------------------------------------------------------------------------

class ReplyStatus(enum.Enum):
    """Outcome of a reply attempt."""

    DRAFT = "draft"       # composed but not sent
    DRY_RUN = "dry_run"   # previewed only
    SENT = "sent"         # successfully sent
    FAILED = "failed"     # send attempted but failed


@dataclass
class ReplyResult:
    """Result of composing, previewing, or sending an email reply."""

    draft: EmailDraft
    status: ReplyStatus = ReplyStatus.DRAFT
    gmail_message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    @property
    def sent(self) -> bool:
        return self.status == ReplyStatus.SENT

    @property
    def dry_run(self) -> bool:
        return self.status == ReplyStatus.DRY_RUN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "draft": self.draft.to_dict(),
            "status": self.status.value,
            "gmail_message_id": self.gmail_message_id,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReplyResult":
        status_str = data.get("status", "draft")
        try:
            status = ReplyStatus(status_str)
        except ValueError:
            status = ReplyStatus.DRAFT

        timestamp = None
        ts_str = data.get("timestamp")
        if ts_str:
            try:
                timestamp = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                pass

        return cls(
            draft=EmailDraft.from_dict(data.get("draft", {})),
            status=status,
            gmail_message_id=data.get("gmail_message_id"),
            error=data.get("error"),
            timestamp=timestamp,
        )
