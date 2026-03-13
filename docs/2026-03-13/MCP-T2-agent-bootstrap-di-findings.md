# [MCP-T2] Agent Bootstrap / DI Findings

> Date: 2026-03-13
> Status: `executed`
> Audit mode: `static / read-only / code-and-test verification`
> Order: `main_a-control-plane-detail-full-survey-audit-order.md`

This document replaces the template and records the executed T2 audit for agent bootstrap, lazy load, and DI wiring in `main_a.py`.

---

## Audit Scope

- `main_a.py`
  - `_attach_agents()`
  - `_init_core_agents()`
  - `_init_v50_modules()`
  - `_ignite_quad_cache_system()`
  - `_load_v50_history()`
- Direct downstream
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/services/*`

## Required Evidence

- `tests/test_stage_transition.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_protocols_services.py`

## Pass Log

- PASS 1: scanned bootstrap entrypoints, V50 lazy load/init flow, Stage 2/3/4 DI boundaries, and required tests. Candidate findings: 4.
- PASS 2: cross-checked code against required tests and prior audit docs. Removed 1 candidate: `_ignite_quad_cache_system()` is still dead code, but this was already documented and no new control-plane break was proven in this pass.
- PASS 3: retained 3 findings below.

## Finding Ledger

| ID | Sev | Status | File / Function | Summary |
|----|-----|--------|-----------------|---------|
| `MCP-T2-01` | `P2` | retained | `main_a.py::_attach_agents`, `_init_v50_modules` | Partial V50 init failure leaves a hybrid app graph while bootstrap still reports success |
| `MCP-T2-02` | `P2` | retained | `main_a.py::_stage_3_batch_blueprinting`, `modules/core/stage3_context.py`, `modules/core/stage3_orchestrator.py` | Stage3 smart-retrieval bypasses the injected DI context and keeps reading `app` directly |
| `MCP-T2-03` | `P1` | retained | `main_a.py::_init_v50_modules` | Legacy JSON-to-DB fallback paths are rooted at `_PROJECTS_DIR` instead of the bound project root |

---

## `MCP-T2-01` - Partial V50 init failure still returns bootstrap success

1. ID
   - `MCP-T2-01`
2. Severity
   - `P2`
3. Summary
   - `_attach_agents()` returns `True` once core agents are present, even if `_init_v50_modules()` throws halfway through optional-module initialization.
   - `_init_v50_modules()` catches the whole V50 block as one non-fatal exception, so already-written attrs remain attached and later attrs remain missing. The caller gets no structured signal that bootstrap is now partial.
4. Code evidence
   - `_lazy_load_v50_modules()` sets `V50_MODULES_AVAILABLE = True` after import success and returns the V50 constructor map: `main_a.py:136-199`.
   - `_attach_agents()` calls `_init_core_agents()`, then `_init_v50_modules()`, then logs full system init and returns `True`: `main_a.py:1918-2016`.
   - `_init_v50_modules()` wraps the entire V50 setup in one `try/except` and only logs on failure: `main_a.py:1562-1883`.
   - The same V50 block incrementally writes app attrs such as `failure_learner`, `character_voice`, `foreshadow_tracker`, `quality_dashboard`, `pass_rate_monitor`, and `context_advisor` before the catch point: `main_a.py:1577-1879`.
   - Stage 4 later snapshots whatever happens to exist on the app into `Stage4Context`: `main_a.py:3424-3460`.
5. Downstream impact boundary
   - The control plane cannot distinguish "V50 unavailable", "V50 fully initialized", and "V50 partially initialized".
   - Stage 2 and Stage 4 consume optional attrs from the app object, so a mid-block failure can produce a mixed graph where some modules are live, some are missing, and bootstrap still proceeds as if initialization finished cleanly.
6. Test evidence or test gap
   - None of the required tests call `_attach_agents()` or `_init_v50_modules()`.
   - `tests/test_stage3_orchestrator.py` and `tests/test_run_stage4_canary.py` exercise downstream orchestrators with injected mocks, not bootstrap partial-failure behavior.
   - There is no required test covering "one V50 module succeeds, a later one fails, bootstrap result stays distinguishable".
7. Duplicate status
   - `none found` in executed audit documents reviewed for this pass.
   - Prior `god-object` docs describe extraction/splitting of `_attach_agents()` but do not record the hybrid-graph-on-success control-plane bug.
8. Recommended follow-up
   - Split `_init_v50_modules()` into independently guarded subgroups or a transaction-like init plan.
   - Return bootstrap status with at least `core_ok`, `v50_ok`, and `partial_failures`, instead of a bare `bool`.
   - Add a regression test that forces an exception after one optional module is attached and before later modules are wired.

---

## `MCP-T2-02` - Stage3 smart retrieval bypasses the injected context boundary

1. ID
   - `MCP-T2-02`
2. Severity
   - `P2`
3. Summary
   - `main_a.py` now injects `Stage3Context.from_app(self)` as the Stage3 boundary, but the smart-retrieval path inside `Stage3Orchestrator` still fetches `context_advisor`, retrieval memory, and genre from `self.app`.
   - This means the advertised DI seam is not the real runtime contract for Stage3 retrieval.
4. Code evidence
   - Stage3 entry injects `Stage3Context.from_app(self)` immediately before delegation: `main_a.py:2802-2807`.
   - `Stage3Context` does not define `context_advisor`, `memory`, or `vec_memory` slots and `from_app()` does not extract them: `modules/core/stage3_context.py:16-43`, `modules/core/stage3_context.py:94-120`.
   - `_generate_blueprint()` reads smart-retrieval dependencies from `self.app` directly:
     - `getattr(self.app, "vec_memory", None) or getattr(self.app, "memory", None)`
     - `getattr(self.app, "context_advisor", None)`
     - `self.app.selected_genre`
     - `modules/core/stage3_orchestrator.py:963-997`
   - By contrast, Stage2 and Stage4 contexts explicitly carry `context_advisor` via `from_app()`:
     - `modules/core/stage2_context.py:60`, `modules/core/stage2_context.py:208-222`
     - `modules/core/stage4_context.py:39`, `modules/core/stage4_context.py:140-156`
5. Downstream impact boundary
   - Replacing or testing Stage3 retrieval through the injected context alone is impossible; callers must still shape the backing `app` object.
   - The thin-delegate contract in `main_a.py` is incomplete: the control plane claims explicit DI, but Stage3 still retains hidden app-level service dependencies.
6. Test evidence or test gap
   - `tests/test_stage3_orchestrator.py:535-579` explicitly sets `app_mock.context_advisor` and asserts the call on that app-level object.
   - `tests/test_stage3_orchestrator.py:909-936` verifies current `Stage3Context` slot mapping, but not a context-driven advisor or memory path.
   - There is no required test proving that Stage3 smart retrieval can run from injected context dependencies without reading `self.app`.
7. Duplicate status
   - `related-but-new-control-plane-surface`
   - `docs/2026-02-23/opus_tf7_b_audit.md:102-112` already recorded that Stage3 DI context and actual SC consumption were split.
   - This audit keeps it because `main_a.py` now presents explicit Stage3 DI injection, so the same issue remains visible at the `main_a.py` control-plane contract boundary.
8. Recommended follow-up
   - Add `context_advisor` and retrieval memory handles to `Stage3Context`.
   - Make `_generate_blueprint()` consume retrieval services only through `ctx`.
   - Replace the current app-bound test with a context-bound regression test, then keep one compatibility test only if backward compatibility is required.

---

## `MCP-T2-03` - Legacy migration fallback is bound to `_PROJECTS_DIR`, not the current project root

1. ID
   - `MCP-T2-03`
2. Severity
   - `P1`
3. Summary
   - When DB-backed V50 data is missing, legacy JSON fallback paths are rebuilt from `self._PROJECTS_DIR` plus `self.current_project.name`.
   - `_PROJECTS_DIR` is the relative string `"projects"`, not the already-bound `self.current_project.paths.root`, so fallback migration depends on the global workspace root instead of the project object chosen at runtime.
4. Code evidence
   - `_PROJECTS_DIR = "projects"`: `main_a.py:235`.
   - Legacy fallback paths under `_init_v50_modules()` use `_PROJECTS_DIR` directly:
     - `failure_learning.json`: `main_a.py:1635-1639`
     - `character_voice.json`: `main_a.py:1689-1694`
     - `foreshadow.json`: `main_a.py:1703-1708`
     - `voice_profiles.json`: `main_a.py:1758-1764`
   - The same function later uses the bound project root correctly for other modules:
     - `project_path = str(self.current_project.paths.root)`
     - `PassRateMonitor(project_path)`
     - `QualityDashboard(Path(project_path))`
     - `main_a.py:1863-1870`
5. Downstream impact boundary
   - JSON-to-DB migration is part of bootstrap, so wrong root binding can import stale or unrelated legacy artifacts into the active project DB.
   - This is a project-boundary bug, not just a path-style inconsistency, because the control plane already owns an authoritative bound project root and then ignores it for part of the bootstrap surface.
6. Test evidence or test gap
   - None of the required tests cover these fallback paths.
   - There is no required test proving that V50 fallback migration follows `current_project.paths.root` for non-default roots, mocked roots, or alternate project bindings.
7. Duplicate status
   - `none found` in executed audit findings reviewed for this pass.
   - `docs/2026-02-23/db_efficiency_plan.md` mentions these legacy file names and path strings as migration work, but not this confirmed control-plane project-binding defect.
8. Recommended follow-up
   - Replace all `_PROJECTS_DIR`-based fallback paths in `_init_v50_modules()` with `self.current_project.paths.root / "logs" / ...`.
   - Add a regression test that binds `current_project.paths.root` to a non-default location and confirms fallback migration reads from that bound root only.

---

## Coverage Gap Log

| Topic | Current status | Needed evidence |
|------|----------------|-----------------|
| `_ignite_quad_cache_system()` | Not retained as a new finding. Still appears to be dead code, but this was already observed in `docs/2026-02-28/TF-31-style-pipeline-audit.md:134`. | If reopened later, prove a current bootstrap caller expects cache injection and does not get it. |
| `_load_v50_history()` | No-op stub at `main_a.py:2026-2038`; no required test demonstrates a real restore contract. | Clarify whether history restore is intentionally removed or still expected. |
| Bootstrap regression coverage | Missing for `_attach_agents()`, `_init_core_agents()`, `_init_v50_modules()`, and JSON fallback migration binding. | Add direct bootstrap tests instead of only downstream orchestrator tests. |

## Closeout

- PASS1 candidate findings: 4
- PASS2 removed as duplicate/weakly-proven: 1
- Final retained findings: 3
- Final summary: `PASS1 4 -> PASS2 remove 1 -> FINAL 3`
