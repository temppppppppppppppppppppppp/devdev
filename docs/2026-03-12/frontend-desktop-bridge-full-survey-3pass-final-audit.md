# 프론트엔드·데스크톱·브리지 연결 전수조사 3-Pass 최종 감사

작성일: 2026-03-12  
인코딩: UTF-8  
감사 기준선: `HEAD=b3cfa0e`, dirty worktree 기준 정적 감사  
가정: `Stage 4 limited canary`가 성공해 백엔드 Stage 4 계약은 닫혔다고 본다. 이번 문서는 그 이후 우선순위를 `프론트엔드/Electron/bridge/engine 연결면`으로 한정한다.

## Executive Summary

이번 감사의 결론은 단순하다.

- `프론트엔드를 볼 시점이다`는 맞다.
- 하지만 핵심 리스크는 디자인이나 렌더링 완성도보다 `Electron main ↔ bridge_server ↔ ProcessRunner ↔ main_a.py` 계약면에 있다.
- 가장 강한 문제는 packaged desktop에서 프로젝트 루트가 둘로 갈라지는 점이다.
  - Electron main은 `내 문서/글도비/projects`를 본다.
  - `bridge_server.py`의 품질/preview/review 엔드포인트는 `resources/engine/projects`를 본다.
  - `ProcessRunner`는 다시 `GEULDOBI_WORKSPACE`를 작업 디렉터리로 써서 런타임 산출물을 `내 문서/글도비` 쪽에 쓴다.
- 따라서 packaged desktop에서 `run` 경로와 `quality dashboard/safe ops/review` 경로가 같은 프로젝트를 본다는 보장이 없다. 이 항목은 이번 감사에서 `P1`로 확정했다.
- 두 번째 강한 문제는 release build 계약이다.
  - `geuldobi-desktop/package.json`은 `../dist/backend`와 `../dist/engine`을 둘 다 패키징 자원으로 요구한다.
  - 그런데 현재 저장소의 `build/build_release.ps1`은 `backend.exe`만 빌드하고, 실제 worktree에도 `dist/engine`이 없다.
  - 따라서 현재 저장소 상태만으로는 packaged desktop 재현성이 닫히지 않는다. 이것도 `P1`로 유지한다.
- 반대로 `프로젝트 설정 surface(author_directives/work_guard)가 엔진에 안 닿는다`는 이전 추정은 현재 코드 기준 오탐이다. Electron main이 프로젝트별 config 파일에 write-through 하고, `main_a.py`와 `ProjectManager`가 그것을 실제로 읽는다.

최종 retained finding은 `P1 2건`, `P2 2건`, `Observation 1건`이다. 현재 방어 가능한 확신도 상한은 `95%`다.

## 1. 조사 범위와 금지사항

포함 범위:

- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/splash/splash.js`
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/DESKTOP-GUIDE.md`
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/api/run_validator.py`
- `build/backend_entry.py`
- `build/backend.spec`
- `build/build_release.ps1`
- `main_a.py`
- `modules/core/project_manager.py`
- 읽기 전용 테스트:
  - `tests/test_process_runner.py`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_api_contract.py`
  - `tests/test_ui_service.py`
- 이전 감사 문서:
  - `docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md`
  - `docs/2026-03-12/system-wide-full-audit-3pass-merged-final.md`
  - `docs/2026-03-09/ui-system-audit.md`

금지사항:

- 코드 수정 안 함
- 테스트 실행 안 함
- Electron 실행/패키징 빌드/실제 데스크톱 수동 검증 안 함

허용한 증거 층:

- 코드
- 읽기 전용 테스트
- 문서
- 현재 파일시스템 상태(`dist/engine` 존재 여부 등)

## 2. 기준선과 조사 버킷

이번 감사는 아래 6개 버킷으로 고정했다.

1. Electron startup/window/splash
2. IPC/preload/renderer action wiring
3. bridge_server/process_runner/main_a 입력 계약
4. packaged mode의 workspace/project root 정합성
5. release build/packaging 계약
6. 테스트/문서 동기화 상태

이전 system-wide 감사는 Electron 항목을 `symbolic packaging contract` 수준으로만 확인해 non-finding으로 닫았지만, 이번 감사는 여기에 `실제 파일 존재`, `packaged env`, `workspace root split`, `테스트 공백`까지 추가로 얹었다.

## 3. Pass 1. 사실 수집

