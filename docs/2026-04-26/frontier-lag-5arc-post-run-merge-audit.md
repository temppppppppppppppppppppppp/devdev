# Frontier Lag 5Arc Post-Run Merge Audit

Date: 2026-04-26
Track: system order / live-run post-run audit
Status: final survey, 3-pass audited
Confidence: 96%

## Scope

This document finalizes the post-run interpretation for the 2026-04-26 Frontier Lag run:

```powershell
python scripts/run_auto_frontier_lag_harness.py run --arc-count 5 --target-project "0_골든카나리아" --reuse-existing-project --poll-interval-seconds 300
```

It supersedes the provisional watchlist in `docs/2026-04-26/frontier-lag-5arc-live-run-watchlist.md`.

It does not commit the generated project artifacts, decide whether to publish the manuscript output, or open a code-fix lane by itself.

## Commit State

Baseline Commit: `6cdd8fe99b685ae489f9552b9d10e5940eb91838`

Baseline Dirty Summary:

- `0_temp.txt` modified by live-run/operator state.
- `docs/2026-04-26/frontier-lag-5arc-live-run-watchlist.md` exists as a draft live-run watchlist.
- `docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md` exists as generated analyzer output with `finalized: False`.
- `projects/0_골든카나리아/` contains the generated run artifacts and DB.

## Evidence Inputs

Primary runtime artifacts:

- `projects/0_골든카나리아/logs/auto_frontier_lag_worker_result.json`
- `projects/0_골든카나리아/logs/auto_frontier_lag_analysis.json`
- `projects/0_골든카나리아/logs/auto_frontier_lag_failure_digest.json`
- `projects/0_골든카나리아/logs/auto_frontier_lag_poll_history.jsonl`
- `projects/0_골든카나리아/logs/runtime_audit_summary.json`
- `projects/0_골든카나리아/logs/pass_rate_monitor.json`
- `projects/0_골든카나리아/project_data.db`

Code and test anchors:

- `main_a.py:3973` through `main_a.py:3997`
- `main_a.py:4174` through `main_a.py:4208`
- `main_a.py:4490` through `main_a.py:4584`
- `scripts/run_auto_frontier_lag_harness.py:800` through `scripts/run_auto_frontier_lag_harness.py:925`
- `tests/test_one_stop_frontier_lag_auto_continue.py:704` through `tests/test_one_stop_frontier_lag_auto_continue.py:722`

Artifact truth checks:

- 9 `stage_attempts` rows were present in `project_data.db`.
- 8 attempts had artifact paths and all 8 artifact files existed.
- All 8 artifact hashes matched the persisted `content_hash` values.
- The remaining attempt, `s3:ep4:arc1:a10:20260426_171126`, had blank artifact path and blank content hash because it was the terminal failed Stage3 attempt.

DB count highlights:

- `stage_attempts`: 9
- `director_selections`: 9
- `blueprints`: 3
- `manuscripts`: 2
- `episode_bibles`: 2
- `episode_meta`: 2
- `ui_events`: 707
- `llm_calls`: 130

## Final Run Interpretation

The run reached a terminal state:

- Worker process exited with code `0`.
- Harness manifest status ended as `worker_success`.
- Worker result status was `success`.
- Runtime shutdown final timestamp was `2026-04-26 18:48:59`.

The requested 5-arc boundary was not reached:

- Requested arc limit: `5`
- `arcs_advanced`: `1`
- `requested_limit_hit`: `false`
- `total_manuscripts`: `2`
- `stop_reason`: `stage3_user_abort`

This is therefore a successful harness/process completion but a failed 5-arc boundary run.

## Root Cause

The immediate stopping point was Stage3 for episode 4:

- Attempt key: `s3:ep4:arc1:a10:20260426_171126`
- Stage: `3`
- Episode: `4`
- Attempt: `10`
- Final verdict: `FAILED`
- Score: `95`
- Persisted contradiction: Blueprint time flow used `2006년 1월 1일` while Arc state required `2006년 1월 3일`.

After Stage3 produced zero successes and at least one failure, the Frontier Lag code correctly entered its human-in-the-loop boundary:

- `main_a.py:4184` checks `s3_success == 0 and s3_fail > 0`.
- `main_a.py:4190` asks whether to skip the failed Arc or stop.
- `main_a.py:4198` to `main_a.py:4208` returns `stop_reason: stage3_user_abort` unless the operator chooses skip.
- The test at `tests/test_one_stop_frontier_lag_auto_continue.py:704` through `tests/test_one_stop_frontier_lag_auto_continue.py:722` explicitly covers this stop path.

So the final blocker is not a harness crash. It is a Stage3 content/continuity failure followed by the currently intentional HIL stop policy.

## Authority Alignment Check

This run did not violate the workspace principle that Python must not make the final pass/reject judgment.

Observed authority chain:

- LLM/Director verdict surfaces recorded Stage3 ep4 as `FAILED`.
- Python runtime routed the pipeline after that verdict and after the HIL policy branch.
- Python did not silently convert the failed Stage3 attempt into a PASS.
- The generated analyzer's `judgment: failed` is an operational boundary judgment, not a narrative quality override.

The subtle distinction matters:

- Narrative/content acceptance remained LLM/Director-owned.
- Runtime continuation remained Python/HIL policy-owned after the Director failure.

