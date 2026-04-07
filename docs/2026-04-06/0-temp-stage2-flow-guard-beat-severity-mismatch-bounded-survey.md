# 0 Temp Stage2 Flow Guard Beat Severity Mismatch Bounded Survey

Date: 2026-04-06
Status: final
Mode: read-only bounded survey
Scope: `0_temp.txt` evidence plus live Stage2 code/tests for the `Flow Guard` vs `beat_sequence` severity mismatch
Canonical Path: `docs/2026-04-06/0-temp-stage2-flow-guard-beat-severity-mismatch-bounded-survey.md`
Primary Evidence:
- `0_temp.txt`
- `modules/core/stage2_validation_pipeline.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_stage2_preflight_helpers.py`
Related Docs:
- `docs/2026-04-06/0-temp-stage2-other-issues-bounded-survey.md`
- `docs/2026-04-06/00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
- Baseline Dirty Summary: `dirty: active Stage2/Stage234 code changes and 2026-04-06 docs remain uncommitted; temp queue remains active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## Findings First

### F-1. The mismatch is real: Python says `CRITICAL`, Director says the issue is structurally thin but not substantively fatal

Direct log evidence from `0_temp.txt`:

- line 535: `Flow Guard` emits `서사 폭주 위험: 비트 수가 화수보다 부족`
- line 542-543: Director says Python raised a `CRITICAL` issue because the `회차별 비트` field was empty, but the tactical document already contains a clear five-episode narrative structure, so it is not treated as a substantive defect

This is not the same as the known non-wuxia state-lock issue.

It is a separate mismatch between:

- Python structural completeness checks on `beat_sequence`
- Director semantic judgment on whether the arc already has usable narrative structure in prose

### F-2. The narrowest owner is Stage2 validation, not the Director and not Stage4

The core logic lives in `modules/core/stage2_validation_pipeline.py`.

Relevant behavior:

- line 1293-1304: if `beat_sequence` count is below `ep_count`, `_stage2_flow_guard()` returns `REJECT`
- line 1317-1327: if normalized beat text is too sparse, `_stage2_flow_guard()` returns `REJECT`
- line 1338-1367: title-only or over-condensed beats also return `REJECT`
- line 545-612: `run_validation()` converts any `Flow Guard REJECT` into a Python advisory with fixed `severity = "CRITICAL"`

That means multiple structurally different cases:

- missing beats
- empty beats
- title-only beats
- condensed beats

all collapse into the same severity tier once they pass through the advisory wrapper.

### F-3. Current tests codify advisory conversion, but not severity discrimination

Evidence from tests:

- `tests/test_stage2_validation_pipeline.py:123-131` asserts under-filled or short `beat_sequence` returns `REJECT`
- `tests/test_stage2_validation_pipeline.py:223-232` asserts a `Flow Guard REJECT` becomes an advisory and processing still `proceed`s
- `tests/test_stage2_preflight_helpers.py:655-673` repeats the same contract at orchestrator/preflight level

What is missing in tests:

- no test distinguishes `CRITICAL` structural collapse from a merely incomplete `beat_sequence`
- no test encodes a case where prose structure is semantically sufficient while beat metadata is sparse
- no test proves that a beat-field gap should downgrade to `MAJOR`, `WARNING`, or metadata-only advisory instead of fixed `CRITICAL`

### F-4. The issue fits the existing Stage2 SSOT better than a new lane

The active Stage2 SSOT already says:

- `beat_sequence` is a field that needs explicit keep-or-drop policy
- Stage2 has contract fragility around structured packet authority

This `Flow Guard` mismatch belongs inside that same backlog because the real question is:

- should `beat_sequence` remain a hard structural contract
- or should it become a lower-authority metadata surface when `tactical_doc` and `episode_details` already carry the narrative truth

That is a Stage2 contract-normalization question, not a Stage4 consumer question and not a new Stage234 lane.

### F-5. Best current reading: severity inflation, not false data fabrication

The survey does **not** prove that `Flow Guard` fabricated a nonexistent problem.

The more careful reading is:

- the beat metadata was genuinely thin or empty
- Python correctly noticed that
- but the current severity mapping likely overstates the operational importance of that defect when prose structure already passes Director review

So this is not:

- "Flow Guard is wrong"

It is:

- "Flow Guard may be right about missing metadata but too aggressive in how that metadata gap is escalated"

## Evidence Map

### Log-side evidence

`0_temp.txt`

- 535: `🚨 [Flow Guard] 서사 폭주 위험: 비트 수가 화수보다 부족`
- 542: Director says Python raised a `CRITICAL` issue because `회차별 비트` is empty
- 543: Director explicitly says the tactical document already includes clear five-episode narrative structure

### Code-side evidence

`modules/core/stage2_validation_pipeline.py`

- 1292-1304: `beat_count` path returns `REJECT`
- 1317-1327: `empty_beats` path returns `REJECT`
- 1338-1367: `beat_condensed` path returns `REJECT`
- 606-611: advisory sink uses fixed `severity: "CRITICAL"`

### Test-side evidence

`tests/test_stage2_validation_pipeline.py`

- 123-131: under-filled or short beats reject
- 223-232: Flow Guard reject becomes advisory and pipeline still proceeds

`tests/test_stage2_preflight_helpers.py`

- 655-673: same advisory-conversion contract at preflight level

## Answers To The Key Questions

### Q1. Is this a real issue or just log noise?

Real issue.

The log shows a concrete mismatch between structural severity and semantic severity, not random noise.

### Q2. What is the narrowest owner set?

Primary owner:

- `modules/core/stage2_validation_pipeline.py`

Secondary owner:

- the existing Stage2 contract policy around `beat_sequence`

Not primary owners:

- Director
- Stage4
- the non-wuxia Stage234 lane

### Q3. Does this justify a new execution lane?

No.

This should be folded into the existing `0_0-stage2-contract-normalization-remediation` SSOT as a residual Stage2 policy seam.

### Q4. What would the future bounded patch shape probably look like?

Not a broad rewrite.

The likely bounded shapes are:

1. separate `beat_count` / `empty_beats` / `beat_condensed` severity tiers
2. downgrade some beat-field failures when prose structure already supplies equivalent narrative truth
3. make `beat_sequence` keep-or-drop policy explicit relative to `tactical_doc` and `episode_details`

This survey does not authorize any of those patches. It only classifies the seam.

## Queue Consequence

No new temp execution item.

No roadmap change.

Recommended routing:

- keep this as supporting evidence under `0_0-stage2-contract-normalization-remediation`

## Boundaries

- no code changes
- no `docs/temp` mutation
- no queue mutation
- no claim that every Flow Guard reject is overstated

The bounded claim is:

- at least one real run shows `beat_sequence` metadata weakness being escalated as `CRITICAL` even though Director semantic review treats the arc structure as substantively acceptable

## 3-Pass Audit Record

Pass 1, structure and scope:

- kept the document narrowly on `Flow Guard` and beat metadata severity
- excluded Stage4 and excluded broader non-wuxia continuity issues

Pass 2, evidence and consistency:

- triangulated the same seam across log, production code, and tests
- avoided claiming a false-positive where the evidence only supports severity inflation

Pass 3, execution and readability:

- gave a clear owner map and queue consequence
- kept the result survey-only and folded into an existing Stage2 lane instead of inventing a new one

Final confidence: `96%`

Final save approved.
