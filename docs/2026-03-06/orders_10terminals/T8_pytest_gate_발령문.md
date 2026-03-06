# T8 발령문 - pytest 게이트

## 미션
- 계약/분기/오류코드 회귀를 자동 테스트로 고정.

## 시작 조건
- 모드: `CODE_LOCK` 또는 `CODE_OPEN`
- 선행 의존: `T1`, `T2`, `T3` 동결 완료
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. key/sub_key 분기 테스트 작성/보강
2. Mode B prompt 왕복/timeout 테스트 작성/보강
3. 위험키 승인 4케이스 테스트 작성/보강
4. 중복 실행/stop 멱등성 테스트 점검

## 최소 커버 항목
- `SUB_KEY_REQUIRED`
- `SUB_KEY_NOT_ALLOWED`
- `INVALID_SUB_KEY`
- `RUN_ALREADY_ACTIVE`
- `INVALID_PROMPT_ID`
- `PROMPT_ALREADY_RESOLVED`
- `RISK_APPROVAL_REQUIRED`
- `RISK_APPROVAL_EXPIRED`
- `RISK_APPROVAL_DUAL_CONTROL_REQUIRED`

## 산출물
- `tests/*` 테스트 코드 또는 테스트 명세

## 완료 기준
1. 핵심 케이스 누락 0건
2. 실패 시 즉시 원인 식별 가능
3. 릴리즈 게이트 증빙에 연결 가능

## handoff
- `docs/2026-03-06/handoff/T8-handoff.md`


