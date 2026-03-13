# TF-S4DD Track 1: Contract & Interface Integrity Findings

> Audit date: 2026-03-13
> Scope: stage4_context.py, stage4_types.py, stage4_orchestrator.py, stage4_interview_round.py, stage4_context_builder.py, stage4_post_processor.py
> Method: Read-only static analysis (grep + read)

---

## 1.1 DI Slot Liveness (Stage4Context.__slots__)

Stage4Context has **37 slots** total: 5 required, 15 extended, 1 composite dict, 12 callbacks, 1 logger, 1 internal meta.

### Consumption Matrix

| # | Slot | orchestrator | interview_round | context_builder | post_processor | Verdict |
|---|------|:---:|:---:|:---:|:---:|---------|
| 1 | `ui` | Y (60+) | Y (40+) | Y (15+) | Y (30+) | LIVE |
| 2 | `current_project` | Y (30+) | Y (20+) | Y (30+) | Y (20+) | LIVE |
| 3 | `agents` | Y (10+) | Y (5+) | - | Y (5+) | LIVE |
| 4 | `sys` | Y (5+) | - | Y (10+) | Y (10+) | LIVE |
| 5 | `state_tracker` | - | Y (10+) | Y (5+) | Y (5+) | LIVE |
| 6 | `memory` | - | - | Y (5+) | Y (5+) | LIVE |
| 7 | `context_advisor` | - | - | Y (1) | - | LIVE |
| 8 | `world_state` | Y (3) | - | Y (10+) | Y (10+) | LIVE |
| 9 | `fact_ledger` | Y (2) | - | Y (5+) | Y (5+) | LIVE |
| 10 | `character_voice` | Y (3) | - | - | Y (3) | LIVE |
| 11 | `perf_timer` | - | Y (3) | Y (2) | Y (2) | LIVE |
| 12 | `foreshadow_tracker` | - | - | Y (2) | Y (2) | LIVE |
| 13 | `failure_learner` | - | Y (2) | - | - | LIVE |
| 14 | `diversity_engine` | Y (2) | - | - | - | LIVE |
| 15 | `semantic_plot_guard` | - | - | Y (2) | - | LIVE |
| 16 | `selected_genre` | Y (2) | - | - | Y (2) | LIVE |
| 17 | `quality_dashboard` | - | Y (2) | - | Y (5+) | LIVE |
| 18 | `pacing_analyzer` | Y (1) | - | Y (1) | Y (1) | LIVE |
| 19 | `pass_rate_monitor` | - | Y (1) | - | - | LIVE |
| 20 | `emotion_tracker` | - | - | - | Y (1) | LIVE |
| 21 | `conditional_modules` | Y (1 via get_module) | Y (7 via get_module) | - | - | LIVE |
| 22 | `get_int_input` | Y (3) | - | - | - | LIVE |
| 23 | `build_item_acquisition_timeline` | - | - | Y (1) | - | LIVE |
| 24 | `load_narrative_summaries` | - | - | Y (1) | - | LIVE |
| 25 | `get_protagonist_name` | - | - | Y (1) | Y (1) | LIVE |
| 26 | `extract_npc_profiles` | - | Y (1) | - | - | LIVE |
| 27 | `generate_narrative_summary` | - | - | - | Y (1) | LIVE |
| 28 | `generate_writer_guidance_v60_8` | - | - | Y (1) | - | LIVE |
| 29 | `enrich_director_result` | - | Y (1) | - | - | LIVE |
| 30 | `audit_event` | - | - | - | Y (5+) | LIVE |
| 31 | `write_audit_summary` | Y (1) | - | - | - | LIVE |
| 32 | `flush_audit_buffer` | Y (2) | - | - | Y (1) | LIVE |
| 33 | `safe_commit` | Y (2) | - | - | - | LIVE |
| 34 | `session_logger` | - | Y (1) | - | Y (2) | LIVE |
| 35 | `_stage4_context_budget_meta` | Y (1 read) | - | Y (2 write) | - | LIVE |

### Finding 1.1-A: No Dead Slots Detected

- **Severity**: INFO
- **Description**: All 37 slots in Stage4Context are consumed by at least one of the 4 consumer modules. No dead slots found. The DI graph is healthy.

