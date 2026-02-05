info = """Programming Languages


AI: Langchain, Vector Databases, AI ETL, Guardrails, Code Gen, Fine-tune, Integrations
API Development: Postman Testing, REST, SonarQube, Swagger API
Databases: Aurora, Mongo, DynamoDB, GraphQL, Redis, SQL, ES
Java: 8+, Android, Maven, Spring Framework 
JavaScript: Node, Vuejs, Nuxtjs, Express, TS
LLMOps: OWASP for LLMs, Privacy and Compliance
Prompt Eng: ReACT, ToT, Augmented Retrieval, Chains, Agents
Python: 2, 3+, Scrapy, Flask, Pandas, FastAPI, Pydantic, Streamlit
Realtime: Kafka, PubNub, Socket.io
Spring: Spring Boot, Spring Data, Spring Profiles, Spring Security
Scripting and Tools: Bash, Fish, Git, Kafka, Vim, Yarn
Web and Web3: Brownie, CSS, Hardhat, HTML, PHP, Solidity

Cloud & Operating Systems

AWS: SA Certified, Amplify, Bedrock, IAM, S3, SageMaker, Serverless, VPCs, etc.
Azure: OpenAI, Virtual Machines
DevOps: Ansible, Consul, Code Pipeline, Cloud Formation, Github Actions, Gitlab CI/CD, Kubernetes hands-on-training
Docker: Compose, Swarm, Registry, Images, Scrpting, API
Google: Cloud, Drive API, Firebase, Oauth2
LLMs: GPT3.5T, GPT4, Claude, Jurasic, CopilotX, Llama, HF, etc.
Orchestration: K8s, K3s, Docker Compose, virt-manager, Firecracker, Podman, Kata
Networking: OpenWRT, PfSense, L2-L3 Switching, DHCP, DNS, VPNs
Elastic Stack: ElasticSearch, Kibana, Beats, Logstash
Linux: ArchLinux, CentOS, Debian, Kali, Mint, Ubuntu, Proxmox
Human Languages: English, Spanish, French (wp)"""

def convert_to_list(info):
    info_list = []
    for line in info.splitlines():
        line = line.strip()
        if line:
            info_list.append(line)
    return info_list

info_list = convert_to_list(info)
