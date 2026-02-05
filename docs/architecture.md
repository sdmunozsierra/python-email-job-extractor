## Architecture overview

At a high level, the pipeline is:

1. **Fetch**: provider pulls recent messages into a normalized `EmailMessage` model
2. **Filter**: a filter pipeline decides which messages look like job opportunities
3. **Extract**: messages are normalized into a job opportunity object (rule-based or LLM)
4. **Render**: opportunities are rendered to Markdown with YAML frontmatter
5. **(Optional) Analyze/Match**: LLM-based job analysis + resume matching + ranking
6. **(Optional) Tailor**: generate tailored resumes using match insights + resume-builder subtree

### Key modules

- `src/email_opportunity_pipeline/providers/`: email providers (currently Gmail)
- `src/email_opportunity_pipeline/filters/`: rule-based filter pipeline + optional LLM filter
- `src/email_opportunity_pipeline/extraction/`: rule-based extractor + optional LLM extractor + Markdown rendering
- `src/email_opportunity_pipeline/matching/`: optional job analysis + resume matching + report rendering
- `src/email_opportunity_pipeline/tailoring/`: resume tailoring engine, adapter, and change reporting
- `src/email_opportunity_pipeline/schemas/`: JSON schemas shipped with the package
- `src/email_opportunity_pipeline/pipeline.py`: orchestration functions used by the CLI
- `src/email_opportunity_pipeline/cli.py`: `email-pipeline` command definitions
- `resume_builder/`: **git subtree** -- the `resume-builder` package for .docx generation

### Resume builder subtree

The `resume_builder/` directory is a git subtree of the
[python-resume-builder](https://github.com/sdmunozsierra/python-resume-builder)
repository. It provides:

- `ResumeSchemaAdapter` -- converts a JSON resume dict into internal models
- `build_resume(person)` -- generates a `.docx` Word document from a `Person` object
- Model classes: `Person`, `Skill`, `Experience`, `Education`, `Cert`, `Project`

The parent project declares it as an editable path dependency in `pyproject.toml`
via `[tool.uv.sources]`, so `uv sync` installs it alongside the main package.

To update the subtree from upstream:

```bash
git fetch resume-builder
git subtree pull --prefix=resume_builder resume-builder main --squash
uv sync
```

### Extension points

#### Add a provider

Implement the `EmailProvider` interface in `providers/base.py`, then register it
in `cli.py`'s `_build_provider`. Providers should return `EmailMessage` objects.

#### Add/modify filters

Filters implement `EmailFilter` and return a `FilterDecision`. The default
filtering behavior is a `KeywordFilter` configured via `FilterRules` with an
optional `LLMFilter` appended.

#### Add/modify extraction

Extraction is done by either:

- `RuleBasedExtractor` (deterministic; regex/heuristics)
- `LLMExtractor` (schema-driven output via OpenAI)

The orchestration function `extract_opportunities(...)` in `pipeline.py` selects
between them based on CLI flags.

#### Tailoring

The tailoring module (`src/email_opportunity_pipeline/tailoring/`) bridges the
matching pipeline with the resume-builder subtree:

- `ResumeAdapter` -- converts between pipeline `Resume` and builder JSON schema
- `TailoringEngine` -- applies match insights (skills, experience, certifications)
  and produces a `TailoredResume` with a full change report
- `TailoringReport` -- documents every modification by category (experience,
  skills, certifications, summary, keywords) with before/after diffs

### Data flow & file formats

Artifacts are JSON wrappers written by `io.py`:

- messages wrapper: `messages: [EmailMessage.to_dict()]`
- opportunities wrapper: `opportunities: [job dict]`
- match results: `match_results: [MatchResult.to_dict()]`
- job analyses: `analyses: [analysis dict]`
- tailoring results: `tailoring_results: [TailoredResume.to_dict()]`

This makes artifacts easy to version, archive, and re-run different stages
without refetching.
