# Canary Root Isolation Plan

Date: 2026-04-24

## Purpose

Canary runs currently write under:

```text
projects/_canary/
```

This keeps live/real project data and disposable proof-run output in the same visual and Git-tracked area. The goal is to stop future canary runs from cluttering `projects/` while preserving compatibility with existing canary evidence.

This document is a plan only. It does not authorize immediate migration of existing canary data.

## Current State

Observed local state:

| Path | Approx Size | Tracked Files | Note |
| --- | ---: | ---: | --- |
| `projects/_canary/` | 933.61 MB | 3,825 | Existing canary proof output and copied project DBs/logs/artifacts. |

Current path helper:

```text
scripts/canary_path_utils.py
```

Current behavior:

- `CANARY_ROOT_NAME = "_canary"`
- `canary_root(app_root)` resolves to `projects/_canary`
- `prefer_canary=True` routes new canary targets to `projects/_canary/<name>`
- `_canary/<name>` is treated as a nested project name under `projects/`

Runtime support already exists for an alternate projects root:

```text
GEULDOBI_PROJECTS_ROOT
```

`main_a.py`, `modules/core/runtime_paths.py`, `modules/core/project_manager.py`, and the desktop bridge path can resolve projects through that environment variable.

## Target Shape

New canary root:

```text
canary/
```

Intended shape:

```text
Geuldobi repo
  projects/
    <real or operator project>
  canary/
    <canary run project>
      project_data.db
      logs/
      drafts/
      plans/
      stage0_output/
```

Do not put new canary runs under `projects/`.

Do not move old `projects/_canary` data during the first implementation pass.

## Compatibility Policy

Use a compatibility-first transition:

| Case | Expected Behavior |
| --- | --- |
| New canary target, no existing project | Write to `canary/<target>`. |
| Existing canary under `canary/<target>` | Prefer `canary/<target>`. |
| Existing legacy canary under `projects/_canary/<target>` | Read as fallback when `require_exists=True`. |
| Explicit absolute path | Preserve current behavior and use the absolute path. |
| Explicit `projects/<name>` | Preserve current behavior and resolve under `projects/`. |
| Explicit `_canary/<name>` | Accept as legacy-compatible input. For new writes, normalize toward `canary/<name>`; for reads, check `canary/<name>` first, then `projects/_canary/<name>`. |

## Implementation Plan

### Phase 1: Path Helper Only

Update `scripts/canary_path_utils.py`:

- Add `DEFAULT_CANARY_DIR_NAME = "canary"`.
- Keep `LEGACY_CANARY_ROOT_NAME = "_canary"`.
- Add `canary_root(app_root)` that resolves in this order:
  - `GEULDOBI_CANARY_ROOT`, if set
  - `<app_root>/canary`
- Add `legacy_canary_root(app_root)` for `<app_root>/projects/_canary`.
- Update `resolve_workspace_project_dir()` so `prefer_canary=True` writes new targets to `canary/<name>`.
- Keep legacy read fallback for existing `projects/_canary/<name>`.
- Update `project_name_from_path()` so callers can distinguish:
  - runtime project name relative to canary root
  - legacy locator for reporting if needed

### Phase 2: Runtime Boot Wrapper

Canary scripts that boot `SovereignApp` must run with:

```text
GEULDOBI_PROJECTS_ROOT=<repo>\canary
```

Scope that environment change to the canary run only, then restore the prior value.

Affected scripts:

```text
scripts/run_stage2_canary.py
scripts/run_stage3_canary.py
scripts/run_stage34_canary.py
scripts/run_stage34_ep_demo_canary.py
scripts/run_stage4_canary.py
```

Stage 2 uses `scripts/canary_stage2_headless.py` through `subprocess.run()`, so the subprocess environment must also receive the temporary canary projects root.

### Phase 3: Tests

Update focused tests first:

```text
tests/test_canary_path_utils.py
tests/test_run_stage2_canary.py
tests/test_run_stage3_canary.py
tests/test_run_stage34_canary.py
tests/test_run_stage34_ep_demo_canary.py
tests/test_run_stage4_canary.py
```

Required assertions:

- New prepared targets resolve under `canary/<name>`.
- Existing legacy `projects/_canary/<name>` can still be analyzed/read.
- Runtime boot receives project name relative to the canary root, not `_canary/<name>`.
- `GEULDOBI_PROJECTS_ROOT` is restored after canary runs.
- Stage 2 subprocess receives `GEULDOBI_PROJECTS_ROOT=<repo>\canary`.

### Phase 4: Ignore Rules

After code/tests pass, add ignore rules for generated canary output:

```text
canary/
```

If a lightweight manifest is desired later, keep only:

```text
canary/README.md
!canary/README.md
```

Default recommendation: ignore the whole `canary/` tree because canary projects contain copied DBs, logs, drafts, artifacts, and run evidence.

### Phase 5: Legacy Data Decision

Do not migrate existing `projects/_canary/` during the code change.

After the new root is proven:

- either leave `projects/_canary/` as old evidence until manual cleanup
- or move it to `글도비_쓰레기통\projects__canary_legacy_<date>`
- or archive only selected summaries before removal

This should be a separate cleanup decision, not part of path isolation.

## Safety Rules

- Do not delete or move existing `projects/_canary/` in the first pass.
- Do not rewrite historical docs that mention `projects/_canary/`.
- Do not change normal project resolution for `projects/<name>`.
- Do not change the formal pytest root `tests/`.
- Do not route real operator projects into `canary/`.
- Environment variable changes must be scoped and restored.

## Verification

Minimum verification after implementation:

```text
python -m py_compile scripts/canary_path_utils.py scripts/run_stage2_canary.py scripts/run_stage3_canary.py scripts/run_stage34_canary.py scripts/run_stage34_ep_demo_canary.py scripts/run_stage4_canary.py
pytest tests/test_canary_path_utils.py -q
pytest tests/test_run_stage2_canary.py tests/test_run_stage3_canary.py tests/test_run_stage34_canary.py tests/test_run_stage34_ep_demo_canary.py tests/test_run_stage4_canary.py -q
```

Optional smoke after focused tests:

```text
python scripts/run_stage4_canary.py analyze --project <known-existing-legacy-canary> --target-ep 2
```

The optional smoke should prove legacy read fallback only. It should not create or migrate old data.

## Acceptance Criteria

The change is complete when:

- New canary prepares create `canary/<target>` instead of `projects/_canary/<target>`.
- Existing legacy canary paths can still be analyzed.
- Live canary execution boots against `canary/` through `GEULDOBI_PROJECTS_ROOT`.
- Normal `projects/` project behavior is unchanged.
- Generated `canary/` output is ignored by Git.
- Security/repository hygiene language can state that canary output is isolated from production project storage.

## Rollback

Rollback should be simple:

- Restore `scripts/canary_path_utils.py` to `projects/_canary` behavior.
- Remove the canary-run `GEULDOBI_PROJECTS_ROOT` wrapper from canary scripts.
- Remove the new `canary/` ignore rule if it was added.

Because existing `projects/_canary/` is not moved in Phase 1, rollback does not require data restoration.

