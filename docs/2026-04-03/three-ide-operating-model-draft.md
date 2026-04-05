# Three-IDE Burst-Mode Draft

Date: 2026-04-03
Status: draft burst-mode reference
Scope: temporary parallel IDE burst mode for Geuldobi runtime work, Stage0 material work, and planning-process standardization

Historical Note: this draft records a capture-time three-worktree recommendation. The worktree labels below are historical examples, not current required absolute paths. It does not replace the active `single IDE default` policy.

## 1. Decision Summary

- default operating mode is `single`
- `split_3ide` is an explicit burst mode, not a standing baseline
- Use `1 main + 2 support` when parallel work is worth the coordination cost.
- `IDE-1` owns the active queue, shared entrypoints, and final merge authority.
- `IDE-2` owns `Stage0 -> BI/TR normalization + downstream material production`.
- `IDE-3` owns `planning production process standardization`.
- Any write-capable parallel setup should use separate `git worktree` paths.
- Shared files are not edited concurrently. Support IDEs escalate shared-file changes to `IDE-1`.

## 2. Role Split

### IDE-1: Main Runtime Lane

Mission:

- Stage 2, Stage 3, Stage 4 bottleneck remediation
- active queue ownership
- final merge and release gate ownership

Primary owned files:

- `main_a.py`
- `modules/core/stage2_*.py`
- `modules/core/stage3_*.py`
- `modules/core/stage4_*.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/chief_writer_context.py`
- `config/prompts/ensemble.yaml`
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/run_stage4_canary.py`

Primary responsibility:

- close runtime-visible blockers
- decide queue order
- integrate support-lane outputs into canonical runtime paths

### IDE-2: Stage0 and BI/TR Lane

Mission:

- Stage0 handoff normalization
- BI/TR production contract cleanup
- downstream planning-material production

Primary owned files:

- `modules/core/stage0_handoff.py`
- `modules/core/stage01_helpers.py`
- `modules/core/project_manager.py`
- `modules/domain/agents/block_enricher.py`
- `scripts/build_bi_from_phase0_and_tr.py`
- `scripts/build_wuxia_bi_from_phase0_and_tr.py`
- `scripts/generate_tr_bibles.py`
- `scripts/check_bi_tr_consumability.py`
- `scripts/audit_bi_5pass.py`
- `scripts/audit_narrative_bi.py`
- `bible/`
- `treatments/`

Primary responsibility:

- reduce Stage0 split-truth risk
- clarify `BI`, `TR`, and DB anchor ownership
- keep production-material outputs consumable by later stages

### IDE-3: Planning Process Standardization Lane

Mission:

- standardize how planning material is produced
- define templates, checklists, contracts, and operator-facing process rules

Primary owned files:

- `docs/2026-04-03/`
- `docs/implementation/` process-only drafts
- `.planning/`
- planning templates, checklists, and workflow notes that do not directly mutate runtime ownership

Primary responsibility:

- standardize planning creation flow
- define review checklist and handoff checklist
- produce process docs without directly changing active runtime code by default

Default restriction:

- `IDE-3` should stay doc-first.
- If a process rule requires code change, it should be proposed to `IDE-1` or `IDE-2` first.

## 3. Shared File Lock Rules

The following files are `IDE-1 only` by default:

- `main_a.py`
- `AGENTS.md`
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- active queue mirrors under `docs/temp/*execution-ssot.md`

Shared-file rule:

1. `IDE-2` and `IDE-3` do not directly edit shared files.
2. If a shared-file change is needed, they produce a small patch or written request.
3. `IDE-1` reviews and applies the final change.

## 4. Worktree Layout

Recommended layout:

- `IDE-1`: main runtime worktree at capture time
- `IDE-2`: sibling Stage0 worktree at capture time
- `IDE-3`: sibling planning-process worktree at capture time

Recommended commands:

```powershell
git worktree add ..\글도비_stage0 -b ops/stage0-bi-tr
git worktree add ..\글도비_process -b ops/process-standardization
```

Operational rule:

- each IDE works on its own branch
- each support branch merges through `IDE-1`
- queue docs are updated only after merge or explicit queue review

## 5. Operating Modes

This mode should be switchable, but it should be an `operations mode`, not an app feature.

Recommended modes:

### `single`

- only `IDE-1` writes
- `IDE-2` and `IDE-3` are closed or read-only
- canonical default mode

### `split_3ide`

- `IDE-1`, `IDE-2`, and `IDE-3` all active
- each IDE edits only its owned scope
- separate worktrees are mandatory
- use only for an explicit bounded burst

### `merge_only`

- `IDE-2` and `IDE-3` stop editing
- `IDE-1` integrates branches, resolves conflicts, and updates queue docs

## 6. Mode Switching Rules

### Enter `split_3ide`

1. `IDE-1` confirms queue owner and shared-file lock owner.
2. all IDE paths are on separate worktrees
3. each worktree has a clean or intentionally committed state
4. file ownership is written down before editing starts

### Enter `merge_only`

1. `IDE-2` and `IDE-3` commit or stash all work
2. `IDE-1` pulls or merges support branches
3. `IDE-1` updates shared docs and queue state after integration

### Return to `single`

1. merge or park support work
2. stop support IDE writes
3. leave final queue authority with `IDE-1`

## 7. Collision Prevention Rules

- do not let two IDEs edit the same Python file in the same window
- do not let support IDEs modify `docs/temp/` execution queue artifacts directly
- do not let `IDE-3` directly rewrite runtime ownership code unless explicitly promoted into a code lane
- do not use the same branch for all IDEs when parallel edits are expected

## 8. Shared vs Local Operating Note

Use two layers instead of one mutable shared slot.

Tracked shared note:

- `.planning/ide_operating_mode.md`
- purpose: stable editor-to-lane map, shared lock ownership, merge reminder, safety checklist
- this file should not contain a single mutable `current IDE` field that every IDE overwrites

Untracked local note:

- `.planning/ide_operating_mode.local.md`
- purpose: per-worktree state such as current focus, branch, worktree path, and dirty-state reminders
- each IDE edits only its own local copy

Reference template:

- `.planning/ide_operating_mode.local.example.md`

The shared file is a human-readable control note.
It is not a runtime contract and should not block work if stale.

## 9. Recommended Starting Policy

Start with this policy:

- default mode: `single`
- treat `single` as the normal resting state, not just the low-effort option
- only switch to `split_3ide` when:
  - `IDE-1` has a real runtime bottleneck lane
  - `IDE-2` has independent Stage0 or BI/TR work
  - `IDE-3` can stay doc-first without runtime-file overlap
- after a parallel burst, return to `merge_only` and then `single`

## 10. Immediate Practical Recommendation

Use the following first:

- `IDE-1`: Stage2/3/4 bottleneck work
- `IDE-2`: Stage0 + BI/TR normalization + downstream planning-material production
- `IDE-3`: planning-process templates, checklists, and handoff standardization only

This keeps the highest-risk runtime lane centralized while still getting useful parallel output from the two support lanes.

## 11. Worktree Lifecycle Checklist

### A. Create

Use separate branches and separate worktree paths before support IDEs begin writing:

```powershell
git worktree add ..\글도비_stage0 -b ops/stage0-bi-tr
git worktree add ..\글도비_process -b ops/process-standardization
```

Creation checklist:

1. `IDE-1` confirms current base branch and shared-file lock owner.
2. `IDE-2` and `IDE-3` receive their branch names and owned file scopes.
3. each support worktree starts clean before editing.
4. `IDE-1` records that the operating mode is now `split_3ide`.

### B. Work

While the worktrees are active:

1. each IDE edits only its owned scope.
2. support IDEs commit in small units.
3. support IDEs do not directly edit queue files or shared lock files.
4. if a support IDE needs a shared-file change, it sends the patch to `IDE-1`.

Recommended support-branch habit:

```powershell
git status --short
git add .
git commit -m "short scoped message"
```

### C. Merge

When the support work is ready:

1. switch the team into `merge_only`.
2. `IDE-2` and `IDE-3` stop editing.
3. `IDE-1` reviews branch diff and merges one support branch at a time.
4. only after merge does `IDE-1` update queue docs if needed.

Recommended merge flow:

```powershell
git merge --no-ff ops/stage0-bi-tr
git merge --no-ff ops/process-standardization
```

If only part of a support branch should land, `IDE-1` may use `git cherry-pick` instead of full merge.

### D. Cleanup

After merge is complete:

```powershell
git worktree remove ..\글도비_stage0
git worktree remove ..\글도비_process
git branch -d ops/stage0-bi-tr
git branch -d ops/process-standardization
```

Cleanup checklist:

1. merged work is visible on the main branch.
2. no needed support commits remain unmerged.
3. queue files are updated only once, from `IDE-1`.
4. operating mode returns to `single` unless another parallel burst is about to start.

## 12. Safety Rules

What actually causes damage is usually not worktree usage itself.
The real risk factors are:

- long-lived uncommitted changes
- two IDEs editing the same file
- support IDEs changing queue state directly
- deleting a branch before its commits are confirmed merged

Safe operating defaults:

1. support IDEs commit early and often.
2. `IDE-1` is the only queue editor.
3. `IDE-1` merges support branches one at a time.
4. end each parallel session with a merge review and cleanup pass.
5. keep stable lane ownership in the tracked shared note and keep mutable per-worktree state in the untracked local note.

## 13. Recovery Notes

If something is missed, it is usually recoverable.

- unmerged support work normally still exists on the support branch
- `git branch -d` refuses to delete unmerged branches in normal cases
- `git worktree remove` should not be used on a dirty support tree without checking status first
- if a branch or HEAD move was mistaken, `git reflog` is the first recovery tool
- the real danger zone is force deletion: `git branch -D` and `git worktree remove --force` bypass normal safety checks
- `git reflog` helps recover commit and HEAD movement, but it does not directly restore uncommitted or untracked files deleted from disk

Minimum recovery checklist:

1. run `git worktree list`
2. run `git branch -vv`
3. run `git log --oneline --graph --decorate --all -20`
4. if needed, inspect `git reflog`

This means the process is not "one miss and everything is lost."
The system is safe enough as long as support IDEs commit regularly, force deletion is avoided by default, and `IDE-1` remains the single merge authority.
