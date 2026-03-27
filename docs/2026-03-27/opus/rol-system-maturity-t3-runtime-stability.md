Date: 2026-03-27
Status: final (3-pass audited)
Document Type: bounded static maturity-band survey (T3 lane)
Canonical Path: `docs/2026-03-27/opus/rol-system-maturity-t3-runtime-stability.md`
Temp Mirror Path: none
Source Order: `docs/2026-03-27/rol-system-maturity-banding-5terminal-master-order.md`
Source Survey Docs:
- `docs/2026-03-23/fresh-run-3pass-audit-report.md`
- `docs/2026-03-23/current-state-situation-survey-report.md`
- `docs/2026-03-27/chaebol-ent-empire-revival-canary-report.md`
- `docs/2026-03-27/chaebol-ent-empire-revival-stage-probe-report.md`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-20/TF-static-complexity-audit-v2.md`
Optional Evidence: `docs/2026-03-27/opus/rol-system-maturity-t3-runtime-stability-evidence.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: 30 tracked+untracked; runtime-lane hotspots: stage3_orchestrator, stage4_retry_runtime, stage4_context_builder, stage4_post_pass_runtime, base_agent, llm_router, anthropic_provider, vertex_provider, blocking_validator`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## 1. Executive Summary

The Runtime Stability / Retry / Recovery / Exercised Paths lane shows a system in **late stabilization with mixed early-optimization traits**. Exercised-path evidence is strong: the 2026-03-22 fresh run completed 213 LLM calls at 100% success with zero P0 regressions, and the 2026-03-27 revival canary/stage probe successfully admitted a new pair and proved Stage 0 through Stage 3 runtime acceptance. Retry, reject, recovery, and soft-failure surfaces are structurally mature with explicit dataclass-driven contracts, dedicated runtime modules, and multi-layered fallback chains.

However, two structural risks from the situation survey remain **unexercised**: Stage 3 REJECT sink fragility (single try/except over a large generation block) and Stage 4 post-pass bible_delta gap. The dirty worktree adds a third dimension: the multi-provider integration (Claude-on-Vertex) touches base_agent retry/continuation logic and the LLM router, adding new runtime surface that has no exercised-path proof yet.

**Verdict**: Supports late-stabilization (yes), supports early-optimization (mixed), supports not-yet-advancement (yes).

---

## 2. Included Coverage / Exclusions

### Included

| Surface | File(s) | Evidence Basis |
|---------|---------|----------------|
| Stage 2 orchestrator runtime | `stage2_orchestrator.py` | static read |
| Stage 3 orchestrator retry/reject | `stage3_orchestrator.py` | static read + fresh-run evidence |
| Stage 4 interview round loop | `stage4_orchestrator.py`, `stage4_interview_round.py` | static read + fresh-run evidence |
| Stage 4 retry runtime | `stage4_retry_runtime.py` | static read |
| Stage 4 reject runtime | `stage4_reject_runtime.py` | static read |
| Stage 4 director runtime | `stage4_director_runtime.py` | static read |
| Stage 4 post-processor | `stage4_post_processor.py` | static read |
| Stage 4 post-pass runtime | `stage4_post_pass_runtime.py` | static read |
| Soft failure system | `soft_failure.py` | static read |
| Session logger | `session_logger.py` | static read |
| Adaptive retry strategy | `adaptive_retry.py` | static read |
| BaseAgent ask/retry chain | `base_agent.py` | static read + dirty diff |
| LLM router + providers | `llm_router.py`, `anthropic_provider.py`, `vertex_provider.py` | static read + dirty diff |
| Fresh run evidence | `fresh-run-3pass-audit-report.md` | historical (2026-03-22) |
| Canary/probe evidence | `chaebol-ent-empire-revival-*` | live (2026-03-27) |

### Excluded

- DB persistence layer internals (T4 lane scope)
- Governance/queue artifacts (T1 lane scope)
- Structural complexity metrics (T2 lane scope)
- Advancement readiness (T5 lane scope)
- Tests, scripts, UI surfaces (not runtime production scope)

---

## 3. Current Evidence Snapshot

### 3.1 Exercised-Path Runtime Proof

| Evidence | Date | Key Numbers | Classification |
|----------|------|-------------|----------------|
| Fresh run (test project) | 2026-03-22 | 213 LLM calls, 100% success, 4 manuscripts, 0 P0, 0 regressions | **exercised** |
| Revival canary (chaebol_ent_empire) | 2026-03-27 | pair consumability pass, schema pass, 0 contract errors | **exercised** |
| Revival stage probe | 2026-03-27 | Stage 0/2/3 all pass, Arc 3789 chars, Blueprint 2855 chars | **exercised** |
| Stage 3 ep6 retry storm | 2026-03-22 | 7 retries, 21 min, $1.05 cost | **exercised** (design tension, not regression) |
| Stage 4 ep5 REJECT | 2026-03-22 | V60.97 swap, Director 50 score, pipeline stop | **exercised** (design tension, not regression) |
| Manager async future recovery | 2026-03-22 | bible_future.result(timeout=120), sync retry fallback | **exercised** (no failure in fresh run) |

### 3.2 Unexercised Structural Risks

| Risk | Source | Why Unexercised | Impact If Triggered |
|------|--------|-----------------|---------------------|
| Stage 3 REJECT sink fragility | Situation survey risk #1 | Fresh run had no generation crash in the inner `_generate_blueprint` try/except | A crash inside the 2-method generation chain would be caught by a single broad except, logging an error but potentially losing detailed failure context |
| Stage 4 post-pass bible_delta gap | Situation survey risk #4 | Manager LLM never failed in fresh run | If Manager LLM fails twice (async + sync), bible_delta=None, FactLedger update skipped, state accumulation gap |
| Multi-provider ask/continuation | Dirty worktree (2026-03-27) | Claude-on-Vertex path not yet run in production | `_normalize_usage` bridging and `hasattr(response, "candidates")` guard could mask provider-specific edge cases |

---

## 4. Top Findings

### F-1. BaseAgent ask() retry chain is mature and exercised [stabilization]

**File**: `modules/domain/agents/base_agent.py` L670-789

The LLM call retry chain handles network errors (up to 22 retries with linear backoff), rate limits (3 retries with model-stack fallback), and quota exhaustion (model-stack fallback chain). The `_handle_api_error` method delegates to three specialized branches: `_handle_network_retry_branch`, `_handle_rate_limit_retry_branch`, `_handle_quota_fallback_branch`. Each branch returns a structured dict with explicit action ("continue", "fallback_response", "raise") and counter state.

Fresh run evidence: 213 LLM calls at 100% success rate. No network/quota/rate-limit fallback was needed. The retry chain is structurally sound but its deep branches remain unexercised in recent runs.

**Maturity**: stabilization (exercised happy path, unexercised deep recovery).

### F-2. Stage 4 retry/reject/post-pass runtime modules are well-separated [optimization]

**Files**: `stage4_retry_runtime.py` (1,075 LOC), `stage4_reject_runtime.py` (819 LOC), `stage4_post_pass_runtime.py` (980 LOC), `stage4_director_runtime.py` (1,464 LOC)

Each Stage 4 sub-concern has been extracted into a dedicated runtime module with dataclass-driven payload contracts. The retry runtime owns PASS_WITH_FIX loop orchestration with explicit iteration gates, patch guards, re-audit, and finalization payloads. The reject runtime owns guidance extraction, retry snapshotting, and reject logging. The post-pass runtime owns atomic world-state settlement with snapshot/rollback.

This separation supports early-optimization: the module boundaries are clean, authority is explicit, and dataclass contracts reduce implicit coupling.

**Maturity**: early-optimization (clean boundaries, explicit contracts).

### F-3. Soft failure system provides structured non-blocking error recording [stabilization]

**File**: `modules/core/soft_failure.py` (176 LOC)

`report_soft_failure()` emits throttled warnings (per-key window), relays to audit_event if available, and persists to `soft_failures.jsonl`. The throttle prevents log flooding. 32 call sites across 7 production modules use it (primarily `stage4_post_processor`, `failure_analyzer`, `validation_orchestrator`).

The system is structurally complete for stabilization. It does not yet feed into an aggregate health dashboard or SLO-like signal, which would be an advancement feature.

**Maturity**: stabilization (exercised via fresh run, no aggregate signaling).

### F-4. Stage 3 REJECT sink: broad catch remains a structural risk [stabilization gap]

**File**: `modules/core/stage3_orchestrator.py` L1703

The `_generate_blueprint` method wraps the entire generation + handoff chain in a single try/except:

```python
try:
    _semantic_bundle = self._build_stage3_blueprint_semantic_bundle(...)
    blueprint, pipeline_result = self._run_stage3_blueprint_generation_handoff(...)
