# 프론트엔드 전역 전량 전수조사 오더

> 작성일: 2026-03-13
> 트랙: `frontend-global`
> 상태: `execution-ready`
> 목적: 데스크톱 프론트엔드의 renderer, Electron shell, preload IPC, bridge 계약, 패키징, 자산, 회귀 신뢰도를 현재 worktree 기준으로 전량 조사한다.
> 방식: 6-terminal 분할, 각 terminal 자체 3PASS, 통합본 3PASS 재감리

---

## 0. 문서 역할

- 이 문서는 `프론트엔드 전역 전량 전수조사` 실행 오더다.
- 이 문서는 코드 수정 오더가 아니다.
- 이 문서는 단순 UI 미관 리뷰 문서가 아니다.
- 이 문서는 `geuldobi-desktop`만 보는 협소한 체크리스트도 아니다.
- 결과 finding namespace는 `[FGS-TN-SEQ]`로 고정한다.
- 터미널 산출물과 통합 감리 문서가 채워지기 전까지는 어떤 항목도 확정 finding으로 간주하지 않는다.

---

## 1. 왜 별도 트랙이 필요한가

기존 문서는 프론트엔드 표면의 일부만 다뤘다.

- [frontend-desktop-bridge-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md): desktop-bridge 연결면 중심 감사
- [ui-frontend-backend-connectivity-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md): 연결성 remediation 범위 고정
- [stage0-work-guard-style-cache-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/stage0-work-guard-style-cache-remediation-execution-ssot.md): Stage 0 작품가드/스타일캐시 보강
- [main_a-control-plane-detail-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md): `main_a.py` control plane 조사
- [main_a-control-plane-detail-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-remediation-execution-ssot.md): control plane remediation

그러나 아직 아래 축을 한 문서로 잠근 적은 없다.

- `geuldobi-desktop/src/index.html` 단일 renderer의 액션 맵, 상태머신, sanitization, 설정 surface
- `geuldobi-desktop/src/main.js`, `preload.js`, `splash/*`의 IPC와 lifecycle 경계
- `bridge_server.py`, `process_runner.py`, `run_validator.py`, `main_a.py`, `prompt-map`, `api-contract`가 공유하는 실행 계약
- `package.json`, `build_release.ps1`, `backend_entry.py`, `DESKTOP-GUIDE.md`가 말하는 packaged artifact model
- `geuldobi-desktop/src/sprites/`와 `UI/`의 live asset vs reference archive 분리
- `geuldobi-desktop/main.js`, `sprite_test.html`, `temp-electron-*.js` 같은 shadow/utility 파일의 생존 이유와 shipping risk
- source-string 비중이 높은 프론트엔드 회귀 테스트가 실제 제품 surface를 얼마나 방어하는지

이번 오더는 위 표면을 하나의 `frontend global` 조사축으로 묶는다.

---

## 2. 공통 조사 규약

### 2.1 조사 모드

- `static`
- `read-only`
- `code-and-test verification`
- `source-report cross-check`
- `filesystem inventory`

### 2.2 허용 증거 층

각 claim은 아래 증거 층 중 최소 2개로 재검증한다.

1. 코드
2. 읽기 전용 테스트
3. 문서/명세
4. 파일시스템 상태
5. shadow file 또는 최근 변경 흔적

두 번째 근거가 없는 항목은 `finding`으로 승격하지 않고 `hypothesis`, `runtime-only`, `needs-live-check`로 내린다.

### 2.3 금지사항

- 코드 수정 금지
- `npm build`, Electron 실행 금지
- packaged installer 수동 QA 금지
- live rerun, canary, destructive op 실검증 금지

예외:

- read-only 근거층 보강을 위한 focused `pytest`는 허용한다.
- 단, 빌드/패키징/실행을 동반하는 테스트는 금지한다.

### 2.4 오탐 방지 원칙

