# Stage3 Blueprint State-Precision Reconciliation Wave Execution SSOT

Date: 2026-03-24
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-24/stage3-blueprint-state-precision-reconciliation-wave-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-blueprint-state-precision-reconciliation-wave-execution-ssot.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: live-run logs/db plus residual survey docs; prior Stage4 temp mirror closure pending`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-merge-audit.md`
- `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth.md`
- `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority.md`
- `docs/2026-03-24/opus-live-run-residual/t6-stage4-carryover-consumption.md`
- `docs/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger.md`
- `docs/2026-03-24/opus-live-run-residual/t10-cleared-non-culprits.md`
Evidence Artifacts:
- `projects/0324_00_/logs/episode_production.jsonl`
- `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0004/attempt_01/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt`
Side-Effect Coverage:
- Stage 3 blueprint prompt assembly
- Stage 3 Python prevalidation and quality-risk surfacing
- Stage 3 Director compare candidate metadata
- no DB schema, JSONL schema, artifact naming, or Stage 4 retry redesign in this wave

## 1. Intent

Prevent Stage 3 from emitting blueprint facts that contradict already-accepted manuscript canon or blur capital/deployment state enough that Stage 4 must repair them later.

This wave is bounded to Stage 3 generation and Stage 3 prevalidation. It is not a Stage 2 redesign and not another Stage 4 carryover wave.

## 2. Baseline Facts

- The prior Stage 4 carryover-expansion wave materially reduced the old covert-infrastructure seam and broad carryover relapse.
- The fresh EP1-EP8 live run now fails mainly when Stage 3 rewrites already-settled facts into new blueprint authority.
- Direct examples:
  - EP2 blueprint flips trust provenance away from EP1 canon.
  - EP3 blueprint stores the notebook in a drawer instead of the already-established safe.
  - EP6 blueprint reopens capital/deployment state after EP5 already committed the position.
  - EP7 blueprint ending hook contains `18년 전` temporal phrasing that should have been blocked before Stage 4.

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
- `modules/domain/agents/chief_writer_context.py`
- Stage 2 arc authoring or density/ep_count redesign
- DB schema, JSONL schema, artifact naming, or world-state schema changes
- broad finance ontology or repo-wide contract renaming

## 4. Pass 1. Inventory Summary

Primary owners:

- `blueprint_constraint_compiler.py`
  - builds Stage 3 constraint blocks
  - already owns continuity, inherited state, stop-line, state-change summaries
- `blueprint_ensemble.py`
  - builds `arc_focus`, `constraints_str`, `prev_info`
  - decides how prior manuscript and prior blueprint context are surfaced to the generator
- `unified_blueprint_validator.py`
  - already owns Python prevalidation before Director compare
- `stage3_orchestrator.py`
  - owns Stage 3 runtime assembly and can inject one bounded Stage 3 fact packet if needed

## 5. Pass 2. Semantic Classification

Class A. Authority-priority gap
- previous accepted manuscript truth is present, but not surfaced as an explicit high-authority fact-lock lane
- arc detail and prior manuscript detail can disagree without a hard precedence rule

Class B. Capital/deployment continuity gap
- investment-state facts are passed around as loose prose, not as compact continuity anchors
- Stage 3 can therefore emit `still available`, `freshly deploy`, or `전액` statements that conflict with the previous accepted episode

Class C. Prevalidation blind spot
- current Python prevalidation checks structure, fidelity, stop-line, and start-location continuity
- it does not currently catch:
  - provenance drift
  - item storage/state drift
  - temporal-deictic hook drift
  - capital-state contradiction against previous accepted state

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage 3 blueprint artifacts under `projects/*/logs/artifacts/stage3/...`
  - artifact naming must remain unchanged
- DB / JSONL / audit sinks:
  - Stage 3 attempt metadata, quality-risk, and advisory payloads may change in content but not shape
- console / operator output:
  - Stage 3 Python warnings and quality-risk reasons will gain new precision warnings
- rollback / retry:
  - more candidate blueprints may be rejected before Director compare when authority drift is detected
- cache / global state:
  - prior manuscript excerpts, previous blueprint, and derived fact-lock summaries
- config / env:
  - not applicable

## 7. Realization Architecture

The wave has one bounded goal: **make accepted prior canon outrank arc pressure when Stage 3 writes the next blueprint**.

The implementation should prefer:

1. compact fact locks over more raw prose
2. prevalidation rejection of wrong blueprint authority over Stage 4 repair
3. investment-state continuity summaries over broad schema redesign

Python still only collects and formats the lock data and validation evidence. Final narrative judgment remains with the LLM inside the tightened Stage 3 boundary.

## 8. Execution Tranches

### Tranche A. Stage3 Fact-Lock Packet

