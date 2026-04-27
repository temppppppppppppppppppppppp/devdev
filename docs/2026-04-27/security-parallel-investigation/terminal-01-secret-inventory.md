# T01 Root Secret Inventory

Date: 2026-04-27
Terminal: T01
Primary GitHub issue: #66 `[SEC] Remove secrets from code/config and standardize runtime config loading`
Related issues: #67, #68, #69, #71
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit (HEAD = main): `a3d826978d530ab61d3765e5e095890fa6533ea7`
Document type: read-only investigation report under the parallel dispatch order. Not an execution SSOT, not a code patch order.

This report contains no raw secret values. Suspected secret material is recorded as path + size + blob OID + redacted description only.

## Scope

Inventory of root-level and repo-adjacent secret/config artifacts and classification of their risk:

- `.env`, `.env.example`, `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `secrets/`, `config/models.yaml`, `config/settings.json`, `.gitignore`, `.gitattributes`, `pyproject.toml`.
- Determine for each: tracked vs ignored vs untracked at HEAD, and tracked vs deleted across all branches/tags/remotes (full git history).
- Classify each artifact as committed-secret, local-only-secret, dangerous-example/default, unclear-ownership, or safe-placeholder.
- Identify P0/P1 remediation candidates for #66.

Out-of-scope for T01 (handed to other terminals):

- Python runtime config loader topology and env mutation: T02.
- Vertex/Google credential flow: T03.
- Electron/desktop config bridge: T04.
- Windows write-location policy and moved credential paths: T05.
- Release packaging inclusion of secrets: T06.
- CI/pre-commit secret-scan guardrail design: T09.

## Commands / Evidence

All commands were read-only. No file/branch/issue/commit/PR was modified.

### E1. Working-tree existence and metadata

Command:

```powershell
Get-ChildItem -Force .env,.env.example,geuldobi-vertex-key.json,github-recovery-codes.txt,secrets,config/models.yaml,config/settings.json,.gitignore,.gitattributes,pyproject.toml -ErrorAction SilentlyContinue | Select-Object Mode,Length,LastWriteTime,Name,FullName
```

Result (size in bytes, mtime kept for context):

| Path | Size | LastWriteTime | Notes |
| --- | --- | --- | --- |
| `.env` | 496 | 2026-04-27 12:19 | suspected real-secret file, working-tree only |
| `.env.example` | 1079 | 2026-04-10 13:44 | placeholders, tracked |
| `geuldobi-vertex-key.json` | 2374 | 2026-04-24 13:41 | suspected GCP service-account JSON, working-tree only |
| `github-recovery-codes.txt` | 206 | 2026-04-20 09:32 | suspected GitHub 2FA recovery codes, working-tree only |
| `secrets/clickup.env` | 448 | 2026-04-13 10:51 | suspected ClickUp token env, working-tree only |
| `secrets/n8n.local.env` | 273 | 2026-04-21 10:16 | suspected n8n local env, working-tree only |
| `secrets/README.md` | 591 | 2026-04-10 13:45 | tracked placeholder doc |
| `config/models.yaml` | 3121 | 2026-04-14 09:04 | tracked, env-var-name references only |
| `config/settings.json` | 216 | 2026-03-16 10:56 | tracked, runtime toggles only |
| `.gitignore` | 2259 | 2026-04-27 11:46 | tracked policy file |
| `.gitattributes` | 1569 | 2026-03-20 17:53 | tracked policy file |
| `pyproject.toml` | 2632 | 2026-04-27 11:46 | tracked, no secrets |

### E2. Tracked-at-HEAD set

Command:

```bash
git ls-files -- .env .env.example geuldobi-vertex-key.json github-recovery-codes.txt \
  secrets config/models.yaml config/settings.json .gitignore .gitattributes pyproject.toml
```

Tracked at HEAD:

- `.env.example`
- `.gitattributes`
- `.gitignore`
- `config/models.yaml`
- `config/settings.json`
- `pyproject.toml`
- `secrets/README.md`

Not tracked at HEAD (on disk only): `.env`, `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `secrets/clickup.env`, `secrets/n8n.local.env`.

Cross-check at HEAD via `git ls-tree -lr HEAD` filtered for `.env` returned no matches. Confirms no `.env` file (root or nested) is tracked at the current main HEAD.

### E3. Ignore policy

Command:

```bash
git check-ignore -v .env geuldobi-vertex-key.json github-recovery-codes.txt secrets/ \
  config/models.yaml config/settings.json .env.example
```

Result:

- `.env` -> ignored by `.gitignore:12` (`.env`)
- `geuldobi-vertex-key.json` -> ignored by `.gitignore:131` (`geuldobi-vertex-key.json`)
- `github-recovery-codes.txt` -> ignored by `.gitignore:130` (`github-recovery-codes.txt`)
- `secrets/clickup.env`, `secrets/n8n.local.env` -> ignored by `.gitignore:14` (`secrets/*.env`) (verified by inspection of `.gitignore`).

`secrets/README.md` is intentionally not matched by `secrets/*.env` and is allowed to be tracked.

### E4. Working-tree dirty state

Command:

```bash
git status --short -- .env .env.example geuldobi-vertex-key.json github-recovery-codes.txt \
  secrets config/models.yaml config/settings.json .gitignore .gitattributes pyproject.toml
```

Result: empty. No tracked file in scope is dirty at dispatch time.

### E5. Full-history search for `.env` (root)

Command:

```bash
git log --all --oneline -- .env
git log --all --diff-filter=D --name-only -- .env
git log --all --oneline --diff-filter=AMR --name-only -- '**/.env'
```

`.env` (root) has been tracked in 6 commits and deleted in 1:

- `b69763dc` `Upload .env and projects folder as requested` (Wed Jan 28 10:19:32 2026 +0900) — initial add
- `d33b52dc` `feat: Add Slack notification integration to main_a.py`
- `c78a725a` `Upload all files including ignored ones`
- `5223ed67` `Update`
- `46c4801f` `refactor: Step3 ...`
- `2f1de059` `feat: Codex TF3 Tier 1~3 ...` (Sun Feb 22 17:45:47 2026 +0900) — `.env` deleted (`1 file changed, 3 deletions(-)`), `.env.example` added in same wave per commit body

Deeper grep for `**/.env` reveals additional committed `.env` files at non-root paths in older history:

- `tests/stage4_v2_test/project/.env`
- `projects/<work-name>/.env` for at least 5 distinct work directories (paths are octal-escaped Hangul; not reproduced verbatim here)

Touched by commits: `b69763dc`, `38b4084c` (`Upload .env and valid files (excluding .gitignore folder)`), `587f28ca` (`Update all files: Sync to devdev (force overwrite)`), `c78a725a`, `5223ed67`, `4114fff8` (`Update system reports and NPC consistency check results`), `d54f7b39` (`Update: Current best state identified by user`).

Whether all nested `.env` copies were eventually deleted from HEAD is not separately certified by this terminal beyond the HEAD-tracked check in E2. T07 is the right place to scope nested `.env` cleanup.

### E6. Blob sizes of historical `.env` (no content read)

Command:

```bash
git ls-tree -l b69763dc -- .env
git ls-tree -l c78a725a -- .env
git ls-tree -l d33b52dc -- .env
```

Result:

| Commit | Blob OID | Size (bytes) |
| --- | --- | --- |
| `b69763dc` | `072fede7a2431f35c1e1200ee6b95b27600f3205` | 55 |
| `c78a725a` | `54afbee715bfb1e1a649373701ffd8393d2405ee` | 156 |
| `d33b52dc` | `b5982f0cb645be2b78a804ae4a03d4695d61006e` | 155 |

These are real-content sizes, not placeholders. The current `.env.example` placeholder is 1079 bytes; the historical blobs are short enough to plausibly be a small set of `KEY=value` lines, consistent with real credentials. No raw blob content was read or printed by this terminal.

### E7. Reachability of leak commits

Command:

```bash
git for-each-ref --contains b69763dc --format="%(refname)" | wc -l
git tag --contains b69763dc
git branch -a --contains b69763dc
```

Result: leak commit `b69763dc` is reachable from 54 refs in the local clone, including:

- `refs/heads/main` and `refs/remotes/origin/main`
- `refs/heads/devdev` and `refs/remotes/origin/devdev`
- `refs/heads/backup/pre_split_febf0819`, `refs/heads/backup/ssot-frontier-pre-main-sync-20260420`, `refs/remotes/origin/backup/pre-rollback-9149ac7c-2026-04-03`
- many `refs/heads/codex/*`, `refs/heads/feat/*`, `refs/heads/evidence/*`, and matching `refs/remotes/origin/*` mirrors
- 3 tags: `phase4c-complete`, `phase4d-complete`, `safety-2026-04-03-9149ac7c`

