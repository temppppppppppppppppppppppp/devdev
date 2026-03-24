Date: 2026-03-24
Status: final (3-pass audited)
Document Type: LLM-friendliness lane survey report
Lane: T1 — Navigation / Entry / Reading Order
Canonical Path: `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry.md`
Evidence Path: `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry-evidence.md`
Master Order: `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`

Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: tracked stage4/state/writer surfaces, docs/temp/queue-state.json, docs/2026-03-23/console.txt, many project artifacts deleted, new docs/2026-03-24/ and stage4 immutable-fact files`

## 1. Executive Summary

Navigation and entry routing for this codebase is **LLM-ready with bounded residual gaps**.

A cold LLM can find the correct entry point (`main_a.py` L4771 `SovereignApp().boot()`), follow the stage pipeline (`Stage 0 -> 2 -> 3 -> 4`), and identify the authoritative orchestrator for each stage — all within the first 2-3 file hops.

The orientation pack (`docs/2026-03-23/llm-codebase-orientation-pack.md`) remains **largely accurate** for the core production pipeline. Post-survey execution SSOT follow-ups (COMPAT markers, menu remap comments, section dividers) were realized and verified.

However, three navigation gaps remain:

1. **`modules/api/` surface entirely absent from orientation pack** — 7 files including `bridge_server.py` (2,372 LOC) are invisible to an LLM using the orientation pack as its starting map.
2. **`main_a.py` SovereignApp (4,781 LOC) lacks a top-of-class ToC** — the first section divider appears at L926, leaving ~580 lines of init/service/bootstrap with no navigation aid.
3. **`_stage_4_v2_chief_writer()` in `main_a.py` L3780 performs lazy init authority** (StateTracker/WorldState/FactLedger/DI injection) before delegating to the orchestrator — its name suggests a thin delegate but it is a critical bootstrap gateway.

Key verdicts:
- **Navigation-ready for this lane: yes** (with 3 bounded gaps)
- **Cheap-fix-first verdict: yes** (all top gaps are doc-only or comment-only)
- **Boundary-refactor can wait: yes**
- **Top 3 highest-ROI quick wins:**
  1. Add `modules/api/` section to orientation pack (doc-only)
  2. Add SovereignApp class-level ToC comment in `main_a.py` (comment-only)
  3. Add authority note to `_stage_4_v2_chief_writer()` docstring (comment-only)

## 2. Included Coverage / Exclusions

### Included (Primary Scope)
| File | Lines | Role |
|---|---|---|
| `main_a.py` | 4,781 | Entry point, SovereignApp, operator menu, stage routing |
| `modules/core/stage01_helpers.py` | 1,023 | Stage 0/1 capsule |
| `modules/core/stage2_orchestrator.py` | 1,731 | Stage 2 Arc orchestration |
| `modules/core/stage3_orchestrator.py` | 2,774 | Stage 3 Blueprint orchestration |
| `modules/core/stage4_orchestrator.py` | 2,414 | Stage 4 Writing orchestration |
| `modules/api/bridge_server.py` | 2,372 | FastAPI desktop bridge |
| `modules/api/process_runner.py` | 808 | Subprocess wrapper |
| `modules/api/control_plane_contract.py` | 92 | API authority contract |
| `modules/api/prompt_broker.py` | 205 | Mode B prompt broker |
| `modules/api/run_validator.py` | 95 | Run request validation |
| `modules/api/risk_approval.py` | 214 | Risk gate |
| `modules/api/prompt_classifier.py` | 172 | Prompt classification |
| `modules/api/__init__.py` | 13 | Package init |
| `docs/2026-03-23/llm-codebase-orientation-pack.md` | 284 | Navigation map (drift target) |

### Excluded
- Stage 4 runtime files (T2 lane)
- Writer/prompt/context files (T3 lane)
- Validation/contract files (T4 lane)
- Persistence/observability files (T5 lane)
- Peripheral/test/governance files (T6 lane)

## 3. Current Read Order or Ownership Map

### 3.1 Orientation Pack Read Order — Live Verification

| # | Orientation Pack Entry | Live Status | Drift |
|---|---|---|---|
| 1 | `main_a.py` — operator menu, stage entry routing | **Accurate** | No drift |
| 2 | `stage01_helpers.py` — Stage 0 capsule | **Accurate** | No drift |
| 3 | `stage2_orchestrator.py` — Stage 2 owner | **Accurate** | No drift |
| 4 | `stage3_orchestrator.py` — Stage 3 owner | **Accurate** | No drift |
| 5 | `stage4_orchestrator.py` — Stage 4 owner shell | **Accurate** | No drift |
| 6 | Stage 4 runtime files | Accurate | (T2 lane) |
| 7 | Shared domain runtimes | Accurate | (T3 lane) |
| 8 | Persistence and state | Accurate | (T5 lane) |

**Verdict**: The core production pipeline reading order has not drifted since the orientation pack was written.

### 3.2 Orientation Pack Coverage Gap — `modules/api/`

The orientation pack has **zero mentions** of `modules/api/`, `bridge_server`, or `process_runner`. This is a significant navigation gap because:
- `bridge_server.py` (2,372 LOC) is the **only FastAPI entry** for the desktop/Electron app
- `process_runner.py` (808 LOC) wraps `main_a.py` as a subprocess for headless operation
- `control_plane_contract.py` defines the **authority path** from desktop to engine
- This surface is the **second entry path** into the pipeline (after direct `main_a.py` console)

### 3.3 Main Entry Flow Verification

```
main_a.py L4771: SovereignApp().boot()
  └─ boot() L1373: _select_genre() → _select_project() → _bind → _restore → _run_main_process()
      └─ _run_main_process() L2145: menu loop
          └─ _dispatch_main_process_choice() L2217:
              0 → _phase_0_recovery() → stage01_helpers
              1 → _stage_1_volumes() → stage01_helpers
              2 → _stage_2_arcs() L2891 → stage2_orchestrator
              3 → _stage_3_batch_blueprinting() L3148 → stage3_orchestrator
              4 → _stage_4_v2_chief_writer() L3780 → [lazy init gateway] → stage4_orchestrator
              5 → _shutdown_app() → exit
              6 → _one_stop_pipeline() L4682 → Stage 2→3→4 sequential
              7 → _frontier_lag_pipeline() → similar to 6 with lag
