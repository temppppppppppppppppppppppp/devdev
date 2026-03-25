# Stage3 Blueprint Clarity / Density Wave1 Execution SSOT

Date: 2026-03-25
Status: closed (closure-audited)
Document Type: execution SSOT
Canonical Path: `docs/2026-03-25/stage3-blueprint-clarity-density-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-blueprint-clarity-density-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: canary_0325 live artifacts/logs, prior closed Stage3 docs, 2026-03-25 survey docs, temp queue empty before promotion`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-25/stage3-partial-canary-3terminal-merge-audit.md`
- `docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md`
- `docs/2026-03-25/opus-bp-clarity-density/t2-stage3-authority-schema.md`
- `docs/2026-03-25/opus-bp-clarity-density/t3-stage3-prevalidation-coverage.md`
Evidence Artifacts:
- `projects/canary_0325/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/canary_0325/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__action_focused.json`
- `projects/canary_0325/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/canary_0325/logs/runtime_audit.jsonl`
- `projects/canary_0325/logs/session/ui_events.jsonl`
Side-Effect Coverage:
- Stage 3 prompt constraint formatting and prompt template wording
- Stage 3 Python prevalidation issues and quality-risk surfacing
- Stage 3 candidate pool / score effects before Director compare
- no Stage 2 schema change, no Stage 4 redesign, no DB/JSONL schema or artifact naming changes in this wave

## 1. Intent

Use the clean Stage 3 partial-canary baseline to improve blueprint clarity/density without reopening the older residual-family fixes.

This wave is not another bug-family containment wave. It is a bounded quality-up wave.

## 2. Baseline Facts

- The partial canary shows the prior Stage 3 culprit family is suppressed across EP1-EP9.
- The remaining blueprint quality limiters are structural and moderate, not catastrophic:
  - authority bands are present in code but flattened in the prompt
  - prevalidation checks structure and contradiction, but does not measure scene specificity or scenario density well
- Stage 2 upstream specificity is not clean enough to call "solved," but it is not the highest-ROI next wave.
- Prompt self-audit is useful, but current evidence supports treating it as a secondary amplifier rather than a primary Wave 1 scope item.

## 3. Scope

Included:
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `config/prompts/ensemble.yaml`
- targeted tests for this wave

Excluded:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage3_orchestrator.py`
- Stage 2 arc schema or prompt redesign
- prompt-level self-audit rollout
- Director retry-feedback redesign
- Stage 4 runtime changes
- DB schema, JSONL schema, artifact naming, or world-state schema changes

## 4. Pass 1. Inventory Summary

Primary owners:

- `blueprint_ensemble.py`
  - assembles the visible authority presentation the blueprint generator sees
  - formats `must_focus`, `stop_line`, continuity, inherited-state, and advisory surfaces
- `ensemble.yaml`
  - carries the user-visible constraint block wording and sequencing inside the blueprint generation prompt
- `unified_blueprint_validator.py`
  - owns Python prevalidation before Director compare
  - currently sees structure and factual contradiction better than clarity/density

## 5. Pass 2. Semantic Classification

Class A. Authority-presentation limiter
- the system has meaningful authority bands
- the prompt makes too many of them look coequal
- the LLM must therefore infer override rules that should be explicit

Class B. Density/specificity validation blind spot
- current prevalidation checks are necessary but too shallow for blueprint clarity
- scene presence is checked, but scene usefulness is not
- scenario length is checked, but scenario density is not

Class C. Deferred amplifiers
- upstream Stage 2 specificity
- self-audit prompt
- scene-level Director retry feedback

These are intentionally out of Wave 1 to preserve clean attribution.

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage 3 blueprint artifacts under `projects/*/logs/artifacts/stage3/...`
  - no artifact naming changes allowed
- DB / JSONL / audit sinks:
  - Stage 3 prevalidation issue content may change
  - quality-risk triggering frequency may change
  - payload shape must not change
- console / operator output:
  - Director-facing warning text may become more clarity/density-specific
  - operator warning visibility may increase for thin blueprints
- rollback / retry:
  - more weak blueprints may be downgraded or lose score before Director compare
- config / env:
  - prompt template text in `config/prompts/ensemble.yaml`

## 7. Realization Architecture

