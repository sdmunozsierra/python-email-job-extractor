"""Education model and builder with support for the resume JSON schema."""


class EducationBuilder:
    def __init__(self):
        self.degree = None           # e.g. "Bachelor of Science"
        self.field = None            # e.g. "Computer Science (Minor in Mathematics)"
        self.major = None            # legacy — kept for backward compat
        self.minor = None            # legacy
        self.school_name = None      # maps to schema "institution"
        self.dates = None            # legacy free-text date
        self.start_date = None       # ISO date string
        self.end_date = None         # ISO date string
        self.location = None
        self.gpa = None
        self.honors = None           # e.g. "Dean's List"
        self.coursework = []
        self.organizations = []
        self.research = []
        self.awards = []

    def with_degree(self, degree):
        self.degree = degree
        return self

    def with_field(self, field):
        self.field = field
        return self

    def with_major(self, major):
        self.major = major
        return self

    def with_minor(self, minor):
        self.minor = minor
        return self

    def with_school_name(self, school_name):
        self.school_name = school_name
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

    def with_location(self, location):
        self.location = location
        return self

    def with_gpa(self, gpa):
        self.gpa = gpa
        return self

    def with_honors(self, honors):
        self.honors = honors
        return self

    def with_coursework(self, coursework):
        self.coursework.append(coursework)
        return self

    def set_coursework(self, coursework):
        self.coursework = coursework
        return self

    def with_organizations(self, organizations):
        self.organizations.append(organizations)
        return self

    def with_research(self, research):
        self.research.append(research)
        return self

    def with_awards(self, awards):
        self.awards.append(awards)
        return self

    def build(self):
        return Education(
            degree=self.degree,
            field=self.field,
            major=self.major,
            minor=self.minor,
            school_name=self.school_name,
            dates=self.dates,
            start_date=self.start_date,
            end_date=self.end_date,
            location=self.location,
            gpa=self.gpa,
            honors=self.honors,
            coursework=self.coursework,
            organizations=self.organizations,
            research=self.research,
            awards=self.awards,
        )


class Education:
    """Represents an education entry.

    Supports both the legacy format (major/minor/school_name)
    and the new JSON schema format (degree/field/institution).
    """

    def __init__(
        self,
        degree=None,
        field=None,
        major=None,
        minor=None,
        school_name=None,
        dates=None,
        start_date=None,
        end_date=None,
        location=None,
        gpa=None,
        honors=None,
        coursework=None,
        organizations=None,
        research=None,
        awards=None,
    ):
        self.degree = degree
        self.field = field
        self.major = major or (field.split("(")[0].strip() if field else None)
        self.minor = minor
        self.school_name = school_name
        self.dates = dates
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.gpa = gpa
        self.honors = honors
        self.coursework = coursework or []
        self.organizations = organizations or []
        self.research = research or []
        self.awards = awards or []

    @property
    def date_range(self):
        if self.dates:
            return self.dates
        start = self.start_date or ""
        end = self.end_date or ""
        if start and end:
            return f"{start} - {end}"
        return end or start or ""

    @property
    def display_title(self):
        """Human-readable title for this education entry."""
        if self.degree and self.field:
            return f"{self.degree} in {self.field}"
        if self.major and self.minor:
            return f"Bachelor of Science in {self.major} and Minor in {self.minor}"
        if self.major:
            return f"Degree in {self.major}"
        return self.field or self.degree or ""

    def __str__(self):
        return (
            f"{self.display_title} — {self.school_name} ({self.date_range})"
        )


class EducationFactory:
    @staticmethod
    def create_education(
        major, minor, school_name, dates, location, gpa, coursework,
        organizations, research, awards
    ):
        """Legacy factory method."""
        return (
            EducationBuilder()
            .with_major(major)
            .with_minor(minor)
            .with_school_name(school_name)
            .with_dates(dates)
            .with_location(location)
            .with_gpa(gpa)
            .with_coursework(coursework)
            .with_organizations(organizations)
            .with_research(research)
            .with_awards(awards)
            .build()
        )

    @staticmethod
    def from_dict(data):
        """Create an Education from a JSON schema dict."""
        builder = EducationBuilder()
        builder.with_degree(data.get("degree"))
        builder.with_field(data.get("field"))
        builder.with_school_name(data.get("institution"))
        builder.with_start_date(data.get("start_date"))
        builder.with_end_date(data.get("end_date"))
        builder.with_location(data.get("location"))
        builder.with_gpa(data.get("gpa"))
        builder.with_honors(data.get("honors"))
        builder.set_coursework(data.get("relevant_coursework", []))
        return builder.build()
