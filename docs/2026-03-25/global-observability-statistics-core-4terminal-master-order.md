# Global Observability + Statistics Core 4-Terminal Master Order

Date: 2026-03-25
Status: survey-master-order
Document Type: system-track survey master order
Canonical Path: `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md`
Temp Mirror Path: none (survey-only)
Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: docs/2026-03-24/console.txt modified, docs/2026-03-25/stage3-latency-efficiency-static-survey.md untracked, no active temp execution queue`

## 1. Intent

Run a 4-lane parallel survey on one bounded topic:

- global observability and statistics core for the live production system

This is not a dashboard redesign order.
This is not a policy-change order.
This is not an execution SSOT bundle.

The purpose is only:
- identify which runtime, quality, retry, and sink-alignment statistics already exist
- identify what is missing for reliable operator judgment
- rank the best bounded instrumentation candidates by ROI and blast radius
- decide whether one compact observability wave should open later

## 2. Core Question

If the next system-level insight gap is not quality logic but observability, what is the smallest shared statistics core that would most improve operator judgment without destabilizing the pipeline?

This master order must help answer:

1. where runtime, timing, token, and cost evidence already exists
2. where pass/fail, quality, score, and warning evidence already exists
3. where retry, rescue, and ASP-effect evidence is missing
4. whether sink alignment across console, JSONL, DB, summary, and canary outputs is coherent enough for a bounded observability wave

## 3. Scope

Included:
- runtime and timing sinks
- pass-rate and quality sinks
- retry, rescue, and ASP-related event sinks
- JSONL / DB / summary / console alignment for operator-facing evidence
- bounded instrumentation options for observability core only

Excluded:
- dashboard or UI redesign
- Stage 2, Stage 3, or Stage 4 quality-policy redesign
- prompt redesign
- execution SSOT creation
- temp queue edits
- immediate code changes
- full data warehouse or analytics platform proposals

## 4. Shared Guardrails

- Survey only. No code changes.
- Do not create execution SSOTs.
- Do not modify `docs/temp/`.
- Do not overwrite shared canonical reports.
- Save only lane outputs under `docs/2026-03-25/opus-observability-core/`.
- Findings first.
- Prefer live code and current sink truth over stale historical rhetoric.
- Distinguish:
  - already existing statistics
  - missing but low-blast instrumentation
  - high-blast observability dreams that should stay deferred
- Do not default to dashboard proposals.
- Do not recommend policy changes from metrics absence alone.
- If confidence is below 95%, do not recommend immediate execution SSOT opening.

## 5. Shared Evidence Surfaces

Required code surfaces:
- `modules/core/metrics_collector.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/quality_dashboard.py`
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- `modules/core/adaptive_retry.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_episode_logging.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/services/audit_service.py`
- `modules/api/control_plane_contract.py`
- `scripts/run_stage3_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/run_auto_frontier_lag_harness.py`

Optional evidence surfaces:
- recent `projects/*/logs/episode_production.jsonl`
- recent `projects/*/logs/runtime_audit_summary.json`
- recent canary summary JSON files
- `projects/*/logs/session/ui_events.jsonl` when present
- recent `docs/2026-03-25/stage3-latency-efficiency-static-survey.md`

## 6. Lane Assignment

### T1. Runtime / Timing / Cost Surfaces

Purpose:
- determine what the system can already measure about wall time, attempt time, and LLM-call cost shape

Focus:
- runtime audit summaries
- timing collectors
- canary summary payloads
- any token/cost sinks or obvious absence thereof

Questions:
- Where do stage, episode, and attempt-level timing facts already exist?
- Is the current system able to attribute runtime to fixed overhead vs LLM calls vs retries?
- Are token/cost fields already captured anywhere, or only inferable?
- What is the best bounded next move for runtime/cost observability?

Save paths:
- `docs/2026-03-25/opus-observability-core/t1-runtime-timing-cost.md`
- optional: `docs/2026-03-25/opus-observability-core/t1-runtime-timing-cost-evidence.md`

### T2. Quality / Verdict / Pass-Rate Surfaces

Purpose:
- determine how well the system currently captures outcome quality, score, warnings, and pass-rate data

Focus:
- pass-rate monitor
- quality dashboard
- episode production sink(s)
- outcome summaries and score fields

Questions:
- Which sinks already capture verdict, score, warning count, and pass-rate reliably?
- Is operator-visible quality evidence duplicated, incomplete, or contradictory across sinks?
- What is the best bounded next move for quality/verdict statistics?

Save paths:
- `docs/2026-03-25/opus-observability-core/t2-quality-verdict-passrate.md`
- optional: `docs/2026-03-25/opus-observability-core/t2-quality-verdict-passrate-evidence.md`

### T3. Retry / Rescue / ASP Statistics

Purpose:
- determine whether the system can already measure retry cost, rescue effectiveness, and ASP contribution

Focus:
- retry runtime
- adaptive retry
- failure analyzer
- ASP or red-team correction paths
- PASS_WITH_FIX / rescue-like event capture

Questions:
- Can the system currently answer how often retry or ASP fires?
- Can it answer rescue rate, improvement delta, added round count, or added wall time?
- Which retry/rescue statistics are missing but low-blast to add?
- Is ASP observability the best immediate candidate, or should it be part of a broader rescue core?

Save paths:
- `docs/2026-03-25/opus-observability-core/t3-retry-rescue-asp.md`
- optional: `docs/2026-03-25/opus-observability-core/t3-retry-rescue-asp-evidence.md`

### T4. Sink Alignment / Operator SSOT / Core Instrumentation Ledger

Purpose:
- determine whether the operator-facing evidence model is coherent enough to support one bounded observability-core wave

Focus:
- console vs JSONL vs DB vs summary vs canary outputs
- sink authority
- duplication or silent gaps
- bounded cross-cutting instrumentation candidates

Questions:
- Which sink should be treated as authoritative for runtime, quality, and rescue stats?
- Where does the current system duplicate, omit, or blur operator evidence?
- If one compact observability-core wave opened later, what should it include and what should stay deferred?

Guardrail:
- This lane must not act like final merge owner.
- It can rank bounded options, not choose the final wave by itself.

Save paths:
- `docs/2026-03-25/opus-observability-core/t4-sink-alignment-instrumentation-ledger.md`
- optional: `docs/2026-03-25/opus-observability-core/t4-sink-alignment-instrumentation-ledger-evidence.md`

## 7. Required Output Shape

Each lane must:
- list findings first
- avoid merged cross-lane conclusions
- avoid implementation claims
- include confidence and limits

Mandatory final lines for every lane:
- `Dominant observability gap in this lane: runtime-cost / quality-verdict / retry-rescue / sink-alignment / mixed / none`
- `Best bounded instrumentation candidate in this lane: <short label>`
- `Should this lane alone trigger a new SSOT: yes / no`

## 8. Merge Rule

After all 4 lanes return, Codex will decide:
- whether one compact observability-core execution SSOT should open
- whether the next wave should focus on runtime attribution, retry/rescue statistics, or sink alignment
- whether fresh live-run evidence is still required before opening the wave

The lanes must not do this themselves.

## 9. Common Opus Order

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md
6. docs/2026-03-25/stage3-latency-efficiency-static-survey.md

Task:
Survey the bounded global observability/statistics core for your assigned lane only.
Survey only. No code changes.

Primary goal:
Determine whether the highest-ROI next observability improvement lives in:
- runtime/timing/cost attribution
- quality/verdict/pass-rate statistics
- retry/rescue/ASP statistics
- or sink-alignment / operator SSOT cleanup

Hard constraints:
- Survey only. No code changes.
- Do not create execution SSOTs.
- Do not touch docs/temp.
- Do not overwrite shared reports.
- Save only your lane output under docs/2026-03-25/opus-observability-core/.
- Keep conclusions bounded and evidence-led.
- Do not default to dashboard redesign.
- Do not recommend policy changes from logging gaps alone.

Mandatory final lines:
- Dominant observability gap in this lane: runtime-cost / quality-verdict / retry-rescue / sink-alignment / mixed / none
- Best bounded instrumentation candidate in this lane: <short label>
- Should this lane alone trigger a new SSOT: yes / no
```

## 10. Terminal Overrides

### T1 Override

```text
docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 1.
Save:
- docs/2026-03-25/opus-observability-core/t1-runtime-timing-cost.md
- optional: docs/2026-03-25/opus-observability-core/t1-runtime-timing-cost-evidence.md
Investigate runtime / timing / cost surfaces only. Focus on stage/episode/attempt wall time, token/cost capture, and runtime attribution only. No dashboard proposals.
```

### T2 Override

```text
docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 2.
Save:
- docs/2026-03-25/opus-observability-core/t2-quality-verdict-passrate.md
- optional: docs/2026-03-25/opus-observability-core/t2-quality-verdict-passrate-evidence.md
Investigate quality / verdict / pass-rate surfaces only. Focus on which sinks are authoritative for score, warning, verdict, and pass-rate, plus operator gaps.
```

### T3 Override

```text
docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 3.
Save:
- docs/2026-03-25/opus-observability-core/t3-retry-rescue-asp.md
- optional: docs/2026-03-25/opus-observability-core/t3-retry-rescue-asp-evidence.md
Investigate retry / rescue / ASP statistics only. Focus on whether the current system can answer trigger rate, rescue rate, improvement delta, and added round/time, plus the smallest instrumentation candidate.
```

### T4 Override

```text
docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 4.
Save:
- docs/2026-03-25/opus-observability-core/t4-sink-alignment-instrumentation-ledger.md
- optional: docs/2026-03-25/opus-observability-core/t4-sink-alignment-instrumentation-ledger-evidence.md
Investigate console / JSONL / DB / summary / canary sink alignment and operator SSOT only. Focus on duplication, omission, authority blur, and the bounded instrumentation ledger.
```

## 11. Dispatch Lines

Use exactly one of the following:

- `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 1`
- `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 2`
- `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 3`
- `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md + terminal 4`
