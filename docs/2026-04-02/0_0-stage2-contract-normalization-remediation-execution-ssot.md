# 0_0 Stage2 Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (2026-04-06 re-audited and promoted from parked after live validation/finalizer revalidation confirmed a still-live Stage2 persistence-authority seam; the bounded preflight/validation/finalizer persistence tranche, the bounded Flow Guard severity tranche, and the same-day bounded non-wuxia persistence state-cleanup tranche have now landed as child slices inside this SSOT, a later 2026-04-08 bounded observability follow-up then surfaced authoritative carryover location/inventory/finance summaries through Stage2 runtime, DB, and operator-visible sinks, and the newest same-day follow-up landed a Stage2 decision/proof-digest hardening slice; the later `projects/000_260408` proof-wave merge audit then showed those proof sinks were only partially closed, and the new `projects/000_260408_B` proof-wave merge audit now validates the bounded proof-sink tranche materially: DB `ui_events` carryover parity, `pass_rate_monitor` parity, `proof_digest.stages.stage2`, and `proof_digest.operational_metadata.stage2_live_session` are live, while the residual `warn` narrows to `director_selections.verdict_reason` drift plus 6 intermediate decision rows without `attempt_key`; broader Stage2 normalization stays queued behind that residual sink hygiene)
Canonical Path: `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2 survey docs and lane drafts untracked`
- Resume Commit: `6dd7712ea9a58802221634081ba199bc872d2349`
- Resume Drift Summary: `2026-04-05 bounded Stage2 realization slices narrowed the lane, the 2026-04-06 global P0-P1 Opus survey confirmed two still-live Stage2 persistence seams, the 2026-04-06 Golden bounded survey added one residual artifact-truth P1 plus abrupt-shutdown observability debt, the workspace then landed truth-preserving packet merges across `stage2_preflight_runtime.py`, `stage2_validation_pipeline.py`, `stage2_finalizer.py`, and `stage2_contracts.py`, the current workspace additionally landed a bounded Flow Guard severity split in `stage2_validation_pipeline.py`, the same-day bounded finalizer persistence cleanup then strips non-wuxia `internal_energy` / `realm` / `qi_nature` / `martial_arts` state noise both before and after `validate_arc()` so accepted artifacts no longer silently rehydrate those fields at save time, the later 2026-04-08 follow-up in `stage2_finalizer.py` then persisted compact carryover-authority summaries for start/end location, inventory, and finance facts so later proof waves can see the authoritative Stage2 packet truth without reopening the lane into a broader redesign, the newest same-day follow-up across `stage2_finalizer.py` plus `audit_service.py` then landed a Stage2 decision/proof-digest hardening slice, the later `docs/2026-04-08/stage23-proof-wave-parallel-merge-audit.md` confirmed that slice only partially closed runtime proof, and the newer `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md` now shows the proof-blocking sinks materially repaired while residual `warn` scope narrows to companion verdict parity plus intermediate decision-row linkage`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
- `docs/2026-04-06/rol-global-terminal2-stage2-pipeline-p0p1.md`
- `docs/2026-04-06/01_golden_stage2_p0_p3_bounded_survey.md`
- `docs/2026-04-08/stage23-proof-wave-parallel-merge-audit.md`
- `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage2-production-consumption-global-evidence.json`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-evidence.json`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json`
- `projects/000_260408/project_data.db`
- `projects/000_260408/logs/runtime_audit_summary.json`
- `projects/000_260408/logs/pass_rate_monitor.json`
- `projects/000_260408/logs/session/decisions.jsonl`
- `projects/000_260408/logs/session/ui_events.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Activate a bounded, implementable `Stage2 contract normalization` tranche focused on truth-preserving persistence shells for `joint_docs.world_joint` and `status_shadow`.

This execution SSOT still exists because the latest survey plus current code revalidation already proved:

- `Stage2` has a real problem
- that problem is primarily `authority packaging / contract drift`, not missing narrative content
- the sharpest still-live Stage2-local P1 in the active queue is now the persistence-time overwrite of LLM-authored packet truth
- therefore the immediate work is a bounded Stage2 sink fix, not a broad Stage2 architecture wave

## 2. Baseline Facts

- `Stage2` is `content-sufficient but schema-fragile`.
- The strongest mission truth lives in `tactical_doc` prose rather than a strong structured packet.
- `constraint_summary` undergoes strength inversion downstream.
- `beat_sequence` and `hybrid_composition` are effectively dropped at the `Stage2 -> Stage3` boundary.
- `semantic_carryover` behaves like a dead or low-signal field in current practice.
- The first clearly visible narrative drift still appears in `Stage3`, not inside Stage2 artifacts themselves.
- Fresh `00_0405` evidence shows a second Stage2-local symptom: selected Stage2 packet truth can diverge from final arc txt truth on bounded location/item carryover even when the business-state spine stays coherent.
- Fresh `00_0405` evidence also shows that key Stage2 correction and retrieval facts are fragmented across `runtime_audit.jsonl` and `quality_metrics.jsonl` instead of being operator-visible in the console.
- 2026-04-06 Opus revalidation proves the remaining Stage2-local high-severity seam is no longer just generic packet drift: `joint_docs.world_joint` and `status_shadow` can still be overwritten by `enriched_block` payloads at validation/finalization time before canonical persistence.
- Fresh `01_golden` evidence confirms a residual Stage2-local contract mismatch: operator-visible cleanup can close falsely, with accepted artifacts still retaining `internal_energy` after console-level removal claims.
- The same `01_golden` evidence also confirms that stale summary sinks and implicit `Arc 5` closure were observed under an abrupt IDE shutdown, so they remain bounded observability and abnormal-shutdown-tolerance debt rather than a queue-promotion trigger over the current persistence tranche.

## 3. Scope

Included:

- current active bounded owner set:
  - `modules/core/stage2_preflight_runtime.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_contracts.py`
- bounded truth-preserving sink merge for `joint_docs.world_joint` and `status_shadow`
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
- broad Stage2 architecture rewrite in the same turn
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
7. persistence-time overwrite of LLM-generated `joint_docs.world_joint` and `status_shadow` by block-level fallback structures

## 5. Pass 2. Semantic Classification

### Class A. Current active bounded tranche

- truth-preserving merge at Stage2 preflight/validation/finalization sinks for `joint_docs.world_joint` and `status_shadow`
- explicit Stage2-owned fallback/backfill policy for `enriched_block` vs refined-arc packet truth

### Class B. Residual realization after the active tranche

- structured mission authority extraction from `tactical_doc`
- Stage2-owned packet alias normalization at emission time
- keep-or-drop decisions for dead or low-signal Stage2 fields

### Class C. Residual but related

- downstream consumer-side vocabulary alignment
- `constraint_summary` strength normalization across stages
- Stage3 compiler/substep reduction

### Class D. Explicitly deferred outside this lane

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

1. Stage2 persistence-authority merge for `joint_docs.world_joint` / `status_shadow`
2. Stage2 mission packet normalization
3. Stage2-owned packet alias normalization
4. dead-field keep-or-drop cleanup
5. bounded observability surfacing
6. bounded regression coverage
7. later runtime proof only after closure candidacy

## 9. Acceptance Criteria

- Stage2 no longer relies on prose `tactical_doc` alone for mission authority
- Stage2 exports a stronger canonical mission packet or equivalent structured authority owner
- Stage2-owned field aliases no longer obscure which packet is canonical at emission time
- `beat_sequence`, `hybrid_composition`, and `semantic_carryover` each have an explicit keep-or-drop policy
- selected Stage2 packet truth and final arc txt truth no longer diverge on bounded carryover location/item/state fields without explicit policy
- canonical persistence no longer overwrites live LLM-authored `joint_docs.world_joint` or `status_shadow` with stale or empty `enriched_block` values
- high-signal Stage2 auto-correct and retrieval-emptiness facts are no longer completely hidden from operator-visible console flow
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage2 packet rendering regressions
- targeted Stage2 packet alias and field-survival regressions
- targeted `stage2_finalizer` / `stage2_validation_pipeline` regressions for `world_joint` and `status_shadow` persistence preservation
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- keep this active tranche below the current `Stage4 consumer` / `Stage4 repair` front pair unless explicit reprioritization changes the queue again
- do not widen this lane into downstream consumer rename cleanup in the same turn
- do not widen this lane into `Stage3` contract tightening in the same turn
- do not widen the persistence tranche into a broad Stage2 architecture sweep in the same turn
- do not run a canary from this lane until the bounded persistence tranche and targeted validation settle
- do not rewrite artifact history in `projects/`

## 12. Temp Queue Notes

- temp status: `partially_realized`
- cleanup condition:
  - keep the temp mirror as an active bounded queue item until explicit closure or formal deactivation
- roadmap dependency:
  - this item stays below active `Stage4` lanes but now sits above parked `Stage3` / `Stage0` future waves

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- promoted this from a parked future wave into an active bounded Stage2 lane
- narrowed the immediate tranche to Stage2 sink-side persistence authority for `joint_docs.world_joint` / `status_shadow`
- kept downstream consumer rename cleanup, Stage3 tightening, and Stage4 remediation out of the current patch scope

Pass 2, evidence and consistency:

- aligned the document with the global Stage2 production-consumption survey verdict and the 2026-04-06 Opus P1 revalidation
- confirmed the same overwrite shell is still live in the current workspace at `stage2_validation_pipeline.py` and `stage2_finalizer.py`

Pass 3, execution and readability:

- made the queue promotion explicit without claiming that the whole broader Stage2 backlog is now front of queue
- made the current owner set and bounded next action explicit
- kept the active tranche implementable instead of broadening it into an architectural rewrite

Confidence: `97%`

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

Queue semantics at the time of this appendix remained unchanged:

- status stayed `parked`
- roadmap priority stayed unchanged
- this did not yet promote the full Stage2 lane above active Stage4 work

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

## 26. 2026-04-06 Opus P0-P1 Revalidation: `world_joint` / `status_shadow` Persistence Seam

The 2026-04-06 global P0-P1 Opus survey did not change queue order, but it did sharpen the active Stage2 future-wave debt into two deterministic persistence-time seams that belong in this SSOT.

Queue semantics remain unchanged:

- status stays `parked`
- roadmap priority stays unchanged
- this does not promote the full Stage2 lane above active Stage4 work

Confirmed live P1 seams:

1. `joint_docs.world_joint` overwrite seam
   - LLM output generates `joint_docs.world_joint` as a required schema field
   - `stage2_validation_pipeline.py` and `stage2_finalizer.py` can overwrite that field with `enriched_block`-owned `joint_docs`
   - canonical arc persistence then saves the overwritten value
   - downstream Stage3/4 consumers can inherit stale or empty world-state carryover
2. `status_shadow` overwrite seam
   - LLM output generates `status_shadow.item_consumption`, `expected_injuries`, and `key_stat_change`
   - validation/finalization can replace `status_shadow` with block-level fallback content before persistence
   - inventory carryover then reads the overwritten `item_consumption`, so consumed items may survive into canonical carryover when later sync shells do not fully recover the loss

Execution consequence:

- the remaining Stage2 parked lane is now explicitly about `truth-preserving persistence shells`, not just broad packet vocabulary cleanup
- the narrowest owner set for this P1 is:
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_validation_pipeline.py`
- static evidence is sufficient to keep these seams in the SSOT; a fresh run is useful for impact measurement, but not required to prove the overwrite path exists

