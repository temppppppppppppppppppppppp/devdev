# Stage234 Baseline-Vs-Today Adversarial 3-Pass Audit

Date: 2026-04-12
Status: final
Canonical Path: `docs/2026-04-12/stage234-baseline-vs-today-adversarial-3pass-audit.md`
Doc Type: pre-run adversarial audit
Scope: same current dirty Stage2-Stage4 tranche versus baseline commit `2b7cb64f`, but evaluated from a skeptical "assume today's changes may be too much" viewpoint
Commit State:
- Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
- Baseline Dirty Summary: `dirty: 26 tracked, 2 untracked within audited S2-S4 tranche; broader workspace also has unrelated docs/material-side drift`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-12/stage234-baseline-vs-today-improvement-3pass-audit.md`
- `docs/2026-04-11/stage234-pre-fresh-run-global-parallel-3pass-audit.md`
Evidence Artifacts:
- same touched Stage2-Stage4 runtime files and tests listed in the improvement audit
Side-Effect Coverage: static code, sink, and targeted regression only; no runtime proof claimed

## 1. Question

If we assume today's tranche may have gone too far, what are the strongest reasons to distrust it before fresh run, and do any of those reasons outweigh the improvement claim?

## 2. Answer First

Adversarial answer:

- the tranche is **not yet safe to trust without fresh run**
- the tranche **does not justify rollback on static evidence alone**
- the biggest real concern is **volume + owner-pressure**, not a newly discovered static correctness break

In other words:

- skeptical verdict on "done": `no`
- skeptical verdict on "net improvement at all": still `yes`

## 3. Pass 1 Audit

### 3.1 The strongest skeptical fact is size

This is a big dirty tranche:

- `26 tracked + 2 untracked`
- `8518 insertions / 1245 deletions`

Adversarial reading:

- this is large enough to hide integration mistakes even when targeted tests stay green
- a single fresh run is not optional anymore; it is the minimum honesty check

### 3.2 The tranche is heavy in audit and helper code

A skeptical reviewer would immediately ask:

- did we improve the system, or did we mostly improve the explanations around the system?

That concern is fair because much of today’s work lives in:

- `modules/core/failure_analyzer.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_raw_evidence.py`

This is good for observability, but it can also hide the fact that runtime behavior itself is not yet proven.

## 4. Pass 2 Audit

### 4.1 Owner-surface pressure is still high and in one place worse

Current recount:

- `FailureAnalyzer`
  - `77` direct methods
  - `4` methods `120+`
  - `2` methods `180+`
  - top hotspots:
    - `_build_sink_alignment_summary_payload` `286`
    - `_collect_sink_alignment_raw_rationale_results` `281`
- `Stage4InterviewRound`
  - `166` direct methods
  - `5` methods `120+`
  - `2` methods `180+`

Adversarial reading:

- today’s tranche may be functionally more coherent, but it definitely did not simplify the main audit owner
- there is a risk that future changes become harder because the audit layer itself is becoming a new hotspot

### 4.2 Whole-file confidence is weaker than shard confidence

Current evidence is strong but bounded:

- targeted touched shards passed: `447 passed`
- whole-file `tests/test_stage4_interview_round.py -q` timed out earlier in this workstream

Adversarial reading:

- targeted shards are correct and valuable
- but they are still not identical to a single monolithic full-file proof

This does not negate the improvement claim, but it does lower confidence that nothing outside the selected Stage4 surfaces moved unexpectedly.

### 4.3 The tranche improves auditability faster than it reduces runtime complexity

This is the deepest skeptical point.

What got much better:

- raw evidence structure
- watchlists
- operator summaries
- sink comparison surfaces

What did not get lighter:

- Stage4 owner complexity
- FailureAnalyzer owner complexity
- Stage2 long-method residue

Adversarial reading:

- the workspace may now explain failures better than before
- but that does not automatically mean it will fail less in runtime

### 4.4 Queue/controller documentation is still stale

The code moved first. The governing docs did not.

Adversarial reading:

- even if code is better, operators can still act on stale controller text
- that means snapshot/fresh-run/post-run audit is required before updating queue and roadmap authority

## 5. Pass 3 Audit

### 5.1 Strongest case against "just keep coding"

The strongest skeptical conclusion is not "revert."
It is:

- stop adding more static layers
- freeze the tranche
- force it through runtime truth

Why:

1. diff volume is already large
2. audit/helper owners are already heavy
3. current evidence is still static + targeted only
4. if runtime disagrees, the longer we wait the harder blame assignment becomes

### 5.2 Strongest case against rollback

Even in adversarial mode, rollback is not justified by the evidence on hand.

Why not:

- compile/lint/UTF-8 all pass
- targeted touched regressions are all green
- no new static `P0/P1` was found
- the new evidence paths are internally coherent enough that post-run diagnosis should be better, not worse

So the skeptical answer is:

- do not revert
- do not declare victory
- do not keep expanding scope

### 5.3 Practical adversarial recommendation

The most conservative reasonable next sequence is:

1. save the two audit docs
2. snapshot commit
3. run one fresh run
4. perform merged post-run audit
5. only then decide whether today’s tranche deserves closure language or further patching

## 6. Conclusion

Adversarially, today’s tranche still survives review.

But the reason it survives is narrow:

- not because it is small
- not because it is elegant everywhere
- not because it is runtime-proven

It survives because no strong static evidence says it made the system worse, while a lot of static evidence says it improved contract continuity and post-run auditability.

The correct skeptical posture is:

- improvement claim: `accepted with caution`
- runtime trust claim: `not accepted yet`
- next action: `snapshot + fresh run + merge audit`

Confidence: `95%`