```

This flow is clear and traceable. No hidden or confusing routing.

### 3.4 API/Desktop Entry Flow

```
modules/api/bridge_server.py: FastAPI app
  POST /run → validate_run_request() → RiskApprovalGate → ProcessRunner.start()
    └─ ProcessRunner spawns main_a.py as subprocess
  POST /stop → ProcessRunner.stop()
  GET /status → runner state
  WS /events → real-time event stream
```

This flow is well-documented inside `bridge_server.py`'s module docstring (L1-16), but invisible from the orientation pack.

## 4. Top Hotspots

| # | File:Line | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|
| H-1 | orientation pack §2-§7 | Navigation | **P1** | `modules/api/` surface (7 files, 3,971 LOC total) not mentioned at all. An LLM following the pack's reading order would never discover the desktop bridge path. | doc-only |
| H-2 | `main_a.py` L346-925 | Navigation | **P1** | SovereignApp class body has no ToC. First section divider at L926. 580 lines of init, services, bootstrap, and helper methods without structural guidance. | comment-only |
| H-3 | `main_a.py` L3780-3852 | Authority | **P1** | `_stage_4_v2_chief_writer()` docstring says "Stage4Orchestrator 위임" but the method performs ~70 lines of StateTracker/WorldState/FactLedger lazy init + DI context injection before delegation. Name and docstring understate its authority role. | comment-only |
| H-4 | `main_a.py` L2948-3065 | Navigation | **P2** | ~15 StateService thin delegates lack `[COMPAT]` markers. They have `[Phase 4B-3] thin delegate` comments but the pattern is inconsistent with Stage 2 delegates (which use `[COMPAT]`). | comment-only |
| H-5 | `stage2_orchestrator.py` L78-137 | Navigation | **P2** | Stage2Orchestrator init block has 3 lazy-init sub-modules (`_validation_pipeline`, `_preflight`, `_finalizer`) but no section comment grouping the property block. | comment-only |
| H-6 | `bridge_server.py` L1-2372 | Navigation | **P2** | Large file (2,372 LOC) with well-structured endpoints but no method-group ToC. Key endpoints (`/run`, `/stop`, `/status`, `/events`) are discoverable but require scrolling. | comment-only |

## 5. Top Quick Wins

| # | Target | Fix Type | Action | ROI |
|---|---|---|---|---|
| QW-1 | `docs/2026-03-23/llm-codebase-orientation-pack.md` §2 or new §8 | doc-only | Add `modules/api/` reading order entry: `bridge_server.py` (FastAPI desktop bridge), `process_runner.py` (subprocess wrapper), `control_plane_contract.py` (authority path contract). Note that this is the second entry path into the pipeline. | **High** — closes the largest navigation gap |
| QW-2 | `main_a.py` L346 | comment-only | Add class-level ToC comment immediately after `class SovereignApp:` line, e.g.: `# --- ToC: __init__ L349 | boot L1373 | main_menu L2145 | Stage 0/1 delegates L2780 | Stage 2 entry L2891 | Stage 3 entry L3148 | Stage 4 entry L3780 | OneStop L4682 | Shutdown L2755 ---` | **High** — eliminates blind scrolling in the largest file |
| QW-3 | `main_a.py` L3780-3783 | comment-only | Expand docstring to: `"""[V64.P3] Stage 4 V2 Chief Writer — LAZY INIT GATEWAY + Stage4Orchestrator 위임. This method initializes StateTracker, WorldState, FactLedger, and Stage4Context (DI injection) before delegating to the orchestrator. It is not a thin delegate."""` | **High** — prevents LLM from skipping this method's authority role |
| QW-4 | `main_a.py` L2948-3065 | comment-only | Add `[COMPAT]` or `[FACADE]` markers to StateService thin delegates for consistency with Stage 2 delegates at L2924-2945. | Medium — improves pattern consistency |
| QW-5 | `bridge_server.py` top of file (after module docstring) | comment-only | Add endpoint ToC comment: `# --- Endpoints: POST /run L___, POST /stop L___, GET /status L___, WS /events L___, POST /run/{run_id}/input L___, GET /quality/* L___ ---` | Medium — speeds up endpoint discovery |
| QW-6 | orientation pack §4.1 | doc-only | Add note: `_stage_4_v2_chief_writer() in main_a.py is a lazy-init gateway, not a thin delegate. It bootstraps StateTracker/WorldState/FactLedger and injects Stage4Context before delegating.` | Medium — prevents authority confusion |
| QW-7 | `stage2_orchestrator.py` L85-137 | comment-only | Add grouping comment before lazy-init property block: `# --- Lazy-init sub-modules: validation_pipeline, preflight, finalizer ---` | Low — minor readability |

