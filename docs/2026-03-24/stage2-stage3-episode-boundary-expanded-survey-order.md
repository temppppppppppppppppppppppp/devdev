Date: 2026-03-24
Status: active
Document Type: system-track survey order
Canonical Path: `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/console.txt`
- `docs/2026-03-24/stage4-immutable-fact-convergence-execution-ssot.md`
- `docs/2026-03-24/현상황요약.txt`
Evidence Artifacts:
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/plans/blueprints/blueprint_0001.txt`
- `projects/00_001/logs/session/llm_io.jsonl`
- `projects/00_001/logs/episode_production.jsonl`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace allowed; tracked stage4/state/writer/validator edits plus deleted historical project artifacts remain in-flight`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `must be re-audited before any implementation or execution-SSOT promotion`

## 1. Purpose

- Define the `expanded Stage 2-3 survey` needed before any implementation wave.
- Separate three questions that are currently entangled:
  - `future-state leakage` from Stage 2/3 inputs
  - `episode allocation under-specification` in Stage 2
  - `manuscript length / scene-density pressure` as a secondary amplifier
- Prevent a premature implementation SSOT from hardening the wrong root-cause model.

This document is a survey order, not an execution SSOT.

## 2. Primary Questions

1. Is the dominant failure in `00_001` really Stage 2 low-density allocation, or is Stage 3 receiving future-only arc-end facts too early?
2. Which specific inputs are leaking later-episode state into early-episode Blueprint generation?
3. Are `episode_details` and `stop_line` still the real positive authority surfaces, or are they being drowned out by broader arc payloads?
4. Is the current Stage 2 density/specificity gate too weak for investment-genre tactical allocation?
5. Is low manuscript length a primary cause, or only a secondary consequence once scope contamination has already happened?

## 3. Scope

Included code surfaces:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/domain/agents/arc_draft_validator.py`
- `modules/domain/agents/four_phase_arc_generator.py`

Included evidence surfaces:
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/plans/blueprints/blueprint_0001.txt`
- `projects/00_001/logs/session/llm_io.jsonl`
- `projects/00_001/logs/episode_production.jsonl`
- `docs/2026-03-23/console.txt`

Included side-effect surfaces:
- Stage 2 prompt/build-time payload composition
- Stage 3 constraint and prompt composition
- Blueprint hard/current-state vs future-only context
- episode allocation diagnostics
- length/density warnings and downstream manuscript pressure signals

Excluded unless needed as evidence:
- Stage 4 retry/routing redesign
- Director policy changes
- Chief Writer redesign outside touched Stage 3 input surfaces
- global manuscript target-length retune
- DB schema or JSONL shape changes
- immediate code patching

## 4. Current Working Hypothesis

Current evidence points to this ordering:

1. `future-state leakage` is the primary suspect
2. `Stage 2 episode allocation under-specification` is the next suspect
3. `low manuscript length / dialogue density` is real but secondary

Why this is still only a hypothesis:
- `00_001` proves the symptom strongly
- but the exact contribution split between `leakage` and `low-density allocation` is not yet isolated enough for direct implementation

## 5. Required 3-Pass Survey Method

### Pass 1. Payload Boundary Re-Audit

- Reconstruct the exact Stage 2 -> Stage 3 payload path for early episodes.
- Classify every touched input as one of:
  - `current-episode hard fact`
  - `prior-episode continuity`
  - `arc-global advisory`
  - `future-only / later-episode fact`
- Explicitly audit:
  - `episode_details`
  - `must_focus`
  - `stop_line`
  - `joint_docs`
  - `state_constraints`
  - `state_changes`
  - `semantic_carryover`
  - world-state / fact-ledger advisory injection
  - `apply_continuity_pins(...)`

Pass 1 output must answer:
- which fields are safe for ep1 hard context
- which fields should be advisory-only
- which fields should be filtered by `episode <= current_ep`

### Pass 2. Evidence Merge Against 00_001

- Re-read the live `00_001` evidence and align each suspect field with concrete contamination evidence.
- Minimum anchors:
  - Stage 2 arc split
  - ep1 Blueprint overconsumption
  - ep1/ep2 prompt evidence in `llm_io.jsonl`
  - episode-level production warnings
- Mark each suspect as:
  - `confirmed leakage`
  - `likely leakage`
  - `density-only`
  - `secondary pressure only`
  - `not supported`

### Pass 3. Density and Length Decision Gate

- Audit whether Stage 2 density checks are materially too weak for this failure family.
- Separate:
  - `insufficient episode tactical specificity`
  - `insufficient manuscript target length`
  - `insufficient dialogue or climax density after correct scoping`
