"""
Streamlit web UI for the Email Opportunity Pipeline.

Launch with:
    email-pipeline ui
    streamlit run src/email_opportunity_pipeline/ui/app.py
    uv run streamlit run src/email_opportunity_pipeline/ui/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

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
    load_tracking,
)
from email_opportunity_pipeline.threading_utils import (
    group_messages_by_thread,
    build_thread_summaries,
)
from email_opportunity_pipeline.ui.runner import (
    RunResult,
    cmd_fetch,
    cmd_filter,
    cmd_extract,
    cmd_analyze,
    cmd_match,
    cmd_tailor,
    cmd_compose,
    cmd_reply,
    cmd_correlate,
    cmd_analytics,
    cmd_track,
    cmd_track_update,
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
    st.sidebar.warning("No artifacts found -- run the pipeline first, or adjust directories above.")

# Build navigation -- always show all pages so users can trigger actions
pages = [
    "Dashboard",
    "Inbox",
    "Messages",
    "Opportunities",
    "Match Results",
    "Tailored Resumes",
    "Reply Drafts",
    "Reply Results",
    "Correlation",
    "Application Tracker",
    "Analytics",
]

page = st.sidebar.radio("Navigate", pages)

st.sidebar.markdown("---")
st.sidebar.caption("Artifacts on disk:")
if artifacts:
    for name, path in sorted(artifacts.items()):
        st.sidebar.caption(f"  {name}: `{path}`")
else:
    st.sidebar.caption("  (none)")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _show_result(result: RunResult) -> None:
    """Display the result of a pipeline command."""
    if result.ok:
        st.success(f"Command succeeded (exit {result.returncode})")
    else:
        st.error(f"Command failed (exit {result.returncode})")
    if result.stdout:
        with st.expander("stdout", expanded=not result.ok):
            st.code(result.stdout, language="text")
    if result.stderr:
        with st.expander("stderr", expanded=not result.ok):
            st.code(result.stderr, language="text")
    st.caption(f"`{' '.join(result.command)}`")


def _file_picker(label: str, key: str, default: str = "", help_text: str = "") -> str:
    """Text input that acts as a simple file path selector."""
    return st.text_input(label, value=default, key=key, help=help_text)


def _resume_picker(key_prefix: str) -> str:
    """Reusable resume file picker."""
    return _file_picker(
        "Resume file (JSON or Markdown)",
        key=f"{key_prefix}_resume",
        default="examples/sample_resume.json",
        help_text="Path to your resume file",
    )


def _llm_model_picker(key_prefix: str) -> str:
    """Reusable LLM model selector."""
    return st.selectbox(
        "LLM model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        key=f"{key_prefix}_llm_model",
    )


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

    # ----- Quick actions -----
    st.markdown("---")
    st.subheader("Quick Actions")

    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        window = st.selectbox("Fetch window", ["30m", "1h", "6h", "1d", "2d", "7d"], index=3, key="dash_window")
        if st.button("Fetch emails", key="dash_fetch"):
            with st.spinner("Fetching emails..."):
                result = cmd_fetch(provider="gmail", window=window, out=str(work_dir / "messages.json"))
            _show_result(result)
            if result.ok:
                st.rerun()
    with qa2:
        if st.button("Filter + Extract", key="dash_filter_extract"):
            ok = True
            with st.spinner("Filtering..."):
                r1 = cmd_filter(input_path=str(work_dir / "messages.json"), out=str(work_dir / "filtered.json"))
            _show_result(r1)
            ok = r1.ok
            if ok:
                with st.spinner("Extracting..."):
                    r2 = cmd_extract(input_path=str(work_dir / "filtered.json"), out=str(work_dir / "opportunities.json"))
                _show_result(r2)
            if ok and r2.ok:
                st.rerun()
    with qa3:
        if st.button("Correlate all", key="dash_correlate"):
            with st.spinner("Correlating..."):
                result = cmd_correlate(
                    out=str(out_dir / "correlation"),
                    work_dir=str(work_dir),
                    out_dir=str(out_dir),
                )
            _show_result(result)
            if result.ok:
                st.rerun()


# ============================================================================
# Inbox (Thread Viewer)
# ============================================================================

def _page_inbox() -> None:
    st.header("Inbox")

    if "messages" not in artifacts:
        st.info("No messages found. Fetch emails from the **Messages** page first.")
        return

    # Load messages -- optionally switch between all fetched and filtered
    source_options = ["All fetched"]
    if "filtered" in artifacts:
        source_options.append("Filtered only")

    col_search, col_source = st.columns([3, 1])
    with col_source:
        show_source = st.selectbox("Source", source_options, key="inbox_source")
    with col_search:
        search_query = st.text_input(
            "Search threads",
            placeholder="Search by subject, sender, or content...",
            key="inbox_search",
        )

    if show_source == "Filtered only" and "filtered" in artifacts:
        messages = load_messages(artifacts["filtered"])
    else:
        messages = load_messages(artifacts["messages"])

    if not messages:
        st.info("No messages to display.")
        return

    # Build thread structure
    threads = group_messages_by_thread(messages)
    summaries = build_thread_summaries(threads)

    # Load correlation data for pipeline status badges
    correlation_lookup: Dict[str, dict] = {}  # message_id -> correlated opp
    if "correlation" in artifacts:
        corr_data = load_correlation(artifacts["correlation"])
        for c in corr_data.get("correlated_opportunities", []):
            for em in c.get("emails", []):
                mid = em.get("message_id", "")
                if mid:
                    correlation_lookup[mid] = c
            # Also index by job_id (which may be a message_id)
            jid = c.get("job_id", "")
            if jid:
                correlation_lookup[jid] = c

    # Apply search filter
    if search_query:
        q = search_query.lower()
        summaries = [
            s for s in summaries
            if q in s.subject.lower()
            or any(q in p.lower() for p in s.participants)
            or q in s.earliest_snippet.lower()
        ]

    total_msgs = sum(s.message_count for s in summaries)
    st.caption(f"{len(summaries)} thread(s)  \u00b7  {total_msgs} message(s)")

    # Thread selection via session state
    if "inbox_selected_thread" not in st.session_state:
        st.session_state.inbox_selected_thread = None

    selected_tid = st.session_state.inbox_selected_thread

    if selected_tid and selected_tid in threads:
        _render_thread_detail(threads[selected_tid], selected_tid, correlation_lookup)
    else:
        # Reset if thread no longer valid
        if selected_tid is not None:
            st.session_state.inbox_selected_thread = None
        _render_thread_list(summaries, correlation_lookup)


def _render_thread_list(
    summaries: list,
    correlation_lookup: dict,
) -> None:
    """Render the inbox thread list view."""
    # Pagination
    PAGE_SIZE = 25
    total_pages = max(1, (len(summaries) + PAGE_SIZE - 1) // PAGE_SIZE)
    if total_pages > 1:
        page_num = st.number_input(
            "Page", 1, total_pages, 1, key="inbox_page",
        )
    else:
        page_num = 1

    start = (page_num - 1) * PAGE_SIZE
    page_summaries = summaries[start : start + PAGE_SIZE]

    for i, summary in enumerate(page_summaries, start=start):
        # Check pipeline status
        badge = ""
        for mid in summary.message_ids:
            if mid in correlation_lookup:
                opp = correlation_lookup[mid]
                stage = opp.get("stage", "")
                match_data = opp.get("match")
                score_str = ""
                if match_data and match_data.get("overall_score"):
                    score_str = f" {match_data['overall_score']:.0f}/100"
                badge = f"{stage}{score_str}"
                break

        # Thread row
        col_subj, col_from, col_date = st.columns([5, 3, 2])
        with col_subj:
            count_prefix = f"({summary.message_count}) " if summary.message_count > 1 else ""
            label = f"{count_prefix}{summary.subject[:70]}"
            if badge:
                label += f"  \u2014  `{badge}`"
            if st.button(label, key=f"inbox_thread_{i}", use_container_width=True):
                st.session_state.inbox_selected_thread = summary.thread_id
                st.rerun()
        with col_from:
            display_from = summary.participants[0][:40] if summary.participants else ""
            if len(summary.participants) > 1:
                display_from += f" +{len(summary.participants) - 1}"
            st.caption(display_from)
        with col_date:
            st.caption(summary.latest_date[:22] if summary.latest_date else "")


def _render_thread_detail(
    messages: list,
    thread_id: str,
    correlation_lookup: dict,
) -> None:
    """Render a full conversation thread."""
    if st.button("\u2190 Back to Inbox", key="inbox_back"):
        st.session_state.inbox_selected_thread = None
        st.rerun()

    # Thread header
    first_msg = messages[0]
    subject = (first_msg.get("headers") or {}).get("subject", "(no subject)")
    st.subheader(subject)
    st.caption(f"{len(messages)} message(s) in thread  \u00b7  Thread ID: `{thread_id[:20]}...`")

    # Pipeline status banner
    for msg in messages:
        mid = msg.get("message_id", "")
        if mid in correlation_lookup:
            _render_pipeline_banner(correlation_lookup[mid])
            break

    st.markdown("---")

    # Render each message (oldest first, latest expanded)
    for i, msg in enumerate(messages):
        _render_single_message(msg, expanded=(i == len(messages) - 1))


def _render_pipeline_banner(opp: dict) -> None:
    """Show a compact pipeline status banner for a correlated opportunity."""
    cols = st.columns(5)
    cols[0].markdown(f"**Stage:** {opp.get('stage', 'N/A')}")
    cols[1].markdown(f"**Title:** {opp.get('job_title', 'N/A')}")
    cols[2].markdown(f"**Company:** {opp.get('company', 'N/A')}")
    match_data = opp.get("match")
    if match_data:
        cols[3].markdown(f"**Score:** {match_data.get('overall_score', 0):.0f}/100")
        cols[4].markdown(f"**Grade:** {match_data.get('match_grade', 'N/A')}")


def _render_single_message(msg: dict, *, expanded: bool = False) -> None:
    """Render a single email message within a thread view."""
    headers = msg.get("headers") or {}
    sender = headers.get("from", "Unknown sender")
    date = headers.get("date", "")

    with st.expander(f"**{sender}** \u2014 {date}", expanded=expanded):
        # Header details
        hdr_col1, hdr_col2 = st.columns(2)
        with hdr_col1:
            st.markdown(f"**From:** {headers.get('from', '')}")
            st.markdown(f"**To:** {headers.get('to', '')}")
            if headers.get("cc"):
                st.markdown(f"**Cc:** {headers['cc']}")
        with hdr_col2:
            st.markdown(f"**Date:** {date}")
            st.markdown(f"**Subject:** {headers.get('subject', '')}")
            if headers.get("in_reply_to"):
                st.caption(f"In-Reply-To: {headers['in_reply_to']}")

        # Labels
        labels = msg.get("labels", [])
        if labels:
            st.markdown(f"**Labels:** {', '.join(labels)}")

        st.markdown("---")

        # Body
        body = msg.get("body") or {}
        body_text = body.get("text", "")
        body_html = body.get("html", "")

        if body_text:
            st.text(body_text[:5000])
        elif body_html:
            st.markdown(body_html[:5000], unsafe_allow_html=True)
        else:
            snippet = msg.get("snippet", "")
            st.caption(snippet if snippet else "(No body content)")

        # HTML toggle
        if body_text and body_html:
            if st.checkbox("Show HTML version", key=f"html_{msg.get('message_id', '')}"):
                st.markdown(body_html[:5000], unsafe_allow_html=True)

        # Attachments
        attachments = msg.get("attachments", [])
        if attachments:
            st.markdown(f"**Attachments ({len(attachments)}):**")
            for att in attachments:
                size_kb = att.get("size", 0) / 1024
                fname = att.get("filename") or att.get("fileName", "unnamed")
                mime = att.get("mimeType", "unknown")
                st.caption(f"  {fname} ({mime}, {size_kb:.1f} KB)")

        # Raw JSON
        with st.expander("Raw message JSON"):
            st.json(msg)


# ============================================================================
# Messages
# ============================================================================

def _page_messages() -> None:
    st.header("Email Messages")

    # ----- Fetch action -----
    with st.expander("Fetch new emails", expanded="messages" not in artifacts):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            provider = st.selectbox("Provider", ["gmail"], key="msg_provider")
        with fc2:
            window = st.selectbox("Time window", ["30m", "1h", "6h", "1d", "2d", "7d"], index=3, key="msg_window")
        with fc3:
            max_results = st.number_input("Max results (0 = unlimited)", 0, 10000, 0, key="msg_max")
        query = st.text_input("Gmail search query (optional)", key="msg_query")

        if st.button("Fetch", key="msg_fetch_btn"):
            with st.spinner("Fetching emails from Gmail..."):
                result = cmd_fetch(
                    provider=provider,
                    window=window,
                    out=str(work_dir / "messages.json"),
                    query=query,
                    max_results=max_results or None,
                )
            _show_result(result)
            if result.ok:
                st.rerun()

    # ----- Filter action -----
    if "messages" in artifacts:
        with st.expander("Filter messages"):
            fc1, fc2 = st.columns(2)
            with fc1:
                rules = _file_picker("Filter rules JSON (optional)", "msg_rules", default="examples/filter_rules.json")
            with fc2:
                use_llm = st.checkbox("Use LLM filter", key="msg_llm_filter")
            if st.button("Run filter", key="msg_filter_btn"):
                with st.spinner("Filtering..."):
                    result = cmd_filter(
                        input_path=str(artifacts["messages"]),
                        out=str(work_dir / "filtered.json"),
                        rules=rules if Path(rules).exists() else "",
                        llm_filter=use_llm,
                    )
                _show_result(result)
                if result.ok:
                    st.rerun()

    # ----- Data display -----
    tab_all, tab_filtered = st.tabs(["All Fetched", "Filtered (passed)"])

    with tab_all:
        if "messages" in artifacts:
            messages = load_messages(artifacts["messages"])
            st.write(f"**{len(messages)}** messages fetched")
            _render_messages_table(messages, key_prefix="all")
        else:
            st.info("No messages.json found. Use the Fetch action above.")

    with tab_filtered:
        if "filtered" in artifacts:
            filtered = load_messages(artifacts["filtered"])
            st.write(f"**{len(filtered)}** messages passed filter")
            _render_messages_table(filtered, key_prefix="filtered")
        else:
            st.info("No filtered.json found. Run the filter first.")


def _render_messages_table(messages: list, *, key_prefix: str) -> None:
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

    with st.expander("Message details"):
        idx = st.number_input(
            "Message index", 0, max(len(messages) - 1, 0), 0,
            key=f"{key_prefix}_msg_detail_idx",
        )
        if 0 <= idx < len(messages):
            st.json(messages[idx])


# ============================================================================
# Opportunities
# ============================================================================

def _page_opportunities() -> None:
    st.header("Extracted Opportunities")

    # ----- Extract action -----
    with st.expander("Extract opportunities", expanded="opportunities" not in artifacts):
        ec1, ec2 = st.columns(2)
        with ec1:
            input_src = "filtered" if "filtered" in artifacts else "messages"
            extract_in = str(artifacts.get(input_src, work_dir / "filtered.json"))
            st.caption(f"Input: `{extract_in}`")
        with ec2:
            use_llm = st.checkbox("Use LLM extraction", key="opp_llm_extract")
        if st.button("Extract", key="opp_extract_btn"):
            with st.spinner("Extracting opportunities..."):
                result = cmd_extract(
                    input_path=extract_in,
                    out=str(work_dir / "opportunities.json"),
                    llm_extract=use_llm,
                )
            _show_result(result)
            if result.ok:
                st.rerun()

    if "opportunities" not in artifacts:
        st.info("No opportunities.json found. Run extraction above or fetch + filter first.")
        return

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

    # ----- Analyze + Match actions -----
    with st.expander("Run Analyze & Match", expanded="match_results" not in artifacts):
        resume = _resume_picker("match")
        llm_model = _llm_model_picker("match")

        mc1, mc2 = st.columns(2)
        with mc1:
            if st.button("Analyze jobs", key="match_analyze_btn"):
                if "opportunities" not in artifacts:
                    st.warning("No opportunities found. Run extraction first.")
                else:
                    with st.spinner("Analyzing jobs with LLM..."):
                        result = cmd_analyze(
                            input_path=str(artifacts["opportunities"]),
                            out=str(work_dir / "job_analyses.json"),
                            llm_model=llm_model,
                        )
                    _show_result(result)
        with mc2:
            if st.button("Match resume", key="match_run_btn"):
                if "opportunities" not in artifacts:
                    st.warning("No opportunities found. Run extraction first.")
                else:
                    analyses = str(artifacts["job_analyses"]) if "job_analyses" in artifacts else ""
                    with st.spinner("Matching resume against jobs..."):
                        result = cmd_match(
                            resume=resume,
                            opportunities=str(artifacts["opportunities"]),
                            analyses=analyses,
                            out=str(out_dir / "matches"),
                            llm_model=llm_model,
                        )
                    _show_result(result)
                    if result.ok:
                        st.rerun()

    if "match_results" not in artifacts:
        st.info("No match results found. Run the Match action above.")
        return

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
            st.json(sorted_matches[idx])

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

    # ----- Tailor action -----
    with st.expander("Generate tailored resumes", expanded="tailoring_results" not in artifacts):
        resume = _resume_picker("tailor")
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            min_score = st.number_input("Min score", 0.0, 100.0, 70.0, key="tailor_min_score")
        with tc2:
            recommendation = st.text_input("Recommendations (comma-sep)", value="strong_apply,apply", key="tailor_rec")
        with tc3:
            top_n = st.number_input("Top N (0 = all)", 0, 100, 5, key="tailor_top")
        no_docx = st.checkbox("Skip .docx generation", key="tailor_no_docx")

        if st.button("Tailor resumes", key="tailor_run_btn"):
            if "match_results" not in artifacts:
                st.warning("No match results found. Run matching first.")
            else:
                with st.spinner("Tailoring resumes..."):
                    result = cmd_tailor(
                        resume=resume,
                        match_results=str(artifacts["match_results"]),
                        out=str(out_dir / "tailored"),
                        opportunities=str(artifacts.get("opportunities", "")),
                        min_score=min_score if min_score > 0 else None,
                        recommendation=recommendation,
                        top=top_n if top_n > 0 else None,
                        no_docx=no_docx,
                    )
                _show_result(result)
                if result.ok:
                    st.rerun()

    if "tailoring_results" not in artifacts:
        st.info("No tailoring results found. Run tailoring above.")
        return

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

    # ----- Compose action -----
    with st.expander("Compose reply emails", expanded="drafts" not in artifacts):
        resume = _resume_picker("compose")
        llm_model = _llm_model_picker("compose")
        cc1, cc2 = st.columns(2)
        with cc1:
            questionnaire = _file_picker("Questionnaire JSON", "compose_q", default="examples/questionnaire.json")
        with cc2:
            recommendation = st.text_input("Recommendations", value="strong_apply,apply", key="compose_rec")
        top_n = st.number_input("Top N (0 = all)", 0, 100, 5, key="compose_top")

        if st.button("Compose drafts", key="compose_run_btn"):
            if "match_results" not in artifacts:
                st.warning("No match results found. Run matching first.")
            else:
                with st.spinner("Composing reply emails..."):
                    result = cmd_compose(
                        resume=resume,
                        match_results=str(artifacts["match_results"]),
                        out=str(out_dir / "replies"),
                        opportunities=str(artifacts.get("opportunities", "")),
                        questionnaire=questionnaire if Path(questionnaire).exists() else "",
                        tailored_dir=str(out_dir / "tailored") if "tailoring_results" in artifacts else "",
                        recommendation=recommendation,
                        top=top_n if top_n > 0 else None,
                        llm_model=llm_model,
                    )
                _show_result(result)
                if result.ok:
                    st.rerun()

    if "drafts" not in artifacts:
        st.info("No drafts found. Compose reply emails above.")
        return

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

    # ----- Draft preview + edit -----
    st.subheader("Draft Preview & Edit")
    idx = st.number_input("Draft index", 0, max(len(drafts) - 1, 0), 0, key="draft_preview_idx")
    if 0 <= idx < len(drafts):
        d = drafts[idx]
        st.markdown(f"**To:** {d.get('to', 'N/A')}")

        # Editable subject and body
        new_subject = st.text_input("Subject", value=d.get("subject", ""), key="draft_edit_subject")
        new_body = st.text_area("Body", value=d.get("body", ""), height=300, key="draft_edit_body")

        if d.get("in_reply_to"):
            st.caption(f"In-Reply-To: {d['in_reply_to']}")
        if d.get("attachment_paths"):
            st.markdown("**Attachments:**")
            for att in d["attachment_paths"]:
                st.caption(f"  {att}")

        # Save edits back to the drafts JSON file
        if st.button("Save edits to drafts.json", key="draft_save_btn"):
            drafts[idx]["subject"] = new_subject
            drafts[idx]["body"] = new_body
            _save_drafts(artifacts["drafts"], drafts)
            st.success(f"Draft {idx} updated and saved.")

    if "drafts_preview" in artifacts:
        with st.expander("Full Drafts Preview (Markdown)"):
            md = artifacts["drafts_preview"].read_text(encoding="utf-8")
            st.markdown(md)


def _save_drafts(path: Path, drafts: list) -> None:
    """Write modified drafts back to the JSON file."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["drafts"] = drafts
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")


