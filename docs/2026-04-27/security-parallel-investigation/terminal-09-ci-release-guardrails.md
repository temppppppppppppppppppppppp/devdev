# T09 CI And Release Guardrails

Date: 2026-04-27
Terminal: T09
Primary GitHub Issues: #66 `[SEC] Remove secrets from code/config and standardize runtime config loading`, #69 `[SEC] Separate test/dev scripts from production source tree`
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Document type: read-only investigation report under the security-parallel-investigation dispatch. Not an execution SSOT, not a code-patch order.
Save path: `docs/2026-04-27/security-parallel-investigation/terminal-09-ci-release-guardrails.md`

## Scope

This terminal surveys whether any **automated guardrail** currently blocks the four high-impact security failure modes implied by issues #66 and #69:

1. Committing a secret into git history (root `.env`, `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, future PRs that re-introduce credentials).
2. Bundling `.env`, secret JSON, recovery codes, PyArmor reg files, or other local secret artifacts into shippable release outputs (`backend.exe`, engine source bundle, Electron `extraResources`, NSIS installer).
3. Shipping `tests/`, `lite_mode/`, `test_mode/`, `spikes/`, `tools/`, `tools2/`, scripts/`_tmp_*.py`, smoke/canary scripts, or `docs/temp/` working artifacts inside a release.
4. Writing settings to `Program Files` / install dir at runtime (release-time guardrail, not source guardrail).

The terminal inspects: `.github/workflows/test.yml`, `.pre-commit-config.yaml`, `pyproject.toml`, `.editorconfig`, `.gitignore`, `.gitattributes`, `scripts/check_utf8_hygiene.py`, `scripts/ops_validator.py`, `build/build_release.ps1`, `build/backend.spec`, `geuldobi-desktop/package.json`, plus already-existing related test guards (`tests/test_desktop_packaging_contract.py`, `tests/test_desktop_shadow_hygiene.py`, `tests/test_check_utf8_hygiene.py`).

Out of scope (handed to other terminals):
- Inventory of which secret files exist on disk and their tracked/ignored state (T01).
- Runtime config loading, fallback order, `.env` reads in Python (T02).
- Vertex auth flow and shared-account governance (T03).
- Desktop/Electron config/settings IPC surfaces (T04).
- Approved Windows config write-path policy (T05).
- Release packaging staging behavior in detail (T06).
- Dev/test/temp file separation policy and inventory (T07).
- EXE access-control authorization model (T08).
- Security response documentation map (T10).

## Commands / Evidence

### Files inspected (UTF-8 reads, no secret values quoted)

- `.github/workflows/test.yml` — 214 lines, four jobs.
- `.pre-commit-config.yaml` — 19 lines, two hook repos.
- `pyproject.toml` — 70 lines, ruff + pytest config only.
- `.editorconfig` — UTF-8 + LF + trailing-whitespace pin.
- `.gitignore` — 132 lines.
- `.gitattributes` — CRLF/LF normalization, no secret-aware rules.
- `scripts/check_utf8_hygiene.py` — 226 lines, encoding/mojibake checker; no secret check.
- `scripts/ops_validator.py` — 493 lines, validates `docs/temp/` queue mirror; no secret check.
- `build/build_release.ps1` — 169 lines.
- `build/backend.spec` — 75 lines, PyInstaller spec, `datas=[]`.
- `geuldobi-desktop/package.json` — Electron-builder block with `extraResources`/`files`.
- `tests/test_desktop_packaging_contract.py` — 124 lines, asserts `**/*.log/.tmp/.bak` filters and inventory presence; no secret-absence assertion.
- `tests/test_desktop_shadow_hygiene.py` — 68 lines, validates shim/preload contracts; no secret-related assertion.
- `tests/test_check_utf8_hygiene.py` — 90 lines, locks UTF-8 contract pins.

### Git tracking state of high-risk artifacts (read-only)

- `git ls-files build/` returns only the four tracked files: `build/backend.spec`, `build/backend_entry.py`, `build/build_release.ps1`, `build/prepare_python_embed.ps1`.
- `git check-ignore -v build/pyarmor-regcode-11492.txt build/pyarmor-regfile-11492.zip build/pyarmor.bug.log` reports each as ignored by `.gitignore:8 build/`. So those PyArmor registration artifacts are **not tracked**, but they sit on disk inside the build dir and are local-only.
- `.gitignore` lines 130–131 explicitly exclude `github-recovery-codes.txt` and `geuldobi-vertex-key.json` from tracking. T01 owns the live status of these files on disk.
- `.gitignore` line 13 ignores `.env`; lines 14 ignores `secrets/*.env`. **Not** ignored at the gitignore layer: `secrets/*.json`, `secrets/*.txt`, `config/settings.json`, `config/models.yaml`. T01/T02 own classification of those.

### CI secret references

`grep -n -i -E "secret|credential" .github/workflows/test.yml`:

```
83:          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
103:          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
127:          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

This is the only secret consumed by CI. No other secret-scanning, gitleaks, trufflehog, detect-secrets, or custom secret-grep step exists in the workflow.

### Pre-commit hooks

`.pre-commit-config.yaml` configures exactly two repos:

- `astral-sh/ruff-pre-commit` v0.9.6 with `ruff` (--fix) and `ruff-format`.
- `repo: local` with `check-utf8-hygiene` calling `scripts/check_utf8_hygiene.py`.

No `detect-secrets`, `gitleaks`, `pre-commit-hooks` (e.g., `forbid-new-submodules`, `check-added-large-files`, `check-private-key`), or repo-local `forbid-secret-paths` hook is configured.

### Release packaging staging (`build/build_release.ps1`)

Step 3 stages the engine source bundle by copying these top-level paths into `dist/engine/`:

```
"main_a.py",
"modules",
"config",
"datasets",
"libraries",
"lite_mode"
```

There is **no exclusion list**. The script does not strip `.env`, `secrets/`, `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `build/pyarmor-*`, `__pycache__/`, `tests/`, `_tmp_*.py`, or other local artifacts. It relies entirely on:

- The fact that those root-level files are not in the bundleItems list, so `Copy-BundleItem` won't pull `.env` or the Vertex key JSON from project root.
- The implicit shape of `config/`, `datasets/`, `libraries/`, `lite_mode/` containing only non-secret content right now.
- `Assert-PackagedResources` only verifies that an inventory of expected files **is present** (positive check). It does not assert that any secret file or test artifact is **absent** (no negative check).

Step 4 hands off to `electron-builder` for the NSIS installer.

### Electron packaging filters (`geuldobi-desktop/package.json`)

`build.extraResources` for the four staged resource roots (`backend`, `engine`, `python-embed`, `workspace-seed`) all share the same filter list:

```
"**/*",
"!**/*.log",
"!**/*.tmp",
"!**/*.bak"
```

`build.files` for the Electron app source includes `"src/**/*"` and excludes `"!node_modules/.cache"` and `"!src/sprites/dbg_desk_*"`.

Notable absences from both filter lists: `!**/.env`, `!**/.env.*`, `!**/secrets/**`, `!**/*.key`, `!**/*credentials*.json`, `!**/*-vertex-key.json`, `!**/github-recovery-codes.txt`, `!**/pyarmor-*`, `!**/__pycache__/**`, `!**/tests/**`, `!**/_tmp_*.py`.

Code-signing block: `"signAndEditExecutable": false`. Combined with the absence of any release authenticity guardrail in CI, the produced installer is unsigned and free to be tampered with after build.

### Existing packaging-related tests

`tests/test_desktop_packaging_contract.py:28-33` asserts:

```python
filters = set(resource["filter"])
assert "**/*" in filters
assert "!**/*.log" in filters
assert "!**/*.tmp" in filters
assert "!**/*.bak" in filters
```

It does **not** assert that secret patterns or test directories are excluded. So even if a developer manually added a `.env` to `dist/engine/` before packaging, this contract test would not flag it.

### Lint job non-blocking semantics

`.github/workflows/test.yml:154-164`:

```
flake8 modules/ --count --select=E9,F63,F7,F82 --show-source --statistics      # blocking, narrow
flake8 modules/ --count --exit-zero --max-complexity=15 --max-line-length=120  # non-blocking
black --check --diff modules/ || true                                          # non-blocking
isort --check-only --diff modules/ || true                                     # non-blocking
```

Lint job is mostly soft. Not a security issue by itself, but it shows the CI pattern of `|| true` which would also weaken any future security check if added the same way.

## Findings

Severities use the dispatch rubric (`P0/P1/P2/P3`). Each finding is paired with its source evidence above.

### F1. No secret-scanning guardrail anywhere in the toolchain — P0

Neither pre-commit nor CI has a secret-detection step. There is no `detect-secrets`, `gitleaks`, `trufflehog`, `git secrets`, `check-private-key`, or repo-local secret-pattern grep. Combined with the fact that historical `.env` / `geuldobi-vertex-key.json` / `github-recovery-codes.txt` artifacts have existed on disk (per T01 scope), a future re-introduction would currently land in `main` undetected on the automation side, with only `.gitignore` standing in the way. `.gitignore` is a tracking filter, not a leak guard — `git add -f` or a renamed copy bypasses it silently.

Evidence: `.pre-commit-config.yaml` (2 hooks only), `.github/workflows/test.yml` (no scanner step), `.gitignore:13,14,130,131`.

### F2. No release-bundle anti-secret/anti-test exclusion — P0

`build/build_release.ps1` stages `main_a.py`, `modules`, `config`, `datasets`, `libraries`, `lite_mode` into `dist/engine/` with no exclude list. `geuldobi-desktop/package.json` `extraResources` filters only `*.log`, `*.tmp`, `*.bak`. There is no allowlist/denylist that would stop a developer's local `.env`, `secrets/*.json`, `*-vertex-key.json`, recovery codes, `__pycache__/`, `pyarmor-*`, or stray test artifacts from being copy-staged into `dist/engine/` (or, if relocated, into `dist/backend/`) and then mirrored verbatim into `Geuldobi-Setup-*.exe`. `Assert-PackagedResources` is a presence-only check.

Evidence: `build/build_release.ps1:32-43, 78-90, 93-110`, `geuldobi-desktop/package.json` `extraResources` block.

### F3. `lite_mode/` is bundled into release engine source without a hygiene contract — P1

`bundleItems` includes `lite_mode`. `lite_mode/projects/` is gitignored (`.gitignore:57`), but the **non-ignored** parts of `lite_mode/` are shipped wholesale. There is no test asserting what `lite_mode/` is allowed to contain at release time, no manifest of its surface area, and no separation between "keep in dev only" code and "ship-safe runtime fallback" code. T07 owns the substance; T09 records that release packaging has no enforcement.

Evidence: `build/build_release.ps1:78-90`, `.gitignore:57, 60`.

### F4. `config/` directory is bundled with no secret-vs-config split — P1

`bundleItems` ships the entire tracked `config/` directory. The dispatch already names `config/settings.json` and `config/models.yaml` as in-scope surfaces (per T01/T02). Because release staging copies `config/` recursively, any tracked file that ever lands in `config/` automatically ships. There is no "secret-bearing config files must be loaded from `%APPDATA%` instead of bundled" enforcement at release time. T05 owns the policy; T09 records the missing release guardrail.

Evidence: `build/build_release.ps1:78-90`, T01/T02/T05 scope hand-offs.

### F5. NSIS installer is unsigned and has no release-authenticity guardrail — P1

`geuldobi-desktop/package.json` sets `"signAndEditExecutable": false`. CI does not produce a release artifact, does not produce a SHA256 manifest, and does not publish a signed `latest.yml`/`latest-release.json`. This is operationally important for #70 (executable access control) because authorization of a copied EXE has no integrity anchor to verify against. T08 owns the access-control model; T09 records that the release pipeline does not currently emit anything an internal allowlist could attest to.

Evidence: `geuldobi-desktop/package.json` `build.win.signAndEditExecutable`.

### F6. `pyproject.toml` ruff `extend-exclude` skips `lite_mode`, `test_mode`, `spikes`, `tools`, `tools2` for lint — P2

These directories are excluded from ruff lint. That is a developer-experience choice, not a bug, but it has a security-adjacent side effect: any secret-leak-style ruff rule (e.g., a custom `# noqa` discipline or future rule pack) would also be skipped for those directories. Combined with `.gitignore` not gitignoring those paths and `build/build_release.ps1` shipping `lite_mode/`, the lint exclusion creates a blind spot exactly where a "junk dev tree" would be most likely to grow. Recommendation belongs to T07/T09 jointly.

Evidence: `pyproject.toml:9-16`.

### F7. CI lint job is largely non-blocking (`|| true`, `--exit-zero`) — P3

Documented for completeness. Not a security finding in itself, but it sets a precedent: any guardrail added to that job in `|| true` style would also be effectively advisory. Future security checks must be **blocking** to count as guardrails.

Evidence: `.github/workflows/test.yml:155-164`.

### F8. CI does not run `scripts/ops_validator.py` or `scripts/check_utf8_hygiene.py` — P3

`check_utf8_hygiene.py` is wired into `pre-commit`, which only runs locally on staged files. CI does not enforce it on the full tree, and CI does not run `ops_validator.py` against `docs/temp/` at all. So any drift introduced by a contributor without pre-commit installed (Codex, third-party PR, web edit) would not be caught at PR time. Marked P3 because it is a hygiene blind spot, not a credential exposure path; it becomes more relevant if/when secret/leak hooks are added to pre-commit and we want them mirrored in CI.

Evidence: `.github/workflows/test.yml`, `.pre-commit-config.yaml`, `scripts/ops_validator.py`.

### F9. No CI guardrail prevents writing to `Program Files` at runtime — informational

`build/build_release.ps1` is a build-time script and naturally writes inside the repo / `dist/`. There is no test asserting the runtime never writes to install dir. This belongs to T05 (Windows path policy) and T08 (EXE chokepoints); T09 records that no automated release-side check exists today to enforce a "no install-dir writes" invariant.

Evidence: T05/T08 hand-off, no matching test in `tests/`.

## Remediation Candidates

Recommendations only. **Do not implement under this read-only wave.** Each candidate names where the guard would live, and what minimum acceptance shape it should have.

### R1. Pre-commit: add a secret-pattern hook (addresses F1, P0)

Add to `.pre-commit-config.yaml`:

- `pre-commit-hooks`: `check-added-large-files` (cap to e.g. 512 KB on staged-by-default), `check-private-key`, `forbid-new-submodules`.
- `gitleaks` (or `detect-secrets` baseline mode) as a local hook with a narrow allowlist for documented test fixtures.
- A repo-local hook that rejects staging of paths matching: `**/.env`, `**/.env.*` except `.env.example`, `**/secrets/**` except `secrets/README.md`, `**/*-vertex-key*.json`, `**/github-recovery-codes*.txt`, `**/pyarmor-*`.

Acceptance: a PR that stages a fake `dummy.env` or `fake-vertex-key.json` is rejected at commit time without needing the developer to remember.

Owner: T01 may want to write the allowlist; T09 owns the wiring.

### R2. CI: add a blocking secret-scan job mirroring R1 (addresses F1, P0)

Add a new job to `.github/workflows/test.yml` that runs on every PR and `push`:

- Same denylist patterns as R1, but applied to the full repo, not just staged files (catches contributors who don't run pre-commit).
- A grep-class scan for high-confidence credential signatures (PEM `BEGIN PRIVATE KEY`, `AKIA[0-9A-Z]{16}`, GitHub PAT prefix, GCP service-account JSON with `"private_key":`).
- Job must be **blocking** (no `|| true`, no `continue-on-error`).
- Job must run even if `secrets.GOOGLE_API_KEY` is unavailable (forks).

Acceptance: a PR that adds a credential file or pastes a key into a comment fails the required check.

### R3. Release pipeline: enforce a packaging denylist (addresses F2, F3, F4, P0/P1)

Two-layer enforcement:

- In `build/build_release.ps1` `Sync-EngineBundle`, after `Copy-BundleItem` is done, run a manifest scan of `dist/engine/` and **fail the build** if any of the following are present: `**/.env`, `**/.env.*`, `**/secrets/**`, `**/*-vertex-key*.json`, `**/github-recovery-codes*.txt`, `**/pyarmor-*`, `**/__pycache__/**`, `**/tests/**`, `**/_tmp_*.py`, `**/spikes/**`, `**/test_mode/**`. Equivalent scan for `dist/backend/` and `dist/workspace-seed/`.
- In `geuldobi-desktop/package.json` `extraResources` filter list and `files` list, add the corresponding `!**/...` exclusions so `electron-builder` strips them even if step 1 misses them.

Add a contract test to `tests/test_desktop_packaging_contract.py` asserting both lists contain those negative patterns. This converts F2 from "filter exists by convention" to "filter shape is locked by test".

### R4. Release pipeline: add a release manifest + SHA256 (addresses F5, P1)

Have `build/build_release.ps1` emit `dist/release-manifest.json` with: build commit, runtime contract id, file list with sha256, build timestamp, and a hash for the produced `Geuldobi-Setup-*.exe`. This is a precondition for any internal allowlist (#70 / T08) and for verifiable "this EXE is the one we built" assertions in incident response (#71 / T10).

Code signing is a separate decision (cost + cert ownership). The hash manifest is the cheap floor.

### R5. CI: run hygiene scripts on full tree on PR (addresses F8, P3)

Add a step that runs `python scripts/check_utf8_hygiene.py .` (or a documented subset) and `python scripts/ops_validator.py --strict` on every PR. Both already exit non-zero on failure, so wiring is mechanical.

### R6. Tighten ruff `extend-exclude` review (addresses F6, P2)

Either:

- Move `lite_mode`, `test_mode`, `spikes`, `tools`, `tools2` out of the production source tree (T07 owns the move), and then drop them from `extend-exclude` because they no longer exist in the lint root, or
- Keep them, but add a counter-test asserting that whatever is excluded from ruff is **also** excluded from release staging (R3 list). Do not let "lint-skipped" and "ship-included" overlap.

### R7. Document and publish CONTRIBUTING-style intake of these guardrails (cross-cuts F1–F8)

After R1–R6 land, T10 should reflect them in the security response doc map so external contributors and Codex agents see the contract before opening PRs. Not implemented under this wave.

## Dependencies On Other Terminals

- **T01** Root secret inventory — needed to write the concrete denylist for R1/R2/R3 without missing a real artifact and without listing nonexistent ones.
- **T02** Runtime config topology — needed to confirm that `config/settings.json` and `config/models.yaml` will survive R3's bundle-time scan (i.e., they must remain non-secret; if they hold secrets today, R3 will break the release until secrets are moved per #66).
- **T05** Windows settings paths — R3 should not strip files that the runtime depends on for non-secret config; the safe subset is determined by T05's approved Windows path policy.
- **T06** Release packaging — full inventory of staged inputs; R3's denylist must align with T06's allowlist of intentionally-staged content.
- **T07** Dev/test separation — R6 (ruff exclude vs ship include) needs T07's keep/move/drop classification. R3's denylist for `tests/`, `spikes/`, `_tmp_*.py`, `test_mode/`, `lite_mode/` must match T07's recommended layout.
- **T08** EXE access control — R4's release manifest is the cheap precondition for any allowlist or signed-token model T08 selects.
- **T10** Security response doc map — should aggregate which guardrails were added vs deferred and surface that to operators.

## Open Questions

1. Are there any GitHub branch-protection or required-status-check rules **outside the workflow file** (set via repo Settings → Rules) that already block secret patterns? T09 cannot see those from inside the working copy; T10 should confirm via the GitHub connector or repo admin.
2. Is `secrets/README.md` the only intentionally-tracked file under `secrets/`, or do other tracked files live there? The answer changes how aggressive the R1/R2 `secrets/**` denylist allowlist clause needs to be. Owned by T01; flagged here so R1's allowlist isn't drafted in a vacuum.
3. Does `lite_mode/` contain any keys, tokens, or test fixtures that would trip R3's denylist? T07 should answer before R3 lands.
4. Does the team plan to introduce code signing for the NSIS installer in the same wave as #70, or treat it as a separate decision? R4 (hash manifest) is independent and cheaper; R5 (signing) is separate.
5. Is `pre-commit` actually installed by every contributor's local environment, or only by some? If installation is inconsistent, R2 (CI mirror) is mandatory rather than nice-to-have.
6. Should `--no-verify` ever be acceptable for emergency commits? If yes, the policy needs to be documented; if no, branch protection should reject commits that lack hook signatures (a separate operational decision).

## Closure Recommendation

T09 is **complete as a read-only finding set** but **does not close issues #66 or #69**.

- For **#66**: T09's contribution is the guardrail layer (R1, R2, R3, R5). Issue closure also requires T01 (secret inventory + history scrub plan), T02 (runtime config rewrite), T03 (Vertex auth migration), and T05 (approved settings path). Do not close #66 on T09 evidence alone.
- For **#69**: T09's contribution is the release-time denylist (R3) and the lint/ship overlap fix (R6). T07 owns the dev/test separation policy itself. Do not close #69 on T09 evidence alone.

Recommended sequencing for the consolidated remediation roadmap (`docs/2026-04-27/security-remediation-roadmap.md`, per dispatch §7):

1. R1 + R2 first (cheap, blocks new bleeding, no architectural decisions needed).
2. T01 / T05 / T07 inputs gathered.
3. R3 + R6 land together (release denylist + lint/ship alignment).
4. R4 lands as precondition for #70 / T08 implementation.
5. R5 lands as ongoing CI hygiene.
6. R7 / T10 close the documentation loop.

No code, config, workflow, or git state was modified during this terminal's investigation.

## 3-Pass Audit (T09 self-check)

Pass 1 — structure and scope:

- PASS. Report follows the dispatch schema (Scope, Commands/Evidence, Findings, Remediation Candidates, Dependencies On Other Terminals, Open Questions, Closure Recommendation).
- PASS. Scope is bounded to CI / pre-commit / hygiene / release guardrails for issues #66 and #69. Other terminals' scopes are explicitly handed off, not annexed.
- PASS. Save path matches dispatch §5 row T09.

Pass 2 — evidence and consistency:

- PASS. All findings cite a concrete file path or grep result. No raw secret values appear; only path names, key names (`GOOGLE_API_KEY`), and pattern classes.
- PASS. Severities (`P0/P1/P2/P3`) match the dispatch rubric and are justified by the named failure mode.
- PASS. `.gitignore`, `.gitattributes`, ruff exclude list, and `extraResources` filter list are quoted or paraphrased without alteration.
- PASS. Findings about "no scanner exists" are bounded to the inspected files; the report acknowledges that branch-protection rules outside the working copy were not inspected (Open Question 1).

Pass 3 — execution and readability:

- PASS. Each remediation names where the guard lives, the acceptance shape, and which other terminal owns its inputs.
- PASS. Dependencies section is paired one-to-one with at least one terminal id, no orphan asks.
- PASS. Closure recommendation explicitly forbids closing #66 / #69 on T09 alone, matching dispatch §7's "no premature closure" rule.

Estimated operational confidence: 96%. Remaining 4% sits in Open Questions 1 and 2 (branch-protection visibility, exact `secrets/` tracked surface) where T09 cannot self-verify without T01 / repo-admin access.
