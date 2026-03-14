# 00_test Log Global Full Survey Audit Order

> 작성일: 2026-03-13
> 대상 프로젝트: `projects/00_test`
> 트랙: `system-order`
> 상태: `execution-ready`
> 조사 현황: `조사 완료`
> 목적: `00_test` 기준으로 root 로그, project 로그, structured JSONL/JSON sink, Electron main/renderer/splash 로그, 테스트 회귀망까지 포함한 로그 전역 전수 조사를 수행한다.
> 방식: `read-only`, `artifact-proof cross-check`, `code-and-test verification`, `3PASS 오더 감리 후 실행`, `3PASS 결과 감리`

---

## 0. 문서 역할

- 이 문서는 `00_test` 전용 로그 전역 전수조사 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 조사 단계에서는 코드 직접 수정, 임시 patch, 로그 파일 변조를 금지한다.
- 모든 근거 문서와 결과 문서는 `UTF-8`로 유지한다. 깨진 한글, 물음표 치환 흔적, replacement character가 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 조사 결과 문서가 채워지기 전까지 어떤 후보도 확정 finding으로 간주하지 않는다.

---

## 1. 왜 별도 오더가 필요한가

2026-03-13 기준 워크스페이스에는 logging hardening, runtime observability, frontend shell/splash 감사가 이미 존재한다. 그러나 `00_test`를 기준으로 아래 질문을 한 장의 오더로 잠근 문서는 없었다.

- root `logs/session_*.log`와 `projects/00_test/logs/session_*.log`가 실제로 하나의 세션을 같은 사실로 보존하는가
- `projects/00_test/logs/session/decisions.jsonl`, `pass_rate_monitor.json`, `runtime_audit_summary.json`, `runtime_audit.jsonl`가 attempt-level lineage를 같은 강도로 보존하는가
- Electron main이 남기는 `electron-main.log`와 renderer/splash가 화면에만 뿌리는 로그 사이에 durable persistence gap이 없는가
- 기존 ROP/FGS 감사의 retained finding이 `00_test` 실증 아티팩트에서도 여전히 살아 있는가
- 현재 테스트가 실제 로그 계약을 잠그는지, 아니면 생성/호출 여부만 보는 thin gate인지

이번 오더는 기존 문서를 재작성하는 대신, `00_test`를 공통 실증 기준으로 묶어 `carry-over open`, `net-new`, `rejected`, `coverage gap`을 분리하는 데 목적이 있다.

### 선행 참조 문서

