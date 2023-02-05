info = """Programming Languages

API Development: Postman, REST, SonarQube, Swagger API
Databases: Aurora, Mongo, DynamoDB, GraphQL, Redis, SQL
Java: 8+, Android, Maven, Spring Framework 
JavaScript: Node, Vuejs, Nuxtjs, Express
Python: 2, 3+, Scrapy, Flask, Pandas
Spring: Spring Boot, Spring Data, Spring Profiles, Spring Security
Scripting and Tools: Bash, Git, Kafka, Vim, Yarn
Web and Web3: Brownie, CSS, Hardhat, HTML, PHP, Solidity

Cloud & Operating Systems

AWS: Solutions Architect Certified, Amplify, IAM, S3, Serverless, VPC, ASG, etc.
DevOps: Ansible, Consul, Code Pipeline, Cloud Formation, Github Actions, Gitlab CI/CD, Kubernetes hands-on-training
Docker: Compose, Swarm, Registry, Images
Elastic Stack: ElasticSearch, Logstash, Kibana
Linux: ArchLinux, CentOS, Debian, Kali Linux,  Mint, Ubuntu, Proxmox
Human Languages: English, Spanish, French (wp)"""

def convert_to_list(info):
    info_list = []
    for line in info.splitlines():
        line = line.strip()
        if line:
            info_list.append(line)
    return info_list

info_list = convert_to_list(info)
