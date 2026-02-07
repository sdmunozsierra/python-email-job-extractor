set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

work_dir := "data"
out_dir := "output"
resume := "examples/sample_resume.json"
questionnaire := "examples/questionnaire.json"
provider := "gmail"
window := "2d"

messages := work_dir + "/messages.json"
filtered := work_dir + "/filtered.json"
opportunities := work_dir + "/opportunities.json"
analyses := work_dir + "/job_analyses.json"
match_results := out_dir + "/matches/match_results.json"
tailored_dir := out_dir + "/tailored"
replies_dir := out_dir + "/replies"
drafts := replies_dir + "/drafts.json"
drafts_preview := replies_dir + "/drafts_preview.md"

@help:
  just --list

@install:
  uv sync

@run-all send="":
  uv run email-pipeline run-all \
    --resume {{resume}} \
    --questionnaire {{questionnaire}} \
    --provider {{provider}} --window {{window}} \
    --work-dir {{work_dir}} --out-dir {{out_dir}} \
    {{send}}

@fetch window=window out=messages:
  uv run email-pipeline fetch --provider {{provider}} --window {{window}} --out {{out}}

@filter in=messages out=filtered:
  uv run email-pipeline filter --in {{in}} --out {{out}}

@extract in=filtered out=opportunities:
  uv run email-pipeline extract --in {{in}} --out {{out}}

@analyze in=opportunities out=analyses:
  uv run email-pipeline analyze --in {{in}} --out {{out}}

@match in=opportunities resume=resume out=out_dir + "/matches" min_score="" recommendation="":
  uv run email-pipeline match \
    --in {{in}} \
    --resume {{resume}} \
    --out {{out}} \
    {{if min_score != "" {"--min-score " + min_score} else {""}}} \
    {{if recommendation != "" {"--recommendation " + recommendation} else {""}}}

@rank in=match_results out=out_dir + "/ranked":
  uv run email-pipeline rank --in {{in}} --out {{out}}

@tailor match_results=match_results opportunities=opportunities resume=resume out=tailored_dir recommendation="" top="":
  uv run email-pipeline tailor \
    --match-results {{match_results}} \
    --opportunities {{opportunities}} \
    --resume {{resume}} \
    --out {{out}} \
    {{if recommendation != "" {"--recommendation " + recommendation} else {""}}} \
    {{if top != "" {"--top " + top} else {""}}}

@compose match_results=match_results opportunities=opportunities questionnaire=questionnaire resume=resume tailored_dir=tailored_dir out=replies_dir recommendation="" top="":
  uv run email-pipeline compose \
    --match-results {{match_results}} \
    --opportunities {{opportunities}} \
    --questionnaire {{questionnaire}} \
    --resume {{resume}} \
    --tailored-dir {{tailored_dir}} \
    --out {{out}} \
    {{if recommendation != "" {"--recommendation " + recommendation} else {""}}} \
    {{if top != "" {"--top " + top} else {""}}}

@reply-preview drafts=drafts out=replies_dir:
  uv run email-pipeline reply --drafts {{drafts}} --out {{out}} --dry-run

@edit-preview file=drafts_preview:
  ${EDITOR:-vi} {{file}}

@reply-send drafts=drafts out=replies_dir override_to="" cc="" bcc="":
  uv run email-pipeline reply \
    --drafts {{drafts}} \
    --out {{out}} \
    {{if override_to != "" {"--override-to " + override_to} else {""}}} \
    {{if cc != "" {"--cc " + cc} else {""}}} \
    {{if bcc != "" {"--bcc " + bcc} else {""}}}

@render in=opportunities out=out_dir + "/rendered":
  uv run email-pipeline render --in {{in}} --out {{out}}

@analytics in=opportunities out=work_dir + "/analytics.json":
  uv run email-pipeline analytics --in {{in}} --out {{out}}

@correlate work_dir=work_dir out_dir=out_dir out="correlation" individual_cards="--individual-cards" full_report="--full-report":
  uv run email-pipeline correlate \
    --work-dir {{work_dir}} \
    --out-dir {{out_dir}} \
    --out {{out}} \
    {{individual_cards}} \
    {{full_report}}

@open-correlation report="correlation/report.md":
  ${EDITOR:-vi} {{report}}
