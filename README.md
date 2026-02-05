[![wakatime](https://wakatime.com/badge/user/65634d68-cd01-4d76-891a-9adfdaff6109/project/f672acb2-2b26-4db0-98b9-79178cf1f654.svg)](https://wakatime.com/badge/user/65634d68-cd01-4d76-891a-9adfdaff6109/project/f672acb2-2b26-4db0-98b9-79178cf1f654)

---

# python-resume-builder

A Python-based resume builder that generates `.docx` Word documents from
structured resume data. Supports two input modes:

1. **JSON resume schema** -- feed a single JSON file that follows the
   standardised schema and get a formatted resume out.
2. **Legacy Python data** -- the original builder pattern using in-code
   Python objects (still fully supported).

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [JSON Resume Schema](#json-resume-schema)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Generate from JSON](#generate-from-json)
  - [Generate from Legacy Python Data](#generate-from-legacy-python-data)
  - [Programmatic Usage](#programmatic-usage)
- [Using as a Git Subtree](#using-as-a-git-subtree)
  - [Why a Subtree?](#why-a-subtree)
  - [Adding the Subtree](#adding-the-subtree)
  - [Typical Parent Repository Layout](#typical-parent-repository-layout)
  - [Generating a Resume from the Parent Repo](#generating-a-resume-from-the-parent-repo)
  - [Pulling Upstream Updates](#pulling-upstream-updates)
  - [Pushing Changes Back Upstream](#pushing-changes-back-upstream)
- [Models Reference](#models-reference)
- [License](#license)

---

## Features

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
python-resume-builder/
├── main.py                        # CLI entry point (--json / --output)
├── sample_resume.json             # Example resume in JSON schema format
├── certs.txt                      # Legacy flat-file certifications
├── requirements.txt               # Python dependencies
├── personal_info/
│   └── sergio_david_munoz_sierra.py   # Legacy Python-coded resume data
└── src/
    ├── schema_adapter.py          # JSON schema -> internal models adapter
    ├── skill.py                   # Skill model (name, level, years, category)
    ├── person_builder.py          # Person / PersonBuilder
    ├── experiece_builder.py       # Experience / ExperienceBuilder / ExperienceFactory
    ├── education_builder.py       # Education / EducationBuilder / EducationFactory
    ├── cert_builder.py            # Cert / CertBuilder / CertFactory
    ├── project_builder.py         # Project / ProjectBuilder / ProjectFactory
    ├── format_experience.py       # Word-doc formatting helpers for experience
    ├── format_education.py        # Word-doc formatting helpers for education
    ├── convert_to_list.py         # Utility: free-text skill block -> list
    └── formatting/
        ├── timeline.py            # Alternating timeline layout
        ├── timeline_2.py          # Timeline variant 2
        └── timeline_3.py          # Timeline variant 3
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

See [`sample_resume.json`](sample_resume.json) for a complete working example.

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

## Quick Start

```bash
# Clone the repository
git clone https://github.com/sdmunozsierra/python-resume-builder.git
cd python-resume-builder

# Install dependencies
pip install -r requirements.txt

# Generate a resume from the sample JSON
python main.py --json sample_resume.json --output my_resume.docx
```

---

## Usage

### Generate from JSON

```bash
python main.py --json path/to/resume.json --output tailored_resume.docx
```

### Generate from Legacy Python Data

```bash
# Uses the hard-coded data in personal_info/
python main.py --output legacy_resume.docx
```

### Programmatic Usage

You can import the adapter directly from another Python project:

```python
from src.schema_adapter import ResumeSchemaAdapter

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
```

---

## Using as a Git Subtree

The most common use case for this repository is to embed it inside a
**parent repository** that holds your personal resume JSON data and any
job-tailoring scripts. A **git subtree** is ideal for this because it:

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

After adding the subtree, your parent repo might look like this:

```
my-resume-project/
├── data/
│   └── resume.json           # Your personal resume JSON (the schema above)
├── scripts/
│   └── tailor.py             # Optional: script that tweaks JSON per job posting
├── output/                   # Generated .docx files (gitignored)
├── resume_builder/           # <-- the subtree (this repo)
│   ├── main.py
│   ├── sample_resume.json
│   ├── src/
│   │   ├── schema_adapter.py
│   │   └── ...
│   └── ...
├── Makefile                  # Convenience targets
├── requirements.txt          # Includes resume_builder/requirements.txt deps
└── README.md
```

### Generating a Resume from the Parent Repo

#### Option A -- Call the builder's CLI directly

```bash
# From the root of the parent repo
python resume_builder/main.py --json data/resume.json --output output/resume.docx
```

#### Option B -- Import programmatically in a tailoring script

```python
# scripts/tailor.py
import json
import sys
import os

# Ensure the subtree root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resume_builder"))

from src.schema_adapter import ResumeSchemaAdapter
from main import build_resume

# Load and optionally modify the resume data
with open("data/resume.json") as f:
    data = json.load(f)

# Example: filter experience to the last 5 years, swap summary, etc.
# data["personal"]["summary"] = "Tailored summary for this role..."

person = ResumeSchemaAdapter.from_dict(data)
doc = build_resume(person)
doc.save("output/tailored_resume.docx")
print("Tailored resume saved.")
```

#### Option C -- Makefile shortcut

```makefile
# Makefile (in the parent repo root)
.PHONY: resume tailored clean

BUILDER = resume_builder/main.py
DATA    = data/resume.json
OUTPUT  = output

resume:
	@mkdir -p $(OUTPUT)
	python $(BUILDER) --json $(DATA) --output $(OUTPUT)/resume.docx

tailored:
	@mkdir -p $(OUTPUT)
	python scripts/tailor.py

clean:
	rm -rf $(OUTPUT)/*.docx
```

Then simply:

```bash
make resume      # Standard resume
make tailored    # Job-specific tailored version
```

### Pulling Upstream Updates

When the resume builder receives new features or fixes:

```bash
# Fetch the latest from the builder remote
git fetch resume-builder

# Merge updates into the subtree directory
git subtree pull --prefix=resume_builder resume-builder main --squash
```

This will squash-merge any new commits into your parent repo. Resolve
conflicts (if any) and commit as usual.

### Pushing Changes Back Upstream

If you fix a bug or add a feature inside `resume_builder/` and want to
contribute it back:

```bash
git subtree push --prefix=resume_builder resume-builder main
```

This extracts commits that touched `resume_builder/` and pushes them to
the upstream repository.

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
