# Architecture Overview

## Pipeline stages

At a high level, the pipeline is:

```
  Fetch ──> Filter ──> Extract ──> Render
                                     │
                              Analyze/Match ──> Tailor
```

1. **Fetch**: A provider pulls recent messages into a normalized `EmailMessage` model.
2. **Filter**: A filter pipeline decides which messages look like job opportunities.
3. **Extract**: Messages are normalized into a job opportunity dict (rule-based or LLM).
4. **Render**: Opportunities are rendered to Markdown with YAML frontmatter.
5. **(Optional) Analyze**: LLM extracts structured job requirements.
6. **(Optional) Match**: LLM matches a resume against opportunities, producing scored results.
7. **(Optional) Tailor**: Generate tailored `.docx` resumes using match insights + resume-builder.

## Key modules

| Module | Path | Description |
|--------|------|-------------|
| Providers | `providers/` | Email providers (currently Gmail) |
| Filters | `filters/` | Rule-based filter pipeline + optional LLM filter |
| Extraction | `extraction/` | Rule-based + LLM extractors, Markdown renderer |
| Matching | `matching/` | Job analysis, resume matching, match reports |
| Tailoring | `tailoring/` | Resume tailoring engine, adapter, change reporting |
| Schemas | `schemas/` | JSON schemas shipped with the package |
| Pipeline | `pipeline.py` | Orchestration functions used by the CLI |
| CLI | `cli.py` | `email-pipeline` command definitions |
| I/O | `io.py` | Read/write JSON artifact wrappers |
| Config | `config.py` | Default settings (window, Gmail scopes) |
| Models | `models.py` | Core dataclasses (EmailMessage, FilterOutcome) |
| Time Window | `time_window.py` | Time window parsing (30m, 6h, 2d) |
| Analytics | `analytics.py` | Pipeline analytics and reporting |
| Vendor | `vendor/resume-builder/` | Git subtree -- `.docx` generation |

---

## Interface contracts

### EmailProvider (`providers/base.py`)

```python
class EmailProvider(ABC):
    @abstractmethod
    def fetch_messages(
        self,
        window: TimeWindow,
        max_results: Optional[int] = None,
        query: Optional[str] = None,
        include_body: bool = True,
    ) -> Iterable[EmailMessage]: ...
```

**Contract**: Given a time window, return an iterable of `EmailMessage` objects.
Providers handle authentication, API pagination, and message parsing internally.
The rest of the pipeline never touches provider-specific APIs.

**Current implementations**: `GmailProvider`

### EmailFilter (`filters/base.py`)

```python
class EmailFilter(ABC):
    name: str = "base"

    @abstractmethod
    def evaluate(self, email: EmailMessage) -> FilterDecision: ...
```

**Contract**: Given an `EmailMessage`, return a `FilterDecision` containing:
- `filter_name`: the filter's name
- `passed`: boolean -- does this email look like a job opportunity?
- `reasons`: list of human-readable reasons

Filters are composed into a `FilterPipeline` which aggregates decisions into a
`FilterOutcome`.

**Current implementations**: `KeywordFilter`, `LLMFilter`

### BaseExtractor (`extraction/extractor.py`)

```python
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, email: EmailMessage) -> Dict[str, Any]: ...
```

**Contract**: Given an `EmailMessage`, return a job opportunity dict conforming
to `schemas/job_opportunity.schema.json`. At minimum it must contain
`job_title`, `company`, and `source_email.message_id`.

**Current implementations**: `RuleBasedExtractor`, `LLMExtractor`

### FilterPipeline (`filters/pipeline.py`)

```python
class FilterPipeline:
    def __init__(self, filters: List[EmailFilter], stop_on_reject: bool = True): ...
    def apply(self, email: EmailMessage) -> FilterOutcome: ...
    def run(self, emails: Iterable[EmailMessage]) -> List[Tuple[EmailMessage, FilterOutcome]]: ...
```

Orchestrates multiple filters in sequence. When `stop_on_reject=True` (default),
evaluation short-circuits on the first rejection.

---

## Matching interfaces

### Resume model (`matching/models.py`)

