<!-- [참고자료] -->
# Runtime Bootstrap / Pytest Memory Incident Context Summary

Date: 2026-03-14
Status: active incident context
Confidence: 95%

## 1. Current Code State
- `residual-print-ui-log-db-full-survey-3pass` is completed.
- `stage0-operator-surface-contract-hardening` is completed.
- `runtime-bootstrap-orchestration-hardening` is in progress.
- `main_a.py` now has explicit boot/shutdown helper seams:
  - `_bind_selected_project()`
  - `_restore_boot_runtime_state()`
  - `_ensure_project_genre_alignment()`
  - `_initialize_project_genre_runtime()`
  - `_initialize_project_runtime_support()`
  - `_shutdown_log()`
  - `_persist_shutdown_*()`
  - `_close_shutdown_resources()`

## 2. Safety Judgment
- The latest `main_a.py` slice does not currently show an immediate structural failure.
- Static validation passed after the slice:
  - `python -m py_compile main_a.py`
  - `python scripts/ops_validator.py --strict`
- Further `main_a.py` refactor work is still on hold until the pytest-related memory incident is better understood.

## 3. Observed Incident
- After running `pytest`, Codex stopped responding first.
- The IDE froze next.
- The IDE showed a reopen/close prompt.
- The machine was shut down before a possible blue-screen escalation.

## 4. Working Hypotheses
- Most likely: heavy test output + pytest capture + IDE/Codex rendering pipeline overload.
- Plausible amplifier: Windows stdio/capture/process behavior.
- Plausible amplifier: parallel or multi-surface test execution.
- Less likely as sole cause: the latest `main_a.py` slice itself.

## 5. Temporary Operating Rule
- On this machine, avoid routine `pytest` runs during normal implementation work.
- Prefer low-output static checks and documentation updates.
- If pytest reproduction is needed, use a controlled run with file logging so the output path is observable.

## 6. Next Decision Gate
- If controlled pytest reproduction shows the same freeze pattern, treat the incident as a test-execution-surface problem first.
- If controlled reproduction is stable, re-evaluate whether the local environment or prior output load was the main trigger.
