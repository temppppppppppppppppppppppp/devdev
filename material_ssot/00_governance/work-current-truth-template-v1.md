# Work Current-Truth Template v1

Date: 2026-04-08
Status: active
Scope: template for work-level current-truth docs used by operators and delegated models

## 1. Role

Use this template when a work has live or in-flight artifacts that are easy to misread from filenames or older handoff notes.

Recommended path:

- `docs/YYYY-MM-DD/{work_id}_live_status.md`

This document is not the pitch truth itself. It is the operator-facing answer to:

- what is the current saved boundary
- which files are authoritative right now
- which older docs are historical only
- what task is allowed next

## 2. Required Sections

### 2.1 `Operator Reading`

Must state:

- `inventory role`
- `operational state`
- `schema status`
- `benchmark alias`
- `benchmark freshness`

### 2.2 `Current Live Artifacts`

List the actual current files:

- canon pitch when present
- preprocess bundle when relevant
- root `Phase0`
- live `TR`
- live `BI`
- published `work_guard` when relevant

If a saved boundary matters, state it here explicitly.

### 2.3 `Boundary Rule`

Must explain:

- where the live saved truth ends
- whether older handoff docs are merged truth or guidance only
- whether filename shape is misleading

### 2.4 `Next Allowed Tasks`

State the next legal tasks in plain language.

Examples:

- `TR continue: Block 26-30 into the same live TR file`
- `TR merge/rebuild: reconstruct Block 22-25 into the same live TR file first`
- `canon tighten only; do not jump to Phase0 yet`

### 2.5 `Known Non-Truth Docs`

List docs that may be useful context but must not be mistaken for current saved truth.

### 2.6 `Delegation Rule`

State the minimum current-truth entry set for a delegated model.

## 3. Examples

Current examples:

- `docs/2026-04-08/jangyeongshil_industrial_revolution_live_status.md`
- `docs/2026-04-08/manual_meridian_archivist_live_status.md`
- `docs/2026-04-08/hoegui_surgeon_live_status.md`
- `docs/2026-04-08/quiet_chaebol_heir_live_status.md`
- `docs/2026-04-08/jaebeol3se_loss_line_live_status.md`

## 4. One-Line Rule

`If a work can be misread from filenames or old handoffs, give it a current-truth doc before delegating it.`
