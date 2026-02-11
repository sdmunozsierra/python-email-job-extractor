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
    write_tailoring_report,
    write_tailoring_results,
    read_tailoring_results,
    read_questionnaire,
    write_drafts,
    read_drafts,
    write_reply_results,
    read_reply_results,
    write_correlation,
    read_correlation,
    write_tracking,
    read_tracking,
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


# ============================================================================
# Resume Tailoring Commands
# ============================================================================

def _cmd_tailor(args: argparse.Namespace) -> None:
    """Tailor a resume for one or more job opportunities using match results."""
    from .tailoring import TailoringEngine
    from .tailoring.report import render_tailoring_report, render_tailoring_summary

    # Load inputs
    resume = read_resume(args.resume)
    print(f"Loaded resume for: {resume.personal.name}")

    match_results = read_match_results(args.match_results)
    print(f"Loaded {len(match_results)} match results")

    # Optionally load opportunities for context
    opportunities = []
    jobs_map = {}
    if args.opportunities:
        opportunities = read_opportunities(args.opportunities)
        for opp in opportunities:
            msg_id = opp.get("source_email", {}).get("message_id")
            if msg_id:
                jobs_map[msg_id] = opp
        print(f"Loaded {len(opportunities)} opportunities for context")

    # Filter match results
    if args.min_score:
        match_results = [r for r in match_results if r.overall_score >= args.min_score]
        print(f"After min-score filter: {len(match_results)} results")

    if args.recommendation:
        recs = set(args.recommendation.split(","))
        match_results = [r for r in match_results if r.recommendation in recs]
        print(f"After recommendation filter: {len(match_results)} results")

    if args.top:
        match_results.sort(key=lambda r: r.overall_score, reverse=True)
        match_results = match_results[:args.top]

    if not match_results:
        print("No match results to tailor for.")
        return

    # Set up engine
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = TailoringEngine(output_dir=out_dir)

    build_docx = not args.no_docx
    tailored_resumes = []

    for i, match_result in enumerate(match_results, 1):
        job = jobs_map.get(match_result.job_id, {})
        job_title = job.get("job_title", "Unknown")
        company = job.get("company", "Unknown")
        print(f"\nTailoring [{i}/{len(match_results)}]: {job_title} at {company}...")

        try:
            tailored = engine.tailor(resume, match_result, job, build_docx=build_docx)
            tailored_resumes.append(tailored)

            # Save individual report
            report_dir = out_dir / "tailoring_reports"
            report_dir.mkdir(parents=True, exist_ok=True)

            # JSON report
            json_path = report_dir / f"{match_result.job_id}_report.json"
            write_tailoring_report(json_path, tailored.report.to_dict())

            # Markdown report
            md_path = report_dir / f"{match_result.job_id}_report.md"
            md = render_tailoring_report(tailored.report)
            md_path.write_text(md, encoding="utf-8")

            # Save tailored resume JSON
            resume_json_path = report_dir / f"{match_result.job_id}_resume.json"
            import json as _json
            resume_json_path.write_text(
                _json.dumps(tailored.resume_data, indent=2),
                encoding="utf-8",
            )

            print(f"  Changes: {tailored.report.total_changes}")
            if tailored.docx_path:
                print(f"  .docx: {tailored.docx_path}")

        except Exception as e:
            print(f"  Error: {e}")

    if not tailored_resumes:
        print("\nNo resumes were tailored successfully.")
        return

    # Save batch results
    batch_results = [tr.to_dict() for tr in tailored_resumes]
    results_path = out_dir / "tailoring_results.json"
    write_tailoring_results(results_path, batch_results)
    print(f"\nBatch results saved to {results_path}")

    # Save summary report
    summary_path = out_dir / "tailoring_summary.md"
    summary_md = render_tailoring_summary(tailored_resumes)
    summary_path.write_text(summary_md, encoding="utf-8")
    print(f"Summary report saved to {summary_path}")

    # Print console summary
    _print_tailoring_summary(tailored_resumes)


def _print_tailoring_summary(tailored_resumes: list) -> None:
    """Print a tailoring summary to console."""
    print("\n" + "=" * 60)
    print(f"TAILORING SUMMARY - {len(tailored_resumes)} Resumes Generated")
    print("=" * 60)

    total_changes = 0
    for i, tr in enumerate(tailored_resumes, 1):
        r = tr.report
        total_changes += r.total_changes
        print(f"\n{i}. {r.job_title} at {r.company}")
        print(f"   Match: {r.match_score:.0f}/100 ({r.match_grade})")
        print(f"   Changes: {r.total_changes}", end="")

        # Show category breakdown
        by_cat = r.changes_by_category
        if by_cat:
            parts = [f"{cat.value}={len(items)}" for cat, items in by_cat.items()]
            print(f" ({', '.join(parts)})")
        else:
            print()

        if tr.docx_path:
            print(f"   .docx: {tr.docx_path}")

    print(f"\nTotal changes across all resumes: {total_changes}")
    docx_count = sum(1 for tr in tailored_resumes if tr.docx_path)
    print(f"Generated .docx files: {docx_count}/{len(tailored_resumes)}")


# ============================================================================
# Full End-to-End Pipeline Command
# ============================================================================

