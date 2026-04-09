# Stage234 Proof-Wave Logging Readiness Survey

Date: 2026-04-09
Status: final
Canonical Path: `docs/2026-04-09/stage234-proof-wave-logging-readiness-survey.md`
Evidence Path: `docs/2026-04-09/stage234-proof-wave-logging-readiness-evidence.json`
Baseline Commit: `b94390cb508a298a28349152bb15876f36662c65`
Baseline Dirty Summary: `dirty worktree already contained active roadmap/SSOT/doc updates plus unrelated narrative/material edits; this survey stayed read-only except for its own dated survey outputs`
Resume Commit: `b94390cb508a298a28349152bb15876f36662c65`
Resume Drift Summary: `same-turn static survey; no branch movement during investigation; findings are grounded in current HEAD code/tests plus one synthetic summary check`

## 1. Question

Can the current Stage 2 / 3 / 4 logging and proof-readback stack support a real merged proof wave without wasting reruns on missing logs, and is the stack strong enough that the operator can reasonably finish the proof wave within three total runs?

## 2. Scope

Included surfaces:
- Stage2 / Stage3 / Stage4 `session_id` propagation and attempt-key lineage
- `runtime_audit.jsonl` and `runtime_audit_summary.json` synthesis
- proof-digest / operational-metadata coverage for latest structured session
- pass monitor / stage-attempt / session-decision / UI-event / episode-production joins where they control proof interpretation
- bridge/dashboard and canary readback surfaces that operators would actually inspect after a run
- invalid-run detectability, especially whether the system distinguishes `absent`, `warn`, and `missing` instead of silently dropping proof evidence

Excluded surfaces:
- fresh live proof-wave execution itself
- new code changes or remediation implementation
- narrative truth review of generated artifacts

## 3. Method

This was a static additional survey with three parallel stage slices:
- Stage2 logging/proof-readiness slice
- Stage3 logging/proof-readiness slice
- Stage4 logging/proof-readiness slice

Shared substrate was then rechecked across:
- `AuditService` proof-digest and latest-session operational metadata
- `main_a.py` summary wiring and pre-summary monitor save hook
- bridge/dashboard proof status and gate-repair readback
- Stage4 canary proof-scope/warning logic

Targeted pytest coverage was run after the static read to confirm the critical observability paths still pass on current HEAD.

## 4. Shared Findings

### 4.1 Latest-session proof digest is real, not doc-only

`AuditService` builds a proof digest from committed persistence plus latest structured session lineage, then writes `runtime_audit_summary.json` with explicit contract metadata. It joins:
- DB stage-attempt rows by `session_id`
- session-decision JSONL rows by `session_id` or attempt-key-derived session suffix
- UI-event DB rows by `session_id`
- runtime audit events by `session_id`

Key evidence:
- `modules/core/services/audit_service.py:188`
- `modules/core/services/audit_service.py:206`
- `modules/core/services/audit_service.py:263`
- `modules/core/services/audit_service.py:606`
- `modules/core/services/audit_service.py:700`
- `modules/core/services/audit_service.py:796`

### 4.2 Operator readback is already wired to the proof artifacts

The bridge/dashboard layer loads `runtime_audit_summary.json` as a first-class payload and combines it with sink-alignment status to expose one operator-facing proof status. Stage4 repair/gate metadata is also surfaced as structured readback rather than console-only output.

Key evidence:
- `modules/api/bridge_server.py:1591`
- `modules/api/bridge_server.py:2091`
- `modules/api/bridge_server.py:2120`
- `tests/test_bridge_quality_summary.py:465`

### 4.3 Summary generation is intentionally terminal-path biased

The current stack writes `runtime_audit_summary.json` on successful stage-complete paths. Non-terminal exits do not synthesize the summary artifact by default. This is not silent data loss because raw audit events still flush, but it means the convenience summary is a terminal-run artifact rather than a mid-run heartbeat.

Key evidence:
- `modules/core/stage2_orchestrator.py:1705`
- `modules/core/stage3_orchestrator.py:775`
- `modules/core/stage4_orchestrator.py:2673`
- `tests/test_stage4_orchestrator.py:249`
- `tests/test_stage4_orchestrator.py:296`

Operational consequence:
- a clean proof-wave run should still be planned as a run that reaches the intended stage-complete summary write
- if a run aborts early, the operator should treat it as an invalid or partial proof attempt and inspect raw audit/DB sinks rather than expecting `runtime_audit_summary.json` to fully close the case

## 5. Stage Findings

### 5.1 Stage2

Verdict: `ready`

