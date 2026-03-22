Date: 2026-03-23
Status: final (3-pass audited, prompt artifact)
Document Type: system-track operator prompt
Canonical Path: `docs/2026-03-23/weekend-long-function-global-3pass-audit-prompt.md`
Temp Mirror Path: none
Source Order Doc:
- `docs/2026-03-23/weekend-long-function-global-3pass-audit-order.md`

## 1. Purpose
- Provide a ready-to-paste operator prompt for the weekend-wide global 3-pass audit over the long-function reduction campaign.
- Keep the prompt aligned with the canonical audit order and current workspace governance.

## 2. Prompt
```text
System-track weekend audit order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/2026-03-23/weekend-long-function-global-3pass-audit-order.md
4. docs/2026-03-20/TF-static-complexity-audit-v2.md
5. docs/2026-03-23/llm-codebase-orientation-pack.md
6. docs/2026-03-23/opus-pass-reject-logging-integrity-survey-order.md
7. docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md
8. docs/2026-03-23/opus-llm-friendliness-global-survey-order.md
9. docs/2026-03-23/opus-llm-friendliness-global-survey-report.md

Task:
Run a weekend-wide global 3-pass integrity audit over the long-function reduction campaign summarized in docs/2026-03-20/TF-static-complexity-audit-v2.md.

Primary goal:
Determine whether the long-function campaign preserved authority, contracts, persistence sinks, and operator-visible behavior across the codebase.

Hard constraints:
- This is audit-first, not a new refactor wave.
- Do not perform broad refactors.
- Do not create a new execution roadmap unless the audit proves implementation work beyond quick fixes.
- Only patch code if:
  - the audit is blocked by a compile/decode/runtime blocker, or
  - a live run proves a clear regression and the user explicitly wants immediate correction.
- If you patch under those conditions, report it as an audit unblocker or regression fix, not as a new tranche.
- Do not overclaim from static reading alone when a path is runnable.
- Final human-readable report cannot be treated as final unless confidence is at least 95%.

Audit scope:
- main_a.py
- modules/core/**/*.py
- modules/domain/agents/**/*.py
- modules/validation/**/*.py
- modules/api/**/*.py
- all tranche families materially represented in docs/2026-03-20/TF-static-complexity-audit-v2.md
- verdict, persistence, rollback, retry, audit, metrics, and operator-visible console paths
- UTF-8 integrity on runtime-facing strings touched by the campaign

Required 3-pass method:

Pass 1. Static Campaign Re-Audit
- Re-walk tranche families from docs/2026-03-20/TF-static-complexity-audit-v2.md by area.
- For each meaningful family, identify:
  - current authoritative owner
  - current semantic core
  - current sink owner
  - current contract / envelope boundary
- Build a family integrity ledger using only these states:
  - intact
  - operator-surface drift
  - sink drift
  - contract drift
  - stale-doc-only
  - unresolved
- Explicitly look for:
  - dead wrappers
  - duplicate definitions
  - stale compatibility residue
  - source-string mojibake
  - hidden instance-state channels that obscure ownership

Pass 2. Live-Merge Verification
- Run bounded fresh paths that sample the campaign across major stage families.
- Minimum live lanes:
  - one Stage 0 operator path
  - one Stage 2 path
  - one Stage 3 path
  - one Stage 4 path
- Capture:
  - console transcript
  - DB side effects when present
  - metrics / audit / file side effects when present
- For each Pass 1 suspicion, mark:
  - confirmed by live evidence
  - not observed live
  - operator-only
  - blocked / not exercised

Pass 3. Closure Merge Audit
- Merge Pass 1 and Pass 2 findings.
- Re-classify every meaningful issue as exactly one of:
  - no confirmed loss
  - operator-surface-only loss
  - persistence loss
  - contract / verdict loss
  - stale survey claim
  - still unresolved
- Re-audit the report before final save.
- If confidence is below 95%, keep the report provisional and say why.

Mandatory questions per family:
1. Who is the current authoritative owner?
2. Which sinks must fire if the family succeeds or rejects?
3. Which operator-visible console lines should appear?
4. Did long-function decomposition change that behavior?
5. Is the current state:
   - intact
   - thinner but equivalent
   - less observable
   - behaviorally regressed

Required output files:
1. Final report:
   docs/2026-03-23/weekend-long-function-global-3pass-audit.md
2. Optional evidence manifest if needed:
   docs/2026-03-23/weekend-long-function-global-evidence-manifest.md

Mandatory report structure:
1. Executive Summary
2. Current Campaign Snapshot
3. Pass 1 Static Re-Audit Findings
4. Pass 2 Live-Merge Findings
5. Pass 3 Closure Merge Findings
6. Family Integrity Ledger
7. Confirmed Regressions
8. Operator-Surface-Only Losses
9. Stale Survey Claims
10. Unresolved Items
11. Quick Fixes Now
12. Next-Week Refactor Candidates
13. Confidence And Limits

Acceptance criteria:
- every major tranche family is classified
- every P0/P1 issue has a concrete file and line anchor
- every claimed regression is tied to source evidence, live evidence, or both
- the report explicitly states whether the campaign caused any confirmed:
  - authority loss
  - persistence loss
  - verdict / contract loss
  - operator-surface loss
- docs/2026-03-20/TF-static-complexity-audit-v2.md trustworthiness is re-scored at the end
- final confidence is at least 95%, or the report remains provisional

Starting order for the audit:
1. Re-open docs/2026-03-20/TF-static-complexity-audit-v2.md
2. Snapshot current live recount and dirty worktree summary
3. Build the family ledger from the audit doc
4. Run Pass 1 static re-audit
5. Run Pass 2 bounded live lanes
6. Merge in Pass 3 and classify all meaningful findings

After writing the report, run:
- python scripts/check_utf8_hygiene.py docs/2026-03-23/weekend-long-function-global-3pass-audit.md
- python scripts/ops_validator.py

In your final response to me:
- summarize confirmed regressions first
- then summarize operator-surface-only losses
- then give overall campaign verdict
- then give confidence
- then list the highest-ROI immediate fixes
- keep it concise and factual
```

## 3. 3-Pass Audit Record
- Pass 1
  - verified the prompt matches the canonical weekend audit order rather than inventing a new flow
- Pass 2
  - verified the required outputs, stop rules, and acceptance criteria remain aligned with current governance
- Pass 3
  - verified the final prompt preserves the 95% confidence gate and does not authorize premature realization

## 4. Confidence
- Confidence: 99%
- Basis:
  - direct derivative of the canonical weekend audit order
  - bounded to survey execution rather than broad implementation
  - rechecked against current workspace document-save and audit rules
