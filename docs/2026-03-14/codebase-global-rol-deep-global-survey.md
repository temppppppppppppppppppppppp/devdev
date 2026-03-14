# Codebase Global ROL Deep Global Survey

Date: 2026-03-14
Status: final
Canonical Path: `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
Related Evidence Manifest: `docs/2026-03-14/codebase-global-rol-deep-global-survey-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%

## 1. Intent
- Re-run the codebase-global ROL survey in deep integrity mode rather than a light tranche inventory.
- Cover macro, micro, cross-cut, and operational views deeply enough that the active execution queue can remain governed by one SSOT roadmap with at least 95% confidence.
- Keep this cycle documentation-only. No runtime, DB, config, or test-behavior code changes are authorized by this survey itself.

## 2. Scope Lock
- included paths:
  - `main_a.py`
  - `modules/`
  - `scripts/`
  - `tests/`
  - `UI/`
  - `geuldobi-desktop/`
  - `config/`
  - root operational files: `main.js`, `smoke_sc.py`, `fix_costs.py`, `fix_costs2.py`, `RESET.py`
- excluded paths:
  - `.git/`, `.venv/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.hypothesis/`
  - generated logs and binary/archive assets unless directly needed as evidence
- change-lock or canary constraints:
  - survey-only mode
  - no code modification to runtime surfaces
  - no config, DB, or process mutation
