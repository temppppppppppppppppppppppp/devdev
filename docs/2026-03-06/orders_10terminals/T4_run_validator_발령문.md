# T4 발령문 - /run 검증 로직

## 미션
- `/run` 검증 경로를 계약대로 구현/검증.

## 시작 조건
- 모드: `CODE_OPEN`
- 선행 의존: `T1`, `T2` 동결 완료
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. key 화이트리스트 검증
2. `key=0`에서 `sub_key` 필수 검증
3. `key!=0`에서 `sub_key` 금지 검증
4. 잘못된 `sub_key` 검증
5. running 중 중복 실행 차단(`RUN_ALREADY_ACTIVE`)

## 기대 오류
- `INVALID_KEY`
- `SUB_KEY_REQUIRED`
- `SUB_KEY_NOT_ALLOWED`
- `INVALID_SUB_KEY`
- `RUN_ALREADY_ACTIVE`

## 산출물
- 백엔드 검증 코드 변경
- 필요 시 테스트 보완

## 완료 기준
1. 계약 오류코드와 실제 반환코드 일치
2. 분기별 회귀 테스트 통과
3. 로그에 원인 코드가 남음

## handoff
- `docs/2026-03-06/handoff/T4-handoff.md`


