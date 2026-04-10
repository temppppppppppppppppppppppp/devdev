# 0_0 Stage34 Scene-Flex Contract Normalization Remediation Execution SSOT

Date: 2026-04-09
Status: closed (2026-04-10 current-worktree closure audit now confirms tranche 1, tranche 2, tranche 3 Wave A/B, and the former parked secondary surfaces are all closure-clean for this lane; broader proof-wave/front queue items remain separate and active)
Canonical Path: `docs/2026-04-09/0_0-stage34-scene-flex-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `removed after 2026-04-10 closure sync (was docs/temp/0_0-stage34-scene-flex-contract-normalization-remediation-execution-ssot.md)`
Commit State:
- Baseline Commit: `dfb44351bc41de1243e0def0bfbcb7336bc93388`
- Baseline Dirty Summary: `dirty: scene-flex secondary-surface code/tests/docs plus unrelated stage0/material edits already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same-turn closure pass lands the former tranche-3 secondary surfaces, adds wave-c regression coverage, and closes this lane on the current workspace state without reordering unrelated proof/front items`
Source Survey Docs:
- `docs/2026-04-09/stage234-scene-split-origin-and-density-survey.md`
- `docs/2026-04-09/stage34-scene-flex-tranche1-residual-blocker-survey.md`
- `docs/2026-04-09/stage34-scene-flex-tranche2-implementation-3pass-audit.md`
- `docs/2026-04-10/stage34-scene-flex-tranche3-pre-implementation-3pass-audit.md`
- `docs/2026-04-10/stage34-scene-flex-tranche3-post-implementation-3pass-audit.md`
- `docs/2026-04-10/stage34-scene-flex-secondary-surface-closure-3pass-audit.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
Evidence Artifacts:
- `docs/2026-04-09/stage234-scene-split-origin-and-density-evidence.json`
- `docs/2026-04-09/stage34-scene-flex-tranche1-residual-blocker-evidence.json`
- `docs/2026-04-09/stage34-scene-flex-tranche2-implementation-evidence.json`
- `docs/2026-04-10/stage34-scene-flex-tranche3-post-implementation-evidence.json`
- `docs/2026-04-10/stage34-scene-flex-secondary-surface-closure-evidence.json`
Side-Effect Coverage: covered

## 1. Intent

Define one bounded execution lane that can reduce the current `scene-count compression pressure` without inflating into a broad rewrite.

This lane exists because the current survey says:

- Stage2 is not the real owner of the problem
- the earliest hard floor sits in Stage3 `<4 scene` gating
- Stage4 then amplifies that floor into `slot coverage + equal reflection + scene-count-based pressure`
- the user wants `obligation-first, variable-scene writing`, not rigid scene boxes

This SSOT originated as a deliberately parked lane below the current proof-wave/front closure stack.
The current operator redirect first activated tranche 1 and tranche 2 so the workspace could relieve the Stage3 hard floor plus the main Stage4 amplification layer without widening into a full heuristic rewrite.
The later 2026-04-10 continuation landed tranche 3 Wave A/B on the active runtime owners, and the current same-day closure pass then normalized the former parked secondary surfaces on the live workspace state and cleared the lane for closure.

## 2. Baseline Facts

- direct Stage2-owned scene-count defect is not promoted
- Stage3 currently hard-fails candidate flows below `4` scenes through:
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/director_ensemble.py`
- Stage3 prompt/schema/validator layers are internally inconsistent across `3`, `4`, `5`, and `6`
- Stage4 mostly consumes the actual `scene_breakdown` dynamically, but adds strong slot pressure through:
  - `### 씬 N` header requirements
  - all-scene reflection language
  - `6 scenes` target grading
  - late-scene anti-summary language that still remains slot-shaped
- compression pressure is real because the stack combines:
  - `4-6 scenes`
  - `800-1500 chars/scene`
  - `4000-6000 total`
  - `scene_count * chars_per_scene` overflow heuristics