def _cmd_run_all(args: argparse.Namespace) -> None:
    """Run the complete pipeline: fetch -> filter -> extract -> analyze ->
    match -> tailor -> compose -> reply (dry-run by default).

    This is the single-command equivalent of running every step manually.
    It is designed for e2e testing and production use:

    - ``--dry-run`` (the default): executes the entire pipeline but does
      **not** send any emails.  Drafts and previews are written to disk
      so you can inspect them before committing.
    - ``--send``: same as above, but actually sends the composed emails
      via Gmail at the end.

    Every intermediate artifact is persisted under ``--work-dir`` so you
    can re-run downstream stages without refetching.
    """
    import json as _json

    from .matching import JobAnalyzer, ResumeMatcher
    from .matching.report import render_match_summary
    from .tailoring import TailoringEngine
    from .tailoring.report import render_tailoring_report, render_tailoring_summary
    from .reply import ReplyComposer, GmailSender, QuestionnaireConfig
    from .reply.report import render_batch_preview, render_send_report

    work_dir = Path(args.work_dir)
    out_dir = Path(args.out_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    dry_run = not args.send
    llm_model = args.llm_model

    # ------------------------------------------------------------------
    # Computed paths
    # ------------------------------------------------------------------
    messages_path = work_dir / "messages.json"
    filtered_path = work_dir / "filtered.json"
    opportunities_path = work_dir / "opportunities.json"
    analyses_path = work_dir / "job_analyses.json"
    matches_dir = out_dir / "matches"
    match_results_path = matches_dir / "match_results.json"
    tailored_dir = out_dir / "tailored"
    replies_dir = out_dir / "replies"

    mode_label = "DRY RUN" if dry_run else "LIVE"
    print("=" * 64)
    print(f"  EMAIL OPPORTUNITY PIPELINE -- FULL RUN ({mode_label})")
    print("=" * 64)
    print()

    # ==================================================================
    # STAGE 1: Fetch
    # ==================================================================
    if args.messages:
        messages_list = list(read_messages(args.messages))
        print(f"[1/8 fetch]   Loaded {len(messages_list)} messages from {args.messages}")
        # Copy to work_dir for consistency
        write_messages(messages_path, messages_list)
    else:
        provider = _build_provider(args.provider)
        window = parse_window(args.window)
        print(f"[1/8 fetch]   Fetching from {args.provider} (window={args.window})...")
        messages_list = list(
            provider.fetch_messages(
                window=window,
                max_results=args.max_results,
                query=args.query,
                include_body=True,
            )
        )
        write_messages(messages_path, messages_list)
        print(f"[1/8 fetch]   Fetched {len(messages_list)} messages -> {messages_path}")

    if not messages_list:
        print("\nNo messages found. Pipeline complete (nothing to process).")
        return

    # ==================================================================
    # STAGE 2: Filter
    # ==================================================================
    print(f"[2/8 filter]  Filtering {len(messages_list)} messages...")
    pipeline = build_filter_pipeline(
        rules_path=args.rules or None,
        use_llm=args.llm_filter,
        llm_model=llm_model,
    )

    analytics = PipelineAnalytics()
    analytics.start()
    for msg in messages_list:
        analytics.record_email_fetch(msg)

    filter_results = filter_messages_with_outcomes(pipeline, messages_list)
    filtered_messages = []
    for email, outcome in filter_results:
        analytics.record_filter_result(email, outcome)
        if outcome.passed:
            filtered_messages.append(email)

    write_messages(filtered_path, filtered_messages)
    print(f"[2/8 filter]  {len(filtered_messages)}/{len(messages_list)} passed -> {filtered_path}")

    if not filtered_messages:
        analytics.finish()
        save_analytics(analytics, work_dir / "analytics.json")
        save_report(analytics, work_dir / "analytics_report.txt")
        print("\nNo messages passed filtering. Pipeline complete.")
        return

    # ==================================================================
    # STAGE 3: Extract
    # ==================================================================
    print(f"[3/8 extract] Extracting opportunities...")
    opportunities = extract_opportunities(
        filtered_messages,
        use_llm=args.llm_extract,
        llm_model=llm_model,
    )
    for opp in opportunities:
        analytics.record_extraction(opp)

    write_opportunities(opportunities_path, opportunities)
    analytics.finish()
    save_analytics(analytics, work_dir / "analytics.json")
    save_report(analytics, work_dir / "analytics_report.txt")

    # Render markdown
    markdown_dir = out_dir / "markdown"
    render_markdown_files(opportunities, markdown_dir)
    print(f"[3/8 extract] {len(opportunities)} opportunities -> {opportunities_path}")

    if not opportunities:
        print("\nNo opportunities extracted. Pipeline complete.")
        return

    # ==================================================================
    # STAGE 4: Analyze (LLM)
    # ==================================================================
    print(f"[4/8 analyze] Analyzing {len(opportunities)} job(s) with LLM...")
    analyzer = JobAnalyzer(model=llm_model)
    analyses = []
    for i, opp in enumerate(opportunities, 1):
        title = opp.get("job_title", "Unknown")
        company = opp.get("company", "Unknown")
        print(f"              [{i}/{len(opportunities)}] {title} at {company}")
        analysis = analyzer.analyze(opp)
        analyses.append(analysis)

    write_job_analyses(analyses_path, analyses)
    print(f"[4/8 analyze] {len(analyses)} analyses -> {analyses_path}")

    # ==================================================================
    # STAGE 5: Match resume (LLM)
    # ==================================================================
    resume = read_resume(args.resume)
    print(f"[5/8 match]   Matching resume ({resume.personal.name}) against {len(opportunities)} jobs...")

    matcher = ResumeMatcher(model=llm_model)
    match_results = matcher.match_batch(resume, opportunities, analyses)

    matches_dir.mkdir(parents=True, exist_ok=True)
    write_match_results(match_results_path, match_results, resume_id=resume.source_file)

    summary_md = render_match_summary(match_results, opportunities)
    (matches_dir / "match_summary.md").write_text(summary_md, encoding="utf-8")
    print(f"[5/8 match]   {len(match_results)} match results -> {match_results_path}")

    # Apply filters for downstream stages
    selected = list(match_results)  # already sorted by score desc
    if args.min_score:
        selected = [r for r in selected if r.overall_score >= args.min_score]
    if args.recommendation:
        recs = set(args.recommendation.split(","))
        selected = [r for r in selected if r.recommendation in recs]
    if args.top:
        selected = selected[: args.top]

    if not selected:
        print("\nNo match results survived filtering. Pipeline complete.")
        _print_run_all_summary(messages_list, filtered_messages, opportunities,
                               match_results, [], [], [], dry_run)
        return

    print(f"              Selected {len(selected)} job(s) for tailoring/reply "
          f"(min_score={args.min_score}, rec={args.recommendation}, top={args.top})")

    # Build jobs map for downstream
    jobs_map: dict = {}
    for opp in opportunities:
        msg_id = opp.get("source_email", {}).get("message_id")
        if msg_id:
            jobs_map[msg_id] = opp

    # ==================================================================
    # STAGE 6: Tailor resumes
    # ==================================================================
    tailored_dir.mkdir(parents=True, exist_ok=True)
    engine = TailoringEngine(output_dir=tailored_dir)
    build_docx = not args.no_docx
    tailored_resumes = []

    print(f"[6/8 tailor]  Tailoring resume for {len(selected)} job(s)...")
    for i, mr in enumerate(selected, 1):
        job = jobs_map.get(mr.job_id, {})
        job_title = job.get("job_title", "Unknown")
        company = job.get("company", "Unknown")
        print(f"              [{i}/{len(selected)}] {job_title} at {company}")
        try:
            tailored = engine.tailor(resume, mr, job, build_docx=build_docx)
            tailored_resumes.append(tailored)

            report_dir = tailored_dir / "tailoring_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            write_tailoring_report(
                report_dir / f"{mr.job_id}_report.json",
                tailored.report.to_dict(),
            )
            md = render_tailoring_report(tailored.report)
            (report_dir / f"{mr.job_id}_report.md").write_text(md, encoding="utf-8")
            (report_dir / f"{mr.job_id}_resume.json").write_text(
                _json.dumps(tailored.resume_data, indent=2), encoding="utf-8"
            )
        except Exception as e:
            print(f"              Error tailoring: {e}")

    if tailored_resumes:
        batch = [tr.to_dict() for tr in tailored_resumes]
        write_tailoring_results(tailored_dir / "tailoring_results.json", batch)
        summary = render_tailoring_summary(tailored_resumes)
        (tailored_dir / "tailoring_summary.md").write_text(summary, encoding="utf-8")

    print(f"[6/8 tailor]  {len(tailored_resumes)} tailored resumes -> {tailored_dir}")

    # ==================================================================
    # STAGE 7: Compose reply emails
    # ==================================================================
    if args.questionnaire:
        questionnaire = read_questionnaire(args.questionnaire)
        print(f"[7/8 compose] Loaded questionnaire from {args.questionnaire}")
    else:
        questionnaire = QuestionnaireConfig()
        print("[7/8 compose] Using default questionnaire configuration")

    # Build attachment map from tailored .docx files
    attachment_map: dict = {}
    for mr in selected:
        job = jobs_map.get(mr.job_id, {})
        company = job.get("company", "Unknown")
        title = job.get("job_title", "Unknown")
        safe_company = "".join(c for c in company if c.isalnum() or c in " _-").strip()
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
        docx_name = f"tailored_resume_{safe_company}_{safe_title}.docx".replace(" ", "_")
        docx_path = tailored_dir / docx_name
        if docx_path.exists():
            attachment_map[mr.job_id] = [str(docx_path)]

    composer = ReplyComposer(model=llm_model)
    print(f"[7/8 compose] Composing {len(selected)} reply email(s) "
          f"(LLM: {'yes' if composer.llm_available else 'template fallback'})...")

    jobs_list = [jobs_map.get(mr.job_id, {}) for mr in selected]
    drafts = composer.compose_batch(
        resume=resume,
        match_results=selected,
        jobs=jobs_list,
        questionnaire=questionnaire,
        attachment_map=attachment_map,
    )

    replies_dir.mkdir(parents=True, exist_ok=True)
    write_drafts(replies_dir / "drafts.json", drafts)
    preview_md = render_batch_preview(drafts)
    (replies_dir / "drafts_preview.md").write_text(preview_md, encoding="utf-8")
    print(f"[7/8 compose] {len(drafts)} drafts -> {replies_dir / 'drafts.json'}")

    # ==================================================================
    # STAGE 8: Reply (dry-run or send)
    # ==================================================================
    reply_label = "DRY RUN" if dry_run else "SENDING"
    print(f"[8/8 reply]   {reply_label} {len(drafts)} email(s)...")

    # Recipient override / audit addresses
    override_to = getattr(args, "override_to", None)
    cc = getattr(args, "cc", None)
    bcc = getattr(args, "bcc", None)

    if override_to:
        print(f"              Recipient override: all emails -> {override_to}")
    if cc:
        print(f"              CC: {', '.join(cc)}")
    if bcc:
        print(f"              BCC: {', '.join(bcc)}")

    sender = GmailSender()
    reply_results = sender.send_batch(
        drafts,
        dry_run=dry_run,
        override_to=override_to,
        cc=cc,
        bcc=bcc,
    )

    write_reply_results(replies_dir / "reply_results.json", reply_results)
    report = render_send_report(reply_results)
    (replies_dir / "reply_report.md").write_text(report, encoding="utf-8")
    print(f"[8/8 reply]   Results -> {replies_dir / 'reply_results.json'}")

    # ==================================================================
    # Final summary
    # ==================================================================
    _print_run_all_summary(
        messages_list, filtered_messages, opportunities,
        match_results, selected, tailored_resumes, reply_results,
        dry_run,
    )


