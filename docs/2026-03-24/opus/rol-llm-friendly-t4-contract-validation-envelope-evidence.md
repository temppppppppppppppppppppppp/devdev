Date: 2026-03-24
Document Type: evidence manifest (T4 lane)

## Path Inventory

### Primary Scope Files
| File | LOC | Surveyed Lines |
|---|---|---|
| `modules/validation/validation_orchestrator.py` | 1,674 | L1-1680 (full) |
| `modules/domain/agents/four_phase_arc_runtime.py` | 1,704 | L1-800 |
| `modules/domain/agents/three_phase_blueprint_runtime.py` | 1,600 | L1-500 |
| `modules/core/pre_director_checklist.py` | 717 | L1-500 |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 692 | L1-500 |
| `modules/domain/agents/base_agent.py` | 2,288 | L1-400, L1750-1950 |

### Validator Family (contract surface only)
| File | Role |
|---|---|
| `modules/validation/pre_llm_validator.py` | TIER 0.25 Python pre-check |
| `modules/validation/continuity_validator.py` | TIER 0.5 episode continuity |
| `modules/validation/blocking_validator.py` | TIER 1 hard-block checks |
| `modules/validation/consistency_validator.py` | TIER 1.5 consistency checks |
| `modules/validation/scoring_validator.py` | TIER 2 LLM scoring |
| `modules/validation/advisory_validator.py` | TIER 3 advisory generation |
| `modules/validation/retrospective_validator.py` | Optional long-term consistency |
| `modules/validation/catharsis_timer.py` | Catharsis timing check |
| `modules/validation/action_scene_evaluator.py` | Action scene quality |
| `modules/validation/batch_validator.py` | Batch validation |
| `modules/validation/blocking_validator_consistency_checks.py` | Blocking sub-checks |
| `modules/validation/blocking_validator_entity_checks.py` | Blocking entity checks |
| `modules/validation/blocking_validator_scene_checks.py` | Blocking scene checks |
| `modules/validation/threshold_helper.py` | Threshold SSOT helper |
| `modules/validation/dialogue_utils.py` | Dialogue utilities |

## Key Evidence Anchors

### Tier Result Schemas (validation_orchestrator.py)
- PRE_LLM result shape: L404-434 (`passed`, `critical_issues`, `warnings`, `score_deduction`)
- CONTINUITY result shape: L436-467 (`passed`, `violations`, `warnings`, `warning_count`)
- BLOCKING result shape: L503-541 (`passed`, `failures`, `warnings`, `degraded_checks`, `failure_count`)
- CONSISTENCY result shape: L542-562 (`unjustifiable_violations`, `justifiable_violations`, `score_penalty`, `feedback`)
- SCORING result shape: L673-707 (`total_score`, `passed`, `message`, `breakdown`)
- ADVISORY result shape: L695-698 (`suggestions`)

### Advisory Side-Channel Keys
- `_continuity_advisory`: produced at L456-461
- `_blocking_advisory`: produced at L535-537
- `_consistency_advisory`: produced at L547-552
- `_retrospective_advisory`: produced at L753-758

### Documented vs Actual Return Contract
- Documented (L336-354): `final_decision`, `blocking_result`, `scoring_result`, `advisory_result`, `total_score`, `feedback`, `self_consistency_used`
- Actual (L777-822 + prior phases): adds `_continuity_advisory`, `_blocking_advisory`, `_consistency_advisory`, `_retrospective_advisory`, `adaptive_threshold`, `detailed_feedback`, `refine_recommended`, `refine_reason`, `catharsis_result`, `action_result`, `pre_llm_result`, `continuity_result`, `consistency_result`, `retrospective_result`

