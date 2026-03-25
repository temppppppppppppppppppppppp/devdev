# Stage3 NPC + Capital Carry-Forward Wave Execution SSOT

Date: 2026-03-24
Status: closed (closure-audited)
Document Type: execution SSOT
Canonical Path: `docs/2026-03-24/stage3-npc-capital-carryforward-wave-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-npc-capital-carryforward-wave-execution-ssot.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: live-run logs/db plus residual survey docs; temp queue empty before this SSOT`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-merge-audit.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t3-stage3-blueprint-truth.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t4-stage4-manuscript-expansion.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t5-validator-retry-semantics.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t6-capital-time-item-diff-ledger.md`
Evidence Artifacts:
- `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_02/patched_after_fix__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0004/attempt_01/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt`
- `projects/0324_00_/logs/episode_production.jsonl`
Side-Effect Coverage:
- Stage 3 fact-lock packet shaping
- Stage 3 capital continuity packet shaping
- Stage 3 Python prevalidation and quality-risk surfacing
- no DB schema, JSONL schema, artifact naming, or Stage 4 retry redesign in this wave

## 1. Intent

Stop Stage 3 from reintroducing stale NPC/institution truth and phantom available-capital state into EP5-EP7 blueprints.

This wave is bounded to Stage 3 carry-forward truth.

It is not:

- a Stage 4 retry redesign
- a sink reconciliation wave
- a Stage 2 density / ep_count wave

## 2. Baseline Facts

- EP3 accepted truth establishes `HMC투자증권` / `VVIP PB센터` authority.
- EP6 and EP7 blueprints drift that authority to `한미증권 본사 VVIP 프라이빗 룸`.
- EP5 blueprint starts from stale capital (`19억 3천만 원`) instead of the accepted EP4 baseline (`19억 원` after deduction).
- EP6 and EP7 blueprints still expose `19억 3천만 원이 예치된 계좌 내역` even after the capital should already be deployed.
- Stage 4 often amplifies those wrong inputs, but the first durable contradiction is already present in Stage 3.

## 3. Scope

Included:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage3_orchestrator.py`
- targeted tests for this wave

Excluded:
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- console / JSONL / DB sink reconciliation
- Stage 2 arc authoring or density / ep_count redesign
- DB schema, JSONL schema, artifact naming, or world-state schema changes

## 4. Pass 1. Inventory Summary

Primary owners:

- `blueprint_constraint_compiler.py`
  - fact-lock and capital-lock packet generation
- `blueprint_ensemble.py`
  - constraint rendering priority into the generator prompt
- `unified_blueprint_validator.py`
  - bounded Python prevalidation before Director compare
- `stage3_orchestrator.py`
  - Stage 3 runtime assembly and optional authority packet injection

## 5. Pass 2. Semantic Classification

Class A. NPC / institution carry-forward blind spot
- current fact-lock packet does not explicitly anchor NPC affiliation / institution truth
- Stage 3 can therefore rewrite institution or venue authority even when prior accepted canon settled it

Class B. Capital carry-forward blind spot
- current capital continuity packet relies too heavily on structured fields that the live blueprint surfaces do not consistently populate
- stale free-text equipment / status strings can bypass the packet and reappear as phantom available capital

Class C. Prevalidation blind spot
- current prevalidation does not reliably catch:
  - institution-name drift against prior accepted canon
  - phantom available-capital drift after capital was already committed

## 6. Execution Tranches

### Tranche A. NPC / Institution Fact-Lock Augmentation