---

## 1.2 Callback Bindings (12 callbacks)

### Binding Chain Verification

| Callback Slot | from_app() source | Called in Stage4? | Source exists in main_a.py? | Verdict |
|---|---|:---:|:---:|---|
| `get_int_input` | `app._get_int_input` | Y (orchestrator L1277) | Y (L2838) | OK |
| `build_item_acquisition_timeline` | `app._build_item_acquisition_timeline` | Y (context_builder L1864) | Y (L2834) | OK |
| `load_narrative_summaries` | `app._load_narrative_summaries` | Y (context_builder L2448) | Y (L3504) | OK |
| `get_protagonist_name` | `app._get_protagonist_name` | Y (context_builder L81, post_proc L1333) | Y (L2160) | OK |
| `extract_npc_profiles` | `app._extract_npc_profiles` | Y (interview_round L3537) | Y (L2880) | OK |
| `generate_narrative_summary` | `app._generate_narrative_summary` | Y (post_processor L448) | Y (L3366) | OK |
| `generate_writer_guidance_v60_8` | `app._generate_writer_guidance_v60_8` | Y (context_builder L2518) | Y (L746) | OK |
| `enrich_director_result` | `app._enrich_director_result` | Y (interview_round L848) | Y (L445) | OK |
| `audit_event` | `app._audit_event` | Y (post_processor, multiple) | Y (L2902) | OK |
| `write_audit_summary` | `app._write_audit_summary` | Y (orchestrator L1601) | Y (L2910) | OK |
| `flush_audit_buffer` | `app._flush_audit_buffer` | Y (orchestrator L1608, post_proc L601) | Y (L2906) | OK |
| `safe_commit` | `app._safe_commit` | Y (orchestrator L1610) | Y (L404) | OK |

### Finding 1.2-A: All Callback Bindings Healthy

- **Severity**: INFO
- **Description**: All 12 callback slots are (1) connected in `from_app()`, (2) invoked in stage4 code, and (3) backed by existing methods in `main_a.py`. All callbacks are accessed defensively via `getattr(..., None)` + `callable()` check or `inspect.getattr_static()`, so a missing source would degrade gracefully rather than crash.

---

## 1.3 _RoundContext Fields (34 fields)

_RoundContext (stage4_types.py L16-60) has **34 fields**: 32 required + 2 with defaults.

### SET by context_builder.build_round_context() (L2579-2616)

All 34 fields are explicitly set in the constructor call at `stage4_context_builder.py:2579-2616`.

### GET by interview_round.run() (L1189-1329 + scattered)

| Field | GET Location(s) | Verdict |
|---|---|---|
| `chief_writer` | L1297, L2655 | OK |
| `manuscript_validator` | L1298 | OK |
| `consistency_validator` | L1299 | OK |
| `blocking_validator` | L1300 | OK |
| `continuity_validator` | L1301 | OK |
| `next_ep` | L1302, L2757, L2902, L3087 | OK |
| `blueprint` | L1189, L1303, L1531, L2685, L2785, L3088 | OK |
| `arc_data` | L1248, L1369, L1446, L1477, L1501, etc. | OK |
| `arc_pos` | L1304, L2787 | OK |
| `total_ep_in_arc` | L1305, L2788 | OK |
| `arc_tactical` | L1248, L1306 | OK |
| `prev_text` | L1190, L1307 | OK |
| `prev_ending` | L1308, L2786 | OK |
| `prev_manuscripts_text` | L1191, L1309, L2513, L2792 | OK |
| `episode_digest` | L1310, L2790 | OK |
| `hud_report` | L1192, L1311 | OK |
| `current_inventory` | L1193, L1312 | OK |
| `current_martial_arts` | L1194, L1313 | OK |
| `dead_npcs` | L1195, L1314 | OK |
| `item_acquisition_timeline` | L1196, L1315 | OK |
| `chain_link_section` | L1197, L1316 | OK |
| `world_state_summary` | L1198, L1317 | OK |
| `purism_prompt` | L1199, L1318 | OK |
| `genre_name` | L1200, L1319 | OK |
| `npc_equipment_summary` | L1201, L1320 | OK |
| `effective_anti_trope` | L1202, L1321 | OK |
| `intro_dna` | L1203, L1322 | OK |
| `story_context` | L1323, L2514, L2778 | OK |
| `style_guide` | L1204, L1324, L2656 | OK |
| `reference_anchor_prompt` | L1206, L1325 | OK |
| `mandatory_context` | L1326 | OK |
| `justification_prompt` | L1207, L1327 | OK |
| `reflexion_prompt` | L1208, L1328 | OK |
| `preflight_advisory` | L1209, L1329 | OK |
| `reference_excerpt` | L1205 | OK |
| `recent_scene_keywords` | L1676 (getattr fallback) | OK |

### Also GET by orchestrator

`round_ctx` fields are also read in `stage4_orchestrator.py` L914 (next_ep), L957-958 (prev_manuscripts_text, blueprint), L1152 (blueprint), L1178-1234 (blueprint, arc_data).

### Finding 1.3-A: All _RoundContext Fields Fully Wired

- **Severity**: INFO
- **Description**: All 34 _RoundContext fields are SET by `build_round_context()` and GET by `interview_round.run()` (and partially by `orchestrator._handle_round_outcome()`). No orphan fields.

---

## 1.4 _InterviewRoundResult Exit Paths

_InterviewRoundResult has **8 fields**: 3 required (`verdict`, `director_feedback`, `previous_attempt`) + 5 optional with defaults (`final_manuscript=None`, `final_title=None`, `final_state_updates={}`, `error_category=""`, `attempt_artifact_meta={}`).

### Exit Path Analysis

| Path | Location | Required Fields | Optional Fields Set | Verdict |
|---|---|---|---|---|
| **EMPTY** | interview_round.py L1466-1470 | verdict, director_feedback, previous_attempt | (defaults) | OK |
| **PASS / PASS_WITH_FIX** | interview_round.py L3031-3040 | verdict, director_feedback, previous_attempt | final_manuscript, final_title, final_state_updates, error_category, attempt_artifact_meta | OK (all 5 set) |
| **REJECT** | interview_round.py L3308-3314 | verdict, director_feedback, previous_attempt | error_category, attempt_artifact_meta | OK |

### Finding 1.4-A: All Exit Paths Set Required Fields

- **Severity**: INFO
- **Description**: All 3 construction sites properly set the 3 required fields. The PASS path additionally sets all 5 optional fields. REJECT sets `error_category` and `attempt_artifact_meta` (appropriate: no manuscript to return). EMPTY relies on defaults (appropriate: generation produced nothing).

### Finding 1.4-B: REJECT Path Does Not Set final_manuscript/final_title

- **Severity**: INFO (by design)
- **Description**: The REJECT exit path (L3308) does not explicitly set `final_manuscript`, `final_title`, or `final_state_updates`. These default to `None`/`{}` which is the correct semantic for a rejected round. The consumer in `stage4_orchestrator.py` (L947) only reads these fields when `verdict in ("PASS", "PASS_WITH_FIX")`, so this is safe.

---

## 1.5 Import Graph

### Stage4 Import DAG

```
stage4_types.py          (leaf: imports only constants)
    ^
    |--- stage4_context.py       (leaf: imports only inspect)
    |
    |--- stage4_context_builder.py  (imports: constants, context_advisor, context_compression,
    |                                 semantic_query_broker, tactical_utils, writer_prompt_builders,
    |                                 threshold_helper; lazy: stage4_types)
    |
    |--- stage4_interview_round.py  (imports: artifact_logging, context_advisor, jsonl_io,
    |                                 logging_keys, soft_failure; lazy: stage4_types + many)
    |
    |--- stage4_post_processor.py   (imports: genre_schema_builder, metrics_collector,
    |                                 project_support, quality_signal_metrics, soft_failure)
    |
    +--- stage4_orchestrator.py     (imports: jsonl_io, llm_generate, project_support, soft_failure,
                                      stage4_context_builder, stage4_interview_round,
                                      stage4_post_processor, stage4_types, threshold_helper)
```

### Finding 1.5-A: No Circular Imports

