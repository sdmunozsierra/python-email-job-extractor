# Email Opportunity Pipeline

Fetch, filter, and normalize email job opportunities into a JSON schema, then
render Markdown with YAML frontmatter for downstream automation. **Now with
Job Analysis and Resume Matching** to rank opportunities and get actionable
insights.

## Documentation

- `docs/cli.md`: CLI commands and examples
- `docs/configuration.md`: environment variables, file formats, rules, and windows
- `docs/architecture.md`: pipeline stages and extension points (providers/filters/extractors)
- `docs/troubleshooting.md`: common setup/runtime issues

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

## Requirements

- Python 3.10+
- Gmail provider: Google OAuth desktop credentials + Gmail API enabled
- LLM features: optional OpenAI dependency + `OPENAI_API_KEY`

## Install (uv)

```
uv venv
source .venv/bin/activate
uv pip install -e .
```

Install (pip):

```
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Optional LLM support (OpenAI):

```
uv pip install -e ".[llm]"
```

## LLM setup (optional)

LLM features (LLM filter, LLM extraction, job analysis, resume matching) use the
OpenAI Python SDK. Set an API key via environment variable:

```
export OPENAI_API_KEY="..."
```

You can also choose the model via `--llm-model` (default: `gpt-4o-mini`).

## Gmail setup

1. Create OAuth credentials in the Google Cloud Console.
2. Download `credentials.json` and place it in the repo root (or set
   `GMAIL_CREDENTIALS_PATH`).
3. First run will open a browser to authorize and create `token.json`.

Environment variables:

- `GMAIL_CREDENTIALS_PATH`: path to OAuth client credentials JSON (default: `credentials.json`)
- `GMAIL_TOKEN_PATH`: path to cached OAuth token JSON (default: `token.json`)

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

Notes:

- The rules file can be partial: only keys you provide override the built-in defaults.
- Add `--analytics` to `filter` to write `filter_analytics.json` and a human-readable
  `filter_analytics_report.txt` alongside the output file.

## Schema + Markdown

The dedicated schema lives at `src/email_opportunity_pipeline/schemas/`.
Markdown is rendered with YAML frontmatter so future automation can parse and
take actions like:

- ask clarifying questions (salary range, start date)
- send tailored resumes
- group conversations for auditing

## Analytics

There are two ways to produce analytics:

- `email-pipeline run` writes `data/analytics.json` and `data/analytics_report.txt` by default
  (disable with `--no-analytics`).
- `email-pipeline analytics` generates analytics from existing artifacts (messages/opportunities),
  useful for iterating on rule changes without refetching.

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

Create your resume in JSON format (see `examples/sample_resume.json`) or Markdown.

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

## Troubleshooting

If you hit setup issues, start with `docs/troubleshooting.md`. The most common
issues are missing Gmail OAuth files (`credentials.json` / `token.json`) or an
unset `OPENAI_API_KEY` when using LLM features.
