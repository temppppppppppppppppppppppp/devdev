# Per-Work Fact Contract Alignment Wave 1 Execution SSOT

Date: 2026-03-27
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-27/per-work-fact-contract-alignment-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/per-work-fact-contract-alignment-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: multi-provider runtime/provider edits, local logs/jsonl churn, narrative quarantine artifact churn, untracked 2026-03-27 survey/design docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-27/per-work-registry-need-compact-survey.md`
- `docs/2026-03-27/per-work-fact-contract-authority-compact-survey.md`
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-design-memo.md`
Evidence Artifacts:
- `modules/core/stage4_context_builder.py`
- `modules/core/stage3_orchestrator.py`
- `modules/validation/blocking_validator_entity_checks.py`
- `modules/validation/blocking_validator.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage3_orchestrator.py`
- `tests/chaos/test_dead_npc_hard_block.py`
Side-Effect Coverage: covered

## 1. Intent
- Realize the bounded `contract-only` wave recommended by the 2026-03-27 synthesis/design memo set.
- Make prompt-facing fact authority explicit without adding a new registry or persistence layer.
- Move one high-certainty contradiction earlier by adding a narrow Stage 3 dead-NPC pre-check.

## 2. Baseline Facts
- Current storage/index coverage is already sufficient across `BI`, `TR`, `FactLedger`, `WorldState`, `StateTracker`, `Entity Registry`, `Reference Anchors`, and `ImmutableFactPacket`.
- The dominant seam is not storage absence; it is that prompt-facing precedence between static seed layers and realized persisted layers is still too implicit.
- `stage4_context_builder.py` already injects canonical realized constraints into tier-0 via:
  - `WorldState.get_canonical_constraints()`
  - `FactLedger.get_canonical_summary()`
- `stage4_context_builder.py` already suppresses overlapping advisory summaries in favor of canonical layers for:
  - `dead_npc`
  - `item_state`
  - `relationship_changes`
  - `npc_injury`
  - `npc_movement`
  - `time_timeline`
  - `financial_state`
- `stage3_orchestrator.py` currently prepends world-state and fact-ledger advisories into semantic context, but does not hard-stop an obviously impossible dead-NPC active-role assignment before Stage 4.
- `blocking_validator_entity_checks.py` already owns the canonical dead-NPC resurrection/action rule at manuscript validation time.

## 3. Scope
Included:
- `modules/core/stage4_context_builder.py`
- `modules/core/stage3_orchestrator.py`
- `modules/validation/blocking_validator_entity_checks.py` only if minimal helper extraction/reuse is required
- bounded regression tests only

Excluded:
- new per-work registry or registry-like persistence layer
- `modules/core/fact_ledger.py`
- `modules/core/world_state.py`
- `modules/domain/agents/state_tracker.py`
- DB schema or persistence redesign
- BI/TR ingestion changes
- fight geography, technique usage logging, or broader under-modeled fact families
- broad Stage 3 truth-gate expansion or Stage 4 validator duplication

## 4. Pass 1. Inventory Summary
- Fact authority already spans three practical bands:
  - static seed: `BI`
  - realized persisted: `FactLedger`, `WorldState`
  - derived/advisory: `StateTracker`, extracted summaries, anchors
- The two concrete owner hotspots for this wave are:
  - Stage 4 canonical prompt assembly
  - Stage 3 blueprint-time impossibility screening
- Existing dead-NPC truth logic already exists; this wave is about timing and prompt clarity, not inventing a new rule family.
- Runtime/test split remains bounded:
  - production code: 2 primary files, 1 optional helper owner
  - tests: Stage 4 context, Stage 3 orchestrator, dead-NPC validator reuse

## 5. Pass 2. Semantic Classification
- Class A. Prompt-facing authority clarification
  - Tell the LLM, explicitly and briefly, that realized persisted layers outrank initial seed/advisory layers when they conflict.
- Class B. Early impossibility guard
  - Move the dead-NPC active-role contradiction from late Stage 4/manuscript validation into a narrow Stage 3 pre-check lane.
- Class C. Deferred field/system expansion
  - Registry introduction, new fact families, and broader persistence/modeling work remain deferred.

## 6. Side-Effect Map
- file writes / artifacts:
  - prompt assembly text changes inside Stage 4 context construction
  - Stage 3 pre-check result/advisory text if rejection or warning is emitted
  - bounded regression tests
- DB / schema / transaction boundaries:
  - not applicable; this wave does not add storage or mutate DB contracts
- JSONL / log / audit sinks:
  - no new sink family
  - existing runtime logs may gain one authority/pre-check diagnostic line
- console / UI / operator output:
  - possible narrower early rejection/advisory surfaced through existing Stage 3 operator output
  - no new UI surface
- rollback / recovery / retry:
  - no new rollback path
  - existing Stage 3 retry/replan behavior remains the boundary
- cache / global state:
  - no new cache or global singleton state
- bootstrap fallback / config-env mutation:
  - not applicable; no env/config mutation in scope

## 7. Realization Architecture
- Keep the existing authority spine intact:
  - `BI` seeds static origin facts
  - `TR` supplies planning intent
  - `FactLedger` owns realized numeric/event evolution
  - `WorldState` owns realized current state
  - derived systems remain advisory unless canonical layers are absent
- Add one short authority statement in the Stage 4 canonical block path so the LLM does not have to infer precedence.
- Add one narrow Stage 3 canonical pre-check that reuses or closely mirrors the existing dead-NPC truth rule without cloning the whole blocking validator.
- Preserve the constitutional split:
  - Stage 3 only blocks obviously impossible assignments
  - Stage 4 and later layers remain responsible for broader truth enforcement and quality judgment

