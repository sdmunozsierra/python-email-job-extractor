# CLI Reference

The package installs two CLI entry points:

- `email-pipeline` -- the main pipeline CLI (installed from the root package)
- `resume-builder` -- the vendor resume builder CLI (installed from `vendor/resume-builder/`)

## email-pipeline

### Global usage

```bash
email-pipeline --help
email-pipeline <command> --help
```

### Available commands

| Command | Description | LLM required |
|---------|-------------|:------------:|
| `run-all` | **Full e2e pipeline** (fetch through reply, dry-run default) | Yes |
| `fetch` | Fetch emails from a provider | No |
| `filter` | Filter emails by keyword rules | Optional |
| `extract` | Extract opportunities to schema JSON | Optional |
| `render` | Render Markdown from opportunities JSON | No |
| `run` | Basic pipeline (fetch + filter + extract + render) | Optional |
| `analytics` | Generate analytics from existing data | No |
| `analyze` | Extract structured requirements from jobs | Yes |
| `match` | Match a resume against job opportunities | Yes |
| `rank` | Filter and rank match results | No |
| `tailor` | Tailor a resume for jobs using match results | No* |
| `compose` | Compose tailored recruiter reply emails | Optional |
| `reply` | Send (or dry-run) composed reply emails | No |
| `correlate` | Correlate opportunities with emails, resumes, and replies | No |

\* The `tailor` command does not call the LLM itself but requires match results
produced by the `match` command (which does). The `resume-builder` vendor
package is needed for `.docx` generation.

---

### `fetch`

Fetch emails from a provider into a messages JSON artifact.

```bash
email-pipeline fetch --provider gmail --window 1d --out data/messages.json
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--provider` | choice | `gmail` | Provider name (currently `gmail`) |
| `--window` | string | `1d` | Time window: `30m`, `6h`, `2d` |
| `--query` | string | `""` | Provider-specific query (Gmail search syntax) |
| `--max-results` | int | unlimited | Cap the number of results |
| `--metadata-only` | flag | off | Fetch metadata only (no body/attachments) |
| `--out` | path | **required** | Output JSON path |

---

### `filter`

Run a keyword-based filtering pipeline (with optional LLM filtering).

```bash
email-pipeline filter --in data/messages.json --out data/filtered.json \
  --rules examples/filter_rules.json
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--in` | path | **required** | Input messages JSON |
| `--out` | path | **required** | Output filtered messages JSON |
| `--rules` | path | `""` | Path to filter rules JSON (overrides defaults) |
| `--llm-filter` | flag | off | Enable LLM filter stage |
| `--llm-model` | string | `gpt-4o-mini` | OpenAI model name |
| `--analytics` | flag | off | Write analytics files next to output |

When `--analytics` is set, two extra files are written next to `--out`:
- `filter_analytics.json`
- `filter_analytics_report.txt`

---

### `extract`

Normalize emails into job opportunity objects.

```bash
email-pipeline extract --in data/filtered.json --out data/opportunities.json
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--in` | path | **required** | Input messages JSON |
| `--out` | path | **required** | Output opportunities JSON |
| `--llm-extract` | flag | off | Enable LLM-based extraction |
| `--llm-model` | string | `gpt-4o-mini` | OpenAI model name |

---

### `render`

Render Markdown files (with YAML frontmatter) from opportunities JSON.

```bash
email-pipeline render --in data/opportunities.json --out out
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--in` | path | **required** | Input opportunities JSON |
| `--out` | path | **required** | Output directory for Markdown files |

---

### `run`

Full pipeline: fetch + filter + extract + render in one step.

```bash
email-pipeline run \
  --provider gmail \
  --window 6h \
  --work-dir data \
  --out-dir out
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--provider` | choice | `gmail` | Provider name |
| `--window` | string | `1d` | Time window |
| `--query` | string | `""` | Provider-specific query |
| `--max-results` | int | unlimited | Cap results |
| `--rules` | path | `""` | Path to filter rules JSON |
| `--llm-filter` | flag | off | Enable LLM filter |
| `--llm-extract` | flag | off | Enable LLM extraction |
| `--llm-model` | string | `gpt-4o-mini` | OpenAI model name |
| `--work-dir` | path | `data` | Where JSON artifacts are written |
| `--out-dir` | path | `out` | Where Markdown files are written |
| `--no-analytics` | flag | off | Disable analytics generation |
| `--show-report` | flag | off | Print analytics report to stdout |

---

### `run-all`

**Full end-to-end pipeline** that executes every stage in sequence:

```
fetch -> filter -> extract -> analyze -> match -> tailor -> compose -> reply
```