### 3.1 Electron main / preload / renderer 토폴로지

- Electron main은 `STATUS_BASE_URL = http://127.0.0.1:8300`을 고정 사용한다.
  - 근거: `geuldobi-desktop/src/main.js:20`, `geuldobi-desktop/src/main.js:279`, `geuldobi-desktop/src/main.js:312-313`
- 개발 모드에서는 `python -m uvicorn modules.api.bridge_server:app --port 8300`을 직접 띄운다.
  - 근거: `geuldobi-desktop/src/main.js:78-84`
- 배포 모드에서는 `resources/backend/backend.exe`를 띄우고, env로 `GEULDOBI_WORKSPACE`와 `GEULDOBI_ENGINE_EXE`를 넘긴다.
  - 근거: `geuldobi-desktop/src/main.js:85-107`
- preload는 renderer에 `run/stop/status`, quality dashboard, safe ops preview, quality review, project list/create/config surface 저장 API를 노출한다.
  - 근거: `geuldobi-desktop/src/preload.js:3-48`
- renderer는 버튼 클릭 시 `window.geuldobiDesktop.runKey(key, subKey, inputs)`로 `/run`을 부른다.
  - 근거: `geuldobi-desktop/src/index.html:6315`
- renderer는 WebSocket으로 `run_started`, `stdout`, `run_completed`, `run_failed`, `prompt_request`를 소비한다.
  - 근거: `geuldobi-desktop/src/index.html:5619-5790`

### 3.2 CLI 입력 계약

- renderer는 `GENRE_INDEX_MAP`으로 장르를 숫자 인덱스로 바꾼다.
  - 근거: `geuldobi-desktop/src/index.html:5437-5448`
- renderer는 프로젝트 dropdown의 현재 순서를 `project_index`로 보존한다.
  - 근거: `geuldobi-desktop/src/index.html:5501-5523`, `geuldobi-desktop/src/index.html:5534-5540`
- `ProcessRunner`는 이 `genre_index`, `project_index`를 stdin 시퀀스로 변환한다.
  - 근거: `modules/api/process_runner.py:550-624`
- `main_a.py`는 여전히 `_select_genre()`와 `_select_project()`의 숫자 기반 CLI 흐름을 사용한다.
  - 근거: `main_a.py:950-952`, `main_a.py:2808-3017`, `main_a.py:3019-3037`
- `_select_project()`는 `Path(self._PROJECTS_DIR).iterdir()` 순서를 그대로 사용한다.
  - 근거: `main_a.py:3028-3037`

### 3.3 품질 대시보드 / safe ops / review 표면

- renderer는 `quality_dashboard` 응답을 fallback 구조와 merge해 쓴다.
  - 근거: `geuldobi-desktop/src/index.html:3573-3652`, `geuldobi-desktop/src/index.html:4274-4311`
- `safe_ops`는 별도 endpoint 결과를 다시 merge한다.
  - 근거: `geuldobi-desktop/src/index.html:4341-4357`
- bridge는 `/quality/summary`, `/quality/dashboard`, `/safe-ops/preview`, `/quality/review`를 제공한다.
  - 근거: `modules/api/bridge_server.py:1412-1502`
- 이 payload는 `_build_quality_dashboard_payload()`와 `_build_safe_ops_preview_payload()`에서 만들어진다.
  - 근거: `modules/api/bridge_server.py:1134-1199`, `modules/api/bridge_server.py:1443-1456`

### 3.4 프로젝트 surface 저장 경로

- Electron main의 `project:list/create`는 packaged 모드에서 `getWorkspaceDir()/projects`를 사용한다.
  - 근거: `geuldobi-desktop/src/main.js:488-493`, `geuldobi-desktop/src/main.js:527-563`
- `project:save-config-surfaces`는 `{project}/config/author_directives.txt`, `{project}/config/work_guard.yaml`에 직접 쓴다.
  - 근거: `geuldobi-desktop/src/main.js:514-520`, `geuldobi-desktop/src/main.js:583-596`
- `ProjectManager`는 실제로 `author_directives.txt`를 로드한다.
  - 근거: `modules/core/project_manager.py:58-64`, `modules/core/project_manager.py:110-116`
- `main_a.py`는 실제로 `work_guard.yaml`을 로드해 guard 래퍼에 연결한다.
  - 근거: `main_a.py:1052-1057`

### 3.5 packaged mode 루트 경로

