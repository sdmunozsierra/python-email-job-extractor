"""Project model and builder with support for the resume JSON schema."""


class ProjectBuilder:
    def __init__(self):
        self.name = None
        self.description = None
        self.url = None
        self.duration = None
        self.team_size = 0
        self.actions = []          # legacy — bullet-point action items
        self.highlights = []       # new schema — key highlights
        self.skills = []           # legacy — skill tags
        self.technologies = []     # new schema — technologies used

    def with_name(self, name):
        self.name = name
        return self

    def with_description(self, description):
        self.description = description
        return self

    def with_url(self, url):
        self.url = url
        return self

    def with_duration(self, duration):
        self.duration = duration
        return self

    def with_team_size(self, team_size):
        self.team_size = team_size
        return self

    def add_action(self, action):
        self.actions.append(action)
        return self

    def set_actions(self, actions):
        self.actions = actions
        return self

    def set_highlights(self, highlights):
        self.highlights = highlights
        return self

    def add_skill(self, skill):
        self.skills.append(skill)
        return self

    def set_skills(self, skills):
        self.skills = skills
        return self

    def set_technologies(self, technologies):
        self.technologies = technologies
        return self

    def build(self):
        return Project(
            self.name,
            self.description,
            self.duration,
            self.team_size,
            self.actions,
            self.skills,
            url=self.url,
            highlights=self.highlights,
            technologies=self.technologies,
        )


class Project:
    """Represents a project entry.

    Supports both the legacy format (actions, skills, team_size, duration)
    and the new JSON schema format (url, technologies, highlights).
    """

    def __init__(
        self,
        name,
        description,
        duration=None,
        team_size=0,
        actions=None,
        skills=None,
        url=None,
        highlights=None,
        technologies=None,
    ):
        self.name = name
        self.description = description
        self.duration = duration
        self.team_size = team_size
        self.actions = actions or []
        self.skills = skills or []
        self.url = url
        self.highlights = highlights or []
        self.technologies = technologies or []

    @property
    def all_bullets(self):
        """Return combined actions + highlights for display."""
        return self.actions + self.highlights

    @property
    def all_tech(self):
        """Return combined skills + technologies for display."""
        return list(dict.fromkeys(self.skills + self.technologies))

    def __str__(self) -> str:
        return f"{self.__dict__}"


class ProjectFactory:
    @staticmethod
    def create_project(name, description, duration, team_size, actions, skills):
        """Legacy factory method."""
        return Project(name, description, duration, team_size, actions, skills)

    @staticmethod
    def from_dict(data):
        """Create a Project from a JSON schema dict."""
        return (
            ProjectBuilder()
            .with_name(data.get("name"))
            .with_description(data.get("description"))
            .with_url(data.get("url"))
            .set_technologies(data.get("technologies", []))
            .set_highlights(data.get("highlights", []))
            .build()
        )