# ============================================================================
# Reply Results
# ============================================================================

def _page_reply_results() -> None:
    st.header("Reply Send Results")

    # ----- Send / dry-run action -----
    with st.expander("Send or preview replies", expanded="reply_results" not in artifacts):
        rc1, rc2 = st.columns(2)
        with rc1:
            dry_run = st.checkbox("Dry run (preview only)", value=True, key="reply_dry_run")
        with rc2:
            send_index = st.number_input("Send only index (-1 = all)", -1, 100, -1, key="reply_index")
        rc3, rc4 = st.columns(2)
        with rc3:
            override_to = st.text_input("Override recipient (testing)", key="reply_override")
        with rc4:
            bcc = st.text_input("BCC (audit)", key="reply_bcc")

        if st.button("Send / preview", key="reply_send_btn"):
            drafts_path = artifacts.get("drafts")
            if not drafts_path:
                st.warning("No drafts found. Compose emails first.")
            else:
                with st.spinner("Sending/previewing emails..."):
                    result = cmd_reply(
                        drafts=str(drafts_path),
                        out=str(out_dir / "replies"),
                        dry_run=dry_run,
                        index=send_index if send_index >= 0 else None,
                        override_to=override_to,
                        bcc=bcc,
                    )
                _show_result(result)
                if result.ok:
                    st.rerun()

    if "reply_results" not in artifacts:
        st.info("No reply results found. Send or dry-run above.")
        return

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
    from collections import Counter
    statuses = [r.get("status", "unknown") for r in results]
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

    # ----- Correlate action -----
    with st.expander("Run correlation", expanded="correlation" not in artifacts):
        resume = _resume_picker("corr")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            min_score = st.number_input("Min score", 0.0, 100.0, 0.0, key="corr_min_score")
        with cc2:
            recommendation = st.text_input("Recommendations", value="", key="corr_rec")
        with cc3:
            top_n = st.number_input("Top N (0 = all)", 0, 100, 0, key="corr_top")

        if st.button("Correlate", key="corr_run_btn"):
            with st.spinner("Correlating artifacts..."):
                result = cmd_correlate(
                    out=str(out_dir / "correlation"),
                    work_dir=str(work_dir),
                    out_dir=str(out_dir),
                    resume=resume if Path(resume).exists() else "",
                    min_score=min_score if min_score > 0 else None,
                    recommendation=recommendation,
                    top=top_n if top_n > 0 else None,
                )
            _show_result(result)
            if result.ok:
                st.rerun()

    if "correlation" not in artifacts:
        st.info("No correlation data found. Run correlation above.")
        return

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
# Application Tracker
# ============================================================================

