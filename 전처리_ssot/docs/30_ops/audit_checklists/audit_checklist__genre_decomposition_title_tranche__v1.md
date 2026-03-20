# Audit Checklist: Genre Decomposition Title Tranche

Date: 2026-03-20
Status: final
Scope: title-tranche audit checklist
Authority: canonical under `전처리_ssot/docs/30_ops/audit_checklists`
Confidence Target: 95%
Current Confidence: 95% for checklist readiness

## 1. Required Inputs

- title-tranche bundle
- tranche manifest
- active roadmap
- prior remediation note if this is a re-audit

If any required input is missing, the reviewer must stop and mark the audit `return_for_remediation`.

## 2. Structural Checks

- Is the title ID stable and does it match the tranche manifest?
- Do the file names follow the canonical naming contract?
- Are scene cards, block cards, cadence, and hook/payoff outputs all present?
- Is the title-tranche output capped at `candidate`?

## 3. Evidence Checks

- Does every reusable claim carry a reproducible `evidence_anchor`?
- Are summaries paraphrase-first rather than raw-text dumps?
- Can the reviewer trace each major claim back to a source episode range without guessing?
- Is any claim over-dependent on one ambiguous scene?

## 4. Label Checks

- Are labels functional rather than source-surface labels?
- Are there proper nouns or source-specific furniture leaking into labels?
- Do near-duplicate labels appear to describe the same pattern?
- Does each label have a clear downstream effect on `TR`, `BI`, or both?

## 5. Transfer Checks

- Is the transferable core distinct from non-transferable residue?
- Are worldbuilding details being treated as structure by mistake?
- Is style imitation being misfiled as structural reuse?
- Does the tranche produce reusable value beyond one favorite title?

## 6. Status and Promotion Checks

- Is each artifact assigned a confidence estimate with a reason?
- Does the status matrix recommend only allowed transitions?
- Is any attempt being made to jump directly from `candidate` to `canonical`?
- Are unresolved disagreements written into handoff or remediation notes?

## 7. Decision Block

Choose one only:

- `pass`
- `fail`
- `return_for_remediation`

The reviewer must also state the allowed status transition:

- remain `candidate`
- advance to `provisional`
- advance to `canonical`
- `rejected`

## 8. Mandatory Fail Triggers

- missing tranche manifest
- missing evidence anchors on major claims
- source-specific nouns inside reusable labels
- no clear connection from the claim set to `TR` or `BI`
- hidden reliance on long copied source passages
- self-approval or non-independent audit context

## 9. Remediation Note

The reviewer must record:

- top three blocking findings
- minimal fix set required for re-audit
- whether re-audit may reuse existing bundle IDs or needs a new version

## 10. 3-Pass Record

### Pass 1 Result

- Locked the checklist to title-tranche audit only.
- Separated required inputs from downstream decision logic.

### Pass 2 Result

- Added evidence, label, transfer, and promotion checks.
- Added explicit fail triggers and a forced decision block.

### Pass 3 Result

- Added remediation requirements so the checklist cannot end as a vague review memo.
- Preserved independence requirements from the roadmap.

## 11. Adversarial Review Record

Primary attacks considered:

- reviewer rubber-stamps the author's tranche
- copied source text hides weak structure work
- labels look reusable but are actually title-specific

Mitigations added:

- required-input gate
- evidence-anchor checks
- forced pass or fail decision
- explicit self-approval fail trigger
