## Why Fix Pack Is Empty Full Survey Audit Order

Date: 2026-03-28
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: why-fix-pack-is-empty

### 1. Goal

Run a bounded system-track survey on the Stage 4 `fix_pack` lifecycle before any new code changes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`Where exactly does fix_pack become empty, and is the recent contract-hardening / harness-like shift the cause or only the thing that exposed a pre-existing empty-fix-pack failure family?`

This survey exists because recent live canary evidence suggests:

- `score=50` can plateau for many rounds with `fix_pack_reason=missing_fix_pack`
- `TF-PATCH-GATE` now blocks fake patch lanes correctly, but the upstream `fix_pack` still remains empty
- IFC and plateau warnings can accumulate without a concrete repair scope change
- the latest canary shows `rewrite` replacing `patch_revision`, but not escaping the same failure family
- there is user concern that the recent Python-first to more contract-centered or harness-like transition may have changed causality, not just observability

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-28/why-fix-pack-is-empty-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py`
- live canary evidence under:
  - `projects/canary_0328_stage4_ifc_bridge_check/logs/`
  - `projects/canary_0328_golden_new2_s4/logs/`
  - inspect raw artifacts where present:
    - `episode_production.jsonl`
    - `runtime_audit.jsonl`
    - `session/decisions.jsonl`
    - `session/llm_io.jsonl`
    - `session_*.log`
- earlier Stage 4 canary evidence only as support, not as sole truth
- already-saved bounded survey context only as support:
  - `docs/2026-03-28/stage4-target-locked-patch-lane-full-survey.md`
  - `docs/2026-03-28/stage4-ifc-bridge-full-survey.md`

Excluded surfaces:

- Stage 2 and Stage 3 redesign
- broad Stage 4 retry-policy redesign
- blueprint generator redesign
- provider abstraction redesign
- narrative quality diagnosis outside the `fix_pack` lifecycle question
- execution SSOT authoring

### 4. Survey Questions

The survey must answer all of these.

1. End-to-end lifecycle truth
- Where is raw `fix_pack` first produced?
- Where is it normalized?
- Where is it evaluated for readiness?
- Where is it copied, downgraded, discarded, or rebuilt?
- Where is `missing_fix_pack` decided?

2. Empty-state origin truth
- In the failing canary lane, is `fix_pack` empty because:
  - Director never emitted usable `fix_pack`
  - Director emitted something but `_normalize_fix_pack()` stripped it
  - Stage 4 gate normalization or carryover removed it
  - retry routing only observed the emptiness after the fact
- The survey must separate these causes explicitly.

3. Contract-vs-causality truth
- Did the recent fail-closed or harness-like contract changes create this failure family?
- Or did they only expose a pre-existing upstream empty-fix-pack defect that fake patch lanes used to mask?
- Do not answer by intuition.
- Answer by line-level flow and, where possible, by test and canary evidence.

4. Valid-empty-vs-bug-empty truth
- In which cases is empty `fix_pack` actually legitimate?
- In which cases is empty `fix_pack` likely a bug or contract collapse?
- Does the current canary lane look like:
  - a legitimate "Director found no local patch scope" case
  - a normalization loss case
  - a classification mistake where local-fixable issues are being treated as generic quality rejection

5. Minimal safe next step
- What is the smallest safe bounded move after the survey?
- Rank only bounded options, not broad redesign.
- Explicitly state whether the first move should be:
  - `director-output / schema tightening`
  - `normalize_fix_pack contract adjustment`
  - `Stage4 carryover preservation fix`
  - `reject-classification correction before fix_pack creation`
  - `accept empty fix_pack as legitimate and move focus to escalation`

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. End-to-End Fix-Pack Lifecycle Map
4. Director Output Truth
5. Normalization and Contract Filtering Truth
6. Canary Failure Interpretation
7. Harness-Shift Causality Assessment
8. Root-Cause Candidates Ranked
9. Recommended Bounded Next Step
10. Open Questions
11. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When using fresh canary evidence:

- distinguish what was actually flushed to artifacts from what only appeared in live console monitoring
- distinguish `patch lane bug fixed` from `upstream fix_pack still empty`
- do not overclaim `10 rounds -> SKIP` if the run was killed before terminal flush

When using historical or prior canary evidence:

- treat it as supporting pattern evidence
- do not let it override the fresh canary on the exact empty-fix-pack question

When discussing recent contract-hardening or harness-like changes:

- do not say "the harness caused it" unless the survey finds a line-level causal path
- do not say "the harness is unrelated" unless the survey proves the empty-fix-pack path existed independently

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a full Stage 4 redesign survey.

Do not default to blueprint escalation as the answer.
This survey is about `why fix_pack is empty`, not about choosing the next escalation lane.

Do not treat every empty `fix_pack` as a bug.
The survey must explicitly distinguish:

- legitimately absent local-fix scope
- invalid or malformed Director payload
- normalization loss
- Stage 4 carryover loss
- post-change observability that merely exposed an older defect

Do not conflate:

- `PASS_WITH_FIX` eligibility failure
- generic `QUALITY_ISSUE`
- IFC advisory presence
- empty `fix_pack`

Those may correlate, but they are not the same claim.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest next move is:

`trace the empty-fix-pack origin precisely before any more canaries or escalation logic changes`

Do not force that conclusion if evidence contradicts it.
But do test it directly against the inspected code and canary artifacts.

### 9. Handoff Rule

After saving the draft survey doc, stop.

Do not audit it.
Do not produce execution docs.
Do not patch code.

The next step will be:

1. internal 3-pass audit of the draft survey
2. bounded execution SSOT creation
3. only then code changes
