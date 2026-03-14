# 프론트엔드-백엔드 전역 전량 전수조사 통합 Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 입력 문서: `FBX-T1` ~ `FBX-T6`
> 방식: `sequential merge + dedupe`

## Executive Summary

- 순차 조사 체인은 `FBX-T1 -> FBX-T2 -> FBX-T3 -> FBX-T4 -> FBX-T5 -> FBX-T6`까지 완료했다.
- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 6건
- retained `P3`: 1건
- 핵심 결론: 현재 runtime은 dev spike와 확장 회귀 기준으로 살아 있지만, contract/test/build 문서층에는 여전히 moderate drift가 남아 있다.

## Severity Ledger

| Severity | Count | IDs |
|----------|------:|-----|
| `P0` | 0 | - |
| `P1` | 0 | - |
| `P2` | 6 | `FBX-T1-001`, `FBX-T2-001`, `FBX-T3-001`, `FBX-T5-001`, `FBX-T5-002`, `FBX-T6-001` |
| `P3` | 1 | `FBX-T2-002` |

## Retained Findings

### [FBX-T1-001] Renderer network ownership is split between bridge-managed and direct-managed surfaces

- **Severity**: `P2`
- **현상**: renderer는 preload bridge 외에 splash `/status`, websocket `/events`, Google API key test fetch를 직접 소유한다.
- **영향 경계**: network surface inventory, CSP, operator-facing connectivity audit
- **중복 여부**: `none`

### [FBX-T2-001] Electron main returns transport error codes outside the documented API contract

- **Severity**: `P2`
- **현상**: `bridgeFetch()`가 `HTTP_*`, `NETWORK_ERROR`를 생성하지만 공식 API contract enum에는 없다.
- **영향 경계**: renderer error handling, desktop operator docs, false contract green
- **중복 여부**: `none`

### [FBX-T3-001] Live websocket `/events` surface is outside the formal API contract

- **Severity**: `P2`
- **현상**: backend와 renderer가 live로 쓰는 `/events` websocket이 API contract와 test gate 바깥에 있다.
- **영향 경계**: event schema drift, live log stream, operator-facing runtime proof
- **중복 여부**: `none`

### [FBX-T5-001] Packaged runtime advertises `engine.exe`, but the build stages a source-tree engine bundle and relies on fallback

- **Severity**: `P2`
- **현상**: packaged env/document는 `engine.exe`를 전제로 하지만 실제 build artifact는 source-tree engine bundle이며 runtime은 fallback에 의존한다.
- **영향 경계**: packaged diagnostics, desktop guide, artifact parity
- **중복 여부**: `none`

### [FBX-T5-002] Root-level `geuldobi-desktop/main.js` is a stale but high-risk drift source

- **Severity**: `P2`
- **현상**: active entry가 아닌 root `main.js`가 별도 해시로 남아 있고 최신 IPC surface를 일부 잃었다.
- **영향 경계**: developer editing path, stale patch reintroduction, audit confusion
- **중복 여부**: `none`

### [FBX-T6-001] Official desktop test gate under-covers live bridge/dashboard/risk surfaces

- **Severity**: `P2`
- **현상**: 공식 `npm test`는 bridge HTTP contract, risk gate, quality dashboard regression을 포함하지 않는다.
- **영향 경계**: CI/package gate, false green, release confidence
- **중복 여부**: `none`

### [FBX-T2-002] Preload exposes dead-candidate IPC surfaces with no active renderer consumers

- **Severity**: `P3`
- **현상**: `getStatus()`와 `getWorkspacePath()`는 IPC로 남아 있으나 active renderer consumer가 없다.
- **영향 경계**: surface sprawl, stale IPC inventory
- **중복 여부**: `related-but-new-surface`

## Dedupe Notes

- `FBX-T3-001`과 `FBX-T6-001`은 모두 coverage gap과 관련 있지만 root cause가 다르다.
  - `FBX-T3-001`: live websocket surface의 contract omission
  - `FBX-T6-001`: official package gate omission
- `FBX-T5-001`과 `FBX-T5-002`는 모두 desktop packaging 축이지만, 하나는 artifact contract drift이고 다른 하나는 stale source drift다.

## Current State

- runtime proof는 확보됐다.
- unresolved `P1`는 없다.
- 후속 remediation execution SSOT와 its 3PASS audit를 작성할 수 있는 상태다.

## Resume Packet

- `Current phase`: `consolidated findings completed`
- `Last completed pass`: `merge/dedupe`
- `Last completed surface`: `FBX-T1~T6 retained open set`
- `Next surface`: `frontend-backend-global-consolidated-findings-3pass-reaudit.md`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
