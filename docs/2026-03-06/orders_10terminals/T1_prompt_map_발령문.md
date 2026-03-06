# T1 발령문 - Prompt Map 동결

## 미션
- `docs/implementation/prompt-map-v1.json` 동결.

## 시작 조건
- 모드: `CODE_LOCK` 또는 `CODE_OPEN`
- 선행 의존: 없음
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. key 전체(`0/1/2/3/4/5/6/44/77/88/99`) 존재 확인
2. `key=0`의 `requires_sub_key=true`, `allowed_sub_keys` 고정
3. 위험키(`44/77/88/99`)에 `requires_double_confirm`, `approval_policy` 고정
4. 기본값/범위(`default/min/max/options`) 누락 점검

## 산출물
- 변경 파일: `docs/implementation/prompt-map-v1.json`

## 완료 기준
1. key 누락 0건
2. 필수 필드 누락 0건
3. T2/T3와 필드명 충돌 0건

## handoff
- `docs/2026-03-06/handoff/T1-handoff.md`

