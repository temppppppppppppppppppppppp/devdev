# UI Frontier Lag Integration 실행 SSOT

작성일: 2026-03-13  
대상 코드: `geuldobi-desktop/src/index.html`, `geuldobi-desktop/src/preload.js`, `modules/api/process_runner.py`, `main_a.py`  
선행 문서:
- `docs/2026-03-13/one-stop-frontier-lag-execution-ssot.md`
- `docs/2026-03-13/one-stop-frontier-lag-3pass-audit.md`
- `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`

문서 상태: `execution ssot`

## Summary

- 이번 범위는 `UI 연결`까지만 한다.
- `빌드`와 `버전 업`은 이번 오더 범위에서 제외한다.
- 목표는 데스크톱 UI에서 새 `7번 Frontier Lag` 모드를 사용자가 명시적으로 선택하고, 기존 브리지/프로세스 경로로 안전하게 실행할 수 있게 만드는 것이다.
- 기존 `6번 One-Stop`은 유지한다.

## Baseline Facts

### 1. backend / engine 쪽은 이미 준비됨

- 메인 메뉴에 새 `7`이 추가되어 있다.
  - `main_a.py:2144`
- 디스패치도 연결돼 있다.
  - `main_a.py:2177`
- `Frontier Lag` helper와 wrapper도 이미 구현돼 있다.
  - `main_a.py:3469`
  - `main_a.py:3495`
  - `main_a.py:3531`

즉 이번 작업은 엔진 구현이 아니라 `desktop surface wiring` 문제다.

### 2. 현재 desktop UI는 `key 6`만 노출

- 실행 패널에 `One-Stop key 6` 버튼만 있다.
  - `geuldobi-desktop/src/index.html:2776`
- 현재 label은 `One-Stop`, meta는 `key 6`이다.
  - `geuldobi-desktop/src/index.html:2777`

### 3. renderer → preload → bridge → process runner 경로는 이미 범용 key 기반

- renderer는 `runKey(key, subKey, inputs)`로 key를 그대로 넘긴다.
  - `geuldobi-desktop/src/index.html:6528`
- preload는 그 payload를 IPC로 그대로 전달한다.
  - `geuldobi-desktop/src/preload.js:10-12`
- process runner도 key를 일반 문자열로 main menu stdin에 그대로 넣는다.
  - `modules/api/process_runner.py:581-597`

따라서 `7` 지원 자체를 위해 bridge/proxy 구조를 뜯을 필요는 없다.

### 4. UI 메타와 stage surface는 현재 `one_stop` 단일 action에 맞춰져 있음

- `ACTION_META.one_stop`만 존재한다.
  - `geuldobi-desktop/src/index.html:3561`
- pipeline strip도 `one_stop`까지만 잡혀 있다.
  - `geuldobi-desktop/src/index.html:3578`
- office state 주석도 `one_stop`만 반영한다.
  - `geuldobi-desktop/src/index.html:3475`

즉 `버튼 하나 추가`만으로 끝나지 않고, `desktop semantics`도 같이 정리해야 한다.

## Goal

사용자가 UI에서 다음 둘을 구분해 실행할 수 있어야 한다.

- `One-Stop (key 6)` = 기존 full-close arc-by-arc
- `Frontier Lag (key 7)` = `Stage 3 = frontier-1`, `Stage 4 = frontier-2`

그리고 이 차이가 다음 surface에 일관되게 반영되어야 한다.

- 실행 패널 버튼
- 현재 단계 title / summary
- pipeline strip
- office 상태 로그
- manager bubble / request log

## Scope

### In Scope

- `index.html` 실행 패널에 `Frontier Lag key 7` 버튼 추가
- renderer action key 신설
- `ACTION_META`에 새 설명 추가
- `PIPELINE_ORDER`와 `currentStage` 관련 표면에 새 action 반영
- 필요 시 `stageHint` / stdout parsing / animation set 등 UI 상태 표면 보강
- `runKey(7, ...)` 실행 smoke 및 desktop-focused regression 추가

### Out of Scope

- build 실행
- `package.json` 버전 변경
- installer 생성
- `main_a.py`의 `Frontier Lag` 동작 변경
- Stage 3/4 engine 수정
- 새 backend API 추가

## Design Decision

### D-1. action id는 `one_stop_frontier_lag`로 분리한다

권장 action id:

- 기존: `one_stop`
- 신규: `one_stop_frontier_lag`

이유:

- UI 설명과 pipeline strip에서 두 모드를 분리할 수 있다.
- `6`과 `7`이 같은 `one_stop` action을 공유하면 실행 전후 로그와 상태칩에서 구분이 사라진다.
- 이미 backend는 key 기반으로 충분히 분기 가능하므로, renderer action만 분리하는 편이 더 명확하다.

### D-2. bridge / preload / process runner는 구조 변경 없이 유지한다

이유:

