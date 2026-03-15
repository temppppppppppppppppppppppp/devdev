# Commit State Minimal Contract

Date: 2026-03-14
Status: active
Applies To: system-track ROL surveys, re-audits, execution SSOTs, and execution roadmaps

## 1. Purpose
- Capture the minimum git workspace anchor needed to tell whether a saved ROL document still represents the live workspace.
- Keep commit-state recording lightweight enough that operators actually keep it current.
- Separate historical canonical authority from later resume or revalidation state.

## 2. Required Minimal Fields
Use exactly these four fields unless the task explicitly needs more detail.

- `Baseline Commit`
  - the git `HEAD` commit when the document's evidence pass begins
- `Baseline Dirty Summary`
  - short summary of `git status --short` at baseline
  - prefer `clean` or a short bounded summary such as `dirty: 2 tracked, 1 untracked; hotspots: main_a.py, modules/api/bridge_server.py`
- `Resume Commit`
  - the git `HEAD` commit when the document is resumed, revalidated, or used to govern implementation
  - if no later resume occurred, use `same-as-baseline`
- `Resume Drift Summary`
  - short bounded summary of what changed between baseline and resume
  - prefer `none` or a summary such as `2 commits since baseline; dirty: 1 tracked; surfaces: scripts/run_stage4_canary.py, tests/test_run_stage4_canary.py`

## 3. Commands
Preferred commands:

- baseline or resume head:
  - `git rev-parse HEAD`
- dirty summary source:
  - `git status --short`
- commit delta source when resuming:
  - `git log --oneline <baseline_commit>..HEAD`

Do not paste long command output into human-facing docs when a short summary is sufficient.

## 4. Usage Rules
- Record baseline fields when substantial survey, re-audit, execution-doc, or roadmap work begins.
- Refresh the resume fields when:
  - resuming a paused ROL item
  - revalidating an execution SSOT or roadmap before implementation
  - closing a delta re-audit that depends on post-baseline workspace drift
- Treat a changed `Resume Commit` or non-empty `Resume Drift Summary` as an authority check, not as automatic invalidation.
- If drift is substantial, say whether the prior canonical doc remains sufficient or must be superseded.

## 5. Placement
Recommended placement is near the top metadata block of:
- deep surveys
- re-audits
- execution SSOTs
- execution roadmaps

Use this shape:

Commit State:
- Baseline Commit: `<hash>`
- Baseline Dirty Summary: `clean | dirty: ...`
- Resume Commit: `same-as-baseline | <hash>`
- Resume Drift Summary: `none | ...`

## 6. Guardrails
- Do not turn commit-state capture into a full git transcript dump.
- Do not omit dirty-state context when the worktree is not clean.
- Do not claim a document reflects the current workspace without refreshing the resume fields first.
- Do not let commit-state notes override live code evidence; they are authority anchors, not substitutes for re-audit.
