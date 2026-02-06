# Email Opportunity Pipeline

Fetch, filter, and normalize email job opportunities into a JSON schema, then
rank them against your resume, generate tailored `.docx` resumes, and **send
personalised reply emails to recruiters** -- all in a single command with a
built-in dry-run mode for safe e2e testing before going live.

## Documentation

- `docs/cli.md`: CLI commands and examples (including `run-all` quickstart)
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
- **Recruiter Reply**: Compose and send personalised reply emails to
  recruiters with LLM-generated content, questionnaire-driven topics
  (salary, location, interview questions), and tailored resume attachments.
- **Opportunity Correlation**: Unified view linking every pipeline artifact
  (email, opportunity, match result, tailored resume, reply) per job -- see
  the complete lifecycle of each opportunity at a glance.
- **One-command e2e**: `run-all` executes the entire pipeline from fetch
  through reply in a single invocation, with a built-in dry-run mode.

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
  reply/                   # Recruiter Reply (compose + send emails)
    __init__.py
    composer.py            # LLM-powered email composition
    models.py              # QuestionnaireConfig, EmailDraft, ReplyResult
    report.py              # Markdown reply report renderer
    sender.py              # Gmail send with dry-run and attachment support
    templates.py           # Prompt templates and fallback email builder
  correlation/             # Job Opportunity Correlation
    __init__.py
    models.py              # CorrelatedOpportunity, CorrelationSummary
    correlator.py          # OpportunityCorrelator engine
    report.py              # Markdown correlation report renderer
  schemas/
    job_opportunity.schema.json
    resume.schema.json
    match_result.schema.json
    correlation.schema.json
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
  questionnaire.json           # Reply preferences (salary, location, questions)
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

### Full pipeline in one command (recommended)

The `run-all` command executes every stage -- from email fetch through
recruiter reply -- in a single invocation.  **It runs in dry-run mode by
default**, so no emails are sent until you explicitly opt in.

```bash
# 1. Set up credentials
export OPENAI_API_KEY="sk-..."        # required for LLM stages
# Place credentials.json in repo root  # Gmail OAuth (see "Gmail setup")

# 2. Edit your preferences
cp examples/questionnaire.json my_questionnaire.json
# ... edit salary, location, questions, tone ...

# 3. Dry-run the full pipeline (safe -- nothing is sent)
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire my_questionnaire.json \
  --provider gmail --window 2d \
  --min-score 70 --recommendation strong_apply,apply --top 5 \
  --work-dir data --out-dir output

# 4. Review the drafts
#    Open output/replies/drafts_preview.md to inspect every email.

# 5. Send for real (when satisfied)
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire my_questionnaire.json \
  --messages data/messages.json \
  --min-score 70 --recommendation strong_apply,apply --top 5 \
  --work-dir data --out-dir output \
  --send
```

Step 5 uses `--messages data/messages.json` to skip refetching (the messages
were already cached in step 3).

### Basic pipeline (fetch + filter + extract only)

If you only need to fetch and extract opportunities without matching/replying:

```bash
email-pipeline run \
  --provider gmail \
  --window 6h \
  --out-dir out \
  --work-dir data
```

### Step-by-step (individual commands)

```bash
email-pipeline fetch --provider gmail --window 6h --out data/messages.json
email-pipeline filter --in data/messages.json --out data/filtered.json
email-pipeline extract --in data/filtered.json --out data/opportunities.json
email-pipeline render --in data/opportunities.json --out out
```

See `docs/cli.md` for the full command reference including `analyze`, `match`,
`rank`, `tailor`, `compose`, and `reply`.

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

## Recruiter Reply

After matching and tailoring, the reply feature lets you compose and send
personalised emails back to recruiters.

### Features

- **LLM-powered composition**: emails reference match insights and candidate strengths
- **Questionnaire-driven topics**: salary, location, availability, interview questions
- **Tailored resume attachments**: `.docx` files from the tailoring step are attached automatically
- **Dry-run mode**: preview every email before sending (the default in `run-all`)
- **Gmail threading**: replies appear in the original recruiter's conversation

### Questionnaire config

Create a JSON file to control what topics are included in your reply:

