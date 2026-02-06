"""Extraction module -- turn raw email messages into structured job opportunities.

Provides a ``BaseExtractor`` interface and two implementations:

- :class:`RuleBasedExtractor` -- deterministic regex/heuristic extraction
- :class:`LLMExtractor` -- schema-driven extraction via OpenAI

The :func:`render_markdown` helper converts a job opportunity dict into
Markdown with YAML frontmatter.
"""

from .extractor import BaseExtractor
from .llm_extractor import LLMExtractor
from .markdown import render_markdown
from .rules_extractor import RuleBasedExtractor
from .schema import JOB_SCHEMA, load_job_schema

__all__ = [
    "BaseExtractor",
    "LLMExtractor",
    "RuleBasedExtractor",
    "render_markdown",
    "JOB_SCHEMA",
    "load_job_schema",
]