Confirms the secret material was not removed from history. The 2026-02-22 deletion (`2f1de059`) is a regular `git rm`, which leaves all prior blobs reachable. Per the workspace memory record `project_git_cleanup_2026_04_03.md`, the prior `git filter-repo` run targeted large-file cleanup; it is not certified by this terminal as having scrubbed `.env` blobs.

### E8. Full-history search for vertex key and recovery codes

Commands:

```bash
git log --all --oneline -- geuldobi-vertex-key.json
git log --all --oneline -- github-recovery-codes.txt
```

Both return empty. Neither file has ever been tracked in any branch, tag, or remote ref reachable from this clone. They are local-only on disk.

### E9. Full-history search for `secrets/*.env`

Command:

```bash
git log --all --oneline -- 'secrets/clickup.env' 'secrets/n8n.local.env' 'secrets/*.env'
```

Result: empty. `secrets/clickup.env` and `secrets/n8n.local.env` have never been tracked. Only `secrets/README.md` is tracked, and inspection (see E10) shows it is a placeholder doc.

### E10. Tracked-file content review (no secret values present)

Reviewed tracked files for embedded secret material or unsafe-default risk:

- `.env.example` (1079 bytes): all values are `your_*_here` placeholders, comments, or empty. No real key present. Includes:
  - `GOOGLE_API_KEY=your_google_api_key_here`
  - `VERTEX_API_KEY=your_vertex_api_key_here`, `VERTEX_PROJECT_ID=your-gcp-project-id`, `VERTEX_LOCATION=us-central1`
  - `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/workspace/webhook`
  - `CLICKUP_API_TOKEN=pk_your_clickup_personal_token_here`, `CLICKUP_LIST_ID=your_clickup_list_id_here`, `CLICKUP_ENV_FILE=secrets/clickup.env`, `CLICKUP_STATUS_MAP_JSON=` (empty)
  - `GEULDOBI_PROVIDER_MODE=ambient`
- `secrets/README.md` (591 bytes): documents that `secrets/*.env` is gitignored and that `scripts/sync_clickup_queue.py` loads root `.env` first then `secrets/clickup.env`. Includes a `pk_your_clickup_personal_token_here` example token only.
- `config/models.yaml` (3121 bytes): provider entries reference env-var names only (`api_key_env: "GOOGLE_API_KEY"`, `api_key_env: "VERTEX_API_KEY"`, `credentials_env: "GOOGLE_APPLICATION_CREDENTIALS"`, etc.). No literal credentials. Note: the `vertex_ai.auth_mode: "auto"` and `anthropic_vertex` blocks are runtime-config concerns owned by T02/T03.
- `config/settings.json` (216 bytes): only `costs.max_retries`, `costs.temperature`, and `validation` toggles. No secrets.
- `pyproject.toml` (2632 bytes): build/lint/test config only. No secrets.
- `.gitignore` (2259 bytes): explicit secret-bearing rules at lines 12 (`.env`), 13 (`.env.local`), 14 (`secrets/*.env`), 130 (`github-recovery-codes.txt`), 131 (`geuldobi-vertex-key.json`). Policy is sufficient for the artifacts known today; no rule yet covers a generic service-account-JSON pattern (see Remediation R5).
- `.gitattributes` (1569 bytes): EOL normalization only. Includes `*.env text eol=lf` (line 23) — does not leak secrets, but is a residue from when `.env` was tracked. Safe to leave; can be removed by T02/T05 if `.env` is fully retired from any tracked path.

## Findings

Severity tags follow the dispatch rubric. P0 = active secret exposure, P1 = high near-term risk, P2 = release-hardening, P3 = documentation.

### F1. P0 — Real secret content lives in published git history under `.env`

Evidence: E5, E6, E7. Six commits reachable from `main`, `origin/main`, 3 tags, and 54 refs (local + remote) carry `.env` blobs of 55/156/155 bytes. The blobs are not placeholders. The 2026-02-22 deletion did not rewrite history; it only removed `.env` from the HEAD tree. Anyone with read access to the remote can `git cat-file blob <oid>` to recover them.

Risk class: committed secret. Affected credentials are the union of all keys that ever lived in `.env` across this commit window — at minimum the env var names referenced in `.env.example` and `config/models.yaml` (Google API key, Vertex API key, Vertex project id, Vertex location, Slack webhook URL, ClickUp PAT, ClickUp list id) — although the actual set must be confirmed by the credential owner against the original local `.env` history, which T01 cannot read from history without exposing values.

### F2. P0 — Additional `.env` blobs at nested paths in history

