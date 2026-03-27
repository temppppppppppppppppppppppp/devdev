# System Maturity Next-Band Wave 1 Execution SSOT

Date: 2026-03-27
Status: closed
Canonical Path: `docs/2026-03-27/system-maturity-next-band-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/system-maturity-next-band-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/router/stage3/stage4/fact/main_a/config surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked dated docs, provider adapter/tests, BI/TR artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `cost-persistence mismatch resolved by fixing round(cost,4)->round(cost,6) in metrics_collector.py; fresh proof artifact now shows coherent identity+usage+cost+persistence on the vertex_ai path`
Source Survey Docs:
- `docs/2026-03-27/rol-system-maturity-banding-5terminal-master-order.md`
- `docs/2026-03-27/rol-system-maturity-banding-5terminal-merge-audit.md`
- `docs/2026-03-27/opus/rol-system-maturity-t1-governance-queue.md`
- `docs/2026-03-27/opus/rol-system-maturity-t2-structure-optimization.md`
- `docs/2026-03-27/opus/rol-system-maturity-t3-runtime-stability.md`
- `docs/2026-03-27/opus/rol-system-maturity-t4-persistence-observability.md`
- `docs/2026-03-27/opus/rol-system-maturity-t5-advancement-readiness.md`
Evidence Artifacts:
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-exception-review-outcome.md`
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-canary-contamination-note.md`
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-stale-reference-sweep.md`
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-stale-reference-findings.txt`
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-stale-reference-cleanup-closure.md`
- `docs/2026-03-27/temp-execution-queue-process-health-scorecard.md`
- `projects/canary_0327_prs_wave1/logs/stage3_canary_summary.json`
- `docs/2026-03-27/system-maturity-next-band-wave1-tranche3-vertex-runtime-proof.json`
- `docs/2026-03-27/system-maturity-next-band-wave1-execution-closure.md`
- live recheck of `projects/canary_0327_prs_wave1/project_data.db`
- live recheck of `tests/test_llm_router.py`
- live recheck of `tests/test_cost_tracking.py`
- live `python scripts/ops_validator.py --strict`
Side-Effect Coverage: covered

## 1. Intent

- record the finalized 3-tranche maturity uplift honestly against the current workspace
- preserve already-landed structural and operator-discipline gains as dated closure evidence
- capture that the exercised `vertex_ai` path now satisfies identity, usage/cost, and persistence linkage requirements
- record that closure cleanup completed and the temp execution queue is exhausted

## 2. Re-Audit Summary

- queue truth:
  - during final realization this was the sole active temp execution item
  - after the closure audit, the temp execution mirror, temp roadmap mirror, and temp queue-state file were removed
  - `python scripts/ops_validator.py --strict` passes on the exhausted queue state
- Tranche 1 truth:
  - retained from earlier work
  - current recount remains `200+ = 0`, `180+ = 3`, `100+ = 189`
  - no structural regression was observed during this re-audit
- Tranche 2 truth:
  - scorecard, stale-reference cleanup, and exception review are present
  - fresh canary on `projects/canary_0327_prs_wave1` is clean and single-process
  - session-scoped evidence for `session_id=20260327_124530` shows `stage_attempts=3`, `blueprints=3`, PASS scores `92/96/88`
  - contaminated `canary_0327_stage3_cadence` remains non-authoritative
- Tranche 3 truth:
  - dated runtime proof artifact: `docs/2026-03-27/system-maturity-next-band-wave1-tranche3-vertex-runtime-proof.json`
  - root cause of the prior cost-persistence mismatch: `metrics_collector.py get_session_stats()` used `round(cost, 4)` which truncated micro-costs (e.g. `0.0000404`) to `0.0`
  - fix: `round(cost, 4)` → `round(cost, 6)` at L414 and L428, aligning with the scope summary which already used 6 decimal places
  - fresh proof (timestamp `2026-03-27T05:12:56+00:00`) now shows coherent cost across all layers:
    - response-layer `cost_usd=4e-05`
    - persistence session `metrics_total_cost_usd=4e-05`
    - persistence model_stats `cost_usd=4e-05`
    - scope `total_cost_usd=4e-05`
    - `cost_coherence_check.all_agree=true`
  - provider identity, usage/cost capture, and persistence linkage all agree on the exercised `vertex_ai` path

## 3. Scope

Included:
- Tranche 1. Structural re-freeze retention and current-state truth
- Tranche 2. Repeatable operator discipline proof
- Tranche 3. Multi-provider exercised-path proof for one chosen runtime path
- canonical SSOT / roadmap / temp queue updates needed to keep the active queue honest

Excluded:
- repo-wide refactor beyond the previously admitted structural tranche
- reopening the closed `provider-request-shape-stability-wave1`
- `_god1_*` replacement
- realm authority / NPC technique-model work
- narrative-pipeline artifacts

## 4. Tranche Status

### Tranche 1. Structural Re-Freeze and Canonical Refresh

Status: satisfied

- `BlueprintEnsembleGenerator._format_constraints` remains below 200 LOC
- current recount: `200+ = 0`, `180+ = 3`, `100+ = 189`
- no net growth in the 180+ band relative to the earlier execution-start baseline

