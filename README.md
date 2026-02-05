# Email Opportunity Pipeline

Fetch, filter, and normalize email job opportunities into a JSON schema, then
render Markdown with YAML frontmatter for downstream automation. **Now with
Job Analysis and Resume Matching** to rank opportunities and get actionable
insights.

## Why this exists

- **Provider-agnostic**: Gmail is supported now, but the interface is designed
  so you can plug in Microsoft, AWS, ForwardEmail, etc.
- **Time-windowed fetch**: Grab the latest X minutes/hours/days.
- **Filtering pipeline**: Rule-based keyword/phrase filtering first, then an
  optional LLM filter.
- **Structured output**: Normalize into a dedicated JSON schema and render
  Markdown with frontmatter so you can ask clarifying questions, send resumes,
  or audit conversations later.
- **Job Analysis**: LLM-powered extraction of structured requirements from job
  postings including skills, experience levels, and technical environment.
- **Resume Matching**: Score and rank job opportunities against your resume
  with detailed insights, gap analysis, and tailoring suggestions.

## Project layout

```
src/email_opportunity_pipeline/
  cli.py
  config.py
  models.py
  io.py
  pipeline.py
  providers/
    base.py
    gmail.py
    gmail_parser.py
  filters/
    base.py
    keyword.py
    llm.py
    rules.py
  extraction/
    schema.py
    extractor.py
    markdown.py
    rules_extractor.py
    llm_extractor.py
  matching/                    # NEW: Job Analysis & Resume Matching
    __init__.py
    models.py                  # Resume, MatchResult, SkillMatch, etc.
    resume_parser.py           # Parse JSON/Markdown resumes
    analyzer.py                # LLM job requirement extraction
    matcher.py                 # LLM resume-job matching
    report.py                  # Markdown report generation
  schemas/
    job_opportunity.schema.json
    resume.schema.json         # NEW
    match_result.schema.json   # NEW
examples/
  filter_rules.json
  sample_resume.json           # NEW
```

## Install (uv)

```
uv venv
source .venv/bin/activate
uv pip install -e .
```

Optional LLM support (OpenAI):

```
uv pip install -e ".[llm]"
```

## Gmail setup

1. Create OAuth credentials in the Google Cloud Console.
2. Download `credentials.json` and place it in the repo root (or set
   `GMAIL_CREDENTIALS_PATH`).
3. First run will open a browser to authorize and create `token.json`.

## Quick start

Fetch the last 24 hours:

```
email-pipeline fetch --provider gmail --window 1d --out data/messages.json
```

Run the full pipeline:

```
email-pipeline run \
  --provider gmail \
  --window 6h \
  --out-dir out \
  --work-dir data
```

Step-by-step:

```
email-pipeline fetch --provider gmail --window 6h --out data/messages.json
email-pipeline filter --in data/messages.json --out data/filtered.json
email-pipeline extract --in data/filtered.json --out data/opportunities.json
email-pipeline render --in data/opportunities.json --out out
```

## Filter rules

Start from `examples/filter_rules.json` to customize allow/deny domains,
keywords, and patterns.

```
email-pipeline filter --in data/messages.json --out data/filtered.json \
  --rules examples/filter_rules.json
```

## Schema + Markdown

The dedicated schema lives at `src/email_opportunity_pipeline/schemas/`.
Markdown is rendered with YAML frontmatter so future automation can parse and
take actions like:

- ask clarifying questions (salary range, start date)
- send tailored resumes
- group conversations for auditing

---

## Job Analysis & Resume Matching

The matching module provides LLM-powered analysis to help you prioritize job
opportunities and prepare tailored applications.

### Features

- **Job Analysis**: Extract structured requirements (skills, experience, education)
- **Resume Matching**: Score jobs against your resume (0-100)
- **Gap Analysis**: Identify missing skills and experience
- **Insights**: Get strengths, concerns, and talking points
- **Resume Tailoring**: Suggestions for customizing your resume per job
- **Application Strategy**: Recommended approach and cover letter focus

### Resume Format

Create your resume in JSON format (see `examples/sample_resume.json`) or Markdown:

```json
{
  "personal": {
    "name": "Your Name",
    "email": "you@email.com",
    "location": "City, State",
    "summary": "Brief professional summary..."
  },
  "skills": {
    "technical": [
      { "name": "Python", "level": "expert", "years": 5 },
      { "name": "AWS", "level": "advanced", "years": 3 }
    ],
    "soft": ["Leadership", "Communication"]
  },
  "experience": [
    {
      "title": "Senior Engineer",
      "company": "Tech Corp",
      "start_date": "2020-01",
      "current": true,
      "achievements": ["Led team of 5", "Built microservices platform"]
    }
  ],
  "education": [
    {
      "degree": "BS",
      "field": "Computer Science",
      "institution": "University"
    }
  ],
  "preferences": {
    "remote_preference": "hybrid",
    "salary_min": 150000,
    "engagement_types": ["FULL_TIME"]
  }
}
```

### Quick Start - Matching

After running the main pipeline to extract opportunities:

```bash
# 1. Analyze jobs to extract structured requirements (optional but recommended)
email-pipeline analyze \
  --in data/opportunities.json \
  --out data/job_analyses.json

# 2. Match your resume against all opportunities
email-pipeline match \
  --resume examples/sample_resume.json \
  --opportunities data/opportunities.json \
  --analyses data/job_analyses.json \
  --out out/matches \
  --individual-reports

# 3. Filter and rank results
email-pipeline rank \
  --in out/matches/match_results.json \
  --min-score 70 \
  --recommendation strong_apply,apply \
  --top 10
```

### Match a Single Job

```bash
# Match against job at index 0
email-pipeline match \
  --resume examples/sample_resume.json \
  --opportunities data/opportunities.json \
  --job-index 0 \
  --out out/match_report.md \
  --format markdown
```

### Match Output

The match command generates:

- `match_results.json` - All match data in JSON format
- `match_summary.md` - Overview report with rankings
- `match_reports/` - Individual detailed reports (with `--individual-reports`)

### Match Scores

| Score | Grade | Recommendation |
|-------|-------|----------------|
| 85-100 | Excellent | Strong Apply |
| 70-84 | Good | Apply |
| 50-69 | Fair | Consider |
| 30-49 | Poor | Skip |
| 0-29 | Unqualified | Not Recommended |

### Scoring Categories

| Category | Weight | Description |
|----------|--------|-------------|
| Skills | 35% | Mandatory and preferred skills match |
| Experience | 30% | Years and role relevance |
| Education | 15% | Degree and field match |
| Location | 10% | Location/remote compatibility |
| Culture Fit | 10% | Work style alignment |

---

## Notes

- Gmail attachments are listed but not downloaded.
- The LLM filter and LLM extractor are **optional**. You can keep everything
  rule-based for predictable behavior.
- Job Analysis and Resume Matching **require** the LLM optional dependency.
