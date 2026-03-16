<!-- [완료] -->
# Encoding Boundary Mojibake Refresh Remediation Execution SSOT

Date: 2026-03-14
Status: closed
Canonical Path: `docs/2026-03-14/encoding-boundary-mojibake-refresh-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/encoding-boundary-mojibake-refresh-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
- Baseline Dirty Summary: `dirty: 7 tracked, 3 untracked; hotspots: docs/implementation/*, 260314-print.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `realized in live workspace with main_a.py bootstrap notice moved to stdout, ProcessRunner stderr marked diagnostic-only, and encoding transport/tests refreshed`
Source Survey Docs:
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-3pass-audit.md`
- `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`
Evidence Artifacts:
- `docs/2026-03-14/db-log-frontier-lag-reaudit-encoding-samples.txt`
Side-Effect Coverage: covered
Primary References:
- `main_a.py`
- `260314-print.txt`
- `projects/00_20260314/logs/session_20260314_213845.log`
- `error.log`
- `tests/test_encoding_boundary_contract.py`

## 1. Intent
- Reopen the mojibake lane as a boundary-remediation item rather than as a source-corruption claim.
- Define which artifacts are authoritative operator truth and which capture paths are non-authoritative or must declare their encoding explicitly.

## 2. Baseline Facts
- The source strings in `main_a.py` are valid UTF-8 and contain the correct Korean operator text.
- `260314-print.txt` and `projects/00_20260314/logs/session_20260314_213845.log` are valid UTF-8 artifacts and preserve the current operator prompts.
- `error.log` is UTF-16 because it was produced through PowerShell stderr redirection, and the embedded UI prompt lines inside that artifact are mojibake.
- The current evidence does not support rewriting source text; it supports tightening the output-boundary contract.

## 3. Scope
Included:
- stdout and stderr boundary handling in the runtime shell
- harness and capture policies for authoritative operator artifacts
- encoding boundary regression tests and docs

Excluded:
- content-level rewriting of existing Korean strings
- unrelated prompt or UI contract changes outside encoding policy
- DB/log sink alignment except where it intersects authoritative artifact policy

## 4. Pass 1. Inventory Summary
- source artifacts confirmed clean: `1` runtime source surface
- authoritative UTF-8 operator artifacts confirmed clean: `2`
- boundary-corrupted stderr artifacts confirmed: `1`
- capture-policy surfaces to standardize: `2`

## 5. Pass 2. Semantic Classification
- Class A:
  - runtime source text and stdout/stderr handling surfaces
- Class B:
  - UTF-8 print/session artifacts and UTF-16 stderr artifact samples
- Class C:
  - prior mojibake closure docs that need a boundary-specific refresh rather than a source-wide reopening

## 6. Side-Effect Map
- file writes / artifacts:
  - print captures
  - session logs
  - stderr/error captures
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - operator-visible artifact policy affects which files are considered authoritative
- console / UI / operator output:
  - yes; this is the core surface
- rollback / recovery / retry:
  - not applicable
- cache / global state:
  - not applicable
- bootstrap fallback / config-env mutation:
  - possible shell or harness encoding settings must be documented explicitly

## 7. Realization Architecture
- `ui.log` and interactive prompts remain authoritative only through stdout plus the durable JSONL/DB sinks that already record them.
- stderr is reserved for true errors, exception traces, and faulthandler output; normal operator prompts must not be treated as authoritative when captured through stderr redirection.
- Harnesses that capture operator-visible text must write UTF-8 files directly from Python or use an explicitly UTF-8 file writer on the shell side. Raw PowerShell `2>` output must not be used as the authoritative operator transcript.
- When a stderr artifact is intentionally kept, its encoding must be declared in the artifact or companion doc. For the current PowerShell path, that means UTF-16.
- Encoding tests should verify both:
  - authoritative UTF-8 artifacts decode cleanly and match source text
  - non-authoritative stderr artifacts are either explicitly decoded under their declared encoding or excluded from operator-truth comparisons

## 8. Execution Tranches
1. Tighten the runtime and harness contract so authoritative operator artifacts are always captured in UTF-8.
2. Fence stderr usage to true error channels and keep prompt/UI text on authoritative stdout/UI sinks.
3. Refresh encoding boundary tests and docs so boundary-only mojibake cannot be mistaken for source corruption.

## 9. Acceptance Criteria
- Authoritative operator artifacts decode as UTF-8 and preserve the same prompt text as the source.
- Stderr capture paths are either explicitly encoded and documented or removed from operator-truth workflows.
- No future audit depends on `error.log`-style artifacts without declared encoding metadata.

## 10. Verification Plan
- Run `tests/test_encoding_boundary_contract.py`.
- Add targeted capture tests that compare source text against UTF-8 operator artifacts.
- Reproduce a bounded stderr capture and confirm it is labeled and interpreted as non-authoritative unless explicitly declared otherwise.
- Re-check the docs that describe print/log capture paths for alignment with the new artifact policy.

## 11. Guardrails
- Do not rewrite source strings purely because one boundary artifact is corrupted.
- Do not treat shell-host default redirection behavior as a stable product contract.
- Do not mix authoritative operator transcript rules with crash-dump or exception-trace capture rules.

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition: satisfied on `2026-03-15` after canonical closure, roadmap closure, and queue cleanup
- roadmap dependency: `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document through the 3-pass audit and reconfirm 95% confidence against the live workspace before patching code

## 14. Closure Note
- closure date: `2026-03-15`
- closure status: `closed`
- implementation result:
  - `main_a.py` no longer emits the faulthandler activation banner on `stderr`; the benign bootstrap notice now stays on `stdout`
  - `modules/api/process_runner.py` now labels `stderr` tails as diagnostic-only, declares `utf-8-replace` decode policy, and ignores the benign faulthandler activation banner if it appears on `stderr`
  - `docs/2026-03-13/encoding-boundary-contract.json` and `docs/implementation/event-schema-v1.json` now codify authoritative `stdout` operator artifacts and non-authoritative `stderr` capture policy
- verification evidence:
  - `python -m pytest tests/test_encoding_boundary_contract.py -q` with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` -> `4 passed`
  - `python -m pytest tests/test_process_runner.py -q` with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` -> `31 passed`
  - `python -m pytest tests/test_desktop_transport_contract.py -q` with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` -> `3 passed`
- residual risk:
  - raw PowerShell `2>` artifacts remain non-authoritative by design and still require declared encoding metadata if someone keeps them for forensics
  - no active code follow-up remains inside this queue item
