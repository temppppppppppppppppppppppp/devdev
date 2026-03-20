# Tranche C: Domain and Agent Layer — Global Survey Draft

```
Status: DRAFT
Authority: NOT AUTHORITY
Role: COLLECTOR ONLY
Execution: NO EXECUTION AUTHORITY
Terminal: 2
Date: 2026-03-20
Baseline Commit: d0fa70f1
```

---

## 1. Scope

### Included
- `modules/domain/agents/` — 47 Python files, ~40,753 LOC
- `modules/validation/` — 10+ validator files (blocking, advisory, scoring, consistency, continuity, orchestrator, batch, pre-LLM, catharsis, retrospective)
- Ensemble patterns (arc_ensemble, blueprint_ensemble, director_ensemble, consensus_validator)
- Retry/fallback patterns across domain + orchestrator boundaries
- Agent-level side effects (state, cache, logging, DB telemetry)
- Decision ownership boundaries and Director sovereignty seams
- Python collection vs LLM judgment drift analysis
- TF evidence cross-reference against live code

### Excluded
- `main_a.py` SovereignApp internals (Tranche B scope)
- `modules/core/` orchestrators (covered at boundary only)
- `scripts/`, `UI/`, `geuldobi-desktop/` (other tranches)
- Narrative pipeline artifacts

### Evidence Sources
- Live code read (47 domain agent files, 10+ validation files)
- Git status (25+ domain files modified, uncommitted — line ending normalization)
- Tests: test_sweep28/29/31, test_continuity_modules, test_four_phase_arc_generator, test_unified_arc_validator, test_base_agent, test_chief_writer, test_director_modules, test_opus_tf5_e6_regressions, test_pass_with_fix, test_quality_regression, test_tier4_ensemble_caching
- TF audit ledger from memory (35 findings, phases 1-5)
- docs/2026-03-18 CODEX-ENTRY-POINT + 3-pass deep audit docs

---

## 2. Agent Surface Inventory

### 2.1 Agent File Map (47 files, 6 categories)

| Category | Files | Total LOC | Key Classes |
|----------|-------|-----------|-------------|
| **Core Foundation** | base_agent.py | ~2,213 | BaseAgent |
| **Director Subsystem** | director.py + 5 sub-modules | ~3,768 | Director (facade), DirectorCachingManager, DirectorGradingSystem, DirectorEnsembleSelector, DirectorContinuityValidator, DirectorQualityAuditor |
| **Arc Generation** | four_phase_arc_generator.py, arc_ensemble.py, arc_critic.py, arc_corrector.py, arc_draft_validator.py, unified_arc_validator.py, constraint_compiler.py | ~6,404 | FourPhaseArcGenerator, ArcEnsembleGenerator, ArcCritic, ArcCorrector |
| **Blueprint Generation** | three_phase_blueprint_generator.py, blueprint_ensemble.py, blueprint_constraint_compiler.py, unified_blueprint_validator.py | ~3,421 | ThreePhaseBlueprintGenerator, BlueprintEnsembleGenerator |
| **Writers** | chief_writer.py + 3 sub-modules, writer.py, weaver.py, block_enricher.py | ~6,401 | ChiefWriter, ChiefWriterContextBuilder, ChiefWriterQualityGate, Writer, Weaver, BlockEnricher |
| **State & Continuity** | state_tracker.py + 3 sub-modules, state_extractor.py, continuity_arc.py, continuity_blueprint.py, continuity_manuscript.py, continuity_inspector.py, continuity_tracker.py | ~8,803 | StateTracker (+NPC, Plots, Financial), StateExtractor, ContinuityArcValidator, ContinuityManuscriptValidator |
| **Analysis & Support** | analyst.py, analyst_prompt_api.py, critic.py, manager.py, preflight_checker.py, consensus_validator.py, manuscript_validator.py, negative_example_injector.py | ~5,792 | Analyst, Critic, Manager, PreflightChecker, ConsensusValidator, ManuscriptValidator |

### 2.2 Inheritance Hierarchy

All 19 primary agents extend `BaseAgent`:
Analyst, ArcCritic, ArcCorrector, ArcEnsembleGenerator, BlockEnricher, BlueprintEnsembleGenerator, ChiefWriter, ConsensusValidator, ContinuityInspector, Critic, Director, FourPhaseArcGenerator, Manager, PreflightChecker, StateExtractor, StateLockedArcGenerator, ThreePhaseBlueprintGenerator, UnifiedArcValidator, Writer, Weaver

