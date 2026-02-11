# Email Opportunity Pipeline -- Justfile
# See https://github.com/casey/just for installation

# Default recipe: list available commands
default:
    @just --list

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

# Install the project and all extras (uv)
install:
    uv venv
    uv sync --all-extras

# Install using pip instead of uv
install-pip:
    python -m venv .venv
    . .venv/bin/activate && pip install -e vendor/resume-builder
    . .venv/bin/activate && pip install -e ".[llm,ui]"

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

# Run the test suite
test *ARGS:
    python -m pytest tests/ {{ARGS}}

# Run tests with verbose output
test-v:
    python -m pytest tests/ -v

# Type-check with mypy (if installed)
typecheck:
    python -m mypy src/email_opportunity_pipeline/ --ignore-missing-imports

# Lint with ruff (if installed)
lint:
    python -m ruff check src/ tests/

# Format with ruff (if installed)
fmt:
    python -m ruff format src/ tests/

# ---------------------------------------------------------------------------
# Pipeline commands
# ---------------------------------------------------------------------------

# Run the full e2e pipeline (dry-run by default)
run-all *ARGS:
    email-pipeline run-all {{ARGS}}

# Fetch emails from Gmail
fetch *ARGS:
    email-pipeline fetch {{ARGS}}

# Filter messages
filter *ARGS:
    email-pipeline filter {{ARGS}}

# Extract opportunities
extract *ARGS:
    email-pipeline extract {{ARGS}}

# Analyze jobs with LLM
analyze *ARGS:
    email-pipeline analyze {{ARGS}}

# Match resume against jobs
match *ARGS:
    email-pipeline match {{ARGS}}

# Rank match results
rank *ARGS:
    email-pipeline rank {{ARGS}}

# Tailor resumes
tailor *ARGS:
    email-pipeline tailor {{ARGS}}

# Compose reply emails
compose *ARGS:
    email-pipeline compose {{ARGS}}

# Send (or dry-run) reply emails
reply *ARGS:
    email-pipeline reply {{ARGS}}

# Correlate all pipeline artifacts
correlate *ARGS:
    email-pipeline correlate {{ARGS}}

# Initialise application tracking
track *ARGS:
    email-pipeline track {{ARGS}}

# Update a tracked application
track-update *ARGS:
    email-pipeline track-update {{ARGS}}

# Generate analytics
analytics *ARGS:
    email-pipeline analytics {{ARGS}}

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

# Launch the Streamlit web dashboard
ui *ARGS:
    email-pipeline ui {{ARGS}}

# Launch Streamlit directly (alternative)
ui-direct port="8501":
    streamlit run src/email_opportunity_pipeline/ui/app.py --server.port={{port}}

# ---------------------------------------------------------------------------
# Quickstart examples
# ---------------------------------------------------------------------------

# Dry-run the full pipeline with sample resume
quickstart-dry:
    email-pipeline run-all \
        --resume examples/sample_resume.json \
        --questionnaire examples/questionnaire.json \
        --provider gmail --window 2d \
        --work-dir data --out-dir output

# Send emails for real (use with caution)
quickstart-send:
    email-pipeline run-all \
        --resume examples/sample_resume.json \
        --questionnaire examples/questionnaire.json \
        --provider gmail --window 2d \
        --work-dir data --out-dir output --send

# Correlate all artifacts after a pipeline run
quickstart-correlate:
    email-pipeline correlate \
        --work-dir data --out-dir output \
        --out output/correlation \
        --full-report --individual-cards

# Initialise tracking after correlation
quickstart-track:
    email-pipeline track \
        --out-dir output \
        --out output/tracking \
        --full-report --individual-cards

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

# Clean generated data and output directories
clean:
    rm -rf data/ output/

# Show project structure
tree:
    @find src/email_opportunity_pipeline -type f -name '*.py' | sort
