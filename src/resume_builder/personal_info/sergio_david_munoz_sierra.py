"""Personal Information for Sergio David Munoz Sierra"""
from resume_builder.experiece_builder import ExperienceFactory
from resume_builder.project_builder import ProjectFactory

# Experience in Reverse Chronological Order

## Job0 - Precision Camera: 12/2013 - 04/2014

job0_project0 = ProjectFactory.create_project(
    "Inventory Tester",
    "Follow rigorous testing methodology",
    "12/2013 - 04/2014",
    1,
    ["Tested cameras to ensure their hardware and software functionality.",
     "Logged and maintained records of different parts and components of cameras.",
     "Provided customer service by offering services and products by phone."],
    ["hardware-testing", "visual-inspection", "customer-service"]
)

job0 = ExperienceFactory.create_experience(
    "Inventory Tester",
    "Precision Camera",
    "12/2013 - 04/2014",
    "El Paso, TX.",
    [job0_project0]
)

## Job1 - Vector Marketing: 04/2014 - 11/2014

job1_project0 = ProjectFactory.create_project(
    "Management Excellence Program",
    "Accepted in management program within one month due to hard work and ethics.",
    "04/2014 - 11/2014",
    4,
    ["Oversaw a group that boosted the success of phone interviews by 10% via specialized scripts.",
     "Forged long time relationships with clients during product presentations.",
     "Reviewed customer forms, received payments, and keep in contact to provide best service.",
     "Expertise in cold calling, sales, and customer service."],
    ["cold-calling", "sales", "customer-service"]
)

job1 = ExperienceFactory.create_experience(
    "Management Excellence Program",
    "Vector Marketing",
    "04/2014 - 11/2014",
    "El Paso, TX.",
    [job1_project0]
)

## Job2 - Total Fun: 12/2014 - 01/2017

job2_project0 = ProjectFactory.create_project(
    "General Manager",
    "Lead a team to provide the best events in the city for children.",
    "12/2014 - 01/2017",
    10,
    ["Hired and trained employees to provide the best customer service.",
     "Reduced training time from one week to three days.",
     "Coordinated research sessions centered on specific customer experience.",
     "Produced a weekly report to the CEO about current status, tactics, strengths, and weaknesses of the company.",
     "Used innovative persuasion and viral-marketing elements to attract potential customers."],
    ["hiring", "training", "customer-service", "marketing", "management"]
)

job2_project1 = ProjectFactory.create_project(
    "Technical Manager",
    "Managed all company's infrastructure and social media.",
    "12/2014 - 01/2017",
    1,
    ["Implemented a customer relational database.",
     "Designed an internal website focused on ease of use for employees.",
     "Managed marketing, social media, strategic deals and PR efforts with local agencies.",
     "Developed scripts that automated group and forum posting on Facebook to raise productivity."],
    ["sql", "web-development", "social-media", "automation", "marketing", "management"]
)

job2 = ExperienceFactory.create_experience(
    "General and Technical Manager",
    "Total Fun",
    "12/2014 - 01/2017",
    "Ciudad Juarez, CHIH.",
    [job2_project0, job2_project1]
)

## Job 3 - T.E.B. Benefits: 04/2017 - 12/2017

job3_project0 = ProjectFactory.create_project(
    "IT Consultant",
    "Modernized the company's software to meet the needs of the clients.",
    "04/2017 - 12/2017",
    1,
    ["Architected from scratch two software programs that imported and parsed multiple csv files.",
     "Automatic information processing to meet specific requirements from different insurance companies.",
     "Created a rigorous testing methodology to eliminate errors on insurance questionnaires",
     "Achieved acceptance of files within 48 hours of submission which used to take weeks or months."],
    ["java", "sql", "automation", "testing", "consulting-it", "etl", "qa"]
)

job3 = ExperienceFactory.create_experience(
    "IT Consultant",
    "T.E.B. Benefits",
    "04/2017 - 12/2017",
    "El Paso, TX.",
    [job3_project0]
)

## Job 4 - Leidos Inc.: 01/2018 - 01/2022

job4_project0 = ProjectFactory.create_project(
    "Android Bluetooth Microprocessor Technology",
    "Android bluetooth beacon modification and discovery",
    "01/2018 - 03/2018",
    2,
    ["Updated and maintained Linux Kernel low level code on any BlueZ compatible devices.",
     "Prototyped a Bluetooth mesh using 4 RaspberryPi devices to track and locate users via Bluetooth packets."],
    ["iot", "c lang", "bluetooth", "linux", "kernel", "android", "java"]
)

