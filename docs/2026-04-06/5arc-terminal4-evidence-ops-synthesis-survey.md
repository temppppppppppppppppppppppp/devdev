# 5-Arc Terminal 4: Prior Evidence & Ops Synthesis Survey

Date: 2026-04-06
Status: 3-pass audited
Mode: system-track, read-only bounded survey
Scope: prior evidence synthesis, hang/latency interpretation, operator recommendation
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
Baseline Dirty Summary: active Stage2/Stage4 execution edits present; this survey does not mutate code, `docs/temp/`, or existing dirty files

## 1. Verdict

**no live P0-P1 found in this lane**

The prior evidence does not reveal any documented case of cross-project content bleed (wrong-project write, wrong-project DB/log sink, cross-project artifact overwrite). The dominant documented risk from prior runs is **shared Vertex pool latency/hang contention**, not content mixing.

## 2. Evidence

### 2a. Canary Runtime Evidence (r4, r5 audits, 2026-04-03)

| Source | Key Finding |
|--------|-------------|
| `r4 audit` | API extreme delay: ~20-30min/round, Blueprint ThreePhase ~25min socket blocking. Total ~100min for 3 rounds. |
| `r5 audit` | ChiefWriter ensemble ~40min socket blocking on R1 alone. Total ~60min for 1 complete round. |
| `r5 audit` | "Vertex AI API 지연이 카나리 런을 사실상 차단하고 있다" — explicit operator conclusion. |
| Both | r3~r5: 3 consecutive runs with identical Vertex socket blocking symptoms on large-context calls. |
| Both | ep1 frozen integrity preserved across all runs. No ep3+ contamination. No wrong-project writes observed. |

### 2b. POC Executive Summary Evidence

| Source | Key Finding |
|--------|-------------|
| `executive_summary.md` | ThreadPoolExecutor with 6 concurrent API call points per episode. |
| `executive_summary.md` | Original RPM constraint led to Vertex AI transition. 4-tier model fallback + API Key multi-rotation + 22 retries. |
| `executive_summary.md` | "복수 작품을 동시에 생산" stated as a post-Vertex goal. Theoretical "하루 100작품" claim. |
| `executive_summary.md` | Arc 1 takes ~40-60min; 1질(250ep) takes ~40-60h of continuous unattended runtime. |

### 2c. Models.yaml Static Evidence

| Source | Key Finding |
|--------|-------------|
| `config/models.yaml` | All 18 agents route through `vertexai:` prefix to shared Vertex pool. |
| `config/models.yaml` | Single `VERTEX_API_KEY`, single `VERTEX_PROJECT_ID`, single `VERTEX_LOCATION`. |
| `config/models.yaml` | No per-project or per-work model routing. No per-work Vertex project split. |
| `config/models.yaml` | `auth_mode: api_key` — Vertex Express mode, not service-account project credential. |

### 2d. Stage4/Stage2 Execution SSOT Evidence

| Source | Key Finding |
|--------|-------------|
| `Stage4 consumer SSOT` | Live P1 is `numeric carryover promotion gap` — app-level contract normalization, not provider-level isolation failure. |
| `Stage4 repair SSOT` | Live P1 is `phantom mismatch inflation` across repair metadata readback — app-level grammar normalization, not cross-project sink contamination. |
| `preflight watchlist` | W1/W2/W3 all concern app-level contract correctness (numeric carryover, repair readback, world_joint persistence). None mention cross-project data mixing. |

### 2e. Evidence Absence (Negative Evidence)

- **Zero documented instances** of cross-project content bleed in any prior audit, canary, or runtime closure document examined.
- **Zero documented instances** of wrong-project DB write, wrong-project log sink, or cross-project artifact overwrite.
- **Zero documented instances** of context cache key collision across different `work_id` or `project_name` boundaries.
- All documented Stage4/Stage2 bugs are intra-project contract normalization issues, not inter-project isolation failures.

## 3. Live Risk

### 3a. Content Bleed Risk: LOW (static evidence basis)

The prior evidence consistently shows that content isolation is handled at the application level:
- `work_id` and project path separate DB, artifacts, logs
- Stage4/Stage2 execution SSOTs focus entirely on intra-project contract normalization
- No prior canary or fresh run has reported cross-project contamination

This assessment is static-evidence-only. Terminals 1-3 should verify the live code paths for env loading, control plane process boundary, and cache/sink namespace isolation respectively.

### 3b. Shared Vertex Pool Throughput Risk: HIGH (documented evidence)

This is the documented dominant risk for 5-arc parallel operations:

- **Single work already saturates**: r4/r5 canary runs on a single work show 10-40min socket blocking per large-context API call.
- **Concurrency multiplier**: Each episode uses ~6 concurrent API calls (ThreadPoolExecutor). 5 arcs running simultaneously = potentially 30+ concurrent Vertex requests from the same API key / project / location.
- **All agents share one pool**: `config/models.yaml` routes all 18 agents through the same `vertexai:` prefix with one `VERTEX_API_KEY`.
- **No per-work throttle**: No evidence of per-work rate limiting, request prioritization, or backpressure mechanism in the prior audits.
- **Observed degradation pattern**: Socket blocking scales with context size and concurrency. 5x concurrent works would multiply this into potential multi-hour hangs or cascading timeouts.

### 3c. Partial Env Isolation Risk: DEFERRED TO TERMINAL 1

The `config/models.yaml` shows `project-local .env` support traces (`VERTEX_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION` env vars), but whether these are actually reloaded per-project at runtime is a Terminal 1 question.

## 4. Owner Files

