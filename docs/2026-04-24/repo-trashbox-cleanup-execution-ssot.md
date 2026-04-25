# Repo Trashbox Cleanup Execution SSOT

Date: 2026-04-24
Status: closed (2026-04-25 bounded low-risk tracked removal complete; broader cleanup requires a new SSOT)
Canonical Path: `docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md`
Temp Mirror Path: `docs/temp/repo-trashbox-cleanup-execution-ssot.md` (removed after closure)
Commit State:
- Baseline Commit: `143cee26d879d5de59ef43757f851e89b8d551c7`
- Baseline Dirty Summary: `dirty: local runtime project outputs, benchmark index, .gitignore key ignore, and new 2026-04-24 hygiene docs; no trashbox file move performed`
- Resume Commit: `0e840af956e40f152b4467189b91762d157c4a4c`
- Resume Drift Summary: `low-risk tracked removal manifest merged via PR #20; manifest-bound tracked removal opened on branch feat/repo-trashbox-low-risk-tracked-removal`
Source Survey Docs:
- `docs/2026-04-24/repo-trashbox-candidate-survey.md`
- `docs/2026-04-24/repo-trashbox-cleanup-adversarial-3pass-audit.md`
- `docs/2026-04-24/canary-root-isolation-plan.md`
- `docs/2026-04-24/ops-sync-harness-current-state-survey.md`
- `docs/2026-04-25/repo-trashbox-cleanup-fresh-reaudit.md`
- `docs/2026-04-25/repo-trashbox-reference-check.md`
- `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md`
- `docs/2026-04-25/repo-trashbox-packaging-scope-fresh-reaudit.md`
- `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
- `docs/2026-04-25/repo-trashbox-low-risk-removal-preflight-reaudit.md`
Evidence Artifacts:
- `modules/core/runtime_paths.py`
- `배포_패키징.ps1`
- `.gitignore`
- `scripts/sync_temp_queue_state.py`
- `scripts/github_issue_readiness.py`
- `scripts/sync_clickup_queue.py`
- `docs/implementation/surface-containment-contract-v1.json`
- `tests/test_surface_containment_contract.py`
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: repo-trashbox-cleanup
  github_issue: 9
  depends_on: []
  status: completed
  queue_role: historical_backing
  roadmap_rank: 1
  tranches:
    - id: reference-check
      title: Candidate reference and runtime dependency check
    - id: quarantine-move-plan
      title: Trashbox quarantine move plan
    - id: packaging-scan-scope
      title: Packaging and security-scan scope cleanup
    - id: git-tracking-cleanup
      title: Git tracking and ignore cleanup
```

## 1. Intent

Quarantine old manual modes, experiments, debug residue, and generated test/demo project data so the main Geuldobi repository view stays focused on production code, formal tests, current docs, and active operational queue files.

The originally proposed local holding area was:

```text
C:\Users\wjjo\Desktop\글도비_쓰레기통
```

On the current PC, the proposed local holding area is:

```text
C:\Users\PC\Desktop\글도비_쓰레기통
```

This document closes the bounded repo-trashbox cleanup lane. The reference-check, quarantine move-plan, packaging/ignore scope, low-risk tracked removal manifest, preflight re-audit, and manifest-bound `git rm` tranches are complete. Larger cleanup surfaces such as `test_mode/`, `lite_mode/`, `spikes/`, and any remaining root temp files require a new SSOT before further action.

## 2. Baseline Facts

Surveyed candidate groups:

- `test_mode/`: maintenance-only/manual mode; currently `1554` tracked files
- `lite_mode/`: lightweight/legacy experiment surface; currently `1554` tracked files
- `spikes/`: one-off probes and build/dist residue
- `MagicMock/`: mock/runtime residue
- `tmp_stage2_digest_debug/`: debug residue
- `rlhf_data/test_project/` and `datasets/test_project/`: generated test project data
- root temp/result residue such as temp text files, local XML result files, crash/error logs, and temporary DB files

Known keep-in-repo groups:

- `tests/`: formal pytest suite
- `docs/temp/`: active operational queue mirror
- production/runtime/supporting code under `modules/`, `scripts/`, `geuldobi-desktop/`, `contracts/`, and `config/`

Canary note:

- `projects/_canary/` is intentionally excluded from this lane.
- Future canary output isolation is parked separately under `canary-root-isolation`.

## 3. Scope

Included:

- candidate reference scan
- Git tracking classification
- safe quarantine plan for `글도비_쓰레기통`
- `.gitignore` and packaging-scope review
- security-review response wording after actual cleanup

Excluded:

- immediate move of any directory or file
- deletion
- history rewrite
- moving `tests/`
- moving `docs/temp/`
- moving `projects/_canary/`
- ClickUp sync
- claiming GitHub issue auto-sync

## 4. Pass 1 - Inventory Summary

Primary target classes:

- retired manual modes
- old experiments
- local debug residue
- generated test/demo data
- root-level temporary result files

Primary non-target classes:

- formal tests
- active queue mirrors
- production runtime code
- canary output pending separate isolation