job4_project1 = ProjectFactory.create_project(
    "mlnOpedia Mobile App",
    "Android and IOS development for Healthcare",
    "04/2018 - 07/2018",
    7,
    ["Created an Android version of an IOS app that was already in production.",
     "Added push notifications to alert users on recommendations and updates.",
     "Implemented bulk upload scripts to automate safe data upload to local and remote servers."],
    ["android", "java", "ios", "objective c", "python", "automation", "push-notifications"]
)

job4_project2 = ProjectFactory.create_project(
    "AWS EC2 Metrics Analytics",
    "AWS CloudWatch metrics monitoring.",
    "08/2018 - 12/2018",
    1,
    ["Created an observation and monitoring webapp for company-wide AWS usage.",
        "Real-time log parsing with emphasis on instances of types Redis and S3.",
        "Deployed a dynamic flask app with organized metrics into a local database.",
        "Forecast usage and cost per active instance using AI models and big data analysis.",
        "Automatic unit and regression testing with over 95% code coverage."],
    ["aws", "aws-ec2", "aws-cloudwatch", "python", "python-boto3", "python-flask", "python-pandas", "python-tensorflow", "python-pytest", "big-data", "forecasting", "testing", "etl", "sql-lite"]
)

job4_project3 = ProjectFactory.create_project(
    "Spring Backend Microservices",
    "Lead a team to implement a data searching backend app.",
    "01/2019 - 01/2020",
    7,
    ["Delivered a SpringBoot app that provides backend microservices as APIs.",
        "Created a plenitude of scripts to interact with containers and perform management actions.",
        "Setup a REST environment that allowed CRUD and advanced operations.",
        "Secure file and file metadata management using SSL and custom validations.",
        "Analyzed code against potential security flaws and incorporated black-box testing.",
        "Raised coverage from 35% to 75% by fixing 100's bugs."],
    ["project-management", "sonarqube", "java", "spring-boot", "spring-data", "spring-profiles", "maven", "gitlab-cicd", "minio", "docker", "docker-compose", "bash"]
)

job4_project4 = ProjectFactory.create_project(
    "Cloud Distributed Scraping System",
    "Led a team to architect and deploy a distributed web scraping system.",
    "01/2020 - 01/2022",
    5,
    ["Managed and orchestrated a containerized fullstack environment of 20+ microservices.",
        "Created scripts that accelerated deployment time from days to less than 10 minutes.",
        "Implemented a testing environment with CI/CD.",
        "Deployed and maintained testing and production environments in the cloud.",
        "Leveraged modern Software engineering techniques on all levels of the stack.",
        "Added visualization of data pipelines at different stages in the process."],
    ["aws", "docker", "docker-compose", "bash", "python", "redis", "kafka", "javascript", "js-express", "elasticsearch", "traefik", "sql"]
)

job4 = ExperienceFactory.create_experience(
   "Lead Software Engineer",
   "Leidos Inc.",
   "01/2018 - 01/2022",
   "Reston, VA",
    [job4_project0, job4_project1, job4_project2, job4_project3, job4_project4]
)

## Job 5 - Infinitive: 01/2022 - 06/2022

job5_project0 = ProjectFactory.create_project(
    "Principal Full Stack",
    "Capital One: AWS Optimization for performance and cost on logs",
    "01/2022 - 06/2022",
    3,
    ["Ingest semi-structured data into singe repository, apply cleansing, enrichment, business logic rules.",
     "Self service through custom models into playbooks.",
     "Story telling including KPIs, Dashboards and Scoreboards that utilized proven design strategies."],
    ["logstash", "elastic-stack", "ansible", "datadog", "kibana", "aws", "data-driven", "data-visualization"]
)

job5 = ExperienceFactory.create_experience(
    "Principal Full Stack",
    "Infinitive",
    "01/2022 - 06/2022",
    "Ashburn, VA",
    [job5_project0]
)

## Job 6 - PubNub: 06/2022 - 10/2023

job6_project0 = ProjectFactory.create_project(
    "Internal Developer Tools",
    "Metrics API and Python Tools",
    "06/2022 - 11/2022",
    1,
    ["Built a CLI 'sdk' on top of PubNub's metrics api.",
        "ETL using Pandas and metric enrichment using .csv files.",
        "Deployed a Flask/FastAPI server on AWS using Elastic Beanstalk and EC2.",
        "Allowed for easy access to metrics and data for all PubNub employees.",
        "Simulate usage, failures and quick usage of many PubNub's server side services."],
   ["python", "etl", "aws", "aws-ec2", "aws-eb", "github-actions", "python-flask", "python-fastapi", "pubnub"]
)

