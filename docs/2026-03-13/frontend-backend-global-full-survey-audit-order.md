# 프론트엔드-백엔드 전역 전량 전수조사 3PASS 감리 — 조사 오더

> 작성일: 2026-03-13
> 트랙 Prefix: `FBX`
> 상태: `completed`
> 조사 현황: `조사 완료`
> 목적: detail 수정이 누적된 현재 워크트리에서 `renderer -> preload -> Electron main -> FastAPI bridge -> ProcessRunner -> engine/bundle` 전 경계를 한 번의 SSOT 오더로 고정한다.
> 방식: `read-only full survey + targeted regression + 3PASS + 95% confidence gate`

---

## 0. 문서 역할

- 이 문서는 코드 수정 오더가 아니라 `전역 전수조사 오더`다.
- 조사 단계에서 코드 직접 수정, 리팩터, revert는 금지한다.
- 모든 근거 문서는 `UTF-8 only`다. `question-mark triplet`, `U+FFFD replacement char`, 깨진 한글이 보이면 즉시 중단하고 인코딩 이상으로 기록한다.
- 개별 후보 finding은 `PASS 3` 전까지 확정으로 취급하지 않는다.
- 기존 slice 문서가 있어도 이번 오더는 `프론트-백엔드 전체 표면`을 다시 잠그는 상위 조사 문서다.
- 실행은 항상 순차 진행으로 고정한다.
  - `master order 보강 -> FBX-T1 -> FBX-T2 -> FBX-T3 -> FBX-T4 -> FBX-T5 -> FBX-T6 -> 통합본 -> 통합본 3PASS 재감리`

---

## 1. 왜 새 오더가 필요한가

기존 문서는 `Stage 0 connectivity`, `frontend-backend remediation`, `desktop bridge`, `UI codebase health`처럼 부분 축을 다뤘다. 그러나 지금 필요한 것은 다음을 한 번에 묶는 `전역 오더`다.

- `geuldobi-desktop/src/index.html`의 renderer surface 전체
- `geuldobi-desktop/src/preload.js`와 `geuldobi-desktop/src/main.js`의 IPC/HTTP bridge 전체
- `modules/api/bridge_server.py`의 `/run`, `/status`, `/quality/*`, `/safe-ops/preview`, `/run/{id}/input`, `WS /events`
- `modules/api/process_runner.py`의 Mode A/B, stdin sequence, env propagation, packaged fallback
- `build/build_release.ps1`, `build/backend_entry.py`, `geuldobi-desktop/package.json`의 dev/prod parity
- 관련 테스트, 계약 문서, stale copy, dead surface, direct bypass surface

즉 이번 오더의 핵심은 "연결성 일부"가 아니라, `UI에서 보이는 의미`와 `실제 backend/runner/build가 수행하는 의미`가 전 경계에서 같은지 재잠금하는 것이다.

---

## 2. 현재 기준선

### 2.1 선행 조사로 이미 확인한 사실

1. active Electron entry는 `geuldobi-desktop/package.json`의 `"main": "src/main.js"`다.
2. packaged resource 계약은 `backend`, `engine`, `python-embed` 3축이다.
3. renderer의 localhost 직접 연결은 현재 아래 세 갈래가 핵심이다.
   - `splash.js`의 `GET /status` polling
   - `index.html`의 `WS /events` 연결
   - `index.html`의 외부 Google API key 테스트 fetch
4. backend bridge는 현재 아래 read/write surface를 가진다.
   - `POST /run`
   - `POST /stop`
   - `GET /status`
   - `POST /run/{run_id}/input`
   - `GET /quality/summary`
   - `GET /quality/dashboard`
   - `GET /safe-ops/preview`
   - `POST /quality/review`
   - `WS /events`
5. `ProcessRunner`는 `0,1,2,3,4,5,6,44,77,88,99` 키를 기본 `Mode B`로 처리한다.
6. Stage 0 style cache choice 주입은 현재 `key=0`, `sub_key=6`에서만 일어난다.
7. `geuldobi-desktop/main.js`는 active entry가 아니며, 현재 `src/main.js`와 해시가 다르고 최신 work guard template IPC도 빠져 있다.
8. `geuldobi-desktop/package.json`의 `test` 스크립트는 desktop 관련 일부 회귀만 포함하며, bridge HTTP/quality dashboard/risk gate 테스트는 포함하지 않는다.

### 2.2 선행 regression 실행 결과

아래 확장 회귀군을 직접 실행해 현재 기준선은 녹색임을 확인했다.

