# 0_0 Stage3 Contract Tightening Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (promoted from parked on 2026-04-07 roadmap reorder; re-audited again against the current workspace before implementation start; the first bounded tranche then landed by widening binding enforcement for `dead_npc`, stop-line/`arc_compliance`, and `fact_lock_*` seams, persisting binding metadata through Stage3 success handoff, and teaching Stage4 to consume that metadata as real Director/retry pressure; a later 2026-04-08 bounded observability follow-up then surfaced actual Stage3 source-anchor summaries for flashback/opening/inherited inventory planning through runtime, DB, and operator-visible sinks; the newest same-day follow-up landed a Stage3 proof-digest / `PassRateMonitor` durability slice, but the later `projects/000_260408` proof-wave merge audit did not exercise Stage3 at all, and the newer `projects/000_260408_B` proof-wave merge audit again shows Stage3 absent by operator choice while the upstream Stage2 handoff packet is structurally ready, so the new Stage3 proof surfaces remain verification-pending until a fresh run actually reaches Stage3; explicit tier-2.5 canary proof still remains required before closure)
Canonical Path: `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2/Stage3 survey docs and lane drafts untracked`
- Resume Commit: `6dd7712ea9a58802221634081ba199bc872d2349`
- Resume Drift Summary: `the queue was later re-ranked to make this the next unopened implementation lane, the 2026-04-07 Stage234 terminal survey confirmed the still-live Stage3 seams as binding-scope gaps plus advisory-only `_stage3_meta` handoff, the originally listed static survey and runtime closure audit now live under archived `docs/이전/` paths, the previously referenced Stage3 artifact JSON paths are no longer present in the active workspace so this SSOT now relies on the archived survey/evidence set plus the 2026-04-07 handoff survey rather than stale artifact-local pointers, the current workspace first landed a bounded tranche across `unified_blueprint_validator.py`, `three_phase_blueprint_runtime.py`, `stage3_orchestrator.py`, `stage4_director_runtime.py`, and `stage4_outcome_runtime.py` with focused regression/static validation, a later same-day follow-up in `stage3_orchestrator.py` then persisted source-anchor summaries for previous-blueprint end state plus current Stage2 carryover start state so flashback/opening/inherited-inventory proof waves have cleaner operator-visible evidence while fresh tier-2.5 canary proof stays deferred, the newest same-day follow-up across `stage3_orchestrator.py` plus `audit_service.py` then landed a Stage3 proof-digest / `PassRateMonitor` durability slice, the later `docs/2026-04-08/stage23-proof-wave-parallel-merge-audit.md` confirmed that the first fresh run never reached Stage3, and the newer `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md` confirms the absence again while also upgrading the upstream Stage2 handoff from sink-drift-risk to structurally ready proof input`
Source Survey Docs:
- `docs/이전/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/이전/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-07/stage234-terminal2-stage3-binding-handoff-survey.md`
- `docs/2026-04-08/stage23-proof-wave-parallel-merge-audit.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md`
Evidence Artifacts:
- `docs/이전/2026-04-02/0_0-stage3-static-global-evidence.json`
- `docs/이전/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-evidence.json`
- `projects/000_260408/project_data.db`
- `projects/000_260408/logs/runtime_audit_summary.json`
- `projects/000_260408/logs/pass_rate_monitor.json`
- `projects/000_260408/logs/session/decisions.jsonl`
- `projects/000_260408/logs/session/ui_events.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded queued lane for `Stage3 contract tightening` without promoting it ahead of active `Stage4` remediation seams.

This execution SSOT exists because the latest static survey proved:

- Stage3 is not hierarchy-free chaos
- Stage3 still remains the first material drift point in artifact truth
- the core problem is `weak enforcement + semantically lossy handoff`, not missing prompt structure alone

## 2. Baseline Facts

- Stage3 generation hierarchy is explicit and reasonably well-structured.
- Stage3 validator/binding is advisory-heavy and cannot independently hard-block the most dangerous seams.
- Stage3 -> Stage4 handoff is transport-clean but semantic-lossy.
- Off-arc invention improved under prior semantic-fidelity work, but timeline/institution drift remains.
- The most important residual debt is not Stage2 content starvation but Stage3 contract enforcement weakness.

## 3. Scope

Included:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- bounded Stage3 binding-scope and escalation hardening surfaces
- bounded Stage3 -> Stage4 semantic handoff preservation where Stage3 owns the machine-readable contract
- targeted Stage3-owned contract metadata emission required to preserve downstream subtype fidelity

Excluded:

- broad Stage3 prompt or generation retuning
- active Stage4 fix-pack/finalization work
- Stage2 contract normalization
- fresh canary execution in this lane
- DB schema redesign
- broad architecture compression in the same turn

## 4. Pass 1. Inventory Summary

Primary debt inventory for this wave:

1. binding scope gap
2. advisory-only enforcement after Python prevalidation
3. structured constraint truth surviving only as prose blueprint semantics at handoff
4. timeline and institution fidelity categories lacking strong Stage3-owned contract coverage

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is reactivated

- binding scope tightening
- Stage3 -> Stage4 semantic contract preservation
- targeted timeline/entity/institution contract tightening only where validator/compiler owns the contract

### Class B. Residual but related

- broad Stage3 prompt retuning
- further reduction of off-arc invention pressure in cold-start episodes
- context caching hierarchy degradation risk

### Class C. Explicitly deferred outside this lane

- current active Stage4 remediation lanes
- Stage2 contract normalization
- fresh canary execution in this turn
- Stage3 external-stage compression itself

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage3 blueprint artifact shape and metadata may change

- DB / schema / transaction boundaries:
  - not applicable for this bounded pending lane

- JSONL / log / audit sinks:
  - Stage3 prevalidation and verdict metadata may become richer or more binding

- console / UI / operator output:
  - advisory / binding categories and severity visibility may change

- rollback / recovery / retry:
  - stronger Stage3 binding can increase early-stage rejection or PASS_WITH_FIX frequency

- cache / global state:
  - cached shared context or model packet ordering could be impacted by contract strengthening

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### Tranche 1. Binding Scope Tightening

Goal:

- stop leaving high-severity seams outside effective binding behavior

Realization direction:

- review category membership and escalation semantics for high-severity Stage3 seams
- tighten which issues remain advisory-only

### Tranche 2. Timeline / Institution Fidelity Tightening

Goal:

- close timeline / institution seams only where Stage3 validator or compiler owns the contract

Realization direction:

- tighten high-severity category coverage for timeline / institution seams
- avoid broad generation retuning in the same lane

### Tranche 3. Semantic Handoff Preservation

Goal:

- make Stage4 receive stronger machine-meaningful Stage3 contract hints

Realization direction:

- preserve more Stage3 semantic subtype information at the handoff boundary
- reduce reliance on prose-only fidelity survival
- emit only the minimum Stage3-owned metadata needed for downstream bounded repair or verification

## 8. Execution Tranches

1. binding scope and escalation tightening
2. Stage3 -> Stage4 semantic contract preservation
3. targeted timeline/entity/institution contract tightening
4. bounded regression coverage
5. later runtime proof only after explicit reactivation

## 8A. Implementation Update (2026-04-07)

- Tranche 1 landed in bounded form:
  - `dead_npc`, `arc_compliance`, `fact_lock_location`, `fact_lock_item`, and `fact_lock_provenance` now participate in Stage3 binding escalation when severity is `MAJOR/CRITICAL`
- Tranche 2 landed in bounded handoff form:
  - Stage3 validation/runtime now preserves `binding_prevalidation_issue_count` plus category metadata through `pipeline_result["phases"]["validate"]` and persisted `_stage3_meta`
  - Stage4 Director and retry escalation now consume those Stage3-owned binding signals as structured caution/escalation input instead of treating them as dead handoff fields
- fresh runtime proof remains deferred:
  - focused pytest, `py_compile`, and `ruff` closed
  - explicit tier-2.5 canary proof is still required before closure

## 8B. Observability Update (2026-04-08)

- a bounded same-lane follow-up is now landed in `stage3_orchestrator.py`
  - Stage3 runtime/advisory sinks now persist `source_anchor_summary`
  - the summary pins previous-blueprint episode/location/transition anchors plus current Stage2 start-location and start-inventory anchors
- operator-visible Stage3 summary logs now echo the compact source-anchor line so later flashback/opening drift can be attributed without digging only through raw blueprint JSON
- this follow-up is observability-only:
  - it does not retune Stage3 generation
  - it does not reopen Stage2 or Stage4 ownership
  - it narrows the next upstream proof wave by making the actual anchor surfaces explicit

## 8C. Runtime Summary / Monitor Durability Update (2026-04-08)

- a later same-lane follow-up is now also landed across `stage3_orchestrator.py` and `audit_service.py`
  - Stage3 `PassRateMonitor` writes now flush immediately after each PASS/REJECT attempt record
  - `audit_service.py` now includes the Stage3 latest-session summary path for attempt coverage, decision-row coverage, artifact-path coverage, and the latest persisted `source_anchor_summary`
- this follow-up stays inside the same bounded lane:
  - it does not retune Stage3 generation
  - it does not change Stage3 semantic ownership
  - it reduces proof-wave dependency on manual DB/JSONL joins for basic Stage3 attribution once a fresh run actually reaches Stage3

## 8D. Fresh Proof-Wave Revalidation (2026-04-08)

- `projects/000_260408` did not exercise Stage3:
  - `stage_attempts` has `0` Stage3 rows
  - `director_selections` has `0` Stage3 rows
  - `blueprints` has `0` rows
  - `logs/artifacts/stage3/` is absent
  - `logs/session/ui_events.jsonl` has `0` `source_anchor_summary` rows
  - `logs/session/decisions.jsonl` has `0` Stage3 rows
  - `logs/pass_rate_monitor.json` has `0` records
- `runtime_audit_summary.json` is internally consistent with that runtime fact:
  - `proof_digest.operational_metadata.stage3_live_session.status = "absent"`
  - `attempt_count = 0`
  - `episodes = []`
- execution consequence:
  - do not treat the current absence as a logging-only failure
  - do not claim the landed Stage3 source-anchor / monitor slice is runtime-validated yet
  - keep this SSOT verification-pending until a fresh run actually reaches Stage3
  - keep the next proof artifact bounded to `Stage2 proof-sink repair -> rerun that reaches Stage3`, not a new Stage3 design lane
- watch item only:
  - the current proof wave does not justify a new upstream owner change, but the eventual Stage3-exercising rerun should still confirm whether Stage2-origin anchor inputs are sufficient for `source_anchor_summary`

## 9. Acceptance Criteria

- highest-risk Stage3 seams no longer remain purely advisory by default
- Stage3 -> Stage4 handoff preserves more than prose-only semantics for key contract fields
- timeline and institution drift have stronger structured enforcement paths where Stage3 validator/compiler owns the contract
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage3 validator regressions
- targeted Stage3 handoff contract regressions
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not activate this lane before explicit operator decision
- do not let this partial lane outrank current active Stage4 seams without deliberate reprioritization
- do not widen this lane into broad Stage3 prompt retuning
- do not widen this lane into Stage2 redesign or Stage4 redesign
- do not run a canary from this lane until explicit operator approval

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - keep the temp mirror as an active verification-pending queue item until explicit closure or replacement
- roadmap dependency:
  - this item stays below active Stage4 lanes and the narrower pending Stage4/Stage2 child slices

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a bounded execution SSOT tied to the live queue rather than widening it into a broad Stage3 rewrite
- narrowed this wave to validator/binding enforcement plus semantic handoff preservation
- excluded broad Stage3 prompt retuning, Stage2 normalization, and active Stage4 remediation from scope

Pass 2, evidence and consistency:

- aligned the document with the archived Stage3 static global survey verdict and the archived runtime closure audit
- refreshed the source/evidence paths so they match the current workspace layout
- removed stale Stage3 artifact-local pointers that no longer exist in the active workspace
- incorporated the 2026-04-07 Stage234 terminal survey as the latest narrow handoff/binding confirmation

Pass 3, execution and readability:

- made the pending promotion explicit
- kept tranches validator/compiler-owned and implementable
- tied future activation to an explicit canary-proof gate rather than implicit urgency

Confidence: `98%`

## 15. 2026-04-08 Fresh Proof-Wave Validation Upgrade (`000_260408_B`)

Evidence basis:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md`
- `0_temp.txt`
- `projects/000_260408_B/project_data.db`
- `projects/000_260408_B/logs/runtime_audit_summary.json`
- `projects/000_260408_B/logs/runtime_audit.jsonl`

