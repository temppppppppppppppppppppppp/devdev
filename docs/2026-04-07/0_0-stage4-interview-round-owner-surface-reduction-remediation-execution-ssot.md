# 0_0 Stage4 Interview-Round Owner-Surface Reduction Remediation Execution SSOT

Date: 2026-04-07
Status: in_progress (the first bounded post-select boundary extraction landed on 2026-04-07, later contract/session/episode/retry/raw-evidence helper work also landed on the live workspace, but the current recount still leaves this as a structure-first, proof-deferred lane with dominant owner pressure in `Stage4InterviewRound`)
Canonical Path: `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `eac3386ce3b19f720e6e12548721df5abe2ee755`
- Baseline Dirty Summary: `dirty: prior Stage3 opening-transition tranche plus docs/temp mirrors already modified in worktree`
- Resume Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
- Resume Drift Summary: `live 3-pass re-audit on the current workspace now finds `Stage4InterviewRound` at 166 direct methods / 2 180+ / 5 120+; the first module-boundary extraction remains landed, later contract/raw-evidence helper work is also landed, and the next useful move is proof-first plus later owner-pressure reopening rather than claiming the older 159-method recount as current truth`
Source Survey Docs:
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-bounded-survey.md`
Evidence Artifacts:
- `none; live AST recount and focused regression evidence are recorded inline below`
Side-Effect Coverage: covered

## 1. Intent

Promote a structure-only pending lane that reduces `Stage4InterviewRound` owner pressure through module-boundary extraction after the current functional queue clears enough to justify it.

This lane is not a hidden runtime blocker.
It exists so the workspace can keep a real owner-surface debt item explicit in the formal queue instead of rediscovering it later during unrelated Stage4 changes.

## 2. Baseline Facts

- historical pre-tranche recount moved from `160 -> 159` direct methods with `3 -> 2` `180+ LOC` and `6 -> 5` `120+ LOC` hotspots when the first post-select extraction landed
- current live recount is now `166` direct methods with `2` `180+ LOC` and `5` `120+ LOC` hotspots, so the lane remains open and the older `159` recount should be treated as a historical tranche anchor rather than current truth
- Existing extracted siblings already exist, and this tranche adds:
  - `Stage4DirectorRuntime`
  - `Stage4PostSelectRuntime`
  - `Stage4RejectRuntime`
  - `Stage4RetryRuntime`
- The remaining heavy families still concentrated in the owner are:
  - director gate normalization / pass-with-fix shaping
  - episode-log / attempt / sink payload assembly
- the landed post-select extraction confirms this is best treated as a `module boundary / owner-surface reduction` lane, not as incremental helper growth inside the same file
- the later helper-heavy contract/raw-evidence work improved auditability but did not solve owner pressure; the lane should therefore remain proof-deferred and avoid pretending that helper growth itself closed the structure problem

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- any new Stage4 boundary module created specifically to reduce `Stage4InterviewRound` owner pressure
- targeted Stage4 contract/regression tests for the extracted families

Excluded:

- current front functional Stage4 consumer fixes
- repair-contract behavior changes
- non-wuxia Stage4 continuity normalization
- Stage2 / Stage3 upstream refactors
- DB schema redesign
- broad prompt redesign

## 4. Pass 1. Inventory Summary

Primary owner inventory:

1. owner shell
   - `stage4_interview_round.py`
2. existing extracted runtime siblings
   - `stage4_director_runtime.py`
   - `stage4_postselect_runtime.py`
   - `stage4_reject_runtime.py`
   - `stage4_retry_runtime.py`
3. high-risk regression surfaces
   - `tests/test_stage4_interview_round.py`
   - `tests/test_stage4_lane2_binding_contract.py`
   - `tests/test_stage4_advisory_escalation_seam.py`

Primary debt inventory:

1. post-select handling was the leading owner hotspot and is now the first landed extraction tranche
2. gate semantics normalization still mixes contract logic, fallback rules, and mutation wiring in one owner method
3. episode-log / sink payload assembly still sits as a long owner-local serialization family
4. the existing runtime helper extraction pattern remains the right direction for the remaining owner pressure

## 5. Pass 2. Semantic Classification

### Class A. Primary extraction families

- landed in this tranche: `_run_post_select_checks` -> `Stage4PostSelectRuntime`
- next primary family: `_normalize_director_gate_semantics`
- next primary family: `_append_episode_log`

### Class B. Secondary extraction / cleanup support

