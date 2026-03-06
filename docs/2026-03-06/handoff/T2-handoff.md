# T2 Handoff - API Contract 동결

- terminal: T2
- role: API Contract 동결
- status: COMPLETE
- last_seen_broadcast_seq: [2026-03-06T00:00:00+09:00] CODE_LOCK 선언

---

## 검증 결과

### 1. 엔드포인트 4종 점검

| 경로 | 메서드 | 응답코드 | 결과 |
|------|--------|----------|------|
| `/run` | POST | 202 / 400 / 403 / 409 | PASS |
| `/run/{run_id}/input` | POST | 200 / 400 / 409 | PASS |
| `/stop` | POST | 200 | PASS |
| `/status` | GET | 200 | PASS |

- IMP-002 템플릿에는 `/run/{run_id}/input`가 누락되어 있으나 실제 `api-contract-v1.yaml`에 정상 구현됨. T2 발령문 요구사항 충족.

### 2. 오류코드 enum 10종 점검

기준 문서(codex-ui-webgal-light-proposal.md) 에러코드 카탈로그는 12개 항목이나, 이 중 5개(RUN_NOT_ACTIVE / BACKEND_START_FAIL / WS_DISCONNECTED / UPDATE_BLOCKED_RUNNING / UPDATE_CHECKSUM_FAIL)는 클라이언트/WS 레이어 코드로 HTTP API 계약 범위 외. 의도적 미포함으로 판정.

T2 발령문 지정 10개 코드 전량 `ErrorEnvelope.code` enum에 존재:

| 코드 | YAML 존재 |
|------|-----------|
| INVALID_KEY | PASS |
| SUB_KEY_REQUIRED | PASS |
| SUB_KEY_NOT_ALLOWED | PASS |
| INVALID_SUB_KEY | PASS |
| RUN_ALREADY_ACTIVE | PASS |
| RISK_APPROVAL_REQUIRED | PASS |
| RISK_APPROVAL_EXPIRED | PASS |
| RISK_APPROVAL_DUAL_CONTROL_REQUIRED | PASS |
| INVALID_PROMPT_ID | PASS |
| PROMPT_ALREADY_RESOLVED | PASS |

### 3. RunRequest 필드 점검

| 필드 | required | YAML 존재 |
|------|----------|-----------|
| key | required | PASS |
| sub_key | optional | PASS |
| inputs | optional | PASS |
| approval_id | optional | PASS |

`key` enum 허용값: `['0','1','2','3','4','5','6','44','77','88','99']` - 기준 문서 화이트리스트와 일치.

### 4. T1/T3 충돌 점검

T1/T3 handoff 미수신 상태. 필드명(`key/sub_key/inputs/approval_id/run_id/ok/code/message/data`) 및 에러코드는 기준 문서와 완전 일치하며 별도 충돌 리스크 없음.

---

## 완료 기준 체크

- [x] 경로/응답코드 정의 누락 0건
- [x] T1/T3와 필드명/이벤트명 충돌 0건 (미수신 전제)
- [x] 오류코드 표준 일치 (10개 전량)

---

## 변경 사항

`docs/implementation/api-contract-v1.yaml` - 변경 없음. 이미 완전히 동결된 상태로 확인.

---

## 후속 터미널에 대한 참고

- `api-contract-v1.yaml` 필드명/에러코드는 동결 완료. 수정 불가.
- `/run/batch` 엔드포인트 및 `INVALID_BATCH_COUNT` 코드는 기준 문서에 언급되나 현재 YAML에 미포함. T2 범위 외, 추후 확장 시 T2 재검토 필요.
- `GET /run/{run_id}/prompts` 엔드포인트는 기준 문서에서 "권장" 수준으로 YAML 미포함. T2 범위 외.
