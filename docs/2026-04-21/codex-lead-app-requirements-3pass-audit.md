# Codex Lead App Requirements 3-Pass Audit

Date: 2026-04-21
Status: final
Scope: requirements and operating design for a lightweight Codex Lead App that acts as the control console for the Codex-centered AI dev team
Path Policy: canonical dated doc only at `docs/2026-04-21/`; no `docs/temp/` mirror because this is a product/ops design note, not an execution SSOT
Side-Effect Coverage: human-facing design only; this document does not itself authorize UI implementation, workflow mutation, merge automation, or agent spawning
Out of Scope:
- replacing GitHub as the authoritative work surface
- making `n8n` the reasoning supervisor
- full autonomous swarm behavior on first release
- narrative-pipeline orchestration

Commit State:
- Baseline Commit: `96814c496ac007dc764e0413e16d01d919e47399`
- Baseline Dirty Summary: `dirty: tracked AGENTS.md plus untracked docs/2026-04-21, ops/, local xlsx`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Evidence Basis:
- `docs/2026-04-21/codex-centered-ai-dev-team-operating-model-3pass-audit.md`
- `docs/2026-04-21/codex-ai-dev-manual-wave-runbook-3pass-audit.md`
- current workspace shortcut rule in `AGENTS.md` for `Codex Lead`
- current local bootstrap surfaces:
  - `.github/ISSUE_TEMPLATE/codex-ai-dev-task.md`
  - `.github/PULL_REQUEST_TEMPLATE/codex-ai-dev-pr.md`
  - `ops/ai-team/bootstrap-manual-wave.ps1`
  - `ops/github/bootstrap-ai-dev-labels.ps1`
  - `ops/n8n/`

## 1. Product Thesis

The `Codex Lead App` is not an IDE and not a worker.

It is a lightweight control console that lets the operator manage a small AI development team without staying glued to implementation details.

The intended interaction is:

1. the operator opens the lead app
2. the operator gives high-level instructions to the lead
3. the lead app holds the authoritative team state needed for that issue wave
4. worker prompts or cards are emitted from the lead app into execution lanes
5. `GitHub` remains the truth for issue / branch / PR state
6. `n8n` mirrors and visualizes outcomes

## 2. Core Design Principles

### 2.1 Authority

- `GitHub` remains the work SSOT
- `Codex Lead App` is the control console, not the work truth
- `n8n` is dispatcher and reporter only
- `ClickUp` is optional human-facing reflection only

### 2.2 Lightweight first

The lead app should feel closer to a mission-control panel than a full IDE:

- fast to open
- fast to glance at
- fast to issue commands from
- easy to leave running in the background

### 2.3 Operator-first

The app must support the user's real goal:

- issue instructions
- go do other things
- come back only for exceptions, approvals, and final decisions

### 2.4 Bounded parallelism

The first release is optimized for:

- `1 lead`
- `2 active Codex worker lanes`
- optional `Claude Junior` helper lane
- optional future canary lane

Do not optimize the first release for a giant swarm.

## 3. What The Lead App Must Know

The lead app must maintain a live state model for each active issue wave.

Minimum required state:

- active GitHub issue id and title
- issue status label
- issue goal
- acceptance criteria
- non-goals
- risk level
- lane count
- worker lane ownership
- each lane's touch allowlist
- each lane's branch
- each lane's worktree path
- lane validation status
- integration branch status
- canary status
- current blockers
- next operator decision needed

Without this state, the lead app is only a chat UI and not a real control console.

## 4. Domain Model

### 4.1 Issue Wave

An `Issue Wave` is the top-level unit inside the app.

Fields:

- `issue_id`
- `title`
- `goal`
- `acceptance`
- `non_goals`
- `risk`
- `ai_state`
- `repo`
- `base_branch`
- `integration_branch`
- `operator_note`

### 4.2 Lane

A `Lane` is a worker-owned bounded execution unit.

Fields:

- `lane_id`
- `issue_id`
- `lane_type`
  - `worker-a`
  - `worker-b`
  - `claude-junior`
  - `hotfix`
  - future: `canary`
- `owner`
- `scope_summary`
- `touch_allowlist`
- `branch`
- `worktree_path`
- `status`
- `validation_level`
- `blocked_reason`

