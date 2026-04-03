# 0_0 Stage4 NpcDrift Relation-Tag Semantic LocalFix Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (code landed, static validation closed, and bounded runtime positive proof captured; no longer the immediate active Stage4 blocker)
Canonical Path: `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: models config changed, active Stage4 docs/tests/code deltas, temp roadmap/queue active, 2026-04-02 survey bundles present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `relation-tag semantic bridge and zero-to-local fix synthesis landed; the r2 Stage4-only sinkproof canary captured positive runtime proof and removed NpcDrift as the immediate live blocker, the later analyzer/readback backfill closed the metadata/sink hygiene gap, and the broader consumer wave now narrows to residual replay quality plus patch-trace observability`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-audit.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-evidence.json`
- `docs/2026-04-02/0_0-stage4-episode-bounded-canary-runtime-evidence.json`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`
Parent Lane:
- `0_0-stage4-consumer-contract-normalization-remediation`
- `0_0-stage2-stage3-stage4-readiness-remediation`

## 1. Answer First

The next bounded Stage4 lane should target one concrete ep2 blocker:

- `NpcDrift relation_to_protag` is persisted as a compressed canonical tag like `집착100/오해-80`
- `NpcDriftAdvisor` compares manuscript prose against that compressed expectation without a semantic-expansion bridge
- when drift escalates, runtime cannot synthesize a fresh local `fix_pack` from advisory-only relation-tag evidence

This is not a Stage2 issue, not a Stage3 issue, and no longer the highest-authority immediate Stage4 blocker after the `r2` Stage4-only sinkproof runtime proof.

It remains a bounded `Stage4 NpcDrift semantic-equivalence + local-fix contract` lane, but it now sits as a runtime-positive substrate/reference seam under the broader Stage4 consumer wave rather than the next live blocker.

## 2. Scope

Included:

- `modules/core/npc_drift_advisor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/world_state.py`
- focused Stage4/NpcDrift regression tests
- roadmap/temp queue refresh

Excluded:

- broad NpcDrift rewrite across every subtype
- Stage2 contract normalization
- Stage3 contract tightening realization
- fresh canary in this document
- Stage4 resume declaration
- DB schema redesign
- artifact rewrites in `projects/`

## 3. Execution Tranches

### Tranche 1. Relation-Tag Semanticization Contract

Goal:

- stop treating compressed relation tags as raw literal expectations during prose-vs-canon drift checking

Bounded targets:

- `npc_drift_advisor.py`
- `stage4_post_pass_runtime.py`
- `world_state.py`

Acceptance shape:

- `relation_to_protag` can retain compressed numeric authority if needed
- but advisory comparison gains a semantic bridge:
  - semantic alias
  - range-class expansion
  - or equivalent bounded normalization
- manuscript prose no longer has to mirror the exact compressed tag surface form to avoid drift

### Tranche 2. Subtype-Aware Strong-Advisory Policy

Goal:

- split `npc_drift` handling so `relation_to_protag` compressed-tag cases are not treated identically to harder structural drifts like role/location/injury contradictions

Bounded targets:

- `stage4_interview_round.py`
- `npc_drift_advisor.py`

Acceptance shape:

- `relation_to_protag` drift keeps strong coverage when clearly contradictory
- but the policy can distinguish:
  - semantic-paraphrase mismatch
  - true relation contradiction
- advisory severity remains bounded and Director authority remains intact

### Tranche 3. Zero-to-Local-Fix Synthesis For Relation-Tag Drift

Goal:

- when the only blocker is a locally repairable relation-tag drift, synthesize a bounded local repair contract instead of collapsing into `strong_advisory_escalation_non_local_fix`

Bounded targets:

- `stage4_interview_round.py`

Acceptance shape:

- advisory-only relation-tag drift can produce bounded:
  - `patch_targets`
  - `must_fix`
  - `success_condition`
- the path remains local and bounded
- no `scene_model` or broad rewrite leakage

### Tranche 4. Focused Regression Closure

Goal:

- add only the regressions required to lock the three contracts above

## 4. Non-Goals

- no broad Stage4 redesign
- no global NpcDrift taxonomy rewrite
- no Stage2/3 reopen
- no canary execution in this document
- no `resolved` or `resume-ready` declaration

## 5. Acceptance Criteria

- `relation_to_protag` compressed-tag drift no longer depends on raw literal tag matching alone
- advisory comparison can distinguish semantic paraphrase from true contradiction for this subtype
- relation-tag drift can synthesize a bounded local fix contract when Director did not already provide one
- existing strong fail-close behavior remains for non-local or structurally unsafe NPC drift cases
- no new `180+ LOC` production function is introduced

## 6. Verification Plan

- `pytest tests/test_stage4_advisory_escalation_seam.py -k "npc_drift or relation" -q`
- `pytest tests/test_stage4_interview_round.py -k "npc_drift or strong_advisory" -q`
- targeted NpcDrift/world-state regressions if new files are added
- `ruff check modules/core/npc_drift_advisor.py modules/core/stage4_interview_round.py modules/core/stage4_post_pass_runtime.py modules/core/world_state.py tests/test_stage4_advisory_escalation_seam.py tests/test_stage4_interview_round.py`
- `python -m py_compile modules/core/npc_drift_advisor.py modules/core/stage4_interview_round.py modules/core/stage4_post_pass_runtime.py modules/core/world_state.py`
- `python scripts/check_utf8_hygiene.py docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md docs/temp/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md docs/2026-04-01/active-temp-execution-roadmap.md docs/temp/execution-roadmap.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 7. Guardrails

- keep `Stage4` paused
- keep this lane bounded to `relation_to_protag` compressed-tag semantics
- do not widen this into all `npc_drift` categories unless runtime evidence later requires it
- preserve Director final authority
- preserve fail-close semantics for truly non-local NPC contradictions

## 8. Temp Queue Notes

- temp status: `partial`
- cleanup condition:
  - keep the temp mirror while this remains a referenced bounded substrate lane under the aggregate Stage4 consumer-contract wave
- roadmap dependency:
  - this lane now sits below the aggregate Stage4 consumer wave as a runtime-positive substrate/reference seam
  - `r2` Stage4-only sinkproof proved the lane is no longer the immediate live blocker
  - the next bounded consumer-side follow-up is now replay/repetition plus patch-trace observability in the existing post-select, flashback, and fix-pack family

## 9. 3-Pass Audit Record

Pass 1, structure and scope:

- bounded the lane to the concrete ep2 NpcDrift blocker
- kept Stage2/3 and broad NpcDrift redesign out of scope

Pass 2, evidence and consistency:

- runtime canary blocker matches the survey root-cause chain
- code-path claims align with `world_state`, `post_pass`, `NpcDriftAdvisor`, and Stage4 escalation logic
- lineage to the aggregate Stage4 contract wave is explicit
- 2026-04-03 runtime closure update adds positive Stage4-only proof that the seam no longer blocks convergence in the current ep2 canary

Pass 3, execution and readability:

- tranches are subtype-bounded and code-owner aligned
- operator consequence is clear: semantic bridge plus local-fix synthesis for one subtype
- runtime proof is now explicitly captured as bounded positive evidence, while broad Stage4 closure remains deferred

Confidence: `96%`
