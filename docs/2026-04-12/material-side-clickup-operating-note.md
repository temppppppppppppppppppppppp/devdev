# Material-Side ClickUp Operating Note

Date: 2026-04-12
Status: active
Scope: material-side production schedule ClickUp mirror

## 1. Purpose

This note fixes the operating meaning of:

- `재료 사이드 clickup 업데이트해`

That request now means:

1. rebuild the material-side queue snapshot
2. sync the current material schedule inventory into the ClickUp production schedule list
3. refresh existing task fields/body instead of touching the system-track ClickUp queue

## 2. Target Surface

Current target list:

- ClickUp List: `1_글도비 - 생산 스케줄`
- List ID: `901817297564`

Current material sync artifacts:

- `docs/temp/material-queue-state.json`
- `docs/temp/clickup-material-sync-state.json`

Current operator entry points:

- `python -X utf8 scripts/sync_material_clickup_queue.py --list-id 901817297564`
- `python -X utf8 scripts/setup_material_clickup_views.py --list-id 901817297564`

## 3. Default Inclusion Rule

Default behavior is `stage-visible material schedule`.

Include by default:

- `canon stage`
- `TR/BI production stage`
- `BI production complete`

Current stage mapping:

- canon anchor only, no live sequential production pointer:
  - ClickUp status `to do`
- live sequential production in flight, including `bi_handoff`:
  - ClickUp status `in progress`
- live pair complete / BI complete:
  - ClickUp status `complete`

Exclude by default:

- retired canon docs
- known negative-exemplar live rows
- stale docs without a canon or sequential production pointer

If the operator explicitly wants a narrower active-only mirror, use:

- `python -X utf8 scripts/sync_material_clickup_queue.py --list-id 901817297564 --active-only`

## 4. Current Field Contract

The production schedule list is field-ready for:

- `Work ID`
- `Material Stage`
- `Ops State`
- `Current Truth Path`
- `Sequential Status Path`
- `Last Sequential Block Pass`
- `Next Unit Type`
- `Next Block ID`
- `Resume Basis`
- `Production Complete`
- `BI Complete`
- `Updated At`

## 5. Separation Rule

Do not mix this lane with the system-track ClickUp queue.

System-track queue mirror remains separate:

- `docs/temp/queue-state.json`
- `docs/temp/clickup-sync-state.json`

Material-side queue mirror remains separate:

- `docs/temp/material-queue-state.json`
- `docs/temp/clickup-material-sync-state.json`

## 6. One-Line Rule

`재료 사이드 clickup 업데이트해` means: sync the stage-visible material schedule lane to the production schedule list, not the system queue.
