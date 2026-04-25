# Repo Trashbox Cleanup Execution SSOT

Date: 2026-04-24
Status: in-progress (2026-04-25 low-risk tracked removal manifest complete; no tracked removal performed)
Canonical Path: `docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md`
Temp Mirror Path: `docs/temp/repo-trashbox-cleanup-execution-ssot.md`
Commit State:
- Baseline Commit: `143cee26d879d5de59ef43757f851e89b8d551c7`
- Baseline Dirty Summary: `dirty: local runtime project outputs, benchmark index, .gitignore key ignore, and new 2026-04-24 hygiene docs; no trashbox file move performed`
- Resume Commit: `bcbe0955a53b57d0e44953ace2db54ffadffc651`
- Resume Drift Summary: `packaging scope merged via PR #19; low-risk tracked removal manifest opened on branch feat/repo-trashbox-low-risk-removal-manifest without tracked cleanup`
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
Evidence Artifacts:
- `modules/core/runtime_paths.py`
- `배포_패키징.ps1`
- `.gitignore`
- `scripts/sync_temp_queue_state.py`
- `scripts/github_issue_readiness.py`
- `scripts/sync_clickup_queue.py`
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: repo-trashbox-cleanup
  github_issue: 9
  depends_on: []
  status: in_progress
  queue_role: front_active
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

This document still does not authorize a move. The reference-check, quarantine move-plan, packaging/ignore scope, and low-risk tracked removal manifest tranches are complete; the next safe scope is a dedicated tracked-removal PR that removes only the manifest-listed paths.

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
4. Git tracking and ignore cleanup (manifest complete on 2026-04-25; actual tracked removal requires a dedicated follow-up PR)

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
