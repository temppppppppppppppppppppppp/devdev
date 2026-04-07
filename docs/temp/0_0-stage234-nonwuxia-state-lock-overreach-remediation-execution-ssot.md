# 0_0 Stage234 Nonwuxia State-Lock Overreach Remediation Execution SSOT

Date: 2026-04-06
Status: partially_realized (2026-04-06 Stage2 producer tranche landed with targeted tests and hygiene/compile checks passing, and the 2026-04-07 workspace reinspection confirmed the Stage4 intake/post-pass tranche is still pending with no hidden landing found)
Canonical Path: `docs/2026-04-06/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-nonwuxia-state-lock-overreach-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
- Baseline Dirty Summary: `dirty: 6 untracked 2026-04-06 survey docs (bounded survey + lane1-5)`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same HEAD; working tree includes landed Stage2 producer-side normalization in arc_ensemble.py, state_extractor.py, analyst.yaml, analyst_prompts.py, shared recovery helper, and targeted Stage2 regressions, while the 2026-04-07 workspace reinspection found the Stage4 target files/tests still encode genre-blind opening/carryover hardening`
Source Survey Docs:
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-bounded-survey.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane1-stage2-origin.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane3-stage4-opening-authority.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane4-stage4-chainlink-postpass.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane5-runtime-evidence-and-tests.md`
Evidence Artifacts:
- `0_temp.txt`
- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_preflight_continuity.py`
- `tests/test_stage4_post_processor.py`
Side-Effect Coverage: covered

## 1. Intent

Realize a bounded cross-stage fix that preserves `natural healing` while reducing false hard-fail pressure on non-wuxia fatigue / recovery / opening continuity.

This execution item exists because the merged survey proved:

- the operator symptom is real and already manifested as a live Director REJECT
- the issue is not `Stage2-only` and not `Stage4-only`
- `Stage2` is the producer of the false obligation
- `Stage4` is the strongest hardening and stickiness layer
- `Stage3` is mostly a passive carrier and should stay secondary in the first patch wave

The intent is not to weaken real injury continuity. The intent is to split:

- `hard injury / true mobility-loss / structurally blocking carryover`
- from
- `soft fatigue / ordinary stress / routine non-wuxia recovery`

## 2. Baseline Facts

- Severity is `P1`: a live investment-fiction run produced a Director REJECT around `신경계 피로 Moderate`, and the retry passed only after an explicit recovery framing was inserted.
- `natural healing` already exists in multiple code paths, but it does not currently govern the strongest producer and consumer authority surfaces.
- Stage2 hardening surfaces are:
  - `modules/domain/agents/arc_ensemble.py`
  - `modules/domain/agents/state_extractor.py`
  - `config/prompts/analyst.yaml`
  - `modules/domain/agents/analyst_prompts.py`
- Stage4 hardening surfaces are:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/stage4_immutable_fact_contract.py`
- Stage3 has a bounded follow-on seam in:
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/blueprint_ensemble.py`
- Existing tests intentionally codify the current overreach, especially:
  - `tests/test_arc_ensemble_lane_a.py`
  - `tests/test_stage4_context_builder.py`

## 3. Scope

Included:

- Stage2 non-wuxia recovery penalty normalization
- Stage2 `recovery_scene_required` and `V60.10` policy split for hard injury vs soft fatigue
- Stage4 opening-authority normalization for non-wuxia soft-state carryover
- Stage4 chain-link persistence normalization for mild `physical_state` and routine `pending_actions`
- bounded Stage3 carryover normalization only if Stage2/Stage4 changes still leave a genre-blind inherited-state seam
- targeted regression updates for producer, consumer, and persistence paths

Excluded:

- broad Stage2 mission-packet or alias normalization
- broad Stage4 numeric carryover / repair-contract work
- repo-wide prompt rewrite
- DB schema redesign
- global Stage-count or architecture compression
- artifact rewrites under `projects/`
- `docs/temp` edits other than the required mirror and roadmap refresh

## 4. Pass 1. Inventory Summary

Primary owner inventory:

1. Stage2 producer / prompt / deterministic scoring
   - `arc_ensemble.py`
   - `state_extractor.py`
   - `analyst.yaml`
   - `analyst_prompts.py`
2. Stage4 intake authority and chain-link persistence
   - `stage4_context_builder.py`
   - `stage4_orchestrator.py`
   - `stage4_post_processor.py`
   - `stage4_immutable_fact_contract.py`
3. Stage3 bounded carryover seam
   - `blueprint_constraint_compiler.py`
   - `blueprint_ensemble.py`
4. Codifying regression layer
   - `tests/test_arc_ensemble_lane_a.py`
   - `tests/test_stage4_context_builder.py`
   - `tests/test_stage4_preflight_continuity.py`
   - `tests/test_stage4_post_processor.py`

Highest-value bounded hotspots:

- Stage2 soft-fatigue misclassification into `recovery_scene_required`
- Stage2 deterministic opening penalty for vague non-wuxia recovery
- Stage4 `hard canon` opening framing for carryover fields
- Stage4 chain-link persistence with no soft/hard distinction