- `unsafe-inline` 존재 자체만으로 finding을 올리지 않는다. Electron 보안 경계와 실제 동적 surface를 함께 본다.
- 단일 대형 `index.html` 자체는 finding이 아니다. 계약 드리프트, 상태 충돌, 테스트 신뢰도 하락이 입증될 때만 승격한다.
- `UI/` 같은 자산 아카이브는 런타임 참조, 빌드 포함, 문서 오인도 중 하나가 입증될 때만 finding 후보가 된다.
- 과거 문서에서 닫힌 항목은 현재 코드/문서/파일시스템이 직접 충돌할 때만 재오픈한다.

### 2.5 3PASS 프로토콜

#### PASS 1 - 초벌 스캔

- 담당 범위의 public entrypoint, helper, IPC handler, 문서, 테스트를 전부 읽는다.
- 후보 finding을 `HIGH`, `MED`, `LOW` 확신도로 분류한다.
- 기존 문서에 이미 등장한 surface인지 표시한다.

#### PASS 2 - 교차 검증

- 코드, 테스트, 문서, 파일시스템을 함께 대조한다.
- 기존 문서의 결론과 현재 worktree가 다르면 차이의 원인을 먼저 명시한다.
- closed item 재오픈은 `현재 코드 직접 반증`이 있을 때만 허용한다.

#### PASS 3 - 확정

- 확정 항목만 `[FGS-TN-SEQ]` 형식으로 채택한다.
- 보고서 말미에 `PASS1 후보 N건 -> PASS2 제거 M건 -> 최종 K건` 요약을 남긴다.
- 미확정 항목은 `coverage gap` 또는 `open question`으로 분리한다.

### 2.6 finding 기록 형식

각 finding은 아래 8개 필드를 반드시 가진다.

1. ID
2. Severity (`P0`, `P1`, `P2`, `P3`)
3. 현상 요약
4. 코드 근거
5. 테스트/문서/파일시스템 보조 근거
6. counter-evidence review
7. 현재 상태 (`confirmed`, `rejected`, `runtime-only`, `needs-live-check`)
8. 권장 후속 조치

### 2.7 Severity 기준

- `P0`: 앱 부팅 불가, 잘못된 파괴적 작업 우회, 전혀 다른 프로젝트/경로 실행, packaged artifact 붕괴
- `P1`: action/key/sub_key drift, approval 경계 파손, workspace/root split, build-doc-contract 붕괴
- `P2`: 설정/상태 동기화 누락, test trust gap, shadow surface drift, 자산/문서/패키징 의미 불일치
- `P3`: 관측성, 로그, dead UI, naming, 유지보수성, source-string brittle test 의존

---

## 3. 기준 문서

- [frontend-desktop-bridge-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md)
- [ui-frontend-backend-connectivity-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md)
- [stage0-work-guard-style-cache-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/stage0-work-guard-style-cache-remediation-execution-ssot.md)
- [main_a-control-plane-detail-full-survey-audit-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-full-survey-audit-order.md)
- [main_a-control-plane-detail-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/main_a-control-plane-detail-remediation-execution-ssot.md)
- [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml)
- [prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)
- [DESKTOP-GUIDE.md](C:/Users/User/Desktop/글도비/geuldobi-desktop/DESKTOP-GUIDE.md)

주의:

- 위 문서들은 참고 기준선이지 자동 정답이 아니다.
- 현재 코드와 파일시스템이 우선이다.

---

## 4. 조사 범위 지도

| Terminal | 초점 | 핵심 범위 |
|---------|------|-----------|
| T1 | Renderer Action Surface | `index.html` 액션 맵, Stage 0/2/3/4/One-Stop/Frontier, 로그/품질/안전 패널 |
| T2 | Project / Settings / Material Surface | 프로젝트 선택, 설정 저장, 작품가드 템플릿, material import/delete, workspace UX |
| T3 | Electron Shell / IPC / Splash | `main.js`, `preload.js`, `splash/*`, window/security/lifecycle, shadow main |
| T4 | Bridge / Runner / Backend Contract | `bridge_server.py`, `process_runner.py`, `run_validator.py`, `main_a.py`, API/Prompt 계약 |
| T5 | Packaging / Runtime Bundle / Asset Inventory | `package.json`, `build_release.ps1`, `backend_entry.py`, `DESKTOP-GUIDE.md`, `dist/`, `UI/`, `sprites/`, temp files |
| T6 | Regression Trust / Coverage Closure | package test script, frontend tests, behavior vs source-string trust, docs/test sync |

