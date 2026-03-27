# Temp Execution Queue Process Health Scorecard

Date: 2026-03-27
Status: final
Scope: `system-maturity-next-band-wave1 tranche2 operator discipline`

## 1. Executive Read
- overall color: amber
- why: active queue remains open but governance is healthy

## 2. Dimensions

| Dimension | Status | Evidence | Notes |
| --- | --- | --- | --- |
| governance alignment | green | `AGENTS.md`, `docs/implementation/operations-governance-map.md` | `AGENTS.md`, init harness, and governance map are present |
| queue integrity | green | `python scripts/ops_validator.py --strict` | strict validator passes |
| canonical/mirror sync | green | `python scripts/ops_validator.py` | canonical and temp queue artifacts are in sync |
| evidence freshness | amber | `none` | one or more active queue items do not have an evidence manifest |
| side-effect coverage | green | `docs/2026-03-27/system-maturity-next-band-wave1-execution-ssot.md` | all active execution docs declare `Side-Effect Coverage: covered` |
| exception debt | green | `none` | no active exception docs detected |
| validator status | green | `python scripts/ops_validator.py --strict` | validator is clean |
| closure readiness | amber | `docs/temp/queue-state.json` | active queue items remain pending or in progress |

## 3. Immediate Actions
- keep queue-state and validator in sync after each execution-doc change
