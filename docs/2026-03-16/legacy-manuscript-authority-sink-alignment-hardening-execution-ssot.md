# legacy-manuscript-authority-sink-alignment-hardening Execution SSOT

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: runtime/stage modules and tests, desktop package/icon/version files, project 0/000 artifacts and db, OPUS manuscript docs, and untracked 2026-03-16 survey docs`
- Resume Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Resume Drift Summary: `same commit; fresh run artifacts and db rows changed in projects/0 and projects/000, so the SSOT was re-audited against post-run merge evidence`
Source Survey Docs:
- `docs/2026-03-16/manuscript-contradiction-audit-opus-revalidation.md`
- `docs/2026-03-16/legacy-real-manuscript-contradiction-survey.md`
- `docs/2026-03-16/legacy-manuscript-current-recurrence-supplemental-survey.md`
- `docs/2026-03-16/legacy-manuscript-contradiction-synthesis-master-report.md`
- `docs/2026-03-16/legacy-manuscript-fresh-run-post-run-merge-audit.md`
Evidence Artifacts:
- `docs/2026-03-16/manuscript-contradiction-audit-opus-revalidation-evidence.txt`
- `docs/2026-03-16/legacy-real-manuscript-contradiction-survey-evidence.txt`
- `docs/2026-03-16/legacy-manuscript-current-recurrence-supplemental-survey-evidence.txt`
- `docs/2026-03-16/legacy-manuscript-contradiction-manual-survey-and-current-risk-assessment-evidence.txt`
- `docs/2026-03-16/legacy-manuscript-fresh-run-post-run-merge-evidence.txt`
Side-Effect Coverage: covered

## 1. Intent

- Formalize the final-authority contract after Stage 4 patch/finalization.
- Prevent operators, analyzers, and future surveys from treating `director_selections` as standalone final truth.
- Bound the handling of pre-existing stale legacy rows without widening into broad contradiction remediation.

## 2. Baseline Facts

- `legacy-real-manuscript-contradiction-survey.md` confirmed no surviving hard contradiction in the bounded final/patched authority manuscripts.
- `legacy-manuscript-fresh-run-post-run-merge-audit.md` confirmed that the fresh bounded run in `projects/0` did not reproduce stale content-hash drift; `ep1-6` all aligned, including patched `ep5`.
- The same post-run merge audit confirmed that `projects/000` had only a startup/shutdown control run on `2026-03-16`; its persisted real production rows for `20260315_190609` also aligned.
- The historical stale-authority pattern remains real in `projects/00_260315 ep4-5`, where `stage_attempts` and DB manuscripts match patched text while `director_selections` still points to `selected_before_fix`.
- Current consumer surfaces still risk over-trusting `director_selections` unless final authority order is explicit.

## 3. Scope

Included:

- `modules/core/db_manager.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/stage4_interview_round.py` only if explicit final-authority projection or metadata surfacing is required
- any thin audit/report/helper surface that still presents `director_selections` as if it were final authority
- targeted tests covering:
  - `PASS_WITH_FIX` lineage resolution
  - `director_selections` vs `stage_attempts` vs final artifact authority order
  - analyzer/report behavior and legacy mismatch surfacing

Excluded:

- broad continuity-validator redesign
- numeric/title/relationship drift hardening beyond authority-sink semantics
- archival/test project full backfill rewrites
- full legacy manuscript re-survey outside the already-completed bounded real-project set

## 4. Pass 1. Inventory Summary

- confirmed execution-worthy issue classes: `1`
- issue class:
  - final-authority contract ambiguity and legacy stale metadata interpretation
- overlapping evidence sources:
  - historical real-project artifacts
  - fresh bounded post-run merge audit
  - current audit/analyzer consumers
- main hotspots:
  - final-authority resolution after `PASS_WITH_FIX`
  - patched/final artifact metadata semantics
  - consumer surfaces that may read `director_selections` alone
  - legacy stale-row surfacing policy

## 5. Pass 2. Semantic Classification

- Class A: final-authority contract
  - define where final truth lives after patch/finalization
- Class B: metadata projection / consumer contract
  - prevent single-table misread by audit/report surfaces
- Class C: legacy mismatch handling
  - decide whether to surface, mark, or bounded-backfill known stale rows
- Class D: regression proof
  - codify the authority order in tests so the old class cannot silently re-enter

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage 4 patched/final authority references may change or be projected differently
- DB / schema / transaction boundaries:
  - `director_selections`, `stage_attempts`, and any explicit authority projection are direct scope
- JSONL / log / audit sinks:
  - analyzer/canary outputs may change authority wording, mismatch status, or legacy warning behavior
- console / UI / operator output:
  - operator-facing explanations of final authority may change
- rollback / recovery / retry:
  - patch/retry interpretation and legacy-mismatch handling are direct scope
- cache / global state:
  - not primary
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- Preserve the historical value of `director_selections` as candidate/review history.
- Make explicit that final authority is resolved from stronger sinks than `director_selections` when patch/finalization occurred.
- Acceptable shapes:
  1. add or expose an explicit final-authority projection with artifact path/hash and status
  2. or leave storage mostly unchanged, but make every inspected consumer resolve final truth from `stage_attempts + manuscripts/episode_production + final/patched artifact`
  3. optionally add a bounded legacy-mismatch marker or backfill tool for previously stale rows
- The key requirement is elimination of `single-table stale authority` as an easy operator mistake, not forcing one exact schema rewrite.

## 8. Execution Tranches

1. Final-authority contract
   - decide and implement the final-authority source of truth for `PASS_WITH_FIX` and patched-final cases
   - either expose explicit final-authority projection or make resolver order explicit in inspected consumers

2. Consumer hardening
   - update analyzer/report/helper surfaces so `director_selections` cannot be presented as standalone final authority
   - make authority order explicit in code and operator-facing summaries

3. Legacy mismatch handling
   - decide how historical stale rows are surfaced or normalized
   - keep the action bounded to real stale examples, not all archived projects

4. Regression proof
   - add focused tests covering:
     - `selected_before_fix` vs `patched_after_fix`
     - authority resolution after patch
     - analyzer/report handling when the sinks differ
     - fresh aligned run behavior staying green

## 9. Acceptance Criteria

- after `PASS_WITH_FIX`, final authority is no longer ambiguous to code or operators
- `director_selections` alone cannot be mistaken for final truth in the main inspected consumer surfaces
- fresh aligned cases like `projects/0 ep5` remain green under the new contract
- regression tests explicitly lock the final-authority order
- legacy stale-authority rows like `00_260315 ep4-5` are either normalized or explicitly surfaced as non-final historical metadata

## 10. Verification Plan

- targeted pytest for Stage 4 persistence/save flow
- targeted pytest for DB manager selection/attempt persistence behavior
- targeted pytest for failure analyzer / canary authority alignment behavior
- targeted pytest for any legacy mismatch marker/backfill helper if one is introduced
- `python -m py_compile` for touched Python files
- `python scripts/check_utf8_hygiene.py` for touched docs/code/tests
- `python scripts/ops_validator.py --strict` after mirror refresh and after later realization

## 11. Guardrails

- Do not widen this lane into broad contradiction remediation based only on OPUS memo totals.
- Do not erase historical candidate-review evidence in `director_selections` if operators still need it.
- Do not patch only one sink while leaving operator-facing consumers able to misread stale authority.
- Do not claim the latest fresh run reproduced drift when the merged audit says it did not.
- Do not claim full contradiction prevention; this lane is about `final authority alignment`, not every continuity class.

## 12. Temp Queue Notes

- temp status: closed
- cleanup condition: canonical closure completed; remove the mirror after validator-confirmed queue cleanup
- roadmap dependency: none; this is a single active execution SSOT

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Update

Date: 2026-03-16
Status: closed
Canonical Roadmap Path: `docs/2026-03-16/legacy-manuscript-authority-sink-alignment-execution-roadmap.md`
Temp Mirror Path: `removed during closure (was docs/temp/legacy-manuscript-authority-sink-alignment-hardening-execution-ssot.md)`

Realized scope:

- added `DBManager.get_stage4_final_authority_rows()` so Stage 4 final authority resolves explicitly from `stage_attempts`
- hardened `FailureAnalyzer.sink_alignment_summary()` to surface `final_authority_contract` and `selection_companion_pre_final_rows` without over-reading `director_selections` as final truth
- propagated the explicit authority contract into `stage4_canary_tools.build_stage4_canary_summary()`
- added focused regression coverage in `tests/test_db_manager.py`, `tests/test_failure_analyzer.py`, and `tests/test_stage4_canary_tools.py`

Verification summary:

- pre-execution validity stage:
  - `python -m pytest tests/test_db_manager.py -k "save_stage_attempt_and_director_selection_persist_attempt_key or update_director_selection_rationale_updates_latest_attempt_row"`
  - `python -m pytest tests/test_failure_analyzer.py -k "sink_alignment_summary_reports_artifact_linkage_issues or sink_alignment_uses_selection_candidate_key_from_episode_production_when_available"`
- post-implementation compile and targeted verification:
  - `python -m py_compile modules/core/db_manager.py modules/core/failure_analyzer.py modules/core/stage4_canary_tools.py tests/test_db_manager.py tests/test_failure_analyzer.py tests/test_stage4_canary_tools.py`
  - `python -m pytest tests/test_db_manager.py`
  - `python -m pytest tests/test_failure_analyzer.py`
  - `python -m pytest tests/test_stage4_canary_tools.py`

Residual risks:

- no schema backfill was applied to historical `director_selections` rows; this lane formalizes resolver order and consumer wording instead
- fresh bounded run `projects/0` remained aligned before implementation, so the realized risk class is historical companion-row misread, not a newly reproduced live corruption
- no full end-to-end desktop/runtime live rerun was executed in this closure turn

Temp cleanup:

- execution SSOT mirror removed: yes
- roadmap mirror removed: yes
- queue-state removed: yes
