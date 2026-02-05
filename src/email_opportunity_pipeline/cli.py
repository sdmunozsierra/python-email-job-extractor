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
from .io import (
    read_messages,
    read_opportunities,
    write_messages,
    write_opportunities,
    read_resume,
    write_match_results,
    write_single_match_result,
    read_match_results,
    write_job_analyses,
    read_job_analyses,
)
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


# ============================================================================
# Job Analysis and Resume Matching Commands
# ============================================================================

def _cmd_analyze(args: argparse.Namespace) -> None:
    """Analyze job opportunities to extract structured requirements."""
    from .matching import JobAnalyzer
    
    opportunities = read_opportunities(args.input)
    print(f"Loaded {len(opportunities)} opportunities from {args.input}")
    
    analyzer = JobAnalyzer(model=args.llm_model)
    analyses = []
    
    for i, opp in enumerate(opportunities, 1):
        title = opp.get("job_title", "Unknown")
        company = opp.get("company", "Unknown")
        print(f"Analyzing [{i}/{len(opportunities)}]: {title} at {company}...")
        
        analysis = analyzer.analyze(opp)
        analyses.append(analysis)
    
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_job_analyses(out_path, analyses)
    
    print(f"\nWrote {len(analyses)} job analyses to {out_path}")
    
    # Print summary
    if analyses:
        print("\n--- Analysis Summary ---")
        for analysis in analyses[:5]:  # Show first 5
            src = analysis.get("source_job", {})
            role = analysis.get("role_summary", {})
            reqs = analysis.get("requirements", {})
            
            print(f"\n{src.get('job_title', 'Unknown')} at {src.get('company', 'Unknown')}")
            print(f"  Level: {role.get('level', 'Unknown')}")
            print(f"  Experience: {reqs.get('years_experience_min', '?')}-{reqs.get('years_experience_max', '+')} years")
            print(f"  Mandatory skills: {len(reqs.get('mandatory_skills', []))}")
            print(f"  Preferred skills: {len(reqs.get('preferred_skills', []))}")


def _cmd_match(args: argparse.Namespace) -> None:
    """Match a resume against job opportunities."""
    from .matching import ResumeMatcher, JobAnalyzer
    from .matching.report import render_match_markdown, render_match_summary
    
    # Load resume
    resume = read_resume(args.resume)
    print(f"Loaded resume for: {resume.personal.name}")
    
    # Load opportunities
    opportunities = read_opportunities(args.opportunities)
    print(f"Loaded {len(opportunities)} opportunities")
    
    # Optionally load pre-computed analyses
    job_analyses = None
    if args.analyses:
        job_analyses = read_job_analyses(args.analyses)
        print(f"Loaded {len(job_analyses)} pre-computed analyses")
    
    # Initialize matcher
    matcher = ResumeMatcher(model=args.llm_model)
    
    # Single job or batch match
    if args.job_index is not None:
        # Match single job
        if args.job_index < 0 or args.job_index >= len(opportunities):
            print(f"Error: job-index {args.job_index} out of range (0-{len(opportunities)-1})")
            return
        
        job = opportunities[args.job_index]
        analysis = job_analyses[args.job_index] if job_analyses else None
        
        print(f"Matching against: {job.get('job_title', 'Unknown')} at {job.get('company', 'Unknown')}")
        result = matcher.match(resume, job, analysis)
        
        # Output
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.format == "json":
            write_single_match_result(out_path, result)
        else:  # markdown
            md = render_match_markdown(result, job)
            out_path.write_text(md, encoding="utf-8")
        
        print(f"\nMatch result saved to {out_path}")
        _print_match_summary(result, job)
    
    else:
        # Batch match all jobs
        print(f"\nMatching against all {len(opportunities)} opportunities...")
        results = matcher.match_batch(resume, opportunities, job_analyses)
        
        # Output
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON results
        results_path = out_dir / "match_results.json"
        write_match_results(results_path, results, resume_id=resume.source_file)
        print(f"Match results saved to {results_path}")
        
        # Save summary report
        summary_path = out_dir / "match_summary.md"
        summary_md = render_match_summary(results, opportunities)
        summary_path.write_text(summary_md, encoding="utf-8")
        print(f"Summary report saved to {summary_path}")
        
        # Save individual match reports if requested
        if args.individual_reports:
            reports_dir = out_dir / "match_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            for result in results:
                job = next((o for o in opportunities 
                           if o.get("source_email", {}).get("message_id") == result.job_id), {})
                md = render_match_markdown(result, job)
                report_path = reports_dir / f"{result.job_id}.md"
                report_path.write_text(md, encoding="utf-8")
            
            print(f"Individual reports saved to {reports_dir}")
        
        # Print summary
        _print_batch_summary(results, opportunities)


def _print_match_summary(result, job: dict) -> None:
    """Print a brief match summary to console."""
    print("\n" + "=" * 60)
    print(f"Match Score: {result.overall_score:.0f}/100 ({result.match_grade.upper()})")
    print(f"Recommendation: {result.recommendation.replace('_', ' ').upper()}")
    print("=" * 60)
    
    print(f"\nSkills: {result.skills_match.score:.0f}/100")
    print(f"  Mandatory: {result.skills_match.mandatory_met}/{result.skills_match.mandatory_total}")
    print(f"  Preferred: {result.skills_match.preferred_met}/{result.skills_match.preferred_total}")
    
    print(f"\nExperience: {result.experience_match.score:.0f}/100")
    
    if result.insights.strengths:
        print("\nKey Strengths:")
        for s in result.insights.strengths[:3]:
            print(f"  + {s}")
    
    if result.insights.concerns:
        print("\nConcerns:")
        for c in result.insights.concerns[:3]:
            print(f"  - {c}")


