from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import EmailMessage, FilterDecision


class EmailFilter(ABC):
    name: str = "base"

    @abstractmethod
    def evaluate(self, email: EmailMessage) -> FilterDecision:
        raise NotImplementedError