- `docs/2026-03-13/runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
- `docs/2026-03-13/ROP-T1-main-a-context-log-wiring-findings.md`
- `docs/2026-03-13/ROP-T3-structured-sink-alignment-findings.md`
- `docs/2026-03-13/ROP-T5-runtime-proof-regression-findings.md`
- `docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md`
- `docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md`

---

## 2. 공통 조사 규약

### 2.1 조사 모드

- `static`
- `read-only`
- `code-and-test verification`
- `artifact-proof cross-check`
- `UTF-8 only`

### 2.2 금지 사항

- 코드 직접 수정 금지
- 테스트 수정 금지
- 로그 재생성 목적으로 destructive rerun 금지
- 기존 문서 finding을 근거 없이 재오픈 금지

### 2.3 finding 기록 형식

확정 finding은 아래 필드를 모두 포함한다.

1. ID
2. Severity (`P0`, `P1`, `P2`, `P3`)
3. 현상 요약
4. 직접 근거
5. downstream 영향 경계
6. 현재 테스트 근거 또는 테스트 부재
7. 기존 문서와의 관계 (`carry-over-open`, `net-new`, `rejected`, `coverage-gap`)
8. 권장 후속 조치

### 2.4 Severity 기준

- `P0`: operator가 로그를 근거로 완전히 반대 사실을 읽게 되는 경우
- `P1`: 동일 run의 핵심 lineage 또는 boot trace가 sink 사이에서 끊기는 경우
- `P2`: durable log blind spot, thin summary, proof coverage gap, stale evidence path drift
- `P3`: shadow surface, trace readability 저하, 문서/증거 포인터 drift

---

## 3. 오더 3PASS 감리 이력

### PASS 1 - 초안

초기 오더는 backend 로그 파일과 structured sink만 보도록 좁게 설계됐다.

- 포함: `main_a.py`, `modules/core/logger.py`, `SessionLogger`, `runtime_audit_summary.json`
- 누락: Electron renderer/splash 콘솔 표면, `00_test` 실 로그 파일 대조, 기존 감사와의 carry-over 구분

### PASS 2 - 보완

두 번째 감리에서 아래 누락을 보완했다.

- root `logs/session_*.log`와 `projects/00_test/logs/session_*.log` 실파일 head/line count 대조 추가
- `geuldobi-desktop/src/main.js`, `src/index.html`, `src/splash/splash.js`의 durable persistence 조사 추가
- 기존 `ROP-*`, `FGS-*` findings 중 `00_test`에서 재검증 가능한 항목을 carry-over로 분리

### PASS 3 - 최종 잠금

최종 감리에서 결과 문서 요구사항을 다음과 같이 잠갔다.

- PASS1 후보, PASS2 기각/중복 제거, PASS3 확정 항목을 모두 남긴다.
- `net-new`와 `carry-over-open`을 반드시 분리한다.
- 실행 근거에는 최소 1회 표적 pytest와 `00_test` 실아티팩트 대조를 포함한다.
- 최종 결과 문서는 `[LGS-TN-SEQ]` 형식 ID를 사용한다.

---

## 4. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | boot/session file routing | `main_a.py`, `modules/core/logger.py`, root `logs/`, `projects/00_test/logs/` |
| T2 | structured sink contract | `session/decisions.jsonl`, `pass_rate_monitor.json`, `runtime_audit_summary.json`, 관련 orchestrator/audit code |
| T3 | desktop durability | `geuldobi-desktop/src/main.js`, `src/index.html`, `src/splash/splash.js`, renderer/splash error persistence |
| T4 | `00_test` artifact proof | 실제 `projects/00_test/logs/*` 산출물, line count, head sample, joinability |
| T5 | regression trust | 관련 pytest, existing docs, missing test surface |

---

## 5. Terminal별 실행 질문

### T1. boot/session file routing

질문:

1. app 부팅 직후 생성되는 root 세션 파일과 project 바인딩 뒤의 project 세션 파일이 하나의 연속 로그로 읽히는가
2. `StudioLogger.retarget()`가 기존 boot 로그를 project 쪽으로 이전하지 않는다면 operator가 project log만 보고 초기 부팅 문맥을 잃는가
3. 현재 테스트는 `SessionLogger.set_log_dir()`만 잠그고 `StudioLogger.retarget()`는 비워 두는가

필수 근거:

- `main_a.py`
- `modules/core/logger.py`
- `tests/test_session_logger.py`
- `logs/session_20260313_195031.log`
- `projects/00_test/logs/session_20260313_195031.log`

### T2. structured sink contract

질문:

1. `decisions.jsonl`이 `pass_rate_monitor.json`과 같은 attempt-level join key를 가지는가
2. `runtime_audit_summary.json`이 run heartbeat를 넘어서 structured SSOT 역할을 할 수 있는가
3. 기존 `ROP-T1`, `ROP-T3` retained finding이 `00_test`에서도 재현되는가

필수 근거:

- `modules/core/stage3_orchestrator.py`
- `modules/core/services/audit_service.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_orchestrator.py`
- `projects/00_test/logs/session/decisions.jsonl`
- `projects/00_test/logs/pass_rate_monitor.json`
- `projects/00_test/logs/runtime_audit_summary.json`

### T3. desktop durability

질문:

1. main process는 어떤 오류를 `electron-main.log`에 남기고, renderer/splash는 어떤 오류를 파일에 남기지 않는가
2. `appendLog()`로 보이는 운영자 로그가 durable sink가 아니라 메모리 500줄 UI 버퍼에 그치는가
3. 이 표면을 잠그는 테스트가 실제로 존재하는가

필수 근거:

- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/splash/splash.js`
- `docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md`

### T4. `00_test` artifact proof

질문:

1. `00_test`는 위 세 범주의 retained/net-new 항목을 실증하는 current artifact를 제공하는가
2. 단순 코드 추론이 아니라 실제 산출물 head/sample/line count로 같은 결론을 방어할 수 있는가

필수 근거:

- `projects/00_test/logs/`
- `logs/`
- `projects/00_test/project_data.db`가 아니라 `logs/*` 위주 artifact

### T5. regression trust

질문:

1. 현재 pytest green은 어떤 로그 계약을 잠그고 어떤 계약을 놓치는가
2. `StudioLogger.retarget()`와 renderer/splash persistence gap은 테스트 부재로 남아 있는가

필수 근거:

- `tests/test_session_logger.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_process_runner.py`

---

## 6. 최종 산출물 요구사항

최종 결과 문서는 아래를 반드시 포함한다.

- 문서명: `docs/2026-03-13/00_test-log-global-full-survey-3pass-final-audit.md`
- 실행 근거:
  - 표적 pytest 1회 이상
  - `00_test` 실 로그 파일 대조
  - 기존 감사 문서 교차검증
- PASS1 후보 총계
- PASS2 기각/중복 제거 이유
- PASS3 확정 findings
- `carry-over-open`과 `net-new` 분리
- `coverage gap / open question`

---

## 7. 종료 조건

아래 조건을 모두 만족하면 본 오더는 완료다.

1. `00_test` 기준 log chain 전 범위를 문서 한 장으로 재구성했다.
2. `carry-over-open`, `net-new`, `rejected`, `coverage gap`이 분리됐다.
3. 각 확정 finding에 실아티팩트와 코드/테스트 근거가 함께 있다.
4. UTF-8 이상 징후 없이 결과 문서가 저장됐다.
