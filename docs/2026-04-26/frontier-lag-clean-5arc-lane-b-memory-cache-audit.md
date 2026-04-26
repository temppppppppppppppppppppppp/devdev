# Frontier Lag Clean 5-Arc - Lane B Memory And Cache Audit

Date: 2026-04-26
Status: read-only audit, parent terminal synthesis after two subagent passes
Document Type: Lane B report under `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
Canonical Path: `docs/2026-04-26/frontier-lag-clean-5arc-lane-b-memory-cache-audit.md`
Temp Mirror: not applicable; lane reports are not execution SSOTs
Baseline Commit: `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
Baseline Dirty Summary:
- `M 0_temp.txt`
- `?? docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `?? docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
- `?? projects/0_골든카나리아/`

## 1. Scope

Lane B answers one bounded question: **are session memory and context caching actually applied in the current `main` workspace and in the observed 5-arc Frontier Lag run, stage by stage?**

Strictly read-only. No code patches. No tests run. Two subagents executed in parallel:

- Subagent A: code/test surfaces (`modules/`, `tests/`).
- Subagent B: observed-run telemetry (`projects/0_골든카나리아/project_data.db`, `projects/0_골든카나리아/logs/`).

Out of scope:
- The Stage3 ep4 binding/prevalidation root cause itself (Lane A).
- External methodology and vendor docs (Lane C).
- Continuity bridge design (Lane D).
- Harness `process_success` vs `objective_success` semantics (Lane E).
- Adversarial governance (Lane F).

Governance constraints honoured:
- Python collects evidence; LLM/Director judges narrative truth.
- Provider-native memory and cache are not treated as authoritative.
- Cache hits are never equated with story memory.

## 2. Evidence

### 2.1 Code surface anchors (from Subagent A)

Envelope contract:
- `modules/core/session_memory_envelope.py:6` `SESSION_MEMORY_ENVELOPE_VERSION = "session-memory-envelope-v1"`
- `modules/core/session_memory_envelope.py:7` `SESSION_MEMORY_ENVELOPE_KEY = "session_memory_envelope"`
- `modules/core/session_memory_envelope.py:92` `build_stage4_session_memory_envelope(...)` produces fields: `schema_version`, `source="stage4_attempt"`, `stage=4`, `ep_num`, `arc_num`, `attempt_num`, `attempt_key`, `session_id`, `candidate{candidate_key,content_hash,artifact_path}`, `verdict_surface`, `retry_surface`, `truth_pins`, `truth_pin_items`, `carryover_refs`, `cache_lineage`, `coverage_warnings`.
- `modules/core/session_memory_envelope.py:192` `cache_lineage` is built from `advisory.get("cache_lineage")`.
- `modules/core/session_memory_envelope.py:196` `attach_session_memory_envelope(advisory_flags, envelope)`.
- `modules/core/session_memory_envelope.py:209` `get_session_memory_envelope(advisory_flags)`.

Stage4 application:
- `modules/core/stage4_interview_round.py:8348-8402` `_with_stage4_session_memory_envelope(...)` builds and attaches.
- `modules/core/stage4_interview_round.py:8631-8657` envelope attached to attempt payload before persistence.
- `modules/core/stage4_interview_round.py:2176-2290` `_hydrate_stage4_previous_attempt_from_row(...)` extracts envelope on resume (line 2190 `envelope = get_session_memory_envelope(advisory_flags)`).
- `modules/core/stage4_orchestrator.py:1794-1822` pre-round hydration call `hydrate_persisted_stage4_previous_attempt(...)`.
- `modules/core/stage4_reject_runtime.py:222-253` carryover projection through reject retry contract.

Stage3 application (negative evidence):
- `grep -n session_memory_envelope modules/core/stage3_orchestrator.py` -> NO MATCHES.
- `grep -n session_memory_envelope modules/core/stage3_envelope_builder.py` -> NO MATCHES.
- Stage3 surfaces `prompt_envelope` (a budget summary) and Stage3-specific advisory flags only.

Stage2 application (negative evidence):
- `grep -n session_memory_envelope modules/core/stage2_orchestrator.py modules/core/stage2_optimizer.py modules/core/stage2_finalizer.py modules/core/stage2_preflight.py` -> NO MATCHES across all four files.
- `modules/core/stage2_optimizer.py` contains `SessionFailureMemory` (prompt-side recency-aware failure list, not a persisted envelope).

