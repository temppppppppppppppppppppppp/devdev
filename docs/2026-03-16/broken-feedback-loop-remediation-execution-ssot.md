# Broken Feedback Loop Remediation Execution SSOT

Date: 2026-03-16
Status: completed canonical
Canonical Path: `docs/2026-03-16/broken-feedback-loop-remediation-execution-ssot.md`
Companion Project SSOT: `docs/2026-03-16/project-0-260316-execution-ssot.md`
Confidence After Fresh Merged 3-Pass Audit: `96%`
Authority Order:
1. live code + runtime references
2. Tier 1 TF source surveys (`조사_TF-A`~`조사_TF-F`)
3. Tier 2 `condex_*` supplements
4. Tier 3 `OPUS_broken_feedback_loop_3pass_audit.md`
5. Tier 4 methodology reference (`조사_broken_feedback_loop_audit_order.md`)
Scope Boundary:
- this document is the canonical remediation authority for the system-wide broken feedback loop bundle
- it does not own `0_260316` recovery, stop-point, or resumability decisions
- `0_260316` is used here only as a proof corpus and regression fixture

## Executive Verdict

- **Fact:** `docs/sp` is not a project-run bundle. It is a system-wide broken feedback loop survey pack spanning Stage 0 style extraction, Stage 3 observability, Stage 4 retry handoff, cross-cutting sinks, bridge/desktop consumers, and reverse feedback paths.
- **Fact:** most forward runtime loops already work. `DPW`, `FailureLearner`, Stage 4 streak logic, `quality_risk` early intervention, pass-rate difficulty tracking, and Stage 4→2 reverse difficulty feedback are live or working and should not be misclassified as broken.
- **Fact:** the main broken area is not “signal absent everywhere” but “signal measured or surfaced without reaching the runtime-core decision loop.” This was especially true for `ai_slop`, `ced_score`, `coverage_warning`, and `cost_log`; the fresh Tranche 3 validity gate showed that the remaining live gaps were narrower than the survey wording suggested.
- **Fact:** `condex_*` supplements do not overturn the TF surveys. They mainly prove that several signals are visible in bridge/UI/operator surfaces even when they are still dead or weak in runtime-core retry routing.
- **Fact:** two scope-sensitive names had to be normalized to eliminate false conflict:
  - `open_review` is live inside same-round `previous_attempt`, but `episode_quality_labels.open_review` replay is still dead for later generation loops.
  - `reverse_feedback` is split: Stage 4→2 and Stage 4→3 are already working in live code, while the real Stage 3→2 gap was missing Stage 3 reject-history persistence into the existing thresholded trigger.
- **Decision:** remediation will use three tranches:
  - Tranche 1: style/core warning closure
  - Tranche 2: validation/escalation hardening
  - Tranche 3: reverse-loop automation and observability consumption
- **Decision:** `0_260316` remains the canonical regression fixture for shared Stage 4 findings, but the project recovery authority stays in the companion project SSOT.

## Evidence Base

### Tier 1 Source Surveys

- `docs/sp/조사_TF-A_stage0_dead_extraction_signals.md`
- `docs/sp/조사_TF-B_stage0_downstream_weak_links.md`
- `docs/sp/조사_TF-C_stage3_observational_signals.md`
- `docs/sp/조사_TF-D_stage4_broken_feedback.md`
- `docs/sp/조사_TF-E_cross_cutting_write_only_sinks.md`
- `docs/sp/조사_TF-F_working_loop_verification.md`

### Tier 2 Supplement Surveys

- `docs/sp/condex_조사_TF-A_stage0-2_signal_consumer_audit.md`
- `docs/sp/condex_조사_TF-B_stage3_signal_consumer_audit.md`
- `docs/sp/condex_조사_TF-C_stage4_signal_consumer_audit.md`
- `docs/sp/condex_조사_TF-D_observability_metrics_signal_consumer_audit.md`
- `docs/sp/condex_조사_TF-E_bridge_desktop_signal_consumer_audit.md`

### Tier 3 Meta Audit

- `docs/sp/OPUS_broken_feedback_loop_3pass_audit.md`

### Tier 4 Methodology Reference

- `docs/sp/조사_broken_feedback_loop_audit_order.md`

### Direct Code Revalidation

