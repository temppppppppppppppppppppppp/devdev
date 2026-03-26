# OPUS Parallel Narrative Operations Order

Date: 2026-03-26
Track: narrative pipeline
Status: active
Scope: 4 practical works only

## 1. Operating Principle

This order uses `work-level parallelism` and forbids `same-work concurrent editing`.

Core rule:

- works may run in parallel
- inside one `work_id`, progression remains serial
- one `work_id` must have exactly one editing owner at a time
- one turn advances exactly one unit for that work
- `Stage 0 -> Planning -> Production -> BI` order may not be skipped
- `Production` lane is limited to one frontline work at a time

Reason:

- local SSOT requires `1턴 1단위`
- Stage 0 artifacts are the gate for Planning
- Production is block-by-block and audit-bound
- same-work parallel edits create drift in `phase0_design`, TR, BI, and audit state

## 2. Common Rules For All OPUS Workers

- UTF-8 only
- read the router and family SSOT before editing
- do not edit another worker's `work_id`
- do not jump from Stage 0 directly to TR
- do not jump from Planning directly to BI
- if stage evidence conflicts, stop and report the conflict first
- end each run with exactly these fields:
  - `work_id`
  - `current_stage`
  - `finished_unit`
  - `changed_files`
  - `next_unit`
  - `stop_reason`

## 3. Lane Layout

### Frontline Lane

- exactly one work may sit here
- allowed stage: `Planning` or `Production`
- purpose: turn ready material into the next canonical artifact without queueing multiple manual-audit bottlenecks

### Upstream Lane

- Stage 0 and early Planning works may run in parallel
- purpose: keep the next frontline candidates warm
- preferred output: locked Stage 0 artifacts or a clear Planning-ready state

### Reconciliation Lane

- use when legacy artifacts and current stage interpretation conflict
- purpose: resolve stage truth before fresh generation
- do not generate TR/BI while reconciliation is unresolved

## 4. Current Assignment Table

### OPUS-A

- `work_id`: `pantech_cyworld_reborn`
- family: `blockguide`
- current stage: `Planning`
- lane: `frontline`
- current goal: advance one `phase0_design` planning unit only
- start files:
  - `treatments/preprocess/pantech_cyworld_reborn/source_manifest.json`
  - `treatments/preprocess/pantech_cyworld_reborn/profile_lock.json`
  - `treatments/preprocess/pantech_cyworld_reborn/material_bundle_summary.json`
  - `treatments/preprocess/pantech_cyworld_reborn/phase0_ready_snapshot.json`
  - `docs/blockguide/treatment-planning-harness.md`
- fixed constraints:
  - preserve 2006~2007 Korean IT transition timing
  - preserve Pantech + Cyworld dual-revival engine
  - preserve telecom certification / QA / first-screen / payment chokepoints
  - preserve audit / succession / capital-structure pressure as simultaneous antagonism

### OPUS-B

- `work_id`: `fallen_prince_buys_joseon`
- family: `blockguide`
- current stage: `Stage 0 preprocess`
- lane: `upstream`
- current goal: build Stage 0 artifacts from canonical evidence, one unit at a time
- start files:
  - `docs/2026-03-10/opus_망국황자는조선을산다.md`
  - `bible/_quarantine/05_bi_fallen_prince_buys_joseon.json`
  - `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
  - `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
  - `전처리_ssot/docs/stage0_source_manifest_harness.md`
  - `전처리_ssot/docs/stage0_profile_lock_harness.md`
  - `전처리_ssot/docs/stage0_material_collection_harness.md`
- caution:
  - this work has salvageable macro architecture but strong skeleton risk
  - Stage 0 must lock historical finance battlefield before any fresh Planning

### OPUS-C

- `work_id`: `medical_wanderer`
- family: `blockguide`
- current stage: `identity lock before Stage 0`
- lane: `upstream`
- current goal: determine canonical source set first, then decide Stage 0 entry
- start files:
  - `bible/기록/medical_wanderer_bi.json`
  - `전처리_ssot/기획안/07_medical_회귀외과의.md`
  - `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
  - `전처리_ssot/docs/stage0_source_manifest_harness.md`
- caution:
  - current BI record and current medical pitch may not be the same work
  - do not generate Stage 0 until work identity is explicitly locked

### OPUS-D

- `work_id`: `wuxia_heavenly_physician`
- family: `wuxguide`
- current stage: `planning-ready reconciliation`
- lane: `reconciliation`
- current goal: reconcile current router truth, preprocess truth, and legacy artifact placement; then choose exactly one next unit
- start files:
  - `treatments/preprocess/wuxia_heavenly_physician/source_manifest.json`
  - `treatments/preprocess/wuxia_heavenly_physician/profile_lock.json`
  - `treatments/preprocess/wuxia_heavenly_physician/material_bundle_summary.json`
  - `treatments/preprocess/wuxia_heavenly_physician/phase0_ready_snapshot.json`
  - `docs/wuxguide/wuxia-planning-harness.md`
- caution:
  - do not assume old `phase0_design` quarantine placement means fresh Production should start immediately
  - resolve stage truth first

## 5. Priority Order

1. `pantech_cyworld_reborn`
2. `fallen_prince_buys_joseon`
3. `medical_wanderer`
4. `wuxia_heavenly_physician`

Interpretation:

- `pantech_cyworld_reborn` is the active frontline candidate
- `fallen_prince_buys_joseon` is the next most valuable upstream build
- `medical_wanderer` needs identity truth before any heavy work
- `wuxia_heavenly_physician` should not consume frontline bandwidth until reconciliation is done

## 6. Stop Conditions

Stop immediately and report if any of the following occurs:

- Stage evidence and router stage disagree
- UTF-8 parse fails
- `manual_audit_pass` gate is missing where required
- canonical source and reference-only source cannot be cleanly separated
- another worker has already modified the same `work_id`
- the next step would skip a required stage

## 7. Handoff Format

Each worker must end with this flat report:

```text
work_id: ...
current_stage: ...
finished_unit: ...
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 8. 3-Pass Self Audit

### Pass 1. Contract Alignment

- kept the order inside narrative-track SSOT boundaries
- preserved `1 work = 1 editing owner`
- preserved `1 turn = 1 unit`

### Pass 2. Operational Usefulness

- each worker has a lane, stage, starting files, and immediate goal
- the order separates frontline, upstream, and reconciliation work so queue collisions are reduced

### Pass 3. Integrity

- saved under dated `docs/2026-03-26/`
- UTF-8 only
- no same-work parallel editing instructions
