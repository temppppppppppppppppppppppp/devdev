# Stage2 Data Shape / PWF Bounded Survey

Date: 2026-04-07
Status: final
Canonical Path: `docs/2026-04-07/stage2-data-shape-pwf-bounded-survey.md`
Scope: live Stage2 contract shape and `PASS_WITH_FIX` patch loop semantics
Execution Doc Requirement: `no-execution-doc-required`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs, treatments, material_ssot, bible, scripts, modules`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Intent

Answer the Stage2-specific form of the same two questions:

1. Is Stage2 mainly `list` or `dict` shaped?
2. Does Stage2 `PWF` behave like diff feedback or like targeted repair instructions?

## Pass 1. Inventory

- Stage2 retry callback resolution is maintained as dict-backed contract maps, not list registries (`modules/core/stage2_context.py:21-58`, `modules/core/stage2_context.py:89-105`).
- The authoritative Stage2 packet merge API is explicitly `dict[str, Any] -> dict[str, Any]` and recursively merges nested dicts (`modules/core/stage2_contracts.py:19-37`).
- `Stage2PassWithFixLoopResult` is a `TypedDict` with `refined_arc: dict[str, Any]` and `audit: dict[str, Any]` (`modules/core/stage2_finalizer.py:361-380`).
- `PASS_WITH_FIX` entry is explicit in finalization: `_run_stage2_pass_with_fix_loop(...)` is called only when Director returns `PASS_WITH_FIX` (`modules/core/stage2_finalizer.py:1091-1109`).
- Selected authoritative-file AST count is dict-heavy:
  - `dict_literals=198`
  - `list_literals=158`
  - `dict_return_annotations=46`
  - `list_return_annotations=10`

## Pass 2. Semantic Classification

- Stage2 is primarily `dict` shaped.
- Lists remain important for ordered evidence and warnings, but the authoritative business objects are dict packets:
  - `refined_arc`
  - `audit`
  - merged authoritative packet
  - patch-pressure / patch-guard metadata

## PWF Semantics

- Stage2 `PWF` is not git-style diff feedback.
- Local patch entry depends on `fix_scope`; `partial` or `full` explicitly block local inplace patching and delegate to retry/regenerate flow (`modules/core/stage2_finalizer.py:2225-2232`, `modules/core/stage2_finalizer.py:2520-2527`).
- The actual patch instruction is the text field `re_slice_instruction`; that string is passed as `director_feedback` into `_inplace_patch_arc(...)` (`modules/core/stage2_finalizer.py:2234-2245`, `modules/core/stage2_finalizer.py:2529-2552`).
- Stage2 does compute and log patch diff after the patch is already produced, but that is observability/guard logic, not the feedback contract itself (`modules/core/stage2_finalizer.py:2297-2308`).
- Re-audit context stores applied changes as bullet-list history under `[PASS_WITH_FIX 재심사 - 이미 적용된 패치]`, again indicating "what was changed" rather than unified diff hunks (`modules/core/stage2_finalizer.py:2362-2369`).

## Direct Answer

- Stage2 answer for question 1: mostly `dict`.
- Stage2 answer for question 2: `PWF` uses targeted repair instructions (`fix_scope` + `re_slice_instruction`) and patch-re-audit loops. It is not authored as git diff text. Diffing exists only as an internal patch guard / log surface after the patch.

## Side-Effect Coverage

- File writes/artifact generation: not central to this question.
- DB writes: not central to this question.
- JSONL/log/audit sinks: applicable; Stage2 logs patch diff and patch guard signals.
- Console/UI output: applicable; Stage2 emits explicit patch attempt and delegation messages.
- Retry/recovery: applicable and inspected; `fix_scope` governs local patch vs retry delegation.
- Cache/global state: not central.
- Config/env/bootstrap fallback: indirectly applicable through patch thresholds, but not the main answer surface.

## Pass 3. Operating Consequence

- If you want future Stage2 contracts to stay aligned with live code, treat `dict` as the extension surface and lists as embedded ordered fields only.
- If you want Stage2 `PWF` to behave more like paragraph-precise editing, you would need richer target metadata than the current instruction-string contract.

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- Scope stayed on Stage2 authority files plus direct `PWF` loop.
- Raw AST count was used only as supporting evidence, not as sole authority.

### Pass 2. Evidence and Consistency

- Contract shape was checked against `stage2_context`, `stage2_contracts`, and `stage2_finalizer`.
- `PWF` semantics were checked at the local patch, diff logging, and re-audit context boundaries.

### Pass 3. Execution and Readability

- The distinction between "instruction contract" and "internal diff logging" is explicit.
- The stage-level answer is actionable for future contract design.

Confidence: `97%`
