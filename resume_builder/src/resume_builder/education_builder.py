"""Education and EducationBuilder -- education entry model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Education:
    """Represents a single education entry."""

    def __init__(
        self,
        degree: str = "",
        field: Optional[str] = None,
        major: Optional[str] = None,
        minor: Optional[str] = None,
        school_name: str = "",
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dates: Optional[str] = None,
        gpa: Optional[str] = None,
        honors: Optional[str] = None,
        coursework: Optional[List[str]] = None,
        organizations: Optional[List[str]] = None,
        research: Optional[List[str]] = None,
        awards: Optional[List[str]] = None,
    ) -> None:
        self.degree = degree
        self.field = field
        self.major = major
        self.minor = minor
        self.school_name = school_name
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        self.dates = dates or self._compute_dates()
        self.gpa = gpa
        self.honors = honors
        self.coursework = coursework or []
        self.organizations = organizations or []
        self.research = research or []
        self.awards = awards or []

    def _compute_dates(self) -> str:
        if self.start_date:
            end = self.end_date or "Present"
            return f"{self.start_date} - {end}"
        return ""

    def __repr__(self) -> str:
        return f"Education(degree={self.degree!r}, school_name={self.school_name!r})"


class EducationBuilder:
    """Fluent builder for :class:`Education`."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def degree(self, degree: str) -> "EducationBuilder":
        self._data["degree"] = degree
        return self

    def field(self, field: str) -> "EducationBuilder":
        self._data["field"] = field
        return self

    def school_name(self, name: str) -> "EducationBuilder":
        self._data["school_name"] = name
        return self

    def location(self, loc: str) -> "EducationBuilder":
        self._data["location"] = loc
        return self

    def start_date(self, date: str) -> "EducationBuilder":
        self._data["start_date"] = date
        return self

    def end_date(self, date: str) -> "EducationBuilder":
        self._data["end_date"] = date
        return self

    def gpa(self, gpa: str) -> "EducationBuilder":
        self._data["gpa"] = gpa
        return self

    def honors(self, honors: str) -> "EducationBuilder":
        self._data["honors"] = honors
        return self

    def build(self) -> Education:
        return Education(**self._data)
