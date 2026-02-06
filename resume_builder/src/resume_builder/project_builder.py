"""Project and ProjectBuilder -- project entry model."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Project:
    """Represents a project entry."""

    def __init__(
        self,
        name: str = "",
        description: Optional[str] = None,
        url: Optional[str] = None,
        duration: Optional[str] = None,
        team_size: Optional[int] = None,
        actions: Optional[List[str]] = None,
        highlights: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.url = url
        self.duration = duration
        self.team_size = team_size
        self.actions = actions or []
        self.highlights = highlights or []
        self.skills = skills or []
        self.technologies = technologies or []

    def __repr__(self) -> str:
        return f"Project(name={self.name!r})"


class ProjectBuilder:
    """Fluent builder for :class:`Project`."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def name(self, name: str) -> "ProjectBuilder":
        self._data["name"] = name
        return self

    def description(self, desc: str) -> "ProjectBuilder":
        self._data["description"] = desc
        return self

    def url(self, url: str) -> "ProjectBuilder":
        self._data["url"] = url
        return self

    def add_highlight(self, highlight: str) -> "ProjectBuilder":
        self._data.setdefault("highlights", []).append(highlight)
        return self

    def add_technology(self, tech: str) -> "ProjectBuilder":
        self._data.setdefault("technologies", []).append(tech)
        return self

    def build(self) -> Project:
        return Project(**self._data)
