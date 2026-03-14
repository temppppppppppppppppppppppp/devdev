# 00_test Log Global Full Survey 3PASS Final Audit

> 작성일: 2026-03-13
> 기준 오더: [00_test-log-global-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/00_test-log-global-full-survey-audit-order.md)
> 조사 모드: `read-only`, `artifact-proof cross-check`, `code-and-test verification`
> 테스트 실행: `pytest -q tests/test_session_logger.py tests/test_stage3_orchestrator.py tests/test_stage4_post_processor.py tests/test_bridge_quality_summary.py tests/test_process_runner.py`
> 테스트 결과: `162 passed in 3.65s`

## Executive Summary

이번 `00_test` 로그 전역 전수조사의 결론은 다음과 같다.

- 기존 ROP 감사에서 열린 structured sink blind spot 두 건은 `00_test` 실아티팩트에서도 그대로 확인됐다.
  - `projects/00_test/logs/session/decisions.jsonl`의 Stage 3 row는 여전히 `attempt_key` 없이 남는다.
  - `projects/00_test/logs/runtime_audit_summary.json`는 run heartbeat만 제공하며 structured SSOT가 아니다.
- 이번 조사에서 새로 확인된 operator-facing blind spot은 두 건이다.
  - `StudioLogger.retarget()`가 root 부팅 로그를 project log로 이관하지 않아 하나의 세션이 root/project 두 파일로 갈라진다.
  - Electron main은 파일 로그를 남기지만 renderer/splash의 다수 오류는 브라우저 콘솔 또는 500줄 UI 버퍼에만 남아 durable persistence가 없다.
- PASS1 후보는 `6건`이었고, PASS2에서 `2건`을 기각했으며, PASS3에서 `P1 2건`, `P2 2건`을 확정했다.

최종 retained finding은 `carry-over-open 2건`, `net-new 2건`이다.

---

## 1. 조사 범위와 실행 근거

### 조사 입력

