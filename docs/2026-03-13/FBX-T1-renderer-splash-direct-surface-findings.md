# FBX-T1 Renderer / Splash / Direct Surface Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 범위: `geuldobi-desktop/src/index.html`, `geuldobi-desktop/src/splash/splash.js`
> 방법: `read-only surface inventory + 3PASS`

## 결론

- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 1건
- 핵심 결론: renderer 표면은 대부분 preload bridge를 통과하지만, 실제 네트워크 표면은 preload만 보면 닫히지 않는다.

## PASS 1

- `splash.js:14`는 `statusBaseUrl + /status`로 직접 `fetch()`를 보낸다.
- `index.html:5972-5973`는 `window.geuldobiDesktop.getBackendUrl()` 이후 직접 `WebSocket(wsUrl)`를 연다.
- `index.html:7409`는 Google API key 검증을 위해 `https://generativelanguage.googleapis.com/...`로 직접 `fetch()`를 보낸다.
- `index.html:3715`, `index.html:3724`와 이후 렌더링 표면은 `escapeHtml()` / `sanitizeToken()`을 통해 고위험 DOM 주입 경계를 감싼다.
- quality/safe-ops/project/material/work_guard/run 경로는 `window.geuldobiDesktop.*`를 통해 preload surface를 탄다.

## PASS 2

- direct network surface는 3개로 수렴했다.
  - splash health polling
  - live event websocket
  - external API key validation
- 그 외 런타임 제어 surface는 preload -> main -> backend 체인으로 정렬된다.
- `requestRiskApprovalId()`는 `index.html:4733`의 `window.prompt()`를 사용하며, 승인 수집 자체는 renderer 로컬 UX에 남아 있다.
- `tests/test_ui_renderer_sanitization.py`는 고위험 동적 surface escaping을 고정하지만, direct network inventory 자체를 검사하지는 않는다.

## PASS 3

### [FBX-T1-001] Renderer network ownership is split between bridge-managed and direct-managed surfaces

- **Severity**: `P2`
- **현상**: renderer 네트워크 표면이 preload bridge 전용이 아니다. splash polling, websocket, 외부 API key 검증은 renderer가 직접 소유한다.
- **코드 근거**:
  - `geuldobi-desktop/src/splash/splash.js:14`
  - `geuldobi-desktop/src/index.html:6`
  - `geuldobi-desktop/src/index.html:5972-5973`
  - `geuldobi-desktop/src/index.html:7409`
- **사용자/운영 영향**: preload/IPC만 조사하면 실제 네트워크 표면을 일부 놓쳐 false green이 발생할 수 있다. CSP, 관측성, 오류 보고 범위를 preload 기준으로만 잡으면 누락된다.
- **테스트 근거**:
  - `tests/test_ui_renderer_sanitization.py`는 DOM sanitization만 고정한다.
  - direct network surface allowlist를 고정하는 전용 회귀는 없다.
- **중복 여부**: `none`
- **권장 후속 조치**: 이후 remediation 없이도 조사/감리 문서에는 `direct-but-approved` 네트워크 표면 allowlist를 항상 별도 유지한다.

## Retained Open Set

- `P2`: `FBX-T1-001`
- `P3`: 없음

## Resume Packet

- `Current phase`: `FBX-T1 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `renderer/splash direct network inventory`
- `Next surface`: `FBX-T2 preload/electron ipc matrix`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
