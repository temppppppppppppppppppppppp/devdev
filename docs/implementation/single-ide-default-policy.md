# Single-IDE Default Policy

Date: 2026-04-05
Status: active
Scope: default operator policy for IDE usage, temporary parallel bursts, and merge authority

## 1. Default Rule

- default operating mode is `single`
- assume one main worktree, one main writer lane, and one final merge authority unless an explicit burst-mode switch is recorded
- do not infer multi-IDE mode from installed editors, past notes, or stale worktree assumptions

## 2. Burst-Mode Rule

- `split_3ide` is a temporary burst mode, not the baseline operating model
- enter it only when there is a bounded parallel payoff that clearly outweighs coordination cost
- if that payoff is not explicit, stay in `single`

Minimum burst gate:

1. `IDE-1` has a real runtime or queue-owner lane that should remain centralized
2. `IDE-2` has an independent Stage0 or BI/TR lane with no shared-file collision
3. `IDE-3` can stay doc-first or process-first without silently editing runtime ownership files
4. separate worktrees and separate branches exist before support writes begin

## 3. Ownership Rule

- read is open, but write is owner-first
- `IDE-1` remains the final merge authority and shared-file lock owner
- support lanes do not directly edit shared queue files or active lock files by default

## 4. Return Rule

- after a bounded parallel burst, return to `merge_only`, then back to `single`
- do not leave the workspace in an implicitly multi-IDE state after the burst is over

## 5. Opus / External Operator Rule

- if handing work to Opus or another external model, never imply that multi-IDE mode is automatically on
- tell the model the current mode explicitly
- give one bounded unit at a time
- if the mode is `single`, the model should behave as if only the main lane is active unless the burst switch is explicitly restated