- 코드
  - `main_a.py`
  - `modules/core/logger.py`
  - `modules/core/session_logger.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/services/audit_service.py`
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/splash/splash.js`
- 테스트
  - `tests/test_session_logger.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_stage4_post_processor.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_process_runner.py`
- 기존 문서
  - `docs/2026-03-13/ROP-T1-main-a-context-log-wiring-findings.md`
  - `docs/2026-03-13/ROP-T3-structured-sink-alignment-findings.md`
  - `docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md`
  - `docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md`
- 실아티팩트
  - `logs/session_20260313_195031.log`
  - `projects/00_test/logs/session_20260313_195031.log`
  - `projects/00_test/logs/session/decisions.jsonl`
  - `projects/00_test/logs/pass_rate_monitor.json`
  - `projects/00_test/logs/runtime_audit_summary.json`

### 아티팩트 핵심 관찰

- root 세션 파일: `logs/session_20260313_195031.log`
  - 크기 `4136 bytes`
  - `32 lines`
  - head에는 `[System] 필수 경로 점검 완료`, `[Phase 0] 프로젝트 '00_test' V20 지능 기동 중...`, DB migration skip 등이 남아 있다.
- project 세션 파일: `projects/00_test/logs/session_20260313_195031.log`
  - 크기 `455387 bytes`
  - `3321 lines`
  - 첫 줄부터 preset registry restore, HUD/Guard/VecMemory 초기화가 시작되며 root boot head는 포함하지 않는다.
- Stage 3 decisions sample:
  - `projects/00_test/logs/session/decisions.jsonl`의 Stage 3 row meta는 `{"arc_no": 1, "quality_risk": false}` 수준이며 `attempt_key`가 없다.
- pass-rate sample:
  - `projects/00_test/logs/pass_rate_monitor.json`의 Stage 3 record는 `attempt_key`, `candidate_key`, `artifact_path`를 모두 가진다.
- runtime summary sample:
  - `projects/00_test/logs/runtime_audit_summary.json`는 `tag`, `timestamp`, `total_events`, `counts`, `latest_event_type`, `recent_events`만 보존한다.

---

## 2. PASS 1 후보 수집

PASS1에서 수집한 후보는 아래 `6건`이었다.

1. root/project 세션 파일이 같은 run의 boot trace를 분할 저장한다.
2. Stage 3 `decisions.jsonl`은 `pass_rate_monitor.json`과 같은 attempt-level join key를 보존하지 않는다.
3. `runtime_audit_summary.json`는 structured SSOT처럼 보이지만 실제로는 completion heartbeat다.
4. renderer/splash 오류가 durable file sink에 남지 않는다.
5. `SessionLogger.set_log_dir()` 자체가 project 바인딩 후 깨질 수 있다.
6. Electron main process/backend stderr도 파일에 남지 않을 수 있다.

---

## 3. PASS 2 교차 검증

### 3.1 기각 / 제거

#### 제거 1. `SessionLogger.set_log_dir()` regression 가설

- `tests/test_session_logger.py:176`은 `set_log_dir()` 변경 후 새 `decisions.jsonl` 생성까지 잠근다.
- 실제 `projects/00_test/logs/session/` 아래에 `decisions.jsonl`, `llm_io.jsonl` 등 session sink가 정상 생성돼 있다.
- 따라서 문제는 `SessionLogger`가 아니라 `StudioLogger`의 root/project file split 쪽으로 좁혀야 한다.

#### 제거 2. Electron main process logging 부재 가설

- `geuldobi-desktop/src/main.js:20-48`은 `electron-main.log`와 `debugLog()`를 선언하고 `uncaughtException`, `unhandledRejection`을 파일에 남긴다.
- `geuldobi-desktop/src/main.js:156-217`은 backend stdout/stderr, spawn error, exit를 기록한다.
- `geuldobi-desktop/src/main.js:267-314`는 `did-fail-load`, `render-process-gone`도 파일에 남긴다.
- 따라서 durable gap은 main process 전체가 아니라 `renderer/splash console` surface로 한정된다.

### 3.2 carry-over 교차 확인

- `LGS-T2-001`은 [ROP-T1-main-a-context-log-wiring-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ROP-T1-main-a-context-log-wiring-findings.md)의 `ROP-T1-001`과 같은 방향의 blind spot이며, 이번에는 `00_test` 실 row로 재확인했다.
- `LGS-T2-002`는 [ROP-T3-structured-sink-alignment-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ROP-T3-structured-sink-alignment-findings.md)의 `ROP-T3-003`과 같은 방향의 blind spot이며, `00_test` summary로 재확인했다.

---

## 4. PASS 3 확정 findings

### [LGS-T1-001] P1 | `StudioLogger.retarget()`가 같은 세션의 boot trace를 root/project 두 파일로 분할한다

- 분류: `net-new`
- 직접 근거:
  - `main_a.py:267`은 app 초기화 시 `init_logger()`를 먼저 호출한다.
  - `main_a.py:1073-1078`은 project binding 뒤 `_studio_logger.retarget(self.current_project.paths.root / "logs")`를 호출한다.
  - `modules/core/logger.py:188-212`의 `retarget()`는 기존 file handler를 닫고 새 file handler를 project 쪽으로 다시 열 뿐, 기존 root 파일 내용을 복제하거나 이어 붙이지 않는다.
  - 실아티팩트 기준 root `logs/session_20260313_195031.log`는 `32 lines / 4136 bytes`이며 초기 부팅 로그를 가진다.
  - 실아티팩트 기준 project `projects/00_test/logs/session_20260313_195031.log`는 `3321 lines / 455387 bytes`이며 preset registry restore 이후부터 시작한다.
- 현상 요약:
  - operator가 project log만 열면 `[System] 필수 경로 점검 완료`, `[Phase 0] 프로젝트 '00_test' V20 지능 기동 중...`, 초기 DB migration skip처럼 가장 앞단 boot trace를 잃는다.
  - 반대로 root log만 열면 이후 장시간 runtime trace가 거의 없다.
- downstream 영향 경계:
  - 하나의 session name을 가진 파일이 두 위치에 나뉘어 존재해 포렌식 시작점이 흔들린다.
  - 특히 project 단위 증거 수집 시 “프로젝트 로그”만 수거하면 초기 binding 전후 문맥이 끊긴다.
- 현재 테스트 근거 또는 테스트 부재:
  - `tests/test_session_logger.py:176`은 `SessionLogger.set_log_dir()`만 검증한다.
  - `tests/`에는 `StudioLogger.retarget()`가 기존 boot 로그를 project 쪽에 보존하는지 잠그는 테스트가 없다.
- 기존 문서와의 관계:
  - `net-new`
  - 기존 문서는 project log path 전환 자체는 다뤘지만, root/project 동일 session file bifurcation과 early-boot trace 상실은 별도 finding으로 잠기지 않았다.
- 권장 후속 조치:
  - `retarget()` 이전 root 파일 내용을 project 파일로 copy/append하거나, 아예 세션 시작 시점부터 project root가 정해질 때까지 임시 buffer를 사용해 단일 파일로 flush해야 한다.
  - 회귀 테스트는 실제 파일 두 개를 읽어 early boot line이 project log에도 존재하는지 검증해야 한다.

### [LGS-T2-001] P1 | `00_test`의 Stage 3 `decisions.jsonl`은 여전히 attempt-level join key를 잃는다

- 분류: `carry-over-open`
- 직접 근거:
  - `modules/core/stage3_orchestrator.py:1312-1318`과 `modules/core/stage3_orchestrator.py:1818-1824`는 Stage 3 decision row를 먼저 기록한다.
  - 같은 파일의 `modules/core/stage3_orchestrator.py:1359-1409`, `modules/core/stage3_orchestrator.py:1872-1921`은 그 뒤에야 `pass_rate_monitor`, `stage_attempts`, `director_selections`로 `attempt_key`, `candidate_key`, `artifact_path`를 흘린다.
  - `projects/00_test/logs/session/decisions.jsonl`의 Stage 3 sample row는 `meta={"arc_no":1,"quality_risk":false}`만 가진다.
  - `projects/00_test/logs/pass_rate_monitor.json`의 대응 row는 `attempt_key`, `candidate_key`, `artifact_path`를 모두 가진다.
- 현상 요약:
  - 동일 Stage 3 run을 `session/decisions.jsonl` 단독으로 보면 multi-attempt, selected candidate, artifact lineage를 복원할 수 없다.
- downstream 영향 경계:
  - session sink만 수집한 운영자 또는 외부 감사자는 Stage 3 포렌식을 위해 반드시 다른 sink를 추가로 열어야 한다.
  - `session/decisions.jsonl`와 `pass_rate_monitor.json`이 같은 event를 다른 해상도로 보존해 cross-sink join contract가 깨진다.
- 현재 테스트 근거 또는 테스트 부재:
  - `tests/test_stage3_orchestrator.py:795`, `tests/test_stage3_orchestrator.py:807`, `tests/test_stage3_orchestrator.py:827`은 `pass_rate_monitor`와 `attempt_key` propagation을 잠근다.
  - `tests/test_session_logger.py`는 decision row 생성 자체는 보지만 Stage 3 decision meta에 `attempt_key`가 들어가는지는 보지 않는다.
- 기존 문서와의 관계:
  - `carry-over-open`
  - [ROP-T1-main-a-context-log-wiring-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ROP-T1-main-a-context-log-wiring-findings.md)의 `ROP-T1-001`을 `00_test` 실 row로 재확인한 것이다.
- 권장 후속 조치:
  - Stage 3 decision row 작성 전에 `attempt_key`, `candidate_key`, `artifact_path`를 계산해 `session_logger.log_decision()` meta로 함께 넘겨야 한다.
  - 회귀 테스트는 `MagicMock` 호출이 아니라 실제 `decisions.jsonl` row를 읽어 key 존재를 확인하는 방식으로 잠가야 한다.

### [LGS-T2-002] P2 | `00_test`의 `runtime_audit_summary.json`는 structured SSOT가 아니라 completion heartbeat에 머문다

- 분류: `carry-over-open`
- 직접 근거:
  - `modules/core/services/audit_service.py:83-101`의 summary payload는 `counts`, `recent_events`, `latest_event_type` 중심이며 `attempt_key`, `candidate_key`, `artifact_path` 같은 structured digest가 없다.
  - `projects/00_test/logs/runtime_audit_summary.json`는 실제로 `tag`, `timestamp`, `total_events`, `counts`, `latest_event_type`, `recent_events`만 가진다.
  - `tests/test_stage4_orchestrator.py:123`은 Stage 4 completion 시 summary write 호출을 잠그지만, structured lineage summary는 검증하지 않는다.
- 현상 요약:
  - summary file은 “무언가 끝났다”는 heartbeat로는 유효하지만, 어떤 attempt/candidate/artifact가 최종 상태인지 재구성할 pivot을 제공하지 않는다.
- downstream 영향 경계:
  - operator가 `runtime_audit_summary.json`만 보고 structured sink alignment가 닫혔다고 판단하면 오판한다.
  - 실제 lineage 증거는 여전히 DB, pass-rate, session log로 내려가서 따로 확인해야 한다.
- 현재 테스트 근거 또는 테스트 부재:
  - summary 존재/호출 여부를 잠그는 테스트는 있다.
  - summary가 attempt-level digest까지 가져야 한다는 테스트는 없다.
- 기존 문서와의 관계:
  - `carry-over-open`
  - [ROP-T3-structured-sink-alignment-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ROP-T3-structured-sink-alignment-findings.md)의 `ROP-T3-003`을 `00_test` summary 실파일로 재확인한 것이다.
- 권장 후속 조치:
  - `runtime_audit_summary.json`의 역할을 명시적으로 `completion-only heartbeat`로 격하하거나,
  - per-stage latest `attempt_key`, `candidate_key`, `artifact_path`, sink completeness를 포함하는 operator summary contract로 승격해야 한다.

### [LGS-T3-001] P2 | renderer/splash 오류는 durable file sink가 아니라 브라우저 콘솔과 500줄 UI 버퍼에 머문다

- 분류: `net-new`
- 직접 근거:
  - `geuldobi-desktop/src/main.js:20-48`은 `electron-main.log`와 `debugLog()`를 정의해 main process 예외를 파일에 남긴다.
  - `geuldobi-desktop/src/main.js:267-314`는 `did-fail-load`, `render-process-gone`도 파일에 남긴다.
  - 그러나 `geuldobi-desktop/src/splash/splash.js:37`, `geuldobi-desktop/src/splash/splash.js:79`의 오류는 `console.error(...)`만 호출한다.
  - `geuldobi-desktop/src/index.html:4676`, `geuldobi-desktop/src/index.html:5839`, `geuldobi-desktop/src/index.html:5879`, `geuldobi-desktop/src/index.html:5994`, `geuldobi-desktop/src/index.html:7908`도 브라우저 콘솔 경고/오류를 직접 남긴다.
  - `geuldobi-desktop/src/index.html:5004-5060`의 `appendLog()`는 DOM에만 로그를 붙이고 `while (logStream.children.length > 500)`로 오래된 행을 제거한다.
- 현상 요약:
  - main process/backend stderr는 파일에 남지만 renderer/splash에서 발생한 parse error, settings load error, project list error, splash bootstrap error는 재실행 뒤 durable 근거가 남지 않을 수 있다.
- downstream 영향 경계:
  - UI 상에서 한 번 봤던 오류가 재현되지 않으면 운영자는 `electron-main.log`만으로 원인을 복구하지 못할 수 있다.
  - 특히 renderer-only 문제는 프로세스가 살아 있어도 file sink에 남지 않아 blind spot이 된다.
- 현재 테스트 근거 또는 테스트 부재:
  - 현재 `tests/`에는 `electron-main.log`, renderer `console.error`, splash console surface, `appendLog()`의 durable persistence를 직접 잠그는 테스트가 없다.
  - [FGS-T3-shell-ipc-splash-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md)는 shell/shadow-main 표면을 다뤘지만 renderer console durability 자체는 확정 finding으로 잠그지 않았다.
- 기존 문서와의 관계:
  - `net-new`
- 권장 후속 조치:
  - main process에서 `webContents.on("console-message", ...)`를 수집해 `electron-main.log`로 relay하거나,
  - renderer/splash 공용 IPC logger를 추가해 file sink와 UI 버퍼를 동시에 남겨야 한다.
  - 회귀 테스트는 renderer console relay와 log pruning 이후 file persistence를 함께 검증해야 한다.

---

## 5. 기각 findings

- `SessionLogger.set_log_dir()` 자체가 project binding 후 깨진다는 가설
  - 판정: `rejected`
  - 이유: 테스트와 `projects/00_test/logs/session/*` 실아티팩트가 정상 생성됨을 보여 준다.
- Electron main process/backend stderr가 파일에 남지 않는다는 가설
  - 판정: `rejected`
  - 이유: `debugLog()`가 main process 예외, backend stdout/stderr, load failure를 이미 `electron-main.log`에 남긴다.

---

## 6. Coverage Gap / Open Question

- 이번 감사는 `00_test` 실아티팩트를 읽는 방식으로 수행했다. Stage 4 degraded soft-failure가 실제 `00_test`에서 발생했을 때 `soft_failures.jsonl`와 `runtime_audit_summary.json`가 얼마나 어긋나는지까지는 별도 재현하지 않았다.
- `renderer/splash` console durable relay 부재는 코드상 분명하지만, 실제 packaged Electron run에서 얼마나 자주 operator 장애로 이어지는지 live desktop 재현까지는 수행하지 않았다.
- root/project 동일 session file bifurcation이 `00_test` 외 다른 프로젝트에서도 반복되는지 repo 전수 집계는 하지 않았다. 이번 문서는 `00_test` 실증에 한정한다.

---

## 7. PASS1 -> PASS2 -> PASS3 요약

- PASS1 후보: `6건`
- PASS2 제거: `2건`
- PASS3 확정: `4건`

확정 ID:

- `LGS-T1-001` `P1` root/project session file bifurcation
- `LGS-T2-001` `P1` Stage 3 decisions join-key gap
- `LGS-T2-002` `P2` runtime summary heartbeat-only blind spot
- `LGS-T3-001` `P2` renderer/splash durable persistence gap

Severity 합계:

- `P0`: `0`
- `P1`: `2`
- `P2`: `2`
- `P3`: `0`

---

## 결론

- `00_test` 기준 로그 체인은 “전혀 안 남는다”보다 “부분별로 남는데 같은 세션과 같은 lineage를 한 파일에서 닫아 주지 못한다”는 문제가 더 크다.
- 기존 ROP 문서가 잡아낸 structured sink blind spot은 아직 live다.
- 이번 조사에서 새로 확인된 운영자 관점의 핵심 결함은 `boot trace bifurcation`과 `renderer/splash durable logging gap`이다.
- 다음 remediation 우선순서는 `1) StudioLogger 단일 세션 파일화`, `2) Stage 3 decision row attempt lineage 보강`, `3) renderer/splash console relay 파일화`, `4) runtime summary 역할 재정의` 순서가 적절하다.
