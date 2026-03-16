# Broken Feedback Loop Remediation Execution Roadmap

Date: 2026-03-16
Status: completed canonical
Canonical Path: `docs/2026-03-16/broken-feedback-loop-remediation-execution-roadmap.md`
System SSOT: `docs/2026-03-16/broken-feedback-loop-remediation-execution-ssot.md`
Project SSOT: `docs/2026-03-16/project-0-260316-execution-ssot.md`
Confidence: `96%`

## Summary

- canonical structure is fixed as `2 SSOT + 1 roadmap`
- the system SSOT owns bundle-wide broken feedback loop remediation
- the project SSOT owns `0_260316` recovery, stop-point, integrity, resumability, and project-specific regression authority
- this roadmap owns ordering, overlap classification, and sync rules between the two SSOTs
- all planned tranches are now closed; no active tranche remains
- the low-priority `control-plane provenance` reader is also closed via bridge `/status`, and `PassRateMonitor.get_patch_effectiveness()` is now closed via bridge quality dashboard; only opportunistic helper cleanups remain

## Why Not One SSOT

- system scope and project scope are different
- refresh cadence is different
- recovery decisions and remediation queues use different acceptance gates
- forcing both into one document would blur authority and make regression refreshes harder

## Overlap Reconciliation

| Topic | Classification | Canonical Authority | Note |
| --- | --- | --- | --- |
| `ai_slop` feedback gap | `shared-consistent` | system SSOT for remediation, project SSOT for proof corpus | same finding, different scope |
| `npc_drift` retry handoff | `shared-consistent` | system SSOT | project SSOT keeps only the proof-corpus boundary while the system SSOT owns remediation status |
| `open_review` | `shared-needs-wording-sync` | system SSOT | must distinguish same-round live handoff from dead label replay |
| `coverage_warning` surfacing | `shared-consistent` | system SSOT | project SSOT keeps only the proof-corpus boundary while the system SSOT owns remediation status |
| `FactLedger` fragility | `system-only` | system SSOT | keep out of project canonical lane except as regression observation |
| `reverse_feedback` auto-trigger status | `system-only` | system SSOT | split Stage 4→2 from Stage 4→3 and Stage 3→2 |
| `dialogue_ratio` style-target linkage | `system-only` | system SSOT | not a `0_260316` recovery fact |
| `cost_log` runtime reader gap | `system-only` | system SSOT | not a `0_260316` recovery fact |
| `ep7` stop point, integrity, resumability | `project-only` | project SSOT | do not promote into system SSOT |
| `Menu 7 이어가기`, `Arc 3 / Blueprint 11 / Manuscript 6` | `project-only` | project SSOT | remain project facts only |

## Pre-Tranche Validity Rule

- before every tranche, validate the current codebase against the system SSOT instead of starting from survey text alone
- the validity check must confirm current producers, consumers, trigger paths, and authority boundaries for the tranche target
- if live code no longer matches the tranche assumptions, refresh the system SSOT first and then re-sync the project SSOT wording if needed
- `0_260316` stays the regression gate after the validity check passes; it is not a substitute for the validity check itself

## Automatic Tranche Loop

For every tranche, run the same control loop:

1. current-code validity check
2. bounded implementation
3. fresh 3-pass audit
4. canonical doc update and any required mirror sync
5. select the next tranche from the refreshed roadmap

Selection rule:

- the next tranche is chosen only after step 4 completes
- if the just-finished tranche changes taxonomy, priority, or regression assumptions, refresh this roadmap before selecting the next tranche
- if no pending tranche clears the new validity gate, stop the loop and re-audit the governing docs first

## Execution Order

### 1. Tranche 1: Low-Risk / High-ROI Core Feedback Closure

- completed on `2026-03-16`
- validity gate confirmed style-signal producers were live, operator/UI readers already existed, and the real gap was bounded Director-mediated retry ingress plus fixed-threshold `dialogue_ratio`
- landed shape:
  - `ai_slop` / `ced_score` now surface through `StyleSignalAdvisor` into Director-mediated retry feedback
  - `dialogue_ratio` now reads the project style target in pre-director validation
  - no new Python hard-reject authority was introduced
- verification:
  - `tests/test_project_support.py` -> `10 passed`
  - `tests/test_pre_director_submodules.py` -> `21 passed`
  - `tests/test_stage4_interview_round.py -k "quality_signal or advisory_style or retry_feedback_provenance"` -> `3 passed`
  - `tests/test_stage4_interview_round.py` -> `82 passed`
  - `ruff check` on touched producer/consumer/test files -> `All checks passed`

