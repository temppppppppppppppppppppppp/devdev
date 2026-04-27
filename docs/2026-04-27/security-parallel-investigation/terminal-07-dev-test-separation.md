# T07 Dev/Test Separation Inventory

- Date: 2026-04-27
- Workspace: `C:\Users\wjjo\Desktop\글도비`
- Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline dirty summary at dispatch start: only `?? docs/2026-04-27/security-parallel-investigation/` (the dispatch + T07 report directory itself).
- Primary GitHub issue: #69 `[SEC] Separate test/dev scripts from production source tree`
- Dispatch document: `docs/2026-04-27/security-parallel-investigation/security-issues-parallel-investigation-dispatch.md`
- Document type: read-only inventory + classification, not an execution SSOT and not a code-move order.

## Scope

Inventory dev / test / temp / experimental files that live inside production-adjacent paths and classify each item against one of:

- `keep production` — legitimate production surface, leave in place.
- `move to tests` — test/probe script that should live under `tests/` instead of a runtime/release-adjacent path.
- `move to scripts/dev` — operator/dev tool that should live under a dev-only namespace (e.g. `scripts/dev/` or a future `dev_tools/`).
- `move to docs/archive` — historical/one-off artifact already inert; relocate to `docs/archive/` to drop it from prod-adjacent listings.
- `ignore + build-exclude` — local-only residue; should stay gitignored AND be hard-excluded from every release path.
- `needs owner decision` — ambiguous ownership / mixed runtime + dev semantics; LLM/owner judgment required before moving.

Inspected paths (per dispatch §5 and prompt T07):

- root files
- `scripts/`
- `tests/`
- `lite_mode/`
- `test_mode/`
- `spikes/`
- `tools/`
- `tools2/`
- `docs/archive/`
- `docs/temp/`
- `.github/workflows/test.yml`

Out of scope (deferred to other terminals):

- secret payload identification → T01.
- runtime config loading topology → T02.
- Vertex / GCP auth flow → T03.
- desktop config bridge surfaces → T04.
- Windows write-location policy → T05.
- final release inclusion/exclusion design and PyInstaller spec edits → T06.
- EXE access-control chokepoints → T08.
- CI / pre-commit guardrails recommendation → T09.
- consolidated security-response doc map → T10.

## Commands / Evidence

All commands were read-only. No file moves, no edits, no git mutations.