By default it runs in **dry-run mode** -- the entire pipeline executes but no
emails are actually sent.  Pass `--send` to transmit for real.
Add `--interactive` to step through each stage, skip parts of the pipeline,
and manually select items before moving forward.

**Dry-run (e2e testing):**

```bash
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --provider gmail --window 2d \
  --work-dir data --out-dir output
```

**Send for real (production):**

```bash
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --provider gmail --window 2d \
  --work-dir data --out-dir output \
  --send
```

**Skip fetch (re-use existing messages):**

```bash
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --messages data/messages.json \
  --work-dir data --out-dir output
```

**With filtering and LLM options:**

```bash
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --provider gmail --window 7d \
  --rules examples/filter_rules.json \
  --llm-filter --llm-extract \
  --min-score 70 --recommendation strong_apply,apply --top 5 \
  --llm-model gpt-4o-mini \
  --work-dir data --out-dir output
```

**Interactive mode (skip stages + select items):**

```bash
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --provider gmail --window 2d \
  --work-dir data --out-dir output \
  --interactive
```

#### Options

**Input sources:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--resume` | path | **required** | Candidate resume file (JSON or Markdown) |
| `--questionnaire` | path | -- | Questionnaire config JSON (see `examples/questionnaire.json`) |
| `--messages` | path | -- | Skip fetch; use an existing messages JSON file |

**Fetch options** (ignored when `--messages` is set):

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--provider` | choice | `gmail` | Provider name |
| `--window` | string | `1d` | Time window (`30m`, `6h`, `2d`) |
| `--query` | string | `""` | Provider-specific query |
| `--max-results` | int | unlimited | Cap fetched messages |

**Filter and extraction:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--rules` | path | `""` | Path to filter rules JSON |
| `--llm-filter` | flag | off | Enable LLM filter |
| `--llm-extract` | flag | off | Enable LLM extraction |

**Match selection** (which jobs to tailor and reply to):

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--min-score` | float | -- | Only tailor/reply for jobs above this score |
| `--recommendation` | string | -- | Comma-separated recommendations (`strong_apply,apply`) |
| `--top` | int | -- | Limit to top N matches by score |

**Output:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--work-dir` | path | `data` | Where JSON artifacts are written |
| `--out-dir` | path | `output` | Where reports, tailored resumes, and replies go |

**Behaviour:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--send` | flag | off | Actually send emails (default is dry-run) |
| `--no-docx` | flag | off | Skip `.docx` generation |
| `--llm-model` | string | `gpt-4o-mini` | LLM model for all stages |
| `--interactive` | flag | off | Prompt to skip stages and select items |

**Recipient override and audit:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--override-to` | string | -- | Redirect **all** reply emails to this address |
| `--cc` | string(s) | -- | One or more CC addresses for every reply email |
| `--bcc` | string(s) | -- | One or more BCC addresses for every reply email |

See the [`reply`](#reply) command for detailed examples and use cases.

#### Output directory structure

After a successful run, the output looks like:

```
data/                           # --work-dir
  messages.json
  filtered.json
  opportunities.json
  job_analyses.json
  analytics.json
  analytics_report.txt

output/                         # --out-dir
  markdown/                     # rendered opportunity files
    <message_id>.md
  matches/
    match_results.json
    match_summary.md
  tailored/
    tailored_resume_<company>_<title>.docx
    tailoring_results.json
    tailoring_summary.md
    tailoring_reports/
      <job_id>_report.md
      <job_id>_report.json
      <job_id>_resume.json
  replies/
    drafts.json
    drafts_preview.md           # <-- review this before sending
    reply_results.json
    reply_report.md

correlation/                    # email-pipeline correlate output
  correlation.json
  correlation_summary.md
  opportunity_cards/            # with --individual-cards
    <job_id>.md
  correlation_full_report.md    # with --full-report