Non-BaseAgent utility classes: DirectorCachingManager, DirectorGradingSystem, DirectorEnsembleSelector, DirectorContinuityValidator, DirectorQualityAuditor, ChiefWriterContextBuilder, ChiefWriterQualityGate, StateTrackerNPC, StateTrackerPlots, StateTrackerFinancial, UnifiedBlueprintValidator, ManuscriptValidator (no REJECT authority)

### 2.3 LLM Interaction Points (self.ask() distribution)

| Agent | ask() Calls | Temperature Range | thinking_level |
|-------|-------------|-------------------|----------------|
| Analyst | 15+ | 0.2–0.8 | varies |
| ArcCorrector | 3 | 0.3–0.4 | — |
| ArcCritic | 1 | 0.2 | "medium" |
| BlockEnricher | 3 | 0.4–0.7 | — |
| ChiefWriter | 1 (+ ensemble) | varies | varies |
| ConsensusValidator | 3 (parallel) | 0.1–0.2 | — |
| Critic | 2 | 0.2–0.3 | — |
| Manager | 2 | 0.1 | — |
| PreflightChecker | 1 | 0.2 | "low" |
| StateExtractor | 2 | 0.2 | "low" |
| StateLockedArcGenerator | 4 | 0.1–0.8 | varies |
| UnifiedArcValidator | 1 | 0.1 | "low" |
| Weaver | 1 | 0.5 | — |
| Writer | 2 | 0.8 | — |

Context caching applied to 5 agents: ChiefWriter, ArcEnsemble, BlueprintEnsemble, DirectorEnsemble, DirectorContinuity.

### 2.4 Validation Tier Architecture (ValidationOrchestrator)

```
TIER 0.25: PRE-LLM     (PreLLMValidator, Python-only)
TIER 0.5:  CONTINUITY   (ContinuityValidator, Python + heuristics)
TIER 1:    BLOCKING      (BlockingValidator, Python — CAN REJECT)
TIER 1.5:  CONSISTENCY   (ConsistencyValidator, Python)
TIER 2:    SCORING       (ScoringValidator, LLM-based — CAN REJECT via threshold)
TIER 3:    ADVISORY      (AdvisoryValidator, Python + optional LLM — CANNOT REJECT)
```

---

## 3. Ownership Seams

### 3.1 Decision Authority Matrix

| Decision | Owner | Can REJECT? | Mechanism | Bypass Possible? |
|----------|-------|-------------|-----------|------------------|
| Arc candidate selection | DirectorEnsembleSelector | Yes | LLM comparison + quality gates | No |
| Blueprint candidate selection | DirectorEnsembleSelector | Yes | LLM comparison + quality gates | No |
| Manuscript quality verdict | DirectorQualityAuditor | Yes | 3-Tier validation + LLM audit | No |
| Adaptive threshold re-eval | DirectorGradingSystem | N/A (adjusts) | Formula [45,85] range | No |
| State update approval | DirectorGradingSystem.on_approve_workflow() | Yes (rejects out-of-bounds) | Hardcoded LIMITS | No |
| Genre compliance | DirectorQualityAuditor (→ GenreGuard) | Advisory to Director | Guard polymorphism | No |
| Blocking validation | BlockingValidator | Yes (hard block) | Python entity/scene checks | No |
| Consensus voting | ConsensusValidator | Yes (2/3 majority) | 3 LLM perspectives parallel | No |
| Advisory suggestions | AdvisoryValidator | No (always PASS) | Python + optional LLM | N/A |
| Manuscript content | ChiefWriter | No (proposes only) | LLM generation | Director can reject |
| Arc strategy | FourPhaseArcGenerator | No (proposes only) | LLM generation | Director can reject |
| Pre-LLM structural | PreLLMValidator | Advisory only | Python regex/heuristic | N/A |

### 3.2 Python-Collection vs LLM-Judgment Boundary

**FACT**: The codebase follows "Python은 수집만, 판단은 LLM이" (대원칙 1).

