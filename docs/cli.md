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
| `fetch` | Fetch emails from a provider | No |
| `filter` | Filter emails by keyword rules | Optional |
| `extract` | Extract opportunities to schema JSON | Optional |
| `render` | Render Markdown from opportunities JSON | No |
| `run` | Full pipeline (fetch + filter + extract + render) | Optional |
| `analytics` | Generate analytics from existing data | No |
| `analyze` | Extract structured requirements from jobs | Yes |
| `match` | Match a resume against job opportunities | Yes |
| `rank` | Filter and rank match results | No |
| `tailor` | Tailor a resume for jobs using match results | No* |

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

## End-to-end workflow

A typical complete workflow:

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
```
