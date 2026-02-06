"""Abstract base class for email filters.

Filters are composable units that decide whether an email looks like a
genuine job opportunity.  Each filter returns a :class:`FilterDecision`
that the :class:`~email_opportunity_pipeline.filters.pipeline.FilterPipeline`
aggregates into a final :class:`~email_opportunity_pipeline.models.FilterOutcome`.

Built-in filters:

- :class:`~email_opportunity_pipeline.filters.keyword.KeywordFilter` --
  rule-based keyword/domain matching.
- :class:`~email_opportunity_pipeline.filters.llm.LLMFilter` -- optional
  LLM-based relevance check.

To add a custom filter, subclass ``EmailFilter``, set a unique ``name``,
and implement :meth:`evaluate`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import EmailMessage, FilterDecision


class EmailFilter(ABC):
    """Interface that every email filter must implement.

    Attributes:
        name: Human-readable identifier for the filter, used in
            analytics and logging (e.g. ``"keyword"``, ``"llm"``).
    """

    name: str = "base"

    @abstractmethod
    def evaluate(self, email: EmailMessage) -> FilterDecision:
        """Evaluate whether an email passes this filter.

        Args:
            email: The email message to evaluate.

        Returns:
            A :class:`FilterDecision` with:
            - ``filter_name``: the filter's :attr:`name`
            - ``passed``: ``True`` if the email is likely a job
              opportunity according to this filter
            - ``reasons``: human-readable list of reasons supporting
              the decision (used for analytics/debugging)
        """
        raise NotImplementedError