Bounded future realization direction:

- preserve LLM-authored `joint_docs.world_joint` and `status_shadow` through validation/finalization unless an explicit Stage2 authority-sync shell replaces them field-by-field
- if replacement is required, add an explicit resync contract parallel to the existing location/inventory syncs rather than silent whole-object overwrite

Revalidation note:

- this update converts the Opus survey finding into execution SSOT language without changing queue priority
- confidence after the 2026-04-06 re-audit remains `97%`

## 27. 2026-04-06 Reprioritization: Active Bounded Persistence Tranche

The operator explicitly promoted this SSOT from parked future wave to active bounded realization after the current workspace revalidation confirmed that the Opus seam is still live in both `modules/core/stage2_validation_pipeline.py` and `modules/core/stage2_finalizer.py`.

Queue semantics now change:

- status is now `partially_realized`
- roadmap priority is promoted above parked `Stage3` and `Stage0` future waves
- this lane still remains below the active `Stage4 consumer` and `Stage4 repair` pair

Active bounded owner set:

- `modules/core/stage2_preflight_runtime.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_contracts.py`

Immediate execution target:

- preserve LLM-authored `joint_docs.world_joint` and `status_shadow` keys through validation/finalization by merging `enriched_block` only as field fallback
- keep explicit location/inventory authority syncs as the only Stage2 shells allowed to rewrite those packets field-by-field
- land targeted regressions before the next fresh run