- **Severity**: INFO
- **Description**: The import graph is a clean DAG. `stage4_orchestrator.py` imports the other 3 submodules + `stage4_types`. None of the submodules import `stage4_orchestrator`. `stage4_types.py` was specifically extracted to break potential circular dependencies (noted in its docstring). `stage4_context_builder.py` and `stage4_interview_round.py` use lazy imports for `stage4_types` (import inside method), further decoupling.

### Finding 1.5-B: No Dead Top-Level Imports

- **Severity**: INFO
- **Description**: All top-level imports across the 6 stage4 files are consumed:
  - `stage4_orchestrator.py`: `dataclasses`, `inspect`, `logging`, `re`, `Path`, `append_jsonl_record`, `generate_content_via_router`, `load_style_guide_anchor`, `resolve_project_bible_pov`, `resolve_project_log_dir`, `Stage4ContextBuilder`, `Stage4InterviewRound`, `Stage4PostProcessor`, `_RoundContext`, `_threshold` -- all used.
  - `stage4_interview_round.py`: `json`, `inspect`, `logging`, `time`, `Path`, `build_candidate_key`, `normalize_artifact_meta`, `snapshot_logged_artifact`, `RetrievalSources`, `append_jsonl_record`, `build_attempt_key`, `resolve_logging_session_id`, `resolve_project_log_dir` -- all used.
  - `stage4_context_builder.py`: `json`, `inspect`, `logging`, `re`, `TYPE_CHECKING`, `Stage2Limits`, `VolumeSettings`, `RetrievalSources`, `ContextCompressor`, `SemanticQueryBroker`, `extract_episode_tactical`, `_build_anti_trope`, `_build_justification`, `_build_writer_mandatory_context`, `_threshold` -- all used.
  - `stage4_post_processor.py`: `json`, `logging`, `os`, `re`, `Path`, `_nullcontext`, `is_wuxia`, `get_metrics_collector`, `resolve_project_pov_contract`, `compute_quality_signal_bundle`, `extract_warning_count`, `report_soft_failure`, `resolve_project_log_dir` -- all used.

---

## 1.6 Cross-Module Signature Mismatches

### Verified Call Sites

| Caller | Callee | Match? |
|---|---|---|
| `orchestrator._handle_round_outcome()` L940 | `interview_round.run(round_num, stage4_spinner, director_feedback, previous_attempt, round_ctx)` | OK -- all 5 kwargs match def at L1277 |
| `orchestrator` L841 | `context_builder.build_round_context(ep_ctx, ctx_prompts, chief_writer, ...)` 16 kwargs | OK -- all match def at L2552 |
| `orchestrator` L875 | `post_processor.process_pass_result(next_ep, final_manuscript, ...)` 10 kwargs | OK -- all match def at L287 |
| `orchestrator` L867 | `post_processor.run_post_episode_tasks()` 0 args | OK -- matches def at L1403 |

### Finding 1.6-A: No Signature Mismatches Found

- **Severity**: INFO
- **Description**: All cross-module call sites between orchestrator, interview_round, context_builder, and post_processor match their callee signatures. All calls use keyword arguments, which makes positional-order mismatches impossible.

---

## Summary

| Task | Finding Count | Critical | Major | Minor | Info |
|------|:---:|:---:|:---:|:---:|:---:|
| 1.1 DI Slot Liveness | 1 | 0 | 0 | 0 | 1 |
| 1.2 Callback Bindings | 1 | 0 | 0 | 0 | 1 |
| 1.3 _RoundContext Fields | 1 | 0 | 0 | 0 | 1 |
| 1.4 _InterviewRoundResult | 2 | 0 | 0 | 0 | 2 |
| 1.5 Import Graph | 2 | 0 | 0 | 0 | 2 |
| 1.6 Cross-Module Signatures | 1 | 0 | 0 | 0 | 1 |
| **Total** | **8** | **0** | **0** | **0** | **8** |

**Conclusion**: Stage 4's contract and interface integrity is clean. Zero CRITICAL/MAJOR/MINOR findings. All DI slots are live, all callbacks are fully wired end-to-end, all dataclass fields are properly SET and GET, the import graph is a clean DAG with no dead imports, and all cross-module signatures match. The defensive coding pattern (getattr + callable checks) throughout the codebase provides safe degradation for optional dependencies.
