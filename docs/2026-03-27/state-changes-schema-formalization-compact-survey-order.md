Date: 2026-03-27
Status: final (3-pass audited)
Document Type: system-track compact survey order
Canonical Path: `docs/2026-03-27/state-changes-schema-formalization-compact-survey-order.md`
Temp Mirror Path: none
Parent Authority:
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-opus-deep-dive-audit.md`
Priority Slot:
- defer Tier 1A

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/context/validator/stage4/orientation/runtime surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Order Summary

Open one bounded compact survey for `state_changes schema formalization`.

This order is survey-only. The goal is to determine the real producer/consumer contract shape of `state_changes`, identify field and enum drift, and decide the smallest viable formalization path.

This order does **not** authorize code changes.

## 2. Hard Guardrails

### Absolute No-Change Rule

Do **not** modify production code.

Do **not**:
- patch `modules/`
- patch `main_a.py`
- patch tests
- patch config
- patch DB or runtime artifacts
- patch `docs/temp/queue-state.json`
- create an execution SSOT
- create a roadmap
- silently escalate into implementation

Allowed outputs:
- survey document
- optional raw evidence note

### Scope Discipline

Keep this survey bounded to `state_changes` contract formalization.

Do **not** widen into:
- full fact-authority redesign
- technique/realm modeling project
- provider consolidation
- writer/context refactor
- global Stage 4 cleanup

## 3. Survey Question

Answer exactly this:

`What is the current runtime contract of state_changes, where do producers and consumers disagree, and what is the smallest safe formalization shape to normalize it without opening a broad redesign?`

## 4. Required Coverage

### Primary Producer Surfaces

- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/domain/agents/state_tracker_plots.py`
- `modules/domain/agents/state_tracker_financial.py`

### Primary Consumer Surfaces

- `modules/core/world_state.py`
- any runtime module in `modules/` that directly reads `arc.get("state_changes")` or `state_changes.get(...)`

### Contract-Adjacent Surfaces

- `modules/validation/blocking_validator.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`

If any of the contract-adjacent surfaces are found to be non-consumers, mark them explicitly as non-applicable rather than skipping them silently.

## 5. Required Outputs

### Canonical Survey Doc

Write:
- `docs/2026-03-27/state-changes-schema-formalization-compact-survey.md`

### Optional Raw Evidence

Only if needed:
- `docs/2026-03-27/state-changes-schema-formalization-evidence.md`

Do not create temp mirrors.

## 6. Minimum Findings Required

The survey is incomplete unless it explicitly contains all of the following.

### A. Producer Inventory

Inventory every currently emitted `state_changes` key in runtime production code.

For each key, record:
- producer owner
- source method
- emitted shape
- whether the value is explicit, derived, or regex fallback

### B. Consumer Inventory

Inventory every runtime consumer of `state_changes`.

For each consumer, record:
- file and method
- keys read
- whether missing keys are tolerated
- whether wrong enum/value silently degrades, skips, or hard-fails
- whether side effects occur from the read

### C. Mismatch Ledger

Build a mismatch ledger with at least these categories:
- field name drift
- shape drift
- enum/value vocabulary drift
- explicit-vs-regex ambiguity
- write-only fields
- read-only expectations

### D. Enum/Vocabulary Table

Produce a concrete vocabulary table for at least:
- relationship fields
- injury fields
- movement/location-like fields if present
- protagonist emotion if present
- any genre-conditional field family encountered

### E. Formalization Recommendation

Pick one bounded recommendation and justify it:
- `TypedDict-first`
- `dataclass/TypedDict hybrid`
- `staged normalization with compatibility shell`

The recommendation must include blast-radius notes and explain why broader redesign is unnecessary right now.

## 7. Required Side-Effect Sweep

Even though this is a schema survey, the following side-effect categories must still be checked.

- `WorldState` mutation paths caused by `state_changes`
- any DB-backed replay path that reuses `state_changes`
- prompt/summary generation paths that surface `state_changes`-derived data
- validator behavior that depends on `state_changes`-derived state

If a side-effect category is non-applicable, say so explicitly.

## 8. Success Criteria

This order is complete only if the resulting survey can answer:

1. Which `state_changes` keys are the current de facto SSOT surface
2. Which keys are advisory, compatibility, dormant, or drift-prone
3. Which producer/consumer mismatches would break or silently degrade behavior
4. What the smallest safe formalization patch shape is

If the survey cannot answer all four, it is not complete and should not be promoted into an execution SSOT.

## 9. Recommended Survey Shape

Keep the survey compact and execution-facing.

Recommended section order:
1. executive summary
2. scope and exclusions
3. producer inventory
4. consumer inventory
5. mismatch ledger
6. enum/vocabulary table
7. formalization recommendation
8. side-effect coverage
9. confidence and limits

## 10. Promotion Rule

This order itself does **not** create an execution SSOT.

Only after the compact survey is complete and 3-pass audited may a later turn decide whether to promote it into:
- one bounded execution SSOT
- or a smaller follow-up survey if the blast radius is still unclear

## 11. Confidence Target

Required confidence for the resulting survey:
- `95%+`

If confidence stays below `95%`, do not final-save the survey as authoritative.

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- document type matches a survey-order open request
- scope remains bounded to `state_changes schema formalization`
- hard no-code-change rule is explicit
- PASS

### Pass 2. Evidence and Consistency
- ordering aligns with the top-level defer freeze
- output paths are canonical dated docs only
- no temp execution semantics were introduced
- PASS

### Pass 3. Execution and Readability
- required findings and success criteria are operationally explicit
- widening risks are explicitly forbidden
- next promotion step is bounded
- PASS

