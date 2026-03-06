# T8 Handoff — pytest 게이트

- 담당: T8 (테스트 자동화)
- 완료 시각: 2026-03-06
- last_seen_broadcast_seq: 0 (T0-broadcast 초기 상태)

---

## 산출물

- 파일: `tests/test_api_contract.py`
- 테스트 수: **50개**
- 결과: **50 passed, 0 failed** (0.53s)

---

## 커버 항목

### 오류코드 10종 전량 (T8 최소 커버 항목)

| 오류코드 | 테스트 클래스 | TC ID |
|----------|-------------|-------|
| `INVALID_KEY` | TestKeyValidation | TC-KEY-001 |
| `SUB_KEY_REQUIRED` | TestKeyValidation | TC-KEY-002 |
| `INVALID_SUB_KEY` | TestKeyValidation | TC-KEY-004 |
| `SUB_KEY_NOT_ALLOWED` | TestKeyValidation | TC-KEY-003 |
| `RUN_ALREADY_ACTIVE` | TestDuplicateRunRejection | TC-DUP-001 |
| `RISK_APPROVAL_REQUIRED` | TestRiskKeyApproval | TC-RISK-001 |
| `RISK_APPROVAL_EXPIRED` | TestRiskKeyApproval | TC-RISK-002 |
| `RISK_APPROVAL_DUAL_CONTROL_REQUIRED` | TestRiskKeyApproval | TC-RISK-003 |
| `INVALID_PROMPT_ID` | TestModeB | TC-PRM-001 |
| `PROMPT_ALREADY_RESOLVED` | TestModeB | TC-PRM-002 |

`TestErrorCodeCoverage` — 10개 코드 전량 도달 가능 + 정의 외 코드 미발생 확인.

### 기능별 커버

| 영역 | 테스트 클래스 | 케이스 수 |
|------|-------------|---------|
| key 화이트리스트 / sub_key 조건 | TestKeyValidation | 11 |
| 중복 실행 거절 (409) | TestDuplicateRunRejection | 3 |
| 위험키 승인 4케이스 (44/77/88/99 × 4시나리오) | TestRiskKeyApproval | 17 |
| Mode B 프롬프트 왕복 / timeout | TestModeB | 6 |
| stop 멱등성 | TestStopIdempotency | 4 |
| /status 반환 형식 | TestStatus | 3 |
| 오류코드 완전성 감사 | TestErrorCodeCoverage | 2 |
| **합계** | | **50** |

---

## 구현 방식

- **RouterStub** — BE 서버 미구현 단계이므로 계약 규칙(api-contract-v1.yaml + prompt-map-v1.json)을 Python 클래스로 내장. 오프라인 실행 가능.
- 서버 구현 후 `RouterStub` 메서드를 `requests` HTTP 호출로 교체하면 동일 테스트를 통합 게이트로 전환 가능.
- `time.sleep(0.01)` 1곳(만료 시나리오) 외 외부 의존성 없음.

---

## 완료 기준 충족 여부

| 기준 | 결과 |
|------|------|
| 핵심 케이스 누락 0건 | PASS (10종 전량 커버) |
| 실패 시 즉시 원인 식별 가능 | PASS (코드 assert 메시지 포함) |
| 릴리즈 게이트 증빙 연결 가능 | PASS (`pytest tests/test_api_contract.py -v` 단독 실행) |

---

## 실행 방법

```bash
pytest tests/test_api_contract.py -v
# 50 passed in 0.53s
```

---

## 후속 터미널 공지

- BE 서버 구현(T4/T5) 완료 시 `RouterStub`을 HTTP 클라이언트로 교체하여 E2E 게이트로 승격 가능.
- 오류코드 추가/변경 시 `EXPECTED_ERROR_CODES` 집합과 `ErrorEnvelope.code enum` 동기화 필요.
