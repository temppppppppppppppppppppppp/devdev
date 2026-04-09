# Stage234 Scene Split Origin and Density Survey

Date: 2026-04-09
Status: final (static parallel survey completed; document 3-pass completed; confidence `96%`)
Canonical Path: `docs/2026-04-09/stage234-scene-split-origin-and-density-survey.md`
Evidence Artifact: `docs/2026-04-09/stage234-scene-split-origin-and-density-evidence.json`
Commit State:
- Baseline Commit: `b94390cb508a298a28349152bb15876f36662c65`
- Baseline Dirty Summary: `dirty worktree already contained roadmap/SSOT edits, dated docs, narrative/material edits, and deleted prior runtime artifacts; this survey stayed read-only except for its own dated outputs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/stage_map/stage3.md`
- `docs/2026-04-09/stage234-proof-wave-logging-readiness-survey.md`
Side-Effect Coverage: `n/a (survey-only)` for runtime side effects, `covered` for prompt/schema/validator/writer/director pressure surfaces

## 1. Intent

Answer one bounded system-track question on current HEAD:

1. where does the current Stage4-era `4 scene` split actually come from
2. is the source Stage2, Stage3, or Stage4
3. is the system truly fixed to exactly four scenes, or is it enforcing a narrower slot-and-coverage contract
4. does the current contract create compression pressure against the desired `variable scene unit` design

The user intent behind this survey is future-facing:
- blueprint should lock `what must happen`
- write should retain bounded freedom over `how many scenes` and `how long each scene should breathe`
- anti-compression rules should beat slot-filling and schema-pass incentives

## 2. Parallel Survey Layout

Three bounded slices were surveyed in parallel:

1. Upstream origin slice
   - Stage2 -> Stage3 handoff
   - Stage3 blueprint schema
   - Stage3 qualification and Director gating
2. Stage4 realization slice
   - writer prompt/template contracts
   - pre-Director manuscript checks
   - Stage4 context consumers
3. Compression-pressure slice
   - scope-overflow and scene-completeness heuristics
   - self-check / feedback / dashboard pressure
   - targeted tests that lock the current scene-count behavior

## 3. Pass 1. Inventory

### 3.1 Stage2 is not the owner of the current `4 scene` floor

Stage2 does talk about `scene engines`, but it does not appear to emit a fixed `scene_count` or `must be 4 scenes` contract into the Stage2 -> Stage3 boundary.

Observed evidence:
- `stage2_preflight` extracts and trims `scene_engines`, then surfaces only `mandatory_scene_engines` hints. (`modules/core/stage2_preflight.py:550-705`)
- the Stage2 -> Stage3 constraint compiler centers `must_focus`, `stop_line`, `continuity`, and `inherited_state`, not explicit scene cardinality. (`modules/domain/agents/blueprint_constraint_compiler.py:124-127`, `:193-240`)
- Stage2/Stage3 boundary guardrail tests verify those sections, not a fixed number of scenes. (`tests/test_stage2_stage3_episode_boundary_guardrail.py:321-327`)

### 3.2 Stage3 contains the earliest hard `4 scene` gates

Current Stage3 behavior is internally split:
- prompt examples and schema surfaces are not one single exact `4`
- but qualification and Director gating both fail closed below `4`

Hard gates:
- `BlueprintEnsembleGenerator._qualify_blueprint_candidates()` only qualifies candidates when `scene_count >= 4` and `integrated_len >= 500`. (`modules/domain/agents/blueprint_ensemble.py:487-492`)
- if nothing qualifies, Stage3 cannot continue through the normal ensemble path. (`modules/domain/agents/blueprint_ensemble.py:604`)
- Stage3 Director single-candidate gating separately rejects `<4` scenes. (`modules/domain/agents/director_ensemble.py:1895-1905`)
- the direct `<4` rejection path is locked by tests. (`tests/test_blueprint_ensemble_generate_ensemble.py:67-87`, `tests/test_director_modules.py:333-343`)

Soft upstream pressure and inconsistency:
- Stage3 prompt example in `ensemble.yaml` shows a `scene_1..scene_4` JSON example. (`config/prompts/ensemble.yaml:393-405`)
- the same prompt also says `scene_breakdown` should be `3~5` scenes, not a fixed four. (`config/prompts/ensemble.yaml:436`, `:449`)
- the Stage3 stage map currently documents the live minimum as `scene_count >= 4`, while the unified validator itself only flags `<3`. (`docs/stage_map/stage3.md:122-128`, `modules/domain/agents/unified_blueprint_validator.py:925-931`)
- Stage3 scenario-density logic already reasons over variable scene counts and has explicit density tests for `3`, `4`, and `5`. (`modules/domain/agents/unified_blueprint_validator.py:1926-1937`, `tests/test_stage3_clarity_density_wave1.py:267-317`)

### 3.3 The schema layer is not exact-four, but it still nudges slot thinking

The core schema layer does not define `exactly 4 scenes`, but it is still not a clean free-form `variable scene unit` contract.

