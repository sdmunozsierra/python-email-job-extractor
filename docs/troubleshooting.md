## Troubleshooting

### Gmail: `FileNotFoundError: credentials.json`

- Create OAuth client credentials (Desktop app) in Google Cloud Console.
- Download the JSON and either:
  - place it at the repo root as `credentials.json`, or
  - set `GMAIL_CREDENTIALS_PATH` to its path.

### Gmail: token isn’t created / auth flow fails

- The first Gmail run opens a local browser flow and writes `token.json`.
- Ensure you can complete the browser auth step on the machine running the CLI.
- If you need a custom token location, set `GMAIL_TOKEN_PATH`.

### LLM features: `RuntimeError: Install optional dependency`

Install the optional extra:

```bash
python -m pip install -e ".[llm]"
```

### LLM features: authentication errors

Set an OpenAI API key:

```bash
export OPENAI_API_KEY="..."
```

If you’re running in CI or a hosted environment, set this as a secret and pass
it as an environment variable.

### `window must look like 30m, 6h, or 2d`

Time windows are limited to integer minutes/hours/days using a suffix:

- `m` minutes
- `h` hours
- `d` days

Examples: `15m`, `6h`, `2d`.

