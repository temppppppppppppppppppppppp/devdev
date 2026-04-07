# Stage3 Container And PWF Survey

Date: 2026-04-07
Status: final
Scope: system-track survey-only
Canonical Path: `docs/2026-04-07/stage3-container-and-pwf-survey.md`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Container Verdict

Stage3 is also `dict`-dominant, with list collections nested inside blueprint structures.

- Runtime carriers are dataclasses whose fields are mostly `dict` plus nested lists.
  - `modules/domain/agents/three_phase_blueprint_runtime.py:21-95`
- Canonical blueprint model is a `dict`-shaped object with nested collections.
  - `scene_breakdown: dict[str, BlueprintScene | str]`
  - `relationship_changes: list[dict]`
  - `protagonist_state: dict`
  - `modules/models/blueprint.py:29-83`
- Stage3 observability and failure classifiers also normalize into dict payloads.
  - `modules/core/stage3_orchestrator.py:53-88`
  - `modules/core/stage3_orchestrator.py:136-161`
- Quantitative readback over targeted Stage3 files: `dict_literals=420`, `list_literals=312`.

Interpretation:

- Blueprint content itself contains many repeated lists.
- But the boundary object being validated, returned, and forwarded is still a dict-style envelope.

## 2. PWF Verdict

Stage3 PWF is validator/director instruction-driven, not diff-driven.

- Validator result preserves `feedback`, `fix_scope`, `fix_scope_reasoning`, and `re_slice_instruction`.
  - `modules/domain/agents/unified_blueprint_validator.py:656-682`
- Runtime patch loop prefers `re_slice_instruction`, then falls back to generic `feedback`.
  - `modules/domain/agents/three_phase_blueprint_runtime.py:1018-1044`
- Local blueprint patch is invoked with `director_feedback=fix_feedback`, not diff text.
  - `modules/domain/agents/three_phase_blueprint_runtime.py:1031-1044`

Tests make the style explicit:

- `씬 3의 전투 장면에서 NPC 대사를 캐릭터 성격에 맞게 수정`
- `씬 5 재배치 필요`
  - `tests/test_pass_with_fix.py:1462-1489`

Verdict:

- not diff
- targeted rewrite instruction
- Stage3 patch loop explicitly prioritizes location-specific instruction text

## 3. Side-Effect Notes

Applicable side effects reviewed:

- operator retry context logging
- `_inplace_patch_blueprint(...)` invocation
- propagation of validator feedback fields into runtime retry state

## 4. 3-Pass Audit Record

### Pass 1. Structure and Scope

- Limited to Stage3 blueprint contract and fix-loop semantics.

### Pass 2. Evidence and Consistency

- Dict dominance was anchored to the blueprint model and runtime envelopes, not only to generic Python literal counts.

### Pass 3. Execution and Readability

- Final answer states the practical rule: Stage3 feedback is "what local blueprint slice to fix", not textual diff output.

Confidence: `96%`