### 4.3 Review Unit

A `Review Unit` holds what the lead must inspect before integration.

Fields:

- `lane_id`
- `changed_files`
- `diff_summary`
- `scope_compliance`
- `risk_note`
- `ready_for_integration`

### 4.4 Canary Run

Fields:

- `issue_id`
- `branch`
- `canary_level`
- `command`
- `started_at`
- `ended_at`
- `status`
- `key_findings`
- `artifact_links`

### 4.5 Summary Card

This is what gets mirrored outward.

Fields:

- `headline`
- `status`
- `human_summary`
- `technical_summary`
- `risk`
- `action_needed`
- `destinations`
  - `GitHub comment`
  - `n8n event`
  - `ClickUp sync`

## 5. Required Screens

### 5.1 Home / Command Console

This is the default lead surface.

Must show:

- active issue waves
- lane count per issue
- blocked items
- canary queue
- items waiting for operator approval
- one command entry surface

The operator should be able to say things like:

- `issue 412 split into 2 lanes`
- `worker 하나 더 붙일 수 있으면 붙여`
- `Claude는 PR 설명만`
- `이거 끝나면 다음 이슈도 준비`

### 5.2 Issue Wave Detail

Must show:

- issue summary
- acceptance and non-goals
- current label
- lane board
- integration status
- open blockers
- last lead decision

This is the main “team leader per issue” screen.

### 5.3 Lane Detail

Must show:

- lane owner
- lane scope
- touch allowlist
- branch and worktree
- recent updates
- validation status
- blocked state

Must expose explicit commands:

- `pause lane`
- `resume lane`
- `rescope lane`
- `close lane`
- `promote to review`

### 5.4 Worker Card Preview

Before sending work to a worker, the lead app must render the exact worker card.

That card should include:

- role
- issue goal
- lane scope
- touch allowlist
- out-of-scope surfaces
- expected validation level
- output format

The operator or lead should be able to inspect this before dispatch.

### 5.5 Review / Integration Screen

Must show:

- lane diffs side by side
- overlapping file warnings
- allowlist violations
- integration branch status
- review verdict options

Required review outcomes:

- `accept into integration`
- `send back to lane`
- `resplit required`
- `hotfix lane required`

### 5.6 Canary Screen

Must show:

- queued canaries
- active canary
- last completed canary
- command used
- status and findings
- recommended next action

This lets the operator ignore low-level logs unless needed.

### 5.7 Event Log / Timeline

Must show:

- issue opened
- lane split
- card dispatched
- lane updated
- lane blocked
- integration started
- canary started
- canary completed
- summary mirrored

This screen is critical for the "I went to watch a movie, what happened?" use case.

## 6. Required Actions

### 6.1 Lead planning actions

- create issue wave
- split issue into `1` or `2` lanes
- expand lane count only after rescope
- declare acceptance and non-goals
- set canary level

### 6.2 Lane control actions

- assign worker
- reassign worker
- freeze scope
- edit touch allowlist
- pause/resume lane
- escalate lane
- close lane

### 6.3 Review actions

- accept lane
- reject lane
- request changes
- merge into integration
- mark overlap conflict

### 6.4 Canary actions

- queue canary
- run canary
- retry canary
- create hotfix lane from canary failure

### 6.5 Mirror actions

- publish GitHub summary
- trigger `n8n` mirror event
- publish ClickUp human summary

Mirror actions must never outrank GitHub truth.

## 7. Required Integrations

### 7.1 GitHub

Must integrate first and best.

Needed surfaces:

- issues
- labels
- comments
- branches
- PRs
- PR review state
- changed files
- commit status / checks

### 7.2 Local Worktree / Branch Manager

Needed because the lead app must know where workers are operating.

The app should at minimum be able to:

- display branch names
- display worktree paths
- call a local bootstrap helper
- show when paths collide or already exist

### 7.3 `n8n`

`n8n` integration is downstream:

- event fan-out
- summary reflection
- notifications
- simple dashboards

`n8n` should not become the app's reasoning engine.

### 7.4 ClickUp

Optional and late.

Only for:

- human summaries
- dashboard reflection
- executive visibility

### 7.5 Claude Junior

Optional helper lane.

