## Stage4 Firewall Family Delta Full Survey Audit Order

Date: 2026-03-29
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-firewall-family-delta

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty tracked drift in stage4/provider/runtime/tests plus temp queue, canary artifacts, and narrative assets; EP3 blueprint patch recheck canary is currently the active live comparison lane`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

### 1. Goal

Run a bounded system-track survey that builds the `pre-patch firewall family baseline` for EP3 before the patched EP3 canary finishes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`What exact reject-family fingerprints defined the old EP3 failure pattern before the blueprint/frontier patch, so that the new EP3 canary can be judged against a stable before-baseline instead of vague memory?`

This survey exists because current evidence suggests:

- the main question is now `did the EP3 BP patch remove the old family?`
- that comparison is much easier if the old family is frozen explicitly
- current prose shorthand such as:
  - `자금 확보 재수행`
  - `완료사건반복`
  - `확정상태회귀`
  - `opening-ending mismatch`
  is useful, but not yet normalized into a single baseline matrix

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-29/stage4-firewall-family-delta-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- pre-patch EP3 evidence only
- primary live evidence sources:
  - `projects/canary_0329_feedback_windowing_check/logs/`
  - `projects/canary_0329_scope_sink_semantics_check/logs/`
  - any immediately prior EP3 canary logs that still reflect the unpatched BP state
- raw sinks:
  - `logs/session/decisions.jsonl`
  - `logs/episode_production.jsonl`
  - `logs/runtime_audit.jsonl`
  - `logs/session/ui_events.jsonl`
- supporting code only as needed to interpret fingerprints:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_outcome_runtime.py`
  - `modules/core/stage4_reject_runtime.py`

Excluded surfaces:

- patched EP3 canary as primary evidence except for naming alignment
- provider-default work
- fallback observability work
- carryover consumption redesign
- blueprint/frontier trigger redesign
- code changes

### 4. Survey Questions

The survey must answer all of these.

1. Old family truth
- What exact EP3 reject families appeared before the BP patch?
- Distinguish at minimum:
  - `continuity_firewall`
  - `post_select_conflict`
  - `director_primary_reject`
  - any `constraint_violation` or `logic_error` overlays

2. Fingerprint truth
- For each old family, what raw signals consistently co-occurred?
- Extract actual combinations of:
  - `gate_basis`
  - `reject_bucket`
  - `contradiction_type`
  - `fix_scope`
  - `authoritative_fix_scope`
  - `repair_scope`
  - `fix_pack_reason`
  - `fix_scope_reasoning`
  - key reject reason phrases

3. Narrative truth
- Which old families corresponded to actual BP conflict themes such as:
  - capital acquisition repeated
  - trust liquidation / cash conversion repeated
  - OTP / legal entity / account setup repeated
  - EP2 study / office / paternal surveillance scene replay
  - opening-end mismatch or completed-event replay

4. Comparison truth
- Which 3-6 baseline fingerprints should the patched EP3 canary be compared against?
- Reduce the baseline to a compact operator-facing family list that can support:
  - `old family removed`
  - `old family weakened`
  - `old family renamed but still present`
  - `new family introduced`

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Pre-Patch EP3 Round Map
4. Old Firewall/Post-Select Family Matrix
5. Narrative Conflict Theme Map
6. Baseline Comparison Set
7. Highest-Risk False Comparisons
8. Recommended Comparison Rule For Patched Canary
9. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When building the baseline:

- prefer raw rows over summary prose
- do not mix patched and unpatched EP3 evidence
- separate `gate family` from `theme interpretation`
- preserve exact field values before collapsing them into operator shorthand

When naming conflict themes:

- distinguish observed raw fingerprint from interpreted narrative label
- label inference explicitly if a theme name is derived from reason text rather than a first-class field

Do not conclude whether the patch succeeded yet.
This survey is only the `before` baseline.

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a broad Stage 4 redesign survey.

Do not reopen:

- provider-default work
- fallback observability work
- broad scope-sink semantics
- broad retry-loop redesign
- blueprint/frontier trigger redesign

unless directly required to decode a field in the old EP3 baseline.

### 8. Preferred Operating Conclusion

The survey should aim to determine:

`the smallest stable old-family baseline that lets operators judge the patched EP3 canary by exact fingerprint deltas instead of vague prose similarity`

Do not force that conclusion if evidence contradicts it.
But do test it directly against the inspected logs.

### 9. Handoff Rule

After saving the draft survey doc, stop.

Do not audit it.
Do not produce execution docs.
Do not patch code.

The next step will be:

1. read patched EP3 canary result
2. compare it against this baseline
3. only then decide whether further BP/frontier work or runtime work is needed
