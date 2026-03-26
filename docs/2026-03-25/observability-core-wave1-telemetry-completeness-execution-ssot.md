# Observability Core Wave 1 Telemetry Completeness Execution SSOT

Date: 2026-03-25
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-25/observability-core-wave1-telemetry-completeness-execution-ssot.md`
Temp Mirror Path: `docs/temp/observability-core-wave1-telemetry-completeness-execution-ssot.md`
Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: docs/2026-03-24/console.txt modified, docs/2026-03-25/stage3-latency-efficiency-static-survey.md untracked, no active temp execution queue`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `live re-audit found parts of the merge candidate already implemented; scope shrunk before opening this SSOT`
Source Survey Docs:
- `docs/2026-03-25/global-observability-statistics-core-4terminal-merge-audit.md`
- `docs/2026-03-25/opus-observability-core/t1-runtime-timing-cost.md`
- `docs/2026-03-25/opus-observability-core/t3-retry-rescue-asp.md`
- `docs/2026-03-25/opus-observability-core/t4-sink-alignment-instrumentation-ledger.md`
- `docs/2026-03-25/stage3-latency-efficiency-static-survey.md`
Evidence Artifacts:
- `modules/domain/agents/base_agent.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/session_logger.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/failure_analyzer.py`
Side-Effect Coverage: covered

## 1. Intent

- Realize one bounded observability-core wave that improves operator-visible telemetry completeness without changing runtime policy, sink authority, or dashboard design.
- Convert the merge-audit recommendation into a smaller execution scope after a live workspace re-audit.
- Keep the wave read-mostly and instrumentation-focused.

## 2. Live Re-Audit Correction

The merge audit candidate was intentionally re-checked against live code before opening this SSOT.

The following are **already implemented enough that they must NOT be reopened in this wave**:
- actual provider-level `usage_metadata` extraction already exists in:
  - `modules/core/providers/gemini_provider.py`
  - `modules/core/providers/vertex_provider.py`
- `BaseAgent` already preserves and forwards token usage into metrics/DB paths via:
  - `_last_llm_usage`
  - `_build_metric_usage_payload()`
  - `_log_llm_call_to_db()`
- Stage 2 / Stage 3 / Stage 4 `PassRateMonitor.record_attempt()` call sites already pass bounded `duration_ms` / `token_cost`

Therefore this SSOT **shrinks** the original merge candidate to the remaining bounded gaps:
- session JSONL `llm_io` completeness
- API wait / timeout / disconnect telemetry completeness
- canary summary telemetry completeness
- read-only rescue effectiveness summary

## 3. Scope

Included:
- `modules/core/session_logger.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/failure_analyzer.py`
- `tests/test_session_logger.py`
- `tests/test_stage4_canary_tools.py`
- `tests/test_failure_analyzer.py`
- minimal new tests only if existing files become too noisy

Excluded:
- `modules/core/metrics_collector.py`
- `modules/core/pass_rate_monitor.py`
- `modules/api/bridge_server.py`
- dashboard/UI redesign
- sink authority contract changes
- DB schema changes
- JSONL path/naming changes
- retry policy / ASP behavior changes
- quality-policy changes
- any fresh-run/canary execution in this wave

## 4. Pass 1. Inventory Summary

- `BaseAgent` already computes token/cost payloads but `SessionLogger.log_llm_call()` does not currently accept or persist those fields.
- `BaseAgent` already logs API failures to DB/session sinks at ask-finalization time, but long wait / timeout / network-retry paths still need explicit re-audit for structured operator evidence.
- `build_stage3_canary_summary()` currently reports attempts, blueprint counts, and sink alignment, but not a compact per-episode telemetry view.
- `FailureAnalyzer` already computes:
  - `quality_distribution()`
  - `patch_trace_summary()`
  - `stage_pass_rates()`
  - `avg_attempts_by_stage()`
  but does not expose one compact rescue-effectiveness helper.

