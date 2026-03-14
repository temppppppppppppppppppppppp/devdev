# FBX-T5 Build / Package / Stale Drift Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 범위: `geuldobi-desktop/package.json`, `build/build_release.ps1`, `build/backend_entry.py`, `geuldobi-desktop/main.js`, `geuldobi-desktop/src/main.js`
> 방법: `build contract cross-check + stale copy classification + 3PASS`

## 결론

- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 2건
- 핵심 결론: packaged runtime은 실제로 fallback path를 기준으로 살아 있고, root-level `geuldobi-desktop/main.js`는 active entry가 아닌 stale duplicate다.

## PASS 1

- `package.json` active Electron entry는 `src/main.js`다.
- `src/main.js`는 packaged mode에서 `GEULDOBI_ENGINE_EXE=resources/engine/engine.exe`를 주입한다.
- `build_release.ps1`는 `backend.exe`만 빌드하고, engine 쪽은 `Sync-EngineBundle`로 source tree를 `dist/engine`에 복사한다.
- `backend_entry.py`는 frozen backend가 `GEULDOBI_PYTHON_PATH`와 `GEULDOBI_ENGINE_ROOT`를 설정한다.
- 현재 worktree 기준 `engine.exe` build artifact는 `build/`, `dist/`, `geuldobi-desktop/dist/` 어디에도 없다.
- `geuldobi-desktop/main.js`와 `geuldobi-desktop/src/main.js`의 SHA256은 서로 다르다.

## PASS 2

- `tests/test_process_runner.py:257-268`은 missing `engine.exe` fallback을 명시적으로 검증한다.
- `geuldobi-desktop/DESKTOP-GUIDE.md`는 packaged runtime이 `engine.exe`를 사용한다고 반복해서 서술한다.
- root `geuldobi-desktop/main.js`는 active runtime entry가 아니며, work_guard template IPC handler도 없다.
- `src/main.js`만이 work_guard template IPC와 approval forwarding을 가진다.

## PASS 3

### [FBX-T5-001] Packaged runtime advertises `engine.exe`, but the build stages a source-tree engine bundle and relies on fallback

- **Severity**: `P2`
- **현상**: Electron packaged env와 desktop guide는 `resources/engine/engine.exe`를 primary로 설명하지만, build script는 `engine.exe`를 생성하지 않고 source-tree engine bundle만 stage한다. 실제 실행은 `ProcessRunner` fallback이 떠받친다.
- **코드 근거**:
  - `geuldobi-desktop/src/main.js:167`
  - `modules/api/process_runner.py:191-196`, `modules/api/process_runner.py:203`
  - `build/build_release.ps1:27`, `build/build_release.ps1:112-117`
  - `build/backend_entry.py:19-25`
  - `geuldobi-desktop/DESKTOP-GUIDE.md:17`, `geuldobi-desktop/DESKTOP-GUIDE.md:24-25`
- **사용자/운영 영향**: packaged runtime 설명과 실제 artifact 구성이 어긋나 있어, 배포 진단과 운영 문서가 `engine.exe`를 기준으로 오판할 수 있다.
- **테스트 근거**:
  - `tests/test_process_runner.py:257-268`은 fallback만 고정한다.
  - build artifact parity를 직접 잠그는 테스트는 없다.
- **중복 여부**: `none`
- **권장 후속 조치**: 다음 remediation에서는 `engine.exe`를 실제 build artifact로 만들거나, 문서와 env 명칭을 source-tree fallback 현실에 맞게 정렬한다.

### [FBX-T5-002] Root-level `geuldobi-desktop/main.js` is a stale but high-risk drift source

- **Severity**: `P2`
- **현상**: package entry는 `src/main.js`인데, root `geuldobi-desktop/main.js`가 별도로 남아 있고 해시도 다르다. 최신 work_guard template IPC는 `src/main.js`에만 존재한다.
- **코드 근거**:
  - `geuldobi-desktop/package.json:5`
  - `SHA256 geuldobi-desktop/main.js = AA3F...9CA1`
  - `SHA256 geuldobi-desktop/src/main.js = 4875...788F`
  - `rg -n "project:list-work-guard-templates|project:apply-work-guard-template|getWorkGuardLibraryDir|resolveWorkGuardTemplatePath" geuldobi-desktop/main.js geuldobi-desktop/src/main.js`
- **사용자/운영 영향**: active가 아닌 파일을 수정 대상으로 착각하면 desktop main drift를 재주입할 수 있다.
- **테스트 근거**:
  - `tests/test_desktop_work_guard_template_contract.py`는 `src/main.js`만 본다.
  - stale root copy를 guard하는 전용 회귀는 없다.
- **중복 여부**: `none`
- **권장 후속 조치**: 이후 정리 단계에서 root copy를 `dead/stale`로 공식 분류하거나 제거 대상 후보로 따로 관리한다.

## Retained Open Set

- `P2`: `FBX-T5-001`, `FBX-T5-002`

## Resume Packet

- `Current phase`: `FBX-T5 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `build/package/runtime artifact parity`
- `Next surface`: `FBX-T6 regression/docs/confidence`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
