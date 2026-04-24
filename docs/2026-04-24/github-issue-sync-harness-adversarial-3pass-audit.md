# GitHub Issue Sync Harness Adversarial 3-Pass Audit

Date: 2026-04-24
Status: final
Canonical Path: `docs/2026-04-24/github-issue-sync-harness-adversarial-3pass-audit.md`
Target Harness: `scripts/sync_github_issues.py`
Related Tests: `tests/test_sync_github_issues.py`

## 1. Audit Question

Can the repo-side active execution queue be mirrored into GitHub Issues without turning GitHub into SSOT, creating duplicate issues, or clobbering hand-written issue content?

Decision:

- Yes, with the current explicit-run design.
- The harness must remain dry-run by default.
- `--apply` is required for GitHub or doc mutations.
- Existing linked issue title/body updates must remain gated behind `--update-existing`.

## 2. Pass 1 - Identity And Duplicate Attack

Adversarial question:

What if the harness links a queue item to the wrong GitHub issue or creates duplicates?

Findings:

- The harness uses `execution_meta.github_issue` as the primary link when present.
- If no issue number is present, it searches GitHub by topic.
- Initial audit found the search fallback too permissive: a single GitHub search result could be linked without checking the title/body marker.
- This was tightened during audit:
  - `gh issue list` now requests issue `body`
  - `issue_matches_topic()` requires the topic in title/url, `topic=<slug>` marker in body, or code-form topic in body
  - the previous "single result means match" fallback was removed

Evidence:

- `python scripts/sync_github_issues.py --skip-queue-refresh --skip-ops-validation`
- `pytest tests/test_sync_github_issues.py tests/test_github_issue_readiness.py -q`

Pass 1 result: pass after remediation.

## 3. Pass 2 - Mutation And Clobber Attack

Adversarial question:

What if a sync run overwrites human-authored issue content or mutates repo docs from stale state?

Findings:

- Default mode is dry-run.
- `--apply` is required for create/link/write-back.
- Already linked issues are reported as `linked` and are not edited by default.
- `--update-existing` is required to replace title/body for linked issues.
- Before normal execution, the harness runs:
  - `scripts/sync_temp_queue_state.py`
  - `scripts/ops_validator.py --strict`
- After write-back changes, it refreshes queue state again and reruns `ops_validator.py --strict`.

Residual risk:

- `--update-existing` can still replace a hand-written GitHub issue body. This is intentional but sharp; keep it operator-explicit.
- A network/API failure after issue creation but before complete write-back can leave an issue created without all docs updated. The next run should link or report the mismatch, but there is no rollback transaction across GitHub and the filesystem.

Pass 2 result: pass with operator guardrails.

## 4. Pass 3 - Queue Integration And SSOT Attack

Adversarial question:

What if GitHub Issues drift into being the source of truth, or the queue validator and readiness checker disagree?

Findings:

- Repo-side SSOT remains:
  - canonical execution SSOT docs
  - `docs/temp/*-execution-ssot.md`
  - `docs/temp/execution-roadmap.md`
  - `docs/temp/queue-state.json`
- GitHub Issues are an external visibility mirror.
- `github_issue_readiness.py` now passes for all five active queue docs:
  - `#5`
  - `#3`
  - `#10`
  - `#8`
  - `#9`
- `ops_validator.py --strict` passes with the Stage0 metadata migration and new GitHub issue links.

Evidence:

```text
python scripts/github_issue_readiness.py
SUMMARY: errors=0 infos=9

python scripts/ops_validator.py --strict
SUMMARY: errors=0 warnings=0

pytest tests/test_sync_github_issues.py tests/test_github_issue_readiness.py -q
13 passed
```

Pass 3 result: pass.

## 5. Verdict

Verdict: approved for explicit operator use.

Confidence: 96/100.

Reasons confidence is not higher:

- GitHub and the local filesystem cannot be mutated transactionally.
- `--update-existing` is intentionally powerful and should stay uncommon.
- The harness depends on GitHub CLI behavior and current repository permissions.

## 6. Operating Guardrails

- Use dry-run first:

```text
python scripts/sync_github_issues.py
```

- Apply only after reviewing planned actions:

```text
python scripts/sync_github_issues.py --apply
```

- Use `--update-existing` only when the operator intentionally wants GitHub issue bodies regenerated from repo queue state.
- Do not treat GitHub Issues as SSOT.
- Do not add bidirectional GitHub-to-roadmap sync without a separate conflict-resolution design.