## 8. Execution Tranches
1. Tranche A. Prompt-facing authority statement
   - insert a short precedence block adjacent to canonical tier-0 injection in `stage4_context_builder.py`
2. Tranche B. Stage 3 dead-NPC pre-check
   - add a narrow pre-check lane in `stage3_orchestrator.py`
   - reuse `blocking_validator_entity_checks.py` logic only if a tiny helper extraction is needed
3. Tranche C. Bounded regression coverage
   - extend existing Stage 4 and Stage 3 tests
   - add one minimal dead-NPC pre-check regression only if existing files cannot host it cleanly

## 9. Acceptance Criteria
- The Stage 4 prompt explicitly states that realized persisted layers outrank seed/advisory layers when they conflict.
- The authority statement stays short, declarative, and local to canonical constraint injection; it must not become a long taxonomy dump.
- The statement explicitly covers at least:
  - `FactLedger numbers > BI seed numbers`
  - `WorldState current state > extracted or advisory summaries`
- Stage 3 rejects or flags dead-NPC active present-time role assignments before Stage 4 work is wasted.
- Flashback, recall, and mention-only cases remain allowed; the pre-check must stay narrow.
- No new registry, DB table, schema, or persistence owner is introduced.

## 10. Verification Plan
- `python -m py_compile modules/core/stage4_context_builder.py modules/core/stage3_orchestrator.py modules/validation/blocking_validator_entity_checks.py`
- `pytest tests/test_stage4_context_builder.py -q`
- `pytest tests/test_stage3_orchestrator.py -q`
- `pytest tests/chaos/test_dead_npc_hard_block.py -q`
- if a new tiny test file is introduced, run it separately and keep it bounded to this wave
- `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py modules/core/stage3_orchestrator.py modules/validation/blocking_validator_entity_checks.py tests/test_stage4_context_builder.py tests/test_stage3_orchestrator.py tests/chaos/test_dead_npc_hard_block.py docs/2026-03-27/per-work-fact-contract-alignment-wave1-execution-ssot.md docs/temp/per-work-fact-contract-alignment-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails
- Do not broaden this into a per-work registry implementation.
- Do not touch `FactLedger` or `WorldState` storage contracts in this wave.
- Do not turn Stage 3 into a clone of Stage 4 validation.
- Keep authority wording compact; this wave is precedence clarification, not prompt bloat.
- If implementation requires more than a tiny helper extraction from validator code, stop and reopen scope rather than silently expanding it.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after closure audit confirms canonical/temp/code coherence
- roadmap dependency: none; this is a single active bounded wave

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1. Structure and Scope
- The execution target matches the design memo exactly:
  - one prompt-facing authority clarification
  - one narrow Stage 3 dead-NPC pre-check
- Registry, persistence redesign, and broader fact-model work remain excluded.
- PASS

Pass 2. Evidence and Consistency
- Stage 4 canonical injection and advisory suppression already exist in live code.
- Stage 3 advisory injection exists, but earlier impossibility checking does not.
- Dead-NPC truth enforcement already exists later in the pipeline, so this wave is a timing/alignment move rather than new rule invention.
- PASS

Pass 3. Execution Readiness
- Included files are bounded and concrete.
- Side effects are enumerated explicitly.
- Verification and closure hooks are concrete and reproducible.
- PASS

Estimated confidence: 97%

---

- Recommended direction: contract-only
- Dominant unresolved seam: prompt-facing authority precedence remains too implicit
- Should Codex open an execution SSOT now: yes

## 15. Closure Note

Closure Date: 2026-03-27
Closure Status: closed (closure-audited)

Realization Summary:
- Stage 4 canonical injection now includes a short authority statement clarifying that realized persisted layers outrank seed/advisory layers on conflict.
- Stage 3 now runs a narrow dead-NPC pre-check before downstream work, rejecting active present-time assignments for deceased NPCs with an explicit `dead_npc_precheck` reason.
- Bounded regression coverage landed in the existing Stage 4 context and Stage 3 orchestrator test files; no new registry, persistence, or DB owner was introduced.

Verification Evidence:
- `python -m py_compile modules/core/stage4_context_builder.py modules/core/stage3_orchestrator.py modules/validation/blocking_validator_entity_checks.py` -> PASS
- `pytest tests/test_stage4_context_builder.py -q` -> `98 passed`
- `pytest tests/test_stage3_orchestrator.py -q` -> `80 passed`
- `pytest tests/chaos/test_dead_npc_hard_block.py -q` -> `7 passed`
- `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py modules/core/stage3_orchestrator.py modules/validation/blocking_validator_entity_checks.py tests/test_stage4_context_builder.py tests/test_stage3_orchestrator.py tests/chaos/test_dead_npc_hard_block.py docs/2026-03-27/per-work-fact-contract-alignment-wave1-execution-ssot.md docs/temp/per-work-fact-contract-alignment-wave1-execution-ssot.md` -> PASS

Residual Risk:
- No blocking residual risk remains inside this wave scope.
- Stage 3 dead-NPC pre-check quality still depends on existing `state_tracker_npc` detection coverage; broader authority ordering and any registry-like follow-up remain explicitly deferred.

Excluded Surface Check:
- `modules/core/fact_ledger.py` not touched
- `modules/core/world_state.py` not touched
- `modules/domain/agents/state_tracker.py` not touched
- DB schema / persistence redesign not opened
- BI/TR ingestion changes not opened
- broader Stage 3 truth-gate expansion and Stage 4 validator duplication not opened
