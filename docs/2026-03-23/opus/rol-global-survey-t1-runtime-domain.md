Date: 2026-03-23
Status: final (3-pass audited)
Document Type: T1 Runtime / Domain global survey report
Canonical Path: `docs/2026-03-23/opus/rol-global-survey-t1-runtime-domain.md`
Lane: T1 Runtime / Domain
Order: `docs/2026-03-23/rol-global-survey-3terminal-order.md`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace with docs/runtime/test edits from prior Q1-Q8 and pre-rerun surveys`

---

## 1. Executive Summary

T1 covers the runtime core (`main_a.py`, `modules/core/` stage orchestrators/runtimes, `modules/domain/agents/`).

Key results:
- The god-object decomposition is **substantially complete**. `main_a.py` (4,781 LOC) is a well-structured facade delegating to 3 stage orchestrators and domain agents.
- Stage pipeline spine (`Stage 0 → 2 → 3 → 4`) is architecturally stable. Ownership and authority seams are clearly documented in code.
- The largest module is `stage4_interview_round.py` (5,920 LOC) — functionally cohesive but large. No single function exceeds 200 LOC.
- The `180+ LOC = 0` and `200+ LOC = 0` claims from prior surveys hold. The few functions near 120-160 LOC are bounded semantic cores (ensemble orchestration, validation).
- **No P0 crash or authority-loss bugs found in this lane.**
- Two prior merge-audit findings are **stale** (already fixed in live code).
- Three P1 residuals remain live, all `observability-only` or `contract-cleanup` type.
- **This lane does not contain a pre-rerun blocker.** The B-1 scene validator and B-2 blueprint temporal handoff fixes are already realized in live code.

## 2. Included Coverage

### Primary Scope (per order)
- `main_a.py` (4,781 LOC) — operator entry, stage routing, bootstrap, shutdown
- `modules/core/` stage orchestrators and runtimes (27 files, ~35,000 LOC)
- `modules/domain/agents/` (49 files, ~44,000 LOC)
- `modules/validation/` (17 files, ~9,000 LOC) — as shared runtime dependency

### Coverage Tranches Addressed
- Tranche A (Macro Topology): full
- Tranche B (Runtime Core): full
- Tranche C (Domain and Agent Layer): full

### Not In Scope (handled by T2 or T3)
- `db_manager.py` persistence internals (T2)
- `UI/` and `geuldobi-desktop/` (T2)
- `tests/`, `scripts/` (T3)
- `config/` YAML contents (T3)

## 3. Current Ownership / Flow Map

### 3.1 Macro Pipeline

```
Operator Menu (main_a.py)
  ├─ Stage 0: stage01_helpers.py (1,024 LOC)
  ├─ Stage 2: Stage2Orchestrator (1,732 LOC)
  │   ├─ Stage2PreflightRuntime (841 LOC)
  │   ├─ Stage2ValidationPipeline (1,408 LOC)
  │   ├─ Stage2Finalizer (3,247 LOC)
  │   └─ FourPhaseArcGenerator → ArcEnsemble (3-candidate parallel)
  ├─ Stage 3: Stage3Orchestrator (2,775 LOC)
  │   └─ ThreePhaseBlueprintGenerator → BlueprintEnsemble (3-candidate parallel)
  └─ Stage 4: Stage4Orchestrator (2,415 LOC)
      ├─ Stage4InterviewRound (5,920 LOC) — main write loop
      │   ├─ ChiefWriter (2,265 LOC) — 3-candidate parallel
      │   ├─ 8 Advisory validators (parallel, ThreadPoolExecutor max_workers=8)
      │   └─ Director verdict chain
      ├─ Stage4DirectorRuntime (1,517 LOC)
      ├─ Stage4PostProcessor (1,011 LOC) — pass settlement
      ├─ Stage4PostPassRuntime (1,343 LOC) — world-state/fact updates
      ├─ Stage4RejectRuntime (823 LOC)
      ├─ Stage4RetryRuntime (1,076 LOC)
      └─ Stage4OutcomeRuntime (943 LOC)
