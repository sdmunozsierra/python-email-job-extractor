"""
Tailoring Engine -- applies match-derived insights to a resume.

Takes a pipeline ``Resume``, a ``MatchResult``, and the original job
opportunity dict.  Produces a ``TailoredResume`` containing:

- The modified resume-builder schema dict (ready for .docx generation)
- A ``TailoringReport`` documenting every change made
- Optionally, the path to the generated .docx file
"""
from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..matching.models import MatchResult, Resume, ResumeTailoring

from .adapter import ResumeAdapter
from .models import (
    ChangeCategory,
    TailoredResume,
    TailoringChange,
    TailoringReport,
)

logger = logging.getLogger(__name__)


class TailoringEngine:
    """Applies tailoring suggestions from match analysis to a resume.

    The engine works in three phases:

    1. **Convert** -- pipeline Resume -> builder schema dict (deep copy).
    2. **Mutate** -- apply each tailoring action, recording a
       :class:`TailoringChange` for every modification.
    3. **Build** (optional) -- hand the tailored dict to resume-builder
       to produce a ``.docx`` file.
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tailor(
        self,
        resume: Resume,
        match_result: MatchResult,
        job: Optional[Dict[str, Any]] = None,
        build_docx: bool = True,
    ) -> TailoredResume:
        """Tailor a resume for a specific job based on match analysis.

        Args:
            resume: Original pipeline Resume object.
            match_result: MatchResult with tailoring suggestions.
            job: Original job opportunity dict (for context in reports).
            build_docx: Whether to generate the .docx file.

        Returns:
            TailoredResume with modified data, report, and optional docx path.
        """
        # Phase 1: Convert to builder schema and deep-copy
        original_data = ResumeAdapter.to_builder_schema(resume)
        tailored_data = copy.deepcopy(original_data)

        # Prepare report
        job = job or {}
        job_id = job.get("source_email", {}).get("message_id", match_result.job_id)
        job_title = job.get("job_title", "Unknown")
        company = job.get("company", "Unknown")

        report = TailoringReport(
            job_id=job_id,
            job_title=job_title,
            company=company,
            resume_name=resume.personal.name,
            match_score=match_result.overall_score,
            match_grade=match_result.match_grade,
        )

        # Phase 2: Apply tailoring changes
        tailoring = match_result.resume_tailoring
        if tailoring:
            self._apply_summary_suggestions(tailored_data, tailoring, report)
            self._apply_skills_highlighting(tailored_data, tailoring, match_result, report)
            self._apply_experience_emphasis(tailored_data, tailoring, match_result, report)
            self._apply_certification_highlighting(tailored_data, tailoring, match_result, report)
            self._apply_keyword_additions(tailored_data, tailoring, report)

        # Phase 3: Optionally build .docx
        docx_path = None
        if build_docx:
            docx_path = self._build_docx(tailored_data, job_id, job_title, company)

        return TailoredResume(
            resume_data=tailored_data,
            report=report,
            docx_path=docx_path,
            original_data=original_data,
        )

    def tailor_batch(
        self,
        resume: Resume,
        match_results: List[MatchResult],
        jobs: Optional[List[Dict[str, Any]]] = None,
        build_docx: bool = True,
    ) -> List[TailoredResume]:
        """Tailor a resume for multiple jobs.

        Args:
            resume: Original pipeline Resume.
            match_results: List of MatchResult objects.
            jobs: Optional list of job dicts aligned with match_results.
            build_docx: Whether to generate .docx files.

        Returns:
            List of TailoredResume objects.
        """
        jobs_list = jobs or [{}] * len(match_results)
        results: List[TailoredResume] = []

        for match_result, job in zip(match_results, jobs_list):
            try:
                tailored = self.tailor(resume, match_result, job, build_docx)
                results.append(tailored)
            except Exception:
                logger.exception(
                    "Failed to tailor resume for job %s", match_result.job_id
                )

        return results

    # ------------------------------------------------------------------
    # Tailoring actions
    # ------------------------------------------------------------------

    def _apply_summary_suggestions(
        self,
        data: Dict[str, Any],
        tailoring: ResumeTailoring,
        report: TailoringReport,
    ) -> None:
        """Apply summary/objective tailoring."""
        if not tailoring.summary_suggestions:
            return

        personal = data.get("personal", {})
        old_summary = personal.get("summary", "")
        new_summary = tailoring.summary_suggestions

        personal["summary"] = new_summary
        data["personal"] = personal

        report.changes.append(TailoringChange(
            category=ChangeCategory.SUMMARY,
            description="Replaced summary with job-tailored version",
            reason="Match analysis suggested a tailored summary for this role",
            before=old_summary,
            after=new_summary,
            field_name="summary",
        ))

    def _apply_skills_highlighting(
        self,
        data: Dict[str, Any],
        tailoring: ResumeTailoring,
        match_result: MatchResult,
        report: TailoringReport,
    ) -> None:
        """Reorder and highlight skills based on job requirements.

        - Skills to highlight are moved to the front of the technical list.
        - Matched mandatory skills are prioritized.
        """
        skills_section = data.get("skills", {})
        technical = skills_section.get("technical", [])

        if not technical:
            return

        highlight_names = set(
            s.lower() for s in (tailoring.skills_to_highlight or [])
        )
        matched_mandatory = set(
            s.lower() for s in (match_result.skills_match.matched_mandatory or [])
        )

        # Combine priority names
        priority_names = highlight_names | matched_mandatory

        if not priority_names:
            return

        # Partition into priority and rest
        priority_skills: List[Dict] = []
        rest_skills: List[Dict] = []

        for skill in technical:
            name = skill.get("name", "").lower()
            if name in priority_names:
                priority_skills.append(skill)
            else:
                rest_skills.append(skill)

        if not priority_skills:
            return

        old_order = [s.get("name", "") for s in technical]
        reordered = priority_skills + rest_skills
        new_order = [s.get("name", "") for s in reordered]

        skills_section["technical"] = reordered
        data["skills"] = skills_section

        report.changes.append(TailoringChange(
            category=ChangeCategory.SKILLS,
            description=f"Reordered technical skills: {len(priority_skills)} priority skills moved to top",
            reason="Highlighted skills matching job requirements and mandatory skills",
            before=", ".join(old_order[:8]) + ("..." if len(old_order) > 8 else ""),
            after=", ".join(new_order[:8]) + ("..." if len(new_order) > 8 else ""),
            field_name="technical",
        ))

        # Log individual skill highlights
        for skill in priority_skills:
            name = skill.get("name", "")
            in_mandatory = name.lower() in matched_mandatory
            in_highlight = name.lower() in highlight_names

            reasons = []
            if in_mandatory:
                reasons.append("mandatory skill match")
            if in_highlight:
                reasons.append("recommended to highlight")

            report.changes.append(TailoringChange(
                category=ChangeCategory.SKILLS,
                description=f"Prioritized skill: {name}",
                reason="; ".join(reasons),
                field_name="technical",
            ))

    def _apply_experience_emphasis(
        self,
        data: Dict[str, Any],
        tailoring: ResumeTailoring,
        match_result: MatchResult,
        report: TailoringReport,
    ) -> None:
        """Emphasize relevant experience entries and achievements.

        - Reorder experience entries so the most relevant positions come first.
        - Surface achievements that the match analysis recommended featuring.
        """
        experience = data.get("experience", [])
        if not experience:
            return

        emphasis_hints = set(
            e.lower() for e in (tailoring.experience_to_emphasize or [])
        )
        featured_achievements = set(
            a.lower() for a in (tailoring.achievements_to_feature or [])
        )

        # Build relevance data from match result
        relevant_positions = match_result.experience_match.relevant_positions or []
        relevance_map: Dict[str, str] = {}
        for pos in relevant_positions:
            key = f"{pos.get('title', '').lower()}|{pos.get('company', '').lower()}"
            relevance_map[key] = pos.get("relevance", "low")

        # Score and sort experiences
        scored: List[tuple] = []
        for idx, exp in enumerate(experience):
            score = 0
            title = exp.get("title", "").lower()
            company = exp.get("company", "").lower()
            key = f"{title}|{company}"

            # Relevance from match analysis
            rel = relevance_map.get(key, "")
            if rel == "high":
                score += 3
            elif rel == "medium":
                score += 2
            elif rel == "low":
                score += 1

            # Emphasis hints from tailoring suggestions
            for hint in emphasis_hints:
                if hint in title or hint in company:
                    score += 2
                    break
                # Check in achievements and description
                desc = (exp.get("description") or "").lower()
                achievements = " ".join(exp.get("achievements", [])).lower()
                if hint in desc or hint in achievements:
                    score += 1
                    break

            # Keep current position at top if still first
            if exp.get("current", False):
                score += 5

            scored.append((score, idx, exp))

        # Sort by score descending, preserving original order for ties
        scored.sort(key=lambda x: (-x[0], x[1]))
        reordered = [item[2] for item in scored]

        old_order = [f"{e.get('title', '')} at {e.get('company', '')}" for e in experience]
        new_order = [f"{e.get('title', '')} at {e.get('company', '')}" for e in reordered]

        if old_order != new_order:
            data["experience"] = reordered
            report.changes.append(TailoringChange(
                category=ChangeCategory.EXPERIENCE,
                description="Reordered experience entries by relevance to target role",
                reason="Match analysis identified varying relevance levels across positions",
                before=" > ".join(old_order),
                after=" > ".join(new_order),
                field_name="experience",
            ))

        # Reorder achievements within each experience entry
        for idx, exp in enumerate(reordered):
            achievements = exp.get("achievements", [])
            if not achievements or not featured_achievements:
                continue

            featured: List[str] = []
            rest: List[str] = []
            for ach in achievements:
                if ach.lower() in featured_achievements:
                    featured.append(ach)
                else:
                    rest.append(ach)

            if featured and featured != achievements[:len(featured)]:
                exp["achievements"] = featured + rest
                report.changes.append(TailoringChange(
                    category=ChangeCategory.EXPERIENCE,
                    description=f"Prioritized {len(featured)} featured achievement(s) in {exp.get('title', '')} at {exp.get('company', '')}",
                    reason="Match analysis recommended featuring these achievements",
                    section_index=idx,
                    field_name="achievements",
                ))

    def _apply_certification_highlighting(
        self,
        data: Dict[str, Any],
        tailoring: ResumeTailoring,
        match_result: MatchResult,
        report: TailoringReport,
    ) -> None:
        """Reorder certifications to prioritize those relevant to the job.

        Uses keywords_to_add and skills_to_highlight as signals for which
        certifications are most relevant.
        """
        skills_section = data.get("skills", {})
        certifications = skills_section.get("certifications", [])

        if not certifications or len(certifications) <= 1:
            return

        # Build relevance signals
        relevant_terms = set()
        for kw in (tailoring.keywords_to_add or []):
            relevant_terms.add(kw.lower())
        for s in (tailoring.skills_to_highlight or []):
            relevant_terms.add(s.lower())
        # Also consider matched mandatory/preferred skills
        for s in (match_result.skills_match.matched_mandatory or []):
            relevant_terms.add(s.lower())
        for s in (match_result.skills_match.matched_preferred or []):
            relevant_terms.add(s.lower())

        if not relevant_terms:
            return

        # Score certifications by relevance
        scored: List[tuple] = []
        for idx, cert in enumerate(certifications):
            score = 0
            cert_name = (cert.get("name", "") or "").lower()
            cert_issuer = (cert.get("issuer", "") or "").lower()

            for term in relevant_terms:
                if term in cert_name or term in cert_issuer:
                    score += 1

            scored.append((score, idx, cert))

        scored.sort(key=lambda x: (-x[0], x[1]))
        reordered = [item[2] for item in scored]

        old_names = [c.get("name", "") for c in certifications]
        new_names = [c.get("name", "") for c in reordered]

        if old_names != new_names:
            skills_section["certifications"] = reordered
            data["skills"] = skills_section

            report.changes.append(TailoringChange(
                category=ChangeCategory.CERTIFICATIONS,
                description="Reordered certifications by relevance to target role",
                reason="Certifications matching job keywords and required skills moved to top",
                before=", ".join(old_names),
                after=", ".join(new_names),
                field_name="certifications",
            ))

    def _apply_keyword_additions(
        self,
        data: Dict[str, Any],
        tailoring: ResumeTailoring,
        report: TailoringReport,
    ) -> None:
        """Track keyword additions recommended by the match analysis.

        Keywords are recorded in the report for reference. They inform
        the summary rewrite and skill highlighting but are not injected
        as raw text to avoid keyword-stuffing.
        """
        keywords = tailoring.keywords_to_add or []
        if not keywords:
            return

        report.changes.append(TailoringChange(
            category=ChangeCategory.KEYWORDS,
            description=f"Identified {len(keywords)} ATS keywords to incorporate",
            reason="Match analysis identified missing keywords for ATS optimization",
            after=", ".join(keywords),
            field_name="keywords",
        ))

    # ------------------------------------------------------------------
    # .docx generation
    # ------------------------------------------------------------------

    def _build_docx(
        self,
        data: Dict[str, Any],
        job_id: str,
        job_title: str,
        company: str,
    ) -> Optional[Path]:
        """Generate a .docx file from the tailored resume data.

        Returns the path to the generated file, or ``None`` if the
        resume-builder package is not available.
        """
        try:
            from resume_builder.schema_adapter import ResumeSchemaAdapter
            from resume_builder.cli import build_resume
        except ImportError:
            logger.warning(
                "resume-builder package not installed; skipping .docx generation. "
                "Run 'uv sync' or 'pip install -e vendor/resume-builder' to enable."
            )
            return None

        output_dir = self.output_dir or Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build a safe filename
        safe_company = "".join(c for c in company if c.isalnum() or c in " _-").strip()
        safe_title = "".join(c for c in job_title if c.isalnum() or c in " _-").strip()
        filename = f"tailored_resume_{safe_company}_{safe_title}.docx".replace(" ", "_")
        docx_path = output_dir / filename

        person = ResumeSchemaAdapter.from_dict(data)
        doc = build_resume(person)
        doc.save(str(docx_path))

        logger.info("Tailored resume saved to %s", docx_path)
        return docx_path


def tailor_resume(
    resume: Resume,
    match_result: MatchResult,
    job: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
    build_docx: bool = True,
) -> TailoredResume:
    """Convenience function to tailor a resume for a single job.

    Args:
        resume: Pipeline Resume object.
        match_result: MatchResult with tailoring suggestions.
        job: Original job opportunity dict.
        output_dir: Where to save generated .docx files.
        build_docx: Whether to generate the .docx.

    Returns:
        TailoredResume with report and optional .docx path.
    """
    engine = TailoringEngine(output_dir=output_dir)
    return engine.tailor(resume, match_result, job, build_docx)
