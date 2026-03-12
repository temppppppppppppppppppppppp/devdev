# Frontend Backend Connection Check Pass3
> 상태: 3차 동적 경로 검증 완료
> 인코딩: UTF-8
> 일시: `2026-03-10 17:23:09 +09:00`
> 범위: `Project / Workspace / Material IPC`

## 목적

이전 1차/2차 체크에서 미실행으로 남겨 둔 `Project`, `Workspace`, `Material` 관련 프론트-메인-파일시스템 경로를 실제 호출 기준으로 검증한다.

## 검증 방식

1. `geuldobi-desktop/src/main.js`의 `ipcMain.handle(...)` 경로를 stubbed packaged runtime으로 실제 호출
2. `geuldobi-desktop/src/preload.js`의 `window.geuldobiDesktop` 노출 채널이 올바른 IPC 채널로 연결되는지 확인
3. 파일 import/delete는 임시 작업 디렉터리와 샘플 파일을 사용해 실제 복사/삭제까지 확인

## 결과

- `project:list`: `PASS`
  - 빈 상태에서 `projects` 디렉터리 생성 및 빈 목록 반환 확인
- `project:create`: `PASS`
  - `UI Audit Project` 생성 성공
  - 동일 이름 재생성 시 `"이미 존재하는 프로젝트입니다"` 반환 확인
- `workspace:get-path`: `PASS`
  - packaged 기준 작업 폴더 경로 반환 확인
- `workspace:open-folder`: `PASS`
  - 동일 경로가 `shell.openPath()`로 전달되는 것까지 확인
- `material:list-files`: `PASS`
  - `bible`, `treatments` 폴더에 대해 빈 목록과 import 후 목록 반환 모두 확인
- `material:import-file`: `PASS`
  - dialog 결과로 주입한 샘플 파일이 각 대상 폴더로 실제 복사됨
  - 검증 파일
    - `sample_bible.txt`
    - `sample_treatment.json`
- `material:delete-file`: `PASS`
  - 정상 파일 삭제 확인
  - `..\\hack.txt` 경로 탈출 시도는 `"invalid filename"`으로 차단 확인

## Preload 검증

`window.geuldobiDesktop` 노출명과 invoke 채널 모두 확인했다.

- 노출명: `geuldobiDesktop`
- 확인 채널
  - `project:list`
  - `project:create`
  - `material:list-files`
  - `material:import-file`
  - `material:delete-file`
  - `workspace:open-folder`
  - `workspace:get-path`

## 추가 보강

- renderer에서 재료 파일 import가 `cancel / failure`일 때도 로그가 남도록 `geuldobi-desktop/src/index.html` 경로를 보강했다.
- `refreshMaterialList()` 실패 시에도 로그를 남기도록 보강했다.

## 종합 판정

- 판정: `PASS`
- 확신도: `97%`

현재 기준으로 `Project / Workspace / Material`까지 포함한 프론트-메인-파일시스템 연결은 정상이다.