```bash
# Baseline state.
git rev-parse HEAD
# -> a3d826978d530ab61d3765e5e095890fa6533ea7
git status --short
# -> ?? docs/2026-04-27/security-parallel-investigation/   (only the report directory itself)

# Tracked-file population per dev-test surface.
git ls-files | grep -c '^tests/'         # 517
git ls-files | grep -c '^scripts/'       # 121
git ls-files | grep -c '^lite_mode/'     # 32
git ls-files | grep -c '^test_mode/'     # 32
git ls-files | grep -c '^tools/'         # 15
git ls-files | grep -c '^tools2/'        # 28
git ls-files | grep -c '^build/'         # 4

# Local-only residue and gitignore confirmation.
ls -1A scripts | grep -E '^_tmp'
# -> _tmp_b41_43.py, _tmp_b44_45.py, _tmp_b46_48.py, _tmp_b49_50.py,
#    _tmp_b51.py, _tmp_densify_batch2.py, _tmp_scrub_meta_numbers.py,
#    _tmp_scrub_pass2.py, _tmp_scrub_pass3.py, _tmp_scrub_pass4.py
git check-ignore -v scripts/_tmp_b41_43.py scripts/_tmp_densify_batch2.py
# -> .gitignore:33 _*.py  scripts/_tmp_b41_43.py
# -> .gitignore:33 _*.py  scripts/_tmp_densify_batch2.py
ls -1A tests | grep -E '^_tmp'           # (none)

# Root residue tracked-state probe.
for f in 0_temp.txt tttt.txt smoke_sc.py md2pdf.py RESET.py main.js generate_empire_reborn_tr70.py; do
  git ls-files --error-unmatch -- "$f" && echo tracked || echo untracked
done
# -> tracked:   0_temp.txt, tttt.txt, smoke_sc.py, md2pdf.py, RESET.py, main.js
# -> untracked: generate_empire_reborn_tr70.py    (matches .gitignore:114 generate_*.py)

# Other root residue.
git status --ignored --short | grep -E 'temp_|test_material|tmp_stage2|tmp_utf8|tmp_project|pyarmor.bug'
# -> !! temp_상태/, !! test_material/, !! tmp_stage2_digest_debug/, !! tmp_project_00_style_survey.db,
#    !! tmp_utf8_check.py, !! tmp_utf8_check.txt, !! pyarmor.bug.log
git ls-files | grep -E '^\.tmp_stage0_msg/'
# -> .tmp_stage0_msg/stage0_output/style_guide.json   (TRACKED, lives under a tmp-named root dir)

# spikes/ tracked footprint.
git ls-files spikes/ | wc -l             # 0
ls -1A spikes/pyinstaller/build          # spike_pyinstaller            (gitignored via .gitignore:58 spikes/)
ls -1A spikes/pyinstaller/dist           # spike_pyinstaller.exe        (gitignored via .gitignore:58 spikes/)

# Canary / smoke / e2e tracked surface in scripts and tests.
git ls-files scripts | grep -E '(canary|smoke|^scripts/diff_canary|prepare_smoke|smoke_fixture)'
# -> scripts/canary_path_utils.py
# -> scripts/canary_semantic_exit.py
# -> scripts/canary_stage2_headless.py
# -> scripts/diff_canary_summaries.py
# -> scripts/e2e_menu_smoke.ps1
# -> scripts/prepare_smoke_fixture.py
# -> scripts/run_stage2_canary.py
# -> scripts/run_stage2_smoke.py
# -> scripts/run_stage34_canary.py
# -> scripts/run_stage34_ep_demo_canary.py
# -> scripts/run_stage3_canary.py
# -> scripts/run_stage3_smoke.py
# -> scripts/run_stage4_canary.py
# -> scripts/run_stage4_smoke.py
# -> scripts/smoke_fixture_contract.py

# tools2 contains test_*.py files OUTSIDE tests/ (not collected by pytest discovery in tests/).
git ls-files tools2 | grep -E 'test_|validation_test'
# -> tools2/test_continuity_validator.py
# -> tools2/test_phase3_systems.py
# -> tools2/test_priority1_security_fixes.py
# -> tools2/test_v0128_validation.py
# -> tools2/test_v43_updates.py
# -> tools2/validation_test_harness.py

# lite_mode dev/probe surface (tracked).
git ls-files lite_mode | grep -E '(test_|inspect_|clean_residue|manual_ui|free_writer|run_arc28|run_fix_arcs|run_patch|run_revalidate|run_stage|split_treatment)'
# -> lite_mode/clean_residue.py
# -> lite_mode/free_writer.py
# -> lite_mode/inspect_delete.py
# -> lite_mode/inspect_gemini_ui.py
# -> lite_mode/inspect_sidebar.py
# -> lite_mode/manual_ui_discovery_probe.py
# -> lite_mode/run_arc28.py
# -> lite_mode/run_fix_arcs.py
# -> lite_mode/run_patch.py
# -> lite_mode/run_revalidate.py
# -> lite_mode/run_stage.py
# -> lite_mode/split_treatment.py
# -> lite_mode/test_background.py
# -> lite_mode/test_bg_check.py
# -> lite_mode/test_bg_covered.py
# -> lite_mode/test_delete_diag.py
# -> lite_mode/test_delete_full.py
# -> lite_mode/test_hide.py
# -> lite_mode/test_minimized.py
# -> lite_mode/test_minimized2.py
# -> lite_mode/test_minimized3.py
# -> lite_mode/test_model_select.py
# -> lite_mode/test_new_chat.py
# -> lite_mode/test_offscreen.py

# docs/temp surface (active execution queue per AGENTS.md).
ls -1A docs/temp
# -> includes: jangyeongshil_3pass_audit.py, jangyeongshil_bi_audit.py
#    plus state JSON files and run-output txt dumps (raw evidence, expected here).

# docs/archive subtree (already-archived dev artifacts).
ls -1A docs/archive
# -> one-off-scripts/, root-notes/, root-residue/, run-inputs/
ls -1A docs/archive/one-off-scripts/2026-04-26
# -> fix_costs.py, fix_costs2.py
ls -1A docs/archive/root-residue/2026-04-26
# -> .tmp_b60_full.txt, bash.exe.stackdump

# Release pathway evidence (touched only as anchor for release-inclusion risk;
# final spec edits belong to T06).
sed -n '70,90p' build/build_release.ps1
# -> Sync-EngineBundle stages: main_a.py, modules, config, datasets, libraries, lite_mode
sed -n '1,40p' 배포_패키징.ps1
# -> $exclude includes: .git, .claude, .pytest_cache, .ruff_cache, .hypothesis, .github,
#    .venv, venv, __pycache__, projects, logs, 백업, lite_mode, spikes, MagicMock,
#    tmp_stage2_digest_debug, test_mode, rlhf_data, datasets, main_tools, tools, tools2, scripts
# -> $excludeFiles: .env, CLAUDE.md, crash_dump.log, error.log, test_results.xml, nu_, nul, 배포_패키징.ps1

# CI surface — tests/ only, plus scripts/run_pytest_lowmem.py runner.
sed -n '1,180p' .github/workflows/test.yml
# -> Confirms only tests/test_*.py paths and scripts/run_pytest_lowmem.py are invoked.
```

