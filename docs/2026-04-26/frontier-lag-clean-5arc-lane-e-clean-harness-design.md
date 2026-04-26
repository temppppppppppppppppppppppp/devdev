# Frontier Lag Clean 5-Arc Lane E - Clean Harness Design

Date: 2026-04-26
Track: system order / Lane E (Terminal 5)
Status: read-only design draft, 3-pass audited
Document Type: harness policy design (no code patch)
Canonical Path: `docs/2026-04-26/frontier-lag-clean-5arc-lane-e-clean-harness-design.md`
Source Order Pack: `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
Baseline Commit: `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
Baseline Dirty Summary:
- `M 0_temp.txt`
- `?? docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `?? docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
- `?? projects/0_골든카나리아/`

## Scope

This document is the Lane E lane report. It addresses the six required harness topics from the order pack:

- separate `process_success` from `objective_success`
- stop showing worker status success as if the requested 5-arc objective passed
- distinguish real operator stop from no-input / default stop
- define Stage3 failure policy options: stop, skip, quarantine
- define strict-quality run vs survey-run behavior
- define final analyzer root-cause naming

It is read-only design. It does not patch code, change tests, edit factsheets, edit blueprints, or relax Director authority. Strict-quality is preserved as the default. Any softer behavior is opt-in.

This lane does not design the continuity bridge packet (Lane D) nor the failure forensic ingest path (Lane A). Where Lane E touches those surfaces, it surfaces the contract boundary only.

## Evidence

### E1. Process success vs objective success surfaces in the observed run

- `scripts/run_auto_frontier_lag_harness.py:551-562` writes `auto_frontier_lag_worker_result.json` with `"status": "success"` and updates the manifest to `"status": "worker_success"` whenever the worker subprocess does not raise. The status is set independently of `frontier_result.arcs_advanced` and `frontier_result.requested_limit_hit`.
- `scripts/run_auto_frontier_lag_harness.py:856-859` is the only place that re-derives objective truth: `boundary_reached = bool(frontier_result.requested_limit_hit) or arcs_advanced >= arc_count`.
- `scripts/run_auto_frontier_lag_harness.py:952-973` collapses the analyzer judgment to two values: `"success"` or `"failed"` (plus `"stalled"`). There is no third value to mark "process completed but objective not reached".
- `main_a.py:4417-4452` emits a "파이프라인 완료 보고" finalize log even when `arcs_advanced < requested_arc_limit` and `stop_reason` is a stop literal, because the finalize function does not branch on objective state.

### E2. HIL boundary in the observed run

- `main_a.py:4184-4208` (Stage3 fail-count branch) calls `self._get_choice_input("...건너뛰고 다음 Arc로? (1=건너뛰기 / 2=중단, 기본: 2): ", choices=("1","2"), default="2", prompt_id="frontier_lag_stage3_skip_choice")`. The branch returns `stop_reason: stage3_user_abort` for both an explicit operator "2" and an empty / EOF response that falls through to the default.
- `main_a.py:4224-4256` (Stage3 exception branch) repeats the same prompt with `prompt_id="frontier_lag_stage3_exception_skip_choice"` and returns `stop_reason: stage3_exception_user_abort`.
- `modules/core/services/ui_service.py:255` defines `get_choice_input`. Its non-interactive contract returns the normalized default silently when stdin is empty or `EOFError` is raised, and emits no telemetry distinguishing "operator typed default" from "no operator present".

### E3. Observed run terminal state

- Worker subprocess exit code `0`, harness manifest status `worker_success`, worker result status `success`.
- `frontier_result`: `arcs_advanced=1`, `requested_arc_limit=5`, `requested_limit_hit=false`, `stop_reason=stage3_user_abort`.
- Analyzer payload: `judgment=failed`, `confidence=90`, `finalized=False`.
- This shows three layers (worker, manifest, console finalize log) emitting "success / 완료" while two layers (analyzer, frontier_result) correctly hold "boundary not reached". The mismatch is the operator hazard.

### E4. Existing CLI surface

- `scripts/run_auto_frontier_lag_harness.py:201-236` defines `parse_args` with sub-commands `plan`, `worker`, `run`, `analyze`. Existing options: `--arc-count`, `--trigger`, `--seed-profile`, `--batch-size`, `--target-project`, `--reuse-existing-project`, `--operational-attempt-cap`, `--soak-profile`, `--poll-interval-seconds`, `--project`.
- Absent: any `--mode`, `--stage3-failure-policy`, `--stage3-skip-budget`, `--quarantine`, `--operator-present` flag. There is no run-mode toggle today.

