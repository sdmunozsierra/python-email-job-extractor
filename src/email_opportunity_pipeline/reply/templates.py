"""
Default email templates and prompt building utilities for the reply composer.

Templates are plain-text / Markdown strings with ``{placeholder}`` markers
that the composer fills in before passing to the LLM.  The module also
provides helper functions to assemble the *system* and *user* prompts
used by the LLM composer.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import QuestionnaireConfig, ReplyTone


# ============================================================================
# Tone descriptions fed to the LLM system prompt
# ============================================================================

TONE_DESCRIPTIONS: Dict[ReplyTone, str] = {
    ReplyTone.PROFESSIONAL: (
        "Write in a polished, professional tone.  Be courteous and direct.  "
        "Avoid slang and keep sentences clear."
    ),
    ReplyTone.ENTHUSIASTIC: (
        "Write in an upbeat, enthusiastic tone.  Show genuine excitement "
        "about the opportunity while remaining professional."
    ),
    ReplyTone.CASUAL: (
        "Write in a friendly, conversational tone.  Keep it warm and "
        "approachable but still respectful."
    ),
    ReplyTone.CONCISE: (
        "Write in an ultra-concise, to-the-point tone.  Use short "
        "sentences and bullet points where appropriate.  Minimise fluff."
    ),
}


# ============================================================================
# Default interview-process questions
# ============================================================================

DEFAULT_INTERVIEW_QUESTIONS: List[str] = [
    "What does the interview process look like and how many rounds should I expect?",
    "Is there a technical assessment or take-home project?",
    "What is the expected timeline from first interview to offer?",
]


# ============================================================================
# System prompt
# ============================================================================

SYSTEM_PROMPT = """\
You are an expert career coach and email copywriter.  Your task is to
compose a professional reply email from a job candidate to a recruiter.

Rules:
- Address the recruiter by name when known; otherwise use a polite greeting.
- Reference the specific job title and company so the recruiter knows which
  role you are responding to.
- Incorporate the candidate's strengths and talking points naturally --
  do NOT simply list them.
- Only include sections the user has opted in to (salary, location,
  interview questions, availability, custom questions).
- Keep the email under {max_length_words} words.
- {tone_instruction}
- End with a clear call to action (e.g. suggest scheduling a call).
- Do NOT invent facts about the candidate.  Use only the information
  provided.
- Output ONLY the email body text (no subject line, no headers).
"""


# ============================================================================
# User prompt builder
# ============================================================================

def build_user_prompt(
    *,
    job_title: str,
    company: str,
    recruiter_name: Optional[str],
    recruiter_email: str,
    original_subject: str,
    original_snippet: str,
    candidate_name: str,
    candidate_summary: Optional[str],
    strengths: List[str],
    talking_points: List[str],
    match_score: Optional[float],
    match_grade: Optional[str],
    questionnaire: QuestionnaireConfig,
) -> str:
    """Assemble the user prompt that describes the specific reply context."""

    sections: List[str] = []

    # -- Job context --
    sections.append("## Job Context")
    sections.append(f"- **Role:** {job_title}")
    sections.append(f"- **Company:** {company}")
    if recruiter_name:
        sections.append(f"- **Recruiter name:** {recruiter_name}")
    sections.append(f"- **Recruiter email:** {recruiter_email}")
    sections.append(f"- **Original subject:** {original_subject}")
    if original_snippet:
        sections.append(f"- **Original snippet:** {original_snippet[:300]}")
    if match_score is not None:
        sections.append(f"- **Match score:** {match_score:.0f}/100 ({match_grade or 'N/A'})")

    # -- Candidate context --
    sections.append("\n## Candidate")
    sections.append(f"- **Name:** {candidate_name}")
    if candidate_summary:
        sections.append(f"- **Summary:** {candidate_summary}")
    if strengths:
        sections.append("- **Key strengths:**")
        for s in strengths[:5]:
            sections.append(f"  - {s}")
    if talking_points:
        sections.append("- **Talking points to weave in:**")
        for tp in talking_points[:5]:
            sections.append(f"  - {tp}")

    # -- Questionnaire sections --
    sections.append("\n## Topics to include in the reply")

    if questionnaire.include_salary and questionnaire.salary_range:
        sections.append(f"\n### Salary expectations")
        sections.append(f"State that the candidate's salary expectation is **{questionnaire.salary_range}**.")
        if questionnaire.salary_notes:
            sections.append(f"Additional context: {questionnaire.salary_notes}")

    if questionnaire.include_location and questionnaire.location_preference:
        sections.append(f"\n### Location / remote preference")
        sections.append(f"Mention: {questionnaire.location_preference}")
        if questionnaire.relocation_notes:
            sections.append(f"Relocation: {questionnaire.relocation_notes}")

    if questionnaire.include_availability:
        if questionnaire.availability:
            sections.append(f"\n### Availability")
            sections.append(f"Mention: {questionnaire.availability}")
        if questionnaire.notice_period:
            sections.append(f"Notice period: {questionnaire.notice_period}")

    if questionnaire.visa_status:
        sections.append(f"\n### Visa / work authorisation")
        sections.append(f"Mention: {questionnaire.visa_status}")

    if questionnaire.include_interview_questions:
        questions = questionnaire.interview_process_questions or DEFAULT_INTERVIEW_QUESTIONS
        if questions:
            sections.append(f"\n### Questions about the interview process")
            sections.append("Politely ask the following questions:")
            for q in questions:
                sections.append(f"- {q}")

    if questionnaire.custom_questions:
        sections.append(f"\n### Additional questions")
        for q in questionnaire.custom_questions:
            sections.append(f"- {q}")

    if questionnaire.extra_instructions:
        sections.append(f"\n### Extra instructions")
        sections.append(questionnaire.extra_instructions)

    return "\n".join(sections)


def build_system_prompt(questionnaire: QuestionnaireConfig) -> str:
    """Build the system prompt with tone and length constraints."""
    tone_instruction = TONE_DESCRIPTIONS.get(
        questionnaire.tone,
        TONE_DESCRIPTIONS[ReplyTone.PROFESSIONAL],
    )
    return SYSTEM_PROMPT.format(
        max_length_words=questionnaire.max_length_words,
        tone_instruction=tone_instruction,
    )


# ============================================================================
# Fallback plain-text template (used when LLM is unavailable)
# ============================================================================

FALLBACK_TEMPLATE = """\
Hi{recruiter_greeting},

