# Three-IDE Ownership Cut Sheet

Date: 2026-04-03
Status: operator short form
Scope: one-page ownership and merge rules for `antigravity`, `vscode`, and `cursor`

## 1. Default Read

- if all three IDEs are still opening `C:\Users\wjjo\Desktop\글도비`, this is still effectively `single` mode
- true parallel write mode starts only after separate `git worktree` paths exist
- until then, use this as a lane map, not as proof that support IDEs are write-safe

## 2. Fixed Editor Map

- `antigravity` -> `IDE-1`
- `vscode` -> `IDE-2`
- `cursor` -> `IDE-3`

## 3. Lane Ownership

### IDE-1

- mission: `Stage2/3/4 bottleneck remediation`
- role: `main pipeline + active queue owner + final merge authority`
- owns first:
  - `main_a.py`
  - `modules/core/stage2_*.py`
  - `modules/core/stage3_*.py`
  - `modules/core/stage4_*.py`
  - runtime canary/smoke scripts
  - shared queue docs after merge review

### IDE-2

- mission: `Stage0 -> BI/TR normalization + downstream planning-material production`
- role: `BI/TR lane`
- owns first:
  - `modules/core/stage0_handoff.py`
  - `modules/core/stage01_helpers.py`
  - `modules/core/project_manager.py`
  - BI/TR build and audit scripts
  - `bible/`
  - `treatments/`

### IDE-3

- mission: `planning production process standardization`
- role: `process-doc lane`
- owns first:
  - `docs/2026-04-03/`
  - `docs/implementation/` process-only drafts
  - `.planning/`

## 4. Shared File Lock

`IDE-1 only` by default:

- `main_a.py`
- `AGENTS.md`
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/temp/*execution-ssot.md`

## 5. Cross-Lane Rule

1. read is open, but write is owner-first
2. if an IDE needs a shared-file change, it sends a patch or request to `IDE-1`
3. if an IDE needs another lane's non-shared file, escalate first instead of silently editing across lanes
4. if separate worktrees do not exist yet, support IDEs should stay proposal-first or doc-first

## 6. Merge Rule

1. switch to `merge_only`
2. stop support IDE writes
3. `IDE-1` merges one support branch at a time
4. only after code merge does `IDE-1` update queue docs
5. remove support worktrees only after merged visibility is confirmed
6. return to `single`

## 7. Daily Safety Check

- `git worktree list`
- `git branch -vv`
- `git status --short`

## 8. Working Interpretation

- this model is about `ownership + merge authority`, not OS-level access control
- the goal is not “nobody else can touch it”
- the goal is “one lane owns the decision, and one lane owns the final merge”

## 9. Local State Rule

- stable ownership stays in tracked docs
- per-worktree mutable state goes in `.planning/ide_operating_mode.local.md`
- do not put a shared mutable `current IDE` slot back into tracked docs

## 10. 3-Pass Note

- pass 1: trimmed to only ownership, locks, merge, and safety
- pass 2: aligned with the larger three-IDE draft and current shared memo
- pass 3: checked for direct operator usability
- confidence: `97%`