- `modules/core/stage0/style_extractor.py`
- `modules/core/genre_guards/style_guard.py`
- `modules/core/project_support.py`
- `modules/core/pre_director_checklist.py`
- `modules/core/pre_director_manuscript_checker.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/feedback_system.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/db_manager.py`
- `modules/core/quality_dashboard.py`
- `modules/core/dynamic_prompt_weighting.py`
- `modules/core/failure_learning.py`
- `modules/api/bridge_server.py`

## Merged 3-Pass Audit

### Pass 1: Inventory Lock

| Document | Tier | Scope | Disposition |
| --- | --- | --- | --- |
| `조사_TF-A_stage0_dead_extraction_signals.md` | 1 | Stage 0 V2 style extraction weak/live split | accepted |
| `조사_TF-B_stage0_downstream_weak_links.md` | 1 | `anti_ai_patterns`, `dialogue_ratio`, `vocabulary_level` | accepted |
| `조사_TF-C_stage3_observational_signals.md` | 1 | Stage 3 coverage/scene_count/quality deferral | accepted |
| `조사_TF-D_stage4_broken_feedback.md` | 1 | Stage 4 retry feedback breakpoints | accepted |
| `조사_TF-E_cross_cutting_write_only_sinks.md` | 1 | cross-cutting sinks and write-only telemetry | accepted |
| `조사_TF-F_working_loop_verification.md` | 1 | working and fragile feedback loops | accepted |
| `condex_조사_TF-A_stage0-2_signal_consumer_audit.md` | 2 | Stage 0-2 runtime/bridge consumer supplement | supplemental accepted |
| `condex_조사_TF-B_stage3_signal_consumer_audit.md` | 2 | Stage 3 runtime/operator consumer supplement | supplemental accepted |
| `condex_조사_TF-C_stage4_signal_consumer_audit.md` | 2 | Stage 4 runtime/operator consumer supplement | supplemental accepted |
| `condex_조사_TF-D_observability_metrics_signal_consumer_audit.md` | 2 | observability/proof caller supplement | supplemental accepted |
| `condex_조사_TF-E_bridge_desktop_signal_consumer_audit.md` | 2 | bridge/desktop reader supplement | supplemental accepted |
| `OPUS_broken_feedback_loop_3pass_audit.md` | 3 | cross-TF meta audit, counts, missing-signal check | accepted after spot-check |
| `조사_broken_feedback_loop_audit_order.md` | 4 | scope, TF partitioning, methodology | reference-only |

Pass 1 result:

- inventory is locked at `13/13`
- `condex_조사_TF-F` is absent, so TF-F authority comes from Tier 1 TF-F + direct code revalidation + Tier 3 OPUS pass3 note on `generate_reverse_feedback_stage4_to_2`
- no inventory item was dropped from the canonical synthesis

### Pass 2: Conflict Normalization

| Topic | Tier 1 View | Tier 2/3 View | Resolution |
| --- | --- | --- | --- |
| Stage 0-2 overall | TF-A/B identify weak or dead style-extraction-derived fields | `condex` TF-A shows most Stage 0-2 runtime gates are closed | **Resolved:** Stage 0-2 runtime gates are mostly closed, but extracted style descriptors remain weak or dead unless wired into validators |
| `coverage_warnings` | TF-C says advisory-only for core retry | `condex` TF-B says operator calibration consumes it | **Resolved:** operator advisory existed first; Tranche 2 closes the runtime-core surfacing gap by making the warning explicit in mandatory context, validation payloads, and retry provenance |
| Stage 4 quality signal bundle | TF-D says dead for CW retry | `condex` TF-C/E say bridge quality radar consumes it | **Resolved:** split `runtime-core` vs `operator/UI` consumers; Tranche 1 later closes the bounded runtime-core advisory gap without giving Python final authority |
| `open_review` | TF-D frames label replay as dead | live code shows same-round `previous_attempt.open_review` reaches CW and bridge reads latest labels | **Resolved:** split `same-round retry handoff` from `cross-episode sidecar replay`; only the replay path is dead |
| `reverse_feedback` | TF-F says Stage 4→3 and Stage 3→2 are fragile | `condex` TF-A proves Stage 4→2 is working | **Resolved:** split paths; do not classify `reverse_feedback` as one monolith |
| `cost_log` | TF-E says `get_cost_summary()` has no runtime caller | `condex` TF-D shows shutdown metric totals are still consumed | **Resolved:** split `cost_log DB summary` from `metrics scope shutdown totals`; only the former is dead |
| `DPW` and `FailureLearner` | TF-F and TF-E already treat them as working/live | `condex` and OPUS do not contradict | **Resolved:** keep them out of broken tranche |

