# Repo Trashbox Reference Check

Date: 2026-04-25
Status: final (Tranche 1 complete; no quarantine move authorized)
Canonical Path: `docs/2026-04-25/repo-trashbox-reference-check.md`
Governing Re-Audit: `docs/2026-04-25/repo-trashbox-cleanup-fresh-reaudit.md`
Governing SSOT: `docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md`

Commit State:
- Baseline Commit: `8ec8435d11e68cdc8ea8f2a431a13a20bfdffcfe`
- Baseline Dirty Summary: `clean branch feat/repo-trashbox-reference-check before documentation updates; read-only candidate inventory and reference scans performed`

## 1. Scope

This tranche checks whether trashbox candidates are referenced by runtime, packaging, lint, tests, docs, or queue artifacts before any physical cleanup.

This document does not authorize:

- moving files to `C:\Users\PC\Desktop\글도비_쓰레기통`
- deleting files
- `git rm` or `git rm --cached`
- changing `.gitignore`
- changing packaging rules

## 2. Evidence Commands

Read-only evidence used:

- candidate file counts and tracked counts with `Get-ChildItem` plus `git ls-files`
- root file inventory with `Get-ChildItem` plus `git ls-files`
- focused references with `rg`
- targeted reads of `modules/core/runtime_paths.py`, `pyproject.toml`, `배포_패키징.ps1`, and `docs/implementation/surface-containment-contract-v1.json`

Whole-root `rg .` should not be used blindly on this workspace because an untracked root `nul` file triggers a Windows OS error.

## 3. Candidate Inventory

| Candidate | Exists | Files | Bytes | Tracked files | Reference-check result |
| --- | --- | ---: | ---: | ---: | --- |
| `test_mode/` | yes | 1574 | 45951451 | 1554 | Maintenance-only per `runtime_paths.py`; excluded by `pyproject.toml` Ruff config and `배포_패키징.ps1`; referenced by tests/docs. Needs Git policy before movement. |
| `lite_mode/` | yes | 1554 | 42426849 | 1554 | Maintenance-only per `runtime_paths.py`; manual-only entries in surface-containment contract; not excluded by packaging. Needs packaging decision and Git policy before movement. |
| `spikes/` | yes | 7 | 26468 | 7 | Mostly docs/material references; no supported runtime reference observed. Needs docs-preservation decision before movement. |
| `MagicMock/` | yes | 2 | 792 | 2 | Root path is residue per surface-containment contract. Generic `MagicMock` string matches many tests and must not be treated as directory dependency. |
| `tmp_stage2_digest_debug/` | yes | 6 | 386870 | 6 | References observed only in trashbox docs. Good quarantine candidate after Git policy decision. |
| `rlhf_data/test_project/` | yes | 6 | 2680 | 6 | References observed in trashbox docs; parent `rlhf_data` is excluded by packaging. Good quarantine candidate after Git policy decision. |
| `datasets/test_project/` | yes | 3 | 42042 | 3 | References observed in trashbox docs and old survey; parent `datasets` is excluded by packaging. Good quarantine candidate after Git policy decision. |

## 4. Root Residue Inventory

Tracked root residue candidates observed:

| Path | Bytes | Tracked | Note |
| --- | ---: | --- | --- |
| `.tmp_b60_full.txt` | 29311 | yes | root temporary text artifact |
| `0_temp.txt` | 22445 | yes | old temp/evidence artifact; many historical docs mention similarly named temp docs |
| `bash.exe.stackdump` | 304 | yes | crash residue |
| `crash_dump.log` | 2267 | yes | packaging excludes by filename |
| `error.log` | 746 | yes | packaging excludes by filename; also a boot fallback surface is `logs/error.log`, not this root file |
| `ops_hardening_rerun_input.txt` | 28 | yes | rerun input residue candidate |
| `p1_rerun_1arc_input.txt` | 42 | yes | rerun input residue candidate |
| `temp.txt` | 18656 | yes | old temp artifact; many historical docs mention similarly named temp docs |
| `temp_triage_test.json` | 4751 | yes | triage temp artifact |
| `temp_시리즈.txt` | 36031 | yes | temp artifact |
| `temp-electron-paths.js` | 252 | yes | packaging/debug temp helper |
| `temp-proc-poll.ps1` | 736 | yes | packaging/debug temp helper |
| `temp-proc-poll-oswarn.ps1` | 825 | yes | packaging/debug temp helper |
| `temp-proc-trace.ps1` | 1031 | yes | packaging/debug temp helper |
| `temp-run-packaged.ps1` | 353 | yes | packaging/debug temp helper |
| `temp-run-packaged-ascii.ps1` | 309 | yes | packaging/debug temp helper |
| `test_results.xml` | 191256 | yes | packaging excludes by filename |
| `tmp_project_00.db` | 876544 | yes | local DB residue candidate |
| `tttt.txt` | 22623 | yes | root text residue candidate |

Untracked local root residue observed:

| Path | Bytes | Tracked | Note |
| --- | ---: | --- | --- |
| `_regen_inventory_from_order.py` | 25698 | no | local generation helper residue |
| `_rewrite_economic_timeline_with_data.py` | 4558 | no | local generation helper residue |
| `_targeted_inventory_fixes.py` | 14139 | no | local generation helper residue |
| `nul` | 0 | no | Windows special-name residue; breaks blind `rg .` scans |
| `temp_inspect.txt` | 21069 | no | local temp residue |
| `test_results_new.xml` | 232 | no | local test-result residue |

## 5. Packaging And Config Findings

- `배포_패키징.ps1` excludes `test_mode`, `rlhf_data`, `datasets`, `crash_dump.log`, `error.log`, `test_results.xml`, `nul`, and several broad tool/log surfaces.
- `배포_패키징.ps1` does not currently exclude `lite_mode`, `spikes`, root `MagicMock`, or `tmp_stage2_digest_debug`.
- `pyproject.toml` excludes `test_mode` from Ruff, but not `lite_mode`.
- `.gitignore` contains `projects/MagicMock/`, but not root `MagicMock/`.
- `modules/core/runtime_paths.py` keeps `lite_mode/` and `test_mode/` classified as maintenance-only compatibility entries.

## 6. Policy Table For Next Tranche

| Group | Recommended next policy before any move |
| --- | --- |
| `test_mode/` | Decide whether to remove from active tree with a large tracked deletion PR, preserve a tracked archive, or split generated project artifacts from code first. |
| `lite_mode/` | Resolve packaging visibility first, then decide whether manual-only bridge files should remain documented while generated project artifacts are removed. |
| `spikes/` | Preserve any useful `result.md` or conclusion notes in docs before moving prototype/build residue. |
| `MagicMock/` | Treat root path separately from test helper string usage; likely safe after Git policy table because it is only 2 tracked files. |
| `tmp_stage2_digest_debug/` | Likely safe after manifest-driven quarantine; no runtime reference observed. |
| `rlhf_data/test_project/` and `datasets/test_project/` | Likely safe after manifest-driven quarantine; parent packaging excludes already exist. |
| root tracked residue | Needs per-file review because many are tracked historical artifacts, not untracked local noise. |
| root untracked residue | Can be handled as local cleanup after confirming no active process needs it. |

## 7. Pass 1 - Structure And Scope

The reference check is limited to read-only inventory and dependency observation. It does not mutate Git, packaging, ignore rules, or candidate files.

Pass 1 result: pass.

## 8. Pass 2 - Evidence And Consistency

Counts and references are bounded to commands run on the current workspace. The known false positive around generic `MagicMock` references is separated from root `MagicMock/` path dependency.

Pass 2 result: pass.

## 9. Pass 3 - Execution Consequence

The next safe tranche is a quarantine move plan and Git policy decision, not an immediate cleanup move.

Pass 3 result: pass.

Confidence: 96/100.
