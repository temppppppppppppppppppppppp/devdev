# FGS-T3 Shell IPC Splash Findings

> 작성일: 2026-03-13
> 상태: `PASS3 complete`
> 범위: Electron shell, preload IPC, splash lifecycle, shadow main, temp scripts

## 조사 범위

- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/splash/*`
- `geuldobi-desktop/main.js`
- `geuldobi-desktop/temp-electron-loadcheck.js`
- `geuldobi-desktop/temp-electron-paths.js`
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/dist/builder-debug.yml`

## PASS 1 사실 수집

- live Electron entry는 `package.json`의 `"main": "src/main.js"`다.
- `src/main.js`는 work_guard template IPC와 workspace/material/project bridge를 포함한다.
- root-level `geuldobi-desktop/main.js`도 존재하지만 `src/main.js`보다 짧고, work_guard template IPC가 빠져 있다.
- builder debug output의 file pattern은 `src/**/*`와 `package.json`만 포함한다.
- splash는 `/status` polling 후 `idle` 상태에서 main 화면으로 넘기는 구조다.

## PASS 2 교차 검증

- `geuldobi-desktop/main.js`와 `geuldobi-desktop/src/main.js`를 비교한 결과, root-level shadow copy에는 `getWorkGuardLibraryDir`, `project:list-work-guard-templates`, `project:apply-work-guard-template` 구간이 없다.
- package build 설정은 `src/**/*`만 shipping 대상으로 잡고 있어 root-level `main.js`와 temp script는 실제 패키지에 포함되지 않는다.
- 따라서 즉시 런타임 버그는 아니지만, 로컬 탐색/수동 수정/문서 해석 시 shadow copy를 잘못 열 가능성이 남아 있다.

## PASS 3 오탐 제거

- `FGS-T3-H1`: temp Electron script가 배포 산출물에 섞여 있음
  - 판정: `rejected`
  - 이유: `builder-debug.yml` 기준 shipping pattern 바깥이다.
- `FGS-T3-H2`: root-level `main.js`가 실제 entrypoint다
  - 판정: `rejected`
  - 이유: package main은 `src/main.js`를 가리킨다.

## 확정 findings

### FGS-T3-001

- Severity: `P3`
- 현상 요약: `geuldobi-desktop/main.js` shadow copy가 live entry인 `src/main.js`와 이미 드리프트했다.
- 코드 근거:
  - `geuldobi-desktop/package.json:5`는 main을 `src/main.js`로 고정한다.
  - `geuldobi-desktop/src/main.js:619`, `:761`, `:774`에는 work_guard template IPC가 있다.
  - 같은 심볼은 `geuldobi-desktop/main.js`에 없다.
- 보조 근거:
  - `git diff --no-index geuldobi-desktop/main.js geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/dist/builder-debug.yml`의 shipping pattern은 `src/**/*`만 포함한다.
- counter-evidence review:
  - 실제 패키지에는 root-level `main.js`가 포함되지 않으므로 즉시 제품 결함은 아니다.
  - 다만 maintenance surface로는 이미 split-brain이다.
- 상태: `confirmed`
- 권장 후속 조치:
  - shadow copy 제거 또는 live entry로 redirect
  - future docs/edit guidance에서 root-level `main.js`를 명시적으로 비활성 파일로 표시

## 기각 findings

- temp Electron script shipping bug
- shadow main live-entry hypothesis

## coverage gap / open question

- splash polling, fallback timer, window handoff는 자동화 테스트가 확인되지 않아 `needs-live-check`로 남는다.

## PASS 요약

- PASS1 후보 3건
- PASS2 제거 2건
- 최종 1건