### E5. Stop reason vocabulary today

Inventory across `main_a.py` Frontier Lag family:

| Literal | Anchor | Source layer |
| --- | --- | --- |
| `completed` | `main_a.py:4412` | initial sentinel before loop |
| `requested_arc_limit_reached` | `main_a.py:4502` | objective limit hit |
| `stage2_design_error` | `main_a.py:4150` | Stage2 exception |
| `stage2_arc_missing_after_generation` | `main_a.py:4164` | Stage2 verification miss |
| `final_close_plan_missing` | `main_a.py:4067` | final close, no arcs |
| `stage3_final_close_error` | `main_a.py:4092` | final close, Stage3 exception |
| `stage3_user_abort` | `main_a.py:4206` | Stage3 fail-count + HIL "2" or default |
| `stage3_exception_user_abort` | `main_a.py:4245` | Stage3 exception + HIL "2" or default |
| `stage4_final_close_no_progress` | `main_a.py:4113` | final close, Stage4 backlog flat |
| `stage4_final_close_error` | `main_a.py:4125` | final close, Stage4 exception |
| `stage4_no_progress_blocked` | `main_a.py:4281` | Stage4 sync, backlog flat |
| `stage4_error` | `main_a.py:4301` | Stage4 unhandled exception |
| `keyboard_interrupt` | `main_a.py:4296` | Stage4 KeyboardInterrupt |
| `frontier_plan_missing` | `main_a.py:4325` | plan computation failure |

Two of these (`stage3_user_abort`, `stage3_exception_user_abort`) carry the "user" semantic but are reachable without any operator action.

### E6. Test coverage today

- `tests/test_one_stop_frontier_lag_auto_continue.py:679-722` covers the Stage3 fail-count stop path. The test mocks `get_choice_input` with `return_value="2"` and asserts `stop_reason == "stage3_user_abort"`. It does not differentiate "operator typed 2" from "no operator present, default taken".
- `tests/test_one_stop_frontier_lag_auto_continue.py:583-621` covers the Stage3 skip-to-continue path with mocked operator typing "1".
- `tests/test_one_stop_frontier_lag_auto_continue.py:725-761` covers `stage4_no_progress_blocked`.
- `tests/test_one_stop_frontier_lag_auto_continue.py:764-851` covers `requested_arc_limit_reached`.
- No test exercises the `frontier_lag_stage3_exception_skip_choice` branch.
- No test exercises an explicit EOF on the Stage3 prompt.

## Findings

### F1. The harness conflates process and objective

Process completion (worker subprocess exit code, manifest status, `worker_result.status`) is emitted as `success` regardless of whether the requested 5-arc objective was reached. Only the analyzer payload at `scripts/run_auto_frontier_lag_harness.py:856-859, 952-973` and the `frontier_result` block carry the objective truth. This is the operator hazard: an unattended observer of manifest or console finalize output sees "success" before the analyzer payload is read.

### F2. The "stage3_user_abort" stop reason is not user-only

Because `_get_choice_input` returns the default silently on EOF and because both the explicit-2 and the EOF path share `stage_reason: stage3_user_abort`, the harness cannot distinguish "operator chose stop" from "no operator was present". This blocks honest unattended-run reporting and is the most important rename in the design.

### F3. Stage3 failure policy is binary today

Today's behavior is: prompt the operator with a 2-option choice (skip 1 arc / stop). There is no skip-budget, no quarantine path, no auto-policy for unattended runs. Strict-quality default is correct, but a survey/triage workflow needs an opt-in alternative.

### F4. Analyzer naming is shallow

`derive_judgment` returns only `success / failed / stalled`. `derive_root_cause` returns a thin set including `requested_arc_boundary_not_reached`, watchdog/worker variants, and stage sink-alignment variants. There is no value to express "boundary not reached because operator was absent and strict default fired" or "boundary not reached because skip budget exhausted". The judgment surface is therefore lossy for unattended ops.

### F5. Diagnostic snapshot for terminal Stage3 failure is absent

Per the Lane A scope and the post-run audit, the terminal failed Stage3 attempt persisted blank `artifact_path` and blank `content_hash`. Lane E does not own that fix, but the design must declare a contract slot for it (so harness reporting can carry the diagnostic id once Lane A or downstream implementation produces one).

