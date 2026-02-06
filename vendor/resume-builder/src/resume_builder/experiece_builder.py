"""Experience model and builder with support for the resume JSON schema."""


class ExperienceBuilder:
    def __init__(self):
        self.role = None
        self.company_name = None
        self.dates = None          # legacy free-text date range
        self.start_date = None     # ISO date string e.g. "2023-11"
        self.end_date = None       # ISO date string or None
        self.current = False
        self.location = None
        self.description = None    # high-level description of the role
        self.achievements = []     # list[str] — bullet-point achievements
        self.technologies = []     # list[str] — technologies used at this role
        self.projects = []         # nested project objects (legacy format)

    def with_role(self, role):
        self.role = role
        return self

    def with_company_name(self, company_name):
        self.company_name = company_name
        return self

    def with_dates(self, dates):
        self.dates = dates
        return self

    def with_start_date(self, start_date):
        self.start_date = start_date
        return self

    def with_end_date(self, end_date):
        self.end_date = end_date
        return self

    def with_current(self, current):
        self.current = current
        return self

    def with_location(self, location):
        self.location = location
        return self

    def with_description(self, description):
        self.description = description
        return self

    def add_achievement(self, achievement):
        self.achievements.append(achievement)
        return self

    def set_achievements(self, achievements):
        self.achievements = achievements
        return self

    def set_technologies(self, technologies):
        self.technologies = technologies
        return self

    def add_project(self, project):
        self.projects.append(project)
        return self

    def build(self):
        return Experience(
            self.role,
            self.company_name,
            self.dates,
            self.location,
            self.projects,
            start_date=self.start_date,
            end_date=self.end_date,
            current=self.current,
            description=self.description,
            achievements=self.achievements,
            technologies=self.technologies,
        )


class Experience:
    """Represents a single work experience entry.

    Supports both the legacy format (nested projects with actions/skills)
    and the new JSON schema format (flat achievements + technologies).
    """

    def __init__(
        self,
        role,
        company_name,
        dates,
        location,
        projects,
        start_date=None,
        end_date=None,
        current=False,
        description=None,
        achievements=None,
        technologies=None,
    ):
        self.role = role
        self.company_name = company_name
        self.dates = dates
        self.start_date = start_date
        self.end_date = end_date
        self.current = current
        self.location = location
        self.description = description
        self.achievements = achievements or []
        self.technologies = technologies or []
        self.projects = projects

    @property
    def date_range(self):
        """Return a human-readable date range string."""
        if self.dates:
            return self.dates
        start = self.start_date or "?"
        end = "Present" if self.current else (self.end_date or "?")
        return f"{start} - {end}"

    def __str__(self):
        proj = []
        if self.projects:
            for project in self.projects:
                if isinstance(project, list):
                    for p in project:
                        proj.append(str(p))
                else:
                    proj.append(str(project))
        proj_str = "\n".join(proj) if proj else ""

        ach_str = ""
        if self.achievements:
            ach_str = "\nAchievements:\n" + "\n".join(
                f"  - {a}" for a in self.achievements
            )

        tech_str = ""
        if self.technologies:
            tech_str = "\nTechnologies: " + ", ".join(self.technologies)

        desc_str = ""
        if self.description:
            desc_str = f"\nDescription: {self.description}"

        parts = [
            f"Role: {self.role}",
            f"Company: {self.company_name}",
            f"Dates: {self.date_range}",
            f"Location: {self.location}",
        ]
        if desc_str:
            parts.append(desc_str)
        if proj_str:
            parts.append(f"Projects:\n{proj_str}")
        if ach_str:
            parts.append(ach_str)
        if tech_str:
            parts.append(tech_str)

        return "\n".join(parts)


class ExperienceFactory:
    @staticmethod
    def create_experience(role, company_name, dates, location, projects):
        """Legacy factory method — creates experience with nested projects."""
        return (
            ExperienceBuilder()
            .with_role(role)
            .with_company_name(company_name)
            .with_dates(dates)
            .with_location(location)
            .add_project(projects)
            .build()
        )

    @staticmethod
    def from_dict(data):
        """Create an Experience from a JSON schema dict."""
        builder = ExperienceBuilder()
        builder.with_role(data.get("title"))
        builder.with_company_name(data.get("company"))
        builder.with_location(data.get("location"))
        builder.with_start_date(data.get("start_date"))
        builder.with_end_date(data.get("end_date"))
        builder.with_current(data.get("current", False))
        builder.with_description(data.get("description"))
        builder.set_achievements(data.get("achievements", []))
        builder.set_technologies(data.get("technologies", []))

        # Build a legacy-compatible dates string
        start = data.get("start_date", "?")
        end = "Present" if data.get("current") else (data.get("end_date") or "?")
        builder.with_dates(f"{start} - {end}")

        return builder.build()
