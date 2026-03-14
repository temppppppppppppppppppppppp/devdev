# FGS-T2 Project Settings Material Findings

> 작성일: 2026-03-13
> 상태: `PASS3 complete`
> 범위: 프로젝트 선택/생성, 설정 surface, work_guard template, material panel, workspace path

## 조사 범위

- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/main.js`
- `modules/core/runtime_paths.py`
- `modules/core/project_manager.py`
- `modules/core/project_support.py`

## PASS 1 사실 수집

- preload는 `listProjects`, `createProject`, `loadProjectConfigSurfaces`, `saveConfigSurfaces`, `listWorkGuardTemplates`, `applyWorkGuardTemplate`, `openWorkspaceFolder`, `getWorkspacePath`, material file APIs를 노출한다.
- Electron main은 packaged 모드에서 `getWorkspaceDir()/projects`와 `getWorkspaceDir()/work_guards`를 기준으로 프로젝트/템플릿 surface를 제공한다.
- renderer 설정 탭은 `author_directives.txt`, `work_guard.yaml`, helper-based work_guard fields, 템플릿 selector를 함께 제공한다.
- material panel은 Bible/Treatment 파일의 list/import/delete surface를 가진다.

## PASS 2 교차 검증

- `tests/test_desktop_work_guard_template_contract.py`, `tests/test_runtime_paths.py`, `tests/test_project_support.py`, `tests/test_project_manager_hud_helpers.py`를 읽었고, 표적 pytest 실행에서도 모두 통과했다.
- `runtime_paths.py`는 `GEULDOBI_PROJECTS_ROOT`를 최우선으로 해석하고, 없을 때만 `GEULDOBI_WORKSPACE/projects`로 fallback한다.
- `ProjectManager`와 `main_a.py`는 `author_directives.txt`, `work_guard.yaml`을 실제 runtime path에서 소비한다.

## PASS 3 오탐 제거

- `FGS-T2-H1`: 프로젝트 설정 surface가 engine과 분리됨
  - 판정: `rejected`
  - 이유: 저장 경로와 runtime 소비 경로가 현재는 직접 연결돼 있다.
- `FGS-T2-H2`: work_guard template 브리지가 미구현
  - 판정: `rejected`
  - 이유: preload, main process, renderer, 회귀 테스트가 모두 존재한다.

## 확정 findings

- 없음

## 기각 findings

- project settings surface disconnected from runtime
- work_guard template bridge missing

## coverage gap / open question

- `material:list-files`, `material:import-file`, `material:delete-file`, `workspace:open-folder`, `workspace:get-path`는 live surface가 존재하지만 관련 자동 테스트는 확인되지 않았다.
- material 파일 작업과 workspace open 동작은 이후 `T6`에서 coverage gap으로 별도 유지한다.

## PASS 요약

- PASS1 후보 2건
- PASS2 제거 2건
- 최종 0건