---

## 5. Terminal 1 - Renderer Action Surface

### 담당 범위

- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- [sprite_test.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/sprite_test.html)

### 핵심 검사 포인트

1. Stage 0 submenu, Stage 2~4, One-Stop, Frontier Lag, 운영 키 라벨/`data-key`/`data-sub-key`/`resolveActionMeta()`가 같은 실행 의미를 공유하는가
2. `project`, `genre`, `api_key`, offline 상태 gating이 실제 버튼 동작과 모순되지 않는가
3. `approvalId`, safe-ops confirm, prompt state, verdict state, pipeline strip가 서로 다른 상태머신을 보지 않는가
4. quality dashboard, safe ops preview, review 입력, artifact ladder, retrieval inspector가 fallback/merge 구조와 맞는가
5. 동적 HTML surface가 `escapeHtml`, `sanitizeToken` 정책과 일관적인가
6. sprite/canvas 로딩 실패가 renderer 전체 붕괴 없이 degrade 되는가
7. UI가 노출하는 Stage 0 선택지와 현재 backend가 허용하는 하위 옵션 집합이 같은가

### 필수 근거

- [test_frontend_stage0_connectivity.py](C:/Users/User/Desktop/글도비/tests/test_frontend_stage0_connectivity.py)
- [test_frontend_frontier_lag_wiring.py](C:/Users/User/Desktop/글도비/tests/test_frontend_frontier_lag_wiring.py)
- [test_ui_renderer_sanitization.py](C:/Users/User/Desktop/글도비/tests/test_ui_renderer_sanitization.py)

### 산출물

- `docs/2026-03-13/FGS-T1-renderer-action-surface-findings.md`

---

## 6. Terminal 2 - Project / Settings / Material Surface

### 담당 범위

- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)
- [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js)
- [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- [project_manager.py](C:/Users/User/Desktop/글도비/modules/core/project_manager.py)
- [runtime_paths.py](C:/Users/User/Desktop/글도비/modules/core/runtime_paths.py)
- [project_support.py](C:/Users/User/Desktop/글도비/modules/core/project_support.py)
- [work_guards](C:/Users/User/Desktop/글도비/work_guards)

### 핵심 검사 포인트

1. 프로젝트 선택, 생성, 설정 로드/저장, workspace 열기 surface가 같은 root semantics를 공유하는가
2. `author_directives.txt`, `work_guard.yaml`, work_guard template library가 실제 runtime 소비 경로와 이어지는가
3. material panel의 Bible/Treatment file import/delete/list가 경로 탈출 없이 동작 의미를 유지하는가
4. 장르 미설정, 프로젝트 미선택, API 키 미입력 상태에서 renderer와 backend 진입 조건이 엇갈리지 않는가
5. 설정 탭과 helper UI가 raw YAML과 helper-generated field를 덮어쓰는 방식이 설명과 일치하는가
6. packaged mode와 dev mode에서 settings path, workspace path, project path 설명이 drift 없이 유지되는가

### 필수 근거

- [test_desktop_work_guard_template_contract.py](C:/Users/User/Desktop/글도비/tests/test_desktop_work_guard_template_contract.py)
- [test_runtime_paths.py](C:/Users/User/Desktop/글도비/tests/test_runtime_paths.py)
- [test_project_support.py](C:/Users/User/Desktop/글도비/tests/test_project_support.py)
- [test_project_manager_hud_helpers.py](C:/Users/User/Desktop/글도비/tests/test_project_manager_hud_helpers.py)

### 산출물

- `docs/2026-03-13/FGS-T2-project-settings-material-findings.md`

---

## 7. Terminal 3 - Electron Shell / IPC / Splash

### 담당 범위

- [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js)
- [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js)
- [splash.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/splash/splash.html)
- [splash.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/splash/splash.js)
- [splash.css](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/splash/splash.css)
- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [geuldobi-desktop/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/main.js)
- `geuldobi-desktop/temp-electron-loadcheck.js`
- `geuldobi-desktop/temp-electron-paths.js`

### 핵심 검사 포인트

1. `contextIsolation=true`, `nodeIntegration=false`, preload-only bridge, CSP가 실제 renderer 사용 방식과 충돌하지 않는가
2. splash polling, backend ready signal, fallback timer, main window 전환이 race 없이 닫히는가
3. preload가 노출하는 surface와 `ipcMain.handle(...)` 목록이 정확히 1:1인가
4. backend 재시작, 종료, crash logging, `render-process-gone`, `did-fail-load` 훅이 복구/진단에 충분한가
5. `geuldobi-desktop/main.js` shadow 파일이 live path인지, dead copy인지, 문서 오인 유발 요소인지 분리되는가
6. temp Electron scripts가 shipping 대상인지, 로컬 spike 흔적인지, build/include 규칙과 충돌하는지 분명한가

### 필수 근거

- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [DESKTOP-GUIDE.md](C:/Users/User/Desktop/글도비/geuldobi-desktop/DESKTOP-GUIDE.md)
- [ui-frontend-backend-connectivity-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md)

### 산출물

- `docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md`

---

## 8. Terminal 4 - Bridge / Runner / Backend Contract

### 담당 범위

- [bridge_server.py](C:/Users/User/Desktop/글도비/modules/api/bridge_server.py)
- [process_runner.py](C:/Users/User/Desktop/글도비/modules/api/process_runner.py)
- [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)
- [backend_entry.py](C:/Users/User/Desktop/글도비/build/backend_entry.py)
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml)
- [prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)

### 핵심 검사 포인트

1. `key`, `sub_key`, `inputs`, `approval_id`, `/run/{run_id}/input`, `/status`, `/quality/*`, `/safe-ops/preview`가 UI와 backend에서 같은 의미를 갖는가
2. Stage 0 허용 sub_key 집합이 UI 노출, validator 화이트리스트, prompt-map, runner 입력 주입 로직에서 같은가
3. genre/project ordinal, boot confirm, style cache mode, work_guard setup가 `main_a.py` 인터랙티브 흐름과 deterministic하게 맞물리는가
4. `GEULDOBI_WORKSPACE`, `GEULDOBI_PROJECTS_ROOT`, `GEULDOBI_ENGINE_ROOT`, `GEULDOBI_ENGINE_EXE` 해석이 runner, bridge, backend entry에서 같은 runtime root를 가리키는가
5. risk approval gate, safe ops preview, quality review가 문서/테스트/코드에서 같은 approval boundary를 공유하는가
6. 문서상 계약과 실제 코드 사이에 `document-only key`, `hidden sub_key`, `ui-only action` drift가 남아 있는가

### 필수 근거

- [test_api_contract.py](C:/Users/User/Desktop/글도비/tests/test_api_contract.py)
- [test_bridge_server_http_contract.py](C:/Users/User/Desktop/글도비/tests/test_bridge_server_http_contract.py)
- [test_bridge_server_desktop_risk_gate.py](C:/Users/User/Desktop/글도비/tests/test_bridge_server_desktop_risk_gate.py)
- [test_bridge_quality_summary.py](C:/Users/User/Desktop/글도비/tests/test_bridge_quality_summary.py)
- [test_process_runner.py](C:/Users/User/Desktop/글도비/tests/test_process_runner.py)
- [test_process_runner_stage0_inputs.py](C:/Users/User/Desktop/글도비/tests/test_process_runner_stage0_inputs.py)
- [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py)
- [test_runtime_paths.py](C:/Users/User/Desktop/글도비/tests/test_runtime_paths.py)

