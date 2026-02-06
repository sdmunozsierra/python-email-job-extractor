"""Email filtering module.

Provides a composable filter pipeline:

- :class:`EmailFilter` -- abstract interface for individual filters
- :class:`KeywordFilter` -- rule-based keyword/domain matching
- :class:`LLMFilter` -- optional LLM-based relevance check
- :class:`FilterPipeline` -- orchestrates multiple filters, aggregating
  :class:`~email_opportunity_pipeline.models.FilterDecision` objects into
  a :class:`~email_opportunity_pipeline.models.FilterOutcome`
- :class:`FilterRules` / :func:`load_rules` -- load/merge user-defined
  filter rule files
"""

from .base import EmailFilter
from .keyword import KeywordFilter
from .llm import LLMFilter
from .pipeline import FilterPipeline
from .rules import FilterRules, load_rules

__all__ = [
    "EmailFilter",
    "KeywordFilter",
    "LLMFilter",
    "FilterPipeline",
    "FilterRules",
    "load_rules",
]
