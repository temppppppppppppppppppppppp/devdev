# [S-T4] API & Desktop 통합 심층 감사 보고서

> 작성일: 2026-03-13
> 터미널: Terminal 4
> 범위: `modules/api/bridge_server.py`, `modules/api/run_validator.py`, `modules/api/process_runner.py`, `geuldobi-desktop/src/preload.js`, `geuldobi-desktop/src/main.js`, API 계약 테스트
> 방법: static / read-only / contract-path cross-check / desktop runtime path inspection

---

## 요약

이번 심층 감사에서 확인된 핵심은 API 자체보다도 **Desktop이 API 보안 경계를 어떻게 우회하거나 축소하는가**였다. 결과는 두 줄로 정리된다.

- Desktop 런타임은 위험 키 승인 경계를 사실상 비워 둔 상태다.
- 반면 테스트는 아직도 오프라인 RouterStub과 옛 상태모델을 기준으로 돌아가고 있어, 실제 데스크톱 경로를 잡아내지 못한다.

즉, 현재 API/Desktop 통합의 핵심 문제는 엔드포인트 부족이 아니라 **실행 경로와 검증 경로가 서로 다른 계약을 믿고 있다**는 점이다.

---

## 확정 발견사항

### [S-T4-001] P1 | Desktop 경로에서 위험 키 dual-control 승인이 사실상 우회된다

- 파일:
  - `geuldobi-desktop/src/preload.js:10-11`
  - `geuldobi-desktop/src/main.js:157-164`
  - `geuldobi-desktop/src/main.js:395-399`
  - `modules/api/bridge_server.py:1293-1300`
- 현상:
  - Desktop는 backend subprocess에 `GEULDOBI_DESKTOP_MODE=1`을 주입한다.
  - renderer/preload의 `runKey()`와 main process `bridge:run` 핸들러는 `approval_id`를 받을 수도, 전달할 수도 없다.
  - 그런데 backend는 desktop mode에서 위험 키(`44/77/88/99`)에 `approval_id`가 없으면 자동 승인한다.
- 영향:
  - OpenAPI와 RiskApprovalGate가 정의한 dual-control 경계가 Desktop 실경로에서는 작동하지 않는다.
  - 위험 키 실행이 "승인 필요"가 아니라 "Desktop이면 자동 승인"으로 바뀐다.
- 판정:
  - 단순 문서 불일치가 아니라 **실제 승인 경계 우회**다.
- 기존 보고서와의 관계:
  - 1차/2차 T1~T5 ledger에는 이 Desktop 승인 우회가 정식 finding으로 올라오지 않았다.

### [S-T4-002] P2 | API 계약 테스트가 실제 `bridge_server` 대신 RouterStub에 묶여 있어 런타임 drift를 숨긴다

- 파일:
  - `tests/test_api_contract.py:9-10`
  - `tests/test_api_contract.py:81-84`
  - `tests/test_run_validator.py:85-88`
  - `modules/api/process_runner.py:39`
- 현상:
  - 계약 테스트는 "BE 서버가 미구현 단계"라는 전제로 RouterStub을 사용한다.
  - 이 스텁은 `waiting_input` 상태를 전제로 하며, `waiting_input/stopping/error`를 `/run` 차단 상태로 보지 않는다.
  - 반면 실제 `ProcessRunner`의 유효 상태는 `idle/starting/running/stopping/error`이고 `waiting_input` 상태는 없다.
  - 무엇보다 실제 Desktop 경로의 auto-approval semantics는 이 테스트 스위트에 반영돼 있지 않다.
- 영향:
  - 테스트가 "계약 회귀 방지"보다 "과거 스텁 가정 보존"에 가깝다.
  - 실제 server/runtime drift가 있어도 테스트가 녹색으로 남을 수 있다.
- 기존 보고서와의 관계:
  - 기존 문서는 contract 파일 누락이나 state enum 자체를 다뤘지만, 본 건은 **테스트 경로가 실제 서버를 검증하지 못하는 구조**를 새로 잡은 것이다.

---

## 정상 확인 항목

- `geuldobi-desktop/src/main.js:632-675`의 Work Guard template 경로 검증은 library root 내부 YAML만 허용한다.
- `geuldobi-desktop/src/preload.js`와 `geuldobi-desktop/src/main.js`의 IPC 채널 대응은 현재 코드상 1:1로 유지된다.
- `docs/implementation/api-contract-v1.yaml`는 현재 트리에서 `/quality/summary`, `/quality/dashboard`, `/safe-ops/preview`, `/quality/review`를 포함한다.

---

## API/Desktop 경계 표

| 층 | 현재 계약 | 실제 동작 |
|----|----------|----------|
| OpenAPI `RunRequest` | `approval_id` 선택 필드 존재 | Desktop IPC 표면에서는 입력 경로 자체가 없음 |
| Desktop preload | `runKey(key, subKey, inputs)` | `approval_id` 전달 불가 |
| Desktop main | `/run` body에 `key/sub_key/inputs`만 전달 | 위험 키 승인 정보 누락 |
| bridge_server | risk key는 `approval_id` 검사 | 단, desktop mode면 누락 시 auto-approve |
| 테스트 | approval 없으면 403 기대 | 실제 Desktop 경로와 불일치 |

---

## 3PASS 감리 로그

### PASS 1 — 후보 4건

- Desktop risk approval bypass
- contract tests vs real server drift
- runner state model drift 재보고 여부
- Work Guard path traversal 가능성

### PASS 2 — 제거 2건

- runner state enum 단독 건: 기존 T5 API ledger와 결이 겹쳐 신규 finding에서 제외
- Work Guard path traversal: 현행 코드에서 방어 확인

### PASS 3 — 최종 2건 확정

- `PASS1 4건 → PASS2 2건 제거 → 최종 2건 확정`

---

## 결론

API & Desktop 심층 감사의 핵심은 "문서가 조금 낡았다"가 아니다. 현재 가장 중요한 문제는 **Desktop이 위험 키 승인 경계를 실질적으로 우회하고 있는데, 테스트는 그 경로를 전혀 감시하지 못한다는 점**이다.

후속 조치 우선순위는 다음과 같다.

1. Desktop IPC 표면에 `approval_id` 및 승인 UX를 실제로 추가
2. `GEULDOBI_DESKTOP_MODE`의 auto-approve 경로를 제거하거나 최소한 explicit operator confirmation으로 대체
3. RouterStub 계약 테스트를 실제 `bridge_server` HTTP/ASGI 테스트로 대체
