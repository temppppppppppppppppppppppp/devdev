# GMR-H Test Envelope & Release Reality Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- `tests/`는 317개 파일 규모로 backend, stage contract, desktop bridge를 폭넓게 커버한다.
- `geuldobi-desktop/package.json`의 `test` 스크립트는 curated subset만 실행한다.
- `build/build_release.ps1`는 backend.exe를 빌드하지만 engine은 source tree를 `dist/engine`으로 stage한다.

## PASS 2 교차 검증

- `geuldobi-desktop/src/main.js` packaged mode는 `GEULDOBI_ENGINE_EXE=resources/engine/engine.exe`를 주입한다.
- `build/backend_entry.py`는 frozen backend가 `GEULDOBI_ENGINE_ROOT=resources/engine`과 `GEULDOBI_PYTHON_PATH=resources/python-embed/python.exe`를 사용하게 한다.
- `modules/api/process_runner.py`는 `engine.exe`가 없으면 `python -u main_a.py` fallback으로 실행한다.
- 반면 `geuldobi-desktop/DESKTOP-GUIDE.md`는 `engine.exe` 중심 제품 설명을 유지한다.

## PASS 3 최종 findings

### [GMR-H-001] desktop package test script는 curated subset이며 전체 live contract를 대표하지 않는다

- Severity: `P2`
- Evidence:
  - `geuldobi-desktop/package.json`
  - `tests/test_desktop_contract_refresh.py`
  - `tests/test_main_a_stage_entry_contracts.py`
  - `tests/test_bridge_server_desktop_risk_gate.py`
- Why macro risk:
  - desktop package test는 smoke/contract subset로 유용하지만, 전체 backend/stage/runtime drift를 닫는 full envelope는 아니다.
  - 문서에서 이 스크립트를 “desktop 전체 회귀”로 과대 해석하면 안 된다.

### [GMR-H-002] 현재 릴리스 현실은 `engine.exe` 제품이 아니라 source-bundle fallback에 더 가깝다

- Severity: `P1`
- Evidence:
  - `build/build_release.ps1`
  - `build/backend_entry.py`
  - `modules/api/process_runner.py`
  - `geuldobi-desktop/DESKTOP-GUIDE.md`
- Why macro risk:
  - build 스크립트는 engine binary를 생성하지 않고 `dist/engine`에 source tree를 stage한다.
  - packaged runtime은 `engine.exe`를 먼저 찾지만, 없으면 embedded Python으로 `main_a.py`를 실행하는 fallback path가 실제 제품 경로가 된다.
  - 문서 설명과 shipping reality가 분리돼 있다.
- Recommended next order:
  - release guide를 “current shipping path” 기준으로 다시 동결하는 문서 오더 필요.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
