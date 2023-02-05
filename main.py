import docx
from person_builder import PersonBuilder
from experiece_builder import ExperienceBuilder
from experiece_builder import ExperienceFactory
from project_builder import ProjectBuilder
from project_builder import ProjectFactory
from cert_builder import CertFactory
from format_experience import format_experience, format_experience_skills



experience = ExperienceBuilder() \
    .with_role("Software Engineer") \
    .with_company_name("Google") \
    .with_dates("January 2020 - Present") \
    .add_project("Project A") \
    .add_project("Project B") \
    .build()

project = ProjectBuilder() \
    .with_name("Project X") \
    .with_description("A sample project.") \
    .with_duration("6 months") \
    .add_action("Developed a new feature.") \
    .add_action("Fixed several bugs.") \
    .add_skill("Java") \
    .add_skill("JavaScript") \
    .build()

person = PersonBuilder() \
    .add_experience("Software Engineer at Google") \
    .add_education("Bachelor's degree in Computer Science from MIT") \
    .add_skill("Python") \
    .add_certification("AWS Solutions Architect") \
    .add_activity("Volunteer at a local homeless shelter") \
    .add_award("Best Employee of the Year award at Google") \
    .add_personal_info("Name", "John Doe") \
    .add_personal_info("Age", 30) \
    .build()

project = ProjectBuilder() \
    .with_name("Capital One: Purple Rain") \
    .with_description("AWS Optimization for performance and cost on log metrics.")\
    .with_duration("6 months") \
    .add_action("Ingest semi-structured data insto singe repository, apply cleansing, enrichment, business logic rules.")\
    .add_skill("log-stash") \
    .add_skill("elastic-stack") \
    .add_action("Self service through custom Models into playbooks.") \
    .add_skill("ansible") \
    .add_action("Story telling including KPIs, Dashboards and Scoreboards that utilized proven design strategies.") \
    .add_skill("Data-Driven Culture") \
    .add_skill("datadog") \
    .add_skill("kibana") \
    .build()

infinitive_experience = ExperienceFactory.create_experience(
    "Principal Full Stack",
    "Infinitive",
    "Jan 2022 - May 2022",
    "Ashburn, VA",
    [project]
)

p1 = ProjectFactory.create_project(
    "Cloud Distributed Scraping System",
    "Led a team to architect and create a web scraper prototype.",
    "1 year",
    5,
    ["Manage and orchestrate environment with fullstack automation of 20+ microservices.",
        "Scripts that accelerated deployment time from days to less than 10 minutes.",
        "Continuous integration and testing into a testing environment backend API app.",
        "Cloud deploy and maintain testing and production environments.",
        "Software engineering on all levels of the stack.",
        "Data pipeline management with visualizations at different spots."],
    ["docker-compose", "bash", "gitlab-ops","express", "aws", "kafka", "python", "redis", "elastic-search", "minio", "traefik", "sql"]
)

p2 = ProjectFactory.create_project(
    "Spring Backend Microservices",
    "Lead a team to implement a data searching backend app.",
    duration="2 years",
    team_size=7,
    actions=["Deliver a SpringBoot app that provides backend microservices oriented APIs.",
        "Scripts that interacts with containers to perform management actions.",
        "Setup REST environment to allow CRUD and advanced operations and interactions.",
        "Secure File management with SSL enabled, file metadata to SQL with custom validation.",
        "Analyze the code against security and coverage metrics. Raised from 35% to 75% in code coverage. Fixed 100+ bugs."],
    skills=["spring-boot", "spring-data", "docker-compose", "gitlab-ops", "mvn-spring-profiles", "minio", "sonarqube"]
)

p3 = ProjectFactory.create_project(
    "AWS Metrics Analysis",
    "R&D: Python AWS CloudWatch metrics analyzer.",
    "2 months",
    1,
    ["Prototype analysis on metrics from AWS uaing only python.",
        "Real-time Cloudwatch parsing from multiple AWS instances of type Redis and S3.",
        "Deploy a dynamic flask app where metrics were organized and added to a local database.",
        "Forecast usage and cost per active instance using AI models and big data analysis.",
        "Automatic unit and regression testing with over 95% code coverage."],
    ["python-boto3","python-flask", "python-pands", "python-sqlalchemy", "tensorflow", "python-pytest", "sql-lite"]
)

p4 = ProjectFactory.create_project(
    "Healthcare - mlnOpedia",
    "Mobile App and services support.",
    "3 months",
    10,
    ["Helped on the development of the Android portion of the project.",
        "Added push notifications with firebase to alert users on recommendations and updates.",
        "Scripts that automated safe data bulk upload to local and remote servers. Now used across the company."],
    ["java-android", "objectivec", "python"]
)

