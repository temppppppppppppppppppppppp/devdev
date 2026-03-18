# Geuldobi V2 Legacy Survey Reentry Aggregate Execution Roadmap

Date: 2026-03-17
Status: completed (all 3 items realized and closed)
Canonical Path: `docs/2026-03-17/geuldobi-v2-legacy-survey-reentry-execution-roadmap.md`
Temp Mirror Path: `removed 2026-03-18`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Queue Snapshot:
- `stage23-semantic-transport-restoration`
- `stage0-stage2-substrate-hardening`
- `stage23-semantic-validation-hardening`
Confidence After 3-Pass Audit: `96%`

## 1. Purpose
- govern the execution-ready subset extracted from three re-audited legacy survey drafts
- record the realized closure state of the execution queue extracted from the re-audited legacy surveys
- prevent direct execution from the broad integrated survey

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `stage23-semantic-transport-restoration` | `docs/2026-03-17/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md` | `removed 2026-03-18` | completed | realized: relationship rationale merge/backfill + `rationale_digest` carry-over + operator-visible stop-line truncation note |
| `stage0-stage2-substrate-hardening` | `docs/2026-03-17/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md` | `removed 2026-03-18` | completed | realized: Bible completeness warning gate + Treatment continuity + injected/existing roadmap validation + PASS_WITH_FIX floor + CDB snapshot |
| `stage23-semantic-validation-hardening` | `docs/2026-03-17/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md` | `removed 2026-03-18` | completed | realized: typed `scene_breakdown` schema/model path + downstream tactical advisories + compare-mode NPC fidelity check |

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
  - richer semantic carry-over reaches Stage 4 and stop-line truncation becomes operator-visible instead of silently collapsing
- closure action:
  - completed on 2026-03-18; temp mirror removed and queue refreshed
- status: **completed** — `relationship_delta` now preserves or merges `trigger` / `justification`, `rationale_digest` reaches Stage 4 tier1, and stop-line truncation widened (300→800 / 200→500) with explicit transported note

### stage0-stage2-substrate-hardening
- completion signal:
  - Stage 0 minimum gates and Stage 2 correctness contracts are explicit and test-covered
- closure action:
  - completed on 2026-03-18; temp mirror removed and queue refreshed
- status: **completed** — Bible completeness warning gate (5 checks with top-level protagonist fact awareness), Treatment details cross-batch continuity, plot_roadmap validation on injected and preexisting paths, PASS_WITH_FIX quality floor, and ConstraintDB snapshot/restore including item registry state

### stage23-semantic-validation-hardening
- completion signal:
  - structural validation is no longer purely form-biased for the targeted slices
- closure action:
  - completed on 2026-03-18; temp mirror removed and queue exhausted
- status: **completed** — typed `scene_breakdown` schema/model path plus main ensemble schema enforcement, tactical named-anchor + action-density advisories, and Arc NPC fidelity checks retained through Director compare mode

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
- confirmed the three-item bundle was exhausted and its temp queue artifacts were removed on 2026-03-18
