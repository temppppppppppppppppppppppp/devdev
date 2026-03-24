Date: 2026-03-24
Document Type: evidence manifest
Lane: T2 — Stage 4 Authority / Verdict Flow
Parent Report: `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict.md`

## 1. File Inventory

| File | Lines | Methods | Dataclasses |
|---|---|---|---|
| `modules/core/stage4_interview_round.py` | 5,979 | 148+ | 8 |
| `modules/core/stage4_director_runtime.py` | 1,518 | 22 | 7 |
| `modules/core/stage4_post_processor.py` | 1,010 | 19 | 0 |
| `modules/core/stage4_post_pass_runtime.py` | 1,350 | 30 | 0 |
| `modules/core/stage4_reject_runtime.py` | 886 | 12 | 3 |
| `modules/core/stage4_retry_runtime.py` | 1,096 | 16 | 8 |
| `modules/domain/agents/director_ensemble.py` | 2,289 | 28 | 4 |

Total: 14,128 lines, 275+ methods, 30 dataclasses.

## 2. Key Line Anchors

### Settled (from prior SSOT, confirmed in live code)
- `stage4_interview_round.py:152-172` — Section Map (navigation aid)
- `stage4_interview_round.py:2248-2251` — `_god1_*` producer comment + TODO
- `stage4_director_runtime.py:102-104` — `_god1_*` consumer comment
- `stage4_director_runtime.py:241-242` — `get_module()` debug log on None
- `stage4_post_pass_runtime.py:1079-1082` — `_save_world_state_atomic` void return docstring
- `stage4_post_processor.py:953` — early-return blast-radius warning

### Active Hotspots
- `director_ensemble.py:1346-1388` — verdict field proliferation (P0)
- `director_ensemble.py:976-1157` — quality gate mutation chain (P1)
- `director_ensemble.py:612-628` — `_EnsembleSelectionState` undocumented (P1)
- `stage4_interview_round.py:2767-2794` — 26-param `_finalize_round_outcome` (P1)
- `stage4_post_pass_runtime.py:26-47` — 7 thin delegates (P1)
- `stage4_interview_round.py:3806-3878` — `_process_verdict` gate logic (P1)
- `stage4_retry_runtime.py:825-909` — retry lane routing (P1)

## 3. Verdict Field Inventory (director_ensemble return)

| Field | Meaning | When they diverge |
|---|---|---|
| `verdict` | Alias of `final_verdict` | Never — always equal |
| `final_verdict` | Post-gate authoritative verdict | After adaptive verdict or firewall override |
| `director_verdict` | Raw LLM verdict before quality gates | Before firewall/adaptive changes |
| `original_verdict` | Same as `director_verdict` | Alias — always equal to `director_verdict` |
| `gate_basis` | Which gate caused the verdict | `director_primary_pass`, `director_primary_reject`, `adaptive_promotion`, `firewall_override` |

**Evidence location:** `director_ensemble.py:1346-1388` return dict, `_derive_gate_basis()` helper.

## 4. Quality Gate Mutation Chain (director_ensemble)

| Method | Line | Mutated Fields |
|---|---|---|
| `_apply_scm_single_candidate_cap` | L1005 | `state.score` (cap to 90 if single candidate >=95) |
| `_apply_contradiction_firewall_gate` | L1023 | `state.firewall_triggered`, `state.firewall_fixable`, `state.firewall_reason`, `state.original_verdict`, `state.score`, `state.pre_firewall_score`, `state.contradiction_details` |
| `_log_numeric_consistency_gate` | L1091 | None (logging only) |
| `_apply_nc3_consistency_penalty` | L1124 | `state.score`, `state.score_breakdown_raw["python_warnings"]` |

## 5. `_god1_*` Channel Attributes

| Attribute | Producer | Consumer | Type |
|---|---|---|---|
| `_god1_stage4_spinner` | interview_round:2252 | director_runtime:105 | spinner object |
| `_god1_round_num` | interview_round:2253 | director_runtime:106 | int |
| `_god1_arc_pos` | interview_round:2254 | director_runtime:107 | int |
| `_god1_total_ep_in_arc` | interview_round:2255 | director_runtime:108 | int |
| `_god1_arc_data` | interview_round:2256 | director_runtime:109 | dict |
| `_god1_prev_manuscript` | interview_round:2257 | director_runtime:110 | str |
| `_god1_director_memory_context` | director_runtime:167 | interview_round:2271 | str (reverse) |

Note: 7th attribute (`_god1_director_memory_context`) flows in reverse — set by consumer, read by producer.

## 6. Post-Pass Settlement Flow

```
Stage4PostProcessor.process_pass_result()
  ├── _save_pass_result_primary_db()        [DB save — fail fast]
  ├── _save_pass_result_quality_sidecars()   [quality metrics]
  ├── _run_pass_result_local_side_effects()  [logs, emotion, artifacts]
  ├── _run_pass_result_post_pass_pipeline()
  │     └── Stage4PostPassRuntime
  │           ├── _submit_manager_async()     [ThreadPoolExecutor]
  │           ├── _memorize_and_validate()    [bible memorization]
  │           ├── _collect_manager_and_build_delta()
  │           ├── _save_world_state_atomic()  [WorldState + FactLedger]
  │           └── _run_post_pass_advisories() [satisfaction, pacing, NPC guards]
  └── _finalize_pass_result_session()        [metrics, perf timer]
```

## 7. Retry Lane Routing (stage4_retry_runtime)

| Lane | Condition | Method |
|---|---|---|
| ASP correction | asp_manuscript available + score conditions | `_run_asp_correction` L1039 |
| Inplace | score >= threshold + patch_enabled | `_run_inplace_retry_lane` L909 |
| Patch/rewrite | patch conditions met | `_run_patch_or_rewrite_retry_lane` L972 |
| Full regeneration | default fallback | via `generate_candidates` L238 |

Priority determined by `_resolve_retry_lane_routing` at L825.

## 8. Thin Delegate Inventory (stage4_post_pass_runtime L26-47)

| Method | Forwards To |
|---|---|
| `_report_soft_failure` | `owner._report_soft_failure` |
| `_raise_if_save_failed` | `owner._raise_if_save_failed` |
| `_extract_state_change_info` | `owner._extract_state_change_info` |
| `_truth_gate_llm_ask` | `owner._truth_gate_llm_ask` |
| `_build_active_pressure_vectors` | `owner._build_active_pressure_vectors` |
| `_normalize_active_pressure_vectors` | `owner._normalize_active_pressure_vectors` |
| `_persist_karma_status` | `owner._persist_karma_status` |
| `_best_effort_rollback_manager` (partial) | `owner._best_effort_rollback_manager` |