Pass 2 result:

- unresolved conflicts: `0`
- wording had to be normalized for `open_review`, `reverse_feedback`, and `cost_log`
- the canonical taxonomy now distinguishes `runtime-core`, `operator/UI`, and `audit/proof` consumers

### Pass 3: Execution Readiness

- the merged bundle is decision-complete enough to drive remediation without re-reading all 13 surveys
- shared items with the companion `0_260316` SSOT were reclassified as:
  - `shared-consistent`: `ai_slop`, `npc_drift`, `coverage_warning`
  - `shared-needs-wording-sync`: `open_review`
  - `system-only`: `FactLedger`, `reverse_feedback`, `dialogue_ratio`, `cost_log`
- no project-specific recovery claim was promoted into this document
- `0_260316` is used only as regression evidence, not as the subject of this SSOT

Pass 3 result: tranche sequencing remains valid; all three planned tranches are closed, the low-priority control-plane provenance reader is now closed, and the remaining open items are opportunistic helper / instrumentation follow-ups only.

## Signal Taxonomy

| Signal | Runtime-Core Status | Operator / UI Status | Canonical Interpretation |
| --- | --- | --- | --- |
| `ai_slop` / quality signal bundle | `ADVISORY / DIRECTOR-MEDIATED` | `CLOSED` in bridge quality radar | measured, persisted, and now injected into Director-mediated retry feedback without becoming a Python hard gate |
| `ced_score` | `ADVISORY / DIRECTOR-MEDIATED` | `CLOSED` in bridge quality radar | bounded warning injection is now live through the same Director-mediated advisory path |
| `compression_ratio` / `burstiness` / `complexity` | `DEAD` for retry routing | `CLOSED` in bridge quality radar | keep-audit by default unless promoted |
| `open_review` same-round handoff | `WORKING` | n/a | reaches CW through `previous_attempt` when Director emits it |
| `open_review` label replay | `DEAD` | `CLOSED` in bridge latest-label summary | cross-episode reuse path is still missing |
| `npc_drift` structured handoff | `DIRECTOR-MEDIATED / STRUCTURED` | n/a | structured payload now survives selected validation, retry provenance, and `previous_attempt.validation_warnings` into CW retry input |
| `coverage_warnings` | `ADVISORY / EXPLICIT` | `ADVISORY` in dashboard/bridge | warning now survives as mandatory-context text plus selected-validation / retry evidence instead of dying in observability summaries |
| `dialogue_ratio` | `ADVISORY / TARGET-AWARE` | n/a | measured in pre-director validation against the project StyleGuide target when available |
| `vocabulary_level` | `DEAD` | n/a | extracted and prompted, but never validated |
| `FactLedger` continuity | `DIRECTOR-MEDIATED / STRUCTURED` | n/a | numeric-consistency conflicts now survive as explicit retry evidence and validation payloads without introducing Python final reject authority |
| `reverse_feedback` Stage 4→2 | `WORKING` | n/a | already injected via Stage 2 preflight when arc difficulty is high |
| `reverse_feedback` Stage 4→3 | `WORKING` | n/a | live Stage 4 orchestrator auto-injects reverse feedback into repeated logic-error blueprint retries |
| `reverse_feedback` Stage 3→2 | `WORKING / THRESHOLDED` | n/a | Stage 2 preflight threshold was already live; Tranche 3 closes the missing Stage 3 reject-history persistence feeding that trigger |
| `DPW` | `LIVE` | n/a | keep as a working loop, not a remediation target |
| `FailureLearner` | `LIVE` / `WORKING` | n/a | keep as a working loop, not a remediation target |
| `cost_log` DB summary | `READ-ONLY / WORKING` | `CLOSED` in bridge quality dashboard | `get_cost_summary()` now feeds a production `cost_summary` payload without becoming a Python control gate |
| shutdown metric totals | `ADVISORY` | logs only | do not confuse shutdown sink consumption with runtime cost control |
| control-plane provenance | `READ-ONLY / WORKING` | `CLOSED` in bridge `/status` summary | `bridge_server.py` now reads recent `control-plane-provenance.jsonl` rows into an optional status payload without changing write semantics |