- End with one of these conclusions:
  - `boundary fix first`
  - `density fix first`
  - `paired small wave`

Do not jump to `increase target length` unless Pass 1 and Pass 2 show the boundary leak is not the main cause.

## 6. Required Work Products

The survey should produce, at minimum:

1. one canonical expanded survey report
2. one `field classification ledger` for Stage 2->3 payload inputs
3. one `00_001 contamination evidence ledger`
4. one bounded decision note choosing:
   - `execution SSOT now`
   - `survey insufficient`
   - `follow-up live sample needed`

Do not create an execution SSOT unless the survey reaches at least 95% confidence on the primary root-cause ordering.

## 7. Mandatory Questions Per Surface

For each audited surface, answer:

1. Is this field/input describing `now`, `already completed before now`, or `arc end`?
2. If it describes `arc end`, why is it present in early-episode prompt context?
3. Does this input act as hard authority, soft advisory, or mixed/ambiguous authority?
4. Can this field be filtered by episode number without breaking valid continuity?
5. If the field is not the main culprit, what evidence clears it?

## 8. Decision Gates

Promote to implementation only if the survey proves:
- the main leakage seam is concrete enough to patch without guesswork
- the positive authority surfaces are clear
- the length question is bounded enough to defer or include explicitly

Stop and do not promote if:
- the evidence still cannot distinguish `leakage` from `density`
- the root cause appears to require a much broader schema redesign
- the survey confidence remains below 95%

## 9. Suggested Deliverable Paths

- order:
  - `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-order.md`
- final survey report:
  - `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
- optional evidence ledger:
  - `docs/2026-03-24/stage2-stage3-episode-boundary-evidence-ledger.md`

## 10. Opus Survey Prompt

```text
System-track survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-order.md
6. docs/2026-03-24/stage4-immutable-fact-convergence-execution-ssot.md
7. docs/2026-03-23/console.txt
8. docs/2026-03-24/현상황요약.txt

Task:
Run an expanded survey of the Stage 2 -> Stage 3 episode-boundary integrity problem before any implementation.

Primary goal:
Determine whether the dominant root cause is:
1. future-state leakage into early-episode Blueprint generation,
2. Stage 2 episode allocation under-specification,
3. manuscript length/density pressure,
or a bounded combination of the first two.

Hard constraints:
- This is survey-first. Do not patch code.
- Do not draft an execution SSOT unless the survey reaches 95% confidence on the primary root-cause ordering.
- Keep the survey bounded to Stage 2 / Stage 3 payload composition, allocation specificity, and downstream length-pressure interpretation.
- Do not reopen Stage 4 redesign.
- Do not propose a broad repo-wide schema rewrite unless the evidence truly forces that conclusion.
- Workspace is dirty. Do not revert unrelated edits.

Required survey scope:
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/core/stage3_orchestrator.py
- modules/domain/agents/blueprint_ensemble.py
- modules/core/stage2_validation_pipeline.py
- modules/domain/agents/arc_draft_validator.py
- modules/domain/agents/four_phase_arc_generator.py
- projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json
- projects/00_001/plans/blueprints/blueprint_0001.txt
- projects/00_001/logs/session/llm_io.jsonl
- projects/00_001/logs/episode_production.jsonl
- docs/2026-03-23/console.txt

Required outputs:
1. a field-classification ledger:
   - current-episode hard fact
   - prior-episode continuity
   - arc-global advisory
   - future-only / later-episode fact
2. a 00_001 contamination evidence ledger
3. a bounded conclusion choosing:
   - boundary fix first
   - density fix first
   - paired small wave
4. if confidence >= 95%, a recommendation for the next execution SSOT scope

Minimum questions to answer:
- Which exact fields are leaking later-episode state into ep1/ep2?
- Are `episode_details` and `stop_line` still the true positive authority surfaces?
- Are current Stage 2 density thresholds too weak for this failure family?
- Is low manuscript length primary or secondary?

Output requirements:
- findings first, ordered by severity
- concrete file/line anchors where possible
- no implementation claims
- if confidence is below 95%, say so explicitly and stop at survey conclusions
```

## 11. 3-Pass Audit Record

- Pass 1
  - confirmed this document is a survey order, not an execution SSOT
- Pass 2
  - confirmed the order is anchored to live `00_001` artifacts and current code surfaces
- Pass 3
  - confirmed the stop rules prevent premature implementation or premature length-retune conclusions

## 12. Confidence

- Confidence: 98%
- Basis:
  - matches current evidence state better than a premature implementation order
  - keeps scope bounded to the exact uncertainty the user identified
  - aligns with current workspace governance: survey first, then execution SSOT only after confidence is high enough