p5 = ProjectFactory.create_project(
    "Android Bluetooth Microprocessor Technology",
    "R&D: Android bluetooth beacon modification and discovery",
    "2 months",
    3,
    ["Maintain and update low level code to run on any linux device that can run BlueZ protocol.",
        "Prototyped a bluetooth mesh using 4 raspberry devices.",
        "Ability to track and locate users using bluetooth beacon packets."],
    ["java-android", "c"]
)

cp1 = ProjectFactory.create_project(
    "Cleta.io",
    "Web3 automated serverless architecture running on AWS prototype.",
    "2 years",
    5,
    ["Architecture and deploy a serverless cloud infrastructure.",
        "Implemented GraphQL schemas, queries, and mutations, tested with AVA.",
        "UI/UX design with interactive wireframing into fullstrack js integrations.",
        "Continuous Delivery from hot-commit to global within 3 minutes.",
        "Smart contracts with tets to deploy into Infura or private Ethereum cloud nodes.",
        "Client facing on cutting edge technologies.",
        "Web3 technology vision, strategy and direction."],
    ["aws-amplify", "aws-dynamo", "aws-s3", "aws-route53", "aws-vpc", "graphql", "ava", "adobe-xd", "nuxt", "solidity"]
)

leidos_experience = ExperienceFactory.create_experience(
    "Lead Software Engineer",
    "Leidos, Inc.",
    "Jan 2018 - Jan 2022",
    "Reston, VA",
    [p1, p2, p3, p4, p5],
)

cleta_experience = ExperienceFactory.create_experience(
    "Founder",
    "Cleta LLC",
    "August 2020 - Present",
    "Arlington, VA",
    [cp1]
)

certs = CertFactory.from_file("certs.txt")
for cert in certs:
    print(cert)

sergio_builder = PersonBuilder()\
    .add_experience(cleta_experience)\
    .add_experience(infinitive_experience)\
    .add_experience(leidos_experience) \
    .add_education("Bachelors degree in Computer Science and Minor in Math from UTEP") \
    .set_skills(
        ["postman", "REST", "sonarqube", "swagger-api",
                "aws-aurora","mongo-db", "graphql", "redis", "sql",
                "java-8+","java-android", "mvn",
                "js-node", "js-vue", "js-nuxt", "js-express",
                "python2", "python3", "python-scrapy", "python-flask", "python-pandas",
                "spring-boot", "spring-security", "spring-profiles", "spring-data",
                "bash", "kafka", "vim", "yarn","solidity",
                "html", "css", "php", "jinja",
                "git", "github-actions", "gitlab-cicd",
                "aws-amplify", "aws-iam", "aws-serverless", "aws-vpc", "aws-codepipeline", "aws-cloudformation",
                "ansible", "consul", "kubernetes-training",
                "docker", "docker-compose", "docker-swarm", "docker-images",
                "elastic-stack", "elastic-search", "log-stash", "kibana",
                "arch-linux", "centos", "debian", "mint", "xbuntu", "proxmox",
                "english-fluent", "spanish-fluent", "french-wp"])\
    .add_activity("1st Place - 2019 RESET Hackathon (Blockchain)")\
    .add_activity("2nd Place - 2021 Verac Hackathon (Android)")\
    .add_activity("3rd Place - 2018 UTD Research Symposium (Android)")\
    .add_activity("4th Place - 2020 SANS Institue CTF (Pen Testing)")\
    .set_certs(certs)
sergio = sergio_builder.build()
#print(sergio)
#for e in sergio.experience:
    #print(e)

def build_resume(person):
    # Create a Word document object
    doc = docx.Document()

    # Add a header with the name and job title
    header = doc.add_heading(person.name, level=1)
    header.add_run("\n" + person.job_title).bold = True

    # Add a section for education
    doc.add_heading("Education", level=2)
    for education_item in person.education:
        doc.add_paragraph(education_item)

    # Add a section for experience
    doc.add_heading("Experience", level=2)
    format_experience(doc, person.experience)
    #for experience_item in person.experience:
        #doc.add_paragraph(str(experience_item))

    # Add a section for skills
    doc.add_heading("Skills", level=2)
    doc.add_heading("Experience Skills", level=3)
    format_experience_skills(doc, person.experience)

    doc.add_heading("Related Skills", level=3)
    p = doc.add_paragraph()
    for skill in person.skills:
        p.add_run(f"{skill}, ")

    # Add a section for activities
    doc.add_heading("Activities", level=2)
    for activity in person.activities:
        doc.add_paragraph(activity)

    # Add a section for certs
    doc.add_heading("Certs", level=2)
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Name'
    hdr_cells[1].text = 'Issue'
    hdr_cells[2].text = 'Date'
    for cert in person.certifications:
        row_cells = table.add_row().cells
        row_cells[0].text = cert.title
        row_cells[1].text = cert.issuer
        row_cells[2].text = cert.completion_date

    return doc

# Example usage
sergio.name = "SDMS"
sergio.job_title = "DreamJob"

resume = build_resume(sergio)

# Save the Word document to a file
resume.save("resume.docx")
