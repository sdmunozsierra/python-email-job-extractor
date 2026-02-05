## CLI reference

The package installs a CLI named `email-pipeline` (see `pyproject.toml`).

### Global usage

```bash
email-pipeline --help
email-pipeline <command> --help
```

### Commands

#### `fetch`

Fetch emails from a provider into a messages JSON artifact.

```bash
email-pipeline fetch --provider gmail --window 1d --out data/messages.json
```

Options:

- `--provider`: provider name (currently `gmail`)
- `--window`: time window like `30m`, `6h`, `2d`
- `--query`: provider-specific query string (Gmail search query). If omitted, uses the window.
- `--max-results`: cap results
- `--metadata-only`: fetch Gmail metadata only (no body/attachments listing)
- `--out`: output JSON path

#### `filter`

Run a keyword-based filtering pipeline (with optional LLM filtering).

```bash
email-pipeline filter --in data/messages.json --out data/filtered.json \
  --rules examples/filter_rules.json
```

Options:

- `--in`: input messages JSON (created by `fetch` or compatible format)
- `--out`: output messages JSON (filtered)
- `--rules`: path to filter rules JSON (optional; overrides defaults)
- `--llm-filter`: enable LLM filter stage (requires `.[llm]` + `OPENAI_API_KEY`)
- `--llm-model`: OpenAI model name (default: `gpt-4o-mini`)
- `--analytics`: write `filter_analytics.json` and `filter_analytics_report.txt` next to `--out`

#### `extract`

Normalize emails into job opportunity objects (schema-backed if using LLM extractor).

```bash
email-pipeline extract --in data/filtered.json --out data/opportunities.json
```

Options:

- `--in`: input messages JSON
- `--out`: output opportunities JSON
- `--llm-extract`: enable LLM-based extraction (requires `.[llm]` + `OPENAI_API_KEY`)
- `--llm-model`: OpenAI model name (default: `gpt-4o-mini`)

#### `render`

Render Markdown files (with YAML frontmatter) from opportunities JSON.

```bash
email-pipeline render --in data/opportunities.json --out out
```

Options:

- `--in`: input opportunities JSON
- `--out`: output directory

#### `run`

Fetch + filter + extract + render in one step.

```bash
email-pipeline run \
  --provider gmail \
  --window 6h \
  --work-dir data \
  --out-dir out
```

Options:

- `--provider`, `--window`, `--query`, `--max-results`: same intent as `fetch`
- `--rules`, `--llm-filter`, `--llm-extract`, `--llm-model`: same intent as `filter`/`extract`
- `--work-dir`: where JSON artifacts are written (default: `data`)
- `--out-dir`: where Markdown is written (default: `out`)
- `--no-analytics`: disable analytics generation
- `--show-report`: print the analytics report to stdout

#### `analytics`

Generate analytics from existing data files (useful when iterating on rules).

```bash
email-pipeline analytics --messages data/messages.json --opportunities data/opportunities.json --out-dir data
```

Options:

- `--messages`: messages JSON file
- `--filtered`: (currently unused by the command implementation; safe to omit)
- `--opportunities`: opportunities JSON file
- `--rules`: rules JSON path (used if re-filtering messages)
- `--out-dir`: output directory (writes `analytics.json` + `analytics_report.txt`)

### Job analysis & resume matching (LLM)

These commands require the optional dependency (`pip install -e ".[llm]"`) and
`OPENAI_API_KEY`.

#### `analyze`

Extract structured requirements from opportunities.

```bash
email-pipeline analyze --in data/opportunities.json --out data/job_analyses.json
```

#### `match`

Match a resume against one or many opportunities.

Single job:

```bash
email-pipeline match \
  --resume examples/sample_resume.json \
  --opportunities data/opportunities.json \
  --job-index 0 \
  --out out/match_report.md \
  --format markdown
```

Batch:

```bash
email-pipeline match \
  --resume examples/sample_resume.json \
  --opportunities data/opportunities.json \
  --analyses data/job_analyses.json \
  --out out/matches \
  --individual-reports
```

#### `rank`

Filter and rank previously computed match results.

```bash
email-pipeline rank --in out/matches/match_results.json --min-score 70 --top 10
```

### Resume tailoring

This command requires the `resume-builder` subtree package (installed
automatically via `uv sync`).

#### `tailor`

Tailor a resume for one or more job opportunities using match results. Generates
tailored `.docx` files and detailed change reports.

```bash
email-pipeline tailor \
  --resume examples/sample_resume.json \
  --match-results out/matches/match_results.json \
  --opportunities data/opportunities.json \
  --out output/tailored
```

Options:

- `--resume`: path to the original resume file (JSON or Markdown)
- `--match-results`: path to match results JSON (output of `match` command)
- `--opportunities`: path to opportunities JSON (for job context in reports)
- `--out`: output directory for tailored resumes, reports, and `.docx` files
- `--min-score`: only tailor for jobs above this match score
- `--recommendation`: comma-separated recommendations to filter (e.g. `strong_apply,apply`)
- `--top`: limit to top N results by score
- `--no-docx`: skip `.docx` generation (JSON/Markdown reports only)

**Outputs per job:**

- `<job_id>_resume.json` -- the tailored resume data
- `<job_id>_report.json` -- structured tailoring report
- `<job_id>_report.md` -- human-readable Markdown change report
- `tailored_resume_<company>_<title>.docx` -- the generated Word document

**Batch outputs:**

- `tailoring_results.json` -- all tailoring results in one file
- `tailoring_summary.md` -- summary across all tailored resumes

