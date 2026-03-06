# Release Gate v1

## Purpose
- Define explicit Go/No-Go rules for the desktop PoC release.
- Prevent deployment when required evidence files are missing.

## Gate Policy
1. All gates must be `PASS`; any single `FAIL` means `NO-GO`.
2. Missing required evidence file is an automatic `NO-GO`.
3. Risk operation controls (`44/77/88/99`) must include approval evidence.

## Gate Mapping (Execution Order v2 §7)
| Gate | Required rule | Minimum evidence |
|---|---|---|
| `G1` | 계약 3종(`prompt-map-v1.json`, `api-contract-v1.yaml`, `event-schema-v1.json`) 동결 확인 | 계약 3종 파일 존재 + `T0-broadcast.md`의 `[PHASE_A_G1_PASS]` 기록 |
| `G2` | `/run` validator + `RISK_*` 분기 동작 확인 | QA 결과에 `SUB_KEY_*`, `INVALID_SUB_KEY`, `RISK_APPROVAL_*` 분기 확인 기록 |
| `G3` | smoke summary 상태 `passed` | `artifacts/smoke/smoke-summary.json` |
| `G4` | pytest 핵심 케이스 통과 | `pytest tests/ -q` 실행 결과(요약 로그 또는 리포트) |
| `G5` | 필수 증빙 파일 존재 | Required Evidence Files 전 항목 |
| `G6` | 위험 승인 샘플 로그 검증 | `risk-approval-log.jsonl` 또는 동등 샘플 로그 |

## Required Evidence Files
| Gate | Evidence file | Owner | Rule |
|---|---|---|---|
| Feature/E2E | `qa-report-v1.16.md` | QA Lead | Must exist and include `TC-P0`, `TC-S1~S4`, `TC-OS`, `TC-RISK` |
| Stability | `run-stability-report.md` | Backend Lead | Must exist and include retry/idempotency checks |
| Security/Signing | `security-signoff.md` | Ops/Security | Must exist and include checksum verification |
| Deployment/Rollback | `release-runbook-check.md` | Release Manager | Must exist and include 5-minute rollback drill |
| Risk Approval Audit | `risk-approval-log.jsonl` | Ops | Must exist and include at least 1 valid approval record |
| Smoke Automation | `artifacts/smoke/smoke-summary.json` | QA/Backend | Must exist and `status=passed` |

## Auto No-Go Conditions
- `G1` 증빙(`계약 3종` + `[PHASE_A_G1_PASS]`) 누락.
- `G2` 증빙(`/run` + `RISK_*` 분기 확인 기록) 누락.
- `G4` 증빙(`pytest` 핵심 케이스 통과 결과) 누락.
- `artifacts/smoke/smoke-summary.json` missing.
- `risk-approval-log.jsonl` missing.
- Smoke summary reports `failed` or `network_error`.
- Any required evidence file exists but is empty (0 bytes).

## Approval Sign-off
| Role | Name | Signature | Date |
|---|---|---|---|
| Product Owner |  |  |  |
| QA Lead |  |  |  |
| Backend Lead |  |  |  |
| Ops/Security |  |  |  |
| Release Manager |  |  |  |

## Final Decision
- Decision: `GO` / `NO-GO`
- Decision date:
- Notes:
