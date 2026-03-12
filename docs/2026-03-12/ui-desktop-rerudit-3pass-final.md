# UI Desktop Rerudit 3-Pass Final

작성일: 2026-03-12  
범위: packaged desktop build chain, packaged backend route proof, packaged smoke  
최종 확신도: `95%`

## Executive Summary

이번 재감리는 `frontend-desktop-bridge-full-survey-3pass-final-audit.md`의 retained desktop/build 항목을 현재 코드와 실제 빌드 산출물 기준으로 다시 닫는 작업이다.

결론은 아래와 같다.

1. `backend`, `engine`, `python-embed` 리소스는 packaged bundle에 모두 포함되었다.
2. packaged backend를 실제 bundled `backend.exe`로 기동했을 때 `status`, `quality/summary`, `quality/dashboard`, `safe-ops/preview`가 모두 `200 OK`로 응답했다.
3. 직접 `Geuldobi.exe`를 띄우는 headless smoke는 이 비대화형 세션에서 1초 내 종료되어 창 상호작용 증명까지는 못 갔다.
4. 따라서 open `P0/P1/P2 = 0`, 잔여 항목은 `Observation 1건`으로만 남긴다.

## Pass 1. Static Build Contract

확인한 packaged 산출물:

- `geuldobi-desktop/dist/win-unpacked/resources/backend/backend.exe`
- `geuldobi-desktop/dist/win-unpacked/resources/engine/main_a.py`
- `geuldobi-desktop/dist/win-unpacked/resources/python-embed/python.exe`

확인한 build 산출물:

- unpacked app: `geuldobi-desktop/dist/win-unpacked/Geuldobi.exe`
- installer: `geuldobi-desktop/dist/Geuldobi Setup 1.0.0.exe`

## Pass 2. Runtime Proof

### 2.1 Packaged backend smoke

bundled backend를 아래 조건으로 직접 기동했다.

- executable: `geuldobi-desktop/dist/win-unpacked/resources/backend/backend.exe`
- workspace: `C:\Users\User\Documents\geuldobi_smoke`
- projects root: `C:\Users\User\Documents\geuldobi_smoke\projects`
- sample project: `00_test_07`

확인 결과:

- `GET /status` -> `200 OK`
- `GET /quality/summary?project=00_test_07&lookback=5` -> `200 OK`
- `GET /quality/dashboard?project=00_test_07&lookback=5` -> `200 OK`
- `GET /safe-ops/preview?project=00_test_07` -> `200 OK`

이로써 packaged backend가 `GEULDOBI_WORKSPACE / GEULDOBI_PROJECTS_ROOT` 기준 project root를 정상 해석하고, quality/safe-ops surface를 실제 데이터와 연결한다는 점을 확인했다.

### 2.2 Builder output

- `npm run build:dir` 성공
- `npm run build` 성공
- installer 최종 산출물:
  - `Geuldobi Setup 1.0.0.exe`
  - size: `223,196,664 bytes`
  - built at: `2026-03-12 17:43:48`

## Pass 3. False Positive Removal

기각/하향:

- `project root split` P1
  - 현재 packaged backend smoke에서 `00_test_07` quality/safe-ops payload를 실제로 불러왔으므로 blocker로 유지하지 않는다.
- `dist/engine build chain 부재` P1
  - `resources/engine/main_a.py`까지 실제 bundle에서 확인했으므로 blocker로 유지하지 않는다.

유지:

- `Observation`: direct `Geuldobi.exe` headless smoke는 비대화형 세션에서 1초 내 종료됐다.
  - 이 환경에서는 창 생성/표시/IPC 상호작용까지 직접 증명하지 못했다.
  - 다만 packaged backend, build output, renderer/main/preload 정적 회귀는 모두 확보돼 있어 blocker로 승격하지 않는다.

## Final Verdict

- `P0 = 0`
- `P1 = 0`
- `P2 = 0`
- `Observation = 1`

현재 desktop/build 축은 release blocker 관점에서 닫혔다.  
남은 것은 headless 세션 한계로 인한 `direct GUI interaction observation`뿐이다.

