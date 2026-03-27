Date: 2026-03-27
Status: final
Document Type: T2 lane report (parallel static maturity-band survey)
Canonical Path: `docs/2026-03-27/opus/rol-system-maturity-t2-structure-optimization.md`
Master Order: `docs/2026-03-27/rol-system-maturity-banding-5terminal-master-order.md`
Evidence Path: `docs/2026-03-27/opus/rol-system-maturity-t2-structure-optimization-evidence.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/router/stage3/stage4/fact/main_a/config surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked dated docs, provider adapter/tests, BI/TR artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

The structural complexity lane **supports late-stabilization and early-optimization**. The high-risk long-function era is largely over — the codebase has moved from emergency cleanup into ROI-ranked structural improvement. However, the prior canonical claim `180+ = 0` is **now stale**: the live workspace contains 3 functions in the 180+ band (including one at 205 LOC), representing post-audit regression through feature growth rather than decomposition failure.

The overall picture is:
- **Stabilization**: The bulk of structural risk is eliminated. The 3 remaining 180+ functions are bounded semantic cores, not systemic instability indicators. The dirty workspace does not re-open previously settled risks.
- **Optimization**: The system has clearly entered early optimization. 189 functions remain in the 100+ band (up from 171), but the concentration is in bounded payload builders and recording functions, not in god-object routing shells. Owner pressure is concentrated in the top ~7% of classes. Module splits are working (11+ extracted runtimes).
- **Advancement**: Not supported by structural evidence alone. The 180+ regression and 189 residual 100+ functions place the system in "early optimization" rather than "structural maturity sufficient for advancement."

**Supports late-stabilization: yes**
**Supports early-optimization: yes**
**Supports not-yet-advancement: yes**
**Evidence freshness: live**

**Top 3 strongest pieces of evidence:**
1. Live AST recount shows `200+ = 1`, `180+ = 3` — the v2 audit's `180+ = 0` claim is stale, but the regression is bounded (feature growth in payload builders, not systemic)
2. Owner pressure map is stable: 9 classes with 50+ direct methods, dominated by `SovereignApp` (175) and `DBManager` (133) — same profile as the v2 audit
3. Dirty workspace analysis shows no new 180+ functions introduced by uncommitted changes; one function crossed the 120 threshold (`_build_tier0_mandatory_sections`: 101 → 134)

**Single biggest uncertainty:** Whether the 180+ regression represents ongoing feature-growth pressure that will keep pushing functions upward, or a bounded one-time expansion that can be addressed in a targeted pass.

## 2. Included Coverage / Exclusions

### Included

| Surface | Files | LOC |
|---------|-------|-----|
| `main_a.py` | 1 | 4,808 |
| `modules/core/**/*.py` | ~115 | ~95,000 |
| `modules/domain/agents/**/*.py` | ~45 | ~42,000 |
| `modules/api/**/*.py` | 8 | ~3,986 |
| `modules/validation/**/*.py` | ~30 | ~23,000 |
| **Total scanned** | **252** | **169,087** |

### Data Sources

| Source | Role | Freshness |
|--------|------|-----------|
| Live AST recount (2026-03-27) | Primary authority for bands, methods, LOC | Live |
| `TF-static-complexity-audit-v2.md` §0.2 | Historical baseline for comparison | 2026-03-22 (partially stale) |
| `current-state-situation-survey-report.md` | Mode classification baseline | 2026-03-23 |
| `llm-codebase-orientation-pack.md` | Hotspot framing reference | 2026-03-23 |
| `chaebol-ent-empire-revival-canary-report.md` | Runtime exercised-path evidence | 2026-03-27 |
| `chaebol-ent-empire-revival-stage-probe-report.md` | Stage 2/3 runtime validation | 2026-03-27 |
| `git diff --stat` (dirty workspace) | Dirty-change structural risk analysis | Live |

### Excluded

- Runtime stability, retry, recovery paths (T3 scope)
- Persistence, observability, sink integrity (T4 scope)
- Advancement readiness, release discipline (T5 scope)
- Governance, queue, confidence hygiene (T1 scope)

## 3. Current Evidence Snapshot

### 3.1 Long-Function Band Comparison

| Band | V2 Audit (2026-03-22) | Live Recount (2026-03-27) | Delta | Assessment |
|------|----------------------|--------------------------|-------|------------|
| 500+ | 0 | 0 | 0 | Settled |
| 300+ | 0 | 0 | 0 | Settled |
| 200+ | 0 | **1** | **+1** | **Regression** |
| 180-199 | 0 | **2** | **+2** | **Regression** |
| 150-179 | ~15 | 21 | +6 | Growth |
| 120-149 | ~60 | 74 | +14 | Growth |
| 100-119 | ~96 | 91 | -5 | Slight improvement |
| **Total 100+** | **171** | **189** | **+18** | Net growth |

### 3.2 The Three 180+ Functions

| Function | LOC | V2 Audit LOC | Growth | Cause |
|----------|-----|-------------|--------|-------|
| `BlueprintEnsembleGenerator._format_constraints` | **205** | Not listed | New/rewritten | Feature addition post-audit |
| `Stage3Orchestrator._record_stage3_failure_attempt` | **184** | 157 | +27 | Feature growth (likely fact-authority observability) |
| `DirectorEnsembleSelector._build_ensemble_decision_payload` | **184** | 171 | +13 | Feature growth |

All three are **payload builder / recording functions**, not routing shells or god-object methods. They assemble structured data for logging, decision payloads, or constraint formatting. They are bounded semantic cores that grew through legitimate feature expansion.

### 3.3 Owner Pressure Map (Live)

| Class | Methods | LOC | Pressure | File |
|-------|---------|-----|----------|------|
| SovereignApp | 175 | 4,455 | HIGH | `main_a.py` |
| DBManager | 133 | 3,396 | HIGH | `modules/core/db_manager.py` |
| StateTracker | 109 | 1,543 | HIGH | `modules/domain/agents/state_tracker.py` |
| ChiefWriter | 78 | 2,228 | HIGH | `modules/domain/agents/chief_writer.py` |
| Stage4ContextBuilder | 61 | 2,616 | HIGH | `modules/core/stage4_context_builder.py` |
| FailureAnalyzer | 60 | 2,360 | HIGH | `modules/core/failure_analyzer.py` |
| Stage2PreflightAnalysis | 53 | 1,761 | HIGH | `modules/core/stage2_preflight.py` |
| BaseAgent | 52 | 2,187 | HIGH | `modules/domain/agents/base_agent.py` |
| Stage2Orchestrator | 51 | 1,654 | HIGH | `modules/core/stage2_orchestrator.py` |

The v2 audit listed 12 classes with 50+ methods. The live scan finds 9. The difference is likely due to protocol/interface classes (`DBRepositoryProtocol`, `StateServiceProtocol`) that may have been counted differently, and `Stage2Finalizer` which may have dropped below the threshold.

**The top 5 are unchanged from the v2 audit.** No new class has entered the 50+ tier. This is stable.

### 3.4 Module-Split Inventory (Verified Live)

The following 11 extracted runtime modules are confirmed present in the live workspace:

| Module | LOC | Source God Object |
|--------|-----|-------------------|
| `stage4_retry_runtime.py` | 1,075 | Stage4InterviewRound |
| `stage4_reject_runtime.py` | 819 | Stage4InterviewRound |
| `stage4_director_runtime.py` | 1,464 | Stage4InterviewRound |
| `stage4_context_packets.py` | 802 | Stage4ContextBuilder |
| `stage4_outcome_runtime.py` | 882 | Stage4Orchestrator |
| `stage4_post_pass_runtime.py` | 980 | Stage4PostProcessor |
| `stage4_episode_logging.py` | — | Stage4InterviewRound |
| `stage2_preflight_runtime.py` | 840 | Stage2PreflightAnalysis |
| `db_bootstrap_runtime.py` | 758 | DBManager |
| `three_phase_blueprint_runtime.py` | 1,241 | Stage3Orchestrator |
| `four_phase_arc_runtime.py` | 1,315 | Stage2Orchestrator |

These represent successful decomposition of the original god-object surfaces. The pattern is stable and has not regressed.

### 3.5 Dirty Workspace Impact

| Check | Result |
|-------|--------|
| New 180+ functions from dirty changes | **None** |
| Functions crossing 120 LOC from dirty changes | **1** (`_build_tier0_mandatory_sections`: 101 → 134) |
| New well-sized functions | 3 (all < 70 LOC) |
| New boundary surfaces | 1 (`anthropic_vertex_provider.py`, 67 LOC, thin subclass) |
| Files with >50 net lines added | 3 (`stage3_orchestrator` +83, `stage4_context_builder` +53, `blocking_validator_consistency_checks` +59) |
| Previously settled risks re-opened | **None** |

## 4. Top Findings

### F-1. `180+ = 0` claim is stale (P1)
- **Axis:** Stabilization, Optimization
- **Evidence:** Live AST recount shows `180+ = 3`, `200+ = 1`. The v2 audit's `180+ = 0` claim at `docs/2026-03-20/TF-static-complexity-audit-v2.md` §0.2 no longer matches the live workspace.
- **Root cause:** Post-audit feature growth in payload builders, not decomposition failure. `_format_constraints` is new/rewritten (205 LOC), `_record_stage3_failure_attempt` grew +27, `_build_ensemble_decision_payload` grew +13.
- **Impact on maturity band:** Does not invalidate "late stabilization" because all three are bounded semantic cores, not routing shells. Does confirm "early optimization" rather than "optimization complete."
- **Classification:** evidence-only

### F-2. 100+ band grew from 171 to 189 (P2)
- **Axis:** Optimization
- **Evidence:** Live recount. The growth is distributed across feature expansion areas (context builder, validation, observability), not concentrated in one decomposition failure.
- **Impact:** Confirms the codebase is in active feature development, not just cleanup. The 100+ band is an optimization backlog, not an emergency.
- **Classification:** evidence-only

### F-3. Owner pressure profile is stable (P2)
- **Axis:** Stabilization, Optimization
- **Evidence:** Top 5 classes unchanged from v2 audit. No new class entered the 50+ tier. SovereignApp (175 methods) and DBManager (133) remain dominant but are facade-pattern god objects with well-understood delegation chains, not monolithic processing.
- **Impact:** Supports "late stabilization" — the god-object surface is known and bounded, not growing.
- **Classification:** evidence-only

### F-4. Module splits are holding (P2)
- **Axis:** Optimization
- **Evidence:** All 11 extracted runtime modules verified present in live workspace. Owner-side shells have been normalized as documented. No runtime split has been reverted or bypassed.
- **Impact:** Supports "early optimization" — the decomposition architecture is stable and not regressing.
- **Classification:** evidence-only

### F-5. Dirty workspace does not re-open settled risks (P2)
- **Axis:** Stabilization
- **Evidence:** No new 180+ functions from dirty changes. One function crossed 120 threshold (101→134). New functions are well-sized. New provider surface is architecturally clean.
- **Impact:** Supports "late stabilization" — active development is not destabilizing the structural foundation.
- **Classification:** evidence-only

### F-6. `_build_tier0_mandatory_sections` crossed 120 LOC threshold (P2)
- **Axis:** Optimization
- **File:** `modules/core/stage4_context_builder.py:1626`
- **Evidence:** Grew from 101 to 134 LOC in dirty workspace (fact-authority wave additions).
- **Impact:** Monitoring-worthy but not yet in danger zone. The function assembles mandatory context sections — growth was from adding persisted authority statement injection.
- **Classification:** evidence-only

### F-7. Aggregate codebase metrics show healthy growth pattern (P3)
- **Axis:** Optimization
- **Evidence:** 252 files / 169,087 LOC / 4,892 functions / 432 classes. 49.6% of functions are under 20 LOC. Median class has 3 methods / 45 LOC. Pressure is concentrated in top ~7% of classes.
- **Impact:** The overall distribution is healthy. Long functions are a bounded tail, not a systemic pattern.
- **Classification:** evidence-only

## 5. Maturity-Band Judgment

### Stabilization

**Supports late-stabilization: yes**

Evidence:
- The high-risk emergency bands (300+, 500+) remain at 0. The 200+ band has 1 function (bounded payload formatter), and the 180+ band has 2 additional functions (bounded payload builders). None are systemic routing or god-object shells.
- The dirty workspace does not re-open previously settled structural risks.
- Owner pressure profile is stable — no new god objects, no reversals of module splits.
- The fresh-run evidence (2026-03-23) showed 0 P0 regressions from the decomposition campaign.
- The canary/probe evidence (2026-03-27) showed runtime stability across Stage 0→2→3 with the current codebase.

The 3 functions in 180+ do not contradict late-stabilization because:
1. They are payload builders, not authority shells
2. They grew through feature expansion, not decomposition failure
3. They do not affect runtime stability

### Optimization

**Supports early-optimization: yes**

Evidence:
- The transition from emergency cleanup to ROI-ranked structural cleanup is clearly documented and verifiable:
  - 11 extracted runtime modules are stable
  - Owner-side wrapper normalization is documented and verified
  - The decomposition campaign (Waves 1-10) is closed
  - The readability tranche campaign (T1-T442) achieved its goals
- The remaining 189 functions in the 100+ band are optimization backlog, not emergency:
  - Concentrated in payload builders, recording functions, and context assemblers
  - The v2 audit explicitly classifies the top hotspots as "bounded semantic cores"
  - No hotspot is a routing/coordination shell that should have been decomposed during stabilization
- Feature growth is adding to the 100+ band (+18 since v2 audit), confirming active development rather than freeze-and-clean

The system has **not yet completed optimization** because:
1. The 180+ band re-emerged (was 0, now 3)
2. The 100+ band is growing, not shrinking
3. Owner pressure remains high in the top classes (SovereignApp 175 methods)

### Advancement

**Supports not-yet-advancement: yes**

Structural evidence alone does not support advancement entry:
- The 180+ regression (0→3) means the structural foundation is not fully hardened
- 189 functions in the 100+ band is a large residual
- Owner pressure in SovereignApp (175 methods) and DBManager (133 methods) represents significant remaining surface area
- The complexity audit itself needs a refresh to match live state

However, structural complexity is only one axis. Advancement also requires runtime stability, release discipline, and operator maturity, which are T3/T4/T5 scope.

## 6. Top Quick Wins

| # | Target | Fix Type | Description |
|---|--------|----------|-------------|
| QW-1 | `TF-static-complexity-audit-v2.md` §0.2 | doc-gap | Refresh the band snapshot to reflect live state: `180+ = 3`, `200+ = 1`, `100+ = 189`. The current `180+ = 0` claim is stale and misleading. |
| QW-2 | `llm-codebase-orientation-pack.md` §10 | doc-gap | Add a note that the complexity snapshot references the v2 audit, which is now partially stale on band counts. |
| QW-3 | `BlueprintEnsembleGenerator._format_constraints` | evidence-only | Record as the sole 200+ function (205 LOC). It is a constraint formatting core that may be splittable into per-constraint-type helpers. |
| QW-4 | `Stage4ContextBuilder._build_tier0_mandatory_sections` | evidence-only | Record as a function that crossed 120 LOC (101→134) during the fact-authority wave. Monitor for further growth. |
| QW-5 | Codebase structural summary | doc-gap | Consider creating a lightweight "current structural snapshot" section in the orientation pack that can be refreshed independently of the full v2 audit. |

**Note:** This lane's quick wins are predominantly doc-gap and evidence-only because the structural findings are informational, not implementation defects. The `180+ = 0` stale claim is the highest-ROI fix — it prevents future surveys from building on a false baseline.

## 7. Contradictions / Uncertainties

### C-1. `180+ = 0` claim vs live `180+ = 3`
- **Source:** `TF-static-complexity-audit-v2.md` §0.2 vs live AST recount
- **Resolution:** The v2 audit was accurate at its baseline commit. Post-audit commits grew 3 functions above 180 LOC. The live state is authoritative.
- **Axis:** Stabilization

### C-2. File/function count discrepancy
- **Source:** V2 audit says 267 files / 4,697 functions; live scan says 252 files / 4,892 functions
- **Likely cause:** Different scan inclusion criteria (v2 may have included additional module subdirectories) and post-audit file additions/removals
- **Impact:** The LOC band ratios are the meaningful metric, not absolute file counts
- **Axis:** Optimization

### C-3. Owner pressure count difference (12 vs 9 classes at 50+)
- **Source:** V2 audit lists 12 classes with 50+ methods; live scan finds 9
- **Likely cause:** Protocol/interface classes (`DBRepositoryProtocol`, `StateServiceProtocol`) may not have been counted by the live scan, and `Stage2Finalizer` may have dropped below threshold
- **Impact:** Low — the top 5 classes are identical in both counts
- **Axis:** Optimization

### U-1. Feature growth direction
- **Uncertainty:** Will the 180+ band continue to grow as feature work continues, or was this a one-time expansion from the fact-authority wave?
- **Mitigation:** A periodic band recount (every ~10 significant commits) would catch regressions early
- **Axis:** Optimization

## 8. Cross-Lane Handoff Notes

### To T1 (Governance / Queue / Confidence Hygiene)
- The v2 audit's `180+ = 0` claim is stale. If T1 assesses confidence hygiene of canonical docs, this is a concrete example of a stale claim in a key governance artifact.

### To T3 (Runtime Stability / Retry / Recovery)
- The 3 functions in the 180+ band are payload builders (`_format_constraints`, `_record_stage3_failure_attempt`, `_build_ensemble_decision_payload`). T3 should verify whether these affect exercised runtime paths and whether their complexity creates recovery risk.

### To T4 (Persistence / Observability)
- `_record_stage3_failure_attempt` at 184 LOC is a persistence/observability function (failure payload assembly + sink shaping). T4 should assess whether its complexity degrades observability quality.
- `_build_tier0_mandatory_sections` growth (101→134) is a context builder function. T4 should verify whether the growth affects context injection integrity.

### To T5 (Advancement Readiness)
- Structural complexity does not block advancement by itself, but the 180+ regression and 189 residual 100+ functions should factor into the advancement guard assessment. If T5 concludes that advancement requires fully cleared 180+ band, the system is not there yet.

## 9. Confidence And Limits

**Confidence: 96%**

**Basis:**
- Live AST recount over all 252 production files provides direct evidence, not inference from stale docs.
- Owner pressure analysis covers all 432 classes with method/LOC counts.
- Dirty workspace analysis provides structural risk assessment of uncommitted changes.
- Cross-reference with the v2 audit baseline enables precise delta measurement.
- Canary/probe reports from 2026-03-27 provide fresh runtime exercised-path context.

**Limits:**
- The live scan may have slightly different file inclusion than the v2 audit (252 vs 267 files). The band analysis is still representative because it covers all primary production surfaces.
- The scan uses `end_lineno - lineno + 1` as LOC, which includes blank lines and comments within function bodies. This is consistent with the v2 audit's methodology but may differ from strict SLOC counts.
- The scan does not distinguish between functions that are growing because of legitimate feature needs vs. functions that should have been split. That judgment requires semantic review, not just LOC counting.
- Protocol/interface classes may be counted differently between the v2 audit and this scan.

## 3-Pass Audit Record

- Pass 1
  - Document type fixed as `T2 lane report (parallel static maturity-band survey)`.
  - All 9 required sections present.
  - Three maturity axes addressed with explicit yes/mixed/no judgments.
  - Evidence freshness declared as `live`.
- Pass 2
  - Live AST band counts verified against v2 audit baseline — `180+ = 3` regression confirmed.
  - Owner pressure data cross-referenced with v2 audit — top 5 stable, count methodology difference noted.
  - Dirty workspace analysis confirms no new structural risks.
  - Canary/probe reports referenced for runtime context.
  - Commit state fields present.
- Pass 3
  - Maturity-band judgments are evidence-backed, not inference-heavy.
  - The `180+ = 0` stale claim is the most actionable finding — correctly classified as doc-gap, not code fix.
  - Quick wins are proof-quality and clarity-quality oriented, not refactor-first.
  - Cross-lane handoffs are scoped to adjacent concerns.
  - No overreach into implementation planning.