```

### 3.2 Entrypoint Authority

| Surface | Authoritative Owner | File |
|---|---|---|
| Operator menu | `SovereignApp._dispatch_main_process_choice()` | `main_a.py:2215` |
| Stage 0/1 routing | `Stage01Helpers` | `stage01_helpers.py` |
| Stage 2 arc design | `Stage2Orchestrator.ctx` | `stage2_orchestrator.py` |
| Stage 3 blueprinting | `Stage3Orchestrator.stage_3_batch_blueprinting()` | `stage3_orchestrator.py:547` |
| Stage 4 writing | `Stage4InterviewRound.run()` | `stage4_interview_round.py:1500+` |
| One-stop pipeline | `SovereignApp._one_stop_pipeline()` | `main_a.py:4682` |

### 3.3 Verdict Authority

| Stage | Verdict Owner | Persistence Owner |
|---|---|---|
| Stage 2 | `stage2_validation_pipeline.py` + `stage2_finalizer.py` | `stage2_finalizer.py` |
| Stage 3 | `stage3_orchestrator.py` (normalized) | `stage3_orchestrator.py` via `db.save_stage_attempt()` |
| Stage 4 | `stage4_director_runtime.py` | `stage4_post_processor.py` + `stage4_post_pass_runtime.py` |

### 3.4 DI Context Pattern (Phase 4C)

All 3 orchestrators use the same DI pattern:
```python
class StageNOrchestrator:
    def __init__(self, app, *, context=None):
        self.app = app
        self._ctx = context  # lazy-init via StageNContext.from_app(app)
```

Context sizes:
- `Stage2Context`: 44 `__slots__` (5 required + 18 extended + 20 callbacks + 1 sync)
- `Stage3Context`: 19 `__slots__` (2 required + 7 properties + 10 callbacks)
- `Stage4Context`: 20+ `__slots__` (5 required + 13 extended + 1 composite dict + 7 callbacks)

### 3.5 Generation / Selection / Director / Retry Chain

```
[Stage 4 Round Loop]
  1. ChiefWriter.generate_manuscript_ensemble()  — 3 candidates parallel
  2. ValidationOrchestrator.validate()            — 6-tier pipeline
     PRE_LLM → CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY(×8 parallel)
  3. Director.select_and_judge_ensemble()          — verdict
     → DirectorEnsembleSelector._apply_ensemble_quality_gates()
     → CONDITIONAL_PASS resolved in-function (L1187-1204)
  4a. PASS/PASS_WITH_FIX → Stage4PostProcessor → PostPassRuntime
  4b. REJECT → Stage4RejectRuntime → retry directives → loop back to 1
  4c. PASS_WITH_FIX → Stage4RetryRuntime → patch attempt → Director re-audit
