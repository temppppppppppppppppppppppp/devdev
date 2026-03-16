<!-- [참고자료] -->
# codebase-global-cleanroom-source-only Deep Global Integrity Survey

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/codebase-global-cleanroom-source-only-deep-global-survey.md`
Related Evidence Manifest: `docs/2026-03-15/codebase-global-cleanroom-source-only-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/docs/log artifacts already present; clean-room survey excludes them from authority`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent
- Produce a clean-room codebase-global survey from the current source tree only.
- Ignore prior audit bundles, run evidence, historical docs, and project artifacts as claim authority.
- Close the full deep-survey contract with a bounded static survey, explicit action mapping, and one single-SSOT roadmap.

## 2. Scope Lock
- included paths:
  - `main_a.py`
  - `modules/`
  - `scripts/`
  - `tests/`
  - `UI/`
  - `geuldobi-desktop/`
  - `config/`
- excluded paths:
  - `docs/YYYY-MM-DD/` historical survey material as evidence authority
  - `projects/`, live logs, DB files, `data/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`
- change-lock or canary constraints:
  - survey-only; no code mutation, no DB mutation, no runtime interaction
- baseline docs read:
  - governance only: init harness, deep survey harness, coverage contract, 3-pass harness, templates, and validator contracts

## 3. Coverage Matrix
- macro views covered:
  - repo topology
  - entrypoints
  - subsystem boundaries
  - control-plane layering
- micro views covered:
  - hotspot ranking
  - prompt anchor counts
  - persistence/write anchor counts
  - selected direct code reads of hotspot files
- cross-cut views covered:
  - observability
  - persistence
  - operator surface
  - contracts/config
  - recovery/retry
  - subprocess/network
  - cache/global state
  - regression/canary
  - shadow/stale authority
- operational views covered:
  - tests and smoke/canary harnesses
  - validator tooling
  - script/runtime separation
- deferred surfaces:
  - runtime behavior, DB content, and live artifact alignment are intentionally deferred out of this clean-room survey

## 4. Macro View
- topology:
  - `main_a.py` remains the runtime spine.
  - `modules/core/` carries the operational bulk.
  - `modules/domain/` holds agent logic and generation strategy.
  - `modules/api/` plus `geuldobi-desktop/src/` form the bridge/control-plane shell.
  - `geuldobi-desktop/src/index.html` is the main active frontend control surface; `UI/` remains mostly asset weight.
  - `tests/` is broad and multi-tiered.
  - `UI/` is asset-heavy rather than control-heavy.
- authority map:
  - runtime entry and console authority: `main_a.py`
  - prompt wrapper layer: `modules/core/services/ui_service.py` and `modules/core/studio_visualizer.py`
  - persistence and many writes: `modules/core/db_manager.py`
  - audit summary and proof digest: `modules/core/services/audit_service.py`
  - JSONL session logging: `modules/core/session_logger.py`
  - subprocess and prompt-broker transport: `modules/api/process_runner.py`, `modules/api/prompt_broker.py`, `modules/api/bridge_server.py`
  - desktop control-plane boundary: `geuldobi-desktop/src/preload.js` and `geuldobi-desktop/src/main.js`
  - active renderer state authority: `geuldobi-desktop/src/index.html`
- runtime/control-flow spine:
  - console mode starts in `main_a.py`
  - stage flows delegate to stage orchestrators and domain agents
  - stage and UI events fan out to DB, JSONL, audit summary, and console surfaces
  - desktop mode routes through `index.html -> preload -> Electron main -> FastAPI bridge -> ProcessRunner -> main_a.py`
  - live runtime events return on a separate websocket path from `/events`
- subsystem boundaries:
  - boundaries exist in file layout but not yet in write authority; prompt, persistence, and audit responsibilities still cross those boundaries heavily
  - desktop command and event channels are separate in implementation but partly conflated in renderer readiness logic

## 5. Micro View
- hotspot ranking:
  - highest action-bearing hotspots are `modules/core/stage4_interview_round.py`, `main_a.py`, `modules/core/db_manager.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage3_orchestrator.py`, `modules/api/bridge_server.py`
  - `geuldobi-desktop/src/splash/lucide.js` is the single largest file but is not the highest-value remediation target
- high-risk files/modules:
  - `main_a.py`: large runtime spine with many raw prompt sites and direct commit/rollback touches
  - `modules/core/db_manager.py`: oversized persistence authority with mixed responsibilities
  - `modules/core/services/ui_service.py` and `modules/core/studio_visualizer.py`: prompt wrapper and telemetry layer
  - `modules/api/process_runner.py`, `modules/api/bridge_server.py`, `modules/api/prompt_broker.py`, `geuldobi-desktop/src/index.html`, `geuldobi-desktop/src/preload.js`, `geuldobi-desktop/src/main.js`: transport/control-plane chain
  - source-text hygiene risk is visible in `main_a.py`, `bridge_server.py`, `ui_service.py`, `studio_visualizer.py`, and Electron main
- dominant mutable state surfaces:
  - app-level state in `main_a.py`
  - DB writes in `DBManager`
  - in-memory runtime audit buffer in `AuditService`
  - prompt registries and process tails in `PromptBroker` and `ProcessRunner`
- dense side-effect clusters:
  - prompt and console output
  - DB writes and transaction calls
  - JSONL/log/audit summary writes
  - Electron IPC and bridge HTTP routes
  - settings/material/project filesystem writes in Electron main

## 6. Cross-Cut Integrity Matrix
- Companion matrix: `docs/2026-03-15/codebase-global-cleanroom-source-only-cross-cut-integrity-matrix.md`
- Key summary:
  - observability and persistence are split across app, DBManager, AuditService, SessionLogger, and stage writers
  - operator prompt authority is split across raw `input(...)`, `_get_int_input(...)`, `UIService.prompt()`, `StudioVisualizer.prompt()`, and bridge-mode prompt brokering
  - source-text hygiene is a distinct cross-cut lane because corruption and detector noise both exist in active source
  - backend-front/control-plane seams are action-bearing on their own because desktop readiness, prompt concurrency, reconnect semantics, and bridge timeouts are not governed by one coherent contract today

## 7. Operational and Regression View
- tests:
  - broad test surface exists, including stage-specific, DB, UI, desktop, audit, and canary-related files
  - direct heuristic tag sweep found strong presence for agent, UI, stage3, stage4, DB, and encoding-related tokens, but those counts are supporting evidence only
  - desktop/frontend tests are strong on route names, schemas, and surface inventories, but weak on run-state semantics such as reconnect resync, prompt concurrency, and command-vs-event readiness separation
- smoke/canary:
  - `scripts/run_stage3_smoke.py`, `scripts/run_stage4_smoke.py`, `scripts/run_stage4_canary.py`, `scripts/run_stage34_canary.py`, and `scripts/run_auto_frontier_lag_harness.py` are present
  - harnesses already reach audit flush, DB, and prompt seams
- repair tooling:
  - `scripts/check_utf8_hygiene.py`
  - `scripts/ops_validator.py`
  - `scripts/validate_deep_global_survey_bundle.py`
  - roadmap and stale-reference tooling
- read-only vs mutation-heavy boundaries:
  - mutation-heavy: runtime app, DBManager callers, Electron settings/material/project handlers
  - read-only or bounded: validators, survey scripts, many smoke helpers, desktop contract files
- fresh-run likely fault watchlist from static evidence:
  - desktop renderer can refuse run commands while websocket is down even if the HTTP bridge path is healthy
  - concurrent `prompt_request` events can be dropped by the renderer while backend pending prompts remain live
  - websocket reconnect restores the socket but not an explicit active-run or pending-prompt snapshot
  - splash handoff, main-window websocket readiness, and bridge HTTP timeout policy are not aligned under one startup contract
  - direct renderer Google API validation fetch has different timeout and telemetry behavior from bridge-managed backend fetches

## 8. Contradiction and Uncertainty Ledger
- Companion ledger: `docs/2026-03-15/codebase-global-cleanroom-source-only-uncertainty-contradiction-ledger.md`
- contradictions closed:
  - `UI/` asset size does not imply it is the main runtime authority
  - splash vendor file size does not dictate roadmap priority
- contradictions still open:
  - the hygiene gate still conflates some legitimate question prompts with suspicious question tokens
  - prompt handling is still governed by multiple authorities
  - desktop command-path readiness is still coupled to websocket state in the renderer
  - prompt concurrency policy differs between renderer and `PromptBroker`
- uncertainty items:
  - runtime reproduction is explicitly out of scope
  - test depth and asset/config liveness remain bounded
  - reconnect and timeout semantics remain source-only inferences until a runtime-focused follow-up
- confidence caps still in effect:
  - none below 95 for source-only bounded claims

## 9. Severity and Action Map
- `P0` items:
  - none from source-only evidence
- `P1` items:
  - active source-text corruption and mojibake-like literals/comments in operator-facing and contract-adjacent files
  - operator prompt authority fragmentation across console, UI wrappers, bridge broker, and desktop transport layers
  - backend-front/control-plane connectivity mismatches across renderer, preload, Electron main, bridge server, and `PromptBroker`
- `P2` items:
  - persistence and observability write authority remain too concentrated and too distributed at the same time
  - DBManager size and transaction exposure raise change-risk and regression-risk
  - bridge/control-plane compatibility and dead-candidate paths add maintenance drag
- action-bearing areas:
  - source-text hygiene and UTF-8 boundary repair
  - backend-front/control-plane connectivity hardening
  - runtime/operator surface unification
  - persistence/observability boundary hardening
- areas with `no-execution-doc-required`:
  - `UI/` asset packs
  - script/utilities as a standalone tranche
  - tests as a standalone execution lane
  - config/prompt maps as a standalone lane in this bundle

## 10. Execution SSOT Mapping

| Area | Classification | Canonical Execution Doc | Notes |
| --- | --- | --- | --- |
| source-text hygiene | action-bearing | `docs/2026-03-15/source-text-utf8-hygiene-remediation-execution-ssot.md` | repair real corruption, narrow detector noise, keep touched-file UTF-8 gate credible |
| backend-front/control-plane connectivity | action-bearing | `docs/2026-03-15/backend-front-control-plane-connectivity-remediation-execution-ssot.md` | decouple command readiness from websocket state, close prompt/reconnect gaps, and normalize desktop bridge behavior |
| runtime/operator surface | action-bearing | `docs/2026-03-15/runtime-operator-surface-unification-remediation-execution-ssot.md` | centralize prompt authority across console and wrapper surfaces after transport semantics are stabilized |
| persistence/observability boundary | action-bearing | `docs/2026-03-15/persistence-observability-boundary-remediation-execution-ssot.md` | reduce write-authority spread and make audit/session sinks more coherent |
| UI asset packs | no-execution-doc-required | none | asset-liveness survey is separate from this bundle |
| scripts/utilities | no-execution-doc-required | none | support and validation surfaces are folded into verification plans |
| tests/regression | no-execution-doc-required | none | regression updates should track each execution lane, not form a separate roadmap lane |

## 11. Single SSOT Roadmap Lineage
- canonical roadmap:
  - `docs/2026-03-15/codebase-global-cleanroom-source-only-execution-roadmap.md`
- temp roadmap mirror:
  - `docs/temp/execution-roadmap.md`
- execution order basis:
  - source-text hygiene first, then backend-front connectivity hardening, then runtime/operator unification, then persistence/observability hardening
- lane or phase structure:
  - Phase 1: source hygiene and detector trust
  - Phase 2: backend-front/control-plane connectivity hardening
  - Phase 3: prompt authority unification
  - Phase 4: persistence/observability boundary reduction

## 12. Confidence Summary
- estimated score:
  - `96/100`
- score rationale:
  - all eight tranches are covered
  - macro, micro, cross-cut, and operational views are all explicit
  - side-effect categories are closed
  - four action-bearing areas are execution-mapped and governed by one roadmap
  - claims are bounded to source-only evidence and do not overreach into runtime assertions
- closed gaps:
  - `UI/` size vs active logic confusion
  - hotspot line-count vs action priority confusion
- remaining gaps:
  - runtime reproduction remains intentionally excluded
  - source hygiene detector noise is still open
  - desktop reconnect and timeout behavior are still source-only inferences
  - asset/config liveness is bounded rather than runtime-proven
- final statement:
  - This survey clears the 95% confidence gate as a clean-room static governing artifact. It is not a runtime-resolution claim, but it is strong enough to govern the next execution-doc-driven realization wave.
