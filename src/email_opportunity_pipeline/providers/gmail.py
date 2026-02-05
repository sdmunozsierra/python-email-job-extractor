from __future__ import annotations

import os
from typing import Iterable, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import DEFAULT_MAX_RESULTS, GMAIL_SCOPES
from ..models import Attachment, EmailHeaders, EmailMessage, EmailSource
from ..time_window import TimeWindow, to_gmail_query
from .base import EmailProvider
from .gmail_parser import (
    extract_body_text,
    get_header,
    list_attachments,
    parse_internal_date_ms,
)


class GmailProvider(EmailProvider):
    def __init__(
        self,
        user_id: str = "me",
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.credentials_path = credentials_path or os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
        self.token_path = token_path or os.getenv("GMAIL_TOKEN_PATH", "token.json")

    def _build_service(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, GMAIL_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def _list_message_ids(
        self,
        service,
        query: str,
        max_results: Optional[int],
    ) -> List[str]:
        msg_ids: List[str] = []
        page_token = None
        page_size = min(DEFAULT_MAX_RESULTS, max_results) if max_results else DEFAULT_MAX_RESULTS

        while True:
            resp = (
                service.users()
                .messages()
                .list(userId=self.user_id, q=query, pageToken=page_token, maxResults=page_size)
                .execute()
            )
            msg_ids.extend([m["id"] for m in resp.get("messages", [])])

            if max_results and len(msg_ids) >= max_results:
                return msg_ids[:max_results]

            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return msg_ids

    def fetch_messages(
        self,
        window: TimeWindow,
        max_results: Optional[int] = None,
        query: Optional[str] = None,
        include_body: bool = True,
    ) -> Iterable[EmailMessage]:
        service = self._build_service()
        search_query = query or to_gmail_query(window)
        msg_ids = self._list_message_ids(service, search_query, max_results)

        messages: List[EmailMessage] = []
        for msg_id in msg_ids:
            fmt = "full" if include_body else "metadata"
            msg = (
                service.users()
                .messages()
                .get(
                    userId=self.user_id,
                    id=msg_id,
                    format=fmt,
                    metadataHeaders=["From", "To", "Cc", "Bcc", "Date", "Subject", "Message-Id"],
                )
                .execute()
            )

            headers = (msg.get("payload", {}) or {}).get("headers", []) or []
            body_info = extract_body_text(msg) if include_body else {"text": "", "text_html": ""}
            attachments = list_attachments(msg.get("payload", {}) or {}) if include_body else []

            email = EmailMessage(
                message_id=msg.get("id", ""),
                thread_id=msg.get("threadId", ""),
                internal_date=parse_internal_date_ms(msg.get("internalDate")),
                headers=EmailHeaders(
                    from_=get_header(headers, "From"),
                    to=get_header(headers, "To"),
                    cc=get_header(headers, "Cc"),
                    bcc=get_header(headers, "Bcc"),
                    date=get_header(headers, "Date"),
                    subject=get_header(headers, "Subject"),
                    message_id=get_header(headers, "Message-Id"),
                ),
                snippet=msg.get("snippet", ""),
                body_text=body_info.get("text", ""),
                body_html=body_info.get("text_html", ""),
                labels=msg.get("labelIds", []) or [],
                attachments=[Attachment.from_dict(a) for a in attachments],
                source=EmailSource(provider="gmail", user_id=self.user_id),
            )
            messages.append(email)

        return messages


def build_gmail_provider() -> GmailProvider:
    return GmailProvider()
