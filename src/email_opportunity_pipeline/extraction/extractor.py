from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from ..models import EmailMessage


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, email: EmailMessage) -> Dict:
        raise NotImplementedError
