# Stage0 Container And PWF Survey

Date: 2026-04-07
Status: final
Scope: system-track survey-only
Canonical Path: `docs/2026-04-07/stage0-container-and-pwf-survey.md`

Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 81 tracked, 52 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Container Verdict

Stage0 is mixed, but the runtime/canonical split is explicit.

- Runtime manager state keeps `treatment` as `list[dict[str, Any]]`.
  - `modules/core/stage0/__init__.py:90-94`
  - `modules/core/stage0/__init__.py:426`
  - `modules/core/stage0/__init__.py:503`
  - `modules/core/stage0/__init__.py:955-957`
- Canonical treatment handoff normalizes to a `dict` envelope with `blocks`.
  - `modules/core/stage0_handoff.py:154-166`
  - `modules/core/stage0_handoff.py:172-185`
  - `modules/core/stage0_handoff.py:293-307`
- Canonical validation explicitly requires `dict.blocks`, not a bare list.
  - `modules/core/response_schemas.py:980-1000`

Verdict:

- raw Stage0 generation path: `list`-leaning
- canonical Stage0 handoff: `dict`-authoritative

## 2. Downstream Handoff Meaning

Stage0 BI/TR handoff is not "list only".

- `plot_roadmap` is validated as `list` entries for Stage2 consumption.
  - `modules/core/stage0_handoff.py:516-549`
- The effective BI root is still a `dict`, and `plot_roadmap` is inserted under that root.
  - `modules/core/stage0_handoff.py:403-466`
  - `modules/core/stage0_handoff.py:469-513`

Interpretation:

- Stage0 produces repeated blocks as lists.
- But the handoff contract that later stages should trust is a `dict` wrapper containing those lists.

## 3. PWF Verdict

Stage0 does not run a `PASS_WITH_FIX` loop.

- Review contract is `PASS | RETRY | REJECT`.
  - `modules/core/stage0/story_expander.py:250-301`
- Fallback review also uses `PASS | RETRY | REJECT`.
  - `modules/core/stage0/story_expander.py:223-248`
- Save path persists `_stage0_review`, but not PWF fix instructions.
  - `modules/core/stage0/__init__.py:543-573`

Verdict:

- no Stage0 PWF
- bounded review gate only

## 4. Side-Effect Notes

Reviewed applicable side effects:

- Stage0 writes `bible.json`, `treatment.json`, and `stage0_state.json`.
- Stage0 also stamps `_stage0_review` into the bible before save.

These side effects do not change the verdict above:

- saved treatment artifact can still be raw-list shaped in the local Stage0 flow
- canonical normalization layer is the later authority boundary

## 5. 3-Pass Audit Record

### Pass 1. Structure and Scope

- Limited to Stage0 runtime, handoff, and validation surfaces.

### Pass 2. Evidence and Consistency

- Runtime list evidence and canonical dict evidence were both kept because they serve different authority layers.

### Pass 3. Execution and Readability

- Final verdict states the split explicitly so later operators do not confuse Stage0 runtime storage with authoritative handoff shape.

Confidence: `97%`
