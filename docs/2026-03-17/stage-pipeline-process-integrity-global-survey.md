# Stage Pipeline Process Integrity Global Survey

Date: 2026-03-17
Status: final
Canonical Path: `docs/2026-03-17/stage-pipeline-process-integrity-global-survey.md`
Related Evidence Manifest: `docs/2026-03-17/stage-pipeline-process-integrity-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent
- execute a bounded repo-wide system-track survey focused on `Stage pipeline process integrity`
- determine whether the current Stage 2/3/4 pipeline produces good manuscripts through a good process, rather than only closing isolated bugs
- unify the 2026-03-17 brainstorming themes into one live-code-governed process map
- stop at survey and prioritization; do not open realization work in this order

## 2. Scope Lock
- included paths:
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/context_advisor.py`
  - `modules/core/adaptive_retry.py`
  - `modules/core/world_state.py`
  - `modules/validation/continuity_validator.py`
  - `modules/domain/agents/chief_writer.py`
  - `modules/domain/agents/director_ensemble.py`
  - `modules/core/quality_dashboard.py`
  - `modules/core/pass_rate_monitor.py`
  - `modules/api/bridge_server.py`
  - targeted regression surfaces in `tests/`
- excluded paths:
  - broad `UI/` and `geuldobi-desktop/` full sweep
  - unrelated scripts, migrations, and desktop/product review
  - narrative `work_id` output quality review
  - runtime-mutating implementation work
- change-lock or canary constraints:
  - survey-only; no code patching
  - no fresh live run in this order
  - existing dirty tracked docs/log were preserved untouched
- baseline docs read:
  - system governance harnesses in `docs/implementation/`
  - 2026-03-17 planning-note bundle as hypothesis seed only

## 3. Coverage Matrix
- macro views covered:
  - Stage 2 -> Stage 3 -> Stage 4 control-flow spine
  - Director / Chief Writer authority split
  - persistence and operator-facing summary surfaces
- micro views covered:
  - hotspot ranking for context assembly, verdict semantics, repair/retry routing, and persistence
  - dominant mutable state and overloaded fields
- cross-cut views covered:
  - context density/ranking
  - authority boundaries
  - gate semantics
  - local repair semantics
  - retry/escalation semantics
  - persistence/observability linkage
- operational views covered:
  - targeted read-only regression shard execution
  - quality dashboard and bridge payload surfaces
- deferred surfaces:
  - broad desktop/UI shell topology
  - fresh runtime trace or canary bundle
  - execution-doc derivation and queue opening

## 4. Macro View

### Topology
- Stage 2 preflight builds retrieval shape, style summary, and reverse-feedback context before blueprint work
- Stage 3 orchestrator persists blueprint failure history and feeds Stage 2 through `stage_rejection_history`
- Stage 4 context builder assembles CW mandatory context, state summaries, SC retrieval results, and retrieval observations
- Stage 4 interview round drives candidate generation, validation, Director judgment, PASS_WITH_FIX, retry routing, and escalation overlays
- Stage 4 post processor persists state deltas into bible, state log, world state, and fact ledger
- quality dashboard + pass-rate monitor + bridge payload expose process traces to operators

### Authority Map
- Python owns collection, formatting, routing, and persistence glue
- Chief Writer owns candidate generation and patch/regenerate mechanics
- Director owns final qualitative judgment, but currently receives a very thick input bundle
- validators and advisories are nominally support layers, but some reference-only surfaces drift toward decision influence
- dashboard and bridge surfaces are read-only observability consumers, not primary policy engines

### Runtime / Control-Flow Spine
- `Stage2PreflightAnalysis` resolves retrieval/work-focus and can inject Stage3->2 reverse-feedback fallback
- `Stage3Orchestrator` appends structured Stage 3 reject history for later Stage 2 use
- `Stage4ContextBuilder` computes `_work_focus`, builds a large `_mc_parts` stack, then merges SC retrieval and non-SC blocks into `mandatory_context`
- `Stage4InterviewRound` runs:
  - round 0 full ensemble
  - Python pre-director validation
  - Director review with heavy `mandatory_context`
  - post-verdict hard gates
  - PASS_WITH_FIX loop or REJECT retry routing