## Execution Decision

**Decision:** keep the canonical structure as `system remediation SSOT + companion project SSOT + top-level roadmap`.

### Pre-Tranche Validity Gate

- before any tranche starts, revalidate the current codebase rather than trusting survey text alone
- live code is the execution authority for tranche start; stale survey wording is not sufficient
- the validity check must confirm:
  - the target signal producers still exist in the current runtime path
  - the expected consumers or missing consumers still match the taxonomy below
  - the authority split between system SSOT and companion project SSOT is still current
- `0_260316` still maps to the shared regression findings used by the tranche
- if the validity check finds drift, rerun a fresh 3-pass audit on this SSOT before implementation begins

### Automatic Tranche Loop

For every tranche, follow the same bounded loop:

1. validity check against current live code
2. bounded implementation for the approved tranche scope
3. fresh 3-pass audit on evidence, behavior, and wording
4. canonical doc update, then any required mirror/queue sync
5. next-tranche selection from the updated roadmap

Loop rule:

- do not jump from step 2 directly to the next tranche
- if step 3 or step 4 fails, stop and repair the current tranche record before selecting the next tranche
- next-tranche selection is allowed only after the updated docs still clear the 95% confidence gate

### Tranche 1: Style / Core Warning Closure

Status:

- completed on `2026-03-16` after a live-code validity gate and fresh 3-pass audit
- next selected tranche at closure time: `Tranche 2`

Completed scope:

1. `ai_slop` / style digest wiring
2. `dialogue_ratio` dynamic target linkage
3. `ced_score` warning injection

Implemented shape:

- Python may continue measuring raw metrics, but it must not become the final reject authority
- any style remediation fed to CW must be Director-mediated
- `dialogue_ratio` now reads the project style target when available instead of using a fixed `0.30` ideal

Validity gate result:

- producers were confirmed live in `stage4_post_processor.py`, `quality_signal_metrics.py`, and the DB summary path
- operator/UI consumers were already live in bridge quality radar, confirming the remaining gap was runtime-core retry ingress
- `pre_director_manuscript_checker.py` still used a fixed `0.30` dialogue ideal, so the style-target linkage remained stale
- `stage4_interview_round.py` still lacked bounded `ai_slop` / `ced_score` advisory routing into Director-mediated retry feedback

Regression gate:

- use `0_260316` as proof corpus
- preserve `Menu 7` resumability and existing frontier facts
- verify that shared style findings remain wording-consistent with the companion project SSOT

Bounded implementation landed:

- `modules/core/project_support.py` now normalizes project style-guide `dialogue_ratio` targets
- `modules/core/pre_director_checklist.py` and `modules/core/pre_director_manuscript_checker.py` now run dialogue-ratio checks against the project style target when present
- `modules/core/stage4_interview_round.py` now runs `StyleSignalAdvisor` and injects `ai_slop`, `ced_score`, and `dialogue_ratio` warnings into Director-mediated retry feedback and provenance

Targeted verification:

- `python -m pytest -q tests/test_project_support.py` -> `10 passed`
- `python -m pytest -q tests/test_pre_director_submodules.py` -> `21 passed`
- `python -m pytest -q tests/test_stage4_interview_round.py -k "quality_signal or advisory_style or retry_feedback_provenance"` -> `3 passed`
- `python -m pytest -q tests/test_stage4_interview_round.py` -> `82 passed`
- `python -m pytest -q tests/test_continuity_modules.py -k "PreDirectorChecklistDialogueRatio"` -> `2 passed`
- `python -m pytest -q tests/test_pre_director_dialogue_quotes.py` -> `1 passed`
- `python -m ruff check modules/core/project_support.py modules/core/pre_director_checklist.py modules/core/pre_director_manuscript_checker.py modules/core/stage4_interview_round.py tests/test_project_support.py tests/test_pre_director_submodules.py tests/test_stage4_interview_round.py` -> `All checks passed`