### 산출물

- `docs/2026-03-13/FGS-T4-bridge-runner-contract-findings.md`

---

## 9. Terminal 5 - Packaging / Runtime Bundle / Asset Inventory

### 담당 범위

- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [build_release.ps1](C:/Users/User/Desktop/글도비/build/build_release.ps1)
- [backend_entry.py](C:/Users/User/Desktop/글도비/build/backend_entry.py)
- [backend.spec](C:/Users/User/Desktop/글도비/build/backend.spec)
- [DESKTOP-GUIDE.md](C:/Users/User/Desktop/글도비/geuldobi-desktop/DESKTOP-GUIDE.md)
- [geuldobi-desktop/dist](C:/Users/User/Desktop/글도비/geuldobi-desktop/dist)
- [dist](C:/Users/User/Desktop/글도비/dist)
- [sprites](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/sprites)
- [UI](C:/Users/User/Desktop/글도비/UI)
- [geuldobi-desktop/main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/main.js)
- `geuldobi-desktop/temp-electron-loadcheck.js`
- `geuldobi-desktop/temp-electron-paths.js`
- [sprite_test.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/sprite_test.html)

### 핵심 검사 포인트

1. `extraResources`, backend entry env, build output, guide 문서가 packaged artifact model을 같은 방식으로 설명하는가
2. 현재 저장소는 `engine.exe`를 전제로 하는지, `engine source bundle + embedded python`을 전제로 하는지 하나로 닫히는가
3. `dist/backend`, `dist/engine`, `python-embed`, `geuldobi-desktop/dist`의 현재 파일시스템 상태와 문서가 일치하는가
4. runtime asset인 `src/sprites/`와 reference archive인 `UI/`가 명확히 분리되는가
5. shadow file, temp script, sprite spike가 build 대상 또는 docs 대상에 잘못 끼어들지 않는가
6. packaged 모드에서 workspace/write path와 engine/read path의 설명이 빌드/문서/코드에서 같은가

### 필수 근거

- [frontend-desktop-bridge-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md)
- [DESKTOP-GUIDE.md](C:/Users/User/Desktop/글도비/geuldobi-desktop/DESKTOP-GUIDE.md)
- [build_release.ps1](C:/Users/User/Desktop/글도비/build/build_release.ps1)
- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)

### 산출물

- `docs/2026-03-13/FGS-T5-packaging-bundle-asset-findings.md`

---

## 10. Terminal 6 - Regression Trust / Coverage Closure

### 담당 범위

- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [test_desktop_contract_refresh.py](C:/Users/User/Desktop/글도비/tests/test_desktop_contract_refresh.py)
- [test_frontend_stage0_connectivity.py](C:/Users/User/Desktop/글도비/tests/test_frontend_stage0_connectivity.py)
- [test_frontend_frontier_lag_wiring.py](C:/Users/User/Desktop/글도비/tests/test_frontend_frontier_lag_wiring.py)
- [test_ui_renderer_sanitization.py](C:/Users/User/Desktop/글도비/tests/test_ui_renderer_sanitization.py)
- [test_desktop_work_guard_template_contract.py](C:/Users/User/Desktop/글도비/tests/test_desktop_work_guard_template_contract.py)
- [test_bridge_server_http_contract.py](C:/Users/User/Desktop/글도비/tests/test_bridge_server_http_contract.py)
- [test_bridge_server_desktop_risk_gate.py](C:/Users/User/Desktop/글도비/tests/test_bridge_server_desktop_risk_gate.py)
- [test_bridge_quality_summary.py](C:/Users/User/Desktop/글도비/tests/test_bridge_quality_summary.py)
- [test_process_runner_stage0_inputs.py](C:/Users/User/Desktop/글도비/tests/test_process_runner_stage0_inputs.py)
- [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py)
- [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml)
- [prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)