```

---

### `analytics`

Generate analytics from existing data files (useful when iterating on rules).

```bash
email-pipeline analytics \
  --messages data/messages.json \
  --opportunities data/opportunities.json \
  --out-dir data
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--messages` | path | -- | Path to messages JSON |
| `--filtered` | path | -- | (reserved, currently unused) |
| `--opportunities` | path | -- | Path to opportunities JSON |
| `--rules` | path | `""` | Rules JSON for re-filtering messages |
| `--out-dir` | path | `.` | Output directory for analytics files |

Produces `analytics.json` and `analytics_report.txt` in the output directory.

---

## Job Analysis & Resume Matching (LLM)

These commands require the optional dependency (`pip install -e ".[llm]"`) and
`OPENAI_API_KEY`.

### `analyze`

Extract structured requirements from opportunities.

```bash
email-pipeline analyze \
  --in data/opportunities.json \
  --out data/job_analyses.json
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--in` | path | **required** | Input opportunities JSON |
| `--out` | path | **required** | Output job analyses JSON |
| `--llm-model` | string | `gpt-4o-mini` | OpenAI model name |

The output contains structured data per job:
- Role summary (title, level, department)
- Requirements (skills, experience, education, certifications)
- Technical environment (languages, frameworks, databases, cloud, tools)
- Culture indicators and compensation analysis
- ATS keywords and role classification

---

### `match`

Match a resume against one or many opportunities.

**Single job:**

```bash
email-pipeline match \
  --resume examples/sample_resume.json \
  --opportunities data/opportunities.json \
  --job-index 0 \
  --out out/match_report.md \
  --format markdown
