"""Execute pipeline CLI commands from the Streamlit UI via subprocess."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class RunResult:
    """Result of a pipeline command execution."""
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    ok: bool = field(init=False)

    def __post_init__(self) -> None:
        self.ok = self.returncode == 0


def _find_cli() -> str:
    """Return the ``email-pipeline`` executable path.

    Falls back to ``python -m email_opportunity_pipeline.cli`` when the
    entry-point script is not on PATH (e.g. editable installs without
    activating the venv).
    """
    found = shutil.which("email-pipeline")
    if found:
        return found
    # Fallback: caller will split on spaces, so return as a single string
    # that gets expanded later.
    return "email-pipeline"


def run_pipeline_command(args: List[str], timeout: int = 600) -> RunResult:
    """Run an ``email-pipeline`` CLI command and return the result.

    Parameters
    ----------
    args:
        Arguments to pass after ``email-pipeline`` (e.g. ``["fetch", "--provider", "gmail"]``).
    timeout:
        Maximum seconds before killing the subprocess.
    """
    cmd = [_find_cli()] + args
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return RunResult(
            command=cmd,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            command=cmd,
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
        )
    except FileNotFoundError:
        return RunResult(
            command=cmd,
            returncode=-1,
            stdout="",
            stderr="email-pipeline not found. Is the package installed?",
        )


# =========================================================================
# Convenience wrappers for each pipeline stage
# =========================================================================

def cmd_fetch(
    *,
    provider: str = "gmail",
    window: str = "1d",
    out: str,
    query: str = "",
    max_results: Optional[int] = None,
    metadata_only: bool = False,
) -> RunResult:
    args = ["fetch", "--provider", provider, "--window", window, "--out", out]
    if query:
        args += ["--query", query]
    if max_results:
        args += ["--max-results", str(max_results)]
    if metadata_only:
        args.append("--metadata-only")
    return run_pipeline_command(args)


def cmd_filter(
    *,
    input_path: str,
    out: str,
    rules: str = "",
    llm_filter: bool = False,
    llm_model: str = "gpt-4o-mini",
) -> RunResult:
    args = ["filter", "--in", input_path, "--out", out]
    if rules:
        args += ["--rules", rules]
    if llm_filter:
        args += ["--llm-filter", "--llm-model", llm_model]
    return run_pipeline_command(args)


def cmd_extract(
    *,
    input_path: str,
    out: str,
    llm_extract: bool = False,
    llm_model: str = "gpt-4o-mini",
) -> RunResult:
    args = ["extract", "--in", input_path, "--out", out]
    if llm_extract:
        args += ["--llm-extract", "--llm-model", llm_model]
    return run_pipeline_command(args)


def cmd_analyze(
    *,
    input_path: str,
    out: str,
    llm_model: str = "gpt-4o-mini",
) -> RunResult:
    args = ["analyze", "--in", input_path, "--out", out, "--llm-model", llm_model]
    return run_pipeline_command(args)


def cmd_match(
    *,
    resume: str,
    opportunities: str,
    out: str,
    analyses: str = "",
    individual_reports: bool = True,
    llm_model: str = "gpt-4o-mini",
) -> RunResult:
    args = ["match", "--resume", resume, "--opportunities", opportunities,
            "--out", out, "--llm-model", llm_model]
    if analyses:
        args += ["--analyses", analyses]
    if individual_reports:
        args.append("--individual-reports")
    return run_pipeline_command(args)


def cmd_tailor(
    *,
    resume: str,
    match_results: str,
    out: str,
    opportunities: str = "",
    min_score: Optional[float] = None,
    recommendation: str = "",
    top: Optional[int] = None,
    no_docx: bool = False,
) -> RunResult:
    args = ["tailor", "--resume", resume, "--match-results", match_results, "--out", out]
    if opportunities:
        args += ["--opportunities", opportunities]
    if min_score is not None:
        args += ["--min-score", str(min_score)]
    if recommendation:
        args += ["--recommendation", recommendation]
    if top is not None:
        args += ["--top", str(top)]
    if no_docx:
        args.append("--no-docx")
    return run_pipeline_command(args)


def cmd_compose(
    *,
    resume: str,
    match_results: str,
    out: str,
    opportunities: str = "",
    questionnaire: str = "",
    tailored_dir: str = "",
    min_score: Optional[float] = None,
    recommendation: str = "",
    top: Optional[int] = None,
    llm_model: str = "gpt-4o-mini",
) -> RunResult:
    args = ["compose", "--resume", resume, "--match-results", match_results,
            "--out", out, "--llm-model", llm_model]
    if opportunities:
        args += ["--opportunities", opportunities]
    if questionnaire:
        args += ["--questionnaire", questionnaire]
    if tailored_dir:
        args += ["--tailored-dir", tailored_dir]
    if min_score is not None:
        args += ["--min-score", str(min_score)]
    if recommendation:
        args += ["--recommendation", recommendation]
    if top is not None:
        args += ["--top", str(top)]
    return run_pipeline_command(args)


def cmd_reply(
    *,
    drafts: str,
    out: str,
    dry_run: bool = True,
    index: Optional[int] = None,
    override_to: str = "",
    cc: str = "",
    bcc: str = "",
) -> RunResult:
    args = ["reply", "--drafts", drafts, "--out", out]
    if dry_run:
        args.append("--dry-run")
    if index is not None:
        args += ["--index", str(index)]
    if override_to:
        args += ["--override-to", override_to]
    if cc:
        args += ["--cc", cc]
    if bcc:
        args += ["--bcc", bcc]
    return run_pipeline_command(args)


def cmd_correlate(
    *,
    out: str,
    work_dir: str = "",
    out_dir: str = "",
    resume: str = "",
    individual_cards: bool = True,
    full_report: bool = True,
    min_score: Optional[float] = None,
    recommendation: str = "",
    top: Optional[int] = None,
) -> RunResult:
    args = ["correlate", "--out", out]
    if work_dir:
        args += ["--work-dir", work_dir]
    if out_dir:
        args += ["--out-dir", out_dir]
    if resume:
        args += ["--resume", resume]
    if individual_cards:
        args.append("--individual-cards")
    if full_report:
        args.append("--full-report")
    if min_score is not None:
        args += ["--min-score", str(min_score)]
    if recommendation:
        args += ["--recommendation", recommendation]
    if top is not None:
        args += ["--top", str(top)]
    return run_pipeline_command(args)


def cmd_analytics(
    *,
    out_dir: str,
    messages: str = "",
    opportunities: str = "",
) -> RunResult:
    args = ["analytics", "--out-dir", out_dir]
    if messages:
        args += ["--messages", messages]
    if opportunities:
        args += ["--opportunities", opportunities]
    return run_pipeline_command(args)
