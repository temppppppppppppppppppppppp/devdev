Date: 2026-03-23
Status: final (3-pass audited, orientation scope)
Document Type: system-track orientation pack
Canonical Path: `docs/2026-03-23/llm-codebase-orientation-pack.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-20/TF-static-complexity-audit-v2.md`
- `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md`
Evidence Basis:
- live production-source structure under `main_a.py + modules/**/*.py`
- current readability/refactor snapshot after `180+ = 0`, `200+ = 0`, `300+ = 0`, `500+ = 0`

Commit State:
- Baseline Commit: `203b328fb35633f9a23fe986862994c8b6dddab7`
- Resume Commit: `same-as-live-workspace`
- Resume Drift Summary: `orientation-only doc; no separate drift baseline`

## 1. Purpose
- Give an LLM a short, stable map of the production codebase without replaying the whole refactor history.
- Reduce search cost for three common questions:
  - where does a request enter?
  - who owns the final decision or persistence?
  - where should console/audit/DB truth be checked?

This is not a full audit, changelog, or narrative design document. It is a navigation pack.

## 2. Reading Order
When entering the codebase cold, use this order.

1. [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py)
   - top-level operator menu, project binding, Stage 0/2/3/4 entry routing, shutdown
2. Stage 0 control plane
   - [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
   - [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py)
3. Stage 2 arc design
   - [stage2_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
   - [stage2_preflight_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_preflight_runtime.py)
   - [stage2_validation_pipeline.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py)
   - [stage2_finalizer.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
4. Stage 3 blueprinting
   - [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
   - [three_phase_blueprint_runtime.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py)
5. Stage 4 production
   - [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
   - [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
   - [stage4_director_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_director_runtime.py)
   - [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)
   - [stage4_post_pass_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py)
6. Shared domain runtimes
   - [four_phase_arc_runtime.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_runtime.py)
   - [director_ensemble.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py)
   - [chief_writer.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py)
   - [chief_writer_context_packets.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer_context_packets.py)
7. Persistence and state
   - [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py)
   - [world_state.py](/c:/Users/User/Desktop/글도비/modules/core/world_state.py)
   - [fact_ledger.py](/c:/Users/User/Desktop/글도비/modules/core/fact_ledger.py)
   - [pass_rate_monitor.py](/c:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py)

## 3. Topology
The production pipeline is still best understood as:

`Stage 0 -> Stage 2 -> Stage 3 -> Stage 4`

The current structure is not a flat god-object anymore. The pattern is:
- `main_a.py` / `SovereignApp`: operator-facing owner and entry routing
- `*_orchestrator.py`: stage owner shells and top-level flow control
- `*_runtime.py`: cohesive runtime authority modules extracted from oversized owners
- `*_post_*` or `*_finalizer.py`: sink and persistence boundaries
- domain agents under `modules/domain/agents/`: strategy, generation, audit, ensemble, and validation cores

Practical rule:
- if a function mostly routes, pauses, or coordinates, start at the owner/orchestrator
- if a function mostly performs generation or adjudication, drop into the runtime/agent module
- if the question is "was it saved", follow the post-processor/finalizer/DB path

## 4. Authority Map
Use this map for “who is final”.

### 4.1 Operator Entry Owner
- [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py)
- Owns:
  - genre/project selection
  - top-level Stage 0/2/3/4 entry
  - one-stop and frontier-lag control plane
  - shutdown and session-level persistence

### 4.2 Stage 0 Authority
- Operator submenu owner:
  - [stage01_helpers.py](/c:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py)
- Reference-analysis authority:
  - [stage0/__init__.py](/c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py)

### 4.3 Stage 2 Authority
- Stage owner:
  - [stage2_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py)
- Preflight and per-attempt analysis authority:
  - [stage2_preflight_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_preflight_runtime.py)
- Validation and reject metrics authority:
  - [stage2_validation_pipeline.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py)
- Pass finalization and constraint/state side effects:
  - [stage2_finalizer.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)

### 4.4 Stage 3 Authority
- Stage owner:
  - [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- Blueprint generation runtime:
  - [three_phase_blueprint_runtime.py](/c:/Users/User/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py)

### 4.5 Stage 4 Authority
- Stage owner:
  - [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- Round execution and retry/reject loop owner:
  - [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- Director review and prevalidation authority:
  - [stage4_director_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_director_runtime.py)
- PASS settlement owner shell:
  - [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)
- Post-pass world-state / manager / advisory runtime:
  - [stage4_post_pass_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py)
- `_god1_*` authority channel:
  - 7 round-local attributes smuggled via instance mutation from [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py) `_run_validation_phase()` (producer) to [stage4_director_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_director_runtime.py) `run_pre_director_validation()` (consumer)
  - predates the runtime split; both sides carry ownership comments

### 4.6 Final PASS/REJECT Truth
- Stage 2:
  - validation/finalizer split between [stage2_validation_pipeline.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_validation_pipeline.py) and [stage2_finalizer.py](/c:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
- Stage 3:
  - final blueprint verdict is normalized on [stage3_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py)
- Stage 4:
  - director verdict authority lives in [stage4_director_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_director_runtime.py)
  - pass-result persistence authority lives in [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py)

## 5. Contract Map
The codebase is easier to follow if contracts are grouped by role rather than by file.

### 5.1 Operator-Facing Contracts
- `ui.log(...)`
  - human-visible progress and result lines
- one-stop / frontier-lag payloads
  - next action, stop reason, delta counts

### 5.2 Verdict Contracts
- common fields seen across Stage 2/3/4:
  - `final_verdict`
  - `director_verdict`
  - `gate_basis`
  - `score`
  - `selection_reason`
  - `verdict_reason`
  - `error_category`

Practical rule:
- `final_verdict` is the durable adjudication field
- `director_verdict` is the raw upstream director result when post-gates or contract normalization may have changed the final outcome
- `gate_basis` explains which post-gate or contract rule produced the final outcome
- Internal validation tier results use tier-specific schemas (`passed`/`failures`/`violations`/`warnings` vs `unjustifiable_violations`/`score_penalty`); see [validation_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py) L82-181 for per-tier shapes

### 5.3 Attempt/Persistence Contracts
- attempt-key identity:
  - built through `logging_keys.build_attempt_key(...)`
- pass-rate sink:
  - [pass_rate_monitor.py](/c:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py)
- DB attempt rows:
  - `save_stage_attempt(...)`
  - `save_director_selection(...)`
- artifact linkage:
  - `candidate_key`
  - `content_hash`
  - `artifact_path`

### 5.4 State / World Contracts
- world-state change application:
  - [world_state.py](/c:/Users/User/Desktop/글도비/modules/core/world_state.py)
- fact-ledger accumulation:
  - [fact_ledger.py](/c:/Users/User/Desktop/글도비/modules/core/fact_ledger.py)
- Stage 4 manager delta and state-log persistence:
  - [stage4_post_pass_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py)

## 6. Observability Map
If the question is "what happened", follow these sinks in this order.

### 6.1 Console
- `ctx.ui.log(...)` or `self.ui.log(...)`
- best for:
  - current stage
  - current attempt
  - wait heartbeat
  - top-line verdict/result

### 6.2 Audit
- [main_a.py](/c:/Users/User/Desktop/글도비/main_a.py) `_audit_event(...)`
- best for:
  - bounded structured event summaries
  - success/failure milestones

### 6.3 Pass-Rate / Metrics
- [pass_rate_monitor.py](/c:/Users/User/Desktop/글도비/modules/core/pass_rate_monitor.py) `record_attempt(...)`
- metrics JSON under project logs
- best for:
  - stage/episode/arc attempt history
  - final verdict, token cost, duration

### 6.4 DB Truth
- [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py)
- stage-attempt, director-selection, manuscript, episode-bible, state-log, and related sidecar tables
- best for:
  - durable truth after a run

### 6.5 Current Gap Model
The recent observability investigation found:
- durable sinks often carry more detail than console
- console is improving, but middle-of-run wait states and causal summaries were historically thinner
- operator-surface regressions that appeared during the long-function campaign were mostly:
  - stale gating
  - mojibake source strings
  - not authority or persistence loss

See [opus-pass-reject-logging-integrity-survey-report.md](/c:/Users/User/Desktop/글도비/docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md#L1).

## 7. How To Read a Hot Path
Use this sequence.

1. Find the owner entry in `main_a.py` or the stage orchestrator.
2. Identify the delegated runtime/agent authority.
3. Identify the verdict contract fields.
4. Identify the persistence owner.
5. Identify the console/audit/pass-rate sinks.

Example:
- "Why did Stage 4 pass"
  - start at [stage4_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
  - follow into [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
  - inspect [stage4_director_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_director_runtime.py) for verdict/gate basis
  - inspect [stage4_post_processor.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py) and [stage4_post_pass_runtime.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py) for settlement/persistence

## 8. LLM-Friendliness Rules
For this codebase, the highest-value non-refactor aids are:
- short phase-boundary comments
- ownership comments where a name looks pure but mutates state or caches
- payload/envelope docstrings where a dict/dataclass mixes operator-facing and persistence-facing fields
- consistent causal logs for PASS/REJECT and long waits

Avoid:
- line-by-line narration
- repeating UI text in comments
- adding comments to obvious thin delegates

## 9. Fast Heuristics
- If a file name contains `orchestrator`, expect owner shell + routing.
- If a file name contains `runtime`, expect cohesive semantic authority.
- If a file name contains `finalizer`, `post_processor`, or `post_pass`, expect sink and persistence boundaries.
- If a question is about “truth”, prefer DB/audit/pass-rate over console.
- If a question is about “what is happening now”, prefer console and heartbeat logs first.

## 10. Known Limits
- This pack is intentionally compressed. It does not enumerate every helper family.
- `100+` bounded semantic cores still exist; they are no longer emergency hotspots, but they still require local reading.
- Historical docs may describe older ownership; current live workspace and current canonical dated docs win.
- Post-survey resolved items (2026-03-23): comment/doc/observability follow-ups from the merged LLM-friendliness post-survey have been realized; see `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md` for the full scope.

## 11. 3-Pass Audit Record
Pass 1. Structure and Coverage
- includes entry flow, owner map, contract map, observability map, and reading order
- PASS

Pass 2. Consistency with Current SSOT
- aligns with the current readability snapshot and the pass/reject integrity survey
- no deprecated `200+`/`300+` hotspot framing retained
- PASS

Pass 3. Compression and Usefulness
- optimized for navigation rather than exhaustive explanation
- sections are short enough to use as an LLM onboarding map
- PASS

## 12. Confidence
Estimated confidence: `97%`

Reasoning:
- high confidence on stage ownership and sink boundaries because those are already stabilized in canonical audit/report docs
- high confidence on the current hotspot framing because `180+ = 0` and `200+ = 0` are current SSOT values
- lower confidence only on future drift if ownership changes again without this map being refreshed
