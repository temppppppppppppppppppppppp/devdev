# 0_0-stage3-state-arbiter-envelope-bounded-remediation Execution SSOT

Date: 2026-04-14
Status: active (3-pass audited; long-horizon bounded execution lane; Tranche A/B landed on the current branch, Tranche C pending)
Canonical Path: `docs/2026-04-14/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `f58059fefd10ed3f41d7bacca3b908dd47ada418`
- Baseline Dirty Summary: `dirty: live 000_260412_a logs/db, 0_temp.txt, and untracked 2026-04-14 diagnostic notes already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `current branch now carries Tranche A EpisodeStateArbiter and Tranche B prompt-envelope budget realization`
Source Survey Docs:
- `docs/2026-04-14/stage3-fundamental-root-cause-bounded-survey.md`
- `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- `docs/2026-04-14/stage3-runtime-retry-structural-debt-survey.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Evidence Artifacts:
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/stage3_prompt_envelope.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/core/stage4_postselect_runtime.py`
Side-Effect Coverage: covered (Stage3 prompt assembly, retry/runtime, validator contract, observability sinks, roadmap queue state)
Confidence: `96%`

## 1. Intent

Realize the smallest bounded architecture lane that attacks the now-confirmed Stage3 root cause:

- no single pre-generation authoritative episode-state packet
- no unified total prompt-envelope budget
- too many Stage3-local interpretation surfaces

This lane exists because the operator explicitly prefers long-horizon root stabilization over another immediate rerun.

This lane is not:

- a `Polaris` rewrite
- a `DecisionKernel` migration
- a broad Stage4 redesign
- a vendor/model retune wave

## 2. Baseline Facts

1. Stage3 already has strong local contracts, but still lacks a pre-generation state arbiter.
2. Stage3 prompt budgeting currently covers retrieval slices, not the total model envelope.
3. Stage3 is functionally a mini pipeline:
   - input assembly
   - producer admission
   - validator plus Director boundary
   - retry coordination
4. Stage4 already has a structured `post_select_conflict` contract, which proves the system can express truth-pin style repair boundaries after generation.
5. The long-horizon opportunity is to move a bounded subset of that discipline earlier, before Stage3 generation.

## 3. Scope

Included:

- authoritative Stage3 input normalization
- Stage3 prompt-envelope budget unification
- bounded owner extraction for the Stage3 mini pipeline
- observability updates needed to keep the new packet and budget visible
- targeted doc and queue updates for this lane

Excluded:

- full cross-stage arbitration for every stage
- Stage4 writer-context redesign
- `Polaris` / `DecisionKernel` migration
- fresh rerun proof as part of this document
- unrelated Stage2 / Stage4 local fixes unless directly required by the new Stage3 packet contract

## 4. Pass 1. Inventory Summary

### Hotspots

- Stage3 input and sink owner:
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1667)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1749)
- Stage3 packet construction:
  - [blueprint_constraint_compiler.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py:44)
- Stage3 producer:
  - [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:743)
  - [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1278)
- Stage3 validator/director boundary:
  - [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:987)
  - [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:1442)
- Stage3 retry owner:
  - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1508)
  - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2489)

### Owner pressure facts

- `Stage3Orchestrator` direct methods: `51`
- `ThreePhaseBlueprintRuntime` direct methods: `37`

### Runtime-vs-survey split

This lane is architecture-first and bounded.

- it will touch runtime code
- it will not open a general codebase-wide refactor

## 5. Pass 2. Semantic Classification

### Class A. Pre-generation truth normalization

Goal:

- resolve source precedence once before generation

Primary surfaces:

- `stage3_orchestrator.py`
- `blueprint_constraint_compiler.py`

### Class B. Prompt-envelope control

Goal:

- measure and bound the total prompt seen by the Stage3 model

Primary surfaces:

- `stage3_orchestrator.py`
- `blueprint_ensemble.py`
- `context_advisor.py`

### Class C. Validation and retry boundary cleanup

Goal:

- reduce duplicated semantic interpretation between validator, runtime, and sink surfaces

Primary surfaces:

- `unified_blueprint_validator.py`
- `three_phase_blueprint_runtime.py`
- `stage3_orchestrator.py`

### Class D. Stage4 asymmetry reuse

Goal:

- reuse the existing `truth_pins` / `rewrite_required_reasons` idea in a bounded pre-generation form

Primary surfaces:

- `stage4_postselect_runtime.py`
- new Stage3 arbiter contract module

## 6. Side-Effect Map

- file writes / artifacts:
  - new bounded runtime modules for arbiter / envelope / coordinator extraction
  - updated execution docs, temp mirror, roadmap, queue-state
- DB / schema / transaction boundaries:
  - no schema migration is authorized in tranche 1
  - Stage3 sink payloads may gain new observability fields for `episode_state_packet` / envelope budget
- JSONL / log / audit sinks:
  - Stage3 runtime logs
  - session decision / stage attempt / director selection surfaces
- console / UI / operator output:
  - Stage3 heartbeat and success/failure summaries should expose the new packet and envelope signals
- rollback / recovery / retry:
  - retry policy must consume the new normalized packet rather than recomputing ad hoc carryover
- cache / global state:
  - Stage3 cached constraint block and semantic bundle paths are in scope
- bootstrap fallback / config-env mutation:
  - not applicable for tranche 1

## 7. Realization Architecture

### 7.1 New bounded substrate

Introduce one Stage3-first authoritative packet:

- `EpisodeStatePacket`

Recommended host:

- `modules/core/episode_state_arbiter.py`

Minimum contract:

- `source_precedence`
- `opening_truth`
- `protagonist_truth`
- `fact_lock_truth`
- `capital_truth`
- `progression_truth`
- `dropped_conflicts`
- `rewrite_required_reasons`

The packet should be built once and then consumed by:

- `BlueprintConstraintCompiler`
- `BlueprintEnsembleGenerator`
- `UnifiedBlueprintValidator`
- Stage3 observability summary

### 7.2 Prompt-envelope control plane

Introduce one bounded envelope surface:

- `Stage3PromptEnvelope`

Recommended host:

- `modules/domain/agents/stage3_prompt_envelope.py`

Responsibilities:

- one whole-envelope ledger across:
  - semantic retrieval
  - constraint bands
  - prev blueprint carryover
  - manuscript ending truth
  - archive appendix
  - work-focus advisories
- archive appendix demotion defaults
- operator-visible budget report

### 7.3 Boundary split targets

Bounded extractions only:

- `Stage3EnvelopeBuilder`
  - owned by Stage3 input assembly
- `Stage3ValidationBoundary`
  - owned by validator/director contract shaping
- `Stage3RetryCoordinator`
  - owned by retry/pass-with-fix routing

These are bounded ownership changes, not a cross-stage kernel rewrite.

## 8. Execution Tranches

1. `Tranche A — EpisodeStateArbiter`
   - status: `landed on the current branch`
   - build `EpisodeStatePacket`
   - define source precedence
   - expose `dropped_conflicts` and `rewrite_required_reasons`
   - thread packet into Stage3 constraint assembly and producer prompt assembly

2. `Tranche B — Unified Prompt Envelope Budget`
   - status: `landed on the current branch`
   - add whole-envelope ledger
   - demote default archive appendix surfaces
   - make operator observability show total chars by lane, not retrieval only

3. `Tranche C — Stage3 Boundary Split`
   - status: `next bounded realization tranche`
   - extract `Stage3EnvelopeBuilder`
   - extract `Stage3ValidationBoundary`
   - extract `Stage3RetryCoordinator`
   - keep behavior stable while reducing semantic duplication

4. `Tranche D — Post-tranche Proof And Fail-Only Stabilization`
   - only after A and B land
   - re-audit docs against live workspace
   - then consider a fresh operator-gated rerun

## 9. Acceptance Criteria

- a single authoritative `EpisodeStatePacket` exists and is the explicit Stage3 pre-generation truth surface
- Stage3 no longer injects the same opening/carryover truth through multiple unrelated prompt lanes without packet provenance
- Stage3 observability reports a whole-envelope budget, not retrieval-only budget
- default archive appendix behavior is bounded and demoted behind compact carryover truth
- Stage3 owner pressure does not increase
- no touched production function enters a new `180+ LOC` band
- targeted Stage3 contract and runtime tests pass

## 10. Verification Plan

- targeted compile:
  - `python -m py_compile` on new and touched Stage3 modules
- targeted tests:
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_blueprint_ensemble_generate_ensemble.py`
  - `tests/test_stage3_blueprint_state_precision_guardrail.py`
  - `tests/test_blueprint_patch_mode.py`
  - `tests/test_failure_analyzer.py`