def _print_run_all_summary(
    messages, filtered, opportunities, all_matches,
    selected_matches, tailored_resumes, reply_results,
    dry_run,
) -> None:
    """Print a consolidated end-of-pipeline summary."""
    from .reply.models import ReplyStatus

    print()
    print("=" * 64)
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"  PIPELINE COMPLETE ({mode})")
    print("=" * 64)
    print()

    print(f"  Fetched messages:     {len(messages)}")
    print(f"  Passed filter:        {len(filtered)}")
    print(f"  Opportunities:        {len(opportunities)}")
    print(f"  Total matches:        {len(all_matches)}")
    print(f"  Selected for reply:   {len(selected_matches)}")
    print(f"  Tailored resumes:     {len(tailored_resumes)}")

    if reply_results:
        sent = sum(1 for r in reply_results if r.status == ReplyStatus.SENT)
        previewed = sum(1 for r in reply_results if r.status == ReplyStatus.DRY_RUN)
        failed = sum(1 for r in reply_results if r.status == ReplyStatus.FAILED)
        print(f"  Emails sent:          {sent}")
        print(f"  Emails previewed:     {previewed}")
        print(f"  Emails failed:        {failed}")

    # Top matches
    if all_matches:
        print()
        print("  Top matches:")
        for i, r in enumerate(all_matches[:5], 1):
            print(f"    {i}. [{r.overall_score:.0f}] {r.match_grade} / {r.recommendation} "
                  f"(job_id={r.job_id[:20]}...)")

    print()
    if dry_run:
        print("  This was a DRY RUN.  No emails were sent.")
        print("  Review drafts in the replies/ directory, then re-run with --send.")
    else:
        print("  Emails have been sent.  Check reply_report.md for details.")
    print()


# ============================================================================
# Recruiter Reply Commands
# ============================================================================

def _cmd_compose(args: argparse.Namespace) -> None:
    """Compose tailored recruiter reply emails using LLM."""
    from .reply import ReplyComposer, QuestionnaireConfig
    from .reply.report import render_batch_preview, render_draft_preview

    # Load inputs
    resume = read_resume(args.resume)
    print(f"Loaded resume for: {resume.personal.name}")

    match_results = read_match_results(args.match_results)
    print(f"Loaded {len(match_results)} match results")

    # Load opportunities for job context
    opportunities = []
    jobs_map: dict = {}
    if args.opportunities:
        opportunities = read_opportunities(args.opportunities)
        for opp in opportunities:
            msg_id = opp.get("source_email", {}).get("message_id")
            if msg_id:
                jobs_map[msg_id] = opp
        print(f"Loaded {len(opportunities)} opportunities for context")

    # Load questionnaire
    if args.questionnaire:
        questionnaire = read_questionnaire(args.questionnaire)
        print(f"Loaded questionnaire from {args.questionnaire}")
    else:
        questionnaire = QuestionnaireConfig()
        print("Using default questionnaire configuration")

    # Filter match results
    if args.min_score:
        match_results = [r for r in match_results if r.overall_score >= args.min_score]
        print(f"After min-score filter: {len(match_results)} results")

    if args.recommendation:
        recs = set(args.recommendation.split(","))
        match_results = [r for r in match_results if r.recommendation in recs]
        print(f"After recommendation filter: {len(match_results)} results")

    if args.top:
        match_results.sort(key=lambda r: r.overall_score, reverse=True)
        match_results = match_results[:args.top]

    if not match_results:
        print("No match results to compose replies for.")
        return

    # Build attachment map from tailoring output
    attachment_map: dict = {}
    if args.tailored_dir:
        tailored_dir = Path(args.tailored_dir)
        if tailored_dir.exists():
            for mr in match_results:
                job = jobs_map.get(mr.job_id, {})
                company = job.get("company", "Unknown")
                title = job.get("job_title", "Unknown")
                safe_company = "".join(
                    c for c in company if c.isalnum() or c in " _-"
                ).strip()
                safe_title = "".join(
                    c for c in title if c.isalnum() or c in " _-"
                ).strip()
                docx_name = (
                    f"tailored_resume_{safe_company}_{safe_title}.docx".replace(
                        " ", "_"
                    )
                )
                docx_path = tailored_dir / docx_name
                if docx_path.exists():
                    attachment_map[mr.job_id] = [str(docx_path)]
            print(f"Found {len(attachment_map)} tailored resume attachments")

    # Compose
    composer = ReplyComposer(model=args.llm_model)
    print(f"\nComposing {len(match_results)} reply emails "
          f"(LLM: {'yes' if composer.llm_available else 'no, using templates'})...")

    jobs_list = [jobs_map.get(mr.job_id, {}) for mr in match_results]
    drafts = composer.compose_batch(
        resume=resume,
        match_results=match_results,
        jobs=jobs_list,
        questionnaire=questionnaire,
        attachment_map=attachment_map,
    )

    print(f"Composed {len(drafts)} drafts")

    # Output
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save drafts JSON
    drafts_path = out_dir / "drafts.json"
    write_drafts(drafts_path, drafts)
    print(f"\nDrafts saved to {drafts_path}")

    # Save preview report
    preview_path = out_dir / "drafts_preview.md"
    preview_md = render_batch_preview(drafts)
    preview_path.write_text(preview_md, encoding="utf-8")
    print(f"Preview report saved to {preview_path}")

    # Save individual previews
    previews_dir = out_dir / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)
    for draft in drafts:
        md = render_draft_preview(draft)
        safe_id = draft.job_id.replace("/", "_").replace("\\", "_")[:60]
        preview_file = previews_dir / f"{safe_id}_preview.md"
        preview_file.write_text(md, encoding="utf-8")
    print(f"Individual previews saved to {previews_dir}")

    # Console summary
    _print_compose_summary(drafts)