- current severity reading from the survey is:
  - `P2`: cross-stage compression-driving contract
  - `P3`: cross-layer scene-count incoherence

## 3. Scope

Included:

- Stage3 scene-cardinality qualification and single-candidate gating
- Stage3 prompt/schema/validator scene-count normalization
- Stage4 writer/director/checker anti-compression contract retuning
- active Director prompt source alignment between `config/prompts/director.yaml` and `modules/domain/agents/director_prompts.py`
- scene-count-based overflow / completeness heuristics that directly sustain compression pressure
- targeted regression coverage for `3-scene`, `4-scene`, and `5-scene` acceptance paths

Excluded:

- Stage2 redesign
- current proof-wave execution
- broad narrative artifact rewrite
- repo-wide blueprint schema rewrite in one tranche
- DB schema redesign
- same-turn runtime behavior claims

## 4. Pass 1. Inventory Summary

Primary owner inventory:

1. Stage3 hard floor
   - `modules/domain/agents/blueprint_ensemble.py`
   - `modules/domain/agents/director_ensemble.py`
2. Stage3 scene-count semantics
   - `config/prompts/ensemble.yaml`
   - `modules/core/response_schemas.py`
   - `modules/domain/agents/unified_blueprint_validator.py`
   - `modules/core/constants.py`
   - `modules/core/cross_agent_verifier.py`
3. Stage4 amplification surfaces
   - `modules/domain/agents/chief_writer.py`
   - `modules/domain/agents/chief_writer_prompts.py`
   - `modules/core/writer_template.py`
   - `modules/core/prompt_builder.py`
   - `config/prompts/director.yaml`
   - `modules/domain/agents/director_prompts.py`
   - `modules/core/feedback_system.py`
   - `modules/core/quality_dashboard.py`
4. Compression heuristics
   - `modules/validation/blocking_validator_scene_checks.py`
   - `modules/core/cross_agent_verifier.py`
   - `modules/core/quality_amplifier.py`

Primary debt inventory:

1. hard `<4` rejection in Stage3
2. mixed `3/4/5/6` scene-count semantics across layers
3. slot-coverage-first Stage4 writing/Director language
4. scene-count-derived overflow pressure that can punish slower, denser scene dwell

## 5. Pass 2. Semantic Classification

### Class A. Primary P2 owners

- Stage3 hard floor:
  - candidate qualification must stop treating `<4` as a universal hard fail
  - single-candidate Director path must stop reopening the same hard floor

### Class B. Secondary P2 amplification

- Stage4 writer/director/checker surfaces must stop equating `quality` with:
  - all scene slots reflected evenly
  - 6-scene target language by default
  - headerized slot completeness as the main proxy for dramatic adequacy

### Class C. P3 coherence cleanup

- prompt/schema/validator/constants/calibration should stop sending conflicting scene-count signals
- `scene_count` should become a soft planning signal, not a hidden authority mismatch across subsystems

## 6. Side-Effect Map

- file writes / artifacts:
  - yes; prompt/schema/validator/writer/checker modules plus tests will change when activated

- DB / schema / transaction boundaries:
  - no DB migration is expected in tranche 1
  - blueprint response schema may change at the contract level, but should remain compatibility-aware

- JSONL / log / audit sinks:
  - not a primary owner
  - may gain more explicit anti-compression verdict reasons later, but no sink redesign is the first tranche

- console / UI / operator output:
  - yes; writer guidance, Director feedback, and dashboard phrasing may change

- rollback / recovery / retry:
  - yes; retry prompts and failure classifications may change because scene-count failure will be demoted

- cache / global state:
  - limited
  - any prompt/schema cache keyed by blueprint contract may need bounded revalidation

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

Preferred realization principle:

- keep blueprint authority on `what must materialize`
- demote fixed-ish scene cardinality to a soft preference
- let Stage4 optimize for dramatic materialization rather than slot coverage

This should be realized as three bounded tranches.