Fresh proof-wave verdict:

1. Stage3 still was not exercised on `000_260408_B`:
   - operator exited from the main menu after `Stage 2 [✅]`
   - `stage_attempts`, `director_selections`, `llm_calls`, and `blueprints` contain `0` Stage3 rows
   - `logs/artifacts/stage3/` is absent
   - `proof_digest.operational_metadata.stage3_live_session.status = "absent"`
2. the absence should now be read more cleanly than on the prior run:
   - it is operator-choice / not exercised, not a fresh Stage3 logging failure
   - the upstream Stage2 proof sinks are no longer the main ambiguity; `stage2_live_session.status = "ok"` and the latest `carryover_authority` packet is fully surfaced
3. the Stage2 -> Stage3 handoff is structurally ready:
   - final Stage2 arc has a reachable artifact path, populated `attempt_key`, populated `selection_reason`, populated `verdict_reason`, populated `fix_scope_reasoning`, and full `carryover_authority`
   - the only promoted watch item is semantic rather than sink-related: arc 3 still records a latent asset-math contradiction inside `verdict_reason`

Execution consequence:

- keep this Stage3 lane verification-pending rather than runtime-failed
- do not open another broad Stage3 patch from absence-only evidence
- take a rerun that actually reaches Stage3 as the next useful proof artifact
- if that rerun still exits before Stage3, treat the cause as runtime/operator control flow first, not as proof-sink regression

Confidence for this validation upgrade: `97%`
