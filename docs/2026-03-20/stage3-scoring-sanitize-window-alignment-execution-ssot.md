# Stage 3 Scoring Sanitize Window Alignment Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage3-scoring-sanitize-window-alignment-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-scoring-sanitize-window-alignment-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-20/rol-low-trust-mmmm-second-tranche-reaudit-3pass-audit.md`
- `docs/mmmm/T04-stage3-pipeline-survey.md`
- `docs/mmmm/T14-validation-pipeline-survey.md`
Evidence Artifacts:
- `modules/validation/scoring_validator.py`
- `modules/core/constants.py`
- `config/settings/validation.yaml`
Side-Effect Coverage:
- config threshold read at import/runtime
- LLM scoring prompt payload length
- validation score / PASS threshold outcome
Commit State:
- Baseline Commit: `9a4f46a8f8193c42e236cf181e0151b26a3167b4`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent
- Align Stage 3 LLM scoring window with actual manuscript length policy.
- Stop silently evaluating only the first 3000 characters of a manuscript whose minimum accepted length is 4000 and target length is 5000.
- Keep the patch bounded to scoring-window behavior and observability only.

## 2. Baseline Facts
- `modules/validation/scoring_validator.py` currently reads:
  - `_SANITIZE_MAX_CHARS = int(_threshold("scoring.sanitize_max_chars", 3000))`
- `config/settings/validation.yaml` currently pins:
  - `sanitize_max_chars: 3000`
- `modules/core/constants.py` manuscript limits remain:
  - `MIN_LENGTH = 4000`
  - `TARGET_LENGTH = 5000`
  - `MAX_LENGTH = 15000`
- current scoring path truncates silently:
  - `_sanitize_manuscript()` returns `sanitized[:_SANITIZE_MAX_CHARS]`

## 3. Problem Statement
- Stage 3 quality scoring can evaluate only the first 3000 characters of a manuscript.
- That under-covers the minimum accepted manuscript length and significantly under-covers the target length.
- This can bias scoring toward strong openings and hide weak later sections.

## 4. Scope

Included:
- `modules/validation/scoring_validator.py`
- `config/settings/validation.yaml`
- targeted validation tests

Excluded:
- global validation redesign
- Stage 4 CoVe / Director semantics
- raw manuscript generation length policy
- full genre-weight rework

## 5. Side-Effect Map
- raising the sanitize window increases LLM scoring input length
- validation cost may rise modestly
- validation scores may shift because more manuscript text is visible
- no DB schema change is intended
- no queue/roadmap change beyond this single item is intended

## 6. Execution Shape

### Tranche 1. Window Alignment
- raise the default scoring sanitize window to a value aligned with manuscript policy
- preferred direction:
  - default should be at least `ManuscriptLimits.TARGET_LENGTH`
  - config override remains allowed

### Tranche 2. Truncation Observability
- add a small signal when truncation actually occurs
- acceptable forms:
  - debug/logging note
  - returned scoring metadata flag
- do not add noisy operator-facing warnings by default

### Tranche 3. Regression Lock
- update targeted tests so the new default and truncation metadata are pinned

## 7. Acceptance Criteria
- Stage 3 scoring no longer defaults to 3000 characters when manuscript target length is 5000
- config override still works
- truncation, if it still occurs, is observable in a bounded way
- targeted validation tests pass
- no unrelated validation semantics change

## 8. Verification Plan
- `python -m pytest tests/test_validation.py -q`
- `python -m pytest tests/test_validation_orchestrator.py -q`
- any narrower scoring-specific shard if available
- `python scripts/check_utf8_hygiene.py ...`
- `git diff --check -- ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 9. Guardrails
- do not widen this into a full validation-pipeline refactor
- do not change score thresholds in the same item
- do not reopen the parallel-path topic in the same patch
- keep the patch bounded to scoring-window alignment and its immediate tests

## 10. Completion Signal
- canonical doc updated to `closed`
- temp mirror removed
- queue-state synced back to empty mode

## 11. Closure Note
- `modules/validation/scoring_validator.py` now aligns the sanitize window with `ManuscriptLimits.TARGET_LENGTH` via the threshold default path.
- Stage 3 scoring results now expose bounded `scoring_input_meta` so truncation is observable without widening operator-facing warnings.
- targeted shards passed:
  - `python -m pytest tests/test_validation.py -q`
  - `python -m pytest tests/test_validation_orchestrator.py -q`
  - `python -m py_compile modules/validation/scoring_validator.py`
