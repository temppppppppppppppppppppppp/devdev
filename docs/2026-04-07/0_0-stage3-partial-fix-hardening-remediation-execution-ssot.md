# 0_0 Stage3 Partial-Fix Hardening Remediation Execution SSOT

Date: 2026-04-07
Status: partially_realized (2026-04-07 merge-survey promotion clarified shared schema dependency and `partial_fix_eval` sink parity inside this lane; a first bounded tranche has now landed across Stage3 validator/runtime/advisory sinks by consuming shared `PatchTargetRecord` records, preserving a Stage3 `fix_pack-lite` contract, appending bounded patch guidance, and persisting `partial_fix_eval` into validate/advisory/meta surfaces, the later 2026-04-10 aborted `00_000` fresh run then promoted this lane from a proof-deferred child to a live runtime bug owner because Stage3 ep1 reaches `PASS_WITH_FIX` locally but the repair loop could discard re-audit `PASS < quality_gate` outcomes back into long reject/retry churn while patch drift still showed secondary preservation debt, the same-day bounded runtime hardening follow-up now preserves low-score `PASS` patch state for the next retry path, the later same-day structural survey plus layering-first adversarial audit then split the remaining owner surfaces more sharply, the first 2026-04-13 live-run retry-plateau follow-up now blocks low-yield inplace retry reopening after `PASS_WITH_FIX` exhaustion and repeated inplace score/signature plateau, a second same-day live-rerun follow-up is now also landed so `Director PASS < quality_gate` no longer reopens the same inplace lane on the next retry and Stage3 blueprint scoring now suppresses blind live-HUD `V46` current-state injection unless an explicit `blueprint_scoring_hud` is supplied, and a later same-day closure-residual follow-up now also accepts advisory-only `scenario_density` residuals as `PASS_WITH_WARNING` without reopening a low-yield local patch lane; the later completed 2026-04-13 rerun now proves that exact acceptance path on `ep4/ep5`, moving this child lane back to deferred verifier / locality debt rather than front-active blocker ownership)
Canonical Path: `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 139 tracked, 106 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Resume Drift Summary: `snapshot main is now authoritative; the bounded Stage3 partial-fix tranche remains landed across validator/runtime/advisory sinks, the later current-HEAD rerun and structural split still keep packet layering / threshold alignment / canonical patch anchors out of this child lane, the 2026-04-13 live-run retry-plateau follow-up continues to block low-yield inplace reopening after repeated `PASS_WITH_FIX unresolved` or repeated inplace score/signature plateau, the later same-day closure-residual follow-up now accepts advisory-only `scenario_density` residuals as `PASS_WITH_WARNING` without reopening a low-yield local patch lane, and the completed rerun now proves that child-lane acceptance path on live evidence so the next action returns to deferred verifier / locality debt rather than another same-family patch loop`
Source Survey Docs:
- `docs/2026-04-07/stage3-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
- `docs/2026-04-07/partial-fix-terminal1-eval-harness-survey.md`
- `docs/2026-04-07/partial-fix-terminal2-shared-patch-address-schema-survey.md`
- `docs/2026-04-07/partial-fix-hardening-parallel-merge-survey.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-10/00_000-stage3-fresh-run-abort-post-run-merge-audit.md`
- `docs/2026-04-10/stage3-blueprint-first-pass-structural-survey.md`
- `docs/2026-04-10/stage3-blueprint-layering-first-adversarial-audit.md`
- `docs/2026-04-13/stage3-live-run-retry-plateau-parallel-full-survey.md`
- `docs/2026-04-13/stage3-live-run-quality-gate-patch-reopen-parallel-full-survey.md`
- `docs/2026-04-13/stage3-live-run-quality-gate-patch-reopen-3pass-audit.md`
- `docs/2026-04-13/stage3-post-run-global-residual-promotion-survey.md`
- `docs/2026-04-13/stage3-live-run-closure-and-residual-families-parallel-full-survey.md`
- `docs/2026-04-13/stage3-closure-residual-fail-only-promotion-survey.md`
Evidence Artifacts:
- `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`
- `0_temp.txt`
- `projects/00_000/logs/session_20260410_143423.log`
- `projects/00_000/logs/session_20260410_160214.log`
- `projects/00_000/logs/runtime_audit_summary.json`
Side-Effect Coverage: covered
Parent Lane:
- `0_0-stage3-contract-tightening-remediation`

