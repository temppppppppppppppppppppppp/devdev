Date: 2026-03-23
Status: active
Document Type: system-track survey order
Canonical Path: `docs/2026-03-23/weekend-long-function-global-3pass-audit-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-20/TF-static-complexity-audit-v2.md`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-order.md`
- `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md`
- `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md`
- `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`

Commit State:
- Baseline Commit: `203b328fb35633f9a23fe986862994c8b6dddab7`
- Baseline Dirty Summary: `dirty workspace allowed; long-function campaign plus post-audit bugfixes remain in-flight`
- Resume Commit: `same-as-baseline unless weekend audit start captures a newer resume point`
- Resume Drift Summary: `must be re-audited at audit start before any final closure claims`

## 1. Purpose
- Define the weekend-wide `global 3-pass audit` for the long-function reduction campaign summarized in `docs/2026-03-20/TF-static-complexity-audit-v2.md`.
- Re-check whether same-file decomposition, owner shell thinning, runtime splits, and observability edits preserved:
  - authority ownership
  - contract meaning
  - persistence and sink behavior
  - operator-visible console behavior
- Separate `true behavioral drift` from `intended duplicate-log collapse`, `thin-shell cleanup`, and `stale survey suspicion`.

This order is not a new refactor wave. It is a campaign-wide integrity audit.

## 2. Primary Questions
1. Did any long-function tranche move or drop the real authority owner for PASS, REJECT, retry, persistence, or rollback?
2. Did any tranche keep verdict behavior but lose DB, audit, metrics, file, or console sinks?
3. Did any tranche introduce dead wrappers, duplicate definitions, stale compatibility residue, or string corruption?
4. Did any tranche improve structure while reducing operator observability in a way that now blocks live debugging?
5. Is `TF-static-complexity-audit-v2.md` still a trustworthy map of the campaign after recent live fixes and follow-up surveys?

## 3. Scope
Included code surfaces:
- `main_a.py`
- `modules/core/**/*.py`
- `modules/domain/agents/**/*.py`
- `modules/validation/**/*.py`
- `modules/api/**/*.py`

Included campaign families:
- every tranche family represented in `docs/2026-03-20/TF-static-complexity-audit-v2.md`
- long-function same-file decomposition tranches
- runtime / module split tranches
- owner/public boundary review tranches
- observability follow-up fixes that touched verdict or sink paths after the campaign

Included side-effect surfaces:
- console / operator-visible output
- DB writes
- audit-event writes
- metrics / pass-rate writes
- file artifact writes
- rollback / retry / failure logging
- UTF-8 integrity on touched runtime-facing strings

Excluded unless needed as evidence:
- narrative-content quality
- fresh design or architecture proposals
- brand-new refactor implementation not required to unblock the audit

## 4. Anchor SSOT
`docs/2026-03-20/TF-static-complexity-audit-v2.md` is the campaign anchor, not the sole truth source.

Use it for:
- tranche ordering
- hotspot history
- owner/runtime split decisions
- band snapshots
- settled vs residual-shell vs hard-review markers

Override rules:
- live workspace source outranks stale survey wording
- post-campaign bugfixes outrank older tranche closure notes
- fresh live-run evidence outranks static suspicion
- unresolved claims stay unresolved until both source and evidence agree

## 5. Required 3-Pass Method

### Pass 1. Static Campaign Re-Audit
- Re-walk tranche families from the audit doc by area.
- Confirm for each family:
  - current owner shell
  - current semantic core
  - current sink owner
  - current contract / envelope boundary
- Build a `campaign integrity ledger` with these states:
  - `intact`
  - `operator-surface drift`
  - `sink drift`
  - `contract drift`
  - `stale-doc-only`
  - `unresolved`

Pass 1 must explicitly re-check:
- dead wrappers
- duplicate defs
- stale helper residue
- source-string mojibake
- authority ambiguity introduced by hidden instance-state channels

### Pass 2. Live-Merge Verification
- Run bounded fresh paths that sample the modified campaign across major stage families.
- Minimum live lanes:
  - Stage 0 operator path
  - one Stage 2 path
  - one Stage 3 path
  - one Stage 4 path
- Capture:
  - console transcript
  - DB / metrics / audit / file side effects when present
  - live mismatches between expected and observed sink behavior
- Mark each Pass 1 suspicion as:
  - `confirmed by live evidence`
  - `not observed live`
  - `operator-only`
  - `blocked / not yet exercised`

### Pass 3. Closure Merge Audit
- Merge Pass 1 and Pass 2 findings into a final closure view.
- Re-classify every meaningful issue as one of:
  - `no confirmed loss`
  - `operator-surface-only loss`
  - `persistence loss`
  - `contract / verdict loss`
  - `stale survey claim`
  - `still unresolved`
- Re-audit the final report and any updated orientation references before final save.
- Do not final-save below 95% confidence.

## 6. Required Work Products
The weekend audit should produce, at minimum:
1. one canonical campaign audit report
2. one tranche-family integrity ledger
3. one live-run mismatch ledger
4. one list of `post-audit quick fixes`, separated into:
   - bugfix now
   - observability now
   - next-week refactor
   - no action

Do not create an execution roadmap unless the audit proves new implementation work beyond quick fixes.

## 7. Area Ordering
Use this campaign-wide ordering unless live evidence forces reprioritization.

1. Stage 0 / Stage 1 operator entry helpers
2. Stage 2 validation / finalizer / orchestrator family
3. Stage 3 orchestrator / blueprint runtime family
4. Stage 4 director / post-pass / processor family
5. high-pressure owner modules:
   - `main_a.py`
   - `db_manager.py`
   - `stage4_interview_round.py`
   - `state_tracker.py`
6. cross-cutting validators / guards / ensemble modules

The goal is campaign integrity first, not numerical hotspot order.

## 8. Mandatory Questions Per Family
For every audited family, answer these questions explicitly.

1. Who is the current authoritative owner?
2. Which sinks must fire if the family succeeds or rejects?
3. Which operator-visible console lines should appear?
4. Did long-function decomposition change that behavior?
5. Is the current state:
   - intact
   - thinner but equivalent
   - less observable
   - behaviorally regressed

## 9. Acceptance Criteria
This weekend audit is complete only if:
- every major tranche family from the campaign is classified
- every P0 or P1 issue has a concrete file and line anchor
- every suspected regression is tied to either source evidence, live evidence, or both
- the final report states whether the campaign caused any confirmed:
  - authority loss
  - persistence loss
  - verdict / contract loss
  - operator-surface loss
- `TF-static-complexity-audit-v2.md` trustworthiness is re-scored at the end
- final confidence is at least 95%

## 10. Stop Rules
- Do not launch another broad refactor wave during the audit.
- Only patch code during the weekend audit if:
  - the audit is blocked, or
  - a live run proves a clear regression and the user explicitly wants immediate correction.
- Do not overclaim on static suspicion without live corroboration when the path is runnable.
- Do not treat reduced duplicate logging as a regression unless operator usefulness materially dropped.

## 11. Suggested Deliverable Paths
- order:
  - `docs/2026-03-23/weekend-long-function-global-3pass-audit-order.md`
- final report:
  - `docs/2026-03-23/weekend-long-function-global-3pass-audit.md`
- optional evidence ledger:
  - `docs/2026-03-23/weekend-long-function-global-evidence-manifest.md`

## 12. Suggested Weekend Opening Sequence
1. Re-open `docs/2026-03-20/TF-static-complexity-audit-v2.md`.
2. Snapshot current live recount and dirty worktree summary.
3. Build the family ledger from the audit doc.
4. Run Pass 1 static re-audit.
5. Execute bounded live lanes for Pass 2.
6. Merge and classify findings in Pass 3.

## 13. 3-Pass Audit Record
- Pass 1
  - confirmed the order is bounded to campaign integrity rather than new realization work
- Pass 2
  - confirmed the method forces both static and live evidence before making campaign-loss claims
- Pass 3
  - confirmed deliverables, stop rules, and confidence gate align with current workspace governance

## 14. Confidence
- Confidence: 98%
- Basis:
  - directly anchored to the campaign SSOT the user named
  - reuses current live-merge and integrity-survey patterns already active in this workspace
  - bounded enough to execute over a weekend without inflating into another refactor program
