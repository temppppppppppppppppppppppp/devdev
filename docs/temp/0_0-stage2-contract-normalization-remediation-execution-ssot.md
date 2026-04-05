# 0_0 Stage2 Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: parked (survey-backed future wave; narrowed to Stage2-owned packet extraction and keep-drop normalization; not active while active Stage4 finalization seams remain higher priority)
Canonical Path: `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2 survey docs and lane drafts untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `2026-04-05 bounded `00_0405` survey added fresh Stage2 evidence: selected packet truth can diverge from final arc txt on location/item carryover, while high-signal correction and retrieval evidence remains hidden in audit/quality sinks; lane remains parked and queue order unchanged`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage2-production-consumption-global-evidence.json`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-evidence.json`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded, implementable future wave for `Stage2 contract normalization` without promoting it into the active queue ahead of current `Stage3 static survey` and unresolved `Stage4` finalization seams.

This execution SSOT exists because the latest survey already proved:

- `Stage2` has a real problem
- but that problem is primarily `authority packaging / contract drift`, not missing narrative content
- the first material drift still appears at `Stage3`
- therefore `Stage2` should be queued as a future upstream normalization wave, not treated as the immediate blocker

## 2. Baseline Facts

- `Stage2` is `content-sufficient but schema-fragile`.
- The strongest mission truth lives in `tactical_doc` prose rather than a strong structured packet.
- `constraint_summary` undergoes strength inversion downstream.
- `beat_sequence` and `hybrid_composition` are effectively dropped at the `Stage2 -> Stage3` boundary.
- `semantic_carryover` behaves like a dead or low-signal field in current practice.
- The first clearly visible narrative drift still appears in `Stage3`, not inside Stage2 artifacts themselves.
- Fresh `00_0405` evidence shows a second Stage2-local symptom: selected Stage2 packet truth can diverge from final arc txt truth on bounded location/item carryover even when the business-state spine stays coherent.
- Fresh `00_0405` evidence also shows that key Stage2 correction and retrieval facts are fragmented across `runtime_audit.jsonl` and `quality_metrics.jsonl` instead of being operator-visible in the console.

## 3. Scope

Included:

- `modules/domain/agents/arc_ensemble.py`
- `config/prompts/ensemble.yaml`
- bounded Stage2 mission-authority packet extraction and emission surfaces
- bounded Stage2-owned alias/export normalization at the Stage2 emission boundary
- bounded keep-or-drop normalization for Stage2-owned low-signal fields
- bounded Stage2 packet-to-txt round-trip normalization for carryover-relevant location/item/state fields
- bounded operator-visible observability for high-signal Stage2 auto-correct and retrieval facts
- regression coverage for Stage2 packet meaning and field survival

Excluded:

- downstream consumer-side rename sweep across `Stage3` / `Stage4`
- `Stage3` contract tightening
- `Stage4` remediation work
- fresh canary or runtime closure proof in this lane
- DB schema redesign
- artifact rewrites in `projects/`
- large terminology rename sweep across the whole repo in one turn

## 4. Pass 1. Inventory Summary

Primary Stage2 authority owners:

- `ArcEnsembleGenerator` and related Stage2 prompt/packet builders
- Stage2 artifact emission under `projects/*/plans/` and Stage2 log artifacts
- Secondary observability owners for later bounded realization:
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/quality_dashboard.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/session_logger.py`

Primary debt inventory for this wave:

1. mission truth trapped in `tactical_doc` prose
2. weak or thin structured bridge fields
3. Stage2-owned fields without explicit keep-or-drop policy
4. Stage2 emission aliases that blur the real canonical packet owner
5. selected Stage2 packet truth not always round-tripping cleanly into final arc txt truth
6. high-signal Stage2 correction and retrieval evidence hidden from operator-visible console flow

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is reactivated

- structured mission authority extraction from `tactical_doc`
- Stage2-owned packet alias normalization at emission time
- keep-or-drop decisions for dead or low-signal Stage2 fields

### Class B. Residual but related

- downstream consumer-side vocabulary alignment
- `constraint_summary` strength normalization across stages
- Stage3 compiler/substep reduction

### Class C. Explicitly deferred outside this lane

- active `Stage4` finalization seams
- current `Stage3` contract tightening future wave
- fresh canary/runtime proof
- broad architecture compression beyond this bounded packet/contract wave

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage2 prompt packet and emitted authority structure may change
  - future Stage2 artifact shape may shift where structured packet fields are strengthened

- DB / schema / transaction boundaries:
  - not applicable for this bounded future wave

- JSONL / log / audit sinks:
- packet field names and summary rendering may change in future surveys and audits
- bounded Stage2 observability facts may be mirrored into operator-visible UI logs in a future realization wave

- console / UI / operator output:
  - Stage2 authority packet logging may become more explicit
  - Stage2 auto-correct and retrieval emptiness may become operator-visible instead of sink-only

- rollback / recovery / retry:
  - not primary in this lane

- cache / global state:
  - possible packet cache key or shared-context shape impact if field names are normalized

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### Tranche 1. Mission Authority Extraction

Goal:

- stop relying on prose `tactical_doc` as the only real mission owner

Realization direction:

- derive a stronger structured mission packet from `tactical_doc`
- strengthen `episode_details` or replace its weak role with a more explicit canonical packet

### Tranche 2. Contract Vocabulary Normalization

Goal:

- make the Stage2 emission owner explicit without widening into downstream rename cleanup

Realization direction:

- normalize Stage2-owned packet aliases at the emission boundary
- reduce ambiguity between `tactical_doc`, `episode_details`, and the canonical mission packet

### Tranche 3. Dead-Field Keep-or-Drop Cleanup

Goal:

- stop carrying fields that are present but non-authoritative

Realization direction:

- explicit keep-or-drop decisions for:
  - `beat_sequence`
  - `hybrid_composition`
  - `semantic_carryover`

### Tranche 4. Bounded Observability Surfacing

Goal:

- stop hiding the strongest Stage2 correction and retrieval facts in audit-only or quality-only sinks

Realization direction:

- mirror high-signal Stage2 auto-correct summaries into operator-visible console/UI flow
- surface empty retrieval/context coverage as an explicit Stage2 warning rather than silent absence
- optionally surface `StateExtractor` tracked-item counts when they materially help operator understanding

## 8. Execution Tranches

1. Stage2 mission packet normalization
2. Stage2-owned packet alias normalization
3. dead-field keep-or-drop cleanup
4. bounded observability surfacing
5. bounded regression coverage
6. later runtime proof only after explicit reactivation

## 9. Acceptance Criteria

- Stage2 no longer relies on prose `tactical_doc` alone for mission authority
- Stage2 exports a stronger canonical mission packet or equivalent structured authority owner
- Stage2-owned field aliases no longer obscure which packet is canonical at emission time
- `beat_sequence`, `hybrid_composition`, and `semantic_carryover` each have an explicit keep-or-drop policy
- selected Stage2 packet truth and final arc txt truth no longer diverge on bounded carryover location/item/state fields without explicit policy
- high-signal Stage2 auto-correct and retrieval-emptiness facts are no longer completely hidden from operator-visible console flow
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage2 packet rendering regressions
- targeted Stage2 packet alias and field-survival regressions
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not let this parked wave outrank active `Stage4` finalization seams without explicit reprioritization
- do not widen this lane into downstream consumer rename cleanup in the same turn
- do not widen this lane into `Stage3` contract tightening in the same turn
- do not run a canary from this lane until explicit reactivation
- do not rewrite artifact history in `projects/`

## 12. Temp Queue Notes

- temp status: `parked`
- cleanup condition:
  - keep the temp mirror as a future-wave queue item until explicit closure or formal deactivation
- roadmap dependency:
  - this item stays below active `Stage4` lanes and below the nearer `Stage3` contract-tightening future wave

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a future bounded execution SSOT, not an active lane
- narrowed the lane to Stage2-owned packet extraction, alias normalization, and keep-or-drop policy only
- excluded downstream consumer rename cleanup, Stage3 tightening, and Stage4 remediation from scope

Pass 2, evidence and consistency:

- aligned the document with the global Stage2 production-consumption survey verdict
- kept claims bounded to known survey evidence and did not overclaim runtime impact

Pass 3, execution and readability:

- made the parking status explicit
- made the reactivation condition explicit
- kept tranches upstream-only and implementable rather than architectural-only

Confidence: `96%`

## 15. 2026-04-05 Evidence Appendix: `00_0405`

This appendix does not reactivate the lane and does not change roadmap order.

It records fresh bounded evidence that sharpens the parked Stage2 problem statement.

### 15.1 Artifact truth

The `00_0405` survey shows that selected Stage2 packet truth and final arc txt truth can diverge before Stage3 ever consumes the artifact.

- `arc_002.txt` ends in the Yeouido SOHO office while the selected Stage2 artifact for arc 2 already ends in the Gangnam representative office.
- `arc_003.txt` starts in the Gangnam representative office, which means the next arc already follows packet truth that the prior txt did not fully round-trip.
- `arc_004` selected packet start-state still carries the Ecuador memo while the final txt start-state drops it.

This is not a business-state collapse.

The same survey shows the numeric/business spine remains broadly coherent:

- about `2.0B KRW` foundation
- about `2.3B KRW` after arc 2
- about `3.0B KRW` after arc 3
- about `4.5B KRW` after arc 4

So the new bounded reading is:

- `Stage2 content-sufficient but packet-to-txt round-trip inconsistent`

### 15.2 Observability

The same survey shows that the strongest Stage2 reasons are fragmented across sinks:

- `ui_events.jsonl` exposes PASS envelopes, deterministic carryover, and state/equipment sync
- `runtime_audit.jsonl` alone exposes high-signal auto-correct reasons such as genre-field removal, `[PATCH-B]` item disappearance repair, and location rewrites
- `quality_metrics.jsonl` alone exposes retrieval emptiness such as `work_focus_present=false` and `vector_context_chars=0`

This means the operator console can confirm that Stage2 synchronization happened, but often cannot see why the system had to repair the arc or that retrieval/context coverage was effectively empty.

### 15.3 Owner impact

The appendix confirms the original parked lane and enriches its owner map.

Primary owner family remains:

- `modules/domain/agents/arc_ensemble.py`
- `config/prompts/ensemble.yaml`

Newly evidenced secondary owner family for the same parked future wave:

- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_preflight.py`
- `modules/core/quality_dashboard.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`

### 15.4 Queue-safe conclusion

The `00_0405` evidence enriches this parked SSOT. It does not justify:

- changing `parked` status
- changing roadmap priority
- promoting Stage2 above the active Stage4 queue
- activating realization tranches in the same turn

## 16. 2026-04-05 Bounded Realization Update: Observability Surfacing

This bounded realization update was executed only because the operator explicitly overrode queue order for a narrow Stage2 implementation slice.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/core/stage2_validation_pipeline.py`
  - mirrors high-signal auto-correct summaries into operator-visible `ui.log`
- `modules/core/stage2_preflight.py`
  - emits an explicit Stage2 retrieval-empty warning when vector context is empty instead of staying silent
- `modules/core/prompt_builder.py`
  - surfaces `StateExtractor` item-count summary into operator-visible `ui.log`

Bounded verification completed:

- `pytest tests/test_stage2_validation_pipeline.py -k "auto_correct_pressure or auto_correct_summary"`
- `pytest tests/test_stage2_preflight.py -k "build_stage2_vector_context_legacy_path_prepends_slot_summary_and_fact_ledger or build_stage2_vector_context_logs_when_retrieval_is_empty"`
- `pytest tests/test_prompt_builder.py -k "app_bound_path_uses_state_extractor_and_audit or app_bound_path_logs_items_tracked_summary"`
- `python -m py_compile modules/core/stage2_validation_pipeline.py modules/core/stage2_preflight.py modules/core/prompt_builder.py`
- `ruff check modules/core/stage2_validation_pipeline.py modules/core/stage2_preflight.py modules/core/prompt_builder.py tests/test_stage2_validation_pipeline.py tests/test_stage2_preflight.py tests/test_prompt_builder.py`
- `python scripts/check_utf8_hygiene.py modules/core/stage2_validation_pipeline.py modules/core/stage2_preflight.py modules/core/prompt_builder.py tests/test_stage2_validation_pipeline.py tests/test_stage2_preflight.py tests/test_prompt_builder.py`

Bounded implementation verdict:

- `Tranche 4. Bounded Observability Surfacing` is now partially realized
- packet-to-txt round-trip normalization and broader Stage2 contract normalization remain future-wave work

## 17. 2026-04-05 Bounded Realization Update: Arc Export Carryover Authority Surfacing

This bounded realization update was executed only because the operator explicitly overrode queue order for another narrow Stage2 implementation slice.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/core/project_manager.py`
  - `plans/arcs/*.txt` export now mirrors a `[Carryover Authority Packet]` block instead of relying on `tactical_doc` prose alone
  - export prefers `state_constraints.arc_end_state.location/equipment` and only falls back to `joint_docs.final_location/physical_inventory` when the structured end-state is absent
  - export now surfaces bounded carryover-relevant start/end location, start/end equipment, acquired items, consumed items, and `world_joint`

Bounded verification completed:

- `pytest tests/test_project_manager_arc_storage.py -q`
- `python -m py_compile modules/core/project_manager.py tests/test_project_manager_arc_storage.py`
- `ruff check modules/core/project_manager.py tests/test_project_manager_arc_storage.py`
- `python scripts/check_utf8_hygiene.py modules/core/project_manager.py tests/test_project_manager_arc_storage.py`

Complexity recount:

- `ProjectContext._normalize_arc_export_list`: `11 LOC`
- `ProjectContext._build_arc_authority_packet_lines`: `53 LOC`
- `ProjectContext._render_arc_txt`: `47 LOC`

Bounded implementation verdict:

- export-side packet-to-txt truth surfacing is now partially realized
- prompt-side and generator-side round-trip normalization remain future-wave work

## 18. 2026-04-05 Bounded Realization Update: Generation Carryover Authority Prompt Normalization

This bounded realization update was executed only because the operator explicitly overrode queue order for another narrow Stage2 implementation slice after a fresh run confirmed that the new observability/export patches were live but retrieval-empty and auto-correct pressure still remained visible in real Stage2 logs.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/domain/agents/four_phase_arc_generator.py`
  - `_generate_prev_context()` now emits a structured `[Carryover Authority Packet]` block inside previous-arc context
  - the packet mirrors `next_arc_start_location`, `next_arc_start_equipment`, `next_arc_start_injuries`, bounded finance carryover, and `carryover_world_joint`
- `modules/domain/agents/arc_ensemble.py`
  - prompt assembly now extracts and injects the carryover packet as its own prompt section instead of relying only on freeform previous-arc prose
  - prohibition summary and candidate evaluation now prefer the packet over loose `위치`/`소지품` regex fallback when judging opening-state continuity
- `config/prompts/ensemble.yaml`
  - `Carryover Authority Packet` is now explicitly ranked above generic `Previous Arc Context`
  - the prompt now instructs the model to open the arc from that packet and to block unearned item appearance unless explicitly acquired

Bounded verification completed:

- `pytest tests/test_arc_ensemble_lane_a.py -q`
- `pytest tests/test_four_phase_arc_generator.py -k "carryover_authority_packet or generate_prev_context_includes_financial_fields or build_prev_context_carryover_lines_direct_helper_includes_financial_fields" -q`
- `pytest tests/test_prompt_loader.py -k "ensemble_yaml_loads" -q`
- `python -m py_compile modules/domain/agents/arc_ensemble.py modules/domain/agents/four_phase_arc_generator.py`
- `python scripts/check_utf8_hygiene.py modules/domain/agents/arc_ensemble.py modules/domain/agents/four_phase_arc_generator.py config/prompts/ensemble.yaml tests/test_arc_ensemble_lane_a.py tests/test_four_phase_arc_generator.py`

Complexity recount:

- `_extract_carryover_authority_packet`: `28 LOC`
- `_normalize_carryover_packet_list`: `23 LOC`
- `_render_carryover_authority_packet`: `29 LOC`
- `ArcEnsembleGenerator._evaluate_candidate`: `157 LOC`
- `FourPhaseArcGenerator._build_prev_context_carryover_lines`: `68 LOC`

Bounded implementation verdict:

- prompt-side carryover authority normalization is now partially realized
- Stage2 still remains retrieval-empty in the observed fresh run, so broader generation quality/readiness normalization remains future-wave work

## 19. 2026-04-05 Bounded Realization Update: Mission Authority Extraction via Episode Details

This bounded realization update was executed only because the operator explicitly overrode queue order for another narrow Stage2 implementation slice after the carryover/export patches were already verified in fresh-run evidence.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/core/response_schemas.py`
  - `episode_details` is now described as the canonical per-episode mission packet rather than a weak optional summary
- `config/prompts/ensemble.yaml`
  - prompt contract now explicitly says `episode_details` wins over conflicting prose and must cover every episode in the arc range
- `modules/domain/agents/arc_ensemble.py`
  - generation finalization now backfills canonical `episode_details` from existing `episode_details`, `beat_sequence`, and bounded `tactical_doc` headers in that priority order
  - candidate scoring now penalizes missing or incomplete `episode_details` mission coverage instead of treating `tactical_doc` prose alone as sufficient

Bounded verification completed:

- `pytest tests/test_arc_ensemble_lane_a.py -q`
- `pytest tests/test_prompt_loader.py -k "ensemble_yaml_loads" -q`
- `python -m py_compile modules/core/response_schemas.py modules/domain/agents/arc_ensemble.py`
- `ruff check modules/core/response_schemas.py modules/domain/agents/arc_ensemble.py tests/test_arc_ensemble_lane_a.py`
- `python scripts/check_utf8_hygiene.py modules/core/response_schemas.py modules/domain/agents/arc_ensemble.py config/prompts/ensemble.yaml tests/test_arc_ensemble_lane_a.py`

Complexity recount:

- `_normalize_episode_detail_lines`: `14 LOC`
- `_normalize_episode_details`: `31 LOC`
- `_extract_episode_detail_map_from_beats`: `25 LOC`
- `_extract_episode_detail_map_from_tactical_doc`: `20 LOC`
- `_build_canonical_episode_details`: `20 LOC`
- `ArcEnsembleGenerator._ensure_required_fields`: stays below `120 LOC`
- `ArcEnsembleGenerator._evaluate_candidate`: remains below the `180+ LOC` guardrail

Bounded implementation verdict:

- `Tranche 1. Mission Authority Extraction` is now partially realized through `episode_details` promotion instead of a brand-new Stage2 packet family
- Stage2 still has broader vocabulary/dead-field/readiness work remaining, but mission truth no longer depends on `tactical_doc` prose alone in the generation path

## 20. 2026-04-05 Bounded Realization Update: Contract Vocabulary Normalization at Generation Boundary

This bounded realization update was executed only because fresh-run evidence still showed repetitive Stage2 auto-correct pressure on `tactical_doc` meta vocabulary, verbose state-field blobs, and `joint_docs` readback drift even after the carryover/mission-authority slices had landed.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/core/response_schemas.py`
  - `location`, `equipment`, `joint_docs.final_location`, and `joint_docs.physical_inventory` now explicitly describe short canonical labels instead of sentence-style prose
- `config/prompts/ensemble.yaml`
  - generation prompt now bans `Arc/Block/Stage` meta terms inside `tactical_doc`
  - prompt now states that `location/final_location/equipment/physical_inventory` must remain compact canonical fields, not descriptive scene sentences
- `modules/domain/agents/arc_ensemble.py`
  - candidate scoring now penalizes meta-vocabulary leakage, verbose location labels, sentence-style inventory blobs, and `joint_docs.final_location / arc_end_state.location` mismatch
  - finalization now backfills `joint_docs.final_location` from `arc_end_state.location` and `joint_docs.physical_inventory` from `arc_end_state.equipment` when the joint surface is empty

Bounded verification completed:

- `pytest tests/test_arc_ensemble_lane_a.py -q`
- `pytest tests/test_prompt_loader.py -k "ensemble_yaml_loads" -q`
- `python -m py_compile modules/core/response_schemas.py modules/domain/agents/arc_ensemble.py`
- `ruff check modules/core/response_schemas.py modules/domain/agents/arc_ensemble.py tests/test_arc_ensemble_lane_a.py`
- `python scripts/check_utf8_hygiene.py modules/core/response_schemas.py modules/domain/agents/arc_ensemble.py config/prompts/ensemble.yaml tests/test_arc_ensemble_lane_a.py`

Complexity recount:

- `_normalize_state_contract_list`: `17 LOC`
- `_looks_like_verbose_state_field`: `10 LOC`
- `_collect_state_contract_vocabulary_issues`: `33 LOC`
- `ArcEnsembleGenerator._ensure_required_fields`: remains below `140 LOC`
- `ArcEnsembleGenerator._evaluate_candidate`: remains below the `180+ LOC` guardrail

Bounded implementation verdict:

- `Tranche 2. Contract Vocabulary Normalization` is now partially realized at the Stage2 generation boundary
- broader readiness normalization and dead-field keep/drop decisions still remain future-wave work

## 21. 2026-04-05 Bounded Realization Update: Validator and Finalizer Contract Alignment

This bounded realization update was executed only because the operator explicitly asked to maximize Stage2 implementation before the next fresh run after the generation-boundary slices had already landed.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/domain/agents/unified_arc_validator.py`
  - Python-side validation now treats `episode_details` as a real mission-authority contract rather than a type-only optional field
  - validation now emits `MAJOR` structure/continuity issues when:
    - `episode_details` coverage is thinner than `ep_count`
    - `episode_details[*].details` is empty
    - `joint_docs.final_location` and `arc_end_state.location` diverge
    - `joint_docs.physical_inventory` and `arc_end_state.equipment` diverge
    - end-state location/inventory fields degrade into sentence-style blobs
- `modules/core/stage2_finalizer.py`
  - finalizer now aligns `joint_docs.physical_inventory` and `arc_end_state.equipment` to one canonical end-inventory truth before persistence
  - finalizer now aligns `joint_docs.final_location` and `arc_end_state.location` to one canonical end-location truth before persistence
  - this reduces packet-to-txt/export drift by making end-state authority explicit at the post-pass sink instead of leaving stale split fields alive

Bounded verification completed:

- `pytest tests/test_unified_arc_validator.py -q`
- `pytest tests/test_tf10_episode_details.py -k "validator" -q`
- `pytest tests/test_stage2_finalizer.py -k "syncs_start_equipment or inventory_from_arc_end_state_authority or final_location_from_arc_end_state_authority" -q`
- `python -m py_compile modules/domain/agents/unified_arc_validator.py modules/core/stage2_finalizer.py tests/test_unified_arc_validator.py tests/test_stage2_finalizer.py`
- `ruff check modules/domain/agents/unified_arc_validator.py modules/core/stage2_finalizer.py tests/test_unified_arc_validator.py tests/test_stage2_finalizer.py`
- `python scripts/check_utf8_hygiene.py modules/domain/agents/unified_arc_validator.py modules/core/stage2_finalizer.py tests/test_unified_arc_validator.py tests/test_stage2_finalizer.py`

Complexity recount:

- `_check_episode_details_contract`: `45 LOC`
- `_check_state_contract_alignment`: `78 LOC`
- `_python_validate`: `30 LOC`
- `_sync_stage2_end_state_inventory_contract`: `46 LOC`
- `_sync_stage2_end_location_contract`: `32 LOC`
- `_finalize_stage2_pass_arc_preparation`: `88 LOC`

Bounded implementation verdict:

- Stage2 acceptance and post-pass sinks now speak the same mission/carryover contract vocabulary as the earlier generation-boundary slices
- the remaining Stage2 pressure is now more cleanly upstream: retrieval emptiness, generation quality, and broader readiness normalization

## 22. 2026-04-05 Bounded Realization Update: Work-Focus Fallback Recovery

This bounded realization update was executed because fresh-run evidence still showed repeated `Stage2 retrieval empty (chars=0, slots=0, scene_engines=0)` rows, which meant the `work_focus` source itself was often collapsing to `{}` before retrieval planning.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/core/stage2_preflight.py`
  - when `sys.guard.select_retrieval_focus()` is unavailable, throws, or returns an effectively empty payload, Stage2 now derives a bounded fallback `work_focus`
  - fallback inputs are limited to existing Stage2 authority surfaces:
    - `block_theme`
    - `plot_suspension`
    - `episode_details`
    - `constraint_summary`
    - bounded `tactical_doc` / `arc_tactical` lines
    - bounded `current_vol_strategy.strategy_doc`
  - fallback output stays narrow:
    - `tracking_slots`
    - `mandatory_scene_engines`
    - empty `registry_profiles`
  - this raises the floor for Stage2 retrieval planning without overriding the normal guard-owned path when that path returns a real focus packet

Bounded verification completed:

- `pytest tests/test_stage2_preflight.py -k "fallback_work_focus or retrieval_is_empty or legacy_path_prepends_slot_summary or advisor_plan_dispatches_vec_and_npc_sources or work_focus_relation_slice_included" -q`
- `python -m py_compile modules/core/stage2_preflight.py tests/test_stage2_preflight.py`
- `python scripts/check_utf8_hygiene.py modules/core/stage2_preflight.py tests/test_stage2_preflight.py`

Complexity recount:

- `_normalize_work_focus_phrase`: `8 LOC`
- `_build_fallback_work_retrieval_focus`: `52 LOC`
- `_resolve_work_retrieval_focus`: `28 LOC`
- `_build_stage2_vector_context`: remains below the `180+ LOC` guardrail

Bounded implementation verdict:

- broader Stage2 readiness normalization still remains future-wave work
- but Stage2 no longer needs a healthy guard response to avoid the degenerate `work_focus={}` floor case

## 23. 2026-04-05 Bounded Realization Update: Raw-Block Work-Focus Recovery

Fresh-run evidence narrowed the remaining `work_focus={}` floor to a live-path mismatch between preflight input shape and the earlier fallback assumptions.

- authoritative evidence from `0000000000_0405` still showed:
  - `Stage2 retrieval empty (chars=0, slots=0, scene_engines=0)` in console/UI
  - `work_focus_present=false`, `tracking_slots_count=0`, `scene_engines_count=0` in `quality_metrics`
- root cause:
  - Stage2 preflight receives the pre-generation `enriched_block`, not the final arc artifact
  - `Analyst.enrich_raw_block_async()` preserves the raw treatment block and only appends newly introduced fields
  - therefore the earlier fallback's reliance on `episode_details` / `constraint_summary` was still too final-artifact-shaped for the live preflight path

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/core/stage2_preflight.py`
  - `_compose_work_focus_text()` now includes raw treatment-block authority surfaces, not only final-arc-like fields
  - `_build_fallback_work_retrieval_focus()` now derives bounded `tracking_slots` / `mandatory_scene_engines` from raw block metadata when the guard path is absent or empty
  - the new raw-block fallback reads only already-authoritative Stage2 inputs:
    - `content.context`
    - `content.event_villain`
    - `content.solution`
    - `content.reward`
    - `stakes`
    - `foreshadow`
    - `callback`
    - `relationship_delta`
    - `time_span`
    - `location`
    - bounded `genre_ext` fields
  - this keeps the fallback narrow while matching the actual preflight input shape seen in live Stage2

Bounded verification completed:

- `pytest tests/test_stage2_preflight.py -k "fallback_work_focus or retrieval_is_empty or raw_block_fallback or legacy_path_prepends_slot_summary or advisor_plan_dispatches_vec_and_npc_sources or work_focus_relation_slice_included" -q`
- `python -m py_compile modules/core/stage2_preflight.py tests/test_stage2_preflight.py`

Complexity recount:

- `_build_raw_block_focus_candidates`: `54 LOC`
- `_compose_work_focus_text`: remains below the `120+ LOC` watch band
- `_build_fallback_work_retrieval_focus`: remains below the `120+ LOC` watch band
- `_build_stage2_vector_context`: remains below the `180+ LOC` guardrail

Bounded implementation verdict:

- Stage2 still is not closure-ready
- retrieval-empty and broader generation/readiness pressure remain future-wave work
- but the live-path mismatch between raw `enriched_block` shape and work-focus fallback has now been explicitly addressed

## 24. 2026-04-05 Bounded Realization Update: Location Label Canonicalization Pressure

The latest `0000000000_0405` fresh run improved Stage2 verdict stability and restored non-empty retrieval planning, but the authoritative operator sinks still showed repeat Stage2 auto-correct pressure on every arc.

- authoritative evidence from `0000000000_0405` showed:
  - `PASS`, `PASS`, `PASS_WITH_FIX -> PASS`
  - `work_focus_present=true`, `tracking_slots_count=3`, `scene_engines_count=2`
  - remaining auto-correct families:
    - verbose sentence-style `arc_start_state.location`
    - verbose `joint_docs.final_location` / `arc_end_state.location`
    - non-wuxia `internal_energy` leakage in structured state packets
- root cause narrowed to two owners:
  - `ArcEnsembleGenerator` still under-penalized verbose start-location labels and non-wuxia state noise during candidate selection
  - Stage2 sync paths still allowed long scene-prose locations to remain the final authority label when a candidate slipped through

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Landed bounded slice:

- `modules/core/stage2_location_contract.py`
  - added a shared `collapse_stage2_location_label()` helper and `is_verbose_stage2_location_label()` detector for Stage2 state fields
- `modules/domain/agents/arc_ensemble.py`
  - `arc_start_state.location` sentence-style prose now counts as a state-contract vocabulary issue
  - non-wuxia `internal_energy` / `realm` / `qi_nature` / `martial_arts` leakage in `arc_start_state` / `arc_end_state` now incurs candidate penalties
- `modules/core/stage2_optimizer.py`
  - start/end location sync now collapses verbose scene prose to a shorter canonical label before authority sync
- `modules/core/stage2_finalizer.py`
  - `joint_docs.final_location` / `arc_end_state.location` sync now canonicalizes the final saved location label
  - first-episode start-state line sync now writes the same short location label into `tactical_doc`

Bounded verification completed:

- `pytest tests/test_stage2_optimizer.py -q`
- `pytest tests/test_arc_ensemble_lane_a.py -q`
- `pytest tests/test_stage2_finalizer.py -k "final_location_from_arc_end_state_authority or sync_stage2_end_location_contract_collapses_verbose_scene_label" -q`

Complexity recount:

- `collapse_stage2_location_label`: `30 LOC`
- `_collect_state_contract_vocabulary_issues`: remains below the `120+ LOC` watch band
- `_sync_stage2_end_location_contract`: remains below the `120+ LOC` watch band
- no touched production function crossed the `180+ LOC` guardrail

Bounded implementation verdict:

- Stage2 still is not closure-ready
- retrieval-empty is no longer the front blocker in this lane
- the remaining Stage2 pressure is now narrower:
  - generation/finalizer location vocabulary drift
  - minor numeric phrasing pressure
  - future-wave dead-field/readiness cleanup

## 25. 2026-04-05 Bounded Realization Update: Arc 3 Entity/Numeric Gate Hardening

The latest `0000000000_0405` Stage2 fresh run narrowed the remaining front blocker to `Arc 3`.

- authoritative failure evidence showed two recurring families:
  - entity naming drift at Director audit:
    - `WTI 원유 6월물` vs canonical `WTI 원유 선물 6월물`
    - `금 가격 차트` / `금 시세 차트` vs canonical `금(XAU/USD) 10년 치 가격 차트`
    - `SW인베스트먼트 오피스` vs canonical `SW 인베스트먼트 임시 오피스텔`
    - `PDA` vs canonical `개인용 PDA 단말기`
  - numeric continuity drift during candidate selection:
    - start total-assets mismatch against carryover packet
    - `investment_calc.final_cash` / `final_total_assets` combinations that do not respect carryover arithmetic

Landed bounded slice:

- `modules/core/stage2_entity_contract.py`
  - added Stage2 entity alias normalization helpers for Director-bound arc payloads
  - explicit alias coverage now includes whitespace/no-whitespace location variants such as `SW인베스트먼트 오피스`
- `modules/core/stage2_finalizer.py`
  - `_prepare_stage2_finalize_audit_state` now canonicalizes `tactical_doc`, `joint_docs`, `state_constraints`, and `episode_details` against the Director entity registry before audit
  - this is a pre-audit shell hardening slice, not a new truth source
- `modules/domain/agents/arc_ensemble.py`
  - candidate scoring now demotes investment arithmetic boundary mismatches before Director selection
  - arithmetic scoring was extracted into `_score_candidate_contract_health` so `_evaluate_candidate` remains below the `180+ LOC` guardrail

Bounded verification completed:

- `pytest tests/test_arc_ensemble_lane_a.py -k "investment_arithmetic_boundary_mismatch or non_wuxia_state_noise" -q`
- `pytest tests/test_stage2_finalizer.py -k "prepare_audit_state_normalizes_entity_aliases_before_director" -q`
- `python -m py_compile modules/domain/agents/arc_ensemble.py modules/core/stage2_finalizer.py modules/core/stage2_entity_contract.py`

Complexity recount:

- `_score_candidate_contract_health`: `63 LOC` (`semantic core`)
- `_collect_investment_arithmetic_issues`: `30 LOC`
- `_evaluate_candidate`: `165 LOC` after extraction (`bounded shell`; `175 -> 203 -> 165` within this tranche, so no net `180+` crossing remains)
- `_prepare_stage2_finalize_audit_state`: `1116 LOC`, still an existing large `bounded shell`; this tranche added pre-audit canonicalization only and did not create a new high-risk band entry

Bounded implementation verdict:

- Stage2 still is not closure-ready
- `retrieval/work_focus` is no longer the front blocker in this lane
- the immediate blocker set is now narrower:
  - Arc 3 entity alias drift that must be verified on the next fresh run
  - Arc 3 numeric continuity phrasing/arithmetic drift
  - future-wave dead-field/readiness cleanup