Reprioritization note:

- this promotion addresses a live P1 truth-loss seam, not the full broader Stage2 normalization backlog
- broader mission-authority, alias, dead-field, and readiness work remains in this SSOT but outside the current bounded tranche

## 28. 2026-04-06 Golden Survey Promotion: Residual Artifact-Truth P1 and Abrupt-Shutdown Debt

The `01_golden` bounded survey is now promoted into this execution SSOT as supporting Stage2 evidence.

It does not create a new execution document and does not widen the current active bounded tranche, but it does refine the residual Stage2 backlog that remains behind the active `joint_docs.world_joint` / `status_shadow` persistence wave.

Queue semantics remain unchanged:

- status stays `partially_realized`
- the current active bounded tranche remains the Stage2 sink-side truth-preserving merge for `joint_docs.world_joint` and `status_shadow`
- broader Stage2 normalization and observability debt remains queued behind that tranche

Promoted residual findings:

1. residual Stage2-local `P1`: console-level false closure on family-field cleanup
   - accepted Golden `Arc 1`, `Arc 3`, and `Arc 4` artifacts still persisted `internal_energy` in `arc_start_state` and `arc_end_state` after `ui_events.jsonl` reported the field removed
   - this confirms that non-wuxia field hygiene is not only a candidate-selection issue; operator-visible repair claims can still disagree with saved artifact bytes
   - execution consequence: keep the broader Stage2 contract-normalization backlog open after the active persistence tranche, with explicit verification that future operator-visible repair claims match persisted artifact truth
