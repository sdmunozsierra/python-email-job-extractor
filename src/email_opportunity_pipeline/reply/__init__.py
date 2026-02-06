"""
Recruiter Reply module.

Compose and send tailored emails back to recruiters with:

- **LLM-powered composition** -- personalised replies that reference
  match insights, candidate strengths, and user-defined questionnaire
  topics (salary, location, interview process, etc.).
- **Dry-run mode** -- preview composed emails without sending.
- **Attachment support** -- attach tailored resumes (.docx) to replies.
- **Batch operation** -- compose and send replies for multiple
  opportunities in a single run.
"""

from .composer import ReplyComposer
from .models import (
    EmailDraft,
    QuestionnaireConfig,
    ReplyResult,
    ReplyStatus,
    ReplyTone,
)
from .report import (
    render_batch_preview,
    render_draft_preview,
    render_send_report,
)
from .sender import GmailSender
from .templates import (
    DEFAULT_INTERVIEW_QUESTIONS,
    render_fallback_template,
)

__all__ = [
    # Composer
    "ReplyComposer",
    # Sender
    "GmailSender",
    # Models
    "EmailDraft",
    "QuestionnaireConfig",
    "ReplyResult",
    "ReplyStatus",
    "ReplyTone",
    # Templates
    "DEFAULT_INTERVIEW_QUESTIONS",
    "render_fallback_template",
    # Reports
    "render_batch_preview",
    "render_draft_preview",
    "render_send_report",
]
