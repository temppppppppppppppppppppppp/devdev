# FBX-T2 Preload / Electron IPC Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 범위: `geuldobi-desktop/src/preload.js`, `geuldobi-desktop/src/main.js`
> 방법: `surface matrix + renderer consumer cross-check + 3PASS`

## 결론

- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 1건
- retained `P3`: 1건
- 핵심 결론: live IPC 매핑은 대체로 맞지만, main-process transport normalizer가 documented API code space 밖의 에러 코드를 만든다.

## PASS 1

- preload는 splash, run/stop/status, quality, prompt resolve, settings, materials, projects, work_guard template, workspace surface를 전부 노출한다.
- main process는 `ipcMain.handle` / `ipcMain.on`로 대응 surface를 갖고 있다.
- `bridgeFetch()`는 HTTP 오류를 `HTTP_${status}`로, transport 오류를 `NETWORK_ERROR`로 바꿔 renderer에 반환한다.
- work_guard template 관련 IPC는 `src/main.js`에만 있고 active renderer도 `src/preload.js`를 통해 이를 소비한다.

## PASS 2

- renderer consumer와 preload surface는 1:1로 대부분 맞는다.
- `tests/test_desktop_work_guard_template_contract.py`는 work_guard template surface와 approval forwarding을 고정한다.
- `tests/test_desktop_contract_refresh.py`는 package test script와 일부 contract surface만 고정한다.
- `getStatus()`와 `getWorkspacePath()`는 preload/main에 존재하지만 active renderer 소비는 찾지 못했다.

## PASS 3

### [FBX-T2-001] Electron main returns transport error codes outside the documented API contract

- **Severity**: `P2`
- **현상**: backend API contract는 `INVALID_KEY`, `RUN_ALREADY_ACTIVE` 같은 enumerated code를 정의하지만, Electron main의 `bridgeFetch()`는 `HTTP_403`, `HTTP_500`, `NETWORK_ERROR`를 별도로 만든다.
- **코드 근거**:
  - `geuldobi-desktop/src/main.js:376-391`
  - `docs/implementation/api-contract-v1.yaml:319-339`
- **사용자/운영 영향**: renderer는 backend contract 외의 code namespace를 실제로 받는다. API contract만 믿고 UI/운영문서를 작성하면 transport failure를 문서 바깥 값으로 맞게 된다.
- **테스트 근거**:
  - `tests/test_api_contract.py`는 backend contract enum을 고정한다.
  - main-process `bridgeFetch()`의 `HTTP_*` / `NETWORK_ERROR` 반환은 전용 회귀가 없다.
- **중복 여부**: `none`
- **권장 후속 조치**: 다음 remediation에서는 main-process transport envelope을 별도 desktop contract로 분리하거나 API contract에 desktop bridge layer를 명시한다.

### [FBX-T2-002] Preload exposes dead-candidate IPC surfaces with no active renderer consumers

- **Severity**: `P3`
- **현상**: `getStatus()`와 `getWorkspacePath()`는 preload/main에 남아 있지만 active renderer 소비가 없다.
- **코드 근거**:
  - `geuldobi-desktop/src/preload.js:13`, `geuldobi-desktop/src/preload.js:53`
  - `geuldobi-desktop/src/main.js:409-410`, `geuldobi-desktop/src/main.js:803-805`
  - `rg -n "getStatus\\(|getWorkspacePath\\(" geuldobi-desktop/src/index.html geuldobi-desktop/src/splash/splash.js` 결과 consumer 없음
- **사용자/운영 영향**: live surface와 dead surface를 구분하지 않으면 IPC drift 면적이 커진다.
- **테스트 근거**: 전용 consumer regression 없음
- **중복 여부**: `none`
- **권장 후속 조치**: 이후 문서/리팩터 단계에서 `live`와 `dead-candidate` IPC 목록을 분리한다.

## Retained Open Set

- `P2`: `FBX-T2-001`
- `P3`: `FBX-T2-002`

## Resume Packet

- `Current phase`: `FBX-T2 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `preload/main ipc matrix`
- `Next surface`: `FBX-T3 bridge/api contract`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
