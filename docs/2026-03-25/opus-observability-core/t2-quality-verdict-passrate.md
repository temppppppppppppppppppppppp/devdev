# T2. Quality / Verdict / Pass-Rate Surfaces

Date: 2026-03-25
Status: survey-only (no execution SSOT)
Lane: T2 — Quality / Verdict / Pass-Rate
Master Order: `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md`
Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
Confidence: 93%

## 1. Scope

This lane surveys:
- Which sinks already capture verdict, score, warning count, and pass-rate reliably
- Whether operator-visible quality evidence is duplicated, incomplete, or contradictory across sinks
- What the best bounded next move for quality/verdict statistics is

Excluded:
- Runtime/timing/cost attribution (T1)
- Retry/rescue/ASP statistics (T3)
- Cross-sink alignment topology (T4)
- Dashboard UI redesign
- Quality-policy changes

## 2. Existing Quality/Verdict Sinks — Full Inventory

### 2.1. DB: `stage_attempts` table (AUTHORITATIVE)

- **Writer**: `db_manager.save_stage_attempt()` — called from Stage 2 (`stage2_finalizer.py`), Stage 3 (`stage3_orchestrator.py`), and Stage 4 (`stage4_interview_round.py L5886`)
- **Fields**: `session_id, ts, stage, ep_num, arc_num, attempt_num, verdict, score, failure_category, reject_reason, fix_scope, model, duration_ms, advisory_flags, attempt_key, generation_method, prompt_version, candidate_key, content_hash, artifact_path, selection_reason, verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, retry_directives, initial_verdict, score_breakdown, is_patch, is_patch_fallback, patch_strategy`
- **Verdict fields**: `verdict` (final), `initial_verdict` (pre-gate), `score`, `score_breakdown` (JSON)
- **Coverage**: Every attempt across Stages 2, 3, 4 — both PASS and REJECT
- **Authority**: Designated authoritative sink per `control_plane_contract.py` and `audit_service._AUTHORITATIVE_ATTEMPT_SINKS`

### 2.2. DB: `director_selections` table (AUTHORITATIVE)

- **Writer**: `db_manager.save_director_selection()` — called from Stage 3 (`stage3_orchestrator.py L1885/2664`) and Stage 4 (`stage4_interview_round.py L2357`)
- **Fields**: `stage, ep_num, round_num, selected_label, selected_strategy, verdict, score, selection_reason, candidate_count, fix_scope, advisory_warnings, verdict_reason, pre_firewall_score, firewall_triggered, firewall_reason, attempt_key, candidate_key, content_hash, artifact_path, director_thinking`
- **Verdict fields**: `verdict`, `score`, `pre_firewall_score`, `firewall_triggered`, `advisory_warnings` (JSON)
- **Coverage**: Director-level verdict for every selection event in Stages 3 and 4
- **Authority**: Authoritative per `audit_service._AUTHORITATIVE_ATTEMPT_SINKS`

### 2.3. DB: `episode_quality_labels` table (AUTHORITATIVE)

- **Writer**: `db_manager.save_episode_quality_label()` — called on PASS episodes
- **Fields**: `ep_num, score, verdict, selection_reason, open_review, score_breakdown, consistency_checklist`
- **Coverage**: Only PASS episodes (final quality label after acceptance)
- **Note**: INSERT OR REPLACE — one row per ep_num (latest-wins)

### 2.4. DB: `episode_quality_signals` table (AUTHORITATIVE)

- **Writer**: `db_manager.save_episode_quality_signal()` — Python-only quality metrics on final manuscript
- **Fields**: `ep_num, ced_score, ai_slop_score, ai_slop_hits, compression_ratio, burstiness, complexity, signal_summary`
- **Coverage**: PASS episodes with Python-computed quality signals (CED, AI slop, compression, burstiness, complexity)
- **Note**: INSERT OR REPLACE semantics

### 2.5. DB: `episode_quality_observations` table (AUTHORITATIVE)

- **Writer**: `db_manager.save_episode_quality_observation()` — operator manual review
- **Fields**: `ep_num, operator_label, note, created_at, updated_at`
- **Coverage**: Only when the operator manually reviews an episode via `/quality/review` endpoint
- **Note**: ON CONFLICT DO UPDATE — one row per ep_num

### 2.6. JSONL: `episode_production.jsonl` (AUTHORITATIVE)