Evidence of compliance:
- Arc ensemble: Python scores structural completeness (20+30+25+25 pt breakdown), but returns `(None, valid_candidates)` — does NOT select the winner. Director makes final selection via LLM.
- Blueprint ensemble: Python gates on minimum (≥4 scenes, ≥500 chars integrated_scenario), does NOT rank qualified candidates.
- UnifiedArcValidator: `# [V61.9] Director 주권주의: CRITICAL만 REJECT, MAJOR는 경고로 Director에게 넘김` — Python flags, LLM decides.
- ManuscriptValidator: `# REJECT 권한 없음! 경고만 생성하여 Director에게 전달` — explicit no-REJECT.

Evidence of potential drift (watchlist items):
- `four_phase_arc_generator.py:955`: `_non_reject_pairs = [pair for pair in _paired_for_director if not pair[1].get("force_reject")]` — Python filters `force_reject` candidates BEFORE Director sees them. This is quality-flag enforcement, not autonomous judgment, since `force_reject` is set by prior Python structural checks. **Inference**: acceptable under 대원칙, since Python is pre-filtering structurally invalid candidates. **Uncertainty**: if force_reject is ever set based on semantic/narrative judgment, this would be a sovereignty violation.
- `director_ensemble.py:530`: `if quality_flag.get("force_reject"): ...` — Python quality flag can force REJECT. This overrides Director LLM decision. Tagged as `[TF-22b]` explicitly: `Director REJECT는 Python이 뒤집지 않음`. **FACT**: The guard is one-directional — Python can force REJECT (structural) but never force PASS over Director REJECT.
- `director_ensemble.py:534`: `elif quality_flag.get("force_pass_with_fix") and decision == "PASS": ...` — Python can downgrade PASS → PASS_WITH_FIX. Director PASS can be constrained but not overridden to full PASS_WITH_FIX without the quality flag.

### 3.3 Director Sovereignty Implementation

**FACT**: Director sovereignty (대원칙 3, "내각제") is extensively tagged in code.

Key enforcement points:
1. `director_ensemble.py:1712`: `# [TF-22b] 디렉터 주권: Director REJECT는 Python이 뒤집지 않음`
2. `director_ensemble.py:1639`: `# [TF-C] 자동감점 제거 — Director 주권 존중 (대원칙 3)`
3. `director_ensemble.py:896`: `# [TF-36] Director 주권: 단일 후보라도 LLM 검토 없이 자동 PASS하지 않는다`
4. `unified_blueprint_validator.py:426`: `# [TF-36] 대원칙 3: Director 없으면 REJECT — 디렉터 주권주의 위반 방지`
5. `unified_arc_validator.py:175`: `# [V61.9] Director 주권주의: CRITICAL만 REJECT, MAJOR는 경고로 Director에게 넘김`

---

## 4. Retry / Fallback Map

### 4.1 API-Level Retry (BaseAgent.ask())

| Retry Type | Max Attempts | Backoff | Exhaustion Action |
|-----------|-------------|---------|-------------------|
| Rate Limit (429) | 3 per model | 30s → 60s → 90s | Fallback to next model |
| Quota Exhausted | len(model_stack) (2-3) | Immediate switch | Cache model 1hr, raise if all exhausted |
| Network Error | 22 | 10s + 5s*i (cap 30s) | check_connectivity() then retry |
| Token Continuation | 5 (MAX_CONTINUATIONS) | None (immediate) | Warn at 3, return partial at 5 |

Model fallback chain: `gemini-2.5-pro → gemini-2.5-flash`
API key rotation: up to 9 keys (GOOGLE_API_KEY through GOOGLE_API_KEY_9), min 10s interval, RLock-protected.

### 4.2 Agent-Level Retry

| Agent/Stage | Trigger | Max Retry | Mechanism | Exhaustion |
|-------------|---------|-----------|-----------|-----------|
| ArcEnsemble | Strategy failure | N/A (3 parallel) | ThreadPoolExecutor, timeout/fallback | Use longest valid candidate |
| BlueprintEnsemble | Strategy failure | N/A (3 parallel) | ThreadPoolExecutor, timeout/fallback | Use first qualified |
| ChiefWriter | Ensemble failure | 1 (single retry) | Sequential fallback | Error candidate returned |
| ConsensusValidator | Perspective timeout | N/A (3 parallel) | ThreadPoolExecutor, 60s per-future | PASS with 0.5 confidence |
| ThreePhaseBlueprint | PASS_WITH_FIX verdict | 3 (_MAX_FIX) | Inplace/partial/full patch loop | Adopt last patched or REJECT |
| FourPhaseArc | Director REJECT | Feedback retry | Re-generate with Director feedback | Use first valid candidate |
| Analyst | Arc generation fail | adaptive (retry_with_feedback) | Feedback-informed regeneration | Fallback to plan_single_arc_v20 |
| BlockEnricher | Batch enrichment fail | Indexed recovery | return_exceptions=True + retry loop | Log + skip failed items |
| DirectorAuditor | Vote timeout | N/A (parallel) | ThreadPoolExecutor, per-vote timeout | Use completed votes only |