```python
@dataclass
class Resume:
    personal: PersonalInfo
    skills: Skills
    experience: List[Experience]
    education: List[Education]
    projects: List[Project]
    preferences: Optional[JobPreferences]
    source_file: Optional[str]
```

Parsed from JSON or Markdown via `ResumeParser.parse()`.

### JobAnalyzer (`matching/analyzer.py`)

```python
class JobAnalyzer:
    def analyze(self, job: Dict[str, Any]) -> Dict[str, Any]: ...
    def analyze_batch(self, jobs: List[Dict]) -> List[Dict]: ...
```

Extracts structured requirements (skills, experience, education, tech stack,
culture indicators) from a job opportunity dict using the OpenAI API.

### ResumeMatcher (`matching/matcher.py`)

```python
class ResumeMatcher:
    def match(self, resume: Resume, job: Dict, job_analysis: Optional[Dict] = None) -> MatchResult: ...
    def match_batch(self, resume: Resume, jobs: List[Dict], job_analyses: Optional[List[Dict]] = None) -> List[MatchResult]: ...
```

Matches a resume against one or more jobs, producing `MatchResult` objects with:
- Category scores (skills 35%, experience 30%, education 15%, location 10%, culture 10%)
- Detailed skill match analysis (mandatory/preferred met/missing)
- Insights (strengths, concerns, opportunities, talking points)
- Resume tailoring suggestions
- Application strategy recommendations

---

## Tailoring interfaces

### ResumeAdapter (`tailoring/adapter.py`)

```python
class ResumeAdapter:
    @classmethod
    def to_builder_schema(cls, resume: Resume) -> Dict[str, Any]: ...
    @classmethod
    def from_builder_schema(cls, data: Dict, source_file: Optional[str] = None) -> Resume: ...
```

Bi-directional adapter between the pipeline's `Resume` model and the
resume-builder JSON schema format. This is the bridge between the matching
module and the vendor package.

### TailoringEngine (`tailoring/engine.py`)

```python
class TailoringEngine:
    def tailor(self, resume: Resume, match_result: MatchResult, job: Optional[Dict] = None, build_docx: bool = True) -> TailoredResume: ...
    def tailor_batch(self, resume: Resume, match_results: List[MatchResult], jobs: Optional[List[Dict]] = None, build_docx: bool = True) -> List[TailoredResume]: ...
```

The engine works in three phases:

1. **Convert** -- pipeline `Resume` -> builder schema dict (deep copy)
2. **Mutate** -- apply tailoring actions (summary, skills reorder, experience
   reorder, certification reorder, keyword tracking), recording a
   `TailoringChange` for every modification
3. **Build** (optional) -- hand the tailored dict to `resume-builder` to
   produce a `.docx` file

### TailoringReport (`tailoring/models.py`)

Every change is tracked in a `TailoringReport`:

| Category | What it tracks |
|----------|---------------|
| `summary` | Summary rewrites |
| `skills` | Skill reordering and highlighting |
| `experience` | Experience reordering and achievement surfacing |
| `certifications` | Certification reordering |
| `keywords` | ATS keyword identification |
| `education` | (reserved for future use) |
| `projects` | (reserved for future use) |

---

## Vendor: resume-builder subtree

