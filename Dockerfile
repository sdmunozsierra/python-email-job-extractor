FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

# Copy vendor dependency first (changes less often)
COPY vendor/ vendor/

# Copy project metadata for dependency resolution
COPY pyproject.toml .

# Install the vendor dependency and project with all extras
RUN pip install --no-cache-dir vendor/resume-builder && \
    pip install --no-cache-dir ".[llm,ui]"

# Copy application source
COPY src/ src/

# Re-install in editable mode so the entry point resolves to local source
RUN pip install --no-cache-dir -e .

# Default directories for pipeline artifacts
RUN mkdir -p /app/data /app/output /app/config /app/resumes

EXPOSE 8502

ENTRYPOINT ["email-pipeline"]
CMD ["--help"]