### 4.3 Stage Orchestrator Fallback Patterns

| Stage | Pattern | Behavior |
|-------|---------|----------|
| Stage 2 | Batch enrichment | asyncio.gather(return_exceptions=True) + indexed retry |
| Stage 3 | Lazy init failures | Non-blocking: state_tracker/world_state/fact_ledger = None |
| Stage 4 | Blueprint preflight | Fail-open: always returns `{"passed": True}` on exception |

### 4.4 Non-Blocking Initialization (Stage 3)

```
StateTracker init → fail → app.state_tracker = None (non-blocking)
WorldState init   → fail → app.world_state = None (non-blocking)
FactLedger init   → fail → app.fact_ledger = None (non-blocking)
```

All lazy-init failures log WARNING but allow stage to continue. Downstream agents must null-check these.

---

## 5. Director Boundary Notes

### 5.1 Director as Routing Facade

**FACT**: Director (386 lines) delegates ALL decisions to 5 sub-modules:
- DirectorCachingManager — cache lifecycle
- DirectorGradingSystem — scoring, adaptive thresholds, state approval
- DirectorEnsembleSelector — candidate comparison, verdict gates
- DirectorContinuityValidator — entity/blueprint/manuscript continuity
- DirectorQualityAuditor — genre validation, character logic, 3-tier audit

Director itself contains no decision logic — it is purely a routing layer.

### 5.2 Verdict Flow

```
Candidate Generation (ArcEnsemble / BlueprintEnsemble / ChiefWriter)
  ↓ produces JSON proposals
Director.compare_and_select_*() / audit_manuscript()
  ↓ delegates to EnsembleSelector / QualityAuditor
  ↓ applies quality gates (force_reject, force_pass_with_fix, score_cap)
  ↓ applies adaptive threshold via GradingSystem
  ↓ returns PASS / PASS_WITH_FIX / REJECT
Orchestrator
  ↓ on PASS: proceed
  ↓ on PASS_WITH_FIX: enter patch loop (max 3)
  ↓ on REJECT: retry with feedback or fail
```

### 5.3 Quality Gate Flags

Python quality flags can modify Director verdicts:
- `force_reject: True` → REJECT regardless of Director LLM (structural disqualification)
- `force_pass_with_fix: True` + Director says PASS → downgrade to PASS_WITH_FIX
- `score_cap: int` → score clamped (never raised, only lowered)

These are one-directional: Python can add constraints but NEVER upgrade a Director REJECT to PASS.

### 5.4 Adaptive Threshold

DirectorGradingSystem.get_adaptive_threshold():
- Base range clamped: [45, 85]
- Modifiers: arc position (intro -5, climax +10), genre bonuses, retry penalty (-5/-10)
- `apply_adaptive_decision()` can upgrade REJECT → CONDITIONAL_PASS if score >= adaptive threshold
- **Inference**: This is the one path where a REJECT can be softened, but it is Director-internal (GradingSystem is a Director sub-module, not an external agent).

### 5.5 State Mutation Gating

`on_approve_workflow()` hardcoded LIMITS:
- `misunderstanding`: max_change 30
- `obsession`: max_change 30
- `wealth`: max_change 10,000
- `internal_energy`: max_increase 200, max_decrease -500

No agent can bypass this gate. SovereignApp calls on_approve_workflow() before applying any state_updates from ChiefWriter.

---

## 6. Side-Effect Sweep

### 6.1 File Writes

| Location | Write Target | Blocking? |
|----------|-------------|-----------|
| analyst.py:1458 | Episode production JSONL log | Non-blocking |
| base_agent.py:571 | DB save_llm_call() telemetry | Non-blocking (except pass on failure) |

No direct file creation in domain agent layer. All artifact writes delegated to DBManager or SovereignApp.

### 6.2 DB Writes

