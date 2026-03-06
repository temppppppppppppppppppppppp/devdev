# T7 발령문 - 스모크 자동화

## 미션
- `scripts/e2e_menu_smoke.ps1` 기준으로 스모크 결과 산출 고정.

## 시작 조건
- 모드: `CODE_LOCK` 또는 `CODE_OPEN`
- 선행 의존: `T2` 동결 완료
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. 스모크 케이스 점검:
   - `SMK-MAIN-001`
   - `SMK-P0-001`
   - `SMK-P0-002`
   - `SMK-P0-003`
   - `SMK-RISK-001`
   - `SMK-STOP-001A/B`
2. 종료코드 규칙 점검(`0/1/2/3`)
3. 산출물 경로 고정:
   - `artifacts/smoke/smoke-summary.json`
   - `artifacts/smoke/smoke-results.jsonl`
   - `artifacts/smoke/smoke-failures.log`

## 산출물
- 스모크 스크립트/운영 메모
- 실행 결과 파일

## 완료 기준
1. summary 파일 생성
2. 실패 시 원인 코드/케이스 식별 가능
3. 재실행 시 동일 포맷 유지

## handoff
- `docs/2026-03-06/handoff/T7-handoff.md`