- `Stage4PostProcessor` converts accepted output into durable state sinks and operator logs

### Subsystem Boundaries
- strong boundary:
  - persistence consumers (`world_state`, `fact_ledger`, `db_manager`) are separated from generation
- blurred boundary:
  - advisory/reference-only layers vs Director decision support
  - fix scope semantics vs retry strategy routing
  - retrieval result ranking vs final prompt composition ranking

## 5. Micro View

### Hotspot Ranking
1. `modules/core/stage4_interview_round.py`
   - central semantic overload point for verdicts, advisories, local repair, retry routing, and escalation
2. `modules/core/stage4_context_builder.py`
   - main context-density and ranking hotspot; high risk of useful retrieval being buried under bulky reference layers
3. `modules/core/stage4_post_processor.py`
   - durability hotspot where narrative deltas become canonical state and must survive re-injection
4. `modules/domain/agents/director_ensemble.py`
   - stable/variable prompt split exists, but caller-provided mandatory bulk still overwhelms hierarchy
5. `modules/core/context_advisor.py`
   - retrieval slot planner is useful, but it plans slots more than final section priority
6. `modules/core/adaptive_retry.py` + retry logic in Stage 4
   - retry policy is present, but budget meaning is split across several layers
7. `modules/core/quality_dashboard.py` / `modules/api/bridge_server.py`
   - observability is much better than before, but it reports process semantics rather than governing them

### High-Risk Files / Modules
- `stage4_interview_round.py`: overloaded semantic junction
- `stage4_context_builder.py`: mandatory context over-accumulation and trim policy
- `stage4_post_processor.py`: durable state sink correctness
- `director_ensemble.py`: decision-core vs appendix blur
- `context_advisor.py`: writer/director asymmetry around work focus

### Dominant Mutable State Surfaces
- `previous_attempt`
- `stage_rejection_history`
- `_last_strategy_budget` / `_last_strategy_count`
- `world_state._state`
- `fact_ledger._ledger`
- `mandatory_context` / `_director_mc_parts`
- dashboard histories (`validation_history`, `retrieval_observation_history`, patch monitor records)

### Dense Side-Effect Clusters
- Stage 3 reject lifecycle:
  - attempt summary
  - stage rejection history
  - cost record
  - dashboard validation
- Stage 4 accept lifecycle:
  - episode bible
  - state log
  - world state
  - fact ledger
  - quality dashboard
  - bridge/dashboard read model

## 6. Cross-Cut Integrity Matrix

| Surface | Current State | Primary Evidence | Integrity Note | Severity |
| --- | --- | --- | --- | --- |
| Context composition | mixed | `stage4_context_builder.py`, `context_advisor.py`, `tests/test_stage4_context_builder.py` | CW context has rich truth and retrieval material, but composition order and trim policy still favor accumulation over ranked consumption | P1 |
| Authority boundary | mixed | `stage4_interview_round.py`, `director_ensemble.py` | Director remains sovereign, but advisory/reference-only material is thick enough to behave like soft decision scaffolding | P1 |
| Gate semantics | mixed | `stage4_interview_round.py`, `quality-gate-semantics-outline.md`, targeted retry tests | verdict, score, fix scope, and downstream gate transitions still overlap semantically | P1 |
| Local repair semantics | mixed | `stage4_interview_round.py`, `tests/test_stage4_interview_round.py` | PASS_WITH_FIX is bounded and safer than naive patching, but still wider than a truly local repair contract | P1 |
| Retry / escalation control | mixed | `stage4_interview_round.py`, `adaptive_retry.py`, `chief_writer.py`, retry shards | round budget, repair budget, strategy budget, escalation budget, and guidance budget exist but are not surfaced as one coherent policy | P1 |
| Persistence durability | strong | `stage4_post_processor.py`, `world_state.py`, `continuity_validator.py`, `tests/test_stage4_post_processor.py` | relationship and pressure carry-over now travel through bible/state_log/world_state/validator paths durably | P2 |
| Observability | strong | `quality_dashboard.py`, `pass_rate_monitor.py`, `bridge_server.py`, bridge tests | process observability is materially improved; dashboard exposes quality signals, retrieval observations, patch effectiveness, proof status, and cost summary | P2 |
| Operator surface | bounded | `bridge_server.py` | bridge quality payload is sufficient for bounded process survey; full desktop/UI review was intentionally excluded | P3 |
| Contracts / config | mixed | threshold gates, prompt loader use in `director_ensemble.py` and Stage 4 modules | many thresholds and reference-only conventions exist, but semantic intent is spread across code and prompt text rather than one contract surface | P2 |
| Recovery / retry | mixed | `stage4_interview_round.py`, `adaptive_retry.py`, `pass_rate_monitor.py` | recovery exists and is test-backed, but routing meaning is harder to reconstruct than necessary | P1 |
| Cache / global state | mixed | `director_ensemble.py`, `quality_dashboard.py`, `stage4_interview_round.py` | caches and global-ish state improve cost and visibility, but add hidden coupling to retry and judgment context | P2 |
| Regression / canary | bounded-strong | targeted pytest shards, existing test surfaces | targeted regression evidence is good for bounded claims; no fresh live run means some runtime composition risk remains unexercised | P2 |
| Stale / shadow authority | mixed | planning notes + live code | brainstorming notes are now preserved, but only live code should govern; reference-only blocks inside runtime still act like shadow authority candidates | P2 |