| Location | Operation | Scope |
|----------|-----------|-------|
| base_agent.py:511-594 | save_llm_call() | Per-LLM-call telemetry |
| base_agent.py:924 | _log_llm_call_to_db() | `except Exception: pass` (silent swallow) |
| stage2_orchestrator.py:322 | save_v20_anchor() | Arc anchor persistence |
| Director sub-modules | No direct DB writes | Delegates to SovereignApp |

### 6.3 Cache Mutations

| Cache | Location | Protection | TTL |
|-------|----------|-----------|-----|
| Gemini context cache | base_agent._context_caches | Lock + LRU (max 50) | 600s / 1800s |
| Quota exhaustion cache | base_agent._quota_exhausted_models | _quota_lock | 3600s |
| Manuscript cache | chief_writer._manuscript_cache | Per-instance (no lock) | Invalidated per ep_num change |
| State cache | state_extractor._state_cache | Per-instance (no lock) | Manual invalidation |
| Director caching | director_caching fields | Per-instance (no lock) | Session-scoped |

### 6.4 Global/Shared State Mutations

| State | Mutated By | When | Protection |
|-------|-----------|------|-----------|
| state_tracker.npc_registry | full_extract_from_arcs() | Stage 2/3 init | Once per stage, no concurrent access |
| state_tracker.financial_number_registry | full_extract_from_arcs() | Stage 2/3 init | Same |
| state_tracker.resolved_plots | full_extract_from_arcs() + list.append | Stage 2/3 init | Same |
| state_tracker.entity_destructions | full_extract_from_arcs() + list.append | Stage 2/3 init | Same |
| ChiefWriter state_updates | Proposed only, gated by Director | Stage 4 post-Director | on_approve_workflow() gate |

### 6.5 Logging Side Effects

| Level | Count | Key Patterns |
|-------|-------|-------------|
| ERROR | ~15 locations | Ensemble crash, parallel processing failure, critical enrichment error |
| WARNING | ~75+ locations | Quota exhaustion, JSON parsing failures, timeouts, advisory issues, cache failures |
| PerfTimer | Many | `[PerfTimer:AgentName] operation_name={duration}s` |

### 6.6 Silent Swallow Patterns

| Location | Exception Handler | Risk |
|----------|------------------|------|
| base_agent.py:806-808 | `except Exception: pass` (metrics end) | Lost diagnostic on metrics failure |
| base_agent.py:891-893 | `except Exception: pass` (metrics end) | Same |
| base_agent.py:924-925 | `except Exception: pass` (DB log) | Lost LLM call telemetry |

These were tagged in sweep-1 Phase 1 (C-1~5 silent swallow logging). Current state shows `pass` with no logging — **Inference**: the sweep addressed some but these 3 may remain as accepted risk (metrics/telemetry, not decision-path).

### 6.7 ThreadPoolExecutor Side Effects

6 parallel execution points:
1. ArcEnsemble: 3 strategies × workers
2. BlueprintEnsemble: 3 strategies × workers
3. ChiefWriter: 1-3 workers
4. ConsensusValidator: 3 perspectives
5. BlockEnricher: batch_size workers, 600s timeout
6. DirectorAuditor: min(3, vote_tasks) workers

All use `as_completed()` with per-future exception capture. Failed futures are logged and skipped, not re-raised.

### 6.8 Not Applicable

- **Config/env mutation**: No domain agent modifies config files or environment variables.
- **Rollback/compensation**: No explicit rollback paths. StateTracker full_extract is idempotent (re-runnable). PASS_WITH_FIX patch loop has no rollback — each iteration overwrites previous.
- **Console/UI output**: Via `_operator_log()` in BaseAgent (L364-383) — structured payload to UI layer, not direct print.
- **Bootstrap fallback**: Genre library fallback (genre-specific → base → empty dict) in Analyst.

---

## 7. Facts

