# T06 Release Packaging Survey

Date: 2026-04-27
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Primary issues: #69 (test/dev separation), #70 (EXE access control), #66 (secrets/config)
Mode: read-only investigation. No code/config/git/GitHub mutation.
Secret handling: no raw secret values, private keys, recovery codes, tokens, or API keys are pasted in this report. Sensitive paths are recorded as paths only.

## Scope

Two parallel release/distribution paths exist in this repo and must be assessed together because they bundle different things and have different exclusion rules:

1. The Electron + PyInstaller release pipeline driven by `build/build_release.ps1` and `geuldobi-desktop/package.json` (`electron-builder`), producing the NSIS installer at `geuldobi-desktop/dist/Geuldobi Setup *.exe`.
2. The ad-hoc whole-workspace ZIP packager `배포_패키징.ps1` at the repo root, producing `C:\gldobi_deploy.zip`.

This report covers what each path bundles, what each path excludes, what credential/dev/log/build residue can leak through, and where an EXE access-control hook from #70 would attach. Final access-control model design belongs to T08; T06 only identifies the chokepoints.

## Commands / Evidence

Surface inspection (filenames/paths only, no secret content):

- `ls -la build/` — confirmed presence of `backend.spec`, `backend_entry.py`, `engine.spec`, `engine.patched.spec`, `build_release.ps1`, `prepare_python_embed.ps1`, plus residue: `pyarmor.bug.log`, `pyarmor-regcode-11492.txt`, `pyarmor-regfile-11492.zip`, `.cache/`, `.pyarmor/`, `build/` (PyInstaller intermediate work), `logs/`, `projects/`.
- `ls dist/` — `backend/`, `engine/`, `workspace-seed/` present.
- `ls dist/backend/` — `_internal/`, `backend.exe` (PyInstaller onedir).
- `ls dist/engine/` — `config/`, `datasets/`, `libraries/`, `lite_mode/`, `main_a.py`, `modules/`. **Plaintext Python source, not pyarmor-obfuscated.**
- `ls dist/engine/modules/` — includes `__pycache__/` (compiled cache shipped alongside source).
- `ls dist/workspace-seed/` — `bible/`, `projects/`, `seed-manifest.json`, `treatments/`.
- `ls dist/workspace-seed/projects/investment_canary_demo/` — only `README.txt` present (sample project source absent at last build).
- `ls geuldobi-desktop/dist/win-unpacked/resources/` — `app.asar`, `backend/`, `elevate.exe`, `engine/`, `python-embed/`, `workspace-seed/` (this is the actual installed footprint).
- `ls geuldobi-desktop/dist/win-unpacked/resources/engine/` — `config/ datasets/ libraries/ lite_mode/ main_a.py modules/` confirms plaintext source ships in the released installer.
- `git ls-files build/` — only the four spec/script files are tracked. All pyarmor regfiles, intermediate `build/build/...`, `.cache/`, `.pyarmor/`, and `pyarmor.bug.log` are untracked working-tree residue.
- `cat .gitignore` — `dist/` and `build/` are ignored at repo level; `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `secrets/*.env` are also ignored. Importantly, `pyarmor-regcode-*.txt`, `pyarmor-regfile-*.zip`, and `pyarmor.bug.log` are NOT explicitly ignored beyond the generic `*.log` rule (which only catches the bug log).
- `cat .pre-commit-config.yaml` — only `ruff` and a UTF-8 hygiene hook. No secret-scan, no packaging guard.
- `ls -la` (root) — `.env`, `.env.example`, `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `0_temp.txt`, `tttt.txt`, `tmp_utf8_check.{py,txt}`, `RESET.py`, `smoke_sc.py`, `tmp_project_00_style_survey.db`, `pyarmor.bug.log`, `secrets/` are all present at root.

Spec/contract reads:

- `build/backend.spec` — bundles only the FastAPI bridge + uvicorn + project `modules.api.*` hidden imports. `datas=[]`. Output: `dist/backend/backend.exe`. Source is wrapped by PyInstaller (no pyarmor on backend).
- `build/engine.spec` — would bundle `config/`, `libraries/`, `treatments/`, `bible/`, `lite_mode/` as datas, plus a walk of `modules/` for hidden imports. **Not invoked by `build_release.ps1`.**
- `build/engine.patched.spec` — pyarmor-patched copy of `engine.spec` referencing `C:\Users\wjjo\Desktop\글도비\.pyarmor\pack\dist`. **Not invoked by `build_release.ps1`.** This file hard-codes a developer-machine absolute path.
- `build/build_release.ps1` — the actual orchestration. Step 2 builds `backend.spec` only. Step 3 calls `Sync-EngineBundle`, which `Copy-Item -Recurse -Force` copies `main_a.py`, `modules/`, `config/`, `datasets/`, `libraries/`, `lite_mode/` into `dist/engine/` (i.e., raw .py source, no obfuscation). Step 3 also runs `geuldobi-desktop/scripts/build_workspace_seed.py`. Step 4 runs `npm run build` (electron-builder).
- `build/prepare_python_embed.ps1` — fetches `python-3.12.8-embed-amd64.zip` into `python-embed/`, enables pip, installs runtime packages (`google-genai`, `python-dotenv`, etc.).
- `geuldobi-desktop/package.json` — `electron-builder` config; `extraResources` pulls `../dist/backend`, `../dist/engine`, `../python-embed`, `../dist/workspace-seed`. The only filter is `"!**/*.log"`, `"!**/*.tmp"`, `"!**/*.bak"`. No filter on `__pycache__/`, `.pyc`, secrets, or dev probe scripts inside the staged trees.
- `geuldobi-desktop/scripts/build_workspace_seed.py` — copies a single `bible/01_bi_*.json`, a single `treatments/01_tr_*.json`, and `projects/smoke_fixture_demo/` into `dist/workspace-seed/`. Hard-fails (`RuntimeError`) if there is not exactly one `01_bi_*.json` or `01_tr_*.json`.
- `배포_패키징.ps1` — root whole-workspace zipper. Folder excludes: `.git, .claude, .pytest_cache, .ruff_cache, .hypothesis, .github, .venv, venv, __pycache__, projects, logs, 백업, lite_mode, spikes, MagicMock, tmp_stage2_digest_debug, test_mode, rlhf_data, datasets, main_tools, tools, tools2, scripts`. File excludes: `.env, CLAUDE.md, crash_dump.log, error.log, test_results.xml, nu_, nul, 배포_패키징.ps1`. Extension excludes: `.pyc, .db, .db-shm, .db-wal`. **`build/`, `dist/`, `secrets/`, `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `.env.example`, `*.log` (other than the two named), `.json` (other than the two named .db variants), `pyarmor-regcode-*.txt`, `pyarmor-regfile-*.zip` are NOT in the exclude list.**

Electron startup chokepoints (paths only; #70 design lives in T08):

- `geuldobi-desktop/src/main.js:1230` — `app.whenReady().then(...)`: single run-once entry before backend spawn or window creation.
- `geuldobi-desktop/src/main.js:463` — `function startBackend()`: spawn site for `backend.exe` (PROD) or `python -m uvicorn` (DEV).
- `geuldobi-desktop/src/main.js:586` and `:625` — `new BrowserWindow(...)` for main + splash; visible-UI gate.
- `build/backend_entry.py` — Python-side startup of `backend.exe`; runs `uvicorn.run(...)` after frozen-mode environment setup.
- `main_a.py` (root) and `dist/engine/main_a.py` (shipped copy) — plaintext engine entry. Because `dist/engine` ships unobfuscated, an end user with the installer can launch `python-embed\python.exe ..\engine\main_a.py` directly, bypassing Electron entirely. This is the most important chokepoint blind-spot for #70.

## Findings

### F1 — `dist/engine/` ships plaintext Python source (P1 for #66/#69 surface, P2 for #70)

- Path: `dist/engine/main_a.py`, `dist/engine/modules/**/*.py` and the same paths under `geuldobi-desktop/dist/win-unpacked/resources/engine/`.
- Evidence: `Sync-EngineBundle` in `build/build_release.ps1:75-91` performs `Copy-Item -Recurse -Force` of project source. `engine.patched.spec` (the pyarmor-aware spec) exists but is not invoked by `build_release.ps1`. Confirmed by directly listing `geuldobi-desktop/dist/win-unpacked/resources/engine/` showing `main_a.py` and `modules/__pycache__/` with raw .py files alongside.
- Risk: any internal-distribution recipient can read the entire engine source tree, including any inline secrets, debug prints, env-var fallback logic, model routing logic, and Director/agent prompts via `config/`. Because the EXE access-control story in #70 assumes "unauthorized copied EXE does not run normally," shipping the source effectively makes EXE-level gating bypassable by re-running `python-embed/python.exe ..\engine\main_a.py` directly.
- Note: this report does not relitigate whether obfuscation (pyarmor) is sufficient as IP protection. It only flags that the build pipeline diverged from `engine.patched.spec` without a documented decision.

### F2 — `__pycache__/` is shipped under `dist/engine/` (P3 hygiene)

- Path: `dist/engine/modules/__pycache__/` and parallel `geuldobi-desktop/dist/win-unpacked/resources/engine/modules/__pycache__/`.
- Evidence: `Sync-EngineBundle` uses `Copy-Item -Recurse -Force` with no exclusion; `package.json#build.extraResources` filter is only `!**/*.log`, `!**/*.tmp`, `!**/*.bak`.
- Risk: low security impact, mostly bloat and cross-machine pyc compatibility surprises. Flagged because the same filter list is the one that needs hardening for F3/F4.

