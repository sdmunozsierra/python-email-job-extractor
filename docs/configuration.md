# Configuration

This project is intentionally lightweight: configuration is primarily via CLI
flags and a small set of environment variables.

## Environment variables

### Gmail provider

The Gmail provider reads OAuth files from the repo root by default:

| Variable | Default | Description |
|----------|---------|-------------|
| `GMAIL_CREDENTIALS_PATH` | `credentials.json` | Path to OAuth client credentials JSON |
| `GMAIL_TOKEN_PATH` | `token.json` | Path to cached OAuth token JSON |

These files are already ignored in `.gitignore`.

### OpenAI / LLM features (optional)

LLM features use the OpenAI Python SDK. Provide credentials via:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | -- | Required for LLM commands (`analyze`, `match`, `compose`, `run-all`, `--llm-filter`, `--llm-extract`) |

The CLI also supports choosing the model via `--llm-model` (default:
`gpt-4o-mini`).

### Gmail send scope

The `reply` and `run-all --send` commands need the `gmail.send` OAuth scope
in addition to `gmail.readonly`.  The first time you send, you may be prompted
to re-authorise.  The token is cached in `token.json` as usual.

---

## Filter rules file

`email-pipeline filter` accepts a JSON rules file (see `examples/filter_rules.json`).

Important behavior:

- The rules file is **merged on top of built-in defaults**, so you can specify
  only the keys you want to override.
- Keys not present in your file fall back to defaults in
  `src/email_opportunity_pipeline/filters/rules.py`.

### Common keys

| Key | Type | Description |
|-----|------|-------------|
| `job_source_domains` | list[str] | Domains treated as strong job sources (ATS / job boards) |
| `non_job_domains` | list[str] | Domain denylist |
| `job_keywords` | list[str] | Strong job keywords |
| `weak_job_keywords` | list[str] | Ambiguous keywords (only count when multiple present) |
| `role_title_patterns` | list[str] | Regex patterns to detect role titles |
| `promo_negative_patterns` | list[str] | Regex patterns for promotions/commerce |
| `transactional_patterns` | list[str] | Regex patterns for receipts/account/security emails |
| `marketing_footer_patterns` | list[str] | Regex patterns to detect newsletter footers |

---

## Time windows

Time windows use the format `<integer><unit>`:

| Suffix | Meaning | Example |
|--------|---------|---------|
| `m` | Minutes | `30m` |
| `h` | Hours | `6h` |
| `d` | Days | `2d` |

This format is parsed by `src/email_opportunity_pipeline/time_window.py`.

---

## Resume format

Resumes can be provided as JSON or Markdown.

### JSON format

See `examples/sample_resume.json` for a complete example. Top-level keys:

```json
{
  "personal": {
    "name": "...",
    "email": "...",
    "phone": "...",
    "location": "...",
    "linkedin": "...",
    "github": "...",
    "portfolio": "...",
    "summary": "..."
  },
  "skills": {
    "technical": [{"name": "Python", "level": "advanced", "years": 5, "category": "languages"}],
    "soft": ["Communication", "Leadership"],
    "languages": [{"language": "English", "proficiency": "native"}],
    "certifications": [{"name": "AWS Solutions Architect", "issuer": "AWS", "date": "2023-01"}]
  },
  "experience": [
    {
      "title": "Senior Engineer",
      "company": "Acme Corp",
      "location": "Remote",
      "start_date": "2021-01",
      "end_date": null,
      "current": true,
      "description": "...",
      "achievements": ["..."],
      "technologies": ["Python", "AWS"]
    }
  ],
  "education": [...],
  "projects": [...],
  "preferences": {
    "desired_roles": ["Senior Software Engineer"],
    "industries": ["Technology"],
    "locations": ["Remote"],
    "remote_preference": "remote_only",
    "engagement_types": ["full_time"]
  }
}
```

### Markdown format

Use standard headings:

```markdown
# Your Name

## Contact
email@example.com
Location: City, State

## Summary
Your professional summary...

## Skills
- Technical: Python (advanced), JavaScript, SQL
- Soft: Communication, Leadership

## Experience
### Senior Engineer at Acme Corp
**Dates:** 2021-01 - Present
**Technologies:** Python, AWS
- Built scalable microservices
- Led team of 5 engineers

## Education
### BS in Computer Science - MIT
**Dates:** 2015 - 2019
**GPA:** 3.8
```

---

## Output artifacts

Most commands write a JSON wrapper object containing timestamps and counts:

