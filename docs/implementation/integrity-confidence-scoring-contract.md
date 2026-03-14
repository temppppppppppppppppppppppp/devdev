# Integrity Confidence Scoring Contract

Date: 2026-03-14
Status: active
Applies To: deep global system-track survey bundles

## 1. Purpose
- Provide a repeatable meaning for "95% confidence" in system-track survey documents.
- Prevent confidence claims from being intuitive or rhetorical only.

## 2. Score Model

| Dimension | Max |
| --- | --- |
| Scope and path coverage completeness | 20 |
| Macro + micro + cross-cut + operational view completeness | 15 |
| Side-effect and durability coverage | 15 |
| Evidence triangulation quality | 15 |
| Contradiction closure quality | 10 |
| Uncertainty ledger quality | 10 |
| Execution-SSOT mapping and single-roadmap coherence | 10 |
| Validation and proof artifacts | 5 |
| Total | 100 |

## 3. Thresholds
- `95-100`: high-confidence final save allowed
- `90-94`: strong draft, but re-audit required before final save
- `80-89`: incomplete for deep survey closure
- `<80`: insufficient; major gaps remain

## 4. Hard Caps
These caps override the raw sum:
- unresolved `P0`: cap at `79`
- unresolved single-sourced `P1`: cap at `89`
- missing cross-cut integrity matrix: cap at `88`
- missing uncertainty and contradiction ledger: cap at `88`
- two or more active execution SSOTs with no single master roadmap: cap at `84`
- missing validator run after roadmap or mirror refresh: cap at `92`

## 5. Required Confidence Summary
A deep survey should explicitly summarize:
- estimated confidence score
- top reasons the score is not higher
- contradictions that were closed
- contradictions or uncertainties that remain open
- what would be needed to push the score higher

## 6. Interpretation Rule
- 95% confidence does not mean zero risk
- it means the survey is sufficiently evidenced, internally consistent, execution-mapped, and contradiction-aware to serve as a governing artifact
