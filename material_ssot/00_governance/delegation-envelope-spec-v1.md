# Delegation Envelope Spec v1

Date: 2026-04-08
Status: active
Scope: normalized task envelopes for delegated or external-model work on the material-side order

## 1. Role

Use this document when a delegated model must be given one bounded task without a long custom explanation every time.

This spec does four things:

- names the allowed task envelopes
- fixes the minimum input set for each envelope
- fixes the allowed write scope for each envelope
- forbids silent stage jumps

## 2. Global Hard Laws

- one delegated task must map to exactly one envelope
- if a work-level current-truth document exists, read it before any older handoff or summary doc
- current-root `material_ssot/` and live artifact paths override older legacy path hints when they conflict
- when a work is split between current-root artifacts and legacy in-flight residue, the operator order or current-truth doc must say whether the next task is `root_admit` or an ordinary downstream envelope
- shared governance docs and family SSOT docs are read-only unless the task is explicitly a harness/governance task
- do not widen a task into a later stage just because the next step seems obvious
- if a task boundary is unclear, stay at the earlier stage and report the stop reason

## 3. Envelope Catalog

### 3.1 `canon_tighten`

- role:
  - tighten or revise a fresh candidate or canon pitch without starting downstream artifacts
- minimum inputs:
  - `material_ssot/20_pitch/README.md`
  - `material_ssot/20_pitch/pitch-philosophy.md`
  - `material_ssot/20_pitch/material-benchmark-readiness-harness-v1.md`
  - target candidate/canon file
  - work-level current-truth doc if it exists
- allowed outputs:
  - target candidate/canon markdown only
- forbidden jumps:
  - no `Phase0`, `TR`, `BI`, or pair registry edits
- minimum validation:
  - `python -X utf8 scripts/material_readiness_validator.py --path <target-md>`

### 3.2 `phase0_build`

- role:
  - build or revise `Phase0` from a pitch-side authority plus preprocess handoff
- minimum inputs:
  - family delegation bootstrap
  - family planning harness
  - target pitch authority file
  - `treatments/preprocess/{work_id}/source_manifest.json`
  - `treatments/preprocess/{work_id}/profile_lock.json`
  - `treatments/preprocess/{work_id}/material_bundle_summary.json`
  - `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`
  - work-level current-truth doc if it exists
- allowed outputs:
  - `treatments/phase0/{work_id}_phase0_design.json`
- forbidden jumps:
  - no `TR` or `BI` generation
- minimum validation:
  - `python scripts/stage0_handoff_validator.py --work-id {work_id}`

### 3.3 `root_admit`

- role:
  - admit or normalize legacy in-flight artifacts into current-root paths before ordinary `TR`/`BI` continuation
- minimum inputs:
  - work-level current-truth doc
  - family delegation bootstrap when it exists
  - target pitch authority or nearest authority anchor named by the current-truth doc
  - only the specific legacy `Phase0` / `TR` / `BI` / `work_guard` / handoff files named by the current-truth doc or operator order
- allowed outputs:
  - current-root `treatments/phase0/...json`
  - current-root live `TR` file
  - current-root live `BI` file when explicitly requested
  - work-level current-truth doc when the saved-boundary location changes
- forbidden jumps:
  - no new story continuation beyond the already saved boundary
  - no benchmark, alias, or registry edits
  - do not invent saved live truth from handoff prose that was never serialized
- minimum validation:
  - every admitted JSON file must parse
  - the saved-boundary statement in the current-truth doc must match the admitted current-root artifact after the task
  - when a current-root file already exists, the task must explicitly preserve or supersede it according to the current-truth doc or operator order

### 3.4 `tr_continue`

- role:
  - continue an already materialized live `TR` boundary
- minimum inputs:
  - family delegation bootstrap
  - family production harness
  - work-level current-truth doc
  - current `Phase0` file
  - current live `TR` file
  - latest authoritative handoff only when the current-truth doc explicitly says it is still relevant
- allowed outputs:
  - current live `TR` file only
- forbidden jumps:
  - no file rename
  - no merge of unsaved handoff memory unless the task is explicitly `tr_merge_rebuild`
  - no `BI` refresh in the same task
- minimum validation:
  - current `TR` JSON must remain parseable after each bounded save
  - obey family block-count cap

### 3.5 `tr_merge_rebuild`

- role:
  - reconstruct or merge handoff-only `TR` material into the live saved `TR` boundary
- minimum inputs:
  - everything required by `tr_continue`
  - only the specific handoff docs named by the current-truth doc or operator order
- allowed outputs:
  - current live `TR` file
  - optional work-level current-truth doc update if the saved boundary changes
- forbidden jumps:
  - do not treat handoff summaries as merged truth until they are serialized into the live `TR` file
  - do not rename the live `TR` file in the same task unless the task is explicitly a rename migration
- minimum validation:
  - current `TR` JSON must parse
  - saved boundary stated in current-truth doc must match the serialized file after the merge

### 3.6 `bi_refresh`

- role:
  - refresh or rebuild a `BI` from the current pitch/Phase0/TR truth
- minimum inputs:
  - family delegation bootstrap
  - family BI harness
  - target pitch authority file
  - current `Phase0`
  - current live `TR`
  - current live `BI` if it exists
  - work-level current-truth doc if it exists
- allowed outputs:
  - target `BI` file only
- forbidden jumps:
  - no `TR` continuation inside the same task
  - no pair benchmark or alias regrade inside the same task unless explicitly requested
- minimum validation:
  - `BI` JSON must parse
  - if the work is a tracked live pair, re-run the pair normalization check

## 4. Current-Truth Rule

When a work has `docs/YYYY-MM-DD/{work_id}_live_status.md` or an equivalent current-truth doc:

- that doc wins over older handoff summaries for task start
- filename heuristics do not beat saved-boundary statements
- historical handoff docs may still be used as input, but only inside the envelope named by the current-truth doc or operator order

## 5. One-Line Rule

`Give the delegated model one envelope, one write scope, one current truth, and one validation path.`
