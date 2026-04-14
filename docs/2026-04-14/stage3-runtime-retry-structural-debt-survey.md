# Stage3 Runtime/Retry Structural Debt Bounded Survey

Date: 2026-04-14
Status: final (3-pass audited)
Canonical Path: `docs/2026-04-14/stage3-runtime-retry-structural-debt-survey.md`
Commit State:
- Baseline Commit: `81b426a688c2a5b6279d254c7746baac1261235b`
- Baseline Dirty Summary: `dirty: Stage3 runtime/docs/tests already modified on current head; hotspots: modules/domain/agents/three_phase_blueprint_runtime.py, modules/domain/agents/blueprint_ensemble.py, modules/domain/agents/director_ensemble.py, modules/domain/agents/three_phase_blueprint_generator.py, tests/test_blueprint_patch_mode.py, tests/test_blueprint_ensemble_generate_ensemble.py, tests/test_director_modules.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## Intent

Audit only the remaining Stage3 runtime/retry structural debt that could still distort runtime behavior before the next rerun. This is a bounded survey, not a big-bang rewrite plan.

## Scope

Read-only survey of:
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/director_ensemble.py`
- Stage3-related tests that pin those surfaces

Out of scope:
- Polaris / DecisionKernel migration
- broad owner-surface refactors outside the four scoped modules
- new runtime feature work

## Pass 1 Inventory

### Runtime / retry owner

The retry coordinator is still concentrated in one owner:
- `_Stage3RepairRouter.build_retry_material()` and `build_validation_material()` normalize repair state in two entry paths
- `decide_phase2_retry()` and `decide_pass_with_fix()` decide route shape from that same normalized surface
- `_run_phase2_generation()` drives in-place patch versus full ensemble selection
- `_run_pass_with_fix_loop()` and `_run_pass_with_fix_iteration()` run the repair loop
- `_resolve_retry_cycle_result()`, `_run_retry_cycle()`, and `_finalize_terminal_failure()` terminate the retry path

Anchors:
- [`three_phase_blueprint_runtime.py:214`](../../modules/domain/agents/three_phase_blueprint_runtime.py:214)
- [`three_phase_blueprint_runtime.py:235`](../../modules/domain/agents/three_phase_blueprint_runtime.py:235)
- [`three_phase_blueprint_runtime.py:265`](../../modules/domain/agents/three_phase_blueprint_runtime.py:265)
- [`three_phase_blueprint_runtime.py:301`](../../modules/domain/agents/three_phase_blueprint_runtime.py:301)
- [`three_phase_blueprint_runtime.py:1507`](../../modules/domain/agents/three_phase_blueprint_runtime.py:1507)
- [`three_phase_blueprint_runtime.py:2404`](../../modules/domain/agents/three_phase_blueprint_runtime.py:2404)
- [`three_phase_blueprint_runtime.py:2498`](../../modules/domain/agents/three_phase_blueprint_runtime.py:2498)
- [`three_phase_blueprint_runtime.py:3041`](../../modules/domain/agents/three_phase_blueprint_runtime.py:3041)
- [`three_phase_blueprint_runtime.py:3168`](../../modules/domain/agents/three_phase_blueprint_runtime.py:3168)

### Ensemble admission owner

`blueprint_ensemble.py` still combines candidate admission, repair, and operator visibility in one screening path:
- `_prepare_blueprint_ensemble_context()` builds prompt context and carryover
- `_generate_single()` shapes retry feedback and prompt payloads
- `_request_blueprint_generation()` owns generation transport and schema extraction
- `_sanitize_blueprint_candidate()` performs contamination filtering, opening-transition normalization, tactical intrusion rejection, replay rejection, and generic contract admission

Anchors:
- [`blueprint_ensemble.py:391`](../../modules/domain/agents/blueprint_ensemble.py:391)
- [`blueprint_ensemble.py:838`](../../modules/domain/agents/blueprint_ensemble.py:838)
- [`blueprint_ensemble.py:1004`](../../modules/domain/agents/blueprint_ensemble.py:1004)
- [`blueprint_ensemble.py:1614`](../../modules/domain/agents/blueprint_ensemble.py:1614)

### Director decision owner

`director_ensemble.py` still mixes compare prompt assembly, selection normalization, quality gates, and sink payload shaping:
- `_resolve_ensemble_selection_state()` rewrites selected candidate state and score provenance
- `_apply_ensemble_quality_gates()` applies contradiction firewall, numeric checks, and adaptive verdict adjustment
- `_build_ensemble_decision_payload()` normalizes the final sink payload
- `_build_blueprint_compare_prompt()` and `_build_arc_compare_result_payload()` bridge the prompt/payload surface

Anchors:
- [`director_ensemble.py:1442`](../../modules/domain/agents/director_ensemble.py:1442)
- [`director_ensemble.py:1523`](../../modules/domain/agents/director_ensemble.py:1523)
- [`director_ensemble.py:1780`](../../modules/domain/agents/director_ensemble.py:1780)
- [`director_ensemble.py:2083`](../../modules/domain/agents/director_ensemble.py:2083)
- [`director_ensemble.py:2524`](../../modules/domain/agents/director_ensemble.py:2524)

### Facade owner

`three_phase_blueprint_generator.py` is already a thin facade over runtime orchestration. Its only notable heavy path is `_inplace_patch_blueprint()`, which is still an owner-side patch helper rather than a separate decision subsystem.

