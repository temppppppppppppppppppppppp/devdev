# Repo Trashbox Quarantine Move Plan

Date: 2026-04-25
Status: final (Tranche 2 plan complete; no file move, delete, or git removal performed)
Canonical Path: `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md`
Governing Reference Check: `docs/2026-04-25/repo-trashbox-reference-check.md`
Governing SSOT: `docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md`

Commit State:
- Baseline Commit: `aed6e2ba2ba3b69c9278ff9484e31ca89bd6d1ba`
- Baseline Dirty Summary: `clean main after PR #17 merged; branch feat/repo-trashbox-move-plan opened before this plan`

## 1. Plan Question

What is the safest move policy for the trashbox cleanup lane after the reference check found many tracked candidates?

Verdict:

- Treat tracked files as repo-history decisions, not local trash moves.
- Do not move tracked candidates outside the repository with plain filesystem operations.
- Split cleanup into small reviewable PRs.
- Use `C:\Users\PC\Desktop\글도비_쓰레기통` only for local quarantine copies or untracked local residue after a manifest exists.

This document does not authorize moving, deleting, `git rm`, `git rm --cached`, `.gitignore` edits, or packaging edits.

## 2. Git Policy

| Policy | Applies to | Meaning |
| --- | --- | --- |
| `keep-labeled` | manual source or useful notes | Keep in repo, label as manual-only or historical backing. |
| `tracked-remove` | tracked generated output or residue | Remove from active tree in a dedicated PR with clear manifest and before/after validation. |
| `docs-preserve-then-remove` | spikes or experiments with useful conclusions | Move conclusions into docs first, then remove prototype/build residue. |
| `config-exclude` | packaging/lint/security scan scope | Update config so maintenance-only residue is not packaged or scanned as runtime. |
| `local-quarantine-copy` | uncertain or untracked local residue | Copy to `글도비_쓰레기통` first; delete only after explicit approval. |
| `separate-lane` | old `projects/_canary/` | Keep out of this lane; canary historical cleanup needs its own SSOT. |

## 3. Candidate Policy Decisions

| Candidate | Current shape | Policy | Next action |
| --- | --- | --- | --- |
| `test_mode/projects/` | `1522` tracked generated project files under `test_mode/` | `tracked-remove` candidate | Separate PR after manifest; do not remove alongside manual source. |
| `test_mode/` manual source files | about `32` tracked non-project/manual files | `keep-labeled` pending deeper manual-mode decision | Keep for now; if removed later, do it after source-level review. |
| `lite_mode/projects/` | `1522` tracked generated project files under `lite_mode/` | `tracked-remove` candidate | Separate PR after manifest; high ROI cleanup. |
| `lite_mode/` manual source files | about `32` tracked non-project/manual files, including bridge/manual helper files | `keep-labeled` plus `config-exclude` | Keep source for now; packaging should exclude `lite_mode` until a final manual-mode decision. |
| `spikes/` | `7` tracked files: four `result.md` notes plus three prototype/spec files | `docs-preserve-then-remove` | Preserve conclusions or keep `result.md`; remove prototype code only after docs decision. |
| `MagicMock/` | `2` tracked soft-failure log files | `tracked-remove` candidate | Low-risk removal PR after manifest; unrelated to test helper string `MagicMock`. |
| `tmp_stage2_digest_debug/` | `6` tracked debug files including one DB | `tracked-remove` candidate | Low-risk removal PR after manifest. |
| `rlhf_data/test_project/` | `6` tracked test-project feedback files | `tracked-remove` candidate | Low-risk removal PR after manifest. |
| `datasets/test_project/` | `3` tracked test-project approved-output files | `tracked-remove` candidate | Low-risk removal PR after manifest. |
| root tracked residue | many tracked temp/log/result files | per-file `tracked-remove` or `keep-labeled` | Do not batch blindly; start with files already excluded by packaging. |
| root untracked residue | local helper/temp files including `nul` | `local-quarantine-copy` | Handle locally only after checking no active process depends on them. |
| `projects/_canary/` | old tracked canary outputs | `separate-lane` | Not part of this cleanup. |

