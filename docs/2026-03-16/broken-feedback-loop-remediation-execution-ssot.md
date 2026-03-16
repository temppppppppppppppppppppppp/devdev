# Broken Feedback Loop Remediation Execution SSOT

Date: 2026-03-16
Status: active canonical
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
- **Fact:** the main broken area is not “signal absent everywhere” but “signal measured or surfaced without reaching the runtime-core decision loop.” This is especially true for `ai_slop`, `ced_score`, `coverage_warning`, and `cost_log`.
- **Fact:** `condex_*` supplements do not overturn the TF surveys. They mainly prove that several signals are visible in bridge/UI/operator surfaces even when they are still dead or weak in runtime-core retry routing.
- **Fact:** two scope-sensitive names had to be normalized to eliminate false conflict:
  - `open_review` is live inside same-round `previous_attempt`, but `episode_quality_labels.open_review` replay is still dead for later generation loops.
  - `reverse_feedback` is split: Stage 4→2 is working, while Stage 4→3 and Stage 3→2 remain fragile because they are not auto-triggered.
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
| `coverage_warnings` | TF-C says advisory-only for core retry | `condex` TF-B says operator calibration consumes it | **Resolved:** operator advisory exists, runtime-core retry still weak/advisory |
| Stage 4 quality signal bundle | TF-D says dead for CW retry | `condex` TF-C/E say bridge quality radar consumes it | **Resolved:** split `runtime-core` vs `operator/UI` consumers; canonical broken status remains for runtime-core retry |
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

Pass 3 result: ready for implementation ordering and roadmap orchestration.

## Signal Taxonomy

| Signal | Runtime-Core Status | Operator / UI Status | Canonical Interpretation |
| --- | --- | --- | --- |
| `ai_slop` / quality signal bundle | `DEAD` for retry routing | `CLOSED` in bridge quality radar | measured and surfaced, but still broken for CW/runtime remediation |
| `ced_score` | `DEAD` for retry routing | `CLOSED` in bridge quality radar | good candidate for bounded warning injection |
| `compression_ratio` / `burstiness` / `complexity` | `DEAD` for retry routing | `CLOSED` in bridge quality radar | keep-audit by default unless promoted |
| `open_review` same-round handoff | `WORKING` | n/a | reaches CW through `previous_attempt` when Director emits it |
| `open_review` label replay | `DEAD` | `CLOSED` in bridge latest-label summary | cross-episode reuse path is still missing |
| `npc_drift` structured handoff | `ADVISORY-ONLY` | n/a | Director sees it, CW does not get a durable structured payload |
| `coverage_warnings` | `ADVISORY-ONLY` / `WEAK` | `ADVISORY` in dashboard/bridge | explicit retry or rebuild surfacing is still missing |
| `dialogue_ratio` | `ADVISORY` | n/a | measured with a fixed threshold, not the project StyleGuide target |
| `vocabulary_level` | `DEAD` | n/a | extracted and prompted, but never validated |
| `FactLedger` continuity | `FRAGILE` | n/a | data exists, but hard escalation is inconsistent or advisory-only |
| `reverse_feedback` Stage 4→2 | `WORKING` | n/a | already injected via Stage 2 preflight when arc difficulty is high |
| `reverse_feedback` Stage 4→3 | `FRAGILE` | n/a | implemented helper, but not auto-triggered |
| `reverse_feedback` Stage 3→2 | `FRAGILE` | n/a | thresholded helper exists, but still not a robust automatic loop |
| `DPW` | `LIVE` | n/a | keep as a working loop, not a remediation target |
| `FailureLearner` | `LIVE` / `WORKING` | n/a | keep as a working loop, not a remediation target |
| `cost_log` DB summary | `DEAD` | n/a | `get_cost_summary()` has no production caller |
| shutdown metric totals | `ADVISORY` | logs only | do not confuse shutdown sink consumption with runtime cost control |
| control-plane provenance | `OPEN` | write-only log | not a tranche priority, but remains an uncovered reader path |

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

Priority:

1. `ai_slop` / style digest wiring
2. `dialogue_ratio` dynamic target linkage
3. `ced_score` warning injection

