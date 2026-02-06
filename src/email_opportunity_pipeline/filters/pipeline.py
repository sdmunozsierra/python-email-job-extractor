"""Filter pipeline -- orchestrates multiple filters into a final decision.

The :class:`FilterPipeline` runs a sequence of :class:`EmailFilter` instances
against each email and aggregates the individual :class:`FilterDecision`
objects into a single :class:`FilterOutcome`.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple

from ..models import EmailMessage, FilterDecision, FilterOutcome
from .base import EmailFilter


class FilterPipeline:
    """Compose multiple :class:`EmailFilter` instances into a single pipeline.

    Args:
        filters: Ordered list of filters to apply.
        stop_on_reject: When ``True`` (default), stop evaluating as soon
            as any filter rejects the email.  Set to ``False`` to collect
            decisions from *all* filters regardless of outcome.
    """

    def __init__(self, filters: List[EmailFilter], stop_on_reject: bool = True) -> None:
        self.filters = filters
        self.stop_on_reject = stop_on_reject

    def apply(self, email: EmailMessage) -> FilterOutcome:
        """Apply all filters to a single email.

        Args:
            email: The email message to evaluate.

        Returns:
            A :class:`FilterOutcome` aggregating all individual
            :class:`FilterDecision` objects.
        """
        decisions: List[FilterDecision] = []
        reasons: List[str] = []
        passed = True

        for flt in self.filters:
            decision = flt.evaluate(email)
            decisions.append(decision)
            if not decision.passed:
                passed = False
                reasons.extend(decision.reasons)
                if self.stop_on_reject:
                    break
            else:
                reasons.extend(decision.reasons)

        return FilterOutcome(passed=passed, reasons=reasons, decisions=decisions)

    def run(self, emails: Iterable[EmailMessage]) -> List[Tuple[EmailMessage, FilterOutcome]]:
        """Apply the pipeline to multiple emails.

        Args:
            emails: Iterable of email messages.

        Returns:
            List of ``(EmailMessage, FilterOutcome)`` tuples, one per
            input email.
        """
        results: List[Tuple[EmailMessage, FilterOutcome]] = []
        for email in emails:
            results.append((email, self.apply(email)))
        return results
