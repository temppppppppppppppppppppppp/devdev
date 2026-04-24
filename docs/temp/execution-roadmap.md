# Active Temp Execution Roadmap

Date: 2026-04-24
Status: active (#5 proof-governor lane closed; stage234-session-memory-max-utilization opened for fresh re-audit and bounded rollout)
Canonical Path: `docs/2026-04-24/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `143cee26d879d5de59ef43757f851e89b8d551c7`
Baseline Dirty Summary: `dirty: local runtime project outputs, benchmark index, .gitignore key ignore, and new 2026-04-24 hygiene docs; no canary code, data migration, or trashbox move performed`
Resume Commit: `fabf78127cbcdfb724c35a38f314a25b94ec9ce5`
Resume Drift Summary: `stage234-session-memory-max-utilization was explicitly opened by the user on 2026-04-24 and fresh re-audited PASS; canary-root-isolation, repo-trashbox-cleanup, and stage0-bi-tr-production-harness-normalization-remediation remain parked unless separately opened`

## 1. Why This Refresh Exists

The 2026-04-23 queue held three honest parked future-wave items. Two repository-hygiene concerns were raised on 2026-04-24:

- canary output currently lands under `projects/_canary/`, making generated proof-run data visually and operationally adjacent to real project data
- maintenance-only/manual/experimental residue such as `test_mode/`, `lite_mode/`, `spikes/`, and root temp outputs should stop cluttering the normal working view

Both concerns are valid but not urgent enough to become front-active implementation work. Canary isolation crosses path helpers, runtime boot environment scoping, Stage 2 subprocess behavior, legacy evidence fallback, and Git ignore policy. Trashbox cleanup crosses reference scanning, Git tracking policy, packaging scope, and security-review framing.

Therefore this refresh parks `canary-root-isolation` as the fourth future wave and `repo-trashbox-cleanup` as the fifth future wave. No code change, data migration, file move, or cleanup is authorized by this roadmap refresh.

After the Standard Vertex cache-proof run on 2026-04-24, `authority-alignment-benchmark-operating-model-hardening` was closed canonically and GitHub issue `#5` was closed as completed. Its canonical SSOT remains historical backing, but its temp mirror is no longer active queue residue.

## 2. Priority Basis

- `stage234-session-memory-max-utilization` is now first because its upstream proof governor has closed and it is the next memory/cache rollout lane.
- `stage0-bi-tr-production-harness-normalization-remediation` remains second because Stage0 runtime handoff normalization is still honest but not front-active.
- `canary-root-isolation` is third because it is a repository hygiene/runtime isolation lane, not a blocker for the proof or memory rollout lanes.
- `repo-trashbox-cleanup` is fourth because it should quarantine old residue only after canary policy is not accidentally swept into a broad cleanup.

## 3. Queue Semantics

- `parked future wave`: still-real execution debt, but not current implementation authority.
- `historical backing`: keep canonical SSOTs for audit history, but do not keep them visible as active queue residue.

Working order:
1. `stage234-session-memory-max-utilization` (opened current lane; cross-stage memory/cache rollout lane whose upstream #5 proof gate is closed and fresh re-audit passed)
2. `stage0-bi-tr-production-harness-normalization-remediation` (parked future wave; Stage0 runtime handoff normalization remains open)
3. `canary-root-isolation` (parked future wave; isolate future canary output from `projects/`, no migration authorized)
4. `repo-trashbox-cleanup` (parked future wave; quarantine maintenance-only/test/experiment residue after canary policy is settled)

Closed historical backing in this closure pass:

- `authority-alignment-benchmark-operating-model-hardening`

## 4. Immediate Next Moves

1. keep the three remaining parked items parked unless the user explicitly opens one
2. execute `stage234-session-memory-max-utilization` as the current bounded memory/cache rollout lane
3. do not implement `canary-root-isolation` or `repo-trashbox-cleanup` from parked SSOTs without fresh approval
4. do not move or delete `projects/_canary/`
5. do not move `test_mode/`, `lite_mode/`, `spikes/`, or root residue from this roadmap refresh
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
