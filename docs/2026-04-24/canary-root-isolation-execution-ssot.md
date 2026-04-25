# Canary Root Isolation Execution SSOT

Date: 2026-04-24
Status: completed (2026-04-25 PR #15 merged canary root isolation; no legacy canary data migration performed)
Canonical Path: `docs/2026-04-24/canary-root-isolation-execution-ssot.md`
Temp Mirror Path: `docs/temp/canary-root-isolation-execution-ssot.md`
Commit State:
- Baseline Commit: `143cee26d879d5de59ef43757f851e89b8d551c7`
- Baseline Dirty Summary: `dirty: local runtime project outputs, benchmark index, .gitignore key ignore, and new 2026-04-24 hygiene docs; no canary code or data migration performed`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `initial documentation-only parking wave`
Source Survey Docs:
- `docs/2026-04-24/canary-root-isolation-plan.md`
- `docs/2026-04-24/canary-root-isolation-adversarial-3pass-audit.md`
- `docs/2026-04-24/repo-trashbox-candidate-survey.md`
- `docs/2026-04-25/canary-root-isolation-fresh-reaudit.md`
Evidence Artifacts:
- `scripts/canary_path_utils.py`
- `scripts/run_stage2_canary.py`
- `scripts/run_stage3_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/run_stage34_ep_demo_canary.py`
- `scripts/run_stage4_canary.py`
- `scripts/canary_stage2_headless.py`
- `modules/core/runtime_paths.py`
- `main_a.py`
- `tests/test_canary_path_utils.py`
- `tests/test_run_stage2_canary.py`
- `tests/test_run_stage3_canary.py`
- `tests/test_run_stage34_canary.py`
- `tests/test_run_stage34_ep_demo_canary.py`
- `tests/test_run_stage4_canary.py`
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: canary-root-isolation
  github_issue: 8
  depends_on: []
  status: completed
  queue_role: historical_backing
  roadmap_rank: null
  tranches:
    - id: helper-contract
      title: Canary path helper contract
    - id: runtime-env-scope
      title: Scoped runtime projects-root binding
    - id: legacy-fallback
      title: Legacy projects/_canary read fallback
    - id: git-hygiene
      title: Generated canary output ignore policy
```

## 1. Intent

Separate future canary run output from normal project storage so `projects/` remains focused on real/operator projects.

The target future shape is:

```text
Geuldobi repo
  projects/
    <operator project>
  canary/
    <generated canary project>
```

This SSOT is now historical backing for the bounded canary root isolation tranche merged on `2026-04-25` via PR #15.

## 2. Current Problem

`projects/_canary/` currently holds large generated proof-run output:

- copied project databases
- runtime logs
- session logs
- drafts and stage artifacts
- canary summaries and companion audits

Local survey found approximately:

```text
projects/_canary/
  size: 933.61 MB
  tracked files: 3,825
```

This makes `projects/` visually noisy and keeps generated canary residue near production project data.

## 3. Scope

Included:

- path helper update for future canary targets
- `GEULDOBI_CANARY_ROOT` optional override
- default future canary root at `<repo>/canary`
- scoped `GEULDOBI_PROJECTS_ROOT=<repo>/canary` during canary runtime boot
- Stage 2 subprocess environment propagation
- legacy read fallback for `projects/_canary`
- `.gitignore` policy for generated `canary/`
- focused test updates

Excluded:

- moving existing `projects/_canary/`
- deleting old canary output
- rewriting historical docs that cite `projects/_canary`
- changing normal `projects/` behavior
- changing formal `tests/` behavior
- changing desktop workspace defaults outside canary execution

## 4. Execution Tranches

1. Canary path helper contract
   - introduce new default `canary/` root
   - keep legacy `_canary` recognition
   - preserve absolute path and explicit `projects/<name>` behavior
2. Scoped runtime projects-root binding
   - bind `GEULDOBI_PROJECTS_ROOT` to `<repo>/canary` only during canary execution
   - restore previous environment state on success and failure
   - pass the scoped environment into Stage 2 subprocess execution
3. Legacy fallback
   - read `canary/<name>` first
   - fall back to `projects/_canary/<name>` only when resolving existing canary evidence
   - keep old evidence usable without migration
4. Git hygiene
   - ignore generated `canary/`
   - avoid tracking copied DBs, logs, artifacts, and drafts
   - leave old `projects/_canary` cleanup as a separate decision

Implementation status on 2026-04-25:

- `scripts/canary_path_utils.py` now routes new canary targets to repo-local `canary/<target>`
- legacy reads still fall back to `projects/_canary/<target>` when `require_exists=True`
- canary runtime scripts now scope `GEULDOBI_PROJECTS_ROOT` during app boot
- Stage 2 subprocess execution now receives the scoped canary runtime environment
- `.gitignore` now ignores generated `canary/` output
- focused validation passed with `py -3.12 -m pytest tests/test_canary_path_utils.py tests/test_run_stage2_canary.py tests/test_run_stage3_canary.py tests/test_run_stage34_canary.py tests/test_run_stage34_ep_demo_canary.py tests/test_run_stage4_canary.py -q`
- GitHub CI passed with `lint`, `syntax-check`, and `test (3.12)`
- merge commit: `fc803ccc94b1ed1fdfe6ea188668300122f8d75c`

## 5. Side-Effect Map

- file writes / artifacts:
  - future canary runs write under `canary/`
  - old `projects/_canary/` remains untouched
- DB / schema / transaction boundaries:
  - no schema change intended
  - copied canary DBs remain generated artifacts
- JSONL / logs:
  - future logs move with the canary project root
  - old logs stay readable through legacy fallback
- console / operator output:
  - canary scripts may show new paths in summaries
  - historical docs are not rewritten
- environment:
  - `GEULDOBI_PROJECTS_ROOT` is scoped during canary execution
  - previous env value must be restored
- rollback:
  - rollback should not require data restoration because old data is not moved

## 6. Acceptance Criteria

- new canary prepare commands create targets under `canary/<target>`
- existing `projects/_canary/<target>` can still be analyzed
- canary runtime boot uses `GEULDOBI_PROJECTS_ROOT=<repo>\canary`
- Stage 2 subprocess receives the same scoped projects root
- normal project commands still resolve through `projects/`
- generated `canary/` output is ignored by Git
- no existing canary data is moved by the implementation

## 7. Verification Plan

Minimum focused verification:

```text
python -m py_compile scripts/canary_path_utils.py scripts/run_stage2_canary.py scripts/run_stage3_canary.py scripts/run_stage34_canary.py scripts/run_stage34_ep_demo_canary.py scripts/run_stage4_canary.py
pytest tests/test_canary_path_utils.py -q
pytest tests/test_run_stage2_canary.py tests/test_run_stage3_canary.py tests/test_run_stage34_canary.py tests/test_run_stage34_ep_demo_canary.py tests/test_run_stage4_canary.py -q
python scripts/sync_temp_queue_state.py
python scripts/ops_validator.py --strict
```

Optional read-only legacy smoke:

```text
python scripts/run_stage4_canary.py analyze --project <known-existing-legacy-canary> --target-ep 2
```

The optional smoke must not move or create legacy data.

## 8. Guardrails

- Do not move, delete, or rewrite existing `projects/_canary/` data in this tranche.
- Do not move `projects/_canary/` as part of the path isolation patch.
- Do not rewrite dated audit/evidence docs that mention `projects/_canary`.
- Do not make `canary/` a tracked generated-output tree.
- Do not let canary-specific environment variables leak into normal runtime execution.
- Do not collapse this lane into the broader trashbox cleanup; it is a bounded runtime path isolation lane.

## 9. Temp Queue Notes

- temp status: `historical backing`
- roadmap role:
  - rank: n/a
  - hygiene/runtime isolation lane
  - not a blocker for current proof or memory rollout lanes
- cleanup condition:
  - keep the mirror while the canary output isolation decision remains parked
  - remove it after implementation closure or after a newer narrower SSOT supersedes it
