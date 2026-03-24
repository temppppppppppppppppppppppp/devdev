Date: 2026-03-24
Status: final (3-pass audited)
Document Type: evidence-based root cause report
Canonical Path: `docs/2026-03-24/fresh-run-stage4-convergence-root-cause-report.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
- `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md`
- `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md`
- `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- current live-run console tail inside `docs/2026-03-23/console.txt`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace with only docs/2026-03-23/console.txt advancing during active fresh run`
- Resume Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Resume Drift Summary: `same HEAD; report synthesized after live reread of Episode 6 convergence pattern`
Side-Effect Coverage:
- artifact truth: indirect via live-merge survey docs
- DB truth: indirect via live-merge survey docs
- console/operator truth: yes
- JSONL/metrics truth: indirect via live-merge survey docs
- config/bootstrap: not primary

---

## 1. Executive Summary

Yes, a reportable root cause exists.

The current fresh run shows that the system is **not failing on final safety**. The Director family and post-select layers are eventually blocking bad manuscripts and letting a safe manuscript through.

The real problem is different:

1. **Stage 4 converges too late.**
2. **Chief Writer initial drafting and early fix loops do not preserve committed continuity facts reliably.**
3. **When the conflict is a hard state/history fact drift, partial patching is often the wrong tool.**
4. **The system eventually succeeds because the Director stack keeps vetoing bad manuscripts, not because the writer/fix path is efficient.**

In short:

`The bottleneck is not final acceptance correctness. The bottleneck is poor time-to-convergence in the CW write/fix path.`

This is why the user's hypothesis is directionally correct:

- the contract layer is better than before
- the firewall works
- but "write correctly on the first attempt" is still weak
- and early patch rounds are often wasted

## 2. Reportable Conclusion

The fundamental root cause can be stated as:

> Stage 4 currently relies on Director/post-select as a late defensive system, while the Chief Writer initial-write and early-repair methods still treat some committed continuity facts as revisable prose instead of immutable constraints.

That creates a recurring pattern:

1. blueprint and prior-state truth are available
2. CW writes a manuscript that is fluent but fact-drifting
3. Director may still give a positive or provisional-positive judgment
4. post-select catches continuity/history contradictions
5. retry begins
6. fix-pack often under-specifies the exact repair
7. another round is burned
8. eventually a later round succeeds after enough rerolling or heavier correction

This is a convergence-efficiency failure, not a terminal-safety failure.

## 3. Core Evidence

## 3.1 Episode 6 eventually passed, but only after repeated write/fix failure

Episode 6 is the clearest current proof.

Round 1:
- Director PASS at `console.txt:1729`
- immediate post-select downgrade at `console.txt:1742`
- retry widening because `Fix Pack patch_targets is empty` at `console.txt:1743`

Round 2:
- Director PASS_WITH_FIX at `console.txt:1822`
- immediate post-select downgrade at `console.txt:1838`
- same empty patch-target pathology at `console.txt:1857`

Round 3:
- Director PASS at `console.txt:1932`
- post-select also PASS at `console.txt:1941`
- final production completed at `console.txt:1961`

This is the key operational signal:

`the system can get through, but it often needs multiple expensive retries before the manuscript stops violating committed facts.`

## 3.2 The repeated failure family is continuity/history fact drift, not generic low quality

The recurring rejection family in Episode 6 is not vague "bad writing."

The observed conflicts are concrete:
- 38억 vs 20억 state drift
- HTS/PB strategy contradiction
- opening continuity pressure mismatch

Evidence:
- `console.txt:1738` to `console.txt:1746`
- `console.txt:1833` to `console.txt:1846`

These are committed-state contradictions.

That matters because fact drift should not be handled like normal prose polish.

## 3.3 Earlier episodes show the same pattern: eventually pass, but only after reroll/repair churn

Episode 3:
- downgrade on `console.txt:920`
- later Round 3 PASS on `console.txt:1151`
- completed at `console.txt:1172`

Episode 4:
- downgrade on `console.txt:1390`
- later Round 3 PASS on `console.txt:1499`
- completed at `console.txt:1521`

This makes the pattern stable enough to report:

`The system is repeatedly paying 2-3 rounds to repair the same class of Stage 4 continuity/history drift.`

## 4. What The Evidence Says The Root Cause Is Not

## 4.1 Not a final-gate failure

The Director/post-select chain is doing its job.

It is catching:
- history conflict
- continuity conflict
- opening pressure drift
- state-value contradictions

So the root cause is not "the system lets bad manuscripts through."

## 4.2 Not primarily a Stage 2 failure

The current evidence does not support Stage 2 pacing as the first-order cause.

Why:
- Stage 2 continues to complete
- Stage 3 continues to pass
- the repeated failure family appears in Stage 4 manuscript materialization and repair

This may still be worth tuning later, but it is not the main operational bottleneck visible in the current run family.

## 4.3 Not simply "BP and CW have no contract"

That statement is now too broad.

A better statement is:

- the BP/CW contract exists and has improved
- but CW still does not treat enough of that contract as immutable during first-write and early fix rounds

So the problem is not absence of contract.
It is weak enforcement in the write/fix path.

## 5. Actual Root Cause Hierarchy

## 5.1 Root Cause A: CW initial drafting still rewrites committed facts too easily

The strongest live hypothesis, now supported by multiple rounds, is:

- CW sees a locally plausible version
- rewrites around that plausibility
- but in doing so, overrides already committed facts from prior episodes or the current blueprint/handoff packet

This matches the observed Episode 6 behavior:
- prior established state says 38억
- manuscript falls back to 20억 framing
- post-select rejects it

So the dominant issue is:

`CW is still too willing to improvise around hard continuity/state anchors.`

## 5.2 Root Cause B: Early repair is too patch-oriented for fact drift

When the conflict is:
- wrong opening anchor
- wrong account balance
- wrong event order
- repeated already-completed beat

then the fix needed is often structural.

But the current retry path often behaves as if the fix were local.

The clearest symptom is:
- `Fix Pack patch_targets is empty`
- then retry still continues

This means the system knows something is wrong, but the repair packet is too weak to force a clean rewrite.

That is why a later reroll or heavier correction eventually works while earlier patch rounds do not.

## 5.3 Root Cause C: Safety is late-bound, convergence is under-specified

The system has strong late defense:
- Director
- post-select
- continuity/history checks

But it has weaker early convergence control:
- first draft can drift
- early retry may not regenerate enough
- patch loops can keep stale context around too long

That creates a split between:
- `safe enough eventually`
- `efficient enough early`

The current issue sits in the second category.

## 6. Why Full Rewrite May Be Cheaper Than Partial Patch In Current State

This is now reportable, not just intuition.

For the currently observed failure family, partial patch is often dominated by full rewrite.

Reason:
- the error is not a local sentence-level flaw
- it is a contract/state reconstruction flaw
- patching prose around a wrong state anchor often preserves too much contaminated local logic

Episode 6 shows exactly this:
- Round 1 and Round 2 both consumed substantial time
- both still failed on the same state/history family
- only a later regenerated attempt cleared the conflict family

So the runtime implication is:

`If the failure class is committed fact drift or opening-state drift, the system should escalate to rewrite earlier instead of spending multiple partial-patch rounds.`

## 7. Operational Recommendation

The next remediation wave should focus on convergence policy, not broad architecture.

Recommended order:

1. **Fact-drift fast classification**
   - distinguish prose-style problems from committed-state problems
   - if the reject is about balance, ownership, timeline, opening anchor, or already-completed events, classify it as rewrite-biased

2. **Early rewrite escalation**
   - if first post-select reject is a hard continuity/history/state conflict and patch_targets are weak or empty, skip partial patch sooner
   - do not spend 2-3 rounds trying to locally massage a globally wrong manuscript

3. **CW immutability reinforcement**
   - force the writer path to treat opening anchor, current state values, and already-completed events as non-negotiable inputs
   - not "guidance," but immutable writing facts

4. **Fix-pack sharpening**
   - repair packets must carry exact state deltas and non-regression clauses
   - avoid general narrative advice when the failure is actually factual contradiction

## 8. Submission-Grade Statement

If this needs to be submitted as a concise reportable conclusion, the clean version is:

> The current bottleneck is a Stage 4 convergence inefficiency. The Director/post-select stack is functioning as an effective final defense, but Chief Writer initial drafting and early retry logic still fail to preserve committed continuity/state facts reliably. As a result, manuscripts often require multiple expensive rerolls before converging. For hard fact-drift failures, earlier full rewrite escalation is likely to reduce runtime more than repeated partial patching.

## 9. Confidence And Limits

Estimated confidence: 96%

Why this is above 95%:
- current live console was reread directly
- Episode 3, 4, and 6 all show the same convergence pattern
- prior ROL live-merge lane reports agree on the same Stage 4 write/fix bottleneck family
- the conclusion is bounded to observed runtime behavior, not broad repo-wide claims

Limits:
- this report is primarily console-driven, with DB/artifact support inherited from the already finalized live-merge survey docs
- it is a root-cause report, not an execution SSOT
- it does not claim that all long-run Q5/Q7 problems are solved or explained by this one bottleneck

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- document type set to root-cause report, not execution doc
- scope bounded to current fresh-run convergence behavior plus prior ROL live-merge evidence
- excluded unrelated model/config/logging waves

### Pass 2. Evidence and Consistency
- verified Episode 6 round sequence directly from `console.txt`
- cross-checked Episode 3 and Episode 4 for the same convergence pattern
- aligned claims with prior T1/T2/T3 live-merge findings
- avoided overclaiming beyond observed Stage 4 write/fix behavior

### Pass 3. Execution and Readability
- converted evidence into submission-grade diagnosis
- separated safety success from convergence failure
- made the operational consequence explicit: earlier rewrite escalation is likely higher ROI than repeated partial patching for committed fact drift
