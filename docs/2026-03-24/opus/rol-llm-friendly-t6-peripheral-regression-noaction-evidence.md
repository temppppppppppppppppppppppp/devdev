Date: 2026-03-24
Document Type: evidence manifest (T6 lane)
Parent Report: `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction.md`

## Raw Path Inventory

### scripts/ (49 .py + 1 .ps1)

#### Ops Validators (8)
- `scripts/ops_validator.py` (306 LOC) — queue-state & docs metadata validation
- `scripts/check_utf8_hygiene.py` (210 LOC) — UTF-8 mojibake detection
- `scripts/mojibake_global_survey.py` (387 LOC) — global corruption detection
- `scripts/validate_deep_global_survey_bundle.py` (148 LOC) — deep survey structure validation
- `scripts/audit_bi_5pass.py` (367 LOC) — generic BI 5-pass audit
- `scripts/audit_wuxia_bi_5pass.py` (296 LOC) — wuxia BI 5-pass audit
- `scripts/audit_narrative_bi.py` (84 LOC) — BI audit router
- `scripts/validate_manual_sweep.py` (310 LOC) — manual sweep findings validation

#### Smoke/Canary Runners (6)
- `scripts/run_stage2_smoke.py` (418 LOC)
- `scripts/run_stage3_smoke.py` (234 LOC)
- `scripts/run_stage4_smoke.py` (272 LOC)
- `scripts/run_stage34_canary.py` (364 LOC)
- `scripts/run_stage4_canary.py` (220 LOC)
- `scripts/e2e_menu_smoke.ps1` (251 LOC) — PowerShell HTTP menu simulator

#### Narrative-Pipeline Tools (7)
- `scripts/narrative_router.py` (112 LOC)
- `scripts/build_narrative_bi.py` (84 LOC)
- `scripts/narrative_tr_batch.py` (74 LOC)
- `scripts/tr_batch_harness.py` (1,406 LOC)
- `scripts/build_bi_from_phase0_and_tr.py` (566 LOC)
- `scripts/build_wuxia_bi_from_phase0_and_tr.py` (477 LOC)
- `scripts/process_and_audit_tr_bi_loop.py` (279 LOC)

#### Data Builders (11)
- `scripts/build_chaebol_allowance_zero_assets.py` (962 LOC) — story-specific
- `scripts/build_fallen_prince_buys_joseon_assets.py` (1,298 LOC) — story-specific
- `scripts/investment_corpus_support.py` (2,099 LOC) — EPUB extraction library
- `scripts/build_investment_epub_corpus.py` (50 LOC)
- `scripts/build_investment_gemini_jsonl.py` (90 LOC)
- `scripts/build_investment_pseudonymized_corpus.py` (54 LOC)
- `scripts/build_title_style_control_dataset.py` (112 LOC)
- `scripts/extract_manuscript_samples.py` (167 LOC)
- `scripts/generate_tr_bibles.py` (496 LOC)
- `scripts/backfill_quality_sidecars.py` (70 LOC)
- `scripts/generate_stagewise_manuscript_truth_report.py` (40 LOC)

#### Ops Support/Utilities (8)
- `scripts/ops_support.py` (211 LOC) — shared metadata/path utilities
- `scripts/sync_temp_queue_state.py` (118 LOC)
- `scripts/build_execution_roadmap.py` (150 LOC)
- `scripts/generate_evidence_manifest.py` (102 LOC)
- `scripts/populate_process_health_scorecard.py` (169 LOC)
- `scripts/run_stale_reference_sweep.py` (106 LOC)
- `scripts/run_pytest_lowmem.py` (453 LOC)
- `scripts/run_auto_frontier_lag_harness.py` (972 LOC)

#### Smoke Infrastructure (2)
- `scripts/smoke_fixture_contract.py` (8 LOC) — naming contract
- `scripts/prepare_smoke_fixture.py` (47 LOC) — fixture copier
- `scripts/regression_validation_tiers.py` (84 LOC) — tier constants