Required shape:

- Python may continue measuring raw metrics, but it must not become the final reject authority
- any style remediation fed to CW must be Director-mediated
- `dialogue_ratio` must stop using a fixed `0.30` ideal and instead read the project style target

Starting gate:

- rerun a codebase validity check on `style_extractor`, `style_guard`, `pre_director_manuscript_checker`, post-pass quality signal persistence, and CW retry ingress before patching
- confirm the tranche still targets a real runtime-core gap rather than an already-closed operator/UI-only sink

Regression gate:

- use `0_260316` as proof corpus
- preserve `Menu 7` resumability and existing frontier facts
- verify that shared style findings remain wording-consistent with the companion project SSOT

### Tranche 2: Validation / Escalation Hardening

Priority:

1. `FactLedger` hard constraint escalation
2. `coverage_warnings` explicit surfacing
3. `npc_drift` structured handoff

Required shape:

- advisory-only facts that should block or escalate must become explicit runtime inputs
- `coverage_warnings` must stop dying in observability summaries
- `npc_drift` must become a structured Director-mediated retry artifact rather than a transient advisory only

Starting gate:

- rerun a codebase validity check on `FactLedger`, `coverage_warnings`, `npc_drift`, and related retry/escalation consumers before patching
- confirm the tranche still targets an escalation gap and not just a documentation wording difference

Regression gate:

- confirm `0_260316` shared Stage 4 findings still reproduce as expected
- confirm no project-specific recovery claim in the companion SSOT becomes stale

### Tranche 3: Reverse-Loop Automation and Observability Consumption

Priority:

1. Stage 4→3 reverse feedback auto-trigger
2. Stage 3→2 reverse feedback auto-trigger
3. `cost_log` runtime consumption

Required shape:

- do not rebuild the already-working Stage 4→2 reverse difficulty path
- only automate the fragile reverse paths that still depend on manual or thresholded manual-style invocation
- either give `cost_log` a real runtime reader or explicitly demote it to audit-only so the dead loop disappears

Starting gate:

- rerun a codebase validity check on reverse-feedback helpers, trigger sites, and `cost_log` readers before patching
- confirm Stage 4→2 remains `WORKING` and that Stage 4→3 / Stage 3→2 / runtime cost consumption still require tranche work

Regression gate:

- `0_260316` remains the shared Stage 4 regression fixture
- bridge/UI consumers must continue working after runtime-core wiring changes

## Acceptance Criteria

- each tranche starts only after a current-code validity check confirms the targeted loop classification is still accurate
- if the pre-tranche validity check discovers drift, this SSOT is refreshed with a new 3-pass audit before code changes begin
- each tranche completes the full loop of validity check -> implementation -> 3-pass audit -> doc update -> next-tranche selection
- Tranche 1 closes the runtime-core gap for `ai_slop`, `dialogue_ratio`, and `ced_score` without giving Python final quality sovereignty.
- Tranche 2 closes the escalation gap for `FactLedger`, `coverage_warnings`, and `npc_drift`.
- Tranche 3 distinguishes the already-working Stage 4→2 path from the still-fragile Stage 4→3 and Stage 3→2 paths and resolves the dead `cost_log` consumer gap.
- `0_260316` remains a valid regression fixture for shared Stage 4 findings after each tranche.
- bridge/desktop/operator surfaces continue to function; runtime-core improvements must not break existing operator visibility.

## Open Items

| Item | Status | Impact |
| --- | --- | --- |
| `control-plane provenance` runtime reader absence | open | low |
| `MetricsCollector.record_retry()` caller absence | open | low |
| `PassRateMonitor.get_patch_effectiveness()` unused helper | open | low |
| `QualityDashboard.get_quality_signal_snapshot()` unused helper | open | low |
| HUD anomaly / blueprint coverage instrumentation producer gaps | open | low |

Notes:

- these open items are intentionally left out of the main tranches because they are lower ROI than the broken runtime-core feedback loops above
- if a later tranche promotes them, this SSOT should be refreshed rather than patched ad hoc