### F6. Director authority is currently respected

The HIL boundary at `main_a.py:4184-4208` does not override Director verdicts; it only routes pipeline continuation. Lane E's design must keep this property: any new policy switch must move the routing decision, never the verdict decision.

## Design

### D1. Result semantics layering

Replace the single `status` axis with two axes that always travel together. Both must be present in `worker_result.json`, the harness manifest, and `auto_frontier_lag_analysis.json`.

- `process_status` (string) - what the subprocess did
  - `success` - subprocess returned without unhandled exception
  - `failed` - subprocess raised before final write
  - `stalled` - watchdog observed no progress past the idle threshold
- `objective_status` (string) - what the requested arc plan achieved
  - `achieved` - `arcs_advanced >= requested_arc_limit` and Director verdict path was clean for every advanced arc
  - `partial` - `arcs_advanced >= 1` but `< requested_arc_limit`
  - `not_reached` - `arcs_advanced == 0`
  - `aborted` - operator explicitly stopped before `requested_arc_limit`
  - `unknown` - process_status is `failed` or `stalled` and objective cannot be inferred
- `objective_arcs_advanced` and `objective_arcs_requested` carried as integers next to the strings.

Compatibility shim: `status` is allowed to remain in JSON as a derived view for one transition window, but the analyzer and the manifest read both new fields. The console finalize block at `main_a.py:4417-4452` must produce one of the four new objective lines regardless of process success.

### D2. HIL stop reason split

Replace `stage3_user_abort` and `stage3_exception_user_abort` with the explicit forms:

| New literal | When emitted |
| --- | --- |
| `stage3_operator_typed_stop` | operator explicitly typed `2` and operator presence was detected |
| `stage3_no_operator_default_stop` | operator presence was not detected, default `2` was taken under non-strict policy |
| `stage3_no_operator_strict_stop` | operator presence was not detected, strict policy fired without prompting |
| `stage3_skip_budget_exhausted_stop` | skip budget reached, next failure forced stop |
| `stage3_exception_operator_typed_stop` | exception path, operator typed `2` |
| `stage3_exception_no_operator_strict_stop` | exception path under strict policy without operator |

The compatibility shim period MAY emit the legacy literal alongside the new literal in JSON only, never as the canonical analyzer field. After the shim window, the legacy literals are removed.

### D3. Operator presence detection

Add a single explicit signal source. The harness reads it once at boot and writes the result to `manifest.operator_presence`.

- `--operator-present {yes,no,auto}` (default `auto`)
- `auto` resolves as `yes` only when stdin is a TTY at boot time of the worker subprocess.
- All Frontier Lag HIL choice points consult `manifest.operator_presence`. When it is `no`, the prompt is not written to stdin at all; the configured failure policy fires directly. When it is `yes`, the existing prompt path is used.

This change is read-only routing; Director still owns verdicts.

### D4. Stage3 failure policy options

Add `--stage3-failure-policy {strict,skip,quarantine}` with default `strict`.

- `strict` (default, current behavior preserved)
  - if operator present: prompt 2-option, default `2`
  - if operator absent: emit `stage3_no_operator_strict_stop` immediately, no prompt
- `skip` (opt-in, requires `--stage3-skip-budget N`, default `N=0` rejected)
  - if Stage3 fail-count branch fires: consume one skip; `arcs_advanced_delta=1`; continue with next arc
  - if budget reaches zero: next failure emits `stage3_skip_budget_exhausted_stop`
  - exception branch is not skip-eligible (defends against silent infrastructure faults); it falls back to strict
- `quarantine` (opt-in, requires explicit confirmation flag `--allow-quarantine`)
  - record the failed attempt with a diagnostic snapshot id (Lane A contract dependency)
  - mark the arc as `quarantined` in the harness manifest and DB-side state row (no factsheet edit; no blueprint synthesis; Python does not author content)
  - continue Stage4 only if Director or downstream Lane D bridge explicitly approves, otherwise skip Stage4 for the quarantined arc
  - `arcs_advanced_delta` is `0` for a quarantined arc; `objective_arcs_advanced` does not increment
  - the run still completes but `objective_status` cannot be `achieved` while any quarantined arc is pending Director adjudication

In all three policies the Director and validator authority remains unchanged. Quarantine only marks; Director still adjudicates.

### D5. Run mode separation

