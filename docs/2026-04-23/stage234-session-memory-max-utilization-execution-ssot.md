# Stage234 Session Memory Max-Utilization Execution SSOT

Date: 2026-04-23
Status: closed (3-pass audited; fresh re-audit PASS on 2026-04-24; upstream #5 proof gate closed; bounded Stage4 envelope seed plus persisted resume hydration landed; bounded Stage3 retrieval-window, budget, and repeated coverage-warning behavior hardening landed; bounded Stage2 retry-memory preservation landed; provider-native sidecars deferred)
Canonical Path: `docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md`
Temp Mirror Path: `none`
Commit State:
- Baseline Commit: `30b9436fc3a5c3fcc3f6397bf23bfe45d24af918`
- Baseline Dirty Summary: `dirty: modified docs/temp/queue-state.json from prior queue sync; untracked docs/2026-04-23/`
- Resume Commit: `fabf78127cbcdfb724c35a38f314a25b94ec9ce5`
- Resume Dirty Summary: `clean at branch open; current working tree carries bounded Stage4 envelope seed, persisted-attempt resume hydration, trim-resistant Stage4 carryover hardening, bounded Stage3 retrieval-window, budget, repeated coverage-warning behavior hardening, bounded Stage2 retry-memory preservation, targeted regressions, and fresh audit/SSOT metadata docs`
- Resume Drift Summary: `PR #11 merged the #5 proof-governor closure into main; fresh re-audit PASS is recorded in docs/2026-04-24/stage234-session-memory-fresh-reaudit-3pass-audit.md; same-day bounded rollout has now landed provider-neutral Stage4 session-memory envelope seeding plus persisted-attempt resume hydration`
Source Survey Docs:
- `docs/2026-04-23/stage234-session-memory-max-utilization-deep-dive-adversarial-3pass-audit.md`
- `docs/2026-04-23/authority-alignment-benchmark-operating-model-hardening-3pass-audit.md`
- `docs/2026-04-24/stage234-session-memory-fresh-reaudit-3pass-audit.md`
Evidence Artifacts:
- `config/models.yaml`
- `modules/core/providers/vertex_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/session_memory_envelope.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_optimizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage3_envelope_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/db_manager.py`
- `tests/test_base_agent.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_chief_writer.py`
- `tests/test_session_memory_envelope.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage2_optimizer.py`
- `tests/test_stage2_orchestrator.py`
- `tests/test_stage2_preflight.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py`
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: stage234-session-memory-max-utilization
  depends_on: []
  tranches:
    - id: cache-path-proof-producer-lanes
      title: Cache-path proof on current producer lanes
    - id: internal-session-memory-envelope-contract
      title: Internal session-memory envelope contract
    - id: stage4-first-runtime-hardening
      title: Stage4-first runtime hardening
    - id: stage3-budget-retrieval-hardening
      title: Stage3 budget and retrieval hardening
    - id: stage2-retry-memory-hardening
      title: Stage2 retry-memory hardening
    - id: optional-provider-native-sidecars
      title: Optional provider-native sidecars
  github_issue: 3
  status: completed
```

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
- A bounded read-only cache proof harness now exists at `scripts/audit_stage34_cache_proof.py`; it reads archived benchmark DB snapshots and surfaces Stage3/Stage4 producer cached-token evidence without changing runtime authority.
- Issue posture remains aligned with the survey:
- `#3` remains the direct rollout lane
- `#5` is now closed historical backing for the upstream proof and benchmark governor lane
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
   - use `scripts/audit_stage34_cache_proof.py` as the first bounded proof surface before any gate relaxation or provider-session rollout
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
- `pytest tests/test_audit_stage34_cache_proof.py -q`
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

- temp status: `opened current lane`
- cleanup condition:
  - keep the mirror while this lane remains a visible queued substrate program
  - remove or replace it only after closure or superseding narrower tranche SSOTs
- roadmap dependency:
  - now ranked first among visible rollout items after `authority-alignment-benchmark-operating-model-hardening` closure
  - upstream `#5` proof lane is satisfied and the 2026-04-24 fresh execution-start re-audit passed

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the 3-pass audit on the source survey and this SSOT
  - confirm at least 95% confidence against current `main`
  - then refresh `Resume Commit` and `Resume Drift Summary` before patching code from this document

## 14. 2026-04-24 First Implementation Unit

Status: bounded Stage4 session-memory envelope seed completed.

Implemented scope:
- Added `modules/core/session_memory_envelope.py` as a provider-neutral JSON-safe envelope builder.
- Attached `session_memory_envelope` to Stage4 attempt telemetry through `advisory_flags`.
- Projected the envelope into pass-rate payloads and persisted it into DB advisory payloads.
- Preserved provider-native cache/session features as optional sidecars; no provider API path was promoted to authority.
- Preserved existing DB schema; the envelope rides the existing `advisory_flags` JSON surface.

Tranche impact:
- Tranche 2, internal session-memory envelope contract: Stage4 seed completed.
- Tranche 3, Stage4-first runtime hardening: telemetry-facing envelope subset completed; persisted-attempt resume hydration moved into the bounded follow-up unit below.
- Stage3 and Stage2 consumption remain pending.

Validation:
- `py -3.12 -m pytest tests/test_session_memory_envelope.py tests/test_stage4_interview_round.py -q` -> 318 passed.
- `python scripts/check_utf8_hygiene.py ...` -> passed for touched code, tests, SSOT, roadmap, queue state, and fresh audit doc.
- Complexity recount: touched production functions remain below 120 LOC; largest touched function is `_build_stage4_db_attempt_payload` at 101 LOC.

## 15. 2026-04-24 Second Implementation Unit

Status: persisted-attempt resume hydration completed.

Implemented scope:
- Reused the provider-neutral envelope through `get_session_memory_envelope(...)` so persisted Stage4 advisory payloads can be replayed without trusting provider-native hidden state.
- Added persisted-attempt hydration in `modules/core/stage4_interview_round.py` to rebuild `previous_attempt` from the latest same-episode `stage_attempts` row, advisory flags, saved artifact text, and compacted prior attempts.
- Threaded `reject_bucket` through the envelope so restart/resume routing keeps the prior rejection lane visible to the next retry.
- Added orchestrator-side pre-round hydration in `modules/core/stage4_orchestrator.py` so restart/resume loads the hydrated attempt before the first retry turn and seeds fallback `director_feedback` from stored merged feedback when needed.
- Preserved the existing DB schema and provider-neutral authority posture; the runtime still reads from DB/advisory/artifact surfaces rather than provider-native session memory.

Tranche impact:
- Tranche 2, internal session-memory envelope contract: Stage4 advisory persistence plus resume-read path completed.
- Tranche 3, Stage4-first runtime hardening: persisted-attempt resume hydration completed.
- Stage4 trim-sensitive truth pinning and numeric baseline-promotion closure moved into the bounded follow-up unit below.
- Stage3 and Stage2 consumption remain pending.

Validation:
- `py -3.12 -m pytest tests/test_session_memory_envelope.py tests/test_stage4_interview_round.py tests/test_stage4_orchestrator.py::TestHandleRoundOutcomeErrorPaths::test_handle_round_outcome_hydrates_persisted_previous_attempt_before_first_round -q` -> 322 passed.
- `python scripts/check_utf8_hygiene.py modules/core/session_memory_envelope.py modules/core/stage4_interview_round.py modules/core/stage4_orchestrator.py tests/test_session_memory_envelope.py tests/test_stage4_interview_round.py tests/test_stage4_orchestrator.py docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md docs/temp/stage234-session-memory-max-utilization-execution-ssot.md docs/2026-04-24/stage234-session-memory-fresh-reaudit-3pass-audit.md` -> passed.
- Residual note: full `tests/test_stage4_orchestrator.py -q` still shows two unrelated `TestCrossEpisodeRepetitionHook` failures rooted in `modules/core/stage4_post_processor.py` deepcopying `sqlite3.Connection`; this tranche did not change that path.

## 16. 2026-04-24 Third Implementation Unit

Status: trim-resistant truth pinning and numeric contract carryover hardening completed.

Implemented scope:
- Preserved structured `truth_pin_items` inside `modules/core/session_memory_envelope.py` so post-select conflict pins survive persistence instead of collapsing away when they arrive as list-form contract metadata.
- Backfilled a stable top-level truth-pin summary from structured pins so persisted envelopes and resumed attempts keep provider-neutral pin keys such as opening continuity or proper-noun/asset drift anchors.
- Hardened `modules/core/stage4_interview_round.py` compact history snapshots to retain truth pins, truth-pin items, reuse contracts, repair contracts, scope authority/origin, and fix-pack provenance through retry-history trimming.
- Extended `modules/core/stage4_reject_runtime.py` carryover projection so reject retry contracts keep truth-pin and numeric-authority context when the runtime rebuilds the next attempt packet.
- Preserved the existing DB schema and provider-neutral authority posture; the added carryover remains derived from DB/advisory/conflict-contract surfaces rather than provider-native session state.

Tranche impact:
- Tranche 3, Stage4-first runtime hardening: trim-sensitive truth pinning completed.
- Tranche 3, Stage4-first runtime hardening: numeric baseline-promotion contract carryover completed for persisted/retry history and resume hydration surfaces.
- Stage4-first runtime hardening is now completed as a bounded tranche.
- Stage3 and Stage2 consumption remain pending.

Validation:
- `py -3.12 -m pytest tests/test_session_memory_envelope.py tests/test_stage4_interview_round.py -q` -> 323 passed.
- `python scripts/check_utf8_hygiene.py modules/core/session_memory_envelope.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py tests/test_session_memory_envelope.py tests/test_stage4_interview_round.py docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md docs/temp/stage234-session-memory-max-utilization-execution-ssot.md docs/2026-04-24/stage234-session-memory-fresh-reaudit-3pass-audit.md` -> passed.

## 17. 2026-04-24 Fourth Implementation Unit

Status: Stage3 anchor-aware retrieval-window hardening completed.

Implemented scope:
- Removed the extra `focus_window[-5:]` tail collapse in `modules/core/stage3_envelope_builder.py`.
- Reused the already bounded anchor-aware `blueprint_window` for Stage3 smart retrieval planning and work-focus resolution.
- Preserved the existing Stage3 bounded-history guardrails because `_select_stage3_anchor_recent_window(...)` still limits the source set to `24 recent + 6 anchor`.
- Kept the provider-neutral authority posture unchanged; only retrieval-planning inputs widened, with no DB/schema or provider-native state promotion.

Tranche impact:
- Tranche 4, Stage3 budget and retrieval hardening: broader anchor-aware retrieval window completed.
- Tranche 4, Stage3 budget and retrieval hardening: budget arbiter moved into the bounded follow-up unit below.
- Stage2 retry-memory hardening remains pending.

Validation:
- `py -3.12 -m pytest tests/test_stage3_orchestrator.py tests/test_stage3_orchestrator_lane_e.py tests/test_stage3_orchestrator_legacy_tail_lane_f.py tests/test_context_advisor.py -q` -> 137 passed.
- `python scripts/check_utf8_hygiene.py modules/core/stage3_envelope_builder.py tests/test_stage3_orchestrator_lane_e.py docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md docs/temp/stage234-session-memory-max-utilization-execution-ssot.md docs/2026-04-24/stage234-session-memory-fresh-reaudit-3pass-audit.md` -> passed.
- `python scripts/ops_validator.py --strict` -> PASS, errors=0, warnings=0.

## 18. 2026-04-24 Fifth Implementation Unit

Status: Stage3 semantic budget-arbiter hardening completed.

Implemented scope:
- Added a bounded Stage3 semantic-context budget arbiter in `modules/core/stage3_orchestrator.py`.
- Converted Stage3 semantic bundle assembly from blind prepend chaining into named sections so advisory blocks, work-focus summary, and retrieval context can be trimmed deterministically against `plan.total_budget_chars`.
- Reused the existing `ContextBudgetTracker` and `build_context_budget_ledger(...)` surfaces so Stage3 observability now records actual dropped chars, overflow, headroom, and trim state instead of only post-hoc over-budget detection.
- Preserved the work-focus summary as a protected section and surfaced whether it survived or was trimmed through `protected_summary_survived`, `trimmed_work_slot_summary`, and `mandatory_context_chars`.
- Added a regression test that fixes the Stage3 contract at the semantic bundle boundary: the final Stage3 semantic context must fit the configured cap, emit `semantic_ctx_budget_trimmed`, and keep the work-focus summary alive.

Tranche impact:
- Tranche 4, Stage3 budget and retrieval hardening: budget arbiter completed.
- Tranche 4, Stage3 budget and retrieval hardening: repeated-coverage-warning promotion remains pending bounded follow-up work.
- Stage2 retry-memory hardening remains pending.

Validation:
- `py -3.12 -m pytest tests/test_stage3_orchestrator.py tests/test_stage3_orchestrator_lane_e.py tests/test_stage3_orchestrator_legacy_tail_lane_f.py tests/test_context_advisor.py -q` -> 138 passed.
- `python scripts/check_utf8_hygiene.py modules/core/stage3_orchestrator.py tests/test_stage3_orchestrator.py docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md docs/temp/stage234-session-memory-max-utilization-execution-ssot.md docs/2026-04-24/stage234-session-memory-fresh-reaudit-3pass-audit.md` -> passed.
- `python scripts/ops_validator.py --strict` -> PASS, errors=0, warnings=0.

## 19. 2026-04-25 Sixth Implementation Unit

Status: Stage3 repeated coverage-warning behavior hardening completed.

Implemented scope:
- Added bounded Stage3 coverage-warning history helpers in `modules/core/stage3_orchestrator.py` that read recent `quality_dashboard.retrieval_observation_history` rows without adding DB schema or provider-native memory authority.
- Promoted repeated Stage3 `coverage_warnings` into deterministic behavior by injecting a `[Stage3 검색 커버리지 경고]` semantic section before budget arbitration when a warning repeats across current and recent Stage3 retrieval observations.
- Kept telemetry honest: the escalation advisory does not fake missing relationship slices or suppress the original `coverage_warnings`; it only instructs the next Blueprint generation to explicitly recover the missing axis.
- Threaded `repeated_coverage_warnings` and `coverage_warning_escalation_included` through Stage3 observability and persisted stage-attempt advisory flags.
- Restored one corrupted Stage3 relation-slice sentinel from mojibake to `[관계 의미 질의]` after byte-level UTF-8 read-back proved it was real source text, not console rendering.

Tranche impact:
- Tranche 4, Stage3 budget and retrieval hardening: repeated coverage-warning behavior promotion completed.
- Tranche 4 is now completed as a bounded Stage3 hardening tranche.
- Stage2 retry-memory hardening remains pending as the next substrate widening step.

Validation:
- `py -3.12 -m pytest tests/test_stage3_orchestrator.py -k "coverage_warning or semantic_context_metadata or normalizes_non_dict_result" -q` -> 3 passed.
- `py -3.12 -m pytest tests/test_stage3_orchestrator.py tests/test_stage3_orchestrator_lane_e.py tests/test_stage3_orchestrator_legacy_tail_lane_f.py tests/test_context_advisor.py -q` -> 139 passed.
- `python scripts/check_utf8_hygiene.py modules/core/stage3_orchestrator.py tests/test_stage3_orchestrator.py` -> passed.
- `git diff --check` -> passed.
- Complexity recount: `_finalize_stage3_blueprint_semantic_bundle` is 142 LOC after the patch; it remains a Stage3 semantic core plus observability sink boundary and stays below the 180 LOC high-risk band.

## 20. 2026-04-25 Seventh Implementation Unit

Status: Stage2 retry-memory preservation hardening completed.

Implemented scope:
- Extended `SessionFailureMemory` to retain richer Stage2 reject context: verdict-derived reason, details, retry directives, runtime advisory, selection reason, fix scope, fix-scope reasoning, and score-breakdown summary.
- Replaced the old recent-failure prompt collapse from `reason[:50]` with bounded head-plus-tail fitting so the newest failure keeps its actionable tail while older recent failures receive progressively smaller prompt budgets.
- Threaded Stage2 REJECT metadata from `Stage2Finalizer` into both `stage_rejection_history` and optimizer failure memory without adding DB schema, provider-native memory authority, or hidden state above existing stage-attempt/session-decision logs.
- Expanded Stage2 patch/retry feedback to include persisted `verdict_reason`, `runtime_advisory`, and `retry_directives`, and taught raw rejection-pattern fallback feedback to preserve retry directives and runtime advisories when the helper callback is unavailable.

Tranche impact:
- Tranche 5, Stage2 retry-memory hardening: richer retained feedback completed.
- Tranche 5, Stage2 retry-memory hardening: recency-aware prompt retention completed.
- Optional provider-native sidecars remain deferred behind internal substrate and benchmark gates.

Validation:
- `py -3.12 -m pytest tests/test_stage2_optimizer.py tests/test_stage2_finalizer.py -k "failure_memory or optimizer_failure or reject_metrics_records_optimizer_failure" -q` -> 3 passed.
- `py -3.12 -m pytest tests/test_stage2_preflight.py -k "build_patch_feedback" -q` -> 2 passed.
- `py -3.12 -m pytest tests/test_stage2_orchestrator.py -k "rejection_pattern_feedback or fit_prompt_text" -q` -> 2 passed.
- `py -3.12 -m pytest tests/test_stage2_optimizer.py tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_orchestrator.py tests/test_stage2_preflight_helpers.py -q` -> 245 passed.
- Complexity recount: touched Stage2 production functions remain below the 120 LOC caution band; largest touched function is `_record_stage2_reject_side_metrics` at 76 LOC.

## 21. 2026-04-25 Closure Note

Status: closed.

Realized scope:
- Tranche 1 cache-path proof remains satisfied by the upstream `#5` proof-governor closure and its retained historical evidence.
- Tranche 2 internal session-memory envelope contract landed through the provider-neutral Stage4 envelope seed and persisted advisory read/write path.
- Tranche 3 Stage4-first runtime hardening landed through persisted-attempt resume hydration, trim-resistant truth pins, and numeric carryover contract preservation.
- Tranche 4 Stage3 budget and retrieval hardening landed through anchor-aware retrieval-window expansion, semantic-context budget arbitration, and repeated coverage-warning behavior promotion.
- Tranche 5 Stage2 retry-memory hardening landed through richer retained feedback and recency-aware prompt retention.
- Tranche 6 optional provider-native sidecars remains intentionally deferred; no provider-native hidden state was promoted above DB, fact-ledger, world-state, anchors, explicit carryover packets, or stage-attempt/session-decision logs.

Verification summary:
- `py -3.12 -m pytest tests/test_stage2_optimizer.py tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_orchestrator.py tests/test_stage2_preflight_helpers.py tests/test_stage3_orchestrator.py tests/test_stage3_orchestrator_lane_e.py tests/test_stage3_orchestrator_legacy_tail_lane_f.py tests/test_context_advisor.py -q` -> 384 passed.
- `python scripts/check_utf8_hygiene.py modules/core/stage2_optimizer.py modules/core/stage2_finalizer.py modules/core/stage2_preflight.py modules/core/stage2_orchestrator.py tests/test_stage2_optimizer.py tests/test_stage2_finalizer.py tests/test_stage2_preflight.py tests/test_stage2_orchestrator.py docs/2026-04-23/stage234-session-memory-max-utilization-execution-ssot.md docs/temp/stage234-session-memory-max-utilization-execution-ssot.md` -> passed before temp cleanup.
- `git diff --check` -> passed.
- `python scripts/ops_validator.py --strict` -> PASS before closure cleanup with errors=0 and warnings=0.

Residual risks:
- Full repository test suite was not run under this closure pass; validation stayed on the touched Stage2/Stage3 memory and retrieval surfaces.
- The previously observed unrelated `tests/test_stage4_orchestrator.py::TestCrossEpisodeRepetitionHook` sqlite connection deepcopy failure remains outside this lane.
- Provider-native `Sessions`, `Live API`, and `Memory Bank` experiments remain future optional sidecars behind explicit fresh survey and benchmark gates.

Temp cleanup:
- execution SSOT mirror removed: yes, after canonical closure.
- roadmap mirror retained: yes, because three parked future-wave items remain in the aggregate temp queue.
- queue-state refreshed: yes, after removing the closed execution SSOT mirror.

Closure 3-pass audit:
- Pass 1 checked realized scope against the six execution tranches and confirmed the only unimplemented tranche is explicitly optional/deferred.
- Pass 2 checked verification evidence against touched Stage2/Stage3 surfaces and recorded the unrun full-suite boundary honestly.
- Pass 3 checked temp-queue cleanup ordering: canonical closure first, roadmap refresh second, temp mirror removal third, queue-state refresh and strict validator last.

Confidence: 96/100.
