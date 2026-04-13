# 0_0 Stage3 Contract Tightening Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (the earlier Stage3 binding/handoff/source-anchor tranches remain landed, the reopened 2026-04-11 truth-first parent tranche is landed on the live workspace, the later fail-only structural hardening tranche is also landed, and the 2026-04-12 live rerun follow-up slice is now likewise landed on the live workspace: success proof sinks now sit behind committed persistence, Stage3 `runtime_advisory` / `retry_directives` normalization is in place, `PASS_WITH_FIX` success-accounting parity is restored, analyzer sink-alignment coverage is widened, `opening_anchor` / `scene_completeness` structural binding failures now escalate to regenerate-only full repair with explicit visibility, ep-boundary replay leakage plus canonical institution drift on the ep2 -> ep3 seam now force regenerate-only repair through `episode_progression` truth and expanded institution fact-lock coverage, the first 2026-04-13 child-lane follow-up blocks the observed Stage3 retry plateau by denying low-yield inplace reopening after `PASS_WITH_FIX` exhaustion or repeated inplace score/signature plateau, the second same-day live-rerun follow-up now also blocks `Director PASS < quality_gate` patch reopening while suppressing blind live-HUD V46 current-state injection during blueprint scoring unless an explicit `blueprint_scoring_hud` is provided, and a narrower same-day closure-residual observability follow-up is now also landed so Stage3 completion stats separate the current-run pass rate from the cumulative generator pass rate; the older first-ensemble visibility follow-up remains documented but not yet landed, and proof remains pending)
Canonical Path: `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2/Stage3 survey docs and lane drafts untracked`
- Resume Commit: `2701e9e6a7d741d455afc930afd94e178ed555d4`
- Resume Drift Summary: `snapshot main is now authoritative; the earlier binding/handoff/source-anchor tranches remain landed, the live workspace on top of current main now also carries the reopened truth-first parent tranche, the bounded Stage3 analyzer sink-alignment coverage follow-up, the later fail-only structural hardening tranche for regenerate-only binding categories plus visibility propagation, the later ep3 replay / institution-truth fail-only follow-up across compiler/validator/runtime, the 2026-04-13 child-lane retry-plateau and quality-gate/truth follow-ups, and the narrower same-day closure-residual observability follow-up in `stage3_orchestrator.py` that now separates current-run pass-rate authority from cumulative generator pass-rate authority while stale 2026-04-11 backup-branch work remains excluded from this SSOT's authority`
Source Survey Docs:
- `docs/이전/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/이전/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-07/stage234-terminal2-stage3-binding-handoff-survey.md`
- `docs/2026-04-08/stage23-proof-wave-parallel-merge-audit.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md`
- `docs/2026-04-12/stage234-ep3-continuity-replay-season-truth-live-run-followup-parallel-survey.md`
- `docs/2026-04-12/stage234-ep3-continuity-replay-season-truth-live-run-followup-3pass-audit.md`
- `docs/2026-04-12/stage3-first-ensemble-visibility-live-run-compact-survey.md`
- `docs/2026-04-10/00_000-stage3-fresh-run-abort-post-run-merge-audit.md`
- `docs/2026-04-10/stage3-blueprint-first-pass-structural-survey.md`
- `docs/2026-04-10/stage3-blueprint-layering-first-adversarial-audit.md`
- `docs/2026-04-13/stage3-live-run-retry-plateau-parallel-full-survey.md`
- `docs/2026-04-13/stage3-live-run-quality-gate-patch-reopen-parallel-full-survey.md`
- `docs/2026-04-13/stage3-live-run-quality-gate-patch-reopen-3pass-audit.md`
- `docs/2026-04-13/stage3-live-run-closure-and-residual-families-parallel-full-survey.md`
- `docs/2026-04-13/stage3-closure-residual-fail-only-promotion-survey.md`
- `docs/2026-04-11/stage23-current-main-static-parallel-survey.md`
Evidence Artifacts:
- `docs/이전/2026-04-02/0_0-stage3-static-global-evidence.json`
- `docs/이전/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-evidence.json`
- `projects/000_260408/project_data.db`
- `projects/000_260408/logs/runtime_audit_summary.json`
- `projects/000_260408/logs/pass_rate_monitor.json`
- `projects/000_260408/logs/session/decisions.jsonl`
- `projects/000_260408/logs/session/ui_events.jsonl`
- `0_temp.txt`
- `projects/00_000/logs/session_20260410_143423.log`
- `projects/00_000/logs/session_20260410_160214.log`
- `projects/00_000/logs/runtime_audit_summary.json`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded queued lane for `Stage3 contract tightening` without promoting it ahead of active `Stage4` remediation seams.

This execution SSOT exists because the latest static survey proved:

- Stage3 is not hierarchy-free chaos
- Stage3 still remains the first material drift point in artifact truth
- the core problem is `weak enforcement + semantically lossy handoff`, not missing prompt structure alone

## 2. Baseline Facts

- Stage3 generation hierarchy is explicit and reasonably well-structured.
- Stage3 validator/binding is no longer purely advisory-heavy: the most dangerous structural seams now escalate to regenerate-only full repair rather than cheap inplace patching.
- Stage3 -> Stage4 handoff is transport-clean but semantic-lossy.
- Off-arc invention improved under prior semantic-fidelity work, but timeline/institution drift remains.
- The most important residual debt is now proof-pending enforcement confirmation plus broader semantic-lossy handoff, not an inability to hard-block the clearest structural seams.
- A smaller same-lane observability seam also remains: the first expensive Stage3 ensemble wait can look stalled on the main console even while session-log evidence proves forward progress.
- A newer same-lane proof seam is now explicit: Stage3 can still spend cost after a real Director `PASS` if the quality gate force-rejects and reopens `inplace`, and blueprint scoring can over-consume live HUD truth when `V46` current-state context is injected too broadly.

## 3. Scope

Included:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- bounded Stage3 binding-scope and escalation hardening surfaces
- bounded Stage3 -> Stage4 semantic handoff preservation where Stage3 owns the machine-readable contract
- targeted Stage3-owned contract metadata emission required to preserve downstream subtype fidelity
- ep-local packet layering / gating for Stage3 blueprint generation input
- threshold alignment across validator, Director compare, and runtime quality-gate seams
- canonical patch-anchor transport for Stage3-local repair feedback

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
  - first-ensemble heartbeat / candidate-progress legibility remains a bounded pending operator surface in this same lane

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

2026-04-12 live-workspace update:

- `opening_anchor`
- `scene_completeness`
- bulk `key_events` omission

now route through regenerate-only full repair instead of staying on the cheap inplace path, and the runtime preserves `binding_regenerate_only_categories` plus `binding_regenerate_only_reason` through validate/retry/meta surfaces.

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

## 8E. Aborted Fresh-Run Revalidation (2026-04-10)

- `docs/2026-04-10/00_000-stage3-fresh-run-abort-post-run-merge-audit.md` is now the newest runtime anchor for this lane
- the fresh `00_000` run finally reached Stage3 episode 1:
  - live logs show multiple Stage3 `PASS_WITH_FIX` entries and entry into the local repair loop
  - this replaces the older absence-only proof posture as the current runtime fact
- the run still does not close this parent lane:
  - the operator aborted the run before Stage3 committed sinks finalized
  - `runtime_audit_summary.json` still reports `stage3_live_session.status = "absent"` for the aborted session
  - `stage_attempts`, `director_selections`, and `blueprints` still contain `0` committed Stage3 rows for this run
- execution consequence:
  - do not treat the remaining blocker as "Stage3 still unexercised"
  - do not open another broad Stage3 redesign from this evidence
  - the immediate owner is now the narrower `0_0-stage3-partial-fix-hardening-remediation` child lane because the live run surfaced a concrete `PASS_WITH_FIX` repair-loop / `TF-35` churn bug inside that ownership surface
  - after the child repair lands, take the next rerun as the useful proof path for this parent lane

## 8F. Same-Day Child-Lane Repair Follow-Up (2026-04-10)

- the bounded Stage3 partial-fix/runtime follow-up is now landed in `three_phase_blueprint_runtime.py`
- that follow-up does not widen this parent lane's scope:
  - it preserves low-score `PASS` patch state for retry carry-forward
  - it aligns reject bookkeeping to the re-audit score
  - it does not retune broad Stage3 generation or reopen Stage2/Stage4 ownership
- execution consequence:
  - the next useful artifact for this parent lane returns to a fresh rerun that reaches Stage3
  - closure still requires a completed rerun, not this bounded local repair alone

## 8F-2. Live Retry Plateau Follow-Up (2026-04-13)

- `docs/2026-04-13/stage3-live-run-retry-plateau-parallel-full-survey.md` is now the newest runtime diagnostic anchor for the Stage3 live rerun plateau.
- the confirmed live symptom was not a hard stall:
  - session logs kept advancing
  - the active failure was a low-yield retry loop around repeated inplace reopenings, repeated `PASS_WITH_FIX unresolved`, and repeated low-score rejections on the same episode family
- immediate ownership stayed split as intended:
  - parent lane ownership remained on Stage3 truth / contract / handoff surfaces
  - child-lane ownership remained on partial-fix retry exhaustion / locality control
- landed outcome:
  - the child lane now tracks reject origin, reject signature, repeated score/signature streaks, and inplace reject streaks
  - Stage3 now blocks inplace patch reopening after `PASS_WITH_FIX` exhaustion or repeated inplace plateau patterns