Why:
- Stage2 PASS/REJECT attempt records are stamped with a resolved `session_id`, stable `attempt_key`, artifact metadata, and pass-monitor writes before proof digest collation.
- Stage2 emits explicit carryover-authority observability into operator-visible/UI-event sinks instead of hiding the seam in a single DB row.
- The proof digest already has tests for the exact failure shapes that would otherwise force reruns just to understand what went wrong: missing monitor sink, rationale drift, blank attempt key, missing session verdict reason, and runtime/retry mismatches.

Key evidence:
- `modules/core/stage2_finalizer.py:3420`
- `modules/core/stage2_finalizer.py:3446`
- `modules/core/stage2_finalizer.py:3479`
- `modules/core/stage2_finalizer.py:3502`
- `modules/core/stage2_finalizer.py:4102`
- `modules/core/stage2_orchestrator.py:1705`
- `modules/core/services/audit_service.py:428`
- `tests/test_stage2_finalizer.py:506`
- `tests/test_audit_service.py:565`
- `tests/test_audit_service.py:668`
- `tests/test_audit_service.py:744`
- `tests/test_audit_service.py:843`
- `tests/test_audit_service.py:876`
- `tests/test_audit_service.py:974`
- `tests/test_audit_service.py:1080`

Stage2 blind spot:
- the convenience summary is still written at the stage-complete tail, not as a continuously refreshed proof snapshot
- this is a bounded operator-friction risk, not a silent logging gap, because Stage2 persistence and warning paths are already explicit

### 5.2 Stage3

Verdict: `mostly_ready`

Why:
- Stage3 writes `stage3_complete` only on normal completion, which is conservative but coherent.
- Source-anchor evidence is persisted in both advisory flags and UI-event metadata, then re-surfaced by `AuditService` as `stage3_live_session` coverage plus latest source-anchor summary.
- `AuditService` explicitly distinguishes Stage3 `absent` from Stage3 `ok`, so a merged proof wave can tell the difference between “Stage3 was not exercised” and “Stage3 evidence vanished.”

Key evidence:
- `modules/core/stage3_orchestrator.py:788`
- `modules/core/stage3_orchestrator.py:1433`
- `modules/core/stage3_orchestrator.py:1890`
- `modules/core/stage3_orchestrator.py:1946`
- `modules/core/services/audit_service.py:477`
- `modules/core/services/audit_service.py:606`
- `tests/test_stage3_orchestrator.py:231`
- `tests/test_stage3_orchestrator.py:1386`
- `tests/test_audit_service.py:1225`

Additional synthetic check:
- a synthetic Stage4-only session was summarized through `AuditService`
- result: `latest_session_id` was populated, `stage3_live_session.status = "absent"`, `stage4_live_session.status = "ok"`, and `target_ep_reached = true`
- this confirms the current stack can classify “Stage3 not reached” without forcing a rerun merely to disambiguate missing logs

Stage3 blind spot:
- there is no fresh real run in this survey proving the live Stage3 path again on current HEAD
- however the question here is logging sufficiency, not semantic correctness, and the current absence-vs-presence classification stack is adequate for proof-wave planning

### 5.3 Stage4

Verdict: `ready`

Why:
- Stage4 logs session scope, target-episode stop, completion, and post-pass contract signals with `session_id`.
- post-pass contract signals are persisted to `episode_production.jsonl` and mirrored into runtime audit events, which gives the proof digest both artifact-side and audit-side evidence for the Stage4 carryover closure question
- bridge/dashboard readback already exposes `gate_repair_summary` and `runtime_audit_summary`
- canary tooling explicitly warns when `runtime_audit_summary` or `pass_rate_monitor` is missing, so proof-wave evidence loss is surfaced as a warning rather than discovered only after multiple reruns

Key evidence:
- `modules/core/stage4_orchestrator.py:587`
- `modules/core/stage4_orchestrator.py:617`
- `modules/core/stage4_orchestrator.py:1508`
- `modules/core/stage4_orchestrator.py:2673`
- `modules/core/stage4_post_pass_runtime.py:1262`
- `modules/core/services/audit_service.py:535`
- `modules/api/bridge_server.py:1591`
- `modules/api/bridge_server.py:2091`
- `modules/core/stage4_canary_tools.py:867`
- `modules/core/stage4_canary_tools.py:1472`
- `main_a.py:418`
- `main_a.py:2398`
- `main_a.py:3135`
- `tests/test_stage4_orchestrator.py:146`
- `tests/test_stage4_orchestrator.py:208`
- `tests/test_stage4_orchestrator.py:249`
- `tests/test_stage4_orchestrator.py:296`
- `tests/test_stage4_post_processor.py:1031`
- `tests/test_bridge_quality_summary.py:465`
- `tests/test_stage4_canary_tools.py:309`

