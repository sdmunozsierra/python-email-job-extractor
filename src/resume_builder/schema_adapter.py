"""Adapter that loads the external resume JSON schema and produces internal model objects.

The external JSON schema has the following top-level keys:
    personal, skills, experience, education, projects, preferences

This adapter:
 1. Maps every recognised field to a first-class attribute on the internal models.
 2. Collects any *unrecognised* keys into an ``extra`` dict so that nothing is
    silently dropped.

Usage::

    from resume_builder.schema_adapter import ResumeSchemaAdapter

    person = ResumeSchemaAdapter.from_json_file("resume.json")
    # or
    person = ResumeSchemaAdapter.from_dict(json_dict)
"""

import json
from pathlib import Path

from resume_builder.person_builder import PersonBuilder
from resume_builder.experiece_builder import ExperienceFactory
from resume_builder.education_builder import EducationFactory
from resume_builder.cert_builder import CertFactory
from resume_builder.project_builder import ProjectFactory
from resume_builder.skill import SkillFactory


# Keys the adapter explicitly handles at each level.
# Anything outside these sets is routed to ``extra``.

_KNOWN_ROOT_KEYS = {"personal", "skills", "experience", "education", "projects", "preferences"}

_KNOWN_PERSONAL_KEYS = {
    "name", "email", "phone", "location",
    "linkedin", "github", "portfolio", "summary",
}

_KNOWN_SKILLS_KEYS = {"technical", "soft", "languages", "certifications"}

_KNOWN_EXPERIENCE_KEYS = {
    "title", "company", "location", "start_date", "end_date",
    "current", "description", "achievements", "technologies",
}

_KNOWN_EDUCATION_KEYS = {
    "degree", "field", "institution", "location",
    "start_date", "end_date", "gpa", "honors", "relevant_coursework",
}

_KNOWN_PROJECT_KEYS = {"name", "description", "url", "technologies", "highlights"}

_KNOWN_CERT_KEYS = {"name", "issuer", "date", "expiry", "credential_id"}

_KNOWN_SKILL_KEYS = {"name", "level", "years", "category"}

_KNOWN_PREFERENCE_KEYS = {
    "desired_roles", "industries", "locations", "remote_preference",
    "salary_min", "salary_currency", "engagement_types",
    "willing_to_relocate", "visa_sponsorship_needed",
}


def _collect_extra(data: dict, known_keys: set) -> dict:
    """Return a dict of keys in *data* that are not in *known_keys*."""
    return {k: v for k, v in data.items() if k not in known_keys}


class ResumeSchemaAdapter:
    """Converts a resume JSON dict (external schema) into an internal ``Person`` object."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def from_json_file(cls, path):
        """Load a JSON file and return a ``Person``."""
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict):
        """Convert a raw dict (already parsed JSON) into a ``Person``."""
        builder = PersonBuilder()

        # 1. Personal info
        cls._apply_personal(builder, data.get("personal", {}))

        # 2. Skills (technical, soft, languages, certifications)
        cls._apply_skills(builder, data.get("skills", {}))

        # 3. Experience
        for exp_data in data.get("experience", []):
            builder.add_experience(ExperienceFactory.from_dict(exp_data))

        # 4. Education
        for edu_data in data.get("education", []):
            builder.add_education(EducationFactory.from_dict(edu_data))

        # 5. Projects (top-level)
        for proj_data in data.get("projects", []):
            builder.add_project(ProjectFactory.from_dict(proj_data))

        # 6. Preferences
        cls._apply_preferences(builder, data.get("preferences", {}))

        # 7. Any unknown top-level keys → extra
        root_extra = _collect_extra(data, _KNOWN_ROOT_KEYS)
        for key, value in root_extra.items():
            builder.set_extra(key, value)

        return builder.build()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _apply_personal(cls, builder, personal: dict):
        if not personal:
            return
        builder.set_name(personal.get("name"))
        builder.set_email(personal.get("email"))
        builder.set_phone(personal.get("phone"))
        builder.set_location(personal.get("location"))
        builder.set_linkedin(personal.get("linkedin"))
        builder.set_github(personal.get("github"))
        builder.set_portfolio(personal.get("portfolio"))
        builder.set_summary(personal.get("summary"))

        # Extra personal fields
        for key, value in _collect_extra(personal, _KNOWN_PERSONAL_KEYS).items():
            builder.set_extra(f"personal.{key}", value)

    @classmethod
    def _apply_skills(cls, builder, skills: dict):
        if not skills:
            return

        # Technical skills → Skill objects
        technical = skills.get("technical", [])
        skill_objects = [SkillFactory.from_dict(s) for s in technical]
        builder.set_skills(skill_objects)

        # Soft skills
        builder.set_soft_skills(skills.get("soft", []))

        # Spoken languages
        builder.set_languages(skills.get("languages", []))

        # Certifications (may live under skills in the external schema)
        for cert_data in skills.get("certifications", []):
            builder.add_certification(CertFactory.from_dict(cert_data))

        # Extra skill-section fields
        for key, value in _collect_extra(skills, _KNOWN_SKILLS_KEYS).items():
            builder.set_extra(f"skills.{key}", value)

    @classmethod
    def _apply_preferences(cls, builder, prefs: dict):
        if not prefs:
            return
        # Store the full preferences dict
        builder.set_preferences(prefs)

        # Also stash unknown preference keys into extra
        for key, value in _collect_extra(prefs, _KNOWN_PREFERENCE_KEYS).items():
            builder.set_extra(f"preferences.{key}", value)
