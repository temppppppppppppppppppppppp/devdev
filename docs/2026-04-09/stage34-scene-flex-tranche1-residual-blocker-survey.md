# Stage34 Scene-Flex Tranche1 Residual Blocker Survey

Date: 2026-04-09
Status: final (bounded residual sweep completed on current HEAD after the tranche-1 `<=1 scene` hard-block demotion; 3-pass audited for implementation planning)
Canonical Path: `docs/2026-04-09/stage34-scene-flex-tranche1-residual-blocker-survey.md`
Commit State:
- Baseline Commit: `a5af976daa5285cc4b34fe7b075948057763f787`
- Baseline Dirty Summary: `dirty: active scene-flex tranche-1 code/doc updates, prompt/schema alignment edits, roadmap mirror refresh, and queue-state refresh already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Docs:
- `docs/2026-04-09/0_0-stage34-scene-flex-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-09/stage234-scene-split-origin-and-density-survey.md`
Evidence Artifact:
- `docs/2026-04-09/stage34-scene-flex-tranche1-residual-blocker-evidence.json`
Side-Effect Coverage: covered

## 1. Intent

Identify the residual scene-count blockers that remain after the current tranche-1 change lowered the earliest Stage3 hard block to `<=1 scene`.

This survey is bounded to:

- direct hard or semi-hard residual gates that can still block `2-scene` / `3-scene` shapes
- Stage4 pressure surfaces that still bias the system back toward `4-6` / `6-scene` slot coverage
- test anchors that currently encode the older scene-count assumptions

This survey is not a new execution SSOT and does not widen into tranche-2 implementation in the same turn.

## 2. Scope

Included:

- `modules/core/cross_agent_verifier.py`
- `modules/core/pre_director_checklist.py`
- `modules/core/pre_director_manuscript_checker.py`
- `modules/domain/agents/director_prompts.py`
- `config/prompts/director.yaml`
- `modules/core/prompt_builder.py`
- `modules/core/feedback_system.py`
- `modules/core/quality_dashboard.py`
- `modules/core/adversarial_self_play.py`
- `modules/core/self_reflection.py`
- `modules/core/agent_intelligence.py`
- `modules/core/confidence_calibration.py`
- `config/prompts/chief_writer.yaml`
- targeted tests that still encode `3-scene` / `4-scene` expectations

Excluded:

- new code changes beyond the already-landed tranche-1 front-gate demotion
- Stage2 remediation
- fresh proof-wave execution
- broad Stage4 anti-compression rewrites in this turn

## 3. Pass 1. Inventory

### A. Direct hard / semi-hard residual blockers

1. `CrossAgentVerifier` still defaults Architect precheck to `min_scenes = 4`.
   - `modules/core/cross_agent_verifier.py:182`
   - `modules/core/cross_agent_verifier.py:183`
   - `modules/core/cross_agent_verifier.py:303`
   - effect:
     - low-scene blueprints can still accrue direct Python violations before LLM review
     - if combined with another violation, the path can short-circuit the LLM compare step

2. `PreDirectorChecklist` still emits a `FAIL` below `3` scenes.
   - `modules/core/pre_director_checklist.py:639`
   - `modules/core/pre_director_checklist.py:646`
   - effect:
     - operator-facing blueprint validation still treats `2-scene` shapes as structurally failing

3. active Director manuscript authority still encodes `4-6 / 6-scene` assumptions.
   - `config/prompts/director.yaml:983`
   - `config/prompts/director.yaml:985`
   - `config/prompts/director.yaml:1064`
   - `config/prompts/director.yaml:1068`
   - mirrored fallback source:
     - `modules/domain/agents/director_prompts.py:372`
     - `modules/domain/agents/director_prompts.py:374`
     - `modules/domain/agents/director_prompts.py:442`
     - `modules/domain/agents/director_prompts.py:446`
   - effect:
     - manuscript-mode Director authority still rewards `6-scene equal coverage`
     - `2-scene` manuscripts still score `0점` on scene composition under the current prompt contract

### B. Pressure / advisory residuals

1. `PreDirectorManuscriptChecker` still skips density/header checks below `3` or `4` scenes.
   - `modules/core/pre_director_manuscript_checker.py:363`
   - `modules/core/pre_director_manuscript_checker.py:453`
   - effect:
     - below-threshold low-scene manuscripts do not get a normalized guidance path; they fall into a semantics gap instead

2. `PromptBuilder` still suppresses the high-impact guide below `4` scenes and keeps equal-reflection phrasing.
   - `modules/core/prompt_builder.py:170`
   - `modules/core/prompt_builder.py:209`
   - `modules/core/prompt_builder.py:539`

3. `FeedbackSystem` still anchors retry/operator guidance around `4` scenes and `6-scene` reflection.
   - `modules/core/feedback_system.py:192`
   - `modules/core/feedback_system.py:194`
   - `modules/core/feedback_system.py:811`
   - `modules/core/feedback_system.py:916`
   - `modules/core/feedback_system.py:927`

4. `QualityDashboard` still tells operators to fully reflect `Blueprint 6개 씬`.
   - `modules/core/quality_dashboard.py:640`
   - `modules/core/quality_dashboard.py:982`

5. `ChiefWriter` prompt source still pushes equal scene weighting.
   - `config/prompts/chief_writer.yaml:59`
   - `config/prompts/chief_writer.yaml:60`

6. auxiliary evaluators still retain older scene-count expectations.
   - `modules/core/adversarial_self_play.py:386`
   - `modules/core/self_reflection.py:98`
   - `modules/core/self_reflection.py:335`
   - `modules/core/agent_intelligence.py:594`
   - `modules/core/confidence_calibration.py:333`

### C. Test anchors encoding the older expectations

1. `PreDirectorChecklist` test still expects `2 scenes -> FAIL`.
   - `tests/test_continuity_modules.py:1082`

2. `PromptBuilder` test still expects `<4 scenes -> empty guide`.
   - `tests/test_prompt_builder.py:132`

3. sweep/source regression still pins the manuscript-checker `<3` guard.
   - `tests/test_sweep33.py:80`

### D. Targeted validation run in this survey

- `python -m pytest tests/test_continuity_modules.py -k "blueprint_scene_count_check" -q` -> PASS
- `python -m pytest tests/test_prompt_builder.py -k "less_than_4_scenes_returns_empty" -q` -> PASS
- `python -m pytest tests/test_sweep33.py -q` -> PASS

## 4. Pass 2. Semantic Classification

### P0

- none

### P1

- none

### P2

Residual `P2` remains.

Owner family A. Stage3 / Architect-side semi-hard blockers

- `modules/core/cross_agent_verifier.py`
- `modules/core/pre_director_checklist.py`

Why this is `P2`:

- the earliest front-gate demotion is already landed, but these surfaces can still reject or structurally fail low-scene shapes before the new contract is consistently honored downstream
- they are not mere prose pressure; they emit violations or `FAIL` severity

Owner family B. Stage4 manuscript authority still tied to `4-6 / 6-scene` scoring

- `config/prompts/director.yaml`
- `modules/domain/agents/director_prompts.py`

Why this is `P2`:

- these lines sit inside active Director manuscript-mode authority, not only guidance copy
- they can still push low-scene manuscripts toward REJECT or low-scoring outcomes even when Stage3 admits them

### P3

Residual `P3` remains.

Owner family C. Pressure / calibration surfaces

- `modules/core/pre_director_manuscript_checker.py`
- `modules/core/prompt_builder.py`
- `modules/core/feedback_system.py`
- `modules/core/quality_dashboard.py`
- `config/prompts/chief_writer.yaml`
- `modules/core/adversarial_self_play.py`
- `modules/core/self_reflection.py`
- `modules/core/agent_intelligence.py`
- `modules/core/confidence_calibration.py`

Why this is `P3`:

- most of these surfaces do not directly own acceptance any more
- but they still teach the system and the operator that `4-6` or `6` is the preferred “normal” shape
- left untouched, they will keep reintroducing anti-compression pressure even after direct hard gates are softened

## 5. Side-Effect Map

- file writes / artifacts:
  - direct artifact generation owners were not modified in this survey
  - prompt and operator-readback wording surfaces remain affected by the residuals

- DB / schema / transaction:
  - not a primary owner in this residual sweep

- JSONL / log / audit sinks:
  - no sink disappearance found
  - `quality_dashboard` and retry/readback wording still carry stale `6-scene` assumptions to operator-facing summaries

- console / UI / operator output:
  - yes
  - `feedback_system`, `prompt_builder`, `quality_dashboard`, and checklist surfaces all shape what operators and downstream LLM calls see

- rollback / recovery / retry:
  - yes
  - retry simplification in `feedback_system` still says `3~4개 씬만 있어도 OK`, which is closer to the new contract than the old `4+`, but still not aligned with the new `<=1 hard block`

- cache / global state:
  - not a direct owner

- bootstrap / env / config mutation:
  - not applicable

## 6. Pass 3. Execution Shape

Recommended next implementation order:

1. `P2-A` Architect-side residual demotion
   - normalize `CrossAgentVerifier` and `PreDirectorChecklist` to the same `<=1 hard block` contract
   - add focused tests so `2-scene dense` shapes no longer fail these owners by default

2. `P2-B` Director manuscript authority realignment
   - retune the active manuscript-mode Director prompt/scoring in `config/prompts/director.yaml`
   - keep fallback `modules/domain/agents/director_prompts.py` aligned in the same turn
   - this is still tranche-1 residual cleanup because it can directly override the newly opened Stage3 path

3. `P3` pressure-surface cleanup
   - demote `4/6-scene` guidance across retry/help/dashboard/calibration surfaces
   - move those surfaces from `slot coverage` wording toward `obligation materialization` wording

4. proof-wave rule
   - do not take a fresh proof wave before `P2-A` and `P2-B` are cleaned
   - after those are cleaned, one bounded proof wave becomes worth running

Not recommended:

- skipping straight to a proof wave now
- opening broad Stage4 anti-compression rewriting before the direct `P2` residual blockers are removed

## 7. Conclusion

Current read:

- `front gate demotion` is landed
- but `scene-flex tranche-1` is not yet semantically closed
- there are still live residual blockers

Severity summary:

- `P0`: none
- `P1`: none
- `P2`: yes
- `P3`: yes

Go / no-go:

- safe to continue implementation: `yes`
- safe to jump straight to proof wave: `no`
- next bounded target: `CrossAgentVerifier + PreDirectorChecklist + Director manuscript prompt/scoring`

## 8. 3-Pass Audit Record

Pass 1. Structure and scope

- kept the document bounded to tranche-1 residual blockers rather than reopening the full scene-flex lane
- separated direct blockers from pressure-only surfaces
- included test anchors because stale tests would otherwise hide the next safe patch order

Pass 2. Evidence and consistency

- all direct blocker claims are tied to current live file paths and line-anchored evidence
- the active Director source remains `config/prompts/director.yaml`, with `modules/domain/agents/director_prompts.py` kept as aligned fallback evidence
- targeted pytest confirmed the older expectations still exist in checklist/prompt-builder/sweep anchors

Pass 3. Execution and readability

- translated the residual inventory into a bounded next patch order
- avoided widening into tranche-2 implementation in the same survey
- kept proof-wave guidance explicit: clean residual `P2` first, then run proof

Confidence: `97%`