Owners:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`

Problem:
- accepted prior canon can settle an institution / venue / affiliation surface
- current Stage 3 fact-lock packet does not surface that as a compact high-priority anchor

Required implementation shape:
- extend the Stage 3 fact-lock packet with one bounded NPC / institution anchor lane
- source only from already-available accepted authority:
  - previous accepted manuscript tail / digest
  - previous blueprint ending state
  - already-present continuity / registry surfaces if available in Stage 3 runtime
- keep it compact:
  - character name
  - institution or venue anchor
  - why it matters if already settled

Guardrails:
- do not build a new repo-wide NPC ontology
- do not move full Episode Bible logic into Stage 3
- keep the packet to high-value anchors only

Acceptance criteria:
- EP6/EP7 class institution drift becomes visible as a Stage 3 authority violation before Stage 4

### Tranche B. Capital Carry-Forward Fallback Extraction

Owners:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_ensemble.py`

Problem:
- the current capital continuity packet is too dependent on structured `ending_state` keys
- the real blueprints often store the relevant money-state in free-text `equipment`, `protagonist_status`, or ending prose

Required implementation shape:
- keep the existing structured packet path
- add one bounded fallback extraction path from already-accepted prior authority:
  - free-text equipment strings
  - protagonist status text
  - compact accepted-manuscript tail cues
- extract only the fields needed for the current failure family:
  - accepted starting capital class
  - already-deployed vs still-available state
  - already-paid deductions when explicitly established

Guardrails:
- do not add new DB schema or world-state schema
- do not attempt a full financial ledger redesign
- if a value cannot be extracted with bounded confidence, omit it instead of guessing

Acceptance criteria:
- EP5 stale `19억 3천만 원` carry-forward is no longer allowed through Stage 3
- EP6/EP7 phantom available-capital surfaces are narrowed or blocked before Stage 4 sees them

### Tranche C. Stage 3 Prevalidation Drift Checks

Owners:
- `modules/domain/agents/unified_blueprint_validator.py`

Problem:
- current prevalidation still lets the actual EP5-EP7 residual family through

Required implementation shape:
- add bounded checks for:
  - institution / affiliation drift against the Stage 3 fact-lock packet
  - phantom available-capital drift against the capital continuity packet
  - repeated stale capital phrases when prior accepted state already marks capital as deployed
- severity rules:
  - hard contradiction -> `CRITICAL`
  - stale / enabling gap -> `MAJOR`

Guardrails:
- do not attempt full semantic comparison of whole manuscripts
- stay on explicit anchor checks only
- do not change Director verdict contracts or scoring payload shapes

Acceptance criteria:
- EP5-, EP6-, and EP7-class drifts become visible in Stage 3 prevalidation
- Stage 3 quality-risk reflects the real residual axes, not only generic structure/start-location issues

## 7. Acceptance Criteria

- Stage 3 fact-lock packet gains bounded NPC / institution anchors
- Stage 3 capital continuity packet can extract the needed carry-forward truth from the live free-text surfaces when structured keys are absent
- Stage 3 prevalidation catches institution drift and phantom available-capital drift before Director compare
- no Stage 4 retry redesign, sink reconciliation work, Stage 2 redesign, DB schema change, or artifact naming change is opened

## 8. Verification Plan

- `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py modules/core/stage3_orchestrator.py`
- `pytest tests/test_stage3_orchestrator.py -q`
- `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
- `pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q`
- `pytest tests/test_blueprint_patch_mode.py -q`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`
- `python scripts/check_utf8_hygiene.py <all touched code/test/doc files>`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 9. Guardrails

- Re-audit this canonical SSOT against the live workspace before patching.
- Keep the wave bounded to Stage 3 fact-lock augmentation, capital carry-forward fallback extraction, and Python prevalidation.
- Do not reopen Stage 4 or sink reconciliation in this wave.
- Do not change DB schema, JSONL schema, artifact naming, or persistence contracts.
- If the patch requires broader narrative-state schema redesign, stop and split that into a later wave.

## 10. Temp Queue Notes

- temp mirror path: `docs/temp/stage3-npc-capital-carryforward-wave-execution-ssot.md`
- queue rule: this mirror becomes the only active temp execution item if promoted
- cleanup condition: remove the temp mirror only after realization plus closure audit

