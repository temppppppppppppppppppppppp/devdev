## Stage4 Target-Locked Patch Lane Full Survey Audit Order

Date: 2026-03-28
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-target-locked-patch-lane

### 1. Goal

Run a bounded system-track survey on the Stage 4 patch lane before any new code changes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`Can Stage 4 be made safer and more deterministic by enforcing a target-locked patch contract before any escalation logic is expanded?`

This survey exists because recent canary evidence suggests:

- repeated `REJECT score=50` loops can continue without meaningful improvement
- `patch_revision` can activate even when `fix_pack` is empty or not contract-ready
- `patch_with_feedback` behaves more like bounded regeneration than true local editing
- `inplace_patch` now has a new deterministic local-op lane, but its integration role is not yet fully mapped
- provider-credit/fallback noise exists, so runtime evidence must be separated from contract logic failures

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-28/stage4-target-locked-patch-lane-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_policy_digest.py`
- `config/settings/stage4_policy_digest.json`
- `config/settings/validation.yaml`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_inplace_local_ops.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_chief_writer_inplace_local_ops.py`
- live canary evidence under:
  - `projects/canary_0328_golden_s4_shadow/logs/`
- historical canary evidence only as support, not as sole truth

Excluded surfaces:

- Stage 2 and Stage 3 broad redesign
- blueprint-generator redesign
- provider abstraction redesign
- full retry-policy replacement
- narrative material quality diagnosis outside Stage 4 patch lane

### 4. Survey Questions

The survey must answer all of these.

1. Patch lane routing truth
- Under exactly what conditions does Stage 4 choose:
  - `inplace`
  - `patch_revision`
  - `rewrite_regenerate`
  - escalation-oriented fallback
- Where does current routing allow `patch_revision` despite missing or non-ready `fix_pack`?

2. Fix-pack contract truth
- Where is `fix_pack` created, normalized, downgraded, or lost?
- Which contract checks are currently enforced?
- Which contract checks are only advisory?
- In the current code, what concrete paths lead to:
  - `missing_fix_pack`
  - `missing_patch_targets`
  - `missing_must_fix`
  - `missing_do_not_regress`
  - `missing_success_condition`

3. Patch semantics truth
- What does `ChiefWriter.inplace_patch(...)` actually do today?
- What does the new deterministic local-op lane do?
- What does `patch_with_feedback(...)` actually do today?
- Which paths are true local editing and which are constrained or bounded regeneration?

4. Failure classification truth
- For the observed Stage 4 retry failures, which ones are best classified as:
  - target-locked patch contract failures
  - patch-lane routing failures
  - blueprint/escalation candidates
  - provider-credit or fallback contamination
- Do not over-attribute a failure to blueprint if a strict local fact patch could plausibly solve it.

5. Minimal safe next step
- What is the smallest safe implementation move?
- The answer must rank only bounded options, not broad redesign.
- Explicitly state whether the first move should be:
  - `fail-closed patch lane gating`
  - `target-locked fix_pack contract strengthening`
  - `patch_with_feedback contract narrowing`
  - `earlier escalation`

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Current Routing Map
4. Fix-Pack Contract Truth Table
5. Patch Semantics Map
6. Failure Taxonomy
7. Live Canary Interpretation
8. Recommended Bounded Next Step
9. Open Questions
10. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When using live canary evidence:

- separate logic failure from provider failure
- do not claim a pure policy regression if provider-credit collapse materially contaminated the run
- do not dismiss the run entirely if it still exposes a valid contract bug

When using historical canary evidence:

- treat it as supporting distribution evidence
- do not let it override fresh live evidence about a concrete bug

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a full Stage 4 survey.

Do not default to "blueprint escalation" as the primary answer unless you prove that:

- target-locked local patching cannot solve the observed lane, and
- contract-correct patch routing would still fail for structural reasons

Do not call `patch_with_feedback` a real patch path unless the survey explicitly distinguishes:

- deterministic local edit
- constrained rewrite
- bounded regenerate

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest first move is:

`keep 10-round ceiling, but forbid fake patch lanes and strengthen target-locked obedience before touching escalation`

Do not force that conclusion if evidence contradicts it.
But do test it directly against the inspected code and logs.

### 9. Handoff Rule

After saving the draft survey doc, stop.

Do not audit it.
Do not produce execution docs.
Do not patch code.

The next step will be:

1. internal 3-pass audit of the draft survey
2. bounded execution SSOT creation
3. only then code changes
