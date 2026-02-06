# Email Opportunity Pipeline

Fetch, filter, and normalize email job opportunities into a JSON schema, then
render Markdown with YAML frontmatter for downstream automation. **Now with
Job Analysis, Resume Matching, and Resume Tailoring** to rank opportunities,
get actionable insights, and generate tailored `.docx` resumes.

## Documentation

- `docs/cli.md`: CLI commands and examples
- `docs/configuration.md`: environment variables, file formats, rules, and windows
- `docs/architecture.md`: pipeline stages, interfaces, vendor integration, and extension points
- `docs/troubleshooting.md`: common setup/runtime issues
- `CONTRIBUTING.md`: development setup and contribution guidelines

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
- **Resume Tailoring**: Automatically generate tailored `.docx` resumes per
  job, emphasizing relevant skills, reordering experience, and tracking every
  change in a detailed report.

## Project layout

```
src/email_opportunity_pipeline/
  __init__.py              # Package root with version
  cli.py                   # email-pipeline CLI entry point
  config.py                # Default settings (window, Gmail scopes)
  models.py                # EmailMessage, FilterDecision, FilterOutcome
  io.py                    # Read/write JSON artifacts
  pipeline.py              # Orchestration (fetch -> filter -> extract -> render)
  time_window.py           # Time window parsing (30m, 6h, 2d)
  analytics.py             # Pipeline analytics and reporting
  providers/
    base.py                # EmailProvider abstract interface
    gmail.py               # Gmail API provider implementation
    gmail_parser.py         # Gmail message parsing
  filters/
    base.py                # EmailFilter abstract interface
    keyword.py             # Rule-based keyword/domain filter
    llm.py                 # Optional LLM-based filter
    pipeline.py            # FilterPipeline orchestrator
    rules.py               # FilterRules model and loader
  extraction/
    extractor.py           # BaseExtractor abstract interface
    schema.py              # Job opportunity JSON schema
    rules_extractor.py     # Deterministic regex/heuristic extractor
    llm_extractor.py       # OpenAI schema-driven extractor
    markdown.py            # Markdown + YAML frontmatter renderer
  matching/                # Job Analysis & Resume Matching (LLM)
    __init__.py
    models.py              # Resume, MatchResult, SkillMatch, etc.
    resume_parser.py       # Parse JSON/Markdown resumes
    analyzer.py            # LLM job requirement extraction
    matcher.py             # LLM resume-job matching
    report.py              # Markdown report generation
  tailoring/               # Resume Tailoring (uses vendor/resume-builder)
    __init__.py
    adapter.py             # Pipeline Resume <-> builder schema adapter
    engine.py              # Tailoring engine (apply match insights)
    models.py              # TailoredResume, TailoringReport, TailoringChange
    report.py              # Markdown tailoring report renderer
  schemas/
    job_opportunity.schema.json
    resume.schema.json
    match_result.schema.json
vendor/
  resume-builder/          # Git subtree: .docx generation from JSON schema
    src/resume_builder/
      cli.py               # resume-builder CLI
      schema_adapter.py    # JSON schema -> Person model adapter
      person_builder.py    # Person builder pattern
      ...
examples/
  filter_rules.json
  sample_resume.json
docs/
  architecture.md
  cli.md
  configuration.md
  troubleshooting.md
```

## Requirements

- Python 3.11+
- Gmail provider: Google OAuth desktop credentials + Gmail API enabled
- LLM features: optional OpenAI dependency + `OPENAI_API_KEY`

## Install

### Using uv (recommended)

```bash
uv venv
source .venv/bin/activate
uv sync
```

`uv sync` automatically installs the vendor `resume-builder` package as an
editable path dependency via `[tool.uv.sources]`.

### Using pip

With pip, install the vendor dependency first, then the main package:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e vendor/resume-builder
pip install -e .
```

### Optional LLM support (OpenAI)

```bash
# uv
uv pip install -e ".[llm]"

# pip
pip install -e ".[llm]"
```

## LLM setup (optional)

LLM features (LLM filter, LLM extraction, job analysis, resume matching) use the
OpenAI Python SDK. Set an API key via environment variable:

```bash
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

```bash
email-pipeline fetch --provider gmail --window 1d --out data/messages.json
```

Run the full pipeline:

```bash
email-pipeline run \
  --provider gmail \
  --window 6h \
  --out-dir out \
  --work-dir data
```

Step-by-step:

```bash
email-pipeline fetch --provider gmail --window 6h --out data/messages.json
email-pipeline filter --in data/messages.json --out data/filtered.json
email-pipeline extract --in data/filtered.json --out data/opportunities.json
email-pipeline render --in data/opportunities.json --out out
```

## Filter rules

Start from `examples/filter_rules.json` to customize allow/deny domains,
keywords, and patterns.

```bash
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

## Resume Tailoring

The tailoring command builds on match results to produce tailored resumes with
tracked changes. It uses the **vendor/resume-builder** subtree package to
generate `.docx` Word documents.

### Quick Start - Tailoring

```bash
# Tailor resume for top matches
email-pipeline tailor \
  --resume examples/sample_resume.json \
  --match-results out/matches/match_results.json \
  --opportunities data/opportunities.json \
  --out output/tailored \
  --min-score 70 \
  --recommendation strong_apply,apply \
  --top 5
```

### Tailoring Output

Per job:
- `<job_id>_resume.json` -- tailored resume data
- `<job_id>_report.json` -- structured change report
- `<job_id>_report.md` -- human-readable Markdown report
- `tailored_resume_<company>_<title>.docx` -- the generated Word document

Batch:
- `tailoring_results.json` -- all results in one file
- `tailoring_summary.md` -- summary across all tailored resumes

### What the tailoring engine does

| Category | Action |
|----------|--------|
| Summary | Replaces with a job-tailored summary from match analysis |
| Skills | Reorders technical skills, prioritizing mandatory/highlighted ones |
| Experience | Reorders entries by relevance, surfaces featured achievements |
| Certifications | Reorders by relevance to target role |
| Keywords | Identifies ATS keywords for reference |

Every change is logged in a `TailoringReport` with before/after diffs.

---

## Vendor: resume-builder

The `vendor/resume-builder/` directory is a **git subtree** of the
[python-resume-builder](https://github.com/sdmunozsierra/python-resume-builder)
repository. It provides:

- `ResumeSchemaAdapter` -- converts a JSON resume dict into internal Person models
- `build_resume(person)` -- generates a `.docx` Word document from a Person object
- A standalone CLI: `resume-builder --json resume.json --output my_resume.docx`

The parent project declares it as an editable path dependency:

```toml
# pyproject.toml
[tool.uv.sources]
resume-builder = { path = "vendor/resume-builder", editable = true }
```

To update the subtree from upstream:

```bash
git fetch resume-builder
git subtree pull --prefix=vendor/resume-builder resume-builder main --squash
uv sync   # or: pip install -e vendor/resume-builder
```

---

## Notes

- Gmail attachments are listed but not downloaded.
- The LLM filter and LLM extractor are **optional**. You can keep everything
  rule-based for predictable behavior.
- Job Analysis, Resume Matching, and Resume Tailoring **require** the LLM
  optional dependency (`pip install -e ".[llm]"`).
- The `resume-builder` vendor package is needed for `.docx` generation in the
  `tailor` command. If not installed, tailoring still produces JSON/Markdown
  reports but skips `.docx` generation.

## Troubleshooting

If you hit setup issues, start with `docs/troubleshooting.md`. The most common
issues are missing Gmail OAuth files (`credentials.json` / `token.json`) or an
unset `OPENAI_API_KEY` when using LLM features.