- **Writer**: `stage4_interview_round.py L5567` (per-attempt), `stage4_orchestrator.py L2003` (escalation events)
- **Fields per entry**: `ep_num, round_num, arc_num, attempt_key, candidate_key, content_hash, artifact_path, verdict, score, initial_verdict, initial_score, director_verdict, final_verdict, final_score, gate_basis, repair_scope, selected, strategy, model, duration_ms, round_total_calls, round_total_tokens, round_total_cost_usd, round_model_breakdown, token_cost, token_usage, error_category, reason, selection_reason, verdict_reason, action_items, score_breakdown, open_review, flags (patch_mode/patch_fallback/tot/mad/asp/strategy_budget/reject_bucket/retry_budget_axes), patch_trace, fix_pack, warnings, final_warnings, candidate_warnings, feedback_provenance`
- **Coverage**: Every Stage 4 attempt — richest single-record payload
- **Authority**: Designated authoritative per `control_plane_contract.py`

### 2.7. JSON: `pass_rate_monitor.json` (NON-AUTHORITATIVE convenience cache)

- **Writer**: `pass_rate_monitor.py` — in-memory `AttemptRecord` list, JSON-serialized every 100 records and on explicit `save()`
- **Fields per record**: `timestamp, stage, episode, arc, attempt_num, success, reject_reason, generation_method, model_tier, duration_ms, token_cost, is_patch, prev_score, patch_fallback, attempt_key, final_verdict, director_verdict, gate_basis, repair_scope, fix_pack, retry_budget_axes, patch_strategy, structural_attempted, error_category, reject_bucket, score_breakdown, candidate_key, content_hash, artifact_path`
- **Coverage**: Last 1000 records across all stages (rolling window)
- **Authority**: Explicitly non-authoritative per docstring — rebuilt from in-memory state; loss is non-destructive

### 2.8. JSONL: `quality_metrics.jsonl` (NON-AUTHORITATIVE convenience cache)

- **Writer**: `quality_dashboard.py` — `_save_record()` appends typed JSONL records
- **Record types**: `validation` (decision/score/violations/warnings/quality_signals), `hud_anomaly`, `blueprint_coverage`, `retrieval_observation`
- **Coverage**: One record per validation event (Stage 2, 3, 4), plus HUD anomaly, blueprint coverage, and retrieval observation events
- **Authority**: Non-authoritative; in-memory accumulation for dashboard rendering

### 2.9. JSONL: `session/decisions.jsonl` (OPTIONAL telemetry)

- **Writer**: `session_logger.py` `log_decision()` — gated by `enabled` flag (default OFF, activated via `validation.yaml`)
- **Fields**: `stage, ep_num, round_num, decision_type, result, score, advisories`
- **Coverage**: Director decision path logging when session logging is enabled
- **Authority**: Explicitly non-authoritative per session_logger docstring

### 2.10. JSON: `runtime_audit_summary.json` (COMPANION snapshot)

- **Writer**: `audit_service.write_audit_summary()` — writes a point-in-time heartbeat with compact proof digest
- **Quality-relevant fields**: `proof_digest.stages.stageN.status`, `proof_digest.stages.stageN.coverage`, `proof_digest.artifacts.*`
- **Authority**: Explicitly non-authoritative companion per `control_plane_contract.py`

### 2.11. Bridge API: `/quality/summary` and `/quality/dashboard` (COMPANION)

- **Builder**: `bridge_server.py` `_build_quality_dashboard_payload()` — aggregates `QualityDashboard`, `PassRateMonitor`, DB queries, `FailureAnalyzer`
- **Exposed payloads**: `quality_summary`, `quality_signal_snapshot`, `result_summary`, `episode_trend`, `score_trend`, `stage_stats`, `common_violations`, `failure_patterns`, `patch_effectiveness`, `episode_rol`, `arc_cost_correlation`, `calibration`, `sink_alignment_summary`, `retrieval_summary`, `cost_summary`, `gate_repair_summary`
- **Authority**: Explicitly non-authoritative companion per `control_plane_contract.py`

## 3. Sink Authority Map

