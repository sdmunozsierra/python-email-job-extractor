from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .analytics import PipelineAnalytics, save_analytics, save_report
from .filters import FilterPipeline, KeywordFilter, LLMFilter, FilterRules, load_rules
from .io import write_messages, write_opportunities
from .models import EmailMessage, FilterOutcome
from .extraction import RuleBasedExtractor, LLMExtractor, render_markdown


@dataclass
class PipelineOutputs:
    messages_path: Path
    filtered_path: Path
    opportunities_path: Path
    markdown_dir: Path
    analytics_path: Optional[Path] = None
    report_path: Optional[Path] = None


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


def filter_messages_with_outcomes(
    pipeline: FilterPipeline, messages: Iterable[EmailMessage]
) -> List[Tuple[EmailMessage, FilterOutcome]]:
    """Filter messages and return both emails and their outcomes."""
    return pipeline.run(messages)


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
    enable_analytics: bool = True,
) -> PipelineOutputs:
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    messages_path = work_dir / "messages.json"
    filtered_path = work_dir / "filtered.json"
    opportunities_path = work_dir / "opportunities.json"
    analytics_path = work_dir / "analytics.json" if enable_analytics else None
    report_path = work_dir / "analytics_report.txt" if enable_analytics else None
    markdown_dir = output_dir

    # Initialize analytics
    analytics = PipelineAnalytics() if enable_analytics else None
    if analytics:
        analytics.start()

    # Convert to list if needed and record fetch metrics
    messages_list = list(messages)
    if analytics:
        for msg in messages_list:
            analytics.record_email_fetch(msg)
    
    write_messages(messages_path, messages_list)

    # Filter with analytics tracking
    pipeline = build_filter_pipeline(rules_path=rules_path, use_llm=use_llm_filter, llm_model=llm_model)
    filter_results = filter_messages_with_outcomes(pipeline, messages_list)
    
    filtered_messages = []
    for email, outcome in filter_results:
        if analytics:
            analytics.record_filter_result(email, outcome)
        if outcome.passed:
            filtered_messages.append(email)
    
    write_messages(filtered_path, filtered_messages)

    # Extract opportunities with analytics tracking
    opportunities = extract_opportunities(
        filtered_messages,
        use_llm=use_llm_extract,
        llm_model=llm_model,
    )
    
    if analytics:
        for opp in opportunities:
            analytics.record_extraction(opp)
    
    write_opportunities(opportunities_path, opportunities)
    render_markdown_files(opportunities, markdown_dir)

    # Finalize and save analytics
    if analytics:
        analytics.finish()
        save_analytics(analytics, analytics_path)
        save_report(analytics, report_path)

    return PipelineOutputs(
        messages_path=messages_path,
        filtered_path=filtered_path,
        opportunities_path=opportunities_path,
        markdown_dir=markdown_dir,
        analytics_path=analytics_path,
        report_path=report_path,
    )
