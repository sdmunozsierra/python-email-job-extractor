from __future__ import annotations

import json
from importlib.resources import files
from typing import Any, Dict


def load_job_schema() -> Dict[str, Any]:
    schema_path = files("email_opportunity_pipeline.schemas").joinpath("job_opportunity.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


JOB_SCHEMA = load_job_schema()