job6_project1 = ProjectFactory.create_project(
    "Solutions Architect",
    "Customer Excellence",
    "06/2022 - 03/2023",
    4,
    ["Client facing on pub/sub cutting edge technologies.",
        "Quickly learn the customer's use case and provide best practices, recommendations, code snippets and prototypes.",
        "Pre/Post sales engineering on technical pitches, analysis, demos, solutions, and use-cases.",
        "Monitor usage and provide recommendations to optimize for cost, performance and security.",
        "Provide technical expertise and support to clients and internal teams."],
    ["solutions-architect", "sales-engineer", "customer-facing", "pubnub"]
)

job6_project2 = ProjectFactory.create_project(
    "AI Solutions Architect",
    "Increase Top of the Funnel",
    "03/2023 - 10/2023",
    3,
    ["Partnership with an AWS internal team of AI Solutions Architects and Engineers for product development and training.",
    "Present every 2 weeks to a high level executive committee about latest AI trends, developments and  project status updates.",
    "Work along the Marketing department to produce AI blogs and content."],
    ["solutions-architect-ai", "aws-partnership", "aws-training", "aws-bedrock", "marketing-blogs", "marketing-automation", "presentations", "consulting-ai"]
)


job6_project3 = ProjectFactory.create_project(
    "AI R&D Engineer",
    "Improve Internal Productivity",
    "03/2023 - 10/2023",
    3,
    ["Architected from scratch a self-hosted production ready containerized environment for deploying modern cloud agnostic AI apps.",
     "Deployed a state of the art Prompt lifecycle management app with specialized tools that optimize employee's tasks.",
     "Vast experience working with closed and OpenSource LLMs and APIs using novel prompt techniques to produce working code, tests, templates, and much more.",
     "Developed RAG with emphasis on QA retrieval for automation of specialized form filling, prompt templates and code generation using custom datasets and vector multi-retrieval.",
     "Created integrations of many services and tools such as OAuth2, Google Drive, Slack, etc.",
     "Used a combination of noSQL, SQL, Vector and Document databases to manage users, prompts, training data and usage data.",
     "Incorporated classic ETL and DataScience techniques to enhance the ETL process including cleaning, labeling, QA, etc."],
    ["llmops", "gen-ai", "prompt-db", "prompt-engineer", "etl-ai", "mlops", "datascience", "python", "langchain", "llm-gpt", "llm-claude", "docker-compose", "bash", "elasticsearch", "mongodb", "postgresql", "redis", "oauth2.0", "aws-lambda", "traefik"]
)


job6 = ExperienceFactory.create_experience(
    "AI Solutions Architect",
    "PubNub",
    "06/2022 - 10/2023",
    "San Francisco, CA / Remote",
    [job6_project0, job6_project1, job6_project2, job6_project3]
)


## Job 7 - Cleta LLC: 08/2020 - DATE

job7_project0 = ProjectFactory.create_project(
    "Cleta.io Serverless Fullstack Web3",
    "Web3 automated serverless architecture running on AWS.",
    "08/2020 - 08/2022",
    5,
    ["Designed and deployed a serverless cloud web3 infrastructure.",
        "Implemented GraphQL schemas, queries, and mutations, tested with AVA.",
        "UI/UX design with interactive wireframing into fullstack js integrations.",
        "Continuous Delivery from hot-commit to global within 3 minutes.",
        "Smart contracts with tets to deploy into Infura or private Ethereum cloud nodes.",
        "Client Consulting on Web3 technology vision, strategy and direction."],
    ["aws", "aws-serverless", "aws-dynamodb", "graphql", "github-actions", "aws-codedeploy", "nodejs", "typescript", "ethereum", "solidity", "web3", "ava", "testing", "ui-ux", "wireframing", "consulting-web3"]
)

job7_project1 = ProjectFactory.create_project(
    "Cleta.io Web3 Dashboard",
    "Web3 Dashboard for Cleta.io",
    "08/2023 - DATE",
    3,
    ["Architected an event-driven serverless cloud infrastructure using Azure enterprise OpenAI along with AWS services.",
        "Client Consulting on AI trends, vision, strategy and direction."],
    ["consulting-ai", "azure", "openai", "aws"]
)

job7 = ExperienceFactory.create_experience(
    "Founder/Creator",
    "Cleta LLC",
    "08/2020 - DATE",
    "Arlington, VA",
    [job7_project0, job7_project1]
)