def _print_batch_summary(results, opportunities: list) -> None:
    """Print a batch match summary to console."""
    print("\n" + "=" * 60)
    print(f"MATCH SUMMARY - {len(results)} Jobs Analyzed")
    print("=" * 60)
    
    # Grade distribution
    grades = {}
    for r in results:
        grades[r.match_grade] = grades.get(r.match_grade, 0) + 1
    
    print("\nGrade Distribution:")
    for grade in ["excellent", "good", "fair", "poor", "unqualified"]:
        count = grades.get(grade, 0)
        if count:
            print(f"  {grade.title()}: {count}")
    
    # Top matches
    top = results[:5]
    if top:
        print("\nTop 5 Matches:")
        for i, r in enumerate(top, 1):
            job = next((o for o in opportunities 
                       if o.get("source_email", {}).get("message_id") == r.job_id), {})
            title = job.get("job_title", "Unknown")[:40]
            company = job.get("company", "Unknown")[:20]
            print(f"  {i}. [{r.overall_score:.0f}] {title} at {company}")
    
    # Action items
    strong = sum(1 for r in results if r.recommendation == "strong_apply")
    apply = sum(1 for r in results if r.recommendation == "apply")
    
    print(f"\nRecommended Actions:")
    print(f"  Strong Apply: {strong}")
    print(f"  Apply: {apply}")


def _cmd_rank(args: argparse.Namespace) -> None:
    """Rank and filter previously computed match results."""
    results = read_match_results(args.input)
    print(f"Loaded {len(results)} match results")
    
    # Filter by minimum score
    if args.min_score:
        results = [r for r in results if r.overall_score >= args.min_score]
        print(f"After min-score filter: {len(results)} results")
    
    # Filter by grade
    if args.grade:
        grades = set(args.grade.split(","))
        results = [r for r in results if r.match_grade in grades]
        print(f"After grade filter: {len(results)} results")
    
    # Filter by recommendation
    if args.recommendation:
        recs = set(args.recommendation.split(","))
        results = [r for r in results if r.recommendation in recs]
        print(f"After recommendation filter: {len(results)} results")
    
    # Sort
    results.sort(key=lambda r: r.overall_score, reverse=True)
    
    # Limit
    if args.top:
        results = results[:args.top]
    
    # Output
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        write_match_results(out_path, results)
        print(f"\nFiltered results saved to {out_path}")
    
    # Print
    print("\n" + "=" * 60)
    print("RANKED RESULTS")
    print("=" * 60)
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Score: {r.overall_score:.0f} | Grade: {r.match_grade} | Rec: {r.recommendation}")
        print(f"   Job ID: {r.job_id}")
        if r.insights.strengths:
            print(f"   Strength: {r.insights.strengths[0][:60]}...")
        if r.skills_match.missing_mandatory:
            print(f"   Gap: {r.skills_match.missing_mandatory[0]}")


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

    # =========================================================================
    # Job Analysis and Resume Matching Commands
    # =========================================================================

    # Analyze command - Extract structured requirements from jobs
    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze job opportunities to extract structured requirements (LLM)"
    )
    analyze.add_argument(
        "--in", dest="input", required=True,
        help="Input opportunities JSON file"
    )
    analyze.add_argument(
        "--out", required=True,
        help="Output job analyses JSON file"
    )
    analyze.add_argument(
        "--llm-model", default="gpt-4o-mini",
        help="LLM model to use for analysis"
    )
    analyze.set_defaults(func=_cmd_analyze)

    # Match command - Match resume against job opportunities
    match = subparsers.add_parser(
        "match",
        help="Match a resume against job opportunities (LLM)"
    )
    match.add_argument(
        "--resume", required=True,
        help="Path to resume file (JSON or Markdown)"
    )
    match.add_argument(
        "--opportunities", required=True,
        help="Path to opportunities JSON file"
    )
    match.add_argument(
        "--analyses",
        help="Path to pre-computed job analyses JSON (optional)"
    )
    match.add_argument(
        "--job-index", type=int,
        help="Match against single job by index (0-based). If not set, matches all."
    )
    match.add_argument(
        "--out", required=True,
        help="Output path (file for single match, directory for batch)"
    )
    match.add_argument(
        "--format", choices=["json", "markdown"], default="markdown",
        help="Output format for single match (default: markdown)"
    )
    match.add_argument(
        "--individual-reports", action="store_true",
        help="Generate individual markdown reports for each job (batch mode)"
    )
    match.add_argument(
        "--llm-model", default="gpt-4o-mini",
        help="LLM model to use for matching"
    )
    match.set_defaults(func=_cmd_match)

    # Rank command - Filter and rank match results
    rank = subparsers.add_parser(
        "rank",
        help="Filter and rank previously computed match results"
    )
    rank.add_argument(
        "--in", dest="input", required=True,
        help="Input match results JSON file"
    )
    rank.add_argument(
        "--out",
        help="Output filtered results JSON file (optional)"
    )
    rank.add_argument(
        "--min-score", type=float,
        help="Minimum overall score to include"
    )
    rank.add_argument(
        "--grade",
        help="Comma-separated grades to include (e.g., excellent,good)"
    )
    rank.add_argument(
        "--recommendation",
        help="Comma-separated recommendations to include (e.g., strong_apply,apply)"
    )
    rank.add_argument(
        "--top", type=int,
        help="Limit to top N results"
    )
    rank.set_defaults(func=_cmd_rank)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
