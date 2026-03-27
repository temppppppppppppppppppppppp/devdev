Date: 2026-03-27
Status: final
Document Type: T1 lane report (parallel static survey)
Canonical Path: `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry.md`
Master Order: `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`
Evidence Path: `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry-evidence.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked llm_router/provider/context/validator surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked multi-provider docs, fact docs, anthropic_vertex provider scaffolding/tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

The Navigation / Entry / Read Order lane is **navigable but mixed on gimmick elegance**. A cold LLM can identify the starting file (`main_a.py`), follow the stage routing chain, and reach the correct orchestrator within 2-3 hops. The orientation pack (`llm-codebase-orientation-pack.md`) remains structurally valid — all 31 listed files exist at their declared paths and the authority map is accurate.

However, several gimmicks degrade navigation confidence:

- **Stage 4 lazy-init gateway** in `main_a.py` performs critical initialization (StateTracker, WorldState, FactLedger) with non-blocking failures — the downstream orchestrator silently receives `None` for any failed component. This is a design decision, not a bug, but it is not locally obvious.
- **Stage 3 implicit state transfer** assigns `state_tracker`, `world_state`, and `fact_ledger` to `self.app` from within the orchestrator, making the orchestrator a hidden producer of app-level state.
- **Stage 2 StateTracker sync-back** copies the orchestrator's state tracker back to the app after Stage 2 completes — a subtle reverse-flow mutation.
- **Dispatch silent fallthrough** in `main_a.py:2257` silently loops on invalid menu choices.
- **Credential injection** in `process_runner.py` passes API keys through environment variables with no audit trail within the module.
- **Orientation pack omissions**: 3 Stage 4 runtime files (`stage4_reject_runtime.py`, `stage4_retry_runtime.py`, `stage4_outcome_runtime.py`) and the entire provider infrastructure layer (`llm_router.py`, `llm_provider.py`, `models_config.py`, `modules/core/providers/`) are missing from the reading order.

None of these findings require immediate code changes. Most are addressable with comment-only or doc-only fixes.

**Navigation-ready for this lane: yes**
**Cheap-fix-first verdict: yes**
**Gimmick-elegance verdict: mixed**
**Boundary-refactor can wait: yes**

**Top 3 highest-ROI quick wins:**
1. Refresh orientation pack reading order to include missing Stage 4 runtimes and provider layer (doc-only)
2. Add a comment block at `main_a.py:3794` explaining the Stage 4 lazy-init gateway contract and non-blocking failure semantics (comment-only)
3. Add a comment at `stage3_orchestrator.py:701` explaining the implicit state transfer to `self.app` and why it exists (comment-only)

## 2. Included Coverage / Exclusions

### Included

| File | Lines | Role |
|------|-------|------|
| `main_a.py` | 4,808 | Operator entry shell, stage routing, shutdown |
| `modules/core/stage01_helpers.py` | 1,029 | Stage 0/1 thin wrapper |
| `modules/core/stage2_orchestrator.py` | 1,731 | Stage 2 owner shell + DI context |
| `modules/core/stage3_orchestrator.py` | 2,851 | Stage 3 owner shell + DI context + implicit state transfer |
| `modules/core/stage4_orchestrator.py` | 2,414 | Stage 4 owner shell + DI context + 3 lazy sub-modules |
| `modules/api/bridge_server.py` | 2,372 | FastAPI HTTP/WS entry point |
| `modules/api/process_runner.py` | 823 | Subprocess lifecycle + credential injection |
| `modules/api/control_plane_contract.py` | 92 | Authority path contract |
| `modules/api/run_validator.py` | 95 | Request validation gate |
| `modules/api/risk_approval.py` | 214 | Risk approval gate (dual-control) |
| `modules/api/prompt_broker.py` | 205 | Mode B interactive prompt lifecycle |
| `modules/api/prompt_classifier.py` | 172 | Stdout prompt parser |
| `modules/api/__init__.py` | 13 | Public module interface |
| `docs/2026-03-23/llm-codebase-orientation-pack.md` | 306 | Navigation map (drift-checked) |

### Excluded

- Stage 2/3/4 downstream runtimes (T3/T4 scope)
- Provider/router/backend elegance (T2 scope)
- Writer/prompt/context injection (T4 scope)
- Fact authority/genre gimmicks (T5 scope)
- Observability/peripheral sweep (T6 scope)
- All dirty tracked files inspected for navigation context only, not for patch candidacy

## 3. Current Read Order / Ownership / Gimmick Map

### 3.1 Cold-Start Reading Order (Verified Against Live Workspace)

A cold LLM entering the codebase should follow this path:

1. **`main_a.py:4798`** — `if __name__ == "__main__"`: `SovereignApp().boot()`
2. **`main_a.py:1387`** — `boot()`: genre selection, project binding, `_run_main_process()`
3. **`main_a.py:2159`** — `_run_main_process()`: infinite menu loop
4. **`main_a.py:2231`** — `_dispatch_main_process_choice()`: stage routing dispatch
5. **Stage 0/1** → `main_a.py:2796/2808` (thin delegates) → `stage01_helpers.py`
6. **Stage 2** → `main_a.py:2907` → `Stage2Orchestrator.stage_2_arcs_async_logic()`
7. **Stage 3** → `main_a.py:3164` (thin delegate) → `Stage3Orchestrator.stage_3_batch_blueprinting()`
8. **Stage 4** → `main_a.py:3794` (lazy-init gateway, NOT thin) → `Stage4Orchestrator.stage_4_v2_chief_writer()`
9. **Shutdown** → `main_a.py:2771`: 4-phase orderly shutdown
10. **API entry** → `bridge_server.py:2057` (`POST /run`) → `process_runner.py` → subprocess `main_a.py`

### 3.2 Ownership Map

| Owner | File | Pattern | DI Context |
|-------|------|---------|------------|
| SovereignApp | `main_a.py` | Entry routing shell | N/A (is the app) |
| Stage01Helpers | `stage01_helpers.py` | Thin wrapper (no DI) | None — uses `self.app` directly |
| Stage2Orchestrator | `stage2_orchestrator.py` | Owner shell + 3 lazy sub-modules | `Stage2Context` [Phase 4C-3] |
| Stage3Orchestrator | `stage3_orchestrator.py` | Owner shell + implicit state transfer | `Stage3Context` [Phase 4C-4] |
| Stage4Orchestrator | `stage4_orchestrator.py` | Owner shell + 3 lazy + 1 eager sub-modules | `Stage4Context` [Phase 4C-2a] |
| BridgeServer | `bridge_server.py` | FastAPI lifespan + routes | `app.state` singletons |
| ProcessRunner | `process_runner.py` | Subprocess lifecycle | Environment dict |

### 3.3 Gimmick Map

| ID | Gimmick | Location | Elegant? | Reason |
|----|---------|----------|----------|--------|
| G-1 | Dispatch silent fallthrough | `main_a.py:2257` | Inelegant | Invalid choice silently loops with no feedback. Not annotated. |
| G-2 | Stage 4 lazy-init gateway (non-blocking failures) | `main_a.py:3794-3879` | Mixed | Design intent is clear (non-blocking, marked `(비차단)`), but the downstream consequence (orchestrator receives `None`) is not documented at the call site. |
| G-3 | Stage 3 implicit state transfer to app | `stage3_orchestrator.py:701-761` | Inelegant | Orchestrator assigns `state_tracker`, `world_state`, `fact_ledger` to `self.app`. This is a hidden producer pattern — the orchestrator mutates the app. Comments exist but the reason is not stated. |
| G-4 | Stage 2 StateTracker sync-back | `main_a.py:2930-2935` | Mixed | After Stage 2, state tracker is pulled from orchestrator context back to app. Comment exists but the why is implicit. |
| G-5 | Credential injection without module-level audit | `process_runner.py:780-823` | Mixed | API keys injected as env vars. Functional and localized in `_build_env()`, but no logging or masking within this module. Audit trail depends on upstream bridge_server events. |
| G-6 | Legacy model map fallback | `main_a.py:1424` | Inelegant | Falls back to V20 config silently if `models.yaml` absent or empty. |
| G-7 | Arc calculation multi-key fallback | `main_a.py:2838-2870` | Mixed | Tries 4 field names (`ep_start`, `start_ep`, `episode_start`, `start_episode`) silently. Defensive but not annotated. |
| G-8 | Mode A/B auto-selection | `process_runner.py:310` | Elegant | Clean: `"B" if key in MODE_B_KEYS else "A"`. One line, explicit, overridable. |
| G-9 | Shutdown exception silent-pass | `main_a.py:2280` | Elegant | Correctly logs and continues to `sys.exit(1)`. Labeled `[SilentPass:Shutdown]`. |
| G-10 | DI context lazy-init with cache invalidation | `stage4_orchestrator.py:493-496` | Elegant | When `ctx` is reassigned, all lazy sub-modules are cleared. Explicit and localized. |
| G-11 | `_god1_*` authority channel | `stage4_interview_round.py:2270` / `stage4_director_runtime.py:102` | Inelegant | 7 round-local attributes passed by instance mutation. Predates the runtime split. Both sides carry ownership comments, but the mechanism itself is a hidden state channel. (Noted in orientation pack §4.5.) |
| G-12 | Eager outcome_runtime instantiation | `stage4_orchestrator.py:479` | Mixed | Breaks the lazy-init pattern for one sub-module without annotation explaining why. |

## 4. Top Hotspots

### P1. Stage 4 lazy-init gateway — non-blocking failure contract unclear at call site
- **File:** `main_a.py:3794-3879`
- **Axis:** Authority, Gimmick Elegance
- **Issue:** StateTracker, WorldState, and FactLedger are initialized with `except Exception` → `None` assignments. The Stage 4 orchestrator receives whatever succeeded, with no contract stating what happens when components are `None`. A cold LLM could reasonably assume these are always present.
- **Fix type:** comment-only
- **Suggested:** Add a 3-line contract comment at L3794 stating: "Non-blocking init: downstream orchestrator must handle None for any of state_tracker/world_state/fact_ledger."

### P1. Stage 3 implicit state transfer to app
- **File:** `stage3_orchestrator.py:701-761`
- **Axis:** Authority, Gimmick Elegance
- **Issue:** Three `_init_*_if_needed()` methods assign domain state directly to `self.app`. The orchestrator is not just a consumer of app state — it is a hidden producer. The comments note what is happening but not why the pattern exists (DI context was added later but the init still writes to app).
- **Fix type:** comment-only
- **Suggested:** Add a 2-line note at L701: "These methods assign to self.app because Stage 4 also reads them from app. The DI context receives them via getattr(app, ...) after this point."

### P1. Orientation pack reading order omissions
- **File:** `docs/2026-03-23/llm-codebase-orientation-pack.md` §2
- **Axis:** Navigation
- **Issue:** 6 files relevant to the Stage 4 authority chain and the provider layer are missing from §2:
  - `stage4_reject_runtime.py` (retry/reject loop)
  - `stage4_retry_runtime.py` (retry/reject loop)
  - `stage4_outcome_runtime.py` (outcome processing)
  - `stage4_context_packets.py` (context pipeline — mentioned in §9 but not in §2)
  - `llm_router.py` / `llm_provider.py` / `models_config.py` / `modules/core/providers/` (provider layer)
- **Fix type:** doc-only
- **Suggested:** Add missing runtimes to §2.5 and provider layer as a new §2.10.

### P2. Dispatch silent fallthrough
- **File:** `main_a.py:2257`
- **Axis:** Local Readability, Gimmick Elegance
- **Issue:** If `choice` matches no case, `return True` silently re-shows the menu. No logging, no warning, no comment.
- **Fix type:** comment-only
- **Suggested:** Add `# [silent-fallthrough] unrecognized choice → re-show menu` at L2257.