- execution consequence:
  - do not open a fresh broad Stage3 redesign from this evidence
  - do not promote visibility-only work over the now-landed plateau breaker
  - take the next useful artifact as the bounded rerun / proof wave

## 8G. Layering-First Design Promotion (2026-04-10 same-day)

- the later current-HEAD rerun captured in `projects/00_000/logs/session_20260410_160214.log` plus the newer `docs/2026-04-10/stage3-blueprint-first-pass-structural-survey.md` and `docs/2026-04-10/stage3-blueprint-layering-first-adversarial-audit.md` now sharpen the remaining parent-lane owner
- the new design conclusion is bounded and execution-bearing:
  - raw arc material is not the primary blocker because ep1 still produces strong first-pass candidates
  - the stronger remaining parent debt is Stage3 input-packet layering mismatch:
    - ep-local hard constraints
    - future relationship / carryover pressure
    - threshold mismatch across validator / Director / runtime
    - patch feedback without canonical anchors
  - simple prompt slimming alone is not enough because the conflict is not only token count but mixed packet authority
- execution consequence:
  - keep this lane as the owner for one bounded structural tranche before the next rerun
  - execute in this order:
    1. `ep-local packet layering / gating`
    2. `threshold alignment`
    3. `canonical patch anchors`
    4. optional later prompt slimming only after the first three land
  - do not open a new queue lane for this design conclusion
  - do not push this ownership back down into the child partial-fix lane
  - the next rerun remains required, but now follows this bounded parent-lane tranche rather than preceding it

## 9. Acceptance Criteria

- highest-risk Stage3 seams no longer remain purely advisory by default
- success proof sinks are not emitted before blueprint persistence and commit succeed
- Stage3 `runtime_advisory` / `retry_directives` no longer default to blank when bounded advisory truth exists
- `PASS_WITH_FIX` success accounting no longer diverges from actual Stage3 success control flow
- Stage3 sink-alignment coverage no longer omits `pass_rate_monitor` / `director_selections` from the bounded final-attempt union
- Stage3 -> Stage4 handoff preserves more than prose-only semantics for key contract fields
- timeline and institution drift have stronger structured enforcement paths where Stage3 validator/compiler owns the contract
- ep-local packet layering no longer forces future-carryover pressure to compete with the episode-local hard packet by default
- Stage3 thresholding no longer depends on the unresolved `800 vs 1000 vs 90` split
- Stage3 patch feedback can carry canonical anchors instead of only freeform repair wording
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage3 validator regressions
- targeted Stage3 handoff contract regressions
- targeted Stage3 success-persistence ordering regressions
- targeted Stage3 advisory / retry sink parity regressions
- targeted `PASS_WITH_FIX` success-accounting regressions
- targeted Stage3 sink-alignment coverage regressions
- targeted later Stage3 ep-local packet-layering / gating regressions
- targeted later Stage3 threshold-alignment and canonical-anchor transport regressions
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
- do not mistake packet layering for raw arc-data slimming only; authority separation comes first
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

## 16. 2026-04-11 Current-Main Static Re-Audit Upgrade

Evidence basis:

- `docs/2026-04-11/stage23-current-main-static-parallel-survey.md`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/failure_analyzer.py`
- direct Stage3 guardrail / observability tests on current `main@2b7cb64f`

Current-main findings:

1. Stage3 success proof sinks still precede blueprint persistence / commit success.
2. Stage3 `runtime_advisory` / `retry_directives` remain blank by default on both success and reject persistence.
3. `PASS_WITH_FIX` remains success in Stage3 control flow but not in pass-rate accounting.

Execution consequence:

- keep this lane as the owner for one bounded truth-first tranche before the next rerun
- execute in this order:
  1. success proof sink ordering after committed persistence
  2. Stage3 advisory / retry sink normalization
  3. `PASS_WITH_FIX` success-accounting parity
- after that tranche lands, return to the already-promoted packet-layering / threshold / canonical-anchor tranche
- do not open a new queue lane for this re-audit; keep it inside this parent Stage3 SSOT

Confidence for this upgrade: `96%`

## 17. 2026-04-11 Live-Workspace Truth-First Landing Update

Evidence basis:

- `modules/core/stage3_orchestrator.py`
- `modules/core/failure_analyzer.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage3_orchestrator_handle_success_lane_c.py`
- `tests/test_failure_analyzer.py`

Live-workspace closures:

1. Stage3 success proof sinks now follow blueprint persistence and commit success.
2. Stage3 success/reject sinks now persist normalized `runtime_advisory` / `retry_directives`.
3. `PASS_WITH_FIX` now follows the success path and success accounting.
4. `FailureAnalyzer` now includes the bounded Stage3 sink-alignment coverage parity for `pass_rate_monitor` / `director_selections` in the final-attempt union and missing-bucket checks.

Execution consequence:

- keep this lane partial, but treat the previously reopened truth-first tranche as landed on the live workspace
- make the next operator action the fresh proof wave rather than another same-day Stage3 patch
- only after runtime evidence lands should this lane decide whether the older `packet layering -> threshold alignment -> canonical patch anchors` follow-up still needs activation
- keep this lane as the owner if the proof wave reopens Stage3 contract drift; otherwise use the proof result to decide demotion or closure bookkeeping without a new lane

## 18. 2026-04-12 EP3 Live-Run Follow-up Re-Audit

3-pass result:

1. The old Stage4 ep2 truth-pin / retry-lane family appears to have improved; the rerun no longer fronts with `대한그룹 -> 유성그룹` plus personal-asset drift.
2. The current blocker is upstream Stage3 truth:
   - `blueprint_0002` already consumes the TV-news / next-action cliffhanger that should have remained later progression.
   - `blueprint_0003` repeats legal-setup / asset-liquidation / father-study beats and reopens canonical institution drift (`대한그룹` -> `한강그룹`).
3. Stage4 is now acting mainly as the downstream verifier by correctly rejecting:
   - spring/winter timeline contradiction
   - replayed ep2 scene families in ep3

Execution consequence:

- keep the earlier truth-first and structural-hardening slices as landed
- treat the bounded parent-owned ep3 fail-only slice as landed across:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/three_phase_blueprint_runtime.py`
- record the landed parent-owned outcomes:
  - ep-boundary replay suppression now flows through `episode_progression_packet` truth
  - canonical institution proper-noun truth now merges manuscript, blueprint, and arc/current-episode sources inside Stage3 fact-lock coverage
  - replay-family and institution-truth violations now reroute to regenerate-only repair rather than cheap local repair
- make the next action the bounded proof wave / rerun rather than another same-day Stage3 parent patch
- keep the older `packet layering -> threshold alignment -> canonical patch anchors` follow-up deferred behind proof of the corrected ep2 -> ep3 seam

Confidence for this landing update: `97%`

## 19. 2026-04-12 First-Ensemble Visibility Follow-up

Evidence basis:

- `docs/2026-04-12/stage3-first-ensemble-visibility-live-run-compact-survey.md`
- `0_temp.txt`
- `projects/000_260412_a/logs/session_20260412_231516.log`
- `projects/000_260412_a/logs/session/ui_events.jsonl`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/blueprint_ensemble.py`

3-pass result:

1. The Stage3 ep1 quiet zone is not a hard runtime stall:
   - session-log evidence shows `ThreePhase runtime -> BP ensemble -> Director` progress
   - the first three Sonnet candidate calls start at `23:17:53` and return by `23:18:46`
2. The operator-facing seam is a visibility split:
   - `0_temp.txt` stops at the broad `제1화 Blueprint 생성 중...` surface
   - `ui_events.jsonl` records the initial `progress` plus one `heartbeat`
   - the richer later progress remains in session/root logging rather than the main console capture
3. The owner stays with this parent Stage3 contract lane:
   - the seam is about Stage3 operator observability during the first expensive ensemble wait
   - it does not justify a new queue family or a cross-stage promotion

Execution consequence:

- keep this as a bounded same-lane follow-up rather than a new remediation family
- do not let it outrank the current proof wave
- if the operator wants observability polish before the next larger refactor wave, implement only:
  - stronger first-ensemble main-console heartbeat surfacing
  - candidate-launch / candidate-return visibility
  - earlier elapsed-time reassurance for the quiet window
- do not widen this into generator retuning, Director retuning, or Stage4/UI redesign

Confidence for this follow-up: `97%`

## 20. 2026-04-13 Closure Residual Observability Landing Update

Evidence basis:

- `docs/2026-04-13/stage3-live-run-closure-and-residual-families-parallel-full-survey.md`
- `docs/2026-04-13/stage3-closure-residual-fail-only-promotion-survey.md`
- `modules/core/stage3_orchestrator.py`
- `tests/test_stage3_orchestrator.py`

Live-workspace closure:

1. Stage3 completion stats no longer mix unlabeled run-local success/failure counts with an unrelated cumulative pass-rate line.
2. The completion surface now prints:
   - current-run pass rate when the current run has attempts
   - cumulative generator pass rate only when it differs from the current-run rate
3. This closes the smaller same-day closure-survey observability drift without reopening the broader first-ensemble visibility lane.

Execution consequence:

- keep this lane partial, but treat the narrower closure-residual observability slice as landed on current `main`
- do not treat this as closure for the older first-ensemble heartbeat follow-up
- keep the next operator-directed action on the bounded proof wave rather than another same-day Stage3 parent patch
