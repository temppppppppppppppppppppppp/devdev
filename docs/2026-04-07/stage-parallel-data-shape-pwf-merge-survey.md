# Stage Parallel Data Shape / PWF Merge Survey

Date: 2026-04-07
Status: final
Canonical Path: `docs/2026-04-07/stage-parallel-data-shape-pwf-merge-survey.md`
Scope: system-track ROL survey-only bundle answering current `list` vs `dict` usage and `PWF` feedback style across Stage0/2/3/4
Execution Doc Requirement: `no-execution-doc-required`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs, treatments, material_ssot, bible, scripts, modules`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Source Survey Docs:
- `docs/2026-04-07/stage0-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage2-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage3-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage4-data-shape-pwf-bounded-survey.md`

Evidence Artifacts:
- `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`

## Intent

Provide one merge answer for the user's two questions while keeping stage-specific evidence separate.

Assumption:
- `PWF` is interpreted as the live `PASS_WITH_FIX` family because the current code uses `_pwf_result`, `PASS_WITH_FIX`, `[PWF-STRUCT]`, and `[PWF-LOCAL]` markers on the relevant repair surfaces.

Queue Note:
- `docs/temp/execution-roadmap.md` is already the active temp-queue controller with 18 items.
- This bundle is survey-only. It does not create or refresh execution SSOT mirrors and does not alter queue order.

## Pass 1. Cross-Stage Inventory

| Stage | Dominant Live Shape | Key Evidence | PWF Presence |
| --- | --- | --- | --- |
| Stage0 | `dict` envelope + `list` children | canonical BI/TR validators and handoff roadmap | no active Stage0 `PWF` loop found |
| Stage2 | mostly `dict` | authoritative packet merge, `TypedDict` audit/result payloads | yes |
| Stage3 | mostly `dict` | success payload, validation/advisory dicts | yes |
| Stage4 | mostly `dict` | retry/runtime payloads, chief-writer/director result dicts | yes, strongest local-targeting |

Selected authoritative-file AST totals:

- Stage0: `dict_literals=112`, `list_literals=130`
- Stage2: `dict_literals=198`, `list_literals=158`
- Stage3: `dict_literals=226`, `list_literals=92`
- Stage4: `dict_literals=696`, `list_literals=544`

Interpretation:
- Stage0 is the only materially mixed stage because it still tolerates raw list treatment inputs and naturally owns ordered roadmap/block arrays.
- Stage2, Stage3, and Stage4 are clearly dict-first on live authority surfaces.

## Pass 2. Direct Answers

### Question 1

Current default answer: we mainly use `dict`.

More precise answer:

- The repo-wide live stage contract pattern is `dict` envelope first.
- `list` is heavily used, but mostly as nested ordered content:
  - `blocks`
  - `plot_roadmap`
  - candidate arrays
  - issues/warnings
  - scene IDs
  - patch histories
- The only stage where `list` still meaningfully competes with `dict` at the top-level contract boundary is Stage0 compatibility intake.

### Question 2

Current default answer: `PWF` does not use git-style diff feedback as its primary contract.

More precise answer by stage:

- Stage2: `fix_scope` + `re_slice_instruction` drive an inplace arc patch; diffing exists only as internal patch logging/guarding.
- Stage3: `fix_scope` + `re_slice_instruction` / `feedback` drive blueprint patch or regenerate delegation; no diff-hunk contract.
- Stage4: `fix_scope` + concrete `feedback` drive the loop, then repair becomes target-aware:
  - structural mode patches specific `scene_id` blocks
  - local-edit mode emits exact replace ops with `old_text`, `new_text`, and text anchors

Operational conclusion:

- If the question is "Does PWF tell us merely 'go fix something'?" -> no. Later stages already carry bounded repair intent.
- If the question is "Does PWF speak in unified diff hunks?" -> also no.
- If the question is "Does PWF reach the level of 'fix this specific local spot'?" -> Stage4 yes, Stage2/3 only partially.

## Side-Effect Coverage

- File writes/artifact generation: not the authority surface for this survey; not used for final claims.
- DB writes: not central to the bounded questions.
- JSONL/log/audit sinks: applicable; Stage2 logs patch diffs and Stage4 emits retry/gate traces.
- Console/UI output: applicable; Stage2/4 emit explicit patch-loop and delegation notices.
- Retry/recovery: applicable and inspected; `fix_scope` is the key branching contract.
- Cache/global state: not central.
- Config/env/bootstrap fallback: only indirectly relevant through patch thresholds.

## Pass 3. Operating Consequence

- For new stage contracts, the live repo norm is: `dict` outside, `list` inside.
- For future PWF upgrades:
  - Stage4 already has a usable target-aware substrate.
  - Stage2/3 would need explicit target schema if you want the same "exact local spot" behavior there.
- If you want literal diff output, treat it as a new contract decision rather than assuming the current PWF stack already does that.

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- The bundle stayed survey-only and did not inflate into execution SSOT or queue mutation.
- Stage split and merge answer are both present.

### Pass 2. Evidence and Consistency

- Claims were tied to live code first and supported by raw AST counts second.
- Active temp queue was inspected and explicitly left unchanged.

### Pass 3. Execution and Readability

- The merge answer resolves both user questions without requiring re-reading all stage docs.
- Follow-on design consequence is explicit: dict-first contracts, non-diff PWF, Stage4 as the strongest target-aware repair surface.

Confidence: `98%`