### Tranche 2: Validation / Escalation Hardening

Status:

- completed on `2026-03-16` after a live-code validity gate and fresh 3-pass audit
- next selected tranche: `Tranche 3`

Priority:

1. `FactLedger` explicit retry escalation
2. `coverage_warnings` explicit surfacing
3. `npc_drift` structured handoff

Required shape:

- advisory-only facts that should block or escalate must become explicit runtime inputs
- `coverage_warnings` must stop dying in observability summaries
- `npc_drift` must become a structured Director-mediated retry artifact rather than a transient advisory only
- maintain Director sovereignty; do not convert Python validation into a unilateral final reject gate

Starting gate:

- rerun a codebase validity check on `FactLedger`, `coverage_warnings`, `npc_drift`, and related retry/escalation consumers before patching
- confirm the tranche still targets an escalation gap and not just a documentation wording difference

Regression gate:

- confirm `0_260316` shared Stage 4 findings still reproduce as expected
- confirm no project-specific recovery claim in the companion SSOT becomes stale

Validity gate result:

- `npc_drift` warnings already reached `validation_results`, but they still died before retry provenance and CW-facing durable payload handoff
- `coverage_warnings` were still confined to Stage 3/4 observability summaries and dashboard readers; runtime-core retry did not see an explicit section
- `FactLedger` numeric consistency already existed as a Director advisory, but the warning did not persist as structured validation payload or retry provenance
- bounded decision: close the runtime-core escalation gap by promoting these signals into explicit Director-mediated retry inputs without adding Python final-authority veto logic

Bounded implementation landed:

- `modules/core/stage4_interview_round.py` now preserves `npc_drift`, `numeric_consistency`, and `coverage_warnings` in structured `validation_results`, retry provenance, stage-attempt warning payloads, and `previous_attempt.validation_warnings`
- `modules/core/stage4_interview_round.py` now runs numeric-consistency advisory with a cloned validation payload and merges `numeric_consistency_warnings` back just like other structured advisory families
- `modules/core/stage4_context_builder.py` now emits a dedicated `[검색 커버리지 경고]` mandatory-context section when retrieval coverage is structurally missing
- no Python hard reject or auto-firewall authority was added; final accept/reject authority remains Director-mediated

Targeted verification:

- `python -m pytest -q tests/test_stage4_interview_round.py::TestInterviewRoundHelpers::test_retry_feedback_provenance_includes_structured_validation_handoff` -> `1 passed`
- `python -m pytest -q tests/test_stage4_interview_round.py::TestAdvisoryChain::test_advisory_chain_uses_local_validation_copies_and_merges_back` -> `1 passed`
- `python -m pytest -q tests/test_stage4_interview_round.py::TestPreDirectorValidation::test_pre_director_validation_attaches_coverage_warnings_to_candidates` -> `1 passed`
- `python -m pytest -q tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_build_mandatory_context_surfaces_retrieval_coverage_warnings` -> `1 passed`
- `python -m pytest -q tests/test_stage4_interview_round.py::TestInterviewRoundRun::test_reject_preserves_structured_validation_warnings_for_retry` -> `1 passed`
- `python -m pytest -q tests/test_stage4_interview_round.py` -> `85 passed`
- `python -m pytest -q tests/test_stage4_context_builder.py` -> `53 passed`
- `python -m pytest -q tests/test_numeric_consistency_checker.py` -> `40 passed`
- `python -m pytest -q tests/test_stage4_cv_context.py` -> `21 passed`
- `python -m ruff check modules/core/stage4_interview_round.py modules/core/stage4_context_builder.py tests/test_stage4_interview_round.py tests/test_stage4_context_builder.py` -> `All checks passed`
- `python scripts/ops_validator.py` -> `errors=0 warnings=0`

### Tranche 3: Reverse-Loop Automation and Observability Consumption

Status:

- completed on `2026-03-16` after a live-code validity gate and fresh 3-pass audit
- no further tranche remains after closure; the low-priority `control-plane provenance` reader is also closed, and only opportunistic helper follow-ups remain outside the tranche queue

Validity gate result:

