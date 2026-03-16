<!-- [참고자료] -->
<\!-- [참고자료] -->
# OPUS Manuscript Contradiction Audit Package Revalidation

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/manuscript-contradiction-audit-opus-revalidation.md`
Evidence Artifact: `docs/2026-03-16/manuscript-contradiction-audit-opus-revalidation-evidence.txt`
Source Package:
- `docs/2026-03-16/manuscript-contradiction-audit-plan.md`
- `docs/2026-03-16/manuscript-contradiction-audit-tf-A-report.md`
- `docs/2026-03-16/manuscript-contradiction-audit-tf-B-report.md`
- `docs/2026-03-16/manuscript-contradiction-audit-tf-C-report.md`
- `docs/2026-03-16/manuscript-contradiction-audit-tf-D-report.md`
- `docs/2026-03-16/manuscript-contradiction-audit-tf-E-report.md`
- `docs/2026-03-16/manuscript-contradiction-audit-tf-F-report.md`
- `docs/2026-03-16/manuscript-contradiction-audit-3pass-audit.md`
- `docs/2026-03-16/manuscript-contradiction-audit-master-report.md`
Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
Baseline Dirty Summary: `dirty: runtime/stage modules and tests, desktop package/icon/version files, project artifacts/db, OPUS manuscript audit docs, and untracked 2026-03-16 survey docs`
Confidence: `96%`

## 1. Purpose

Re-audit the OPUS manuscript contradiction audit package before treating any part of it as current authority. The package is broad and useful, but it was produced from an older code/runtime context and mixes live projects with archival, proof, and explicit test artifacts.

## 2. Short Answer

The OPUS package is not safe to treat as a direct execution authority.

- It is useful as a `historical broad memo` and `lead list`.
- It is not trustworthy as a `final-authority contradiction ledger`.
- Its aggregate totals and code-remediation percentages should be downgraded.
- Only the parts that survive cross-check against real final/patched authority manuscripts and current live code should be promoted.

## 3. Scope Reclassification

### 3.1 What the package clearly did well

- It built a broad manual reading sweep over many `manuscripts` rows.
- It organized contradiction classes into a reusable taxonomy:
  - `M-1` character / identity drift
  - `M-2` timeline drift
  - `M-3` location drift
  - `M-4` asset / numeric drift
  - `M-5` relationship drift
  - `M-6` event continuity drift
- It surfaced a large lead list of candidate problem shapes worth cross-checking against real authority texts.

### 3.2 What the package did not fully establish

- It did not materially ground judgments in Stage 4 final-authority sinks such as:
  - `stage_attempts`
  - `director_selections`
  - final/patched artifact paths
  - patch lineage after `PASS_WITH_FIX`
- It therefore cannot independently prove that a contradiction survives in the published final authority manuscript.

Operationally, this means the package is a `DB-manuscripts-first` survey, not a `final-authority artifact truth + metadata truth + narrative truth` survey.

## 4. Live Cross-Checks

### 4.1 Scope composition

The package claims a `24 DB` sweep, but the target set is mixed:

- `4` real projects:
  - `projects/0`
  - `projects/000`
  - `projects/00_20260314`
  - `projects/00_260315`
- `19` archival / proof / rerun / `기록용` projects
- `1` explicit test artifact project:
  - `projects/코덱스_테스트`

That mixed scope is not invalid, but it sharply lowers how directly the aggregate totals map to current live operator risk.

### 4.2 Internal count drift

The package is internally inconsistent on basic aggregate counts.

- plan: `24 DB`, `109화`, `546,661자`
- OPUS 3-pass doc: `24 DB`, `109화`, `546,661자`
- master report header: `24 DB`, `109화`, `546,661자`
- master report aggregate row: `110화`
- plan labels `TF-F` as `13화`
- TF-F report labels itself `24 episodes total`
- TF-F also marks `projects/코덱스_테스트` as `N/A (test artifact)`

This does not destroy the package, but the package-wide totals are not stable enough to use as high-authority execution inputs without re-summing the underlying rows.

### 4.3 Authority-surface gap

The package plan references `episode_bibles`, `state_logs`, and anchor-style tables, but the saved reports do not materially operate on the authority sinks that now matter most for final manuscript truth:

- `stage_attempts`
- `director_selections`
- `final/patched artifact` identity
- patch lineage after `PASS_WITH_FIX`

That matters because our higher-authority real-manuscript survey found the surviving issue not in the final text itself, but in stale metadata authority after patch.

## 5. Cross-Source Reconciliation

### 5.1 What the higher-authority surveys say

The current best authority chain is:

1. `docs/2026-03-16/legacy-real-manuscript-contradiction-survey.md`
2. `docs/2026-03-16/legacy-manuscript-current-recurrence-supplemental-survey.md`
3. `docs/2026-03-16/legacy-manuscript-contradiction-manual-survey-and-current-risk-assessment.md`
4. this OPUS package

### 5.2 Reconciled findings

- The OPUS package was directionally right that continuity / numeric / carryover classes matter.
- The OPUS package overstates how many of those remain in `final authority` texts.
- Our real-manuscript survey directly read the final/patched authority texts in the overlapping real projects and did **not** find surviving hard contradictions there.
- The one class that survives cross-source confirmation is `stale metadata authority`:
  - legacy real project evidence: confirmed
  - current code recurrence: confirmed structurally possible now

## 6. Revalidated Authority Classification

### Keep as supported lead material

- contradiction taxonomy `M-1` through `M-6`
- historical watchlist references involving:
  - `projects/000`
  - `projects/00_260315`
- the broad intuition that carryover continuity and numeric drift deserve scrutiny

### Downgrade to memo-only

- aggregate contradiction totals: `75`
- package-wide severity totals
- package-wide `code-fixable` percentages
- direct remediation order inferred from archival/test mixes

### Exclude from direct execution authority

- any claim that a contradiction still survives in final authority without:
  - direct final/patched artifact read
  - `stage_attempts` / metadata confirmation
- any code-priority decision derived mainly from `기록용`, proof-refresh, rerun, backup, or explicit test artifacts

## 7. Operational Conclusion

This OPUS package should be treated as:

- `historical research memo`: yes
- `manual contradiction lead list`: yes
- `current final-authority contradiction SSOT`: no
- `direct execution queue driver`: no

The right use is to merge only the portions that survive higher-authority cross-check. Under that rule, the strongest execution-worthy outcome is not a broad contradiction overhaul. It is a narrow metadata authority hardening lane centered on patched-final sink alignment and stale-authority misuse prevention.
