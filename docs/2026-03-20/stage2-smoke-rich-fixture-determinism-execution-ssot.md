# Stage2 Smoke Rich-Fixture Determinism Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage2-smoke-rich-fixture-determinism-execution-ssot.md`
Temp Mirror Path: `removed at closure`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: post-run roadmap queue, smoke verification outputs, active temp roadmap`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/stage2-smoke-rich-fixture-determinism-3pass-audit.md`
- `docs/2026-03-20/smoke-fixture-alignment-execution-ssot.md`
- `docs/2026-03-20/rol-post-run-execution-roadmap.md`
Evidence Artifacts:
- `scripts/run_stage2_smoke.py`
- `projects/코덱스_테스트/logs/smoke_fixture_prep.json`
- `projects/코덱스_테스트/plans/arcs/arc_1.json`
- `projects/코덱스_테스트/plans/arcs/arc_2.json`
- `projects/코덱스_테스트/plans/arcs/arc_3.json`
- `projects/smoke_fixture_demo/`
- `tests/test_smoke_fixture_contract.py`
- `tests/test_smoke_fixture_tools.py`
Side-Effect Coverage: covered

## 1. Intent

Make Stage2 smoke deterministic on the canonical rich fixture.

The target behavior is simple:
- Stage2 smoke should verify a bounded fresh Stage2 run
- it should not accidentally resume from inherited `arc_004`
- it should not rely on a mock Director score that guarantees quality-gate failure

## 2. Baseline Facts

- the canonical smoke source intentionally contains `3` arcs and `11` blueprints
- the original smoke harness used the live disposable DB as-is
- the original mock Director score was fixed at `82`
- the original verification run therefore produced `arc_4_failure_report.txt` and `stage2/arc_004/`
- this is a smoke-harness determinism issue, not a fixture-alignment issue

## 3. Scope

Included:
- `scripts/run_stage2_smoke.py`
- minimal helper or bounded fixture-reset logic if needed
- focused tests for deterministic Stage2 smoke start state

Excluded:
- general Stage2 runtime redesign
- smoke target renaming
- Stage3/Stage4 smoke redesign
- broader live-run roadmap changes beyond queue ordering

## 4. Realization Architecture

### Tranche 1. Explicit bounded start state
- before Stage2 smoke starts, make the Stage2 start state explicit
- acceptable implementations:
  - clear or shadow inherited arc anchor state inside the disposable target before the smoke run, or
  - build a Stage2-only disposable snapshot with zero arcs but the same canonical lineage

### Tranche 2. Deterministic pass-side mock semantics
- the Stage2 smoke mock Director should not guarantee quality-gate failure by construction
- use a bounded pass-side score/decision contract that lets the intended smoke path complete

### Tranche 3. Smoke seam stabilization
- treat smoke-only collaborator seams as harness responsibilities
- acceptable bounded stabilizers:
  - truthy commit callback contract
  - deterministic analyzer stub
  - no-op perf timer
  - fail-closed output verification

### Tranche 4. Regression lock
- add focused regression that proves:
  - Stage2 smoke on the canonical rich fixture no longer writes `arc_4_failure_report.txt` on the baseline path
  - the smoke run no longer depends on inherited `arc_001~003` to look successful

## 5. Acceptance Criteria

- Stage2 smoke on `projects/코덱스_테스트` exercises a bounded fresh Stage2 pass path
- no baseline `arc_4_failure_report.txt` is written during the normal deterministic smoke run
- exported Stage2 smoke arcs reflect newly exercised smoke output, not inherited fixture arcs only
- desktop/Stage3/Stage4 smoke contracts remain unchanged

## 6. Validation Plan

- focused tests for the Stage2 smoke harness contract
- rerun:
  - `python scripts/prepare_smoke_fixture.py --force`
  - `python scripts/run_stage2_smoke.py`
- confirm:
  - no `logs/arc_*_failure_report.txt` on the baseline run
  - `plans/arcs/arc_1.json`
  - `plans/arcs/arc_2.json`
  - `plans/arcs/arc_3.json`
- UTF-8 hygiene
- `git diff --check`
- `python scripts/ops_validator.py`

## 7. Queue Priority

- priority:
  - `1`
- rationale:
  - directly follows smoke-fixture verification
  - future smoke evidence remains noisier until this is fixed

## 8. Closure Note

Realization completed on `2026-03-20`.

What landed:
- bounded Stage2 reset of inherited rich-fixture arc state
- pass-side Director mock semantics
- smoke-only commit callback fix
- smoke-only analyzer/perf-timer stabilization
- fail-closed post-run verification instead of manual fallback save

Verification evidence:
- `python -m pytest tests/test_smoke_fixture_contract.py -q`
- `python -m pytest tests/test_smoke_fixture_tools.py -q`
- `python scripts/prepare_smoke_fixture.py --force`
- `python scripts/run_stage2_smoke.py`

Observed closure state:
- no `logs/arc_*_failure_report.txt`
- `plans/arcs/arc_1.json`
- `plans/arcs/arc_2.json`
- `plans/arcs/arc_3.json`

Residual risk:
- the smoke harness still uses bounded synthetic collaborators by design; this item does not upgrade Stage2 smoke into a full live LLM verification run

## 9. Confidence

- pass 1:
  - residual cluster and code path aligned
- pass 2:
  - scope bounded to smoke harness determinism
- pass 3:
  - closure state checked against active roadmap
- estimated confidence:
  - `0.98`
