# IDE Operating Mode

Status: shared lane map
Last Updated: 2026-04-05

## Current Mode

- mode: `single`
- parallel activation: `inactive`
- main owner: `IDE-1`
- support lanes: `reserved for burst mode only`

Default operating assumption is `one main worktree + one main writer lane`.
`split_3ide` is a temporary burst mode, not the baseline.
`IDE-1` remains merge owner and shared-file lock owner.

## Stable Editor Assignment

Use this tracked file for stable lane ownership only:

- `antigravity` -> `IDE-1`
- `vscode` -> `IDE-2`
- `cursor` -> `IDE-3`

This file should not be rewritten every time a different IDE reads it.
Do not use a single mutable `current IDE` slot here.

Quick reference:

- `docs/implementation/single-ide-default-policy.md`
- `docs/2026-04-03/three-ide-ownership-cut-sheet.md`

## Active Worktree Snapshot

- `IDE-1` / `antigravity`
  - path: `.`
  - branch: `ops/material-ssot-1ide-default`

Reserved burst-mode lanes:

- `IDE-2` / `vscode`
  - activate only after an explicit `split_3ide` switch
  - recommended path when active: `..\글도비_stage0`
- `IDE-3` / `cursor`
  - activate only after an explicit `split_3ide` switch
  - recommended path when active: `..\글도비_process`

## Stable Lane Map

### IDE-1

- editor: `antigravity`
- lane: `Stage 2/3/4 bottleneck remediation`
- role: `main pipeline + active queue owner + final merge authority`

Owned here first:

- `main_a.py`
- `modules/core/stage2_*.py`
- `modules/core/stage3_*.py`
- `modules/core/stage4_*.py`
- `modules/domain/agents/chief_writer_context.py`
- runtime canary/smoke scripts
- active queue docs after merge review

### IDE-2

- editor: `vscode`
- lane: `Stage0 -> BI/TR normalization + downstream planning-material production`
- role: `BI/TR production lane`

Owned here first:

- `modules/core/stage0_handoff.py`
- `modules/core/stage01_helpers.py`
- `modules/core/project_manager.py`
- BI/TR build and audit scripts
- `bible/`
- `treatments/`

### IDE-3

- editor: `cursor`
- lane: `planning production process standardization`
- role: `process-doc lane`

Owned here first:

- `docs/2026-04-03/`
- `docs/implementation/` process-only drafts
- `.planning/`
- planning templates, checklists, and workflow notes that do not directly mutate runtime ownership

## Local Per-Worktree Note

Per-IDE mutable state belongs in:

- `.planning/ide_operating_mode.local.md`

Rules:

1. this local file is untracked and may differ per worktree
2. each IDE edits only its own local copy
3. use the local file for `current focus`, `branch`, `worktree path`, and dirty-state reminders
4. do not push local-state churn back into this shared tracked note

Reference template:

- `.planning/ide_operating_mode.local.example.md`

## Do Not Edit Here By Default

- `main_a.py`
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/temp/*execution-ssot.md`
- active Stage0, Stage2, Stage3, Stage4 runtime files owned by another IDE lane

## Shared File Lock Owner

- owner: `IDE-1`

Locked by default:

- `main_a.py`
- `AGENTS.md`
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/temp/*execution-ssot.md`

## Mode Change Checklist

Before `split_3ide`:

- confirm the current task really benefits from a temporary parallel burst
- separate worktrees created
- support branches created
- file ownership written down
- queue owner confirmed

Before `merge_only`:

- support IDEs commit or stash
- merge owner confirmed as `IDE-1`
- queue docs update reserved to `IDE-1`

## Daily Safety Checks

Run before ending a parallel session:

- `git worktree list`
- `git branch -vv`
- `git status --short`

Run before deleting a support worktree:

- confirm support branch is merged or intentionally parked
- confirm no dirty files remain in the support worktree
- confirm shared queue docs were updated only by `IDE-1`

## Merge Reminder

Recommended order:

1. switch to `merge_only`
2. stop support IDE writes
3. merge support branches one at a time in `IDE-1`
4. update queue docs only after code merge
5. remove worktrees
6. return to `single`

## Notes

- This file is a lightweight shared operator memo.
- It is not a runtime config file.
- Keep stable ownership here and keep per-worktree mutable state in the local note.
- If this file and the actual git state disagree, actual git state wins.
