# Stage3 Fundamental Root-Cause Bounded Survey

Date: 2026-04-14
Status: final (3-pass audited; code-first bounded survey)
Canonical Path: `docs/2026-04-14/stage3-fundamental-root-cause-bounded-survey.md`
Commit State:
- Baseline Commit: `f58059fefd10ed3f41d7bacca3b908dd47ada418`
- Baseline Dirty Summary: `dirty: live 000_260412_a logs/db, 0_temp.txt, and untracked 2026-04-14 diagnostic notes already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- `docs/2026-04-14/stage3-runtime-retry-structural-debt-survey.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-13/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md`
Companion Notes Reviewed But Not Treated As Authority:
- `docs/2026-04-14/pipeline-fundamental-verification-20q.md`
- `docs/2026-04-14/arbiter-state-normalization-layer-diagnostic.md`
Evidence Artifacts:
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/stage4_postselect_runtime.py`
Side-Effect Coverage: covered (Stage3 prompt assembly, retry/runtime, validation, S4 carryover contract, operator observability, queue docs)
Confidence: `96%`

## 1. Intent

Re-check the true Stage3 root cause from live code, not from prior survey prose alone.

This survey asks one bounded question:

- what is the highest-ROI long-horizon fix point if the operator prefers debt-first stabilization over another immediate rerun?

This is not a global architecture rewrite order.

## 2. Scope

Included:

- Stage3 input assembly and observability:
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/context_advisor.py`
- Stage3 state/constraint packet construction:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
- Stage3 producer contract surface:
  - `modules/domain/agents/blueprint_ensemble.py`
- Stage3 validator / director boundary:
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/director_ensemble.py`
- Stage3 retry/runtime owner:
  - `modules/domain/agents/three_phase_blueprint_runtime.py`
- Stage4 comparison surface for asymmetry check:
  - `modules/domain/agents/chief_writer.py`
  - `modules/domain/agents/chief_writer_context.py`
  - `modules/domain/agents/chief_writer_context_packets.py`
  - `modules/core/stage4_postselect_runtime.py`

Excluded:

- `Polaris` / `DecisionKernel` migration
- model or vendor swaps
- new narrative features
- broad Stage4 writer redesign
- fresh rerun proof itself

## 3. Pass 1. Inventory Summary

### 3.1 Stage3 does not consume one normalized truth surface

The current Stage3 path feeds overlapping authority through multiple parallel lanes:

1. `constraint_block` carries continuity, inherited state, fact-lock, capital, and episode progression:
   - [blueprint_constraint_compiler.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py:44)
   - [blueprint_constraint_compiler.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py:475)
   - [blueprint_constraint_compiler.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py:635)
   - [blueprint_constraint_compiler.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py:815)

2. producer prompt input separately carries four authority bands plus prev blueprint and manuscript archive tiers:
   - [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1278)
   - [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1902)

3. orchestrator adds another semantic lane with smart retrieval, work focus, world-state/style/fact-ledger advisories, and anchor summaries:
   - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1353)
   - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1578)
   - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1667)

Operational consequence:

- Stage3 does not fail only because upstream truth is unresolved.
- Stage3 also fails because the same episode truth is expressed in repeated, partially overlapping forms.

### 3.2 Budgeting is real for retrieval, weak for the total prompt envelope

Stage3 records a retrieval budget ledger for `semantic_ctx`:

- [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1628)
- [context_advisor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/context_advisor.py:165)

But the largest carryover lanes are outside that bounded view:

- previous manuscripts can still scale up to `context.max_context_chars` (`1,000,000` default): [constants.py](/c:/Users/wjjo/Desktop/글도비/modules/core/constants.py:142), [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1773)
- producer `prev_info` can still carry Tier 2 and Tier 4 archive surfaces up to `400,000` chars each:
  - [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1914)
  - [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1944)

Operational consequence:

- the system measures part of the Stage3 context budget
- but not the real whole-envelope budget seen by the model

### 3.3 Stage3 is already a mini pipeline, not a thin generator

Producer-side interpretation exists:

- opening-transition normalization and fail-closed omission handling: [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1142)
- tactical intrusion screening: [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1123)
- replay / episode-progression screening: [blueprint_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py:1778)

Validator-side interpretation exists:

- Python prevalidation: [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:1442)
- Director payload / repair contract shaping: [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:987)

Runtime-side interpretation exists:

- retry feedback / fix-pack shaping: [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:961)
- retry route and pass-with-fix routing: [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1508), [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2489)

Operational consequence:

- S3 is not a neutral structure pass
- it already interprets, rejects, reroutes, and teaches repair

### 3.4 Stage4 has an explicit post-select conflict contract that S3 lacks pre-generation

Stage4 post-select checks build structured conflict artifacts:

- conflict fingerprint: [stage4_postselect_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_postselect_runtime.py:165)
- conflict contract: [stage4_postselect_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_postselect_runtime.py:213)
- carryover into retry lane: [stage4_postselect_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_postselect_runtime.py:617)

ChiefWriter consumes that structured retry contract:

- [chief_writer.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/chief_writer.py:117)
- [chief_writer.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/chief_writer.py:1335)

