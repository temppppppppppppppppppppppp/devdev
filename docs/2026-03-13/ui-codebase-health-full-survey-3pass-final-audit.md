# UI Codebase Health Full Survey 3Pass Final Audit

작성일: 2026-03-13  
대상 범위:
- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/splash/*`
- `geuldobi-desktop/package.json`
- desktop/bridge/UI 관련 테스트와 API contract 문서

금지 준수:
- 코드 직접 수정 없음
- 이번 턴에서는 문서화와 읽기/테스트/스파이크 실행만 수행

## Executive Summary

- 감리 결과: `retained finding 있음`
- 최종 확신도: `95%`
- 핵심 결론:
  - desktop shell 자체는 부팅된다.
  - 하지만 `UI 표면`과 `bridge/API contract` 사이에 실제 dead path가 1건 있다.
  - 또 renderer는 `unsafe-inline CSP + unsanitized innerHTML` 조합을 광범위하게 사용해, user/DB 문자열이 UI를 오염시킬 수 있다.
  - 그 외 큰 축은 `test/docs gate drift`와 `renderer monolith debt`다.

## Baseline Inventory

- renderer 메인 파일: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html) `7717` lines
- Electron main: [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js) `759` lines
- preload: [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js) `51` lines
- splash:
  - [splash.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/splash/splash.html)
  - [splash.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/splash/splash.js)
  - [splash.css](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/splash/splash.css)
- build config: [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)

검증 근거:
- `pytest -q tests/test_process_runner.py tests/test_bridge_quality_summary.py tests/test_frontend_frontier_lag_wiring.py tests/test_api_contract.py tests/test_run_validator.py`
  - 결과: `139 passed`
- `npm run start:spike`
  - 결과: splash → backend idle → main window 전환 성공, `/status` 및 `/quality/dashboard` `200 OK`

## Pass 1: 사실 수집

### desktop boot / bridge 구조

- Electron main은 `contextIsolation: true`, `nodeIntegration: false`로 열려 있다.
  - [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js):253
  - [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js):255
  - [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js):256
- preload는 `window.geuldobiDesktop`에 제한된 IPC surface를 노출한다.
  - [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js):3
  - [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js):10
- renderer는 `runKey(key, subKey, inputs)`로 key를 그대로 전달한다.
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):6534
- main process는 `/run`으로 key를 그대로 전달한다.
  - [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js):395
  - [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js):399

### 현재 UI surface

- 실행 패널에는 `One-Stop key 6`과 `Frontier Lag key 7`이 같이 노출된다.
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):2776
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):2779
- `ACTION_META`, `PIPELINE_ORDER`, `ANIMATED_STAGES`도 `one_stop_frontier_lag`를 안다.
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):3561
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):3562
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):3579
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4997

### contract / test gate 표면

- `/run` validator는 허용 key에 아직 `7`이 없다.
  - [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py):24
  - [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py):25
- API contract 문서도 아직 `7`을 모른다.
  - [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml):107
  - [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml):113
- prompt-map과 API contract test도 key를 `6`까지만 본다.
  - [prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json):101
  - [test_api_contract.py](C:/Users/User/Desktop/글도비/tests/test_api_contract.py):37
  - [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py):14
  - [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py):70

### renderer rendering 방식

- 메인 renderer CSP는 `unsafe-inline`을 허용한다.
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):6
- 동시에 renderer는 backend/DB/user 문자열을 `innerHTML`로 대량 렌더링한다.
  - safe ops: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):3969
  - artifact ladder: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4038
  - retrieval cards: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4089
  - quality radar: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4218
  - compare rows: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4330
  - operator observations: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4443
  - advisory candidates: [index.html](C:/Users\User\Desktop\글도비/geuldobi-desktop/src/index.html):4460
  - material file names: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):7524

## Pass 2: 교차 검증

### Finding 1: UI에 노출된 `key 7`이 실제 `/run`에서 막힌다

심각도: `P1`

근거:
- UI는 `Frontier Lag key 7`을 렌더링한다.
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):2779
- main/preload는 key를 generic하게 전달한다.
  - [preload.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/preload.js):10
  - [main.js](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/main.js):395
- 하지만 validator 허용 목록에는 `7`이 없다.
  - [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py):24
  - [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py):25
- 직접 read-only 검증에서도 `validate_run_request("7", None, "idle") -> INVALID_KEY`가 재현됐다.
- 관련 tests/doc도 모두 `7`을 invalid로 고정하고 있다.
  - [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py):14
  - [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml):113

판정:
- 이건 이론적 위험이 아니라 `현재 UI dead path`다.
- 사용자는 버튼을 누를 수 있지만 runtime은 곧바로 400으로 끝난다.

### Finding 2: `unsafe-inline` CSP 아래 unsanitized `innerHTML`이 광범위하다

심각도: `P1`

근거:
- 메인 renderer는 `script-src 'unsafe-inline'`을 허용한다.
  - [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):6
- 동시에 backend/DB/user 값이 escaping 없이 `innerHTML`에 주입된다.
  - `action.summary`, `action.notes`: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):3969
  - `item.detail`, `item.path`: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4038
  - retrieval warnings/recent rows: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4108, [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4128
  - `row.note`, `row.operator_label`, `item.reason`: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4443, [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):4460
  - material file names: [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html):7524
- escape helper는 확인되지 않았다.

판정:
- 이건 단순 미관 문제나 code style 문제가 아니다.
- renderer가 DB/log/user note/file name을 HTML로 해석할 수 있는 구조다.
- Electron에서 injected script/event handler가 실행되면 `window.geuldobiDesktop` API surface를 악용할 여지가 생긴다.

### Finding 3: desktop test/docs gate가 실제 UI surface를 못 지킨다

심각도: `P2`

근거:
- desktop package 자체의 test script는 여전히 `No tests configured`다.
  - [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json):6
  - [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json):11
- 실제 repo tests는 존재하지만 desktop workflow에 연결돼 있지 않다.
  - [test_frontend_frontier_lag_wiring.py](C:/Users/User/Desktop/글도비/tests/test_frontend_frontier_lag_wiring.py)
  - [test_process_runner.py](C:/Users/User/Desktop/글도비/tests/test_process_runner.py)
- 더 나쁜 점은 API contract/test가 stale 상태라, `key 7` dead path를 정상으로 인증하고 있었다.
  - [test_api_contract.py](C:/Users/User/Desktop/글도비/tests/test_api_contract.py):37
  - [test_run_validator.py](C:/Users/User/Desktop/글도비/tests/test_run_validator.py):14

판정:
- 지금 gate는 “테스트가 없다”보다 “틀린 계약을 통과시킨다”에 가깝다.
- 그래서 최근 UI wiring regression이 전체 suite green 상태에서도 새어 나왔다.

### Finding 4: renderer monolith가 blast radius를 키운다

심각도: `Observation`

근거:
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html) 한 파일에 markup/style/script가 `7717` lines로 몰려 있다.
- dashboard, office, settings, material manager, prompt dialog, websocket, safe ops, quality panels가 전부 한 파일에 결합돼 있다.

판정:
- 이건 지금 당장 runtime을 깨는 결함은 아니다.
- 다만 변경 blast radius와 audit 난도를 지속적으로 키운다.
- retained blocker라기보다 구조 debt observation으로 유지한다.

## Pass 3: 오탐 제거

다음 항목은 조사했지만 retained finding으로 올리지 않았다.

- `Electron main window boot failure`
  - 기각
  - `npm run start:spike`에서 splash, backend, main window, `/status`, `/quality/dashboard`가 정상 동작했다.
- `preload surface 과다 노출`
  - 기각
  - 노출 surface는 여전히 제한적이며 `contextIsolation: true`, `nodeIntegration: false` 조합을 유지한다.
- `packaging contract 자체 붕괴`
  - 기각
  - 이번 조사 목적은 UI health이고, dev spike 기준 packaged 이전 desktop shell은 동작한다.
  - 다만 build/test gate 결합도는 별도 P2로 남긴다.

## Re-Audit Loop

초기 후보에서 아래를 낮췄다.

- `7717줄 monolith 자체를 P1`로 보려던 판단
  - 과함
  - 실제 blocker는 아니다.
- `splash 종료 시 Bridge fetch failed`를 runtime defect로 볼지 여부
  - 기각
  - spike auto-close 직후 backend 종료 레이스에서 반복되는 종료성 로그로 해석하는 편이 맞다.

남긴 retained finding은 아래 3건뿐이다.
- `P1`: key 7 dead path
- `P1`: unsafe-inline + unsanitized innerHTML
- `P2`: stale desktop test/docs gate

## Verification Evidence

- `pytest -q tests/test_process_runner.py tests/test_bridge_quality_summary.py tests/test_frontend_frontier_lag_wiring.py tests/test_api_contract.py tests/test_run_validator.py`
  - 결과: `139 passed`
- `npm run start:spike`
  - splash 표시 성공
  - backend idle 감지 성공
  - main window 전환 성공
  - `/status` `200 OK`
  - `/quality/dashboard` `200 OK`
- direct validator probe:
  - `validate_run_request("6") -> OK`
  - `validate_run_request("7") -> INVALID_KEY`

## Confidence Ledger

- `70`: UI codebase 인벤토리 전수 확인
- `+10`: Electron main/preload/renderer/validator/API contract/test gate 교차 검증 완료
- `+10`: UI-related tests `139 passed`와 desktop spike 부팅 증거 확보
- `+5`: 오탐 제거 후 retained finding을 3건으로 압축
- `-0`: 남은 불확실성은 packaged runtime과 실제 악성 payload injection 실증뿐이며, 정적 근거로도 finding 유지가 충분
- 최종: `95`

## Final Judgment

- UI codebase는 `대체로 동작`하지만 `clean`은 아니다.
- 지금 시점의 최우선 retained risk는 `Frontier Lag key 7 dead path`다.
- 그다음은 `unsanitized innerHTML + unsafe-inline CSP` 조합이다.
- test/docs gate도 stale해서 같은 종류의 drift를 다시 허용할 수 있다.

이번 턴은 읽기 전용 조사, 테스트, spike 실행, 문서화만 수행했다. 코드 수정은 하지 않았다.