1. **47 Python files** in modules/domain/agents/, ~40,753 LOC total.
2. **19 agent classes** extend BaseAgent; 12+ utility/helper classes do not.
3. **Director is a routing facade** (386 lines) delegating to 5 sub-modules.
4. **ValidationOrchestrator** runs 5+1 tiers: PRE-LLM → CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY.
5. **BlockingValidator** and **ConsensusValidator** (2/3 vote) are the only non-Director entities with hard REJECT authority.
6. **AdvisoryValidator** always returns `passed: True` — explicitly cannot REJECT.
7. **ManuscriptValidator** explicitly documents `REJECT 권한 없음` — advisory only.
8. **Python quality flags** (force_reject, force_pass_with_fix, score_cap) are one-directional: constrain but never upgrade.
9. **TF-22b** is live in code: `Director REJECT는 Python이 뒤집지 않음`.
10. **TF-36** is live in code: single candidate still requires LLM review, no auto-PASS.
11. **State mutations** are gated by `on_approve_workflow()` with hardcoded LIMITS.
12. **No agent** directly modifies StateTracker during Stage 4 — all proposals go through Director approval → SovereignApp.
13. **6 ThreadPoolExecutor** sites across domain agents, all with timeout and per-future exception handling.
14. **Model fallback chain**: gemini-2.5-pro → gemini-2.5-flash, with up to 9 API key rotation.
15. **3 silent swallow** `except Exception: pass` patterns remain in base_agent.py (metrics/telemetry paths).
16. **PASS_WITH_FIX** patch loop max 3 iterations in ThreePhaseBlueprintGenerator, with inplace/partial/full fix_scope.
17. **Context caching** (Gemini API) applied to 5 agents with 50KB minimum, 600s/1800s TTL.
18. **0 FIXME/HACK/WORKAROUND/TEMPORARY markers** found in domain agent code.
19. **1 TODO** in base_agent.py:604 — JSON schema mode expansion review (non-critical).
20. **25+ domain agent files** show as modified in git status — line ending normalization (CRLF→LF) pending commit.

---

## 8. Inferences

1. **Director sovereignty is well-enforced.** Multiple TF tags (TF-22b, TF-36, TF-C) confirm code-level guards. No live code path allows an external agent to override Director REJECT. The adaptive threshold mechanism is Director-internal.

2. **Python → LLM judgment boundary is mostly clean.** Python handles structural scoring (field completeness, char counts, scene minimums) and returns candidates for Director LLM comparison. The one notable wrinkle is `force_reject` flag filtering before Director sees candidates — this is structural disqualification, not semantic judgment, so likely compliant with 대원칙 1.

3. **ConsensusValidator timeout fallback to PASS may be risky.** When all 3 perspectives time out, the system returns PASS with 0.5 confidence. In a quota-exhausted scenario, this could let low-quality content through. This is a known fail-open design choice.

4. **Stage 4 blueprint preflight is fail-open by design.** `_preflight_validate_blueprint()` returns `{"passed": True}` on any exception. This means structural blueprint issues can silently pass into manuscript generation.

5. **Silent swallow in base_agent.py telemetry** (3 locations) means LLM cost tracking can silently fail. The pipeline continues but cost/token metrics may be incomplete.

6. **Cache coherency between agents relies on per-instance isolation**, not shared locks. Only `_context_caches` (Gemini API cache, class-level) uses a Lock. Agent-specific caches (manuscript_cache, state_cache) are per-instance with no concurrent access protection. This is safe only if no two threads access the same agent instance simultaneously — which appears to be the case given the ThreadPoolExecutor patterns spawn new agent instances per task.

7. **The on_approve_workflow() LIMITS are hardcoded.** Changes to state validation bounds require code modification. There is no config-driven override for these limits. This is intentional (prevents accidental loosening) but reduces operational flexibility.

8. **Ensemble parallelism is well-bounded.** All ThreadPoolExecutor usages have timeouts, per-future exception capture, and graceful degradation. No unbounded thread spawning observed.

---

## 9. Uncertainty / Contradictions

### 9.1 Uncertainty Items

| ID | Item | Uncertainty Level | Reason |
|----|------|-------------------|--------|
| U-1 | `force_reject` flag origin scope | MEDIUM | force_reject is set by Python pre-checks (structural). If any path sets force_reject based on semantic/narrative analysis, it would violate 대원칙 1. Need to verify all force_reject call sites beyond four_phase_arc_generator.py |
| U-2 | ConsensusValidator all-timeout behavior | LOW-MEDIUM | Code returns PASS with 0.5 confidence on full timeout. Effect in production unknown — frequency of full timeout not measurable from code alone |
| U-3 | Stage 4 preflight fail-open blast radius | LOW | Fail-open may let malformed blueprints into ChiefWriter. Downstream Director audit should catch issues, but adds unnecessary LLM cost. Production frequency unknown |
| U-4 | Silent swallow count vs sweep-1 claims | LOW | Memory says sweep-1 addressed C-1~5 silent swallow logging. 3 `except: pass` patterns remain in base_agent.py. Were these explicitly accepted as risk, or missed? |
| U-5 | Per-instance cache thread safety | LOW | ChiefWriter._manuscript_cache and StateExtractor._state_cache have no Lock. Safe only if agent instances are never shared across threads. Inferred from ThreadPoolExecutor patterns (new instances per task) but not verified via explicit contract |
| U-6 | Analyst ask() count (15+) | STALE-POSSIBLE | Memory notes Analyst as OPT-1 candidate for context caching (10+ ask() calls, 30-50K repeated context). Live code shows 15+ ask() calls but context caching not applied. Status of OPT-1 decision unknown |
| U-7 | director_ensemble.py line count discrepancy | LOW | One agent reported 26,025 lines, another reported ~1,952 lines. Likely measurement error in one agent. Need verification of actual LOC |
| U-8 | Director sub-module direct DB writes | LOW | Agents report "no direct DB writes" from Director sub-modules, but exhaustive verification of all director_*.py files for DB-touching patterns was not done line-by-line |

