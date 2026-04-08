# Wuxguide Delegation Bootstrap

Date: 2026-04-08
Status: active
Family: `wuxguide`

## 1. Role

This is the first-read bootstrap for delegated or external models working on one `wuxguide` task.

Read this before:

- `wuxia-planning-harness.md`
- `wuxia-production-harness.md`
- `wuxia-bi-production-harness.md`

## 2. First Read Order

1. `material_ssot/README.md`
2. `material_ssot/00_governance/delegation-envelope-spec-v1.md`
3. work-level current-truth doc if it exists
4. `SSOT_wuxguide-integrated-order.md`
5. the task-specific harness only after the envelope is known

Current-root rule:

- `material_ssot/` plus live artifact paths are the current root
- when a work-level current-truth doc says the saved boundary is smaller than the filename implies, the saved boundary wins
- historical handoff docs are guidance only until their content is actually merged into the live `TR` file

## 3. Task Entry By Envelope

### 3.1 `canon_tighten`

Read:

- `material_ssot/20_pitch/README.md`
- `material_ssot/20_pitch/pitch-philosophy.md`
- `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
- target candidate/canon file

Write:

- target candidate/canon file only

### 3.2 `phase0_build`

Read:

- `wuxia-planning-harness.md`
- target pitch authority
- preprocess 4-pack
- work-level current-truth doc when it exists

Write:

- `treatments/phase0/{work_id}_phase0_design.json` only

### 3.3 `root_admit`

Read:

- work-level current-truth doc
- target pitch authority or nearest authority anchor named by that doc
- only the specific legacy `Phase0` / `TR` / `BI` / `work_guard` / handoff files named by that doc or the operator order
- `wuxia-planning-harness.md` or `wuxia-production-harness.md` only as needed by the admitted artifact type

Write:

- current-root `Phase0`, live `TR`, or live `BI` files only as explicitly named by the operator order
- current-truth doc only if the saved-boundary location changes

### 3.4 `tr_continue`

Read:

- `wuxia-production-harness.md`
- current root `Phase0`
- current live `TR`
- work-level current-truth doc
- latest authoritative handoff note only when the current-truth doc keeps it in the entry set

Write:

- current live `TR` file only

### 3.5 `tr_merge_rebuild`

Read:

- everything required for `tr_continue`
- only the specific handoff docs named by the current-truth doc or operator order

Write:

- current live `TR` file
- current-truth doc only if the saved boundary changes

### 3.6 `bi_refresh`

Read:

- `wuxia-bi-production-harness.md`
- current pitch authority
- current root `Phase0`
- current live `TR`
- current live `BI`
- current-truth doc when it exists

Write:

- current live `BI` file only

## 4. No-Touch Rules

- do not edit shared governance or family SSOT docs during normal work-level delegation
- do not infer merged truth from `tr_block_070_draft` naming alone
- do not silently promote handoff-only Block 22-25 style summaries into live truth
- do not jump from pitch directly to `TR` or `BI` unless the envelope explicitly allows it

## 5. One-Line Rule

`For wuxguide delegation, saved boundary beats filename, current truth beats handoff memory.`