- 현재 경로는 `key`를 그대로 전달한다.
- 새 mode `7`은 `main_a.py`가 이미 처리한다.
- 따라서 desktop 쪽 구현 포인트는 `UI semantics`, `state labeling`, `test coverage`다.

### D-3. pipeline strip에는 별도 surface를 둔다

권장:

- `PIPELINE_ORDER = ["stage_0", "stage_2", "stage_3", "stage_4", "one_stop", "one_stop_frontier_lag"]`

또는 최소한 `Frontier Lag`를 `one_stop`와 별도 short/title로 그린다.

이유:

- 둘은 목적과 runtime shape가 다르다.
- `FULL RUN`과 `FRONTIER LAG`를 같은 칩으로 처리하면 사용자가 현재 어떤 정책으로 돌리는지 알기 어렵다.

## Required Changes

### E-1. Run panel button 추가

대상:

- `geuldobi-desktop/src/index.html:2766-2779`

변경:

- 기존 `One-Stop key 6` 아래 또는 옆에
  - `data-action="one_stop_frontier_lag"`
  - `data-key="7"`
  - label 예시: `Frontier Lag`
  - meta 예시: `key 7`

### E-2. ACTION_META 추가

대상:

- `geuldobi-desktop/src/index.html:3556-3567`

추가 예시:

- `one_stop_frontier_lag: { title: "Frontier Lag", summary: "Arc frontier는 전진시키고 Stage 3/4는 한 박자 늦춰 실행", short: "FRONTIER" }`

### E-3. office / pipeline state 반영

대상:

- `geuldobi-desktop/src/index.html:3475`
- `geuldobi-desktop/src/index.html:3578`
- `geuldobi-desktop/src/index.html:4996`

필수:

- `officeState.currentStage` 설명 주석에 새 action 추가
- `PIPELINE_ORDER`에 새 action 추가
- `ANIMATED_STAGES`에 새 action 추가 여부 결정

권장:

- `one_stop_frontier_lag`도 animation을 허용한다.
- 이유: 실행 체감은 one-stop 계열이므로 visual rhythm을 공유하는 편이 자연스럽다.

### E-4. stdout stage hint / bubble labeling 보강

대상:

- `geuldobi-desktop/src/index.html:6219-6224`

권장:

- stdout만으로는 `one_stop` vs `frontier_lag`를 판정하지 않는다.
- 실행 시작 시 이미 `officeState.currentStage = action`으로 잠기므로, stdout regex는 현행 유지해도 된다.
- 단, `FrontierLag` 로그가 추가로 보이는 만큼 manager bubble에 `Frontier Lag` wording이 유지되게 action meta를 분리한다.

### E-5. tests / smoke 추가

최소 요구:

- `index.html` inline script syntax 확인
- renderer 실행 button이 `runKey("7", ...)`를 호출하는 smoke
- `ACTION_META.one_stop_frontier_lag` 누락 방지 test 또는 equivalent lint/smoke

가능하면:

- desktop-side run mode smoke를 별도 테스트에 추가
- 기존 `key 6` regression 유지

## Acceptance Criteria

다음이 모두 만족되어야 한다.

1. 실행 패널에서 `One-Stop key 6`과 `Frontier Lag key 7`이 동시에 보인다.
2. `Frontier Lag` 클릭 시 renderer가 `runKey("7", ...)`를 호출한다.
3. current stage title/summary가 `One-Stop`이 아니라 `Frontier Lag`로 유지된다.
4. pipeline strip과 office UI가 기존 `one_stop`와 구분 가능한 상태를 보여준다.
5. 기존 `key 6` 동작과 표시는 회귀하지 않는다.

## Risks

### R-1. UI action 분리 없이 key만 7로 추가하는 경우

- 실행은 될 수 있다.
- 하지만 상태 패널, 로그, bubble, pipeline strip이 전부 `One-Stop`으로만 보일 수 있다.
- 이 경우 기능은 되지만 UX는 잘못된다.

### R-2. PIPELINE_ORDER 미반영

- 현재 단계는 바뀌는데 상단 strip이 기대와 다르게 보일 수 있다.
- 특히 `Frontier Lag`가 `IDLE`처럼 보이거나 마지막 칩에 동기화되지 않을 수 있다.

### R-3. build 범위 오염

- 이번 오더에서 `1.9.0`까지 같이 잡으면 범위가 넓어진다.
- build와 버전업은 UI wiring이 닫힌 뒤 별도 오더로 가는 것이 맞다.

## Verification Plan

- `node --check` equivalent on extracted inline script 또는 기존 방식의 문법 확인
- frontend/dev spike 실행에서 버튼 렌더와 currentStage 표면 확인
- desktop bridge run smoke에서 `7` payload 확인
- 기존 `6` regression 확인

## Final Judgment

- 현재 구조상 `UI 연결만` 따로 떼어 처리하는 것이 맞다.
- backend/bridge 경로는 이미 준비되어 있으므로, 이번 오더는 `renderer semantics + desktop state surface`에 집중하면 된다.
- 본 문서는 `execution-ready`로 확정한다.