The lead app should be able to create a low-authority helper task such as:

- write PR summary
- convert logs to human summary
- tidy issue text

## 8. Command and Card Design

### 8.1 Operator command style

The app must support short natural commands.

Examples:

- `리드, 412 split`
- `이거 worker 하나 늘릴 수 있으면 늘려`
- `Claude는 PR 설명만`
- `지금 상태 요약`
- `blocker만 보여줘`
- `canary 언제 끝나`

### 8.2 Worker card schema

Every dispatched worker card must contain:

- `issue_id`
- `lane_id`
- `goal`
- `acceptance`
- `non_goals`
- `scope_summary`
- `touch_allowlist`
- `validation_level`
- `branch`
- `worktree_path`
- `report_back_format`

This is what keeps worker behavior bounded.

## 9. Idle-Operator Mode

This is a first-class requirement.

The lead app must support the operator being absent.

That means:

- it holds active issue-wave state while the operator is away
- it records major events in a timeline
- it can produce a one-screen summary on return
- it highlights only the decisions that truly need the operator

Minimum return summary:

- active issues
- blocked lanes
- waiting approvals
- canary outcomes
- next recommended action

## 10. Safety Guardrails

### 10.1 No hidden authority transfer

The app must not silently let:

- `n8n`
- `ClickUp`
- `Claude Junior`

become the decision authority.

### 10.2 No scope-free worker dispatch

The app must refuse to dispatch a worker lane without:

- touch allowlist
- acceptance criteria
- non-goals
- branch
- worktree

### 10.3 No merge without review state

The app must treat merge recommendation as blocked unless:

- review is complete
- integration branch exists
- canary result is attached or explicitly waived

### 10.4 No over-parallelization by default

The app must bias toward:

- two worker lanes max initially
- explicit rescope before expansion

## 11. MVP Recommendation

### 11.1 MVP features

Build these first:

- home / command console
- issue wave detail
- lane detail
- worker card preview
- event log
- GitHub issue and PR data ingestion
- local worktree/branch display

### 11.2 Defer until after MVP

- autonomous lane expansion
- more than two worker lanes
- canary lane as a dedicated permanent worker
- ClickUp writeback in the primary UI
- large `n8n` orchestration editor inside the app

## 12. Rollout Order

### 12.1 Phase A

Lead app as a read/write control console over manual wave operations.

### 12.2 Phase B

Lead app emits worker cards and reads GitHub state automatically.

### 12.3 Phase C

Lead app pushes summaries into `n8n` and receives mirrored operational telemetry back.

### 12.4 Phase D

Lead app supports bounded lane expansion, hotfix lane creation, and richer idle-operator mode.

## 13. Success Criteria

The lead app is successful when:

- the operator can manage one issue wave without opening a full coding IDE
- the operator can disappear and return without losing the thread
- the lead app always knows lane scope, branch, worktree, and blocker state
- worker cards remain bounded and inspectable
- GitHub remains the work truth
- `n8n` becomes a mirror, not a supervisor

## 14. Three-Pass Self-Audit

### 14.1 Pass 1. Structure and scope

Findings:

- the draft risked drifting into a vague product brainstorm instead of a control-console requirements doc
- the app had to be clearly separated from both IDE and worker concepts

Changes applied:

- centered the document on control-console requirements
- defined explicit domain objects, screens, actions, and integrations

### 14.2 Pass 2. Evidence and consistency

Findings:

- the app authority model had to remain consistent with the already approved Codex operating model
- `n8n` and ClickUp positioning had to stay subordinate

Changes applied:

- anchored authority to GitHub and the Codex operating model
- explicitly rejected `n8n` as supervisor
- kept ClickUp reflection-only

### 14.3 Pass 3. Execution and readability

Findings:

- the design needed to support the user's real “go do something else” behavior
- the minimum operator-return summary was initially implied rather than explicit

Changes applied:

- added idle-operator mode as a first-class requirement
- defined the exact minimum return summary
- kept MVP scope bounded to avoid overbuilding

Confidence:

- Estimated confidence after 3-pass audit: `96%`
- Remaining uncertainty: exact app implementation surface (desktop app, web app, or lightweight launcher shell) is still an execution decision, not a design ambiguity
