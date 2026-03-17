# Geuldobi V2 Legacy Survey Reentry Aggregate Execution Roadmap

Date: 2026-03-17
Status: active
Canonical Path: `docs/2026-03-17/geuldobi-v2-legacy-survey-reentry-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: prior lane1~3 and follow-on item edits, runtime log, authority-hygiene changes, survey bundles, and local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; queue opened from re-audited legacy survey docs`
Queue Snapshot:
- `stage23-semantic-transport-restoration`
- `stage0-stage2-substrate-hardening`
- `stage23-semantic-validation-hardening`
Confidence After 3-Pass Audit: `96%`

## 1. Purpose
- govern the execution-ready subset extracted from three re-audited legacy survey drafts
- keep one roadmap SSOT for the new temp execution queue
- prevent direct execution from the broad integrated survey

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `stage23-semantic-transport-restoration` | `docs/2026-03-17/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md` | `docs/temp/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md` | active | restore trigger / rationale / carry-over survival into Stage 4 |
| `stage0-stage2-substrate-hardening` | `docs/2026-03-17/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md` | `docs/temp/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md` | active | Stage 0 quality floor, handoff contract, Stage 2 correctness |
| `stage23-semantic-validation-hardening` | `docs/2026-03-17/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md` | `docs/temp/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md` | active | scene schema, tactical specificity, bounded fidelity checks |

## 3. Dependency Graph
- `stage23-semantic-transport-restoration -> stage23-semantic-validation-hardening`
- `stage0-stage2-substrate-hardening -> stage23-semantic-validation-hardening`
- shared substrate:
  - landed provenance / budget ledgers
  - landed lane2 / lane3 gate semantics
- strategic reference only:
  - `ssot_integrated-survey.md` may inform later queue expansion but does not control this queue

## 4. Execution Order
1. `stage23-semantic-transport-restoration`
2. `stage0-stage2-substrate-hardening`
3. `stage23-semantic-validation-hardening`

Priority rationale:
- item 1 gives the fastest direct improvement to current Stage 4 output quality and reuses already-landed provenance work
- item 2 raises the upstream quality floor and hardens real correctness gaps without over-expanding scope
- item 3 should validate richer truth and clearer contracts, not today's thinner carry-over path

## 5. Per-Item Notes

### stage23-semantic-transport-restoration
- completion signal:
  - richer semantic carry-over reaches Stage 4 and is provenance-visible
- closure action:
  - remove its temp mirror and mark item completed

### stage0-stage2-substrate-hardening
- completion signal:
  - Stage 0 minimum gates and Stage 2 correctness contracts are explicit and test-covered
- closure action:
  - remove its temp mirror and mark item completed

### stage23-semantic-validation-hardening
- completion signal:
  - structural validation is no longer purely form-biased for the targeted slices
- closure action:
  - remove its temp mirror and mark item completed

## 6. Stop-Line
- do not execute directly from `ssot_integrated-survey.md`
- do not open live-run or benchmark lanes from this roadmap without a fresh queue
- before any code edit, re-run 3-pass audit on the targeted canonical SSOT and this roadmap against the then-current workspace

## 7. 3-Pass Audit Notes

### Pass 1. Coverage
- queue contains only execution-worthy material extracted from the legacy surveys

### Pass 2. Dependency
- ordering now matches shared substrate and validation dependencies

### Pass 3. ROI
- broad or already-landed integrated-survey material was kept out of the queue
