# 0_0 Stage2 Partial-Fix Hardening Remediation Execution SSOT

Date: 2026-04-07
Status: partially_realized (2026-04-07 merge-survey promotion clarified shared schema dependency and `partial_fix_eval` sink parity inside this lane; a first bounded Stage2 tranche has now landed across the finalizer, a shared Stage2 partial-fix helper module, and the Arc in-place patch surface by normalizing `fix_pack-lite`, forwarding shared `PatchTargetRecord` payloads into Stage2 patch prompts, and persisting `partial_fix_eval` plus compact fix-pack metadata into Stage2 attempt/director sinks while broader verifier hardening and fresh proof remain deferred)
Canonical Path: `docs/2026-04-07/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 139 tracked, 106 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `2026-04-07 bounded Stage2 partial-fix tranche landed across `stage2_partial_fix_contract.py`, `stage2_finalizer.py`, and `four_phase_arc_generator.py`: Stage2 now normalizes a bounded `fix_pack-lite` contract with shared `PatchTargetRecord` records, the PASS_WITH_FIX loop forwards that contract into Arc in-place patch prompts, and Stage2 attempt/director telemetry now preserves compact `fix_pack` plus `partial_fix_eval` payloads with focused validation closed`
Source Survey Docs:
- `docs/2026-04-07/stage2-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
- `docs/2026-04-07/partial-fix-terminal1-eval-harness-survey.md`
- `docs/2026-04-07/partial-fix-terminal2-shared-patch-address-schema-survey.md`
- `docs/2026-04-07/partial-fix-hardening-parallel-merge-survey.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`
Side-Effect Coverage: covered
Parent Lane:
- `0_0-stage2-contract-normalization-remediation`

## 1. Intent

Create a bounded pending Stage2 lane for improving partial-fix precision without reopening the broader Stage2 normalization lane.

This promotion incorporates the 2026-04-07 merge-survey verdict: no new queue rank is needed, but this lane must explicitly consume the shared `PatchTargetRecord` dependency and emit the Stage2 side of bounded `partial_fix_eval` sink parity once fix-pack-lite and verifier tranches land.

This lane exists because current Stage2 behavior is workable but coarse:

- `fix_scope` decides whether local patch is allowed
- `re_slice_instruction` is the real patch input
- `_inplace_patch_arc(...)` receives one feedback string and returns a patched arc object

That means Stage2 still lacks:

- explicit patch target metadata
- stable section/field addressing
- targeted post-patch verification before broad re-audit
- a disciplined bridge between local exact fix and broader partial/full regenerate paths

## 2. Baseline Facts

- Stage2 is dict-first at the authority level, especially in finalizer payloads and patch-loop state.
- Current `PASS_WITH_FIX` entry is explicit and bounded by `fix_scope`.
- `partial` or `full` already block local patch and delegate to broader retry flow.
- `_inplace_patch_arc(...)` still patches the Arc JSON object as a whole, but it can now consume bounded Stage2 `fix_pack-lite` guidance instead of relying on one free-form repair string alone.
- Current Stage2 finalizer now normalizes shared `PatchTargetRecord` payloads into a bounded `fix_pack-lite` contract before invoking local Arc patching.
- Current runtime now persists compact `fix_pack` and `partial_fix_eval` payloads into Stage2 attempt metadata and director selections when verifier-backed local patching runs.

## 3. Scope

Included:

- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/four_phase_arc_generator.py`
- bounded Stage2-local patch routing and patch-loop hardening
- bounded section/field-target metadata for Stage2 partial-fix
- bounded Stage2 attempt metadata for `partial_fix_eval` sink parity

Excluded:

- broader Stage2 mission authority normalization
- new queue rank creation
- Stage4-style before/after excerpt trace
- broader Stage2 packet alias or dead-field cleanup
- Stage3 or Stage4 redesign
- fresh canary execution in this documentation turn

## 4. Pass 1. Inventory Summary

Primary Stage2 partial-fix surfaces:

1. finalizer `PASS_WITH_FIX` loop
2. `_inplace_patch_arc(...)`
3. patch-guard / re-audit context appended around Stage2 retries

Primary debt inventory for this wave:

1. Stage2 partial-fix still depends on one repair string rather than target metadata
2. Arc patching lacks stable section/field addresses
3. post-patch success is inferred mainly through broad re-audit
4. Stage2 cannot yet choose confidently between exact local fix, bounded section patch, and broader regenerate using one explicit contract family
5. the lane still lacks one explicit shared schema dependency and one bounded `partial_fix_eval` sink shape

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is activated

- shared `PatchTargetRecord` dependency consumed by Stage2 fix-pack-lite
- Stage2 fix-pack-lite contract for finalizer -> patch-generator handoff
- stable section/field targeting for Arc partial repair
- bounded Stage2 post-patch verifier plus `partial_fix_eval` sink emission before broad re-audit

### Class B. Residual but related

- richer patch traces and operator retry context
- better repeated-attempt escalation when the same section keeps failing
- stronger preservation of untouched Arc fields during local patch

### Class C. Explicitly deferred outside this lane

- broader Stage2 mission/authority normalization
- Stage3 redesign
- Stage4 repair-contract work
- broad Stage2 architecture rewrite

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage2 arc artifacts may preserve untouched sections more reliably during partial-fix retries

- DB / schema / transaction boundaries:
  - existing Stage2 attempt metadata may gain a bounded `partial_fix_eval` object; no new table/column is allowed in this lane

- JSONL / log / audit sinks:
  - Stage2 patch traces and retry summaries may become more target-specific and more measurable

- console / UI / operator output:
  - Stage2 local-patch target, `target_kind`, and fallback reasons may become more explicit without pretending to expose Stage4-style text excerpts

- rollback / recovery / retry:
  - Stage2 should exit futile local patch loops earlier when target locality is weak

- cache / global state:
  - not primary in this lane

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### Tranche 0. Shared PatchTargetRecord Dependency

Goal:

- consume one shared target-record contract without opening a new Stage2-specific dialect

Realization direction:

- require Stage2 `patch_targets` to consume the shared `PatchTargetRecord` dependency anchored in Stage4 rank `9`
- treat `field_path` plus bounded section identifiers as the Stage2-relevant address primitives
- forbid Stage4-only `text_anchor` requirements from becoming mandatory in this dict-first lane

### Tranche 1. Stage2 Fix-Pack-Lite Contract

Goal:

- stop handing only one instruction string to Arc partial-fix machinery

Realization direction:

- add bounded metadata for:
  - `patch_targets`
  - `must_fix`
  - `do_not_regress`
  - `success_condition`
  - `target_kind`
- require `patch_targets` to be structured records, not free strings

### Tranche 2. Section / Field-Aware Arc Patch

Goal:

- move Stage2 from whole-Arc "patch somehow" behavior toward bounded section/field targeting

Realization direction:

- introduce stable target families for:
  - tactical section
  - state-constraint section
  - bounded field path
- use `tactical_section`, `state_constraint`, and `field_value` as the Stage2-local `target_kind` family
- preserve untouched Arc regions by default

### Tranche 3. Targeted Post-Patch Verification and Eval Sink

Goal:

- verify that the local Stage2 issue is resolved before the next broad re-audit and persist one bounded measurement sink

Realization direction:

- add a bounded verifier for targeted section/field changes
- check:
  - requested issue resolution
  - preservation of untouched authority fields
  - minimum locality realism
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

- reduce repeated ineffective Stage2 local patch attempts

Realization direction:

- escalate earlier when the same target keeps failing
- preserve better patch-history evidence in re-audit context
- preserve enough target identity in retry metadata for later shared aggregation
- do not fabricate Stage4-style text before/after excerpts in this dict-first lane

## 8. Execution Tranches

1. shared `PatchTargetRecord` dependency consumed by Stage2
2. Stage2 finalizer/generator fix-pack-lite contract
3. Stage2 section/field-aware Arc patching
4. Stage2 targeted post-patch verifier plus `partial_fix_eval` sink
5. Stage2 retry exhaustion and trace hardening
6. bounded regression coverage
7. later runtime proof only after explicit reactivation

## 9. Acceptance Criteria

- Stage2 no longer relies on one repair string alone for local patch routing
- Stage2 `patch_targets` consume the shared record shape with bounded section / `field_path` semantics
- Stage2 can name bounded section/field targets for Arc partial repair
- Stage2 verifies local partial-fix success before broad re-audit whenever credible
- Stage2 emits a bounded `partial_fix_eval` sink object when verifier-backed local patching runs
- untouched Arc regions are preserved more consistently during local repair
- Stage2 does not promise fake Stage4-style text excerpt traces
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage2 finalizer regressions
- targeted Arc patch regressions
- targeted Stage2 attempt-metadata / `partial_fix_eval` sink regressions
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not activate this lane before explicit operator decision
- do not let this lane outrank the current Stage4 front or the broader residual Stage2 normalization lane without deliberate reprioritization
- do not widen this lane into broad Stage2 mission/authority redesign
- do not widen this lane into Stage3 or Stage4 redesign
- do not fabricate Stage4-style before/after excerpt trace obligations from inside this lane
- do not run canary/live proof from this lane until explicit operator approval

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - keep the temp mirror as a promoted pending queue item until explicit closure, replacement, or merge into a later active Stage2 wave
- roadmap dependency:
  - this item stays below the active Stage4 front, below the broader residual Stage2 lane, and above soak-only references

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a bounded pending Stage2 lane, not a front-active implementation lane
- separated partial-fix hardening from the broader Stage2 normalization lane
- absorbed the merge-survey result by expanding the existing Stage2 lane rather than inventing a new queue rank

Pass 2, evidence and consistency:

- anchored claims to live finalizer and Arc patch-generator code
- kept the document consistent with the 2026-04-07 Stage2 bounded survey
- aligned the execution scope with the 2026-04-07 eval-harness and shared-schema survey conclusions

Pass 3, execution and readability:

- made the path explicit: shared schema -> fix-pack-lite -> section/field targeting -> verifier/sink -> retry hardening
- kept activation subordinate to the current active queue order

Confidence: `97%`

## 15. 2026-04-07 Implementation Update

- added `modules/core/stage2_partial_fix_contract.py` as the bounded Stage2 helper owning `fix_pack-lite` normalization, Stage2 partial-fix guidance rendering, and `partial_fix_eval` payload construction over the shared `PatchTargetRecord` contract
- `stage2_finalizer.py` now normalizes Stage2 fix-pack-lite payloads during PASS_WITH_FIX retry loops, forwards them into `_inplace_patch_arc(...)`, preserves compact `fix_pack` plus `partial_fix_eval` in the re-audit loop state, and writes the same payloads into both `stage_attempts` advisory flags and `director_selections.advisory_warnings`
- `four_phase_arc_generator.py` now appends bounded Stage2 fix-pack guidance to the in-place Arc patch prompt so section/field-aware targets reach the local patch operator without widening into a new Stage2 architecture wave
- targeted validation closed on `tests/test_stage2_finalizer.py`, `tests/test_arc_patch_mode.py`, and `tests/test_inplace_reliability.py`; fresh canary/live proof remains deferred by operator choice
