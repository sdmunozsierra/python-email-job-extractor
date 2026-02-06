"""
LLM-powered email composer for recruiter replies.

Takes job opportunity data, match results, resume info, and user
questionnaire preferences, then generates a personalised email body
using an LLM (or falls back to a plain-text template).
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..matching.models import MatchResult, Resume

from .models import EmailDraft, QuestionnaireConfig
from .templates import (
    build_system_prompt,
    build_user_prompt,
    render_fallback_template,
)

logger = logging.getLogger(__name__)


def _extract_recruiter_name(from_header: str) -> Optional[str]:
    """Try to pull a human name from an RFC-822 ``From`` header.

    Examples:
        "Jane Doe <jane@example.com>" -> "Jane Doe"
        "jane@example.com"            -> None
    """
    if not from_header:
        return None
    match = re.match(r"^(.+?)\s*<", from_header)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        if name:
            return name
    return None


def _extract_email_address(from_header: str) -> str:
    """Extract just the email address from a ``From`` header."""
    match = re.search(r"<([^>]+)>", from_header)
    if match:
        return match.group(1).strip()
    # Might be a bare email address
    return from_header.strip()


def _build_reply_subject(original_subject: str) -> str:
    """Build a ``Re:`` subject line, avoiding double ``Re:`` prefixes."""
    subject = original_subject.strip()
    if subject.lower().startswith("re:"):
        return subject
    return f"Re: {subject}"


class ReplyComposer:
    """Compose tailored recruiter reply emails using an LLM.

    Falls back to a plain-text template when the LLM is unavailable
    (e.g. no ``openai`` package or no API key).
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ) -> None:
        self.model = model
        self._client = None
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
        except ImportError:
            logger.warning(
                "openai package not installed -- falling back to template-based "
                "composition.  Run `pip install -e '.[llm]'` for LLM support."
            )
        except Exception as exc:
            logger.warning("Could not initialise OpenAI client: %s", exc)

    @property
    def llm_available(self) -> bool:
        return self._client is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compose(
        self,
        *,
        resume: Resume,
        match_result: MatchResult,
        job: Dict[str, Any],
        questionnaire: QuestionnaireConfig,
        attachment_paths: Optional[List[str]] = None,
    ) -> EmailDraft:
        """Compose a single recruiter reply email.

        Args:
            resume: The candidate's resume.
            match_result: Match analysis for this job.
            job: The original job opportunity dict.
            questionnaire: User preferences for the reply.
            attachment_paths: Paths to files to attach (e.g. tailored .docx).

        Returns:
            An ``EmailDraft`` ready for preview or sending.
        """
        source_email = job.get("source_email", {}) or {}
        from_header = source_email.get("from", "")
        recruiter_name = _extract_recruiter_name(from_header)
        recruiter_email = _extract_email_address(from_header)
        original_subject = source_email.get("subject", job.get("job_title", ""))
        original_snippet = source_email.get("snippet", "")
        original_message_id = source_email.get("message_id_header", "")
        thread_id = source_email.get("thread_id", "")
        job_id = source_email.get("message_id", match_result.job_id)

        job_title = job.get("job_title", "Unknown")
        company = job.get("company", "Unknown")

        # Compose the email body
        if self.llm_available:
            body_text = self._compose_with_llm(
                job_title=job_title,
                company=company,
                recruiter_name=recruiter_name,
                recruiter_email=recruiter_email,
                original_subject=original_subject,
                original_snippet=original_snippet,
                resume=resume,
                match_result=match_result,
                questionnaire=questionnaire,
            )
        else:
            body_text = render_fallback_template(
                job_title=job_title,
                company=company,
                recruiter_name=recruiter_name,
                candidate_name=resume.personal.name,
                questionnaire=questionnaire,
            )

        return EmailDraft(
            to=recruiter_email,
            subject=_build_reply_subject(original_subject),
            body_text=body_text,
            in_reply_to=original_message_id or None,
            references=original_message_id or None,
            thread_id=thread_id or None,
            attachment_paths=list(attachment_paths or []),
            job_id=job_id,
            job_title=job_title,
            company=company,
            match_score=match_result.overall_score,
            match_grade=match_result.match_grade,
            recruiter_name=recruiter_name,
        )

    def compose_batch(
        self,
        *,
        resume: Resume,
        match_results: List[MatchResult],
        jobs: List[Dict[str, Any]],
        questionnaire: QuestionnaireConfig,
        attachment_map: Optional[Dict[str, List[str]]] = None,
    ) -> List[EmailDraft]:
        """Compose reply drafts for multiple job opportunities.

        Args:
            resume: The candidate's resume.
            match_results: List of match results.
            jobs: List of job opportunity dicts aligned with match_results.
            questionnaire: Shared user preferences.
            attachment_map: Optional mapping of job_id -> list of attachment paths.

        Returns:
            List of ``EmailDraft`` objects.
        """
        attachment_map = attachment_map or {}
        drafts: List[EmailDraft] = []

        for match_result, job in zip(match_results, jobs):
            job_id = job.get("source_email", {}).get("message_id", match_result.job_id)
            attachments = attachment_map.get(job_id, [])
            try:
                draft = self.compose(
                    resume=resume,
                    match_result=match_result,
                    job=job,
                    questionnaire=questionnaire,
                    attachment_paths=attachments,
                )
                drafts.append(draft)
            except Exception:
                logger.exception("Failed to compose reply for job %s", job_id)

        return drafts

    # ------------------------------------------------------------------
    # LLM composition
    # ------------------------------------------------------------------

    def _compose_with_llm(
        self,
        *,
        job_title: str,
        company: str,
        recruiter_name: Optional[str],
        recruiter_email: str,
        original_subject: str,
        original_snippet: str,
        resume: Resume,
        match_result: MatchResult,
        questionnaire: QuestionnaireConfig,
    ) -> str:
        """Use the LLM to generate a personalised email body."""
        system_prompt = build_system_prompt(questionnaire)
        user_prompt = build_user_prompt(
            job_title=job_title,
            company=company,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_email,
            original_subject=original_subject,
            original_snippet=original_snippet,
            candidate_name=resume.personal.name,
            candidate_summary=resume.personal.summary,
            strengths=match_result.insights.strengths,
            talking_points=match_result.insights.talking_points,
            match_score=match_result.overall_score,
            match_grade=match_result.match_grade,
            questionnaire=questionnaire,
        )

        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            body = response.output_text.strip()
            if body:
                return body
        except Exception:
            logger.exception("LLM composition failed; falling back to template")

        # Fallback
        return render_fallback_template(
            job_title=job_title,
            company=company,
            recruiter_name=recruiter_name,
            candidate_name=resume.personal.name,
            questionnaire=questionnaire,
        )