Wave 1 should make the blueprint generator and prevalidation layer agree on two things:

1. which Stage 3 inputs are truly hard authority
2. what counts as a thin blueprint even when it is structurally present

The implementation should prefer:

- explicit priority ordering over more raw advisory text
- bounded Python heuristics over large schema redesign
- clean canary attribution over bundling in secondary amplifiers

## 8. Execution Tranches

### Tranche A. Explicit Authority Re-Banding

Owners:
- `modules/domain/agents/blueprint_ensemble.py`
- `config/prompts/ensemble.yaml`

Problem:
- hard constraints and advisory context are visually too flat
- the LLM must guess conflict precedence even though the system already has it implicitly

Required implementation shape:
- restructure the visible constraint block into explicit bands:
  - `IMMUTABLE`
  - `HARD CONSTRAINT`
  - `EXPECTED CONTINUITY`
  - `ADVISORY`
- add a short priority preamble that states conflict resolution order
- keep `FACT-LOCK` and `CAPITAL-LOCK` at the top
- ensure `stop_line` remains clearly reject-bearing
- on degraded paths, avoid surfacing duplicated `must_focus.content` as if it were two independent authorities

Guardrails:
- do not redesign the whole blueprint schema
- do not add new runtime persistence
- do not expand the prompt with a large new advisory block

Acceptance criteria:
- the prompt makes authority precedence explicit instead of implicit
- hard constraints and advisory guidance no longer share the same visual band
- degraded-path duplication becomes narrower or absent

### Tranche B. Scene-Specificity + Scenario-Density Prevalidation

Owners:
- `modules/domain/agents/unified_blueprint_validator.py`

Problem:
- structurally valid but vague blueprints pass too easily
- Python prevalidation cannot currently distinguish "present" from "usefully specific"

Required implementation shape:
- add two bounded prevalidation check families:
  - scene-specificity check
  - scenario-density check
- keep the checks heuristic and explicit, for example:
  - too-short scene goals / summaries
  - scenes with zero or near-zero concrete action/event content
  - integrated_scenario that clears char floor but lacks enough scene coverage or concrete anchors
- surface issues through the existing prevalidation issue path
- keep quality-risk payload shape unchanged

Guardrails:
- do not attempt full semantic grading of prose
- do not replace Director judgment with Python verdict authority
- do not introduce NLP-heavy or model-dependent parsing in this wave

Acceptance criteria:
- thin scene goals/summaries are visible to prevalidation
- integrated_scenario density weakness is visible to prevalidation beyond the current raw char floor
- the new warnings remain bounded and do not require schema redesign

## 9. Deferred Follow-Ups

Explicitly deferred from Wave 1:

- prompt-level self-audit instruction
- Stage 2 `episode_details` specificity floor
- scene-level Director retry feedback
- schema tightening for scene-entry object-only enforcement

These remain valid later waves, but not part of this first clarity/density pass.

## 10. Acceptance Criteria

- Stage 3 prompt authority bands become explicit and conflict ordering is visible
- Stage 3 prevalidation can flag scene thinness and scenario density weakness through bounded heuristics
- no Stage 2 redesign, Stage 4 redesign, DB/JSONL schema change, or artifact naming change is opened
- the wave remains narrow enough for a clean post-patch canary

## 11. Verification Plan

- `python -m py_compile modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py`
- `pytest tests/test_prompt_loader.py -q`
- `pytest tests/test_tier4_ensemble_caching.py -q`
- `pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`
- `pytest tests/test_stage3_orchestrator.py -q`
- `python scripts/check_utf8_hygiene.py <all touched code/test/doc/config files>`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 12. Guardrails

- Re-audit this canonical SSOT against the live workspace before patching.
- Keep the wave bounded to Stage 3 prompt authority presentation and Stage 3 Python prevalidation.
- Do not reopen Stage 2 or Stage 4 in this wave.
- Do not change DB schema, JSONL schema, artifact naming, or persistence contracts.
- Do not bundle prompt self-audit into this wave just because it is easy; keep attribution clean.
- If implementation pressure starts pulling in schema redesign, split that into a later wave instead of inflating this one.

## 13. Temp Queue Notes

