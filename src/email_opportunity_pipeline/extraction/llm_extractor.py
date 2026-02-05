from __future__ import annotations

import json
from typing import Optional

from ..models import EmailMessage
from .extractor import BaseExtractor
from .schema import JOB_SCHEMA


SYSTEM_INSTRUCTIONS = (
    "Extract job opportunity data from recruiter/job emails into the provided JSON schema. "
    "Rules: do not invent details, use null/[] when missing. Identify all engagement options "
    "(FULL_TIME, PART_TIME, CONTRACT_W2, CONTRACT_C2C, CONTRACT_1099). If multiple options are "
    "offered, create one entry per option and place differences in the option object. "
    "Provide evidence snippets for title, location/remote, engagement type, constraints, and pay."
)


class LLMExtractor(BaseExtractor):
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install optional dependency: pip install -e '.[llm]'") from exc

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract(self, email: EmailMessage) -> dict:
        prompt = {
            "message_id": email.message_id,
            "thread_id": email.thread_id,
            "headers": email.headers.to_dict(),
            "snippet": email.snippet,
            "body_text": (email.body_text or "")[:6000],
            "attachments": [att.to_dict() for att in email.attachments],
        }

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=True)},
            ],
            text={"format": {"type": "json_schema", "json_schema": JOB_SCHEMA}},
        )
        return json.loads(response.output_text)