Stage4 blind spot:
- `runtime_audit_summary.json` is not written for early-return / interrupt / exception paths
- raw audit flush still occurs, and canary logic already treats missing summary as a surfaced warning
- therefore this is a run-shape caveat, not a hidden logging defect

## 6. Proof-Wave Run Budget Judgment

Judgment: `yes`

Current HEAD is logging-ready enough that the operator should be able to finish the Stage2/3/4 proof wave within three total runs without rerunning just because essential proof logs are missing.

Reasoning:
- Run 1 can be the primary merged proof wave.
- Run 2 is only needed if Run 1 is infra-invalid or aborts before terminal summary synthesis.
- Run 3 is a bounded fail-only confirmation run after an actual fix, not an evidence-harvest rerun.

Why this is credible:
- Stage2 proof digest already promotes missing or inconsistent evidence to explicit `warn` states.
- Stage3 can be classified as `absent` rather than silently disappearing.
- Stage4 proof closure has both runtime-audit and artifact/readback surfaces, plus canary warnings for missing summary/monitor artifacts.

What should not happen now:
- separate consumer-only and repair-only evidence reruns just to gather missing logs
- repeated Stage4 canaries for proof bookkeeping that the current readback stack can already answer in one merged run

## 7. Severity Assessment

- `P0`: none
- `P1`: none
- `P2`: none
- `P3`: one bounded watch item

Bounded `P3` watch item:
- `runtime_audit_summary.json` remains a terminal-path artifact across Stage2/3/4 rather than a guaranteed summary for interrupted runs
- this raises operator friction on invalid runs, but it does not create silent proof loss because raw audit events, DB stage attempts, session decisions, UI events, pass monitor caches, and bridge/canary warnings still remain available

## 8. Targeted Validation Performed

All commands below passed on current HEAD:
- `python -m pytest tests/test_audit_service.py -k "stage2_proof_digest or stage2_missing_monitor or stage2_rationale_drift or stage2_blank_attempt_key or stage2_missing_verdict_reason or stage2_runtime_retry or stage2_richest" -q`
- `python -m pytest tests/test_audit_service.py -k "warn_tag or latest_stage4_session" -q`
- `python -m pytest tests/test_stage4_orchestrator.py -k "stage4_completion_writes_runtime_audit_summary or log_stage4_session_scope_writes_control_decision_and_audit_event or log_target_ep_reached_writes_control_decision_and_audit_event or stage4_early_return_does_not_write_runtime_audit_summary or stage4_interrupt_does_not_write_runtime_audit_summary or stage4_exception_does_not_write_runtime_audit_summary_and_flushes" -q`
- `python -m pytest tests/test_bridge_quality_summary.py -k "runtime_audit_summary or gate_repair_summary" -q`
- `python -m pytest tests/test_stage4_post_processor.py -k "STAGE4_POST_PASS_CONTRACT or post_pass_contract_signal" -q`
- `python -m pytest tests/test_stage3_orchestrator.py -k "source_anchor_summary or stage3_attempt_key_uses_metrics_session_id_when_available or stage3_reject_cost_record_uses_metrics_session_id_when_available" -q`
- `python -m pytest tests/test_stage4_canary_tools.py -k "gate_repair_summary or stage3_probe_scope or runtime_audit_summary" -q`
- `python -m pytest tests/test_stage2_finalizer.py -k "attempt_key_uses_metrics_session_id_when_available" -q`
- `python -m pytest tests/test_stage4_interview_round.py -k "attempt_key_uses_metrics_session_id_when_available or normalized_request.session_id" -q`
- `python -m pytest tests/test_logging_keys.py -q`
- `python -m pytest tests/test_audit_service.py -k "pre_summary_hook_before_proof_digest" -q`
- `python -m pytest tests/test_audit_service.py -k "operational_metadata_for_latest_stage4_session" -q`

## 9. 3-Pass Audit Record

Pass 1. Structure and scope:
- survey type matches the request
- scope includes Stage2 / Stage3 / Stage4 plus shared proof-readback substrate
- excluded surfaces are explicit

Pass 2. Evidence and consistency:
- all key claims are tied to live code/tests or the synthetic summary check
- file paths and line anchors were rechecked against current HEAD
- baseline and resume commit-state metadata were recorded

Pass 3. Execution/readability:
- document ends in an operator-useful judgment: logging is sufficient for a three-run proof-wave budget, with one bounded terminal-summary caveat
- next operational consequence is clear: run one merged proof wave, not repeated logging-only canaries

Confidence:
- estimated confidence `97%`