### 핵심 검사 포인트

1. 현재 프론트엔드 회귀망이 behavior-first인지, source-string brittle guard 중심인지 구분되는가
2. splash lifecycle, material file ops, workspace open path, packaged asset load, quality dashboard merge, offline mode가 테스트 사각지대인지 정리되는가
3. package-level `npm test` surface와 실제 포함 테스트 목록이 최신 프론트 계약을 반영하는가
4. 문서 명세와 테스트가 서로 다른 truth source를 잠그고 있지 않은가
5. 조사 종료 후 `95%` 확신도까지 방어 가능한지, 아니면 frontend surface 특성상 `needs-live-check`가 남는지 정직하게 계산되는가

### 필수 근거

- [test_desktop_contract_refresh.py](C:/Users/User/Desktop/글도비/tests/test_desktop_contract_refresh.py)
- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)
- [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml)
- [prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)

### 산출물

- `docs/2026-03-13/FGS-T6-regression-trust-findings.md`

---

## 11. 통합 산출물 규칙

각 terminal 문서는 아래 순서를 따른다.

1. 조사 범위
2. PASS 1 사실 수집
3. PASS 2 교차 검증
4. PASS 3 오탐 제거
5. 확정 findings
6. 기각 findings
7. coverage gap / open question
8. `PASS1 후보 N건 -> PASS2 제거 M건 -> 최종 K건`

최종 통합 문서는 아래 경로로 고정한다.

- `docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md`

선택 산출물:

- `docs/2026-03-13/frontend-global-full-survey-evidence-index.md`

통합본은 반드시 아래를 포함한다.

- T1~T6 finding ledger 재구성
- retained / rejected / runtime-only 분리
- 기존 문서와 충돌하는 결론이 있으면 차이 원인 명시
- `renderer`, `IPC`, `bridge`, `packaging`, `asset`, `regression` coverage 표

---

## 12. 완료 기준

- T1~T6 산출물 6건이 모두 존재한다
- 통합 감리 문서 1건이 존재한다
- 아래 surface가 모두 증거 index에 들어간다
  - renderer action map
  - project/settings/material surface
  - shell/preload/splash
  - bridge/runner/validator/backend contract
  - packaging/runtime bundle/asset inventory
  - regression trust/docs sync
- retained finding과 rejected finding이 명시적으로 분리된다
- 과거 문서에서 닫혔던 항목을 재오픈한 경우, current code/doc/filesystem 근거가 함께 제시된다
- 확신도 `95%` 또는 읽기 전용 기준 방어 가능한 상한이 제시된다
- 실제 remediation은 이 문서가 아니라 후속 execution SSOT에서만 다룬다

---

## 13. 이번 턴의 범위

- 원본 오더 작성 시점의 기본 범위는 `전수조사 오더 문서 작성`이었다.
- 2026-03-13 후속 지시로 실제 전수조사 실행과 3PASS 문서화까지 진행했다.
- 이번 execution에서는 코드 수정 없이, read-only pytest와 정적 대조만 사용했다.

## 14. 실행 산출물

2026-03-13 실행 결과 아래 문서들이 생성됐다.

- [FGS-T1-renderer-action-surface-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T1-renderer-action-surface-findings.md)
- [FGS-T2-project-settings-material-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T2-project-settings-material-findings.md)
- [FGS-T3-shell-ipc-splash-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md)
- [FGS-T4-bridge-runner-contract-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T4-bridge-runner-contract-findings.md)
- [FGS-T5-packaging-bundle-asset-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T5-packaging-bundle-asset-findings.md)
- [FGS-T6-regression-trust-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T6-regression-trust-findings.md)
- [frontend-global-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md)
- [frontend-global-full-survey-3pass-reaudit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-reaudit.md)
- [frontend-global-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-remediation-execution-ssot.md)
- [frontend-global-remediation-execution-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-remediation-execution-3pass-audit.md)
