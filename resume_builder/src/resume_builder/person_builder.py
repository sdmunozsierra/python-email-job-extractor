"""Person and PersonBuilder -- the central resume data model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .skill import Skill


class Person:
    """Container for all resume data.

    Every recognised field from the JSON schema is a first-class attribute.
    Unknown / extra fields are captured in :pyattr:`extra` so the builder is
    forward-compatible with schema extensions.
    """

    def __init__(
        self,
        name: str = "",
        email: Optional[str] = None,
        phone: Optional[str] = None,
        location: Optional[str] = None,
        linkedin: Optional[str] = None,
        github: Optional[str] = None,
        portfolio: Optional[str] = None,
        summary: Optional[str] = None,
        experience: Optional[List[Any]] = None,
        education: Optional[List[Any]] = None,
        skills: Optional[List[Skill]] = None,
        soft_skills: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        certifications: Optional[List[Any]] = None,
        projects: Optional[List[Any]] = None,
        activities: Optional[List[str]] = None,
        awards: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.email = email
        self.phone = phone
        self.location = location
        self.linkedin = linkedin
        self.github = github
        self.portfolio = portfolio
        self.summary = summary
        self.experience = experience or []
        self.education = education or []
        self.skills = skills or []
        self.soft_skills = soft_skills or []
        self.languages = languages or []
        self.certifications = certifications or []
        self.projects = projects or []
        self.activities = activities or []
        self.awards = awards or []
        self.preferences = preferences or {}
        self.extra = extra or {}

    def __repr__(self) -> str:
        return f"Person(name={self.name!r})"


class PersonBuilder:
    """Fluent builder for constructing a :class:`Person`."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def name(self, name: str) -> "PersonBuilder":
        self._data["name"] = name
        return self

    def email(self, email: str) -> "PersonBuilder":
        self._data["email"] = email
        return self

    def phone(self, phone: str) -> "PersonBuilder":
        self._data["phone"] = phone
        return self

    def location(self, location: str) -> "PersonBuilder":
        self._data["location"] = location
        return self

    def linkedin(self, url: str) -> "PersonBuilder":
        self._data["linkedin"] = url
        return self

    def github(self, url: str) -> "PersonBuilder":
        self._data["github"] = url
        return self

    def portfolio(self, url: str) -> "PersonBuilder":
        self._data["portfolio"] = url
        return self

    def summary(self, summary: str) -> "PersonBuilder":
        self._data["summary"] = summary
        return self

    def add_experience(self, exp: Any) -> "PersonBuilder":
        self._data.setdefault("experience", []).append(exp)
        return self

    def add_education(self, edu: Any) -> "PersonBuilder":
        self._data.setdefault("education", []).append(edu)
        return self

    def add_skill(self, skill: Skill) -> "PersonBuilder":
        self._data.setdefault("skills", []).append(skill)
        return self

    def add_certification(self, cert: Any) -> "PersonBuilder":
        self._data.setdefault("certifications", []).append(cert)
        return self

    def add_project(self, project: Any) -> "PersonBuilder":
        self._data.setdefault("projects", []).append(project)
        return self

    def preferences(self, prefs: Dict[str, Any]) -> "PersonBuilder":
        self._data["preferences"] = prefs
        return self

    def build(self) -> Person:
        return Person(**self._data)
