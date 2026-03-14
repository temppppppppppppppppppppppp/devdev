# 00_test 로그 전역 전수조사 후속 수정 실행 SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 목표: `00_test` 로그 전역 전수조사에서 확정된 4개 retained finding을 실행 가능한 수정 단위로 정리하고, 범위 밖 항목을 분리한다.

## 1. 소스와 위계

이 문서는 아래 근거 계층을 병합한 실행 기준 문서다.

1. 직접 감사 결과
   - `docs/2026-03-13/00_test-log-global-full-survey-3pass-final-audit.md`
   - `docs/2026-03-13/00_test-log-global-full-survey-audit-order.md`
2. 기존 retained finding 문서
   - `docs/2026-03-13/ROP-T1-main-a-context-log-wiring-findings.md`
   - `docs/2026-03-13/ROP-T3-structured-sink-alignment-findings.md`
   - `docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md`
3. 직접 재확인한 런타임/로그 근거
   - `logs/session_20260313_195031.log`
   - `projects/00_test/logs/session_20260313_195031.log`
   - `projects/00_test/logs/session/decisions.jsonl`
   - `projects/00_test/logs/pass_rate_monitor.json`
   - `projects/00_test/logs/runtime_audit_summary.json`
4. 인접 참고 근거
   - `00_test_print.txt`

판정 원칙은 아래와 같다.

- `00_test` 실아티팩트와 현재 코드가 함께 뒷받침하는 항목만 실행 대상으로 유지한다.
- 이미 PASS2에서 기각된 가설은 SSOT 실행 범위에 다시 넣지 않는다.
- 로그 계약 수정과 기능 결함 수정을 섞지 않는다.
- 큰 스키마 확장보다, operator가 실제로 놓치는 증거 연속성과 joinability를 우선한다.

## 2. 병합 판정 요약

### 2.1 유지되는 실행 대상

- `LGS-T1-001`
  - `StudioLogger.retarget()`가 root/project 세션 파일을 분할해 early boot trace가 project log에 남지 않는다.
- `LGS-T2-001`
  - Stage 3 `session/decisions.jsonl`이 `attempt_key`, `candidate_key`, `artifact_path` 없이 저장돼 session sink 단독 포렌식이 끊긴다.
- `LGS-T2-002`
  - `runtime_audit_summary.json`는 structured SSOT가 아니라 completion heartbeat에 머문다.
- `LGS-T3-001`
  - renderer/splash 오류가 durable file sink가 아니라 브라우저 콘솔과 UI 버퍼에 머문다.

### 2.2 실행 범위에서 내리는 항목

- `SessionLogger.set_log_dir()` 자체 결함
  - 이유: 테스트와 `projects/00_test/logs/session/*` 실아티팩트 기준으로 기각됐다.
- Electron main process logging 부재
  - 이유: `electron-main.log`와 `debugLog()`가 이미 main/backend surface를 파일에 남긴다.
- `00_test_print.txt` 말미의 Stage 4 `generate_writer_guidance_v60_8` / `__slots__` 충돌
  - 이유: 실제 기능 결함일 수 있으나, 이번 SSOT는 로그 계약/증거 계층 수정 오더다.
  - 처리: 별도 시스템 수정 오더로 분리한다.

## 3. 실행 대상

### E-1. StudioLogger 단일 세션 파일 연속성 보장

- 대상 파일
  - `main_a.py`
  - `modules/core/logger.py`
  - 필요 시 관련 테스트 추가
- 문제
  - app는 `init_logger()`로 root `logs/session_<session>.log`를 먼저 만들고,
  - project binding 뒤 `retarget()`로 `projects/<name>/logs/session_<session>.log`로 file handler를 갈아끼운다.
  - 이때 root 파일의 초기 boot line은 project 파일로 이어지지 않는다.
- 실행 방향
  - `retarget()` 이전에 축적된 file content를 새 project log로 copy/append하거나,
  - root 임시 파일 대신 메모리 buffer 또는 shared append strategy로 단일 session file continuity를 보장한다.
  - session name은 유지하고, 기존 root/project dual-write 의존 로직은 만들지 않는다.
- 가드레일
  - stdout/stderr 콘솔 출력 구조는 깨지지 않아야 한다.
  - historical log backfill은 이번 범위에 넣지 않는다.
  - 새 프로젝트 바인딩 전 crash가 나더라도 최소 root boot log는 남아야 한다.
