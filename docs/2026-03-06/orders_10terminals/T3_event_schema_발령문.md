# T3 발령문 - Event Schema 동결

## 미션
- `docs/implementation/event-schema-v1.json` 동결.

## 시작 조건
- 모드: `CODE_LOCK` 또는 `CODE_OPEN`
- 선행 의존: 없음
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. 공통 필드 고정:
   - `event_version`
   - `seq`
   - `run_id`
   - `type`
   - `ts`
   - `payload`
2. `type` enum 점검:
   - `run_started`, `progress`
   - `prompt_request`, `prompt_resolved`, `prompt_timeout`
   - `run_completed`, `run_failed`
3. `prompt_*` 조건부 payload 필수 필드 점검

## 산출물
- 변경 파일: `docs/implementation/event-schema-v1.json`

## 완료 기준
1. JSON schema 파싱 성공
2. `prompt_*` 필수 필드 누락 0건
3. T2 API 계약과 이벤트명 충돌 0건

## handoff
- `docs/2026-03-06/handoff/T3-handoff.md`


