# T9 발령문 - 릴리즈 게이트/운영 증빙

## 미션
- `release-gate-v1.md` 기준으로 Go/No-Go 판정을 운영 문서로 고정.

## 시작 조건
- 모드: `CODE_LOCK` 또는 `CODE_OPEN`
- 선행 의존: `T7`, `T8` 결과 확보
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. 필수 증빙 파일 존재성 점검
2. `NO-GO` 자동 조건 점검:
   - smoke summary 누락
   - risk approval log 누락
   - smoke 상태 failed/network_error
   - 필수 증빙 0바이트
3. 승인 서명란/책임자 최신화
4. 운영 증빙 목록 정리

## 필수 증빙
- `qa-report-v1.16.md`
- `run-stability-report.md`
- `security-signoff.md`
- `release-runbook-check.md`
- `risk-approval-log.jsonl`
- `artifacts/smoke/smoke-summary.json`

## 산출물
- `docs/implementation/release-gate-v1.md` 갱신
- 최종 Go/No-Go 판정 메모

## 완료 기준
1. 증빙 누락 0건
2. `NO-GO` 조건 자동 적용 가능
3. 승인자/날짜/결론 기입 완료

## handoff
- `docs/2026-03-06/handoff/T9-handoff.md`


