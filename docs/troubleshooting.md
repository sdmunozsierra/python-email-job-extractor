# Troubleshooting

## Installation issues

### pip: `ERROR: No matching distribution found for resume-builder`

When installing with pip, the `[tool.uv.sources]` path dependency is not
recognized. Install the vendor package first:

```bash
pip install -e vendor/resume-builder
pip install -e .
```

### uv: vendor package not found

If `uv sync` fails to find the vendor package, make sure the subtree is present:

```bash
ls vendor/resume-builder/pyproject.toml
```

If the file is missing, the subtree may not have been pulled. Re-add it:

```bash
git subtree add --prefix=vendor/resume-builder <remote-url> main --squash
uv sync
```

### `ModuleNotFoundError: No module named 'resume_builder'`

The vendor package is not installed. Fix:

```bash
# uv
uv sync

# pip
pip install -e vendor/resume-builder
```

---

## Gmail issues

### `FileNotFoundError: credentials.json`

- Create OAuth client credentials (Desktop app) in Google Cloud Console.
- Download the JSON and either:
  - place it at the repo root as `credentials.json`, or
  - set `GMAIL_CREDENTIALS_PATH` to its path.

### Token isn't created / auth flow fails

- The first Gmail run opens a local browser flow and writes `token.json`.
- Ensure you can complete the browser auth step on the machine running the CLI.
- If you need a custom token location, set `GMAIL_TOKEN_PATH`.

### Gmail API not enabled

If you see errors about the Gmail API being disabled:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **APIs & Services > Library**.
3. Search for "Gmail API" and enable it for your project.

---

## LLM issues

### `RuntimeError: Install optional dependency`

Install the optional LLM extra:

```bash
# uv
uv pip install -e ".[llm]"

# pip
pip install -e ".[llm]"
```

### Authentication errors / `openai.AuthenticationError`

Set an OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

If you're running in CI or a hosted environment, set this as a secret and pass
it as an environment variable.

### Rate limit errors

The `analyze` and `match` commands make one LLM call per job opportunity. For
large batches, you may hit rate limits. Strategies:

- Use a higher-tier API key.
- Process in smaller batches (use `--job-index` for single jobs).
- Add delays between calls (not yet built into the CLI).

---

## CLI issues

### `window must look like 30m, 6h, or 2d`

Time windows are limited to integer minutes/hours/days using a suffix:

| Suffix | Meaning | Examples |
|--------|---------|---------|
| `m` | minutes | `15m`, `30m` |
| `h` | hours | `6h`, `12h` |
| `d` | days | `1d`, `7d` |

### `email-pipeline: command not found`

The script may not be on your PATH. Try:

```bash
# Check where it was installed
pip show email-opportunity-pipeline

# Run via Python module instead
python -m email_opportunity_pipeline.cli --help
```

Or add the install directory to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### `resume-builder: command not found`

Same as above -- the vendor CLI may not be on your PATH:

```bash
python -m resume_builder --help
```

---

## Tailoring issues

### `.docx` generation skipped / warning about resume-builder

The tailoring engine gracefully degrades if `resume-builder` is not installed.
You will see:

```
WARNING: resume-builder package not installed; skipping .docx generation.
```

To fix, install the vendor package:

```bash
pip install -e vendor/resume-builder
```

JSON and Markdown reports will still be generated regardless.

### `KeyError` or unexpected schema errors during tailoring

This usually means the resume JSON does not match the expected schema. Verify
your resume JSON has the required top-level keys:

```json
{
  "personal": { "name": "..." },
  "skills": { "technical": [...] },
  "experience": [...],
  "education": [...]
}
```

See `examples/sample_resume.json` for a complete example.

### Tailoring produces no changes

If the `TailoringReport` shows zero changes, the match result likely had empty
tailoring suggestions. This can happen if:

- The LLM returned minimal tailoring data.
- The match score was very high (little to change).
- The resume already closely matches the job.

---

## Docker / Kubernetes issues

### `docker build` fails with pip errors

Make sure the `.dockerignore` is present and excludes `.venv`, `__pycache__`,
and other local artifacts. If you see network errors during `pip install`,
check your Docker network configuration or proxy settings.

### Container cannot authenticate with Gmail

The Gmail OAuth flow requires a browser. You **must** complete the OAuth flow
locally first to generate `token.json`, then supply it to the container via a
Secret or volume mount:

```bash
# Run locally once to generate token.json
email-pipeline fetch --provider gmail --window 1h --out /dev/null

# Then mount the token into the container
docker run --rm \
  -v "$PWD/token.json:/app/secrets/gmail/token.json:ro" \
  -v "$PWD/credentials.json:/app/secrets/gmail/credentials.json:ro" \
  email-pipeline:latest fetch --provider gmail --window 1h --out /app/data/test.json
```

In Kubernetes, store both files in the `gmail-credentials` Secret.

### CronJob pods stuck in `CrashLoopBackOff`

Common causes:

1. **Missing secrets** -- the `OPENAI_API_KEY` or Gmail credentials are not
   configured. Check `kubectl -n email-pipeline get secrets`.
2. **Missing resume** -- the CronJob expects a resume at
   `/app/resumes/resume.json`. Copy it into the PVC first.
3. **PVC not bound** -- check `kubectl -n email-pipeline get pvc` to ensure
   all volumes are bound.

### Streamlit UI pod not ready

The Deployment has readiness and liveness probes on port 8502. If the pod is
not becoming ready:

1. Check logs: `kubectl -n email-pipeline logs deploy/email-pipeline-ui`
2. Verify the Streamlit extra is installed in the image (`pip install ".[ui]"`)
3. Ensure the port matches (8502 in both the container and the probe)

---

## Data issues

### `JSONDecodeError` when reading artifacts

All artifact files must be valid JSON. Common causes:

- File was truncated (e.g. disk full during write).
- Manual editing introduced syntax errors.
- File encoding is not UTF-8.

### Empty results from `filter`

If all messages are filtered out:

1. Check `--analytics` output to see why messages were rejected.
2. Review your rules file -- restrictive rules may exclude valid opportunities.
3. Try running without a rules file to use defaults: `email-pipeline filter --in data/messages.json --out data/filtered.json`

### Match results all show score 0

This usually indicates an LLM API failure. Check:

1. `OPENAI_API_KEY` is set and valid.
2. The model name is correct (default: `gpt-4o-mini`).
3. Network connectivity to the OpenAI API.
