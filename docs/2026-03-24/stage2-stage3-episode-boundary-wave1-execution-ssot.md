Date: 2026-03-24
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
Temp Mirror Path: `removed after closure (former path: docs/temp/stage2-stage3-episode-boundary-wave1-execution-ssot.md)`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: active stage4/state/writer/validator edits, orientation/doc updates, and deleted historical project artifacts; docs/temp queue currently empty except queue-state.json`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD; Wave 1 realization landed in blueprint_constraint_compiler.py, stage3_orchestrator.py, targeted boundary regressions, and one closure-audit docstring alignment patch`
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-order.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
Evidence Artifacts:
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/plans/blueprints/blueprint_0001.txt`
- `projects/00_001/logs/session/llm_io.jsonl`
- `projects/00_001/logs/episode_production.jsonl`
- live source anchors in `modules/domain/agents/blueprint_constraint_compiler.py` and `modules/core/stage3_orchestrator.py`
Side-Effect Coverage: covered

---

# Stage 2-Stage 3 Episode Boundary Wave 1 Execution SSOT

## 1. Intent

Realize the first of two bounded waves for the `00_001` failure family.

Wave 1 goal:
- stop future-episode leakage at the Stage 2 -> Stage 3 boundary so an early episode blueprint cannot consume later-episode facts or later-episode treatment events as if they were current-episode obligations

Why now:
- the expanded survey reached 97% confidence that three leakage seams, not manuscript length or generic density, are the primary root cause of the cascade seen in `00_001`
- the dominant seam is patchable without reopening a broad refactor or a Stage 4 redesign

Wave split:
- Wave 1: boundary fix first
- Wave 2: Stage 2 allocation/density follow-up only after Wave 1 lands and is revalidated

## 2. Baseline Facts

Primary root-cause ordering from the survey:
1. `state_changes` episode filtering is missing in `blueprint_constraint_compiler.py`
2. Stage 3 treatment block injection exposes the full arc with only a soft guard
3. stop line covers only `ep+1`, leaving `ep+2+` content unguarded

Confirmed live anchors:
- `modules/domain/agents/blueprint_constraint_compiler.py:525-609`
  - `_summarize_state_changes()` emits arc-wide future state without filtering by current episode
- `modules/core/stage3_orchestrator.py:1115-1172`
  - `_inject_stage3_treatment_block_context()` injects full-arc treatment content into the prompt
- `modules/domain/agents/blueprint_constraint_compiler.py:305-346`
  - `_extract_stop_line()` blocks only the next episode

Positive authority surfaces that should remain authoritative:
- `episode_details`
- `must_focus`
- `stop_line` concept itself
- continuity pins and past-verified advisory inputs

Explicit non-primary contributor:
- `Stage 2 final ep_count / episode allocation judgment left to the LLM` remains a plausible secondary amplifier, but current evidence does not justify mixing that redesign into Wave 1
- that topic belongs to Wave 2 follow-up, alongside `episode_details` specificity and allocation-balance work

## 3. Scope

Included:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage3_orchestrator.py`
- targeted regression tests for Stage 2 -> Stage 3 boundary integrity
- bounded documentation/comments only if needed to keep the new contract legible in touched paths

Excluded:
- `modules/core/stage2_validation_pipeline.py`
- `modules/domain/agents/arc_draft_validator.py`
- `modules/domain/agents/four_phase_arc_generator.py`
- Stage 4 retry or Director policy redesign
- global manuscript target-length retune
- broad prompt redesign beyond the touched leakage seams
- DB schema, JSONL schema, artifact naming, or persistence changes
- any attempt to move final creative episode allocation judgment entirely from LLM to Python in this wave

## 4. Pass 1. Inventory Summary

- runtime blast radius is small:
  - 2 production files are primary owners
  - 1 or more targeted regression test files should lock the behavior
- failure impact is high:
  - these seams sit directly on the Stage 3 blueprint prompt assembly path
  - leakage here propagates downstream into manuscript continuity failures and expensive Director-led recovery
- the dominant runtime path is:
  - Stage 2 arc payload
  - `BlueprintConstraintCompiler.compile()`
  - `Stage3Orchestrator` prompt augmentation
  - Stage 3 blueprint generation prompt

## 5. Pass 2. Semantic Classification

- Class A. Hard future-state leakage
  - `state_changes_summary` currently promotes future episode state as present-tense hard constraint material
- Class B. Soft-but-loud future exposure
  - treatment block is nominally advisory, but its narrative vividness makes it effectively hard for blueprint drafting
- Class C. Negative constraint undercoverage
  - stop line concept is correct, but current implementation only forbids the next episode
- Class D. Deferred amplifiers
  - sparse `episode_details`
  - Stage 2 density/allocation guard weakness
  - manuscript length pressure

Wave 1 should only realize Classes A-C.

## 6. Side-Effect Map

