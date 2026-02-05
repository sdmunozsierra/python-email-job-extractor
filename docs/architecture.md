## Architecture overview

At a high level, the pipeline is:

1. **Fetch**: provider pulls recent messages into a normalized `EmailMessage` model
2. **Filter**: a filter pipeline decides which messages look like job opportunities
3. **Extract**: messages are normalized into a job opportunity object (rule-based or LLM)
4. **Render**: opportunities are rendered to Markdown with YAML frontmatter
5. **(Optional) Analyze/Match**: LLM-based job analysis + resume matching + ranking

### Key modules

- `src/email_opportunity_pipeline/providers/`: email providers (currently Gmail)
- `src/email_opportunity_pipeline/filters/`: rule-based filter pipeline + optional LLM filter
- `src/email_opportunity_pipeline/extraction/`: rule-based extractor + optional LLM extractor + Markdown rendering
- `src/email_opportunity_pipeline/matching/`: optional job analysis + resume matching + report rendering
- `src/email_opportunity_pipeline/schemas/`: JSON schemas shipped with the package
- `src/email_opportunity_pipeline/pipeline.py`: orchestration functions used by the CLI
- `src/email_opportunity_pipeline/cli.py`: `email-pipeline` command definitions

### Extension points

#### Add a provider

Implement the `EmailProvider` interface in `providers/base.py`, then register it
in `cli.py`’s `_build_provider`. Providers should return `EmailMessage` objects.

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

### Data flow & file formats

Artifacts are JSON wrappers written by `io.py`:

- messages wrapper: `messages: [EmailMessage.to_dict()]`
- opportunities wrapper: `opportunities: [job dict]`

This makes artifacts easy to version, archive, and re-run different stages
without refetching.

