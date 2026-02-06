"""
Email sender with dry-run support and attachment handling.

Uses the Gmail API ``users.messages.send`` endpoint (requires the
``gmail.send`` scope).  In *dry-run* mode the email is formatted but
never transmitted -- allowing the user to review the draft first.
"""
from __future__ import annotations

import base64
import logging
import mimetypes
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

from .models import EmailDraft, ReplyResult, ReplyStatus

logger = logging.getLogger(__name__)


def _build_mime_message(draft: EmailDraft, from_address: str) -> MIMEMultipart:
    """Build a fully-formed MIME message from an ``EmailDraft``.

    Handles:
    - Plain-text body (and optional HTML alternative)
    - ``In-Reply-To`` / ``References`` threading headers
    - File attachments with correct MIME types
    """
    # Use multipart/mixed so we can add attachments
    msg = MIMEMultipart("mixed")
    msg["To"] = draft.to
    msg["From"] = from_address
    msg["Subject"] = draft.subject

    # Threading headers
    if draft.in_reply_to:
        msg["In-Reply-To"] = draft.in_reply_to
    if draft.references:
        msg["References"] = draft.references

    # Body -- prefer multipart/alternative if we have HTML
    if draft.body_html:
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(draft.body_text, "plain", "utf-8"))
        alt.attach(MIMEText(draft.body_html, "html", "utf-8"))
        msg.attach(alt)
    else:
        msg.attach(MIMEText(draft.body_text, "plain", "utf-8"))

    # Attachments
    for attachment_path_str in draft.attachment_paths:
        attachment_path = Path(attachment_path_str)
        if not attachment_path.exists():
            logger.warning("Attachment not found, skipping: %s", attachment_path)
            continue

        content_type, _ = mimetypes.guess_type(str(attachment_path))
        if content_type is None:
            content_type = "application/octet-stream"

        maintype, subtype = content_type.split("/", 1)

        with open(attachment_path, "rb") as fp:
            attachment = MIMEApplication(fp.read(), _subtype=subtype)

        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment_path.name,
        )
        msg.attach(attachment)

    return msg


class GmailSender:
    """Send emails via the Gmail API.

    Requires OAuth credentials with the ``gmail.send`` scope.

    Usage::

        sender = GmailSender()          # uses default credential paths
        result = sender.send(draft)      # actually send
        result = sender.send(draft, dry_run=True)  # preview only
    """

    def __init__(
        self,
        user_id: str = "me",
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.credentials_path = credentials_path or os.getenv(
            "GMAIL_CREDENTIALS_PATH", "credentials.json"
        )
        self.token_path = token_path or os.getenv(
            "GMAIL_TOKEN_PATH", "token.json"
        )

    # ------------------------------------------------------------------
    # Auth (mirrors GmailProvider but with send scope)
    # ------------------------------------------------------------------

    def _build_service(self):
        """Build an authorised Gmail API service with send scope."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        from ..config import GMAIL_SEND_SCOPES

        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(
                self.token_path, GMAIL_SEND_SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, GMAIL_SEND_SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(
        self,
        draft: EmailDraft,
        *,
        dry_run: bool = False,
        from_address: Optional[str] = None,
    ) -> ReplyResult:
        """Send (or dry-run) a single email draft.

        Args:
            draft: The email draft to send.
            dry_run: If ``True``, build the MIME message but do not
                transmit it.  The formatted body is still available in
                the returned ``ReplyResult``.
            from_address: Sender address override.  Defaults to the
                authenticated Gmail user.

        Returns:
            ``ReplyResult`` indicating success, failure, or dry-run status.
        """
        from_address = from_address or self.user_id

        if dry_run:
            # Build the MIME message for validation but don't send
            try:
                _build_mime_message(draft, from_address)
            except Exception as exc:
                return ReplyResult(
                    draft=draft,
                    status=ReplyStatus.FAILED,
                    error=f"MIME build error during dry run: {exc}",
                )
            return ReplyResult(draft=draft, status=ReplyStatus.DRY_RUN)

        # Real send
        try:
            service = self._build_service()
            mime_msg = _build_mime_message(draft, from_address)
            raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("ascii")

            body: dict = {"raw": raw}
            if draft.thread_id:
                body["threadId"] = draft.thread_id

            sent = (
                service.users()
                .messages()
                .send(userId=self.user_id, body=body)
                .execute()
            )

            gmail_id = sent.get("id", "")
            logger.info(
                "Sent reply to %s for %s at %s (Gmail ID: %s)",
                draft.to,
                draft.job_title,
                draft.company,
                gmail_id,
            )
            return ReplyResult(
                draft=draft,
                status=ReplyStatus.SENT,
                gmail_message_id=gmail_id,
            )

        except Exception as exc:
            logger.exception("Failed to send reply to %s", draft.to)
            return ReplyResult(
                draft=draft,
                status=ReplyStatus.FAILED,
                error=str(exc),
            )

    def send_batch(
        self,
        drafts: List[EmailDraft],
        *,
        dry_run: bool = False,
        from_address: Optional[str] = None,
    ) -> List[ReplyResult]:
        """Send (or dry-run) multiple email drafts.

        Args:
            drafts: List of email drafts.
            dry_run: If ``True``, preview only.
            from_address: Optional sender address override.

        Returns:
            List of ``ReplyResult`` objects.
        """
        results: List[ReplyResult] = []
        for draft in drafts:
            result = self.send(draft, dry_run=dry_run, from_address=from_address)
            results.append(result)
        return results