- baseline docs read:
  - `docs/2026-03-14/codebase-global-rol-system-full-survey-3pass-audit.md`
  - `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
  - `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md`
  - `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md`
  - `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md`
  - `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md`
  - `docs/2026-03-14/codebase-global-rol-system-survey-execution-roadmap.md`
- fresh evidence artifacts:
  - `docs/2026-03-14/codebase-global-rol-deep-survey-inventory.json`
  - `docs/2026-03-14/codebase-global-rol-deep-survey-side-effects.json`
  - `docs/2026-03-14/codebase-global-rol-deep-survey-entrypoints.txt`
  - `docs/2026-03-14/codebase-global-rol-deep-survey-regression-surface.txt`

## 3. Coverage Matrix
- macro views covered:
  - repo topology and entrypoint authority
  - runtime/control-plane spine
  - subsystem boundary ownership
- micro views covered:
  - executable hotspot ranking
  - bulky asset outlier separation
  - mutable state and side-effect clusters
- cross-cut views covered:
  - observability durability split
  - persistence and recovery ownership
  - contract/config drift surfaces
  - shadow and stale-authority risk
- operational views covered:
  - regression/test partitions
  - smoke/canary mutation boundary
  - desktop bridge and direct network allowlist
- deferred surfaces:
  - historical dated docs remain reference-only
  - static art/archive assets remain outside action-bearing execution planning

## 4. Macro View
- active surveyed files after exclusions: `722`
- dominant roots: `tests 347`, `modules 265`, `config 55`, `scripts 26`, `geuldobi-desktop 15`, `UI 8`
- dominant extensions: `.py 582`, `.json 49`, `.txt 35`, `.yaml 24`, `.js 13`
- runtime authority map:
  - Python runtime authority remains centered in `main_a.py`
  - backend control plane authority remains in `modules/api/bridge_server.py`
  - engine subprocess boundary remains in `modules/api/process_runner.py`
  - authoritative Electron entry remains `geuldobi-desktop/src/main.js`
  - compatibility shim remains `geuldobi-desktop/main.js`
  - manual debug shadow remains root `main.js`
- shadow and auxiliary entry surfaces:
  - `geuldobi-desktop/temp-electron-loadcheck.js`
  - `geuldobi-desktop/temp-electron-paths.js`
  - these behave as utility probes, not authorities, but they enlarge the stale-edit surface
- runtime/control-flow spine:
  - bootstrap: stdio normalization, faulthandler, env/model load, project and genre selection in `main_a.py`
  - composition: service, DB, session logger, UI, state, stage helper wiring in `main_a.py`
  - operator surface split: `StudioVisualizer`, `Stage01Helpers`, `stage0/__init__.py`, `UIService`, direct `input`
  - desktop chain: Electron main -> FastAPI bridge -> ProcessRunner -> `main_a.py`
  - shutdown: pass-rate, audit, metrics, DB commit/close, memory close, failure logging in the app shell

## 5. Micro View
- bulk asset outliers that distort naive LOC ranking:
  - `config/style_references/investment/0_합본_원본_backup.txt`
  - `config/style_references/investment/참조작품1/0_합본.txt`
  - `geuldobi-desktop/src/splash/lucide.js`
  - `modules/core/laws/seeds/*.json`
- executable hotspot ranking:
  - `modules/core/stage4_interview_round.py` `4846` LOC
  - `main_a.py` `4221` LOC
  - `modules/core/db_manager.py` `3503` LOC
  - `modules/core/stage4_context_builder.py` `2690` LOC
  - `modules/domain/agents/state_tracker_npc.py` `2204` LOC
  - `modules/domain/agents/four_phase_arc_generator.py` `2130` LOC
  - `modules/core/stage3_orchestrator.py` `2067` LOC
  - `modules/domain/agents/base_agent.py` `2044` LOC
  - `modules/api/bridge_server.py` `1763` LOC
  - `modules/core/stage2_preflight.py` `1663` LOC
- dominant mutable state surfaces:
  - `BaseAgent` holds `_session_logger_global`, `_quota_exhausted_models`, `_api_keys`, `_context_caches`
  - `VecMemory` holds `_embed_cache`, shared DB connection mode, and initialization flags
  - `StudioLogger` holds singleton global logger state and retargetable file handlers
  - `DBManager` retains long-lived connection, cursor, and migration/recovery ownership
  - `main_a.py` retains module-level bootstrap flags and lazy-load state
- dense side-effect clusters:
  - `modules/core/stage0/__init__.py`: `100` raw `print`, `14` `input`, `7` write openings, `4` `json.dump`
  - `modules/core/stage01_helpers.py`: `105` `ui.log`, `19` `input`, `2` write openings, `2` `json.dump`
  - `main_a.py`: `44` raw `print`, `247` `ui.log`, `11` `input`
  - `modules/core/db_manager.py`: `361` SQLite-related hits
  - `modules/api/bridge_server.py`: backend route and JSONL provenance surface
  - `geuldobi-desktop/src/main.js`: spawn, settings write, debug log, direct surface ownership

## 6. Cross-Cut Integrity Matrix

| Cross-Cut Surface | Authority / Owner | Key Touchpoints | Major Side-Effects | Evidence Classes Used | Known Gap | Governing Execution Doc |
| --- | --- | --- | --- | --- | --- | --- |
| Observability | `StudioVisualizer`, `logger.py`, `session_logger.py`, app shell | `main_a.py`, `modules/core/studio_visualizer.py`, `modules/core/logger.py`, `modules/core/session_logger.py` | console lines, file logs, JSONL session logs | A+B+C+D | operator-visible output and durable sinks still diverge | `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md` |
| Persistence | `DBManager`, `AuditService`, `SessionLogger` | `modules/core/db_manager.py`, `modules/core/services/audit_service.py`, `modules/core/stage4_orchestrator.py` | SQLite writes, runtime audit JSONL, episode production JSONL | A+B+C | runtime shell still owns commit/close boundaries directly | `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md` |
| Operator Surface | Stage 0 and CLI/UI adapters | `modules/core/stage0/__init__.py`, `modules/core/stage01_helpers.py`, `modules/core/services/ui_service.py`, `main_a.py` | prompts, selections, console frames, config mutation confirmations | A+B+C | no single operator contract for Stage 0 and Stage 1 surfaces yet | `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md` |
| Contracts / Config | runtime and desktop contract docs plus package metadata | `geuldobi-desktop/package.json`, `docs/implementation/api-contract-v1.yaml`, `docs/implementation/event-schema-v1.json` | route drift, event drift, packaged env drift | A+C+D+E | contracts are strong, but they require continuous refresh against code | `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md` |
| Recovery / Retry | `DBManager`, `ProcessRunner`, stage retry surfaces | `modules/core/db_manager.py`, `modules/api/process_runner.py`, `modules/core/stage2_preflight.py` | integrity recovery, stop/restart, retry/fallback logic | A+B+C | recovery logic is present but ownership is split across runtime layers | `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md` |
| Subprocess / Network | Electron main, bridge server, process runner | `geuldobi-desktop/src/main.js`, `modules/api/bridge_server.py`, `modules/api/process_runner.py`, `geuldobi-desktop/src/splash/splash.js` | backend spawn, engine spawn, `/status`, `/events`, prompt transport | A+B+C+D | shadow entry and direct-network allowlists need continued fencing | `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md` |
| Cache / Global State | `BaseAgent`, `VecMemory`, `StudioLogger` | `modules/domain/agents/base_agent.py`, `modules/core/vec_memory.py`, `modules/core/logger.py` | shared caches, singleton logger state, key rotation, embed cache reuse | A+B | hidden mutable state still raises project-switch and boot-seam risk | `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md` |
| Regression / Canary | tests + smoke/canary scripts | `tests/`, `scripts/run_stage4_canary.py`, `scripts/run_stage34_canary.py`, `scripts/run_stage*_smoke.py` | project log writes, DB touches, patched input, runtime mutation | A+B+C | read-only contract checks and mutation-heavy proof runs remain mixed in operator mental model | `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md` |
| Shadow / Stale Authority | desktop shadows and utility probes | root `main.js`, `geuldobi-desktop/main.js`, `geuldobi-desktop/temp-electron-loadcheck.js`, `geuldobi-desktop/temp-electron-paths.js` | stale edits, ownership confusion, false entrypoint interpretation | A+B+C+E | tests fence the main shim, but utility probe files still increase authority confusion surface | `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md` |

## 7. Operational and Regression View
- current regression surface:
  - `301` Python test files
  - `4` JavaScript test files
- current bucket split:
  - `other 233`
  - `stage_pipeline 34`
  - `persistence_observability 18`
  - `desktop_ui 13`
  - `backend_control_plane 7`
- canary and smoke helpers:
  - canary: `scripts/run_stage34_canary.py`, `scripts/run_stage4_canary.py`
  - smoke: `scripts/run_stage2_smoke.py`, `scripts/run_stage3_smoke.py`, `scripts/run_stage4_smoke.py`
- read-only contract lanes already exist and materially reduce uncertainty:
  - `tests/test_desktop_shadow_hygiene.py`
  - `tests/test_desktop_direct_surface_contract.py`
  - `tests/test_main_a_boot_binding.py`
  - `tests/test_api_contract.py`
- mutation-heavy proving surfaces remain active:
  - `tests/test_run_stage4_canary.py`
  - smoke/canary scripts that boot live app flows, patch `input`, and write `canary_summary.json` plus companion audits
- operational direct-network notes:
  - splash direct poll to `/status` remains explicitly allowlisted
  - main renderer direct WebSocket `/events` remains explicitly allowlisted
  - Google API key validation fetch remains direct from the renderer by contract

## 8. Contradiction and Uncertainty Ledger
- contradictions closed:

| ID | Claim Area | Conflicting Evidence | Current Interpretation | Confidence Impact | Closure Action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `C-01` | desktop authority | `geuldobi-desktop/src/main.js`, `geuldobi-desktop/main.js`, root `main.js` | authoritative entry is `geuldobi-desktop/src/main.js`; `geuldobi-desktop/main.js` is shim; root `main.js` is manual debug shadow only | none after closure | confirmed with `package.json` and `tests/test_desktop_shadow_hygiene.py` | closed |
| `C-02` | observability sink meaning | file-first logger vs `ui.log` vs JSONL session logger | this is a deliberate split with a known gap, not an undocumented contradiction; human-visible output still lacks one durable substrate | low | keep as action-bearing execution item instead of ambiguous architecture drift | closed |
| `C-03` | hotspot ranking distortion | giant `.txt`/vendor assets vs executable code | bulky assets must be tracked separately from executable hotspots | none after closure | separate bulk asset outliers from executable hotspot table | closed |

- contradictions still open:
  - none at `P0` or architecture-authority level

- uncertainty items:

| ID | Topic | Missing Proof | Why It Matters | Temporary Bound | Confidence Impact | Closure Action | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `U-01` | Stage 0 surface seam ownership | one canonical Stage 0 contract implementation does not yet exist | prompts and operator events still span `stage0/__init__`, `Stage01Helpers`, `UIService`, and `main_a.py` | bounded by one Stage 0 execution doc and queue order | low | resolve during Stage 0 operator contract implementation | open |
| `U-02` | shadow utility probe hygiene | temp Electron probe files are not yet fenced by dedicated contract language | future edits could mistake probes for supported runtime entries | bounded by desktop control-plane doc and existing shadow hygiene tests | low | fold probes into desktop ownership fence during implementation | open |
| `U-03` | full operator-event durability | console-visible lines still outnumber durable structured operator events | later LLM analysis still cannot reconstruct every operator-visible event from one sink | bounded by the active residual-print execution doc and roadmap priority | low | realize durable operator-event substrate first | open |

- confidence caps still in effect:
  - none below the 95 threshold

## 9. Severity and Action Map
- `P0` items:
  - none confirmed from the current read-only deep survey
- `P1` items:
  - operator-visible observability is still split across `print`, `ui.log`, file logging, and partial JSONL durability
  - `main_a.py` still concentrates bootstrap, composition, prompt, and shutdown ownership
  - Stage 0 and Stage 1 operator surfaces still mix CLI-era prompts with newer UI/log adapters
  - desktop control-plane authority is well-fenced but still exposed to shadow and utility-surface confusion if not governed tightly
  - regression choice architecture still mixes read-only contract checks and mutation-heavy proof runs
- action-bearing areas:
  - operator-event durability
  - runtime bootstrap/orchestration hardening
  - Stage 0 operator contract hardening
  - desktop control-plane hardening
  - regression/canary rationalization
- areas with `no-execution-doc-required`:
  - bulk style reference text assets
  - static or bundled frontend assets such as `lucide.js`
  - historical docs and governance notes not acting as runtime authorities

## 10. Execution SSOT Mapping

| Area | Classification | Canonical Execution Doc | Notes |
| --- | --- | --- | --- |
| operator-visible runtime event durability | action-bearing | `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md` | keep first in queue because later items depend on durable operator events |
| runtime bootstrap and orchestration hardening | action-bearing | `docs/2026-03-14/runtime-bootstrap-orchestration-hardening-execution-ssot.md` | revalidated; now explicitly includes `Stage01Helpers` as a live seam |
| Stage 0 operator surface contract hardening | action-bearing | `docs/2026-03-14/stage0-operator-surface-contract-hardening-execution-ssot.md` | revalidated; scope now clearly spans `stage0/__init__`, `Stage01Helpers`, and `UIService` |
| desktop control-plane surface hardening | action-bearing | `docs/2026-03-14/desktop-control-plane-surface-hardening-execution-ssot.md` | revalidated against package entry, preload surface, direct-network contracts, and shadow hygiene tests |
| regression and canary surface rationalization | action-bearing | `docs/2026-03-14/regression-canary-surface-rationalization-execution-ssot.md` | revalidated against the current 301-Python + 4-JS test surface and active smoke/canary helpers |

## 11. Single SSOT Roadmap Lineage
- canonical roadmap:
  - `docs/2026-03-14/codebase-global-rol-system-survey-execution-roadmap.md`
- temp roadmap mirror:
  - `docs/temp/execution-roadmap.md`
- execution order basis:
  - substrate-first
  - operator-event durability before seam extraction
  - seam extraction before Stage 0 and desktop contract hardening
  - regression tiering last
- lane or phase structure:
  - lane 1: substrate and runtime ownership
    - `residual-print-ui-log-db-full-survey-3pass`
    - `runtime-bootstrap-orchestration-hardening`
  - lane 2: operator surface and control plane
    - `stage0-operator-surface-contract-hardening`
    - `desktop-control-plane-surface-hardening`
  - lane 3: verification envelope
    - `regression-canary-surface-rationalization`

## 12. Confidence Summary
- estimated score: `96/100`
- score rationale:
  - scope and path coverage completeness: `20/20`
  - macro + micro + cross-cut + operational completeness: `15/15`
  - side-effect and durability coverage: `14/15`
  - evidence triangulation quality: `14/15`
  - contradiction closure quality: `9/10`
  - uncertainty ledger quality: `9/10`
  - execution-SSOT mapping and single-roadmap coherence: `10/10`
  - validation and proof artifacts: `5/5`
- closed gaps:
  - desktop authority hierarchy is now explicitly evidenced and not ambiguous
  - executable hotspot ranking is separated from bulky data or vendor assets
  - active queue still converges into one roadmap with no competing SSOT
- remaining gaps:
  - operator-visible event durability is still a queued implementation task, not an already-landed substrate
  - Stage 0 and Stage 1 prompt surfaces remain split across several helpers
  - utility Electron probe files still enlarge the stale-authority surface
- final statement:
  - current deep survey evidence is sufficient to keep one SSOT roadmap active with no confirmed `P0` items and five bounded `P1` execution areas
  - no unresolved contradiction currently forces confidence below 95%
