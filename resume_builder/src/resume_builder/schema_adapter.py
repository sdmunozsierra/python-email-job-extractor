"""Adapter that converts a JSON resume schema dict into internal models.

This is the primary programmatic entry point for consumers that want to
load a resume from JSON and hand it to :func:`resume_builder.cli.build_resume`.

Usage::

    from resume_builder.schema_adapter import ResumeSchemaAdapter

    person = ResumeSchemaAdapter.from_json_file("resume.json")
    # -- or --
    person = ResumeSchemaAdapter.from_dict(data)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cert_builder import Cert
from .education_builder import Education
from .experiece_builder import Experience
from .person_builder import Person
from .project_builder import Project
from .skill import Skill


class ResumeSchemaAdapter:
    """Convert a standardised JSON resume schema into a :class:`Person`."""

    # ------------------------------------------------------------------
    # Public class methods
    # ------------------------------------------------------------------

    @classmethod
    def from_json_file(cls, path: str | Path) -> Person:
        """Load a JSON file and return a :class:`Person`."""
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Person:
        """Build a :class:`Person` from a resume-schema dict.

        Every recognised key is mapped to a first-class attribute.  Unknown
        keys are collected in ``person.extra``.
        """
        personal = data.get("personal", {}) or {}
        skills_data = data.get("skills", {}) or {}
        experience_data = data.get("experience", []) or []
        education_data = data.get("education", []) or []
        projects_data = data.get("projects", []) or []
        preferences_data = data.get("preferences", {}) or {}

        # Skills
        technical_skills = cls._parse_technical_skills(skills_data.get("technical", []))
        soft_skills: List[str] = skills_data.get("soft", []) or []
        languages: List[str] = cls._parse_languages(skills_data.get("languages", []))
        certifications = cls._parse_certifications(skills_data.get("certifications", []))

        # Experience
        experience = cls._parse_experience(experience_data)

        # Education
        education = cls._parse_education(education_data)

        # Projects
        projects = cls._parse_projects(projects_data)

        # Collect unknown top-level keys into extra
        known_keys = {"personal", "skills", "experience", "education", "projects", "preferences"}
        extra = {k: v for k, v in data.items() if k not in known_keys}

        return Person(
            name=personal.get("name", ""),
            email=personal.get("email"),
            phone=personal.get("phone"),
            location=personal.get("location"),
            linkedin=personal.get("linkedin"),
            github=personal.get("github"),
            portfolio=personal.get("portfolio"),
            summary=personal.get("summary"),
            experience=experience,
            education=education,
            skills=technical_skills,
            soft_skills=soft_skills,
            languages=languages,
            certifications=certifications,
            projects=projects,
            preferences=preferences_data,
            extra=extra,
        )

    # ------------------------------------------------------------------
    # Internal parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_technical_skills(raw: List[Any]) -> List[Skill]:
        skills: List[Skill] = []
        for item in raw or []:
            if isinstance(item, dict):
                skills.append(Skill(
                    name=item.get("name", ""),
                    level=item.get("level"),
                    years=item.get("years"),
                    category=item.get("category"),
                ))
            elif isinstance(item, str):
                skills.append(Skill(name=item))
        return skills

    @staticmethod
    def _parse_languages(raw: List[Any]) -> List[str]:
        langs: List[str] = []
        for item in raw or []:
            if isinstance(item, dict):
                lang = item.get("language", "")
                prof = item.get("proficiency")
                langs.append(f"{lang} ({prof})" if prof else lang)
            elif isinstance(item, str):
                langs.append(item)
        return langs

    @staticmethod
    def _parse_certifications(raw: List[Any]) -> List[Cert]:
        certs: List[Cert] = []
        for item in raw or []:
            if isinstance(item, dict):
                certs.append(Cert(
                    title=item.get("name") or item.get("title", ""),
                    issuer=item.get("issuer"),
                    completion_date=item.get("date") or item.get("completion_date"),
                    expiry=item.get("expiry"),
                    credential_id=item.get("credential_id"),
                ))
            elif isinstance(item, str):
                certs.append(Cert(title=item))
        return certs

    @staticmethod
    def _parse_experience(raw: List[Dict[str, Any]]) -> List[Experience]:
        entries: List[Experience] = []
        for item in raw or []:
            entries.append(Experience(
                role=item.get("title", ""),
                company_name=item.get("company", ""),
                location=item.get("location"),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                current=item.get("current", False),
                description=item.get("description"),
                achievements=item.get("achievements", []) or [],
                technologies=item.get("technologies", []) or [],
            ))
        return entries

    @staticmethod
    def _parse_education(raw: List[Dict[str, Any]]) -> List[Education]:
        entries: List[Education] = []
        for item in raw or []:
            entries.append(Education(
                degree=item.get("degree", ""),
                field=item.get("field"),
                school_name=item.get("institution", ""),
                location=item.get("location"),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                gpa=item.get("gpa"),
                honors=item.get("honors"),
                coursework=item.get("relevant_coursework", []) or [],
            ))
        return entries

    @staticmethod
    def _parse_projects(raw: List[Dict[str, Any]]) -> List[Project]:
        entries: List[Project] = []
        for item in raw or []:
            entries.append(Project(
                name=item.get("name", ""),
                description=item.get("description"),
                url=item.get("url"),
                technologies=item.get("technologies", []) or [],
                highlights=item.get("highlights", []) or [],
            ))
        return entries
