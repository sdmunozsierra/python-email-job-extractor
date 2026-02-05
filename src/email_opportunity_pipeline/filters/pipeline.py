from __future__ import annotations

from typing import Iterable, List, Tuple

from ..models import EmailMessage, FilterDecision, FilterOutcome
from .base import EmailFilter


class FilterPipeline:
    def __init__(self, filters: List[EmailFilter], stop_on_reject: bool = True) -> None:
        self.filters = filters
        self.stop_on_reject = stop_on_reject

    def apply(self, email: EmailMessage) -> FilterOutcome:
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
        results: List[Tuple[EmailMessage, FilterOutcome]] = []
        for email in emails:
            results.append((email, self.apply(email)))
        return results