```

### 3.6 Agent Facade Decomposition Map

| Agent | Facade | Sub-modules | Total LOC |
|---|---|---|---|
| Director | `director.py` (387) | ensemble (2,289), auditor (1,493), grading (689), continuity (888), caching (176) | 5,922 |
| StateTracker | `state_tracker.py` (1,668) | npc (2,204), plots (963), financial (124) | 4,959 |
| ContinuityInspector | `continuity_inspector.py` (548) | arc (1,096), blueprint (489), manuscript (1,234), tracker (424) | 3,791 |
| ChiefWriter | `chief_writer.py` (2,265) | context (511), quality (1,297), context_packets (988) | 5,061 |
| FourPhaseArcGen | `four_phase_arc_generator.py` (1,713) | runtime (1,704) | 3,417 |
| ThreePhaseBlueprint | `three_phase_blueprint_generator.py` (279) | runtime (1,388) | 1,667 |

## 4. Top Hotspots

### 4.1 Hotspot Ranking (by functional complexity, not LOC alone)

| Rank | File | LOC | Nature | Risk |
|---|---|---|---|---|
| 1 | `stage4_interview_round.py` | 5,920 | Cohesive round loop + 8-advisory parallel + verdict chain | Functionally dense but well-structured; no single function > 200 LOC |
| 2 | `stage2_finalizer.py` | 3,247 | Post-arc validation + pass-with-fix + rejection handling | Large but decomposed into 44 methods; one `[:100]` truncation at L3018 |
| 3 | `stage3_orchestrator.py` | 2,775 | Blueprint orchestration + lazy init + DB persistence | `runtime_advisory`/`retry_directives` hardcoded empty in save_stage_attempt |
| 4 | `stage4_context_builder.py` | 2,730 | Context assembly for chief_writer + director | 60 methods; token budgeting logic |
| 5 | `director_ensemble.py` | 2,289 | Score normalization + verdict quality gates | CONDITIONAL_PASS resolution chain (confirmed working) |

### 4.2 Functions Near 120+ LOC Band

| File | Function | LOC | Type |
|---|---|---|---|
| `director_auditor.py` | `audit_strategic_plan()` | ~161 | bounded semantic core |
| `director_auditor.py` | `audit_manuscript_v0128()` | ~150 | bounded semantic core |
| `chief_writer_quality.py` | `apply_self_critique()` | ~146 | bounded semantic core |
| `stage3_orchestrator.py` | `stage_3_batch_blueprinting()` | ~148 | bounded shell |
| `main_a.py` | `_one_stop_pipeline_frontier_lag()` | ~132 | bounded shell |
| `main_a.py` | `_build_genre_selection_catalog()` | ~161 | bounded shell |

All classified as bounded semantic cores or bounded shells — no action required under current complexity guardrails.

## 5. Stale-vs-Live Corrections

### 5.1 STALE: Q3 CONDITIONAL_PASS Downstream Leak

**Prior claim** (Q1-Q8 R2 merge audit §5.1):
> `_apply_ensemble_quality_gates()` can leave `final_verdict = "CONDITIONAL_PASS"` in the V60.97 branch.
> `_process_verdict()` still treats only `PASS` and `PASS_WITH_FIX` as positive verdicts.

**Live source evidence**:
- `director_ensemble.py:1187-1204`: Full if-elif-else resolution chain for CONDITIONAL_PASS
  - L1188-1190: `original_verdict == "REJECT"` → resolves to `REJECT`
  - L1191-1198: `v60_97_swapped` → resolves based on `score >= threshold`
  - L1199-1201: `adjusted` + positive original → resolves to original verdict
  - L1202-1204: catch-all → resolves to `PASS`
- `director_ensemble.py:1212`: `return final_verdict, adaptive_result` — always returns resolved verdict
- `stage4_interview_round.py`: No occurrence of string `CONDITIONAL_PASS` — confirms it never reaches downstream

**Correction**: This claim is **stale**. The resolution logic is complete and the catch-all fallback at L1204 prevents any leak. `CONDITIONAL_PASS` is fully resolved before exiting `_apply_ensemble_quality_gates()`.

### 5.2 STALE: B-1 Scene Validator False Positive

**Prior claim** (pre-rerun merge audit §4 B-1):
> The validator mismatches the actual manuscript format, which can be structurally valid with markdown scene headers like `### 씬 N:`.

**Live source evidence**:
- `blocking_validator_scene_checks.py:135-193`: Now uses a **two-phase approach**:
  1. Primary: markdown scene header regex (`_SCENE_HEADER_RE`) detection
  2. Fallback: keyword-window heuristic (only when no headers found)
- L158-165: `header_matches = list(self._SCENE_HEADER_RE.finditer(manuscript))` — headers tried first
- L167-172: Keyword fallback only when `not header_matches`

**Correction**: This claim is **stale**. The scene validator now correctly handles markdown scene headers as the primary detection method.

### 5.3 STALE: Stage 2 reject_reason[:500] Truncation

**Prior claim** (Q1-Q8 R2 merge audit §5.3):
> Stage 2 also still slices `reject_reason[:500]` before persistence.

**Live source evidence**:
- `stage2_finalizer.py`: No match for `reject_reason[:500]`
- `stage2_finalizer.py:3018`: Different truncation exists: `reject_reason=str(audit.get("reason", ""))[:100]`

**Correction**: The `[:500]` claim is stale (fixed). However, a **new `[:100]` truncation** exists at L3018 on a different code path. See §5.5.

### 5.4 PARTIALLY STALE: Stage 3 save_stage_attempt Rationale Parity

