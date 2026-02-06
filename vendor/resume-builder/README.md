[![wakatime](https://wakatime.com/badge/user/65634d68-cd01-4d76-891a-9adfdaff6109/project/f672acb2-2b26-4db0-98b9-79178cf1f654.svg)](https://wakatime.com/badge/user/65634d68-cd01-4d76-891a-9adfdaff6109/project/f672acb2-2b26-4db0-98b9-79178cf1f654)

---

# resume-builder

A Python package that generates `.docx` Word documents from structured
resume data.  Managed with [**uv**](https://docs.astral.sh/uv/) and
distributed as an installable package with a `resume-builder` console
script.

Supports two input modes:

1. **JSON resume schema** -- feed a single JSON file that follows the
   standardised schema and get a formatted resume out.
2. **Legacy Python data** -- the original builder pattern using in-code
   Python objects (still fully supported).

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Console Script](#console-script)
  - [Module Invocation](#module-invocation)
  - [Programmatic Usage](#programmatic-usage)
- [JSON Resume Schema](#json-resume-schema)
- [Using as a Git Subtree](#using-as-a-git-subtree)
  - [Why a Subtree?](#why-a-subtree)
  - [Adding the Subtree](#adding-the-subtree)
  - [Typical Parent Repository Layout](#typical-parent-repository-layout)
  - [Generating a Resume from the Parent Repo](#generating-a-resume-from-the-parent-repo)
  - [Pulling Upstream Updates](#pulling-upstream-updates)
  - [Pushing Changes Back Upstream](#pushing-changes-back-upstream)
- [Development](#development)
- [Models Reference](#models-reference)
- [License](#license)

---

## Features

- Installable via `uv sync` with a real `[project.scripts]` entry point.
- Parses a standardised **JSON resume schema** (personal info, skills,
  experience, education, projects, certifications, preferences).
- Every recognised field is mapped to a **first-class attribute** on the
  internal models -- no silent data loss.
- Unknown / extra fields are captured in an `extra` dict catch-all so the
  builder is forward-compatible with schema extensions.
- Structured **technical skills** with `name`, `level`, `years`, and
  `category`.
- Separate **soft skills**, **spoken languages**, and **preferences**
  sections.
- Full backward compatibility with the original Python builder-pattern data.
- Generates clean `.docx` files with headings, tables, and bullet points.

---

## Project Structure

```
resume-builder/
├── pyproject.toml                         # PEP 621 metadata, deps, entry point
├── sample_resume.json                     # Example resume in JSON schema format
├── certs.txt                              # Legacy flat-file certifications
├── LICENSE
├── README.md
└── src/
    └── resume_builder/                    # <-- the installable package
        ├── __init__.py                    # Package version & docstring
        ├── __main__.py                    # python -m resume_builder support
        ├── cli.py                         # CLI entry point (resume-builder command)
        ├── schema_adapter.py              # JSON schema -> internal models
        ├── skill.py                       # Skill model (name, level, years, category)
        ├── person_builder.py              # Person / PersonBuilder
        ├── experiece_builder.py           # Experience / ExperienceBuilder
        ├── education_builder.py           # Education / EducationBuilder
        ├── cert_builder.py                # Cert / CertBuilder / CertFactory
        ├── project_builder.py             # Project / ProjectBuilder
        ├── format_experience.py           # Word-doc experience formatting
        ├── format_education.py            # Word-doc education formatting
        ├── convert_to_list.py             # Utility: free-text -> list
        ├── personal_info/                 # Legacy Python-coded resume data
        │   ├── __init__.py
        │   └── sergio_david_munoz_sierra.py
        └── formatting/
            ├── __init__.py
            ├── timeline.py
            ├── timeline_2.py
            └── timeline_3.py
```

### Key packaging details

| Concept | Where |
|---|---|
| Build backend | `setuptools>=61` (in `[build-system]`) |
| Package root | `src/resume_builder/` via `[tool.setuptools] package-dir = {"" = "src"}` |
| Console script | `resume-builder` -> `resume_builder.cli:main` (in `[project.scripts]`) |
| `python -m` support | `src/resume_builder/__main__.py` |

Because a `[build-system]` is declared, `uv sync` automatically installs
the project into the venv and generates the console script.

---

## Prerequisites

- **Python >= 3.11**
- [**uv**](https://docs.astral.sh/uv/) (recommended) -- or any PEP 517
  compatible tool (`pip`, `build`, etc.)

Install uv if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/sdmunozsierra/python-resume-builder.git
cd python-resume-builder

# Install the project + deps into a managed venv
uv sync

# Generate a resume from the sample JSON
uv run resume-builder --json sample_resume.json --output my_resume.docx
```

---

## Usage

### Console Script

After `uv sync`, the `resume-builder` command is available:

```bash
# From JSON schema
uv run resume-builder --json path/to/resume.json --output tailored.docx

# Legacy Python data (uses built-in sample data)
uv run resume-builder --output legacy.docx
```

### Module Invocation

```bash
uv run python -m resume_builder --json resume.json --output out.docx
```

### Programmatic Usage

Import the adapter directly from another Python project:

```python
from resume_builder.schema_adapter import ResumeSchemaAdapter
from resume_builder.cli import build_resume

# From a JSON file
person = ResumeSchemaAdapter.from_json_file("resume.json")

# -- or from a dict (e.g. loaded from an API, database, etc.)
import json
with open("resume.json") as f:
    data = json.load(f)
person = ResumeSchemaAdapter.from_dict(data)

# Access all fields
print(person.name)                # "Sergio Munoz"
print(person.skills[0])           # "Python (expert) 9y"
print(person.skills[0].category)  # "languages"
print(person.soft_skills)         # ["Technical Leadership", ...]
print(person.preferences)         # {"desired_roles": [...], ...}
print(person.extra)               # {} -- catch-all for unknown keys

# Build the .docx
doc = build_resume(person)
doc.save("output.docx")
```

---

## JSON Resume Schema

The builder accepts a JSON file with the following top-level sections:

| Section | Description |
|---|---|
| `personal` | Name, email, phone, location, linkedin, github, portfolio, summary |
| `skills` | `technical` (structured), `soft` (list), `languages` (list), `certifications` (list) |
| `experience` | Array of roles with achievements, technologies, dates, and a current flag |
| `education` | Array of degrees with institution, field, honors, coursework |
| `projects` | Top-level projects with technologies, highlights, and optional URL |
| `preferences` | Desired roles, industries, locations, remote preference, salary, engagement types |

See [`sample_resume.json`](sample_resume.json) for a complete working
example.

<details>
<summary>Minimal JSON example</summary>

```json
{
  "personal": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "summary": "Software engineer with 5 years of experience."
  },
  "skills": {
    "technical": [
      { "name": "Python", "level": "expert", "years": 5, "category": "languages" }
    ],
    "soft": ["Leadership", "Communication"]
  },
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Acme Corp",
      "location": "Remote",
      "start_date": "2020-01",
      "end_date": null,
      "current": true,
      "description": "Built backend services.",
      "achievements": ["Reduced API latency by 40%"],
      "technologies": ["Python", "FastAPI", "PostgreSQL"]
    }
  ],
  "education": [
    {
      "degree": "Bachelor of Science",
      "field": "Computer Science",
      "institution": "State University",
      "end_date": "2019-05"
    }
  ]
}
```

</details>

---

## Using as a Git Subtree

The most common use case for this repository is to embed it inside a
**parent repository** that holds your personal resume JSON data and any
job-tailoring scripts.  A **git subtree** is ideal for this because it:

- Keeps the resume builder code directly in your tree (no submodule
  headaches).
- Lets you pull upstream improvements with a single command.
- Optionally lets you push local fixes back upstream.

### Why a Subtree?

| Approach | Pros | Cons |
|---|---|---|
| **Subtree** | Single clone, no extra init steps, works in CI | Slightly larger repo history |
| Submodule | Smaller clone | Requires `git submodule init/update`, breaks CI if forgotten |
| pip install | Clean separation | Must publish a package or use git+https, harder to customise |

For a repo whose purpose is to consume this builder, generate tailored
resumes, and stay up to date -- **subtree wins**.

### Adding the Subtree

From the root of your parent repository, run:

```bash
# 1. Add python-resume-builder as a remote (one-time)
git remote add resume-builder https://github.com/sdmunozsierra/python-resume-builder.git

# 2. Fetch its branches
git fetch resume-builder

# 3. Add it as a subtree under a directory (e.g. resume_builder/)
git subtree add --prefix=resume_builder resume-builder main --squash
```

The `--squash` flag collapses the builder's history into a single merge
commit, keeping your parent repo's log clean.

### Typical Parent Repository Layout

After adding the subtree your parent repo might look like this:

```
my-resume-project/
├── data/
│   └── resume.json               # Your personal resume JSON
├── scripts/
│   └── tailor.py                  # Tweaks JSON per job posting
├── output/                        # Generated .docx files (gitignored)
├── resume_builder/                # <-- the subtree (this repo)
│   ├── pyproject.toml
│   ├── sample_resume.json
│   └── src/
│       └── resume_builder/        # The installable package
│           ├── cli.py
│           ├── schema_adapter.py
│           └── ...
├── pyproject.toml                 # Parent project config (see below)
├── Makefile
└── README.md
```

#### Parent `pyproject.toml`

The parent repo can declare `resume-builder` as an **editable path
dependency** so that `uv sync` in the parent also installs the subtree's
package:

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "my-resume-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "resume-builder",
]

[tool.uv.sources]
resume-builder = { path = "resume_builder", editable = true }
```

After `uv sync` in the parent, `resume-builder` is installed and importable.

### Generating a Resume from the Parent Repo

#### Option A -- Call the console script directly

```bash
# After uv sync in the parent repo
uv run resume-builder --json data/resume.json --output output/resume.docx
```

#### Option B -- Import programmatically in a tailoring script

```python
# scripts/tailor.py
import json
from resume_builder.schema_adapter import ResumeSchemaAdapter
from resume_builder.cli import build_resume

# Load and optionally modify the resume data
with open("data/resume.json") as f:
    data = json.load(f)

# Example: swap summary for a specific role
# data["personal"]["summary"] = "Tailored summary for this role..."

person = ResumeSchemaAdapter.from_dict(data)
doc = build_resume(person)
doc.save("output/tailored_resume.docx")
print("Tailored resume saved.")
```

```bash
uv run python scripts/tailor.py
```

#### Option C -- Makefile shortcut

```makefile
.PHONY: resume tailored clean

resume:
	@mkdir -p output
	uv run resume-builder --json data/resume.json --output output/resume.docx

tailored:
	@mkdir -p output
	uv run python scripts/tailor.py

clean:
	rm -rf output/*.docx
```

```bash
make resume      # Standard resume
make tailored    # Job-specific tailored version
```

### Pulling Upstream Updates

When the resume builder receives new features or fixes:

```bash
git fetch resume-builder
git subtree pull --prefix=resume_builder resume-builder main --squash
```

Then re-sync the venv:

```bash
uv sync
```

### Pushing Changes Back Upstream

If you fix a bug or add a feature inside `resume_builder/` and want to
contribute it back:

```bash
git subtree push --prefix=resume_builder resume-builder main
```

---

## Development

```bash
# Clone & setup
git clone https://github.com/sdmunozsierra/python-resume-builder.git
cd python-resume-builder
uv sync

# Run the CLI
uv run resume-builder --json sample_resume.json

# Run as module
uv run python -m resume_builder --json sample_resume.json

# Quick import test
uv run python -c "from resume_builder import __version__; print(__version__)"
```

### Without uv

If you prefer not to use uv, a standard pip workflow still works:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
resume-builder --json sample_resume.json
```

---

## Models Reference

| Model | Key Attributes |
|---|---|
| `Person` | `name`, `email`, `phone`, `location`, `linkedin`, `github`, `portfolio`, `summary`, `experience`, `education`, `skills`, `soft_skills`, `languages`, `certifications`, `projects`, `activities`, `awards`, `preferences`, `extra` |
| `Skill` | `name`, `level`, `years`, `category` |
| `Experience` | `role`, `company_name`, `location`, `start_date`, `end_date`, `current`, `dates`, `description`, `achievements`, `technologies`, `projects` |
| `Education` | `degree`, `field`, `major`, `minor`, `school_name`, `location`, `start_date`, `end_date`, `dates`, `gpa`, `honors`, `coursework`, `organizations`, `research`, `awards` |
| `Cert` | `title`, `issuer`, `completion_date`, `expiry`, `credential_id` |
| `Project` | `name`, `description`, `url`, `duration`, `team_size`, `actions`, `highlights`, `skills`, `technologies` |

Every model supports both the **new JSON schema** fields and the **legacy**
fields for full backward compatibility.

---

## License

[MIT](LICENSE) -- Copyright (c) 2023 Sergio Sierra