## Findings

### F1. `lite_mode/` dev probes are bundled into the release engine [P1]

`build/build_release.ps1` (`Sync-EngineBundle`) explicitly stages `lite_mode` into `dist/engine` alongside `main_a.py`, `modules`, `config`, `datasets`, and `libraries`. `lite_mode/` itself contains 23+ tracked dev / probe scripts (`test_background.py`, `test_bg_check.py`, `test_delete_*.py`, `test_hide.py`, `test_minimized*.py`, `test_model_select.py`, `test_new_chat.py`, `test_offscreen.py`, `inspect_delete.py`, `inspect_gemini_ui.py`, `inspect_sidebar.py`, `manual_ui_discovery_probe.py`, `clean_residue.py`, `free_writer.py`, `run_arc28.py`, `run_fix_arcs.py`, `run_patch.py`, `run_revalidate.py`, `run_stage.py`, `split_treatment.py`).

Risk class: release-inclusion / dev-surface leakage. These probes were authored against external UI (Gemini web UI discovery, window background/minimized state) and are not part of the runtime contract `source_bundle_primary` advertises. They ride into the packaged engine because the staging unit is `lite_mode/` (whole-directory copy), not a curated subset.

Why P1, not P0: no secret payload was confirmed in lite_mode probes within the time-bounded T07 read; the issue is dev-surface bleed into the production bundle, not credential exposure. T01 / T03 may still upgrade severity if probe code is later shown to call shared accounts.

### F2. `lite_mode/` and `test_mode/` are near-duplicate dev probe trees [P2]

`git ls-files` reports 32 tracked files in each, with overlapping filenames (`bridge/gemini_driver.py`, `bridge/runner.py`, `bridge/state_ledger.py`, `bridge/ui_discovery.py`, `clean_residue.py`, `inspect_*.py`, `run_*.py`, `split_treatment.py`, `test_*.py`). `.gitignore:55-56` ignores per-tree `lite_mode/projects/` and `test_mode/projects/`, signaling that these are operator probe environments rather than runtime modules.

Risk class: ambiguous ownership + duplicate maintenance surface. Two places to forget to scrub when secrets, tokens, or operator notes leak in.

### F3. `배포_패키징.ps1` is a divergent release path with weaker exclusions [P2]

`배포_패키징.ps1` is a manual ZIP packager that walks the working tree (not `git ls-files`) and excludes `lite_mode`, `test_mode`, `tools`, `tools2`, `scripts`, `spikes`, `tmp_stage2_digest_debug`, `백업`, `MagicMock`, `.pytest_cache`, `.ruff_cache`, `.hypothesis`, `.github`, `__pycache__`. It excludes `.env`, but it does NOT exclude:

- `tests/` — the entire test tree ships in this ZIP.
- root residue: `0_temp.txt`, `tttt.txt`, `smoke_sc.py`, `RESET.py`, `md2pdf.py`, `main.js`, `generate_empire_reborn_tr70.py`, `tmp_utf8_check.py`, `tmp_utf8_check.txt`, `pyarmor.bug.log`.
- root tmp dirs: `temp_상태/`, `test_material/`, `tmp_stage2_digest_debug/` is excluded but `temp_상태/` and `test_material/` are not.
- secret-shaped sibling files outside `.env`: T01 owns the secret-file inventory, but T07 records the inclusion-rule gap because it reads on the dev/test axis too.

Risk class: divergent release rules across two ship paths. Even if `build/build_release.ps1` is hardened, `배포_패키징.ps1` provides a quieter alternate route. Final exclusion-rule design is T06's call; T07 records the surface delta.

### F4. Root residue files are tracked into git [P2]

Tracked under repo root (confirmed via `git ls-files --error-unmatch`):

- `0_temp.txt` — captured stdout from `python main_a.py` (V40 SOVEREIGN COCKPIT banner). Last touched on `2026-04-09 b94390cb checkpoint`. No production caller.
- `tttt.txt` — same nature, narrower terminal width.
- `smoke_sc.py` — smoke runner that calls real Gemini API ("실제 Gemini API를 호출합니다. 비용 ~$0.5~2") and patches `config/settings/validation.yaml` in place. Last touched on `4f3c2478 fix(genre): wuxia 전용 서비스를 비무협 장르에서 조건부 초기화`.
- `RESET.py` — operational project-reset tool; mutates `bible_data` actual_truth and DB rows.
- `md2pdf.py` — markdown-to-PDF converter utility.
- `main.js` — root-level Electron shadow entry, header explicitly states *"Manual debug shadow entry only. Authoritative Electron entry lives at `geuldobi-desktop/src/main.js`."*