### P2. Credential injection lacks module-level observability note
- **File:** `process_runner.py:780-823`
- **Axis:** Observability, Gimmick Elegance
- **Issue:** `_build_env()` injects 12+ environment variables (API keys, Vertex credentials, Anthropic key) with no audit log or masking note within this module. The audit trail exists upstream in bridge_server provenance logging, but a reader of `process_runner.py` alone cannot verify that.
- **Fix type:** comment-only
- **Suggested:** Add a docstring to `_build_env()`: "Credential injection — audit trail is in bridge_server provenance log, not in this module."

## 5. Top Quick Wins

| # | Location | Fix Type | Description |
|---|----------|----------|-------------|
| QW-1 | `llm-codebase-orientation-pack.md` §2 | doc-only | Add 3 missing Stage 4 runtimes (`reject`, `retry`, `outcome`) and `stage4_context_packets.py` to reading order. Add provider infrastructure as §2.10. |
| QW-2 | `main_a.py:3794` | comment-only | Add 3-line contract comment explaining Stage 4 lazy-init gateway: non-blocking failures, downstream `None` contract, why this is not a thin delegate. |
| QW-3 | `stage3_orchestrator.py:701` | comment-only | Add 2-line note explaining why `_init_*_if_needed()` assigns to `self.app` instead of only to `self.ctx`. |
| QW-4 | `main_a.py:2257` | comment-only | Add `# [silent-fallthrough] unrecognized choice → re-show menu` at the bare `return True`. |
| QW-5 | `process_runner.py:780` | comment-only | Add docstring to `_build_env()` noting credential injection scope and that audit trail is in bridge_server, not here. |
| QW-6 | `main_a.py:2930` | comment-only | Add 1-line note explaining Stage 2 StateTracker sync-back pattern: "Pull state_tracker from orchestrator ctx back to app for Stage 3/4 consumption." |
| QW-7 | `main_a.py:1424` | comment-only | Add `# [legacy-fallback] V20 config used only if models.yaml absent` at the legacy model map fallback. |

