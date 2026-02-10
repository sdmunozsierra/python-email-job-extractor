# Architecture Overview

## Pipeline stages

At a high level, the pipeline is:

```
  Fetch ──> Filter ──> Extract ──> Render
                                     │
                              Analyze/Match ──> Tailor ──> Compose ──> Reply
                                                                        │
                                                                   Correlate
                                                                        │
                                                                     Track

  [  run-all  ──────────────────────────────────────────────────────────── ]
```

The `run-all` command orchestrates all stages in a single invocation with
dry-run (default) or live send (`--send`) mode.

1. **Fetch**: A provider pulls recent messages into a normalized `EmailMessage` model.
2. **Filter**: A filter pipeline decides which messages look like job opportunities.
3. **Extract**: Messages are normalized into a job opportunity dict (rule-based or LLM).
4. **Render**: Opportunities are rendered to Markdown with YAML frontmatter.
5. **(Optional) Analyze**: LLM extracts structured job requirements.
6. **(Optional) Match**: LLM matches a resume against opportunities, producing scored results.
7. **(Optional) Tailor**: Generate tailored `.docx` resumes using match insights + resume-builder.
8. **(Optional) Compose**: LLM composes personalised recruiter reply emails from match insights + questionnaire.
9. **(Optional) Reply**: Send or dry-run composed emails, with tailored resumes attached.
10. **(Optional) Correlate**: Build a unified view linking all artifacts per opportunity.
11. **(Optional) Track**: Manage the post-reply application lifecycle (status, interviews, offers, outcomes).

## Key modules

| Module | Path | Description |
|--------|------|-------------|
| Providers | `providers/` | Email providers (currently Gmail) |
| Filters | `filters/` | Rule-based filter pipeline + optional LLM filter |
| Extraction | `extraction/` | Rule-based + LLM extractors, Markdown renderer |
| Matching | `matching/` | Job analysis, resume matching, match reports |
| Tailoring | `tailoring/` | Resume tailoring engine, adapter, change reporting |
| Reply | `reply/` | Recruiter reply composer, sender, templates, reports |
| Correlation | `correlation/` | Unified opportunity-email-resume correlation |
| Tracking | `tracking/` | Post-reply application tracking (status, interviews, offers, outcomes) |
| Schemas | `schemas/` | JSON schemas shipped with the package |
| Pipeline | `pipeline.py` | Orchestration functions used by the CLI |
| CLI | `cli.py` | `email-pipeline` command definitions |
| I/O | `io.py` | Read/write JSON artifact wrappers |
| Config | `config.py` | Default settings (window, Gmail scopes) |
| Models | `models.py` | Core dataclasses (EmailMessage, FilterOutcome) |
| Time Window | `time_window.py` | Time window parsing (30m, 6h, 2d) |
| Analytics | `analytics.py` | Pipeline analytics and reporting |
| UI | `ui/` | Streamlit web dashboard for exploring artifacts |
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

## Reply interfaces

### ReplyComposer (`reply/composer.py`)

```python
class ReplyComposer:
    def compose(self, *, resume: Resume, match_result: MatchResult, job: Dict, questionnaire: QuestionnaireConfig, attachment_paths: Optional[List[str]] = None) -> EmailDraft: ...
    def compose_batch(self, *, resume: Resume, match_results: List[MatchResult], jobs: List[Dict], questionnaire: QuestionnaireConfig, attachment_map: Optional[Dict[str, List[str]]] = None) -> List[EmailDraft]: ...
```

Uses an LLM to generate personalised recruiter reply emails.  The composer
builds a system prompt from the `QuestionnaireConfig` (tone, length) and a
user prompt from job context, match insights, and candidate strengths.

When the LLM is unavailable (no `openai` package or API key), it falls back
to a plain-text template (`reply/templates.py`).

### GmailSender (`reply/sender.py`)

```python
class GmailSender:
    def send(self, draft: EmailDraft, *, dry_run: bool = False, from_address: Optional[str] = None) -> ReplyResult: ...
    def send_batch(self, drafts: List[EmailDraft], *, dry_run: bool = False, from_address: Optional[str] = None) -> List[ReplyResult]: ...
```

Sends emails via the Gmail API `users.messages.send` endpoint.  Handles:
- MIME message construction (multipart with text body + attachments)
- Threading headers (`In-Reply-To`, `References`)
- Gmail thread ID for conversation threading
- Dry-run mode (builds MIME but does not transmit)

Requires OAuth credentials with `gmail.send` scope (see `config.py`
`GMAIL_SEND_SCOPES`).

### QuestionnaireConfig (`reply/models.py`)

```python
@dataclass
class QuestionnaireConfig:
    salary_range: Optional[str] = None
    location_preference: Optional[str] = None
    availability: Optional[str] = None
    interview_process_questions: List[str] = field(default_factory=list)
    custom_questions: List[str] = field(default_factory=list)
    tone: ReplyTone = ReplyTone.PROFESSIONAL
    max_length_words: int = 300
    # ... plus salary_notes, relocation_notes, notice_period, visa_status,
    #     include_* flags, extra_instructions
```