Risk class:

- `0_temp.txt` and `tttt.txt` are pure stdout dumps — no production caller, accidental commits.
- `smoke_sc.py` is dev-only but ships into `배포_패키징.ps1` ZIPs because the root level is not excluded.
- `main.js` is a shadow entry that must never be elevated by packaging into the desktop runtime — its own header forbids it.
- `RESET.py` and `md2pdf.py` are operator tools that belong under a dev-only namespace.

### F5. `.tmp_stage0_msg/stage0_output/style_guide.json` is tracked under a tmp-named root directory [P2]

Even though `_*.py` and `tmp_*` patterns are gitignored, the leading-dot tmp directory `.tmp_stage0_msg/` is not matched and one descendant file (`stage0_output/style_guide.json`) is tracked. The directory naming claims tmp/ephemeral semantics but the artifact is being shipped via git history.

Risk class: contract / naming mismatch. Either the directory should be renamed to a non-tmp canonical path (and excluded from temp-cleanup harnesses), or the file should be moved to a stable home and the directory removed.

### F6. `tools2/test_*.py` and `tools2/validation_test_harness.py` are V44-era test artifacts living outside `tests/` [P2]

Tracked under `tools2/`: `test_continuity_validator.py`, `test_phase3_systems.py`, `test_priority1_security_fixes.py`, `test_v0128_validation.py`, `test_v43_updates.py`, `validation_test_harness.py`. Sibling docs `STABILITY_REPORT_V44.md` and `V44_ENHANCEMENT_PLAN.md` confirm this is a legacy V44 hardening surface. They are not collected by pytest (collection is rooted at `tests/`).

Risk class: stale test surface masquerading as a tool tree. Not executed in CI, not curated under `tests/`. `배포_패키징.ps1` excludes `tools2/`, so this is not a release-inclusion risk today, but it is an audit confusion vector and a place where stale assertions can drift from the live contract.

### F7. `tools/` is mixed prod-adjacent builders and one-off HTML [P3]

Tracked: `bible_builder.py`, `treatment_builder.py`, `treatment_extractor.py`, `genre_library_builder.py`, `db_porter.py`, `make_BP.py`, `story_expander.py`, `concat_txt.py`, `blueprint_name_fixer.py`, `fix_future_items.py`, `normalize_arcs_db.py`, plus three HTML files (`glodobi_overview_ppt.html`, `pipeline_visualizer.html`, `stage2_ppt_generator.html`) and `manual_ops/README.md`. The Korean filename `0_json만들기.py` is also tracked.

Risk class: low. These are operator tools, are excluded from `배포_패키징.ps1`, and the desktop release does not stage `tools/`. The naming `tools/` vs `tools2/` is itself a confusion vector — owner intent on splitting them is not documented.

### F8. `scripts/` mixes prod hygiene + canary/smoke + ops automation [P3]

121 tracked files. Broad sub-shapes:

- prod hygiene + ops invariants: `check_utf8_hygiene.py`, `ops_validator.py`, `ops_support.py`, `mojibake_global_survey.py`, `validate_*`, `populate_process_health_scorecard.py`, `run_pytest_lowmem.py`, `sync_temp_queue_state.py`, `build_execution_roadmap.py`, `run_stale_reference_sweep.py`, `generate_evidence_manifest.py` (referenced from AGENTS.md as canonical operator entry points).
- canary / smoke / e2e: `canary_path_utils.py`, `canary_semantic_exit.py`, `canary_stage2_headless.py`, `diff_canary_summaries.py`, `e2e_menu_smoke.ps1`, `prepare_smoke_fixture.py`, `run_stage2_canary.py`, `run_stage2_smoke.py`, `run_stage34_canary.py`, `run_stage34_ep_demo_canary.py`, `run_stage3_canary.py`, `run_stage3_smoke.py`, `run_stage4_canary.py`, `run_stage4_smoke.py`, `smoke_fixture_contract.py`.
- material / benchmark / clickup / github automation: `setup_clickup_views.py`, `sync_clickup_queue.py`, `setup_material_clickup_views.py`, `sync_material_clickup_queue.py`, `sync_github_issues.py`, `sync_narrative_reference_bank.py`, `material_*`, `benchmark_*`, `audit_benchmark_*`.
- tr/bi/episode batch builders: `produce_arc07.py`, `produce_block_59_70.py`, `produce_tr_blocks_*.py`, `tr_batch_harness.py`, `wuxia_tr_batch_harness.py`, `narrative_tr_batch.py`.

