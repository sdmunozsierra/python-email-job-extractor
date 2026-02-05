## Configuration

This project is intentionally lightweight: configuration is primarily via CLI
flags and a small set of environment variables.

### Environment variables

#### Gmail provider

The Gmail provider reads OAuth files from the repo root by default:

- `GMAIL_CREDENTIALS_PATH`: defaults to `credentials.json`
- `GMAIL_TOKEN_PATH`: defaults to `token.json`

These files are already ignored in `.gitignore`.

#### OpenAI / LLM features (optional)

LLM features use the OpenAI Python SDK. Provide credentials via:

- `OPENAI_API_KEY`

The CLI also supports choosing the model via `--llm-model` (default:
`gpt-4o-mini`).

### Filter rules file

`email-pipeline filter` accepts a JSON rules file (see `examples/filter_rules.json`).

Important behavior:

- The rules file is **merged on top of built-in defaults**, so you can specify
  only the keys you want to override.
- Keys not present in your file fall back to defaults in
  `src/email_opportunity_pipeline/filters/rules.py`.

Common keys:

- `job_source_domains`: domains treated as strong job sources (ATS / job boards)
- `non_job_domains`: domain denylist
- `job_keywords`: strong job keywords
- `weak_job_keywords`: ambiguous keywords (only count when multiple are present)
- `role_title_patterns`: regex patterns to detect role titles
- `promo_negative_patterns`: regex patterns for promotions/commerce
- `transactional_patterns`: regex patterns for receipts/account/security emails
- `marketing_footer_patterns`: regex patterns to detect newsletter footers

### Time windows

Time windows use the format:

- `30m` for minutes
- `6h` for hours
- `2d` for days

This format is parsed by `src/email_opportunity_pipeline/time_window.py`.

### Output artifacts

Most commands write a wrapper object containing timestamps and counts. For example:

- `messages.json` contains `{ fetched_at_utc, count, messages: [...] }`
- `opportunities.json` contains `{ created_at_utc, count, opportunities: [...] }`
- `match_results.json` contains `{ created_at_utc, resume_id, count, match_results: [...] }`
- `job_analyses.json` contains `{ created_at_utc, count, analyses: [...] }`

Markdown output is written as one file per opportunity using the source email
message id, e.g. `out/<message_id>.md`.