## 7. Operational and Regression View

### Tests
- targeted read-only shards executed in memory-conservative sequence:
  - `tests/test_stage4_context_builder.py -k "plan_stage4_retrieval or work_slot_summary or active_pressure_vectors"` -> `2 passed`
  - `tests/test_stage4_interview_round.py -k "reduced_strategy_budget or full_strategy_budget or post_select_conflict or advisory"` -> `11 passed`
  - `tests/test_stage4_post_processor.py -k "relationship_changes or active_pressure_vectors"` -> `2 passed`
  - `tests/test_stage3_orchestrator.py -k "rejection_history"` -> `1 passed`
  - `tests/test_stage2_preflight.py -k "stage3_reverse_feedback"` -> `2 passed`
  - `tests/test_bridge_quality_summary.py -k "patch_effectiveness or quality_signal_snapshot"` -> `2 passed`

### Smoke / Canary
- no fresh live run or canary execution was opened in this order
- this survey therefore relies on:
  - live code reading
  - targeted regression surfaces
  - operator-surface code inspection

### Repair Tooling
- PASS_WITH_FIX loop exists and is bounded
- retry tooling includes:
  - inplace patch
  - patch-with-feedback
  - regenerate-with-feedback
  - ToT / MAD / ASP overlays
  - adaptive retry guidance injection

### Read-Only vs Mutation-Heavy Boundaries
- this order stayed fully read-only except for documentation outputs
- mutation-heavy paths (DB save, state log save, world-state update, bridge payload generation) were inspected through code and tests rather than live writes

## 8. Contradiction and Uncertainty Ledger

### Contradictions Closed
- persistence gap on relationship and threat carry-over is no longer the main open process blocker; live code now shows durable pressure and relationship paths from Stage 4 post-processing into continuity consumers
- Stage3->2 reverse-feedback persistence is no longer purely aspirational; reject history is now recorded and consumed by Stage 2 preflight logic
- observability is no longer mostly write-only; quality dashboard and bridge server now expose retrieval, quality-signal, patch-effectiveness, and proof-status summaries

### Contradictions Still Open
- `reference only` vs `decision support`
  - some runtime text explicitly labels advisory/stats as reference-only, but the prompt structure still places them in judgment context thick enough to influence outcomes
- `retrieval quality` vs `composition quality`
  - slot planning is present, but final prompt ordering still lets Tier 2 bulk bury Tier 1 retrieval value
- `repair scope` vs `verdict semantics`
  - current Stage 4 flow still lets verdict, fix scope, score, and routing bleed into each other