#### Stale/Orphaned (4)
- `scripts/tf_c1_patch.py` (99 LOC) — hard-coded path to `C:\Users\wjjo\Desktop\`, one-shot
- `scripts/render_later_hardening_autopilot.py` (353 LOC) — TF remediation artifact
- `scripts/repair_tr_korean_utf8.py` (711 LOC) — initial UTF-8 repair, 8 hard-coded stories
- `scripts/gemini_cover_title_edit.py` (249 LOC) — cover art utility, intentionally isolated

### tests/ (384 .py files)

| Directory | File Count | Purpose |
|---|---|---|
| root | 351 | Unit tests (stage, agent, validation, sweep, lane, wave) |
| chaos/ | 8 | Chaos engineering / failure mode |
| e2e/ | 10 | End-to-end with real DB + mock LLM |
| integration/ | 3 | DI chain wiring verification |
| property/ | 5 | Hypothesis property-based tests |
| stage3_isolated_test/ | 3 tests + 6 artifact files | Stage 3 isolated + stale JSON |
| stage4_v2_test/ | 2 tests + project/results dirs | Stage 4 v2 + stale artifacts |

### UI/ (binary assets)
- Total size: 337 MB
- Code files: 0
- Contents: Character Generator 2.0 (.exe + .zip), Fantasy Battlers (.zip), Fungus Cave tileset (.zip), sprite grid PNGs, char_preview/ directory

### geuldobi-desktop/ (Electron app)

| File | Lines | Category |
|---|---|---|
| src/main.js | 1,237 | Main process |
| src/preload.js | 92 | Context bridge |
| src/desktop_control_plane_contract.js | 98 | IPC SSOT |
| src/desktop_bridge_client.js | 62 | Bridge accessors |
| src/index.html | 10,082 | UI shell |
| src/quality_page_bootstrap.js | 916 | Quality dashboard |
| src/quality_react_helpers.js | 769 | React helpers |
| src/quality_react_runtime.js | 30 | React runtime |
| src/renderer_state_bootstrap.js | 661 | State machine |
| src/console_relay.js | 56 | Console capture |
| src/splash/* | ~280 | Splash screen |
| DESKTOP-GUIDE.md | 367 | Documentation |
| package.json | v1.5.7 | Config (Electron ^40.8.0, React ^18.3.1) |

Stale files:
- `temp-electron-loadcheck.js` (Mar 12)
- `temp-electron-paths.js` (Mar 12)
- `src/sprite_test.html` (Mar 8)

### docs/implementation/ (47 files)

| Category | Count | Status |
|---|---|---|
| Harnesses | 14 | All active, all dated 2026-03-14/15 |
| Templates | 10 | All active |
| Contracts (md) | 6 | All active |
| Contracts (json/yaml) | 6 | All active |
| Schemas/data | 4 | All active |
| Reference/guide docs | 5 | 2 missing metadata (risk-approval-checklist, release-gate-v1) |
| Code files (stale) | 2 | `input_route.py`, `prompt_broker.py` — superseded |
| Samples subdir | 1 | `samples/risk-approval-log.samples.jsonl` |

## Stale Authority Evidence

### docs/implementation/prompt_broker.py vs modules/api/prompt_broker.py
- `docs/implementation/` version: 182 LOC, uses `typing.Optional`, `typing.List`, `datetime.timezone`
- `modules/api/` version: 205 LOC, uses `collections.abc.Callable`, `datetime.UTC`, PEP 604 unions, extra `prompt_text` field
- Divergence: modernized types + added fields in modules/api/ version
- Only references to docs/implementation/ version: `docs/2026-03-06/handoff/T5-handoff.md`, `spikes/bridge/result.md`

### docs/implementation/input_route.py vs modules/api/bridge_server.py
- `docs/implementation/input_route.py`: standalone FastAPI router, 78 LOC
- `modules/api/bridge_server.py:2168-2170`: route now inline (`@app.post("/run/{run_id}/input")`)
- `input_route.py` L11 contains misleading self-referential import comment
- Only references: same stale handoff docs

### scripts/tf_c1_patch.py
- L7: `target = r"C:\Users\wjjo\Desktop\글도비\modules\core\db_manager.py"` — non-portable hard-coded path
- Purpose: one-shot regex patch for transaction nesting fix
- Not referenced from any test, harness, or AGENTS.md

## Active Temp Queue State (read-only)
```json
{
  "queue_mode": "single",
  "active_item_count": 1,
  "items": [{
    "topic": "genre-contamination-guardrail",
    "status": "pending",
    "canonical_path": "docs/2026-03-24/genre-contamination-guardrail-execution-ssot.md"
  }]
}
```
Not modified per master order Section 3 constraints.