## 5. Pass 2. Semantic Classification

### Class A. First-wave must-fix owners

- Stage2 hard-vs-soft policy split
- Stage4 opening / chain-link hard-vs-soft policy split

### Class B. Secondary bounded follow-on

- Stage3 inherited-state carryover downgrade for non-critical, non-wuxia fatigue
- compatibility wording updates in blueprint formatting if Stage2/Stage4 still leave residual over-hardening

### Class C. Explicitly deferred

- broad Stage2 contract cleanup already tracked by `0_0-stage2-contract-normalization-remediation`
- broad Stage4 consumer/repair cleanup already tracked by the current Stage4 pair
- cross-stage vocabulary unification already tracked by `0_0-stage234-cross-stage-contract-normalization-remediation`

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage2 arc planning prompts and constraint packets may change
  - Stage4 opening-context text and chain-link carryover rendering may change
  - generated arc/blueprint/manuscript openings may naturally use fewer forced recovery beats in non-wuxia works

- DB / schema / transaction boundaries:
  - no schema redesign is planned
  - `chain_link_{ep}` payload meaning may change if soft/hard carryover semantics are introduced

- JSONL / log / audit sinks:
  - Director and Stage2 advisory/reject wording may soften for soft-fatigue cases
  - runtime audit text may shift where `recovery_scene_required` and carryover obligations are reported

- console / UI / operator output:
  - fewer genre-inappropriate recovery-fail messages should appear
  - operator-visible phrasing may become more explicit about `hard injury` vs `soft fatigue`

- rollback / recovery / retry:
  - retry loops should trigger less often on false non-wuxia fatigue hardening
  - true injury recovery enforcement must remain intact

- cache / global state:
  - not expected to be primary
  - bounded packet field semantics may need synchronized readers if new soft/hard flags are introduced

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This lane should be realized as a bounded dual-owner patch, not as a broad cross-stage rewrite.

Architecture rule:

- first split the policy in Stage2 where the false obligation is produced
- then split the carryover semantics in Stage4 where the obligation becomes sticky
- touch Stage3 only if the passive carryover layer still re-hardens the downgraded state after the first two owners are fixed

Preferred contract direction:

- `hard`: true injury, structural movement lock, plot-critical unresolved danger, real mobility limitation
- `soft`: mental fatigue, stress, overwork, mild headache, routine pending actions, ordinary elapsed recovery

The implementation does not have to use literal `hard`/`soft` field names, but it must create an equivalent distinction that both producer and consumer honor.

## 8. Execution Tranches

1. Stage2 producer normalization
   - narrow non-wuxia fatigue detection in `arc_ensemble.py`
   - stop treating ordinary elapsed-time markers as fatigue by default
   - split `recovery_scene_required` logic in `state_extractor.py`
   - soften `V60.10` / prompt wording for soft fatigue without weakening true injury paths

2. Stage4 intake normalization
   - soften `[Stage4 Opening Scene Authority]` for soft-state carryover
   - stop defaulting mild `physical_state` and routine `pending_actions` to hard-canon behavior
   - keep true injury and true plot-critical carryover strong

3. Stage4 post-pass persistence normalization
   - add soft/hard semantics or equivalent filtering to chain-link extraction/load/consumption
   - prevent mild fatigue from becoming sticky next-episode mandatory state by default

4. Optional Stage3 bounded follow-on
   - only if `blueprint_constraint_compiler.py` or `blueprint_ensemble.py` still re-hardens downgraded states after tranches 1-3

5. Regression and bounded runtime verification
   - update tests that intentionally lock the old overreach
   - add explicit non-wuxia soft-fatigue regressions
   - add at least one bounded runtime/operator-path check before closure

## 9. Acceptance Criteria

- non-wuxia soft fatigue no longer automatically implies hard `recovery_scene_required`
- Stage2 no longer rejects or heavily penalizes ordinary non-wuxia openings solely because recovery is implicit or time-based without stronger injury evidence
- Stage4 no longer injects mild fatigue or routine pending actions as hard canon by default
- chain-link persistence no longer makes mild soft-state carryover sticky across episodes by default
- true injury and true hard continuity cases still remain hard
- `natural healing` remains a valid behavior
- targeted tests encode the new split explicitly
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted sequential pytest shards:
  - `tests/test_arc_ensemble_lane_a.py`
  - `tests/test_stage4_context_builder.py`
  - `tests/test_stage4_preflight_continuity.py`
  - `tests/test_stage4_post_processor.py`
  - any new targeted Stage2/Stage4 regression file added by the patch
- `python -m py_compile` on touched production modules
- `ruff check` on touched production/test files
- `python scripts/check_utf8_hygiene.py` on touched code/docs
- `python scripts/ops_validator.py --strict`
- bounded runtime confirmation after code patching:
  - one non-wuxia investment/business-power sample should no longer force a false recovery beat
  - one real injury path should still enforce strong continuity

## 11. Guardrails