## 11. Opus Execution Order

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-merge-audit.md
5. docs/temp/stage3-npc-capital-carryforward-wave-execution-ssot.md
6. docs/2026-03-24/stage3-npc-capital-carryforward-wave-execution-ssot.md
7. docs/2026-03-24/console.txt

Task:
Implement the bounded Stage 3 NPC + capital carry-forward wave.

Primary goal:
Stop EP5-EP7 blueprint drift by fixing only:
- NPC / institution fact-lock carry-forward
- capital carry-forward fallback extraction
- Stage 3 prevalidation for institution drift and phantom available-capital drift

Hard constraints:
- Follow the execution SSOT exactly.
- Re-audit the canonical execution SSOT against the live workspace before patching.
- Keep the wave bounded to Stage 3.
- Do not open Stage 4 retry redesign.
- Do not open sink reconciliation / observability redesign.
- Do not open Stage 2 density or ep_count redesign.
- Do not change DB schema, JSONL schema, or artifact naming.
- Workspace is dirty. Do not revert unrelated edits.
- Use apply_patch for edits.
- Respect UTF-8 hygiene on all touched files.
- Do not close the execution SSOT; Codex will audit and close it.

Implementation targets:
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/domain/agents/blueprint_ensemble.py
- modules/domain/agents/unified_blueprint_validator.py
- modules/core/stage3_orchestrator.py
- targeted tests for this wave

Acceptance targets:
- EP6/EP7 institution drift is no longer allowed through Stage 3
- EP5 stale-capital carry-forward is no longer allowed through Stage 3
- EP6/EP7 phantom available-capital surfaces are narrowed or blocked before Stage 4
- no forbidden Stage 4 / sink / schema changes are introduced

Required verification:
- python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py modules/core/stage3_orchestrator.py
- pytest tests/test_stage3_orchestrator.py -q
- pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q
- pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q
- pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q
- pytest tests/test_blueprint_patch_mode.py -q
- pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q
- python scripts/check_utf8_hygiene.py <all touched code/test/doc files>
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize changes by tranche
- list exact verification results
- list residual risks
- explicitly confirm that Stage 4 and sink reconciliation were not opened
- do not claim closure; Codex will audit and close it
```

## 12. Closure Audit

Closure Date: 2026-03-25
Closure Status: closed (closure-audited)

Verification rerun by Codex:
- `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py modules/core/stage3_orchestrator.py`
- `pytest tests/test_stage3_orchestrator.py -q` -> `78 passed`
- `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q` -> `25 passed`
- `pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q` -> `29 passed`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q` -> `39 passed`
- `pytest tests/test_blueprint_patch_mode.py -q` -> `43 passed`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q` -> `23 passed`
- `ruff check modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py tests/test_stage3_blueprint_state_precision_guardrail.py tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `python scripts/check_utf8_hygiene.py modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py tests/test_stage3_blueprint_state_precision_guardrail.py tests/test_stage3_npc_capital_carryforward_guardrail.py docs/2026-03-24/stage3-npc-capital-carryforward-wave-execution-ssot.md docs/temp/stage3-npc-capital-carryforward-wave-execution-ssot.md`

Closure notes:
- Closure audit found three bounded hygiene blockers not reflected in the implementation summary: one redundant `f` prefix, one extra blank line in the new test file, and one ambiguous loop variable name. Those were corrected without widening scope.
- Stage 4 retry redesign was not opened.
- Sink reconciliation / observability redesign was not opened.
- DB schema, JSONL schema, and artifact naming remain unchanged.

Residual risks:
- Institution suffix matching is intentionally bounded; non-standard institution names may still evade the fact-lock path.
- Capital fallback extraction still relies on bounded free-text patterns rather than a full ledger model.
- Fresh live run validation after this Stage 3 wave has not been rerun yet, so operational suppression of EP5-EP7 residuals remains verified by tests, not by a new live run.
