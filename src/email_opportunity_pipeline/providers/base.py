from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..models import EmailMessage
from ..time_window import TimeWindow


class EmailProvider(ABC):
    @abstractmethod
    def fetch_messages(
        self,
        window: TimeWindow,
        max_results: Optional[int] = None,
        query: Optional[str] = None,
        include_body: bool = True,
    ) -> Iterable[EmailMessage]:
        raise NotImplementedError
