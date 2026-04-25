# Repo Trashbox Cleanup Fresh Re-Audit

Date: 2026-04-25
Status: final (reference-check tranche authorized only; no move/delete/git-rm authorized)
Canonical Path: `docs/2026-04-25/repo-trashbox-cleanup-fresh-reaudit.md`
Governing SSOT: `docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md`
Temp Mirror: `docs/temp/repo-trashbox-cleanup-execution-ssot.md`

Commit State:
- Baseline Commit: `8ec8435d11e68cdc8ea8f2a431a13a20bfdffcfe`
- Baseline Dirty Summary: `clean main after PR #16 merged canary root isolation queue closure; branch feat/repo-trashbox-reference-check opened before this re-audit`

## 1. Re-Audit Question

Can the parked `repo-trashbox-cleanup` lane be opened safely on the current workspace without repeating stale assumptions from the 2026-04-24 parking docs?

Verdict:

- Yes, but only for Tranche 1: candidate reference and runtime dependency check.
- No physical move, delete, `git rm`, `git rm --cached`, packaging edit, or ignore-policy edit is authorized by this re-audit.
- The previous holding path `C:\Users\wjjo\Desktop\글도비_쓰레기통` is stale for this PC. The current proposed local holding path is `C:\Users\PC\Desktop\글도비_쓰레기통`, but it remains a proposal only.

## 2. Fresh Drift Findings

- The active temp queue now has one item: `repo-trashbox-cleanup`.
- `canary-root-isolation` is closed and merged, so future canary output is isolated under `canary/`; old `projects/_canary/` remains excluded from this lane.
- `test_mode/` and `lite_mode/` each currently have `1554` tracked files, higher than the old survey count for `test_mode/`; immediate movement would create a large and hard-to-review Git diff.
- Root residue candidates are mostly tracked, including `0_temp.txt`, `temp.txt`, `temp_시리즈.txt`, `temp_triage_test.json`, `test_results.xml`, `tmp_project_00.db`, `crash_dump.log`, and `error.log`.
- The root `nul` file is present and untracked. It also causes whole-root `rg .` scans to emit an OS error on Windows, so future scans should use explicit scopes or ignore `nul`.

## 3. Pass 1 - Structure And Scope

The 2026-04-24 execution SSOT remains structurally valid as a parked execution doc. Its first tranche is correctly scoped to reference checking before any destructive operation.

Pass 1 result: pass with two required updates:

- mark the queue item as front-active for reference-check only
- replace the stale PC holding path with the current PC proposal while keeping movement unauthorized

## 4. Pass 2 - Evidence And Consistency

Fresh read-only evidence confirms that the old parking audit was conservative in the right direction:

- `modules/core/runtime_paths.py` still labels `lite_mode/` and `test_mode/` as maintenance-only compatibility surfaces, not supported runtime.
- `pyproject.toml` excludes `test_mode` from Ruff, but not `lite_mode`.
- `배포_패키징.ps1` excludes `test_mode`, `rlhf_data`, `datasets`, `crash_dump.log`, `error.log`, and `test_results.xml`, but not `lite_mode`, `spikes`, root `MagicMock`, or `tmp_stage2_digest_debug`.
- `docs/implementation/surface-containment-contract-v1.json` still names several `lite_mode` files as manual-only and names root `MagicMock` as residue.

Pass 2 result: pass, but the fresh reference-check must separate "candidate path reference" from generic string references such as Python's `MagicMock` test helper usage.

## 5. Pass 3 - Execution Safety

The safe operating consequence is not cleanup yet. The safe next step is a documentation-backed reference check that produces a Git policy table for the next tranche.

Guardrails retained:

- do not move `tests/`
- do not move `docs/temp/`
- do not move old `projects/_canary/`
- do not move tracked candidate directories without a Git policy table
- do not treat `글도비_쓰레기통` as a second unmanaged source repository

Pass 3 result: pass.

## 6. Confidence

Confidence: 96/100.

Reasoning:

- Current queue and branch state were rechecked.
- Candidate counts were refreshed.
- Known stale path drift was identified and bounded.
- No claim in this document authorizes irreversible cleanup.

Residual uncertainty:

- The next tranche still needs a human-facing policy decision for large tracked candidate groups before any movement or Git removal occurs.