- `post-select` history readback / helper migration that naturally moves with the new boundary owner
- `_backfill_strong_advisory_fix_pack`
- `_build_retry_feedback_provenance`
- adjacent payload builders and trace helpers that naturally move with the extracted family

### Class C. Explicitly deferred outside this lane

- live behavior changes
- sink contract reinterpretation
- Stage4 queue reprioritization above active functional items
- same-file helper multiplication as a substitute for boundary extraction

## 6. Realization Architecture

This lane should be realized as owner-surface reduction, not cosmetic cleanup.

Preferred direction:

- keep `Stage4InterviewRound` as the coordinator shell
- move one family at a time behind explicit boundary owners
- freeze behavior with targeted tests before each extraction tranche
- recount direct-method and long-function pressure after the extraction wave

Implementation rule:

- prefer new module boundaries over adding more same-file helpers to an owner already above the pressure line

## 7. Execution Tranches

1. contract freeze and owner map
   - landed with focused regression freeze around post-select downgrade, retry-round reuse, and positive-verdict transition routing

2. post-select boundary extraction
   - landed: `stage4_postselect_runtime.py` now owns post-select conflict collection, history readback, and downgrade payload assembly
   - `Stage4InterviewRound` now delegates to the new boundary owner and no longer owns `_run_post_select_checks` / `_build_manuscript_history_for_check`

3. gate-semantics boundary extraction
   - move pass-with-fix / authoritative-scope normalization into a dedicated boundary owner

4. attempt-log boundary extraction
   - move episode-log / attempt payload assembly out of the owner shell

5. recount and closure
   - focused recount / validation landed for this tranche
   - full lane closure still waits on later extraction tranches or an explicit proof-first decision

## 8. Acceptance Criteria

- no new `180+ LOC` function is introduced
- at least one current `180+ LOC` hotspot is reduced below `180 LOC` or moved out of `Stage4InterviewRound`
- later closure should demonstrate a real reduction from the current live `166` direct-method reality rather than citing only the historical `160 -> 159` tranche anchor
- extracted families have explicit owner boundaries rather than same-file helper sprawl
- targeted Stage4 regressions pass without semantic drift
- current live complexity recount is recorded (`166` direct methods / `2` `180+ LOC` / `5` `120+ LOC`), while the earlier `159 / 2 / 5` remains a historical first-tranche anchor only

## 9. Verification Plan

- targeted Stage4 regression shards for the extracted family
- `pytest` on touched Stage4 contract files only, sequentially
- `python -m py_compile` on touched production modules
- `ruff check` on touched production/test files
- UTF-8 hygiene on touched docs/code
- post-change AST recount for:
  - direct method count
  - `120+ LOC` functions
  - `180+ LOC` functions

## 10. Guardrails

- do not activate this lane ahead of the active functional Stage4 pair
- do not activate this lane ahead of the currently pending functional Stage3/Stage0 waves without explicit reprioritization
- do not use same-file helper growth as the main realization strategy
- do not silently change verdict, retry, or sink semantics under the name of refactor
- keep behavior-preservation tests ahead of extraction work

## 11. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - keep the mirror while this remains a recognized partial structure lane
  - remove only on explicit closure, deactivation, or replacement
- roadmap dependency:
  - below the active Stage4 consumer / repair / non-wuxia lanes
  - below the broader pending functional waves
  - above soak-only reference lanes

## 12. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before any code refactor begins from this document

## 13. 3-Pass Audit Record

Pass 1, structure and scope:

- execution SSOT type is correct for an active partial structure lane
- the first bounded tranche stays limited to the post-select family and one new boundary module

Pass 2, evidence and consistency:

- historical pre-tranche recount confirmed `160` direct methods / `3` `180+ LOC` / `6` `120+ LOC`
- historical first-tranche recount confirmed `159` direct methods / `2` `180+ LOC` / `5` `120+ LOC`
- current live recount is `166` direct methods / `2` `180+ LOC` / `5` `120+ LOC`, so later closure should cite current proof-first reality rather than the older historical tranche count alone
- focused regression shards preserved post-select downgrade and positive-verdict transition behavior

Pass 3, execution and readability:

- boundary-first extraction landed without broad Stage4 logic rewrite
- the remaining gate/attempt families stay explicit rather than getting hidden behind same-file helper growth
- because this lane is no longer unopened, the next unopened code lane now moves to `stage0-treatment-enrich-retirement-remediation`

Confidence: `97%`