- `backend_entry.py`는 frozen 모드에서 `GEULDOBI_ENGINE_ROOT = resources/engine`를 주입한다.
  - 근거: `build/backend_entry.py:19-24`
- `process_runner.PROJECT_ROOT`는 `GEULDOBI_ENGINE_ROOT`를 우선 사용한다.
  - 근거: `modules/api/process_runner.py:33-35`
- 그런데 `ProcessRunner`는 subprocess `cwd`를 `GEULDOBI_WORKSPACE`로 잡는다.
  - 근거: `modules/api/process_runner.py:182-199`
- 반면 `bridge_server._get_project_dir()`는 `PROJECT_ROOT / "projects"`를 본다.
  - 근거: `modules/api/bridge_server.py:174-187`

### 3.6 패키징 / 빌드

- Electron package는 `../dist/backend`와 `../dist/engine`을 extraResources로 요구한다.
  - 근거: `geuldobi-desktop/package.json:39-48`
- 현재 `build/build_release.ps1`은 Step 2에서 `backend.exe`만 빌드한다.
  - 근거: `build/build_release.ps1:7-8`, `build/build_release.ps1:47-68`
- 현재 worktree에는 `dist/backend/backend.exe`는 존재하지만 `dist/engine`은 없다.
  - 근거: 파일시스템 확인 결과 `Test-Path dist\\engine == False`, `Test-Path dist\\backend\\backend.exe == True`

### 3.7 테스트/문서

- `geuldobi-desktop/package.json`의 `test` 스크립트는 `"No tests configured"`다.
  - 근거: `geuldobi-desktop/package.json:9-11`
- `tests/test_process_runner.py`는 runner 단위 계약을 본다.
  - 근거: `tests/test_process_runner.py`
- `tests/test_bridge_quality_summary.py`는 실제 quality endpoint를 직접 호출한다.
  - 근거: `tests/test_bridge_quality_summary.py:9-40`
- `tests/test_api_contract.py`는 실제 서버가 아니라 `RouterStub`로 오프라인 계약 검증을 한다.
  - 근거: `tests/test_api_contract.py:9-10`, `tests/test_api_contract.py:85-88`
- 따라서 `/run` 실제 서버, Electron IPC, renderer, packaged desktop end-to-end를 덮는 회귀망은 없다.

## 4. Pass 2. 교차 검증

### 4.1 packaged 프로젝트 루트 split

이 항목은 3층 교차 검증으로 confirmed 했다.

- Electron main packaged path:
  - `getWorkspaceDir()`는 `문서/글도비`
  - `getProjectsDir()`는 packaged 모드에서 `getWorkspaceDir()/projects`
  - 근거: `geuldobi-desktop/src/main.js:43-50`, `geuldobi-desktop/src/main.js:488-493`
- backend/env path:
  - `main.js`는 backend.exe spawn env에 `GEULDOBI_WORKSPACE`와 `GEULDOBI_ENGINE_EXE`를 넣는다.
  - 근거: `geuldobi-desktop/src/main.js:97-107`
- backend import/root path:
  - `backend_entry.py`는 `GEULDOBI_ENGINE_ROOT=resources/engine`
  - `process_runner.PROJECT_ROOT`는 그 값을 읽는다.
  - `bridge_server._get_project_dir()`는 `PROJECT_ROOT/projects`
  - 근거: `build/backend_entry.py:19-24`, `modules/api/process_runner.py:33-35`, `modules/api/bridge_server.py:174-187`

정리:

- packaged mode에서 `run` 경로는 `GEULDOBI_WORKSPACE` 쪽에서 실행된다.
- 하지만 quality/safe-ops/review read path는 `resources/engine/projects`를 향한다.
- 따라서 프로젝트 선택 UI, 실제 실행 산출물, 품질 대시보드가 같은 디렉터리를 본다고 볼 수 없다.

이 항목은 추정이 아니라 direct code contradiction이다.

### 4.2 release build completeness

이 항목도 3층 교차 검증으로 confirmed 했다.

- package 계약: `dist/backend`, `dist/engine`
  - 근거: `geuldobi-desktop/package.json:39-48`
- build 스크립트: `backend.exe`만 언급
  - 근거: `build/build_release.ps1:7-8`, `build/build_release.ps1:47-68`
- 실제 파일시스템: `dist/engine` 부재
  - 근거: 현재 worktree `Test-Path dist\\engine == False`