Add `--mode {strict-quality,survey}` with default `strict-quality`.

- `strict-quality` (default)
  - implies `--stage3-failure-policy=strict`
  - rejects `--stage3-failure-policy=skip` and `--stage3-failure-policy=quarantine` unless explicitly paired with the matching policy flag
  - any objective_status other than `achieved` is reported as a clear failure surface for follow-up
- `survey`
  - permits `skip` and `quarantine` policies
  - intended for evidence collection, root-cause discovery, and Lane D bridge probing
  - never overrides Director verdicts; survey runs are still subject to all validators
  - the analyzer marks the run with `objective_status=partial` rather than `failed` when survey policies were the reason a Stage3 arc was skipped or quarantined

This is the boundary that prevents survey relaxation from leaking into strict runs by accident.

### D6. Analyzer root cause naming

Extend `derive_root_cause` and `derive_judgment` outputs.

`derive_judgment` becomes:

- `success` - `process_status=success` and `objective_status=achieved`
- `partial` - `process_status=success` and `objective_status=partial`
- `not_reached` - `process_status=success` and `objective_status=not_reached`
- `aborted` - `objective_status=aborted` (explicit operator stop)
- `failed` - `process_status=failed`
- `stalled` - watchdog stalled or watchdog observed runtime failure

`derive_root_cause` is normalized so that the operator can read the cause without parsing strings:

- `boundary_reached_clean`
- `boundary_not_reached_no_operator_strict_stop`
- `boundary_not_reached_operator_typed_stop`
- `boundary_not_reached_skip_budget_exhausted`
- `boundary_not_reached_quarantine_pending_adjudication`
- `boundary_not_reached_stage4_no_progress`
- `boundary_not_reached_stage2_design_error`
- `worker_failed_<short_error_token>`
- `watchdog_stalled_after_two_idle_windows`
- `watchdog_observed_runtime_failure`

The new vocabulary preserves the Lane F principle that Python is not the narrative judge - these are operational labels for routing-level events, not content judgments.

### D7. Console finalize policy

The console finalize block at `main_a.py:4417-4452` must print exactly one of these lines as its final headline:

- `[FrontierLag] OBJECTIVE 달성: 5/5 Arc 전진 완료`
- `[FrontierLag] OBJECTIVE 부분 달성: arcs_advanced/requested 미달, root_cause=<...>`
- `[FrontierLag] OBJECTIVE 실패: 0개 Arc 전진, root_cause=<...>`
- `[FrontierLag] OBJECTIVE 운영자 중단: arcs_advanced/requested, root_cause=<...>`
- `[FrontierLag] PROCESS 실패: <short_error_token>`
- `[FrontierLag] WATCHDOG 정지: <stalled|failed>`

The current "파이프라인 완료" string is removed from the unconditional path; it survives only inside the OBJECTIVE 달성 line.

### D8. Diagnostic snapshot contract slot

For the Stage3 terminal failed attempt, the harness manifest gains a slot `stage3_terminal_failure_snapshot` with fields:

- `attempt_key` (existing)
- `diagnostic_artifact_path` (filled by Lane A or downstream implementation)
- `diagnostic_artifact_hash`
- `director_verdict_id`
- `director_verdict_reason`

Lane E does not produce the snapshot; it reserves the structural slot so reporting is uniform.

## Policy Matrix

| Surface | Strict default | Survey opt-in | Notes |
| --- | --- | --- | --- |
| `--mode` | `strict-quality` | `survey` | survey requires explicit flag |
| `--stage3-failure-policy` | `strict` | `skip` or `quarantine` | non-strict requires `--mode=survey` |
| `--stage3-skip-budget` | n/a | required for `skip` | rejected without `skip` policy |
| `--allow-quarantine` | n/a | required for `quarantine` | safety acknowledgment |
| `--operator-present` | `auto` | `auto` | TTY detection at worker boot |
| HIL prompt fired? | only if operator detected | only if operator detected | EOF cannot fake a verdict |
| `process_status` field | required | required | always present |
| `objective_status` field | required | required | always present |
| Director verdict authority | unchanged | unchanged | Lane F invariant |
| Factsheet auto-edit | forbidden | forbidden | Lane D / Lane F invariant |

## Required Test Cases (before implementation)

These are read-only assertions about target test coverage, not test code. They should land before any production-code change driven by this design.