- file writes / artifacts:
  - production code changes in Stage 3 prompt assembly surfaces
  - new or updated regression tests
  - no new artifact family required
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - prompt payload content recorded in runtime logs will change
  - sink shape and schema must not change
- console / UI / operator output:
  - no new operator surface required
  - existing logs may show shorter or more tightly scoped prompt sections
- rollback / recovery / retry:
  - no retry policy redesign in scope
  - downstream rejection frequency may improve, but only as a consequence
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

Wave 1 operating rule:
- Python may tighten the allowed fact window and negative constraints
- Python must not seize the creative allocation decision or rewrite Stage 2 into a fully deterministic allocator in this wave
- LLM remains responsible for narrative judgment inside the bounded current-episode window

Required architecture:
1. filter hard state so only `episode <= current_ep` facts become current blueprint constraints
2. re-scope or structurally separate treatment block content so later-episode events are not consumed as direct blueprint input
3. expand the negative boundary so all future episode content is outside the allowed blueprint window

Preferred conservation rules:
- preserve `episode_details`, `must_focus`, continuity pins, and past-verified advisory inputs as the positive authority surfaces
- keep `semantic_carryover` and `joint_docs` unchanged unless a test proves they are directly causing the current wave's failure
- if treatment-block per-episode slicing is ambiguous, prefer hard separation or future-only quarantine over speculative field parsing

Wave 2 deferred topics:
- `episode_details` minimum specificity gate
- allocation balance checks across episodes
- whether the current `final ep_count judgment to the LLM` split needs a bounded redesign
- manuscript length tuning

## 8. Execution Tranches

1. `state_changes` boundary filter
- add current-episode filtering so future episode entries do not enter `state_changes_summary` as active constraints
- keep already-committed prior/current facts available for continuity

2. treatment block scoping
- reduce or isolate full-arc treatment injection so later-episode `event_villain`, `solution`, or equivalent content is not treated as current-episode blueprint fuel
- preserve enough context for arc coherence without reintroducing future-event leakage

3. stop-line expansion
- extend the negative boundary beyond `ep+1`
- implementation may enumerate all future episodes or use an equivalent blanket prohibition, but the outcome must cover all future content rather than only the next episode

4. regression lock
- add targeted tests that prove the three seams remain bounded
- keep the verification surface focused on Stage 3 prompt/constraint composition and no-regression continuity

## 9. Acceptance Criteria

- current-episode Stage 3 prompt inputs no longer surface future-episode `state_changes` as active current constraints
- treatment block no longer exposes later-episode events as direct blueprint-driving content for the current episode
- stop line or equivalent negative guard covers all future episodes, not only `ep+1`
- current and prior committed continuity facts remain available where they were previously legitimate
- no changes are introduced to:
  - Stage 2 density gates
  - final ep_count judgment ownership
  - Stage 4 retry routing
  - Director policy
  - DB or JSONL schema

## 10. Verification Plan

- `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage3_orchestrator.py`
- targeted pytest shards:
  - `pytest tests/test_stage3_orchestrator.py -q`
  - `pytest tests/test_blueprint_patch_mode.py -q`
  - targeted boundary regression file for this wave, e.g. `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
- inspect or assert prompt assembly surfaces for:
  - filtered `state_changes`
  - treatment block scoping or quarantine
  - expanded stop-line coverage
- `python scripts/check_utf8_hygiene.py modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage3_orchestrator.py tests/test_stage3_orchestrator.py tests/test_blueprint_patch_mode.py tests/test_stage2_stage3_episode_boundary_guardrail.py docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md docs/temp/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

Recommended post-realization operator check:
- rerun the affected `00_001` episode boundary path or a bounded fresh continuation slice to confirm ep1-style overconsumption no longer recurs through the touched Stage 3 surfaces

## 11. Guardrails

- do not widen into Wave 2 during implementation
- do not modify Stage 2 density or allocation heuristics in this wave
- do not convert creative episode allocation judgment into a Python-owned decision engine
- do not redesign Stage 4 retries, Director policy, or manuscript selection
- do not alter persistence contracts, JSONL payload shapes, or DB schema
- do not remove positive authority surfaces that are already correct
- if a desired fix requires broad treatment-block redesign, stop at the most conservative bounded isolation that satisfies the acceptance criteria

## 12. Temp Queue Notes

- temp status: closed; mirror removed after closure audit
- cleanup condition:
  - Wave 1 realization completed
  - canonical execution SSOT closure-audited
  - temp mirror removed
- roadmap dependency:
  - none while this remains the only active execution item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- queue-state tracking: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run the document 3-pass audit against the live workspace before patching code from this SSOT
  - refresh `Resume Commit` and `Resume Drift Summary` before realization

## 14. Opus Execution Prompt

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-order.md
5. docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md
6. docs/temp/stage2-stage3-episode-boundary-wave1-execution-ssot.md
7. docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md
8. docs/2026-03-24/현상황요약.txt
9. docs/2026-03-23/console.txt

Task:
Implement Wave 1 only of the Stage 2 -> Stage 3 episode-boundary fix.

