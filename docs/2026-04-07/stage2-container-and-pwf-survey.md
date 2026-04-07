# Stage2 Container And PWF Survey

Date: 2026-04-07
Status: final
Scope: system-track survey-only
Canonical Path: `docs/2026-04-07/stage2-container-and-pwf-survey.md`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Container Verdict

Stage2 is `dict`-dominant.

- Core Stage2 payload families are defined as `TypedDict`.
  - `modules/core/stage2_orchestrator.py:26-75`
  - `modules/core/stage2_finalizer.py:361-380`
- Stage2 authoritative merge function is recursive `dict -> dict` preservation.
  - `modules/core/stage2_contracts.py:19-37`
- Quantitative readback over targeted Stage2 files: `dict_literals=384`, `list_literals=278`, `TypedDict=8`.

Interpretation:

- Stage2 still carries lists inside payloads, such as enriched batch tuples or per-arc collections.
- But authority-bearing envelopes and finalizer return shapes are mostly `dict`.

## 2. PWF Verdict

Stage2 PWF is instruction-driven and local-scope-gated, not diff-driven.

- `PASS_WITH_FIX` enters a patch + Director re-audit loop.
  - `modules/core/stage2_finalizer.py:1091-1109`
- Local patch is allowed only when `fix_scope` is present and not `partial/full`.
  - `modules/core/stage2_finalizer.py:2225-2233`
  - `modules/core/stage2_finalizer.py:2519-2533`
- The patch call passes a string instruction, not a diff payload.
  - `modules/core/stage2_finalizer.py:2234-2244`
- Stage2 may append additional blocking hints into `re_slice_instruction`.
  - `modules/core/stage2_finalizer.py:2863-2868`

Tests confirm the same contract shape:

- `1문단 수정`, `약 40억을 약 18억으로 수정`, `숫자 불일치 정정`
  - `tests/test_pass_with_fix.py:764-794`
  - `tests/test_pass_with_fix.py:800-827`

Verdict:

- not unified diff
- explicit repair instruction string + `fix_scope`
- local patch only when scope remains `inplace`

## 3. Side-Effect Notes

Applicable side effects reviewed:

- operator patch logs via `self.ctx.ui.log`
- `_inplace_patch_arc(...)` invocation
- audit field mutation for `re_slice_instruction`, `fix_scope`, and re-audit state

Non-goal for this survey:

- runtime truth of every Stage2 artifact sink

## 4. 3-Pass Audit Record

### Pass 1. Structure and Scope

- Limited to Stage2 payload contracts and PWF loop semantics.

### Pass 2. Evidence and Consistency

- Contract verdict anchored to `TypedDict` definitions and merge logic, not to generic syntax counts alone.

### Pass 3. Execution and Readability

- Final answer reduces to one usable rule: Stage2 trusts dict envelopes and uses instruction-string PWF, not diff hunks.

Confidence: `97%`