Cache substrate:
- `modules/domain/agents/base_agent.py:2376` `_context_caches = {}` class store.
- `modules/domain/agents/base_agent.py:2379` `_MIN_CACHE_CONTENT = int(_SYSTEM_CFG.get("cache", {}).get("min_content_chars", 50000))`.
- `modules/domain/agents/base_agent.py:2615` `_ask_with_cached_context(cache_name, prompt, ...)`.
- `modules/domain/agents/base_agent.py:757-800` `_log_context_cache_attempt_to_db(...)`.
- `modules/domain/agents/base_agent.py:152-173` `_context_cache_lineage_is_current(...)` and `_context_cache_lineage_bypass_reason(...)`.
- `modules/core/providers/gemini_provider.py:41` and `modules/core/providers/vertex_provider.py:145` surface `cached_content_token_count`.

DB schema:
- `modules/core/db_bootstrap_runtime.py:480-506` `context_cache_attempts` columns: `id, ts, stage, ep_num, agent_name, model, cache_type, project_name, content_chars, min_content_chars, ttl_seconds, cache_outcome, cache_reason, cache_name, content_hash, error_msg`.
- `modules/core/db_manager.py:3254-3310` `save_context_cache_attempt(...)`.
- `modules/core/db_bootstrap_runtime.py:529` `("advisory_flags", "TEXT")` on `stage_attempts`.
- `modules/core/db_bootstrap_runtime.py:470` `("cached_tokens", "INTEGER")` on `llm_calls`.

Tests:
- `tests/test_session_memory_envelope.py` 4 tests cover build / attach / get / truth-pin items, including explicit `cache_lineage` assertion.
- `tests/test_base_agent.py:980-1040` four `cached_context_*` lineage tests.
- `tests/test_audit_stage34_cache_proof.py:115-149`, `tests/test_audit_stage34_cache_gate_corpus.py:73-99` reproduce the `context_cache_attempts` schema for proof harness corpora.
- No tests cover Stage3 or Stage2 envelope persistence (negative evidence: cross-grep returns Stage4-only).

### 2.2 Observed-run telemetry (from Subagent B)

Session id: `20260426_171126`. DB: `projects/0_골든카나리아/project_data.db`.

`stage_attempts` row counts: stage2=2, stage3=4, stage4=3 (9 rows total).

Envelope-key membership in each row's parsed `advisory_flags` JSON:

| stage | ep | attempt | total_keys | session_memory_envelope | cache_lineage |
|---|---|---|---|---|---|
| 2 | 1 | a1 | 5 | False | False |
| 2 | 2 | a1 | 5 | False | False |
| 3 | 1 | a1 | 19 | False | False |
| 3 | 2 | a1 | 17 | False | False |
| 3 | 3 | a1 | 17 | False | False |
| 3 | 4 | a10 | 19 | False | False |
| 4 | 1 | a1 | 8 | True | True (nested `{}`) |
| 4 | 2 | a1 | 11 | True | True (nested `{}`) |
| 4 | 2 | a2 | 10 | True | True (nested `{}`) |

`cache_lineage` is a nested key inside the Stage4 envelope (sibling of `truth_pins`, `coverage_warnings`). On every Stage4 row in this run it serializes as the empty dict `{}`.

`context_cache_attempts` distribution (28 rows total, 100% `skipped`):

| cache_reason | rows |
|---|---|
| content_too_short | 26 |
| vertex_api_key_explicit_cache_unsupported | 2 |

Per-stage skipped distribution: stage2=4, stage3=16, stage4=8. Gate `min_content_chars=50000` on every row. Observed `content_chars` ceilings: stage2 <=15,020; stage3 <=19,579; stage4 <=60,461 (the 60,461 row was rejected by the explicit-cache-unsupported reason, not by size).

`llm_calls.cached_tokens` reality across 130 rows:

| metric | value |
|---|---|
| rows with cached_tokens > 0 | 3 |
| sum(cached_tokens) | 44,007 |
| max(cached_tokens) | 14,669 |
| `context_cache_outcome` distinct values | only NULL |

The three non-zero rows are all Stage3 ep4 BlueprintEnsemble fan-out within a 20-second window:
- id=101 ts=2026-04-26T18:17:36 cached=14,669
- id=102 ts=2026-04-26T18:17:38 cached=14,669
- id=103 ts=2026-04-26T18:17:56 cached=14,669

Every row has NULL `context_cache_name`, `context_cache_content_hash`, `context_cache_outcome` -- provider-implicit, no client lineage written.

