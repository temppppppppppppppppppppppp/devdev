# Stage2 -> Stage3 Semantic Carryover Boundary Wave2 Execution SSOT

Date: 2026-03-24
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
Baseline Dirty Summary: dirty workspace; active temp queue empty before this SSOT; many unrelated modified/deleted files already present outside this wave
Resume Commit: `529869adddb35c93c3ec557aeaed665de168daef`
Resume Drift Summary: initial creation; no prior realization attempt for this SSOT
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
- `docs/2026-03-24/stage2-stage3-residual-leakage-10terminal-merge-audit.md`
- `docs/2026-03-24/opus-residual/t2-stage2-arc-payload.md`
- `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals.md`
- `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace.md`
- `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger.md`
Evidence Artifacts:
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`
- `projects/00_001/logs/episode_production.jsonl`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
Side-Effect Coverage:
- Stage 3 constraint compilation
- Stage 3 live prompt formatting
- blueprint prompt contract visibility
- no DB/schema/JSONL/artifact naming change allowed in this wave

## 1. Problem Statement

Wave 1 removed the major `state_changes`, treatment-block, and stop-line undercoverage seams, but the fresh rerun still let ep1 absorb ep3/ep4 completion state. The post-rerun 10-lane merge audit isolates the remaining culprit to residual Stage 3 prompt-boundary leakage:

1. `semantic_carryover` still presents arc-end signals as live positive prompt fuel.
2. `_extract_immutable_fact_carryover()` still bypasses the episode boundary for ep2+.
3. `blueprint_ensemble` still fails to render the already-computed all-future stop-line data.

This wave is bounded to those seams only.

## 2. Included Scope

- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- targeted regression tests for this wave

## 3. Explicitly Excluded Scope

- `modules/core/stage3_orchestrator.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/domain/agents/arc_draft_validator.py`
- `modules/domain/agents/four_phase_arc_generator.py`
- `genre_ext` quarantine
- Stage 2 density/allocation redesign
- `final ep_count judgment` ownership changes
- Stage 4 / Director / retry policy redesign
- manuscript target-length tuning
- DB schema, JSONL schema, artifact naming, or persistence contract changes
- first-episode special-rule redesign

## 4. Execution Decision

Open one compact realization wave focused on residual prompt-boundary integrity. The goal is not to redesign arc semantics. The goal is to stop arc-end state from reading as current-episode obligation fuel.

## 5. Tranche Plan

### Tranche A. Semantic Carryover Boundary

Owner:

- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`

Problem:

- `semantic_carryover` currently carries `growth_justification`, `foreshadow_anchors`, and `continuity_checkpoints` into the live blueprint prompt with no episode scoping.
- In `00_001`, `continuity_checkpoints` and `growth_justification` echo ep3/ep4 completion state and correlate directly with ep1 overconsumption.

Required implementation shape:

- Preserve the useful semantic surface only if it cannot act as current-episode completion fuel.
- `relationship_rationale` may remain if rendered as relational context, not as present-tense obligation.
- `continuity_checkpoints` must not appear in the current-episode blueprint prompt as affirmative continuity lines.
- `growth_justification` must not appear as current-episode progress fuel when it encodes future achievement.
- `foreshadow_anchors`, if kept, must be explicitly future-only advisory and must not be rendered as current-episode continuity.
- If the design choice is between heuristic episode guessing and conservative suppression/quarantine, prefer conservative suppression/quarantine.

Acceptance criteria:

- ep1 prompt no longer exposes arc-end lines like `capital secured` or `corporation setup complete` as current-episode semantic carryover.
- the remaining semantic block, if any, is clearly advisory and cannot be confused with must-do or already-done current-episode facts.
- positive authority surfaces remain intact:
  - `must_focus`
  - `continuity`
  - `inherited_state`
  - Wave 1 filtered `state_changes_summary`

### Tranche B. Immutable Fact Carryover Episode Filter

Owner:

- `modules/domain/agents/blueprint_constraint_compiler.py`

Problem:

- `_extract_immutable_fact_carryover()` still reads arc-wide `state_changes` for ep2+ and bypasses the Wave 1 episode boundary.

Required implementation shape:

- pass current episode context into IFC extraction
- reuse a bounded `episode <= current_ep` filter for episode-tagged entries
- null-episode entries may remain only if they are truly arc-global and not future-episode completions

Acceptance criteria:

- ep2+ IFC output cannot include future-episode deaths, relationship flips, item changes, or skill acquisitions solely because they exist later in arc-level `state_changes`
- ep1 behavior remains unchanged as blank/no-op for IFC

### Tranche C. Stop-Line Live Prompt Parity

Owner:

- `modules/domain/agents/blueprint_ensemble.py`

Problem:

- the compiler now computes `future_eps`, but the live formatter only renders the next-episode stop line

Required implementation shape:

- `_format_constraints()` must render both:
  - next-episode stop line
  - all `future_eps` entries
- preserve or strengthen the blanket all-future prohibition already established in the compiler contract

Acceptance criteria:

- the live prompt surface matches the Wave 1 compiler contract for all-future episode prohibition
- this remains a defense-in-depth improvement and does not alter DB or artifact contracts

## 6. Required Tests

- add or update targeted tests covering semantic-carryover quarantine/suppression behavior
- add or update targeted tests covering IFC episode filtering for ep2+
- add or update targeted tests covering `future_eps` rendering in the live prompt formatter
- preserve Wave 1 regression guarantees

## 7. Required Verification

- `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py`
- `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
- `pytest tests/test_blueprint_patch_mode.py -q`
- `pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q`
- `python scripts/check_utf8_hygiene.py <all touched code/test/doc files>`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 8. Residual Risks

- `genre_ext` may remain a secondary amplifier after this wave; it is intentionally excluded unless fresh evidence still points there after realization
- the Stage 4 first-episode location note remains untouched and is not validated as part of this wave
- Stage 2 density/allocation balance remains deferred
- if `semantic_carryover` currently serves hidden coherence value in late episodes, overly aggressive suppression could reduce arc-level flavor; prefer minimal, conservative quarantine targeted at obligation-like fields

## 9. Closure Rule

Do not close this execution SSOT from the implementation terminal. Codex performs the closure audit.

Closure audit result:

- realized implementation matches the three-tranche scope
- no excluded Stage 2 / Stage 4 / `genre_ext` expansion detected
- targeted verification re-run by Codex passed
- residual runtime risk remains: no fresh post-wave live run was executed during closure audit

## 10. Opus Execution Order

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-24/stage2-stage3-residual-leakage-10terminal-merge-audit.md
5. docs/temp/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md
6. docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md
7. docs/2026-03-24/현상황요약.txt
8. docs/2026-03-24/console.txt

Task:
Implement the bounded residual Stage 3 leakage wave defined in the execution SSOT.

Primary goal:
Stop the remaining arc-end prompt leakage that still causes ep1/early-episode overconsumption after Wave 1.

Hard constraints:
- Follow the execution SSOT exactly.
- Re-audit the canonical execution SSOT against the live workspace before patching; shrink scope if any item is already resolved.
- Keep this wave bounded to:
  - semantic_carryover boundary
  - immutable fact carryover episode filter
  - live stop-line render parity
- Do not open Stage 2 density/allocation redesign.
- Do not touch `final ep_count judgment` ownership.
- Do not open `genre_ext` quarantine in this wave.
- Do not touch Stage 4, Director, retry policy, DB schema, JSONL schema, or artifact naming.
- Preserve positive authority surfaces like `must_focus`, `continuity`, and inherited state.
- Prefer conservative suppression/quarantine over heuristic episode guessing when semantic carryover entries are ambiguous.
- Workspace is dirty. Do not revert unrelated edits.
- Use apply_patch for edits.
- Respect UTF-8 hygiene on all touched files.
- Do not close the execution SSOT; Codex will audit and close it.

Implementation targets:
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/domain/agents/blueprint_ensemble.py
- targeted tests for this wave

Acceptance targets:
- current-episode prompt no longer treats arc-end continuity checkpoints as present-tense obligations
- IFC for ep2+ cannot read future-episode state_changes
- live prompt renders all-future stop lines, not next-episode only
- no forbidden Stage 2 / Stage 4 / schema changes are introduced

Required verification:
- python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py
- pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q
- pytest tests/test_blueprint_patch_mode.py -q
- pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q
- python scripts/check_utf8_hygiene.py <all touched code/test/doc files>
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize changes by tranche
- list exact verification results
- list residual risks
- explicitly confirm that Stage 2 density/allocation and `genre_ext` were not opened
- do not claim closure; Codex will audit and close it
```
