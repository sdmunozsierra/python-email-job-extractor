from __future__ import annotations

DEFAULT_MAX_RESULTS = 500
DEFAULT_WINDOW = "1d"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

# Scopes required for sending emails (reply feature).
# Includes ``gmail.send`` in addition to ``gmail.readonly``.
GMAIL_SEND_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
