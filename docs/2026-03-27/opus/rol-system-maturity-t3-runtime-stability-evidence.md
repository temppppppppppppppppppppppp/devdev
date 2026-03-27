Date: 2026-03-27
Document Type: evidence manifest (T3 lane)
Parent Report: `docs/2026-03-27/opus/rol-system-maturity-t3-runtime-stability.md`

---

## Evidence Anchor List

### Live Evidence (2026-03-27)

| # | Anchor | Type | Key Observation |
|---|--------|------|-----------------|
| E1 | `modules/core/stage4_retry_runtime.py` L84-236 | source | RetryRuntime class: PASS_WITH_FIX loop with explicit iteration gate, patch guard, re-audit, finalization payloads (all dataclass-driven) |
| E2 | `modules/core/stage4_reject_runtime.py` L48-100 | source | RejectRuntime class: guidance extraction, retry snapshotting, reject logging with dataclass payloads |
| E3 | `modules/core/stage4_post_pass_runtime.py` L1029-1078 | source | Atomic metadata failure handler with WorldState/FactLedger rollback + in-memory snapshot restoration |
| E4 | `modules/core/stage4_post_pass_runtime.py` L390-464 | source | Manager LLM future chain: async-to-sync fallback with explicit cancel + error logging |
| E5 | `modules/core/soft_failure.py` L118-175 | source | `report_soft_failure()`: throttled warning + audit_event relay + JSONL persistence |
| E6 | `modules/core/session_logger.py` L1-19 | source | SessionLogger docstring: "OPTIONAL best-effort telemetry, NOT authoritative truth" |
| E7 | `modules/domain/agents/base_agent.py` L670-789 | source | ask() retry chain: network (22 max), rate-limit (3 max + model stack), quota (model stack fallback) |
| E8 | `modules/core/adaptive_retry.py` L70-96 | source | AdaptiveRetryStrategy: 8 error types with per-type max retries and wait times |
| E9 | `modules/core/stage3_orchestrator.py` L1703-1711 | source | Stage 3 _generate_blueprint broad catch-all: single try/except over build+handoff chain |
| E10 | `modules/core/stage4_orchestrator.py` L1518-1560 | source | Stage 4 interview loop: N-round with configurable max (default 5), explicit disposition-based loop control |
| E11 | `modules/core/stage4_orchestrator.py` L1562-1615 | source | Finalize round outcome: explicit N-round exhaustion handling with operator choice (use best / skip) |
| E12 | `git diff` base_agent.py | dirty diff | `_normalize_usage()` bridge (Claude/OpenAI -> Gemini keys), `hasattr(response, "candidates")` guard |
| E13 | `git diff` llm_router.py | dirty diff | `AnthropicVertexProvider` registration, `auth_mode` parameter addition |
| E14 | `git diff` stage3_orchestrator.py | dirty diff | `_apply_stage3_dead_npc_precheck` added inside generation chain (inside broad catch-all scope) |
| E15 | `git diff` stage4_retry_runtime.py | dirty diff | Comment-only: retry lane routing priority documentation added |
| E16 | `docs/2026-03-27/chaebol-ent-empire-revival-canary-report.md` | canary | pair consumability pass, 0 contract errors, schema drift check clean |
| E17 | `docs/2026-03-27/chaebol-ent-empire-revival-stage-probe-report.md` | probe | Runtime admission pass, Stage 2 arc 3789 chars (5 ep), Stage 3 blueprint 2855 chars (5 scenes) |

### Historical Evidence (2026-03-22 to 2026-03-23)

| # | Anchor | Type | Key Observation |
|---|--------|------|-----------------|
| H1 | `docs/2026-03-23/fresh-run-3pass-audit-report.md` | fresh run | 213 LLM, 100% success, 4 manuscripts, 0 P0, 0 regressions |
| H2 | Fresh run: Stage 3 ep6 7-retry storm | exercised | TF-35 threshold tension (score < 90), 21 min, $1.05 -- design tension not regression |
| H3 | Fresh run: Stage 4 ep5 REJECT | exercised | V60.97 swap + Director 50 score -- length gate vs quality gate tension |
| H4 | Fresh run: NPC encyclopedia DEGRADED x24 | exercised | Test environment state_tracker.npc_registry empty -- expected environment gap |
| H5 | Fresh run: Manager async future | exercised | bible_future.result(timeout=120) succeeded on all 4 pass episodes |
| H6 | `docs/2026-03-23/current-state-situation-survey-report.md` risk #1 | survey | Stage 3 REJECT sink fragility -- not exercised in fresh run |
| H7 | `docs/2026-03-23/current-state-situation-survey-report.md` risk #4 | survey | Stage 4 post-pass bible_delta gap -- not exercised in fresh run |

---

## Live vs Historical Split

| Category | Count | Weight |
|----------|-------|--------|
| Live source reads (2026-03-27) | 15 | primary |
| Live dirty diffs (2026-03-27) | 4 | primary |
| Live canary/probe (2026-03-27) | 2 | primary |
| Historical fresh run (2026-03-22) | 5 | strong support |
| Historical survey claims (2026-03-23) | 2 | support only (live source wins on conflict) |

---

## Exercised vs Unexercised Risk Separation

### Exercised (real runtime proof exists)
- LLM call success chain (213/213)
- Stage 3 retry loop (ep6, 7 retries)
- Stage 4 REJECT path (ep5)
- Runtime admission for new pair (canary + probe)
- Manager async future happy path

### Unexercised (structural risk, no runtime proof)
- BaseAgent deep retry branches (network error 22-retry, quota fallback chain)
- Stage 3 broad catch-all crash path
- Stage 4 Manager LLM double-failure path (async + sync both fail)
- Multi-provider Claude-on-Vertex continuation/usage path
- Session logger failure/rotation path

---

## Compact Contradiction Notes

| ID | Tension | Resolution |
|----|---------|------------|
| C1 | Situation survey says "single try/except over 146 LOC" for Stage 3 catch-all; live source shows the scope is now larger due to dead-NPC precheck addition | Live source wins. Risk is marginally wider. |
| C2 | Fresh run "100% success" vs BaseAgent having 22-retry network branch | No contradiction. 100% success means the deep retry branches were not needed, not that they are broken. |
| C3 | Revival probe "PASS" vs terminal pipe crash during interactive menu | No contradiction. The crash was in Windows pipe handling (Rich console), not in runtime admission logic. Programmatic verification proved the pipeline. |
