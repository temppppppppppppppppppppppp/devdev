# Stage234 Session Memory Max-Utilization Execution SSOT

Date: 2026-04-23
Status: execution-ready (3-pass audited; parked future wave; downstream rollout lane gated by independent #5 proof lane)
Canonical Path: `docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage234-session-memory-max-utilization-execution-ssot.md`
Commit State:
- Baseline Commit: `30b9436fc3a5c3fcc3f6397bf23bfe45d24af918`
- Baseline Dirty Summary: `dirty: modified docs/temp/queue-state.json from prior queue sync; untracked docs/2026-04-23/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `2026-04-23 issue-5 formalization re-audit split the upstream proof governor into its own execution lane and moved this item to rank 2 with an explicit dependency`
Source Survey Docs:
- `docs/2026-04-23/stage234-session-memory-max-utilization-deep-dive-adversarial-3pass-audit.md`
- `docs/2026-04-23/authority-alignment-benchmark-operating-model-hardening-3pass-audit.md`
Evidence Artifacts:
- `config/models.yaml`
- `modules/core/providers/vertex_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/stage2_optimizer.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage3_envelope_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/db_manager.py`
- `tests/test_base_agent.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_chief_writer.py`
- `tests/test_stage2_optimizer.py`
- `tests/test_stage4_interview_round.py`
Side-Effect Coverage: covered

## 1. Intent

- Convert the 2026-04-23 survey into one execution-ready SSOT for the `S2-S3-S4` session-memory lane.
- Keep this lane honest as a queued substrate program, not a front-active implementation order.
- Preserve current SSOT governance: hard truth remains in DB, fact-ledger, world-state, anchors, and explicit carryover packets.

## 2. Baseline Facts

- Current `main` routes the core Stage2, Stage3, and Stage4 producer lanes back through `vertexai:gemini-*`.
- `VertexAIProvider` remains a plain `generate_content(...)` path, but usage payloads can already surface `cached_content_token_count`.
- `BaseAgent` already contains a live context-cache substrate, but local gating still requires `cache.min_content_chars = 50000`.
- Stage3 already carries a bounded history window of `24 recent + 6 anchor` with a `36` item cache cap.
- Stage4 has the richest retry-memory substrate today, including persisted attempts and operator-facing summary surfaces, but no general runtime resume hydrator was found on current `main`.
- Issue posture remains aligned with the survey:
  - `#3` remains the direct rollout lane
  - `#5` is now a separate upstream proof and benchmark governor lane with its own execution SSOT
  - `#6` keeps this work coupled to authority and donor structure rather than isolated

## 3. Scope

Included:

- `config/models.yaml`
- provider capability and cache-call surfaces in `modules/core/providers/`
- `modules/domain/agents/base_agent.py`
- Stage2 retry and truncation surfaces in `modules/core/stage2_preflight.py` and `modules/core/stage2_optimizer.py`
- Stage3 history, budget, retrieval, and cache-adjacent surfaces in `modules/core/stage3_orchestrator.py` and `modules/core/stage3_envelope_builder.py`
- Stage4 retry, resume, persistence, and patch-lineage surfaces in `modules/core/stage4_interview_round.py`, `modules/core/stage4_reject_runtime.py`, and `modules/core/db_manager.py`
- queue artifacts for this execution lane

Excluded:

- provider-native memory as SSOT
- immediate `Vertex Live API` or `Agent Engine Sessions` migration
- donor-structure implementation work from `#4`
- unrelated Stage4 owner-surface refactors
- manual artifact rewrites under `projects/`

## 4. Pass 1. Inventory Summary

- Five memory families already exist on current `main`:
  - hard-truth memory
  - retrieval memory
  - session-local retry memory
  - prompt-prefix cache substrate
  - observability memory
- Highest-value live hotspots are:
  - `BaseAgent` cache creation and reuse
  - Stage3 windowing and budget competition
  - Stage4 retry-loop continuity across restart and trimming
  - Stage2 `SessionFailureMemory` preservation and truncation policy
- The workspace does not lack memory surfaces; it lacks normalization, proof-grade observability, and trim- or restart-resistant reuse.

## 5. Pass 2. Semantic Classification

- Class A: upstream proof dependency
  - cache hit or miss visibility
  - cached-token accounting
  - continuity, retry-count, and cost deltas now belong to the standalone `#5` lane
- Class B: provider-neutral memory substrate
  - one internal session-memory envelope that survives provider swaps
- Class C: Stage4-first runtime hardening
  - resume hydration
  - trim-resistant pinning
  - numeric baseline-promotion closure
- Class D: Stage3 budget and retrieval policy
  - one pre-generation arbiter
  - broader anchor-aware retrieval
- Class E: Stage2 retry-memory preservation
  - richer retained feedback
  - recency-aware retention instead of over-lossy collapse
- Class F: optional provider-native sidecars
  - `Sessions`
  - `Live API`
  - `Memory Bank`

## 6. Side-Effect Map

- file writes / artifacts:
  - this document wave writes canonical and temp execution docs plus roadmap refreshes
  - later implementation tranches would affect benchmark summaries, proof snapshots, and possibly stage-level audit artifacts
- DB / schema / transaction boundaries:
  - no schema change is authorized in the initial benchmark and cache-proof tranches
  - if envelope persistence needs new fields or joins, re-audit before patching
- JSONL / log / audit sinks:
  - likely proof targets include `quality_metrics.jsonl`, `runtime_audit_summary.json`, session decision logs, and stage-attempt lineage joins
  - logging may be extended for cache-hit or envelope-use observability, but logs remain non-authoritative
- console / UI / operator output:
  - dashboard or bridge summaries may gain cache or resume proof readouts
  - operator-facing verification should remain explicit about authority vs telemetry
- rollback / recovery / retry:
  - Stage4 and Stage3 retry semantics are directly affected by this lane
  - restart-safe hydration must not bypass Director authority or post-pass truth gates
- cache / global state:
  - `BaseAgent._context_caches`, project-service cache clears, state extractors, and app-side cached summaries are relevant
  - cache behavior must be measured before any threshold relaxation
- bootstrap fallback / config-env mutation:
  - initial tranches may touch cache thresholds or provider capability handling
  - no environment mutation is authorized in this execution packet

## 7. Realization Architecture

- Use a substrate-first, benchmark-gated sequence.
- Prove the existing cache path before introducing new provider session machinery.
- Define one internal session-memory envelope that can hold:
  - recent compressed summary
  - truth pins
  - last accepted verdict surface
  - retry directives and retry budgets
  - carryover packet references
  - coverage-warning history
  - optional cache-lineage metadata
- Roll out by stage in the order already supported by issue `#3` and the codebase: `Stage4 -> Stage3 -> Stage2`.
- Keep provider-native session features as optional sidecars until the internal envelope and benchmark proof show clear need.

## 8. Execution Tranches

1. Cache-path proof on current producer lanes
   - consume the upstream `#5` proof substrate for cache hit, cached-token, retry-count, continuity, and cost deltas
   - verify real cache reuse on Stage4 and Stage3 heavy shared-context paths
   - benchmark the local `50000`-char gate instead of assuming it is correct
2. Internal session-memory envelope contract
   - define one provider-neutral substrate for retries, resumes, and stage handoff
3. Stage4-first runtime hardening
   - implement persisted-attempt resume hydration
   - protect trim-sensitive truth pins
   - close numeric baseline-promotion seams
4. Stage3 budget and retrieval hardening
   - add one budget arbiter
   - stop over-narrow retrieval from `focus_window[-5:]`
   - promote repeated coverage warnings into behavior
5. Stage2 retry-memory hardening
   - retain richer failure memory
   - make truncation more recency-aware
6. Optional provider-native sidecars
   - test `Sessions`, `Live API`, or `Memory Bank` only after internal and benchmark gates are satisfied

## 9. Acceptance Criteria

- Producer lanes expose proof-grade cache hit or miss visibility and `cached_content_token_count` where supported.
- The local `cache.min_content_chars = 50000` rule is benchmarked before any reduction is proposed.
- One provider-neutral session-memory envelope contract is written and tied to real retry and handoff surfaces.
- Stage4 has a defined persisted-attempt resume-hydration path before wider Stage3 or Stage2 rollout.
- No provider-native hidden state is promoted above DB, fact-ledger, world-state, anchors, or explicit carryover packets.

## 10. Verification Plan

- `pytest tests/test_base_agent.py -q`
- `pytest tests/test_blueprint_ensemble_generate_ensemble.py -q`
- `pytest tests/test_chief_writer.py -q`
- `pytest tests/test_stage2_optimizer.py -q`
- `pytest tests/test_stage4_interview_round.py -q`
- sequential low-memory shards only; no `xdist` or parallel pytest
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not treat provider-native memory as authority.
- Do not pivot the main pipeline to `Live API` first.
- Do not treat session logs as replay truth.
- Do not lower the cache gate without measurement.
- Do not start code realization from this SSOT without a fresh 3-pass re-audit against the live workspace state.

## 12. Temp Queue Notes

- temp status: `parked future wave`
- cleanup condition:
  - keep the mirror while this lane remains a visible queued substrate program
  - remove or replace it only after closure or superseding narrower tranche SSOTs
- roadmap dependency:
  - ranked second behind `authority-alignment-benchmark-operating-model-hardening`
  - may not promote to front-active until the upstream `#5` proof lane is satisfied enough to make memory deltas measurable

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the 3-pass audit on the source survey and this SSOT
  - confirm at least 95% confidence against current `main`
  - then refresh `Resume Commit` and `Resume Drift Summary` before patching code from this document