## Stage Results

Stage2:

- 2 Stage2 attempts.
- Both had persisted artifact paths.
- Both artifact hashes matched DB hashes.
- Runtime proof digest status: `ok`.

Stage3:

- 4 Stage3 attempts.
- Episodes 1, 2, and 3 produced blueprint artifacts.
- Episode 4 failed after attempt 10 with no final artifact.
- Runtime proof digest status: `warn`.
- The warning is consistent with the failed terminal Stage3 attempt having no artifact metadata.

Stage4:

- 3 Stage4 attempts across 2 episodes.
- Episode 1 manuscript passed.
- Episode 2 first attempt rejected, then patched/in-place attempt passed.
- 2 final manuscript outputs exist.
- Runtime proof digest status: `warn` because selection/verdict/runtime advisory mismatch fields and rationale metadata gaps remain in the proof digest.

## Artifact Truth

Generated user-visible outputs exist for the portion of the run that completed:

- `projects/0_골든카나리아/plans/arcs/arc_001.txt`
- `projects/0_골든카나리아/plans/arcs/arc_002.txt`
- `projects/0_골든카나리아/plans/blueprints/blueprint_0001.txt`
- `projects/0_골든카나리아/plans/blueprints/blueprint_0002.txt`
- `projects/0_골든카나리아/plans/blueprints/blueprint_0003.txt`
- `projects/0_골든카나리아/drafts/ep_0001.txt`
- `projects/0_골든카나리아/drafts/ep_0002.txt`

Counts observed by path census:

- `plans/arcs`: 2 files
- `plans/blueprints`: 3 files
- `drafts`: 4 files including settlement JSON files
- `logs/artifacts/stage2`: 2 final arc JSON files
- `logs/artifacts/stage3`: 3 final blueprint JSON files
- `logs/artifacts/stage4`: 6 manuscript/retry artifact files

## Side-Effect Coverage

File writes:

- Project DB, session logs, metrics, runtime audit, artifact JSON/TXT files, plans, drafts, and generated analysis files were written under `projects/0_골든카나리아/`.

DB writes:

- `project_data.db` existed at shutdown and had 14,241,792 bytes.
- Relevant persisted tables include `stage_attempts`, `director_selections`, `blueprints`, `manuscripts`, `episode_bibles`, `episode_meta`, `cost_log`, and `ui_events`.

JSONL/log/audit sinks:

- `runtime_audit.jsonl`, `episode_production.jsonl`, `quality_metrics.jsonl`, session JSONL logs, and poll history were present.

Console/UI:

- The poll history captured live liveness and terminal process exit.
- Terminal rendering was not used as encoding evidence.

Rollback/retry:

- Stage4 retry and in-place patch path were exercised.
- Stage3 retry exhausted on ep4 and then entered the HIL stop path.

Cache/global state:

- Context cache and vector-related tables were present, but no code-level cache mutation was changed by this audit.

Config/env:

- The run used `config/author_directives.txt` and `config/work_guard.yaml` inside the generated project.
- No repository config or environment file was changed by this audit.

## 3-Pass Audit

Pass 1 - fact extraction:

- PASS. Worker result, harness manifest, poll history, runtime analysis, runtime summary, DB counts, and artifact paths agree on a terminal run ending at `2026-04-26 18:48:59`.
- PASS. The run advanced 1 arc, produced 2 manuscripts, and did not reach the requested 5-arc boundary.

Pass 2 - contradiction check:

- PASS. `worker_status: success` and `judgment: failed` are not contradictory because they refer to different layers: process completion versus requested boundary outcome.
- PASS. The earlier generated auto analysis has `confidence: 90%` and `finalized: False`; this document does not treat it as final authority.
- PASS. The first DB probe that returned `db_exists: false` was discarded because Korean path transfer into inline Python was faulty; PowerShell path resolution plus Python argument passing confirmed the DB exists.

Pass 3 - decision audit:

- PASS. The root cause is bounded to Stage3 ep4 timeline contradiction plus the intentional HIL stop path.
- PASS. No claim is made that the whole content pipeline is globally broken.
- PASS. No claim is made that Python made the narrative pass/reject decision.
- PASS. The audit separates completed artifacts from the failed requested 5-arc boundary.

Confidence:

- 96%.
- The score is not higher because generated artifact content quality was not deeply line-edited in this audit; the audit focuses on run boundary, authority alignment, sink integrity, and artifact existence/hash truth.

## Follow-Up Decision

Recommended next lane if we continue:

1. Decide whether Frontier Lag should remain HIL-blocking on Stage3 failure or gain a bounded, explicit auto-skip policy for unattended harness runs.
2. Investigate the Stage3 ep4 timeline contradiction source: Arc state expected `2006년 1월 3일`, but candidate blueprint metadata used `2006년 1월 1일`.
3. Consider adding a failed-Stage3 diagnostic artifact so terminal failed attempts do not produce blank artifact metadata.
4. Re-audit Stage4 proof digest warnings separately if we want to close the remaining selection/verdict/runtime advisory mismatch signals.

No `docs/temp/` execution mirror is created by this audit. The follow-up items are real, but they should be split into an execution SSOT only after we choose which lane to realize first.