Stage3 ep4 terminal failure (`stage_attempts` id=9, attempt 10):
- `verdict=FAILED`, `score=95`, `failure_category=validation_contradiction`, `initial_verdict=PASS_WITH_FIX`.
- `reject_reason` literal contains: `contradictions=메타데이터 타임라인 불일치: Blueprint의 시간 흐름은 '2006년 1월 1일'로 설정되어 있으나, Arc 상태는 '2006년 1월 3일'을 요구함.`
- `director_selections` id=9: `final_verdict=FAILED`, `downstream_override_applied=1`, `verdict_reason` ends `binding prevalidation repair required`.
- No `blueprints` row for ep4 (only ep1/ep2/ep3 persisted). No `content_hash` / `artifact_path` bound (`runtime_audit_summary.json` `artifact_metadata_missing` ledger).

Worker-level shape:
- `auto_frontier_lag_worker_result.json`: `status=success`, `arcs_advanced=1`, `requested_limit_hit=false`, `stop_reason=stage3_user_abort`.
- `auto_frontier_lag_analysis.json`: `judgment=failed`, `root_cause=requested_arc_boundary_not_reached`.
- `runtime_audit.jsonl` 24 events; only `blueprint_fail: ep_4_all_retries_exhausted` carries the failure semantics. No `timeline_drift`, `binding_prevalidation_*`, `cache_*`, or `session_memory_*` event types exist.

## 3. Findings

### 3.1 Stage-by-stage verdict table

| Stage | Session memory envelope | Context cache (client) | LLM-side cached tokens | Verdict (memory) | Verdict (cache) |
|---|---|---|---|---|---|
| Stage2 | NOT applied (no `session_memory_envelope` key on any of 2 rows; `SessionFailureMemory` is prompt-side only) | NOT applied (4/4 attempts skipped, all `content_too_short`; ceiling 15,020 chars vs 50,000 gate) | none (0 of 20 stage2 `llm_calls`) | NOT APPLIED | TELEMETRY-ONLY |
| Stage3 | NOT applied (no envelope key on any of 4 rows; only Stage3-specific advisory flags such as `gate_semantics`, `repair_contract`, `coverage_warnings`, `prompt_envelope` budget summary) | NOT applied (16/16 attempts skipped, all `content_too_short`; ceiling 19,579 chars vs 50,000 gate) | provider-implicit only (3 ep4 BlueprintEnsemble fan-out rows, 14,669 cached_tokens each, no client lineage written) | NOT APPLIED | TELEMETRY-ONLY (provider-implicit credit visible, no client cache events) |
| Stage4 | APPLIED (envelope key present on 3/3 rows; `cache_lineage` nested but empty `{}`; persisted into `stage_attempts.advisory_flags`; hydrated on resume via `get_session_memory_envelope` + `_hydrate_stage4_previous_attempt_from_row`) | NOT applied (8/8 attempts skipped: 6 `content_too_short`, 2 `vertex_api_key_explicit_cache_unsupported`) | none (0 of 54 stage4 `llm_calls`) | APPLIED (substrate; cache_lineage slot empty) | TELEMETRY-ONLY |

Top-line numerical anchors:
- Memory envelope persistence: Stage4 3/3, Stage3 0/4, Stage2 0/2.
- Client cache hits in this run: 0 across all 28 attempts.
- Provider-implicit cache credit: 44,007 tokens, exclusively on Stage3 ep4 BlueprintEnsemble fan-out, no lineage written.
- Cache gate uniformly 50,000 chars; Stage2/Stage3 max content 15-20 KB -- the gate is functionally dormant for those producer paths in this run.

### 3.2 Could memory or cache have prevented the Jan 1 vs Jan 3 failure?

**No.** Three independent reasons:

1. **Stage3 has no envelope.** The terminal failure was on Stage3 ep4 attempt 10. Stage3 persists no `session_memory_envelope` (0/4 rows). Even the Stage4-style envelope contract carries `truth_pins` from Stage4 conflict resolution, not arc-state timeline authority. The required date `2006년 1월 3일` lives in arc plan / state extractor surfaces, not in any envelope field.

2. **Cache is not memory.** The order pack and AGENTS.md governance both forbid treating cache hits as story memory. The 44,007 cached tokens are cost relief on a fan-out triple; they have no `cache_name`, no `content_hash`, no `outcome` column populated. They cannot project arc-state authority into a Blueprint candidate.

3. **Stage4-applied envelope's `cache_lineage` is empty.** Even on the stage where the envelope IS applied, the `cache_lineage` field serialises as `{}` on every row in this run -- the slot exists but is never populated. So even if Stage3 had an envelope today, the cache-lineage carrier is dormant.