Owners:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/stage3_orchestrator.py`

Problem:
- previous accepted manuscript state is buried inside long `prev_info` / manuscript text
- no compact high-priority packet says “these facts are already settled; do not rewrite them”

Required implementation shape:
- add one bounded Stage 3 fact-lock summary built from already-available authorities:
  - previous accepted manuscript tail / digest
  - previous blueprint ending state
  - prior accepted item/location anchors when explicitly known
- surface it ahead of or alongside existing constraints as an explicit higher-priority contract
- include only compact high-value fields:
  - provenance / source-of-funds anchors
  - key item location/state anchors
  - immediate time/day carryover anchors
  - already-completed action/planning anchors

Guardrails:
- do not add a repo-wide fact ontology
- do not move Stage 4 carryover logic into Stage 3 wholesale
- keep the packet compact and derived only from existing authority

Acceptance criteria:
- EP2-type provenance flips are blocked at Stage 3 input authority level
- EP3-type item-location drift is explicitly represented as a fact lock before generation

### Tranche B. Capital-State Continuity Packet

Owners:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_ensemble.py`

Problem:
- investment-state continuity is currently loose prose
- Stage 3 can reopen already-committed cash or position state as if it were still undecided

Required implementation shape:
- add one compact Stage 3 capital continuity summary for investment runs, derived from accepted prior authority
- keep it bounded to fields the current run actually needs:
  - entering balance class
  - deployed vs available status
  - pending expenditure / already-paid expenditure
  - active position status when explicitly established
- render it as a contract lane, not a new DB schema

Guardrails:
- do not redesign the whole financial ledger subsystem
- do not add new persistence tables or JSONL shapes
- if a field cannot be derived cleanly, omit it instead of guessing

Acceptance criteria:
- EP6-type “already deployed but still freshly available” contradictions are no longer allowed through Stage 3
- EP5/EP6 money-state language becomes narrower and less ambiguous before Stage 4 sees it

### Tranche C. Blueprint Prevalidation Fact Reconciliation

Owners:
- `modules/domain/agents/unified_blueprint_validator.py`

Problem:
- current Python prevalidation does not catch the actual residual conflict family

Required implementation shape:
- extend Python prevalidation with bounded checks for:
  - provenance drift against prior accepted fact lock
  - item storage/state drift against prior accepted fact lock
  - capital/deployment contradiction against prior accepted continuity packet
  - temporal-deictic ending-hook drift in future-memory contexts (`18년 전` class errors)
- mark these as prevalidation issues before Director compare
- use severity boundedly:
  - hard contradiction -> `CRITICAL`
  - stale/ambiguous enabling gap -> `MAJOR`

Guardrails:
- do not attempt full semantic comparison of whole manuscripts
- stay on explicit anchor checks only
- do not change Director verdict contracts or scoring payload shapes

Acceptance criteria:
- EP2-, EP3-, and EP7-class defects become visible in Stage 3 prevalidation
- Stage 3 quality-risk now reflects the real residual axes rather than only structure/start-location issues

## 9. Acceptance Criteria

- Stage 3 gains an explicit fact-lock lane for previously settled facts
- Stage 3 gains a bounded capital continuity lane for investment-state carryover
- Python prevalidation catches provenance, item-state, capital-state, and temporal-deictic blueprint drift before Director compare
- no Stage 2 redesign, Stage 4 retry redesign, DB schema change, or artifact naming change is opened

## 10. Verification Plan

- `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py modules/core/stage3_orchestrator.py`
- `pytest tests/test_stage3_orchestrator.py -q`
- `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
- `pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q`
- `pytest tests/test_blueprint_patch_mode.py -q`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q`
- `python scripts/check_utf8_hygiene.py <all touched code/test/doc files>`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails

- Re-audit this canonical SSOT against the live workspace before patching.
- Keep the wave bounded to Stage 3 authority prioritization, continuity packet shaping, and Python prevalidation.
- Do not reopen Stage 2 density/allocation or another Stage 4 carryover wave here.
- Do not change DB schema, JSONL schema, artifact naming, or persistence contracts.
- Do not promote speculative arc truth over already-accepted manuscript truth for settled facts.
- If a prospective patch requires broader schema redesign, stop and split that into a later wave instead of inflating this one.

## 12. Closure Audit Note

Closure audit completed on 2026-03-24 after bounded code review and verification of the implemented Stage 3 wave.

Closure basis:

- Fact-lock and capital-continuity packets landed in:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/blueprint_ensemble.py`
- Stage 3 prevalidation reconciliation checks landed in:
  - `modules/domain/agents/unified_blueprint_validator.py`
- The bounded verification set passed:
  - `python -m py_compile modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py modules/core/stage3_orchestrator.py`
  - `pytest tests/test_stage3_orchestrator.py -q`
  - `pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
  - `pytest tests/test_stage2_stage3_semantic_carryover_guardrail.py -q`
  - `pytest tests/test_blueprint_patch_mode.py -q`
  - `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q`
  - `ruff check` on touched production/test files
  - `python scripts/check_utf8_hygiene.py ...`
  - `python scripts/sync_temp_queue_state.py`
  - `python scripts/ops_validator.py`

Closure interpretation:

- this execution wave is considered realized and closure-worthy
- the targeted residual seam moved from survey state into implemented Stage 3 guardrails
- no Stage 2 redesign, Stage 4 retry redesign, DB schema change, or artifact naming change was opened

Residual note:

- no fresh post-patch live run has been executed yet
- the next operator action should be a fresh live run to confirm that EP2/EP3/EP6/EP7 class defects are now intercepted or narrowed in practice
