# Document 3-Pass Audit Harness

Date: 2026-03-14
Status: active
Applies To: human-facing workspace documents
Related Templates:
- `docs/implementation/execution-ssot-template.md`
- `docs/implementation/execution-roadmap-template.md`
- `docs/implementation/execution-closure-template.md`
- `docs/implementation/evidence-manifest-template.md`
- `docs/implementation/execution-exception-template.md`
- `docs/implementation/process-health-scorecard-template.md`
Related Governance:
- `docs/implementation/operations-governance-map.md`

## 1. Purpose
- Standardize the mandatory 3-pass audit performed before human-facing documents are finalized.
- Reduce drift between draft intent, evidence, and saved document state.
- Provide a reusable save gate for surveys, audits, execution SSOTs, roadmaps, harnesses, and operating notes.
- Require a post-pass confidence threshold of at least 95% before final save.

## 2. Applies To
- survey docs
- audit docs
- execution SSOT docs
- execution roadmap docs
- harness docs
- README and operating-note docs
- report-style human-facing docs

Raw machine evidence files such as plain inventory `.txt` or `.json` may be generated earlier, but any document that interprets them must pass this harness before final save.

This harness also applies when an existing execution SSOT or execution roadmap is about to govern live code modification. In that case, run the audit again against the current workspace state before implementation starts.

## 3. Save Gate
Required order:

1. draft
2. pass 1 audit
3. pass 2 audit
4. pass 3 audit
5. targeted re-audit until estimated confidence is at least 95%
6. final save

For execution SSOT documents:
- save canonical dated doc only after the 3-pass audit and 95% confidence gate
- then refresh the temp mirror copy

## 4. Pass 1. Structure and Scope
Check:
- the document type matches the request
- scope is explicit
- included and excluded surfaces are clear
- path policy is correct
- section order is usable
- no obvious missing major section
- the relevant template has been followed when one exists

Typical failures:
- survey presented as execution doc
- execution doc without acceptance criteria
- queue policy or canonical/temp policy omitted
- side-effect scope absent where required

## 5. Pass 2. Evidence and Consistency
Check:
- claims match available evidence
- file paths and artifact paths are correct
- counts and inventories are internally consistent
- canonical path and temp mirror path are not inverted
- when the document is a ROL survey, re-audit, execution SSOT, or roadmap, the minimal commit-state fields are present and coherent
- referenced survey docs, evidence artifacts, and side-effect coverage are coherent
- no contradiction between AGENTS rules and harness rules

Typical failures:
- stale counts
- mismatched file names
- drift between canonical and temp semantics
- missing or stale baseline/resume commit-state metadata on a resumed ROL doc
- overclaiming beyond inspected evidence
- missing canonical/temp metadata on execution docs

## 6. Pass 3. Execution and Readability
Check:
- the document is actionable, not only descriptive
- sequence, ownership, or queue logic is clear
- overreach has been trimmed
- guardrails are explicit
- cleanup and follow-up conditions are explicit
- the final saved version is the intended one

Typical failures:
- roadmap without execution order
- temp queue rules without cleanup behavior
- long descriptive text with no operating consequence
- redundant duplication better handled by a referenced harness

## 7. Confidence Gate
After pass 3, estimate whether the saved document is at least 95% trustworthy for its intended operational use.

Check:
- claims are bounded to inspected evidence
- key terminology and scope are stable
- important ambiguity has been either resolved or explicitly disclosed
- the likely next reader would not need a corrective rewrite to act on the document

If confidence is below 95%:
- do not final save yet
- perform targeted additional review and revision
- repeat until the threshold is met or explicitly report that the threshold could not be achieved

## 8. Minimal Completion Markers
Before final save, confirm:
- document type is correct
- scope is explicit
- evidence basis is coherent
- side-effect coverage is addressed or marked not applicable
- next action or operating consequence is clear
- save path is correct
- canonical vs temp semantics are correct if execution docs are involved
- estimated confidence is at least 95%

## 9. Guardrails
- Do not skip a pass because the document is short.
- Do not mirror an execution SSOT to `docs/temp/` before this audit completes.
- Do not treat draft output as final merely because the content looks complete.
- Do not save a human-facing doc whose key paths or artifacts have not been checked.
- Do not treat completion of pass 3 alone as sufficient if confidence is still below 95%.
- Do not begin code modification from an execution SSOT or roadmap whose current-state re-audit has not been completed.
