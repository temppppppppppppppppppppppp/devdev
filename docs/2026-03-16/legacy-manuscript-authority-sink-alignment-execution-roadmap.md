<!-- [완료] -->
<\!-- [참고자료] -->
# Legacy Manuscript Authority Sink Alignment Execution Roadmap

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/legacy-manuscript-authority-sink-alignment-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: runtime/stage modules and tests, desktop package/icon/version files, project 0/000 artifacts and db, OPUS manuscript docs, and untracked 2026-03-16 survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-16/legacy-manuscript-fresh-run-post-run-merge-audit.md`
- `docs/2026-03-16/legacy-manuscript-contradiction-synthesis-master-report.md`
- `docs/2026-03-16/legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md`
Confidence: `97%`

## 1. Intent

Provide an explicit queue controller for the single active legacy-manuscript execution lane.

This roadmap exists because the operator explicitly requested a roadmap artifact after fresh-run revalidation, even though the queue currently contains one item only.

## 2. Queue Inventory

| Order | Status | Topic | Canonical Path | Temp Path |
| --- | --- | --- | --- | --- |
| 1 | completed | legacy manuscript authority sink alignment hardening | `docs/2026-03-16/legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md` | `docs/temp/legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md` |

## 3. Ordering Rationale

- there is only one active queue item
- fresh-run post-run merge evidence narrowed the lane but did not remove it
- the next action remains this lane because it is the only survivor after OPUS revalidation, real-manuscript survey, current recurrence review, and fresh-run merge audit

## 4. Execution Order

1. Re-audit the governing canonical SSOT against the live workspace immediately before code modification.
2. Implement final-authority contract hardening.
3. Harden analyzer/report/helper consumers so `director_selections` is not over-read as final truth.
4. Add bounded legacy mismatch handling for historical stale rows if the implementation shape requires it.
5. Run targeted verification, then close the SSOT and remove its temp mirror.

## 5. Acceptance And Cleanup

The roadmap is exhausted when:

- the single SSOT is realized and closed
- `docs/temp/legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md` is removed
- `docs/temp/execution-roadmap.md` is removed
- `docs/temp/queue-state.json` is refreshed or removed to reflect an empty queue

Closure status:

- the single SSOT has been realized and marked `closed`
- the temp mirror, temp roadmap, and queue-state snapshot were removed in this closure turn

## 6. Guardrails

- do not re-open broad manuscript contradiction remediation from this roadmap
- do not claim fresh-run reproduction if later implementation notes rely only on historical stale rows
- do not begin realization without a fresh current-state 3-pass audit of the governing SSOT

## 7. Closure Update

- realized files:
  - `modules/core/db_manager.py`
  - `modules/core/failure_analyzer.py`
  - `modules/core/stage4_canary_tools.py`
- verification:
  - `python -m py_compile modules/core/db_manager.py modules/core/failure_analyzer.py modules/core/stage4_canary_tools.py tests/test_db_manager.py tests/test_failure_analyzer.py tests/test_stage4_canary_tools.py`
  - `python -m pytest tests/test_db_manager.py`
  - `python -m pytest tests/test_failure_analyzer.py`
  - `python -m pytest tests/test_stage4_canary_tools.py`
- residual risk:
  - historical companion rows were not schema-backfilled; the lane closes on explicit authority resolution and consumer hardening
