"""Email provider module.

Defines the :class:`EmailProvider` interface and concrete implementations.

Currently supported:

- :class:`GmailProvider` -- fetch messages via the Gmail API (OAuth 2.0)
"""

from .base import EmailProvider
from .gmail import GmailProvider, build_gmail_provider

__all__ = [
    "EmailProvider",
    "GmailProvider",
    "build_gmail_provider",
]
