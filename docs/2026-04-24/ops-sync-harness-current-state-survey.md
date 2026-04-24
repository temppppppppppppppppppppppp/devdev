# Ops Sync Harness Current State Survey

Date: 2026-04-24
Status: final
Canonical Path: `docs/2026-04-24/ops-sync-harness-current-state-survey.md`

## 1. Question

Does parking an execution item in the repo roadmap automatically create or update GitHub Issues or ClickUp tasks?

Short answer after the 2026-04-24 harness improvement:

- Roadmap -> `docs/temp/queue-state.json`: manual/local script sync.
- Roadmap -> GitHub Issues: explicit script sync through `scripts/sync_github_issues.py`; not automatic background sync.
- GitHub Issues -> roadmap: no detected importer.
- Roadmap -> ClickUp: not automatic; explicit user-requested one-way mirror only.
- ClickUp -> roadmap: not SSOT and no detected authoritative reverse sync.

## 2. Evidence

Repo queue state:

- `scripts/sync_temp_queue_state.py` reads temp execution SSOT mirrors and `docs/temp/execution-roadmap.md`.
- It writes `docs/temp/queue-state.json`.
- It parses optional `execution_meta.github_issue`, but it does not create, update, or comment on GitHub Issues.

GitHub issue readiness:

- `scripts/github_issue_readiness.py` checks whether every active temp execution SSOT mirror has `execution_meta.github_issue`.
- It reports readiness for issue-driven workflows.
- It does not create missing issues.
- Current run after the GitHub issue sync harness improvement found links for all five active queue docs: `#5`, `#3`, `#10`, `#8`, and `#9`.
- `stage0-bi-tr-production-harness-normalization-remediation` was migrated to the execution metadata block contract and linked to GitHub issue `#10`.

GitHub issue sync:

- `scripts/sync_github_issues.py` mirrors repo-side queue items into GitHub Issues.
- It is dry-run by default.
- `--apply` creates missing issues or links matched issues back into `execution_meta.github_issue`.
- Already linked issues are not title/body-updated unless `--update-existing` is passed.
- This keeps existing hand-written issue bodies from being overwritten during routine queue maintenance.
- The harness passed a 3-pass adversarial audit in `docs/2026-04-24/github-issue-sync-harness-adversarial-3pass-audit.md`.

GitHub comment helper:

- `scripts/post_benchmark_operator_comment.py` can preview or post a benchmark operator snapshot to an existing GitHub issue.
- It requires explicit `--post`.
- It is not a generic roadmap-to-issue sync.

ClickUp sync:

- `scripts/sync_clickup_queue.py` says it is intentionally one-way: repo queue artifacts -> ClickUp visualization.
- It needs an explicit list id or environment configuration and an explicit run.
- `README.md` states ClickUp is an external visibility surface and should be reflected only after explicit user request.
- `docs/2026-04-10/clickup-system-development-direction-operating-note.md` says the repo remains the authoritative queue and ClickUp should not become semantic or technical SSOT.

## 3. Current Operating Model

The current model is:

```text
canonical execution SSOT docs
  -> docs/temp/*-execution-ssot.md mirrors
  -> docs/temp/execution-roadmap.md
  -> scripts/sync_temp_queue_state.py
  -> docs/temp/queue-state.json
```

External mirrors are explicit:

```text
repo queue artifacts
  -> explicit sync_github_issues.py run
  -> GitHub Issues

repo queue artifacts
  -> explicit sync_clickup_queue.py run
  -> ClickUp
```

## 4. Risk If We Pretend It Is Automatic

- A parked item can exist locally without a GitHub issue until `sync_github_issues.py --apply` is run.
- A GitHub issue can exist without `execution_meta.github_issue`.
- ClickUp can be stale if no explicit sync was requested.
- `queue-state.json` can be current while external surfaces remain outdated.
- The repo can remain valid under `ops_validator.py --strict` even when GitHub issue readiness fails.

## 5. Recommended Next Harness Shape

Keep the current default:

- no automatic external writes during routine queue edits
- ClickUp only on explicit user request
- GitHub issue creation only on explicit user request

The bounded GitHub harness should continue to keep:

- idempotent create/update by `execution_meta.topic`
- explicit `--post` or `--apply` mutation flag
- dry-run default
- write-back of `execution_meta.github_issue`
- duplicate detection by title and topic marker
- refusal unless `python scripts/ops_validator.py --strict` passes

Do not add bidirectional ClickUp or GitHub sync until repo-side SSOT and conflict rules are deliberately designed.