Current activation scope:

- tranche 1 residual closure is landed and closure-clean
- tranche 2 anti-compression contract promotion is closure-clean
- tranche 3 Wave A/B runtime closure is landed and bounded-canary clean
- tranche 3 secondary prompt/dashboard/template/collector surfaces are now normalized on the current workspace state
- the broader proof-wave/front stack remains active, but it is no longer a dependency that keeps this scene-flex lane open

Realization tranches:

1. `scene-cardinality demotion`
   - remove the hard universal `<4` floor from Stage3 qualification/judgment
   - replace it with obligation completeness + density/readability checks

2. `anti-compression contract promotion`
   - retune Stage4 writer/director/checker prompts away from `all scene slots equally covered`
   - promote:
     - summary ban
     - later-scene non-collapse
     - resistance / stalemate / reversal dwell time
     - payoff dramatization over mention-only closure

3. `overflow heuristic normalization`
   - stop using `scene_count * fixed chars_per_scene` as the dominant overflow authority
   - replace with checks that punish compression and skip-summary behavior more directly

Architectural sequencing rule:

- do not start with Stage4 prompt cosmetics alone
- first demote the Stage3 hard floor
- then rewrite Stage4 amplification
- only then normalize overflow heuristics that still assume rigid scene slots

## 8. Execution Tranches

### Tranche 1. Stage3 Scene-Cardinality Demotion

Status: `implemented on current HEAD; residual sweep closed`

Goal:

- remove Stage3 as the earliest hard owner of the four-scene box

Targets:

- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/director_ensemble.py`
- `config/prompts/ensemble.yaml`
- `modules/core/response_schemas.py`
- `modules/domain/agents/unified_blueprint_validator.py`

Residual closure surfaces landed in the same tranche:

- `modules/core/cross_agent_verifier.py`
- `modules/core/pre_director_checklist.py`
- `config/prompts/director.yaml`
- `modules/domain/agents/director_prompts.py`
- `modules/core/pre_director_manuscript_checker.py`
- `modules/core/prompt_builder.py`
- `modules/core/feedback_system.py`
- `modules/core/quality_dashboard.py`
- `config/prompts/chief_writer.yaml`
- `config/prompts/writer_rules.json`
- `modules/core/adversarial_self_play.py`
- `modules/core/self_reflection.py`
- `modules/core/agent_intelligence.py`
- `modules/core/confidence_calibration.py`
- `modules/domain/agents/director_grading.py`

Outputs:

- no universal hard `<4` gate
- one coherent first-pass scene-count contract
- tests that allow `2-scene` and `3-scene` blueprints when obligation density is adequate
- Architect precheck and Pre-Director checklist now honor the same `<=1 hard block` contract
- active Director manuscript authority no longer hardcodes `4-6 / 6-scene` scoring as default judgment authority
- bounded writer/operator/calibration surfaces now bias toward obligation materialization and late-scene non-collapse instead of `6개 씬 모두 반영`

### Tranche 2. Stage4 Anti-Compression Contract Promotion

Status: `implemented on current HEAD; closure-clean`

Goal:

- retarget Stage4 from slot coverage to obligation materialization and dramatic dwell time

Targets:

- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/writer_template.py`
- `modules/core/prompt_builder.py`
- `config/prompts/director.yaml`
- `modules/domain/agents/director_prompts.py`
- `modules/core/feedback_system.py`
- `modules/core/quality_dashboard.py`

Outputs:

- `all scenes equally reflected` language is demoted across the remaining active writer/director/template/feedback surfaces
- anti-compression rules are promoted with planning-anchor compatibility preserved
- `6 scenes all reflected` is no longer used as default fallback authority
- scene headers remain compatibility anchors, but equal-slot distribution is no longer the main quality proxy

### Tranche 3. Overflow / Completeness Heuristic Normalization

Status: `fully closed on the current workspace state; Wave A/B plus former parked secondary surfaces are all validated`

Goal:

- remove rigid scene-count-derived compression incentives from the active validator / precheck / confidence / continuity logic without widening into dormant prompt/dashboard cleanup

Implemented Wave A:

- `modules/validation/blocking_validator_scene_checks.py`
- `modules/core/cross_agent_verifier.py`
- `modules/core/pre_director_checklist.py`
- `modules/core/confidence_calibration.py`

Implemented Wave B:

- `modules/domain/agents/director_continuity.py`

Shared helper added:

- `modules/core/scene_obligation_heuristics.py`

Formerly parked secondary surfaces now landed on the current workspace state:

- `modules/core/quality_amplifier.py`
- `modules/core/writer_template.py`
- `modules/core/quality_dashboard.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/manuscript_validator.py`

Outputs:

- overflow checks are no longer dominated by `scene_count * fixed chars_per_scene`
- completeness and confidence checks now favor materialized obligations and late-scene non-collapse on the active runtime seam
- Stage4 operator-path warnings no longer attach low-scene false pressure to dense `2-scene` and `3-scene` manuscripts on the live `PreCheck / Confidence / CrossVerify` path
- `DirectorContinuityValidator` now accepts dense `2-scene` tail-heavy manuscripts while still rejecting weak `3-scene` under-reflection
- prompt/template/dashboard/manuscript-collector secondaries now align with the same obligation-first contract instead of preserving older rigid `4-6` or raw slot-proxy language
- targeted regressions now protect both the active runtime seam and the former secondary surfaces without reopening unrelated queue families

## 9. Acceptance Criteria

- a well-formed `2-scene` blueprint can survive Stage3 when obligation density is sufficient
- a well-formed `3-scene` blueprint can still survive Stage3 when obligation density is sufficient
- a `5-scene` blueprint remains valid without conflicting schema/prompt/validator signals
- Stage4 no longer defaults to `6개 씬 모두 반영` as the main quality proxy
- Stage4 guidance explicitly rewards anti-compression behaviors instead of equal slot filling
- overflow logic no longer primarily punishes manuscripts just because fewer scenes hold more dramatic dwell time
- no new `180+ LOC` function is introduced during realization

## 10. Verification Plan

Before implementation start from this document:

- re-run this document 3-pass against live HEAD
- re-open the source survey and confirm the owner split still holds
- refresh roadmap ordering if a higher-priority live lane appears

Targeted verification executed on the current workspace state after Wave A/B plus the secondary-surface closure landed:

- `python -m pytest tests/test_scene_flex_wave_c.py -q`
- `python -m pytest tests/test_scene_flex_wave_a.py tests/test_scene_flex_wave_b.py -q`
- `python -m pytest tests/test_v55_modules.py -k "WriterTemplate" -q`
- `python -m pytest tests/test_stage3_clarity_density_wave1.py -k "ScenarioDensityPrevalidation" -q`
- `python -m pytest tests/test_director_continuity_blueprint_v60.py tests/test_director_modules.py -k "validate_blueprint_completeness" -q`
- `python -m pytest tests/test_stage4_interview_round.py -k "run_director_optional_validation_modules_routes_checklist_confidence_and_crossverify" -q`
- `python -m py_compile modules/core/quality_amplifier.py modules/core/writer_template.py modules/core/quality_dashboard.py modules/domain/agents/manuscript_validator.py modules/domain/agents/unified_blueprint_validator.py tests/test_scene_flex_wave_c.py`
- `ruff check modules/core/quality_amplifier.py modules/core/writer_template.py modules/core/quality_dashboard.py modules/domain/agents/manuscript_validator.py modules/domain/agents/unified_blueprint_validator.py tests/test_scene_flex_wave_c.py`
- `python scripts/check_utf8_hygiene.py modules/core/quality_amplifier.py modules/core/writer_template.py modules/core/quality_dashboard.py modules/domain/agents/manuscript_validator.py modules/domain/agents/unified_blueprint_validator.py tests/test_scene_flex_wave_c.py`
- touched-function recount on current HEAD:
  - `modules/validation/blocking_validator_scene_checks.py::_check_scope_overflow` = `81 LOC`
  - `modules/core/cross_agent_verifier.py::_python_precheck_writer` = `63 LOC`
  - `modules/core/pre_director_checklist.py::_check_manuscript_blueprint_alignment` = `141 LOC`
  - `modules/core/confidence_calibration.py::_score_manuscript_scene_coverage` = `40 LOC`
  - `modules/domain/agents/director_continuity.py::_validate_blueprint_completeness_v60` = `65 LOC`
  - no new `180+ LOC` function was introduced by this tranche
