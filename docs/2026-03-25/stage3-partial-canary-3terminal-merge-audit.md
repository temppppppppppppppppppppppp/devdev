# Stage3 Partial Canary 3-Terminal Merge Audit

Date: 2026-03-25
Status: final
Document Type: merge audit
Canonical Path: `docs/2026-03-25/stage3-partial-canary-3terminal-merge-audit.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: canary_0325 live artifacts/logs, prior closed Stage3 docs, 2026-03-25 survey docs, temp queue empty at merge start`
Source Survey Docs:
- `docs/2026-03-25/opus-stage3-partial-canary/t1-stage3-canary-chronology.md`
- `docs/2026-03-25/opus-stage3-partial-canary/t2-blueprint-artifact-truth.md`
- `docs/2026-03-25/opus-stage3-partial-canary/t3-stage3-mechanism-audit.md`
Evidence Artifacts:
- `projects/canary_0325/logs/runtime_audit.jsonl`
- `projects/canary_0325/logs/session/ui_events.jsonl`
- `projects/canary_0325/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__action_focused.json`
- `projects/canary_0325/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/canary_0325/logs/artifacts/stage3/ep_0009/attempt_01/final_blueprint__emotion_focused.json`
Side-Effect Coverage:
- Stage 3 prompt constraint assembly
- Stage 3 Python prevalidation warning surfacing
- Stage 3 quality-risk metadata
- inventory gap post-verdict annotation
- no Stage 4 conclusion in this audit

## 1. Scope

This merge audit covers only the `canary_0325` Stage 3 partial canary.

It does not claim end-to-end Stage 3 -> Stage 4 success. Stage 4 evidence remains out of scope for this document.

## 2. Converged Findings

### Finding A. The old Stage 3 culprit family is suppressed in the partial canary

All three lanes converge on the same operational fact:

- EP1-EP9 all reached Stage 3 `PASS`
- every episode passed on the first attempt
- the prior residual family around institution drift and phantom available-capital carry-forward did not recur in the canary blueprints

This is stronger than "reduced." For the bounded Stage 3 canary surface, it is a real suppression signal.

### Finding B. EP7 inventory-gap output is advisory-only and not a new Stage 3 blocker

The lanes agree that the EP7 inventory-gap warning is:

- generated after the Stage 3 verdict is already `PASS`
- logged for operator visibility and downstream continuity support
- not part of the blocking validation path

The gap reflects a legitimate state transition rather than a contradiction.

### Finding C. EP8 temporal-deictic warning is a healthy catch, not a relapse

The canary shows one bounded warning family on EP8:

- `temporal_deictic`
- `quality_risk: true`
- reduced candidate pool
- final score `92`
- verdict still `PASS`

The lanes converge that this is:

- correctly caught by Python prevalidation
- surfaced to Director
- accepted in narrative context

This is evidence that the current warning path is functioning, not evidence of a new dominant blocker.

## 3. Cleared Non-Culprits

The three lanes collectively clear the following from immediate action:

- the prior Stage 3 institution-name drift family in this canary
- the prior stale/phantom available-capital family in this canary
- inventory-gap synthesis as a blocker
- temporal-deictic warning existence by itself as a new systemic defect

## 4. Residual Limits

- This is a partial canary only. It does not settle whether Stage 4 still amplifies other seams.
- The chronology lane contains console-render mojibake in copied tables; merge conclusions here rely on the artifact-backed parts of the lane docs, not the broken console glyphs.
- The canary proves suppression on this run, not universal immunity across future works or genres.

## 5. Merge Conclusion

The partial canary is usable and positive:

- it materially supports that the recently closed Stage 3 residual-family waves changed live Stage 3 behavior
- it does not, by itself, justify a new bug-fix execution SSOT
- it does provide a clean enough baseline to open a new quality-up wave for blueprint clarity/density if the structural survey supports one

## 6. Confidence

Estimated confidence: 96%

Why this clears the 95% gate:

- all three lanes align on the main conclusion
- the conclusion is grounded in live canary artifacts, not only paraphrased console text
- the document is intentionally bounded to Stage 3 partial-canary interpretation and avoids overclaiming Stage 4 outcomes

## 7. Final Decision

- Old Stage 3 culprit family in merged canary view: `suppressed`
- New Stage 3 blocker from this partial canary alone: `none`
- Should this merge alone open a new SSOT: `no`, but it is strong supporting evidence for a separate clarity/density quality-up wave