## 5. Pass 2 - Semantic Classification

Class A - Keep in repo:

- `tests/`
- `docs/temp/`
- production/runtime/support code

Class B - Candidate quarantine:

- `test_mode/`
- `lite_mode/`
- `spikes/`
- root temp/result residue
- generated test/demo project data

Class C - Separate lane:

- `projects/_canary/`

## 6. Side-Effect Map

File writes / artifacts:

- Future local-only quarantine work may copy files to `C:\Users\PC\Desktop\글도비_쓰레기통`.
- This parking pass writes documentation only.

DB / schema / transaction boundaries:

- Not applicable for this documentation pass.
- Future cleanup must not move production project DBs.

JSONL / log / audit sinks:

- Future cleanup must distinguish production project logs from generated test/canary logs.

Console / UI / operator output:

- Future cleanup should produce a before/after move manifest.

Rollback / recovery / retry:

- Future cleanup must keep a reversible manifest until the user approves deletion or Git removal.

Cache / global state:

- Not applicable.

Bootstrap fallback / config-env mutation:

- Not applicable for this lane, except packaging and ignore policy review.

## 7. Realization Architecture

The cleanup should run as a narrow, manifest-driven quarantine:

1. enumerate candidates
2. scan references
3. classify Git tracking
4. prepare move manifest
5. copy or move to `글도비_쓰레기통`
6. update ignore and packaging scope
7. rerun validators

The canonical repo docs remain the SSOT. GitHub Issues and ClickUp are only visibility layers.

## 8. Execution Tranches

1. Candidate reference and runtime dependency check (complete on 2026-04-25; no move authorized)
2. Trashbox quarantine move plan (complete on 2026-04-25; no move authorized)
3. Packaging and security-scan scope cleanup (complete on 2026-04-25; no tracked cleanup authorized)
4. Git tracking and ignore cleanup (complete on 2026-04-25; removed only the 21 manifest-listed tracked residue files)

## 9. Acceptance Criteria

- `tests/` remains in place and still runs as the formal suite.
- `docs/temp/` remains the active queue mirror.
- `projects/_canary/` is not moved by this lane.
- Each moved candidate has a manifest entry.
- Tracked-file changes are intentional, manifest-bound, and reviewable.
- Packaging excludes maintenance-only/non-runtime residue where appropriate.
- `python scripts/ops_validator.py --strict` passes after queue/document updates.

## 10. Verification Plan

Documentation validation:

- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Future implementation validation:

- `rg` reference scan for each candidate path
- `git status --short` after each move tranche
- targeted packaging exclusion scan
- focused pytest only if runtime-facing references are changed

Future low-risk tracked removal validation:

- remove only the 21 paths listed in `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
- keep `test_mode/`, `lite_mode/`, `spikes/`, `projects/_canary/`, `tests/`, and `docs/temp/` unchanged
- run `python -m pytest tests/test_surface_containment_contract.py tests/test_runtime_authority_contract.py -q`

## 11. Guardrails

- Do not delete on first pass.
- Do not move active queue docs.
- Do not move canary through trashbox cleanup.
- Do not use ClickUp as SSOT.
- Do not assume roadmap parking creates GitHub Issues automatically.
- Do not clean tracked files without a Git policy table.
- Do not clean tracked files outside the low-risk manifest without a new manifest refresh.

## 12. Temp Queue Notes

- temp status: in_progress
- cleanup condition: remove temp mirror after the trashbox cleanup is either implemented and closed, or superseded by a narrower SSOT
- roadmap dependency: after `canary-root-isolation`

## 13. Validation And Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- queue refresh command: `python scripts/sync_temp_queue_state.py`
- GitHub readiness command: `python scripts/github_issue_readiness.py`
- closure harness: `docs/implementation/execution-closure-harness.md`

## 14. Closure Note - 2026-04-25 Low-Risk Tracked Removal

Closure status: closed.

Implemented:

- removed exactly the 21 tracked paths listed in `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
- updated `docs/implementation/surface-containment-contract-v1.json` and `tests/test_surface_containment_contract.py` so the contract now asserts those tracked residue surfaces are absent and future generated residue remains ignored
- removed no runtime code, formal tests, active queue docs, canary data, `test_mode/`, `lite_mode/`, or `spikes/`
- created no local trashbox holding directory and performed no history rewrite

Verification evidence:

- preflight re-audit passed at `docs/2026-04-25/repo-trashbox-low-risk-removal-preflight-reaudit.md`
- post-removal `git ls-files -- MagicMock tmp_stage2_digest_debug rlhf_data/test_project datasets/test_project crash_dump.log error.log test_results.xml tmp_project_00.db` returns no tracked files
- queue closure refresh writes `docs/temp/queue-state.json` with `queue_mode: empty`
- local validation commands are recorded in the removal PR body

Residual scope:

- `test_mode/`, `lite_mode/`, and `spikes/` remain intentionally out of scope.
- Remaining root residue outside the 21-path manifest remains intentionally out of scope.
- Any future cleanup must start from a fresh SSOT or manifest rather than reopening this closed temp queue item.
