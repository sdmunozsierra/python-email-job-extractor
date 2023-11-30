class PersonBuilder:
    def __init__(self):
        self.name = None
        self.experience = []
        self.education = []
        self.skills = []
        self.certifications = []
        self.activities = []
        self.awards = []
        self.personal_info = {}

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

    def add_certification(self, certification):
        self.certifications.append(certification)
        return self

    def set_certs(self, certs):
        self.certifications = certs
        return self

    def add_activity(self, activity):
        self.activities.append(activity)
        return self

    def add_award(self, award):
        self.awards.append(award)
        return self

    def add_personal_info(self, key, value):
        self.personal_info[key] = value
        return self

    def build(self):
        return Person(
            self.experience,
            self.education,
            self.skills,
            self.certifications,
            self.activities,
            self.awards,
            self.personal_info,
        )


class Person:
    def __init__(
        self,
        experience,
        education,
        skills,
        certifications,
        activities,
        awards,
        personal_info,
    ):
        self.experience = experience
        self.education = education
        self.skills = skills
        self.certifications = certifications
        self.activities = activities
        self.awards = awards
        self.personal_info = personal_info

    def __str__(self) -> str:
        return f'{self.__dict__}'