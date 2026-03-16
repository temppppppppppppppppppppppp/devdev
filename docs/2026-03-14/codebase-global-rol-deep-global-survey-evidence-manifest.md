<!-- [참고자료] -->
# Codebase Global ROL Deep Global Survey Evidence Manifest

Date: 2026-03-14
Status: final
Topic: `codebase-global-rol`
Related Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
Related Execution Docs:
- `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
- `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md`
- `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md`
- `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md`
- `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md`
Related Roadmap:
- `docs/2026-03-14/codebase-global-rol-system-survey-execution-roadmap.md`

## 1. Summary
- evidence scope: fresh live-code inventory, side-effect census, entrypoint map, regression surface map, and targeted authority-contract reads
- freshness note: regenerated from the live workspace on 2026-03-14 for the deep integrity survey cycle
- known limits: counts are path- and pattern-based; semantic interpretation remains in the master survey doc

## 2. Artifact Index

| Artifact | Type | Acquired By | Freshness | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
| `docs/2026-03-14/codebase-global-rol-deep-survey-inventory.json` | inventory | live workspace census | fresh | deep survey + future delta checks | included roots, extension counts, LOC ranking, root-level hotspot splits |
| `docs/2026-03-14/codebase-global-rol-deep-survey-side-effects.json` | side-effect census | regex inventory over live code | fresh | deep survey + execution SSOT refresh | includes `print`, `ui_log`, `logging`, `input`, DB/network/subprocess patterns |
| `docs/2026-03-14/codebase-global-rol-deep-survey-entrypoints.txt` | entrypoint map | live workspace scan | fresh | deep survey + control-plane review | captures Python main guards, Electron entrypoints, IPC, FastAPI, subprocess surfaces |
| `docs/2026-03-14/codebase-global-rol-deep-survey-regression-surface.txt` | regression summary | live test/script census | fresh | deep survey + regression execution doc | current test counts and smoke/canary helper inventory |
| `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md` | prior canonical survey | baseline lineage read | current same-day baseline | contradiction and delta reference | earlier global survey bundle for comparison and queue continuity |
| `docs/2026-03-14/codebase-global-rol-system-survey-execution-roadmap.md` | roadmap authority | canonical queue read | current | queue governance | single active roadmap for the queued execution bundle |

## 3. Primary Live References
- `main_a.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage0/__init__.py`
- `modules/core/services/ui_service.py`
- `modules/core/studio_visualizer.py`
- `modules/core/logger.py`
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- `modules/core/vec_memory.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/main.js`
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/src/preload.js`
- `main.js`
- `tests/test_desktop_shadow_hygiene.py`
- `tests/test_desktop_direct_surface_contract.py`
- `tests/test_main_a_boot_binding.py`
- `tests/test_run_stage4_canary.py`
- `docs/implementation/desktop-runtime-contract-v1.json`
- `docs/implementation/desktop-ipc-surface-contract-v1.json`
- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/event-schema-v1.json`

## 4. Evidence Class Coverage

| Class | Coverage | Representative Sources |
| --- | --- | --- |
| `A` direct live code | covered | `main_a.py`, `modules/core/logger.py`, `modules/api/bridge_server.py`, `geuldobi-desktop/src/main.js` |
| `B` structured inventory | covered | `codebase-global-rol-deep-survey-inventory.json`, `codebase-global-rol-deep-survey-side-effects.json`, `codebase-global-rol-deep-survey-entrypoints.txt` |
| `C` operational or verification surface | covered | `tests/test_desktop_shadow_hygiene.py`, `tests/test_desktop_direct_surface_contract.py`, `tests/test_main_a_boot_binding.py`, `tests/test_run_stage4_canary.py` |
| `D` config or contract authority | covered | `geuldobi-desktop/package.json`, `desktop-runtime-contract-v1.json`, `api-contract-v1.yaml`, `event-schema-v1.json` |
| `E` historical or governance lineage | covered | `codebase-global-rol-system-full-survey-3pass-audit.md`, active execution SSOT docs, active roadmap |

## 5. Limitations
- line-of-code rankings include large bundled or content assets unless explicitly separated in the survey narrative
- regex side-effect counts are intentionally broad and should be interpreted with direct file reads for critical claims
- this manifest records evidence presence and reuse potential; it does not replace the contradiction and uncertainty ledger in the master survey
