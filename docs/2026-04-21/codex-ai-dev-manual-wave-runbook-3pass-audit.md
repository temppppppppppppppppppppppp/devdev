# Codex AI Dev Manual Wave Runbook 3-Pass Audit

Date: 2026-04-21
Status: final
Scope: first manual GitHub-centered issue wave for the Codex-led AI dev-team model
Path Policy: canonical dated doc only at `docs/2026-04-21/`; no `docs/temp/` mirror because this is a runbook note, not an execution SSOT
Side-Effect Coverage: human operating guidance, GitHub template usage, and local worktree bootstrap only
Out of Scope:
- unattended merge automation
- multi-issue swarm execution
- autonomous `n8n` intake mutation

Commit State:
- Baseline Commit: `96814c496ac007dc764e0413e16d01d919e47399`
- Baseline Dirty Summary: `dirty: untracked docs/2026-04-21, ops/, local xlsx`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Evidence Basis:
- `docs/2026-04-21/codex-centered-ai-dev-team-operating-model-3pass-audit.md`
- `.github/ISSUE_TEMPLATE/codex-ai-dev-task.md`
- `.github/PULL_REQUEST_TEMPLATE/codex-ai-dev-pr.md`
- `ops/ai-team/bootstrap-manual-wave.ps1`
- `ops/github/ai-dev-labels.json`

## 1. Goal

Prove the minimum Codex-centered AI development lane with one issue, up to two worker branches, one integration branch, and one bounded `L1` canary.

## 2. Preconditions

- The issue is created from the Codex AI Dev Task template.
- The issue starts with exactly one `ai:` label, normally `ai:ready`.
- `Codex Lead` is named before any worker starts.
- Worker lane count is `1` or `2`, never more for the first proving wave.
- Each worker receives:
  - file scope
  - touch allowlist
  - acceptance criteria
  - non-goals
  - expected canary level

## 3. Bootstrap

Optional helper commands:

```powershell
.\ops\ai-team\bootstrap-manual-wave.ps1 -IssueId 412 -DryRun
.\ops\github\bootstrap-ai-dev-labels.ps1 -UpdateExisting
.\ops\ai-team\bootstrap-manual-wave.ps1 -IssueId 412
```

Expected branch layout:

- `integration/412`
- `task/412-a`
- `task/412-b`

Expected worktree layout:

- `..\wt-412-int`
- `..\wt-412-a`
- `..\wt-412-b`

## 4. Worker Rules

- Worker A edits only its touch allowlist.
- Worker B edits only its touch allowlist.
- If a worker needs another file, stop and resplit through `Codex Lead`.
- Workers run `L0` checks only unless the lead explicitly overrides that rule.
- Workers do not merge directly to `main`.

## 5. Review and Integration

1. Workers open PRs or diffs against `integration/<issue-id>`.
2. `Codex Lead` reviews both lanes.
3. If scopes collided, stop and reduce to one owner for the conflicting file.
4. Merge accepted worker branches into the integration branch only.
5. Move the issue to `ai:review` and then `ai:canary` when integration is ready.

## 6. Canary

- `Codex Lead` owns `L1` canary.
- Use a bounded run that matches the issue surface.
- For the current workspace, a representative `L1` is:

```powershell
python -X utf8 scripts/run_stage4_canary.py run --project projects/00_0420 --target-ep 4
```

- If canary fails, create a bounded hotfix lane or return to the worker lane owner.

## 7. Closeout

- `Human Approver` reviews the final evidence.
- Only after that may the issue move to `ai:done`.
- `n8n`, when enabled later, may mirror summary and status outward.
- `ClickUp` may receive a human-facing summary, but it does not become authoritative.

## 8. Success Criteria

The first manual wave is considered successful when:

- one issue completes the full path from `ai:ready` to merge recommendation
- no worker edits outside its touch allowlist
- only one integration branch is used
- one bounded `L1` canary is run
- the final summary can be posted to GitHub without ambiguity

## 9. Three-Pass Self-Audit

### 9.1 Pass 1. Structure and scope

Findings:

- the runbook needed to stay procedural and avoid re-explaining the entire operating model
- bootstrap commands and success criteria were initially missing

Changes applied:

- narrowed the doc to one proving wave
- added bootstrap commands and success criteria

### 9.2 Pass 2. Evidence and consistency

Findings:

- the runbook had to align with the operating model's authority order
- the helper script and template paths needed to be explicit

Changes applied:

- anchored the runbook to the canonical operating-model doc
- named the exact template and helper-script paths

### 9.3 Pass 3. Execution and readability

Findings:

- the worker and canary rules needed to be easy to scan during live use
- closeout needed to stay explicit about human approval and ClickUp non-authority

Changes applied:

- kept the runbook stepwise
- made merge and ClickUp rules explicit in the closeout section

Confidence:

- Estimated confidence after 3-pass audit: `96%`
- Remaining uncertainty: the exact first issue number and future label automation payloads are live-run details, not document-level unknowns
