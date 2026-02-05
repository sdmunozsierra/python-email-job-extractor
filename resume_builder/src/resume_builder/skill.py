"""Skill model with name, level, years, and category."""

from __future__ import annotations

from typing import Any, Dict, Optional


class Skill:
    """Represents a technical skill with proficiency metadata.

    Attributes:
        name: Skill name (e.g. "Python").
        level: Proficiency level (beginner, intermediate, advanced, expert).
        years: Years of experience with the skill.
        category: Grouping category (languages, frameworks, databases, ...).
    """

    def __init__(
        self,
        name: str,
        level: Optional[str] = None,
        years: Optional[float] = None,
        category: Optional[str] = None,
    ) -> None:
        self.name = name
        self.level = level
        self.years = years
        self.category = category

    # ----- helpers -----
    def __str__(self) -> str:
        parts = [self.name]
        if self.level:
            parts.append(f"({self.level})")
        if self.years:
            parts.append(f"{self.years}y")
        return " ".join(parts)

    def __repr__(self) -> str:
        return f"Skill(name={self.name!r}, level={self.level!r}, years={self.years!r}, category={self.category!r})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "years": self.years,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data.get("name", ""),
            level=data.get("level"),
            years=data.get("years"),
            category=data.get("category"),
        )
