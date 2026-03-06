# T5 발령문 - Mode B 입력 라우트/WS 이벤트

## 미션
- `/run/{run_id}/input` 및 `prompt_*` 이벤트 왕복 경로 구현/검증.

## 시작 조건
- 모드: `CODE_OPEN`
- 선행 의존: `T2`, `T3` 동결 완료
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. `/run/{run_id}/input` 라우트 처리
2. `prompt_request` 발행 시 `prompt_id` 추적
3. 사용자 응답 시 `prompt_resolved` 발행
4. 타임아웃 시 `prompt_timeout` + default 적용
5. 중복 입력 차단(`PROMPT_ALREADY_RESOLVED`)

## 기대 오류
- `INVALID_PROMPT_ID`
- `PROMPT_ALREADY_RESOLVED`

## 산출물
- 입력 라우트 구현 코드
- WS 이벤트 처리 코드

## 완료 기준
1. `prompt_request -> input -> prompt_resolved` 왕복 성공
2. timeout 분기 정상 동작
3. 이벤트 스키마 검증 통과

## handoff
- `docs/2026-03-06/handoff/T5-handoff.md`