1. `test_objective_status_achieved` - 5 arcs requested, 5 produced, asserts `process_status=success`, `objective_status=achieved`, `judgment=success`.
2. `test_objective_status_partial` - 5 arcs requested, 1 produced + Stage3 fail with operator stop, asserts `objective_status=partial` or `aborted`, never `success`.
3. `test_objective_status_not_reached` - 5 arcs requested, 0 produced, asserts `objective_status=not_reached`.
4. `test_no_operator_strict_stop_distinct_literal` - simulate non-TTY stdin under default mode, asserts `stop_reason=stage3_no_operator_strict_stop`, asserts NO `_get_choice_input` invocation, asserts NO `stage3_user_abort` literal in any sink.
5. `test_operator_typed_stop_literal` - simulate TTY operator typing `2`, asserts `stop_reason=stage3_operator_typed_stop`.
6. `test_operator_typed_skip_continues` - simulate TTY operator typing `1` under default policy, asserts `arcs_advanced_delta=1` and `stop_reason=None`.
7. `test_stage3_skip_budget_exhausts` - `--mode=survey --stage3-failure-policy=skip --stage3-skip-budget=2` with three Stage3 failures, asserts first two skip, third emits `stage3_skip_budget_exhausted_stop`.
8. `test_stage3_quarantine_marks_without_authoring` - `--mode=survey --stage3-failure-policy=quarantine --allow-quarantine`, asserts manifest gains a `quarantined_arc` entry, asserts no blueprint or factsheet write occurred for the quarantined arc, asserts `objective_status` is not `achieved` for the run.
9. `test_stage3_exception_branch_under_strict` - simulate exception in Stage3 orchestrator with non-TTY, asserts `stop_reason=stage3_exception_no_operator_strict_stop` (not `stage3_exception_user_abort`).
10. `test_manifest_emits_objective_status` - asserts every terminal manifest write contains both `process_status` and `objective_status`.
11. `test_console_finalize_headline_matches_objective` - asserts the final headline string is exactly one of the six allowed forms in section D7.
12. `test_director_authority_unchanged_under_quarantine` - asserts Director verdict cannot be flipped to PASS by the quarantine path.
13. `test_legacy_status_compat_window` - asserts both new fields are present and the legacy `status` field, if present, never contradicts the new fields during the shim window.

## Risks

| Severity | Risk | Mitigation |
| --- | --- | --- |
| P1 | A skip-budget run quietly turns into objective_status=achieved under operator misconfiguration | strict-quality default; skip and quarantine require `--mode=survey`; analyzer never reports `achieved` while quarantined arcs are pending |
| P1 | Quarantine could be misread as a Director-approved bypass | quarantine is marked-only; Director still adjudicates; manifest contract requires explicit Director verdict id before objective_status is allowed to escalate |
| P2 | Operator-presence auto-detection misclassifies headless CI as operator-present | TTY check is the conservative direction; if TTY is uncertain, treat as no-operator and route to strict-stop, not skip |
| P2 | Vocabulary churn breaks downstream telemetry consumers | shim window for legacy `status` and `stage3_user_abort` literals; both forms emitted in JSON during the window; analyzer prefers the new literals |
| P2 | Survey runs leak into strict reporting if both flag combinations are accepted | parser rejects mismatched combinations at boot; harness emits a startup banner naming the resolved mode |
| P3 | Console headline change confuses operators used to "파이프라인 완료" | release note plus the OBJECTIVE 달성 form keeps a recognizable string when the run is fully clean |
| P3 | The `stage3_terminal_failure_snapshot` slot stays empty until Lane A lands | the slot is structural; absence is a known TODO with a documented handoff to Lane A |

No P0 risk is identified for this design under the constraints in section 3 of the order pack.

## Recommendation

Adopt this design as the input to the harness execution SSOT (`docs/2026-04-26/frontier-lag-clean-5arc-harness-execution-ssot.md` per the order pack section 12) only after Lane A, Lane B, Lane D, and Lane F lane reports exist and Headquarters synthesis reaches at least 95% confidence.

Implementation order if approved (mirrors order pack section 12 with Lane E ownership noted):

1. Add `process_status` and `objective_status` to `worker_result.json`, `auto_frontier_lag_analysis.json`, and the harness manifest. (Lane E owned.)
2. Add `--operator-present`, `--mode`, `--stage3-failure-policy`, `--stage3-skip-budget`, `--allow-quarantine` flags. Strict default preserved. (Lane E owned.)
3. Split `stage3_user_abort` and `stage3_exception_user_abort` into the explicit literals in section D2; emit both during the shim window. (Lane E owned.)
4. Wire `derive_judgment` and `derive_root_cause` to the new vocabulary. (Lane E owned.)
5. Reserve the `stage3_terminal_failure_snapshot` manifest slot. (Lane E owned, Lane A fills.)
6. Add the 13 test cases in section "Required Test Cases" before changing production paths.
7. Run a single bounded fresh Frontier Lag validation in `survey` mode with `skip-budget=1` to verify the new vocabulary flows end to end.

Strict default behavior is preserved. No Director or validator authority is moved. No factsheet, blueprint, or arc edit is introduced by this design.

## Subagent Cross-Check

This lane used two read-only Explore subagents per the order pack subagent policy.

- Subagent A (process / result semantics) confirmed:
  - `scripts/run_auto_frontier_lag_harness.py:551-562` writes `worker_result.status="success"` and updates manifest to `worker_success` independent of objective state.
  - `scripts/run_auto_frontier_lag_harness.py:856-859, 952-973` is the only objective-aware re-derivation; judgment is binary success / failed.
  - The 14 stop_reason literals listed in section E5 match this lane's grep.
  - The Stage3 ep4 terminal failed attempt persisted blank `artifact_path` and blank `content_hash`, matching the post-run audit.
- Subagent B (HIL policy / test coverage) confirmed:
  - Both Stage3 HIL branches share the same prompt text and use `or "2"` collapse so EOF and explicit-2 are indistinguishable downstream.
  - `_get_choice_input` resolves through `modules/core/services/ui_service.py:255` and silently returns the normalized default on EOF / non-interactive stdin.
  - No `--auto-skip`, `--strict`, `--survey`, or `--quarantine` flag exists in `parse_args` today; the harness has no run-mode switch.
  - Existing tests cover the explicit-2 stop and explicit-1 skip paths but never exercise EOF directly and never exercise the exception branch HIL prompt.

The parent terminal cross-checked subagent claims at:
- `scripts/run_auto_frontier_lag_harness.py:201-236` (CLI args, no skip / mode flags)
- `scripts/run_auto_frontier_lag_harness.py:540-580` (worker status emission)
- `main_a.py:4174-4256` (HIL boundary)
- `main_a.py:4417-4452` (finalize block)
- `tests/test_one_stop_frontier_lag_auto_continue.py:679-722` (Stage3 stop test)

No subagent claim is rejected. One subagent inference (line numbers around 425-432 for poll snapshots) was not load-bearing for the design and was not verified. All load-bearing anchors are verified.

## 3-Pass Mini Audit

Pass 1 - structure and scope: PASS.

The document follows the order pack's required section list (Scope, Evidence, Findings, Risks, Recommendation, Subagent Cross-Check, 3-Pass Mini Audit) plus the design-specific Design and Policy Matrix sections, and explicitly does not patch code. Strict default is preserved as the order pack requires.

Pass 2 - evidence and consistency: PASS.

Every load-bearing claim cites a file:line anchor or a stop_reason literal that has been verified against the live workspace. The objective vs process mismatch is grounded in `scripts/run_auto_frontier_lag_harness.py:551-562, 856-859, 952-973` and `main_a.py:4417-4452`. The HIL EOF collapse is grounded in `main_a.py:4189-4197, 4228-4236` plus `modules/core/services/ui_service.py:255`. The Stage3 failure policy options are constrained by the AGENTS.md non-negotiable governance: Python collects, LLM/Director judges, no factsheet auto-edit, Director sovereignty.

Pass 3 - execution readability: PASS.

A future implementer reading only this document gets: required CLI flags, required JSON fields, required stop_reason literals, required console headlines, required test cases, and an explicit Risks table with mitigations. Nothing in the design grants Python authority to override Director verdicts. Nothing in the design weakens validation. Survey relaxation is gated behind `--mode=survey` and explicit `--allow-quarantine` acknowledgment.

Estimated confidence: 96%.

The score is not higher because (a) the diagnostic snapshot slot at section D8 depends on Lane A landing, (b) the legacy compatibility shim window length is intentionally left unspecified for Headquarters synthesis to set, and (c) any TTY detection edge case (Windows console host vs ConPTY vs CI) may need a follow-up sub-design once Headquarters opens the execution SSOT.