- UTF-8 hygiene:
  - `python scripts/check_utf8_hygiene.py ...`
- queue/doc validation:
  - `python scripts/ops_validator.py --strict`

Fresh rerun validation is explicitly deferred to Tranche D.

## 11. Guardrails

- do not widen this lane into `Polaris` or `DecisionKernel`
- do not perform a big-bang Stage3/Stage4 rewrite
- do not open fresh rerun proof before Tranche A and Tranche B land and the governing docs are re-audited; the current workspace now satisfies the local landing precondition but has not started proof execution
- keep backward-compatible sink read paths where practical during migration
- prefer packet-first consolidation over more local lexical heuristics

## 12. Temp Queue Notes

- temp status: `in_progress (Tranche A/B landed on the current branch; Tranche C pending)`
- cleanup condition:
  - remove the temp mirror only after the long-horizon lane is realized or explicitly demoted
- roadmap dependency:
  - `docs/2026-04-01/active-temp-execution-roadmap.md`
- local controller note:
  - for the current local session, this lane represents the operator's debt-first long-horizon option and should be treated as a valid front alternative to fresh rerun proof

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least `95%` confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Notes

Pass 1:

- matched the execution scope to the bounded root-cause survey
- kept `Polaris` and global kernel work out of scope

Pass 2:

- checked that the proposed tranches line up with current live hotspots and not with stale prose alone
- verified that the largest missing substrate is pre-generation arbitration plus total-budget control

Pass 3:

- turned the root-cause findings into bounded implementation waves
- made rerun intentionally post-tranche rather than immediate
