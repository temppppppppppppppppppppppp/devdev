# React Office Animation Runtime Isolation Audit

Date: 2026-03-20
Mode: system-track focused React follow-up
Confidence: 0.95

## Scope

- React program follow-up after the bounded renderer-state tranches
- Live code targets:
  - `geuldobi-desktop/src/index.html`
  - `geuldobi-desktop/src/renderer_state_bootstrap.js`
  - `geuldobi-desktop/src/renderer_state_react_helpers.js`
- Governing React docs:
  - `docs/2026-03-19/react-migration-renderer-state-view-execution-ssot.md`
  - `docs/2026-03-19/react-migration-execution-roadmap.md`

## Summary

The React migration is now at the edge of the first genuinely high-risk renderer boundary.

What remains in the main renderer is no longer mostly read-only panel ownership or shell state assembly. The next dense cluster is the office animation/runtime block:

- canvas sizing and resize timing
- sprite/image preload
- draw loop ownership via `requestAnimationFrame`
- office background and decorative rendering
- live stage flow rendering
- click hit-testing on the canvas
- mode effects and notice scroll
- animation skip/mute semantics

This cluster should not be treated as a normal React island candidate.

## Live Findings

Current live shape in `geuldobi-desktop/src/index.html`:

- `officeCanvas` remains authoritative
- the renderer still owns:
  - `canvas`
  - `ctx`
  - `resizeCanvas()`
  - `scheduleOfficeCanvasResize()`
  - `officeState`
  - `agentRuntime`
- sprite/image loading remains inline:
  - `loadAllSprites()`
  - `officeBgImg`
  - `deskTileImg`
  - decor atlases
- draw loop remains inline:
  - `drawOfficeBackground()`
  - `drawWallDisplay()`
  - `drawLLMFlow()`
  - `drawAgent()`
  - `drawModeEffect()`
  - `drawNoticeScroll()`
  - `draw()`
- canvas hit-testing and click bubble logic remain inline
- skip/mute buttons still directly mutate `officeState`

Operational meaning:

- the office runtime is still a stateful canvas program, not just a view fragment
- it is coupled to shell state but not yet safely isolated behind a module boundary

## Why This Is High Risk

This area is risky for three reasons.

1. It owns time

- `requestAnimationFrame`
- frame counters
- animation timing
- resize timing

2. It owns visual authority

- sprite load success/failure
- canvas draw order
- active agent highlighting
- verdict effects
- office notice rail

3. It touches live shell semantics

- `officeState.skipAnimation`
- `officeState.mute`
- stage/action rendering
- active agent flow

If this is moved carelessly, the likely regressions are:

- blank office screen
- off-by-one or stalled animation
- broken sprite load fallback
- wrong active agent or verdict effect
- click/hit-box mismatch after resize

## Decision

Do not move office animation ownership into React lifecycle code yet.

Preferred next step:

- isolate the office runtime into a dedicated non-React renderer module first
- keep canvas authority, draw loop authority, and runtime state ownership explicit
- let React consume office status around that module, not replace the module yet

Not recommended yet:

- React component ownership of the draw loop
- React ownership of sprite preload
- React ownership of prompt/run-stop semantics through office state coupling

## Recommended Safe Tranche

Safe high-risk entry should be:

1. extract the office runtime block into a dedicated external module
2. keep public inputs narrow:
   - canvas element
   - office state snapshot
   - agent runtime snapshot
   - shell callbacks only where strictly needed
3. keep the following authority unchanged:
   - `_showPromptDialog`
   - `_resolveCurrentPrompt`
   - run/stop orchestration
   - websocket/control-plane ownership

This would be an isolation tranche, not a React rewrite tranche.

## Not In Scope Yet

- prompt ownership migration
- prompt queue/controller rewrite
- run/stop controller rewrite
- preload/main authority changes
- canvas removal or replacement

## Conclusion

The next React-adjacent step is not “convert office animation to React.” It is “extract the office runtime into an explicit non-React module boundary first.” That keeps the migration moving while avoiding the worst ownership collision in the current desktop renderer.
