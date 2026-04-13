# Stage4 Style Guide Anchor Fallback Compact Survey

Date: 2026-04-12
Status: active
Confidence: `97%`
Canonical Path: `docs/2026-04-12/stage4-style-guide-anchor-fallback-compact-survey.md`
Scope: `Stage0 style_guide anchor reuse -> Stage4 session style fallback prompt`
Track: system-track

## 1. Answer First

Yes, this is a real bounded operator-friction seam, and it is small enough to promote directly into execution without opening a brand-new queue family.

The current live workspace already proves that the project can hold a persisted `style_guide`, but `Stage4` can still re-prompt the operator with `1.카카오 / 2.네이버` because persisted-style reuse is incorrectly gated by `stage0_available` instead of project-local style-guide truth.

Recommended owner:

- keep this under `0_0-stage234-cross-stage-contract-normalization-remediation`
- treat it as a bounded cross-stage contract slice rather than a new top-level Stage4 lane

## 2. Evidence

### 2.1 Persisted style truth already exists in the project

- `projects/000_0412-1/project_data.db` contains `anchors.key = "style_guide"` with a populated serialized payload
- `projects/000_0412-1/stage0_output/style_guide.json` exists and contains:
  - `tone = 진지`
  - `pov = 혼합`
  - `selected_primary_pov = 혼합`
  - `effective_primary_pov = 혼합`
  - `external_pov_insert_policy = 제한적 허용`
  - non-empty `reference_excerpt`

### 2.2 Stage4 still prompts from a fallback branch

- `modules/core/stage4_orchestrator.py`
  - `_resolve_session_style_guide(...)` loads persisted style only when `saved_style and stage0_available`
  - it also builds a Bible-POV minimum guide only when `not style_guide and stage0_available`
  - otherwise it falls back to the operator prompt:
    - `👉 스타일 선택 (1.카카오 / 2.네이버)`

### 2.3 The gate is global/module availability, not project-local readiness

- `modules/core/stage4_orchestrator.py`
  - `_load_session_runtime_dependencies()` imports `STAGE0_AVAILABLE` from `modules.core.spinners`
  - this is then passed into `_prepare_session_style_payload(...)`
- therefore the Stage4 prompt can appear even when the project already has persisted style-guide truth

### 2.4 Stage0 does already persist style-guide truth

- `modules/core/stage01_helpers.py`
  - reverse-engineering and style-analysis paths both call `save_v20_anchor("style_guide", ...)`
- this means the missing piece is not generation, but reliable downstream reuse

## 3. Semantic Classification

### Class A. Proven seam

- persisted `style_guide` truth exists
- Stage4 can still ask the operator for platform style
- the re-prompt is therefore unnecessary fallback behavior, not missing project data

### Class B. Likely root cause

- persisted-style reuse is over-gated by `stage0_available`
- Stage4 is treating `Stage0 module availability` as if it were `project style-guide availability`

### Class C. Bounded execution shape

1. decouple persisted-style reuse from `stage0_available`
2. allow a Stage0-free load path from:
   - anchor first
   - `stage0_output/style_guide.json` second
3. when the operator does choose `카카오/네이버` fallback, persist a backward-compatible minimal style anchor so the same question does not repeat next time

## 4. Side-Effect Notes

- file writes / artifacts:
  - may update project-local style-guide anchor or stage0-style fallback metadata
- DB / schema:
  - anchor update only; no schema migration needed
- console / UI:
  - removes unnecessary `카카오 / 네이버` prompt when persisted style truth already exists
- retry / recovery:
  - not applicable beyond session-style hydration
- config / env:
  - not applicable

## 5. Recommendation

Promote this immediately as a bounded tranche under the existing cross-stage contract lane.

Do not open a new queue family.

## 6. 3-Pass Audit Record

Pass 1:

- confirmed the question is about persisted style reuse, not manuscript DB persistence
- bounded the seam to `Stage0 style truth -> Stage4 style hydration`

Pass 2:

- verified project-local truth exists in both DB anchor and `stage0_output/style_guide.json`
- verified Stage4 fallback prompt is still reachable from code

Pass 3:

- verified the likely fix is small, local, and queue-compatible
- concluded existing `0_0-stage234-cross-stage-contract-normalization-remediation` is the right owner
