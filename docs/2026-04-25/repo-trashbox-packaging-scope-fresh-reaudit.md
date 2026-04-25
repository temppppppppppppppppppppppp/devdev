# Repo Trashbox Packaging Scope Fresh Re-Audit

Date: 2026-04-25
Status: final (packaging and ignore scope authorized; no tracked removal authorized)
Canonical Path: `docs/2026-04-25/repo-trashbox-packaging-scope-fresh-reaudit.md`
Governing Move Plan: `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md`
Governing SSOT: `docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md`

Commit State:
- Baseline Commit: `01ef453ab606ecbb7fb17658543892dff2fa86a5`
- Baseline Dirty Summary: `clean main after PR #18 merged; branch feat/repo-trashbox-packaging-scope opened before this re-audit`

## 1. Re-Audit Question

Can the repo-trashbox cleanup lane proceed from move planning into packaging and ignore scope cleanup without moving or removing tracked files?

Verdict:

- Yes. Packaging and ignore scope cleanup is the next safe tranche.
- This tranche may update `배포_패키징.ps1`, `.gitignore`, and `pyproject.toml` to classify maintenance-only or generated-residue surfaces outside runtime packaging and broad lint scope.
- This tranche does not authorize moving files, deleting files, `git rm`, `git rm --cached`, or creating `C:\Users\PC\Desktop\글도비_쓰레기통`.

## 2. Fresh Config Findings

- `배포_패키징.ps1` already excludes `test_mode`, `rlhf_data`, `datasets`, `crash_dump.log`, `error.log`, `test_results.xml`, and `nul`.
- `배포_패키징.ps1` does not exclude `lite_mode`, `spikes`, root `MagicMock`, or `tmp_stage2_digest_debug`.
- `.gitignore` ignores `projects/MagicMock/`, but not root `MagicMock/`, `tmp_stage2_digest_debug/`, or the generated `test_mode/projects/` and `lite_mode/projects/` trees.
- `pyproject.toml` excludes `test_mode`, `tools`, and `tools2` from Ruff, but not `lite_mode` or `spikes`.
- `docs/implementation/surface-containment-contract-v1.json` classifies `lite_mode` files as manual-only and root `MagicMock` as residue, supporting config-only exclusion.

## 3. Pass 1 - Structure And Scope

The change is config-only. It should not alter runtime code, project data, tracked residue files, or queue document ownership beyond recording tranche progress.

Pass 1 result: pass.

## 4. Pass 2 - Evidence And Consistency

The scope follows `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md` PR A:

- add maintenance-only and residue directories to packaging excludes
- add future-residue ignore rules while leaving existing tracked files untouched
- exclude manual/prototype surfaces from broad Ruff traversal

Pass 2 result: pass.

## 5. Pass 3 - Execution Consequence

The next implementation may edit:

- `.gitignore`
- `pyproject.toml`
- `배포_패키징.ps1`
- queue docs that record tranche completion

Required validation:

- PowerShell parse check for `배포_패키징.ps1`
- TOML parse check for `pyproject.toml`
- focused pytest for the surface-containment config contract
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- `python scripts/check_utf8_hygiene.py` on touched text/config/docs
- `git diff --check`

Pass 3 result: pass.

Confidence: 96/100.