def _print_compose_summary(drafts: list) -> None:
    """Print a compose summary to console."""
    print("\n" + "=" * 60)
    print(f"COMPOSE SUMMARY - {len(drafts)} Drafts Generated")
    print("=" * 60)

    for i, d in enumerate(drafts, 1):
        score = f"{d.match_score:.0f}" if d.match_score is not None else "N/A"
        att = f" (+{len(d.attachment_paths)} attachment(s))" if d.attachment_paths else ""
        print(f"\n{i}. {d.job_title} at {d.company}")
        print(f"   To: {d.to}")
        print(f"   Subject: {d.subject}")
        print(f"   Match: {score}/100{att}")

    with_attachments = sum(1 for d in drafts if d.attachment_paths)
    print(f"\nDrafts with attachments: {with_attachments}/{len(drafts)}")
    print("\nReview drafts, then run 'reply' to send (or use --dry-run).")


def _cmd_reply(args: argparse.Namespace) -> None:
    """Send (or dry-run) composed recruiter reply emails."""
    from .reply import GmailSender
    from .reply.report import render_send_report

    # Load drafts
    drafts = read_drafts(args.drafts)
    print(f"Loaded {len(drafts)} email drafts from {args.drafts}")

    if not drafts:
        print("No drafts to send.")
        return

    # Filter by index if requested
    if args.index is not None:
        if args.index < 0 or args.index >= len(drafts):
            print(f"Error: index {args.index} out of range (0-{len(drafts)-1})")
            return
        drafts = [drafts[args.index]]
        print(f"Selected draft {args.index}: {drafts[0].job_title} at {drafts[0].company}")

    dry_run = args.dry_run
    mode_label = "DRY RUN" if dry_run else "SENDING"
    print(f"\n--- {mode_label}: {len(drafts)} email(s) ---\n")

    # Parse recipient overrides
    override_to = getattr(args, "override_to", None)
    cc = getattr(args, "cc", None)
    bcc = getattr(args, "bcc", None)

    if override_to:
        print(f"  Recipient override: all emails -> {override_to}")
    if cc:
        print(f"  CC: {', '.join(cc)}")
    if bcc:
        print(f"  BCC: {', '.join(bcc)}")

    # Send / dry-run
    sender = GmailSender()
    results = sender.send_batch(
        drafts,
        dry_run=dry_run,
        override_to=override_to,
        cc=cc,
        bcc=bcc,
    )

    # Output
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save results JSON
    results_path = out_dir / "reply_results.json"
    write_reply_results(results_path, results)
    print(f"\nResults saved to {results_path}")

    # Save report
    report_md = render_send_report(results)
    report_path = out_dir / "reply_report.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"Report saved to {report_path}")

    # Console summary
    _print_reply_summary(results, dry_run)


def _print_reply_summary(results: list, dry_run: bool) -> None:
    """Print a reply summary to console."""
    from .reply.models import ReplyStatus

    print("\n" + "=" * 60)
    mode = "DRY RUN" if dry_run else "SEND"
    print(f"REPLY {mode} SUMMARY - {len(results)} email(s)")
    print("=" * 60)

    for i, r in enumerate(results, 1):
        d = r.draft
        status_icon = {
            ReplyStatus.SENT: "[SENT]",
            ReplyStatus.DRY_RUN: "[PREVIEW]",
            ReplyStatus.FAILED: "[FAILED]",
            ReplyStatus.DRAFT: "[DRAFT]",
        }.get(r.status, "[?]")

        print(f"\n{i}. {status_icon} {d.job_title} at {d.company}")
        print(f"   To: {d.to}")
        if d.original_to:
            print(f"   Original To: {d.original_to} (overridden)")
        if d.cc:
            print(f"   CC: {', '.join(d.cc)}")
        if d.bcc:
            print(f"   BCC: {', '.join(d.bcc)}")
        if r.gmail_message_id:
            print(f"   Gmail ID: {r.gmail_message_id}")
        if r.error:
            print(f"   Error: {r.error}")

    sent = sum(1 for r in results if r.status == ReplyStatus.SENT)
    failed = sum(1 for r in results if r.status == ReplyStatus.FAILED)
    previewed = sum(1 for r in results if r.status == ReplyStatus.DRY_RUN)

    print(f"\nSent: {sent} | Previewed: {previewed} | Failed: {failed}")

    if dry_run:
        print("\nThis was a dry run. No emails were sent.")
        print("Remove --dry-run to actually send the emails.")


# ============================================================================
# Application Tracking Commands
# ============================================================================

def _cmd_track(args: argparse.Namespace) -> None:
    """Initialise application tracking from correlation data and/or display
    the current tracking state."""
    from .tracking import (
        ApplicationTracker,
        render_tracking_report,
        render_application_card,
    )

    tracker = ApplicationTracker()

    # Load existing tracking data (idempotent merge)
    tracking_file = args.tracking_file
    if not tracking_file:
        out_path = Path(args.out)
        candidate = out_path / "tracking.json"
        if candidate.exists():
            tracking_file = str(candidate)

    if tracking_file and Path(tracking_file).exists():
        existing_apps, _ = read_tracking(tracking_file)
        tracker.load_existing(existing_apps)
        print(f"Loaded {len(existing_apps)} existing tracked applications from {tracking_file}")

    # Discover or use explicit correlation file
    correlation_path = args.correlation
    if not correlation_path:
        out_dir = Path(args.out_dir) if args.out_dir else None
        if out_dir and (out_dir / "correlation" / "correlation.json").exists():
            correlation_path = str(out_dir / "correlation" / "correlation.json")

    if correlation_path and Path(correlation_path).exists():
        correlated, _ = read_correlation(correlation_path)
        from .correlation.models import OpportunityStage

        min_stage_str = args.min_stage or "replied"
        try:
            min_stage = OpportunityStage(min_stage_str)
        except ValueError:
            min_stage = OpportunityStage.REPLIED

        new_count = tracker.init_from_correlation(correlated, min_stage=min_stage)
        print(f"Initialised {new_count} new application(s) from correlation data")
    else:
        if not tracking_file:
            print("No correlation data or existing tracking file found.")
            print("Run 'correlate' first, or provide --correlation / --tracking-file.")
            return

    all_apps = tracker.get_all()
    if not all_apps:
        print("No applications to track.")
        return

    # Filter by status if requested
    if args.status:
        from .tracking.models import ApplicationStatus
        statuses = set(args.status.split(","))
        all_apps = [a for a in all_apps if a.status.value in statuses]
        print(f"After status filter: {len(all_apps)} applications")

    summary = tracker.build_summary()

    # Output
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = out_path / "tracking.json"
    write_tracking(json_path, tracker.get_all(), summary)
    print(f"\nTracking data saved to {json_path}")

    # Summary report
    summary_path = out_path / "tracking_summary.md"
    summary_md = render_tracking_report(summary, all_apps, include_cards=False)
    summary_path.write_text(summary_md, encoding="utf-8")
    print(f"Summary report saved to {summary_path}")

    # Individual cards
    if args.individual_cards:
        cards_dir = out_path / "application_cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        for app in all_apps:
            card_md = render_application_card(app)
            safe_id = app.job_id.replace("/", "_").replace("\\", "_")[:60]
            card_path = cards_dir / f"{safe_id}.md"
            card_path.write_text(card_md, encoding="utf-8")
        print(f"Individual cards saved to {cards_dir}")

    # Full report
    if args.full_report:
        full_path = out_path / "tracking_full_report.md"
        full_md = render_tracking_report(summary, all_apps, include_cards=True)
        full_path.write_text(full_md, encoding="utf-8")
        print(f"Full report saved to {full_path}")

    # Console summary
    _print_tracking_summary(summary, all_apps)