**Ratio check:** 6/7 = 86% are comment-only or doc-only. Passes the >50% rule.

## 6. Gimmick Elegance Judgment

### Elegant Gimmicks (well-localized, explicit, traceable)

- **G-8 Mode A/B auto-selection** (`process_runner.py:310`): One line, explicit, overridable.
- **G-9 Shutdown silent-pass** (`main_a.py:2280`): Correctly labeled `[SilentPass:Shutdown]`, logs before exit.
- **G-10 DI context cache invalidation** (`stage4_orchestrator.py:493`): Explicit, localized, self-documenting.

### Mixed Gimmicks (functional but not fully explicit)

- **G-2 Stage 4 lazy-init gateway**: Design intent is sound (non-blocking), but the downstream contract (`None` handling) is not stated at the call site.
- **G-4 Stage 2 sync-back**: Comment exists but lacks the "why."
- **G-5 Credential injection**: Localized in `_build_env()` but missing observability note.
- **G-7 Multi-key arc fallback**: Defensive but not annotated.
- **G-12 Eager outcome_runtime**: Breaks lazy pattern without explaining why.

### Inelegant Gimmicks (hidden, implicit, or undocumented)

- **G-1 Dispatch silent fallthrough**: No annotation, no logging on unrecognized input.
- **G-3 Stage 3 implicit state transfer**: Orchestrator mutates app without explicit contract. A cold reader would not expect an orchestrator to be a producer of app-level domain state.
- **G-6 Legacy model map fallback**: Silent fallback to V20 config with no annotation.
- **G-11 `_god1_*` channel**: 7 attributes passed by instance mutation across module boundaries. Already documented in orientation pack, but the mechanism itself is a hidden state channel by design.