Anchors:
- [`three_phase_blueprint_generator.py:66`](../../modules/domain/agents/three_phase_blueprint_generator.py:66)
- [`three_phase_blueprint_generator.py:114`](../../modules/domain/agents/three_phase_blueprint_generator.py:114)
- [`three_phase_blueprint_generator.py:159`](../../modules/domain/agents/three_phase_blueprint_generator.py:159)

## Pass 2 Semantic Classification

### 1. Runtime retry coordinator drift

Classification: `can-wait`

Why it matters:
- the same retry state is still read, normalized, mutated, and consumed in one owner
- a future drift in `fix_scope`, `binding_issue_count`, or retry feedback shaping would still propagate through the next attempt
- this is the highest ROI extraction seam because it is the smallest boundary that still owns live routing

High-ROI seam:
- extract `Stage3RetryCoordinator` or `RetryRoutePlanner` from `three_phase_blueprint_runtime.py`
- keep `_run_*` orchestration in place, move route/state normalization and retry feedback shaping out first

### 2. Candidate admission is mixed with repair

Classification: `can-wait`

Why it matters:
- `_sanitize_blueprint_candidate()` both rejects and repairs candidates
- rejection order decides which error family survives
- the method mutates `scene["key_events"]` in place, so screening is not pure admission

High-ROI seam:
- extract `BlueprintCandidateAdmission` or `CandidateScreeningPipeline`
- keep contamination checks pure, return explicit `admitted / repaired / rejected` state, and let the caller apply mutation

### 3. Director surface still spans prompt, gate, and sink

Classification: `can-wait`

Why it matters:
- compare prompt construction, selection-state normalization, adaptive gate application, and sink payload shaping are all in one owner
- the current tests pin the round-trip, so this is not a rerun blocker, but it remains a drift hotspot

High-ROI seam:
- extract `DirectorCompareSurface` plus `DirectorDecisionSurfaceBuilder`
- keep prompt assembly separate from sink normalization

### 4. Generator facade is not a split target

Classification: `Polaris-non-goal`

Why it matters:
- the generator is already a thin shell over runtime
- a Polaris / DecisionKernel style rewrite would be a much larger structural move than this bounded lane needs

## Pass 3 Execution Shape

The best bounded path is not a big rewrite. It is a small seam-first cleanup:

1. freeze the retry-routing contract behind a coordinator seam
2. keep candidate admission pure enough to stop hidden in-place mutation from spreading
3. leave Director sink shaping as a later cleanup unless runtime evidence regresses

That ordering keeps the live retry path readable without changing the whole owner map.

## Side-Effect Map

Relevant runtime side-effects in the scoped files:
- console / operator logs
- `pipeline_result` mutation
- retry-state mutation
- `pass_rate_monitor` / intermediate-reject recording through the owner shell
- prompt shaping and response parsing

Not in scope for this survey:
- DB schema changes
- file/artifact persistence redesign
- queue/roadmap membership changes

## Tests Read

Pinned by Stage3-related tests:
- `tests/test_blueprint_patch_mode.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_director_modules.py`

Representative branch coverage:
- retry-feedback shaping and local-patch gate visibility: [`tests/test_blueprint_patch_mode.py:1321`](../../tests/test_blueprint_patch_mode.py:1321), [`tests/test_blueprint_patch_mode.py:1460`](../../tests/test_blueprint_patch_mode.py:1460)
- retry routing and pass-with-fix blocks: [`tests/test_blueprint_patch_mode.py:1484`](../../tests/test_blueprint_patch_mode.py:1484), [`tests/test_blueprint_patch_mode.py:1660`](../../tests/test_blueprint_patch_mode.py:1660), [`tests/test_blueprint_patch_mode.py:1801`](../../tests/test_blueprint_patch_mode.py:1801), [`tests/test_blueprint_patch_mode.py:1954`](../../tests/test_blueprint_patch_mode.py:1954), [`tests/test_blueprint_patch_mode.py:2079`](../../tests/test_blueprint_patch_mode.py:2079)
- candidate admission and contamination rejection: [`tests/test_blueprint_ensemble_generate_ensemble.py:528`](../../tests/test_blueprint_ensemble_generate_ensemble.py:528), [`tests/test_blueprint_ensemble_generate_ensemble.py:549`](../../tests/test_blueprint_ensemble_generate_ensemble.py:549), [`tests/test_blueprint_ensemble_generate_ensemble.py:579`](../../tests/test_blueprint_ensemble_generate_ensemble.py:579), [`tests/test_blueprint_ensemble_generate_ensemble.py:694`](../../tests/test_blueprint_ensemble_generate_ensemble.py:694), [`tests/test_blueprint_ensemble_generate_ensemble.py:736`](../../tests/test_blueprint_ensemble_generate_ensemble.py:736)
- Director compare and advisory round-trip: [`tests/test_director_modules.py:303`](../../tests/test_director_modules.py:303), [`tests/test_director_modules.py:329`](../../tests/test_director_modules.py:329), [`tests/test_director_modules.py:478`](../../tests/test_director_modules.py:478), [`tests/test_director_modules.py:515`](../../tests/test_director_modules.py:515), [`tests/test_director_modules.py:589`](../../tests/test_director_modules.py:589), [`tests/test_director_modules.py:640`](../../tests/test_director_modules.py:640)

## Confidence And Policy

Inference: current contract-debt closure is approximately `94%`.

Reasoning:
- no new must-before-rerun blocker was found in the scoped runtime/retry owners
- the remaining issues are structural seams, not new live contract breaks
- the current tests already pin the branch behavior on the identified surfaces

Policy result:
- rerun is not blocked by a new structural debt emergency
- if more work is desired before rerun, the highest-ROI seam is `Stage3RetryCoordinator`