def _cmd_track_update(args: argparse.Namespace) -> None:
    """Update status, notes, interviews, or offers for a tracked application."""
    from .tracking import ApplicationTracker
    from .tracking.models import (
        ApplicationStatus,
        FinalOutcome,
        InterviewRecord,
        InterviewType,
        OfferDetails,
    )
    from .tracking.report import render_tracking_report

    # Load existing tracking data
    tracking_file = Path(args.tracking_file)
    if not tracking_file.exists():
        print(f"Error: tracking file not found: {tracking_file}")
        return

    existing_apps, _ = read_tracking(tracking_file)
    tracker = ApplicationTracker()
    tracker.load_existing(existing_apps)
    print(f"Loaded {len(existing_apps)} tracked applications")

    job_id = args.job_id
    action = args.action

    try:
        if action == "status":
            if not args.status:
                print("Error: --status is required for action=status")
                return
            new_status = ApplicationStatus(args.status)
            tracker.update_status(job_id, new_status, note=args.note)
            print(f"Updated {job_id} -> {new_status.value}")

        elif action == "outcome":
            if not args.outcome:
                print("Error: --outcome is required for action=outcome")
                return
            outcome = FinalOutcome(args.outcome)
            tracker.set_outcome(job_id, outcome, note=args.note)
            print(f"Set outcome for {job_id} -> {outcome.value}")

        elif action == "interview":
            interview_type_str = args.interview_type or "other"
            try:
                interview_type = InterviewType(interview_type_str)
            except ValueError:
                interview_type = InterviewType.OTHER

            record = InterviewRecord(
                interview_type=interview_type,
                scheduled_at=args.scheduled_at,
                completed=args.completed,
                interviewer_name=args.interviewer,
                notes=args.note,
            )
            tracker.add_interview(job_id, record)
            print(f"Added interview for {job_id}: {interview_type.value}")

        elif action == "offer":
            offer = OfferDetails(
                salary=args.salary,
                equity=args.equity,
                bonus=args.bonus,
                start_date=args.start_date,
                notes=args.note,
            )
            tracker.set_offer(job_id, offer)
            print(f"Set offer for {job_id}")

        elif action == "note":
            if not args.note:
                print("Error: --note is required for action=note")
                return
            tracker.add_note(job_id, args.note)
            print(f"Added note to {job_id}")

        else:
            print(f"Error: unknown action '{action}'")
            return

    except KeyError as e:
        print(f"Error: {e}")
        return
    except ValueError as e:
        print(f"Error: invalid value: {e}")
        return

    # Write back
    summary = tracker.build_summary()
    out_dir = Path(args.out) if args.out else tracking_file.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    write_tracking(out_dir / "tracking.json", tracker.get_all(), summary)
    print(f"Tracking data saved to {out_dir / 'tracking.json'}")

    # Regenerate summary report
    summary_md = render_tracking_report(summary, tracker.get_all(), include_cards=False)
    (out_dir / "tracking_summary.md").write_text(summary_md, encoding="utf-8")
    print(f"Summary report updated at {out_dir / 'tracking_summary.md'}")

    # Show updated application
    app = tracker.get_application(job_id)
    if app:
        print(f"\nUpdated: {app.job_title} at {app.company}")
        print(f"  Status: {app.status.value}")
        if app.final_outcome:
            print(f"  Outcome: {app.final_outcome.value}")
        print(f"  Interviews: {len(app.interviews)}")
        print(f"  Offer: {'Yes' if app.offer else 'No'}")


def _print_tracking_summary(
    summary: "TrackingSummary",
    applications: list,
) -> None:
    """Print a brief tracking summary to console."""
    print()
    print("=" * 64)
    print("  APPLICATION TRACKING SUMMARY")
    print("=" * 64)
    print()

    print(f"  Total Tracked:        {summary.total_tracked}")
    print(f"  Active:               {summary.active_count}")
    print(f"  Total Interviews:     {summary.total_interviews}")
    print(f"  Offers Received:      {summary.offers_received}")

    if summary.avg_match_score > 0:
        print(f"  Avg Match Score:      {summary.avg_match_score:.1f}")

    # Status breakdown
    if summary.by_status:
        print()
        print("  By Status:")
        for status in ["applied", "interviewing", "offered", "closed"]:
            count = summary.by_status.get(status, 0)
            if count:
                print(f"    {status.title():16s} {count}")

    # Outcome breakdown
    if summary.by_outcome:
        print()
        print("  Outcomes:")
        for outcome in ["accepted", "declined", "rejected", "withdrawn", "ghosted"]:
            count = summary.by_outcome.get(outcome, 0)
            if count:
                print(f"    {outcome.title():16s} {count}")

    # Top applications
    active = [a for a in applications if a.is_active][:5]
    if active:
        print()
        print("  Active Applications:")
        for i, a in enumerate(active, 1):
            score = f"{a.match_score:.0f}" if a.match_score is not None else "--"
            company = a.company[:25] if a.company else "Unknown"
            title = a.job_title[:30] if a.job_title else "Unknown"
            print(f"    {i}. [{score}] {a.status.value.title():14s} {title} at {company}")

    print()


# ============================================================================
# Job Opportunity Correlation Command
# ============================================================================

def _cmd_ui(args: argparse.Namespace) -> None:
    """Launch the Streamlit web dashboard."""
    try:
        import streamlit.web.cli as stcli
    except ImportError:
        print(
            "Streamlit is not installed.  Install the 'ui' extra:\n"
            "  uv sync --all-extras       # recommended (uv)\n"
            "  pip install -e '.[ui]'     # or with pip"
        )
        return

    import sys
    from pathlib import Path as _Path

    app_path = str(
        _Path(__file__).resolve().parent / "ui" / "app.py"
    )

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
        f"--server.port={args.port}",
        "--",
    ]
    stcli.main()