**Comment/doc/observability composition**: 7/7 items are comment-only or doc-only (100% > required 50%).

## 6. Deferred Refactor Candidates

| # | Target | Description | Fix Type | Rationale |
|---|---|---|---|---|
| DR-1 | `main_a.py` L346-4781 | SovereignApp (4,435 LOC class body) still carries ~40 thin delegates and ~20 facade methods that could be further pruned or consolidated. Not urgent: they are individually labeled and not hiding authority. | boundary-refactor (defer: long-term) | Method count pressure is cosmetic rather than comprehension-blocking. The delegates are clearly labeled after the post-survey follow-up. |
| DR-2 | `main_a.py` L3558-3778 | Narrative summary system (~220 LOC) mixes LLM call, text assembly, and persistence in one method family. Could be extracted to a dedicated runtime module. | boundary-refactor (defer: long-term) | Self-contained family, no authority confusion. Extraction is clean but not navigation-critical. |
| DR-3 | `bridge_server.py` L1-2372 | Large single-file API server. Could be split into route modules. Well-structured internally with endpoint docstrings. | boundary-refactor (defer: long-term) | The file has a clear module docstring and endpoint pattern. Navigation cost is bounded by endpoint-level search. |

## 7. No-Action / Settled Areas

| Area | Reason |
|---|---|
| `stage01_helpers.py` L529-536 (menu remap) | **Resolved** — clear comment now present: `# Menu remap: show_menu returns 4 (style analysis) / 5 (work guard), but handler table uses 5 / 6 because slot 4 = block extension.` |
| `main_a.py` L2924-2945 (Stage 2 COMPAT delegates) | **Resolved** — `[V64.P3][COMPAT] thin delegate — authority is Stage2Orchestrator` on all 5 delegates. |
| `main_a.py` L2755-2778 (shutdown sequence) | **Resolved** — Phase 1/2/3/4 comments now present from post-survey follow-up. |
| `main_a.py` `\uXXXX` unicode escapes | **Resolved** — grep confirms zero `\uXXXX` escape patterns remain. Korean keywords are in literal form. |
| `stage4_orchestrator.py` L60-460 (dataclass preamble) | **Settled** — has `# ── Dataclass family:` grouping headers after post-survey follow-up. |
| `stage3_orchestrator.py` section dividers | **Settled** — `─────` dividers at 6 section boundaries (L544, 696, 761, 877, 1010, 1642). |
| `stage2_orchestrator.py` section dividers | **Settled** — `═══` dividers at L885, L1676. |
| `control_plane_contract.py` | **Settled** — excellent authority documentation. Docstring at L1-15 maps the full authority path from desktop to engine. |
| `process_runner.py` | **Settled** — clear docstring (L1-15) with role, usage, and stdin sequence. |
| `prompt_broker.py`, `run_validator.py`, `risk_approval.py`, `prompt_classifier.py` | **Settled** — small focused files (95-214 LOC each), self-explanatory. |
| Boot sequence (`main_a.py` L1-100) | **Settled** — bootstrap functions are clearly commented with version tags. |
| Main menu (`main_a.py` L2188-2203) | **Settled** — explicit key→stage mapping with status indicators. |