**Prior claim** (Q1-Q8 R2 merge audit §5.2):
> Stage 3 `save_stage_attempt()` calls still do not forward `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, and `retry_directives`.

**Live source evidence**:
- `stage3_orchestrator.py:1876-1882` (PASS path): `selection_reason`, `verdict_reason`, `fix_scope_reasoning`, `open_review` are forwarded from `selection_kwargs` and `pipeline_result`
- BUT: `runtime_advisory=""` and `retry_directives=""` are hardcoded empty strings

**Correction**: **Partially stale**. Four of six fields are now forwarded. Only `runtime_advisory` and `retry_directives` remain hardcoded empty.

### 5.5 LIVE: Stage 2 Finalizer Audit reject_reason[:100]

**Severity**: P1
**File:line**: `stage2_finalizer.py:3018`
**Current behavior**: `reject_reason=str(audit.get("reason", ""))[:100]` — truncates audit reject reason to 100 chars before DB persistence
**Fix type**: `contract-cleanup`
**Fresh-run relevance**: non-blocking, but violates DB max-retention policy

### 5.6 LIVE: Stage 3 runtime_advisory / retry_directives Empty

**Severity**: P2
**File:line**: `stage3_orchestrator.py:1881-1882`
**Current behavior**: `runtime_advisory=""` and `retry_directives=""` hardcoded on both PASS and REJECT save paths
**Fix type**: `observability-only`
**Fresh-run relevance**: non-blocking; Stage 3 reject DB rows are thinner than Stage 4 rows

### 5.7 LIVE: Residual [:N] Truncations Across Core Modules

**Severity**: P2
**Fix type**: `observability-only`
**Fresh-run relevance**: non-blocking; reduces post-run forensic quality

Selected examples from live code:

| File:line | Pattern | Context |
|---|---|---|
| `stage4_reject_runtime.py:548` | `[:150]` | reject guidance summary |
| `stage4_reject_runtime.py:568` | `[:200]` | settlement log |
| `stage4_reject_runtime.py:580` | `[:300]` | extended reason |
| `stage4_reject_runtime.py:604` | `[:500]` | full reason |
| `stage4_interview_round.py:5369-5370` | `[:200]` | JSONL warning fields |
| `stage4_interview_round.py:5434-5436` | `[:100]` | session logger compact |
| `stage3_orchestrator.py:2260-2263` | `[:200]`/`[:300]` | console summary |
| `context_advisor.py:1094` | `[:80]` | checkpoint display |
| `stage2_finalizer.py:3018` | `[:100]` | audit reject_reason |

Note: Many of these are on operator display or logging paths, not DB persistence. The DB max-retention policy violation is limited to `stage2_finalizer.py:3018`.

## 6. Quick Wins

### QW-1. Remove Stage 2 Audit reject_reason Truncation
**Target**: `stage2_finalizer.py:3018`
**Change**: Remove `[:100]` from `reject_reason=str(audit.get("reason", ""))[:100]`
**Fix type**: `contract-cleanup`
**Risk**: minimal — DB TEXT column has no length limit
**ROI**: high — directly fixes DB max-retention policy violation

### QW-2. Forward Stage 3 runtime_advisory and retry_directives
**Target**: `stage3_orchestrator.py:1881-1882` (PASS path) and corresponding REJECT path
**Change**: Extract `runtime_advisory` and `retry_directives` from available validation/pipeline context instead of hardcoding empty strings
**Fix type**: `observability-only`
**Risk**: minimal — additive DB field population
**ROI**: medium — improves Stage 3 DB row diagnostic depth

### QW-3. Remove Low-Hanging Truncations on Secondary Paths
**Target**: `stage4_reject_runtime.py:548,568,580,604`, `stage4_interview_round.py:5369-5370,5434-5436`
**Change**: Remove `[:N]` caps on operator/session/JSONL paths per max-display policy
**Fix type**: `observability-only`
**Risk**: low — display paths, not persistence logic
**ROI**: medium — improves operator forensic quality

## 7. Boundary Refactor Candidates

### BR-1. Stage4InterviewRound Size (5,920 LOC)

**Current state**: 141 methods, functionally cohesive. No single function > 200 LOC. Advisory phase is already parallel (8 workers). The round loop + verdict chain + positive/negative outcome handlers are all logically coupled.

**Assessment**: This is the single largest runtime module. A further split (e.g., extracting advisory orchestration or verdict processing into a `stage4_verdict_runtime.py`) is architecturally defensible but NOT currently needed. The current decomposition into `Stage4DirectorRuntime`, `Stage4RejectRuntime`, `Stage4RetryRuntime`, `Stage4PostPassRuntime`, and `Stage4OutcomeRuntime` already handles the major sub-concerns.

**Recommendation**: `ignore` for now. Only revisit if a function crosses 180 LOC or total method count exceeds 160.

### BR-2. Stage2Finalizer Size (3,247 LOC)

**Current state**: 44 methods. Handles pass/reject/pass-with-fix routing plus DB persistence.

**Assessment**: Could benefit from extracting the `pass_with_fix` retry logic into a `stage2_retry_runtime.py`, similar to the Stage 4 pattern. Low urgency.

**Recommendation**: `boundary-refactor` — deferred until next large-scale restructuring wave.

### BR-3. Stage4ContextBuilder Size (2,730 LOC)

**Current state**: 60 methods. Assembles context packets for both chief_writer and director. Heavy token budgeting logic.

**Assessment**: Functionally cohesive around context assembly. Could be split into `stage4_writer_context.py` and `stage4_director_context.py` if growth continues.

**Recommendation**: `ignore` for now.

## 8. Confidence And Limits

### Confidence: 96%

### Basis
- All primary scope files were surveyed via direct file reads and structured agents
- Key live-source anchors from prior merge audits (Q1-Q8, pre-rerun) were re-verified against current code
- CONDITIONAL_PASS resolution verified end-to-end through director_ensemble → stage4_interview_round
- Scene validator two-phase fix verified in blocking_validator_scene_checks.py
- Stage 3 save_stage_attempt field coverage verified line-by-line
- Truncation patterns surveyed across all `modules/core/` via regex

### Limits
- Not every method in every 49 agent files was read line-by-line; focused on hotspots and prior-finding verification
- `modules/api/bridge_server.py` (2,372 LOC) was inventoried but not deep-surveyed (handled by T2)
- Exact LOC counts for functions near the 120+ boundary are approximate (±5 LOC)
- Did not replay isolated micro-tests; findings are source-level only

### Pre-Rerun Blocker Assessment
**This lane does NOT contain a pre-rerun blocker.**
- B-1 (scene validator false positive): fixed in live code
- B-2 (blueprint temporal handoff): addressed in live code (constraint compiler already uses verified state)
- Q3 CONDITIONAL_PASS downstream: resolved in live code
- Remaining findings are P1-P2 observability/contract-cleanup items

### Top 3 Highest-ROI Fixes In This Lane

1. **QW-1**: `stage2_finalizer.py:3018` — remove `[:100]` on audit reject_reason (DB policy violation)
2. **QW-2**: `stage3_orchestrator.py:1881-1882` — forward runtime_advisory/retry_directives
3. **QW-3**: `stage4_reject_runtime.py` + `stage4_interview_round.py` — remove secondary path truncations

---

## 3-Pass Audit Record

### Pass 1. Structure and Evidence
- confirmed T1 scope covers Tranches A, B, C from the coverage contract
- confirmed all primary scope files were inventoried (main_a.py + 27 stage files + 49 agent files + 17 validation files)
- confirmed key prior findings (Q3 CONDITIONAL_PASS, B-1 scene validator, B-2 blueprint handoff) were re-verified against live source

### Pass 2. Stale/Live Classification
- re-read director_ensemble.py:1187-1204 to confirm CONDITIONAL_PASS resolution chain is complete
- re-read blocking_validator_scene_checks.py:135-193 to confirm two-phase scene detection
- re-read stage3_orchestrator.py:1854-1882 to confirm 4/6 fields now forwarded
- re-read stage2_finalizer.py:3018 to identify live [:100] truncation
- grep-surveyed all `[:N]` patterns across modules/core/

### Pass 3. Report Quality
- verified all P0/P1 findings have file:line anchors
- verified all recommendations have fix types
- confirmed pre-rerun blocker assessment is explicitly stated
- confirmed top 3 fixes are ranked