## 4. Proposed PR Sequence

### PR A - Packaging And Ignore Scope

Purpose:

- prevent maintenance-only surfaces from accidental packaging or scan treatment as runtime

Candidate changes:

- add `lite_mode`, `spikes`, `MagicMock`, and `tmp_stage2_digest_debug` to `배포_패키징.ps1` exclusions
- add root `MagicMock/` and `tmp_stage2_digest_debug/` to `.gitignore` for future generated residue after tracked cleanup
- consider adding `lite_mode` to Ruff excludes only if the team accepts manual-only source as non-lint scope

### PR B - Low-Risk Tracked Residue Removal

Purpose:

- remove small tracked generated/debug/test-project residue before touching the giant manual-mode trees

Candidate remove set:

- `MagicMock/`
- `tmp_stage2_digest_debug/`
- `rlhf_data/test_project/`
- `datasets/test_project/`
- root files already excluded by packaging: `crash_dump.log`, `error.log`, `test_results.xml`, `tmp_project_00.db`

Required validation:

- `git status --short`
- `python scripts/ops_validator.py --strict`
- targeted reference scan for each removed path

### PR C - Manual Mode Generated Project Data

Purpose:

- remove the bulk of repo clutter while preserving manual-mode source for a later decision

Candidate remove set:

- `test_mode/projects/`
- `lite_mode/projects/`

Required validation:

- focused reference scan for `test_mode/projects` and `lite_mode/projects`
- packaging and Ruff config check
- GitHub CI

### PR D - Spikes Preservation

Purpose:

- retain useful spike conclusions without keeping prototype/build residue in the normal source view

Candidate policy:

- preserve or copy `spikes/**/result.md` conclusions into a docs note
- remove `spikes/pyinstaller/spike_pyinstaller.py`
- remove `spikes/pyinstaller/spike_pyinstaller.spec`
- remove `spikes/subprocess/spike_subprocess.py`

### PR E - Manual Source Final Decision

Purpose:

- decide whether `test_mode/` and `lite_mode/` manual source should stay as maintenance-only reference, move under a named archive, or be removed

Do not run this PR until the generated project data is already out of the way.

## 5. Move Manifest Template

Use this manifest shape before any cleanup PR that removes tracked files:

```yaml
trashbox_manifest:
  schema_version: trashbox-manifest-v1
  source_commit: <commit>
  action: tracked-remove | docs-preserve-then-remove | local-quarantine-copy
  holding_area: C:\Users\PC\Desktop\글도비_쓰레기통
  candidates:
    - path: <repo-relative path>
      tracked_files: <count>
      reference_scan: <summary or doc link>
      preservation_policy: <none | docs-note | local-copy>
      rollback: git revert <commit> or restore from holding_area
  validation:
    - python scripts/ops_validator.py --strict
    - git diff --check
```

## 6. Pass 1 - Structure And Scope

This plan separates local quarantine, Git-tracked removal, packaging scope, and manual-source decisions. It does not conflate "outside repo trashbox" with a committed cleanup PR.

Pass 1 result: pass.

## 7. Pass 2 - Evidence And Consistency

The split follows the 2026-04-25 reference check:

- `test_mode/` and `lite_mode/` each have `1554` tracked files.
- `test_mode/projects/` and `lite_mode/projects/` account for `1522` tracked files each.
- small candidates have explicit tracked file lists and no supported-runtime references observed.
- packaging currently excludes `test_mode`, `rlhf_data`, `datasets`, and several root files, but not `lite_mode`, `spikes`, root `MagicMock`, or `tmp_stage2_digest_debug`.

Pass 2 result: pass.

## 8. Pass 3 - Execution Consequence

The next safe implementation tranche is PR A: packaging and ignore scope. PR B can follow after PR A if the operator wants actual tracked cleanup.

Pass 3 result: pass.

Confidence: 96/100.

Residual risk:

- removing tracked files is intentionally deferred because it changes repository history shape and should be reviewed in small PRs.
