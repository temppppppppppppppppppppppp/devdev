<!-- [미완] -->
# Stagewise Manuscript Truth / Narrative Continuity Follow-Up Execution SSOT

Date: 2026-03-15
Status: closed
Canonical Path: `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-followup-execution-ssot.md`
Temp Mirror Path: `docs/temp/stagewise-manuscript-truth-and-narrative-continuity-followup-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, active roadmap/temp edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked post-remediation docs plus projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `execution-start re-audit passed; bounded manuscript-truth helper, generator script, generated report/json, and targeted tests landed`
Source Survey Docs:
- `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-investigation.md`
- `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-3pass-audit.md`
- `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-followup-3pass-audit.md`
- `docs/2026-03-15/codebase-stagewise-live-merge-000-session_20260315_190609-stagewise-evidence.txt`
- `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-investigation.md`
Evidence Artifacts:
- `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-evidence.txt`
- `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.md`
- `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.json`
- `projects/000/logs/episode_production.jsonl`
- `projects/000/logs/session/decisions.jsonl`
- `projects/000/logs/artifacts/stage2/`
- `projects/000/logs/artifacts/stage3/`
- `projects/000/logs/artifacts/stage4/`
Side-Effect Coverage: covered

## 1. Intent
- Turn the newly confirmed manuscript-truth gap into one bounded execution lane before the broad residual post-remediation follow-up lane.
- Create a reusable audit/report authority for `Stage 2 arc -> Stage 3 blueprint -> Stage 4 terminal manuscript` truth.
- Close the current dependence on ad hoc grep and manual artifact-shape interpretation when a run reaches a patched or retried Stage 4 finish.

## 2. Baseline Facts
- The selected `projects/000` stagewise run has real output artifacts at every process stage:
  - Stage 2 selected arc artifacts: `2`
  - Stage 3 selected blueprint artifacts: `7`
  - Stage 4 artifact files across retries and terminal outputs: `21`
- Entry metadata is asymmetric:
  - Arc 1 selected Stage 2 artifact has a blank `constraint_summary`
  - Arc 2 selected Stage 2 artifact has a populated `constraint_summary`
- Blueprint authority is rich but incomplete:
  - Stage 3 decisions preserve rich reasons
  - Stage 4 Episode 5 still had to reject a candidate because Episode 4's realized all-in ending and Episode 5's blueprint assumptions were in conflict
- Terminal manuscript authority is uneven:
  - some terminal truth lands as `final_manuscript__*.txt`
  - some terminal truth lands as `patched_after_fix__*.txt`

## 3. Scope
Included:
- bounded post-run manuscript-truth surfacing for the selected stagewise run shape
- cross-stage continuity reporting between selected Stage 2 arc truth, Stage 3 blueprint truth, and Stage 4 terminal truth
- terminal Stage 4 artifact-authority normalization where a small implementation or report contract is needed
- decision-doc or report outputs if the bounded lane resolves without code changes

Excluded:
- prompt-contract or menu `7` work
- backend-front/control-plane work
- DB pooling or sink-consolidation realization
- full literary scoring, taste ranking, or market-read judgments
- broad Stage 4 generation redesign

## 4. Pass 1. Inventory Summary
- process stages to compare: `3`
  - Stage 2 arc truth
  - Stage 3 blueprint truth
  - Stage 4 terminal manuscript truth
- strongest continuity hotspot:
  - Episode 4 -> Episode 5 handoff in the selected run
- terminal artifact shapes to normalize:
  - `final_manuscript__*`
  - `patched_after_fix__*`
- direct evidence sinks already available:
  - `decisions.jsonl`
  - `episode_production.jsonl`
  - selected artifact files on disk

## 5. Pass 2. Semantic Classification
- Class A:
  - canonical post-run manuscript-truth report or helper surface
- Class B:
  - cross-episode continuity authority between blueprint pass truth and final manuscript truth
- Class C:
  - terminal artifact-shape normalization for patched-vs-final authority

## 6. Side-Effect Map
- file writes / artifacts:
  - bounded docs, reports, or helper outputs in `docs/2026-03-15/`
  - targeted tests or small audit helpers may be added if the lane grows beyond pure documentation
- DB / schema / transaction boundaries:
  - read-only by default
  - no schema migration is assumed
- JSONL / log / audit sinks:
  - the lane reads `episode_production.jsonl` and `decisions.jsonl`
  - no sink rewrite is assumed unless a successor lane is created
- console / UI / operator output:
  - not primary
- rollback / recovery / retry:
  - preserve current Stage 4 retry semantics
  - this lane explains and surfaces retry truth; it does not redesign the retry engine
- cache / global state:
  - not primary
- bootstrap fallback / config-env mutation:
  - not applicable by default

## 7. Realization Architecture
- Step 1:
  - define one canonical comparison surface for:
    - Stage 2 carryover metadata
    - Stage 3 selected blueprint ending/continuity promises
    - Stage 4 terminal artifact truth
- Step 2:
  - materialize one bounded report or helper that can surface cases like Episode 4 -> Episode 5 without manual grep
- Step 3:
  - normalize post-run treatment of Stage 4 patched finals so `patched_after_fix__*` can be treated as terminal manuscript truth when that is the real winning output
- Step 4:
  - if the bounded report/report-helper work expands into nontrivial runtime code change, split that change into a successor execution SSOT rather than bloating this lane

## 8. Execution Tranches
1. Save the final processwise manuscript-truth investigation and keep its evidence lineage explicit.
2. Produce one bounded manuscript-truth report or helper contract for the selected run shape.
3. Capture one explicit continuity proof path for the Episode 4 -> Episode 5 contradiction-and-repair sequence.
4. Decide whether terminal Stage 4 artifact authority can be normalized as documentation only or needs a small implementation successor.
5. Refresh the master roadmap and temp queue only through this single lane.

## 9. Acceptance Criteria
- A saved artifact can explain the selected run across:
  - Stage 2 carryover metadata truth
  - Stage 3 blueprint truth
  - Stage 4 terminal manuscript truth
- The Episode 4 -> Episode 5 contradiction path and repair path can be surfaced without ad hoc manual grep.
- `patched_after_fix__*` terminal outputs are treated explicitly in the audit authority model rather than as ambiguous leftovers.
- No backend-front, menu `7`, or broad Stage 4 redesign work is reopened inside this lane.

## 10. Verification Plan
- document/queue integrity:
  - `python scripts/ops_validator.py --strict`
- if the lane stays documentation-only:
  - save the bounded report artifacts and keep source-to-evidence lineage explicit
- if the lane grows into code:
  - run targeted pytest shards around the touched audit/helper surfaces only

## 11. Guardrails
- Do not claim a full automated literary-quality verdict.
- Do not reopen the backend-front/runtime operator queue inside this lane.
- Do not silently absorb this lane into `TF-012` through `TF-020` without an explicit roadmap mutation.
- Do not treat missing uniform naming as missing manuscript truth.

## 12. Temp Queue Notes
- temp status: complete
- cleanup condition:
  - temp mirror removed after canonical closure, roadmap refresh, queue-state sync, and validator pass
- roadmap dependency:
  - closed as the predecessor authority for the broad post-remediation unqueued survey follow-up lane

## 13. Validation And Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run this document through the 3-pass audit and confirm at least `95%` confidence against the current workspace state before any realization patching begins

## 14. Closure Notes
- Landed:
  - `modules/core/stagewise_manuscript_truth_report.py`
  - `scripts/generate_stagewise_manuscript_truth_report.py`
  - `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.md`
  - `docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.json`
- Verification:
  - `python -m py_compile modules/core/stagewise_manuscript_truth_report.py scripts/generate_stagewise_manuscript_truth_report.py tests/test_stagewise_manuscript_truth_report.py`
  - `python -m pytest tests/test_stagewise_manuscript_truth_report.py`
  - `python scripts/generate_stagewise_manuscript_truth_report.py --project projects/000 --markdown-output docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.md --json-output docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.json --project-label projects/000`
  - `python scripts/check_utf8_hygiene.py modules/core/stagewise_manuscript_truth_report.py scripts/generate_stagewise_manuscript_truth_report.py tests/test_stagewise_manuscript_truth_report.py docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-followup-3pass-audit.md docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.md docs/2026-03-15/stagewise-manuscript-truth-and-narrative-continuity-report.json`
- Residual risk:
  - the saved report is post-run authority only; it does not move continuity enforcement upstream into Stage 3
- Closure decision:
  - acceptance criteria satisfied
  - this lane is `closed`
  - the next active lane is `post-remediation-unqueued-survey-followups-execution-ssot.md`
