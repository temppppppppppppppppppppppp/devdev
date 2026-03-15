# source-text-and-runtime-encoding-hygiene-remediation Execution SSOT

Date: 2026-03-15
Status: execution-ready
Canonical Path: `docs/2026-03-15/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/source-text-and-runtime-encoding-hygiene-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/pdf/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs: `docs/2026-03-15/codebase-global-log-evidence-merged-3pass-audit.md`; `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`
Evidence Artifacts: `docs/2026-03-15/codebase-global-log-evidence-merged-source-inventory.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-hotspot-ranking.txt`; `docs/2026-03-15/codebase-global-log-evidence-merged-runtime-log-db-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- Repair confirmed mojibake and corrupted operator-facing text in active source.
- Restore trust in operator/output encoding by making hygiene tooling safe on the current Windows cp949 host as well as on UTF-8-aware editors.
- Keep future touched-file UTF-8 enforcement credible instead of forcing operators to ignore false alarms or shell crashes.

## 2. Baseline Facts
- Confirmed source corruption remains in active files such as `main_a.py` and `modules/core/session_logger.py`.
- Current runtime artifacts show that durable JSONL and DB sinks can still be UTF-8-clean while source comments, literal strings, and shell-host emission remain unsafe.
- `scripts/check_utf8_hygiene.py` remains part of the control surface for future edits, so detector correctness and shell-safe output are part of this lane.

## 3. Scope
Included:
- `main_a.py`
- `modules/core/session_logger.py`
- `modules/core/services/ui_service.py`
- `modules/core/studio_visualizer.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/main.js`
- `modules/core/logger.py`
- `scripts/check_utf8_hygiene.py`
- targeted tests for hygiene and shell-safe output

Excluded:
- runtime DB/schema refactors
- audit-summary finalization logic
- desktop reconnect or prompt-transport lifecycle changes
- historical docs and archived evidence

## 4. Pass 1. Inventory Summary
- There are two real surfaces, not one:
  - corrupted or mojibake-like active source text
  - unsafe output/render paths for tooling and host-visible snippets
- Runtime evidence narrows this lane:
  - structured sinks are not globally broken
  - the problem is scoped to source text plus operator/output boundaries

## 5. Pass 2. Semantic Classification
- Class A: real corrupted literals and comments in active runtime or control-plane files
- Class B: shell-unsafe emission and snippet formatting in tooling
- Class C: detector grammar that must distinguish real corruption from legitimate Korean prompts

## 6. Side-Effect Map
- file writes / artifacts:
  - touched source files, tooling, tests, and possibly contract docs only
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - indirect only; runtime log readability should improve, but this lane does not redesign sink ownership
- console / UI / operator output:
  - direct primary effect
- rollback / recovery / retry:
  - not primary
- cache / global state:
  - not primary
- bootstrap fallback / config-env mutation:
  - not primary

## 7. Realization Architecture
- Repair active source file text first.
- Make `check_utf8_hygiene.py` and any adjacent operator-facing tooling emit shell-safe output without losing diagnostic fidelity.
- Keep the detector strict on true corruption but bounded enough for legitimate Korean prompt text and ordinary punctuation.

## 8. Execution Tranches
1. Enumerate and repair confirmed mojibake in the scoped source files.
2. Harden the hygiene tool and adjacent output helpers for cp949-safe emission and stable snippets.
3. Add regression cases for:
   - true-positive corruption
   - legitimate Korean prompts
   - shell-safe output on the current Windows host

## 9. Acceptance Criteria
- No scoped active source file contains confirmed mojibake or corrupted operator-visible text.
- The hygiene tool no longer crashes when findings include emoji or non-cp949 text.
- Legitimate Korean prompts do not become routine false positives.
- The lane does not mask true corruption just to reduce noise.

## 10. Verification Plan
- `python scripts/check_utf8_hygiene.py <touched files>`
- targeted pytest for hygiene tool behavior and shell-safe output
- `python -m py_compile` for touched Python files
- optional spot-check of source snippets that previously displayed corrupted text

## 11. Guardrails
- Do not mass-rewrite unrelated docs or corpora in this lane.
- Do not downgrade the detector into a pass-through tool.
- Do not claim runtime sink repair from this lane alone.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove temp mirror only after realization is validated and closed
- roadmap dependency: second item in `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md`

## 13. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- bundle validator: `python scripts/validate_deep_global_survey_bundle.py --survey-doc docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