Thank you for reaching out about the {job_title} position at {company}.  \
I appreciate your interest and would love to learn more.

{salary_paragraph}\
{location_paragraph}\
{availability_paragraph}\
{questions_paragraph}\
I have attached my resume for your review.  I would be happy to schedule \
a call at your convenience to discuss this opportunity further.

Best regards,
{candidate_name}
"""


def render_fallback_template(
    *,
    job_title: str,
    company: str,
    recruiter_name: Optional[str],
    candidate_name: str,
    questionnaire: QuestionnaireConfig,
) -> str:
    """Render the plain-text fallback template (no LLM required)."""

    recruiter_greeting = f" {recruiter_name}" if recruiter_name else ""

    salary_paragraph = ""
    if questionnaire.include_salary and questionnaire.salary_range:
        salary_paragraph = (
            f"Regarding compensation, my expected range is {questionnaire.salary_range}."
        )
        if questionnaire.salary_notes:
            salary_paragraph += f"  {questionnaire.salary_notes}"
        salary_paragraph += "\n\n"

    location_paragraph = ""
    if questionnaire.include_location and questionnaire.location_preference:
        location_paragraph = (
            f"In terms of location, {questionnaire.location_preference}."
        )
        if questionnaire.relocation_notes:
            location_paragraph += f"  {questionnaire.relocation_notes}"
        location_paragraph += "\n\n"

    availability_paragraph = ""
    if questionnaire.include_availability and questionnaire.availability:
        availability_paragraph = f"Regarding availability, {questionnaire.availability}."
        if questionnaire.notice_period:
            availability_paragraph += f"  My current notice period is {questionnaire.notice_period}."
        availability_paragraph += "\n\n"

    questions_lines: list[str] = []
    if questionnaire.include_interview_questions:
        questions = questionnaire.interview_process_questions or DEFAULT_INTERVIEW_QUESTIONS
        if questions:
            questions_lines.append("I also have a few questions about the process:")
            for q in questions:
                questions_lines.append(f"  - {q}")
    if questionnaire.custom_questions:
        if not questions_lines:
            questions_lines.append("I also have a few questions:")
        for q in questionnaire.custom_questions:
            questions_lines.append(f"  - {q}")
    questions_paragraph = "\n".join(questions_lines) + "\n\n" if questions_lines else ""

    return FALLBACK_TEMPLATE.format(
        recruiter_greeting=recruiter_greeting,
        job_title=job_title,
        company=company,
        salary_paragraph=salary_paragraph,
        location_paragraph=location_paragraph,
        availability_paragraph=availability_paragraph,
        questions_paragraph=questions_paragraph,
        candidate_name=candidate_name,
    )
