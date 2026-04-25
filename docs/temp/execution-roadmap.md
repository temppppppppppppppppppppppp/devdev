# Active Temp Execution Roadmap

Date: 2026-04-24
Status: active (repo-trashbox-cleanup low-risk tracked removal manifest complete; next actual tracked removal PR)
Canonical Path: `docs/2026-04-24/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `143cee26d879d5de59ef43757f851e89b8d551c7`
Baseline Dirty Summary: `dirty: local runtime project outputs, benchmark index, .gitignore key ignore, and new 2026-04-24 hygiene docs; no canary code, data migration, or trashbox move performed`
Resume Commit: `bcbe0955a53b57d0e44953ace2db54ffadffc651`
Resume Drift Summary: `stage234-session-memory-max-utilization was explicitly opened by the user on 2026-04-24, fresh re-audited PASS, and closed on 2026-04-25 after bounded Stage4, Stage3, and Stage2 memory rollout; stage0-bi-tr-production-harness-normalization-remediation Tranche 2 was merged on 2026-04-25 via PR #13; canary-root-isolation was merged on 2026-04-25 via PR #15 and closed via PR #16; repo-trashbox-cleanup reference-check merged via PR #17, move-plan merged via PR #18, packaging-scope merged via PR #19, and low-risk tracked removal manifest opened on branch feat/repo-trashbox-low-risk-removal-manifest`

## 1. Why This Refresh Exists

The 2026-04-23 queue held three honest parked future-wave items. Two repository-hygiene concerns were raised on 2026-04-24:

- canary output currently lands under `projects/_canary/`, making generated proof-run data visually and operationally adjacent to real project data
- maintenance-only/manual/experimental residue such as `test_mode/`, `lite_mode/`, `spikes/`, and root temp outputs should stop cluttering the normal working view

Both concerns are valid but not urgent enough to become front-active implementation work. Canary isolation crosses path helpers, runtime boot environment scoping, Stage 2 subprocess behavior, legacy evidence fallback, and Git ignore policy. Trashbox cleanup crosses reference scanning, Git tracking policy, packaging scope, and security-review framing.

Therefore this refresh parks `canary-root-isolation` as the fourth future wave and `repo-trashbox-cleanup` as the fifth future wave. No code change, data migration, file move, or cleanup is authorized by this roadmap refresh.

After the Standard Vertex cache-proof run on 2026-04-24, `authority-alignment-benchmark-operating-model-hardening` was closed canonically and GitHub issue `#5` was closed as completed. Its canonical SSOT remains historical backing, but its temp mirror is no longer active queue residue.

## 2. Priority Basis

- `stage234-session-memory-max-utilization` is now closed historical backing after its bounded memory/cache rollout landed.
- `stage0-bi-tr-production-harness-normalization-remediation` is now historical backing after PR #13 merged the runtime handoff normalization tranche.
- `canary-root-isolation` is now historical backing after PR #15 merged the canary root isolation tranche.
- `repo-trashbox-cleanup` is the only remaining queue item after canary policy settlement; reference-check, move-plan, packaging/ignore scope, and the low-risk tracked residue manifest are complete, and an actual manifest-bound tracked removal PR is next.

## 3. Queue Semantics

- `front-active tracked cleanup implementation`: current implementation authority is limited to the 21 paths listed in `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`.
- `parked future wave`: still-real execution debt, but not current implementation authority.
- `historical backing`: keep canonical SSOTs for audit history, but do not keep them visible as active queue residue.

Working order:
1. `repo-trashbox-cleanup` (front-active tracked cleanup implementation; actual removal must be manifest-bound and reviewable)

Closed historical backing in this closure pass:

- `authority-alignment-benchmark-operating-model-hardening`
- `stage234-session-memory-max-utilization`
- `stage0-bi-tr-production-harness-normalization-remediation`
- `canary-root-isolation`

## 4. Immediate Next Moves

