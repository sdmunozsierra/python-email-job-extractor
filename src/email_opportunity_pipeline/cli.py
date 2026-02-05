from __future__ import annotations

import argparse
from pathlib import Path

from .analytics import (
    PipelineAnalytics,
    generate_report,
    save_analytics,
    save_report,
)
from .config import DEFAULT_WINDOW
from .io import read_messages, read_opportunities, write_messages, write_opportunities
from .pipeline import (
    build_filter_pipeline,
    extract_opportunities,
    filter_messages_with_outcomes,
    render_markdown_files,
    run_pipeline,
)
from .providers.gmail import GmailProvider
from .time_window import parse_window


def _build_provider(name: str):
    if name == "gmail":
        return GmailProvider()
    raise ValueError(f"Unknown provider: {name}")


def _cmd_fetch(args: argparse.Namespace) -> None:
    provider = _build_provider(args.provider)
    window = parse_window(args.window)
    messages = provider.fetch_messages(
        window=window,
        max_results=args.max_results,
        query=args.query,
        include_body=not args.metadata_only,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_messages(out_path, messages)
    print(f"Wrote messages to {out_path}")


def _cmd_filter(args: argparse.Namespace) -> None:
    messages = list(read_messages(args.input))
    pipeline = build_filter_pipeline(
        rules_path=args.rules,
        use_llm=args.llm_filter,
        llm_model=args.llm_model,
    )
    
    # Track analytics if requested
    analytics = PipelineAnalytics() if args.analytics else None
    if analytics:
        analytics.start()
        for msg in messages:
            analytics.record_email_fetch(msg)
    
    results = filter_messages_with_outcomes(pipeline, messages)
    filtered = []
    for msg, outcome in results:
        if analytics:
            analytics.record_filter_result(msg, outcome)
        if outcome.passed:
            filtered.append(msg)
    
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_messages(out_path, filtered)
    print(f"Wrote {len(filtered)} filtered messages to {out_path}")
    
    # Save analytics if requested
    if analytics:
        analytics.finish()
        analytics_dir = out_path.parent
        analytics_path = analytics_dir / "filter_analytics.json"
        report_path = analytics_dir / "filter_analytics_report.txt"
        save_analytics(analytics, analytics_path)
        save_report(analytics, report_path)
        print(f"Analytics saved to {analytics_path}")
        print(f"Report saved to {report_path}")
        
        # Print summary
        print(f"\n--- Filter Summary ---")
        print(f"Total processed: {analytics.total_emails_filtered}")
        print(f"Passed: {analytics.emails_passed_filter} ({analytics.filter_pass_rate:.1f}%)")
        print(f"Failed: {analytics.emails_failed_filter} ({analytics.filter_fail_rate:.1f}%)")


def _cmd_extract(args: argparse.Namespace) -> None:
    messages = read_messages(args.input)
    opportunities = extract_opportunities(messages, use_llm=args.llm_extract, llm_model=args.llm_model)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_opportunities(out_path, opportunities)
    print(f"Wrote {len(opportunities)} opportunities to {out_path}")


def _cmd_render(args: argparse.Namespace) -> None:
    opportunities = read_opportunities(args.input)
    out_dir = Path(args.out)
    render_markdown_files(opportunities, out_dir)
    print(f"Wrote {len(opportunities)} markdown files to {out_dir.resolve()}")


def _cmd_run(args: argparse.Namespace) -> None:
    provider = _build_provider(args.provider)
    window = parse_window(args.window)
    messages = list(
        provider.fetch_messages(
            window=window,
            max_results=args.max_results,
            query=args.query,
            include_body=True,
        )
    )

    outputs = run_pipeline(
        messages=messages,
        output_dir=Path(args.out_dir),
        work_dir=Path(args.work_dir),
        rules_path=args.rules,
        use_llm_filter=args.llm_filter,
        use_llm_extract=args.llm_extract,
        llm_model=args.llm_model,
        enable_analytics=not args.no_analytics,
    )

    print("Pipeline complete:")
    print(f"  Messages: {outputs.messages_path}")
    print(f"  Filtered: {outputs.filtered_path}")
    print(f"  Opportunities: {outputs.opportunities_path}")
    print(f"  Markdown: {outputs.markdown_dir}")
    
    if outputs.analytics_path and outputs.report_path:
        print(f"  Analytics: {outputs.analytics_path}")
        print(f"  Report: {outputs.report_path}")
        
        # Print the report to console if requested
        if args.show_report:
            print("\n")
            print(outputs.report_path.read_text(encoding="utf-8"))


def _cmd_analytics(args: argparse.Namespace) -> None:
    """Generate analytics from existing data files."""
    analytics = PipelineAnalytics()
    analytics.start()
    
    messages = []
    
    # Load messages
    if args.messages:
        messages = list(read_messages(args.messages))
        for msg in messages:
            analytics.record_email_fetch(msg)
        print(f"Loaded {len(messages)} messages from {args.messages}")
    
    # Run filter analysis on messages (always run if we have messages)
    if messages:
        pipeline = build_filter_pipeline(rules_path=args.rules if args.rules else None)
        results = filter_messages_with_outcomes(pipeline, messages)
        
        for msg, outcome in results:
            analytics.record_filter_result(msg, outcome)
        
        print(f"Filtered {len(messages)} messages")
    
    # Load and analyze opportunities
    if args.opportunities:
        opportunities = read_opportunities(args.opportunities)
        for opp in opportunities:
            analytics.record_extraction(opp)
        print(f"Loaded {len(opportunities)} opportunities from {args.opportunities}")
    
    analytics.finish()
    
    # Output
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    analytics_path = out_dir / "analytics.json"
    report_path = out_dir / "analytics_report.txt"
    
    save_analytics(analytics, analytics_path)
    save_report(analytics, report_path)
    
    print(f"\nAnalytics saved to {analytics_path}")
    print(f"Report saved to {report_path}")
    
    # Always print the report
    report = generate_report(analytics)
    print("\n")
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Email opportunity pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Fetch command
    fetch = subparsers.add_parser("fetch", help="Fetch emails from a provider")
    fetch.add_argument("--provider", default="gmail", choices=["gmail"])
    fetch.add_argument("--window", default=DEFAULT_WINDOW, help="Time window like 30m, 6h, 2d")
    fetch.add_argument("--query", default="", help="Provider-specific query string")
    fetch.add_argument("--max-results", type=int, default=None)
    fetch.add_argument("--metadata-only", action="store_true")
    fetch.add_argument("--out", required=True, help="Output JSON path")
    fetch.set_defaults(func=_cmd_fetch)

    # Filter command
    filt = subparsers.add_parser("filter", help="Filter emails by keyword rules")
    filt.add_argument("--in", dest="input", required=True, help="Input messages JSON")
    filt.add_argument("--out", required=True, help="Output filtered JSON")
    filt.add_argument("--rules", default="", help="Path to filter rules JSON")
    filt.add_argument("--llm-filter", action="store_true")
    filt.add_argument("--llm-model", default="gpt-4o-mini")
    filt.add_argument("--analytics", action="store_true", help="Generate analytics report")
    filt.set_defaults(func=_cmd_filter)

    # Extract command
    extract = subparsers.add_parser("extract", help="Extract opportunities to schema JSON")
    extract.add_argument("--in", dest="input", required=True, help="Input messages JSON")
    extract.add_argument("--out", required=True, help="Output opportunities JSON")
    extract.add_argument("--llm-extract", action="store_true")
    extract.add_argument("--llm-model", default="gpt-4o-mini")
    extract.set_defaults(func=_cmd_extract)

    # Render command
    render = subparsers.add_parser("render", help="Render markdown from opportunities JSON")
    render.add_argument("--in", dest="input", required=True, help="Input opportunities JSON")
    render.add_argument("--out", required=True, help="Output directory for markdown")
    render.set_defaults(func=_cmd_render)

    # Run command (full pipeline)
    run = subparsers.add_parser("run", help="Fetch + filter + extract + render")
    run.add_argument("--provider", default="gmail", choices=["gmail"])
    run.add_argument("--window", default=DEFAULT_WINDOW, help="Time window like 30m, 6h, 2d")
    run.add_argument("--query", default="", help="Provider-specific query string")
    run.add_argument("--max-results", type=int, default=None)
    run.add_argument("--rules", default="", help="Path to filter rules JSON")
    run.add_argument("--llm-filter", action="store_true")
    run.add_argument("--llm-extract", action="store_true")
    run.add_argument("--llm-model", default="gpt-4o-mini")
    run.add_argument("--work-dir", default="data", help="Where to write JSON artifacts")
    run.add_argument("--out-dir", default="out", help="Where to write markdown files")
    run.add_argument("--no-analytics", action="store_true", help="Disable analytics generation")
    run.add_argument("--show-report", action="store_true", help="Print analytics report to console")
    run.set_defaults(func=_cmd_run)

    # Analytics command (standalone)
    analytics = subparsers.add_parser("analytics", help="Generate analytics from existing data")
    analytics.add_argument("--messages", help="Path to messages JSON file")
    analytics.add_argument("--filtered", help="Path to filtered messages JSON file")
    analytics.add_argument("--opportunities", help="Path to opportunities JSON file")
    analytics.add_argument("--rules", default="", help="Path to filter rules JSON (for re-filtering)")
    analytics.add_argument("--out-dir", default=".", help="Output directory for analytics files")
    analytics.set_defaults(func=_cmd_analytics)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
