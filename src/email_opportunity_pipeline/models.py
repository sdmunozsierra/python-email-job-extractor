from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EmailHeaders:
    from_: str = ""
    to: str = ""
    cc: str = ""
    bcc: str = ""
    date: str = ""
    subject: str = ""
    message_id: str = ""
    in_reply_to: str = ""
    references: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "from": self.from_,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "date": self.date,
            "subject": self.subject,
            "message_id_header": self.message_id,
            "in_reply_to": self.in_reply_to,
            "references": self.references,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailHeaders":
        return cls(
            from_=data.get("from", ""),
            to=data.get("to", ""),
            cc=data.get("cc", ""),
            bcc=data.get("bcc", ""),
            date=data.get("date", ""),
            subject=data.get("subject", ""),
            message_id=data.get("message_id_header", ""),
            in_reply_to=data.get("in_reply_to", ""),
            references=data.get("references", ""),
        )


@dataclass
class Attachment:
    filename: str
    mime_type: str
    size: int
    attachment_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "mimeType": self.mime_type,
            "size": self.size,
            "attachmentId": self.attachment_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attachment":
        return cls(
            filename=data.get("filename", ""),
            mime_type=data.get("mimeType", ""),
            size=int(data.get("size", 0)),
            attachment_id=data.get("attachmentId", ""),
        )


@dataclass
class EmailSource:
    provider: str
    user_id: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "provider": self.provider,
            "userId": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailSource":
        return cls(
            provider=data.get("provider", ""),
            user_id=data.get("userId", ""),
        )


@dataclass
class EmailMessage:
    message_id: str
    thread_id: str
    internal_date: Optional[datetime]
    headers: EmailHeaders
    snippet: str
    body_text: str
    body_html: str
    labels: List[str] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    source: Optional[EmailSource] = None

    def to_dict(self) -> Dict[str, Any]:
        internal_ms = None
        internal_iso = None
        if self.internal_date:
            internal_ms = int(self.internal_date.timestamp() * 1000)
            internal_iso = self.internal_date.replace(tzinfo=timezone.utc).isoformat()

        return {
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "internal_date_ms": internal_ms,
            "internal_date_iso": internal_iso,
            "labels": list(self.labels),
            "headers": self.headers.to_dict(),
            "snippet": self.snippet,
            "body": {
                "text": self.body_text,
                "html": self.body_html,
            },
            "attachments": [att.to_dict() for att in self.attachments],
            "source": self.source.to_dict() if self.source else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailMessage":
        internal_date = None
        internal_ms = data.get("internal_date_ms")
        if internal_ms:
            internal_date = datetime.fromtimestamp(int(internal_ms) / 1000, tz=timezone.utc)

        headers = EmailHeaders.from_dict(data.get("headers", {}) or {})
        attachments = [Attachment.from_dict(a) for a in (data.get("attachments", []) or [])]
        source = EmailSource.from_dict(data.get("source", {}) or {})

        body = data.get("body", {}) or {}
        return cls(
            message_id=data.get("message_id", ""),
            thread_id=data.get("thread_id", ""),
            internal_date=internal_date,
            headers=headers,
            snippet=data.get("snippet", ""),
            body_text=body.get("text", ""),
            body_html=body.get("html", ""),
            labels=data.get("labels", []) or [],
            attachments=attachments,
            source=source,
        )


@dataclass
class FilterDecision:
    filter_name: str
    passed: bool
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filter_name": self.filter_name,
            "passed": self.passed,
            "reasons": list(self.reasons),
        }


@dataclass
class FilterOutcome:
    passed: bool
    reasons: List[str] = field(default_factory=list)
    decisions: List[FilterDecision] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "reasons": list(self.reasons),
            "decisions": [d.to_dict() for d in self.decisions],
        }
