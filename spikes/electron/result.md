# Spike 4 결과 보고서 (Electron 스플래시 스켈레톤)

- 일시: 2026-03-06
- 오더: `docs/2026-03-06/P0_스파이크_실행오더.md` §스파이크 4
- 디자인 참조: `docs/2026-03-05/codex-ui-webgal-light-proposal.md` §스플래시 스크린

## 산출물
- `geuldobi-desktop/` Electron 스켈레톤 프로젝트 생성
- 스플래시/메인/IPC/폴백 구현:
  - `geuldobi-desktop/src/main.js`
  - `geuldobi-desktop/src/preload.js`
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/splash/splash.html`
  - `geuldobi-desktop/src/splash/splash.css`
  - `geuldobi-desktop/src/splash/splash.js`
- 본 문서: `spikes/electron/result.md`

## 구현 체크
- [x] `geuldobi-desktop/` 디렉터리 생성 + `npm init` + Electron 설치
- [x] PenLine(lucide) 아이콘 + 로딩바 + "시작하는 중..." 스플래시 구성
- [x] `/status` (`http://127.0.0.1:8300/status`) 1초 폴링
- [x] `state == "idle"` 시 메인 윈도우 전환
- [x] 서버 미기동 시 3초 폴백 전환
- [x] `%LOCALAPPDATA%/Geuldobi/.first_run` 기반 첫 실행 문구 분기

## 실행 로그
검증 명령:
```powershell
cmd /C "set SPIKE_AUTOCLOSE_MS=5000&& npm start"
```

주요 로그:
```text
> geuldobi-desktop@1.0.0 start
> cmd /C "set ELECTRON_RUN_AS_NODE=&& electron ."

SPIKE-4: splash window shown
SPIKE-4: switched to main window (fallback-timeout)
SPIKE-4: auto-close after 5000ms
```

## 판정
- 판정 기준: `npm start` 실행 시 스플래시 창 + 로딩바 애니메이션 표시
- 결과: **PASS**

## 참고 사항
- 환경 변수 `ELECTRON_RUN_AS_NODE=1`가 사전 설정된 환경에서도 실행되도록 `start` 스크립트에서 해당 변수를 명시 해제함.
- 실행 중 Chromium disk cache 권한 경고(`Unable to create cache`)가 관측되었으나, 스플래시 표시/전환 동작 자체에는 영향 없음.