| File | Format | Producer | Consumer |
|------|--------|----------|----------|
| `messages.json` | `{ fetched_at_utc, count, messages: [...] }` | `fetch`, `run` | `filter`, `analytics` |
| `filtered.json` | `{ fetched_at_utc, count, messages: [...] }` | `filter`, `run` | `extract` |
| `opportunities.json` | `{ created_at_utc, count, opportunities: [...] }` | `extract`, `run` | `render`, `analyze`, `match` |
| `job_analyses.json` | `{ created_at_utc, count, analyses: [...] }` | `analyze` | `match` |
| `match_results.json` | `{ created_at_utc, resume_id, count, match_results: [...] }` | `match` | `rank`, `tailor` |
| `tailoring_results.json` | `{ created_at_utc, count, tailoring_results: [...] }` | `tailor`, `run-all` | -- |
| `drafts.json` | `{ created_at_utc, count, drafts: [...] }` | `compose`, `run-all` | `reply` |
| `reply_results.json` | `{ created_at_utc, count, reply_results: [...] }` | `reply`, `run-all` | -- |

Markdown output is written as one file per opportunity using the source email
message ID, e.g. `out/<message_id>.md`.

---

## Docker

The `Dockerfile` at the project root builds an image with all dependencies
pre-installed. Key paths inside the container:

| Container path | Purpose |
|---------------|---------|
| `/app/data` | Pipeline JSON artifacts (`--work-dir`) |
| `/app/output` | Reports, tailored resumes, replies (`--out-dir`) |
| `/app/resumes` | Resume input files |
| `/app/config` | ConfigMap-mounted filter rules and questionnaire |
| `/app/secrets/gmail/` | Gmail OAuth credentials (mounted from Secret) |

### Environment variables in Docker/K8s

When running in a container, all the same environment variables apply.
In Kubernetes they are supplied via Secrets and ConfigMaps:

| Variable | K8s source | Manifest |
|----------|-----------|----------|
| `OPENAI_API_KEY` | `Secret/email-pipeline-secrets` | `k8s/secrets.yaml` |
| `GMAIL_CREDENTIALS_PATH` | Set to `/app/secrets/gmail/credentials.json` | `k8s/deployment.yaml` |
| `GMAIL_TOKEN_PATH` | Set to `/app/secrets/gmail/token.json` | `k8s/deployment.yaml` |

The Gmail OAuth files are stored as `Secret/gmail-credentials` and mounted as
files rather than environment variables, since the application reads them by
path.

---

## Kubernetes configuration

### Secrets (`k8s/secrets.yaml`)

Two secrets:

1. **`email-pipeline-secrets`** -- `OPENAI_API_KEY` as a string
2. **`gmail-credentials`** -- `credentials.json` and `token.json` file contents

Replace the placeholder values before deploying. For production, use
`kubectl create secret` or a secrets manager (Sealed Secrets, External Secrets
Operator) instead of committing secrets.

### ConfigMap (`k8s/configmap.yaml`)

Holds `filter_rules.json` and `questionnaire.json`. Edit the ConfigMap to
customise pipeline behaviour without rebuilding the image.

### Persistent volumes (`k8s/pvc.yaml`)

| PVC | Size | Mount path | Purpose |
|-----|------|-----------|---------|
| `pipeline-data` | 1Gi | `/app/data` | JSON artifacts |
| `pipeline-output` | 2Gi | `/app/output` | Reports, resumes, replies |
| `pipeline-resumes` | 500Mi | `/app/resumes` | Resume input files |

All volumes use `ReadWriteOnce` access mode and are shared between the
Deployment (UI) and CronJob (pipeline).

### CronJob schedule (`k8s/cronjob.yaml`)

Default: every 6 hours (`0 */6 * * *`). Edit the `schedule` field to change.

### Image reference (`k8s/kustomization.yaml`)

Set `newName` to your container registry path:

```yaml
images:
  - name: email-pipeline
    newName: <your-registry>/email-pipeline
    newTag: latest
```

---

## Vendor: resume-builder

The `vendor/resume-builder/` directory is a git subtree of the
python-resume-builder package. It is declared as a dependency in `pyproject.toml`:

```toml
[project]
dependencies = [
  ...
  "resume-builder",
]

[tool.uv.sources]
resume-builder = { path = "vendor/resume-builder", editable = true }
```

### Installation

**uv** (recommended): `uv sync` handles the vendor path dependency automatically.

**pip**: Install the vendor package explicitly first:

```bash
pip install -e vendor/resume-builder
pip install -e .
```

### What it provides

After installation, two things are available:

1. **Python package** (`resume_builder`): Used by the tailoring engine to
   convert resume JSON into `.docx` documents.
2. **CLI** (`resume-builder`): Standalone command to build `.docx` resumes.

### Configuration

The vendor package has no environment variables. Its only inputs are:

- A JSON resume file (via `--json` on the CLI, or `ResumeSchemaAdapter.from_dict()` in Python)
- An output path (via `--output` on the CLI, or `doc.save()` in Python)

If the `resume-builder` package is not installed, the `tailor` command will
still produce JSON/Markdown reports but will skip `.docx` generation and log
a warning.