2. reclassified operational debt under abrupt shutdown
   - the operator later confirmed the IDE was abruptly closed during `Arc 5`
   - `pass_rate_monitor.json` and `runtime_audit_summary.json` staying stale, plus the lack of an explicit `Arc 5` interrupted marker, now read as abnormal-shutdown tolerance and observability gaps rather than proof of a normal-run persistence defect
   - execution consequence: keep these items as future bounded observability and resume-hardening debt; they do not outrank the active persistence tranche
3. candidate-only residual
   - `power_changes` drift across accepted artifacts remains real but unpromoted until a consumer trace closes concrete downstream dependence

Golden survey guardrail:

- this appendix does not justify regenerating accepted Golden arcs
- this appendix does not reclassify Stage2 as a narrative-content collapse
- this appendix does not promote the broader Stage2 backlog above the active `Stage4 consumer` / `Stage4 repair` pair

## 29. 2026-04-06 Bounded Realization Update: Persistence-Authority Tranche Landed

The bounded `joint_docs.world_joint` / `status_shadow` persistence-authority tranche is now landed for the current Stage2 owner family.

Landed owner set:

- `modules/core/stage2_contracts.py`
- `modules/core/stage2_preflight_runtime.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`

Landed behavior:

- `merge_stage2_authoritative_packet()` now preserves non-empty refined-arc packet truth while backfilling only missing or empty fallback fields
- Stage2 FourPhase PASS post-processing no longer performs whole-object overwrite of `joint_docs` / `status_shadow` from `enriched_block`
- validation continuity PASS handling no longer drops existing authoritative `world_joint` when `corrected_joint_docs` is partial
- finalizer persistence preparation continues to preserve authoritative packet truth while still allowing deterministic inventory/location authority syncs to run field-by-field

Verification evidence:

- `pytest tests/test_stage2_contracts.py tests/test_stage2_preflight.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py tests/test_stage2_finalizer_lane_e.py -q`
  - result: `171 passed`
- `python -m py_compile modules/core/stage2_contracts.py modules/core/stage2_preflight_runtime.py modules/core/stage2_validation_pipeline.py tests/test_stage2_contracts.py tests/test_stage2_preflight.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py`
- `ruff check modules/core/stage2_contracts.py modules/core/stage2_preflight_runtime.py modules/core/stage2_validation_pipeline.py tests/test_stage2_contracts.py tests/test_stage2_preflight.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py`
- `python scripts/check_utf8_hygiene.py modules/core/stage2_contracts.py modules/core/stage2_preflight_runtime.py modules/core/stage2_validation_pipeline.py tests/test_stage2_contracts.py tests/test_stage2_preflight.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py`

Closure reading:

- the immediate bounded Stage2 truth-loss seam that motivated the active tranche is now closure-candidate for the current owner set
- this SSOT stays `partially_realized`, not `closed`, because it still carries deferred Stage2 normalization debt beyond the landed persistence child tranche
- the temp execution mirror remains queued because the canonical SSOT still owns residual follow-up scope

Residual risks and deferred scope:

- residual artifact-truth false closure on non-wuxia family-field cleanup, as captured in `01_golden`
- abnormal-shutdown observability and explicit interruption-marking debt, also captured in `01_golden`
- broader mission-authority extraction, alias normalization, and dead-field keep-or-drop work
- no fresh live run has yet been used to convert this bounded landing into a runtime closure audit

## 30. 2026-04-06 Opus Follow-Up: No-New-Lane Confirmation and Flow-Guard Severity Inflation

Follow-up evidence docs:

- `docs/2026-04-06/0-temp-stage2-other-issues-bounded-survey.md`
- `docs/2026-04-06/0-temp-stage2-flow-guard-beat-severity-mismatch-bounded-survey.md`
- `docs/2026-04-06/0-temp-stage2-opus-terminal1-flow-guard-severity-memo.md`
- `docs/2026-04-06/0-temp-stage2-opus-followup-terminal2-no-new-lane-confirmation.md`

Queue semantics remain unchanged:

- no new execution SSOT is promoted from the `0_temp.txt` follow-up wave
- no roadmap reorder is justified by the Opus follow-up
- this Stage2 SSOT remains the correct home for the residual `beat_sequence` / `Flow Guard` policy seam

Confirmed follow-up reading:

1. `0_temp.txt` does contain other real issue families beyond the already-promoted non-wuxia state-lock lane, but those families are already documented and owned:
   - numeric arithmetic drift remains covered by the existing Arc 3/4 Stage2 survey and the active Stage4 consumer lane
   - entity reject/retry remains covered by the existing Arc 5 Stage2 survey and still reads as retry-only residue
   - repeated `Patch pressure exceeded -> advisory only` remains supporting evidence for observability/patch-path debt, not a separate front queue item
2. the only plausible under-documented residual confirmed by the Opus follow-up is the `Flow Guard` / `beat_sequence` severity mismatch
3. that mismatch is best classified as `severity inflation`, not false-positive fabrication:
   - Python correctly detects thin or empty `beat_sequence` metadata
   - but the current advisory sink still escalates those `Flow Guard REJECT` paths as fixed `CRITICAL` severity even when Director semantic review judges the prose structure substantively sufficient

Bounded owner set:

- primary owner: `modules/core/stage2_validation_pipeline.py`
- secondary owner: Stage2 contract policy for `beat_sequence`

The Opus memo also sharpened a broader contract observation inside the same owner family:

- the Stage2 validation advisory sink is effectively flat-severity for multiple sources, not just `flow_guard`
- the current sink path treats `consensus`, `flow_guard`, `duplicate_guard`, `draft_validator`, `arc_corrector_*`, and `continuity_inspector` advisories too uniformly at the severity layer

Execution consequence:

- keep this seam inside the broader Stage2 residual backlog rather than promoting a separate lane
- treat it as a future bounded Stage2 policy/observability subtask after the already-landed persistence-authority tranche
- the likely future patch shape, if later activated, is:
  - tiered severity by `diagnostics.type` rather than flat `CRITICAL`
  - explicit keep-or-drop policy for `beat_sequence`
  - bounded downgrade path when `tactical_doc` / `episode_details` already provide semantically sufficient structure

Guardrail:

- this appendix does not demote the active front pair (`Stage4 consumer`, `Stage4 repair`)
- this appendix does not demote the active `Stage234 non-wuxia state-lock overreach` lane
- this appendix does not convert the Stage2 residual backlog into an immediate implementation order

3-pass update note:

- Pass 1: bounded this update to Opus follow-up conclusions only, with no queue mutation
- Pass 2: confirmed the new memos support, rather than overturn, the current Stage2 SSOT reading
- Pass 3: recorded only the execution consequence that matters operationally: keep the seam in this SSOT and do not create a new lane

Confidence for this appendix: `96%`

## 31. 2026-04-06 Bounded Realization: Flow-Guard Severity Split Landed

Implementation audit:

- `docs/2026-04-06/0_0-stage2-flow-guard-severity-tranche-3pass-audit.md`
- `docs/2026-04-06/0_0-stage2-flow-guard-severity-landed-3pass-audit.md`

Landed code/tests:

- `modules/core/stage2_validation_pipeline.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_stage2_preflight_helpers.py`

What changed:

1. the `flow_guard` advisory sink no longer forces every reject into fixed `CRITICAL`
2. `diagnostics.type in {beat_count, empty_beats, beat_condensed}` now maps to `MAJOR`
3. stagnation-class or unknown rejects remain `CRITICAL`
4. `entity` handling was intentionally left untouched in this tranche

Execution consequence:

- the Stage2 SSOT no longer treats the `Flow Guard` severity split as purely future/speculative
- the broader advisory-tier flattening problem still remains residual debt inside this same SSOT
- no new lane, roadmap reorder, or queue promotion is justified by this landed slice

Targeted verification:

- `pytest tests/test_stage2_validation_pipeline.py -k "flow_guard" -q`
- `pytest tests/test_stage2_preflight_helpers.py -k "flow_guard_reject_becomes_advisory" -q`
- `python -m py_compile modules/core/stage2_validation_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_stage2_preflight_helpers.py`
- `ruff check modules/core/stage2_validation_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_stage2_preflight_helpers.py`

Residual scope:

- broader severity normalization across non-`flow_guard` advisory sources
- possible future contract work on explicit `beat_sequence` keep-or-drop policy

Confidence for this landed slice: `97%`

## 36. 2026-04-08 Fresh Proof-Wave Validation Upgrade (`000_260408_B`)