## 1. Intent

Create a bounded pending Stage3 lane that upgrades blueprint partial-fix behavior from feedback-string-driven patching toward target-aware, verifier-backed partial repair.

This promotion incorporates the 2026-04-07 merge-survey verdict: no new queue rank is needed, but this lane must explicitly consume the shared `PatchTargetRecord` dependency and emit the Stage3 side of bounded `partial_fix_eval` sink parity once fix-pack-lite and verifier tranches land.

This lane exists because current Stage3 behavior is clear but still coarse:

- `fix_scope` governs whether local patch is allowed
- `re_slice_instruction` is preferred over generic `feedback`
- `_inplace_patch_blueprint(...)` still receives only one feedback string and returns a whole blueprint object

That means Stage3 already supports bounded partial-fix loops, but it still lacks:

- Stage4-style explicit target metadata
- stable field or scene addressing
- targeted post-patch verification before full re-audit

## 2. Baseline Facts

- Stage3 is dict-first at the contract level, especially in validation and success payloads.
- `PASS_WITH_FIX` is first-class in Stage3 retry/runtime flow.
- Current Stage3 local patch entry uses:
  - `fix_scope`
  - `re_slice_instruction`
  - `feedback`
- `_inplace_patch_blueprint(...)` patches the blueprint as a whole object, not as a target-addressed scene/path operation.
- Current Stage3 validator/runtime path can now preserve a bounded `fix_pack-lite` carrying structured `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, and `target_kind` when the validator emits it.
- Current Stage3 runtime can now persist a bounded `partial_fix_eval` sink plus compact fix-pack metadata through `phases.validate`, Stage3 advisory warnings, and saved `_stage3_meta`; a dedicated verifier/exhaustion tranche still remains open.

## 3. Scope

Included:

- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- bounded Stage3 validator output and blueprint patch-loop hardening
- bounded scene/path-target metadata for Stage3-local repair
- bounded Stage3 attempt metadata for `partial_fix_eval` sink parity

Excluded:

- broad Stage3 contract tightening or binding redesign
- broad Stage3 prompt retuning
- ep-local packet layering / gating
- threshold alignment across validator / Director / runtime
- canonical patch-anchor transport
- new queue rank creation
- Stage4-style before/after excerpt trace
- Stage4 fix-pack redesign
- Stage2 redesign
- fresh canary execution in this documentation turn

## 4. Pass 1. Inventory Summary

Primary Stage3 partial-fix surfaces:

1. validator result payload
2. runtime fix-loop selection on `fix_scope`
3. `_inplace_patch_blueprint(...)`

Primary debt inventory for this wave:

1. Stage3 partial-fix is still driven by one repair string rather than structured patch targets
2. blueprint patching lacks a stable scene/path address contract
3. post-patch acceptance still depends on broad re-audit rather than a bounded target verifier
4. repeated local patch attempts have weaker locality guarantees than Stage4
5. the lane still lacks one explicit shared schema dependency and one bounded `partial_fix_eval` sink shape

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is activated

- shared `PatchTargetRecord` dependency consumed by Stage3 fix-pack-lite
- Stage3 `fix_pack-lite` contract for validator/runtime handoff
- scene/path-aware blueprint patch targeting
- bounded Stage3 post-patch verifier plus `partial_fix_eval` sink emission before full re-audit

### Class B. Residual but related

- richer Stage3 patch traces and retry summaries
- better repeated-attempt exhaustion heuristics
- stronger preservation of unchanged scene sections during patch

### Class C. Explicitly deferred outside this lane

- broad Stage3 contract-tightening realization
- Stage3 prompt redesign
- Stage4 repair grammar work
- Stage2 packet redesign

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage3 blueprint outputs may preserve more stable untouched sections during partial-fix rounds

- DB / schema / transaction boundaries:
  - existing Stage3 attempt metadata may gain a bounded `partial_fix_eval` object; no new table/column is allowed in this lane

- JSONL / log / audit sinks:
  - Stage3 retry metadata may become richer, more target-specific, and more measurable

- console / UI / operator output:
  - Stage3 patch target, `target_kind`, and fallback reasons may become more explicit without pretending to expose Stage4-style text excerpts

- rollback / recovery / retry:
  - Stage3 local patch retries should become more selective and earlier-exiting when locality is not credible

- cache / global state:
  - not primary in this lane

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### Tranche 0. Shared PatchTargetRecord Dependency

Goal:

- consume one shared target-record contract without opening a new Stage3-specific dialect

Realization direction:

- require Stage3 `patch_targets` to consume the shared `PatchTargetRecord` dependency anchored in Stage4 rank `9`
- treat `scene_id` and `field_path` as the Stage3-relevant address primitives
- forbid Stage4-only `text_anchor` requirements from becoming mandatory in this dict-first lane

### Tranche 1. Stage3 Fix-Pack-Lite Contract

Goal:

- stop passing only one undifferentiated repair string from validator to patch loop

Realization direction:

- extend Stage3 validator/runtime handoff with bounded metadata:
  - `patch_targets`
  - `must_fix`
  - `do_not_regress`
  - `success_condition`
  - `target_kind`
- require `patch_targets` to be structured records, not free strings

### Tranche 2. Scene / Path-Aware Blueprint Patch

Goal:

- move Stage3 from whole-object "fix this somehow" patching toward target-aware blueprint repair

Realization direction:

- allow scene-key or field-path targets for blueprint partial-fix
- use `scene_block`, `field_value`, and `state_constraint` as the Stage3-local `target_kind` family
- preserve untouched scene sections and non-target paths by default

### Tranche 3. Targeted Post-Patch Verification and Eval Sink

Goal:

- verify whether the local Stage3 issue was actually fixed before the next broad review and persist one bounded measurement sink

Realization direction:

- add a bounded verifier for target scene/path changes
- check:
  - issue disappearance
  - preservation of non-target sections
  - minimal local-change realism
- emit one bounded `partial_fix_eval` sink object carrying:
  - `patch_round`
  - `patch_target_id`
  - `target_kind`
  - `must_fix_resolved`
  - `do_not_regress_held`
  - `success_condition_met`
  - `fallback_reason`
- keep Python on fact collection only; the verifier booleans come from the LLM-side verifier and are only persisted by runtime code

### Tranche 4. Retry Exhaustion Hardening

Goal:

- reduce repeated ineffective Stage3 local patch attempts

Realization direction:

- detect repeated failures on the same scene/path target

### 2026-04-13 Live Retry Plateau Update

- `three_phase_blueprint_runtime.py` now tracks Stage3 reject origin, reject signature, repeated reject-score/signature streaks, inplace reject streaks, and advisory-only reject streaks inside `_ThreePhaseRetryState`.
- `_finalize_pass_with_fix_failure(...)` now labels exhausted patch loops as `pass_with_fix_unresolved`, so the next retry no longer reopens the same cheap inplace lane by default.
- `_run_phase2_generation(...)` now blocks inplace patch reopening when the current retry state shows:
  - `PASS_WITH_FIX` exhaustion on the immediately preceding reject
  - repeated inplace score plateau
  - repeated inplace issue/signature plateau
  - repeated advisory-only residual plateau
- this follow-up is intentionally fail-only:
  - it does not widen Stage3 packet layering
  - it does not retune broad Stage3 prompting
  - it aims only to stop the low-yield retry loop visible in the 2026-04-12/13 live run logs
- later same-day live-rerun follow-up:
  - `three_phase_blueprint_runtime.py` now marks `Director PASS < quality_gate` downgrades with `reject_origin=quality_gate_reject`
  - the same retry-plateau gate now blocks the next retry from reopening `inplace` on that quality-gate family and instead routes back to `full_ensemble`
  - `scoring_validator.py` now suppresses blind `martial_hud`/`actual_truth` V46 injection during `mode=BLUEPRINT` scoring unless an explicit `blueprint_scoring_hud` is supplied
- escalate earlier to broader regenerate flow when locality has collapsed
- preserve enough target identity in retry metadata for later shared aggregation
- do not fabricate Stage4-style text before/after excerpts in this dict-first lane

## 8. Execution Tranches

1. shared `PatchTargetRecord` dependency consumed by Stage3
2. Stage3 validator/runtime fix-pack-lite contract
3. Stage3 scene/path-aware blueprint patching
4. Stage3 targeted post-patch verifier plus `partial_fix_eval` sink
5. Stage3 retry exhaustion and trace hardening
6. bounded regression coverage
7. later canary proof only after explicit reactivation

## 8A. Implementation Update (2026-04-07)

Landed bounded tranche:

- `unified_blueprint_validator.py` now normalizes and preserves Stage3 `fix_pack-lite` payloads with shared `PatchTargetRecord` records when Director compare/single-result payloads provide them.
- `three_phase_blueprint_runtime.py` now carries that Stage3 fix-pack contract into the in-place blueprint patch loop, appends bounded patch-target guidance to the repair feedback, preserves `phases.validate.fix_pack`, and emits `partial_fix_eval` from the re-audit-backed patch outcome.
- `stage3_orchestrator.py` now preserves compact `fix_pack` plus `partial_fix_eval` data into Stage3 advisory warnings and saved `_stage3_meta`, so later readback and downstream consumers no longer lose the Stage3-side partial-fix sink.

Residual deferred inside this lane:

- dedicated target verifier hardening beyond re-audit-backed sink emission
- retry exhaustion logic keyed by repeated `patch_target_id`
- fresh canary/live proof

## 8B. Runtime Revalidation Update (2026-04-10)

- the aborted `00_000` fresh run is the first current-HEAD proof artifact in this lane that actually reaches Stage3 ep1
- the new live finding is action-bearing:
  - Stage3 enters `PASS_WITH_FIX`
  - local patching runs
  - re-audit can return `PASS`
  - if that `PASS` stays below the quality gate, the runtime logs `[TF-35]` and falls back into the broader reject/retry path instead of preserving the improved patched state cleanly for the next attempt
- the same run also shows secondary patch-preservation debt:
  - one patch path drops `scene_breakdown`
  - another local patch expands by `+52.8%`, which is too large to treat as comfortably local
- execution consequence:
  - this lane is no longer only "fresh proof deferred"
  - it now owns the immediate bounded fail-only runtime repair before the next merged proof wave or Stage3-reaching rerun

## 8C. Implementation Update (2026-04-10 same-day)

Landed bounded runtime follow-up:

- `three_phase_blueprint_runtime.py` now preserves patched blueprint state and re-audit payloads when Stage3 patch re-audit returns `PASS` below the quality gate
- the same runtime path now stamps `verdict` / `decision` back into the re-audit payload so downstream retry/finalizer bookkeeping does not lose the last re-audit meaning
- `_finalize_pass_with_fix_failure(...)` now adopts the latest patched blueprint for retry carry-forward on `PASS`, `PASS_WITH_FIX`, and `PASS_WITH_WARNING`, and it uses the re-audit score rather than the stale pre-patch score when logging and recording the reject state

Residual deferred inside this lane after the follow-up:

- deeper scene/path preservation hardening when local patch drift is too large
- dedicated verifier logic beyond broad re-audit-backed measurement
- retry-exhaustion logic keyed tightly to repeated `patch_target_id`
- fresh rerun proof on current HEAD

## 8D. Parent-Lane Structural Split Update (2026-04-10 same-day)

- the later current-HEAD rerun plus `docs/2026-04-10/stage3-blueprint-first-pass-structural-survey.md` and `docs/2026-04-10/stage3-blueprint-layering-first-adversarial-audit.md` now clarify that this child lane is not the correct owner for the whole remaining Stage3 design debt
- the stronger split is now:
  - this child lane keeps:
    - verifier hardening
    - retry-exhaustion keyed by repeated targets
    - local patch-preservation / locality hardening
  - the parent `0_0-stage3-contract-tightening-remediation` lane now keeps:
    - ep-local packet layering / gating
    - threshold alignment
    - canonical patch anchors
- execution consequence:
  - do not widen this child lane into packet-layering work
  - keep the current same-day runtime repair as landed
  - treat the next code-first structural step as parent-lane work, with this child lane returning afterward for narrower verifier/locality follow-up if still needed

## 8E. Closure Residual Fail-Only Update (2026-04-13 same-day)

Evidence basis:

- `docs/2026-04-13/stage3-live-run-closure-and-residual-families-parallel-full-survey.md`
- `docs/2026-04-13/stage3-closure-residual-fail-only-promotion-survey.md`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `tests/test_blueprint_patch_mode.py`

Live-workspace closure:

1. Advisory-only `scenario_density` residuals no longer reopen the low-yield Stage3 local patch lane once the verdict already sits in `PASS_WITH_FIX`.
2. The runtime now promotes that exact residual shape to bounded `PASS_WITH_WARNING` acceptance instead.
3. The validate sink now records explicit acceptance metadata for that bounded soft landing.

Execution consequence:

- keep this child lane partial, but treat the closure-residual fail-only slice as landed on current `main`
- do not widen this same-day change into broader advisory-family policy
- keep the next operator-directed action on the bounded post-proof parent slice rather than another same-family patch cycle

## 8F. Post-Run Proof Update (2026-04-13 same-day)

Evidence basis:

- `docs/2026-04-13/stage3-post-run-global-residual-promotion-survey.md`
- `0_temp.txt`
- `projects/000_260412_a/logs/session_20260413_113134.log`

Live-workspace proof result:

1. the completed rerun proves the child-lane `scenario_density` acceptance path on `ep4` and `ep5`
2. the rerun still reaches `ep6` closure and exits cleanly, so this child lane is no longer the front Stage3 blocker for rerun completion
3. the new Stage3 front residual is parent-owned terminal-quality-gate coherence on `ep6`, not another child-lane advisory reopening

Execution consequence:

- keep this child lane partial, but treat the advisory-only `scenario_density` slice as both landed and live-proven
- do not front-reactivate this lane for the same advisory family
- keep the remaining child debt bounded to verifier / retry-exhaustion / locality preservation
- let the parent `0_0-stage3-contract-tightening-remediation` lane own the new `ep6` post-proof quality-gate coherence follow-up

## 9. Acceptance Criteria

- Stage3 no longer relies on one repair string alone for partial-fix routing
- Stage3 `patch_targets` consume the shared record shape with `scene_id` / `field_path` semantics
- Stage3 can name bounded scene/path targets for blueprint partial repair
- Stage3 verifies local partial-fix success before broad re-audit whenever credible
- Stage3 emits a bounded `partial_fix_eval` sink object when verifier-backed local patching runs
- untouched blueprint regions are preserved more consistently
- Stage3 does not promise fake Stage4-style text excerpt traces
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage3 validator/runtime regressions
- targeted blueprint patch regressions
- targeted Stage3 attempt-metadata / `partial_fix_eval` sink regressions
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not activate this lane before explicit operator decision
- do not let this lane outrank the pending Stage3 contract-tightening lane without deliberate reprioritization
- do not widen this lane into broad Stage3 prompt retuning
- do not absorb parent-lane packet layering / threshold alignment / canonical anchor work into this child lane
- do not widen this lane into Stage4 or Stage2 redesign
- do not fabricate Stage4-style before/after excerpt trace obligations from inside this lane
- do not run canary/live proof from this lane until explicit operator approval

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - keep the temp mirror as a promoted pending queue item until explicit closure, replacement, or merge into a later active Stage3 wave
- roadmap dependency:
  - this item stays below the current active Stage4 front in the global queue, and inside the Stage3 family its same-day bounded runtime hardening is now landed while closure still waits on a fresh rerun

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a bounded pending Stage3 lane, not a front-active implementation lane
- separated Stage3 partial-fix hardening from the broader Stage3 contract-tightening lane
- absorbed the merge-survey result by expanding the existing Stage3 lane rather than inventing a new queue rank

Pass 2, evidence and consistency:

- anchored claims to live validator/runtime/generator patch paths
- kept the document consistent with the 2026-04-07 Stage3 bounded survey
- aligned the execution scope with the 2026-04-07 eval-harness and shared-schema survey conclusions

Pass 3, execution and readability:

- made the path explicit: shared schema -> fix-pack-lite -> scene/path targeting -> verifier/sink -> retry hardening
- kept activation subordinate to current Stage4 and pending Stage3 queue order

Confidence: `97%`
