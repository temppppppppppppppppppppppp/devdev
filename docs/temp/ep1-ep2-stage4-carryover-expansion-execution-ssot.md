# EP1 -> EP2 Stage4 Carryover Expansion Execution SSOT

Date: 2026-03-24
Status: execution-ready
Canonical Path: `docs/2026-03-24/ep1-ep2-stage4-carryover-expansion-execution-ssot.md`
Temp Mirror Path: `docs/temp/ep1-ep2-stage4-carryover-expansion-execution-ssot.md`
Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
Baseline Dirty Summary: `dirty workspace; active temp queue empty before this SSOT; many unrelated tracked edits/deletions already present outside this wave`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-24/ep1-ep2-stage4-carryover-expansion-survey-report.md`
- `docs/2026-03-24/ep1-ep2-handoff-residual-opus-survey-report.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
Evidence Artifacts:
- `projects/00_0324_2/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_04/selected_before_fix__A.txt`
- `projects/00_0324_2/logs/episode_production.jsonl`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_interview_round.py`
Side-Effect Coverage:
- Stage 4 writer prompt assembly
- previous-attempt retry snapshot shaping
- retry-budget axes / rewrite-vs-patch steering
- Stage 4 JSONL / session logging continuity
- no DB schema or artifact naming change allowed in this wave

## 1. Intent

Reduce the ep2-style Stage 4 retry spiral where:

- the writer invents covert operational infrastructure not yet grounded on page,
- post-select correctly rejects it,
- but retry guidance still preserves too much of the offending expansion and spends rounds on local repairs.

This wave is not a Stage 2 or Stage 3 redesign. It is a bounded Stage 4 handoff and retry-integrity wave.

## 2. Baseline Facts

- The old ep1 overconsumption leak was materially reduced by the earlier closed waves.
- The fresh blocker in `00_0324_2` is downstream:
  - Stage 4 adds burner-phone / offshore infrastructure not stored in the ep2 blueprint.
  - Stage 4 also replays already-computed WTI planning too aggressively.
  - Retry guidance preserves the action-oriented invention as a strength while patching local continuity details.
- The saved ep2 blueprint is still an amplifier:
  - it overweights liquidation planning and WTI timing,
  - but it does not explicitly store the full covert network that later appears in Stage 4 prose.

## 3. Scope

Included:
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_reject_runtime.py`
- targeted tests for this wave

Excluded:
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `selected -> validation_result` normalization redesign unless live mismatch evidence appears during implementation re-audit
- Stage 2 density / allocation / ep_count redesign
- Director scoring model redesign
- post-select validator rule redesign
- DB schema, JSONL schema, artifact naming, or persistence contract changes
- global genre policy cleanup

## 4. Pass 1. Inventory Summary

Primary hotspots:

- prompt packing:
  - `chief_writer_context.py`
  - `chief_writer_prompts.py`
- carryover packet substrate:
  - `chief_writer_context_packets.py`
- reject / retry shaping:
  - `stage4_reject_runtime.py`
  - `stage4_interview_round.py`

Runtime split:

- production runtime only
- no script-only or README-only realization in this wave
- tests are targeted support, not the delivery surface

## 5. Pass 2. Semantic Classification

Class A. Prompt authority hierarchy gap
- structured scene contract and long-form integrated prose currently share the same Step 1 authority lane

Class B. Carryover ceiling gap
- Stage 4 sees previous-episode material, but not through a compact "do not invent beyond these already-established assets/capabilities" lane

Class C. Reject-budget hygiene gap
- post-select hard conflicts still allow retry states that preserve or even praise the conflicting invention and keep patch-biased retry budgets alive

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage 4 attempt artifacts under `projects/*/logs/artifacts/stage4/...`
  - must preserve current artifact naming
- DB / schema / transaction boundaries:
  - existing attempt logging only
  - schema changes forbidden
- JSONL / log / audit sinks:
  - `episode_production.jsonl`
  - session decision logging
  - retry pathology logging
  - payload shape must remain compatible
- console / UI / operator output:
  - Director / reject feedback text will change in emphasis if retry guidance is tightened
  - no intentional log removal
- rollback / recovery / retry:
  - this is a primary surface; fix_scope, retry_budget_axes, and previous_attempt shaping are in scope
- cache / global state:
  - previous_attempt chain
  - advisory summaries
  - consecutive empty patch counters
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