| Sink | Authority | Verdict | Score | Warnings | Pass-Rate | Quality Signals |
|---|---|---|---|---|---|---|
| DB `stage_attempts` | AUTHORITATIVE | yes | yes | via advisory_flags | derivable | no |
| DB `director_selections` | AUTHORITATIVE | yes | yes | yes (advisory_warnings) | derivable | no |
| DB `episode_quality_labels` | AUTHORITATIVE | yes (PASS only) | yes | no | no | no |
| DB `episode_quality_signals` | AUTHORITATIVE | no | CED/slop/etc. | no | no | yes |
| DB `episode_quality_observations` | AUTHORITATIVE | label only | no | no | no | operator-subjective |
| JSONL `episode_production` | AUTHORITATIVE | yes (full chain) | yes (initial+final) | yes (full) | derivable | no |
| JSON `pass_rate_monitor` | non-authoritative | yes | yes | limited | yes (computed) | no |
| JSONL `quality_metrics` | non-authoritative | yes | yes | count only | derivable | via quality_signals |
| JSONL `session/decisions` | optional telemetry | yes | yes | limited | no | no |
| JSON `runtime_audit_summary` | companion | no | no | no | no | no |
| Bridge `/quality/*` | companion | aggregated | aggregated | aggregated | aggregated | aggregated |

## 4. Gap Analysis

### 4.1. What Is Already Well-Covered

1. **Per-attempt verdict and score**: `stage_attempts` + `director_selections` + `episode_production.jsonl` provide complete, authoritative, per-attempt verdict/score data for Stages 2, 3, and 4. Redundant and cross-checkable.

2. **Pass-rate computation**: `PassRateMonitor` computes first-attempt pass rate, eventual pass rate, avg attempts to pass, method success rates, and trend analysis. This is derived from in-memory records and is already available via the bridge `/quality/*` endpoints.

3. **Quality signal tracking (Python-only)**: CED score, AI slop score, compression ratio, burstiness, complexity — stored in DB `episode_quality_signals`. Available via bridge dashboard.

4. **Failure pattern analysis**: `FailureAnalyzer` provides `stage_pass_rates()`, `top_failure_categories()`, `advisory_reject_correlation()`, `avg_attempts_by_stage()`, `failure_prompt_patterns()`, `top_success_patterns()`. Available via bridge dashboard.

5. **Sink alignment verification**: `FailureAnalyzer.sink_alignment_summary()` already cross-checks `stage_attempts` vs `director_selections` vs `episode_production.jsonl` for field consistency, coverage gaps, and verdict mismatches. Available in canary summaries and bridge dashboard.

6. **Operator review path**: `/quality/review` POST endpoint allows manual quality observations with structured labels. Stored in DB `episode_quality_observations`.

7. **Episode ROL (Return on Latency)**: `PassRateMonitor.get_episode_rol_snapshot()` joins attempt data with quality scores to compute per-episode ROL. Available via bridge dashboard.

8. **Arc difficulty + cost correlation**: `PassRateMonitor.get_arc_cost_correlation()` joins arc difficulty with cost data. Available via bridge dashboard.

### 4.2. Gaps and Weaknesses

**GAP-1: Stage 3 quality signal coverage is weaker than Stage 4**

- Stage 3 writes to `stage_attempts` and `director_selections` (verdict/score), and to `quality_metrics.jsonl` (via `quality_dashboard.record_validation()`).
- But Stage 3 does NOT write Python-only quality signals (`episode_quality_signals`) — CED, AI slop, compression, burstiness, complexity are only computed and stored for Stage 4 PASS episodes.
- Stage 3 verdict is blueprint-level (not manuscript-level), so the Python-only signal absence is architecturally expected. However, this means the quality signal trend and dashboard data for Stage 3 is limited to verdict/score only, without independent Python-computed quality proxies.
- **Impact**: Low. Stage 3 quality is Director judgment on blueprint quality; Python signals are manuscript-level metrics. Architecturally coherent.

**GAP-2: `pass_rate_monitor.json` rolling window may lose historical data**

- `PassRateMonitor` keeps only the last 1000 records in memory and JSON. For a high-attempt session this window may be insufficient for long-term trend analysis.
- **Impact**: Low. DB `stage_attempts` is the authoritative long-term store. `pass_rate_monitor.json` is explicitly non-authoritative, rebuilt fresh each session.

**GAP-3: `quality_metrics.jsonl` has no cap or rotation**

- `QualityDashboard._save_record()` appends JSONL lines with no rotation or size cap. Over many sessions, this file could grow unbounded.
- In contrast, `SessionLogger` has rotation (`_maybe_rotate()`). `quality_metrics.jsonl` does not.
- **Impact**: Medium-low. The file is non-authoritative, and `_load_metrics()` reads sequentially with per-line error tolerance, but unbounded growth could slow dashboard startup.

**GAP-4: Warning count aggregation loses semantic detail**