### Uncertainty Items
- whether Director-side and CW-side context restructuring should stay one lane or split into two lanes
- whether retry budget and PASS_WITH_FIX should stay one repair-policy lane or split into semantics vs execution-control
- how far bounded survey findings would shift under a fresh live run with long-context saturation

### Confidence Caps Still In Effect
- no hard cap from unresolved critical contradiction is active
- confidence is moderated by:
  - no fresh live run
  - no execution-doc derivation in this turn
  - bounded exclusion of full UI/desktop sweep

## 9. Severity and Action Map

### P1 Findings
- `P1-A` Context architecture remains accumulation-heavy
  - Fact:
    - Stage 4 writer computes work focus and slot summary, but the final prompt still mixes truth, retrieval, state tracker bulk, lookback, future-arc, and advisory material in one large composition path
  - Inference:
    - the main issue is not missing retrieval machinery but missing composition ranking and tier protection
  - Decision:
    - highest-ROI lane is `CW context architecture`, not raw retrieval expansion

- `P1-B` Director judgment semantics are overloaded
  - Fact:
    - Director receives candidate evidence plus a thick mandatory-context block containing advisory, Python warnings, reference-only stats, and conflict notes
  - Inference:
    - judgment quality risk is now more about hierarchy blur than missing evidence
  - Decision:
    - highest-ROI lane is `Director decision-core austerity + gate semantics cleanup`

- `P1-C` Local repair and retry policy are present but semantically split
  - Fact:
    - local patching, regenerate, reduced/full strategy budgets, ToT/MAD/ASP, and adaptive guidance all exist
  - Inference:
    - process readability suffers because retry budgets are distributed across multiple implicit layers
  - Decision:
    - highest-ROI lane is `local repair contract + retry budget policy cleanup`

### P2 Findings
- persistence/continuity and observability are materially improved and now support higher-level process refactors instead of blocking them
- these are not the first execution lanes unless new runtime contradictions are discovered under fresh live run conditions

### Action-Bearing Areas
- `lane-1`: CW context architecture
- `lane-2`: Director gate semantics and prompt austerity
- `lane-3`: PASS_WITH_FIX + retry architecture

### Areas With `no-execution-doc-required`
- none permanently
- all three action-bearing lanes are execution-worthy, but execution-doc creation was intentionally deferred by this survey-only stop line

## 10. Execution SSOT Mapping

| Area | Classification | Canonical Execution Doc | Notes |
| --- | --- | --- | --- |
| `lane-1: CW context architecture` | deferred action-bearing | none in this survey-only turn | derive from context-delivery + composition-ranking notes when explicit execution order is given |
| `lane-2: Director gate semantics and prompt austerity` | deferred action-bearing | none in this survey-only turn | derive from quality-gate-semantics + director-prompt-austerity notes when explicit execution order is given |
| `lane-3: PASS_WITH_FIX + retry architecture` | deferred action-bearing | none in this survey-only turn | derive from local-repair-contract + retry-budget-policy notes when explicit execution order is given |

## 11. Single SSOT Roadmap Lineage
- canonical roadmap: none in this survey-only bundle
- temp roadmap mirror: none
- execution order basis:
  - if explicit realization follows, order should start with `lane-1` and `lane-2` before `lane-3`
- lane or phase structure:
  - Phase 1: context architecture
  - Phase 2: judgment semantics
  - Phase 3: repair/retry semantics

## 12. Confidence Summary
- estimated score: `95/100`
- score rationale:
  - scope-complete within the bounded survey lock
  - macro + micro + cross-cut + operational views all covered
  - evidence triangulated across live code, structured search/test surfaces, and governance/planning lineage
  - contradiction and uncertainty ledger included explicitly
  - targeted regression shards confirm the most critical bounded claims
- closed gaps:
  - persistence durability and observability are no longer the primary blockers
  - Stage3->2 reverse feedback and Stage4 carry-over durability are live-code-backed, not speculative
- remaining gaps:
  - no fresh live run
  - no execution-SSOT bundle opened
  - bounded exclusion of full UI/desktop sweep
- final statement:
  - for the bounded `Stage pipeline process integrity` scope, this survey is sufficiently evidenced and internally consistent to support future execution planning at a 95% confidence gate
