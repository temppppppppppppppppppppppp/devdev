# Security Issues Parallel Investigation Dispatch

Date: 2026-04-27
Status: final after 3-pass document audit
Workspace: `C:\Users\wjjo\Desktop\글도비`
Repository: `temppppppppppppppppppppppp/devdev`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Baseline dirty summary: no tracked dirty files were reported by `git status --short` at dispatch start.
Document type: read-only parallel investigation order, not an execution SSOT and not a source-code patch order.

## 1. Source Issues

| Issue | Priority | Title | Dispatch Role |
| --- | --- | --- | --- |
| [#66](https://github.com/temppppppppppppppppppppppp/devdev/issues/66) | P0 | `[SEC] Remove secrets from code/config and standardize runtime config loading` | Primary blocker. Dispatch first and split across secret inventory, runtime config topology, UI/config bridge, and CI guardrails. |
| [#67](https://github.com/temppppppppppppppppppppppp/devdev/issues/67) | P1 | `[SEC] Migrate Vertex AI authentication away from shared Barobook account` | High priority, coupled to #66. Needs provider/auth-flow evidence and possible docs-only closure path if GCP is already handled. |
| [#68](https://github.com/temppppppppppppppppppppppp/devdev/issues/68) | P1 | `[SEC] Move local app settings to approved user config directory` | High priority, coupled to #66. Needs runtime path, Windows path, config UI, and installer/write-location survey. |
| [#69](https://github.com/temppppppppppppppppppppppp/devdev/issues/69) | P2 | `[SEC] Separate test/dev scripts from production source tree` | Release-hardening work. Needs inventory and packaging exclusion plan. |
| [#70](https://github.com/temppppppppppppppppppppppp/devdev/issues/70) | P2 | `[SEC] Add executable access control for internal distribution` | Release-hardening work. Needs startup chokepoint and feasible internal authorization model. |
| [#71](https://github.com/temppppppppppppppppppppppp/devdev/issues/71) | P3 | `[DOCS] Document security response and current mitigation status` | Documentation aggregator. Should consume the investigation outputs before final response closure. |

## 2. Priority Reading

The practical urgency order is:

1. #66 P0 secrets/config standardization.
2. #68 P1 local settings path cleanup because it determines where non-secret runtime config can safely live.
3. #67 P1 Vertex AI auth because it may contain both secret-handling and account-governance risk.
4. #70 P2 executable access control because release gating design depends on the approved config/auth model.
5. #69 P2 dev/test separation because release build exclusion is important, but less urgent than credential exposure.
6. #71 P3 security response documentation after evidence exists.

If only some terminals are available, run T01-T06 first. With 10+ terminals, run all T01-T10 in parallel.

## 3. Evidence Basis For This Dispatch

Confirmed by GitHub connector:

- Issues #66-#71 are open and contain the priorities listed above.

Confirmed by local checkout inspection:

- Root contains `.env`, `.env.example`, `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, `secrets/`, `config/`, `build/`, `dist/`, `geuldobi-desktop/`, `modules/`, `scripts/`, `tests/`, `UI/`, `lite_mode/`, and `test_mode/`.
- `git ls-files` reports tracked release/config surfaces including `.env.example`, `config/models.yaml`, `config/settings.json`, `secrets/README.md`, `build/backend.spec`, `build/build_release.ps1`, `geuldobi-desktop/package.json`, and `배포_패키징.ps1`.
- Provider/config surfaces include `modules/core/config_manager.py`, `modules/core/google_client_factory.py`, `modules/core/models_config.py`, `modules/core/runtime_paths.py`, `modules/core/llm_provider.py`, `modules/core/llm_router.py`, `modules/core/providers/anthropic_vertex_provider.py`, `modules/core/providers/gemini_provider.py`, and `modules/core/providers/vertex_provider.py`.
- Desktop/build surfaces include `geuldobi-desktop/main.js`, `geuldobi-desktop/preload.js`, `geuldobi-desktop/src/`, `build/backend_entry.py`, `build/backend.spec`, `build/build_release.ps1`, and `.github/workflows/test.yml`.
- `rg` was unavailable in this Codex app session because the bundled `rg.exe` launch was denied by WindowsApps permissions. Future investigators may use `git grep`, PowerShell `Select-String -List`, or another safe scanner.

Security handling constraint:

- Do not paste secret values into reports.
- If a file contains a suspected secret, record only path, key name if safe, redacted prefix class, and risk category.
- Do not modify source code in this wave.

## 4. Global Rules For All Terminals

All terminals must follow these rules:

- Read `AGENTS.md` first enough to respect system-track, UTF-8, and Python-judgment limits.
- Treat this as read-only investigation. Do not edit production code, config, `.env`, GitHub issues, commits, branches, or PRs.
- The only allowed write is the assigned report path under `docs/2026-04-27/security-parallel-investigation/`.
- Use UTF-8 for the report.
- Do not print or save raw secret values, credential JSON private keys, recovery codes, tokens, or API keys.
- If using scanners, prefer path-only or redacted output.
- Include exact file paths and line numbers only when the line does not expose secret material. If line text exposes a secret, record the path and a redacted description instead.
- Mark findings as `P0`, `P1`, `P2`, or `P3` according to likely security impact.
- Separate evidence from recommendation. Python or shell may collect data; final risk judgment belongs to the LLM investigator.
- If a report needs another terminal's area, note the dependency instead of widening into a conflicting survey.

Required report schema:

```md
# TXX Report Title

## Scope

## Commands / Evidence

## Findings

## Remediation Candidates

## Dependencies On Other Terminals

## Open Questions

## Closure Recommendation
```

## 5. Terminal Dispatch Matrix

| Terminal | Primary Issue(s) | Focus | Save Path |
| --- | --- | --- | --- |
| T01 | #66 | Root secrets and tracked/ignored secret inventory | `docs/2026-04-27/security-parallel-investigation/terminal-01-secret-inventory.md` |
| T02 | #66, #68 | Python runtime config loading topology | `docs/2026-04-27/security-parallel-investigation/terminal-02-runtime-config-topology.md` |
| T03 | #67, #66 | Vertex AI and Google auth flow | `docs/2026-04-27/security-parallel-investigation/terminal-03-vertex-auth-flow.md` |
| T04 | #66, #68, #70 | Desktop/Electron config and settings surfaces | `docs/2026-04-27/security-parallel-investigation/terminal-04-desktop-config-surfaces.md` |
| T05 | #68, #66 | Windows settings path and write-location policy | `docs/2026-04-27/security-parallel-investigation/terminal-05-windows-settings-paths.md` |
| T06 | #69, #70, #66 | Release packaging and included/excluded files | `docs/2026-04-27/security-parallel-investigation/terminal-06-release-packaging.md` |
| T07 | #69 | Test/dev/temp artifact separation | `docs/2026-04-27/security-parallel-investigation/terminal-07-dev-test-separation.md` |
| T08 | #70, #68 | EXE access-control chokepoints and feasible design | `docs/2026-04-27/security-parallel-investigation/terminal-08-exe-access-control.md` |
| T09 | #66, #69 | CI/pre-commit/release guardrails for secrets and packaging | `docs/2026-04-27/security-parallel-investigation/terminal-09-ci-release-guardrails.md` |
| T10 | #71 | Security response documentation and mitigation status map | `docs/2026-04-27/security-parallel-investigation/terminal-10-security-response-doc-map.md` |

## 6. Copy-Paste Prompts

### Prompt T01

```text
You are Terminal T01 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issue: #66 [SEC] Remove secrets from code/config and standardize runtime config loading
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-01-secret-inventory.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- This is read-only investigation. Do not edit source/config/env/GitHub/git state.
- Do not print or save raw secret values. Redact all tokens, private keys, recovery codes, API keys, and credential JSON fields.
- Write only the assigned report path, in UTF-8.

Scope:
- Inventory root and repo-adjacent secret/config artifacts: .env, .env.example, geuldobi-vertex-key.json, github-recovery-codes.txt, secrets/, config/models.yaml, config/settings.json, .gitignore, .gitattributes, pyproject.toml.
- Determine which of those files are tracked, ignored, or untracked.
- Classify risk: committed secret, local-only secret, dangerous example/default, unclear ownership, safe placeholder.
- Identify immediate P0/P1 remediation candidates for #66.

Suggested safe commands:
- git status --short -- .env .env.example geuldobi-vertex-key.json github-recovery-codes.txt secrets config/models.yaml config/settings.json .gitignore .gitattributes pyproject.toml
- git ls-files -- .env .env.example geuldobi-vertex-key.json github-recovery-codes.txt secrets config/models.yaml config/settings.json .gitignore .gitattributes pyproject.toml
- Get-ChildItem -Force .env,.env.example,geuldobi-vertex-key.json,github-recovery-codes.txt,secrets -ErrorAction SilentlyContinue
- Use redacted byte/hash checks if needed; never paste secret contents.

Report schema:
# T01 Root Secret Inventory
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T02

```text
You are Terminal T02 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issues: #66 and #68
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-02-runtime-config-topology.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not edit code/config/GitHub/git state.
- Do not expose secret values.
- Write only the assigned report path, in UTF-8.

Scope:
- Map Python runtime config loading and settings ownership.
- Inspect at minimum: main_a.py, modules/core/config_manager.py, modules/core/models_config.py, modules/core/runtime_paths.py, modules/core/llm_provider.py, modules/core/llm_router.py, modules/core/provider_mode.py, config/models.yaml, config/settings.json.
- Find where config is loaded, merged, defaulted, mutated, or passed into providers.
- Specifically check for .env loading/mutation, arbitrary path reads, secret-vs-non-secret conflation, and undocumented fallback order.

Suggested safe commands:
- git grep -n -i -E "dotenv|load_dotenv|\\.env|settings|config|models.yaml|runtime_paths|APPDATA|LOCALAPPDATA|Program Files" -- main_a.py modules/core config || true
- If git grep is slow, use PowerShell Select-String on the exact files above.

Report schema:
# T02 Runtime Config Loading Topology
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T03

```text
You are Terminal T03 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issue: #67 [SEC] Migrate Vertex AI authentication away from shared Barobook account
Related issue: #66
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-03-vertex-auth-flow.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not edit code/config/GitHub/git state.
- Do not expose service-account JSON, private keys, project secrets, or tokens.
- Write only the assigned report path, in UTF-8.

Scope:
- Map Vertex/GCP auth flow and provider usage.
- Inspect at minimum: modules/core/google_client_factory.py, modules/core/providers/vertex_provider.py, modules/core/providers/anthropic_vertex_provider.py, modules/core/providers/gemini_provider.py, modules/core/models_config.py, config/models.yaml, scripts/probe_claude_vertex_matrix.py, any docs mentioning Vertex/GCP/Barobook.
- Determine whether a shared Barobook/common account is hardcoded, documented, assumed by env var, or only an external operational concern.
- Identify if this can be implementation work, documentation-only closure, or both.

Suggested safe commands:
- git grep -n -i -E "vertex|gcp|google_application_credentials|service_account|credentials|project_id|location|barobook|바로북" -- modules config scripts docs README.md || true
- For sensitive matches, record path and redacted description only.

Report schema:
# T03 Vertex AI Authentication Flow
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T04

```text
You are Terminal T04 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issues: #66, #68, #70
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-04-desktop-config-surfaces.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not edit code/config/GitHub/git state.
- Do not expose secret values.
- Write only the assigned report path, in UTF-8.

Scope:
- Inspect Electron/desktop config and settings bridge surfaces.
- Inspect at minimum: geuldobi-desktop/main.js, geuldobi-desktop/preload.js, geuldobi-desktop/src/main.js, geuldobi-desktop/src/preload.js, geuldobi-desktop/src/desktop_bridge_client.js, geuldobi-desktop/src/desktop_control_plane_contract.js, geuldobi-desktop/src/*state*, geuldobi-desktop/package.json.
- Identify any settings UI, IPC, localStorage, file read/write, backend bridge, or config exposure path that could leak or mutate secrets/config.
- Note possible startup chokepoints useful for #70, but leave full access-control design to T08.

Suggested safe commands:
- git grep -n -i -E "config|settings|env|token|secret|auth|license|allowlist|localStorage|ipc|appData|userData|path" -- geuldobi-desktop || true

Report schema:
# T04 Desktop Config Surfaces
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T05

```text
You are Terminal T05 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issue: #68 [SEC] Move local app settings to approved user config directory
Related issue: #66
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-05-windows-settings-paths.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not edit code/config/GitHub/git state.
- Do not expose secret values.
- Write only the assigned report path, in UTF-8.

Scope:
- Survey Windows local settings paths and write-location behavior.
- Inspect at minimum: modules/core/runtime_paths.py, modules/core/config_manager.py, main_a.py, build/backend_entry.py, build/build_release.ps1, 배포_패키징.ps1, geuldobi-desktop/main.js, geuldobi-desktop/package.json.
- Find writes/reads involving .env, cwd-relative settings, APPDATA, LOCALAPPDATA, Program Files, userData, install directory, build/dist directory, or arbitrary user-supplied paths.
- Recommend a single approved Windows path policy, likely %APPDATA%/글도비/ for user settings and a separate secret mechanism for credentials.

Suggested safe commands:
- git grep -n -i -E "APPDATA|LOCALAPPDATA|Program Files|\\.env|settings|config|write_text|open\\(|mkdir|userData|app.getPath|cwd|Path.home|expanduser" -- main_a.py modules build geuldobi-desktop *.ps1 || true

Report schema:
# T05 Windows Settings Path Survey
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T06

```text
You are Terminal T06 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issues: #69, #70, #66
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-06-release-packaging.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not edit code/config/GitHub/git state.
- Do not expose secret values.
- Write only the assigned report path, in UTF-8.

Scope:
- Inspect release packaging and distribution inclusion/exclusion rules.
- Inspect at minimum: build/backend.spec, build/engine.spec if present, build/engine.patched.spec if present, build/build_release.ps1, build/prepare_python_embed.ps1, 배포_패키징.ps1, geuldobi-desktop/package.json, geuldobi-desktop/scripts/build_workspace_seed.py, dist/ shape by filenames only.
- Determine whether tests, scripts/dev, docs/temp, archive, .env, secrets, credential files, pyarmor reg files, local build logs, or root residues can be bundled into release artifacts.
- Identify where EXE access-control hook would enter packaging/startup, but leave final design to T08.

Suggested safe commands:
- Get-ChildItem -Force build,dist,geuldobi-desktop -ErrorAction SilentlyContinue
- git grep -n -i -E "datas|exclude|include|hiddenimport|pyinstaller|nuitka|dist|build|secrets|\\.env|tests|scripts|archive|docs/temp|pyarmor|license" -- build geuldobi-desktop *.ps1 || true

Report schema:
# T06 Release Packaging Survey
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T07

```text
You are Terminal T07 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issue: #69 [SEC] Separate test/dev scripts from production source tree
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-07-dev-test-separation.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not move files or edit code/config/GitHub/git state.
- Do not expose secret values if found incidentally.
- Write only the assigned report path, in UTF-8.

Scope:
- Inventory dev/test/temp/experimental files that are mixed into production-adjacent paths.
- Inspect root files, scripts/, tests/, lite_mode/, test_mode/, spikes/, tools/, tools2/, docs/archive/, docs/temp/, .github/workflows/test.yml.
- Classify items into keep production, move to tests, move to scripts/dev, move to docs/archive, ignore/build-exclude, or needs owner decision.
- Pay special attention to root residue files, scripts/_tmp*.py, smoke/canary scripts, and release inclusion risk.

Suggested safe commands:
- git ls-files | Select-String -Pattern "(^|/)(test|tests|spikes|archive|tmp|_tmp|smoke|canary|dev|debug)"
- Get-ChildItem -Force | Where-Object { $_.Name -match "tmp|test|smoke|debug|recovery|key|env" }

Report schema:
# T07 Dev/Test Separation Inventory
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T08

```text
You are Terminal T08 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issue: #70 [SEC] Add executable access control for internal distribution
Related issue: #68
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-08-exe-access-control.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not edit code/config/GitHub/git state.
- Do not design by hardcoding secrets into code. Do not expose secret values.
- Write only the assigned report path, in UTF-8.

Scope:
- Identify runtime startup chokepoints where EXE access control could be enforced.
- Inspect at minimum: build/backend_entry.py, main_a.py, modules/api/bridge_server.py, modules/api/process_runner.py, modules/api/control_plane_contract.py, modules/core/runtime_paths.py, geuldobi-desktop/main.js, geuldobi-desktop/preload.js, geuldobi-desktop/src/main.js.
- Propose 2-3 feasible internal distribution authorization models, with tradeoffs:
  - internal account login,
  - allowlisted user identity,
  - signed license/token,
  - machine/user-bound token,
  - online verification vs offline fallback.
- Identify minimal "unauthorized copied EXE does not run normally" implementation path and where config/secrets should live.

Suggested safe commands:
- git grep -n -i -E "main\\(|if __name__|startup|bridge|process_runner|auth|login|license|token|allowlist|machine|user|app.whenReady|BrowserWindow" -- main_a.py build modules geuldobi-desktop || true

Report schema:
# T08 EXE Access-Control Chokepoints
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T09

```text
You are Terminal T09 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issues: #66 and #69
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-09-ci-release-guardrails.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and security handling rules.
- Read-only investigation only. Do not edit workflows/config/GitHub/git state.
- Do not expose secret values.
- Write only the assigned report path, in UTF-8.

Scope:
- Survey current CI, pre-commit, hygiene, and release guardrails relevant to secrets and dev/test packaging.
- Inspect at minimum: .github/workflows/test.yml, .pre-commit-config.yaml, scripts/check_utf8_hygiene.py, scripts/ops_validator.py, pyproject.toml, build/build_release.ps1, geuldobi-desktop/package.json.
- Determine whether any automated guard currently prevents committing secrets, bundling .env/secrets, shipping tests/dev/temp files, or writing to Program Files.
- Recommend guardrail additions, but do not implement them.

Suggested safe commands:
- git grep -n -i -E "secret|credential|env|pre-commit|pytest|ruff|exclude|build|dist|release|hygiene|validate|test" -- .github .pre-commit-config.yaml pyproject.toml scripts build geuldobi-desktop/package.json || true

Report schema:
# T09 CI And Release Guardrails
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

### Prompt T10

```text
You are Terminal T10 for the 글도비 security parallel investigation.

Workspace: C:\Users\wjjo\Desktop\글도비
Primary GitHub issue: #71 [DOCS] Document security response and current mitigation status
Related issues: #66, #67, #68, #69, #70
Save your report to: docs/2026-04-27/security-parallel-investigation/terminal-10-security-response-doc-map.md

Rules:
- Read AGENTS.md first enough to follow system-track, UTF-8, and document rules.
- Read-only investigation only. Do not edit source/GitHub/git state.
- You may read terminal reports T01-T09 if they already exist, but do not wait indefinitely for them.
- Do not expose secret values.
- Write only the assigned report path, in UTF-8.

Scope:
- Create a security-response documentation map for issues #66-#71.
- Identify the final canonical doc that should eventually summarize security feedback, current mitigation status, decisions, owners, evidence, and residual risk.
- Search existing docs for related security/config/auth/release notes so the final response doc does not duplicate stale or conflicting material.
- If T01-T09 reports are absent, create a "pending evidence" status matrix.
- If any T01-T09 reports are present, summarize their status without claiming closure.

Suggested safe commands:
- Get-ChildItem docs/2026-04-27/security-parallel-investigation -Force -ErrorAction SilentlyContinue
- git grep -n -i -E "security|secret|credential|vertex|gcp|appdata|program files|release|packaging|license|access control" -- docs README.md AGENTS.md .github build geuldobi-desktop modules config || true

Report schema:
# T10 Security Response Documentation Map
## Scope
## Commands / Evidence
## Findings
## Remediation Candidates
## Dependencies On Other Terminals
## Open Questions
## Closure Recommendation
```

## 7. Merge Plan After Terminal Reports

After T01-T10 complete:

1. Collect the ten reports from `docs/2026-04-27/security-parallel-investigation/`.
2. Build a consolidated security remediation roadmap in `docs/2026-04-27/security-remediation-roadmap.md`.
3. Convert only implementation-ready items into execution SSOTs if needed.
4. If execution SSOTs are created, save canonical dated docs first and only then mirror to `docs/temp/`.
5. Do not start implementation until the consolidated roadmap or relevant execution SSOT passes the document 3-pass audit with at least 95% confidence.

## 8. 3-Pass Document Audit

Pass 1 - structure and scope:

- PASS. This document is a dispatch/order document, not an execution SSOT.
- PASS. Source issues, priority ordering, evidence basis, global rules, terminal matrix, prompts, and merge plan are explicit.
- PASS. Save paths are under dated docs and each terminal has a unique report path.

Pass 2 - evidence and consistency:

- PASS. Issue priorities match the fetched GitHub issue bodies.
- PASS. Baseline commit and dirty summary are recorded.
- PASS. Local path evidence is bounded to inspected checkout surfaces and does not claim full remediation.
- PASS. The document does not include raw secret values.

Pass 3 - execution and readability:

- PASS. Ten prompts are copy-paste ready and each has scope, rules, commands, and report schema.
- PASS. Parallel write conflicts are avoided by unique report files.
- PASS. Follow-up merge behavior is clear and prevents premature implementation.

Estimated operational confidence: 96%.