def _cmd_correlate(args: argparse.Namespace) -> None:
    """Correlate job opportunities with emails, resumes, and reply status.

    Builds a unified view linking every pipeline artifact for each opportunity.
    Supports auto-discovery of artifacts from standard work-dir / out-dir paths.
    """
    from .correlation import (
        OpportunityCorrelator,
        render_correlation_report,
        render_opportunity_card,
    )

    correlator = OpportunityCorrelator()

    work_dir = Path(args.work_dir) if args.work_dir else None
    out_dir = Path(args.out_dir) if args.out_dir else None

    # ------------------------------------------------------------------
    # Load artifacts (explicit paths take priority over auto-discovery)
    # ------------------------------------------------------------------

    # Messages
    messages_path = args.messages
    if not messages_path and work_dir and (work_dir / "messages.json").exists():
        messages_path = str(work_dir / "messages.json")
    if messages_path:
        messages = list(read_messages(messages_path))
        correlator.add_messages(messages)
        print(f"Loaded {len(messages)} messages from {messages_path}")

    # Opportunities
    opportunities_path = args.opportunities
    if not opportunities_path and work_dir and (work_dir / "opportunities.json").exists():
        opportunities_path = str(work_dir / "opportunities.json")
    if opportunities_path:
        opportunities = read_opportunities(opportunities_path)
        correlator.add_opportunities(opportunities)
        print(f"Loaded {len(opportunities)} opportunities from {opportunities_path}")

    # Match results
    match_path = args.match_results
    if not match_path and out_dir and (out_dir / "matches" / "match_results.json").exists():
        match_path = str(out_dir / "matches" / "match_results.json")
    if match_path:
        match_results = read_match_results(match_path)
        correlator.add_match_results(match_results)
        print(f"Loaded {len(match_results)} match results from {match_path}")

    # Tailoring results
    tailored_dir_path = args.tailored_dir
    if not tailored_dir_path and out_dir and (out_dir / "tailored").exists():
        tailored_dir_path = str(out_dir / "tailored")
    if tailored_dir_path:
        tailored_dir = Path(tailored_dir_path)
        results_file = tailored_dir / "tailoring_results.json"
        if results_file.exists():
            tailoring_results = read_tailoring_results(results_file)
            correlator.add_tailoring_results(tailoring_results, tailored_dir)
            print(f"Loaded {len(tailoring_results)} tailoring results from {results_file}")

    # Drafts
    drafts_path = args.drafts
    if not drafts_path and out_dir and (out_dir / "replies" / "drafts.json").exists():
        drafts_path = str(out_dir / "replies" / "drafts.json")
    if drafts_path:
        drafts = read_drafts(drafts_path)
        correlator.add_drafts(drafts)
        print(f"Loaded {len(drafts)} drafts from {drafts_path}")

    # Reply results
    reply_path = args.reply_results
    if not reply_path and out_dir and (out_dir / "replies" / "reply_results.json").exists():
        reply_path = str(out_dir / "replies" / "reply_results.json")
    if reply_path:
        reply_results = read_reply_results(reply_path)
        correlator.add_reply_results(reply_results)
        print(f"Loaded {len(reply_results)} reply results from {reply_path}")

    # ------------------------------------------------------------------
    # Correlate
    # ------------------------------------------------------------------

    print("\nCorrelating artifacts...")
    correlated = correlator.correlate()

    if not correlated:
        print("No opportunities found to correlate.")
        return

    # ------------------------------------------------------------------
    # Filter
    # ------------------------------------------------------------------

    if args.min_score is not None:
        correlated = [
            c for c in correlated
            if c.match and c.match.overall_score >= args.min_score
        ]
        print(f"After min-score filter ({args.min_score}): {len(correlated)}")

    if args.recommendation:
        recs = set(args.recommendation.split(","))
        correlated = [
            c for c in correlated
            if c.match and c.match.recommendation in recs
        ]
        print(f"After recommendation filter: {len(correlated)}")

    if args.stage:
        stages = set(args.stage.split(","))
        correlated = [c for c in correlated if c.stage.value in stages]
        print(f"After stage filter: {len(correlated)}")

    if args.top:
        correlated = correlated[:args.top]

    if not correlated:
        print("No opportunities remain after filtering.")
        return

    # ------------------------------------------------------------------
    # Load optional resume name for the summary
    # ------------------------------------------------------------------

    resume_name = None
    resume_file = None
    if args.resume:
        try:
            resume = read_resume(args.resume)
            resume_name = resume.personal.name
            resume_file = args.resume
        except Exception:
            resume_file = args.resume

    # ------------------------------------------------------------------
    # Build summary
    # ------------------------------------------------------------------

    summary = correlator.build_summary(
        correlated,
        resume_name=resume_name,
        resume_file=resume_file,
    )

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = out_path / "correlation.json"
    write_correlation(json_path, correlated, summary)
    print(f"\nCorrelation data saved to {json_path}")

    # Summary report
    summary_path = out_path / "correlation_summary.md"
    summary_md = render_correlation_report(summary, correlated, include_cards=False)
    summary_path.write_text(summary_md, encoding="utf-8")
    print(f"Summary report saved to {summary_path}")

    # Individual cards
    if args.individual_cards:
        cards_dir = out_path / "opportunity_cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        for c in correlated:
            card_md = render_opportunity_card(c)
            safe_id = c.job_id.replace("/", "_").replace("\\", "_")[:60]
            card_path = cards_dir / f"{safe_id}.md"
            card_path.write_text(card_md, encoding="utf-8")
        print(f"Individual cards saved to {cards_dir}")

    # Full report (summary + cards in one file)
    if args.full_report:
        full_path = out_path / "correlation_full_report.md"
        full_md = render_correlation_report(summary, correlated, include_cards=True)
        full_path.write_text(full_md, encoding="utf-8")
        print(f"Full report saved to {full_path}")

    # ------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------

    _print_correlation_summary(summary, correlated)