### 2. Tranche 2: Validation / Escalation Hardening

- completed on `2026-03-16`
- validity gate confirmed the real gap was not missing producers but missing structured runtime handoff for `FactLedger`, `coverage_warning`, and `npc_drift`
- landed shape:
  - `npc_drift` now survives selected-validation payloads, retry provenance, and CW-facing retry warning payloads
  - `coverage_warning` now surfaces through a dedicated `[검색 커버리지 경고]` mandatory-context section and structured retry evidence
  - `FactLedger` numeric consistency now survives as explicit Director-mediated retry evidence without introducing Python hard-reject authority
- verification:
  - `tests/test_stage4_interview_round.py` -> `85 passed`
  - `tests/test_stage4_context_builder.py` -> `53 passed`
  - `tests/test_numeric_consistency_checker.py` -> `40 passed`
  - `tests/test_stage4_cv_context.py` -> `21 passed`
  - `ruff check` on touched producer/consumer/test files -> `All checks passed`
  - `python scripts/ops_validator.py` -> `errors=0 warnings=0`
- regression gate:
  - `0_260316` remains a valid proof corpus
  - wording in the project SSOT remains consistent for shared topics
  - shared items do not become duplicated canonical queues in the project SSOT

### 3. Tranche 3: Reverse-Loop Automation / Observability Consumption

- completed on `2026-03-16`
- live-code validity gate result:
  - Stage 4→3 was already auto-triggered in `stage4_orchestrator.py`; no patch was needed there
  - Stage 3→2 already had the thresholded consumer in `stage2_preflight.py`, but Stage 3 REJECT paths were not persisting `stage_rejection_history`
  - `cost_log` DB summaries still lacked a production read surface
- landed shape:
  - `stage3_orchestrator.py` now persists compact Stage 3 reject-history entries used by the existing Stage 3→2 threshold trigger
  - `bridge_server.py` now exposes `cost_summary` from `DBManager.get_cost_summary()` in the bridge quality dashboard
  - existing Stage 4→3 auto-trigger behavior was revalidated and left intact
  - post-tranche bounded closure also landed: `bridge_server.py` now reads recent `control-plane-provenance.jsonl` rows into an optional `/status` summary
- regression gate:
  - Stage 4→2 reverse difficulty path remains intact
  - Stage 4→3 and Stage 3→2 are now reclassified from fragile to working based on fresh live-code evidence
  - runtime cost consumption changes do not break existing shutdown telemetry
- verification:
  - `tests/test_stage3_orchestrator.py` -> `72 passed`
  - `tests/test_stage2_preflight.py` -> `27 passed`
  - `tests/test_bridge_quality_summary.py tests/test_cost_tracking.py` -> `15 passed`
  - `tests/test_stage4_orchestrator.py -k "stage4_to_3_feedback"` -> `1 passed`
  - `tests/test_bridge_server_http_contract.py` -> `8 passed`
  - `tests/test_control_plane_approval_provenance_ssot.py tests/test_bridge_server_desktop_risk_gate.py` -> `7 passed`
  - `ruff check` on touched producer/consumer/test files -> `All checks passed`
  - `python scripts/ops_validator.py` -> `errors=0 warnings=0`

### 4. Post-Tranche Sync

- after each tranche, refresh the system SSOT with a fresh 3-pass audit
- do not start the next tranche until the new current-code validity check passes on the then-live codebase
- only update the project SSOT if one of these changes:
  - a shared finding changes wording or status
  - `0_260316` regression evidence changes
  - project recovery/resumability facts change
- do not rewrite project-only recovery sections for system-only remediation movement
- after the doc refresh, automatically choose the next highest-priority pending tranche whose starting gate still passes
- current outcome: no pending tranche remains; the roadmap is closed pending any future re-open triggered by a fresh validity gate
- residual low-priority items are now outside the remediation queue unless a future validity gate promotes them; `PassRateMonitor.get_patch_effectiveness()` no longer belongs to that residual set

## Acceptance Criteria

- the system SSOT and project SSOT remain non-overlapping in authority
- shared topics stay classified as `shared-consistent` or `shared-needs-wording-sync`; `conflict` must remain `0`
- implementers can choose the next tranche without consulting the raw `docs/sp` bundle
- each tranche begins only after a current-code validity check confirms the roadmap assumptions still match live code
- each tranche ends with updated docs before the next tranche is selected
- `0_260316` continues serving as the regression gate for shared Stage 4 findings while remaining the sole authority for project recovery facts
