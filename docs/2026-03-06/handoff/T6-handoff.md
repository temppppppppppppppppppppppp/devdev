# T6 Handoff — 위험키 승인 게이트

- 작성: 2026-03-06
- 담당: T6 (Risk Approval)
- last_seen_broadcast_seq: [2026-03-06T00:00:00+09:00] CODE_LOCK 선언

---

## 결론

`modules/api/risk_approval.py` 구현 완료. 4케이스(없음/만료/2인미충족/정상) 전량 통과. 감사 로그 추적 가능. 회귀 테스트 13개 PASS.

---

## 구현 내용

**파일:** `modules/api/risk_approval.py`

### 클래스 구조

```
ApprovalRecord (dataclass)
    approval_id, key, ticket_id, requested_by
    approved_by_primary, approved_by_secondary
    reason, created_at, expires_at, status

RiskApprovalGate
    __init__(store, audit_log_path)
    register(record)          # 승인 레코드 주입
    validate(key, approval_id, operator, _now) → ValidationResult
    _write_audit(...)         # logs/risk-approval-log.jsonl 추가
```

### 검증 순서 (4단계)

| 순서 | 조건 | 오류코드 | HTTP |
|---|---|---|---|
| 1 | `approval_id` 없음 또는 빈 문자열 | `RISK_APPROVAL_REQUIRED` | 403 |
| 2 | `approval_id` 가 store 에 없음 | `RISK_APPROVAL_REQUIRED` | 403 |
| 3 | `now > record.expires_at` | `RISK_APPROVAL_EXPIRED` | 403 |
| 4 | `approved_by_primary == approved_by_secondary` | `RISK_APPROVAL_DUAL_CONTROL_REQUIRED` | 403 |
| 통과 | 위 조건 없음 | `OK` | 202 |

### 감사 로그 스키마 (JSONL)

```json
{
  "log_id": "uuid",
  "ts": "ISO8601",
  "key": "44",
  "approval_id": "APR-...",
  "operator": "op1",
  "verdict": "OK | RISK_APPROVAL_*",
  "ok": true,
  "ticket_id": "OPS-...",
  "approved_by_primary": "alice",
  "approved_by_secondary": "bob",
  "expires_at": "ISO8601"
}
```

### 시각 주입 (_now 파라미터)

- `validate(_now=datetime(...))` — 테스트 시 실제 시계 의존 제거
- 운영 코드에서는 `_now=None` (기본값) → `datetime.now(tz=timezone.utc)` 사용

---

## 테스트 결과

**파일:** `tests/test_risk_approval.py` — 13개 케이스

| 분기 | 케이스 수 | 결과 |
|---|---|---|
| RISK_APPROVAL_REQUIRED (없음/빈값/미등록) | 3 | PASS |
| RISK_APPROVAL_EXPIRED | 1 | PASS |
| RISK_APPROVAL_DUAL_CONTROL_REQUIRED | 1 | PASS |
| 정상 통과 (4개 위험키) | 4 | PASS |
| 감사 로그 성공 기록 | 1 | PASS |
| 감사 로그 실패 기록 | 1 | PASS |
| 감사 로그 누적 | 1 | PASS |
| 만료 로그 검증 | 1 | PASS |

---

## 완료 기준 점검

| 기준 | 결과 |
|---|---|
| 승인 4케이스(없음/만료/2인미충족/정상) 분기 통과 | ✅ 전량 통과 |
| 감사로그 추적 가능 | ✅ approval_id + ticket_id + approvers + timestamps |
| 계약 오류코드와 일치 | ✅ 3개 RISK_APPROVAL_* 코드 전량 일치 |

---

## 감사 로그 기본 경로

- `logs/risk-approval-log.jsonl` (프로젝트 루트 기준)
- 디렉토리 없으면 자동 생성 (`mkdir -p` 등가)
- 기록 실패 시 예외 삼킴 + `logger.exception()` 기록 (비치명)

---

## T7/FastAPI 인계 사항

- `/run` handler 에서 T4 검증 통과 후, `key in RISK_KEYS` 이면 `RiskApprovalGate.validate()` 호출
- `approval_id` 는 `RunRequest.approval_id` 필드에서 추출
- `operator` 는 세션/인증 컨텍스트에서 주입
- `store` 는 운영 환경에서 DB 또는 외부 approval 서비스로 교체 가능 (인터페이스 동일)
