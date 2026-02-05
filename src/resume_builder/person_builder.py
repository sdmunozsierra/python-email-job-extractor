"""Person model and builder with support for the resume JSON schema."""


class PersonBuilder:
    def __init__(self):
        # Identity / contact — first-class fields from schema.personal
        self.name = None
        self.email = None
        self.phone = None
        self.location = None
        self.linkedin = None
        self.github = None
        self.portfolio = None
        self.summary = None

        # Core resume sections
        self.experience = []
        self.education = []
        self.skills = []          # list[Skill] — structured technical skills
        self.soft_skills = []     # list[str]  — from schema.skills.soft
        self.languages = []       # list[dict] — spoken languages {language, proficiency}
        self.certifications = []
        self.projects = []        # top-level projects from schema.projects
        self.activities = []
        self.awards = []

        # Preferences (desired roles, industries, locations, etc.)
        self.preferences = {}

        # Legacy / catch-all
        self.personal_info = {}   # kept for backward compatibility
        self.extra = {}           # catch-all for truly unexpected data

    # --- Identity setters ---------------------------------------------------

    def set_name(self, name):
        self.name = name
        return self

    def set_email(self, email):
        self.email = email
        return self

    def set_phone(self, phone):
        self.phone = phone
        return self

    def set_location(self, location):
        self.location = location
        return self

    def set_linkedin(self, linkedin):
        self.linkedin = linkedin
        return self

    def set_github(self, github):
        self.github = github
        return self

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio
        return self

    def set_summary(self, summary):
        self.summary = summary
        return self

    # --- Core resume sections -----------------------------------------------

    def add_experience(self, experience):
        self.experience.append(experience)
        return self

    def add_education(self, education):
        self.education.append(education)
        return self

    def add_skill(self, skill):
        self.skills.append(skill)
        return self

    def set_skills(self, skills):
        self.skills = skills
        return self

    def set_soft_skills(self, soft_skills):
        self.soft_skills = soft_skills
        return self

    def add_soft_skill(self, soft_skill):
        self.soft_skills.append(soft_skill)
        return self

    def set_languages(self, languages):
        self.languages = languages
        return self

    def add_language(self, language):
        self.languages.append(language)
        return self

    def add_certification(self, certification):
        self.certifications.append(certification)
        return self

    def set_certs(self, certs):
        self.certifications = certs
        return self

    def add_project(self, project):
        self.projects.append(project)
        return self

    def set_projects(self, projects):
        self.projects = projects
        return self

    def add_activity(self, activity):
        self.activities.append(activity)
        return self

    def add_award(self, award):
        self.awards.append(award)
        return self

    # --- Preferences --------------------------------------------------------

    def set_preferences(self, preferences):
        self.preferences = preferences
        return self

    # --- Legacy / catch-all -------------------------------------------------

    def add_personal_info(self, key, value):
        self.personal_info[key] = value
        return self

    def set_extra(self, key, value):
        """Store any data that does not fit an existing field."""
        self.extra[key] = value
        return self

    # --- Build --------------------------------------------------------------

    def build(self):
        return Person(
            name=self.name,
            email=self.email,
            phone=self.phone,
            location=self.location,
            linkedin=self.linkedin,
            github=self.github,
            portfolio=self.portfolio,
            summary=self.summary,
            experience=self.experience,
            education=self.education,
            skills=self.skills,
            soft_skills=self.soft_skills,
            languages=self.languages,
            certifications=self.certifications,
            projects=self.projects,
            activities=self.activities,
            awards=self.awards,
            preferences=self.preferences,
            personal_info=self.personal_info,
            extra=self.extra,
        )


class Person:
    """Represents a person's complete resume data."""

    def __init__(
        self,
        experience=None,
        education=None,
        skills=None,
        certifications=None,
        activities=None,
        awards=None,
        personal_info=None,
        # New first-class fields
        name=None,
        email=None,
        phone=None,
        location=None,
        linkedin=None,
        github=None,
        portfolio=None,
        summary=None,
        soft_skills=None,
        languages=None,
        projects=None,
        preferences=None,
        extra=None,
    ):
        # Identity / contact
        self.name = name
        self.email = email
        self.phone = phone
        self.location = location
        self.linkedin = linkedin
        self.github = github
        self.portfolio = portfolio
        self.summary = summary

        # Core resume sections
        self.experience = experience or []
        self.education = education or []
        self.skills = skills or []
        self.soft_skills = soft_skills or []
        self.languages = languages or []
        self.certifications = certifications or []
        self.projects = projects or []
        self.activities = activities or []
        self.awards = awards or []

        # Preferences
        self.preferences = preferences or {}

        # Legacy / catch-all
        self.personal_info = personal_info or {}
        self.extra = extra or {}

        # Convenience aliases kept for backward-compat with main.py
        self.job_title = None

    def __str__(self) -> str:
        return f"{self.__dict__}"