```json
{
  "salary_range": "$180,000 - $220,000 USD",
  "location_preference": "Remote or hybrid in SF Bay Area",
  "availability": "Available in 2-3 weeks",
  "interview_process_questions": [
    "How many interview rounds?",
    "Is there a take-home project?"
  ],
  "custom_questions": ["How is the engineering team structured?"],
  "tone": "professional",
  "max_length_words": 300
}
```

See `examples/questionnaire.json` for the full schema.  Available tones:
`professional`, `enthusiastic`, `casual`, `concise`.

### Quick Start - Reply

Using `run-all` (simplest):

```bash
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --provider gmail --window 2d \
  --work-dir data --out-dir output
# Review output/replies/drafts_preview.md, then re-run with --send
```

Or step-by-step (after running match + tailor):

```bash
# Compose drafts
email-pipeline compose \
  --resume examples/sample_resume.json \
  --match-results out/matches/match_results.json \
  --opportunities data/opportunities.json \
  --questionnaire examples/questionnaire.json \
  --tailored-dir output/tailored \
  --out output/replies \
  --recommendation strong_apply,apply --top 5

# Preview (dry-run)
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies --dry-run

# Send
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies
```

---

## Job Opportunity Correlation

The `correlate` command creates a unified view that links every pipeline
artifact (email, opportunity, match result, tailored resume, and reply) for
each job opportunity.  This makes it easy to see exactly where each
opportunity stands in the pipeline and review all related data at a glance.

### Features

- **Unified correlation**: Links emails, opportunities, match scores, tailored
  resumes, and reply status for each job
- **Auto-discovery**: Automatically finds artifacts from `--work-dir` and
  `--out-dir` without specifying each file path
- **Rich reports**: Markdown summary tables with score breakdowns, grade
  distribution, and pipeline progress
- **Individual cards**: Detailed per-opportunity Markdown cards with score bars,
  skills analysis, timeline, and reply previews
- **Flexible filtering**: Filter by match score, recommendation, pipeline
  stage, or top-N
- **JSON output**: Machine-readable correlation data for downstream processing

### Quick Start - Correlation

After running the main pipeline (or any subset of stages):

```bash
# Auto-discover artifacts from standard directories
email-pipeline correlate \
  --work-dir data \
  --out-dir output \
  --out correlation \
  --individual-cards \
  --full-report

# Or specify explicit paths
email-pipeline correlate \
  --messages data/messages.json \
  --opportunities data/opportunities.json \
  --match-results output/matches/match_results.json \
  --tailored-dir output/tailored \
  --drafts output/replies/drafts.json \
  --reply-results output/replies/reply_results.json \
  --resume examples/sample_resume.json \
  --out correlation
```

### Filtering

```bash
# Only top matches
email-pipeline correlate \
  --work-dir data --out-dir output --out correlation \
  --min-score 70 --recommendation strong_apply,apply --top 10

# Only opportunities that reached a specific stage
email-pipeline correlate \
  --work-dir data --out-dir output --out correlation \
  --stage replied,tailored
```

### Correlation Output

The `correlate` command generates:

- `correlation.json` -- Full correlated data in JSON
- `correlation_summary.md` -- Overview report with score tables and pipeline progress
- `opportunity_cards/` -- Individual Markdown cards per opportunity (with `--individual-cards`)
- `correlation_full_report.md` -- Single comprehensive report (with `--full-report`)

### Pipeline Stages

Each opportunity is tracked through these pipeline stages:

| Stage | Icon | Description |
|-------|------|-------------|
| Fetched | 📬 | Email received from provider |
| Filtered | 🔍 | Passed filtering rules |
| Extracted | 📋 | Job opportunity extracted |
| Analyzed | 🧪 | Job requirements analyzed |
| Matched | 🎯 | Resume matched against job |
| Tailored | ✂️ | Resume tailored for job |
| Composed | ✉️ | Reply email drafted |
| Replied | ✅ | Reply sent (or dry-run) |

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
- Sending emails requires Gmail OAuth credentials with the `gmail.send` scope.
  The first time you use `reply` or `run-all --send`, you may be prompted to
  re-authorise your Google account.
- The `run-all` command defaults to **dry-run mode**.  Pass `--send` to
  actually transmit emails.

## Troubleshooting

If you hit setup issues, start with `docs/troubleshooting.md`. The most common
issues are missing Gmail OAuth files (`credentials.json` / `token.json`) or an
unset `OPENAI_API_KEY` when using LLM features.