```powershell
python -m pytest -q `
  tests/test_run_validator.py `
  tests/test_api_contract.py `
  tests/test_bridge_server_http_contract.py `
  tests/test_bridge_server_desktop_risk_gate.py `
  tests/test_bridge_quality_summary.py `
  tests/test_frontend_frontier_lag_wiring.py `
  tests/test_frontend_stage0_connectivity.py `
  tests/test_ui_renderer_sanitization.py `
  tests/test_desktop_contract_refresh.py `
  tests/test_desktop_work_guard_template_contract.py `
  tests/test_process_runner_stage0_inputs.py
```

결과:

- `151 passed in 3.48s`

이 결과는 baseline 근거로 사용하되, 최종 확신도 95%는 아래 3PASS 및 live/dev parity 근거까지 채워야만 선언 가능하다.

---

## 3. 조사 범위

### 포함

| 구간 | 주요 파일 |
|------|-----------|
| Renderer / Splash | `geuldobi-desktop/src/index.html`, `geuldobi-desktop/src/splash/splash.js` |
| Preload / Main IPC | `geuldobi-desktop/src/preload.js`, `geuldobi-desktop/src/main.js` |
| Stale copy / package entry drift | `geuldobi-desktop/main.js`, `geuldobi-desktop/package.json` |
| Bridge / Runner | `modules/api/bridge_server.py`, `modules/api/process_runner.py`, `modules/api/run_validator.py`, `modules/api/risk_approval.py`, `modules/api/prompt_broker.py`, `modules/api/prompt_classifier.py` |
| Engine handoff | `main_a.py`의 메뉴 boot 경로 중 runner와 직접 맞물리는 부분 |
| Build / Package | `build/build_release.ps1`, `build/backend_entry.py` |
| Contract / Docs | `docs/implementation/api-contract-v1.yaml`, `README.md`, `geuldobi-desktop/DESKTOP-GUIDE.md`, 관련 remediation 문서 |
| Regression | frontend/desktop/bridge 관련 pytest 일체 |

### 제외

- Stage 2/3/4 서사 알고리즘 품질 자체
- LLM prompt 품질 심사 자체
- renderer 구조 전면 분해
- CSP strict mode 전환
- packaged installer 수동 QA 전체
- 코드 수정, 배포, 버전 bump

---

## 4. 6개 트랙

| 트랙 | 초점 | 핵심 질문 |
|------|------|-----------|
| `FBX-T1` | Renderer / Splash / direct surface | renderer가 쓰는 surface가 preload/bridge 계약과 정확히 맞는가. 승인된 direct fetch/ws 외 우회 경로가 없는가 |
| `FBX-T2` | Preload / Electron main / IPC | `window.geuldobiDesktop.*` 사용처, preload 노출, `ipcMain.handle`, backend 요청이 1:1 대응하는가 |
| `FBX-T3` | FastAPI bridge / read-only dashboard / risk gate | API contract, error code, status model, quality/safe-ops payload가 UI 기대와 맞는가 |
| `FBX-T4` | ProcessRunner / boot/menu handoff | Mode A/B, stdin sequence, env, style cache injection, risk approval handoff가 실제 menu boot와 맞는가 |
| `FBX-T5` | Build / package / stale copy drift | dev/prod parity가 유지되는가. stale duplicate source가 active surface와 혼동을 만들지 않는가 |
| `FBX-T6` | Regression / docs / confidence closure | `npm test` 외 누락 회귀를 포함해 전체 gate를 잠그는가. 95% 확신도 ledger를 방어할 수 있는가 |

---

## 5. 트랙별 상세 조사 포인트

### FBX-T1 Renderer / Splash / direct surface

대상:

- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/splash/splash.js`

핵심 점검:

1. `window.geuldobiDesktop.*` 사용 목록을 전수 추출한다.
2. direct `fetch()`와 `WebSocket()` 호출을 전수 추출해 `허용된 직접 surface`와 `우회 surface`로 분류한다.
3. run panel, quality dashboard, safe ops, quality review, project config, work_guard template, material import/delete, workspace open이 모두 preload surface를 통해 들어가는지 확인한다.
4. sanitization helper가 고위험 동적 surface에 일관되게 적용되는지 회귀 근거와 함께 잠근다.
5. `connect-src` CSP가 실제 네트워크 표면과 일치하는지 확인한다.

초기 집중 포인트:

- splash의 `GET /status`
- renderer의 `WS /events`
- API key test의 외부 direct fetch
- risk approval 입력이 prompt 기반인지, backend request surface와 별개인지