def _print_correlation_summary(
    summary: "CorrelationSummary",
    correlated: list,
) -> None:
    """Print a brief correlation summary to console."""
    print()
    print("=" * 64)
    print("  JOB OPPORTUNITY CORRELATION SUMMARY")
    print("=" * 64)
    print()

    if summary.resume_name:
        print(f"  Candidate:            {summary.resume_name}")
    print(f"  Total Opportunities:  {summary.total_opportunities}")
    print(f"  Matched:              {summary.matched_count}")
    print(f"  Tailored Resumes:     {summary.tailored_count}")

    replies_total = (
        summary.replies_sent + summary.replies_dry_run
        + summary.replies_drafted + summary.replies_failed
    )
    print(f"  Replies:              {replies_total}")
    print(f"  Pipeline Complete:    {summary.pipeline_complete_count}")

    if summary.matched_count > 0:
        print()
        print(f"  Avg Match Score:      {summary.avg_match_score:.1f} / 100")
        print(f"  Best Score:           {summary.max_match_score:.1f} / 100")

    # Top matches
    top = [c for c in correlated if c.match][:5]
    if top:
        print()
        print("  Top Matches:")
        for i, c in enumerate(top, 1):
            score = f"{c.match.overall_score:.0f}" if c.match else "--"
            grade = c.match.match_grade if c.match else "--"
            company = c.company[:25] if c.company else "Unknown"
            title = c.job_title[:30] if c.job_title else "Unknown"
            print(f"    {i}. [{score}] {grade.title():12s} {title} at {company}")

    # Stage breakdown
    if summary.by_stage:
        print()
        print("  Pipeline Stages:")
        for stage, count in sorted(summary.by_stage.items()):
            print(f"    {stage.title():12s} {count}")

    print()


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

    # =========================================================================
    # Full End-to-End Pipeline Command
    # =========================================================================

    run_all = subparsers.add_parser(
        "run-all",
        help="Full e2e pipeline: fetch -> filter -> extract -> analyze -> "
             "match -> tailor -> compose -> reply (dry-run by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Run the complete pipeline from email fetch through recruiter reply.\n"
            "\n"
            "By default this executes in DRY-RUN mode: the entire pipeline runs\n"
            "but no emails are actually sent.  Drafts and previews are written\n"
            "to disk so you can inspect them.  Pass --send to transmit for real.\n"
            "\n"
            "Quickstart (dry-run):\n"
            "  email-pipeline run-all \\\n"
            "    --resume examples/sample_resume.json \\\n"
            "    --questionnaire examples/questionnaire.json \\\n"
            "    --provider gmail --window 2d \\\n"
            "    --work-dir data --out-dir output\n"
            "\n"
            "Quickstart (send for real):\n"
            "  email-pipeline run-all \\\n"
            "    --resume examples/sample_resume.json \\\n"
            "    --questionnaire examples/questionnaire.json \\\n"
            "    --provider gmail --window 2d \\\n"
            "    --work-dir data --out-dir output --send\n"
        ),
    )

    # -- Input sources --
    run_all_input = run_all.add_argument_group("input sources")
    run_all_input.add_argument(
        "--resume", required=True,
        help="Path to the candidate resume file (JSON or Markdown)"
    )
    run_all_input.add_argument(
        "--questionnaire",
        help="Path to questionnaire config JSON (salary, location, questions); "
             "see examples/questionnaire.json"
    )
    run_all_input.add_argument(
        "--messages",
        help="Skip fetching and use an existing messages JSON file instead"
    )

    # -- Fetch options --
    run_all_fetch = run_all.add_argument_group("fetch options (ignored when --messages is set)")
    run_all_fetch.add_argument("--provider", default="gmail", choices=["gmail"])
    run_all_fetch.add_argument("--window", default=DEFAULT_WINDOW,
                               help="Time window like 30m, 6h, 2d (default: %(default)s)")
    run_all_fetch.add_argument("--query", default="", help="Provider-specific query string")
    run_all_fetch.add_argument("--max-results", type=int, default=None,
                               help="Cap the number of fetched messages")

    # -- Filter / extract options --
    run_all_filter = run_all.add_argument_group("filter and extraction")
    run_all_filter.add_argument("--rules", default="",
                                help="Path to filter rules JSON")
    run_all_filter.add_argument("--llm-filter", action="store_true",
                                help="Enable LLM filter stage")
    run_all_filter.add_argument("--llm-extract", action="store_true",
                                help="Enable LLM extraction")

    # -- Match / tailor / reply filtering --
    run_all_select = run_all.add_argument_group("match selection (which jobs to tailor + reply to)")
    run_all_select.add_argument("--min-score", type=float,
                                help="Only tailor/reply for jobs with at least this match score")
    run_all_select.add_argument("--recommendation",
                                help="Comma-separated recommendations (e.g. strong_apply,apply)")
    run_all_select.add_argument("--top", type=int,
                                help="Limit to top N matches by score")

    # -- Output --
    run_all_output = run_all.add_argument_group("output directories")
    run_all_output.add_argument("--work-dir", default="data",
                                help="Where JSON artifacts are written (default: %(default)s)")
    run_all_output.add_argument("--out-dir", default="output",
                                help="Where reports, tailored resumes, and replies go (default: %(default)s)")

    # -- Behaviour --
    run_all_behaviour = run_all.add_argument_group("behaviour")
    run_all_behaviour.add_argument("--send", action="store_true",
                                   help="Actually send reply emails (default is dry-run)")
    run_all_behaviour.add_argument("--no-docx", action="store_true",
                                   help="Skip .docx generation")
    run_all_behaviour.add_argument("--llm-model", default="gpt-4o-mini",
                                   help="LLM model for all LLM stages (default: %(default)s)")

    # -- Recipient override & audit --
    run_all_recipient = run_all.add_argument_group("recipient override and audit")
    run_all_recipient.add_argument(
        "--override-to",
        help="Redirect ALL reply emails to this address instead of the "
             "original recruiter (useful for testing).  The original "
             "recipient is preserved in reports."
    )
    run_all_recipient.add_argument(
        "--cc", nargs="+", metavar="ADDR",
        help="One or more CC addresses added to every reply email"
    )
    run_all_recipient.add_argument(
        "--bcc", nargs="+", metavar="ADDR",
        help="One or more BCC addresses added to every reply email "
             "(hidden from the primary recipient)"
    )

    run_all.set_defaults(func=_cmd_run_all)

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

    # =========================================================================
    # Resume Tailoring Command
    # =========================================================================

    tailor = subparsers.add_parser(
        "tailor",
        help="Tailor a resume for job opportunities using match results"
    )
    tailor.add_argument(
        "--resume", required=True,
        help="Path to the original resume file (JSON or Markdown)"
    )
    tailor.add_argument(
        "--match-results", required=True,
        help="Path to match results JSON file (from 'match' command)"
    )
    tailor.add_argument(
        "--opportunities",
        help="Path to opportunities JSON file (for job context in reports)"
    )
    tailor.add_argument(
        "--out", required=True,
        help="Output directory for tailored resumes and reports"
    )
    tailor.add_argument(
        "--min-score", type=float,
        help="Only tailor for jobs with at least this match score"
    )
    tailor.add_argument(
        "--recommendation",
        help="Comma-separated recommendations to tailor for (e.g. strong_apply,apply)"
    )
    tailor.add_argument(
        "--top", type=int,
        help="Limit to top N match results by score"
    )
    tailor.add_argument(
        "--no-docx", action="store_true",
        help="Skip .docx generation (produce JSON/Markdown reports only)"
    )
    tailor.set_defaults(func=_cmd_tailor)

    # =========================================================================
    # Recruiter Reply Commands
    # =========================================================================

    # Compose command -- generate reply drafts
    compose = subparsers.add_parser(
        "compose",
        help="Compose tailored reply emails to recruiters (LLM-powered)"
    )
    compose.add_argument(
        "--resume", required=True,
        help="Path to the candidate resume file (JSON or Markdown)"
    )
    compose.add_argument(
        "--match-results", required=True,
        help="Path to match results JSON file (from 'match' command)"
    )
    compose.add_argument(
        "--opportunities",
        help="Path to opportunities JSON file (for recruiter contact info)"
    )
    compose.add_argument(
        "--questionnaire",
        help="Path to questionnaire config JSON (salary, location, questions, etc.)"
    )
    compose.add_argument(
        "--tailored-dir",
        help="Directory containing tailored .docx resumes to attach"
    )
    compose.add_argument(
        "--out", required=True,
        help="Output directory for composed drafts and previews"
    )
    compose.add_argument(
        "--min-score", type=float,
        help="Only compose replies for jobs with at least this match score"
    )
    compose.add_argument(
        "--recommendation",
        help="Comma-separated recommendations to compose for (e.g. strong_apply,apply)"
    )
    compose.add_argument(
        "--top", type=int,
        help="Limit to top N match results by score"
    )
    compose.add_argument(
        "--llm-model", default="gpt-4o-mini",
        help="LLM model to use for email composition"
    )
    compose.set_defaults(func=_cmd_compose)

    # Reply command -- send composed drafts
    reply = subparsers.add_parser(
        "reply",
        help="Send (or dry-run) composed recruiter reply emails"
    )
    reply.add_argument(
        "--drafts", required=True,
        help="Path to drafts JSON file (from 'compose' command)"
    )
    reply.add_argument(
        "--out", required=True,
        help="Output directory for send results and report"
    )
    reply.add_argument(
        "--dry-run", action="store_true",
        help="Preview emails without sending (validate MIME, report only)"
    )
    reply.add_argument(
        "--index", type=int,
        help="Send only the draft at this index (0-based)"
    )
    reply.add_argument(
        "--override-to",
        help="Redirect ALL emails to this address instead of the original "
             "recruiter (useful for testing).  The original recipient is "
             "preserved in reports."
    )
    reply.add_argument(
        "--cc", nargs="+", metavar="ADDR",
        help="One or more CC addresses added to every email (e.g. for "
             "audit / manager visibility)"
    )
    reply.add_argument(
        "--bcc", nargs="+", metavar="ADDR",
        help="One or more BCC addresses added to every email (hidden from "
             "the primary recipient, useful for audit trails)"
    )
    reply.set_defaults(func=_cmd_reply)

    # =========================================================================
    # Correlation Command
    # =========================================================================

    correlate = subparsers.add_parser(
        "correlate",
        help="Correlate job opportunities with emails, resumes, and replies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Build a unified correlation view that links every pipeline artifact\n"
            "(email, opportunity, match result, tailored resume, reply) for each\n"
            "job opportunity.  Generates a rich Markdown report and JSON data.\n"
            "\n"
            "Auto-discovery mode (simplest):\n"
            "  email-pipeline correlate --work-dir data --out-dir output --out correlation\n"
            "\n"
            "Explicit paths:\n"
            "  email-pipeline correlate \\\n"
            "    --messages data/messages.json \\\n"
            "    --opportunities data/opportunities.json \\\n"
            "    --match-results output/matches/match_results.json \\\n"
            "    --tailored-dir output/tailored \\\n"
            "    --drafts output/replies/drafts.json \\\n"
            "    --reply-results output/replies/reply_results.json \\\n"
            "    --out correlation\n"
        ),
    )

    # -- Auto-discovery paths --
    correlate_auto = correlate.add_argument_group(
        "auto-discovery",
        "When provided, standard artifact paths are discovered automatically "
        "under these directories (same layout as run-all output)."
    )
    correlate_auto.add_argument(
        "--work-dir",
        help="Work directory (contains messages.json, opportunities.json, etc.)"
    )
    correlate_auto.add_argument(
        "--out-dir",
        help="Output directory (contains matches/, tailored/, replies/)"
    )

    # -- Explicit artifact paths --
    correlate_input = correlate.add_argument_group("explicit artifact paths")
    correlate_input.add_argument(
        "--messages",
        help="Path to messages JSON file"
    )
    correlate_input.add_argument(
        "--opportunities",
        help="Path to opportunities JSON file"
    )
    correlate_input.add_argument(
        "--match-results",
        help="Path to match results JSON file"
    )
    correlate_input.add_argument(
        "--tailored-dir",
        help="Directory containing tailoring_results.json and .docx files"
    )
    correlate_input.add_argument(
        "--drafts",
        help="Path to drafts JSON file"
    )
    correlate_input.add_argument(
        "--reply-results",
        help="Path to reply results JSON file"
    )
    correlate_input.add_argument(
        "--resume",
        help="Path to resume file (for candidate name in reports)"
    )

    # -- Filtering --
    correlate_filter = correlate.add_argument_group("filtering")
    correlate_filter.add_argument(
        "--min-score", type=float,
        help="Only include opportunities with at least this match score"
    )
    correlate_filter.add_argument(
        "--recommendation",
        help="Comma-separated recommendations to include (e.g. strong_apply,apply)"
    )
    correlate_filter.add_argument(
        "--stage",
        help="Comma-separated pipeline stages to include (e.g. matched,tailored,replied)"
    )
    correlate_filter.add_argument(
        "--top", type=int,
        help="Limit to top N opportunities (by match score)"
    )

    # -- Output --
    correlate_output = correlate.add_argument_group("output")
    correlate_output.add_argument(
        "--out", required=True,
        help="Output directory for correlation results"
    )
    correlate_output.add_argument(
        "--individual-cards", action="store_true",
        help="Generate individual Markdown cards per opportunity"
    )
    correlate_output.add_argument(
        "--full-report", action="store_true",
        help="Generate a single comprehensive report with all cards included"
    )

    correlate.set_defaults(func=_cmd_correlate)

    # =========================================================================
    # Application Tracking Commands
    # =========================================================================

    track = subparsers.add_parser(
        "track",
        help="Initialise and view application tracking from correlation data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Bootstrap application tracking from correlation data and/or view\n"
            "the current tracking state.  Produces a tracking.json file and\n"
            "Markdown reports.\n"
            "\n"
            "Auto-discovery mode (simplest):\n"
            "  email-pipeline track --out-dir output --out output/tracking\n"
            "\n"
            "Explicit paths:\n"
            "  email-pipeline track \\\n"
            "    --correlation output/correlation/correlation.json \\\n"
            "    --out output/tracking --full-report --individual-cards\n"
        ),
    )

    # -- Auto-discovery paths --
    track_auto = track.add_argument_group(
        "auto-discovery",
        "When provided, the correlation file is discovered automatically "
        "from the output directory."
    )
    track_auto.add_argument(
        "--out-dir",
        help="Output directory (contains correlation/ from a prior correlate run)"
    )

    # -- Explicit paths --
    track_input = track.add_argument_group("explicit artifact paths")
    track_input.add_argument(
        "--correlation",
        help="Path to correlation.json (from 'correlate' command)"
    )
    track_input.add_argument(
        "--tracking-file",
        help="Path to existing tracking.json to merge with (for idempotent re-runs)"
    )

    # -- Filtering --
    track_filter = track.add_argument_group("filtering")
    track_filter.add_argument(
        "--min-stage", default="replied",
        help="Minimum pipeline stage for initialisation (default: replied)"
    )
    track_filter.add_argument(
        "--status",
        help="Comma-separated statuses to display (e.g. applied,interviewing)"
    )

    # -- Output --
    track_output = track.add_argument_group("output")
    track_output.add_argument(
        "--out", required=True,
        help="Output directory for tracking results"
    )
    track_output.add_argument(
        "--individual-cards", action="store_true",
        help="Generate individual Markdown cards per application"
    )
    track_output.add_argument(
        "--full-report", action="store_true",
        help="Generate a single comprehensive report with all cards included"
    )

    track.set_defaults(func=_cmd_track)

    # -- track-update command --
    track_update = subparsers.add_parser(
        "track-update",
        help="Update status, notes, interviews, or offers for a tracked application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Modify a specific tracked application.  Requires an existing\n"
            "tracking.json file (from the 'track' command).\n"
            "\n"
            "Examples:\n"
            "  # Update status\n"
            "  email-pipeline track-update \\\n"
            "    --tracking-file output/tracking/tracking.json \\\n"
            "    --job-id MSG_ID --action status --status interviewing\n"
            "\n"
            "  # Record an interview\n"
            "  email-pipeline track-update \\\n"
            "    --tracking-file output/tracking/tracking.json \\\n"
            "    --job-id MSG_ID --action interview \\\n"
            "    --interview-type technical --scheduled-at 2026-02-15\n"
            "\n"
            "  # Record an offer\n"
            "  email-pipeline track-update \\\n"
            "    --tracking-file output/tracking/tracking.json \\\n"
            "    --job-id MSG_ID --action offer --salary '150k USD'\n"
            "\n"
            "  # Accept an offer\n"
            "  email-pipeline track-update \\\n"
            "    --tracking-file output/tracking/tracking.json \\\n"
            "    --job-id MSG_ID --action outcome --outcome accepted\n"
        ),
    )

    track_update.add_argument(
        "--tracking-file", required=True,
        help="Path to tracking.json"
    )
    track_update.add_argument(
        "--job-id", required=True,
        help="Job ID of the application to update"
    )
    track_update.add_argument(
        "--action", required=True,
        choices=["status", "outcome", "interview", "offer", "note"],
        help="Type of update to perform"
    )
    track_update.add_argument(
        "--status",
        choices=["applied", "interviewing", "offered", "closed"],
        help="New application status (for action=status)"
    )
    track_update.add_argument(
        "--outcome",
        choices=["accepted", "declined", "rejected", "withdrawn", "ghosted"],
        help="Final outcome (for action=outcome)"
    )
    track_update.add_argument(
        "--interview-type",
        choices=["phone_screen", "technical", "behavioral", "system_design",
                 "hiring_manager", "panel", "onsite", "other"],
        help="Interview type (for action=interview)"
    )
    track_update.add_argument(
        "--scheduled-at",
        help="Interview date/time (for action=interview)"
    )
    track_update.add_argument(
        "--interviewer",
        help="Interviewer name (for action=interview)"
    )
    track_update.add_argument(
        "--completed", action="store_true",
        help="Mark interview as completed (for action=interview)"
    )
    track_update.add_argument(
        "--salary",
        help="Offer salary (for action=offer)"
    )
    track_update.add_argument(
        "--equity",
        help="Offer equity (for action=offer)"
    )
    track_update.add_argument(
        "--bonus",
        help="Offer bonus (for action=offer)"
    )
    track_update.add_argument(
        "--start-date",
        help="Offer start date (for action=offer)"
    )
    track_update.add_argument(
        "--note",
        help="Free-form note (used by all actions)"
    )
    track_update.add_argument(
        "--out",
        help="Output directory (default: same as tracking file directory)"
    )

    track_update.set_defaults(func=_cmd_track_update)

    # =========================================================================
    # Streamlit UI Command
    # =========================================================================

    ui_parser = subparsers.add_parser(
        "ui",
        help="Launch the Streamlit web dashboard",
        description=(
            "Start the interactive Streamlit dashboard to explore pipeline\n"
            "artifacts, match results, tailored resumes, and reply drafts.\n"
            "\n"
            "Requires the 'ui' extra:  pip install -e '.[ui]'\n"
        ),
    )
    ui_parser.add_argument(
        "--port", type=int, default=8501,
        help="Port for the Streamlit server (default: 8501)"
    )
    ui_parser.set_defaults(func=_cmd_ui)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
