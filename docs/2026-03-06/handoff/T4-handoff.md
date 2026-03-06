# T4 Handoff — /run 검증 로직

- 작성: 2026-03-06
- 담당: T4 (/run validator)
- last_seen_broadcast_seq: [2026-03-06T00:00:00+09:00] CODE_LOCK 선언

---

## 결론

`modules/api/run_validator.py` 구현 완료. 5개 오류코드 전량 계약과 일치. 회귀 테스트 47개 PASS.

---

## 구현 내용

**파일:** `modules/api/run_validator.py`

### 검증 함수 시그니처

```python
def validate_run_request(
    key: str,
    sub_key: Optional[str],
    runner_state: str,
) -> ValidationResult:
```

### 검증 순서 (4단계)

| 순서 | 조건 | 오류코드 | HTTP |
|---|---|---|---|
| 1 | `key not in ALLOWED_KEYS` | `INVALID_KEY` | 400 |
| 2a | `key=="0"` and `sub_key` 없음 | `SUB_KEY_REQUIRED` | 400 |
| 2b | `key=="0"` and `sub_key not in ALLOWED_SUB_KEYS` | `INVALID_SUB_KEY` | 400 |
| 3 | `key!="0"` and `sub_key is not None` | `SUB_KEY_NOT_ALLOWED` | 400 |
| 4 | `runner_state == "running"` | `RUN_ALREADY_ACTIVE` | 409 |

### 허용 상수

```python
ALLOWED_KEYS = {"0","1","2","3","4","5","6","44","77","88","99"}
ALLOWED_SUB_KEYS = {"0","1","2","3","4","5","6"}
RISK_KEYS = {"44","77","88","99"}
```

---

## 테스트 결과

**파일:** `tests/test_run_validator.py` — 47개 케이스

| 분기 | 케이스 수 | 결과 |
|---|---|---|
| INVALID_KEY | 7 | PASS |
| SUB_KEY_REQUIRED | 2 | PASS |
| INVALID_SUB_KEY | 5 | PASS |
| SUB_KEY_NOT_ALLOWED | 10 | PASS |
| RUN_ALREADY_ACTIVE | 5 | PASS |
| 정상 통과 (non-zero keys) | 10 | PASS |
| 정상 통과 (key=0 sub_keys) | 7 | PASS |
| 비running 상태 통과 | 1 | PASS |

---

## 완료 기준 점검

| 기준 | 결과 |
|---|---|
| 계약 오류코드와 실제 반환코드 일치 | ✅ 5개 전량 일치 |
| 분기별 회귀 테스트 통과 | ✅ 47/47 PASS |
| 로그에 원인 코드가 남음 | ✅ `logger.warning("INVALID_KEY key=%r", key)` 등 전 분기 기록 |

---

## T5/T7 인계 사항

- `validate_run_request()` 는 FastAPI 라우터에서 `/run` handler 진입 직후 호출하면 됨
- `runner_state` 는 싱글톤 `RunnerState.state` 를 주입
- `RISK_KEYS` 상수를 T6의 `RiskApprovalGate` 와 공유 (`from modules.api.run_validator import RISK_KEYS`)