### Envelope Dataclass Inventory (four_phase_arc_runtime.py)
| Dataclass | Lines | Key Fields |
|---|---|---|
| `_FourPhaseRuntimeBootstrap` | L20-33 | protagonist_config, ep_count_suggestion, pacing_signals, pipeline_result, pre_items, pre_grants, feedback, base_director_feedback |
| `_FourPhaseConstraintEnvelope` | L36-41 | full_constraint_block, preflight_result, cached_constraint_block, cached_preflight |
| `_FourPhaseGenerationEnvelope` | L44-55 | best_arc, all_candidates, prev_arc_context, feedback, prev_rejected_arc, prev_reject_feedback, prev_selected_strategy, spare_candidates, should_continue, patch_succeeded |
| `_FourPhaseGenerationCandidateEnvelope` | L58-65 | best_arc, all_candidates, spare_candidates, feedback, should_continue, patch_succeeded |
| `_FourPhasePatchEnvelope` | L68-71 | best_arc, patch_succeeded |
| `_FourPhaseCandidateEnvelope` | L74-80 | all_candidates, ns3b_director_advisory, investment_director_advisory, investment_advisory, candidate_quality_flags |
| `_FourPhaseDirectorCandidateEnvelope` | L83-86 | valid_for_director, valid_quality_flags |
| `_FourPhaseDirectorSelectionEnvelope` | L89-98 | best_arc, feedback, prev_rejected_arc, prev_reject_feedback, prev_selected_strategy, spare_candidates, should_continue, should_return |
| `_FourPhaseValidationEnvelope` | L101-110 | best_arc, feedback, prev_rejected_arc, prev_reject_feedback, prev_selected_strategy, spare_candidates, should_continue, should_return |
| `_FourPhaseRuntimeState` | L113-128 | protagonist_config, ep_count_suggestion, pacing_signals, pipeline_result, pre_items, pre_grants, feedback, base_director_feedback, prev_rejected_arc, prev_reject_feedback, prev_selected_strategy, spare_candidates, cached_constraint_block, cached_preflight |
| `_FourPhaseRetryCycleEnvelope` | L131-134 | best_arc, should_continue, should_return |

### Repeated Fields Across FourPhase Envelopes
| Field | Appears In |
|---|---|
| `best_arc` | GenerationEnvelope, GenerationCandidateEnvelope, PatchEnvelope, DirectorSelectionEnvelope, ValidationEnvelope, RetryCycleEnvelope (6) |
| `feedback` | RuntimeBootstrap, GenerationEnvelope, GenerationCandidateEnvelope, DirectorSelectionEnvelope, ValidationEnvelope, RuntimeState (6) |
| `prev_rejected_arc` | GenerationEnvelope, DirectorSelectionEnvelope, ValidationEnvelope, RuntimeState (4) |
| `prev_reject_feedback` | GenerationEnvelope, DirectorSelectionEnvelope, ValidationEnvelope, RuntimeState (4) |
| `prev_selected_strategy` | GenerationEnvelope, DirectorSelectionEnvelope, ValidationEnvelope, RuntimeState (4) |
| `spare_candidates` | GenerationEnvelope, GenerationCandidateEnvelope, DirectorSelectionEnvelope, ValidationEnvelope, RuntimeState (5) |
| `should_continue` | GenerationEnvelope, GenerationCandidateEnvelope, DirectorSelectionEnvelope, ValidationEnvelope, RetryCycleEnvelope (5) |
| `should_return` | DirectorSelectionEnvelope, ValidationEnvelope, RetryCycleEnvelope (3) |

### Parameter Count Verification
- `_run_generation_phase()` at L730-757: 27 named parameters confirmed
- `_run_generate_retry_cycle()` at L435-454: 14 named parameters + state object

### Pre-Director Checklist Contract
- `ChecklistResult` dataclass: `passed`, `items`, `fail_count`, `warning_count`, `summary`, `blocking_reasons`
- `CheckItem` dataclass: `category`, `name`, `passed`, `severity`, `message`
- `CheckCategory` enum: 13 categories
- `CheckSeverity` enum: PASS, WARNING, FAIL

### Blueprint Constraint Compiler Contract
- `compile()` return keys: `ep_num`, `arc_no`, `arc_position`, `must_focus`, `stop_line`, `continuity`, `inherited_state`, `arc_constraint_summary`, `state_changes_summary`, `semantic_carryover`, `immutable_fact_carryover`