- preserve `natural healing`
- do not weaken true injury continuity or real mobility-loss handling
- do not turn this into a global Stage4 wording softening unrelated to the verified symptom
- do not widen into broad Stage2/Stage4 refactors in the same execution wave
- do not patch Stage3 first
- do not touch `docs/temp` outside mirror and roadmap synchronization

## 12. Temp Queue Notes

- temp status: `partially_realized`
- cleanup condition:
  - keep the mirror until bounded code realization, targeted verification, and either closure or explicit deactivation
- roadmap dependency:
  - below `0_0-stage4-consumer-contract-normalization-remediation`
  - below `0_0-stage4-repair-contract-normalization-remediation`
  - above `0_0-stage2-contract-normalization-remediation`
  - above the parked broad `0_0-stage234-cross-stage-contract-normalization-remediation` substrate lane

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- document type matches a bounded execution SSOT
- scope is limited to the verified non-wuxia state-lock overreach seam
- active Stage4 broad lanes remain above this item in queue order

Pass 2, evidence and consistency:

- claims are bounded to the 2026-04-06 lane surveys and merged bounded survey
- owner split is coherent with the runtime evidence: Stage2 producer, Stage4 hardener, Stage3 secondary
- canonical/temp semantics are explicit

Pass 3, execution and readability:

- tranches move from producer policy split to consumer/persistence normalization
- guardrails preserve natural healing and true injury severity
- the document is actionable without widening into a global cross-stage rewrite

Confidence: `96%`

Current-State Re-Audit:
- `docs/2026-04-06/0_0-stage234-nonwuxia-state-lock-overreach-stage2-tranche-3pass-audit.md`
- `docs/2026-04-07/0_0-stage234-nonwuxia-state-lock-overreach-stage4-reinspection-3pass-audit.md`

## 15. 2026-04-06 Stage2 Producer Tranche Update

Landed owner set:

- `modules/core/non_wuxia_recovery_policy.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/state_extractor.py`
- `config/prompts/analyst.yaml`
- `modules/domain/agents/analyst_prompts.py`
- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_state_extractor_non_wuxia.py`

Landed behavior:

- non-wuxia soft fatigue no longer auto-hardens into `recovery_scene_required`
- `StateExtractor` now normalizes non-wuxia soft fatigue/stress to advisory continuity instead of hard recovery obligation
- `V60.10` constraint prompt now splits hard injury vs soft-state advisory for non-wuxia
- Stage2 non-wuxia recovery penalty no longer fires on implicit/time-based soft recovery alone
- physical-injury cases still remain the hard path inside the Stage2 producer layer
- Stage2 prompt text now explicitly says non-wuxia soft fatigue does not require an opening-beat recovery scene

Verification completed:

- `pytest tests/test_arc_ensemble_lane_a.py -k "non_wuxia_recovery or implicit_non_wuxia or explicit_non_wuxia or hard_injury" -q`
- `pytest tests/test_state_extractor_non_wuxia.py tests/test_sweep32.py -k "state_extractor" -q`
- `python -m py_compile modules/core/non_wuxia_recovery_policy.py modules/domain/agents/arc_ensemble.py modules/domain/agents/state_extractor.py tests/test_arc_ensemble_lane_a.py tests/test_state_extractor_non_wuxia.py`
- `ruff check modules/core/non_wuxia_recovery_policy.py modules/domain/agents/arc_ensemble.py modules/domain/agents/state_extractor.py tests/test_arc_ensemble_lane_a.py tests/test_state_extractor_non_wuxia.py`
- `python scripts/check_utf8_hygiene.py modules/core/non_wuxia_recovery_policy.py modules/domain/agents/arc_ensemble.py modules/domain/agents/state_extractor.py config/prompts/analyst.yaml modules/domain/agents/analyst_prompts.py tests/test_arc_ensemble_lane_a.py tests/test_state_extractor_non_wuxia.py`

Current reading after Stage2-first implementation:

- Stage2 producer-side false hardening is materially reduced
- the lane is not closure-ready because Stage4 intake and Stage4 post-pass persistence still remain open
- the next bounded implementation step inside this SSOT is Stage4, not Stage3

## 16. 2026-04-07 Workspace Reinspection: Stage4 Tranche Still Pending

Reinspection evidence:

- `docs/2026-04-07/0_0-stage234-nonwuxia-state-lock-overreach-stage4-reinspection-3pass-audit.md`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `modules/core/stage4_orchestrator.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_immutable_fact_contract.py`

Current reading:

1. no hidden Stage4 landing was found in the current workspace
2. `[Stage4 Opening Scene Authority]` still uses genre-blind hard-canon wording for non-wuxia carryover
3. `carryover_pending_actions` and related chain-link fields still render as hard opening obligations by default
4. current Stage4 tests still codify the generic hard behavior rather than a non-wuxia soft/hard split

Queue consequence:

- keep the lane in the same roadmap position
- keep status as `partially_realized`
- keep Stage3 deferred
- prepare the next bounded code step as Stage4-only normalization across opening-authority plus carryover persistence/rendering surfaces

Implementation-ready owner set:

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_pass_runtime.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_immutable_fact_contract.py`
- `tests/test_stage4_post_processor.py`

Confidence for this reinspection update: `97%`
