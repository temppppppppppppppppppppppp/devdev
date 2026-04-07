# Stage4 Data Shape / PWF Bounded Survey

Date: 2026-04-07
Status: final
Canonical Path: `docs/2026-04-07/stage4-data-shape-pwf-bounded-survey.md`
Scope: live Stage4 contract shape and cross-cut `PASS_WITH_FIX` implementation in chief-writer/director lanes
Execution Doc Requirement: `no-execution-doc-required`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs, treatments, material_ssot, bible, scripts, modules`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Intent

Determine whether Stage4 is mainly `list` or `dict` shaped, and whether its `PWF` path behaves like diff feedback or like targeted location-specific repair.

## Pass 1. Inventory

- Shared Stage4 types are dict-heavy even when they carry list children:
  - `_RoundContext.blueprint: dict`
  - `_RoundContext.arc_data: dict`
  - `_InterviewRoundResult.previous_attempt: dict`
  - `_InterviewRoundResult.final_state_updates: dict`
  - plus bounded list fields such as inventories and recent keywords (`modules/core/stage4_types.py:15-89`).
- Retry/runtime payload dataclasses are dominated by dict fields such as `fix_pack_contract`, `current_audit_result`, `patch_trace`, `re_audit`, and `director_result` (`modules/core/stage4_retry_runtime.py:14-83`).
- Structural patch planning returns a dict that holds `target_scene_ids: list[str]`, `target_index_map: dict[str, int]`, and merged plan text (`modules/domain/agents/chief_writer.py:1335-1396`).
- Selected authoritative-file AST count is dict-heavy:
  - `dict_literals=696`
  - `list_literals=544`
  - `dict_return_annotations=138`
  - `list_return_annotations=70`

## Pass 2. Semantic Classification

- Stage4 is primarily `dict` shaped.
- Lists are still essential for ordered manuscript blocks, scene IDs, candidate arrays, and patch histories, but the control-plane and authority surfaces are dict-first.

## PWF Semantics

- Director-side contract explicitly asks for `PASS_WITH_FIX + fix_scope="inplace" + feedback` when a local repair is possible; output JSON must include `decision`, `fix_scope`, `score`, `contradictions`, `feedback`, and `fix_scope_reasoning` (`modules/domain/agents/director_ensemble.py:2036-2063`, `modules/domain/agents/director_ensemble.py:2329-2350`).
- Stage4 gate refuses to let `PASS_WITH_FIX` continue unless the local-fix contract is valid. Invalid or missing scope is downgraded to `REJECT` (`modules/core/stage4_interview_round.py:2696-2757`).
- Structural patch mode is explicitly target-based, not diff-based:
  - choose `target_scene_ids`
  - build `boundary_context`
  - send only target scenes
  - expect JSON `{"patched_blocks": {"scene_id": "patched text"}, "patch_state_updates": {...}}`
  - merge only those scene blocks back into the manuscript (`modules/domain/agents/chief_writer.py:1344-1396`, `modules/domain/agents/chief_writer.py:1447-1505`).
- Local-edit mode is even more position-specific:
  - `target_kind`
  - `patch_targets`
  - up to 6 replace operations
  - each op carries `old_text`, `new_text`, `anchor_before`, `anchor_after`
  - whole-manuscript rewrite is explicitly forbidden (`modules/domain/agents/chief_writer_inplace_local_ops.py:20-45`, `modules/domain/agents/chief_writer_inplace_local_ops.py:82-120`, `modules/domain/agents/chief_writer_inplace_local_ops.py:164-220`).
- Re-audit story context records already-applied patches as bullet history, not as diff hunks (`modules/core/stage4_interview_round.py:6737-6745`).

## Direct Answer

- Stage4 answer for question 1: mostly `dict`.
- Stage4 answer for question 2: `PWF` is not git diff feedback. It is targeted repair guidance with increasingly explicit location data:
  - Director: `fix_scope` + concrete feedback
  - Structural patch: specific `scene_id` targets
  - Local edit patch: exact replace ops with text anchors
- Of all stages, Stage4 is the closest to "edit this exact local spot" behavior.

## Side-Effect Coverage

- File writes/artifact generation: not central to this bounded survey.
- DB writes: not central to this bounded survey.
- JSONL/log/audit sinks: applicable through patch traces, gate notices, and retry observability.
- Console/UI output: applicable; Stage4 emits policy and patch-loop notices.
- Retry/recovery: applicable and inspected; Stage4 heavily enforces local-fix eligibility before entering the loop.
- Cache/global state: not central.
- Config/env/bootstrap fallback: indirectly applicable through patch thresholds and fix-pack contracts.

## Pass 3. Operating Consequence

- If new Stage4 payloads are added, they should stay dict-first and embed lists only where ordering matters.
- If the goal is human-readable "paragraph 2, scene 5, replace X with Y" style repair, Stage4 already has the best substrate in the repo.
- If the goal is literal unified diff output, that is not the current design and would be a new contract, not a small tweak.

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- The document stayed bounded to Stage4 authority and cross-cut `PWF` surfaces.
- It covers both chief-writer and director sides.

### Pass 2. Evidence and Consistency

- Dict/list claims were checked against Stage4 types, retry runtime, chief writer, and director contract prompts.
- `PWF` conclusions are based on live code that actually enters or blocks the patch loop.

### Pass 3. Execution and Readability

- The stage answer is direct and operational: Stage4 already supports targeted local repair, but not diff-hunk feedback.

Confidence: `98%`