1. open a dedicated tracked-removal PR for only the 21 paths listed in `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
2. do not reopen `stage234-session-memory-max-utilization` without a fresh live anchor or narrower follow-up SSOT
3. do not reopen Stage0 production-harness normalization without a fresh dedicated re-audit
4. do not move or delete existing `projects/_canary/` without a fresh cleanup SSOT
5. do not move `test_mode/`, `lite_mode/`, `spikes/`, or old `projects/_canary/` from this roadmap refresh
6. refresh `docs/temp/queue-state.json`
7. validate the queue with `python scripts/ops_validator.py --strict`
8. reflect the queue to ClickUp only if the user explicitly asks for it

## 5. Cleanup Rule

- keep temp mirrors only for still-live opened or parked items
- preserve retired items canonically, but do not keep them as visible queue residue
- remove a temp mirror only after implementation closure or a newer narrower SSOT supersedes it
- leave `docs/temp/README.md`
- do not reopen retired lanes without a fresh live anchor and a bounded survey

## Pass 1

- canary-root-isolation was checked against path-resolution risk
- bulk `_canary` replacement was rejected as unsafe
- the safe shape is helper-layer routing plus legacy fallback

## Pass 2

- canary-root-isolation was checked against runtime boot risk
- `GEULDOBI_PROJECTS_ROOT` scoping is required during canary execution
- Stage 2 subprocess environment propagation is required

## Pass 3

- canary-root-isolation was checked against repository hygiene risk
- generated `canary/` output must be ignored
- old `projects/_canary/` cleanup remains a separate decision

Confidence: 96/100

## Repo Trashbox Cleanup Pass 1

- repo-trashbox-cleanup was checked against classification risk
- `tests/` and `docs/temp/` were explicitly retained
- canary output was excluded from this broad cleanup lane

## Repo Trashbox Cleanup Pass 2

- repo-trashbox-cleanup was checked against Git tracking and destructive-operation risk
- tracked candidates require a reference scan and Git policy table before movement
- first execution must be reversible and manifest-driven

## Repo Trashbox Cleanup Pass 3

- repo-trashbox-cleanup was checked against packaging and security-review risk
- packaging scope, `.gitignore`, and response wording require their own tranche
- GitHub Issues and ClickUp remain external mirrors, not automatic SSOT sync

Confidence: 95/100

## 2026-04-25 Repo Trashbox Reference-Check Refresh

- fresh re-audit saved at `docs/2026-04-25/repo-trashbox-cleanup-fresh-reaudit.md`
- reference-check saved at `docs/2026-04-25/repo-trashbox-reference-check.md`
- `test_mode/` and `lite_mode/` each currently have `1554` tracked files, so immediate movement remains unauthorized
- `MagicMock` string matches in tests are not root `MagicMock/` path dependencies
- current PC holding path proposal is `C:\Users\PC\Desktop\글도비_쓰레기통`, but it is not created or used by this tranche

Confidence: 96/100

## 2026-04-25 Repo Trashbox Quarantine Move Plan Refresh

- move plan saved at `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md`
- tracked files are treated as repo-history decisions, not local trash moves
- `test_mode/projects/` and `lite_mode/projects/` each account for `1522` tracked files and should be separate cleanup PRs
- next safe implementation tranche is packaging and ignore scope, followed by low-risk tracked residue removal if approved
- no trashbox directory was created and no file move, delete, `git rm`, packaging edit, or ignore edit was performed by the move-plan tranche

Confidence: 96/100

## 2026-04-25 Repo Trashbox Packaging Scope Refresh

- fresh packaging re-audit saved at `docs/2026-04-25/repo-trashbox-packaging-scope-fresh-reaudit.md`
- `배포_패키징.ps1` excludes `lite_mode`, `spikes`, root `MagicMock`, and `tmp_stage2_digest_debug`
- `.gitignore` covers future root `MagicMock/`, `tmp_stage2_digest_debug/`, `test_mode/projects/`, and `lite_mode/projects/` residue
- `pyproject.toml` excludes manual/prototype surfaces `lite_mode` and `spikes` from broad Ruff traversal
- no tracked cleanup, file movement, deletion, or `git rm` was performed

Confidence: 96/100

## 2026-04-25 Repo Trashbox Low-Risk Tracked Removal Manifest Refresh

- tracked removal manifest saved at `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
- the next implementation authority is limited to exactly 21 tracked files, 1503197 bytes total
- `crash_dump.log` and `error.log` are classified as tracked residue only; runtime crash/log behavior must not change in the removal PR
- `test_mode/`, `lite_mode/`, `spikes/`, `projects/_canary/`, `tests/`, and `docs/temp/` remain outside the removal set
- no tracked cleanup, file movement, deletion, or `git rm` was performed by the manifest tranche

Confidence: 96/100