Operational consequence:

- the system already knows how to express `conflict_contract` and `truth_pins`
- it just does so after generation, not before Stage3 generation

## 4. Pass 2. Adversarial Hypothesis Audit

### Hypothesis A. `S3 failure is mostly validator over-reject`

Verdict: rejected as the primary explanation.

Reason:

- producer admission already rejects before validator spend
- runtime retry policy already reshapes the next attempt
- validator strictness matters, but it is one layer inside a broader multi-interpretation path

### Hypothesis B. `S3 failure is mostly upstream conflict overload`

Verdict: partially accepted.

Reason:

- there is no single pre-generation arbiter resolving source precedence
- but the failure is not only inherited from upstream
- Stage3 multiplies the ambiguity by re-expressing the same authority across several prompt lanes

### Hypothesis C. `contract debt cleanup should have been sufficient`

Verdict: rejected as sufficient.

Reason:

- contract debt was real and worth fixing
- but current code still lacks one authoritative pre-generation state packet and one total envelope budget
- therefore contract cleanup alone cannot guarantee stable Stage3 behavior

### Hypothesis D. `S3 should be treated as non-authoritative, so its local design matters less`

Verdict: rejected.

Reason:

- S3 is not final truth authority, but it is still a decisive provisional authority surface
- if its provisional packet is noisy or duplicated, blueprint generation destabilizes before S4 can help

## 5. Pass 3. Root-Cause Judgment

Primary root-cause stack:

1. missing pre-generation `EpisodeStateArbiter`
   - no single episode-state packet establishes source precedence once before generation

2. ungoverned total Stage3 prompt envelope
   - the system budgets retrieval slices but not the actual combined model payload

3. duplicated interpretation surfaces inside Stage3
   - producer, validator, runtime, and sink-building each reinterpret partially overlapping truth

4. owner-surface and retry-structure debt as an amplifier
   - `Stage3Orchestrator` direct methods: `51`
   - `ThreePhaseBlueprintRuntime` direct methods: `37`
   - notable hotspot lengths:
     - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:1749)
     - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2489)

This means the most durable improvement point is not one more lexical local fix.

It is a bounded architecture lane:

- pre-generation state arbitration
- unified Stage3 envelope budgeting
- bounded Stage3 boundary split

## 6. Improvement Point Ranking

### P1. Pre-generation state arbiter

Create one authoritative `episode_state_packet` before Stage3 generation.

Minimum responsibilities:

- source precedence resolution
- dropped/suppressed conflict ledger
- final carryover packet for:
  - opening location/time
  - protagonist state
  - fact-lock
  - capital carryover
  - progression replay bans

### P2. Unified Stage3 prompt envelope budget

Count and gate the real full prompt envelope, not just retrieval slices.

Minimum responsibilities:

- one ledger covering:
  - semantic context
  - constraints
  - prev-info tiers
  - manuscript carryover appendix
  - work-focus advisories
- default demotion of archive appendix surfaces behind compact carryover packet truth

### P3. Bounded Stage3 boundary split

Separate the current Stage3 mini pipeline into bounded owners:

- `Stage3EnvelopeBuilder`
- `Stage3ValidationBoundary`
- `Stage3RetryCoordinator`

This is not a `Polaris` rewrite.

It is a bounded owner-pressure reduction so the arbiter and budget contracts stop drifting.

### P4. Pull selected Stage4 conflict semantics earlier

Do not wait until post-select to express every contradiction as a structured contract.

The bounded pre-S3 version should at least produce:

- `truth_pins`
- `source_precedence`
- `dropped_conflicts`
- `rewrite_required_reasons` when local repair is unsafe

## 7. Execution Consequence

This survey authorizes a long-horizon bounded execution lane.

Canonical execution SSOT:

- `docs/2026-04-14/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`

Temp mirror:

- `docs/temp/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`

Queue consequence:

- if the operator stays on long-horizon root-cause mode, this new lane should outrank fresh rerun proof for the local session
- rerun remains operator-gated and should not be auto-presented as the practical next step while this debt-first mode is active

## 8. Validation Basis

Static basis used in this survey:

- `git rev-parse HEAD`
- `git status --short`
- targeted code-path re-audit across the Stage3 input, producer, validator, runtime, and Stage4 post-select surfaces
- hotspot recount via AST inventory for:
  - `stage3_orchestrator.py`
  - `three_phase_blueprint_runtime.py`
  - `blueprint_ensemble.py`
  - `unified_blueprint_validator.py`
  - `chief_writer.py`

## 9. 3-Pass Audit Notes

Pass 1:

- re-established code-first scope without trusting prior prose
- checked both Stage3 and the relevant Stage4 asymmetry surface

Pass 2:

- challenged the easy explanations (`validator only`, `upstream only`, `contract debt only`)
- all three were insufficient under hostile reading

Pass 3:

- converted the survey into bounded operating consequences
- kept `Polaris` / `DecisionKernel` migration explicitly out of scope

Final bounded judgment:

- Stage3 contract debt cleanup was necessary
- but the long-horizon root fix point is `EpisodeStateArbiter + unified envelope budget + bounded boundary split`
