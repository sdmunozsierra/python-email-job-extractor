from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .filters import FilterPipeline, KeywordFilter, LLMFilter, FilterRules, load_rules
from .io import write_messages, write_opportunities
from .models import EmailMessage
from .extraction import RuleBasedExtractor, LLMExtractor, render_markdown


@dataclass
class PipelineOutputs:
    messages_path: Path
    filtered_path: Path
    opportunities_path: Path
    markdown_dir: Path


def build_filter_pipeline(
    rules_path: Optional[str] = None,
    use_llm: bool = False,
    llm_model: str = "gpt-4o-mini",
) -> FilterPipeline:
    rules = load_rules(rules_path) if rules_path else FilterRules.default()
    filters = [KeywordFilter(rules=rules)]
    if use_llm:
        filters.append(LLMFilter(model=llm_model))
    return FilterPipeline(filters=filters)


def filter_messages(
    pipeline: FilterPipeline, messages: Iterable[EmailMessage]
) -> List[EmailMessage]:
    results = pipeline.run(messages)
    passed = [email for email, outcome in results if outcome.passed]
    return passed


def extract_opportunities(
    messages: Iterable[EmailMessage],
    use_llm: bool = False,
    llm_model: str = "gpt-4o-mini",
) -> List[dict]:
    extractor = LLMExtractor(model=llm_model) if use_llm else RuleBasedExtractor()
    return [extractor.extract(msg) for msg in messages]


def render_markdown_files(opportunities: List[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for job in opportunities:
        source = job.get("source_email", {}) or {}
        msg_id = source.get("message_id") or "unknown"
        markdown = render_markdown(job)
        (output_dir / f"{msg_id}.md").write_text(markdown, encoding="utf-8")


def run_pipeline(
    messages: Iterable[EmailMessage],
    output_dir: Path,
    work_dir: Path,
    rules_path: Optional[str] = None,
    use_llm_filter: bool = False,
    use_llm_extract: bool = False,
    llm_model: str = "gpt-4o-mini",
) -> PipelineOutputs:
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    messages_path = work_dir / "messages.json"
    filtered_path = work_dir / "filtered.json"
    opportunities_path = work_dir / "opportunities.json"
    markdown_dir = output_dir

    write_messages(messages_path, messages)

    pipeline = build_filter_pipeline(rules_path=rules_path, use_llm=use_llm_filter, llm_model=llm_model)
    filtered_messages = filter_messages(pipeline, messages)
    write_messages(filtered_path, filtered_messages)

    opportunities = extract_opportunities(
        filtered_messages,
        use_llm=use_llm_extract,
        llm_model=llm_model,
    )
    write_opportunities(opportunities_path, opportunities)
    render_markdown_files(opportunities, markdown_dir)

    return PipelineOutputs(
        messages_path=messages_path,
        filtered_path=filtered_path,
        opportunities_path=opportunities_path,
        markdown_dir=markdown_dir,
    )