Risk class: low for the prod hygiene set, mixed for canary/smoke and one-off batch builders. `배포_패키징.ps1` excludes `scripts/` so release inclusion is not the worry here. The risk is observability / reviewability — owner intent (which entries are ops invariants vs which are throwaway batch builders) is implicit.

### F9. `scripts/_tmp_*.py` and root `tmp_*.py / tmp_*.txt / tmp_*.db` are correctly gitignored [INFO]

`scripts/` contains 10 local-only files matching `_tmp_*.py`, all caught by `.gitignore:33 _*.py` and not tracked. Root contains `tmp_utf8_check.py`, `tmp_utf8_check.txt`, `tmp_project_00_style_survey.db`, `tmp_stage2_digest_debug/`, all gitignored. `generate_empire_reborn_tr70.py` is gitignored via `.gitignore:114 generate_*.py`. `pyarmor.bug.log` is gitignored via `.gitignore:35 *.log`.

Risk class: this is a gitignore PASS, but it depends on every release path running git-aware copy. `배포_패키징.ps1` walks the working tree, so untracked-but-on-disk files still ship unless explicitly excluded. T06 and T09 own the release-aware exclusion design.

### F10. `spikes/` is gitignored at root and only holds local PyInstaller throwaways [INFO]

`.gitignore:58 spikes/` excludes the whole directory; `git ls-files spikes/` returns zero tracked files. On disk: `spikes/pyinstaller/build/spike_pyinstaller`, `spikes/pyinstaller/dist/spike_pyinstaller.exe`. Already excluded by `배포_패키징.ps1` and not staged by `build/build_release.ps1`.

Risk class: PASS. Nothing to move; nothing to ship.

### F11. `docs/temp/` already contains live audit Python and run-output dumps [P3]

Tracked under `docs/temp/`: `jangyeongshil_3pass_audit.py`, `jangyeongshil_bi_audit.py`, plus state JSON files and `phase0_debug_output.txt`, `phase0_debug2_output.txt`, `phase0_run_output.txt`, `stage2_run_output.txt`, `stage3_run_output.txt`. AGENTS.md §`Operations Governance` and §`System Survey Harness` define `docs/temp/` as the active execution queue surface and require a canonical `docs/YYYY-MM-DD/` original. Audit Python that mutates nothing is acceptable here, but tracked Python under `docs/temp/` must have an SSOT counterpart per workspace contract; T07 only flags the surface, not the contract status.

Risk class: low for security; medium for governance hygiene. Outside T07 mandate to resolve.

### F12. `docs/archive/` is functioning as designed [INFO]

`docs/archive/one-off-scripts/2026-04-26/` already holds `fix_costs.py`, `fix_costs2.py`. `docs/archive/root-residue/2026-04-26/` already holds `.tmp_b60_full.txt`, `bash.exe.stackdump`. The archive layout (one-off-scripts, root-residue, root-notes, run-inputs) is the right destination for items flagged `move to docs/archive` below.

### F13. `tests/` is correctly located [INFO]

`tests/` has 517 tracked files, structured with `__init__.py`, `conftest.py`, `chaos/`, `e2e/`, `integration/`, `property/`, `stage3_isolated_test/`, `stage4_v2_test/`, `README.md`. `.github/workflows/test.yml` invokes only `tests/test_*.py` plus `scripts/run_pytest_lowmem.py` as the runner. The `tests/_tmp_*` pattern is empty (no `_tmp_` files under `tests/`). No #69 separation work is needed inside `tests/` itself.

## Remediation Candidates

These are *candidates* — not implementation orders. Each row records the proposed disposition, a one-line rationale, and any precondition (T06 release-spec alignment, T01 secret-clearance, owner judgment, etc.). T07 does not move, copy, edit, or delete files in this wave.

### Root files

