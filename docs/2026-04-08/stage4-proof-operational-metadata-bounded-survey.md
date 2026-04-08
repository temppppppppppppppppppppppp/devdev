# Stage4 Proof Operational Metadata Bounded Survey

Date: 2026-04-08
Status: final (3-pass audited; queue-absorbed into `0_0-stage4-partial-fix-hardening-remediation`; no new queue topic)
Canonical Path: `docs/2026-04-08/stage4-proof-operational-metadata-bounded-survey.md`
Commit State:
- Baseline Commit: `6dd7712ea9a58802221634081ba199bc872d2349`
- Baseline Dirty Summary: `dirty: active temp queue mirrors plus operator-side docs/material files and untracked canary dirs already present before this survey`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Execution Docs:
- `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
Evidence Files:
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- `tests/test_audit_service.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_stage4_post_processor.py`
Side-Effect Coverage: covered

## 1. Question

What is the minimum real-pipeline observability tranche needed so an actual fresh run can later be reused as proof without introducing mandatory operator-only `proof_intent` input or opening a new queue topic?

## 2. Scope

Included:

- Stage4 control-plane runtime metadata
- Stage4 post-pass contract signal metadata
- `runtime_audit_summary.json` proof-digest extension for latest-session operational metadata
- existing session, DB, and JSONL sinks used as evidence substrate

Excluded:

- mandatory user-supplied `proof_intent`
- new DB tables or columns
- canary harness changes
- broad Stage4 repair/consumer redesign
- Stage2 or Stage3 functional changes
- queue-rank creation

## 3. Evidence Inventory

1. `modules/core/stage4_orchestrator.py`
   - already emits `target_ep_reached` to `session_logger.log_decision()` and `audit_event()`
   - already emits `stage4_complete` to `audit_event()` and then writes `runtime_audit_summary.json`
   - does not currently emit a start-of-session scope marker
   - current control-plane audit payloads do not consistently carry `session_id`
2. `modules/core/stage4_post_pass_runtime.py`
   - already persists `STAGE4_POST_PASS_CONTRACT` to `episode_production.jsonl`
   - already mirrors that signal into `audit_event("stage4_post_pass_contract_signal", ...)`
   - current payload does not carry `session_id`
3. `modules/core/services/audit_service.py`
   - already builds compact sink-alignment truth into `runtime_audit_summary.json`
   - already resolves the latest structured `session_id`
   - does not currently summarize whether the latest live session exercised retry, patch, or post-pass contract paths
4. `modules/core/db_manager.py`
   - already persists `session_id` and `attempt_key` on `stage_attempts`
   - already exposes raw adjunct payload storage if richer per-attempt proof metadata is needed later
5. `modules/core/session_logger.py`
   - already supports control-plane `decision_type` plus arbitrary `meta`
   - therefore can host bounded Stage4 scope metadata without schema changes

## 4. Findings

1. The current pipeline is already strong at sink-alignment proof, but weak at compact run-level interpretation. It can tell us whether persisted truth aligns, yet it does not cleanly answer which proof-relevant paths were exercised by the latest live session.
2. The missing seam is auto-derived operational metadata, not a new authority sink. `stage_attempts`, `episode_production.jsonl`, `runtime_audit.jsonl`, and `session/decisions.jsonl` already provide enough substrate.
3. Making `proof_intent` mandatory for real fresh runs would overfit canary-style operation and would incorrectly turn optional operator labeling into a runtime requirement.
4. The bounded high-ROI patch is to add session-scoped Stage4 metadata at the control-plane and post-pass edges, then let `AuditService` summarize that metadata into the existing proof digest.

## 5. Recommended Execution Shape

1. Emit a bounded `stage4_session_scope` control-plane event at Stage4 session start.
   - required fields: `session_id`, `start_ep`, `target_ep`, `total_planned_ep`
   - sinks: `session/decisions.jsonl` plus `runtime_audit.jsonl`
2. Attach `session_id` to the existing Stage4 control-plane and post-pass proof surfaces.
   - `target_ep_reached`
   - `stage4_complete`
   - `STAGE4_POST_PASS_CONTRACT`
3. Extend `runtime_audit_summary.json -> proof_digest` with latest-session operational metadata.
   - `stage3_live_session`
   - `stage4_live_session`
   - `retry_exercised`
   - `patch_exercised`
   - `post_pass_contract_signal_count`
   - `non_exercised_reasons`
4. Keep the tranche bounded.
   - no new queue topic
   - no new DB schema
   - no mandatory `proof_intent`
   - no canary-tool changes required

## 6. Queue Consequence

- absorb this work into `0_0-stage4-partial-fix-hardening-remediation`
- treat it as a proof-aware observability follow-up under the same deferred verifier family
- do not reinterpret it as Stage4 closure by itself

## 7. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a bounded survey note rather than a new execution SSOT
- made the no-new-queue-topic decision explicit
- separated real-pipeline metadata from canary-only concerns

Pass 2, evidence and consistency:

- anchored every claim to live runtime owners already inspected in `stage4_orchestrator.py`, `stage4_post_pass_runtime.py`, `audit_service.py`, `session_logger.py`, and `db_manager.py`
- kept authority claims aligned with existing sink ownership rather than inventing new truth owners
- bounded the patch to metadata emission plus summary synthesis

Pass 3, execution and readability:

- reduced the recommended patch to four concrete actions
- kept optional operator metadata (`proof_intent`) explicitly out of the runtime requirement set
- left queue ownership with the existing Stage4 partial-fix lane

Confidence: `96%`
