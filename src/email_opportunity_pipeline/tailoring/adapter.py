"""
Adapter layer between the email-opportunity-pipeline matching models and
the resume-builder JSON schema format.

Translates our internal ``Resume`` (matching.models) to/from the dict
format expected by ``ResumeSchemaAdapter.from_dict()``.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from ..matching.models import (
    Resume,
    PersonalInfo,
    Skills,
    Skill,
    Language,
    Certification,
    Experience,
    Education,
    Project,
    JobPreferences,
)


class ResumeAdapter:
    """Bi-directional adapter between pipeline Resume and builder schema."""

    # ------------------------------------------------------------------
    # Pipeline Resume -> Builder schema dict
    # ------------------------------------------------------------------

    @classmethod
    def to_builder_schema(cls, resume: Resume) -> Dict[str, Any]:
        """Convert a pipeline Resume into a resume-builder JSON schema dict.

        The resulting dict can be passed straight to
        ``ResumeSchemaAdapter.from_dict(data)`` to get a Person object for
        .docx generation.
        """
        data: Dict[str, Any] = {}

        # Personal
        p = resume.personal
        data["personal"] = {
            "name": p.name,
            "email": p.email,
            "phone": p.phone,
            "location": p.location,
            "linkedin": p.linkedin,
            "github": p.github,
            "portfolio": p.portfolio,
            "summary": p.summary,
        }

        # Skills
        technical: List[Dict[str, Any]] = []
        for s in resume.skills.technical:
            technical.append({
                "name": s.name,
                "level": s.level,
                "years": s.years,
                "category": s.category,
            })

        languages: List[Dict[str, Any]] = []
        for lang in resume.skills.languages:
            languages.append({
                "language": lang.language,
                "proficiency": lang.proficiency,
            })

        certifications: List[Dict[str, Any]] = []
        for cert in resume.skills.certifications:
            certifications.append({
                "name": cert.name,
                "issuer": cert.issuer,
                "date": cert.date,
                "expiry": cert.expiry,
                "credential_id": cert.credential_id,
            })

        data["skills"] = {
            "technical": technical,
            "soft": list(resume.skills.soft),
            "languages": languages,
            "certifications": certifications,
        }

        # Experience
        data["experience"] = []
        for exp in resume.experience:
            data["experience"].append({
                "title": exp.title,
                "company": exp.company,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "current": exp.current,
                "description": exp.description,
                "achievements": list(exp.achievements),
                "technologies": list(exp.technologies),
            })

        # Education
        data["education"] = []
        for edu in resume.education:
            data["education"].append({
                "degree": edu.degree,
                "field": edu.field_of_study,
                "institution": edu.institution,
                "location": edu.location,
                "start_date": edu.start_date,
                "end_date": edu.end_date,
                "gpa": edu.gpa,
                "honors": edu.honors,
                "relevant_coursework": list(edu.relevant_coursework),
            })

        # Projects
        data["projects"] = []
        for proj in resume.projects:
            data["projects"].append({
                "name": proj.name,
                "description": proj.description,
                "url": proj.url,
                "technologies": list(proj.technologies),
                "highlights": list(proj.highlights),
            })

        # Preferences
        if resume.preferences:
            prefs = resume.preferences
            data["preferences"] = {
                "desired_roles": list(prefs.desired_roles),
                "industries": list(prefs.industries),
                "locations": list(prefs.locations),
                "remote_preference": prefs.remote_preference,
                "salary_min": prefs.salary_min,
                "salary_currency": prefs.salary_currency,
                "engagement_types": list(prefs.engagement_types),
                "willing_to_relocate": prefs.willing_to_relocate,
                "visa_sponsorship_needed": prefs.visa_sponsorship_needed,
            }

        return data

    # ------------------------------------------------------------------
    # Builder schema dict -> Pipeline Resume
    # ------------------------------------------------------------------

    @classmethod
    def from_builder_schema(
        cls,
        data: Dict[str, Any],
        source_file: Optional[str] = None,
    ) -> Resume:
        """Convert a resume-builder schema dict back into a pipeline Resume."""
        return Resume.from_dict(data, source_file=source_file)

    # ------------------------------------------------------------------
    # Deep-copy helper for safe mutation
    # ------------------------------------------------------------------

    @classmethod
    def deep_copy_schema(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return a deep copy of a builder schema dict.

        Ensures the original resume data is never mutated during tailoring.
        """
        return copy.deepcopy(data)


def adapt_resume_to_builder_schema(resume: Resume) -> Dict[str, Any]:
    """Convenience function: convert pipeline Resume to builder schema dict."""
    return ResumeAdapter.to_builder_schema(resume)