- 성공 기준
  - project log head에도 `[System] 필수 경로 점검 완료`, `[Phase 0] 프로젝트 ... 기동 중...` 같은 초기 boot line이 존재한다.
  - 같은 `session_<name>.log`를 root/project 두 곳에서 따로 읽지 않아도 boot부터 runtime까지 이어진다.
  - 회귀 테스트가 `StudioLogger.retarget()` 후 project file continuity를 직접 검증한다.

### E-2. Stage 3 session decision row에 attempt lineage 주입

- 대상 파일
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/session_logger.py`
  - `tests/test_stage3_orchestrator.py`
  - 필요 시 `tests/test_session_logger.py`
- 문제
  - Stage 3 decision row는 먼저 기록되고, `attempt_key/candidate_key/artifact_path`는 그 다음 sink들에만 기록된다.
  - 결과적으로 `session/decisions.jsonl` 단독으로는 attempt-level join이 불가능하다.
- 실행 방향
  - success/reject 경로 모두에서 `attempt_key`, `candidate_key`, `artifact_path` 산출 시점을 앞당기거나,
  - 최소한 `session_logger.log_decision()` 호출 시 동일 meta를 넘기도록 순서를 정렬한다.
  - logger schema 자체를 새로 만들기보다 기존 `meta` 필드를 활용한다.
- 가드레일
  - 기존 `pass_rate_monitor`, `stage_attempts`, `director_selections` payload shape는 깨지지 않아야 한다.
  - Stage 2/4까지 한 번에 확장하지 않는다. 이번 tranche는 Stage 3 first fix다.
- 성공 기준
  - `projects/*/logs/session/decisions.jsonl`의 Stage 3 row에서 `meta.attempt_key`, `meta.candidate_key`, `meta.artifact_path`를 읽을 수 있다.
  - focused regression이 `MagicMock` call만이 아니라 실제 `decisions.jsonl` row 검증으로 잠긴다.

### E-3. renderer/splash console 오류 durable relay 추가

- 대상 파일
  - `geuldobi-desktop/src/main.js`
  - 필요 시 `geuldobi-desktop/src/preload.js`
  - 필요 시 frontend/desktop 회귀 테스트
- 문제
  - main process는 `electron-main.log`를 남기지만,
  - splash와 renderer의 `console.error`/`console.warn`는 브라우저 콘솔 또는 500줄 UI 버퍼에만 머문다.
  - 특히 `WS parse error`, `Settings load error`, `Project list error`, splash bootstrap 오류는 durable file sink가 없다.
- 실행 방향
  - main process에서 `mainWindow.webContents`와 `splashWindow.webContents`의 `console-message`를 수집해 `electron-main.log`로 relay한다.
  - 최소 범위는 `warn/error` 우선이며, 필요 시 `info`까지 확장할 수 있다.
  - 이 tranche에서는 `appendLog()` 전체를 영구 저장 대상으로 바꾸지 않는다.
- 가드레일
  - log flood를 막기 위해 severity/type 필터 또는 prefix를 둔다.
  - backend stdout/stderr logging과 중복돼도 operator가 구분할 수 있도록 source를 표시한다.
- 성공 기준
  - renderer/splash에서 발생한 `console.error`/`console.warn`가 `electron-main.log`에 source window와 함께 남는다.
  - 기존 `did-fail-load`, `render-process-gone`, backend stderr logging은 유지된다.
  - 회귀 테스트 또는 최소 smoke guard가 renderer console relay 존재를 잠근다.

### E-4. `runtime_audit_summary.json` 역할 고정

- 대상 파일
  - `modules/core/services/audit_service.py`
  - canary/analysis consumer 문서 또는 테스트
  - 관련 감사 문서
- 문제
  - 현재 summary는 attempt-level lineage를 보존하지 않는데도 operator가 구조 증거처럼 오해할 수 있다.
- 실행 방향
  - 이번 tranche는 summary 스키마를 크게 확장하지 않는다.
  - 대신 `runtime_audit_summary.json`를 `runtime heartbeat + compact proof digest`로 명시하고,
  - `runtime_audit_summary.json`는 operator-facing compact proof surface이지 sole attempt-level SSOT는 아니라는 contract를 고정한다.
  - structured provenance는 `pass_rate_monitor`, `stage_attempts`, `director_selections`, `session/decisions.jsonl`에서 확인해야 한다는 contract를 문서/테스트/consumer에 반영한다.
  - canary/audit 쪽에서 summary 단독을 SSOT로 쓰는 해석이 있다면 이를 제거한다.
- 가드레일
  - summary payload를 비호환적으로 바꾸지 않는다.
  - DB/JSONL sink redesign은 별도 tranche다.
- 성공 기준
  - 코드 주석, 테스트, 문서 어디에서도 `runtime_audit_summary.json`를 sole attempt-level SSOT처럼 취급하지 않는다.
  - operator-facing 문서가 `runtime heartbeat + compact proof digest` 역할과 authoritative structured sink 역할을 명시적으로 분리한다.

## 4. 실행 순서

1. `E-1` StudioLogger 단일 세션 파일 연속성
2. `E-2` Stage 3 decision attempt lineage
3. `E-3` renderer/splash durable relay
4. `E-4` runtime summary 역할 고정

이 순서로 두는 이유는 아래와 같다.

- `E-1`, `E-2`는 현재 `00_test` 실아티팩트 기준 P1이며, operator 포렌식에 바로 영향을 준다.
- `E-3`는 desktop 증거 연속성 강화지만 main/backend logging은 이미 있어 P2다.
- `E-4`는 schema redesign보다 contract freeze가 핵심이라 마지막 tranche로 둔다.

## 5. 검증 계획

### 공통

- 수정 파일 `py_compile` 또는 동등한 문법 검증
- UTF-8 only 확인

### E-1 검증

- focused test:
  - `StudioLogger.retarget()` 호출 전후 동일 session file continuity 검증
- 실증:
  - 새 로그 파일 head에 root boot line 포함 확인

### E-2 검증

- focused test:
  - Stage 3 success/reject 후 `decisions.jsonl` row의 `meta.attempt_key`
  - `meta.candidate_key`
  - `meta.artifact_path`
- 기존 stage3 attempt lineage 테스트와 함께 green 유지

### E-3 검증

- focused test 또는 smoke guard:
  - window `console-message` hook 존재
  - renderer/splash 경고가 `electron-main.log` sink로 relay됨
- 기존 backend/main logging 동작 불변 확인

### E-4 검증

- 관련 문서/consumer/test에서 `runtime_audit_summary.json`를 heartbeat로만 취급하는지 확인
- summary 단독을 structured SSOT로 해석하는 문구 제거 확인

## 6. 3PASS 문서 감리

### PASS 1

초안은 4개 finding을 모두 코드 수정으로 해결하는 공격적 계획이었다.

- `E-4`도 summary payload 확장으로 해결하려 했다.
- `00_test_print.txt`의 Stage 4 runtime 오류도 같은 문서에 넣으려 했다.

판정:

- 과도했다.
- summary blind spot은 이번 tranche에서 contract freeze로 줄이는 편이 안전하다.
- Stage 4 기능 결함은 로그 계약 오더와 분리해야 한다.

### PASS 2

두 번째 감리에서 범위를 아래처럼 줄였다.

- `E-4`를 대규모 schema 변경이 아닌 `heartbeat-only 역할 고정`으로 변경
- renderer/splash 항목은 `appendLog()` 영구 저장 전체가 아니라 `console-message relay` 우선으로 축소
- `00_test_print.txt`의 `__slots__` 충돌은 인접 이슈로만 기록하고 실행 대상에서 제외

판정:

- 실행 가능성이 높아졌다.
- 4개 retained finding 모두에 대응하지만, 한 tranche에서 감당 가능한 범위로 줄었다.

### PASS 3

최종 감리에서 아래 보강을 추가했다.

- 각 실행 항목마다 대상 파일, 가드레일, 성공 기준을 분리
- `P1` 우선순위를 앞단에 고정
- 실아티팩트 검증과 focused regression을 함께 요구

최종 판정:

- 이 문서는 지금 바로 구현 오더로 전환 가능한 `execution-ready` 상태다.

## 7. 최종 판정

- 이번 후속 수정 SSOT는 `3개 코드 하드닝 + 1개 contract freeze`로 정리하는 것이 맞다.
- `00_test`에서 직접 확인된 P1 두 건은 별도 proof 없이 바로 수정 대상으로 올려도 된다.
- `runtime_audit_summary.json`는 성급한 schema 확장보다 역할 오해를 먼저 제거하는 편이 안전하다.
- `00_test_print.txt`의 Stage 4 오류는 실제 중요할 수 있지만, 이 문서에서 함께 잡으면 로그 계약 수정이 흐려진다.
