# Email Opportunity Pipeline

Fetch, filter, and normalize email job opportunities into a JSON schema, then
render Markdown with YAML frontmatter for downstream automation.

## Why this exists

- **Provider-agnostic**: Gmail is supported now, but the interface is designed
  so you can plug in Microsoft, AWS, ForwardEmail, etc.
- **Time-windowed fetch**: Grab the latest X minutes/hours/days.
- **Filtering pipeline**: Rule-based keyword/phrase filtering first, then an
  optional LLM filter.
- **Structured output**: Normalize into a dedicated JSON schema and render
  Markdown with frontmatter so you can ask clarifying questions, send resumes,
  or audit conversations later.

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
  schemas/
    job_opportunity.schema.json
examples/
  filter_rules.json
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

## Notes

- Gmail attachments are listed but not downloaded.
- The LLM filter and LLM extractor are **optional**. You can keep everything
  rule-based for predictable behavior.
