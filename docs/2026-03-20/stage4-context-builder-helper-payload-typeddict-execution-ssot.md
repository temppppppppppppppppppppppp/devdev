# Stage4 Context Builder Helper Payload TypedDict Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage4-context-builder-helper-payload-typeddict-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-context-builder-helper-payload-typeddict-execution-ssot.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: ongoing stage/smoke/doc/project churn, low-trust intake bundle, prior closed decomposition tranche`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/typed-dict-helper-payload-live-reaudit-3pass-audit.md`
- `docs/2026-03-20/typed-dict-helper-payload-hotspot-survey-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage4_context_builder.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_continuity_packet.py`
- `tests/test_chief_writer_context.py`
Side-Effect Coverage: covered

## 1. Intent
- Make Stage 4 context-builder helper payloads explicit with local `TypedDict` contracts.
- Reduce branch opacity in retrieval/focus/coverage assembly without changing the returned writer context.

## 2. Baseline Facts
- `build_mandatory_context` is now a coordinator over helper-based section builders
- helper payloads are stable but currently plain dicts
- this file has high branch density, so named payload contracts improve readability disproportionately

## 3. Scope
Included:
- `modules/core/stage4_context_builder.py`
- same-file `TypedDict` definitions for helper payloads
- immediate helper annotation alignment

Excluded:
- retrieval algorithm changes
- Stage 4 governance/retry/policy changes
- raw writer context payload redesign
- shared typing-module extraction

## 4. Pass 1. Inventory Summary
- candidate helpers:
  - `_resolve_work_retrieval_focus`
  - `_build_tier0_mandatory_sections`
  - `_collect_stage4_retrieval_context`
  - `_compose_context_with_retrieval_coverage`
  - `_build_tier12_auxiliary_sections`

## 5. Pass 2. Semantic Classification
- Class A:
  - work-focus / slot-resolution payload
- Class B:
  - tiered section assembly payloads
- Class C:
  - retrieval/coverage recomposition payloads

## 6. Side-Effect Map
- file writes / artifacts:
  - none
- DB / schema / transaction boundaries:
  - read-only retrievals only
- JSONL / log / audit sinks:
  - existing retrieval observations only
- console / UI / operator output:
  - existing warnings only
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - unchanged reads and observation hooks only
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- keep `TypedDict` definitions local to `stage4_context_builder.py`
- type helper output shapes, not the whole narrative payload stack
- preserve public writer-context return shape

## 8. Execution Tranches
1. Introduce local `TypedDict` definitions for focus, tier, retrieval, and coverage payloads.
2. Annotate helper returns and caller sites in `build_mandatory_context`.
3. Re-run direct Stage 4 context regressions and close.

## 9. Acceptance Criteria
- helper payload shapes are explicit
- `build_mandatory_context` return contract remains unchanged
- direct Stage 4 context-builder regressions continue to pass

## 10. Verification Plan
- `python -m pytest tests/test_stage4_context_builder.py -q`
- `python -m pytest tests/test_continuity_packet.py -q`
- `python -m pytest tests/test_chief_writer_context.py -q`

## 11. Guardrails
- do not widen this item into raw blueprint/manuscript `TypedDict` work
- do not mix retrieval behavior changes with typing work
- do not add a repo-wide static checker in this tranche

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition:
  - remove mirror after realization and closure
- roadmap dependency:
  - third item; independent enough to follow the Stage 2 pair

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Progress Note
- 2026-03-20 realization completed:
  - introduced local `TypedDict` contracts for work-focus, retrieval, coverage, and auxiliary helper payloads
  - annotated helper return signatures and direct caller payload variables inside `build_mandatory_context`
- Closure note:
  - acceptance criteria satisfied
  - direct Stage 4 context-builder regression shards passed after typing refinement
