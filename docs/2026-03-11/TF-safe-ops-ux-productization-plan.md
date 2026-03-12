# TF Safe Ops UX Productization Plan

Date: 2026-03-11
Status: IMPLEMENTED
Confidence: 97%
Encoding: UTF-8

## Scope

Safe operation buttons in the desktop UI currently exist, but they are still operator-hostile:

- `Rollback`
- `Wipe`
- `Reset`
- `Rewind`

The backend consistency layer is already repaired, including `director_selections.stage` split and stage-aware cleanup. The remaining gap is UX:

- there is no read-only impact preview,
- there is no stage-aware explanation of what will be deleted vs preserved,
- destructive confirmation still uses a generic browser `confirm()`,
- the current UI does not surface the new Stage 2 vs Stage 4 split to the operator.

This batch productizes Safe Ops without changing the actual destructive semantics.

## 3-Pass Audit

### Pass 1. Correctness

Current code facts:

- Safe-op buttons exist in desktop UI:
  - `Rollback` / `Wipe` / `Reset` / `Rewind`
- Current renderer confirmation is still generic:
  - `정말 실행하시겠습니까? / 되돌릴 수 없습니다`
- Backend already exposes exact rollback impact counts via `DBManager.get_rollback_impact(target_ep)`.
- Backend cleanup semantics are now stage-aware:
  - Stage 2 reset/rewind clears Stage 2 `director_selections`
  - episode rollback/wipe clears Stage 4 `director_selections`

Therefore the missing work is not backend safety logic but operator visibility and action clarity.

### Pass 2. Safety

This batch must remain read-only before execution:

- preview endpoint must not mutate DB,
- preview endpoint must never call `reset_after()` or service methods,
- confirm modal must not bypass existing backend risk flow,
- target-specific deletion logic must remain in existing backend runtime paths.

### Pass 3. Completeness

This batch is complete if all of the following are true:

1. Desktop can fetch a project-scoped safe-op preview.
2. UI shows, per action:
   - what is deleted,
   - what is preserved,
   - which stage selection history is affected.
3. Destructive actions use a dedicated modal instead of raw `confirm()`.
4. Runbook text matches the new UI wording.

## Current UX Problems

### P1. Generic confirm

Current renderer confirmation uses one generic browser dialog for all destructive actions.

Result:

- `Rollback` and `Reset` feel equally vague even though their blast radius is different.
- Stage-aware deletion semantics are invisible.

### P1. No impact preview

The system knows a lot more than it shows:

- latest episode,
- stage stats,
- rollback impact counts,
- artifact ladder state.

But Safe Ops still gives the operator almost no preview.

### P1. No preserved-vs-deleted split

The real operator question is not just “how dangerous is this?”

It is:

- what will be removed,
- what will remain usable afterward,
- whether setup surfaces such as BI/TR/style/work guard survive.

### P2. Stage split is invisible

The `director_selections.stage` split is fixed in backend, but the UI does not explain:

- Stage 2 reset/rewind affects Stage 2 selection history,
- episode rollback/wipe affects Stage 4 review history.

## Implementation Plan

### 1. Read-only preview endpoint

Add a bridge endpoint that returns safe-op preview data for the selected project.

Return shape:

- project status:
  - latest episode
  - current arc count
- per action preview:
  - title
  - summary
  - deletes[]
  - preserves[]
  - notes[]
  - optional impact counts for actions that can be previewed safely without extra prompts

Rules:

- `reset` preview uses project-wide stage/design and downstream blast description
- `wipe` preview uses episode-derived artifact counts from `target_ep=1`
- `rollback` preview is generic until target episode is chosen in runtime
- `rewind` preview is generic until target arc is chosen in runtime

### 2. Electron IPC wiring

Expose one read-only IPC method:

- `bridge:get-safe-ops-preview`

### 3. Renderer Safe Ops panel

Add a compact Safe Ops preview surface near operations:

- per-action cards or rows
- deleted vs preserved lists
- stage-aware notes
- current project context

### 4. Dedicated confirm modal

Replace generic destructive `confirm()` with a dedicated modal that shows:

- action title,
- short summary,
- deleted,
- preserved,
- note on Stage 2 vs Stage 4 selection history,
- final confirm button.

The actual runtime target prompt still comes from existing backend flow.

## Out of Scope

- undo stack
- snapshot backup/restore
- target-aware pre-prompt UI replacing runtime prompt broker
- changing backend destructive semantics

## Acceptance Criteria

1. `Safe Ops` preview is available for the selected project.
2. `Rollback`, `Wipe`, `Reset`, `Rewind` no longer use raw browser `confirm()`.
3. UI explicitly distinguishes:
   - setup/config preserved data
   - downstream deleted data
   - Stage 2 vs Stage 4 selection handling
4. Existing destructive commands still execute through current backend flow.

## Recommended Order

1. `bridge_server.py`
2. `main.js`
3. `preload.js`
4. `index.html`
5. `runbook.md`

## Final Judgment

PASS.

This is a high-ROI UX batch because:

- the backend consistency work is already done,
- the product risk is operator confusion rather than algorithmic failure,
- the implementation can stay read-only before confirmation.

## Implementation Result

Implemented:

- `bridge_server.py`
  - `safe_ops` added to dashboard payload
  - `GET /safe-ops/preview`
- `main.js`
  - `bridge:get-safe-ops-preview`
- `preload.js`
  - `getSafeOpsPreview()`
- `index.html`
  - Safe Ops preview panel
  - dedicated destructive confirm modal
  - stage-aware deleted vs preserved explanation

Validation:

- `pytest tests/test_bridge_quality_summary.py -q` -> `6 passed`
- `node --check geuldobi-desktop/src/main.js`
- `node --check geuldobi-desktop/src/preload.js`
- `npm run start:spike` -> PASS
- `python -m pytest tests/ -q` -> `3880 passed, 16 skipped, 1 warning`
- `python -m pytest --collect-only -q tests` -> `3896 collected`

Known residual:

- `start:spike` auto-close 직전 `/quality/dashboard` fetch 실패 1회는 기존 종료 artifact로 유지
