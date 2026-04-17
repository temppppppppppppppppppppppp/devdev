# Stage3 ep9 Generator Long-Term Direction Adversarial 3-Pass Audit

Date: 2026-04-17
Status: final
Canonical Path: `docs/2026-04-17/stage3-ep9-generator-longterm-direction-adversarial-3pass-audit.md`
Temp Mirror Path: `not-applicable`

Commit State:
- Baseline Commit: `ce0f3b47b465fcd67796f75e0497a5f7c7b2424f`
- Baseline Dirty Summary: `dirty: 8 tracked, 5 untracked; hotspots: blueprint_constraint_compiler.py, blueprint_ensemble.py, three_phase_blueprint_runtime.py, stage3_retry_coordinator.py, canary artifacts/docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Scope
- Question under audit: whether the proposed direction of `short-term rescue abandoned -> Stage3 generator structural fix` is the correct next owner for the ep9 failure lane.
- Included surfaces:
  - Stage3 prompt/constraint shaping
  - Stage3 ensemble candidate generation and candidate screening
  - Stage3 retry feedback / retry plateau handling
  - Stage3 replay / stop-line / structural prevalidation contracts
  - latest bounded canary evidence for `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1`
- Excluded surfaces:
  - Stage4 runtime
  - broader Stage234 queue realization
  - new implementation or live rerun authorization

## Evidence Basis
- Runtime evidence:
  - `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1/logs/stage3_canary_summary.json`
  - `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1/logs/session_20260417_144754.log`
  - `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1/logs/session/llm_io.jsonl`
  - `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1/plans/blueprints/blueprint_0008.txt`
- Code evidence:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/three_phase_blueprint_runtime.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/stage3_retry_coordinator.py`
- Governance evidence:
  - `docs/implementation/system-order-init-harness.md`
  - `docs/implementation/system-full-survey-execution-harness.md`
  - `docs/implementation/document-3pass-audit-harness.md`
  - `docs/implementation/commit-state-minimal-contract.md`

## Executive Verdict
The long-term direction is broadly correct, but only in a narrowed form.

- Correct core diagnosis:
  - the remaining owner is no longer `ep9 authority missing`
  - the remaining owner is `Stage3 generator collapse into replay basin or thin-structure basin`
- Correct long-term move:
  - fix generator structure before any new rerun
- Required narrowing:
  - prioritize `ensemble surface diversification` and `retry basin classification`
  - treat `validator refinement` as a later precision pass, not the first fix
  - do not let the compiler become a story-authoring engine via hardcoded scene-slot mandates

Recommended verdict label: `qualified-yes`.

## Findings
- High: the current failure lane is generator-side, not authority-side. The prompt now carries replay guard, surface guidance, and reserved-beat guidance, but ep9 still fails after 10 retries with no `blueprint_0009`. `blueprint_db_count` remains `8`. Evidence: `stage3_canary_summary.json`, `blueprint_constraint_compiler.py:1241`, `blueprint_constraint_compiler.py:1291`, `blueprint_ensemble.py:1450`.
- High: the ensemble currently diversifies style, not surface. Strategy spread is `action/emotion/dialogue`, but there is no mechanism forcing disjoint location/person/procedural ownership across workers. Evidence: `blueprint_ensemble.py:52`, `blueprint_ensemble.py:507`, `blueprint_ensemble.py:604`.
- High: the replay gate is currently coarse enough that a valid continuation lane can be squeezed if it reuses the same venue and overlapping cast across two or more scenes. The matcher keys primarily on location variants plus character overlap. Evidence: `unified_blueprint_validator.py:2196`.
- Medium: retry infrastructure already tracks plateau metadata, but it is tuned for validation/inplace/advisory plateaus, not `candidate_disqualified basin` repetition. Evidence: `three_phase_blueprint_runtime.py:438`, `three_phase_blueprint_runtime.py:1334`, `three_phase_blueprint_runtime.py:2010`.
- Medium: structural admission is a real second basin. When candidates move off the replay lane, they often die at `scene_completeness` and insufficient scene payload rather than replay. Evidence: `blueprint_ensemble.py:1190`, `session_20260417_144754.log:445`, `session_20260417_144754.log:580`.
- Medium: broad validator relaxation would be a risky first move. Current evidence shows many candidates are genuinely replay-heavy, so simply loosening the validator would likely pass bad continuations rather than create good ones. Evidence: `session_20260417_144754.log:290`, `session_20260417_144754.log:337`, `session_20260417_144754.log:934`.

## Pass 1. Structure And Scope Audit
Question attacked: is the proposed long-term direction even targeting the right owner?

Adversarial challenge:
- Maybe ep9 is still fundamentally an authority or arc-boundary problem, so generator refactor would be mis-scoped.

Counter-evidence:
- The compiler already emits progression packet, surface guidance, and future reserved-beat guidance into the prompt path. `blueprint_constraint_compiler.py:451` and `blueprint_ensemble.py:1450` confirm these are present in the producer constraint bundle.
- The latest runtime still ends at `ep9 all retries failed (10)` with repeated replay-candidate rejection and under-structured candidate rejection. `session_20260417_144754.log:290`, `:445`, `:580`, `:940`.
- The latest ep8 output still hands off ep9 from the same `VIP 라운지 / 한시우 / 박성호 / 전결권이 없으면 지점장 부르세요` axis, which explains why the next episode generation surface is narrow, but it does not prove authority absence. `blueprint_0008.txt:9`, `:15`, `:37`.

Pass 1 verdict:
- The direction is correctly scoped at Stage3 generator architecture, not at Stage4 or cross-stage authority repair.