### 9.2 Contradiction Items

| ID | TF Claim | Live Code State | Assessment |
|----|----------|-----------------|------------|
| CT-1 | Memory: "2,114 passed + 68 xfailed" (Opus TF 감사 완료 기준) | git status shows 90+ test files modified (uncommitted). Test counts may have changed. | STALE-POSSIBLE — test count needs fresh run verification |
| CT-2 | Memory: sweep-1 "C-1~5 silent swallow logging" resolved | 3 `except Exception: pass` remain in base_agent.py (L806, 891, 924) | NEEDS VERIFICATION — may be intentionally accepted risk, or incomplete sweep |
| CT-3 | docs/2026-03-18 3-pass audit: "28 confirmed issues" (5 CRITICAL) | No corresponding execution SSOT or patch evidence in current git log | STALE/UNRESOLVED — audit findings may be documentation-only without realization |

---

## 10. Candidate Watchlist

### 10.1 High-Priority Watch Items

| ID | Area | Issue | Reason for Watch |
|----|------|-------|------------------|
| W-1 | ConsensusValidator | All-timeout → PASS (0.5 confidence) | Fail-open on critical validation tier. Could allow low-quality through in quota-exhausted scenarios |
| W-2 | Stage 4 Preflight | Fail-open `{"passed": True}` on exception | Silent structural issue passthrough. Adds unnecessary LLM cost at minimum |
| W-3 | force_reject scope | Python structural disqualification flag | Verify all call sites are genuinely structural, not semantic judgment |
| W-4 | base_agent.py silent swallows | 3x `except Exception: pass` in telemetry | Potential loss of cost/metrics data, hard to diagnose |

### 10.2 Medium-Priority Watch Items

| ID | Area | Issue | Reason for Watch |
|----|------|-------|------------------|
| W-5 | Analyst context caching | Not applied (15+ ask() calls with repeated context) | Potential cost optimization. Memory notes OPT-1 status |
| W-6 | StateTracker write-back | Stage 2 → Stage 3 → StateTracker sync | Historical bug (sweep-2 Phase 1, CRITICAL StateTracker 동기화 누락). Pattern requires ongoing vigilance |
| W-7 | Adaptive threshold [45,85] | Hardcoded bounds | If thresholds need adjustment, requires code change. No config-driven override |
| W-8 | PASS_WITH_FIX exhaustion | Max 3 patch iterations → adopt or REJECT | After exhaustion, last-patched version may still have known issues |

### 10.3 Low-Priority / Hygiene Items

| ID | Area | Issue |
|----|------|-------|
| W-9 | Line ending normalization | 25+ domain files modified (CRLF→LF), uncommitted |
| W-10 | 1 TODO in base_agent.py:604 | JSON schema mode expansion — non-blocking |
| W-11 | director_ensemble.py LOC discrepancy | Verify actual line count |

---

## 11. TF Evidence Notes

### 11.1 TF Tags Found in Live Domain Code