except Exception as gen_err:
    _logging.error(f" [V61.3] ...")
    blueprint = None
    pipeline_result = {"final_verdict": "ERROR", "error": str(gen_err)}
```

This catch-all converts any exception into a generic ERROR verdict. A crash in semantic retrieval, treatment block injection, or timeline advisory will be indistinguishable from a generation failure. The fresh run did not trigger this path.

The dirty worktree adds a new `_apply_stage3_dead_npc_precheck` call inside the generation chain (L1508-1513), increasing the surface covered by this single catch-all.

**Maturity**: stabilization gap (structural risk, unexercised).

### F-5. Stage 4 post-pass atomic settlement has explicit rollback [stabilization]

**File**: `modules/core/stage4_post_pass_runtime.py` L1029-1078

The `_handle_atomic_metadata_failure` method implements explicit rollback for WorldState and FactLedger when the atomic save fails. It captures in-memory snapshots before persistence, attempts per-manager rollback in sequential mode, and falls back to in-memory snapshot restoration if manager rollback fails. The failure is reported via soft_failure and logged to the operator.

The Manager LLM future chain (`_collect_manager_audit_result`, L390-464) implements async-to-sync fallback: if `bible_future.result(timeout=120)` fails, it cancels the future and retries synchronously. If both fail, it returns empty dict and logs `[XC-002]`.

**Maturity**: stabilization (structurally sound, partially exercised via fresh run happy path).

### F-6. Multi-provider integration adds unexercised retry surface [stabilization risk]

**Files**: `base_agent.py` (dirty), `llm_router.py` (dirty), `vertex_provider.py` (dirty)

The dirty worktree introduces:
1. `_normalize_usage()` bridging Claude/OpenAI token keys to Gemini-canonical keys (base_agent.py)
2. `hasattr(response, "candidates")` guard for non-Gemini responses in continuation logic (base_agent.py)
3. `AnthropicVertexProvider` registration in the router (llm_router.py)
4. `auth_mode` parameter for Vertex (vertex_provider.py)

These changes extend the retry/continuation surface to handle non-Gemini providers. The `hasattr(response, "candidates")` guard in `_extract_and_merge_response` (L1396) prevents crashes for Claude responses, but it also means Claude responses will skip continuation detection entirely. The fresh-run and canary evidence predate these changes.

**Maturity**: stabilization risk (new surface, zero exercised-path proof).

### F-7. SessionLogger is correctly classified as optional telemetry [stabilization]

**File**: `modules/core/session_logger.py`

The docstring explicitly classifies session JSONL files as "OPTIONAL best-effort telemetry" with "authoritative truth" in db_manager and episode_production.jsonl. The logger uses a threading.Lock for JSONL write safety, tracks its own health via `get_health_snapshot()`, and supports graceful shutdown via `begin_shutdown()`.

**Maturity**: stabilization (clean authority classification, no exercised failure evidence needed).

### F-8. Adaptive retry strategy is comprehensive but may be undertested [optimization candidate]

**File**: `modules/core/adaptive_retry.py`

The `AdaptiveRetryStrategy` handles 8 error types with per-type max retries and wait times. It tracks agent-level failure statistics and escalation thresholds. This is a stabilization-era asset that could become an optimization target (consolidation with the BaseAgent retry chain).

**Maturity**: stabilization asset, optimization candidate.

---

## 5. Maturity-Band Judgment

### Declarations

- **Supports late-stabilization: yes**
  - Fresh run (213 LLM, 100% success, 0 P0) proves exercised-path runtime stability
  - Revival canary + stage probe prove runtime admission for new content pairs
  - Retry/reject/recovery modules are structurally mature with explicit contracts
  - Soft failure system provides structured non-blocking error recording
  - Two unexercised risks remain but are bounded structural risks, not active instability

- **Supports early-optimization: mixed**
  - Stage 4 runtime module separation (retry/reject/post-pass/director) shows optimization-grade boundary work
  - Dataclass payload contracts across Stage 4 runtimes show deliberate contract normalization
  - However, the multi-provider integration is in-flight (dirty worktree) with zero exercised-path proof
  - Stage 3 still has the broad catch-all that was identified pre-optimization
  - No runtime-level cost/latency optimization evidence (that is T4/T5 scope)

- **Supports not-yet-advancement: yes**
  - No automated runtime health gate or SLO-like signal exists
  - Soft failure JSONL is not aggregated into a health dashboard
  - No canary automation; the revival probe was manual
  - Multi-provider surface has no regression gate
  - Session logger is optional and disabled by default

### Axis Summary

| Axis | Judgment | Strongest Evidence |
|------|----------|-------------------|
| Stabilization | **Late** | Fresh run 213/213 success + revival stage probe pass + explicit rollback/recovery in Stage 4 post-pass |
| Optimization | **Early** | Stage 4 runtime module separation + dataclass contracts; tempered by multi-provider in-flight + Stage 3 catch-all |
| Advancement | **Not entered** | No automated health gate, no canary automation, no SLO signal, no release contract |

---

## 6. Top Quick Wins

These are proof-quality or clarity-quality oriented, not refactor-first.

### QW-1. Stage 3 catch-all split [evidence-only]

Record the exact split boundary for the Stage 3 `_generate_blueprint` catch-all. The semantic bundle build and the generation handoff are independent failure domains. Splitting the catch-all into two try/except blocks would preserve detailed failure context without changing any runtime behavior. This is a documentation + future-patch note, not an immediate action.

### QW-2. Multi-provider exercised-path proof [evidence-only]

Run a bounded canary through the Claude-on-Vertex path (or at minimum a unit-level smoke test) to prove that the `_normalize_usage` bridge and the `hasattr(response, "candidates")` guard work under real provider responses. This would close the biggest current uncertainty in this lane.

### QW-3. Soft failure aggregation note [doc-gap]

Document the current soft_failure JSONL schema and the fact that no aggregate health signal is derived from it. This makes the advancement gap explicit and prevents future overclaiming.

---

## 7. Contradictions / Uncertainties

### Contradiction: Stage 3 dirty additions expand catch-all scope

The dirty worktree adds `_apply_stage3_dead_npc_precheck` inside the generation chain that is covered by the single broad catch-all. This means the structural risk identified in the situation survey (risk #1) has become slightly larger, not smaller, since the survey was written. The survey text says "single try/except over 146 LOC"; the current live surface is larger due to the new call site.

**Resolution**: Live source wins over old survey wording. The risk is the same kind but marginally wider.

### Uncertainty: Multi-provider continuation semantics

The `hasattr(response, "candidates")` guard means Claude responses skip continuation detection entirely. If a Claude response requires continuation (e.g., max_output_tokens hit), the current code will treat it as complete. This may be intentional (Claude providers handle continuation differently) or may be a gap. Without exercised-path proof, this remains the biggest uncertainty.

### Uncertainty: Revival probe terminal pipe crash

The stage probe report notes "I/O operation on closed file" due to Windows pipe + Rich console interaction. This was classified as "non-revival unrelated system issue." This classification is correct for the revival judgment, but it means the full interactive menu loop has not been proven end-to-end for the new pair. Only programmatic verification succeeded.

---

## 8. Cross-Lane Handoff Notes

### To T1 (Governance)
- The revival canary/probe was manual and ad-hoc. There is no governance artifact or repeatable gate for canary runs. T1 may want to flag this as an advancement gap.

### To T2 (Structure)
- Stage 3 catch-all (F-4) is a structural complexity issue that was already identified in the complexity audit. T2 should verify whether the dirty additions change the hotspot LOC count.

### To T4 (Persistence/Observability)
- Stage 4 post-pass bible_delta gap (unexercised risk) has persistence and observability implications. If Manager LLM fails, FactLedger state accumulation has a gap. T4 should assess whether the soft_failure JSONL recording is sufficient for post-hoc diagnosis.
- SessionLogger authority classification ("optional best-effort") means session JSONL loss does not affect durable truth. T4 should verify that the durable sinks (db_manager, episode_production.jsonl) are independently sufficient.

### To T5 (Advancement)
- No automated canary, no health gate, no SLO. Soft failure system exists but is not aggregated. These are advancement blockers visible from the runtime stability lane.

---

## 9. Confidence And Limits

**Estimated confidence: 96%**

Basis:
- Fresh run evidence is the strongest single proof and it is well-documented with 3-pass audit
- Revival canary and stage probe are from today (2026-03-27) and directly prove runtime admission
- Static code reading covers all primary scope files
- Dirty worktree diffs are small and bounded (227 insertions across 8 files)
- All unexercised risks are explicitly separated from exercised-path proof

The 4% gap is from:
- Multi-provider continuation semantics uncertainty (2%) -- no exercised-path proof for the new Claude-on-Vertex path
- Stage 3 catch-all expanded scope without exercised-path proof for the new dead-NPC precheck (1%)
- Revival probe terminal pipe issue leaves the full interactive loop unproven for the new pair (1%)

---

## Mandatory Declarations

- Supports late-stabilization: **yes**
- Supports early-optimization: **mixed**
- Supports not-yet-advancement: **yes**
- Evidence freshness: **mixed** (fresh run 2026-03-22, canary/probe 2026-03-27, static code read 2026-03-27)
- Top 3 strongest pieces of evidence in this lane:
  1. Fresh run 213/213 LLM success with 0 P0 regressions (2026-03-22)
  2. Revival stage probe Stage 0/2/3 all-pass with real LLM content (2026-03-27)
  3. Stage 4 post-pass atomic rollback + Manager async-to-sync fallback (live source)
- Single biggest uncertainty in this lane: **Multi-provider (Claude-on-Vertex) continuation and usage normalization has zero exercised-path proof**

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- Confirmed survey lane scope matches master order T3 definition
- All 9 required sections present
- Included/excluded surfaces explicitly listed
- Evidence split into exercised vs unexercised
- PASS

### Pass 2. Evidence and Consistency
- Fresh run evidence matches source doc claims (213 LLM, 100% success)
- Dirty diff line counts match git diff --stat output (227 insertions, 8 files)
- Situation survey risk #1 wording updated to reflect live source (catch-all scope expanded)
- Canary/probe dates match source docs (2026-03-27)
- No overclaiming beyond inspected evidence
- PASS

### Pass 3. Execution and Readability
- Maturity declarations are explicit yes/mixed/no
- Quick wins are proof-quality oriented, not refactor-first
- Cross-lane handoffs are actionable
- Confidence gap is bounded and explained
- PASS
