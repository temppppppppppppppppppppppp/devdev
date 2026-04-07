# Stage0 Data Shape / PWF Bounded Survey

Date: 2026-04-07
Status: final
Canonical Path: `docs/2026-04-07/stage0-data-shape-pwf-bounded-survey.md`
Scope: live Stage0 canonical BI/TR contract shape and PWF presence check
Execution Doc Requirement: `no-execution-doc-required`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs, treatments, material_ssot, bible, scripts, modules`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Intent

Answer two bounded questions for Stage0 only:

1. Is the live Stage0 surface mainly `list` or `dict` shaped?
2. Does Stage0 currently participate in `PWF` (`PASS_WITH_FIX`) style feedback/runtime loops?

## Pass 1. Inventory

- Canonical BI is a `dict` rooted at `MasterBible`, and it requires `MasterBible.protagonist_config` as `dict` plus `MasterBible.plot_roadmap` as non-empty `list` (`modules/core/response_schemas.py:900-919`).
- Canonical TR is not raw `list` anymore. Canonical validation requires a `dict` wrapper with `blocks: list[...]` (`modules/core/response_schemas.py:973-1001`).
- Compatibility mode still accepts raw treatment shapes `list`, `dict.blocks`, and `dict.treatments` (`modules/core/response_schemas.py:923-939`).
- Stage0 handoff emits `plot_roadmap` as `list[dict]`; each roadmap entry is a `dict` keyed by `block_no`, `tactical_doc`, `joint_docs`, `state_changes`, and similar payload fields (`modules/core/stage0_handoff.py:329-350`).
- Stage0 consumer payload extraction is dict-centric and only dips into lists for ordered text fragments such as `key_events` (`modules/core/stage0_handoff.py:358-400`).
- Selected authoritative-file AST count is mixed, but still envelope-first:
  - `dict_literals=112`
  - `list_literals=130`
  - `dict_return_annotations=13`
  - `list_return_annotations=16`
  - interpretation: Stage0 is the most mixed stage because it still carries compatibility loaders and ordered roadmap/block arrays.

## Pass 2. Semantic Classification

- Stage0 is not "pure list" anymore.
- The canonical authority is `dict` envelope + ordered `list` children:
  - BI: `dict` root containing `plot_roadmap: list[dict]`
  - TR: canonical `dict.blocks`, not raw top-level list
- The remaining raw-list support is compatibility tolerance, not the canonical contract.

## Direct Answer

- Stage0 answer for question 1: `dict` is the canonical shape, but Stage0 still has the heaviest `list` presence because roadmap/block sequencing is intrinsic to the stage.
- Stage0 answer for question 2: no active Stage0 `PWF` runtime loop was found in the inspected live Stage0 authority files. Stage0 uses validation and handoff normalization, not `PASS_WITH_FIX` patch/re-audit flow.

## Side-Effect Coverage

- File write/artifact generation: not authoritative for this question; not inspected beyond contract-producing helpers.
- DB writes: not applicable to the bounded question.
- JSONL/log/audit sinks: not material to the answer.
- Console/UI output: Stage0 menu/UI exists, but it is not part of the `list` vs `dict` contract answer.
- Retry/recovery: no Stage0 `PWF` retry loop found in inspected authority files.
- Cache/global state: not material.
- Config/env/bootstrap fallback: not material.

## Pass 3. Operating Consequence

- If a new Stage0 contract is added, it should follow the current canonical direction: `dict` wrapper first, ordered `list` nested inside it where sequencing matters.
- Treat raw top-level treatment `list` as backward-compatibility input, not as the shape to extend.
- Do not assume Stage0 already has `PWF` semantics just because later stages do.

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- Scope stayed bounded to Stage0 live authority surfaces.
- Canonical/compat distinction is explicit.

### Pass 2. Evidence and Consistency

- BI/TR assertions were checked against `modules/core/response_schemas.py`.
- Roadmap payload shape was checked against `modules/core/stage0_handoff.py`.
- No Stage0-local `PASS_WITH_FIX` loop was found in the inspected authority set.

### Pass 3. Execution and Readability

- The document answers both user questions directly.
- Compatibility-vs-canonical consequences are explicit enough for follow-on design work.

Confidence: `96%`
