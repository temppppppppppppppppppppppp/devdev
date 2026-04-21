<!-- lead-memory:v1 -->
# Lead Memory

update_owner: codex-lead
updated_at: YYYY-MM-DDTHH:MM:SS+09:00
source_of_truth: github-issue-pr

## Issue Card

issue_id: <issue-number>
state: ai:ready | ai:split | ai:coding | ai:review | ai:canary | ai:blocked | ai:done
goal: <one-line goal>
acceptance: <short acceptance 1>; <short acceptance 2>
non_goals: <short non-goal 1>; <short non-goal 2>
risk: low | high
integration_branch: integration/<issue-id> | none
active_prs: <pr-number list> | none
next_decision: <operator-or-lead decision needed> | none

## Lane Card

lane: a
owner: codex-worker-a
role: implementation
scope: <short scope summary>
allowlist: <path>; <path>
branch: task/<issue-id>-a
worktree: ../wt-<issue-id>-a
status: planned | coding | review | blocked | done
blocker: none

lane: b
owner: codex-worker-b | none
role: implementation | test | hardening | hotfix | reserve
scope: <short scope summary> | none
allowlist: <path>; <path> | none
branch: task/<issue-id>-b | none
worktree: ../wt-<issue-id>-b | none
status: idle | planned | coding | review | blocked | done
blocker: none

## Canary Card

run_kind: fresh-run | L0 | L1 | L2 | not-started
owner: codex-runner | none
command: <exact command> | none
status: not-started | running | failed | passed | waiting-rerun
last_failure: <one-line latest failure> | none
artifacts: <log path or PR or comment link> | none
next_retry: <who does what next> | none

## Notes

- Keep one active memory comment per issue wave.
- Update this comment in place.
- If a value is not known yet, use `unknown`.
- If a value is explicitly empty, use `none`.