The `vendor/resume-builder/` directory is a git subtree of the
[python-resume-builder](https://github.com/sdmunozsierra/python-resume-builder)
repository. It provides:

- `ResumeSchemaAdapter` -- converts a JSON resume dict into internal `Person` models
- `build_resume(person)` -- generates a `.docx` Word document from a `Person` object
- Model classes: `Person`, `Skill`, `Experience`, `Education`, `Cert`, `Project`
- CLI: `resume-builder --json resume.json --output my_resume.docx`

### How the pipeline uses resume-builder

```
Pipeline Resume ──[ResumeAdapter]──> Builder Schema Dict
                                         │
                          ┌────────────────┘
                          ▼
               ResumeSchemaAdapter.from_dict()
                          │
                          ▼
                    Person object
                          │
                          ▼
                   build_resume(person)
                          │
                          ▼
                    .docx Document
```

The `TailoringEngine` mutates the builder schema dict (step 2 above) before
passing it to `ResumeSchemaAdapter`, so the final `.docx` reflects all
tailoring changes.

### Dependency declaration

The parent project declares resume-builder as a dependency:

```toml
# pyproject.toml
[project]
dependencies = [
  ...
  "resume-builder",
]

[tool.uv.sources]
resume-builder = { path = "vendor/resume-builder", editable = true }
```

- **uv**: `uv sync` resolves this automatically via `[tool.uv.sources]`.
- **pip**: Install the vendor package first: `pip install -e vendor/resume-builder`

### Updating the subtree

```bash
git fetch resume-builder
git subtree pull --prefix=vendor/resume-builder resume-builder main --squash
uv sync   # or: pip install -e vendor/resume-builder
```

---

## Data flow and file formats

Artifacts are JSON wrappers written by `io.py`:

| Artifact | Wrapper key | Writer | Reader |
|----------|-------------|--------|--------|
| Messages | `messages: [EmailMessage.to_dict()]` | `write_messages()` | `read_messages()` |
| Opportunities | `opportunities: [job dict]` | `write_opportunities()` | `read_opportunities()` |
| Match results | `match_results: [MatchResult.to_dict()]` | `write_match_results()` | `read_match_results()` |
| Job analyses | `analyses: [analysis dict]` | `write_job_analyses()` | `read_job_analyses()` |
| Tailoring results | `tailoring_results: [TailoredResume.to_dict()]` | `write_tailoring_results()` | -- |
| Tailoring report | Direct dict | `write_tailoring_report()` | -- |

All wrappers include a `created_at_utc` (or `fetched_at_utc`) timestamp and a
`count` field. This makes artifacts easy to version, archive, and re-run
different stages without refetching.

### Typical data flow

```
email-pipeline fetch  --> data/messages.json
email-pipeline filter --> data/filtered.json
email-pipeline extract --> data/opportunities.json
email-pipeline render --> out/*.md
email-pipeline analyze --> data/job_analyses.json
email-pipeline match  --> out/matches/match_results.json
                          out/matches/match_summary.md
                          out/matches/match_reports/*.md
email-pipeline rank   --> (stdout or filtered JSON)
email-pipeline tailor --> output/tailored/
                           tailoring_results.json
                           tailoring_summary.md
                           tailoring_reports/<job_id>_report.md
                           tailoring_reports/<job_id>_resume.json
                           tailored_resume_<company>_<title>.docx
```

---

## Extension points

### Add a provider

1. Implement the `EmailProvider` interface in `providers/`.
2. Return `EmailMessage` objects.
3. Register the provider in `cli.py` (`_build_provider`) and add it to the
   argparse `choices`.
4. Update docs: `README.md`, `docs/architecture.md`, `docs/configuration.md`.

### Add/modify filters

Filters implement `EmailFilter` and return a `FilterDecision`. The default
filtering behavior is a `KeywordFilter` configured via `FilterRules` with an
optional `LLMFilter` appended. To add a new filter:

1. Subclass `EmailFilter` in `filters/`.
2. Set a unique `name` attribute.
3. Implement `evaluate()`.
4. Add the filter to `build_filter_pipeline()` in `pipeline.py`.

### Add/modify extraction

Extraction is done by either:

- `RuleBasedExtractor` (deterministic; regex/heuristics)
- `LLMExtractor` (schema-driven output via OpenAI)

The orchestration function `extract_opportunities(...)` in `pipeline.py` selects
between them based on CLI flags. To add a new extractor, subclass `BaseExtractor`.

### Modify tailoring actions

The `TailoringEngine` has five action methods:

- `_apply_summary_suggestions()`
- `_apply_skills_highlighting()`
- `_apply_experience_emphasis()`
- `_apply_certification_highlighting()`
- `_apply_keyword_additions()`

To add a new tailoring action (e.g. education or projects), add a new method
and call it from `tailor()`. Make sure to record `TailoringChange` objects.

### Add a new resume format

The `ResumeParser` in `matching/resume_parser.py` currently supports JSON and
Markdown. To add a new format (e.g. YAML, PDF):

1. Add a `_parse_<format>()` method to `ResumeParser`.
2. Register the file extension in `parse()`.
3. Return a `Resume` object.