Evidence basis:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md`
- `projects/000_260408_B/project_data.db`
- `projects/000_260408_B/logs/runtime_audit_summary.json`
- `projects/000_260408_B/logs/pass_rate_monitor.json`
- `projects/000_260408_B/logs/session/decisions.jsonl`
- `projects/000_260408_B/logs/session/ui_events.jsonl`

Fresh proof-wave verdict:

1. the previously front-blocking Stage2 proof-sink tranche is now materially validated on the fresh rerun:
   - DB `ui_events` now has `3` `carryover_authority` rows, matching session JSONL
   - `logs/pass_rate_monitor.json` now has `3` committed Stage2 rows with clean attempt/hash/artifact parity
   - `logs/session/decisions.jsonl` now has `9` Stage2 rows including `3` `arc_final` rows with `session_id`, `attempt_key`, `candidate_key`, `artifact_path`, `selection_reason`, `verdict_reason`, `fix_scope_reasoning`, and compact `carryover_authority`
   - `runtime_audit_summary.json` now has `proof_digest.available = true`, `proof_digest.stages.stage2`, and `proof_digest.operational_metadata.stage2_live_session.status = "ok"`
2. the residual Stage2 `warn` is now narrow rather than tranche-blocking:
   - `director_selections.verdict_reason` is blank on `3/3` while `stage_attempts` and `arc_final` are populated
   - `session_decision_rows_without_attempt_key = 6` comes only from the intermediate `3 x arc` plus `3 x arc_design` rows
3. contradiction cleanup from the five-terminal survey is now canonical:
   - `rationale_metadata_missing = 3` is driven by `director_selections.verdict_reason`, not by blank `arc_final.meta.reason`
   - do not promote the Terminal 5 mojibake claim; live UTF-8 DB readback was clean
   - do not promote the Terminal 3 Stage2-source-blank reading; `stage_attempts.selection_reason`, `verdict_reason`, and `fix_scope_reasoning` are populated on all `3` rows
4. lower-tier residuals remain inside the same lane:
   - preview lists stay intentionally capped at `3` items
   - `director_selections.selected_label` remains blank
   - arc 3 still carries a latent asset-math semantic contradiction inside `verdict_reason`

Execution consequence:

- treat the old Stage2 proof-sink repair tranche as runtime-validated at the proof-blocking level
- keep the remaining Stage2 work inside this same SSOT as bounded sink hygiene rather than as the next front proof blocker
- do not open a new queue lane and do not reorder the queue from this validation alone
- shift the next useful proof artifact to a rerun that actually reaches Stage3; only reopen code here first if the operator explicitly wants to clear the residual `warn` before that rerun

Confidence for this validation upgrade: `97%`

## 34. 2026-04-08 Bounded Realization: Final Decision / Proof-Digest Surfacing Hardened

Implementation evidence:

- `modules/core/stage2_finalizer.py`
- `modules/core/services/audit_service.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_audit_service.py`

What changed:

1. Stage2 final persistence now emits an additional authoritative `session_logger.log_decision` row with `attempt_key`, `candidate_key`, `artifact_path`, `selection_reason`, `verdict_reason`, `fix_scope_reasoning`, and compact `carryover_authority`
2. `audit_service.py` now contains the Stage2-specific proof-digest path that is intended to surface Stage2 attempt coverage, decision-row coverage, artifact-path coverage, and the latest carryover-authority event snapshot
3. the code-level goal of this slice is to keep Stage2 proof triage from depending only on DB readback when fresh runs need quick operator-visible attribution

Execution consequence:

- the landed code narrowed the Stage2 evidence problem to a bounded proof-sink question rather than a broad contract redesign question
- later `projects/000_260408` runtime evidence confirmed this slice is only partially realized at the sink layer: structured carryover truth survives across DB/director/jsonl, but summary/session parity still remains incomplete

Targeted verification:

- `pytest tests/test_stage2_finalizer.py -k "authoritative_session_decision or pass_metrics_fall_back_to_director_compare_meta_for_selection_reason" -q`
- `pytest tests/test_audit_service.py -k "operational_metadata" -q`
- `python -m py_compile modules/core/stage2_finalizer.py modules/core/services/audit_service.py tests/test_stage2_finalizer.py tests/test_audit_service.py`
- `ruff check modules/core/stage2_finalizer.py modules/core/services/audit_service.py tests/test_stage2_finalizer.py tests/test_audit_service.py`

Residual scope after this landed slice:

- broader Stage2 mission-authority / alias / dead-field normalization still remains inside this SSOT
- abnormal-shutdown observability debt from `01_golden` still remains separate
- fresh live-run proof is still required before closure
- Stage2 proof-sink parity still remains open: DB `ui_events` misses `carryover_authority`, `decisions.jsonl` still lacks attempt-level join keys and reasoning surfaces, `pass_rate_monitor` remains empty, and `proof_digest.operational_metadata.stage2_live_session` is still absent in the latest fresh run

Confidence for this landed slice: `97%`

## 35. 2026-04-08 Fresh Proof-Wave Merge Revalidation

Evidence basis:

- `docs/2026-04-08/stage23-proof-wave-parallel-merge-audit.md`
- `projects/000_260408/project_data.db`
- `projects/000_260408/logs/runtime_audit_summary.json`
- `projects/000_260408/logs/pass_rate_monitor.json`
- `projects/000_260408/logs/session/decisions.jsonl`
- `projects/000_260408/logs/session/ui_events.jsonl`
- `projects/000_260408/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/000_260408/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/000_260408/logs/artifacts/stage2/arc_003/attempt_01/final_arc__conservative.json`

Fresh proof-wave verdict:

1. the Stage2 carryover-authority slice is now materially real at the structured runtime layer:
   - `stage_attempts.advisory_flags.carryover_authority`
   - `director_selections.advisory_warnings.carryover_authority`
   - `logs/session/ui_events.jsonl` `event_kind = carryover_authority`
   all agree for `ep1 -> ep2 -> ep3`
2. the same proof wave also confirms the Stage2 proof-sink repair is not closed:
   - DB `ui_events` has `0` `carryover_authority` rows while `ui_events.jsonl` has `3`
   - `logs/session/decisions.jsonl` still contains only `arc` / `arc_design` summary rows and still omits `attempt_key`, `candidate_key`, `artifact_path`, `fix_scope_reasoning`, and `advisory_flags.carryover_authority`
   - `arc_design.meta.fix_scope` stays blank on all `3` rows despite `stage_attempts.fix_scope = "inplace"`
   - `logs/pass_rate_monitor.json` remains `0` records despite `3` committed Stage2 PASS rows
   - `runtime_audit_summary.json` still has `proof_digest.available = false`, `proof_digest.stages = {}`, and no `proof_digest.operational_metadata.stage2_live_session`
3. some missing reasoning fields are not sink-only loss:
   - `stage_attempts.selection_reason` is blank on `3/3`
   - `stage_attempts.verdict_reason` is blank on `3/3`
   - `director_selections.verdict_reason` is blank on `3/3`
   - `director_selections.selection_reason` survives only on `ep1`
4. lower-tier residuals remain inside the same lane:
   - `end_inventory_preview` stays stale on `ep2` / `ep3`
   - `arc_003` keeps a structured-vs-prose inventory mismatch (`end_inventory_count = 7` vs artifact prose `소지품: 변경 없음`)

Execution consequence:

- keep this inside the existing Stage2 SSOT; do not open a new queue lane
- the next bounded Stage2 tranche is now explicit:
  - session decision sink parity
  - `pass_rate_monitor` parity
  - `proof_digest.operational_metadata.stage2_live_session`
  - DB `ui_events` parity for `carryover_authority`
- do not widen this into a broad Stage2 contract rewrite from this audit alone
- keep Stage2 ahead of Stage3 for the next proof-oriented follow-up because Stage2 now has fresh, concrete sink drift while Stage3 still lacks an exercised sample

Confidence for this revalidation: `97%`

## 32. 2026-04-07 Bounded Realization: Non-Wuxia Persistence State Cleanup Landed

Implementation evidence:

- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage2_finalizer_lane_e.py`

