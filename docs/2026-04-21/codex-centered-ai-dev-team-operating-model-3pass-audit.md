# Codex-Centered AI Dev Team Operating Model 3-Pass Audit

Date: 2026-04-21
Status: final
Scope: system-track operating model for a GitHub-centered AI parallel development team in this workspace
Path Policy: canonical dated doc only at `docs/2026-04-21/`; no `docs/temp/` mirror because this is an operating-model note, not an execution SSOT
Side-Effect Coverage: documentation and future workflow governance only; this save does not itself authorize code mutation, merge automation, or ClickUp authority changes
Out of Scope:
- narrative-pipeline governance
- auto-merge or unattended production shipping
- replacing existing repo queue governance with ClickUp
- expanding to a many-role autonomous mesh before the minimal lane proves stable

Commit State:
- Baseline Commit: `96814c496ac007dc764e0413e16d01d919e47399`
- Baseline Dirty Summary: `dirty: 2 untracked; surfaces: ops/, local xlsx`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Evidence Basis:
- `AGENTS.md` document-save rule and system-track governance
- `README.md` ClickUp rule: ClickUp is an external visibility surface, not authoritative queue state
- `docs/implementation/temp-execution-queue-roadmap-harness.md` ClickUp reflection rule and authority order
- live workspace state on 2026-04-21:
  - Docker Desktop installed and running
  - `n8n` installed locally
  - local `ops/n8n/` bootstrap present for future automation rollout

## 1. Decision Summary

The operating direction is:

1. `GitHub` is the working SSOT for AI development flow.
2. `Codex` is the primary technical authority.
3. `Claude` is explicitly downgraded to a junior helper lane.
4. `n8n` is not the team lead; it is a dispatcher and reporter.
5. `ClickUp` remains a human-facing summary surface only, and it is synced only on explicit human request.
6. Automation rollout is phased: document first, then manual run, then low-risk read-mostly automation, then guarded intake automation.

This is intentionally not a full autonomous org chart. It is a minimal operating system for a small AI development team that can run today without collapsing into coordination overhead.

## 2. Authority Model

### 2.1 Core authority order

For this AI development lane, operating authority is:

1. human approval for merge and priority
2. GitHub issue / branch / PR / diff / review state
3. test and canary evidence
4. Codex Lead judgment
5. n8n automation output
6. ClickUp summary

### 2.2 Workspace compatibility note

This document does not override the workspace-wide queue rule that repo-side canonical docs and temp mirrors outrank ClickUp. It extends that same philosophy into the AI dev-team lane:

- repo and GitHub stay authoritative
- ClickUp mirrors outcomes for humans only when a human explicitly asks for that mirror
- automation reflects state; it does not invent authority

## 3. Team Topology

### 3.1 Minimum team

- `Codex Lead`
  - owns task split, technical direction, review gate, canary promotion, and merge recommendation
- `Codex Worker A`
  - owns one bounded implementation lane
- `Codex Worker B`
  - owns a second bounded implementation lane
- `Claude Junior`
  - owns low-authority support work only
- `n8n`
  - owns event routing, notifications, and summary sync only
- `Human Approver`
  - owns final priority changes and merge approval

### 3.2 Explicit non-goals

Do not start with:

- separate planner, spec writer, repo custodian, reviewer, and canary seats
- n8n as an autonomous supervisor
- more than two parallel Codex coding lanes
- automatic state mutation based on fuzzy LLM judgment

## 4. Role Contracts

### 4.1 Codex Lead

Allowed:

- split a GitHub issue into bounded worker lanes
- assign `file_scope`, touch allowlist, acceptance criteria, and canary level
- review worker diffs
- decide whether work may enter integration
- run or approve integration-level canary
- recommend merge

Not allowed:

- hand off core authority to n8n
- allow worker edits outside declared scope without explicit replan

### 4.2 Codex Workers

Allowed:

- edit only the files or directories on their touch allowlist
- run fast local validation
- raise blocker notes when task split is wrong

Not allowed:

- changing global architecture direction
- touching sibling worker scope without approval
- running heavyweight final canary as their default loop

### 4.3 Claude Junior

Allowed:

- PR description drafts
- issue hygiene
- log summarization
- documentation first drafts
- change summaries for humans
- repetitive clerical or categorization tasks

Not allowed:

- final technical review gate
- merge decision
- canary pass/fail authority
- primary task decomposition authority

### 4.4 n8n

Allowed:

- receive GitHub events
- trigger approved workflows
- copy summarized status into GitHub comments
- copy summarized status into ClickUp only when a human explicitly asks for the slower human-facing mirror
- notify on timeout, failure, or canary completion

Not allowed:

- acting as the team lead
- deciding task split quality
- deciding whether code is correct
- mutating authoritative state from ambiguous heuristics

## 5. Operating Flow

### 5.1 Canonical minimal flow

1. `GitHub Issue` enters `ai:ready`
2. `Codex Lead` splits the issue into at most two bounded worker lanes
3. `Codex Worker A/B` implement in parallel on separate branches and worktrees
4. `Codex Lead` reviews, integrates, and resolves overlap
5. `Codex Lead` runs `L0` then `L1` canary on the integration branch
6. `Human Approver` merges after review and evidence check
7. `n8n` mirrors summaries and outcomes to human-facing surfaces only where the surface is explicitly requested

### 5.2 Why this flow is preferred

- parallelism exists where code can truly diverge
- review and canary remain centralized enough to avoid chaos
- Claude is helpful without holding authority
- n8n removes clerical work without becoming a reasoning bottleneck

## 6. Git and Scope Rules

### 6.1 Branch naming

- `integration/<issue-id>`
- `task/<issue-id>-a`
- `task/<issue-id>-b`
- `hotfix/<issue-id>-canary`

### 6.2 Worktree naming

- `..\wt-<issue-id>-a`
- `..\wt-<issue-id>-b`
- `..\wt-<issue-id>-int`

### 6.3 Touch allowlist rule

Each worker lane must receive:

- `file_scope`
- explicit touch allowlist
- acceptance criteria
- non-goals
- expected canary level

`file_scope` is descriptive.

Touch allowlist is binding.

If a worker needs to edit outside the allowlist, that is a replan event and must return to `Codex Lead`.

### 6.4 Integration rule

Worker branches do not merge directly to `main`.

They merge first into `integration/<issue-id>`, where review and canary happen.

## 7. GitHub State Model

### 7.1 Recommended labels

- `ai:ready`
- `ai:split`
- `ai:coding`
- `ai:review`
- `ai:canary`
- `ai:blocked`
- `ai:done`
- `scope:single-file`
- `scope:multi-file`
- `risk:low`
- `risk:high`

Keep exactly one `ai:` state label active at a time.

### 7.2 Transition ownership

- `ai:ready -> ai:split`: `Codex Lead`
- `ai:split -> ai:coding`: `Codex Lead` after worker scopes are frozen
- `ai:coding -> ai:review`: GitHub event or explicit lead action when worker PRs exist
- `ai:review -> ai:canary`: `Codex Lead`
- `ai:canary -> ai:done`: `Codex Lead` plus human merge approval
- any state -> `ai:blocked`: worker or lead may signal, but the lead owns unblock direction

The important rule is that `n8n` may mirror or relay these transitions, but it should not invent them from fuzzy reasoning.

## 8. Canary Policy

### 8.1 Levels

- `L0`: import checks, lint, smoke, very fast local confidence
- `L1`: bounded target validation for the actual issue surface
- `L2`: expensive integrated validation

### 8.2 Initial rule

- workers run `L0`
- `Codex Lead` runs `L1` on the integration branch
- `L2` is opt-in and used when risk justifies it

For the current workspace, `python -X utf8 scripts/run_stage4_canary.py run --project projects/00_0420 --target-ep 4` should be treated as an `L1` lane, not the default validation loop for every worker seat.

## 9. n8n Positioning

### 9.1 Approved positioning

`n8n = dispatcher + reporter`

That means:

- webhook intake
- event fan-out
- low-risk workflow triggering
- result posting
- explicit-request ClickUp sync

### 9.2 Rejected positioning

`n8n = supervisor`

Rejected because:

- reasoning and debugging are weaker than in the coding agent lane
- hidden workflow state becomes hard to audit
- too much automation authority early will outpace operational clarity

## 10. ClickUp Positioning

ClickUp remains human-facing only.

Use it for:

- summary views
- executive visibility
- operator dashboards
- non-authoritative reminders

Default operating rule:

- do not sync ClickUp during routine GitHub- or repo-side issue work
- sync ClickUp only when a human explicitly asks for the mirror
- prefer GitHub issues and repo docs for everyday agent-facing flow because ClickUp sync latency is not worth paying on every queue update

Do not use it for:

- authoritative task truth
- technical review truth
- merge gating
- canary truth

## 11. Automation Rollout Order

### 11.1 Stage 0

Freeze this operating model and run one full issue manually.

Manual proving acceptance:

- one GitHub issue completes the full path from `ai:ready` to merge recommendation
- exactly two or fewer Codex worker lanes are used
- no worker edits outside its touch allowlist
- integration happens only through `integration/<issue-id>`
- one bounded `L1` canary run is executed on the integration branch
- one GitHub-facing summary and one human-facing summary are produced without changing authority order

### 11.2 Stage 1

Automate `wf_pr_summary` first.

Reason:

- read-mostly
- low risk
- high clerical payoff

### 11.3 Stage 2

Automate `wf_canary_report`.

Reason:

- useful visibility
- still bounded by explicit canary evidence

### 11.4 Stage 3

Automate `wf_github_intake` last.

Reason:

- it changes front-door workflow behavior
- it is the easiest place to create silent process drift if automated too early

## 12. Failure and Fallback Rules

### 12.1 Lead fallback

`Codex Lead` is a single point of failure if left undefined.

Required fallback:

- `Human Approver` may temporarily act as fallback lead
- or a secondary Codex seat may be promoted explicitly for one issue wave

### 12.2 Worker conflict

If two workers need the same file:

1. stop parallel coding on that file
2. return to lead for a resplit
3. prefer a single-owner merge over scope ambiguity

### 12.3 Automation failure

If `n8n` fails:

- do not block coding
- fall back to manual GitHub comments and manual ClickUp sync
- keep authoritative truth in GitHub and repo docs

## 13. Three-Pass Self-Audit

### 13.1 Pass 1. Structure and scope

Findings:

- the earlier concept risked becoming a full org chart instead of a minimal operating model
- `n8n supervisor` language created authority ambiguity
- the initial role count was too high for immediate adoption

Changes applied:

- reduced the startup topology to `Codex Lead + Worker A/B + Claude Junior + n8n + Human Approver`
- made `n8n` explicitly non-supervisory
- bounded the document to the minimum team that can run today

### 13.2 Pass 2. Evidence and consistency

Findings:

- ClickUp positioning had to match existing workspace governance
- authority needed to remain repo and GitHub first
- automation sequencing needed to reflect the already-installed local `n8n` bootstrap without overclaiming live workflow coverage

Changes applied:

- aligned ClickUp language with `README.md` and queue harness rules
- made GitHub and canary evidence the operational authority
- treated `ops/n8n/` as a future rollout surface, not proof that workflows already exist

### 13.3 Pass 3. Execution and readability

Findings:

- worker collision prevention was underspecified
- label transition ownership needed to be explicit
- canary level ownership needed to stay simple enough for first adoption

Changes applied:

- added the touch allowlist rule
- added label transition ownership
- fixed the initial canary model to `workers=L0`, `lead=L1`, `L2=opt-in`
- made the rollout order explicit: document -> manual run -> summary automation -> canary reporting -> intake automation

## 14. Final Direction

Proceed with this direction:

1. keep `GitHub` as the AI dev-team SSOT
2. keep `Codex` as the primary technical authority
3. keep `Claude` in a junior helper lane only
4. keep `n8n` as dispatcher and reporter, not team lead
5. prove the model with one manual issue wave before deeper automation

Confidence:

- Estimated confidence after 3-pass audit: `97%`
- Reason the confidence is not higher: live GitHub label setup and real workflow payload shapes are not yet materialized, so the structure is final but the field-level automation details still need first-run confirmation
