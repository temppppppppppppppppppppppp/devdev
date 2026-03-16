<!-- [참고자료] -->
# Codebase Global ROL System Survey Evidence Manifest

Date: 2026-03-14
Status: final
Topic: `codebase-global-rol-system-survey`
Related Survey Docs:
- `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
Related Execution Docs:
- `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
- `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md`
- `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md`
- `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md`
- `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md`

## 1. Summary
- evidence scope: codebase-global inventory, side-effect pattern summary, entrypoint sweep, and regression-surface index
- freshness note: generated from the live workspace on 2026-03-14 with build and dependency exclusions applied
- known gaps: historical docs were used only as contract references; this manifest is anchored to live code and raw generated artifacts

## 2. Artifact Index

| Artifact | Type | Acquired By | Freshness | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
| `docs/2026-03-14/codebase-global-rol-system-survey-inventory.json` | inventory | inline Python summary | fresh | survey + execution | root counts, LOC hotspots, top subdirs, and excluded surfaces |
| `docs/2026-03-14/codebase-global-rol-system-survey-side-effects.json` | side-effect map | inline Python summary | fresh | survey + execution | operator output, persistence, subprocess, network, and input density |
| `docs/2026-03-14/codebase-global-rol-system-survey-entrypoints.txt` | entrypoint sweep | `rg` | fresh | survey + execution | authoritative runtime, desktop, and smoke/canary entry surfaces |
| `docs/2026-03-14/codebase-global-rol-system-survey-regression-surface.txt` | regression inventory | `rg --files` | fresh | survey + execution | test and script surfaces for smoke, canary, desktop, and stage flows |
| `main_a.py` | live code reference | direct read | fresh | survey + execution | engine bootstrap and runtime shell |
| `modules/core/db_manager.py` | live code reference | direct read | fresh | survey + execution | primary SQLite authority |
| `modules/core/session_logger.py` | live code reference | direct read | fresh | survey + execution | durable JSONL sink subset |
| `modules/core/logger.py` | live code reference | direct read | fresh | survey + execution | file-first logger behavior |
| `modules/core/studio_visualizer.py` | live code reference | direct read | fresh | survey + execution | current console plus file dual sink |
| `modules/core/services/ui_service.py` | live code reference | direct read | fresh | survey + execution | Stage 0 selection helper and print/input surface |
| `modules/core/stage0/__init__.py` | live code reference | direct read | fresh | survey + execution | dominant Stage 0 operator surface |
| `modules/api/bridge_server.py` | live code reference | direct read | fresh | survey + execution | backend HTTP and WebSocket control plane |
| `modules/api/process_runner.py` | live code reference | direct read | fresh | survey + execution | subprocess runner and prompt surface |
| `geuldobi-desktop/src/main.js` | live code reference | direct read | fresh | survey + execution | authoritative Electron main process |
| `geuldobi-desktop/src/preload.js` | live code reference | direct read | fresh | survey + execution | IPC bridge boundary |
| `geuldobi-desktop/src/splash/splash.js` | live code reference | direct read | fresh | survey + execution | direct splash `/status` poll surface |
| `geuldobi-desktop/package.json` | contract reference | direct read | fresh | survey + execution | build and packaging entry authority |
| `docs/implementation/desktop-runtime-contract-v1.json` | contract reference | direct read | fresh | survey + execution | packaged runtime model contract |
| `docs/implementation/desktop-ipc-surface-contract-v1.json` | contract reference | direct read | fresh | survey + execution | live vs dead-candidate IPC contract |
| `docs/implementation/api-contract-v1.yaml` | contract reference | direct read | fresh | survey + execution | backend HTTP plus direct-network allowlist contract |
| `docs/implementation/event-schema-v1.json` | contract reference | direct read | fresh | survey + execution | runtime event stream schema |

## 3. Limitations
- file and LOC counts include live fixture payloads and runtime data seeds where those files materially affect behavior
- Korean path fragments in raw artifacts may show mojibake in some terminals even when the stored files are UTF-8
- this manifest does not replace per-execution-doc current-state re-audit before implementation starts
