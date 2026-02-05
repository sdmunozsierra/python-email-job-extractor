from __future__ import annotations

import argparse
from pathlib import Path

from .config import DEFAULT_WINDOW
from .io import read_messages, read_opportunities, write_messages, write_opportunities
from .pipeline import build_filter_pipeline, extract_opportunities, render_markdown_files, run_pipeline
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
    messages = read_messages(args.input)
    pipeline = build_filter_pipeline(
        rules_path=args.rules,
        use_llm=args.llm_filter,
        llm_model=args.llm_model,
    )
    filtered = [msg for msg, outcome in pipeline.run(messages) if outcome.passed]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_messages(out_path, filtered)
    print(f"Wrote {len(filtered)} filtered messages to {out_path}")


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
    )

    print("Pipeline complete:")
    print(f"  Messages: {outputs.messages_path}")
    print(f"  Filtered: {outputs.filtered_path}")
    print(f"  Opportunities: {outputs.opportunities_path}")
    print(f"  Markdown: {outputs.markdown_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Email opportunity pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="Fetch emails from a provider")
    fetch.add_argument("--provider", default="gmail", choices=["gmail"])
    fetch.add_argument("--window", default=DEFAULT_WINDOW, help="Time window like 30m, 6h, 2d")
    fetch.add_argument("--query", default="", help="Provider-specific query string")
    fetch.add_argument("--max-results", type=int, default=None)
    fetch.add_argument("--metadata-only", action="store_true")
    fetch.add_argument("--out", required=True, help="Output JSON path")
    fetch.set_defaults(func=_cmd_fetch)

    filt = subparsers.add_parser("filter", help="Filter emails by keyword rules")
    filt.add_argument("--in", dest="input", required=True, help="Input messages JSON")
    filt.add_argument("--out", required=True, help="Output filtered JSON")
    filt.add_argument("--rules", default="", help="Path to filter rules JSON")
    filt.add_argument("--llm-filter", action="store_true")
    filt.add_argument("--llm-model", default="gpt-4o-mini")
    filt.set_defaults(func=_cmd_filter)

    extract = subparsers.add_parser("extract", help="Extract opportunities to schema JSON")
    extract.add_argument("--in", dest="input", required=True, help="Input messages JSON")
    extract.add_argument("--out", required=True, help="Output opportunities JSON")
    extract.add_argument("--llm-extract", action="store_true")
    extract.add_argument("--llm-model", default="gpt-4o-mini")
    extract.set_defaults(func=_cmd_extract)

    render = subparsers.add_parser("render", help="Render markdown from opportunities JSON")
    render.add_argument("--in", dest="input", required=True, help="Input opportunities JSON")
    render.add_argument("--out", required=True, help="Output directory for markdown")
    render.set_defaults(func=_cmd_render)

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
    run.set_defaults(func=_cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
