class ExperienceBuilder:
    def __init__(self):
        self.role = None
        self.company_name = None
        self.dates = None
        self.location = None
        self.projects = []

    def with_role(self, role):
        self.role = role
        return self

    def with_company_name(self, company_name):
        self.company_name = company_name
        return self

    def with_dates(self, dates):
        self.dates = dates
        return self

    def with_location(self, location):
        self.location = location
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
        )


class Experience:
    def __init__(self, role, company_name, dates, location, projects):
        self.role = role
        self.company_name = company_name
        self.dates = dates
        self.location = location
        self.projects = projects

    def __str__(self):
        proj =  []
        for project in self.projects:
            for p in project:
                proj.append(p)
        proj = "\n".join(str(p) for p in proj)
        return f"Role: {self.role}\nCompany: {self.company_name}\nDates: {self.dates}\nLocation: {self.location}\nProjects:\n{proj}"


class ExperienceFactory:
    @staticmethod
    def create_experience(role, company_name, dates, location, projects):
        return ExperienceBuilder() \
            .with_role(role) \
            .with_company_name(company_name) \
            .with_dates(dates) \
            .with_location(location) \
            .add_project(projects) \
            .build()