The wave uses one bounded Stage 4 contract split:

1. `scene_breakdown`, opening-anchor, immutable facts, and prior-manuscript carryover remain authoritative.
2. `integrated_scenario` remains available, but is explicitly downgraded to advisory narrative draft material.
3. Retry guidance must treat post-select hard conflicts as conflict-first, not praise-first.

Python still only collects and formats the relevant surfaces. It does not make final story judgments. The writer LLM remains free inside the narrowed contract.

## 8. Execution Tranches

### Tranche A. Blueprint Hierarchy Separation

Owners:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_prompts.py`

Problem:

- `_extract_blueprint_sections()` appends `integrated_scenario` directly into the same prompt slot as structured `scene_breakdown`.
- The final writer prompt does not state that structured scene data and carryover contracts outrank long-form integrated prose.
- `stage4_interview_round.py` passes the raw blueprint into both WritingDirective generation and common writer kwargs, so the same overreaching prose is reused before the prompt is even built.

Required implementation shape:

- add one bounded `writer_blueprint` normalization seam in Stage 4 before WritingDirective generation and common writer kwargs are built
- keep `scene_breakdown` and `integrated_scenario` as separate rendered surfaces
- label `integrated_scenario` as advisory draft, not equal-authority scene contract
- add one explicit precedence contract:
  - opening anchor
  - immutable facts
  - prev-digest / prior-manuscript facts
  - structured scene breakdown
  override advisory integrated prose if they conflict

Acceptance criteria:

- Stage 4 no longer feeds the raw unsanitized blueprint prose into all writer-facing subpaths
- the writer prompt no longer presents integrated prose as coequal with the structured scene contract
- blueprint scene goals and anchors remain fully available
- no Stage 3 contract or artifact shape changes are introduced

### Tranche B. Stage4 Carryover Ceiling Packet

Owners:

- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_context.py`

Problem:

- current carryover surfaces do not compactly state the protagonist's already-established operational ceiling
- the writer can still invent hidden phone / broker / offshore scaffolding while technically following a planning-heavy investment blueprint

Required implementation shape:

- add one bounded carryover packet for Stage 4 only
- derive it from already-available authorities such as:
  - previous manuscript
  - previous digest
  - world-state / existing packet inputs when available
- make the packet state explicit things like:
  - opening body-position / key item state when explicitly available
  - already-completed planning facts that should not be replayed as fresh discovery
  - no-new-infrastructure rule for covert tools/contacts/entities absent prior or structured current authority

Guardrail:

- do not invent a global ontology of "all possible finance infrastructure"
- keep the packet compact and derived-only
- prefer explicit "not yet established on page" wording over Python auto-judging genre realism

Acceptance criteria:

- Stage 4 prompt explicitly warns against introducing covert operational assets or offshore structures that are not established in prior/current authority surfaces
- Stage 4 prompt explicitly warns against replaying already-finished planning math as if newly completed
- existing positive carryover surfaces remain available

### Tranche C. Post-Select Retry Hygiene

Owners:

- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_interview_round.py`

Problem:

- after post-select hard conflicts, retry state can still preserve offending invented infrastructure as something not to regress
- retry budgeting can stay patch-biased, including early `post_select_conflict` force-patch routing, even when the remaining problem is not local-only

Required implementation shape:

- when a reject is driven by post-select continuity/history/IFC hard conflict:
  - do not preserve praise or do-not-regress signals that directly depend on the conflicted invention
  - prefer rewrite/regenerate-oriented retry budgeting over `patch_revision` or forced early patch when the conflict is not narrowly local
- keep local patch mode available only when the surviving defect is truly local-only

Acceptance criteria:

- retries after post-select hard conflicts no longer carry forward the offending invented infrastructure as a protected strength
- retry budgeting is widened when the conflict family is broader than a local phrase/sentence repair, including removal of unconditional early patch bias for those cases
- JSONL / DB payload shapes remain unchanged

## 9. Acceptance Criteria

- Stage 4 prompt hierarchy clearly separates authoritative structured blueprint/carryover surfaces from advisory integrated prose
- Stage 4 prompt contains a bounded carryover ceiling against new covert infrastructure and repeated completed-planning replay
- retries after post-select hard conflicts are conflict-first, no longer preserve the offending invention as a do-not-regress strength, and do not default to early patch bias unless the defect is truly local-only
- no Stage 2 / Stage 3 / Director / DB schema redesign is opened

## 10. Verification Plan

- `python -m py_compile modules/core/stage4_interview_round.py modules/domain/agents/chief_writer_context.py modules/domain/agents/chief_writer_context_packets.py modules/domain/agents/chief_writer_prompts.py modules/core/stage4_reject_runtime.py`
- `pytest tests/test_chief_writer_context.py -q`
- `pytest tests/test_stage4_interview_round.py -q`
- `pytest tests/test_stage4_immutable_fact_contract.py -q`
- `pytest tests/test_stage4_handoff_carryover_guardrail.py -q`
- `python scripts/check_utf8_hygiene.py <all touched code/test/doc files>`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails

- Follow this execution SSOT exactly.
- Re-audit the canonical execution SSOT against the live workspace before patching; shrink scope if any tranche is already resolved.
- Keep the wave bounded to Stage 4 prompt hierarchy, carryover packeting, and retry hygiene.
- Do not open Stage 2 density/allocation or Stage 3 blueprint redesign here.
- Do not change DB schema, JSONL schema, artifact naming, or director selection payload shape.
- Preserve the rule that Python collects/contracts and the writer LLM decides narrative realization inside those bounds.
- Workspace is dirty. Do not revert unrelated edits.
- Do not close this execution SSOT from the implementation terminal; Codex performs closure audit.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: remove the temp mirror only after realization plus closure audit
- roadmap dependency: none if this remains the only temp execution item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Opus Execution Order

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-24/ep1-ep2-stage4-carryover-expansion-survey-report.md
5. docs/temp/ep1-ep2-stage4-carryover-expansion-execution-ssot.md
6. docs/2026-03-24/ep1-ep2-stage4-carryover-expansion-execution-ssot.md
7. docs/2026-03-24/console.txt
8. docs/2026-03-24/현상황요약.txt

Task:
Implement the bounded Stage 4 carryover-expansion fix wave.

Primary goal:
Stop ep2-style Stage 4 invention of covert infrastructure and repeated completed-planning replay from surviving across retries.

Hard constraints:
- Follow the execution SSOT exactly.
- Re-audit the canonical execution SSOT against the live workspace before patching.
- Keep the wave bounded to:
  - Stage 4 blueprint hierarchy separation
  - Stage 4 carryover ceiling packet
  - post-select retry hygiene
- Do not open Stage 2 density/allocation redesign.
- Do not open Stage 3 blueprint generation redesign.
- Do not redesign Director scoring.
- Do not change DB schema, JSONL schema, or artifact naming.
- Preserve Python-as-collector / LLM-as-judge.
- Workspace is dirty. Do not revert unrelated edits.
- Use apply_patch for edits.
- Respect UTF-8 hygiene on all touched files.
- Do not close the execution SSOT; Codex will audit and close it.

Implementation targets:
- modules/domain/agents/chief_writer_context.py
- modules/domain/agents/chief_writer_context_packets.py
- modules/domain/agents/chief_writer_prompts.py
- modules/core/stage4_interview_round.py
- modules/core/stage4_reject_runtime.py
- targeted tests for this wave

Acceptance targets:
- integrated_scenario no longer acts as coequal blueprint authority in the writer prompt
- Stage 4 normalizes a writer-facing blueprint before WritingDirective / prompt assembly reuse
- Stage 4 gets a compact no-new-infrastructure carryover ceiling grounded in prior/current authority
- retries after post-select hard conflicts no longer preserve the conflicting invention as a protected strength
- no forbidden Stage 2 / Stage 3 / Director / schema changes are introduced

Required verification:
- python -m py_compile modules/core/stage4_interview_round.py modules/domain/agents/chief_writer_context.py modules/domain/agents/chief_writer_context_packets.py modules/domain/agents/chief_writer_prompts.py modules/core/stage4_reject_runtime.py
- pytest tests/test_chief_writer_context.py -q
- pytest tests/test_stage4_interview_round.py -q
- pytest tests/test_stage4_immutable_fact_contract.py -q
- pytest tests/test_stage4_handoff_carryover_guardrail.py -q
- python scripts/check_utf8_hygiene.py <all touched code/test/doc files>
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize changes by tranche
- list exact verification results
- list residual risks
- explicitly confirm that Stage 2, Stage 3 generation, and Director redesign were not opened
- do not claim closure; Codex will audit and close it
```