- `QualityDashboard.record_validation()` stores `"warnings": len(result.get("warnings", []))` — only the count, not the warning content.
- `episode_production.jsonl` preserves full `warnings`, `final_warnings`, and `candidate_warnings` arrays with content.
- `stage_attempts` stores `advisory_flags` JSON but not per-warning detail.
- Operator cannot reconstruct per-episode warning content from the dashboard alone; must go to `episode_production.jsonl` for full detail.
- **Impact**: Low. The authoritative JSONL has full content. The dashboard count is sufficient for trend monitoring.

**GAP-5: No cross-stage quality signal join**

- Each stage writes independently to its own sinks. There is no existing query or view that joins Stage 2 arc selection quality → Stage 3 blueprint quality → Stage 4 manuscript quality for the same episode/arc as a unified quality chain.
- `FailureAnalyzer` provides per-stage analysis but not an explicit cross-stage quality-chain view.
- **Impact**: Medium. Operators cannot currently answer "does a high Stage 2 score predict high Stage 4 score?" without manual joins. However, the data exists across the DB tables — only the query/view is missing.

**GAP-6: `episode_quality_labels` and `episode_quality_signals` exist only for PASS episodes**

- REJECT episodes do not get quality labels or Python-only signals recorded.
- For REJECT episodes, the only quality data is: verdict/score in `stage_attempts` + `director_selections`, plus the full `episode_production.jsonl` entry.
- There is no Python-only quality signal computed for rejected manuscripts (CED, AI slop, etc.).
- **Impact**: Low-Medium. Rejected manuscript quality signals could help diagnose why rejection happened, but computing them adds work for artifacts that will be discarded. The reject_reason and score_breakdown fields already provide diagnostic value.

**GAP-7: No aggregate quality health metric**

- The system has many individual quality signals (score, CED, AI slop, compression, burstiness, pass rate, trend) but no single computed "quality health" composite metric.
- The operator must interpret multiple signals independently via the dashboard.
- **Impact**: Low. A composite metric risks hiding detail. The current multi-signal approach is defensible. A composite would be a nice-to-have for at-a-glance monitoring, not a gap in observability.

## 5. Confidence Assessment

| Category | Confidence | Notes |
|---|---|---|
| Authoritative sinks identified | 98% | Explicit authority contract exists |
| Non-authoritative companions identified | 95% | Some companion endpoints may have unlisted aggregation logic |
| Gap severity ratings | 90% | GAP-5 and GAP-6 impact estimates may shift with operator workflow data |
| Recommendation | 90% | Requires confirmation that cross-stage join is not already available elsewhere |

Overall estimated confidence: **93%**

## 6. Findings Summary

1. **Quality/verdict/pass-rate observability is the most mature of the four survey lanes.** The system has 5 authoritative sinks (3 DB tables + 1 JSONL + 1 DB table pair) and 4 companion sinks with clear authority designations.

2. **Verdict and score data is richly captured** at every attempt across all production stages, with both authoritative and companion surfaces cross-checkable via `FailureAnalyzer.sink_alignment_summary()`.

3. **Pass-rate computation already exists** with first-attempt rate, eventual rate, trend, alerts, method success rates, and ROL calculations.

4. **The main observability gaps are not in data capture but in data joins** — specifically the absence of a cross-stage quality chain view (GAP-5) and the REJECT-only quality signal gap (GAP-6).

5. **`quality_metrics.jsonl` rotation absence (GAP-3)** is the only low-blast instrumentation issue, and it's a maintenance concern rather than an observability gap.

6. **No existing statistics are missing for reliable operator judgment of individual episode quality.** The gap is in higher-level aggregate analysis (cross-stage trends, composite health).

## 7. Recommendation

**Do not open an execution SSOT for this lane.** The quality/verdict/pass-rate observability is already mature, with clear authority contracts and rich data capture.

If a bounded observability-core wave opens later, this lane's contribution would be:
- **Low priority**: Add `quality_metrics.jsonl` rotation (GAP-3, ~10 lines)
- **Medium priority**: Add a DB view or query helper for cross-stage quality chain (GAP-5, requires design)
- **Deferred**: REJECT episode quality signals (GAP-6, adds work per rejected artifact — ROI unclear)
- **Deferred**: Aggregate quality health composite (GAP-7, design risk)

---

Dominant observability gap in this lane: mixed (cross-stage join + REJECT signal coverage, not verdict/score capture)
Best bounded instrumentation candidate in this lane: cross-stage quality chain view (GAP-5)
Should this lane alone trigger a new SSOT: no
