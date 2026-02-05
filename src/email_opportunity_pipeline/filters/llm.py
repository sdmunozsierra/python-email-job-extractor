from __future__ import annotations

import json
from typing import Optional

from ..models import EmailMessage, FilterDecision
from .base import EmailFilter


class LLMFilter(EmailFilter):
    name = "llm"

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install optional dependency: pip install -e '.[llm]'") from exc

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def evaluate(self, email: EmailMessage) -> FilterDecision:
        body = email.body_text or ""
        body = body[:4000]

        prompt = {
            "subject": email.headers.subject,
            "from": email.headers.from_,
            "snippet": email.snippet,
            "body": body,
        }

        system = (
            "Decide if this email is a job opportunity. "
            "Return JSON with keys: keep (boolean) and reason (string). "
            "Keep only real job opportunities or recruiter outreach."
        )

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=True)},
            ],
            text={"format": {"type": "json_object"}},
        )

        try:
            data = json.loads(response.output_text)
        except json.JSONDecodeError:
            data = {"keep": False, "reason": "invalid LLM response"}

        return FilterDecision(
            filter_name=self.name,
            passed=bool(data.get("keep")),
            reasons=[data.get("reason", "llm decision")],
        )