### FBX-T2 Preload / Electron main / IPC

대상:

- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/main.js`

핵심 점검:

1. preload에 노출된 모든 메서드와 renderer 사용처를 대조한다.
2. 모든 preload 메서드가 `ipcMain.handle` 또는 `ipcMain.on`과 연결되는지 확인한다.
3. `bridge:run`, `bridge:stop`, `bridge:status`, `bridge:get-url`, `bridge:get-cli-contract`, `project:*`, `material:*`, `workspace:*`의 full matrix를 만든다.
4. settings, materials, project config, work_guard template, workspace path, splash event, app ready event가 모두 main process에서 정상 처리되는지 확인한다.
5. `bridgeFetch()`가 HTTP error envelope을 어떻게 normalise하는지 기록하고 UI 기대와 비교한다.

초기 집중 포인트:

- work_guard template IPC는 `src/main.js`에 있고 `geuldobi-desktop/main.js`에는 없다.
- `approval_id`는 preload -> main -> `/run` body까지 전달된다.

### FBX-T3 FastAPI bridge / dashboard / risk gate

대상:

- `modules/api/bridge_server.py`
- `modules/api/run_validator.py`
- `modules/api/risk_approval.py`
- `docs/implementation/api-contract-v1.yaml`

핵심 점검:

1. 실제 route 목록과 API contract 문서를 대조한다.
2. `RunAccepted`, `ErrorEnvelope`, `StatusEnvelope` 필드와 error code enum이 runtime과 일치하는지 확인한다.
3. risk approval gate가 desktop mode에서도 `approval_id`를 강제하는지 검증한다.
4. `quality/summary`, `quality/dashboard`, `safe-ops/preview`, `quality/review`가 read-only/read-write 경계를 지키는지 확인한다.
5. websocket event payload가 `run_started`, `stdout`, `run_completed`, `run_failed`, `run_stopped`, prompt flow를 일관되게 전달하는지 확인한다.

초기 집중 포인트:

- bridge 서버는 run bridge만이 아니라 dashboard 집계 책임까지 갖고 있다.
- UI는 이 read-only payload를 깊게 소비하므로 shape drift를 별도 finding 후보로 분리한다.

### FBX-T4 ProcessRunner / boot/menu handoff

대상:

- `modules/api/process_runner.py`
- `main_a.py`의 boot/menu entry 관련 surface
- `build/backend_entry.py`

핵심 점검:

1. `project_index`, `genre_index`, 장르 mismatch confirm, `key/sub_key`의 stdin sequence를 전수 표로 고정한다.
2. Mode A와 Mode B의 차이, stdin close 여부, prompt 감지 방식, last prompt diagnostics를 정리한다.
3. `stage0_style_cache_mode` 주입이 실제 sub_key 6에만 걸리는지 확인한다.
4. env propagation이 `GOOGLE_API_KEY`, 추가 키, `GEULDOBI_WORKSPACE`, `GEULDOBI_PROJECTS_ROOT`, `GEULDOBI_ENGINE_EXE`, `GEULDOBI_PYTHON_PATH`까지 정확히 이어지는지 확인한다.
5. packaged fallback과 source-tree fallback이 `cwd/workspace` 기준으로 충돌하지 않는지 본다.

### FBX-T5 Build / package / stale copy drift

대상:

- `geuldobi-desktop/package.json`
- `build/build_release.ps1`
- `build/backend_entry.py`
- `geuldobi-desktop/main.js`
- `geuldobi-desktop/src/main.js`

핵심 점검:

1. dev mode와 packaged mode의 backend/engine/python 경로가 같은 의미를 유지하는지 확인한다.
2. `extraResources`와 `build_release.ps1` staging 로직이 같은 산출물을 기대하는지 확인한다.
3. active entry가 아닌 duplicate source가 존재할 때, 패키징/수정/감리에서 혼동을 만드는지 판정한다.
4. `files: ["src/**/*"]` 때문에 제외되는 파일과 실제 runtime entry를 명시적으로 분리한다.
5. stale copy는 `dead`, `stale but benign`, `high-risk drift source` 중 하나로 분류한다.

초기 집중 포인트:

- `geuldobi-desktop/main.js`는 active runtime entry가 아니다.
- 그러나 사람은 이 파일을 수정 대상으로 착각할 수 있으므로 `drift amplifier` 후보로 본다.

### FBX-T6 Regression / docs / confidence closure

대상:

- frontend/desktop/bridge 관련 pytest
- `README.md`
- `geuldobi-desktop/DESKTOP-GUIDE.md`
- `docs/implementation/api-contract-v1.yaml`
- 관련 remediation 문서

핵심 점검:

1. `npm test`가 실제 전역 프론트-백엔드 조사 게이트로 충분한지 판정한다.
2. 현재 누락된 bridge/dashboard/risk gate 회귀가 package script 밖에 있는지 명시한다.
3. 문서와 코드의 역할 분담이 현재 runtime surface와 맞는지 확인한다.
4. 최종 confidence ledger를 작성하고, 95% 미달 사유가 남으면 구체적으로 적는다.
5. `PASS1 후보 -> PASS2 제거 -> PASS3 확정` 통합본을 만들고 오탐 제거 기록을 남긴다.

---

## 6. 3PASS 프로토콜

### PASS 1 - 표면 전수 인벤토리

- 파일을 전수 읽고 아래 매트릭스를 만든다.
  - renderer symbol
  - preload method
  - ipc handler
  - HTTP/WS path
  - backend function
  - runner/process/build consumer
  - test evidence
  - doc evidence
- surface는 반드시 아래 중 하나로 분류한다.
  - `live`
  - `direct-but-approved`
  - `stale-duplicate`
  - `dead-candidate`
  - `doc-only`

### PASS 2 - 교차 검증

- expanded pytest gate를 다시 실행한다.
- `package.json`, `build_release.ps1`, `backend_entry.py`를 대조해 dev/prod parity를 확인한다.
- `geuldobi-desktop/main.js`와 `geuldobi-desktop/src/main.js`를 해시와 handler 목록으로 비교한다.
- API contract 문서와 실제 route/error/status 모델을 대조한다.
- renderer direct fetch/ws 목록이 PASS 1 분류와 맞는지 오탐 제거한다.

### PASS 3 - 최종 재감리

- 확정 finding만 `FBX-TN-SEQ` 형식으로 채택한다.
- severity는 `P0`, `P1`, `P2`, `P3`로 고정한다.
- 각 finding에 아래 8개 필드를 강제한다.
  1. ID
  2. Severity
  3. 현상 요약
  4. 코드 근거
  5. 사용자/운영 영향
  6. 테스트 근거 또는 테스트 부재
  7. 중복 여부
  8. 권장 후속 조치

---

## 7. 95% 확신도 게이트

아래 ledger를 모두 채워야만 `95%`를 주장할 수 있다.

| 항목 | 점수 |
|------|------:|
| 전역 surface inventory 완료 | +60 |
| expanded pytest gate 녹색 | +10 |
| renderer-preload-main-backend-runner chain 교차 검증 | +10 |
| build/package/dev parity 검증 | +10 |
| stale duplicate / direct bypass 분류 완료 | +5 |
| 합계 | 95 |

감점 규칙:

- live boot 또는 dev spike 근거가 전혀 없으면 `-5`
- unresolved `P1`가 남으면 `-5`
- `package.json` test gate와 실제 조사 gate 사이 누락 회귀가 미정리면 `-5`
- `npm --prefix geuldobi-desktop run start:spike`가 실패하면 코드 수정 없이 실패 로그를 evidence로 남기고 confidence를 `90` 이하로 cap 한다

즉, 최종 95%는 아래 조건을 동시에 만족할 때만 가능하다.

1. `P0` 0건
2. unresolved `P1` 0건
3. expanded pytest gate 통과
4. stale duplicate와 direct surface가 `live/stale/dead`로 전부 분류됨
5. 최소 1회 dev spike 또는 동등 runtime proof가 첨부됨

위 중 하나라도 빠지면 `95%` 선언 금지다.

---

## 8. compaction 대응 / 연속 진행 규칙

컨텍스트 compaction 이후에도 이 조사 체인을 끊기지 않게 재개하려면 아래 순서를 강제한다.

### 8.1 재개 시 최우선 재오픈 문서

1. 본 문서 `frontend-backend-global-full-survey-audit-order.md`
2. 마지막으로 수정된 `FBX-T*` 개별 문서
3. `frontend-backend-global-consolidated-findings.md`가 있으면 그 문서
4. `frontend-backend-global-consolidated-findings-3pass-reaudit.md`가 있으면 그 문서

### 8.2 재개 판단 기준

- 기억으로 현재 위치를 추정하지 않는다.
- 아래 4개 중 가장 최근에 실제 파일로 남아 있는 지점을 재개 포인터로 삼는다.
  1. 마지막 완료된 트랙 문서
  2. 마지막 완료된 PASS 로그
  3. 마지막 retained open set
  4. 통합본의 마지막 반영 시점

### 8.3 Resume Packet 최소 슬롯

모든 `FBX-T*` 문서와 통합 문서 말미에는 아래 6개 슬롯을 남긴다.

1. `Current phase`
2. `Last completed pass`
3. `Last completed surface`
4. `Next surface`
5. `Reopen reason codes used`
6. `Stop gate or blocker`

### 8.4 연속 진행 규칙

- 정지 게이트가 없으면 다음 미완료 트랙으로 바로 이동한다.
- 트랙 안에서는 `PASS 1 -> PASS 2 -> PASS 3`를 끊지 않는다.
- compaction이 발생해도 같은 트랙의 같은 PASS를 다시 처음부터 추정하지 말고, 파일에 남은 마지막 PASS 상태부터 재개한다.
- baseline reopen은 reason code 없이 허용하지 않는다.
- 통합본이 생성된 뒤에는 개별 트랙보다 통합본이 더 최신이면 통합본을 기준으로 재개한다.

---

## 9. 권장 검증 명령

```powershell
rg -n "geuldobiDesktop\\.|fetch\\(|WebSocket\\(" geuldobi-desktop/src/index.html geuldobi-desktop/src/splash/splash.js
rg -n "ipcMain.handle|ipcMain.on|contextBridge|bridgeFetch|spawn\\(" geuldobi-desktop/src/preload.js geuldobi-desktop/src/main.js
rg -n "@app\\.(get|post|websocket)|def .*endpoint|validate_run_request|RiskApprovalGate|PromptBroker" modules/api
Get-FileHash geuldobi-desktop/main.js -Algorithm SHA256
Get-FileHash geuldobi-desktop/src/main.js -Algorithm SHA256
python -m pytest -q tests/test_run_validator.py tests/test_api_contract.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_bridge_quality_summary.py tests/test_frontend_frontier_lag_wiring.py tests/test_frontend_stage0_connectivity.py tests/test_ui_renderer_sanitization.py tests/test_desktop_contract_refresh.py tests/test_desktop_work_guard_template_contract.py tests/test_process_runner_stage0_inputs.py
npm --prefix geuldobi-desktop run start:spike
```

주의:

- `npm test`만으로는 조사 완료 선언 금지
- `npm start:spike` 실패 시 로그와 실패 지점을 evidence로 남기고 confidence를 감점한다

---

## 10. 산출물

`docs/2026-03-13/` 아래에 아래 파일을 만든다.

1. `frontend-backend-global-full-survey-audit-order.md`
2. `FBX-T1-renderer-splash-direct-surface-findings.md`
3. `FBX-T2-preload-electron-ipc-findings.md`
4. `FBX-T3-bridge-backend-contract-findings.md`
5. `FBX-T4-process-runner-engine-handoff-findings.md`
6. `FBX-T5-build-package-stale-drift-findings.md`
7. `FBX-T6-regression-doc-confidence-findings.md`
8. `frontend-backend-global-consolidated-findings.md`
9. `frontend-backend-global-consolidated-findings-3pass-reaudit.md`

---

## 11. 완료 판정

아래를 모두 만족해야 본 오더를 닫는다.

1. `FBX-T1 ~ FBX-T6` 문서가 모두 존재한다.
2. 각 문서가 `PASS 1`, `PASS 2`, `PASS 3` 요약을 가진다.
3. 통합본이 개별 finding을 재구성하고 중복/오탐 제거를 명시한다.
4. confidence ledger가 숫자로 채워진다.
5. 최종 문서가 `95%` 또는 그 미달 사유를 구체적으로 적는다.
6. UTF-8 오염이 없다.

---

## 12. 현재 상태

- 본 오더는 `completed` 상태로 닫혔다.
- `FBX-T1 ~ FBX-T6`, 통합본, 통합본 3PASS 재감리 문서가 모두 생성됐다.
- expanded pytest gate는 `151 passed in 3.48s`로 유지됐고, `npm --prefix geuldobi-desktop run start:spike` runtime proof도 성공했다.
- UTF-8 오염 검사는 문서 체인 전체에서 `NO_ENCODING_ISSUES`로 닫혔다.
- 후속 문서로 `frontend-backend-global-remediation-execution-ssot.md`와 `frontend-backend-global-remediation-3pass-audit.md`가 추가됐다.
- 현재 실행 포인터는 `frontend-backend-global-remediation-3pass-audit.md`의 `execution-ready / 95% confidence`다.
- 코드 수정은 별도 remediation 오더에서만 논의한다.
