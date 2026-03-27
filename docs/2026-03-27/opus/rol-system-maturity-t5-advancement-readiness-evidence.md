Date: 2026-03-27
Type: evidence manifest (T5 lane)
Parent Report: `docs/2026-03-27/opus/rol-system-maturity-t5-advancement-readiness.md`

## Control Inventory

| Control | Path | Type | LOC | Exercised |
|---|---|---|---|---|
| Release Gate v1 | `docs/implementation/release-gate-v1.md` | Policy doc | 54 | Never |
| Risk Approval Checklist | `docs/implementation/risk-approval-checklist.md` | Checklist | 27 | Unknown |
| Risk Approval Gate | `modules/api/risk_approval.py` | Production code | 214 | 1 record (rejection) |
| Risk Approval Tests | `tests/test_risk_approval.py` | Test suite | - | Yes |
| Risk Approval Log | `logs/risk-approval-log.jsonl` | Audit log | 1 | 1 record |
| Run Validator | `modules/api/run_validator.py` | Production code | 95 | Yes (always-on) |
| Run Validator Tests | `tests/test_run_validator.py` | Test suite | - | Yes |
| Ops Validator | `scripts/ops_validator.py` | Automation | 306 | Yes (passing --strict) |
| Ops Validator Harness | `docs/implementation/ops-validator-harness.md` | Harness | 66 | Yes |
| Stage 3 Canary | `scripts/run_stage3_canary.py` | Automation | - | Unknown |
| Stage 3+4 Canary | `scripts/run_stage34_canary.py` | Automation | - | Unknown |
| Stage 4 Canary | `scripts/run_stage4_canary.py` | Automation | ~120 | Yes (2026-03-27) |
| Regression Tiers | `scripts/regression_validation_tiers.py` | Inventory | 60 | Partial |
| Health Scorecard Harness | `docs/implementation/process-health-scorecard-harness.md` | Harness | 39 | Yes |
| Health Scorecard Script | `scripts/populate_process_health_scorecard.py` | Automation | 169 | Once (2026-03-14) |
| Health Scorecard Instance | `docs/2026-03-14/temp-execution-queue-process-health-scorecard.md` | Output | 27 | 2026-03-14 |
| Exception Registry Harness | `docs/implementation/exception-registry-harness.md` | Harness | 36 | Never |
| Stale Sweep Harness | `docs/implementation/stale-reference-sweep-harness.md` | Harness | 57 | Yes |
| Stale Sweep Script | `scripts/run_stale_reference_sweep.py` | Automation | 106 | Once (2026-03-14) |
| Stale Sweep Output | `docs/2026-03-14/operations-governance-stale-reference-sweep.md` | Output | - | 2026-03-14 |
| Smoke Stage 2 | `scripts/run_stage2_smoke.py` | Automation | - | Unknown |
| Smoke Stage 3 | `scripts/run_stage3_smoke.py` | Automation | - | Unknown |
| Smoke Stage 4 | `scripts/run_stage4_smoke.py` | Automation | - | Unknown |
| E2E Menu Smoke | `scripts/e2e_menu_smoke.ps1` | Automation | - | Unknown |

## Live Evidence (2026-03-27)

| Artifact | Type | Key Result |
|---|---|---|
| `docs/2026-03-27/chaebol-ent-empire-revival-canary-report.md` | Canary | TR+BI consumability PASS, 0 errors |
| `docs/2026-03-27/chaebol-ent-empire-revival-stage-probe-report.md` | Stage probe | Stage 0→2→3 chain PASS |
| `docs/2026-03-27/chaebol-ent-empire-stage4-canary-report.md` | Stage 4 canary | Full S2→3→4 chain, manuscript produced |
| `docs/temp/queue-state.json` | Queue state | empty, 0 items |

## Historical Evidence

| Artifact | Date | Key Result |
|---|---|---|
| `docs/2026-03-23/fresh-run-3pass-audit-report.md` | 2026-03-23 | 213 LLM calls, 4 manuscripts, 0 P0 |
| `docs/2026-03-23/current-state-situation-survey-report.md` | 2026-03-23 | Stabilization mode, 97% confidence |
| `docs/2026-03-20/TF-static-complexity-audit-v2.md` | 2026-03-20 | 180+=0, 100+=171 |
| `docs/2026-03-14/temp-execution-queue-process-health-scorecard.md` | 2026-03-14 | 7/8 green, 1 amber |

## Advancement Entry Guard Scorecard

| # | Condition | Score | Notes |
|---|---|---|---|
| 1 | Real operator-facing gate | 0.3 | Built but never exercised |
| 2 | Repeatable canary | 0.7 | Exercised once, no cadence |
| 3 | Exception handling discipline | 0.2 | Harness built, 0 records |
| 4 | Observable health reporting | 0.5 | Infrastructure complete, 13 days stale |
| 5 | Multiple current evidence sources | 0.9 | Canary triad + fresh run + ops validator |
| **Total** | **Majority threshold (3/5)** | **2.6/5** | **Not met** |

## Missing Artifacts

| Expected | Path | Status |
|---|---|---|
| Smoke summary | `artifacts/smoke/smoke-summary.json` | Directory missing |
| Release gate sign-off | `docs/implementation/release-gate-v1.md` rows 42-48 | Empty |
| Approved risk record | `logs/risk-approval-log.jsonl` | Only rejections |
| Current scorecard | `docs/2026-03-27/*scorecard*` | Does not exist |
| Exception records | `docs/2026-*/exception-*` | None found |