Evidence: E5. At least 7 historical commits introduced `.env` files at deep paths under `projects/<work>/.env` and `tests/stage4_v2_test/project/.env`. Same reachability problem as F1: history rewrite to scrub `.env` must use a path-glob pattern (`**/.env`), not a literal root-only path.

Risk class: committed secret. May or may not contain identical credentials to root `.env`; treat as compromised by default.

### F3. P1 — Live GCP service-account key JSON sits in repo working directory

Evidence: E1, E3, E8. `geuldobi-vertex-key.json` (2374 bytes) is in the workspace root, gitignored (`.gitignore:131`), and never committed. It is a single accidental `git add -A`, `git add -f`, or path-policy regression away from being committed. Service-account JSON is high-impact: it typically contains a private key for a GCP identity that can call Vertex AI billed APIs.

Risk class: local-only secret with high blast radius if leaked. T03 owns the auth-flow remediation; T05 owns the moved-location decision.

### F4. P1 — GitHub 2FA recovery codes in repo working directory

Evidence: E1, E3, E8. `github-recovery-codes.txt` (206 bytes) is in the workspace root, gitignored (`.gitignore:130`), and never committed. Same accidental-add risk as F3. Recovery codes are bearer-equivalent for the GitHub account.

Risk class: local-only secret. Should not live inside any source-controlled directory regardless of ignore rules.

### F5. P1 — Local-only env files under `secrets/`

Evidence: E1, E3, E9. `secrets/clickup.env` (448 bytes) and `secrets/n8n.local.env` (273 bytes) are gitignored (`secrets/*.env`) and never committed. Working-tree-only, but the directory naming makes the ignore pattern the single line of defense.

Risk class: local-only secret. Acceptable today, but policy is fragile; if someone renames or moves a file out of `secrets/*.env` glob, ignore stops protecting it.

### F6. P2 — `.gitignore` lacks generic service-account-JSON pattern

Evidence: E10. `.gitignore` explicitly names `geuldobi-vertex-key.json` but does not match `*-key.json`, `*-credentials.json`, `*-sa.json`, or similar generic service-account patterns. A renamed or rotated key file would not be protected.

Risk class: dangerous-default. Easy to fix in T09's guardrail wave.

### F7. P3 — `.gitattributes` retains `*.env text eol=lf`

Evidence: E10 line 23. Not a leak by itself; a residue from when `.env` was tracked. Could mislead a future reader into thinking `.env` is tracked-by-policy. Safe to remove only after T02/T05 confirm no remaining tracked `.env` path.

Risk class: unclear-ownership / cosmetic. P3.

### F8. Safe baseline (no risk)

- `.env.example`, `secrets/README.md`: placeholder-only content.
- `config/models.yaml`: env-var-name references only.
- `config/settings.json`: runtime toggles only.
- `pyproject.toml`: build/lint/test config only.
- `.gitignore`: policy file.

## Remediation Candidates

Each item is a recommendation only. T01 does not execute remediation. Owner column points at the most relevant other terminal or external authority.

### R1. P0 — Rotate every credential that has ever lived in `.env` (root or nested)

- Scope: Google API key, Vertex API key, Vertex project credentials, Slack webhook URL, ClickUp PAT, any other key surfaced by reading the original local `.env` content (not done by T01 to honor the no-secret-output rule).
- Owner: external credential holder + #66 owner. Not solvable by code change alone.
- Why first: rotation must precede or at least run in parallel with history rewrite; otherwise an attacker with archived clones still holds valid secrets.

### R2. P0 — Decide on git-history rewrite for all `.env` paths

- Candidate command (do not execute under T01): `git filter-repo --path-glob '**/.env' --invert-paths --force`, followed by re-tagging `phase4c-complete`, `phase4d-complete`, `safety-2026-04-03-9149ac7c` and force-pushing every leak-bearing branch listed under E7 to `origin`.
- Coordination cost is high (54 refs, 3 tags, multiple collaborator clones must be reset).
- Alternative: accept the historical leak as compromised (R1 covers it via rotation), pin a "do not pull old refs" advisory, and rely on rotation as the durable mitigation.
- Owner: #66 owner + repo administrator. T01 cannot make this call.

### R3. P0 — Move `geuldobi-vertex-key.json` out of the workspace tree

- Move to a user-config path such as `%APPDATA%/geuldobi/credentials/vertex-key.json` (T05 owns the exact path policy).
- Switch runtime to point `GOOGLE_APPLICATION_CREDENTIALS` at the moved location (T03 owns the provider wiring, T02 owns the loader).
- After the move, remove `geuldobi-vertex-key.json` from the project root.