Observed evidence:
- the response schema describes `scene_breakdown` as keyed by `scene_1..scene_5`. (`modules/core/response_schemas.py:614-620`)
- the Pydantic model keeps `scene_breakdown` as a dict and does not hard-pin four. (`modules/models/blueprint.py:50`)
- constants and calibration disagree with the schema wording by preferring `6` as target and `4` as minimum. (`modules/core/constants.py:336-337`, `modules/core/confidence_calibration.py:327-333`)
- `cross_agent_verifier` also defaults to `min_scenes = 4`. (`modules/core/cross_agent_verifier.py:182-185`)

### 3.4 Stage4 is not hard-coded to exactly four scenes

The current Stage4-side runtime mostly consumes `len(scene_breakdown)` dynamically. That means Stage4 is not the earliest owner of the `4` floor.

Observed evidence:
- Stage4 context surfaces iterate the blueprint’s actual `scene_breakdown` rather than forcing `4`. (`modules/core/stage4_context_builder.py:353-356`, `:492-497`)
- `chief_writer` structural patch flow also derives `expected_blocks` from `len(scene_breakdown)`. (`modules/domain/agents/chief_writer.py:1333-1343`)
- manuscript scene-header checks use `expected_count = len(scene_breakdown)` and compute header requirements from that count. (`modules/core/pre_director_manuscript_checker.py:308-319`)
- blocking validator scope/completeness checks derive scene count from the blueprint dynamically. (`modules/validation/blocking_validator_scene_checks.py:72-74`, `:151-170`)

### 3.5 Stage4 amplifies slot rigidity and coverage pressure

Even though Stage4 is not the first hard `4 scene` source, it strongly amplifies the effect by treating the blueprint as a scene-slot contract that must be reflected evenly and explicitly.

Observed evidence:
- chief-writer guidance says to reflect all blueprint scenes with balanced weight. (`modules/domain/agents/chief_writer.py:136`)
- chief-writer prompts require explicit `### 씬 N: 제목` headers and say all scenes must be written in order without omission. (`modules/domain/agents/chief_writer_prompts.py:169-172`)
- writer template repeats the same header contract and warns that a single prose block is rejectable. (`modules/core/writer_template.py:275-278`)
- prompt-builder self-checklist says `scene_count` scenes must all be reflected evenly and explicitly bans `front-heavy / back-summary` behavior. (`modules/core/prompt_builder.py:533-540`)
- Director prompts set a `6 scenes` goal, require at least `4` on retries `0-1`, and score scene composition by how many designed scenes are reflected. (`modules/domain/agents/director_prompts.py:360-374`, `:441-446`)
- feedback and dashboard surfaces reinforce the same norm: `6개 씬 모두 반영`, `모든 씬 순서대로`, `후반부 씬 주의`. (`modules/core/feedback_system.py:811`, `:856`, `:916`, `:927`; `modules/core/quality_dashboard.py:640`)

### 3.6 Compression pressure is real and cross-layered

The current stack does not only ask for more scenes. It also constrains length and balance in a way that can push writing toward compressed scene coverage.

Observed evidence:
- `quality_amplifier` frames the design target as `4-6` scenes, `800-1500` chars per scene, `4000-6000` total. (`modules/core/quality_amplifier.py:294-297`)
- `blocking_validator_scene_checks` sets manuscript scope overflow as `scene_count * chars_per_scene`, with default `1500` chars/scene, then warns or rejects above that range. (`modules/validation/blocking_validator_scene_checks.py:95-121`)
- `cross_agent_verifier` uses the same family of expected-length logic and can flag overflow. (`modules/core/cross_agent_verifier.py:270-274`)
- prompt-builder and feedback surfaces also push fixed minimum total length plus equal scene reflection. (`modules/core/prompt_builder.py:538-540`, `modules/core/feedback_system.py:903-929`)

## 4. Pass 2. Semantic Classification

### 4.1 Answer to the direct question

`S4 currently writes 4 scenes` is not the most accurate reading.

More accurate reading:
- the system is not hard-fixed to exactly four scenes at Stage4 runtime
- the earliest hard `4` floor comes from Stage3 qualification and Stage3 Director gating
- Stage4 then amplifies that floor into a rigid scene-slot execution style through:
  - explicit scene headers
  - all-scene coverage requirements
  - balanced-density pressure
  - scene-count-based length heuristics

So the current effective behavior is:
- `minimum 4` as a hard upstream gate
- `goal 6` in several downstream prompt/grading surfaces
- `3~5` in some Stage3 prompt/schema wording
- dynamic consumption of the actual scene count once a blueprint exists

This is not `exact four`.
It is `cross-stage scene-cardinality incoherence plus slot-coverage pressure`.

### 4.2 Why the current contract fights the desired variable-scene design

The user’s desired model is:
- blueprint fixes obligation
- writer can rebalance scene count and dwell time
- anti-compression beats equal-slot fill