## 5. Pass 2. Semantic Classification

- Class A. `session telemetry completeness`
  - enrich optional session JSONL `llm_io` records with token/cost metadata already available at the caller
- Class A2. `API wait/failure telemetry completeness`
  - verify and, if needed, minimally enrich structured evidence for long API waits, timeout failures, and connection/network retry paths
- Class B. `canary summary completeness`
  - add compact Stage 3 canary telemetry fields without changing canary execution flow
- Class C. `read-only rescue effectiveness`
  - add one analyzer surface that summarizes rescue attempt counts and outcome quality deltas
- Class D. `explicit defers`
  - anything requiring sink redesign, schema change, or dashboard work

## 6. Side-Effect Map

- file writes / artifacts:
  - existing JSONL and canary summary files gain extra fields only
  - no new log file families
- DB / schema / transaction boundaries:
  - none in this wave
- JSONL / log / audit sinks:
  - `session/llm_io.jsonl` becomes richer
  - `stage3_canary_summary.json` becomes richer
  - read-only analyzer adds no persistent sink by itself
- console / UI / operator output:
  - unchanged unless test/debug output changes incidentally
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - none
- bootstrap fallback / config-env mutation:
  - none

## 7. Realization Architecture

### Tranche A. Session `llm_io` telemetry completeness

Goal:
- persist already-available token/cost facts into optional session JSONL

Implementation shape:
- extend `SessionLogger.log_llm_call()` to accept optional:
  - `input_tokens`
  - `output_tokens`
  - `cached_tokens`
  - `thinking_tokens`
  - `total_cost_usd`
- update the bounded `BaseAgent` session-logger call site(s) to pass those fields when available
- keep the fields optional and backward-compatible

Guardrail:
- do not change DB telemetry code in this tranche

### Tranche A2. API wait / timeout / disconnect telemetry verification

Goal:
- ensure that very long API waits, timeout failures, and connection/network-retry paths leave structured evidence the operator can inspect later

Implementation shape:
- verify whether the existing `BaseAgent` paths for:
  - long API call waits
  - timeout failures
  - network/connection retry loops
  already emit structured evidence to session/operator sinks
- if any of those paths are console-only, add the smallest additive telemetry needed so the event is reconstructible later
- prefer existing sinks:
  - session `ui_events.jsonl`
  - session `llm_io.jsonl`
  - DB `llm_calls`

Guardrail:
- do not add new sink families
- do not add policy changes to retry/wait behavior
- do not add heartbeat spam; only bounded event-level evidence

### Tranche B. Stage 3 canary summary telemetry enrichment

Goal:
- make Stage 3 canary summaries useful for runtime/cost interpretation without requiring manual DB queries

Implementation shape:
- enrich `build_stage3_canary_summary()` with a compact per-episode telemetry section derived from existing sinks, such as:
  - attempt duration
  - token cost
  - attempt count
  - final verdict / score
- keep the payload compact; no raw prompt/response material
- keep summary generation read-only

Guardrail:
- do not redesign `run_stage3_canary.py`
- do not add new canary subcommands

### Tranche C. Read-only rescue effectiveness helper

Goal:
- answer whether rescue paths materially help, without changing retry/ASP policy

Implementation shape:
- add one read-only `FailureAnalyzer` helper that summarizes rescue effectiveness from existing authoritative/companion sinks
- bounded output should cover:
  - rescue_attempted_count
  - rescue_succeeded_count
  - rescue_success_rate_pct
  - average score delta where derivable
  - ASP-used count when derivable

Guardrail:
- no DB schema change
- no persistent write
- no policy decision inside the analyzer

## 8. Acceptance Criteria

