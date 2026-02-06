"""Abstract base class for email providers.

Every email provider (Gmail, Outlook, IMAP, etc.) implements the
:class:`EmailProvider` interface so the rest of the pipeline stays
provider-agnostic.

To add a new provider:

1. Subclass ``EmailProvider`` in a new module under ``providers/``.
2. Implement :meth:`fetch_messages` to yield ``EmailMessage`` objects.
3. Register the provider in ``cli.py`` (``_build_provider``) and update
   ``--provider`` choices.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..models import EmailMessage
from ..time_window import TimeWindow


class EmailProvider(ABC):
    """Interface that every email provider must implement.

    A provider is responsible for connecting to an email service and
    returning a stream of :class:`~email_opportunity_pipeline.models.EmailMessage`
    objects within a given :class:`~email_opportunity_pipeline.time_window.TimeWindow`.
    """

    @abstractmethod
    def fetch_messages(
        self,
        window: TimeWindow,
        max_results: Optional[int] = None,
        query: Optional[str] = None,
        include_body: bool = True,
    ) -> Iterable[EmailMessage]:
        """Fetch email messages from the provider.

        Args:
            window: Time range to fetch messages from.  The provider
                should return only messages whose internal date falls
                within ``[window.start, window.end]``.
            max_results: Optional upper limit on the number of messages
                returned.  ``None`` means no limit.
            query: Optional provider-specific query string (e.g. a Gmail
                search query) applied *in addition to* the time window.
            include_body: When ``True`` (default), fetch the full body
                text and HTML.  When ``False``, populate only metadata
                fields (headers, snippet, labels, attachments list).

        Returns:
            An iterable of :class:`EmailMessage` objects.  The iterable
            may be lazy (generator) or eager (list).

        Raises:
            RuntimeError: If the provider cannot connect or authenticate.
        """
        raise NotImplementedError
