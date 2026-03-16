<!-- [완료] -->
# FrontierLag Nonstop UTF-8 Hygiene Remediation 3-Pass Audit

Date: 2026-03-15
Status: final
Canonical Follow-On: `docs/2026-03-15/frontierlag-nonstop-utf8-hygiene-remediation-execution-ssot.md`
Baseline Commit: `083c86d9`
Baseline Dirty Summary: `modified=31, deleted=54, untracked=9`
Source Survey Doc:
- `docs/2026-03-15/codebase-global-live-merge-00_260315-post-run-merge-audit.md`
Evidence Artifact:
- `docs/2026-03-15/frontierlag-nonstop-utf8-hygiene-remediation-evidence.txt`
Confidence: `96%`

## 1. Intent
- Convert the fresh `P1` pair into one compact execution item before any code changes:
  - restore true no-input nonstop behavior for interactive menu `7`
  - narrow and harden the UTF-8 hygiene gate so it stops catching valid Korean prompts and stops crashing on cp949 PowerShell output
- Resolve current authority drift between the two closed FrontierLag prompt-policy docs.

## 2. Scope
Included:
- `main_a.py` FrontierLag interactive entry policy
- `scripts/check_utf8_hygiene.py`
- directly related regression tests
- predecessor execution docs that must be explicitly superseded

Excluded:
- shutdown-race / async teardown
- runtime audit summary or DB sink remediation
- prompt dedup work already validated as retained
- roadmap creation; this is a single compact item

## 3. Pass 1. Structure and Scope Audit
- Correct document type:
  - this is an execution-prep audit leading to one compact execution SSOT
- Scope is explicit:
  - one runtime operator contract surface
  - one tooling guardrail surface
- Included/excluded boundaries are narrow enough for a direct focused patch later
- Canonical/temp queue policy is coherent for a single item
- Side-effect-bearing surfaces are known:
  - CLI/operator prompts
  - session/UI logs
  - pre-commit / script CLI output
  - regression tests

Pass 1 judgment:
- pass

## 4. Pass 2. Evidence and Consistency Audit
- `main_a.py:4197` still contains the initial tranche prompt
- `main_a.py:4206` still logs the initial selected batch size
- live session evidence confirms the prompt is emitted before FrontierLag starts
- predecessor docs conflict in a way that matters operationally:
  - `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md` says zero normal-path prompt
  - `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md` says ask once, default `3`
  - fresh run proves the latter is live, while the user requirement is the former
- `scripts/check_utf8_hygiene.py:50` regex is broad enough to hit valid Korean question prompts
- `scripts/check_utf8_hygiene.py:177` direct stdout emission is incompatible with cp949 PowerShell when snippets contain emoji
- existing tests line up with the current, now-undesired behavior:
  - `tests/test_one_stop_frontier_lag_auto_continue.py` asserts the initial prompt text
  - `tests/test_check_utf8_hygiene.py` currently expects the false-positive rule

Pass 2 judgment:
- pass

## 5. Pass 3. Execution and Readability Audit
- The execution shape is clear:
  1. restore no-input nonstop on menu `7`
  2. preserve harness-only override seams
  3. tighten UTF-8 gate semantics around real mojibake, not normal Korean questions
  4. make the CLI output path shell-safe on Windows
  5. realign tests and predecessor document authority
- No unnecessary substrate or roadmap inflation is needed
- Guardrails are concrete:
  - do not reopen prompt dedup work
  - do not mix in shutdown-race or audit-summary changes
  - do not weaken UTF-8 gating so far that real mojibake slips through silently

Pass 3 judgment:
- pass

## 6. Supersession Decision
- The new execution item must supersede the interactive policy portion of:
  - `docs/2026-03-15/interactive-prompt-contract-refresh-execution-ssot.md`
- It also restores the operator-facing intention originally captured in:
  - `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
- The UTF-8 hygiene half is net-new and has no earlier closed execution doc authority.

## 7. Confidence Gate
- `96%` is justified because:
  - both P1 findings are directly tied to exact code lines plus fresh run evidence
  - predecessor contradiction is explicit, not inferred
  - the implementation surface is small and test targets are known
- The score is not higher because:
  - the next fix still needs one policy call preserved in code: harness overrides must stay prompt-free while interactive menu `7` becomes prompt-free again

## 8. Ready-State
- This audit passes the 3-pass save gate.
- A canonical execution SSOT can be saved now.
- A single `docs/temp/` mirror is allowed after the canonical doc is saved because confidence exceeds `95%`.