- `session/llm_io.jsonl` can include token/cost fields when available, while remaining backward-compatible if not available
- `BaseAgent` session logging passes already-known token/cost fields without reopening provider or DB logic
- long API wait / timeout / connection-failure paths are explicitly re-audited, and any missing structured evidence is added through existing sinks only
- `build_stage3_canary_summary()` includes compact telemetry data useful for Stage 3 efficiency reading
- `FailureAnalyzer` exposes one bounded rescue-effectiveness summary method
- no sink authority contract changes
- no dashboard or bridge payload redesign
- no DB schema changes

## 9. Verification Plan

- `python -m py_compile modules/core/session_logger.py modules/domain/agents/base_agent.py modules/core/stage4_canary_tools.py modules/core/failure_analyzer.py`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_session_logger.py -q`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_stage4_canary_tools.py -q`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_failure_analyzer.py -q`
- run any small additional targeted test file if introduced
- `python scripts/check_utf8_hygiene.py modules/core/session_logger.py modules/domain/agents/base_agent.py modules/core/stage4_canary_tools.py modules/core/failure_analyzer.py tests/test_session_logger.py tests/test_stage4_canary_tools.py tests/test_failure_analyzer.py docs/2026-03-25/observability-core-wave1-telemetry-completeness-execution-ssot.md docs/temp/observability-core-wave1-telemetry-completeness-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 10. Guardrails

- Do not reopen provider usage extraction logic unless the live re-audit proves a concrete bug.
- Do not reopen `PassRateMonitor` wiring unless a concrete unpopulated call site is found during implementation.
- Do not change API retry budgets, timeout policy, or key-rotation policy in this wave.
- Do not add new DB tables or columns.
- Do not add new dashboard endpoints or change bridge payload shape.
- Do not implement retry-policy or ASP-policy changes.
- Keep all new telemetry fields optional and additive.

## 11. Temp Queue Notes

- temp status: pending
- cleanup condition:
  - implementation complete
  - targeted verification complete
  - Codex closure audit complete
- roadmap dependency:
  - none while this is the only active execution item

## 12. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 13. 3-Pass Audit Notes

- Pass 1 scope result:
  - shrunk from the merge-audit candidate after live code re-audit
  - bounded to telemetry completeness and read-only rescue analysis only
- Pass 2 evidence result:
  - live code confirms provider usage extraction and pass-rate wiring are already present
  - remaining gaps are session JSONL completeness, canary summary completeness, and analyzer completeness
- Pass 3 actionability result:
  - implementation surfaces are explicit
  - verification is targeted
  - exclusions prevent architecture churn
- Estimated confidence: 96%

## 14. Closure Audit

- Closure status: closed (closure-audited)
- Closure audit summary:
  - Tranche A complete: session `llm_io` now accepts optional token/cost fields and bounded `BaseAgent` call sites forward them when available
  - Tranche A2 complete: existing structured evidence for long API wait / timeout / disconnect paths was re-audited and found sufficient; no policy or sink-family changes were needed
  - Tranche B complete: Stage 3 canary summary now includes compact `episode_telemetry` derived read-only from existing DB sinks
  - Tranche C complete: `FailureAnalyzer.rescue_effectiveness()` landed, and closure audit tightened `asp_used_count` so it counts only explicit ASP evidence instead of generic patch strategies
- Verification rerun:
  - `python -m py_compile modules/core/session_logger.py modules/domain/agents/base_agent.py modules/core/stage4_canary_tools.py modules/core/failure_analyzer.py`
  - `pytest tests/test_session_logger.py -q` -> `25 passed`
  - `pytest tests/test_stage4_canary_tools.py -q` -> `10 passed`
  - `pytest tests/test_failure_analyzer.py -q` -> `23 passed`
  - `python scripts/check_utf8_hygiene.py ...` -> pass
  - `python scripts/ops_validator.py` -> pass
- Residual risk:
  - `total_cost_usd` in session JSONL remains absent when metrics are disabled; token counts still persist and this remains additive-only by design
  - `episode_telemetry` is only as complete as `llm_calls` rows for the canary run; empty telemetry remains a valid read-only outcome when logging is unavailable
