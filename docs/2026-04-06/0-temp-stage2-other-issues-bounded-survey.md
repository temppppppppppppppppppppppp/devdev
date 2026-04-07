# 0 Temp Stage2 Other Issues Bounded Survey

Date: 2026-04-06
Status: final
Mode: read-only bounded survey
Scope: `0_temp.txt` triage for additional Stage2-visible issues beyond the already-known non-wuxia `V60.10 STATE LOCK` overreach
Canonical Path: `docs/2026-04-06/0-temp-stage2-other-issues-bounded-survey.md`
Primary Evidence:
- `0_temp.txt`
Related Existing Docs:
- `docs/2026-04-06/00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md`
- `docs/2026-04-06/00_골든-stage2-terminal2-arc5-entity-reject-and-retry.md`
- `docs/2026-04-06/00_골든-stage2-terminal3-observability-and-owner-map.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
Commit State:
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
- Baseline Dirty Summary: `dirty: active Stage2/Stage234 code changes and 2026-04-06 docs remain uncommitted; temp queue and roadmap remain active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## Findings First

### F-1. Yes, `0_temp.txt` contains other real issues besides the known state-lock case

Direct evidence in `0_temp.txt` shows four additional issue families:

1. numeric arithmetic drift in Arc 3 and Arc 4
2. Arc 5 entity-name reject and retry
3. repeated `Patch pressure exceeded -> advisory only, PASS 유지`
4. a `Flow Guard` severity mismatch tied to an empty `beat_sequence`-style field

However, only one of these currently looks like a likely under-documented residual seam. The others are already covered by existing 2026-04-06 Stage2 surveys or the active Stage2/Stage4 queue.

### F-2. Numeric arithmetic drift is real, but it is not a new queue item

High-signal lines from `0_temp.txt`:

- line 469-474: Arc 3 shows a half-sell arithmetic contradiction, then a `PASS_WITH_FIX` patch
- line 507-512: Arc 4 Director REJECT explicitly cites a severe mathematical contradiction
- line 545-547: Arc 4 later shows a second bounded total-assets mismatch, then another `PASS_WITH_FIX` patch

This is a real issue family, but it is already documented and routed:

- the Arc 3/4 run-specific analysis is already in `00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md`
- the broader numeric carryover authority owner is already the active `Stage4 consumer` lane in the roadmap
- the Stage2 side of numeric phrasing/arithmetic hardening is already reflected inside `0_0-stage2-contract-normalization-remediation-execution-ssot.md`

Bounded reading:

- this log confirms recurrence
- this log does not justify a new execution SSOT

### F-3. Arc 5 entity-name reject is real, but currently retry-only residue

High-signal lines from `0_temp.txt`:

- line 575-581: Director REJECT asks to normalize entity naming such as `블랙베리 -> 블랙베리 8700`, `법인 계좌 -> 법인 통장`, `후계 구도 -> 후계 다툼`
- line 578: `[Director REJECT] [V61] Entity 명칭 불일치 5건 발견`
- line 596: the next retry passes with score 100

This is not speculative. The log shows a real reject/retry cost.

But the current classification remains:

- real issue
- already documented in `00_골든-stage2-terminal2-arc5-entity-reject-and-retry.md`
- not the current front blocker
- no new queue promotion required from this log alone

### F-4. `Patch pressure exceeded` is repeated and meaningful, but still reads as a supporting signal, not a separate front lane

High-signal lines from `0_temp.txt`:

- line 477: `Patch pressure exceeded -> advisory only, PASS 유지`
- line 550: same message repeats

Why it matters:

- the system reaches `PASS_WITH_FIX`
- Director re-review passes
- but the patch application path still logs that the patch pressure threshold was exceeded, so the patch is treated as advisory-only

Why it is not promoted here:

- the same run still converges successfully by line 600-601
- the Arc 3/4 patch-pressure behavior is already documented in `00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md`
- the stronger remaining queue owners are still `Stage4 consumer`, `Stage4 repair`, and the already-active non-wuxia Stage234 lane

Bounded reading:

- this is real supporting evidence for patch-path ambiguity and operator observability debt
- it is not enough, by itself, to create a new execution doc today

### F-5. The only plausible under-documented residual from this log is `Flow Guard` severity inflation around empty beat fields

High-signal lines from `0_temp.txt`:

- line 535: `Flow Guard` reports `서사 폭주 위험: 비트 수가 화수보다 부족`
- line 542-543: Director explicitly says Python raised a `CRITICAL` issue because the `회차별 비트` field was empty, but rejects that as a substantive narrative problem because the tactical document already contains a clear five-episode structure

This matters because it shows a mismatch between:

- Python-side structural severity
- Director-side semantic severity

Current best reading:

- this is not a content failure
- this is not a front Stage4 issue
- this is a Stage2 contract/observability problem around `beat_sequence` or equivalent beat-field policy

Owner mapping:

- `modules/core/stage2_validation_pipeline.py`
- the existing `Stage2 contract normalization` lane, especially its dead-field keep-or-drop policy for `beat_sequence`

Queue consequence:

- keep it inside the existing `0_0-stage2-contract-normalization-remediation` SSOT
- do not create a separate temp execution item from this log alone

### F-6. The startup `VecMemory` warning is not promoted from this survey

High-signal lines from `0_temp.txt`:

- line 64-65: shared-mode `vec_episodes` table unavailable, vector engine disabled in that connection
- later lines 495, 528, 569: vector-search completion still appears during Stage2
- line 693: `VecMemory 연결 해제 완료`

Bounded reading:

- the startup warning is real
- but this specific log still shows retrieval activity later and the full Stage2 batch completes successfully
- from this evidence alone, it does not rise to a separate problem classification

## Issue Classification

| Issue Family | Evidence In `0_temp.txt` | Current Classification | Existing Owner / Doc | New Queue Item? |
| --- | --- | --- | --- | --- |
| Non-wuxia state-lock overreach | 505-516 | real, already promoted P1 | `0_0-stage234-nonwuxia-state-lock-overreach-remediation` | no |
| Numeric arithmetic drift | 469-474, 507-512, 545-547 | real, already documented | `00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md`; Stage4 consumer lane | no |
| Entity reject/retry | 575-581, 596 | real, retry-only residue | `00_골든-stage2-terminal2-arc5-entity-reject-and-retry.md` | no |
| Patch pressure exceeded | 477, 550 | real supporting signal | `00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md`; Stage2/Stage4 observability debt | no |
| Flow Guard beat-field severity inflation | 535, 542-543 | real residual candidate | `0_0-stage2-contract-normalization-remediation` | no, fold into existing SSOT |
| VecMemory shared warning | 64-65 | not promoted from this log | not enough evidence | no |

## Answers To The Practical Questions

### Q1. Are there other problems in `0_temp.txt`?

Yes.

The strongest additional issues visible in the log are:

- numeric arithmetic drift
- entity-name reject/retry
- repeated patch-pressure warnings
- Flow Guard severity inflation on empty beat metadata

### Q2. Which of those are actually new?

From this log alone, none of the first three look new.

- numeric drift is already documented
- entity reject/retry is already documented
- patch-pressure repetition is already documented as supporting evidence

The only bounded candidate that still looks under-documented is:

- Stage2 `Flow Guard` severity inflation when beat metadata is empty but the prose structure is still semantically coherent

Even that does not justify a new queue item. It fits the existing `Stage2 contract normalization` SSOT better than a fresh lane.

### Q3. Does this survey change the active roadmap order?

No.

The current queue remains coherent:

1. `Stage4 consumer`
2. `Stage4 repair`
3. `Stage234 non-wuxia state-lock overreach`
4. broader `Stage2 contract normalization`

This log adds support for the existing Stage2 residual lane, but does not outrank the active front pair or the already-promoted non-wuxia lane.

### Q4. What is the concrete next documentation consequence?

Use this survey as a triage summary only.

If the user later wants a deeper follow-up, the cleanest next bounded survey would be:

- a focused `Stage2 Flow Guard / beat_sequence severity mismatch` survey

That would still belong under the existing Stage2 SSOT unless it uncovers a materially larger owner set than the current evidence suggests.

## Boundaries

- no code changes
- no `docs/temp` mutation
- no roadmap mutation
- no execution SSOT promotion from this survey

The bounded claim is:

- `0_temp.txt` does show other real issue families
- most are already documented or already owned by active queue items
- the only likely under-documented residual is the Stage2 beat-field / Flow Guard severity mismatch

## 3-Pass Audit Record

Pass 1, structure and scope:

- kept the document bounded to `0_temp.txt` triage
- distinguished `new issue` from `already documented issue`
- kept execution and roadmap changes out of scope

Pass 2, evidence and consistency:

- all promoted findings are anchored to direct line-level evidence from `0_temp.txt`
- each issue family was checked against existing 2026-04-06 Stage2 docs and the active roadmap
- avoided promoting the startup `VecMemory` warning because the later same-session evidence does not support a blocking interpretation

Pass 3, execution and readability:

- findings lead with operator-relevant triage, not file dump
- queue consequence is explicit: no new execution item
- the one residual candidate is named concretely enough for a later focused survey if needed

Final confidence: `96%`

Final save approved.
