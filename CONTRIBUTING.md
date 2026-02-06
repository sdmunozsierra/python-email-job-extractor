# Contributing

Thanks for contributing!

## Development setup

### Using uv (recommended)

```bash
uv venv
source .venv/bin/activate
uv sync
```

This installs the main package, the vendor `resume-builder` subtree, and all
dependencies in one step.

### Using pip

With pip, install the vendor dependency first:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e vendor/resume-builder
pip install -e .
```

### Optional LLM features

```bash
# uv
uv pip install -e ".[llm]"

# pip
pip install -e ".[llm]"
```

## Running locally

Once installed, the CLI entry points are available:

```bash
email-pipeline --help
resume-builder --help
```

If you prefer not to install the scripts, you can also run:

```bash
python -m email_opportunity_pipeline.cli --help
python -m resume_builder --help
```

## Project structure

```
src/email_opportunity_pipeline/   # Main package
  providers/                      # Email providers (Gmail, etc.)
  filters/                        # Filter pipeline
  extraction/                     # Opportunity extraction
  matching/                       # Job analysis & resume matching (LLM)
  tailoring/                      # Resume tailoring (uses vendor/resume-builder)
  schemas/                        # JSON schemas
vendor/
  resume-builder/                 # Git subtree: .docx resume generation
examples/
docs/
```

## Adding a new email provider

1. Implement the provider in `src/email_opportunity_pipeline/providers/` by
   subclassing the `EmailProvider` interface:

   ```python
   from email_opportunity_pipeline.providers.base import EmailProvider
   from email_opportunity_pipeline.models import EmailMessage
   from email_opportunity_pipeline.time_window import TimeWindow

   class MyProvider(EmailProvider):
       def fetch_messages(self, window, max_results=None, query=None, include_body=True):
           # Return Iterable[EmailMessage]
           ...
   ```

2. Return normalized `EmailMessage` objects.
3. Register the provider in `src/email_opportunity_pipeline/cli.py` (`_build_provider`)
   and add it to the argparse `choices=...`.
4. Update docs:
   - `README.md` setup section
   - `docs/architecture.md`
   - `docs/configuration.md` (any env vars)

## Adding a filter

1. Subclass `EmailFilter` in `src/email_opportunity_pipeline/filters/`:

   ```python
   from email_opportunity_pipeline.filters.base import EmailFilter
   from email_opportunity_pipeline.models import EmailMessage, FilterDecision

   class MyFilter(EmailFilter):
       name = "my_filter"

       def evaluate(self, email: EmailMessage) -> FilterDecision:
           passed = ...  # Your logic
           return FilterDecision(filter_name=self.name, passed=passed, reasons=[...])
   ```

2. Wire it into `build_filter_pipeline()` in `pipeline.py`.
3. Update docs if the filter has new CLI flags or configuration.

## Adding an extractor

1. Subclass `BaseExtractor` in `src/email_opportunity_pipeline/extraction/`:

   ```python
   from email_opportunity_pipeline.extraction.extractor import BaseExtractor

   class MyExtractor(BaseExtractor):
       def extract(self, email):
           # Return a dict conforming to schemas/job_opportunity.schema.json
           return {...}
   ```

2. Wire it into `extract_opportunities()` in `pipeline.py`.

## Changing the matching module

The matching module lives at `src/email_opportunity_pipeline/matching/`:

- `models.py`: Resume, MatchResult, and related dataclasses. If you add fields,
  update both `to_dict()` and `from_dict()` methods, and update the JSON schema
  in `matcher.py` (`MATCH_ANALYSIS_SCHEMA`).
- `analyzer.py`: Job analysis LLM integration. The analysis schema is defined
  in `JOB_ANALYSIS_SCHEMA`.
- `matcher.py`: Resume matching LLM integration. The match schema is defined in
  `MATCH_ANALYSIS_SCHEMA`.
- `resume_parser.py`: Resume parsing for JSON and Markdown formats.
- `report.py`: Markdown report rendering.

## Changing the tailoring module

The tailoring module lives at `src/email_opportunity_pipeline/tailoring/`:

- `adapter.py`: Converts between pipeline `Resume` and resume-builder JSON
  schema. Update this if either model changes.
- `engine.py`: Contains the tailoring actions. To add a new action:
  1. Add a `_apply_<action>()` method.
  2. Record `TailoringChange` objects for every modification.
  3. Call the method from `tailor()`.
- `models.py`: `TailoredResume`, `TailoringReport`, `TailoringChange`,
  `ChangeCategory`. Add new categories to the `ChangeCategory` enum if needed.
- `report.py`: Markdown report rendering for tailoring results.

## Working with the vendor subtree

The `vendor/resume-builder/` directory is a **git subtree** of the
[python-resume-builder](https://github.com/sdmunozsierra/python-resume-builder)
repository.

### Making changes to vendor code

If you need to modify `vendor/resume-builder/`:

1. Make changes directly in `vendor/resume-builder/`.
2. Commit as part of this repository.
3. Optionally push changes back to the upstream repo using `git subtree push`.

### Pulling updates from upstream

```bash
git fetch resume-builder
git subtree pull --prefix=vendor/resume-builder resume-builder main --squash
uv sync   # or: pip install -e vendor/resume-builder
```

### Adding the remote (first time)

```bash
git remote add resume-builder https://github.com/sdmunozsierra/python-resume-builder.git
```

## Changing filters or extraction

- Filters live under `src/email_opportunity_pipeline/filters/`.
- Rule-based extraction lives under `src/email_opportunity_pipeline/extraction/`.
- If you change output structure, keep schemas and docs aligned:
  - Schemas: `src/email_opportunity_pipeline/schemas/`
  - Docs: `README.md`, `docs/configuration.md`

## Documentation changes

Docs live in:

- `README.md` -- project overview and quick start
- `docs/architecture.md` -- pipeline stages, interfaces, data flow
- `docs/cli.md` -- CLI command reference
- `docs/configuration.md` -- environment variables, file formats, rules
- `docs/troubleshooting.md` -- common issues and fixes
- `CONTRIBUTING.md` -- this file

Keep examples executable and match CLI flags exactly (see `cli.py`).

## Checklist before submitting

- [ ] Code follows existing style (type hints, docstrings on public APIs)
- [ ] New features have corresponding CLI flags if user-facing
- [ ] New CLI flags are documented in `docs/cli.md`
- [ ] New environment variables are documented in `docs/configuration.md`
- [ ] New interfaces/models have `to_dict()` / `from_dict()` for serialization
- [ ] `__init__.py` exports are updated for new public APIs
- [ ] README is updated if the change is user-visible
