<!-- [참고자료] -->
# Codebase Stagewise Deep Global Survey Draft

Date: 2026-03-15
Status: draft-live-run-pending
Canonical Intent: per-stage deep survey across Stage `0~4` during an active live run
Project: `projects/000`
Structured Session Id: `20260315_190609`
Observed Plain Log Token: `20260315_190600`
Process State:
- `python main_a.py` still alive
- bounded Stage 4 content slice appears complete through episode `6`
- application terminal shutdown state not yet observed
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Evidence:
- `docs/2026-03-15/codebase-stagewise-live-merge-000-session_20260315_190609-stagewise-evidence.txt`
- `docs/2026-03-15/codebase-stagewise-live-merge-000-session_20260315_190609-live-run-evidence-manifest.md`
- `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-investigation.md`
- `docs/2026-03-15/codebase-global-log-evidence-merged-deep-global-survey.md`

## 1. Survey Frame
- This is a stagewise expansion of the existing global survey bundle.
- It is not a final closure note because live evidence is still moving.
- The survey is organized by Stage `0`, `1`, `2`, `3`, `4`, then cross-cut substrate.

## 2. Stage 0
Primary source surfaces:
- `modules/core/stage01_helpers.py`
- `modules/core/stage0/`
- Stage 0 related tests around style, POV, and frontend connectivity

Current live evidence:
- Stage 0 menu/setup surfaces appear in the session log.
- `projects/000/stage0_output/style_guide.json` exists and was written early in the run.

Draft findings:
- Stage 0 still shares authority with Stage 1 inside `stage01_helpers.py`, so stage-boundary ownership is not clean.
- Current runtime evidence only confirms the style-guide save path, not the full Stage 0 branch matrix.
- Stage 0 remains operator-heavy and prompt-heavy; prompt surface stability should continue to be treated as a first-class risk.

Draft risk classification:
- `P2 source-led`
- biggest uncertainty: branch coverage, not current hard failure evidence

## 3. Stage 1
Primary source surfaces:
- `modules/core/stage01_helpers.py`
- minimal dedicated tests

Current live evidence:
- no Stage 1 execution in the current run

Draft findings:
- Stage 1 has the smallest dedicated code surface and is effectively nested inside Stage 0/1 helper ownership.
- Because the current fresh run skipped Stage 1, this lane is source-led only in this draft.
- The stage is easy to under-observe because it lacks strong dedicated runtime artifacts relative to later stages.

Draft risk classification:
- `P3 source-led`
- main concern is observability and boundary clarity rather than a proved runtime defect

## 4. Stage 2
Primary source surfaces:
- `main_a.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_optimizer.py`

Current live evidence:
- `stage_attempts`: 2 rows for Stage 2
- `director_selections`: 2 rows for Stage 2
- `logs/artifacts/stage2`: 2 final arc artifacts
- live log shows Arc 1 and Arc 2 completed
- repeated runtime warning says Arc 1 lacks `constraint_summary`

Draft findings:
- Stage 2 output generation itself looks durable in the current run.
- The stronger risk is not immediate generation failure but downstream handoff quality.
- The repeated `constraint_summary` omission warning suggests Stage 2 may under-deliver constraint context into later stages even when Stage 2 itself passes.

Draft risk classification:
- `P1 source+live`
- probable problem type: `successful generation with partial downstream contract erosion`

## 5. Stage 3
Primary source surfaces:
- `main_a.py`
- `modules/core/stage3_orchestrator.py`
- blueprint agent and validator surfaces

Current live evidence:
- `stage_attempts`: 7 rows for Stage 3
- `director_selections`: 7 rows for Stage 3
- `plans/blueprints`: 7 files
- `logs/artifacts/stage3`: 7 files
- live log shows both Arc 1 and Arc 2 Stage 3 completions

Draft findings:
- Stage 3 is producing artifacts consistently in the current run.
- FrontierLag backlog behavior appears to be functioning: blueprint frontier advances ahead of manuscripts.
- The main Stage 3 risk in this draft is downstream:
  - Stage 3 metadata and constraints must survive into Stage 4
  - current summary surfaces lag behind later Stage 4 writes, so Stage 3 completion should not yet be treated as globally finalized

Draft risk classification:
- `P2 live`
- likely issue is not blueprint generation failure but incomplete finalization/lineage visibility while the app remains open

## 6. Stage 4
Primary source surfaces:
- `main_a.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/director_ensemble.py`

Current live evidence:
- `stage_attempts`: 11 Stage 4 rows
- `director_selections`: 11 Stage 4 rows
- `drafts`: 6 final manuscript files
- `logs/artifacts/stage4`: 21 files
- episode 4 and 5 show multi-round retry/reject/pass cycles in `decisions.jsonl`
- rationale fields are present in structured sinks

Draft findings:
- Stage 4 remains the dominant complexity and failure surface.
- The current run reinforces the earlier interpretation:
  - Director critique surfaces are rich
  - CW retry payload is rich
  - but carryover quality is still vulnerable after repeated budget trims and retry loops
- Structured sinks still show mojibake-like operator text in payloads, so Stage 4 observability remains text-corrupted even when the lineage fields exist.
- Episode 4 and 5 retries show the system can persist detailed reasons, but they also show how much reasoning volume accumulates before final pass.

Draft risk classification:
- `P1 live`
- dominant problem type:
  - `context compression / retry-loop pressure`
  - `structured-text mojibake in human-facing payloads`

## 7. Cross-Cut Stage Dependencies
- Stage 0 and Stage 1 share helper authority.
- Stage 2 constraint truth is expected downstream by Stage 3 and Stage 4.
- Stage 3 blueprint/meta truth is a prerequisite for reliable Stage 4 continuity.
- Stage 4 depends on recent manuscript history, world state, relation slices, and prior rationale.
- Current runtime summary and pass-rate artifacts lag behind the later Stage 4 writes, so cross-stage finalization is not quiescent yet.

## 8. Provisional Global Ranking
1. Stage 4
2. Stage 2 to Stage 4 handoff
3. Stage 3 finalization visibility
4. Stage 0 prompt-heavy authority
5. Stage 1 observability thinness

## 9. Draft Conclusions
- The stagewise picture is not "all stages failing equally."
- Current live evidence points to:
  - Stage 4 as the main active risk surface
  - Stage 2 handoff quality as an upstream amplifier
  - Stage 3 as operationally stable but not yet fully finalized at the observability layer
  - Stage 0/1 as lighter but still structurally under-separated
- Final severity and execution decisions must wait for a true terminal app state.