### Overall Verdict

**Gimmick-elegance verdict: mixed**

The dominant pattern is that gimmicks are **functional and localized** (one owner, bounded scope), but **insufficiently annotated** for a cold LLM. Most inelegant gimmicks can be made understandable with comment-only or doc-only fixes, not refactoring.

## 7. Deferred Refactor Candidates

| # | Target | Scope | Rationale |
|---|--------|-------|-----------|
| DR-1 | `_god1_*` authority channel | `stage4_interview_round.py` / `stage4_director_runtime.py` | 7 attributes smuggled by instance mutation. Predates runtime split. Both sides carry comments. A clean fix would use a named data structure or a dedicated handoff method. Low urgency because the pattern is stable and documented in the orientation pack. |
| DR-2 | Stage 3 implicit state transfer | `stage3_orchestrator.py:701-761` | The orchestrator assigns domain state to `self.app`. A cleaner pattern would be a return value or explicit callback, but the current pattern is stable and only used by one caller (`main_a.py`). |
| DR-3 | Stage 4 lazy-init gateway extraction | `main_a.py:3794-3879` | This 85-line method is the only Stage entry that is NOT a thin delegate. Extracting it to a `stage4_bootstrap.py` or into the orchestrator itself would simplify `main_a.py`. Low urgency because the method is well-bounded and marked `[V64.P3]`. |

**Cap: 3/3. All marked long-term / defer.**

## 8. No-Action / Settled Areas