즉, source-level symbolic contract는 맞지만 operational build chain은 닫히지 않았다.

### 4.3 project surface wiring

이전 추정 중 하나는 여기서 기각했다.

- Electron main은 `{project}/config/author_directives.txt`, `work_guard.yaml`에 write-through 한다.
  - 근거: `geuldobi-desktop/src/main.js:514-520`, `geuldobi-desktop/src/main.js:583-596`
- `ProjectManager`는 `author_directives.txt`를 읽는다.
  - 근거: `modules/core/project_manager.py:110-116`
- `main_a.py`는 `work_guard.yaml`을 읽어 guard를 감싼다.
  - 근거: `main_a.py:1052-1057`

따라서 `설정 surface가 엔진과 분리돼 있다`는 과거 주장에는 현재 코드 기준 직접 반증이 있다.

### 4.4 quality dashboard payload drift 여부

이 항목은 `강한 리스크지만 즉시 bug 아님`으로 낮췄다.

- renderer는 `createEmptyQualityDashboard()` fallback을 갖고 있고,
- dashboard payload를 shallow merge + section merge로 받는다.
  - 근거: `geuldobi-desktop/src/index.html:3573-3652`, `geuldobi-desktop/src/index.html:4274-4311`
- bridge는 quality payload 기본 구조를 `_quality_dashboard_defaults()`로 제공한다.
  - 근거: `modules/api/bridge_server.py:191-293`
- `tests/test_bridge_quality_summary.py`도 이 payload 계열을 읽기 전용으로 검증한다.

따라서 `payload key 하나만 빠져도 renderer가 즉시 붕괴한다`는 주장은 오탐으로 봤다. 다만 renderer contract test 부재는 retained risk로 남긴다.

### 4.5 CLI ordinal coupling

이 항목은 현재 작동 중인 contract이지만, 강한 숨은 결합으로 confirmed 했다.

- renderer는 장르/프로젝트를 숫자로 직렬화한다.
  - 근거: `geuldobi-desktop/src/index.html:5437-5452`
- runner는 숫자 stdin 시퀀스로 밀어 넣는다.
  - 근거: `modules/api/process_runner.py:576-624`
- `main_a.py`는 여전히 숫자 순서 기반 선택기다.
  - 근거: `main_a.py:2808-3017`, `main_a.py:3019-3037`

이 구조는 현재는 맞지만, 앞으로 `main_a.py` 메뉴 순서/genre 순서/프로젝트 나열 정책이 바뀌면 데스크톱이 조용히 오작동할 수 있다.

### 4.6 테스트망

이 항목은 bug보다는 assurance gap으로 confirmed 했다.

- package-level Electron test 없음
  - 근거: `geuldobi-desktop/package.json:9-11`
- `/run` 계약은 실제 서버가 아니라 `RouterStub`로만 검증
  - 근거: `tests/test_api_contract.py:9-10`, `tests/test_api_contract.py:85-88`
- 실제 bridge quality endpoint unit test는 존재
  - 근거: `tests/test_bridge_quality_summary.py:9-40`
- runner unit test도 존재
  - 근거: `tests/test_process_runner.py`

즉, backend-adjacent 단위 보호막은 있으나 `Electron IPC + bridge live server + packaged path` 회귀망은 비어 있다.

## 5. Pass 3. 오탐 제거 및 재분류

### 5.1 기각한 주장

1. `프로젝트 설정 surface가 엔진과 분리돼 있다`
- 기각
- 이유: `author_directives.txt`와 `work_guard.yaml`은 실제 저장·로드 경로가 연결돼 있다.

2. `quality dashboard payload는 key 누락 시 즉시 프론트가 깨진다`
- 기각
- 이유: renderer fallback merge가 존재하고, bridge default payload도 존재한다.

3. `Electron packaging contract 자체가 코드와 분리돼 있다`
- 부분 기각
- 이유: symbolic contract 자체는 맞다.
- 다만 operational build chain과 packaged project root split은 별도 finding으로 승격했다.

### 5.2 관찰로 낮춘 항목

1. `splash fallback-timeout`
- `main.js`는 8초 뒤 main window를 먼저 띄울 수 있고, renderer는 5초 후 backend 미감지 배지를 보여준다.
- 현재 코드상 의도된 degraded UX로 보이며, 직접 붕괴 증거는 없다.

## 6. 확정 Findings

### F-FE-01. Packaged desktop에서 project root가 split된다

