# Stage2 Headless Prompt Remediation Execution SSOT

Date: 2026-04-20
Status: closed
Canonical Path: `docs/2026-04-20/stage2-headless-prompt-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage2-headless-prompt-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `466bbe4c1bc400d4539fb8ad19fa001856b8acce`
- Baseline Dirty Summary: `dirty: .gitignore modified; local sensitive recovery-code file now ignored`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-20/stage2-headless-prompt-remediation-bounded-survey.md`
- `docs/2026-04-20/stage2-headless-prompt-remediation-3pass-audit.md`
Evidence Artifacts:
- `docs/2026-04-20/stage2-headless-prompt-remediation-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent

Remove Stage2 failure-path and completion prompt blocking from explicitly headless runs while preserving the existing interactive CLI and desktop prompt-broker behavior.

## 2. Baseline Facts

- Stage2 failure-path retry exhaustion currently enters an operator prompt loop
- Stage2 completion currently pauses for Enter when `target_arc_count is None`
- desktop prompt-broker runs must remain interactive even though transport may be non-TTY
- dedicated Stage2 headless runner exists and is the safest bounded opt-in surface for this change

## 3. Scope

Included:

- `modules/core/stage2_orchestrator.py`
- `scripts/canary_stage2_headless.py`
- optional dedicated script-side headless-contract alignment if needed
- targeted tests for headless auto-abort and completion pause suppression

Excluded:

- bridge auth / UI hardening
- Stage3 / Stage4 prompt behavior
- broad Stage2 contract normalization or refactor

## 4. Pass 1. Inventory Summary

- primary runtime owner: `Stage2Orchestrator`
- supporting bounded entrypoint: `scripts/canary_stage2_headless.py`
- prompt surfaces to preserve:
  - default interactive failure handling
  - desktop prompt-broker behavior
- prompt surfaces to suppress in headless mode:
  - retry-exhausted operator choice loop
  - Stage2 completion Enter pause

## 5. Pass 2. Semantic Classification

- Class A. Must change
  - failure-path operator prompt in explicit headless runs
  - completion pause in explicit headless runs
- Class B. Must preserve
  - normal interactive CLI prompt behavior
  - desktop prompt-broker behavior
- Class C. Guardrails
  - do not infer headless from `target_arc_count`
  - do not infer headless from non-TTY alone

## 6. Realization Architecture

Preferred shape:

1. add a Stage2-local helper that resolves an explicit headless failure policy
2. default that helper to `prompt`
3. let dedicated headless scripts opt into `abort`
4. reuse the same policy to suppress the Stage2 completion pause

This is a bounded runtime contract change, not a broader interaction-stack rewrite.

## 7. Execution Tranches

1. add Stage2 headless-policy helpers and wire failure handling
2. suppress Stage2 completion pause under the same headless policy
3. activate the policy from the dedicated Stage2 headless runner
4. add targeted regression tests
5. run compile and targeted pytest verification

## 8. Acceptance Criteria

- explicit headless Stage2 runs do not call `input()` on retry exhaustion
- explicit headless Stage2 runs abort after writing failure evidence
- explicit headless Stage2 runs do not pause for Enter on completion
- default interactive Stage2 behavior remains prompt-driven
- desktop-mode prompt bridge is not reclassified as headless by this wave

## 9. Verification Plan

- `python -m py_compile modules/core/stage2_orchestrator.py scripts/canary_stage2_headless.py tests/test_stage2_orchestrator_lane_f.py`
- targeted pytest on Stage2 prompt-contract tests
- optional headless canary contract test refresh if touched

## 10. Guardrails

- do not change retry counts or retry semantics
- do not silently convert desktop bridge runs into auto-abort
- do not mix this with bridge auth, logging, or Stage4 architecture work
- if the fix needs a broader prompt-stack contract, stop and reopen survey scope

## 11. Temp Queue Notes

- compact realization rule:
  - this item is allowed to realize in the same turn after the governing audit
  - realization completed in the same turn, so no temp mirror is retained in `docs/temp/`

## 12. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- execution-start rule:
  - recheck this document against live code before patching

## 13. 3-Pass Audit Record

Pass 1:

- scope stayed bounded to Stage2 prompt suppression for explicit headless runs
- desktop / bridge and broader Stage2 architecture were kept out of scope

Pass 2:

- implementation kept the new policy explicit via env seam rather than heuristics
- failure-report writing remains intact before auto-abort
- completion pause suppression reuses the same bounded policy

Pass 3:

- verification is direct and targeted
- queue overreach was avoided by closing the item in the same turn

Confidence: `97/100`

## 14. Closure Note

- closure date: `2026-04-20`
- implementation result:
  - `modules/core/stage2_orchestrator.py` now suppresses failure-path prompts only when explicit Stage2 headless policy is enabled
  - the same policy suppresses the Stage2 completion Enter pause
  - `scripts/canary_stage2_headless.py` now enables that explicit Stage2 headless policy
  - `scripts/run_stage2_smoke.py` now enables the same explicit Stage2 headless policy for unattended smoke execution
  - `tests/test_smoke_fixture_contract.py` now pins that smoke entrypoint contract
  - default interactive Stage2 behavior remains prompt-driven
- verification evidence:
  - `python -m py_compile modules/core/stage2_orchestrator.py scripts/canary_stage2_headless.py tests/test_stage2_orchestrator_lane_f.py`
  - `ruff check modules/core/stage2_orchestrator.py scripts/canary_stage2_headless.py tests/test_stage2_orchestrator_lane_f.py`
  - `python scripts/check_utf8_hygiene.py modules/core/stage2_orchestrator.py scripts/canary_stage2_headless.py tests/test_stage2_orchestrator_lane_f.py docs/2026-04-20/stage2-headless-prompt-remediation-evidence.txt docs/2026-04-20/stage2-headless-prompt-remediation-bounded-survey.md docs/2026-04-20/stage2-headless-prompt-remediation-3pass-audit.md docs/2026-04-20/stage2-headless-prompt-remediation-execution-ssot.md`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_stage2_orchestrator_lane_f.py tests/test_run_stage2_canary.py` -> `9 passed`
  - `python -m py_compile scripts/run_stage2_smoke.py tests/test_smoke_fixture_contract.py modules/core/stage2_orchestrator.py scripts/canary_stage2_headless.py tests/test_stage2_orchestrator_lane_f.py`
  - `ruff check scripts/run_stage2_smoke.py tests/test_smoke_fixture_contract.py modules/core/stage2_orchestrator.py scripts/canary_stage2_headless.py tests/test_stage2_orchestrator_lane_f.py`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_smoke_fixture_contract.py tests/test_stage2_orchestrator_lane_f.py tests/test_run_stage2_canary.py` -> `16 passed`
- queue effect:
  - no retained temp mirror
  - no parked-board reorder required
- residual risk:
  - current unattended Stage2 entrypoints are aligned on the same explicit contract: `scripts/canary_stage2_headless.py`, `scripts/run_stage2_smoke.py`
  - any future unattended Stage2 entrypoint must opt into the same explicit headless env contract if it needs deterministic auto-abort behavior
