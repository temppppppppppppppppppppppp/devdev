# Codex Lead Memory Cards Minimal System 3-Pass Audit

Date: 2026-04-21
Status: final
Scope: lightweight GitHub-centered memory-card system that lets a session-based `Codex Lead` recover issue-wave state without a dedicated app
Path Policy: canonical dated doc only at `docs/2026-04-21/`; no `docs/temp/` mirror because this is an operating-note design, not an execution SSOT
Side-Effect Coverage: documentation and lightweight operator workflow only; this document does not itself authorize merge automation, unattended orchestration, or GitHub state mutation
Out of Scope:
- dedicated Lead UI or desktop app
- autonomous worker spawning
- replacing GitHub as SSOT
- making `n8n` a reasoning supervisor
- forcing every issue to use a heavyweight memory artifact

Commit State:
- Baseline Commit: `96814c496ac007dc764e0413e16d01d919e47399`
- Baseline Dirty Summary: `dirty: tracked AGENTS.md plus untracked docs/2026-04-21, .github/, ops/, local xlsx`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Evidence Basis:
- `docs/2026-04-21/codex-centered-ai-dev-team-operating-model-3pass-audit.md`
- `docs/2026-04-21/codex-ai-dev-manual-wave-runbook-3pass-audit.md`
- `docs/2026-04-21/codex-lead-app-requirements-3pass-audit.md`
- current workspace shortcut rules in `AGENTS.md` for `Codex Lead` and `Meta Lead`
- current repo bootstrap surfaces:
  - `.github/ISSUE_TEMPLATE/codex-ai-dev-task.md`
  - `.github/PULL_REQUEST_TEMPLATE/codex-ai-dev-pr.md`
  - `ops/ai-team/bootstrap-manual-wave.ps1`
  - `ops/n8n/`

## 1. Decision Summary

Before building a Lead app, the workspace should use a minimal memory system:

1. keep `GitHub` as the work truth
2. keep exactly one active lead-memory comment per issue wave
3. keep that comment short, structured, and updated in place
4. use only three cards inside that comment:
   - `Issue Card`
   - `Lane Card`
   - `Canary Card`
5. let `n8n` read and mirror the card, not reason over it

This gives the Lead a small external memory without turning operations into a product project too early.

## 2. Why This Exists

The immediate problem is not missing UI. It is Lead cognitive overload.

When a session ends, a new `Codex Lead` should not need to reconstruct everything from:

- long chat history
- scattered GitHub comments
- partial PR text
- raw canary logs

The memory-card system exists to externalize only the minimum state that must survive across sessions:

- what the issue is trying to achieve
- which lanes are active
- what the last important run found
- what decision is currently waiting

## 3. Storage Contract

### 3.1 Canonical storage

For each active issue wave, maintain one designated top-level GitHub issue comment with this marker:

`<!-- lead-memory:v1 -->`

That marker is the only hard requirement.

If the team later wants to pin the comment or link it from the issue body, that is allowed, but the base contract is only:

- one designated comment
- updated in place
- latest state wins

### 3.2 Why not more than one memory comment

Multiple memory comments recreate the same overload the system is supposed to remove.

The rule is:

- one issue wave
- one active memory comment
- one current state

Historical details can live in normal comments, logs, PRs, and artifacts.

## 4. The Three Cards

### 4.1 Issue Card

Purpose:
- hold stable issue-wave intent
- give the Lead enough context to resume without rereading the whole issue

Required fields:
- `issue_id`
- `state`
- `goal`
- `acceptance`
- `non_goals`
- `risk`
- `integration_branch`
- `active_prs`
- `next_decision`

Keep this card short.

Good:
- one-line goal
- short acceptance bullets joined by `;`
- one explicit next decision

Bad:
- long narrative recap
- design essay
- repeated logs

### 4.2 Lane Card

Purpose:
- externalize who is doing what
- prevent Lead memory from becoming the lane board

Each active lane gets one repeated lane block.

Required fields per lane:
- `lane`
- `owner`
- `role`
- `scope`
- `allowlist`
- `branch`
- `worktree`
- `status`
- `blocker`

Default rule:
- start with at most `2` active worker lanes
- a third lane is allowed only if it is clearly `test`, `hardening`, `hotfix`, or `reserve`

### 4.3 Canary Card

Purpose:
- preserve the latest run truth without drowning the Lead in logs

Required fields:
- `run_kind`
- `owner`
- `command`
- `status`
- `last_failure`
- `artifacts`
- `next_retry`