| Path | Tracked | Disposition | Rationale | Precondition |
| --- | --- | --- | --- | --- |
| `0_temp.txt` | yes | move to `docs/archive/root-residue/2026-04-27/` then untrack | Captured `python main_a.py` stdout dump, no production caller. | None internal to T07. |
| `tttt.txt` | yes | move to `docs/archive/root-residue/2026-04-27/` then untrack | Same nature as `0_temp.txt`, narrower terminal. | None internal to T07. |
| `smoke_sc.py` | yes | move to `scripts/dev/smoke_sc.py` (or `tools/` operator namespace) | Real-API smoke, not a unit test, mutates `config/settings/validation.yaml` in place. | Owner decision on permanent home; T01 must confirm script does not embed secret defaults. |
| `RESET.py` | yes | move to `scripts/dev/reset_project.py` | Operator reset tool for a single project, not a runtime entry. | Owner decision on naming. |
| `md2pdf.py` | yes | move to `scripts/dev/md2pdf.py` | Doc-conversion utility, not invoked by runtime. | None internal to T07. |
| `main.js` | yes | needs owner decision (keep + harden header OR move to `geuldobi-desktop/dev/`) | File header self-declares "Manual debug shadow entry only" and forbids packaging. Survival in repo root keeps mis-pickup risk alive. | T04 desktop-bridge survey + T06 release inclusion both touch this file's promotion path. |
| `generate_empire_reborn_tr70.py` | no (gitignored) | ignore + build-exclude | Already gitignored via `generate_*.py`. Confirm `배포_패키징.ps1` skips root-level `generate_*.py` (it does not today; T06 should add). | T06. |
| `tmp_utf8_check.py` / `tmp_utf8_check.txt` | no (gitignored) | ignore + build-exclude | Already gitignored. Same release-aware exclusion concern as above. | T06. |
| `pyarmor.bug.log` | no (gitignored) | ignore + build-exclude | Already gitignored via `*.log`. | T06. |
| `tmp_project_00_style_survey.db` | no (gitignored) | ignore + build-exclude | Already gitignored via `tmp_*.db`. | T06. |
| `tmp_stage2_digest_debug/` | no (gitignored) | ignore + build-exclude | Already gitignored. | T06. |
| `temp_상태/` | no (gitignored) | ignore + build-exclude | Local screenshot scratch (`1.png` … `5.png`). Add explicit exclusion in `배포_패키징.ps1`. | T06. |
| `test_material/` | no (gitignored) | ignore + build-exclude | Already gitignored. T06 must confirm `배포_패키징.ps1` excludes (it does not today). | T06. |
| `.tmp_stage0_msg/` | partially tracked | needs owner decision | One descendant file is tracked (`stage0_output/style_guide.json`). Either rename directory to non-tmp canonical home, or move the JSON to a stable path and remove the directory. | Owner decision. |

### `lite_mode/` and `test_mode/`

| Path | Tracked | Disposition | Rationale | Precondition |
| --- | --- | --- | --- | --- |
| `lite_mode/test_*.py`, `lite_mode/inspect_*.py`, `lite_mode/manual_ui_discovery_probe.py`, `lite_mode/clean_residue.py`, `lite_mode/free_writer.py`, `lite_mode/run_arc28.py`, `lite_mode/run_fix_arcs.py`, `lite_mode/run_patch.py`, `lite_mode/run_revalidate.py`, `lite_mode/run_stage.py`, `lite_mode/split_treatment.py` | yes | needs owner decision: move to `lite_mode/dev/` subdir AND build-exclude that subdir, or move to `scripts/dev/lite_mode_probes/` | These are dev probes; they currently ship into `dist/engine` because `build/build_release.ps1` whole-directory copies `lite_mode`. | T06 must update `Sync-EngineBundle` once destination is chosen. |
| `lite_mode/bridge/*.py`, `lite_mode/main_lite.py`, `lite_mode/ARCHITECTURE.md` | yes | keep production (subject to T06 confirming runtime contract still requires lite_mode bundle) | These are the actual lite-mode runtime surfaces referenced by `ARCHITECTURE.md`. | T06 audit. |
| `test_mode/*` | yes | needs owner decision (likely consolidate with `lite_mode/` or relocate to `scripts/dev/test_mode_probes/`) | Near-duplicate of lite_mode probes. Already excluded by `배포_패키징.ps1` and not staged by `build/build_release.ps1`, so this is structural cleanup, not security blocker. | Owner decision. |

### `tools/` and `tools2/`