| TF Tag | File | Line Reference | Content | Live Status |
|--------|------|---------------|---------|-------------|
| TF-22b | director_ensemble.py | L1712 | `Director REJECT는 Python이 뒤집지 않음` | LIVE — code enforces |
| TF-36 | director_ensemble.py | L896 | `단일 후보라도 LLM 검토 없이 자동 PASS하지 않는다` | LIVE — code enforces |
| TF-36 | unified_blueprint_validator.py | L426 | `Director 없으면 REJECT — 디렉터 주권주의 위반 방지` | LIVE — code enforces |
| TF-C | director_ensemble.py | L1639 | `자동감점 제거 — Director 주권 존중 (대원칙 3)` | LIVE — code enforces |
| TF-C | director_ensemble.py | L1647 | `미응답 감점 제거 — Director 주권 존중` | LIVE — code enforces |
| TF-46 | three_phase_blueprint_generator.py | L570 | `PASS_WITH_FIX는 Director 주권 존중 — gate 미적용` | LIVE — code enforces |
| TF-25-04 | base_agent.py | L14 | `validation.yaml SSOT` | LIVE — configuration reference |
| TF-6-07 | director_grading.py | (implied) | Adaptive threshold range clamped [45,85] | LIVE — code enforces |
| V61.9 | unified_arc_validator.py | L175 | `CRITICAL만 REJECT, MAJOR는 경고로 Director에게 넘김` | LIVE — code enforces |
| TF-PLV-1 | validation_orchestrator.py | L208 | protagonist_name 전달 to PreLLMValidator | LIVE — code enforces |

### 11.2 TF-Related Test Coverage

| Test File | Test Count | TF Coverage |
|-----------|-----------|-------------|
| test_sweep28.py | 32 | Chain verification, cross-agent, multi-agent, quality dashboard, audit service |
| test_sweep29.py | 12 | Stage4ContextBuilder, ContinuityManuscript, DirectorQualityAuditor, BlockingValidator |
| test_sweep31.py | 11 | Integer coercion fixes (ArcCritic, DirectorAuditor, MultiAgentDeliberation, CrossAgentVerifier) |
| test_continuity_modules.py | ~70 | Continuity arc/blueprint/manuscript, DirectorQualityAuditor, BlockingValidator |
| test_four_phase_arc_generator.py | 15 | Arc generation, constraint compilation, validation |
| test_unified_arc_validator.py | 3 | State constraints, timeline fallback |
| test_base_agent.py | 14 | JSON parsing, error classification, context cache, logging |
| test_opus_tf5_e6_regressions.py | regression suite | TF phases 5-6 |
| test_pass_with_fix.py | PASS_WITH_FIX feature | Advisory fix path |
| test_tier4_ensemble_caching.py | ~150 lines | Context cache plumbing, prompt stub injection |

All domain agent test files: **0 xfail markers** — all tests expected to pass.

### 11.3 TF vs Live Code Alignment Summary

| Category | Aligned | Uncertain | Contradicted |
|----------|---------|-----------|-------------|
| Director sovereignty guards | 5 tags confirmed live | 0 | 0 |
| Python/LLM boundary | 3 tags confirmed live | 1 (force_reject scope) | 0 |
| Adaptive threshold bounds | 1 confirmed [45,85] | 0 | 0 |
| Silent swallow resolution | — | 1 (sweep-1 C-1~5 vs 3 remaining) | 0 |
| Test counts | — | 1 (2,114+68 xfailed may be stale) | 0 |

---

## Appendix: Core Dependency Map (Domain → Core)

Most frequently imported core modules by domain agents:

| Core Module | Domain Consumers | Purpose |
|-------------|-----------------|---------|
| validation.threshold_helper._threshold | 8+ agents | Config-driven threshold values |
| core.prompt_loader.PromptLoader | 7+ agents | YAML prompt template loading |
| core.constants (AIModels, GenreTypes, ManuscriptLimits, etc.) | 14+ agents | System-wide constants |
| core.llm_provider (LLMRequest, LLMResponse) | base_agent.py | LLM API abstraction |
| core.llm_router.get_shared_llm_router | base_agent.py | Model routing |
| core.hud_utils (build_hud_context, get_hud_trend_safe) | 3+ agents | HUD context for prompts |
| core.metrics_collector | base_agent.py | Cost/token tracking |
| core.response_schemas (ARC_DESIGN_SCHEMA, BLUEPRINT_SCHEMA) | 4+ agents | JSON schema definitions |
| core.genre_schema_builder | 4+ agents | Genre-specific schema building |
| core.adaptive_retry (retry_with_feedback) | analyst.py | Feedback-informed retry wrapper |
| core.fact_ledger | director_auditor.py | Numeric fact summarization |
| core.primitive_guard | four_phase_arc_generator.py | Constraint enforcement |

No reverse imports detected: domain agents do NOT import from main_a.py. Dependency flows inward only.
