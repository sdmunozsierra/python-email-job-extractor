class ProjectBuilder:
    def __init__(self):
        self.name = None
        self.description = None
        self.duration = None
        self.team_size = 0
        self.actions = []
        self.skills = []

    def with_name(self, name):
        self.name = name
        return self

    def with_description(self, description):
        self.description = description
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

    def add_skill(self, skill):
        self.skills.append(skill)
        return self

    def build(self):
        return Project(
            self.name,
            self.description,
            self.duration,
            self.team_size,
            self.actions,
            self.skills,
        )


class Project:
    def __init__(self, name, description, duration, team_size, actions, skills):
        self.name = name
        self.description = description
        self.duration = duration
        self.team_size = team_size
        self.actions = actions
        self.skills = skills

    def __str__(self) -> str:
        return f'{self.__dict__}'

class ProjectFactory:
    @staticmethod
    def create_project(name, description, duration, team_size, actions, skills):
        return Project(name, description, duration, team_size, actions, skills)