Primary goal:
Stop future-episode leakage at the Stage 3 blueprint input boundary by fixing only these three seams:
- state_changes episode filtering
- treatment block future-event exposure
- stop line undercoverage

Hard constraints:
- Follow the execution SSOT exactly.
- Re-audit the canonical execution SSOT against the live workspace before patching; shrink scope if any item is already resolved.
- Keep this wave bounded to Stage 3 boundary integrity.
- Do not open Wave 2.
- Do not touch Stage 2 density gates, allocation-balance validation, or `final ep_count judgment` ownership in this wave.
- Do not redesign Director policy, Stage 4 retry routing, or manuscript target length.
- Do not change DB schema, JSONL schema, or artifact naming.
- Workspace is dirty. Do not revert unrelated edits.
- Preserve the rule that Python narrows the allowed fact window, but creative allocation judgment still belongs to the LLM.
- Preserve positive authority surfaces (`episode_details`, `must_focus`, continuity pins, past-verified advisory inputs).
- If treatment-block per-episode slicing is ambiguous, prefer conservative hard separation/quarantine over speculative parser logic.
- Use apply_patch for edits.
- Respect UTF-8 hygiene on all touched files.
- Do not close the execution SSOT; Codex will audit and close it.

Implementation targets:
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/core/stage3_orchestrator.py
- targeted tests for this wave

Explicitly excluded:
- modules/core/stage2_validation_pipeline.py
- modules/domain/agents/arc_draft_validator.py
- modules/domain/agents/four_phase_arc_generator.py
- Stage 4 and Director redesign
- manuscript length retune
- broad prompt architecture rewrite

Acceptance targets:
- future episode state_changes do not appear as current blueprint constraints
- treatment block no longer injects later-episode event content as current-episode blueprint fuel
- stop line or equivalent prohibition covers all future episodes
- prior/current legitimate continuity facts remain available
- no forbidden Stage 2/Stage 4/schema changes are introduced

Required verification:
- python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage3_orchestrator.py
- pytest tests/test_stage3_orchestrator.py -q
- pytest tests/test_blueprint_patch_mode.py -q
- pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q
- python scripts/check_utf8_hygiene.py <all touched code/test/doc files>
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize changes by seam
- list exact verification results
- list residual risks
- explicitly confirm that Wave 2 was not opened
- do not claim closure; Codex will audit and close it
```

Short dispatch line:
- `docs/temp/stage2-stage3-episode-boundary-wave1-execution-ssot.md + Wave 1만 bounded 구현해. state_changes filter / treatment block scope / stop line expansion만, Wave 2 금지, closure는 하지 말고 verification까지.`

## 15. 3-Pass Audit Summary

Pass 1. Structure and Scope
- execution SSOT scope is explicit and limited to Wave 1 boundary repair
- canonical and temp semantics are correct
- Wave 2 topics are explicitly deferred rather than silently mixed in

Pass 2. Evidence and Consistency
- root-cause claims are tied to the survey order and final survey report
- live source anchors match the report's three primary leakage seams
- commit-state metadata and queue semantics are coherent with the live workspace

Pass 3. Execution and Readability
- tranches, guardrails, and acceptance criteria are narrow enough for direct realization
- the Python-vs-LLM responsibility split is preserved instead of overcorrecting into deterministic allocation logic
- the embedded Opus prompt is aligned with the bounded execution scope

Confidence
- estimated confidence: 97%

## 16. Closure Note

- Realization state:
  - closed
- Closure audit result:
  - `state_changes` is filtered to current-episode scope before entering the Stage 3 blueprint constraint prompt
  - treatment block injection now carries arc-framing fields only and quarantines later-episode event payload
  - stop line now covers all future episodes instead of only `ep+1`
  - Wave 2 topics remained unopened

### Closure Verification

- `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage3_orchestrator.py`
- `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q` -> `25 passed`
- `pytest tests/test_stage3_orchestrator.py -q` -> `78 passed`
- `pytest tests/test_blueprint_patch_mode.py -q` -> `43 passed`
- post-audit docstring alignment recheck:
  - `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage3_orchestrator.py`
  - `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q` -> `25 passed`
- `python scripts/check_utf8_hygiene.py modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage3_orchestrator.py tests/test_stage2_stage3_episode_boundary_guardrail.py tests/test_stage3_orchestrator.py docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md docs/temp/stage2-stage3-episode-boundary-wave1-execution-ssot.md`

### Residual Risk

- `semantic_carryover` foreshadow anchors can still describe arc-end state abstractly; this remained outside Wave 1 by design
- `episode_details` specificity and Stage 2 allocation-balance weakness remain Wave 2 topics
- `genre_ext` still enters the treatment overview; acceptable for Wave 1, but still worth watching
- `modules/domain/agents/blueprint_constraint_compiler.py` contains pre-existing `[IFC]` carryover logic in the same dirty file; closure for this SSOT does not newly certify that out-of-scope path