## 8. Cross-Lane Handoff Notes

| To Lane | Note |
|---|---|
| T2 (Stage 4 Authority) | H-3 (lazy init gateway) affects T2's authority chain understanding. `_stage_4_v2_chief_writer()` performs DI injection that T2 needs to know about as the upstream source of `Stage4Context`. |
| T3 (Writer/Context) | The DI context injection at `main_a.py` L3848 (`Stage4Context.from_app(self)`) is the single point where all Stage 4 context is assembled. T3 should verify context reception clarity from this point. |
| T5 (Persistence/Observability) | `bridge_server.py` has its own observability surface (`control-plane-provenance.jsonl`, `/quality/*` endpoints) that T5 should check for sink ownership clarity. |
| T6 (Peripheral/Stale) | `modules/api/` absence from orientation pack is also relevant to T6's stale-authority sweep. |

## 9. Confidence And Limits

**Confidence: 96%**

Basis:
- All files in primary scope were directly inspected against live workspace state.
- Orientation pack reading order was verified file-by-file against live code.
- Prior survey findings (H7 unicode, H14 menu remap, H16 COMPAT markers) were verified as resolved.
- The `modules/api/` gap is clear and unambiguous.
- Section divider presence was verified by pattern grep across all orchestrator files.

Limits:
- `main_a.py` internal method interactions were sampled, not exhaustively traced (4,781 lines).
- `bridge_server.py` endpoints were checked at module docstring level; deep route handler logic was not fully traced (T4/T5 scope).
- This survey is static-only. No fresh run was executed.

## 10. 3-Pass Audit Record

### Pass 1 — Structure and Scope
- All 3 T1 lane questions answered (entry clarity, orientation pack drift, thin delegate/compat risk).
- All P0/P1 items have `file:line` anchors.
- All recommendations have fix types.
- Quick wins: 7 items, 100% comment-only/doc-only (exceeds 50% threshold).
- Deferred refactors: 3 items, all marked `defer: long-term`.
- PASS

### Pass 2 — Evidence and Consistency
- Orientation pack reading order verified against live files: no stale path, no renamed file.
- Post-survey SSOT follow-up (COMPAT markers, menu remap, shutdown comments, section dividers) verified as realized.
- `\uXXXX` escape removal verified by pattern grep (0 matches).
- `modules/api/` gap verified by orientation pack text search (0 mentions of api/bridge/process_runner).
- H-3 lazy init gateway verified by direct code read of L3780-3852.
- No contradiction between findings and prior survey report.
- PASS

### Pass 3 — Actionability and Readability
- Quick wins are actionable without opening refactor waves.
- No-action list prevents re-investigation of resolved items.
- Cross-lane handoff notes are specific and bounded.
- Report follows mandatory structure from master order.
- PASS

### Confidence Gate
- Estimated confidence: 96%
- Threshold: 95%
- Gate: **PASS** — status set to `final`.