### Tranche 2. Repeatable Operator Discipline Proof

Status: satisfied

- process health scorecard: `docs/2026-03-27/temp-execution-queue-process-health-scorecard.md`
- stale-reference cleanup closure: `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-stale-reference-cleanup-closure.md`
- exception review outcome: `docs/2026-03-27/system-maturity-next-band-wave1-tranche2-exception-review-outcome.md`
- clean canary:
  - command: `python scripts/run_stage3_canary.py full --source-project 코덱스_테스트 --target-project canary_0327_prs_wave1 --from-ep 1 --target-ep 3 --force`
  - session: `20260327_124530`
  - results: 3 episodes, all first-attempt PASS (`92/96/88`)
  - DB truth: session-scoped evidence shows `stage_attempts=3`, `blueprints=3`; older historical rows remain in the project DB outside this session
  - contaminated `canary_0327_stage3_cadence` was not used

### Tranche 3. Multi-Provider Exercised-Path Proof

Status: satisfied

- chosen path: `vertex_ai` (`vertexai:gemini-2.5-flash`)
- dated runtime proof: `docs/2026-03-27/system-maturity-next-band-wave1-tranche3-vertex-runtime-proof.json`
- code fix required: `modules/core/metrics_collector.py` L414 and L428: `round(cost, 4)` → `round(cost, 6)` to preserve micro-costs in `get_session_stats()`
- runtime execution (timestamp `2026-03-27T05:12:56+00:00`):
  - `generate_llm_response_via_router(client=None, model="vertexai:gemini-2.5-flash", ...)`
  - traversed: `LLMProviderRouter` → `VertexAIProvider` → Vertex AI API → `LLMResponse` → `BACKEND_FAMILY_MAP` safety belt → `MetricsCollector`
- provider identity: `vertex_ai / google_vertex / gemini` (differs from default `gemini / google_direct / gemini`)
- usage/cost capture: `input=18, output=14, thinking=22, cost_usd=4e-05`
- persistence linkage: session `20260327_141245`, `total_calls=1`, `total_cost_usd=4e-05`, model_stats `cost_usd=4e-05`
- cost coherence: `all_agree=true` across response-layer, session, model_stats, and scope
- this is verified runtime evidence, not code/test-only inference

## 5. Acceptance Status

- Tranche 1: satisfied
- Tranche 2: satisfied
- Tranche 3: satisfied
- wave-level status:
  - stronger than the starting label on all three axes (structural, operator-discipline, multi-provider)
  - starting label: `late stabilization / early optimization / not yet advancement`
  - post-wave: at least `early optimization with bounded multi-provider proof`
  - closed

## 6. Verification Summary

- live queue validation:
  - `python scripts/ops_validator.py --strict`
- current document hygiene:
  - `python scripts/check_utf8_hygiene.py docs/2026-03-27/system-maturity-next-band-wave1-execution-ssot.md docs/2026-03-27/state-and-maturity-execution-roadmap.md docs/temp/system-maturity-next-band-wave1-execution-ssot.md docs/temp/execution-roadmap.md`
- carried evidence from the already-closed provider/request-shape wave remains valid for the shared clean canary target, but does not by itself satisfy Tranche 3 runtime proof

## 7. Temp Queue Notes

- temp status: removed
- cleanup condition: satisfied and executed; all three tranches have coherent dated evidence
- this was the sole active queue item; the temp execution mirror, temp roadmap mirror, and temp queue-state file were removed during closure audit

## 8. Closure Record

- all 3 tranches satisfied with dated evidence
- code fix: `modules/core/metrics_collector.py` L414 and L428 `round(cost, 4)` → `round(cost, 6)` (aligned session-stats precision with scope-summary precision to preserve micro-costs)
- Tranche 3 proof artifact: `docs/2026-03-27/system-maturity-next-band-wave1-tranche3-vertex-runtime-proof.json`
- closure note: `docs/2026-03-27/system-maturity-next-band-wave1-execution-closure.md`
- residual scope intentionally left out:
  - exercised-path proof for Claude/Anthropic providers (neither enabled in `config/models.yaml`)
  - exercised-path proof for OpenAI provider (not enabled)
  - broader provider stack redesign

## 9. 3-Pass Audit Record

Pass 1. Structure and Scope
- identified the cost-persistence mismatch root cause: `round(cost, 4)` truncation in `get_session_stats()`
- fix is narrowly bounded to 2 lines in `metrics_collector.py`
- PASS

Pass 2. Evidence and Consistency
- fresh runtime proof shows `cost_coherence_check.all_agree=true`
- response-layer, session, model_stats, and scope costs all report `4e-05`
- provider identity `vertex_ai / google_vertex / gemini` correctly distinguished from default `gemini / google_direct / gemini`
- PASS

Pass 3. Execution and Readability
- the SSOT now reflects the completion of all three tranches with coherent evidence
- the proof artifact is self-contained, machine-readable, and includes the coherence check
- PASS

## 10. Confidence

Estimated confidence: 98%