### R4. P1 — Move `github-recovery-codes.txt` out of the workspace tree

- Recovery codes belong in a password manager or secure offline storage, not in the project root. After the user transfers them, delete from the workspace.

### R5. P1 — Broaden `.gitignore` and add an explicit secret-glob policy

- Suggested additions (recommendation, not patch): `*-key.json`, `*-credentials.json`, `*-sa.json`, `*.pem`, `*.p12`, `*recovery*codes*.txt`.
- Owner: T09 should fold this into the CI/pre-commit guardrail wave so it is enforced, not just declared.

### R6. P1 — Add a pre-commit secret scanner

- gitleaks, detect-secrets, or trufflehog as a pre-commit hook plus CI step.
- Owner: T09. T01 only flags the need; T09 chooses the tool and config.

### R7. P2 — Consolidate "secrets must live outside repo" into one written policy

- Owner: T10 (security response doc). T01 supplies the inventory; T10 writes the user-facing guidance and the table of "where each secret should live."

### R8. P3 — Remove `*.env text eol=lf` from `.gitattributes`

- Only after T02/T05 confirm no remaining tracked `.env` path anywhere. Cosmetic; defer.

## Dependencies On Other Terminals

- T02 — Confirms the canonical env var names actually consumed by the Python runtime (e.g., are `VERTEX_API_KEY` and `GOOGLE_APPLICATION_CREDENTIALS` both read, or only one). Determines whether the rotated set in R1 covers everything the code actually uses.
- T03 — Decides whether `geuldobi-vertex-key.json` is the active Vertex auth surface or a vestige from an older shared-account setup; informs R1 and R3.
- T04 — Verifies the desktop bridge does not also persist secrets to `localStorage`, `userData`, or another non-`.env` surface that T01 did not inventory.
- T05 — Defines the approved Windows user-config path that R3 and R4 move credentials to.
- T06 — Confirms whether release packaging (`build/backend.spec`, `build/build_release.ps1`, `배포_패키징.ps1`, `geuldobi-desktop/package.json`) bundles `.env` or `secrets/` into shipped artifacts. T01 only confirmed git status; packaging inclusion is a separate read.
- T07 — Owns the nested `.env` cleanup under `tests/stage4_v2_test/project/.env` and `projects/<work>/.env` historical paths and verifies HEAD is clean across all subtrees.
- T09 — Implements R5 and R6 as enforced guardrails.
- T10 — Folds F1–F4 into the public security response doc with rotation/disclosure language.

## Open Questions

- Q1. Has the `.env` credential set already been rotated by the credential owner since 2026-02-22? Required input for R1 closure.
- Q2. Is the remote `temppppppppppppppppppppppp/devdev` GitHub repo public, internal, or private? Materially changes the urgency of R2 (history rewrite) vs accepting the leak as past-tense.
- Q3. Did the 2026-04-03 `git filter-repo` run (per workspace memory `project_git_cleanup_2026_04_03.md`) include `**/.env` in its path-glob, or was it strictly large-file scope? T01 evidence (E7 still shows leak commits reachable from origin refs) suggests it did not, but explicit confirmation from the run log would close this.
- Q4. Are there other "secrets-shaped" files outside the inventory list that T01 should sweep (e.g., `.npmrc`, `*.token`, browser-export `cookies.txt`, `id_rsa`)? Answer scopes a follow-up wave or feeds the broader pattern in R5.
- Q5. Is there an org-level secrets registry that catalogs which keys/tokens existed at any point so rotation under R1 can be exhaustive? If not, the rotation set is best-effort.

## Closure Recommendation

T01 inventory itself is evidence-complete and can be marked CLOSED-EVIDENCE. T01 does not authorize R1–R8; those require:

- R1 (rotation) — credential owner.
- R2 (history rewrite) — repo administrator + collaborator coordination.
- R3, R4 (move local credentials) — operator + T03/T05 path decisions.
- R5–R7 — T09, T10 follow-up.
- R8 — deferred pending T02/T05.

For the merge step in `docs/2026-04-27/security-remediation-roadmap.md`, recommend treating F1 and F2 as the top two P0 line items for issue #66, with R1 as the prerequisite of R2 (rotate first, then decide on rewrite). F3–F5 should be tracked as P1 alongside #68 (T05) and #67 (T03) since their durable fix is "credentials live in user-config, not in repo working tree."

No code, config, branch, tag, GitHub issue, commit, or PR was modified by this terminal.