```

**Batch (all jobs):**

```bash
email-pipeline match \
  --resume examples/sample_resume.json \
  --opportunities data/opportunities.json \
  --analyses data/job_analyses.json \
  --out out/matches \
  --individual-reports
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--resume` | path | **required** | Resume file (JSON or Markdown) |
| `--opportunities` | path | **required** | Opportunities JSON |
| `--analyses` | path | -- | Pre-computed job analyses JSON (optional) |
| `--job-index` | int | -- | Match single job by 0-based index |
| `--out` | path | **required** | Output path (file for single, dir for batch) |
| `--format` | choice | `markdown` | Output format for single match: `json` or `markdown` |
| `--individual-reports` | flag | off | Generate per-job Markdown reports (batch mode) |
| `--llm-model` | string | `gpt-4o-mini` | OpenAI model name |

**Batch outputs:**
- `match_results.json` -- all match data
- `match_summary.md` -- overview report with rankings
- `match_reports/*.md` -- individual reports (with `--individual-reports`)

---

### `rank`

Filter and rank previously computed match results.

```bash
email-pipeline rank \
  --in out/matches/match_results.json \
  --min-score 70 \
  --recommendation strong_apply,apply \
  --top 10
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--in` | path | **required** | Input match results JSON |
| `--out` | path | -- | Output filtered results JSON (optional) |
| `--min-score` | float | -- | Minimum overall score |
| `--grade` | string | -- | Comma-separated grades (`excellent,good`) |
| `--recommendation` | string | -- | Comma-separated recommendations (`strong_apply,apply`) |
| `--top` | int | -- | Limit to top N results |

Results are always sorted by score descending and printed to stdout.

---

## Resume Tailoring

### `tailor`

Tailor a resume for one or more job opportunities using match results. Generates
tailored `.docx` files and detailed change reports.

```bash
email-pipeline tailor \
  --resume examples/sample_resume.json \
  --match-results out/matches/match_results.json \
  --opportunities data/opportunities.json \
  --out output/tailored
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--resume` | path | **required** | Original resume file (JSON or Markdown) |
| `--match-results` | path | **required** | Match results JSON (from `match`) |
| `--opportunities` | path | -- | Opportunities JSON (for job context) |
| `--out` | path | **required** | Output directory |
| `--min-score` | float | -- | Only tailor for jobs above this score |
| `--recommendation` | string | -- | Comma-separated recommendations to filter |
| `--top` | int | -- | Limit to top N results by score |
| `--no-docx` | flag | off | Skip `.docx` generation |

**Per-job outputs:**
- `tailoring_reports/<job_id>_resume.json` -- tailored resume data
- `tailoring_reports/<job_id>_report.json` -- structured change report
- `tailoring_reports/<job_id>_report.md` -- Markdown change report
- `tailored_resume_<company>_<title>.docx` -- Word document

**Batch outputs:**
- `tailoring_results.json` -- all results in one file
- `tailoring_summary.md` -- summary across all tailored resumes

---

## Recruiter Reply

### `compose`

Compose tailored reply emails to recruiters using LLM-powered personalisation.
Generates email drafts that incorporate match insights, candidate strengths,
and user-defined questionnaire topics (salary, location, interview process, etc.).

```bash
email-pipeline compose \
  --resume examples/sample_resume.json \
  --match-results out/matches/match_results.json \
  --opportunities data/opportunities.json \
  --questionnaire examples/questionnaire.json \
  --tailored-dir output/tailored \
  --out output/replies \
  --recommendation strong_apply,apply \
  --top 5
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--resume` | path | **required** | Candidate resume file (JSON or Markdown) |
| `--match-results` | path | **required** | Match results JSON (from `match`) |
| `--opportunities` | path | -- | Opportunities JSON (for recruiter contact info) |
| `--questionnaire` | path | -- | Questionnaire config JSON (salary, location, etc.) |
| `--tailored-dir` | path | -- | Directory with tailored `.docx` resumes to attach |
| `--out` | path | **required** | Output directory for drafts and previews |
| `--min-score` | float | -- | Only compose for jobs above this score |
| `--recommendation` | string | -- | Comma-separated recommendations to filter |
| `--top` | int | -- | Limit to top N results by score |
| `--llm-model` | string | `gpt-4o-mini` | LLM model for email composition |

**Outputs:**
- `drafts.json` -- all email drafts in machine-readable format
- `drafts_preview.md` -- batch preview report (Markdown)
- `previews/<job_id>_preview.md` -- individual draft previews

When no `--questionnaire` is provided, a default configuration is used.  When
the LLM is unavailable (no `openai` package or API key), a plain-text template
is used as a fallback.

#### Questionnaire config

The questionnaire JSON controls which topics to include and how the LLM should
write the reply.  See `examples/questionnaire.json` for the full schema:

```json
{
  "salary_range": "$180,000 - $220,000 USD",
  "location_preference": "Remote or hybrid in SF Bay Area",
  "availability": "Available in 2-3 weeks",
  "interview_process_questions": [
    "How many interview rounds?",
    "Is there a take-home project?"
  ],
  "custom_questions": [
    "What does a typical day look like?"
  ],
  "tone": "professional",
  "max_length_words": 300
}
```

Available tones: `professional`, `enthusiastic`, `casual`, `concise`.

---

### `reply`

Send (or dry-run preview) previously composed email drafts.

**Dry-run (preview without sending):**

```bash
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies \
  --dry-run
```

**Actually send:**

```bash
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--drafts` | path | **required** | Drafts JSON file (from `compose`) |
| `--out` | path | **required** | Output directory for results and report |
| `--dry-run` | flag | off | Preview emails without sending |
| `--index` | int | -- | Send only the draft at this index (0-based) |
| `--override-to` | string | -- | Redirect **all** emails to this address (original is preserved in reports) |
| `--cc` | string(s) | -- | One or more CC addresses added to every email |
| `--bcc` | string(s) | -- | One or more BCC addresses added to every email |

**Recipient override and audit:**

The `--override-to`, `--cc`, and `--bcc` flags are designed for two key scenarios:

1. **Testing / staging:** Use `--override-to you@example.com` to redirect all
   outgoing emails to your own mailbox.  The original recruiter address is
   preserved in reports (`original_to` field) so you can verify everything
   looks correct before switching to live mode.

2. **Audit trail / visibility:** Use `--bcc audit@yourcompany.com` to silently
   copy every outgoing email to a compliance or audit mailbox, or use
   `--cc manager@yourcompany.com` for visible copies.

These flags are also available on `run-all`.

**Examples:**

```bash
# Test: redirect all emails to yourself
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies \
  --override-to test@example.com

# Audit: BCC a compliance mailbox on every sent email
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies \
  --bcc audit@example.com

# Combine: override recipient + BCC audit
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies \
  --override-to test@example.com \
  --bcc audit@example.com compliance@example.com
```

**Outputs:**
- `reply_results.json` -- machine-readable send results
- `reply_report.md` -- Markdown report of what was sent / previewed

**Note:** Sending requires OAuth credentials with the `gmail.send` scope.
The first time you send, you may be prompted to re-authorise your Google
account to grant the send permission.

---

## resume-builder (vendor CLI)

The vendor `resume-builder` package provides a standalone CLI for generating
`.docx` resumes from JSON or legacy Python data.

```bash
resume-builder --help
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--json` | path | -- | Resume JSON file path. If omitted, uses legacy data. |
| `--output` | path | `resume.docx` | Output `.docx` file name |

### Examples

```bash
# From JSON schema
resume-builder --json examples/sample_resume.json --output my_resume.docx

# Python API
python -c "
from resume_builder.schema_adapter import ResumeSchemaAdapter
from resume_builder.cli import build_resume

person = ResumeSchemaAdapter.from_json_file('examples/sample_resume.json')
doc = build_resume(person)
doc.save('my_resume.docx')
"
```

---

## Job Opportunity Correlation

### `correlate`

Build a unified correlation view that links every pipeline artifact (email,
opportunity, match result, tailored resume, reply) for each job opportunity.
Generates rich Markdown reports and machine-readable JSON data.

**Auto-discovery mode (simplest):**

```bash
email-pipeline correlate \
  --work-dir data \
  --out-dir output \
  --out correlation \
  --individual-cards \
  --full-report
```

**Explicit paths:**

```bash
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

**With filtering:**

```bash
email-pipeline correlate \
  --work-dir data --out-dir output \
  --out correlation \
  --min-score 70 --recommendation strong_apply,apply --top 10
```

#### Options

**Auto-discovery:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--work-dir` | path | -- | Work directory (messages.json, opportunities.json, etc.) |
| `--out-dir` | path | -- | Output directory (matches/, tailored/, replies/) |

**Explicit artifact paths:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--messages` | path | -- | Path to messages JSON file |
| `--opportunities` | path | -- | Path to opportunities JSON file |
| `--match-results` | path | -- | Path to match results JSON file |
| `--tailored-dir` | path | -- | Directory containing tailoring_results.json |
| `--drafts` | path | -- | Path to drafts JSON file |
| `--reply-results` | path | -- | Path to reply results JSON file |
| `--resume` | path | -- | Resume file (for candidate name in reports) |

**Filtering:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--min-score` | float | -- | Only include opportunities above this score |
| `--recommendation` | string | -- | Comma-separated recommendations to include |
| `--stage` | string | -- | Comma-separated pipeline stages to include |
| `--top` | int | -- | Limit to top N opportunities by score |

**Output:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--out` | path | **required** | Output directory for correlation results |
| `--individual-cards` | flag | off | Generate per-opportunity Markdown cards |
| `--full-report` | flag | off | Generate single comprehensive report with all cards |

**Outputs:**
- `correlation.json` -- Full correlated data in JSON
- `correlation_summary.md` -- Overview report with score tables
- `opportunity_cards/<job_id>.md` -- Individual cards (with `--individual-cards`)
- `correlation_full_report.md` -- Single report with all cards (with `--full-report`)

---

## End-to-end workflow

### One command (recommended)

The `run-all` command runs every stage in a single invocation.  By default it
operates in **dry-run mode** so nothing is sent:

```bash
# 1. Dry-run -- fetch, filter, extract, analyze, match, tailor, compose, preview
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --provider gmail --window 2d \
  --min-score 70 --recommendation strong_apply,apply --top 5 \
  --work-dir data --out-dir output

# 2. Review output/replies/drafts_preview.md

# 3. Send for real (once you are satisfied)
email-pipeline run-all \
  --resume examples/sample_resume.json \
  --questionnaire examples/questionnaire.json \
  --messages data/messages.json \
  --min-score 70 --recommendation strong_apply,apply --top 5 \
  --work-dir data --out-dir output --send
```

The second invocation uses `--messages data/messages.json` to skip
refetching and reuse the cached messages from step 1.

### Step-by-step (advanced)

If you need more control over individual stages:

```bash
# 1. Fetch emails
email-pipeline fetch --provider gmail --window 2d --out data/messages.json

# 2. Filter for job opportunities
email-pipeline filter --in data/messages.json --out data/filtered.json \
  --rules examples/filter_rules.json --analytics

# 3. Extract structured opportunities
email-pipeline extract --in data/filtered.json --out data/opportunities.json

# 4. Render Markdown
email-pipeline render --in data/opportunities.json --out out

# 5. Analyze jobs (LLM)
email-pipeline analyze --in data/opportunities.json --out data/job_analyses.json

# 6. Match resume against all jobs (LLM)
email-pipeline match \
  --resume examples/sample_resume.json \
  --opportunities data/opportunities.json \
  --analyses data/job_analyses.json \
  --out out/matches \
  --individual-reports

# 7. Rank and filter matches
email-pipeline rank \
  --in out/matches/match_results.json \
  --min-score 70 --top 10

# 8. Tailor resume for top matches
email-pipeline tailor \
  --resume examples/sample_resume.json \
  --match-results out/matches/match_results.json \
  --opportunities data/opportunities.json \
  --out output/tailored \
  --recommendation strong_apply,apply \
  --top 5

# 9. Compose recruiter reply emails (LLM)
email-pipeline compose \
  --resume examples/sample_resume.json \
  --match-results out/matches/match_results.json \
  --opportunities data/opportunities.json \
  --questionnaire examples/questionnaire.json \
  --tailored-dir output/tailored \
  --out output/replies \
  --recommendation strong_apply,apply \
  --top 5

# 10. Review drafts (dry run)
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies \
  --dry-run

# 11. Send emails to recruiters
email-pipeline reply \
  --drafts output/replies/drafts.json \
  --out output/replies

# 12. Correlate all artifacts (review full lifecycle)
email-pipeline correlate \
  --work-dir data --out-dir output \
  --resume examples/sample_resume.json \
  --out correlation \
  --individual-cards --full-report
```