- Severity: `P1`
- 상태: `확인함`
- 깨진 계약:
  - Electron main의 프로젝트 관리와 bridge_server의 quality/read path가 같은 프로젝트 루트를 본다는 계약
- 직접 근거:
  - `geuldobi-desktop/src/main.js:43-50`
  - `geuldobi-desktop/src/main.js:97-107`
  - `geuldobi-desktop/src/main.js:488-493`
  - `build/backend_entry.py:19-24`
  - `modules/api/process_runner.py:33-35`
  - `modules/api/process_runner.py:182-199`
  - `modules/api/bridge_server.py:174-187`
  - `modules/api/bridge_server.py:1412-1502`
- 반대 근거 검토:
  - `ProcessRunner`가 workspace를 쓰므로 실행 경로 자체는 맞을 수 있다.
  - 하지만 `bridge_server`는 workspace가 아니라 `PROJECT_ROOT/projects`를 읽는다.
  - 즉 run path와 dashboard/review path가 분리된다.
- 왜 오탐이 아닌가:
  - packaged mode path 세트가 서로 다른 파일에서 직접 충돌한다.
  - 추정이 아니라 코드상 명시된 루트가 두 개다.
- 사용자 영향:
  - packaged desktop에서 quality dashboard가 비어 보이거나, safe ops preview/review가 실제 작업 프로젝트와 다른 위치를 읽고 쓸 수 있다.
- 테스트 미실행 사유:
  - Electron packaged app과 bridge live server를 실제 실행하지 않았다.

### F-FE-02. Release build chain이 `dist/engine`을 닫지 못한다

- Severity: `P1`
- 상태: `확인함`
- 깨진 계약:
  - release build가 Electron이 요구하는 `dist/backend`와 `dist/engine` 둘 다 공급해야 한다는 계약
- 직접 근거:
  - `geuldobi-desktop/package.json:39-48`
  - `build/build_release.ps1:7-8`
  - `build/build_release.ps1:47-80`
  - 현재 파일시스템: `dist/backend/backend.exe` 존재, `dist/engine` 부재
- 반대 근거 검토:
  - 별도 사외/비공개 engine 빌드 프로세스가 있을 수는 있다.
  - 그러나 저장소 내부 자동화 기준으로는 그 경로가 문서/스크립트에 없다.
- 왜 오탐이 아닌가:
  - repo 내 빌드 스크립트와 package 자원 계약 사이에 직접 공백이 있다.
- 사용자 영향:
  - packaged desktop release 재현성 불가
  - Electron Builder 단계에서 누락 또는 잘못된 bundle 위험
- 테스트 미실행 사유:
  - 실제 electron-builder를 돌리지 않았다.

### F-FE-03. Desktop run path는 `main_a.py` CLI ordinal contract에 숨겨져 결합돼 있다

- Severity: `P2`
- 상태: `확인함`
- 깨진 계약:
  - GUI action이 semantic API가 아니라 CLI 번호 순서와 prompt 흐름에 의존하지 않아야 한다는 일반적 desktop contract
- 직접 근거:
  - `geuldobi-desktop/src/index.html:5437-5452`
  - `geuldobi-desktop/src/index.html:5501-5523`
  - `modules/api/process_runner.py:576-624`
  - `main_a.py:2808-3017`
  - `main_a.py:3019-3037`
- 반대 근거 검토:
  - 현재 시점의 숫자 순서는 서로 일치한다.
  - 따라서 현재 즉시 broken state는 아니다.
- 왜 오탐이 아닌가:
  - 구조적 결합 자체는 명백하다.
  - `main_a.py` 순서 변경이 생기면 desktop 오작동이 조용히 발생할 수 있다.
- 사용자 영향:
  - 장르/프로젝트 오선택
  - Stage key 오주입
  - 프로젝트 순서 drift 시 다른 프로젝트 실행
- 테스트 미실행 사유:
  - 실제 GUI→bridge→main_a 대화형 흐름을 수동 실행하지 않았다.

### F-FE-04. Electron/renderer 회귀망이 거의 없다

- Severity: `P2`
- 상태: `확인함`
- 깨진 계약:
  - 프론트-브리지 계약에 대한 최소한의 회귀 안전망
