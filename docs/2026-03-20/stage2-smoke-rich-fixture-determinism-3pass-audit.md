# Stage2 Smoke Rich-Fixture Determinism Audit

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage2-smoke-rich-fixture-determinism-3pass-audit.md`
Related Execution SSOT: `docs/2026-03-20/stage2-smoke-rich-fixture-determinism-execution-ssot.md`
Related Closure Item: `docs/2026-03-20/smoke-fixture-alignment-execution-ssot.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: post-run roadmap queue, smoke verification outputs, active temp roadmap`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/smoke-fixture-alignment-execution-ssot.md`
- `docs/2026-03-20/rol-post-run-execution-roadmap.md`
Evidence Artifacts:
- `scripts/run_stage2_smoke.py`
- `projects/코덱스_테스트/logs/smoke_fixture_prep.json`
- `projects/코덱스_테스트/plans/arcs/arc_1.json`
- `projects/코덱스_테스트/plans/arcs/arc_2.json`
- `projects/코덱스_테스트/plans/arcs/arc_3.json`
- `projects/smoke_fixture_demo/`
Side-Effect Coverage: covered

## 1. Purpose

Classify the residual warning cluster seen after the successful smoke-fixture verification run.

The question is narrow:
- was the remaining Stage2 warning/failure-report cluster still part of fixture alignment, or
- did the verification expose a new bounded smoke-harness determinism issue?

## 2. Baseline Facts

- `python scripts/prepare_smoke_fixture.py --force` restored `projects/코덱스_테스트` from canonical source `projects/smoke_fixture_demo`.
- the restored disposable target already contains a rich baseline:
  - arcs: `3`
  - latest blueprint number: `11`
  - manuscripts: `0`
- the original residual smoke run wrote `projects/코덱스_테스트/logs/arc_4_failure_report.txt`.
- the same residual run also wrote `projects/코덱스_테스트/logs/artifacts/stage2/arc_004/`.
- `scripts/run_stage2_smoke.py` hardcodes a mock Director result of:
  - `decision=PASS`
  - `score=82`
  - `reason=mock ok`
- the Stage2 runtime treats a score below the quality threshold as reject/failure-report territory.

## 3. Classification

This is not fixture-poverty anymore.

The aligned fixture contract worked:
- desktop spike ran
- Stage3 smoke ran
- Stage4 smoke ran
- Stage2 smoke used the same disposable target
- no historical audit project was used as the live target

The residual issue is different:
- the canonical smoke source is intentionally preseeded with `3` arcs
- Stage2 smoke therefore resumes from `arc_004` instead of exercising a fresh bounded `arc_001~003` run
- the mock Director score of `82` then guarantees a quality-gate failure for that resumed arc

So the residual cluster is best classified as:
- `real follow-up`
- `bounded smoke-harness determinism issue`
- not a blocker for smoke-fixture alignment closure

## 4. Why It Matters

If left as-is, Stage2 smoke gives a misleading success shape:
- exported `arc_1~3` files can look like a fresh Stage2 pass
- but those files come from the inherited rich fixture baseline
- the actual fresh run work is the failed `arc_004` continuation path

That weakens smoke meaning and can confuse later live-merge audits.

## 5. Split Decision

- close `smoke-fixture-alignment` as completed
- open one new bounded execution item:
  - `stage2-smoke-rich-fixture-determinism-execution-ssot`
- keep this new item ahead of the Stage4 observability queue items because it affects the reliability of future bounded smoke evidence

## 6. Resolution Outcome

The bounded determinism issue is resolved.

Implemented changes:
- the smoke runner resets inherited Stage2 arc state before execution
- the mock Director score moved to a pass-side contract
- the smoke-only commit seam now returns truthy success instead of committing and then being treated as failure
- smoke-only `NarrativeAnalyzer` and `perf_timer` seams are stabilized for deterministic execution
- the runner now fails closed if failure reports are written or if fewer than `3` arcs are saved

Verified closure:
- `python -m pytest tests/test_smoke_fixture_contract.py -q`
- `python -m pytest tests/test_smoke_fixture_tools.py -q`
- `python scripts/prepare_smoke_fixture.py --force`
- `python scripts/run_stage2_smoke.py`

Observed outcome:
- no `logs/arc_*_failure_report.txt`
- `plans/arcs/arc_1.json`
- `plans/arcs/arc_2.json`
- `plans/arcs/arc_3.json`
- bounded fresh `3`-arc output instead of inherited `arc_004` continuation noise

## 7. Confidence

- pass 1:
  - verification outputs and live smoke artifacts checked
- pass 2:
  - realization rerun confirmed the bounded smoke path
- pass 3:
  - closure consequences and queue impact rechecked
- estimated confidence:
  - `0.98`