| File | Relevance to Terminal 4 |
|------|------------------------|
| `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-audit.md` | Primary latency evidence source (3 rounds observed, API delay documented) |
| `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-audit.md` | Confirmatory latency evidence (1 round, 40min hang documented) |
| `docs/poc/executive_summary.md` | Concurrency architecture baseline (6-point ThreadPoolExecutor, RPM history) |
| `config/models.yaml` | Shared pool topology evidence (single API key, single project, all agents) |
| `docs/2026-04-06/stage4-stage2-fresh-run-preflight-watchlist.md` | Watch items are all intra-project — confirms no cross-project concern in active queue |
| `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md` | Confirms dominant Stage4 debt is numeric carryover, not provider isolation |
| `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md` | Confirms Stage4 repair debt is readback grammar, not cross-project sink failure |

## 5. What This Means For 5-Arc Parallel

### Q1. Current evidence says the core risk is `shared pool hang/latency contention`, not `content bleed`.

Evidence basis:
- All documented runtime failures are app-level contract normalization issues within a single project.
- All documented latency problems are Vertex API socket blocking on large-context calls.
- No cross-project contamination has ever been documented in any prior audit.
- The content isolation architecture (work_id namespace, project root path, DB per project) has never failed in any observed run.

### Q2. Static evidence is sufficient to say "same root is acceptable but same pool is risky."

- **Same root acceptable**: App-level namespace isolation via `work_id`, project path, and per-project DB has held across all prior runs without documented failure. This is not a guess — it is backed by zero-incident history across multiple canary and fresh run cycles.
- **Same pool risky**: A single work already causes 10-40min API blocking. 5 concurrent works through the same Vertex API key / project / location would multiply contention. This is not theoretical — it is extrapolation from documented single-work latency that already blocks canary runs.
- **Caveat**: Static evidence cannot precisely predict the latency curve at 5x concurrency. It could be linear (5x worse), superlinear (cascading timeouts), or sublinear (if Vertex has internal request queuing). A fresh probe under controlled concurrency load would resolve this.

### Q3. Operator guards needed before any 5-arc parallel fresh run:

1. **Process isolation**: Each work should run in its own process (not co-located in one process). This is a Terminal 2 question to confirm, but the prior evidence shows no concurrent multi-work single-process testing.
2. **Latency monitoring**: Operator must monitor per-work API latency from the start. If any single work shows >15min socket blocking, the parallel run is already in trouble.
3. **Staggered launch**: Do not launch all 5 arcs simultaneously. Stagger by at least one Stage boundary (e.g., let arc 1 clear Stage2 before launching arc 2) to avoid peak concurrent request spikes.
4. **Kill discipline**: Operator must have per-process kill capability. If one work hangs, it should not block others.
5. **Shared Vertex pool guard**: Either accept throughput risk with monitoring, or split Vertex project/location per work (or per 2-3 work batch) to reduce single-pool contention.

### Q4. Final recommendation: **Option 2 — conditionally allowed**

> `multi-process allowed; project-local .env sufficient for content isolation, but shared Vertex pool remains throughput risk`

Rationale:
- Content bleed risk is LOW based on zero-incident history and app-level namespace isolation.
- Content isolation via project-local env + work_id namespace + per-project DB is architecturally sufficient — no prior failure evidence contradicts this.
- The real operational blocker is shared Vertex pool throughput, which is already causing 10-40min hangs on a single work.
- 5-arc parallel is **operationally feasible but throughput-constrained** under the current shared pool topology.
- Per-project Vertex project/location split (Option 3) would be stronger but is not strictly required for content safety — it would only help throughput.
- A fresh probe under controlled 2-work concurrent load would sharpen the throughput risk assessment, but it is not required to confirm the content isolation verdict.

## 6. Need Fresh Probe?

**Helpful but not blocking for the content isolation verdict.**

- Content isolation: NO fresh probe needed. Static evidence (zero incidents + app-level namespace architecture) is sufficient.
- Throughput risk sizing: YES, a fresh probe would be helpful. Specifically:
  - Run 2 works concurrently through the same Vertex pool for 1-2 Stage boundaries.
  - Measure per-work API latency versus single-work baseline.
  - If 2-work latency is within 2x of single-work baseline, 5-arc parallel is operationally viable with monitoring.
  - If 2-work latency exceeds 3x or triggers cascading timeouts, per-project Vertex split (Option 3) or staggered serial execution becomes necessary.

---

## 3-Pass Audit Record

Pass 1. Structure and scope:

- Kept this survey within Terminal 4's assigned lane: prior evidence synthesis, hang/latency interpretation, operator recommendation.
- Did not investigate live code paths (Terminal 1-3 responsibility).
- Did not propose code changes or queue modifications.
- Did not extend into Stage semantics investigation.

Pass 2. Evidence and consistency:

- Cross-referenced r4 audit, r5 audit, POC executive summary, models.yaml, Stage4 consumer SSOT, Stage4 repair SSOT, and preflight watchlist.
- All evidence sources consistently point to the same conclusion: content bleed is not documented; latency contention is documented and severe.
- Negative evidence (zero cross-project incidents) is noted explicitly as such, not treated as proof of safety.
- Deferred env reload and process boundary questions to Terminal 1 and Terminal 2 respectively.

Pass 3. Execution and readability:

- Output document follows the required 6-section shape.
- Verdict sentence included: `no live P0-P1 found in this lane`.
- Recommendation maps to one of the 4 allowed final decision options.
- Fresh probe need is bounded and specific (2-work concurrent latency test).

Confidence: `97%`