The Jan 1 vs Jan 3 contradiction was caught by the Stage3 binding/prevalidation `downstream_override_applied=1` path (`director_selections` id=9), not by Director's quality scoring. Memory or cache could not have surfaced this earlier in the current architecture; this is a continuity-bridge problem (Lane D), not a memory/cache rollout gap.

### 3.3 Triangulated facts

- Stage4 envelope is substrate-applied but **observability of `cache_lineage` is empty** in this run. Reason: zero successful client cache attempts, so nothing to lineage.
- The 50,000-char cache gate is uniformly enforced and is the proximate reason 26/28 client attempts are skipped. Whether 50,000 is right is an open benchmarking question (acceptance criteria #2 in the 2026-04-23 SSOT) -- not answerable from this single run.
- `vertex_api_key_explicit_cache_unsupported` (2 stage4 rows) is a provider-policy block, not a content-size block; lowering the gate would not change those.
- Provider-implicit cached_tokens on the Stage3 ep4 BlueprintEnsemble fan-out is the only visible cache benefit in the run. It saved tokens on three identical-credit calls but provided no continuity carry.

## 4. Risks

R1. **Stage3 lacks any envelope persistence.** Across 10 retries on ep4, the prior 9 attempts and their reject reasons / fix-pack metadata are not surfaced as a hydratable structure on subsequent attempts. The retry loop relies on Stage3-internal coverage-warning history (added in 2026-04-25 implementation unit #6) but not on a stage-agnostic envelope. Severity: P1 for clean 5-arc reliability.

R2. **Stage2 lacks envelope persistence.** `SessionFailureMemory` is prompt-side and dies with the process. Resume across a worker restart loses Stage2 retry memory. Severity: P2 (Stage2 has only 2 attempts in this run, but resume scenarios could regress).

R3. **`cache_lineage` slot is dormant.** Stage4 advisory carries the field but the run produced zero client cache hits to populate it. If/when client cache fires, telemetry is ready; until then this is a schema slot pretending to be coverage. Severity: P3 (telemetry posture, not failure mode).

R4. **Provider-implicit cached_tokens with NULL lineage.** 44,007 cached tokens on Stage3 ep4 BlueprintEnsemble fan-out had no `context_cache_name` / `context_cache_content_hash` / `context_cache_outcome` written. If anyone ever treats provider-implicit cache as story-memory authority, stale narrative content can leak across episode boundaries undetected. Severity: P1 governance risk.

R5. **No runtime_audit event for binding-prevalidation contradictions.** Lane B-adjacent observability gap: the Jan 1 vs Jan 3 contradiction is buried in `stage_attempts.reject_reason` text and `pass_rate_monitor.reject_reason`. `runtime_audit.jsonl` only emits `blueprint_fail: ep_4_all_retries_exhausted`. Future audits cannot triage by event type. Severity: P2 (observability), but Lane A-adjacent.

R6. **Cache gate (`cache.min_content_chars=50000`) is uniformly applied without measurement.** 2026-04-23 SSOT acceptance criteria #2 requires benchmarking before any reduction. This run did not produce that benchmark. Severity: P3 if no one proposes lowering; P1 if anyone proposes lowering it as a "fix" for cache hit rate.

## 5. Recommendation

R-A. **Do not lower `cache.min_content_chars` to 'fix' cache miss rate.** The 5-arc failure is not a cache problem. Lowering the gate would expand provider-side cache surface without addressing the Stage3 ep4 binding/prevalidation contradiction.

R-B. **Do not promote provider-implicit cached_tokens to authority.** The 44,007 cached tokens visible on the Stage3 ep4 fan-out are cost telemetry only; client lineage columns must remain the source of truth for any cache-as-substrate claim.

R-C. **Open a bounded Stage3 envelope tranche before any Stage2 widening.** The Stage4 envelope contract is reusable substrate. A Stage3 envelope (provider-neutral, persisted into `stage_attempts.advisory_flags`) would surface arc-state timeline authority, the prior attempt's reject reason, and the binding/prevalidation contradiction lineage so retry attempts after #1 see what attempt #1-#9 hit. This addresses R1 directly.

R-D. **Decide `cache_lineage` semantics before populating it.** The dormant `{}` slot will be tempting to fill from provider-implicit credit. Lane B recommends: only populate `cache_lineage` from successful **client** cache attempts (`cache_outcome=created|hit`), with `cache_name`, `content_hash`, `model`, and gate. Provider-implicit credit must remain `llm_calls.cached_tokens` only.

R-E. **Defer cache-gate benchmark until Stage3 envelope substrate exists.** Benchmarking with Stage3 invisible-to-resume retries is uninformative.

R-F. **Refer the Jan 1 vs Jan 3 case to Lane D.** This is a continuity authority projection question (arc-state -> Blueprint candidate), not a memory/cache rollout question.

These are recommendations only. Lane B does not implement, and the order pack defers all implementation to post-synthesis SSOT.

## 6. Subagent Cross-Check

Two subagents ran independently and the cross-check is consistent on every load-bearing fact:

- Stage4-only envelope claim: Subagent A grep across `modules/core/stage[234]_*.py` returned matches in Stage4 files only. Subagent B independently confirmed by parsing `advisory_flags` JSON keys on all 9 `stage_attempts` rows -- 3/3 Stage4 carry `session_memory_envelope`, 0/4 Stage3 and 0/2 Stage2 do.
- Cache-gate constant: Subagent A anchored `_MIN_CACHE_CONTENT = ... default 50000` at `base_agent.py:2379`. Subagent B confirmed every `context_cache_attempts.min_content_chars` row equals 50,000.
- Cache-skip dominance: Subagent A noted the gate logic. Subagent B observed 26/28 skips with `content_too_short` and 2/28 with `vertex_api_key_explicit_cache_unsupported` (no other reasons exist in this run).
- `cached_tokens` schema column: Subagent A anchored `db_bootstrap_runtime.py:470` `("cached_tokens", "INTEGER")` on `llm_calls`. Subagent B independently exercised the column with 130 rows, 3 non-zero, sum 44,007.
- `cache_lineage` semantics: Subagent A anchored the field at `session_memory_envelope.py:192` and the test assertion at `test_session_memory_envelope.py:61`. Subagent B observed the field as nested empty `{}` on every Stage4 row in the run.
- Stage3 ep4 terminal failure: Subagent B anchored the Director PASS_WITH_FIX/95 -> `final_verdict=FAILED` flip via `downstream_override_applied=1`, with `verdict_reason` ending `binding prevalidation repair required` and `reject_reason` carrying the literal Jan 1 vs Jan 3 contradiction text.

No contradictions surfaced between the two subagent reports.

## 7. 3-Pass Mini Audit

Pass 1 - structure and scope: PASS.

The report uses the order-pack mandated section names (`Scope`, `Evidence`, `Findings`, `Risks`, `Recommendation`, `Subagent Cross-Check`, `3-Pass Mini Audit`) plus the parent-terminal verdict table. Read-only constraint honoured: no code changes, no DB writes, no test runs. Subagent allocation matches Section 4 of the order pack (one to code/test surfaces, one to DB/log telemetry; parent kept the verdict table).

Pass 2 - evidence and consistency: PASS.

Every load-bearing claim is anchored to either (a) a file path with a line number from Subagent A, or (b) a sqlite3 query result, parsed JSON key listing, or log file content from Subagent B. The two subagents independently triangulate the same facts (envelope presence, cache gate, skip distribution, cached_tokens count). Stage classification distinguishes "applied" (Stage4 envelope), "not applied" (Stage2/Stage3 envelope; all stages client cache), and "telemetry-only" (provider-implicit cached_tokens; dormant `cache_lineage` slot) per the order pack's required taxonomy. The Jan 1 vs Jan 3 prevention question is answered with three independent reasons, none of which collapses cache into memory.

Pass 3 - execution readability: PASS.

The verdict table is one row per stage with two verdict columns (memory, cache). Recommendations are bounded to read-only design-and-defer guidance and explicitly forbid the most dangerous shortcut (lowering the cache gate to chase hit rate). Risks carry severity labels. Lane handoffs (Jan 1 vs Jan 3 -> Lane D; binding-prevalidation observability -> Lane A) are explicit.

Estimated confidence: 95%.

Residual uncertainty (the missing 5%):
- This run has only 9 `stage_attempts` rows; a single-run sample cannot prove envelope behaviour under restart/resume in production. The hydration path is anchored by code (`stage4_orchestrator.py:1794-1822`) and unit tests, but no resume cycle was exercised in this Frontier Lag run -- absence of regression here is evidence-of-absence-only at the unit level.
- The `vertex_api_key_explicit_cache_unsupported` skip reason was not investigated in depth; whether that policy will permanently block the largest Stage4 contexts (60,461-char) from client caching is an open question outside Lane B's scope.
