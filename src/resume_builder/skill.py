"""Skill model for structured technical skills."""


class SkillBuilder:
    def __init__(self):
        self.name = None
        self.level = None
        self.years = None
        self.category = None

    def with_name(self, name):
        self.name = name
        return self

    def with_level(self, level):
        self.level = level
        return self

    def with_years(self, years):
        self.years = years
        return self

    def with_category(self, category):
        self.category = category
        return self

    def build(self):
        return Skill(self.name, self.level, self.years, self.category)


class Skill:
    """Represents a structured technical skill with level, years, and category."""

    def __init__(self, name, level=None, years=None, category=None):
        self.name = name
        self.level = level
        self.years = years
        self.category = category

    def __str__(self):
        parts = [self.name]
        if self.level:
            parts.append(f"({self.level})")
        if self.years:
            parts.append(f"{self.years}y")
        return " ".join(parts)

    def __repr__(self):
        return f"Skill(name={self.name!r}, level={self.level!r}, years={self.years!r}, category={self.category!r})"

    def __eq__(self, other):
        if isinstance(other, Skill):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        if isinstance(other, Skill):
            return (self.name or "") < (other.name or "")
        if isinstance(other, str):
            return (self.name or "") < other
        return NotImplemented


class SkillFactory:
    @staticmethod
    def create_skill(name, level=None, years=None, category=None):
        return Skill(name, level, years, category)

    @staticmethod
    def from_dict(data):
        """Create a Skill from a JSON schema dict."""
        return Skill(
            name=data.get("name"),
            level=data.get("level"),
            years=data.get("years"),
            category=data.get("category"),
        )

    @staticmethod
    def from_string(name):
        """Create a simple Skill from just a name string (backward compat)."""
        return Skill(name=name)