This card is not only for formal canary.

It can also track:
- fresh run
- bounded `L1`
- retry after patch
- waiting state before rerun

## 5. Minimal Formatting Contract

Use:
- simple markdown headings
- `field: value` lines
- repeated lane blocks under one `Lane Card` section

Avoid:
- markdown tables unless a specific workflow needs them
- nested checklists
- prose paragraphs inside the comment body
- freeform commentary mixed into state fields

Reason:
- easier for a tired human to scan
- easier for `n8n` or scripts to parse later
- lower update friction

## 6. Update Rules

### 6.1 Ownership

- `Codex Lead` owns `Issue Card`
- `Codex Lead` owns `Lane Card`
- `Runner` or current run owner may draft raw run notes, but `Codex Lead` consolidates the `Canary Card`
- `n8n` is read-only against the card unless explicitly authorized for mirror comments later

### 6.2 Update timing

Update the memory comment when one of these happens:

- issue split frozen
- lane added, closed, or rescope required
- blocker appears or clears
- integration branch changes
- fresh run or canary reaches a meaningful state
- the next operator decision changes

Do not update it for every tiny local thought.

### 6.3 Unknowns

If a field is not known yet, write:

- `unknown`

If a field is explicitly empty, write:

- `none`

That is better than leaving ambiguous blanks.

## 7. Rehydrate Contract For Session-Based Lead

When a new session starts with `코덱스 리드` or equivalent, the Lead should recover in this order:

1. read the issue title and current labels
2. locate the comment containing `<!-- lead-memory:v1 -->`
3. read `Issue Card`
4. read only active or blocked lane blocks in `Lane Card`
5. read `Canary Card`
6. inspect open PRs only if the memory card says they are active
7. reply with a short current-state summary before doing deeper work

The Lead should not reread the full issue history by default if the memory card is current and coherent.

## 8. `n8n` Read Model

`n8n` should treat the memory card as a mirror source, not a decision engine.

Minimal read model:

1. find issue comment containing `<!-- lead-memory:v1 -->`
2. parse the three sections
3. extract only operational fields:
   - `state`
   - lane statuses
   - blockers
   - run status
   - next decision
4. render dashboard or summary

`n8n` should not infer missing authority or invent new state transitions from vague prose.

## 9. Recommended Output On Return

After reading the memory card, the Lead should answer in a short fixed shape:

- `Current issue`
- `Issue state`
- `Active lanes`
- `Blockers`
- `Waiting decision`
- `Recommended next action`

This is intentionally small. The goal is fast re-entry, not a report.

## 10. Practical Boundaries

Use the memory-card system when:

- an issue wave is active across sessions
- more than one lane exists
- a fresh run or rerun loop is involved
- the operator wants to step away and return later

Do not force it when:

- a change is a tiny one-shot bugfix
- there is no active lane split
- the memory card would be longer than the issue itself

If the card becomes bloated, shrink it. The system only works while it stays lighter than raw history.

## 11. Initial Recommendation

Start with:

- `Issue Card`
- `Lane Card`
- `Canary Card`
- one designated GitHub issue comment
- manual updates by `Codex Lead`

Only after this proves useful should the workspace consider:

- issue-body backlink to the comment
- `n8n` dashboard parsing
- helper scripts to refresh or validate card structure

## 12. Three-Pass Self-Audit

### 12.1 Pass 1. Structure and scope

Findings:
- the draft initially drifted toward a mini app spec instead of a small operating artifact
- the memory system needed a hard cap on concepts and fields

Changes applied:
- reduced the design to one comment and three cards
- removed broader UI or workflow ambitions
- kept the contract focused on rehydration and low-friction updates

### 12.2 Pass 2. Evidence and consistency

Findings:
- the design had to remain consistent with existing GitHub-first, n8n-subordinate governance
- a strong dependency on comment pinning would create avoidable platform ambiguity

Changes applied:
- made the marker comment, not pinning, the actual contract
- kept `n8n` read-only and mirror-first
- aligned the design with the existing Codex Lead and manual-wave documents

### 12.3 Pass 3. Execution and readability

Findings:
- a memory system fails if updating it feels heavier than using it
- too many fields or prose sections would recreate Lead overload

Changes applied:
- switched to `field: value` formatting
- defined explicit update triggers
- bounded the return summary to six short lines

Confidence:
- Estimated confidence after 3-pass audit: `97%`
- Remaining uncertainty: exact GitHub operating habit for linking the designated memory comment into day-to-day workflow still needs one live issue-wave trial