- temp mirror path: `docs/temp/stage3-blueprint-clarity-density-wave1-execution-ssot.md`
- queue rule: this mirror becomes the only active temp execution item if promoted
- cleanup condition: remove the temp mirror only after realization plus closure audit

## 14. Opus Execution Order

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-25/stage3-partial-canary-3terminal-merge-audit.md
5. docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md
6. docs/temp/stage3-blueprint-clarity-density-wave1-execution-ssot.md
7. docs/2026-03-25/stage3-blueprint-clarity-density-wave1-execution-ssot.md
8. docs/2026-03-25/pre-director-self-audit-stagewise-survey-order.md

Task:
Implement Wave 1 only of the Stage 3 blueprint clarity/density improvement.

Primary goal:
Improve blueprint clarity/density by fixing only:
- prompt authority re-banding
- scene-specificity prevalidation
- scenario-density prevalidation

Hard constraints:
- Follow the execution SSOT exactly.
- Re-audit the canonical execution SSOT against the live workspace before patching.
- Keep the wave bounded to Stage 3.
- Do not open Stage 2 redesign.
- Do not open prompt self-audit rollout in this wave.
- Do not open Stage 4 retry or Director redesign.
- Do not change DB schema, JSONL schema, or artifact naming.
- Workspace is dirty. Do not revert unrelated edits.
- Use apply_patch for edits.
- Respect UTF-8 hygiene on all touched files.
- Do not close the execution SSOT; Codex will audit and close it.

Implementation targets:
- modules/domain/agents/blueprint_ensemble.py
- modules/domain/agents/unified_blueprint_validator.py
- config/prompts/ensemble.yaml
- targeted tests for this wave

Acceptance targets:
- authority precedence is explicit in the blueprint prompt
- hard constraints and advisory surfaces no longer share one flat visual band
- thin scene goals/summaries can be flagged before Director compare
- weak scenario density can be flagged before Director compare
- no Stage 2 / Stage 4 / schema changes are introduced

Required verification:
- python -m py_compile modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py
- pytest tests/test_prompt_loader.py -q
- pytest tests/test_tier4_ensemble_caching.py -q
- pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q
- pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q
- pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q
- pytest tests/test_stage3_orchestrator.py -q
- python scripts/check_utf8_hygiene.py <all touched code/test/doc/config files>
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize changes by tranche
- list exact verification results
- list residual risks
- explicitly confirm that prompt self-audit, Stage 2 redesign, and Stage 4 redesign were not opened
- do not claim closure; Codex will audit and close it
```

## 15. Closure Audit Note

Closure audit completed on 2026-03-25 after bounded code review and verification rerun.

Closure basis:

- authority re-banding landed in:
  - `modules/domain/agents/blueprint_ensemble.py`
- scene-specificity and scenario-density prevalidation landed in:
  - `modules/domain/agents/unified_blueprint_validator.py`
- targeted regression coverage landed in:
  - `tests/test_stage3_clarity_density_wave1.py`
  - `tests/test_tier4_ensemble_caching.py`
  - `tests/test_stage2_stage3_semantic_carryover_guardrail.py`

Verification rerun by Codex:

- `python -m py_compile modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py`
- `pytest tests/test_prompt_loader.py -q` -> `29 passed`
- `pytest tests/test_tier4_ensemble_caching.py -q` -> `16 passed`
- `pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q` -> `29 passed`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q` -> `39 passed`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q` -> `23 passed`
- `pytest tests/test_stage3_orchestrator.py -q` -> `78 passed`
- `pytest tests/test_stage3_clarity_density_wave1.py -q` -> `25 passed`
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

Closure notes:

- `config/prompts/ensemble.yaml` remained untouched. This did not block closure because the authority re-banding was realized at the rendered constraint-block layer in `blueprint_ensemble.py`, which is the live authority surface the generator actually receives.
- Prompt self-audit rollout was not opened.
- Stage 2 redesign was not opened.
- Stage 4 redesign was not opened.
- DB schema, JSONL schema, and artifact naming remain unchanged.

Residual risk:

- This wave is verified by targeted tests and Stage 3 partial-canary evidence, but not yet by a fresh full post-patch Stage3->4 canary. The next operator action should be a bounded live run to confirm that the clarity/density improvements reduce weak-blueprint drift without introducing over-rejection.
