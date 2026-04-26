# Root Cost Fix Script Archive Execution SSOT

Date: 2026-04-26
Status: completed
Canonical Path: `docs/2026-04-26/root-cost-fix-script-archive-execution-ssot.md`
Temp Mirror Path: `docs/temp/root-cost-fix-script-archive-execution-ssot.md`
GitHub Issue: `https://github.com/temppppppppppppppppppppppp/devdev/issues/45`

Commit State:
- Baseline Branch: `codex/root-cost-fix-script-archive`
- Baseline Commit: `e1e70272553aec97d3e4b9a260ad1dbc491967be`
- Baseline Dirty Summary: active live-run artifacts are present but excluded: modified `0_temp.txt`, untracked live-run watchlist/runtime-analysis docs, and untracked `projects/0_골든카나리아/`

Source Documents:
- `docs/2026-04-26/root-hygiene-cleanup-plan.md`
- `docs/2026-04-26/root-rerun-input-archive-execution-ssot.md`
- `docs/2026-04-25/repo-trashbox-reference-check.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`

## 1. Purpose

Archive two tracked root one-off cost-fix scripts without deleting their historical content.

This SSOT authorizes only this exact move:

```text
fix_costs.py
  -> docs/archive/one-off-scripts/2026-04-26/fix_costs.py

fix_costs2.py
  -> docs/archive/one-off-scripts/2026-04-26/fix_costs2.py
```

## 2. Fresh Evidence

Tracked-state check:

```text
git ls-files -- fix_costs.py fix_costs2.py
```

Result:

```text
fix_costs.py
fix_costs2.py
```

Reference scan:

```text
rg --fixed-strings -l -- "fix_costs.py"
rg --fixed-strings -l -- "fix_costs2.py"
rg --fixed-strings -n -- "사업승인요청서-글도비.md"
```

Observed result:

```text
fix_costs.py
fix_costs2.py
```

Both scripts point at:

```text
C:\Users\wjjo\Desktop\글도비\docs\2026-03-11\사업승인요청서-글도비.md
```

Interpretation:

- These are tracked root residue files, not ignored local scratch.
- They are one-off document mutation scripts with a stale absolute path.
- No runtime, test, packaging, or supported operator dependency was observed.
- Archiving is safer than deletion because the scripts preserve historical cost-edit evidence.

## 3. Included Scope

- Create `docs/archive/one-off-scripts/2026-04-26/` if missing.
- Move `fix_costs.py` and `fix_costs2.py` into that archive directory.
- Preserve both files as tracked archive evidence. Pre-commit may normalize Python formatting, but no runtime use is authorized from the archive.
- Add this execution SSOT.

## 4. Excluded Scope

Do not touch:

- `0_temp.txt`
- `temp_inspect.txt`
- `docs/2026-04-26/frontier-lag-5arc-live-run-watchlist.md`
- `docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `projects/0_골든카나리아/`
- `RESET.py`
- `smoke_sc.py`
- `로직_리서치/`
- `.gitignore`
- runtime code, tests, packaging, DB files, or live-run artifacts

## 5. Side-Effect Map

File writes and tracked moves:

- Yes. Exactly two tracked file moves plus this execution document.

DB writes:

- Not applicable.

JSONL, log, audit sinks:

- Not applicable.

Console or UI output:

- Not applicable.

Rollback and recovery:

- A normal Git revert restores both scripts to the repository root.

Cache or global state:

- Not applicable.

Bootstrap, config, or environment mutation:

- Not applicable.

## 6. Implementation Plan

1. Create `docs/archive/one-off-scripts/2026-04-26/`.
2. Move `fix_costs.py` into the archive directory.
3. Move `fix_costs2.py` into the archive directory.
4. Confirm the root no longer tracks either script.
5. Confirm the archive path tracks both scripts.
6. Validate UTF-8 hygiene and staged diff whitespace.
7. Keep the PR scoped to the two renames and this SSOT.

## 7. Acceptance Criteria

- `git ls-files -- fix_costs.py fix_costs2.py` returns no root files.
- `git ls-files -- docs/archive/one-off-scripts/2026-04-26` returns both archived scripts.
- Active live-run artifacts remain untouched.
- `RESET.py`, `smoke_sc.py`, `temp_inspect.txt`, and `로직_리서치/` remain untouched.
- UTF-8 hygiene passes for touched files.
- Staged diff whitespace check passes.

## 8. Adversarial Audit Pass 1 - Stale Absolute Path Attack

Attack question:

Could these scripts still be useful operator tools?

Finding:

- Both scripts hard-code another Windows user path under `C:\Users\wjjo\Desktop\글도비\...`.
- Running them as-is on the current machine would not target the current workspace path.
- Their purpose is a dated one-off business-approval cost rewrite, not a reusable root operator tool.

Pass 1 result: pass.

## 9. Adversarial Audit Pass 2 - Reference Breakage Attack

Attack question:

Could moving these files break runtime, tests, packaging, or docs?

Finding:

- Fresh reference scan found no external dependency on the file names.
- The only direct document target string appears inside the two scripts themselves.
- No runtime, test, packaging, or supported operator reference was observed.

Pass 2 result: pass.

## 10. Adversarial Audit Pass 3 - Over-Cleanup Attack

Attack question:

Could this accidentally expand into broad root cleanup?

Finding:

- Scope is exactly two cost-fix scripts.
- Other dirty-looking root files are explicitly excluded.
- `.gitignore` and runtime code are out of scope.
- Live-run evidence is frozen.

Pass 3 result: pass.

## 11. Confidence Gate

Confidence: 97/100.

Reason:

- The scripts are tracked, stale, self-contained one-off mutation helpers.
- Archiving preserves evidence while cleaning the root.
- The move is small, reviewable, and reversible.

## 12. Implementation Closure

Implemented moves:

```text
fix_costs.py
  -> docs/archive/one-off-scripts/2026-04-26/fix_costs.py

fix_costs2.py
  -> docs/archive/one-off-scripts/2026-04-26/fix_costs2.py
```

Post-implementation evidence:

```text
git ls-files -- fix_costs.py fix_costs2.py
```

Result:

```text
<no output>
```

```text
git ls-files -- docs/archive/one-off-scripts/2026-04-26
```

Result:

```text
docs/archive/one-off-scripts/2026-04-26/fix_costs.py
docs/archive/one-off-scripts/2026-04-26/fix_costs2.py
```

Validation:

```text
python scripts/check_utf8_hygiene.py docs/2026-04-26/root-cost-fix-script-archive-execution-ssot.md docs/temp/root-cost-fix-script-archive-execution-ssot.md docs/archive/one-off-scripts/2026-04-26/fix_costs.py docs/archive/one-off-scripts/2026-04-26/fix_costs2.py
git diff --check --cached
git diff --check -- docs/2026-04-26/root-cost-fix-script-archive-execution-ssot.md docs/archive/one-off-scripts/2026-04-26/fix_costs.py docs/archive/one-off-scripts/2026-04-26/fix_costs2.py
```

Result: pass.

Pre-commit note:

- During the first commit attempt, `ruff` and `ruff-format` normalized the archived Python files.
- The archive therefore preserves the scripts as tracked historical evidence with formatting normalization, not as byte-for-byte forensic copies.
- This is acceptable for this lane because the files are stale one-off mutation helpers and no runtime use is authorized from the archive.

Temp mirror closure:

- `docs/temp/root-cost-fix-script-archive-execution-ssot.md` was used as the active execution mirror during implementation.
- Because this queue item is completed in the same wave, the temp mirror should be deleted before PR staging.
