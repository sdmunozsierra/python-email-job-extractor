class EducationBuilder:
    def __init__(self):
        self.major = None
        self.minor = None
        self.school_name = None
        self.dates = None
        self.location = None
        self.gpa = 0.0
        self.coursework = []
        self.organizations = []
        self.research = []
        self.awards = []

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

    def with_location(self, location):
        self.location = location
        return self

    def with_gpa(self, gpa):
        self.gpa = gpa
        return self

    def with_coursework(self, coursework):
        self.coursework.append(coursework)
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
        return self
    #{
            #'major': self.major,
            #'minor': self.minor,
            #'school_name': self.school_name,
            #'dates': self.dates,
            #'location': self.location,
            #'gpa': self.gpa,
            #'coursework': self.coursework,
            #'organizations': self.organizations,
            #'research': self.research,
            #'awards': self.awards
        #}


class Education:
    def __init__(self, major, minor, school_name, dates, location, gpa, coursework, organizations, research, awards):
        self.major = major
        self.minor = minor
        self.school_name = school_name
        self.dates = dates
        self.location = location
        self.gpa = gpa
        self.coursework = coursework
        self.organizations = organizations
        self.research = research
        self.awards = awards

class EducationFactory:
    @staticmethod
    def create_education(major, minor, school_name, dates, location, gpa, coursework, organizations, research, awards):
        return EducationBuilder() \
            .with_major(major) \
            .with_minor(minor) \
            .with_school_name(school_name) \
            .with_dates(dates) \
            .with_location(location) \
            .with_gpa(gpa) \
            .with_coursework(coursework) \
            .with_organizations(organizations) \
            .with_research(research) \
            .with_awards(awards) \
            .build()