| Path | Tracked | Disposition | Rationale | Precondition |
| --- | --- | --- | --- | --- |
| `tools2/test_*.py`, `tools2/validation_test_harness.py` | yes | move to `docs/archive/legacy-tests-v44/2026-04-27/` | V44-era stale tests outside pytest collection root; sibling reports already say V44. | Owner sign-off that no live caller exists. |
| `tools2/STABILITY_REPORT_V44.md`, `tools2/V44_ENHANCEMENT_PLAN.md`, `tools2/project_full_source.md`, `tools2/글도비_제작로직_설명서.txt` | yes | move to `docs/archive/v44-tools/2026-04-27/` | Historical analysis docs, not living references. | Owner sign-off. |
| `tools2/temp.py`, `tools2/ep15_expanded.txt` | yes | move to `docs/archive/one-off-scripts/2026-04-27/` and `docs/archive/run-inputs/2026-04-27/` respectively | Throwaway one-off output. | None. |
| `tools2/{apply_v3.py, apply_v3_pt2.py, expand_ep15.py, sanitize_reference.py, reverse_bible.py, rlhf_interface.py, studio_dashboard.py, performance_dashboard.py, arc_dashboard.py, automate_snack.py, cost_calculation.py, full_project_cost.py, style_transfer.py}` | yes | needs owner decision (split: keep operator tools, archive legacy V44 helpers) | Mixed. Some look like operator dashboards, others like one-time migration scripts. | Owner walkthrough. |
| `tools2/pytest.ini`, `tools2/requirements.txt` | yes | needs owner decision | A nested `pytest.ini` under `tools2/` can shadow root `pyproject.toml`/pytest config if collection is ever rerooted. Verify with T09 (CI guardrails owner). | T09. |
| `tools/{bible_builder.py, treatment_builder.py, treatment_extractor.py, genre_library_builder.py, db_porter.py, make_BP.py, story_expander.py, blueprint_name_fixer.py, fix_future_items.py, normalize_arcs_db.py, concat_txt.py, 0_json만들기.py}` | yes | keep production (operator namespace) | Excluded from both release paths. Owner-driven operator surface. | None. |
| `tools/*.html` (`glodobi_overview_ppt.html`, `pipeline_visualizer.html`, `stage2_ppt_generator.html`) | yes | needs owner decision | One-off HTML; could move to `docs/archive/visualizers/` if not actively maintained. | Owner. |

### `scripts/`

| Path pattern | Tracked | Disposition | Rationale | Precondition |
| --- | --- | --- | --- | --- |
| `scripts/run_*_canary.py`, `scripts/run_*_smoke.py`, `scripts/canary_*.py`, `scripts/diff_canary_summaries.py`, `scripts/prepare_smoke_fixture.py`, `scripts/smoke_fixture_contract.py`, `scripts/e2e_menu_smoke.ps1` | yes | keep production (consider sub-directory `scripts/canary/` for clarity) | These are referenced by tracked `tests/test_*canary*.py` and `tests/test_*smoke*.py`. Not a security risk, but readability gain. | Owner. |
| `scripts/{check_utf8_hygiene.py, ops_validator.py, ops_support.py, mojibake_global_survey.py, validate_*.py, populate_process_health_scorecard.py, run_pytest_lowmem.py, sync_temp_queue_state.py, build_execution_roadmap.py, run_stale_reference_sweep.py, generate_evidence_manifest.py, validate_deep_global_survey_bundle.py}` | yes | keep production | Canonical operator entry points referenced in AGENTS.md. | None. |
| `scripts/{produce_arc07.py, produce_block_59_70.py, produce_tr_blocks_*.py, generate_*.py for non-_tr_ batches, build_*.py one-off corpus builders}` | yes | needs owner decision | Mixed one-off batch runners. Some are reusable; some are date-bounded. Owner triage. | Owner. |
| `scripts/_tmp_*.py` (10 files) | no (gitignored) | ignore + build-exclude | Already PASS. Confirm `배포_패키징.ps1` excludes `scripts/` (it does), and confirm no other release path traverses scripts/. | T06. |

### `tests/`

| Path | Disposition | Rationale |
| --- | --- | --- |
| `tests/**` | keep production | Correct location, only collection root, CI references match. No #69 work needed inside. |
| `tests/__pycache__/`, `tests/.pytest_cache/`, `tests/__init__.py` | keep production | Standard. |

### `docs/temp/` and `docs/archive/`

| Path | Disposition | Rationale |
| --- | --- | --- |
| `docs/temp/jangyeongshil_3pass_audit.py`, `docs/temp/jangyeongshil_bi_audit.py` | needs owner decision | Tracked Python under `docs/temp/`. AGENTS.md requires canonical SSOT under `docs/YYYY-MM-DD/`. Verify counterpart exists, otherwise relocate. |
| `docs/temp/*_run_output.txt`, `docs/temp/*_debug_output.txt`, `docs/temp/queue-state.json`, `docs/temp/material-queue-state.json`, `docs/temp/clickup-*-state.json` | keep production (per AGENTS.md temp queue contract) | These are expected raw evidence + queue state. |
| `docs/archive/one-off-scripts/2026-04-26/{fix_costs.py, fix_costs2.py}` | keep archived | Already correctly placed. |
| `docs/archive/root-residue/2026-04-26/{.tmp_b60_full.txt, bash.exe.stackdump}` | keep archived | Already correctly placed. |

### `spikes/`

| Path | Disposition | Rationale |
| --- | --- | --- |
| `spikes/**` | ignore + build-exclude | Already gitignored at root via `spikes/`. Already excluded by `배포_패키징.ps1`. Already not staged by `build/build_release.ps1`. PASS. |

### CI workflow

| Path | Disposition | Rationale |
| --- | --- | --- |
| `.github/workflows/test.yml` | keep production | Only references `tests/test_*.py` and `scripts/run_pytest_lowmem.py`. No dev-tree leakage. T09 owns guardrail recommendations beyond #69 separation. |

