# 0_0 Stage2-Stage3 Stage4-Readiness Parallel Bounded Survey

Date: 2026-03-31
Status: final (3-pass audited)
Document Type: bounded parallel survey
Canonical Path: `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
Temp Mirror Path: `(none - survey only)`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `0_0 live runtime logs/db/artifacts dirty; 0_temp console scratch dirty; lane draft docs untracked`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `no contradictory code drift observed during synthesis; lane drafts and active 0_0 runtime sinks remain dirty`
Track: system
Mode: bounded survey, no realization
Source Master Order:
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-master-order.md`
Source Lane Drafts:
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane1-stage2-authority-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane2-stage3-transform-validator-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane3-artifact-truth-vertical-slice-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane4-stage4-intake-readiness-draft.md`
Direct Recheck Surfaces:
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `projects/0_0/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json`
- `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/0_0/logs/artifacts/stage3/ep_0005/attempt_06/final_blueprint__action_focused.json`

## 1. Answer-First

No, `0_0` Stage 2 and Stage 3 are not uniformly Stage4-ready.

The correct diagnosis is:

- `Stage 2` is content-sufficient but schema-fragile.
- `Stage 3` is the primary blocker.
- `Stage 4` is not the primary fault, but its intake path is fail-open and therefore absorbs upstream contamination instead of stopping it.

More concretely:

- `Arc 1 (ep 1-4)` is broadly Stage4-ready.
- `Arc 2 (ep 5-9)` is not Stage4-ready in its current artifact state.
- The first structural break happens at the `Stage 2 -> Stage 3` boundary, where Stage 3 fabricates narrative content that the Stage 2 arc authority did not authorize, and the validator stack does not block the contaminated blueprint.

Therefore the right top-level verdict is:

- `Stage2/3 structurally fragile overall`
- with a stronger sub-verdict:
- `Stage 3 is structurally blocking for Stage 4 progression in Arc 2`

Keeping Stage 4 paused for this investigation was the correct operational choice.

## 2. Hard Conclusions

### H-1. Stage 2 is not the primary blocker.

The real Stage 2 artifacts are rich and concrete enough for downstream use. The core tactical document, episode ranges, timeline, and state packets are present and materially usable. The main Stage 2 weakness is schema instability, not content absence.

Direct recheck:

- `arc_drive.narrative_drive` keys differ materially between:
  - `projects/0_0/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json`
  - `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- This confirms Stage 2 authority is content-rich but shape-unstable.

### H-2. The first major structural break is Stage 3 generation fidelity.

`Arc 2 ep_0005` is the clearest proof. The Stage 2 tactical source is a financial leverage scene. The Stage 3 blueprint introduces unapproved physical violence, a thug intrusion beat, and additional narrative content that is not in the arc source.

Direct recheck:

- Stage 2 tactical source in `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
  - financial call with `박성호 PB`
  - `WTI 6월물`
  - `15억` leverage order
- Stage 3 blueprint in `projects/0_0/logs/artifacts/stage3/ep_0005/attempt_06/final_blueprint__action_focused.json`
  - `불량배` intrusion
  - physical confrontation
  - downstream threat setup

That is not a mild drift. It is a contract violation.

### H-3. Stage 3 validator coverage is insufficient to protect Stage 4.

The validator stack detects some severe problems but does not block them reliably, and several Stage4-relevant dimensions remain blind or weakly covered.

Direct recheck:

- `modules/domain/agents/blueprint_ensemble.py`
  - `constraint_summary` is placed in the `ADVISORY` band
- `modules/domain/agents/unified_blueprint_validator.py`
  - binding prevalidation is centered on:
    - `scene_completeness`
    - `arc_timeline`
    - `capital_unit`
  - this is not enough to guarantee Stage4-readiness

### H-4. Stage 4 intake is structurally sound, but operationally fail-open.

Stage 4 can consume the blueprint shape. That is not the main problem. The problem is that Stage 4 accepts contaminated upstream blueprints and tries to recover later with softer checks.

Direct recheck:

- `modules/core/stage4_orchestrator.py:719-723`
  - preflight is explicitly documented as fail-open
- `modules/core/stage4_orchestrator.py:904-916`
  - non-high or downgraded issues become pass-through
- `modules/core/stage4_immutable_fact_contract.py:252-253`
  - `must_materialize` falls back to `goal`
  - `must_not_erase` defaults empty

### H-5. Stage 3 -> Stage 4 handoff is missing explicit negative constraints.

All directly inspected Stage 3 artifacts (`ep_0001`, `ep_0002`, `ep_0005`, `ep_0006`, `ep_0008`) had:

- `must_materialize` missing in all scenes
- `must_not_erase` missing in all scenes

This means the Stage 4 IFC can carry opening anchors and scene goals, but it cannot strongly express "do not erase X" obligations because Stage 3 never provides them.

## 3. Medium-Confidence Conclusions

### M-1. Stage 2 schema fragility likely amplifies Stage 3 drift, but is not enough by itself to explain Arc 2 contamination.

The free-form `arc_drive` and mixed-granularity state fields create handoff risk. But the Arc 2 failures are too large to be explained by schema noise alone. The dominant issue is Stage 3 authority demotion plus retry drift.

### M-2. Retry behavior appears to worsen authority fidelity in hard episodes.

Lane 2 and Lane 3 both point to high-attempt episodes (`ep_0005`, `ep_0006`) as the worst cases. This strongly suggests retry loops are not converging toward the Stage 2 arc source under pressure.

### M-3. `ep_0008` is structurally cleaner than `ep_0005/0006` but should not be overread as globally healthy.

Stage 4 intake inspection judged `ep_0008` one of the cleaner structural blueprints. That does not nullify the Arc 2 narrative-truth problem. It only means the artifact shape is cleaner than the worst contaminated examples.

## 4. Open Questions

1. How far the Arc 2 contamination extends through `ep_0007` and `ep_0009` was not directly inspected at the same depth as `ep_0005`, `ep_0006`, and `ep_0008`.
2. The regex fragility around tactical extraction is structurally real, but this survey did not find a proven live `0_0` failure where the regex silently failed.
3. The exact split between strategy misalignment and retry-induced drift inside Stage 3 is not fully closed. Both are implicated.

## 5. Stage2 -> Stage3 -> Stage4 Readiness Ladder

| Layer | Verdict | Meaning |
|---|---|---|
| Stage 2 source authority | `stage2-fragile` | Content is sufficient; schema is unstable; not the main blocker |
| Stage 3 transformation | `stage3-fragile` | Authority is weakened and sometimes contradicted during blueprint generation |
| Stage 3 validator | `insufficient` | Detects some defects but does not reliably stop Stage4-hostile artifacts |
| Artifact truth | `artifact-fragile` overall | Arc 1 ready enough; Arc 2 contains blocking contamination |
| Stage 4 intake | `intake-fragile` | Intake can consume shape, but accepts contaminated input fail-open |

Operational interpretation:

- `Arc 1`: progression possible
- `Arc 2`: progression should not be trusted without upstream remediation

## 6. Artifact Truth / Metadata Truth / Narrative Truth Matrix

| Slice | Artifact Truth | Metadata Truth | Narrative Truth | Result |
|---|---|---|---|---|
| Arc 1 Stage 2 | Present, parseable, rich | Aligned | Aligned | healthy |
| Arc 1 Stage 3 | Present, parseable, structurally complete | Aligned | Mostly aligned to arc | Stage4-ready with caveats |
| Arc 1 Stage 4 intake | Consumes fields correctly | Aligned | Early manuscripts follow blueprint | acceptable |
| Arc 2 Stage 2 | Present, parseable, rich | Aligned | Aligned | healthy source |
| Arc 2 Stage 3 | Present and structurally complete | Often says pass despite severe issues | Contradicts arc source in key places | blocking contamination |
| Arc 2 Stage 4 intake | Can consume blueprint shape | Accepts upstream issues through fail-open preflight | Cannot be expected to repair fabricated upstream content | fragile consumer of bad input |

## 7. Per-Episode Readiness Table

| Episode | Stage 2 authority | Stage 3 blueprint shape | Narrative truth vs arc | Stage 4 readiness | Notes |
|---|---|---|---|---|---|
| `ep_0001` | strong | strong | aligned | ready | first-pass healthy path |
| `ep_0002` | strong | strong | mostly aligned | ready with conflict risk | intake/manuscript chain is coherent |
| `ep_0005` | strong | structurally complete | blocking drift | not ready | fabricated violence, institution drift, timeline issue |
| `ep_0006` | strong | structurally complete | blocking drift | not ready | high-attempt churn suggests non-convergence |
| `ep_0008` | adequate source | structurally cleaner | still not fully trusted at narrative layer | fragile | cleaner shape does not erase Arc 2 contamination risk |

## 8. Primary Cause Ranking

### 1. Stage 3 generation fidelity to Stage 2 authority

This is the main blocker. Stage 3 is not preserving arc authority reliably in the hard slice.

### 2. Stage 3 validator blind spots and non-blocking behavior

Even when the system notices severe defects, the artifact can still survive as a usable blueprint candidate.

### 3. Stage 3 retry drift under pressure

Hard episodes appear to move away from arc-faithful output rather than toward it.

### 4. Stage 4 fail-open intake and IFC contract gaps

This is secondary, but it increases downstream churn by letting contaminated artifacts through.

### 5. Stage 2 schema instability

Real, but not the primary current blocker.

## 9. Bounded Remediation Seam Ranking

1. `Stage 3 authority promotion`
   - move Stage 2 prohibition and tactical authority out of weak advisory treatment
   - especially `constraint_summary` and arc tactical prohibitions
2. `Stage 3 blocking validator for Stage4-readiness`
   - add explicit blocking coverage for:
     - opening anchor integrity
     - mission clarity
     - timeline specificity
     - protagonist-state consistency
     - source-authority contradiction
3. `Stage 3 retry authority preservation`
   - retries must not progressively weaken the original arc contract
4. `Stage 3 -> Stage 4 negative obligation contract`
   - populate `must_not_erase`
   - promote explicit `must_materialize`
5. `Stage 2 schema normalization`
   - stabilize `arc_drive` and related authority packets

## 10. Decision

A new execution SSOT is justified.

The correct focus is not `Stage 4 remediation first`.
The right focus is:

- `Stage 2/3 Stage4-readiness remediation`
- centered on Stage 3 generation fidelity and validator hardening
- with Stage 4 intake only as a secondary containment layer

Stage 4 should remain paused until that upstream readiness lane is addressed or a narrower operator decision overrides the pause.

## 11. 3-Pass Audit Record

Pass 1, structure and scope:

- kept the document bounded to the user question: whether Stage 2 and Stage 3 are structurally able to support Stage 4
- kept Stage 4 in consumer-readiness scope only
- did not escalate into implementation

Pass 2, evidence and consistency:

- merged all four lane drafts
- directly rechecked the strongest claims in live code and real `0_0` artifacts
- resolved the apparent `ep_0008` tension by separating structural readiness from narrative-truth readiness

Pass 3, execution and readability:

- reduced the result to one ranked blocker model
- made the next operational consequence explicit
- kept the output as survey only, with no `docs/temp` mutation

Confidence: `96%`
