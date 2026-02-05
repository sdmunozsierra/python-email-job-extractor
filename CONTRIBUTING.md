## Contributing

Thanks for contributing!

### Development setup

Using `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

With optional LLM features:

```bash
uv pip install -e ".[llm]"
```

Using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### Running locally

Once installed, the CLI entrypoint is available as:

```bash
email-pipeline --help
```

If you prefer not to install the script, you can also run:

```bash
python -m email_opportunity_pipeline.cli --help
```

### Adding a new email provider

- Implement the provider in `src/email_opportunity_pipeline/providers/` by
  subclassing the `EmailProvider` interface.
- Return normalized `EmailMessage` objects.
- Register the provider in `src/email_opportunity_pipeline/cli.py` (`_build_provider`)
  and add it to the argparse `choices=...`.
- Update docs:
  - `README.md` setup section
  - `docs/architecture.md`
  - `docs/configuration.md` (any env vars)

### Changing filters or extraction

- Filters live under `src/email_opportunity_pipeline/filters/`.
- Rule-based extraction lives under `src/email_opportunity_pipeline/extraction/`.
- If you change output structure, keep schemas and docs aligned:
  - schemas: `src/email_opportunity_pipeline/schemas/`
  - docs: `README.md`, `docs/configuration.md`

### Documentation changes

Docs live in:

- `README.md`
- `docs/`

Keep examples executable and match CLI flags exactly (see `src/email_opportunity_pipeline/cli.py`).