## Dependencies On Other Terminals

- **T01 (root secret inventory).** If T01 confirms any `lite_mode/` or `test_mode/` probe embeds a real token / cookie / API key (Gemini-UI probes are likely to read `~/.config/google-chrome` or similar), F1 escalates from P1 to P0 because dev probes are then shipping secret-touching code paths into `dist/engine`. T07 explicitly does not open lite_mode probe internals to keep the security handling rule (no secret-value exposure) intact.
- **T03 (Vertex auth flow).** If `lite_mode/bridge/gemini_driver.py` or any probe drives Gemini through a shared Barobook account, the dev/test surface is also a credential-governance surface. F1 disposition then must coordinate with the auth migration plan.
- **T04 (desktop config surfaces).** Owns the final word on root `main.js` shadow entry promotion risk. T07 records the file but defers the keep/move/delete call.
- **T06 (release packaging).** Owns the actual `Sync-EngineBundle` edit, the curated `lite_mode/` subset spec, and the `배포_패키징.ps1` exclusion-list edit. All "build-exclude" rows above feed into T06's exclusion plan.
- **T08 (EXE access control).** If access-control entry is added at `build/backend_entry.py` or `geuldobi-desktop/src/main.js`, it must run BEFORE any lite_mode probe surface is reachable, otherwise F1 becomes a bypass.
- **T09 (CI / pre-commit guardrails).** Owns recommendations to (a) block new tracked files matching `^(0_|tttt|smoke_|RESET\.py|md2pdf\.py|main\.js|tmp_|generate_)`, (b) reject `_tmp_*.py` reaching staging, (c) prevent `tools2/test_*.py` from being collected by an alternate `pytest.ini`, (d) gate `배포_패키징.ps1` against a curated allowlist instead of ad-hoc denylist.
- **T10 (security response doc map).** Receives this F1–F13 inventory as input to the consolidated remediation map for #69.

## Open Questions

1. Is `lite_mode/` still part of the runtime contract `source_bundle_primary` advertises, or can it be split into `lite_mode/runtime/` (shipped) + `lite_mode/dev/` (excluded)? (Owner / T06.)
2. What is the canonical home for operator-only Python — `scripts/dev/`, `tools/`, or a new `dev_tools/`? Today the repo has three overlapping namespaces (`tools/`, `tools2/`, `main_tools/` per `배포_패키징.ps1` exclusion list). (Owner.)
3. Is `배포_패키징.ps1` still the operator-facing share path, or has `build/build_release.ps1` superseded it? If both remain, exclusion rules must be unified. (Owner / T06.)
4. Should `.tmp_stage0_msg/stage0_output/style_guide.json` be relocated to a stable path under `config/` or `data/`, or is the tmp-named container intentional? (Owner.)
5. Are `tools2/test_*.py` referenced by any external runner (CI, manual ops, GitHub Actions other than `test.yml`)? `git grep` was deferred to keep T07 read-only and bounded; T09 is better positioned to confirm. (T09.)
6. Should `0_temp.txt` and `tttt.txt` be removed from git history (`git filter-repo`) or only untracked + archived? Memory says a 04-03 history cleanup is partially done; coordinate. (Owner; cross-reference history-cleanup wave.)

## Closure Recommendation

T07 closure is **conditional documentation closure**: this report is sufficient to retire issue #69's discovery phase, but #69 itself stays open until:

1. T06 ships an updated `build/build_release.ps1` that either curates `lite_mode/` to a runtime-only subset or excludes a `lite_mode/dev/` subdir.
2. T06 ships an updated `배포_패키징.ps1` (or replaces it) with explicit exclusions for `0_temp.txt`, `tttt.txt`, `smoke_sc.py`, `RESET.py`, `md2pdf.py`, root-level `main.js`, root-level `generate_*.py`, `tmp_*`, `temp_상태/`, `test_material/`, and any other root residue T01 surfaces.
3. The owner decides destinations for the `needs owner decision` rows above (root `main.js`, lite_mode dev split, tools/tools2 reorganization, `.tmp_stage0_msg/` rename).
4. T09 adds a pre-commit / CI guard against re-introducing the same root-residue patterns.
5. The relocation moves themselves are executed in a follow-up `chore(structure)` wave that is NOT this read-only investigation. T07 explicitly does not perform the moves.

Until those four items land, #69 should remain open with this report linked as evidence.

Internal confidence: ~93% on inventory completeness and ~88% on remediation routing (uncertainty concentrated in F2 lite_mode/test_mode duplication intent and F11 docs/temp governance). Recommend re-audit if F1 escalates to P0 after T01/T03 close.
