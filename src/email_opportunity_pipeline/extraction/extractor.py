"""Abstract base class for opportunity extractors.

An extractor takes an :class:`~email_opportunity_pipeline.models.EmailMessage`
and returns a **job opportunity dict** conforming to the JSON schema at
``src/email_opportunity_pipeline/schemas/job_opportunity.schema.json``.

Built-in extractors:

- :class:`~email_opportunity_pipeline.extraction.rules_extractor.RuleBasedExtractor` --
  deterministic regex/heuristic extraction.
- :class:`~email_opportunity_pipeline.extraction.llm_extractor.LLMExtractor` --
  schema-driven extraction via the OpenAI API.

To add a custom extractor, subclass ``BaseExtractor`` and implement
:meth:`extract`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models import EmailMessage


class BaseExtractor(ABC):
    """Interface that every opportunity extractor must implement."""

    @abstractmethod
    def extract(self, email: EmailMessage) -> Dict[str, Any]:
        """Extract a job opportunity from an email message.

        The returned dict should conform to the job opportunity JSON
        schema (see ``schemas/job_opportunity.schema.json``).  At a
        minimum it should contain:

        - ``job_title`` (str)
        - ``company`` (str)
        - ``source_email.message_id`` (str)

        Args:
            email: The email message to extract from.

        Returns:
            A dictionary representing the job opportunity.  Keys vary
            by extractor but follow the project's JSON schema.

        Raises:
            ValueError: If the email cannot be parsed into a valid
                opportunity.
        """
        raise NotImplementedError
