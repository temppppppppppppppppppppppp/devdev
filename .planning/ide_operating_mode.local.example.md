# IDE Operating Mode Local Note

Status: local example
Last Updated: 2026-04-03

This file is intentionally per-worktree and should remain untracked.

## Local Identity

- current IDE: `IDE-X`
- editor: `antigravity | vscode | cursor`
- worktree path: `C:\path\to\worktree`
- branch: `branch-name`

## Local Focus

- lane: `short lane name`
- current focus: `what this worktree is doing right now`
- shared-file change needed: `yes | no`

## Before Pause

- `git worktree list`
- `git branch -vv`
- `git status --short`

## Before Merge

- support IDE commits or stashes all work
- `IDE-1` is confirmed as merge owner
- shared queue docs are updated only after merge

## Notes

- Edit this file freely in one worktree.
- Do not use it as a shared coordination file across all IDEs.