- UTF-8 hygiene on touched docs/code
- dedicated runtime evidence captured in `docs/2026-04-10/stage34-scene-flex-tranche3-post-implementation-evidence.json`
- secondary-surface closure evidence captured in `docs/2026-04-10/stage34-scene-flex-secondary-surface-closure-evidence.json`

## 11. Guardrails

- explicit reprioritization has now landed tranche 3 Wave A/B plus the former parked secondaries; do not misread that closure as closure of unrelated proof/front queue items
- do not patch Stage2 first
- do not remove `scene_breakdown` as a concept in tranche 1
- do not turn tranche 1 into a broad schema rewrite
- do not let Stage4 prompt retuning outrun Stage3 hard-floor demotion
- do not remove scene headers or template anchors in tranche 2; keep compatibility while demoting equal-slot authority
- do not replace one rigid scene-count rule with another hidden rigid dwell-time rule
- keep touched functions below the workspace complexity guardrails
- do not misread unrelated residual `Confidence:medium` style/length noise as reopened scene-flex pressure

## 12. Temp Queue Notes

- temp status: `closed (tranche-1/2/3 closure-clean on current workspace state; temp mirror removed after closure sync)`
- cleanup condition:
  - canonical SSOT remains as historical authority for the lane
  - temp mirror is removed because no active scene-flex execution work remains in `docs/temp/`
- roadmap dependency:
  - explicit operator redirect temporarily bypassed the older parked posture long enough to close tranche 1, tranche 2, tranche 3 Wave A/B, and the secondary-surface follow-up
  - the broader proof-wave/front closure work remains pending and should not be silently closed or removed
  - removal of this temp mirror does not reorder or close any unrelated queue lane

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1. Structure and scope:

- kept this as one bounded future lane rather than a broad pipeline rewrite
- separated Stage3 owner work, Stage4 amplification, and heuristic normalization into tranches
- kept Stage2 explicitly out of tranche 1 ownership

Pass 2. Evidence and consistency:

- source survey still supports `Stage3 hard floor + Stage4 amplification` as the owner split
- current codebase revalidation confirms that `config/prompts/director.yaml` and the residual blocker survey still identify the same active pressure family
- current-head implementation closes the direct residual P2/P3 blockers identified by the bounded tranche-1 survey and lands the tranche-2 anti-compression retune without silently widening into tranche 3
- the later tranche-2 closure audit confirms direct `P0-P3` absence on current HEAD
- the later tranche-3 post-implementation audit plus bounded operator-path canary cleared the active runtime owner set, and the current closure audit now clears the formerly parked secondaries on the same workspace state
- roadmap state now supports removing only this lane's temp mirror while leaving the broader proof/front queue intact
- touched-function recount stays below the workspace complexity guardrails for this tranche
- no live `P0-P1` over-claim was introduced

Pass 3. Execution and readability:

- acceptance criteria still focus on pressure relief, not schema cosmetics
- verification plan now records the landed Wave A/B regression set, the bounded Stage4 operator-path evidence, and the secondary-surface closure regressions
- current re-audit records tranche-1 residual closure, tranche-2 contract promotion, tranche-3 Wave A/B runtime closure, and the former secondary surfaces as closure-clean on the current workspace state

Confidence: `98%`
