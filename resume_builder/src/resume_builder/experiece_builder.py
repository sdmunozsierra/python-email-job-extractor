"""Experience and ExperienceBuilder -- work experience model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Experience:
    """Represents a single work experience entry.

    Supports both the new JSON schema fields and legacy fields for full
    backward compatibility.
    """

    def __init__(
        self,
        role: str = "",
        company_name: str = "",
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        current: bool = False,
        dates: Optional[str] = None,
        description: Optional[str] = None,
        achievements: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None,
        projects: Optional[List[str]] = None,
    ) -> None:
        self.role = role
        self.company_name = company_name
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        self.current = current
        self.dates = dates or self._compute_dates()
        self.description = description
        self.achievements = achievements or []
        self.technologies = technologies or []
        self.projects = projects or []

    def _compute_dates(self) -> str:
        if self.start_date:
            end = self.end_date or "Present"
            return f"{self.start_date} - {end}"
        return ""

    def __repr__(self) -> str:
        return f"Experience(role={self.role!r}, company_name={self.company_name!r})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "company_name": self.company_name,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "current": self.current,
            "dates": self.dates,
            "description": self.description,
            "achievements": self.achievements,
            "technologies": self.technologies,
            "projects": self.projects,
        }


class ExperienceBuilder:
    """Fluent builder for :class:`Experience`."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def role(self, role: str) -> "ExperienceBuilder":
        self._data["role"] = role
        return self

    def company_name(self, name: str) -> "ExperienceBuilder":
        self._data["company_name"] = name
        return self

    def location(self, loc: str) -> "ExperienceBuilder":
        self._data["location"] = loc
        return self

    def start_date(self, date: str) -> "ExperienceBuilder":
        self._data["start_date"] = date
        return self

    def end_date(self, date: str) -> "ExperienceBuilder":
        self._data["end_date"] = date
        return self

    def current(self, current: bool = True) -> "ExperienceBuilder":
        self._data["current"] = current
        return self

    def dates(self, dates: str) -> "ExperienceBuilder":
        self._data["dates"] = dates
        return self

    def description(self, desc: str) -> "ExperienceBuilder":
        self._data["description"] = desc
        return self

    def add_achievement(self, achievement: str) -> "ExperienceBuilder":
        self._data.setdefault("achievements", []).append(achievement)
        return self

    def add_technology(self, tech: str) -> "ExperienceBuilder":
        self._data.setdefault("technologies", []).append(tech)
        return self

    def build(self) -> Experience:
        return Experience(**self._data)