- 직접 근거:
  - `geuldobi-desktop/package.json:9-11`
  - `tests/test_api_contract.py:9-10`
  - `tests/test_api_contract.py:85-88`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_process_runner.py`
- 반대 근거 검토:
  - backend-adjacent 단위 테스트는 일부 존재한다.
  - 특히 quality endpoint와 process runner 단위 테스트는 있다.
- 왜 오탐이 아닌가:
  - 그러나 Electron main/preload/index.html/packaged path를 직접 덮는 테스트는 없다.
- 사용자 영향:
  - 프론트-브리지 drift가 실제 사용 전까지 숨을 수 있다.
- 테스트 미실행 사유:
  - 이번 턴에서는 실행형 회귀를 돌리지 않았다.

## 7. Observation

### O-FE-01. Splash fallback은 backend 준비 전에 main window를 열 수 있다

- 상태: `확인함`
- 근거:
  - `geuldobi-desktop/src/main.js:252-259`
  - `geuldobi-desktop/src/splash/splash.js`
  - `geuldobi-desktop/src/index.html:7237-7251`
- 판단:
  - degraded UX 설계로 보이며 즉시 수정 우선순위는 아니다.
  - 다만 packaged startup 문제를 체감상 더 흐리게 만들 수 있다.

## 8. 재감리 후 최종 판정

이번 문서 작성 중 추가 재감리로 바뀐 핵심은 두 가지다.

1. 이전 system-wide 문서의 `Electron packaging non-finding`은 유지되지 않는다.
- 이유:
  - 그 감사는 `package.json`과 `main.js`의 symbolic contract만 봤다.
  - 이번 감사는 `backend_entry.py`, `bridge_server.py`, 실제 `dist/engine` 부재까지 포함해 operational contract를 다시 봤다.

2. 2026-03-09 UI 감사의 `project config surface 미연결` 추정은 현재 코드 기준으로 폐기한다.
- 이유:
  - 현재는 Electron main이 프로젝트 config surface를 실제 파일로 쓰고, 엔진이 그 파일을 실제로 읽는다.

## 9. 확신도 Ledger

현재 확신도: `95%`

가산:

- `70`: 조사 버킷 전수 인벤토리 완료
- `+10`: Electron main / bridge_server / process_runner / main_a / build 스크립트의 핵심 계약을 소스 기준으로 교차 고정
- `+5`: 읽기 전용 테스트 계층 확인
- `+5`: 파일시스템 계층에서 `dist/engine` 부재 직접 확인
- `+5`: 이전 문서의 stale claim 재판정 및 오탐 제거
- `+5`: packaged path split을 `main.js + backend_entry.py + bridge_server.py` 삼중 근거로 닫음

차감:

- `-5`: 실제 packaged Electron 실행과 electron-builder 재현은 아직 하지 않음

판정:

- `95%`는 이번 정적 감사 범위에서 방어 가능한 상한이다.
- 더 올리려면 packaged desktop 수동 실행 또는 빌드 재현이 필요하다.

## 10. 잔여 불확실성

| 항목 | 상태 | 이번 감사에서 못 닫은 이유 |
|---|---|---|
| electron-builder가 `dist/engine` 부재 시 hard fail인지, 아니면 빈 번들로 진행하는지 | runtime-only | 실제 build 미실행 |
| packaged desktop에서 quality dashboard가 실제로 어떤 오동작 UX를 보이는지 | runtime-only | packaged app 미실행 |
| CLI prompt wording 변화가 Mode B dialog 흐름에 얼마나 민감한지 | runtime-only | 실제 대화형 세션 미실행 |

## 11. 다음 액션 우선순위

canary success를 전제로 하면 프론트엔드 쪽 다음 우선순위는 아래 순서가 맞다.

1. `packaged project root split` 정합성 해결
2. `release build chain`에 engine 산출물 경로/자동화 고정
3. `GUI → bridge → main_a` 숫자 ordinal 결합 축소 또는 명시적 contract 잠금
4. 최소한의 Electron/IPC/packaged smoke 회귀망 추가
5. 그 다음에야 렌더러 구조정리나 시각적 개편을 논하는 게 맞다

즉, 현재 프론트엔드 과제의 중심은 디자인 리프레시가 아니라 `desktop contract hardening`이다.

## 12. Evidence Index

| ID | subsystem | claim | evidence_type | file_ref | risk | confidence_delta | status |
|---|---|---|---|---|---|---|---|
| E-FE-001 | desktop main | packaged mode는 workspace와 engine exe env를 같이 전달한다 | code | `geuldobi-desktop/src/main.js:97-107` | medium | +2 | confirmed |
| E-FE-002 | packaged env | backend frozen entry는 `GEULDOBI_ENGINE_ROOT=resources/engine`를 주입한다 | code | `build/backend_entry.py:19-24` | high | +2 | confirmed |
| E-FE-003 | bridge path | bridge quality/read path는 `PROJECT_ROOT/projects`를 사용한다 | code | `modules/api/bridge_server.py:174-187` | high | +3 | confirmed |
| E-FE-004 | run path | runner subprocess cwd는 `GEULDOBI_WORKSPACE`다 | code | `modules/api/process_runner.py:182-199` | high | +2 | confirmed |
| E-FE-005 | desktop project list | packaged 프로젝트 목록은 workspace/projects를 본다 | code | `geuldobi-desktop/src/main.js:488-493`, `527-563` | high | +2 | confirmed |
| E-FE-006 | packaging | Electron package는 `dist/backend`와 `dist/engine` 둘 다 요구한다 | code | `geuldobi-desktop/package.json:39-48` | high | +2 | confirmed |
| E-FE-007 | release automation | 공식 build script는 backend만 빌드한다 | code | `build/build_release.ps1:47-80` | high | +2 | confirmed |
| E-FE-008 | filesystem | 현재 worktree에 `dist/engine`이 없다 | filesystem | `dist/` | high | +2 | confirmed |
| E-FE-009 | renderer run contract | renderer는 장르/프로젝트를 숫자 index로 직렬화한다 | code | `geuldobi-desktop/src/index.html:5437-5452` | medium | +2 | confirmed |
| E-FE-010 | runner stdin | runner는 index를 stdin sequence로 변환한다 | code | `modules/api/process_runner.py:576-624` | medium | +2 | confirmed |
| E-FE-011 | main_a contract | `main_a.py`는 숫자 기반 `_select_genre/_select_project` 흐름이다 | code | `main_a.py:2808-3037` | medium | +2 | confirmed |
| E-FE-012 | config surface | project config surface는 실제 파일로 저장된다 | code | `geuldobi-desktop/src/main.js:514-520`, `583-596` | low | +1 | confirmed |
| E-FE-013 | engine wiring | engine은 `author_directives.txt`와 `work_guard.yaml`을 실제로 읽는다 | code | `modules/core/project_manager.py:110-116`, `main_a.py:1052-1057` | low | +1 | confirmed |
| E-FE-014 | renderer fallback | quality dashboard missing key는 fallback merge가 흡수한다 | code | `geuldobi-desktop/src/index.html:3573-3652`, `4274-4311` | low | +1 | confirmed |
| E-FE-015 | API assurance | `/run` 계약 테스트는 RouterStub 오프라인 검증이다 | test | `tests/test_api_contract.py:9-10`, `85-88` | medium | +1 | confirmed |
| E-FE-016 | quality assurance | quality endpoint 실제 함수 테스트는 존재한다 | test | `tests/test_bridge_quality_summary.py:9-40` | low | +1 | confirmed |
| E-FE-017 | package test gap | Electron package test는 설정돼 있지 않다 | code | `geuldobi-desktop/package.json:9-11` | medium | +1 | confirmed |
| E-FE-018 | splash | splash fallback-timeout은 degraded open을 허용한다 | code | `geuldobi-desktop/src/main.js:252-259`, `geuldobi-desktop/src/splash/splash.js` | low | +1 | confirmed |

## 13. 커버리지 표

| 버킷 | 커버 여부 | 조사 결과 |
|---|---|---|
| Electron startup/window/splash | 완료 | `main.js`, `splash.js` 확인 |
| IPC/preload/renderer wiring | 완료 | `preload.js`, `index.html` 확인 |
| bridge_server/process_runner/main_a 계약 | 완료 | `bridge_server.py`, `process_runner.py`, `main_a.py` 확인 |
| packaged mode workspace/project root | 완료 | `main.js`, `backend_entry.py`, `bridge_server.py` 교차 확인 |
| packaging/release build | 완료 | `package.json`, `build_release.ps1`, `dist/` 확인 |
| 테스트/문서 동기화 | 완료 | 관련 테스트와 이전 감사 문서 재판정 |

최종 판정:

- 범위 누락 없음
- retained finding은 `프론트 디자인`보다 `desktop contract`에 집중됨
- canary가 성공해도 이 문서의 `P1` 두 건은 별도로 닫아야 한다