Controls what topics to include and how the LLM should compose the email.
Serialisable to/from JSON via `to_dict()` / `from_dict()`.

---

## Correlation interfaces

### OpportunityCorrelator (`correlation/correlator.py`)

```python
class OpportunityCorrelator:
    def add_messages(self, messages: List[EmailMessage]) -> None: ...
    def add_opportunities(self, opportunities: List[Dict]) -> None: ...
    def add_match_results(self, results: List[MatchResult]) -> None: ...
    def add_tailoring_results(self, results: List[Dict], tailored_dir: Optional[Path] = None) -> None: ...
    def add_drafts(self, drafts: List[EmailDraft]) -> None: ...
    def add_reply_results(self, results: List[ReplyResult]) -> None: ...
    def correlate(self) -> List[CorrelatedOpportunity]: ...
    def build_summary(self, correlated: List[CorrelatedOpportunity], resume_name: Optional[str] = None) -> CorrelationSummary: ...
```

Links all pipeline artifacts by their shared `job_id` / `message_id`. The
`correlate()` method returns a list of `CorrelatedOpportunity` objects sorted
by match score (highest first, unmatched last).

### CorrelatedOpportunity (`correlation/models.py`)

```python
@dataclass
class CorrelatedOpportunity:
    job_id: str
    job_title: str
    company: str
    stage: OpportunityStage          # fetched -> ... -> replied
    pipeline_complete: bool
    email: Optional[EmailSummary]    # source email
    match: Optional[MatchSummary]    # match result
    tailoring: Optional[TailoringSummary]  # tailored resume
    reply: Optional[ReplySummary]    # reply status
    # ... plus timeline, contact, locations
```

A unified view of a single job opportunity across the entire pipeline.
Tracks pipeline progress through `OpportunityStage` and provides
lightweight summaries of each linked artifact.

### Report rendering (`correlation/report.py`)

```python
def render_correlation_summary(summary, correlated) -> str: ...
def render_opportunity_card(c: CorrelatedOpportunity) -> str: ...
def render_correlation_report(summary, correlated, include_cards=False) -> str: ...
```

Generates Markdown reports with:
- Executive summary tables
- Match score breakdowns with visual progress bars
- Grade and recommendation distribution
- Pipeline progress tracker with stage icons
- Individual opportunity cards with full details

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
| Email drafts | `drafts: [EmailDraft.to_dict()]` | `write_drafts()` | `read_drafts()` |
| Reply results | `reply_results: [ReplyResult.to_dict()]` | `write_reply_results()` | `read_reply_results()` |
| Questionnaire | Direct dict | `write_questionnaire()` | `read_questionnaire()` |
| Correlation | `correlated_opportunities: [...]` | `write_correlation()` | `read_correlation()` |
| Tracking | `tracked_applications: [...]` | `write_tracking()` | `read_tracking()` |

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
email-pipeline compose --> output/replies/
                             drafts.json
                             drafts_preview.md
                             previews/<job_id>_preview.md
email-pipeline reply  --> output/replies/
                             reply_results.json
                             reply_report.md
email-pipeline correlate --> correlation/
                               correlation.json
                               correlation_summary.md
                               opportunity_cards/<job_id>.md
                               correlation_full_report.md
email-pipeline track    --> output/tracking/
                               tracking.json
                               tracking_summary.md
                               application_cards/<job_id>.md
                               tracking_full_report.md
```

---

## Streamlit Web Dashboard

The `ui/` module provides an interactive web interface for exploring pipeline
artifacts.  It reads the same JSON files produced by the CLI commands.

### Module layout

| File | Description |
|------|-------------|
| `ui/__init__.py` | Package init |
| `ui/app.py` | Main Streamlit application (page routing, layout, widgets) |
| `ui/state.py` | Artifact discovery and JSON loading helpers |

### Artifact discovery

`state.discover_artifacts(work_dir, out_dir)` scans the standard directory
layout produced by `run-all` and returns a dict of artifact name to `Path`.
The dashboard uses this to conditionally show navigation pages only when
their data exists on disk.

### Pages

| Page | Data source | Key widgets |
|------|-------------|-------------|
| Dashboard | messages, filtered, opportunities, matches | Metric cards, top matches |
| Messages | messages.json, filtered.json | Dataframe, JSON detail expander |
| Opportunities | opportunities.json | Dataframe, two-column detail view |
| Match Results | match_results.json | Score histogram, ranked table, detail |
| Tailored Resumes | tailoring_results.json | Change table, before/after diffs |
| Reply Drafts | drafts.json | Table, email preview with body |
| Reply Results | reply_results.json | Status breakdown, send report |
| Correlation | correlation.json | Stage bar chart, unified table |
| Application Tracker | tracking.json | Status distribution, update forms, timeline |
| Analytics | analytics.json | Metrics, domain/date charts, report |

### Launch

The UI can be launched via the CLI (`email-pipeline ui`) or directly with
`streamlit run src/email_opportunity_pipeline/ui/app.py`.

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