| Area | Status | Rationale |
|------|--------|-----------|
| Stage 0/1 thin delegates (`main_a.py:2796-2810`) | Settled | Clean delegation, marked `[Phase 4C-1b]`. No gimmick. |
| Stage 2 [COMPAT] stubs (`main_a.py:2939-2961`) | Settled | All 5 thin delegates are marked `[V64.P3][COMPAT]` with explicit authority note. |
| Shutdown 4-phase sequence (`main_a.py:2771-2794`) | Settled | Well-structured, each phase named, audit-logged, silent-pass labeled. |
| `control_plane_contract.py` | Settled | Pure data contract, 92 lines, clear authority path. |
| `run_validator.py` | Settled | Pure validation gate, 95 lines, no gimmick. |
| `risk_approval.py` | Settled | Dual-control enforcement, clean, self-contained. |
| `prompt_classifier.py` | Settled | Pure text parsing, no side effects, no gimmick. |
| `prompt_broker.py` | Settled | Isolated prompt lifecycle, mixed sync/async is documented. |
| `__init__.py` | Settled | Standard re-export module. |
| DI context `from_app()` pattern | Settled | Consistent across Stage 2/3/4. Well-understood. |
| SovereignApp init 3-phase structure | Settled | `_init_core_runtime_state`, `_init_session_and_service_runtime`, `_init_optional_module_slots` — clear and bounded. |
| Post-survey SSOT comment/doc follow-ups | Settled | All items from `llm-friendliness-post-survey-execution-ssot.md` were realized and closed. |

## 9. Cross-Lane Handoff Notes

### To T2 (Provider / Router / Backend-Family-Capability Elegance)
- `process_runner.py:780-823` injects Vertex and Anthropic credentials alongside Google API keys. T2 should verify whether the provider layer consumes these correctly.
- The orientation pack does not mention the provider infrastructure at all. T2 findings should feed into a pack refresh.
- `main_a.py:1424` legacy model map fallback (`_get_agent_model_map()`) may interact with the models.yaml schema that T2 is surveying.

### To T3 (Stage 4 Authority / Verdict / Retry Gimmicks)
- `_god1_*` authority channel (G-11) is a T1 navigation finding but a T3 authority finding. T3 should assess whether the 7-attribute smuggling creates verdict-tracing difficulty.
- Stage 4 lazy-init gateway (G-2) means T3 should verify how the Stage 4 runtime handles `None` state components.

### To T4 (Writer / Prompt / Context Injection Elegance)
- `stage4_context_packets.py` is missing from the orientation pack reading order. T4 should verify its role in the context pipeline.

### To T5 (Fact Authority / Genre Gimmick / Contract State)
- Stage 3 implicit state transfer (G-3) creates `state_tracker`, `world_state`, and `fact_ledger` on the app. T5 should verify whether the authority chain from these objects is clear.

### To T6 (Observability / Peripheral / No-Action Sweep)
- `bridge_server.py` provenance logging is the audit trail for credential injection — T6 should verify that it covers all injected keys.
- `main_a.py` shutdown sequence writes to audit/metrics/session sinks — T6 should verify sink coverage.

## 10. Confidence And Limits

**Confidence: 96%**

**Basis:**
- All 14 scope files were read and surveyed against the 6-axis model.
- All 31 orientation pack file references were verified against the live workspace.
- The `_god1_*` authority channel was verified at both producer and consumer sites.
- Gimmick judgments are grounded in specific `file:line` anchors.
- The prior post-survey execution SSOT closure was confirmed as settled.

**Limits:**
- `main_a.py` is 4,808 lines. Deep analysis focused on entry routing, stage dispatch, shutdown, and known gimmick sites. Helper families in the 3,000-4,000 line range (genre selection, narrative summary, reset/rollback) were checked for navigation relevance but not exhaustively surveyed.
- `bridge_server.py` is 2,372 lines. Route definitions and lifecycle were surveyed; WebSocket event-schema details were noted but not deeply traced.
- Dirty tracked files (`process_runner.py`, `stage3_orchestrator.py`, `stage4_context_builder.py`) were inspected for current navigation structure, not for uncommitted patch content.
- Provider infrastructure layer files (`llm_router.py`, `llm_provider.py`, `models_config.py`, `providers/`) were noted as orientation pack omissions but not deeply surveyed — that is T2 scope.

## 3-Pass Audit Record

- Pass 1
  - Document type fixed as `T1 lane report (parallel static survey)`.
  - Scope bounded to navigation/entry/read-order surfaces.
  - All 10 required sections present.
  - Fix-type priority rule applied: 6/7 quick wins are comment-only or doc-only.
  - Deferred refactor candidates capped at 3.
- Pass 2
  - File paths and line-number anchors verified against live workspace.
  - Orientation pack drift checked — all 31 files confirmed, 6 omissions identified.
  - No contradiction with AGENTS.md or harness rules.
  - Commit-state fields present and coherent.
  - Cross-lane handoff notes scoped to adjacent lanes only.
- Pass 3
  - Gimmick elegance verdicts grounded in the 5-criterion test from the master order.
  - No overreach into implementation planning.
  - Quick wins are actionable without behavior change.
  - Settled areas explicitly listed.
  - Final verdicts stated.
