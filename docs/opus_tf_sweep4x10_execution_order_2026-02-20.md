# OPUS TF Sweep 4x10 Execution Order (2026-02-20)

## 1) Mission
- Run the 4 sweep plans as a 10-cycle program.
- Do not run blind repeated scans.
- Use fixed loop per cycle: Detect -> Patch -> Re-validate -> Record delta.

## 2) Input Plans
- `docs/codex_lifecycle_sweep100_plan.md`
- `docs/codex_reverse_exception_sweep100_plan.md`
- `docs/codex_contract_compliance_sweep100_plan.md`
- `docs/codex_adversarial_sweep100_plan.md`

## 3) Hard Rules
- Every finding must include `file:line`, trigger condition, and impact stage.
- No "issue only by pattern match"; final evidence must be from manual code reading.
- Python/static checks are advisory only; final reject/accept decision is LLM or director policy.
- Do not report design intent as bug without contradiction evidence.
- No duplicate finding IDs across cycles. Re-open only with new evidence.
- One patch batch must be followed by tests and quick re-sweep before next cycle.

## 4) Team Topology Per Cycle
- TF-1: lifecycle sweep owner
- TF-2: reverse-exception sweep owner
- TF-3: contract-compliance sweep owner
- TF-4: adversarial sweep owner
- TF-5: integrator (dedupe, severity, merge)
- TF-6: patch owner
- TF-7: test and regression owner

## 5) Fixed Loop (Apply to Cycle 01..10)
1. Sweep Run
- TF-1..TF-4 run their assigned plans in parallel.
- Output raw findings to cycle workspace.

2. Merge and Dedupe
- TF-5 merges all findings.
- Remove duplicates and false positives.
- Assign severity: `P0`, `P1`, `P2`.

3. Patch Batch
- TF-6 patches only `P0/P1` selected for this cycle.
- Keep patch size bounded (recommend <= 5 issues per batch).

4. Test Gate
- TF-7 runs required tests (targeted + full suite if available).
- Record pass/fail and regression notes.

5. Quick Re-sweep
- TF-1..TF-4 run short verification on changed paths.
- Confirm fixed issues closed, check for regressions.

6. Cycle Close
- Update scorecard and carry-over backlog.
- Freeze outputs, then move to next cycle.

## 6) Cycle Deliverables
- `docs/opus_tf_cycleNN_findings.md`
- `docs/opus_tf_cycleNN_patchset.md`
- `docs/opus_tf_cycleNN_test_and_resweep.md`
- `docs/opus_tf_cycleNN_delta.md`
- `docs/opus_tf_4x10_master_scoreboard.md` (append every cycle)

## 7) Severity Policy
- `P0`: crash, data loss/corruption, rollback failure, wrong commit semantics, hard contract break.
- `P1`: deterministic wrong behavior, high-impact continuity break, retry/idempotency violation.
- `P2`: contained quality degradation, low-risk edge behavior, observability gap.

## 8) 10-Cycle Focus Map
- Cycle 01-02: baseline correctness, crash paths, contract hard breaks.
- Cycle 03-04: retry/fallback/rollback/idempotency.
- Cycle 05-06: state memory continuity, cross-stage data flow.
- Cycle 07-08: context truncation/budget fidelity and hidden regressions.
- Cycle 09: false-positive purge and intent-vs-bug final review.
- Cycle 10: stabilization run, closure report, remaining debt list.

## 9) Exit Criteria
- All discovered `P0` closed and revalidated.
- No new `P0` in final quick re-sweep.
- `P1` has explicit decision: fixed now or accepted debt with owner/date.
- Master scoreboard up to date for all 10 cycles.

## 10) Copy-Paste Order for OPUS
```text
Execute a 10-cycle program with 4 parallel sweeps:
1) docs/codex_lifecycle_sweep100_plan.md
2) docs/codex_reverse_exception_sweep100_plan.md
3) docs/codex_contract_compliance_sweep100_plan.md
4) docs/codex_adversarial_sweep100_plan.md

For each cycle:
Detect -> Merge/Dedupe -> Patch(P0/P1) -> Test -> Quick Re-sweep -> Close.

Mandatory finding schema:
- id
- severity(P0/P1/P2)
- file:line
- trigger condition
- impact stage
- why not design intent
- patch status
- revalidation result

Output files:
- docs/opus_tf_cycleNN_findings.md
- docs/opus_tf_cycleNN_patchset.md
- docs/opus_tf_cycleNN_test_and_resweep.md
- docs/opus_tf_cycleNN_delta.md
- docs/opus_tf_4x10_master_scoreboard.md
```