The current contract fights that in three ways:

1. It treats `scene_breakdown` as a first-class structural slot map.
2. It rewards coverage count and balanced reflection more than dramatized scene dwell.
3. It enforces both minimum total length and per-scene scope ceilings, which increases compression pressure when the scene count rises.

That means the system currently biases toward:
- “cover all slots”
- “keep later slots from looking omitted”
- “stay within per-scene scope”

instead of:
- “let scene units breathe where resistance, stalemate, reversal, and aftermath need more page-time”

### 4.3 Important internal inconsistency

There is one clear cross-stage inconsistency family:

- Stage3 prompt says `3~5` scenes. (`config/prompts/ensemble.yaml:436`, `:449`)
- response schema names `scene_1..scene_5`. (`modules/core/response_schemas.py:618`)
- unified validator allows `3+`. (`modules/domain/agents/unified_blueprint_validator.py:925-931`)
- constants and several downstream surfaces target `6`. (`modules/core/constants.py:336-337`, `modules/domain/agents/director_prompts.py:360-374`)
- Stage3 ensemble and Director hard-reject `<4`. (`modules/domain/agents/blueprint_ensemble.py:492`, `modules/domain/agents/director_ensemble.py:1897`)

This inconsistency is itself part of the density/compression problem, because the pipeline sends mixed scene-count signals before the writer even starts.

## 5. Pass 3. Execution Consequence

If the future goal is to move from `fixed-ish scene boxes` to `variable scene units`, the primary owners are:

1. Stage3 blueprint contract/gating
   - remove or relax the hard `<4` fail gates
   - replace scene-count qualification with obligation-completeness plus density/readability checks
2. blueprint schema/prompt normalization
   - stop mixing `3~5`, `min 4`, `target 6`, and `scene_1..scene_5`
   - promote a variable scene-unit representation or open scene map contract
3. Stage4 writer/director/checker policy
   - shift from `all scenes evenly reflected` to `all blueprint obligations materialized without compression`
   - replace equal per-scene pressure with anti-compression rules such as:
     - summary ban
     - resistance / stalemate / reversal dwell time
     - later-scene non-collapse
     - payoff must be dramatized, not merely mentioned

What should not be done first:
- patching Stage2
- treating Stage4 as the sole owner of the current `4 scene` tendency
- adding more same-family prompt nudges without first normalizing the upstream scene-count contract

## 6. Severity Ledger

Overall reading on current HEAD:

- `P0`: none
- `P1`: none
- `P2`: yes
- `P3`: yes

`P2`:
- cross-stage scene-cardinality and slot-coverage contract now materially biases the writer toward compression and schema-oriented scene filling instead of flexible dramatization
- owners are primarily Stage3 hard gates plus Stage4 amplification surfaces

`P3`:
- scene-cardinality semantics are internally inconsistent across prompt, schema, validator, constants, grading, and feedback layers (`3`, `4`, `5`, `6` all appear as meaningful boundaries)

Stage ownership shorthand:
- direct Stage2-owned issue: none promoted
- direct Stage3-owned issue: yes, hard minimum gate contribution
- direct Stage4-owned issue: yes, amplification / compression-pressure contribution
- practical remediation owner: mixed Stage3 + Stage4

## 7. Targeted Validation Performed

All commands below passed on current HEAD:

- `python -m pytest tests/test_blueprint_ensemble_generate_ensemble.py -k "qualify_blueprint_candidates_tracks_pass_and_fail_metadata" -q`
- `python -m pytest tests/test_director_modules.py -k "compare_and_select_single_candidate_reject_few_scenes" -q`
- `python -m pytest tests/test_prompt_builder.py -k "less_than_4_scenes_returns_empty or with_scene_count" -q`
- `python -m pytest tests/test_blocking_validator_submodules.py -k "scope_overflow_smoke or markdown_scene_headers_pass or markdown_scene_headers_incomplete_rejects" -q`

What these confirm:
- Stage3 qualification still hard-favors `4` scenes
- Stage3 Director still rejects fewer than `4`
- prompt-builder still treats `<4` as a reduced/non-ideal structure band while surfacing `6` in self-check
- blocking validator still ties structure and scope checks to dynamic scene count and explicit scene headers

## 8. 3-Pass Audit Record

Pass 1. Structure and scope:
- kept the document bounded to `scene split origin + density/compression pressure`
- separated origin, amplification, and compression instead of flattening them into one claim
- answered the direct `S2 or S3?` question explicitly

Pass 2. Evidence consistency:
- reconciled Stage3 prompt/schema wording against live Stage3 hard gates
- distinguished Stage4 dynamic consumption from Stage4 amplification pressure
- did not over-claim `exact 4 fixed` where evidence only supported `min 4 + goal 6 + slot pressure`

Pass 3. Execution usefulness:
- ended with a direct severity ledger
- identified the true future owner set for a variable-scene refactor
- kept survey-only posture and did not inflate into an execution SSOT or implementation plan

Confidence: `96%`