def _page_application_tracker() -> None:
    st.header("Application Tracker")

    # ----- Init tracking action -----
    with st.expander("Initialise / refresh tracking", expanded="tracking" not in artifacts):
        if st.button("Initialise from correlation", key="track_init_btn"):
            if "correlation" not in artifacts:
                st.warning("No correlation data found. Run correlation first.")
            else:
                tracking_file = str(out_dir / "tracking" / "tracking.json")
                kwargs = {
                    "out": str(out_dir / "tracking"),
                    "out_dir": str(out_dir),
                    "individual_cards": True,
                    "full_report": True,
                }
                if Path(tracking_file).exists():
                    kwargs["tracking_file"] = tracking_file
                with st.spinner("Initialising tracking..."):
                    result = cmd_track(**kwargs)
                _show_result(result)
                if result.ok:
                    st.rerun()

    if "tracking" not in artifacts:
        st.info("No tracking data found. Initialise tracking above.")
        return

    data = load_tracking(artifacts["tracking"])
    summary = data.get("summary", {})
    applications = data.get("tracked_applications", [])

    if not applications:
        st.info("No tracked applications.")
        return

    # ----- Summary metrics -----
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tracked", summary.get("total_tracked", 0))
    col2.metric("Active", summary.get("active_count", 0))
    col3.metric("Interviews", summary.get("total_interviews", 0))
    col4.metric("Offers", summary.get("offers_received", 0))

    if summary.get("avg_match_score", 0) > 0:
        st.caption(f"Avg match score: {summary['avg_match_score']:.1f}")

    # ----- Status distribution -----
    by_status = summary.get("by_status", {})
    if by_status:
        st.subheader("Status Distribution")
        st.bar_chart(by_status)

    # ----- Outcome distribution -----
    by_outcome = summary.get("by_outcome", {})
    if by_outcome:
        st.subheader("Outcomes")
        st.bar_chart(by_outcome)

    # ----- Applications table -----
    rows = []
    for app in applications:
        rows.append({
            "Job Title": (app.get("job_title") or "N/A")[:40],
            "Company": (app.get("company") or "N/A")[:25],
            "Status": app.get("status", "N/A"),
            "Outcome": app.get("final_outcome") or "--",
            "Score": f"{app.get('match_score', 0):.0f}" if app.get("match_score") is not None else "N/A",
            "Interviews": len(app.get("interviews", [])),
            "Offer": "Yes" if app.get("offer") else "No",
        })
    st.dataframe(rows, use_container_width=True)

    # ----- Detail view -----
    with st.expander("Application details"):
        idx = st.number_input(
            "Application index", 0, max(len(applications) - 1, 0), 0,
            key="track_detail_idx",
        )
        if 0 <= idx < len(applications):
            st.json(applications[idx])

    # ----- Update actions -----
    st.subheader("Update Application")

    job_ids = [app.get("job_id", "") for app in applications]
    job_labels = [
        f"{app.get('job_title', 'Unknown')[:30]} at {app.get('company', 'Unknown')[:20]} ({app.get('job_id', '')[:15]}...)"
        for app in applications
    ]

    selected_idx = st.selectbox(
        "Select application", range(len(job_labels)),
        format_func=lambda i: job_labels[i],
        key="track_update_select",
    )
    selected_job_id = job_ids[selected_idx] if job_ids else ""

    action = st.selectbox(
        "Action", ["status", "outcome", "interview", "offer", "note"],
        key="track_update_action",
    )

    update_kwargs: dict = {
        "tracking_file": str(artifacts["tracking"]),
        "job_id": selected_job_id,
        "action": action,
        "out": str(out_dir / "tracking"),
    }

    if action == "status":
        update_kwargs["status"] = st.selectbox(
            "New status",
            ["applied", "interviewing", "offered", "closed"],
            key="track_new_status",
        )
        update_kwargs["note"] = st.text_input("Note (optional)", key="track_status_note")

    elif action == "outcome":
        update_kwargs["outcome"] = st.selectbox(
            "Outcome",
            ["accepted", "declined", "rejected", "withdrawn", "ghosted"],
            key="track_outcome",
        )
        update_kwargs["note"] = st.text_input("Note (optional)", key="track_outcome_note")

    elif action == "interview":
        update_kwargs["interview_type"] = st.selectbox(
            "Interview type",
            ["phone_screen", "technical", "behavioral", "system_design",
             "hiring_manager", "panel", "onsite", "other"],
            key="track_interview_type",
        )
        update_kwargs["scheduled_at"] = st.text_input("Scheduled at (date/time)", key="track_sched")
        update_kwargs["interviewer"] = st.text_input("Interviewer name", key="track_interviewer")
        update_kwargs["completed"] = st.checkbox("Completed", key="track_completed")
        update_kwargs["note"] = st.text_input("Notes", key="track_interview_note")

    elif action == "offer":
        update_kwargs["salary"] = st.text_input("Salary", key="track_salary")
        update_kwargs["equity"] = st.text_input("Equity", key="track_equity")
        update_kwargs["bonus"] = st.text_input("Bonus", key="track_bonus")
        update_kwargs["start_date"] = st.text_input("Start date", key="track_start")
        update_kwargs["note"] = st.text_input("Notes", key="track_offer_note")

    elif action == "note":
        update_kwargs["note"] = st.text_input("Note", key="track_note_text")

    if st.button("Submit update", key="track_update_btn"):
        if not selected_job_id:
            st.warning("No application selected.")
        else:
            with st.spinner("Updating..."):
                result = cmd_track_update(**update_kwargs)
            _show_result(result)
            if result.ok:
                st.rerun()

    # ----- Markdown report -----
    if "tracking_summary" in artifacts:
        with st.expander("Tracking Summary Report (Markdown)"):
            md = artifacts["tracking_summary"].read_text(encoding="utf-8")
            st.markdown(md)


# ============================================================================
# Analytics
# ============================================================================

def _page_analytics() -> None:
    st.header("Pipeline Analytics")

    # ----- Regenerate action -----
    with st.expander("Regenerate analytics"):
        if st.button("Regenerate", key="analytics_regen_btn"):
            with st.spinner("Generating analytics..."):
                result = cmd_analytics(
                    out_dir=str(work_dir),
                    messages=str(artifacts.get("messages", "")),
                    opportunities=str(artifacts.get("opportunities", "")),
                )
            _show_result(result)
            if result.ok:
                st.rerun()

    if "analytics" not in artifacts:
        st.info("No analytics data found. Run the pipeline or regenerate above.")
        return

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
    "Inbox": _page_inbox,
    "Messages": _page_messages,
    "Opportunities": _page_opportunities,
    "Match Results": _page_match_results,
    "Tailored Resumes": _page_tailored_resumes,
    "Reply Drafts": _page_reply_drafts,
    "Reply Results": _page_reply_results,
    "Correlation": _page_correlation,
    "Application Tracker": _page_application_tracker,
    "Analytics": _page_analytics,
}

handler = _PAGE_MAP.get(page)
if handler:
    handler()
else:
    st.error(f"Unknown page: {page}")
