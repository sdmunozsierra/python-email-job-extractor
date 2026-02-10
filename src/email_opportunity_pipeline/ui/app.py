"""
Streamlit web UI for the Email Opportunity Pipeline.

Launch with:
    email-pipeline ui
    streamlit run src/email_opportunity_pipeline/ui/app.py
    uv run streamlit run src/email_opportunity_pipeline/ui/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the package is importable when Streamlit runs this file as a script.
# ``streamlit run .../app.py`` executes the file directly so Python does not
# recognise the parent package and relative imports fail.  We add the project
# ``src/`` directory to sys.path so absolute imports resolve correctly.
# ---------------------------------------------------------------------------
_src_dir = str(Path(__file__).resolve().parent.parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import streamlit as st

from email_opportunity_pipeline.ui.state import (
    discover_artifacts,
    load_analytics,
    load_drafts,
    load_match_results,
    load_messages,
    load_opportunities,
    load_reply_results,
    load_tailoring_results,
    load_correlation,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Email Opportunity Pipeline",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar -- directory selector & navigation
# ---------------------------------------------------------------------------

st.sidebar.title("Email Opportunity Pipeline")

work_dir = Path(
    st.sidebar.text_input("Work directory", value="data", help="Directory containing pipeline JSON artifacts")
)
out_dir = Path(
    st.sidebar.text_input("Output directory", value="output", help="Directory containing reports and results")
)

artifacts = discover_artifacts(work_dir, out_dir)

if artifacts:
    st.sidebar.success(f"{len(artifacts)} artifact(s) found")
else:
    st.sidebar.warning("No artifacts found. Run the pipeline first, or adjust the directories above.")

# Build navigation from available data
pages = ["Dashboard"]
if "messages" in artifacts or "filtered" in artifacts:
    pages.append("Messages")
if "opportunities" in artifacts:
    pages.append("Opportunities")
if "match_results" in artifacts:
    pages.append("Match Results")
if "tailoring_results" in artifacts:
    pages.append("Tailored Resumes")
if "drafts" in artifacts:
    pages.append("Reply Drafts")
if "reply_results" in artifacts:
    pages.append("Reply Results")
if "correlation" in artifacts:
    pages.append("Correlation")
if "analytics" in artifacts:
    pages.append("Analytics")

page = st.sidebar.radio("Navigate", pages)

st.sidebar.markdown("---")
st.sidebar.caption("Artifacts on disk:")
for name, path in sorted(artifacts.items()):
    st.sidebar.caption(f"  {name}: `{path}`")


# ============================================================================
# Dashboard
# ============================================================================

def _page_dashboard() -> None:
    st.header("Pipeline Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    messages = load_messages(artifacts["messages"]) if "messages" in artifacts else []
    filtered = load_messages(artifacts["filtered"]) if "filtered" in artifacts else []
    opportunities = load_opportunities(artifacts["opportunities"]) if "opportunities" in artifacts else []
    matches = load_match_results(artifacts["match_results"]) if "match_results" in artifacts else []

    col1.metric("Fetched emails", len(messages))
    col2.metric("Passed filter", len(filtered))
    col3.metric("Opportunities", len(opportunities))
    col4.metric("Match results", len(matches))

    # Second row
    col5, col6, col7, col8 = st.columns(4)

    tailoring = load_tailoring_results(artifacts["tailoring_results"]) if "tailoring_results" in artifacts else []
    drafts = load_drafts(artifacts["drafts"]) if "drafts" in artifacts else []
    replies = load_reply_results(artifacts["reply_results"]) if "reply_results" in artifacts else []

    col5.metric("Tailored resumes", len(tailoring))
    col6.metric("Email drafts", len(drafts))
    col7.metric("Replies sent/previewed", len(replies))
    col8.metric("Artifacts on disk", len(artifacts))

    # Filter pass rate
    if messages and filtered:
        pass_rate = len(filtered) / len(messages) * 100
        st.markdown(f"**Filter pass rate:** {pass_rate:.1f}% ({len(filtered)}/{len(messages)})")

    # Top matches preview
    if matches:
        st.subheader("Top Match Results")
        top = sorted(matches, key=lambda m: m.get("overall_score", 0), reverse=True)[:5]
        for i, m in enumerate(top, 1):
            score = m.get("overall_score", 0)
            grade = m.get("match_grade", "N/A")
            rec = m.get("recommendation", "N/A")
            job_id = m.get("job_id", "unknown")[:40]
            st.markdown(f"{i}. **{score:.0f}/100** ({grade}) -- {rec} -- `{job_id}`")

    # Quick links
    if "analytics_report" in artifacts:
        st.subheader("Analytics Report")
        report_text = artifacts["analytics_report"].read_text(encoding="utf-8")
        with st.expander("View full analytics report"):
            st.code(report_text, language="text")


# ============================================================================
# Messages
# ============================================================================

def _page_messages() -> None:
    st.header("Email Messages")

    tab_all, tab_filtered = st.tabs(["All Fetched", "Filtered (passed)"])

    with tab_all:
        if "messages" in artifacts:
            messages = load_messages(artifacts["messages"])
            st.write(f"**{len(messages)}** messages fetched")
            _render_messages_table(messages)
        else:
            st.info("No messages.json found.")

    with tab_filtered:
        if "filtered" in artifacts:
            filtered = load_messages(artifacts["filtered"])
            st.write(f"**{len(filtered)}** messages passed filter")
            _render_messages_table(filtered)
        else:
            st.info("No filtered.json found.")


def _render_messages_table(messages: list) -> None:
    if not messages:
        st.info("No messages to display.")
        return

    rows = []
    for msg in messages:
        headers = msg.get("headers", {})
        rows.append({
            "Subject": headers.get("subject", "")[:80],
            "From": headers.get("from", "")[:50],
            "Date": headers.get("date", ""),
            "Labels": ", ".join(msg.get("labels", [])[:3]),
            "ID": msg.get("message_id", "")[:20],
        })
    st.dataframe(rows, use_container_width=True)

    # Detail expander
    with st.expander("Message details"):
        idx = st.number_input("Message index", 0, max(len(messages) - 1, 0), 0, key="msg_detail_idx")
        if 0 <= idx < len(messages):
            msg = messages[idx]
            st.json(msg)


# ============================================================================
# Opportunities
# ============================================================================

def _page_opportunities() -> None:
    st.header("Extracted Opportunities")
    opportunities = load_opportunities(artifacts["opportunities"])
    st.write(f"**{len(opportunities)}** opportunities extracted")

    if not opportunities:
        st.info("No opportunities to display.")
        return

    rows = []
    for opp in opportunities:
        rows.append({
            "Job Title": opp.get("job_title", "N/A")[:50],
            "Company": opp.get("company", "N/A")[:30],
            "Location": ", ".join(opp.get("locations", [])[:2]) if opp.get("locations") else ("Remote" if opp.get("remote") else "N/A"),
            "Remote": "Yes" if opp.get("remote") else "No",
            "Source": opp.get("source_email", {}).get("message_id", "")[:20],
        })
    st.dataframe(rows, use_container_width=True)

    with st.expander("Opportunity details"):
        idx = st.number_input("Opportunity index", 0, max(len(opportunities) - 1, 0), 0, key="opp_detail_idx")
        if 0 <= idx < len(opportunities):
            opp = opportunities[idx]
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"### {opp.get('job_title', 'Unknown')}")
                st.markdown(f"**Company:** {opp.get('company', 'N/A')}")
                st.markdown(f"**Locations:** {', '.join(opp.get('locations', [])) or 'N/A'}")
                st.markdown(f"**Remote:** {'Yes' if opp.get('remote') else 'No'}")
            with col_b:
                st.json(opp)


# ============================================================================
# Match Results
# ============================================================================

def _page_match_results() -> None:
    st.header("Resume Match Results")
    matches = load_match_results(artifacts["match_results"])
    st.write(f"**{len(matches)}** match results")

    if not matches:
        st.info("No match results to display.")
        return

    # Summary metrics
    scores = [m.get("overall_score", 0) for m in matches]
    avg_score = sum(scores) / len(scores) if scores else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Score", f"{avg_score:.1f}")
    col2.metric("Best Score", f"{max(scores):.0f}" if scores else "N/A")
    col3.metric("Matches >= 70", sum(1 for s in scores if s >= 70))

    # Score distribution bar chart
    st.subheader("Score Distribution")
    import collections
    buckets = collections.Counter()
    for s in scores:
        bucket = f"{int(s // 10) * 10}-{int(s // 10) * 10 + 9}"
        buckets[bucket] += 1
    chart_data = dict(sorted(buckets.items()))
    st.bar_chart(chart_data)

    # Table
    rows = []
    for m in sorted(matches, key=lambda x: x.get("overall_score", 0), reverse=True):
        rows.append({
            "Score": f"{m.get('overall_score', 0):.0f}",
            "Grade": m.get("match_grade", "N/A"),
            "Recommendation": m.get("recommendation", "N/A"),
            "Job ID": m.get("job_id", "")[:30],
        })
    st.dataframe(rows, use_container_width=True)

    # Detail view
    with st.expander("Match details"):
        idx = st.number_input("Match index (sorted by score)", 0, max(len(matches) - 1, 0), 0, key="match_detail_idx")
        sorted_matches = sorted(matches, key=lambda x: x.get("overall_score", 0), reverse=True)
        if 0 <= idx < len(sorted_matches):
            m = sorted_matches[idx]
            st.json(m)

    # Markdown summary
    if "match_summary" in artifacts:
        with st.expander("Match Summary Report (Markdown)"):
            md = artifacts["match_summary"].read_text(encoding="utf-8")
            st.markdown(md)


# ============================================================================
# Tailored Resumes
# ============================================================================

def _page_tailored_resumes() -> None:
    st.header("Tailored Resumes")
    results = load_tailoring_results(artifacts["tailoring_results"])
    st.write(f"**{len(results)}** tailored resumes generated")

    if not results:
        st.info("No tailoring results to display.")
        return

    rows = []
    for r in results:
        report = r.get("report", {})
        rows.append({
            "Job Title": report.get("job_title", "N/A")[:40],
            "Company": report.get("company", "N/A")[:25],
            "Match Score": f"{report.get('match_score', 0):.0f}",
            "Grade": report.get("match_grade", "N/A"),
            "Changes": report.get("total_changes", 0),
            "Has .docx": "Yes" if r.get("docx_path") else "No",
        })
    st.dataframe(rows, use_container_width=True)

    with st.expander("Tailoring details"):
        idx = st.number_input("Result index", 0, max(len(results) - 1, 0), 0, key="tailor_detail_idx")
        if 0 <= idx < len(results):
            r = results[idx]
            report = r.get("report", {})
            changes = report.get("changes", [])
            if changes:
                st.subheader("Changes Applied")
                for c in changes:
                    st.markdown(f"- **{c.get('category', 'N/A')}**: {c.get('description', '')}")
                    if c.get("before"):
                        st.caption(f"Before: {c['before'][:100]}")
                    if c.get("after"):
                        st.caption(f"After: {c['after'][:100]}")
            st.json(r)

    if "tailoring_summary" in artifacts:
        with st.expander("Tailoring Summary Report (Markdown)"):
            md = artifacts["tailoring_summary"].read_text(encoding="utf-8")
            st.markdown(md)


# ============================================================================
# Reply Drafts
# ============================================================================

def _page_reply_drafts() -> None:
    st.header("Reply Email Drafts")
    drafts = load_drafts(artifacts["drafts"])
    st.write(f"**{len(drafts)}** email drafts composed")

    if not drafts:
        st.info("No drafts to display.")
        return

    rows = []
    for d in drafts:
        rows.append({
            "Job Title": d.get("job_title", "N/A")[:40],
            "Company": d.get("company", "N/A")[:25],
            "To": d.get("to", "N/A")[:30],
            "Subject": d.get("subject", "N/A")[:50],
            "Score": f"{d.get('match_score', 0):.0f}" if d.get("match_score") is not None else "N/A",
            "Attachments": len(d.get("attachment_paths", [])),
        })
    st.dataframe(rows, use_container_width=True)

    st.subheader("Draft Preview")
    idx = st.number_input("Draft index", 0, max(len(drafts) - 1, 0), 0, key="draft_preview_idx")
    if 0 <= idx < len(drafts):
        d = drafts[idx]
        st.markdown(f"**To:** {d.get('to', 'N/A')}")
        st.markdown(f"**Subject:** {d.get('subject', 'N/A')}")
        if d.get("in_reply_to"):
            st.caption(f"In-Reply-To: {d['in_reply_to']}")
        st.markdown("---")
        st.markdown(d.get("body", "(empty body)"))
        if d.get("attachment_paths"):
            st.markdown("**Attachments:**")
            for att in d["attachment_paths"]:
                st.caption(f"  {att}")

    if "drafts_preview" in artifacts:
        with st.expander("Full Drafts Preview (Markdown)"):
            md = artifacts["drafts_preview"].read_text(encoding="utf-8")
            st.markdown(md)


# ============================================================================
# Reply Results
# ============================================================================

def _page_reply_results() -> None:
    st.header("Reply Send Results")
    results = load_reply_results(artifacts["reply_results"])
    st.write(f"**{len(results)}** reply results")

    if not results:
        st.info("No reply results to display.")
        return

    rows = []
    for r in results:
        draft = r.get("draft", {})
        rows.append({
            "Job Title": draft.get("job_title", "N/A")[:40],
            "Company": draft.get("company", "N/A")[:25],
            "To": draft.get("to", "N/A")[:30],
            "Status": r.get("status", "N/A"),
            "Gmail ID": r.get("gmail_message_id", "N/A")[:20] if r.get("gmail_message_id") else "N/A",
            "Error": r.get("error", "")[:40] if r.get("error") else "",
        })
    st.dataframe(rows, use_container_width=True)

    # Status breakdown
    statuses = [r.get("status", "unknown") for r in results]
    from collections import Counter
    status_counts = Counter(statuses)
    col1, col2, col3 = st.columns(3)
    col1.metric("Sent", status_counts.get("sent", 0))
    col2.metric("Dry Run", status_counts.get("dry_run", 0))
    col3.metric("Failed", status_counts.get("failed", 0))

    if "reply_report" in artifacts:
        with st.expander("Reply Report (Markdown)"):
            md = artifacts["reply_report"].read_text(encoding="utf-8")
            st.markdown(md)


# ============================================================================
# Correlation
# ============================================================================

def _page_correlation() -> None:
    st.header("Job Opportunity Correlation")
    data = load_correlation(artifacts["correlation"])

    summary = data.get("summary", {})
    correlated = data.get("correlated_opportunities", [])

    if not correlated:
        st.info("No correlation data to display.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Opportunities", summary.get("total_opportunities", 0))
    col2.metric("Matched", summary.get("matched_count", 0))
    col3.metric("Tailored", summary.get("tailored_count", 0))
    col4.metric("Pipeline Complete", summary.get("pipeline_complete_count", 0))

    if summary.get("avg_match_score"):
        col5, col6 = st.columns(2)
        col5.metric("Avg Match Score", f"{summary['avg_match_score']:.1f}")
        col6.metric("Best Score", f"{summary.get('max_match_score', 0):.1f}")

    # Stage breakdown
    by_stage = summary.get("by_stage", {})
    if by_stage:
        st.subheader("Pipeline Stage Distribution")
        st.bar_chart(by_stage)

    # Table
    rows = []
    for c in correlated:
        match_data = c.get("match", {})
        rows.append({
            "Job Title": (c.get("job_title") or "N/A")[:40],
            "Company": (c.get("company") or "N/A")[:25],
            "Stage": c.get("stage", "N/A"),
            "Score": f"{match_data.get('overall_score', 0):.0f}" if match_data else "N/A",
            "Grade": match_data.get("match_grade", "") if match_data else "",
            "Has Reply": "Yes" if c.get("reply") else "No",
        })
    st.dataframe(rows, use_container_width=True)

    with st.expander("Correlation details"):
        idx = st.number_input("Opportunity index", 0, max(len(correlated) - 1, 0), 0, key="corr_detail_idx")
        if 0 <= idx < len(correlated):
            st.json(correlated[idx])

    if "correlation_summary" in artifacts:
        with st.expander("Correlation Summary Report (Markdown)"):
            md = artifacts["correlation_summary"].read_text(encoding="utf-8")
            st.markdown(md)


# ============================================================================
# Analytics
# ============================================================================

def _page_analytics() -> None:
    st.header("Pipeline Analytics")
    analytics = load_analytics(artifacts["analytics"])

    if not analytics:
        st.info("No analytics data found.")
        return

    # Timing
    timing = analytics.get("timing", {})
    if timing.get("duration_seconds"):
        st.caption(f"Processing time: {timing['duration_seconds']:.2f}s")

    # Input metrics
    inp = analytics.get("input_metrics", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Emails Fetched", inp.get("total_emails_fetched", 0))
    col2.metric("With Body", inp.get("emails_with_body", 0))
    col3.metric("Metadata Only", inp.get("emails_metadata_only", 0))

    # Filter metrics
    filt = analytics.get("filter_metrics", {})
    col4, col5, col6 = st.columns(3)
    col4.metric("Total Filtered", filt.get("total_filtered", 0))
    col5.metric("Passed", filt.get("passed", 0))
    col6.metric("Pass Rate", f"{filt.get('pass_rate_percent', 0):.1f}%")

    # Extraction metrics
    ext = analytics.get("extraction_metrics", {})
    st.subheader("Extraction Quality")
    col7, col8, col9, col10 = st.columns(4)
    col7.metric("Opportunities", ext.get("total_opportunities", 0))
    col8.metric("With Company", ext.get("with_company", 0))
    col9.metric("With Role", ext.get("with_role", 0))
    col10.metric("With Salary", ext.get("with_salary", 0))

    # Top domains
    domains = analytics.get("top_domains", {})
    if domains:
        st.subheader("Top Email Domains")
        st.bar_chart(domains)

    # Score distribution
    score_dist = analytics.get("score_distribution", {})
    all_scores = score_dist.get("all_scores", {})
    if all_scores.get("count", 0) > 0:
        st.subheader("Score Distribution")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Min Score", f"{all_scores.get('min', 0):.1f}")
        col_b.metric("Avg Score", f"{all_scores.get('avg', 0):.1f}")
        col_c.metric("Max Score", f"{all_scores.get('max', 0):.1f}")

    # Emails by date
    by_date = analytics.get("emails_by_date", {})
    if by_date:
        st.subheader("Emails by Date")
        st.bar_chart(by_date)

    # Top failure reasons
    fail_reasons = analytics.get("top_fail_reasons", {})
    if fail_reasons:
        st.subheader("Top Failure Reasons")
        for reason, count in list(fail_reasons.items())[:10]:
            st.markdown(f"- **{count}** -- {reason[:80]}")

    # Full report
    if "analytics_report" in artifacts:
        with st.expander("Full Analytics Report"):
            report = artifacts["analytics_report"].read_text(encoding="utf-8")
            st.code(report, language="text")

    with st.expander("Raw analytics JSON"):
        st.json(analytics)


# ============================================================================
# Page routing
# ============================================================================

_PAGE_MAP = {
    "Dashboard": _page_dashboard,
    "Messages": _page_messages,
    "Opportunities": _page_opportunities,
    "Match Results": _page_match_results,
    "Tailored Resumes": _page_tailored_resumes,
    "Reply Drafts": _page_reply_drafts,
    "Reply Results": _page_reply_results,
    "Correlation": _page_correlation,
    "Analytics": _page_analytics,
}

handler = _PAGE_MAP.get(page)
if handler:
    handler()
else:
    st.error(f"Unknown page: {page}")
