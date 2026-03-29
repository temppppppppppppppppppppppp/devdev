## Stage4 Blueprint Frontier Patch Trigger Semantics Full Survey Audit Order

Date: 2026-03-29
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-blueprint-frontier-patch-trigger-semantics

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty tracked drift in stage4/provider/runtime/tests plus temp queue, canary artifacts, and narrative assets; retry-loop-compression live validation is complete and scope-sink semantics is the current adjacent semantics lane`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

### 1. Goal

Run a bounded system-track survey on the Stage 4 `blueprint/frontier patch trigger semantics` problem before any new escalation or patch-trigger changes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`When Stage 4 encounters continuity-firewall or related structural reject families, what exact runtime conditions trigger blueprint/frontier patch behavior versus another manuscript retry, and where is that trigger contract authoritative today?`

This survey exists because current evidence suggests:

- recent clean Gemini canaries showed a major improvement on one previously expensive family
- EP3 compressed from 8 rounds to 2 rounds, with the decisive step described as `V75-D inplace blueprint patch`
- this implies the current bottleneck may no longer be carryover visibility, but rather:
  - when a manuscript problem is reclassified into a blueprint/frontier problem
  - which runtime contract triggers that transition
  - whether the trigger is stable, explainable, and operator-readable

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-29/stage4-blueprint-frontier-patch-trigger-semantics-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_orchestrator.py`
- any helper directly linked from those files that decides:
  - `continuity_firewall`
  - `blueprint_regenerated`
  - `repair_scope`
  - `fix_scope`
  - V75-family blueprint/frontier patching
- targeted tests as support:
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_orchestrator.py`
  - any V75-D or blueprint-patch specific tests if present
- live evidence as support:
  - `projects/canary_0329_feedback_windowing_check/logs/`
  - `projects/canary_0329_retry_loop_compression_check/logs/`
  - `projects/canary_0329_scope_sink_semantics_check/logs/` only if relevant
- prior bounded context only as support:
  - `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`
  - `docs/2026-03-29/stage4-scope-sink-semantics-full-survey.md`
  - `docs/2026-03-29/stage4-carryover-contract-consumption-full-survey.md`

Excluded surfaces:

- provider-default work
- fallback observability work
- broad scope-sink redesign
- narrative-pipeline artifacts
- broad blueprint authoring redesign
- execution SSOT authoring
- code changes

### 4. Survey Questions

The survey must answer all of these.

1. Trigger truth
- What exact conditions trigger blueprint/frontier patch behavior today?
- Is the trigger keyed by:
  - gate family
  - score band
  - contradiction bucket streak
  - continuity-firewall family
  - blueprint_regenerated state
  - another hidden latch
- Which function is authoritative for that trigger?

2. Lane truth
- Once the trigger fires, what lane actually changes?
- Does the system:
  - patch blueprint/frontier only
  - keep manuscript lane but alter upstream substrate
  - perform both in one round
- Which fields expose that transition to operators?

3. Ownership truth
- Which parts are Director-authored versus runtime-derived?
- Is blueprint/frontier patching:
  - a runtime policy contract
  - a Director signaled lane
  - an orchestrator escalation
  - a mixed path across modules

4. Stability truth
- Is the V75-D style transition deterministic enough to treat as a reusable contract?
- Or was the 8R -> 2R case merely one successful opportunistic path with weak generality?
- Which evidence supports reuse versus one-off luck?

5. Smallest safe next move
- After the survey, what is the smallest safe next move?
- Rank only bounded options such as:
  - documenting the trigger semantics only
  - surfacing missing operator metadata
  - tightening one trigger precondition
  - adding one explicit transition marker
  - no code change because current trigger is already sound

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Trigger Ownership Map
4. Gate-to-Blueprint/Frontier Transition Matrix
5. Live Canary Evidence
6. Root-Cause Assessment
7. Highest-Risk Operator Misreads
8. Bounded Remediation Options Ranked
9. Recommended Bounded Next Step
10. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When discussing trigger semantics:

- distinguish manuscript retry from blueprint/frontier patch behavior
- distinguish trigger conditions from post-trigger side effects
- distinguish Director-authored signal from runtime-derived escalation
- do not infer a trigger merely from a canary summary line unless code and raw rows support it

When using live canaries:

- prefer raw rows from `episode_production.jsonl`, `runtime_audit.jsonl`, and `ui_events.jsonl`
- treat prose summaries as secondary
- label inference explicitly if the exact V75-D handoff is not directly visible in a single sink

When discussing success:

- do not assume `8R -> 2R` proves a general rule by itself
- explicitly separate:
  - proved contract behavior
  - plausible but not yet generalized behavior

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a broad Stage 4 redesign survey.

Do not reopen:

- provider-default work
- fallback observability work
- feedback-windowing work
- carryover consumption redesign
- broad scope-sink semantics redesign

unless inspected code proves a direct dependency on blueprint/frontier trigger behavior.

Do not recommend Python-side story judgment changes.
Do not recommend forcing blueprint patch merely to reduce round count.
This survey is about `trigger semantics`, not blunt compression.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest first move is:

`freeze one explicit trigger matrix for when continuity-firewall or adjacent structural families move from manuscript retry into blueprint/frontier patch behavior, so future canaries and operators can distinguish a true upstream substrate correction from another ordinary retry`

Do not force that conclusion if evidence contradicts it.
But do test it directly against the inspected code and raw canary artifacts.

### 9. Handoff Rule

After saving the draft survey doc, stop.

Do not audit it.
Do not produce execution docs.
Do not patch code.

The next step will be:

1. internal 3-pass audit of the draft survey
2. bounded execution SSOT creation if ROI is still high
3. only then code changes
