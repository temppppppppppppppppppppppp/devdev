# Stage3 Data Shape / PWF Bounded Survey

Date: 2026-04-07
Status: final
Canonical Path: `docs/2026-04-07/stage3-data-shape-pwf-bounded-survey.md`
Scope: live Stage3 blueprint contract shape and `PASS_WITH_FIX` behavior
Execution Doc Requirement: `no-execution-doc-required`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs, treatments, material_ssot, bible, scripts, modules`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Intent

Establish the dominant Stage3 data shape and the exact style of Stage3 `PWF`.

## Pass 1. Inventory

- Stage3 success recording persists a dict payload carrying `verdict`, `score`, `selection_reason`, `fix_scope`, `advisory_warnings`, `artifact_path`, and similar fields (`modules/core/stage3_orchestrator.py:2449-2521`).
- Stage3 runtime marks revision-required when verdict is `PASS_WITH_FIX` or `PASS_WITH_WARNING`, so `PWF` is first-class in the blueprint lane (`modules/core/stage3_orchestrator.py:1733-1739`).
- Selected authoritative-file AST count is strongly dict-heavy:
  - `dict_literals=226`
  - `list_literals=92`
  - `dict_return_annotations=21`
  - `list_return_annotations=7`
- `three_phase_blueprint_runtime` uses dict validation payloads and dict blueprint objects throughout retry and patch lanes.

## Pass 2. Semantic Classification

- Stage3 is predominantly `dict` shaped.
- Lists mostly carry `issues`, warning arrays, or preview snippets. The authoritative runtime packet is still dict-first.

## PWF Semantics

- Stage3 `PWF` is not diff text.
- It reads `fix_scope`; if missing, it falls back to `"inplace"` or `"full"` by threshold. If `fix_scope` is `partial` or `full`, local patching is blocked and control returns to the generation loop (`modules/domain/agents/three_phase_blueprint_runtime.py:1018-1025`).
- Local patch feedback comes from `re_slice_instruction` or `feedback`, then that string is passed to `_inplace_patch_blueprint(...)` as `director_feedback` (`modules/domain/agents/three_phase_blueprint_runtime.py:1031-1045`).
- Re-audit continues to carry `feedback`, `issues`, and `fix_scope` fields, confirming that Stage3 repair is driven by structured advisory fields, not diff hunks (`modules/domain/agents/three_phase_blueprint_runtime.py:1130-1158`, `modules/core/stage3_orchestrator.py:2466-2478`).
- There is an early-exit guard on score stall during repeated `PWF` attempts, which further confirms looped re-audit rather than patch-by-diff (`modules/domain/agents/three_phase_blueprint_runtime.py:964-978`).

## Direct Answer

- Stage3 answer for question 1: mostly `dict`.
- Stage3 answer for question 2: `PWF` is instruction-driven. It uses `fix_scope` plus `re_slice_instruction` / `feedback`, not git diff syntax and not paragraph-number hunks.

## Side-Effect Coverage

- File writes/artifact generation: not central here.
- DB writes: not central here.
- JSONL/log/audit sinks: applicable through success/advisory payloads, but not the main contract under review.
- Console/UI output: applicable; operator logs carry feedback and fix-scope context.
- Retry/recovery: applicable and inspected; `fix_scope` controls local patch vs regenerate delegation.
- Cache/global state: not central.
- Config/env/bootstrap fallback: not central.

## Pass 3. Operating Consequence

- Future Stage3 contracts should keep dict-first payloads if they want to stay aligned with current runtime.
- If finer-grained "edit this exact paragraph" control is desired, Stage3 currently lacks Stage4-style explicit target coordinates and would need a richer fix-pack schema.

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- The document stayed bounded to Stage3 blueprint/runtime surfaces.
- The two user questions are answered separately.

### Pass 2. Evidence and Consistency

- Stage3 success payload, revision flags, and `PWF` patch loop were all checked in live code.
- No claim depends on stale docs or tests alone.

### Pass 3. Execution and Readability

- The document makes the Stage3 limitation explicit: structured repair exists, but not scene/anchor-precise patch targeting.

Confidence: `97%`
