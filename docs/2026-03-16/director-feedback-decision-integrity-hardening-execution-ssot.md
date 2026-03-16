# director-feedback-decision-integrity-hardening Execution SSOT

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/director-feedback-decision-integrity-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/director-feedback-decision-integrity-hardening-execution-ssot.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: wide workspace code/docs changes already present; OPUS memo re-audit and survivor queue promotion in progress`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `lane implemented in live code/tests; awaiting temp cleanup`
Source Survey Docs:
- `docs/2026-03-16/opus-survivor-intake-authority-reclassification.md`
- `docs/2026-03-15/opus/detail-subsystem-tf-consolidated-ssot.md`
Evidence Artifacts:
- `docs/2026-03-16/opus-survivor-intake-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent
- Correct live decision-integrity defects that directly distort retry feedback and Director approval outcomes.
- Realize only the survivor items still supported by live code: `TF-FB-01`, `TF-FB-02`, `TF-DG-01`, `TF-DG-02`.

## 2. Baseline Facts
- `FeedbackSystem.quantify_reject_feedback()` still ignores the `score_breakdown` lookup result and synthesizes quantities heuristically.
- `DirectorGrading.on_approve_workflow()` still approves if any update is applied, even when some updates are rejected.
- `DirectorGrading` category mapping still duplicates `commercial_appeal` and `emotion_arc` across multiple buckets.

## 3. Scope
Included:
- `modules/core/feedback_system.py`
- `modules/domain/agents/director_grading.py`
- targeted tests for feedback quantification and approval workflow semantics

Excluded:
- scoring-validator design-tradeoff items already classified as closed or memo-only
- continuity fail-open items owned by another lane
- Stage 4 escalation logging and history-context work

## 4. Pass 1. Inventory Summary
- Survivor count in this lane: `4`
- Main hotspots:
  - fabricated quantitative retry guidance
  - partial reject approval masking
  - non-uniform hidden category weighting

## 5. Pass 2. Semantic Classification
- Class A: fabricated or misleading feedback numbers (`TF-FB-01`, `TF-FB-02`)
- Class B: approval masking under mixed applied/rejected updates (`TF-DG-01`)
- Class C: hidden category-score duplication (`TF-DG-02`)

## 6. Side-Effect Map
- file writes / artifacts:
  - no primary artifact-format changes
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - optional decision diagnostics may change
- console / UI / operator output:
  - feedback wording and approval semantics can change operator-visible outcomes
- rollback / recovery / retry:
  - direct scope because retry feedback is the primary target
- cache / global state:
  - not primary
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Convert feedback quantification to consume actual scored evidence or an explicit bounded fallback contract.
- Make approval semantics fail-closed when any rejected update remains.
- Normalize category mappings so each metric contributes intentionally once.

## 8. Execution Tranches
1. Repair `quantify_reject_feedback()` to use real score inputs or explicit fallback markers.
2. Fix partial-reject approval masking in `DirectorGrading`.
3. Normalize duplicate category weighting and add focused regression tests.

## 9. Acceptance Criteria
- feedback quantification no longer fabricates numeric detail while discarding available score inputs
- mixed applied/rejected update sets do not report blanket approval
- category score composition reflects intentional weighting only once per metric

## 10. Verification Plan
- targeted pytest for `feedback_system.py`
- targeted pytest for `director_grading.py`
- `python -m py_compile` for touched Python files

## 11. Guardrails
- Do not widen this lane into broad scoring-model redesign.
- Do not hide approval-policy changes behind cosmetic logging.
- Do not keep heuristic numbers unless they are labeled as heuristics and bounded by explicit contract.

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition: remove the mirror after realization and closure
- roadmap dependency: `docs/2026-03-16/opus-survivor-followup-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Notes
- Implemented:
  - `FeedbackSystem.quantify_reject_feedback()` now consumes `score_breakdown` evidence when present and labels heuristic output explicitly when it is not.
  - `DirectorGrading.on_approve_workflow()` now fail-closes mixed applied/rejected update sets.
  - `DirectorGrading._extract_category_score()` no longer duplicates `commercial_appeal` or `emotion_arc` across multiple buckets.
- Verification:
  - `python -m py_compile modules/core/feedback_system.py modules/domain/agents/director_grading.py tests/test_feedback_system.py tests/test_director_modules.py`
  - `python -m pytest tests/test_feedback_system.py tests/test_director_modules.py`
  - `python scripts/check_utf8_hygiene.py modules/core/feedback_system.py modules/domain/agents/director_grading.py tests/test_feedback_system.py tests/test_director_modules.py`
- Residual risk:
  - none within this bounded lane; broader scoring-model redesign remains intentionally out of scope.