What changed:

1. Stage2 finalizer now strips non-wuxia state-noise fields (`internal_energy`, `realm`, `qi_nature`, `martial_arts`) before persistence-shell repair/finalization continues
2. the same cleanup now runs again after `validate_arc()` so `ArcState` default hydration cannot silently reintroduce `internal_energy` into accepted non-wuxia `arc_start_state` / `arc_end_state`
3. operator-visible `[Non-Wuxia State Cleanup]` logging plus audit events now describe the exact persisted cleanup phase and removed field families
4. wuxia paths intentionally remain untouched

Execution consequence:

- the Golden residual `artifact-truth false closure` seam is now narrower than the original survey reading
- accepted non-wuxia artifacts no longer depend on candidate-side cleanup alone to keep wuxia-only state fields out of persisted `state_constraints`
- this SSOT still remains `partially_realized` because broader mission-authority, alias/dead-field policy, observability, and fresh live-run closure work are still deferred

Targeted verification:

- `pytest tests/test_stage2_finalizer.py tests/test_stage2_finalizer_lane_e.py -q`
- `python -m py_compile modules/core/stage2_finalizer.py tests/test_stage2_finalizer.py tests/test_stage2_finalizer_lane_e.py`
- `ruff check modules/core/stage2_finalizer.py tests/test_stage2_finalizer.py tests/test_stage2_finalizer_lane_e.py`

Residual scope after this landed slice:

- explicit fresh live-run impact check for the broader Stage2 residual SSOT before any wider reactivation
- remaining mission-authority / alias / dead-field normalization still queued inside the same SSOT
- abnormal-shutdown observability debt from `01_golden`

Confidence for this landed slice: `97%`

## 33. 2026-04-08 Bounded Realization: Carryover-Authority Observability Surfaced

Implementation evidence:

- `modules/core/stage2_finalizer.py`
- `tests/test_stage2_finalizer.py`

What changed:

1. Stage2 finalizer now builds a compact `carryover_authority` summary from the authoritative Stage2 packet surfaces
2. the summary pins start/end location, start/end inventory counts and previews, plus finance hints such as `total_assets` / `capital` / `investment_calc`
3. the same summary now persists into `stage_attempts.advisory_flags` and `director_selections.advisory_warnings`
4. operator-visible logs now echo a bounded `[Stage2 Carryover Authority]` line so later upstream proof waves can see which Stage2 facts were actually packaged

Execution consequence:

- later fresh runs can distinguish Stage2 packet truth from downstream Blueprint/Writer drift more quickly
- this follow-up is observability-only and does not reopen broader Stage2 normalization or queue rank

Targeted verification:

- `pytest tests/test_stage2_finalizer.py -k "carryover_authority or pass_metrics_persist_carryover_authority_summary" -q`
- `python -m py_compile modules/core/stage2_finalizer.py tests/test_stage2_finalizer.py`
- `ruff check modules/core/stage2_finalizer.py tests/test_stage2_finalizer.py`

Residual scope after this landed slice:

- broader Stage2 mission-authority / alias / dead-field normalization still remains inside this SSOT
- abnormal-shutdown observability debt from `01_golden` still remains separate
- fresh live-run proof is still required before closure

Confidence for this landed slice: `97%`