### F3 — `배포_패키징.ps1` does not exclude `dist/`, `build/`, `secrets/`, root credential files (P0 for #66, P0 for #69)

- Path: `배포_패키징.ps1` (project root, tracked).
- Evidence: the script's `$exclude` and `$excludeFiles` arrays are listed verbatim under "Commands / Evidence". `build/`, `dist/`, `secrets/` are absent from `$exclude`. `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `.env.example`, `pyarmor-regcode-*.txt`, `pyarmor-regfile-*.zip` are absent from `$excludeFiles`. The `*.log`, `*.json`, `*.zip`, `*.txt` extensions are not in the extension filter (only `.pyc`, `.db`, `.db-shm`, `.db-wal`).
- Risk: the moment an operator runs `.\배포_패키징.ps1` from the repo root with the current working tree, `C:\gldobi_deploy.zip` will contain at minimum:
  - `geuldobi-vertex-key.json` (Vertex/GCP service-account JSON — credential leak to whoever receives the ZIP).
  - `github-recovery-codes.txt` (GitHub account recovery codes — full account-takeover material).
  - `secrets/clickup.env`, `secrets/n8n.local.env` (the `secrets/*.env` gitignore rule does not extend to ZIP).
  - `.env.example` (low risk if it's truly an example, but it is not in the exclude list either).
  - `build/pyarmor-regcode-11492.txt`, `build/pyarmor-regfile-11492.zip` (paid pyarmor license registration material — license fraud / IP escape risk).
  - `build/.cache/python-3.12.8-embed-amd64.zip` (large but low-risk).
  - `build/build/...` PyInstaller intermediates (hash leakage; not credential-grade but unnecessary).
  - `dist/engine/**/*.py` (entire engine source tree, see F1).
  - `pyarmor.bug.log` at repo root.
  - Numerous `tmp_*`, `0_temp.txt`, `tttt.txt`, `RESET.py`, `smoke_sc.py` root residues (T07's domain).
- Severity: this is the single most likely real-world leak channel because operators tend to use this script for convenience drops. Treat as P0 for both #66 and #69.

### F4 — `extraResources` filter only excludes `*.log`, `*.tmp`, `*.bak` (P1 for #66, P2 for #69)

- Path: `geuldobi-desktop/package.json:45-86`.
- Evidence: each of the four `extraResources` entries (`backend`, `engine`, `python-embed`, `workspace-seed`) carries the identical three-pattern filter.
- Risk: anything ending in `.json`, `.yaml`, `.txt`, `.env`, `.py`, `.zip` inside the four staging trees flows straight into the installer. Today the staging trees are clean of secrets because `Sync-EngineBundle` only copies `modules`, `config`, `datasets`, `libraries`, `lite_mode`, `main_a.py`. But there is no defense-in-depth: if a future change to `Sync-EngineBundle` (or to `engine.spec` if revived) adds `secrets/`, `.env`, root credential files, or a developer's local config dump, the installer will silently include it. Also, `python-embed/` ships with whatever `prepare_python_embed.ps1` placed inside, which is fine today (no secrets) but is an unverified surface.

### F5 — `engine.patched.spec` hard-codes a developer-machine absolute path and references files outside the workspace contract (P2 for #66/#69)

- Path: `build/engine.patched.spec:102-103`.
- Evidence: the spec embeds `srcpath = ['C:\\Users\\wjjo\\Desktop\\글도비']` and `obfpath = 'C:\\Users\\wjjo\\Desktop\\글도비\\.pyarmor\\pack\\dist'`. There is no corresponding `.pyarmor/pack/dist` tree at workspace root (only `build/.pyarmor/config`).
- Risk: if anyone re-enables the pyarmor path, the build will either fail (RuntimeError "No obfuscated script found") or quietly fall back to a stale state. The spec also discloses workspace user identity in any redistributed copy of the spec file. Low secret risk; medium reproducibility/tamper risk.

### F6 — `build/pyarmor-regcode-11492.txt`, `build/pyarmor-regfile-11492.zip`, `build/pyarmor.bug.log` are untracked but locally present and not protected from `배포_패키징.ps1` (P1 for #66)

- Evidence: `git ls-files build/` returns only `backend.spec backend_entry.py build_release.ps1 prepare_python_embed.ps1`. `git status` baseline reports no tracked dirty files. The reg files are working-tree only. `.gitignore` does not name them; the catch-all `*.log` covers `pyarmor.bug.log` for git, and the generic `build/` rule covers everything under `build/` for git, but `배포_패키징.ps1` does not respect `.gitignore`.
- Risk: pyarmor commercial registration material leaving the host machine via the ad-hoc ZIP. Severity drops if `dist/engine` is plaintext (F1) and pyarmor isn't even active in the active build path, but the regfiles are still license-grade artifacts that should not leave the developer machine.

### F7 — `build_workspace_seed.py` ships sample materials whose privacy class is unverified (P3 for #66)

- Path: `geuldobi-desktop/scripts/build_workspace_seed.py:69-107`.
- Evidence: `_require_single` picks the single `bible/01_bi_*.json` and the single `treatments/01_tr_*.json` from the developer's working directory and copies them verbatim into `dist/workspace-seed/`. The sample project source `projects/smoke_fixture_demo` is currently absent (`dist/workspace-seed/projects/investment_canary_demo/README.txt` is the placeholder branch).
- Risk: depends on whether the chosen `01_bi_*` and `01_tr_*` artifacts are intended for public distribution. This is content/IP risk, not credential risk. Flagged so #71 (security response doc) and a content owner can confirm the seed selection is intentional.

### F8 — `build_release.ps1` does not assert "no secrets in staged trees" before electron-builder runs (P1 for #66)

- Path: `build/build_release.ps1:144` — `Assert-PackagedResources` only checks that four expected files exist, never that unexpected files are absent.
- Risk: there is no guardrail step between `Sync-EngineBundle` and `npm run build` that scans the staged `dist/backend`, `dist/engine`, `python-embed`, `dist/workspace-seed` for `.env`, `*key*.json`, `*.pem`, `pyarmor-reg*`, `secrets/`, `__pycache__/`, etc. A future drift in `Sync-EngineBundle`'s `bundleItems` is immediately a release-time leak.

### F9 — Backend `backend.exe` and `python-embed/python.exe` have no auth gate at startup (P2 for #70)

- Paths: `build/backend_entry.py`, `geuldobi-desktop/src/main.js:463-552`, `python-embed/python.exe` (binary).
- Evidence: `backend_entry.py` only sets up `GEULDOBI_*` environment variables and starts uvicorn on `127.0.0.1:8300`. `startBackend()` in main.js spawns it with `windowsHide: true` but performs no licensing/authn check. Because `dist/engine/main_a.py` ships plaintext, an unauthorized recipient can launch `python-embed\python.exe ..\engine\main_a.py` directly and bypass the Electron shell entirely.
- Risk: this is the packaging-side input to #70's design; final access-control model is T08's. T06 confirms there is no current gate at any of these three layers (Electron `whenReady`, `backend.exe` entry, `python-embed` direct invocation).

### F10 — `__pycache__/` shipped under `geuldobi-desktop/dist/win-unpacked/` parallels root cache, no source-purge step (P3)

- Evidence: same as F2 but at the installer footprint level.
- Risk: low. Recorded for completeness.

## Remediation Candidates

Treat the list as candidates for #66/#69/#70; T06 does not implement.

1. **(P0, #66+#69)** Rewrite `배포_패키징.ps1` to default-deny then opt-in. Concrete moves:
   - Add `dist`, `build`, `secrets`, `python-embed`, `node_modules`, `geuldobi-desktop\dist`, `geuldobi-desktop\node_modules` to `$exclude`.
   - Add `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `.env.example`, `pyarmor.bug.log`, `pyarmor-regcode-*.txt`, `pyarmor-regfile-*.zip`, `*.pem`, `*.key`, `id_rsa*`, `*key*.json` to `$excludeFiles`/pattern matches.
   - Or, much safer: replace the script's "everything-by-default minus blocklist" model with an explicit allowlist of paths that ship.
   - Have the script call `git check-ignore` to honor `.gitignore` as a first filter; refuse to include anything `.gitignore` ignores.
   - Add a final pre-zip `grep`-style guard for `BEGIN PRIVATE KEY`, `recovery-codes`, `service_account`, `api_key=`-style markers; abort if found.
2. **(P0, #66)** Decide whether `배포_패키징.ps1` is still needed at all. It overlaps with `build_release.ps1`; if the only legitimate distribution path is the NSIS installer, retire `배포_패키징.ps1` and remove the tracked file.
3. **(P1, #66+#69)** Tighten `geuldobi-desktop/package.json#build.extraResources` filters to also exclude `__pycache__/`, `*.pyc`, `.env`, `.env.*`, `*key*.json`, `secrets/`, `pyarmor-reg*`, plus a `**/.git*` guard.
4. **(P1, #66)** Insert a pre-`npm run build` guardrail step in `build/build_release.ps1` that scans `dist/backend`, `dist/engine`, `python-embed`, `dist/workspace-seed` for forbidden patterns (`.env`, `*key*.json`, `secrets`, `pyarmor-reg*`, `BEGIN PRIVATE KEY`, etc.) and aborts on any hit. This is the audit T09 will likely also recommend; T06 specifically wants it because `Sync-EngineBundle` is the only fence between project root and shipped resources.
5. **(P1, #69)** Decide explicitly whether `dist/engine/` ships plaintext (current behavior) or via `engine.patched.spec` pyarmor pipeline. If pyarmor is the intended IP boundary, repair `engine.patched.spec`'s hard-coded path, restore the `.pyarmor/pack/dist` build step, and switch `build_release.ps1` Step 3 to invoke pyarmor + PyInstaller instead of `Sync-EngineBundle`. If plaintext is intentional, document that in the security response (#71) so #70 doesn't depend on assumptions T08 cannot verify.
6. **(P2, #70)** Provide T08 with the chokepoint inventory below as the candidate insertion sites for a startup access check:
   - Electron `app.whenReady` — earliest UI-side gate.
   - Electron `startBackend` — last gate before the local FastAPI server boots.
   - `build/backend_entry.py` `__main__` — before `uvicorn.run`.
   - `main_a.py` top of `if __name__ == "__main__":` — needed because of the plaintext-source bypass risk (F1+F9). T08 will choose which combination is feasible.
7. **(P2, #69)** Move `pyarmor-regcode-*.txt`, `pyarmor-regfile-*.zip`, `pyarmor.bug.log` out of `build/` into a `~/.pyarmor-licenses/` location outside the workspace, or at minimum add them to `.gitignore` as an explicit named pattern (defense-in-depth even though `build/` is already broad-ignored) and to `배포_패키징.ps1` excludes.
8. **(P3, #69)** Consider rolling the "no `__pycache__/` in shipped trees" guard into `build_release.ps1` (cheap to add, eliminates F2 and F10).

## Dependencies On Other Terminals

- T01 (root secret inventory) — owns the authoritative list of credential files at the repo root. T06 only flags that `배포_패키징.ps1` does not exclude them; T01's inventory feeds T06's exclude list.
- T02 (runtime config topology) — owns whether `config/settings.json` and `config/models.yaml` contain only env-var names. T06 spot-checked `config/models.yaml` (env-var names only, no values), but the binding decision is T02's.
- T03 (Vertex auth flow) — owns whether `geuldobi-vertex-key.json` is the canonical credential file or a leftover. T06's F3 assumes worst-case (it is real and credential-grade). If T03 confirms it is no longer needed, F3 severity changes from "credential leak via ZIP" to "stale credential file on disk."
- T04 (desktop config surfaces) — owns the IPC settings/Electron-side config write surfaces. T06's F4 is adjacent but limited to electron-builder packaging; T04 owns runtime-side disclosure paths.
- T05 (Windows settings paths) — owns whether `python-embed/` writes settings or runtime data into the install dir vs `%APPDATA%`. T06 only confirms `python-embed/` is shipped in the installer.
- T07 (dev/test separation) — owns the inventory of `lite_mode/`, `test_mode/`, `tools/`, `tools2/`, `scripts/`, root residue files. T06's F1/F3 reference these because `lite_mode/` is bundled into `dist/engine/` and root residues are bundled by `배포_패키징.ps1`.
- T08 (EXE access control) — owns the access-control model selection. T06 supplies the chokepoint inventory in F9 and Remediation #6.
- T09 (CI / pre-commit / release guardrails) — owns the automation side. T06's Remediation #4 is intended as a release-time guard; T09 may absorb or complement it with a pre-commit guard.
- T10 (security response documentation) — should fold F1, F3, F4, F8, F9 into the residual-risk and current-mitigation status sections.

## Open Questions

1. Is `배포_패키징.ps1` still an authorized distribution channel, or is the NSIS installer the only sanctioned channel? If the latter, the script should be retired rather than hardened.
2. Is the engine intended to ship as plaintext Python (current behavior) or as pyarmor-obfuscated (per `engine.patched.spec`)? If pyarmor was abandoned, when and why? Need a captured decision before #70 design.
3. Is `geuldobi-vertex-key.json` still the active Vertex credential? T03 should confirm; T06's worst-case assumption may overstate severity if T03 reports the key is dead.
4. Is `dist/workspace-seed/` (the bible/treatment seed) considered shippable IP? If yes, no action; if no, `build_workspace_seed.py` selection rule needs review.
5. Are the pyarmor reg files (`build/pyarmor-regcode-11492.txt`, `build/pyarmor-regfile-11492.zip`) under license terms that prohibit redistribution? Severity of F6 depends on the pyarmor license contract.
6. Does `python-embed/` get shipped with any developer-installed extra packages beyond what `prepare_python_embed.ps1` lists? T06 inspected only the script's intent, not the actual `python-embed/` working tree contents.

## Closure Recommendation

Do **not** close #66, #69, or #70 based on this report alone.

- For #66: F3 (credential leak via `배포_패키징.ps1`) and F4 (weak `extraResources` filter) must be remediated and the remediation merged before #66 can move toward closure. T06 alone is sufficient evidence to keep #66 P0 status.
- For #69: F1 (plaintext engine ship), F2/F10 (`__pycache__` ship), F6 (pyarmor regfile leak risk via ZIP), and F8 (no pre-build secrets scan) must each be either fixed or explicitly accepted in a written decision before #69 can close.
- For #70: T06 confirms there is no startup gate today and supplies the chokepoint inventory (F9, Remediation #6). #70 stays open and waits on T08's design.

Recommended next action sequence:

1. Park `배포_패키징.ps1` (or rewrite to allowlist) before any other change — this is the highest blast-radius leak channel today.
2. Add `extraResources` filter hardening + `build_release.ps1` pre-build guard (Remediation #3, #4).
3. Resolve the plaintext-vs-pyarmor decision (Remediation #5) so T08 has a fixed packaging surface to design against.
4. Forward chokepoint inventory to T08 for #70.
5. Feed F1, F3, F4, F8, F9 into T10's residual-risk and mitigation-status doc.

Estimated investigator confidence (this report): 95%.