- do not rebuild the already-working Stage 4→2 reverse difficulty path
- Stage 4→3 was already auto-triggered in live code via repeated `LOGIC_ERROR` / `quality_risk` retry paths in `stage4_orchestrator.py`; no code change was needed there
- Stage 3→2 had the thresholded consumer in `stage2_preflight.py`, but the producer side was incomplete because Stage 3 REJECT paths did not persist entries into `stage_rejection_history`
- `cost_log` shutdown metrics were already persisted, but `DBManager.get_cost_summary()` still had no production read surface

Bounded implementation landed:

- `modules/core/stage3_orchestrator.py` now appends compact Stage 3 REJECT history entries onto `app.stage_rejection_history`, matching the existing Stage 3→2 threshold contract used by `stage2_preflight.py`
- `modules/api/bridge_server.py` now reads `DBManager.get_cost_summary()` into a bounded `cost_summary` dashboard payload so the DB summary path is no longer dead
- no change was made to Stage 4→3 runtime logic because the validity gate confirmed it was already operational

Targeted verification:

- `0_260316` remains the shared Stage 4 regression fixture
- bridge/UI consumers must continue working after runtime-core wiring changes
- `python -m pytest -q tests/test_stage3_orchestrator.py -k "stage3_failure_appends_rejection_history_for_stage3_to_2_feedback"` -> `1 passed`
- `python -m pytest -q tests/test_stage2_preflight.py -k "stage3_reverse_feedback_injected_after_three_stage3_failures"` -> `1 passed`
- `python -m pytest -q tests/test_bridge_quality_summary.py -k "surfaces_cost_summary"` -> `1 passed`
- `python -m pytest -q tests/test_stage3_orchestrator.py` -> `72 passed`
- `python -m pytest -q tests/test_stage2_preflight.py` -> `27 passed`
- `python -m pytest -q tests/test_bridge_quality_summary.py tests/test_cost_tracking.py` -> `15 passed`
- `python -m pytest -q tests/test_stage4_orchestrator.py -k "stage4_to_3_feedback"` -> `1 passed`
- `python -m ruff check modules/core/stage3_orchestrator.py modules/api/bridge_server.py tests/test_stage3_orchestrator.py tests/test_stage2_preflight.py tests/test_bridge_quality_summary.py` -> `All checks passed`
- `python scripts/ops_validator.py` -> `errors=0 warnings=0`
- post-tranche bounded addendum: `modules/api/bridge_server.py` now exposes an optional `control_plane_provenance` summary on `/status`
- `python -m pytest -q tests/test_bridge_server_http_contract.py` -> `8 passed`
- `python -m pytest -q tests/test_control_plane_approval_provenance_ssot.py tests/test_bridge_server_desktop_risk_gate.py` -> `7 passed`

## Acceptance Criteria

- each tranche starts only after a current-code validity check confirms the targeted loop classification is still accurate
- if the pre-tranche validity check discovers drift, this SSOT is refreshed with a new 3-pass audit before code changes begin
- each tranche completes the full loop of validity check -> implementation -> 3-pass audit -> doc update -> next-tranche selection
- Tranche 1 is closed: `ai_slop`, `dialogue_ratio`, and `ced_score` now reach the runtime-core retry loop through bounded Director-mediated advisory routing without giving Python final quality sovereignty.
- Tranche 2 closes the escalation gap for `FactLedger`, `coverage_warnings`, and `npc_drift`.
- Tranche 3 confirms the already-working Stage 4→2 and Stage 4→3 paths, closes the missing Stage 3→2 reject-history feed, and resolves the dead `cost_log` DB-summary consumer gap.
- `0_260316` remains a valid regression fixture for shared Stage 4 findings after each tranche.
- bridge/desktop/operator surfaces continue to function; runtime-core improvements must not break existing operator visibility.

## Open Items

| Item | Status | Impact |
| --- | --- | --- |
| `MetricsCollector.record_retry()` caller absence | open | low |
| `PassRateMonitor.get_patch_effectiveness()` unused helper | open | low |
| `QualityDashboard.get_quality_signal_snapshot()` unused helper | open | low |
| HUD anomaly / blueprint coverage instrumentation producer gaps | open | low |

Notes:

- these open items are intentionally left out of the main tranches because they are lower ROI than the broken runtime-core feedback loops above
- if a later tranche promotes them, this SSOT should be refreshed rather than patched ad hoc