## Pass 2. Evidence And Consistency Audit
Question attacked: are all four proposed long-term sub-directions equally justified?

Adversarial challenge:
- The proposal may be over-broad. Some sub-directions may be grounded, others may be intuition without sufficient evidence.

Assessment by sub-direction:

### 1. Compiler-side machine-readable surface contracts
Evidence for:
- Current compiler output is still advisory text only: `surface_guidance` and `future_beat_reservations` are strings, not structured obligations. `blueprint_constraint_compiler.py:1241`, `:1291`.
- This matches the observed weakness that producer prompts carry the idea but not a strong structural lane.

Adversarial caution:
- If the compiler starts deciding story staging in detail, it risks crossing the workspace rule that Python should collect/package constraints, not become the authorial decision-maker.
- Therefore the correct version is not `scene 2 must be branch manager office` hardcoding.
- The acceptable version is generic machine-readable structure such as:
  - max repeated primary surface count
  - minimum off-axis procedural scene count
  - required presence of at least one non-replay institution line when procedural must-focus exists

Verdict:
- `yes, but only as generic structural contracts derived from authority`, not story-specific slot authoring.

### 2. Ensemble surface diversification
Evidence for:
- Current worker strategies are style-only. They do not own disjoint surfaces. `blueprint_ensemble.py:52`, `:507`.
- Runtime evidence shows multiple workers falling into the same VIP-lounge replay basin in the same retry. `session_20260417_144754.log:290`, `:302`, `:337`, `:392`, `:934`.

Verdict:
- This is the strongest and most directly evidenced long-term direction.

### 3. Basin-aware retry steering
Evidence for:
- Retry state already records reject signatures, plateau reasons, and prior feedback. `three_phase_blueprint_runtime.py:1334`, `:2010`.
- However plateau logic currently emphasizes validation reopen and inplace/advisory plateaus, not repeated `candidate_disqualified` replay-vs-structure basins. `three_phase_blueprint_runtime.py:438`, `:1533`.

Verdict:
- Strongly justified.
- This should classify failures into at least:
  - replay-heavy basin
  - structure-thin basin
  - contamination basin
- Then choose different retry instructions, rather than repeating one generic disqualified message.

### 4. Validator continuation-vs-replay refinement
Evidence for:
- The replay detector is location-plus-character-overlap driven and trips once two or more prior scene families match. `unified_blueprint_validator.py:2273`, `:2278`, `:2294`.
- This can over-squeeze narrow-handoff episodes.

Adversarial caution:
- The logs show many rejected candidates really are replay-heavy. A looser validator would likely let bad candidates through without improving generation quality.

Verdict:
- Valid as a later precision fix.
- Not justified as the first or main long-term owner.

Pass 2 verdict:
- The overall direction is evidence-consistent, but the sub-priority order matters:
  1. ensemble diversification
  2. basin-aware retry steering
  3. compiler-side generic structural contracts
  4. validator refinement last

## Pass 3. Execution And Readability Audit
Question attacked: even if the direction is right, is the implementation shape likely to be healthy?

Adversarial challenge:
- The direction could be conceptually right but operationally wrong if it turns into more same-file accretion inside already-hot owners.

Evidence:
- `blueprint_constraint_compiler.py`: 1808 lines
- `blueprint_ensemble.py`: 2097 lines
- `three_phase_blueprint_runtime.py`: 3089 lines
- `unified_blueprint_validator.py`: 2605 lines

Risks:
- adding more ad hoc if-else lanes into these owners would satisfy the diagnosis while worsening maintainability and future drift
- broad validator surgery first would be high blast radius
- compiler-side story-specific slot hardcoding would mix packaging with authorial decision logic

Required implementation guardrails:
- prefer module-boundary extraction over piling more helpers into the same files
- keep the compiler responsible for generic structural packets, not specific scene authorship
- keep retry basin classification attached to observed reject signatures and screening reasons, not hand-written per-arc heuristics
- keep validator changes precision-oriented:
  - richer replay family semantics
  - not blanket threshold relaxation

Pass 3 verdict:
- The direction remains valid only if implemented as boundary cleanup plus generic contract enrichment, not as hot-file rule accumulation.

## Final Judgment
The proposed long-term direction is the right owner, but the implementation should be narrowed to this sequence:

1. `BlueprintEnsemble` surface diversification
   - make workers own different surface families rather than only different prose styles
2. `ThreePhase` basin-aware retry steering
   - detect replay-heavy vs structure-thin vs contamination basins and switch retry instructions accordingly
3. `BlueprintConstraintCompiler` generic structural packet enrichment
   - emit machine-readable off-axis/reuse limits without dictating story-specific scene content
4. `UnifiedBlueprintValidator` replay refinement
   - refine continuation-vs-replay precision after upstream generation is improved

Explicit non-recommendations:
- do not rerun before the structural wave lands
- do not lead with broad validator loosening
- do not hardcode episode-specific scene prescriptions in Python
- do not realize this as more same-file accretion in the existing hot owners

## Side-Effect Coverage
- File/artifact truth: checked for canary summary, latest session log, `llm_io.jsonl`, and latest ep8 blueprint
- Prompt/validation sink truth: checked in compiler, ensemble, retry, validator code
- DB writes: not applicable for this audit decision
- Stage4/runtime downstream behavior: not applicable for this audit decision
- temp mirror handling: not applicable because this is an audit note, not an execution SSOT

## Confidence
- Estimated confidence: 97%
- Reason:
  - the owner diagnosis is triangulated across live runtime evidence and current code
  - the main uncertainty is not whether the long-term direction is needed, but how much of it should be implemented in which owner and in what order
