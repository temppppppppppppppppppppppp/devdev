# T2 발령문 - API Contract 동결

## 미션
- `docs/implementation/api-contract-v1.yaml` 동결.

## 시작 조건
- 모드: `CODE_LOCK` 또는 `CODE_OPEN`
- 선행 의존: 없음
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. `/run`, `/run/{run_id}/input`, `/stop`, `/status` 계약 점검
2. 오류코드 enum 점검:
   - `INVALID_KEY`
   - `SUB_KEY_REQUIRED`
   - `SUB_KEY_NOT_ALLOWED`
   - `INVALID_SUB_KEY`
   - `RUN_ALREADY_ACTIVE`
   - `RISK_APPROVAL_REQUIRED`
   - `RISK_APPROVAL_EXPIRED`
   - `RISK_APPROVAL_DUAL_CONTROL_REQUIRED`
   - `INVALID_PROMPT_ID`
   - `PROMPT_ALREADY_RESOLVED`
3. `RunRequest` 필드(`key/sub_key/inputs/approval_id`) 고정

## 산출물
- 변경 파일: `docs/implementation/api-contract-v1.yaml`

## 완료 기준
1. 경로/응답코드 정의 누락 0건
2. T1/T3와 필드명/이벤트명 충돌 0건
3. 오류코드 표준 일치

## handoff
- `docs/2026-03-06/handoff/T2-handoff.md`


