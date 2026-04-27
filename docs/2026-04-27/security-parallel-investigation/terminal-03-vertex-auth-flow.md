# T03 Vertex AI Authentication Flow

Date: 2026-04-27
Terminal: T03 (read-only investigation)
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Primary GitHub issue: #67 `[SEC] Migrate Vertex AI authentication away from shared Barobook account`
Related issue: #66
Document type: read-only investigation report, not an execution SSOT and not a source-code patch order.
Save path: `docs/2026-04-27/security-parallel-investigation/terminal-03-vertex-auth-flow.md`

## Scope

T03 maps how this codebase authenticates to Vertex AI and to Claude-on-Vertex, and decides whether issue #67 (shared Barobook account migration) is a code problem, a documentation/operations problem, or both.

In-scope surfaces actually inspected:

- `modules/core/google_client_factory.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_vertex_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/provider_mode.py`
- `modules/core/models_config.py`
- `modules/core/llm_router.py` (provider-config defaults)
- `modules/api/process_runner.py` (UI→backend env passthrough; lines 90–115 and 870–908)
- `config/models.yaml`
- `.env.example`
- `secrets/README.md`
- `scripts/probe_claude_vertex_matrix.py`
- `README.md` (env-var documentation, lines 100–128)
- `docs/제안서_0318/이전 자료.md` (sole repo doc that names the shared `barobook001@gmail.com` account)
- `docs/poc/vertex_ai_migration.md` (Vertex transition rationale, 2026-03-03)
- `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md` (already-applied prep patch around `GEULDOBI_VERTEX_AUTH_MODE`)
- `docs/2026-04-27/gcp-iam-5arc-cleanrun-prerun-baseline.json` (env presence baseline)
- `docs/2026-04-19/survey/T10-security-ops.md` (P0-1 .env plaintext key context)
- `docs/2026-04-06/5arc-terminal1-provider-env-guard-survey.md` (auth-mode prior survey)
- `docs/2026-04-24/repo-trashbox-cleanup-adversarial-3pass-audit.md` (vertex key gitignore decision)

Explicit out-of-scope (handed to other terminals):

- Root secret inventory, `.env` plaintext keys, `geuldobi-vertex-key.json` body inspection → T01.
- Runtime config loading topology and `.env` mutation semantics → T02.
- Desktop/Electron settings UI bridging Vertex envs → T04.
- Windows path policy for credential JSON write/read locations → T05.
- Bundling `geuldobi-vertex-key.json` / `.env` into release artifacts → T06.
- CI/pre-commit guards for service-account JSON or key strings → T09.
- Final security response doc summary → T10.

## Commands / Evidence

All commands were read-only. No raw secret values, JSON private keys, recovery codes, tokens, or API keys are reproduced below; only paths, env-var names, redacted descriptions, and behavioural facts.

### E1. Vertex auth code paths (two parallel implementations)

`modules/core/google_client_factory.py:86–132` defines `build_google_genai_client(...)`:

- Reads `_raw_provider_config("vertex_ai")` from `config/models.yaml`.
- Reads `GEULDOBI_VERTEX_AUTH_MODE` env (`google_client_factory.py:65–67`); falls back to `auth_mode` from config; default literal `"api_key"` if neither is set.
- Auth mode `"api_key"` → `genai.Client(vertexai=True, api_key=<VERTEX_API_KEY>)`.
- Auth mode `"project_credentials"` → reads `VERTEX_PROJECT_ID|VERTEX_LOCATION` (or `GOOGLE_CLOUD_PROJECT|GOOGLE_CLOUD_LOCATION`) and optionally `GOOGLE_APPLICATION_CREDENTIALS` via `google.auth.load_credentials_from_file(..., scopes=["https://www.googleapis.com/auth/cloud-platform"])`.
- Auth mode `"auto"` → resolves to `api_key` if `VERTEX_API_KEY` is present, else `project_credentials` (`google_client_factory.py:96–97`).

`modules/core/providers/vertex_provider.py:11–114` defines `VertexAIProvider` with the same three modes, the same env-var contract, and the same `_AUTH_MODES = {"api_key", "project_credentials", "auto"}`. `_resolve_auth_mode()` at `vertex_provider.py:62–73` reads `GEULDOBI_VERTEX_AUTH_MODE` first, then constructor `auth_mode`. Constructor default is `"api_key"` (`vertex_provider.py:23`).

Two implementations exist because `google_client_factory` is the SSOT for ad-hoc Google client creation (e.g., visual lab, probe scripts) and `VertexAIProvider` is the LLM-router-managed runtime path. The auth contracts are aligned but duplicated; that is itself a maintenance risk.

### E2. Claude-on-Vertex path is project-credentials only

`modules/core/providers/anthropic_vertex_provider.py:41–63`:

- Reads `VERTEX_PROJECT_ID` (or `GOOGLE_CLOUD_PROJECT`) and `VERTEX_LOCATION` (or `GOOGLE_CLOUD_LOCATION`), default region `"us-east5"`.
- Calls `from anthropic import AnthropicVertex` and `AnthropicVertex(project_id=..., region=...)`.
- No `api_key` branch exists; the official `anthropic[vertex]` SDK delegates to Application Default Credentials (ADC).

This means Claude-on-Vertex traffic is **structurally bound to GCP project identity**, not to a Vertex API key. Any Claude routing through Vertex is bound to whichever GCP project `VERTEX_PROJECT_ID` points to.

### E3. Provider-config defaults and `auth_mode: "auto"` default

`config/models.yaml:15–34`:

```yaml
vertex_ai:
  enabled: true
  sdk: "google-genai"
  auth_mode: "auto"
  api_key_env: "VERTEX_API_KEY"
  project_id_env: "VERTEX_PROJECT_ID"
  location_env: "VERTEX_LOCATION"
  credentials_env: "GOOGLE_APPLICATION_CREDENTIALS"
anthropic_vertex:
  enabled: false
  sdk: "anthropic"
  project_id_env: "VERTEX_PROJECT_ID"
  location_env: "VERTEX_LOCATION"
```

`auth_mode: "auto"` is the live default. Combined with the resolver in `google_client_factory.py:96–97` and `vertex_provider.py:69–73`, presence of `VERTEX_API_KEY` silently selects the api_key path unless the operator explicitly sets `GEULDOBI_VERTEX_AUTH_MODE=project_credentials`.

`modules/core/llm_router.py:18–37` confirms the same env contract at the router defaults layer (`api_key_env: "VERTEX_API_KEY"`, `project_id_env: "VERTEX_PROJECT_ID"`, `location_env: "VERTEX_LOCATION"`, `credentials_env: "GOOGLE_APPLICATION_CREDENTIALS"`).

### E4. Recent prep patch

`docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md:23–27`:

> A previous run attempt on `projects/0000_골든카나리아` was stopped before accepting it as proof because logs showed Vertex API-key auth could override project/location credentials. … `VertexAIProvider` now lets `GEULDOBI_VERTEX_AUTH_MODE` override provider config `auth_mode`. With `GEULDOBI_VERTEX_AUTH_MODE=project_credentials`, `VERTEX_API_KEY` no longer silently wins when provider config is `auth_mode: auto`.

Cross-checked against the live source: the override is present in both `vertex_provider.py:62–73` and `google_client_factory.py:65–67`. The override exists, but the **default** behaviour without setting that env still routes through api_key when `VERTEX_API_KEY` is set, because `config/models.yaml` ships `auth_mode: "auto"` and `_AUTH_MODES` still accepts `"auto"`.

### E5. No `barobook` / `바로북` string appears in source code

`grep -i 'barobook|바로북'` across the workspace (excluding archived `docs/이전/` and the historical 제안서 doc) returns zero hits in `modules/`, `scripts/`, `geuldobi-desktop/`, `config/`, `tests/`, `build/`, `UI/`, `lite_mode/`, `test_mode/`, `main_a.py`, `README.md`. The only meaningful hit is:

- `docs/제안서_0318/이전 자료.md:103` — `구글 vertex 및 claude, openAi 사용 ID : barobook001@gmail.com (소설사업부 공용 ID)`.

That is a Korean budget-approval document, not runtime code. The shared-account fact lives **outside the codebase**, in operator/billing reality.

### E6. Local on-disk credential file (path-only, body NOT read)

- `git ls-files -- geuldobi-vertex-key.json` → empty (not tracked).
- `git check-ignore -v geuldobi-vertex-key.json` → `.gitignore:131:geuldobi-vertex-key.json`.
- `git ls-files --others --ignored --exclude-standard` confirms the file present but ignored.
- Stat shows the file exists at workspace root (size ~2.4 KB, mtime 2026-04-24). Body NOT read by T03 to avoid handling service-account JSON content.
- `docs/2026-04-24/repo-trashbox-cleanup-adversarial-3pass-audit.md:75` corroborates: `geuldobi-vertex-key.json is already excluded locally and has also been added to .gitignore`.

T03 cannot determine from path-only evidence whether this key file was issued under the shared `barobook001@gmail.com` GCP project or under a separate per-user/per-machine project. That requires operator confirmation against the GCP console.

### E7. Probe script and `.env` mutation

`scripts/probe_claude_vertex_matrix.py:67–80` (`load_dotenv_file`) mutates `os.environ` directly from `.env` text. It is the only Vertex-auth-relevant script in this T03 scope that loads the `.env` for the probe. Visual-lab cover/illustration scripts and `scripts/run_gold_manuscript_benchmark.py`, `scripts/gemini_cover_title_edit.py` read `VERTEX_PROJECT_ID|GOOGLE_CLOUD_PROJECT` directly without an api_key fallback — those paths can only authenticate via ADC/credentials JSON.

### E8. Desktop/UI passthrough of Vertex env vars

`modules/api/process_runner.py:886–896` (under `provider_mode in {ambient, vertex_ai}`):

```python
for env_key, input_key in (
    ("VERTEX_API_KEY", "vertex_api_key"),
    ("VERTEX_PROJECT_ID", "vertex_project_id"),
    ("VERTEX_LOCATION", "vertex_location"),
    ("GOOGLE_APPLICATION_CREDENTIALS", "google_credentials_path"),
):
    value = inputs.get(input_key)
    if value:
        env[env_key] = str(value)
```

Tests `tests/test_process_runner.py:253–327` exercise this exact passthrough. The desktop/UI is therefore the runtime-config bridge that decides which user/account credentials reach the backend; per-user migration cannot be a code-only change because the UI surface controls the inputs (referred to T04).

### E9. README and `.env.example` nudge toward `VERTEX_API_KEY` first

- `.env.example:9–11` — `VERTEX_API_KEY=...`, `VERTEX_PROJECT_ID=your-gcp-project-id`, `VERTEX_LOCATION=us-central1`. Comment at `.env.example:8` reads `Vertex AI (used when GEULDOBI_PROVIDER_MODE=vertex_ai, or ambient + models.yaml points to vertex)`.
- `README.md:122–126` — lists `VERTEX_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS` as multi-provider envs.

A new operator copying `.env.example` and pasting a `VERTEX_API_KEY` (e.g., the shared barobook key) will end up on the api_key path under the current `auth_mode: "auto"` default, with no per-user identity binding.

### E10. Pre-existing 2026-04-06 finding on `api_key` mode and pool isolation

`docs/2026-04-06/5arc-terminal1-provider-env-guard-survey.md:74–77, 137, 160`:

> `api_key` 모드에서는 `VERTEX_PROJECT_ID`, `VERTEX_LOCATION` env 변수가 client 생성에 사용되지 않는다. … `project_credentials` 모드로 전환하면 `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` 를 통해 명시적 pool 분리가 가능하지만, 현재 운영에서 사용하지 않는다.

This was already known internally one month before #67. The api_key path bypasses project/location pool isolation entirely; only `project_credentials` carries per-project identity into the request.

## Findings

### F1 (P1) — `auth_mode: "auto"` default makes api_key the default identity surface, which is exactly the shared-account vector

**Evidence:** E3, E4, E10. Default `config/models.yaml:18` ships `auth_mode: "auto"`. Resolver picks api_key when `VERTEX_API_KEY` is present (`google_client_factory.py:96–97`, `vertex_provider.py:69–73`). The api_key path does not bind to GCP project identity (E10).

**Why this is the #67 root cause inside the codebase:**

- If the operator pastes the shared `barobook001@gmail.com`-issued `VERTEX_API_KEY` into `.env`, every Vertex call goes through that single identity regardless of which user is generating content.
- The recently added `GEULDOBI_VERTEX_AUTH_MODE` override (E4) is opt-in; absent that env, behaviour is unchanged.
- The fix the operator applied during prep (set `GEULDOBI_VERTEX_AUTH_MODE=project_credentials`) is fragile because it relies on every operator/script remembering to set it.

**Severity:** P1. Aligned with the issue priority.

### F2 (P2) — Two parallel auth implementations duplicate the api_key-bypass risk

**Evidence:** E1. `google_client_factory.build_google_genai_client` and `VertexAIProvider._resolve_auth_mode/_get_client` re-implement the same auth contract independently. Behaviour is currently aligned (E4 verified both gained the override at the same time), but any future tightening (e.g., dropping `"auto"`) must be applied in both files.

**Severity:** P2. Maintenance risk, not a live exploit.

### F3 (P1) — Claude-on-Vertex is structurally project-credentials-only, so the migration is asymmetric

**Evidence:** E2. `AnthropicVertexProvider` has no api_key path. `anthropic_vertex` is currently `enabled: false` in `config/models.yaml:29`, but the implementation, the router default (`llm_router.py:31–37`), and the probe script (`scripts/probe_claude_vertex_matrix.py:174–209`) are wired and tested.

**Implication:** Once `anthropic_vertex` is enabled, the system **cannot** route Claude through a shared API key — it will use whatever GCP project ADC resolves to. If the migration target is a per-user GCP identity, this provider will already behave correctly. The Gemini-on-Vertex provider is the only laggard.

**Severity:** P1 (positive constraint, but operator must be aware).

### F4 (P2) — Local credential file `geuldobi-vertex-key.json` provenance is unknown

**Evidence:** E6. File exists, gitignored, not tracked, body not read. Filename strongly suggests it is the service-account JSON for the GCP project that backs the shared barobook account.

**Severity:** P2 (uncertain provenance, not a committed-secret leak). Cannot be raised to P0 without confirming whether the key derives from the shared account; T01 owns the inventory step.

### F5 (P2) — `.env.example` and README primary-channel both nudge toward the api_key path

**Evidence:** E9. `.env.example:9` lists `VERTEX_API_KEY=...` first. README:122 puts it before `VERTEX_PROJECT_ID`. Combined with F1, this pushes operators toward the shared-account-friendly path.

**Severity:** P2. Documentation hygiene problem that compounds F1.

### F6 (P3) — `scripts/probe_claude_vertex_matrix.py` mutates `os.environ` from `.env`

**Evidence:** E7. Probe scripts reading `.env` with `os.environ[key] = value` is a known anti-pattern (also flagged by 5arc-terminal1 survey). T03 only cares because the probe sets `VERTEX_LOCATION` per attempt (`probe_claude_vertex_matrix.py:175`), which then leaks into any subsequent in-process auth resolution.

**Severity:** P3. Diagnostic-only; out of #67's hot path. Note for T02.

### F7 (P1) — Operator/IAM facts that fix #67 are outside this codebase

**Evidence:** E5. The shared-account fact lives only in `docs/제안서_0318/이전 자료.md:103`, which records `barobook001@gmail.com (소설사업부 공용 ID)` is the human/billing identity used for VertexAI/Claude/OpenAI. There is no code constant, env default, or hard-coded `project_id` referencing barobook anywhere in `modules/`, `scripts/`, `config/`, `geuldobi-desktop/`, `build/`, `tests/`. Whatever shared identity is in production today flows through `.env` values that the operator chose, not through the source tree.

**Implication:** A pure docs-only closure is **insufficient** because of F1+F5, but a pure code-only closure is **also insufficient** because the actual `barobook001@gmail.com` identity has to be replaced in GCP IAM / billing / OAuth, which only the operator can do.

**Severity:** P1.

## Remediation Candidates

These are remediation **candidates** for the consolidated roadmap (per dispatch §7). T03 does not implement.

### RC1 — Flip `auth_mode` default away from `"auto"`

**What:** Change `config/models.yaml:18` `auth_mode: "auto"` to `auth_mode: "project_credentials"`. Optionally drop the `"auto"` value from `_AUTH_MODES` in both `vertex_provider.py:14` and `google_client_factory.py` (resolver in `:96–97` and `:69–73`) once we confirm no caller depends on it.

**Why:** Removes the silent api_key win that is the in-code shared-account vector (F1).

**Cost:** Operators currently relying on `VERTEX_API_KEY`-only setups will fail loudly until they provide `VERTEX_PROJECT_ID` + `VERTEX_LOCATION` (and optionally `GOOGLE_APPLICATION_CREDENTIALS`). Loud failure is acceptable for a security-driven change.

**Owner:** code change — system-track. Unblocks #67's code surface.

### RC2 — Single-source the Vertex auth resolver

**What:** Have `VertexAIProvider._get_client` delegate to `build_google_genai_client(provider_mode="vertex_ai")`, or extract a common `resolve_vertex_client(...)` helper used by both. Eliminate the duplicate `_AUTH_MODES` list.

**Why:** Removes the two-implementation drift risk (F2).

**Cost:** Touches both files, requires re-running `tests/test_llm_router.py` (51 cases) and the `scripts/run_stage4_canary.py` env-strip test surface.

**Owner:** code change — system-track. Should follow RC1 to avoid double-edit churn.

### RC3 — Re-order `.env.example` and README to lead with `project_credentials`

**What:** In `.env.example`, demote `VERTEX_API_KEY` below `VERTEX_PROJECT_ID|VERTEX_LOCATION|GOOGLE_APPLICATION_CREDENTIALS`, and rewrite the inline comment so the recommended path is project credentials. In `README.md:115–128`, lead the multi-provider section with the project-credentials trio.

**Why:** Makes the path of least resistance for new operators the per-user-friendly path (F5).

**Cost:** Doc-only. Coordinated with T01 (`.env.example`) and T10 (security-response doc).

**Owner:** docs change — system-track.

### RC4 — Confirm provenance of `geuldobi-vertex-key.json` and quarantine if barobook-issued

**What:** Operator (not T03) confirms in GCP IAM whether `geuldobi-vertex-key.json` was issued under the shared `barobook001@gmail.com` project. If yes: rotate, revoke, replace with a per-user/per-machine service account, and move the file out of workspace root (T05 owns the path policy).

**Why:** F4 cannot be resolved by code reading alone.

**Cost:** Operator IAM time + one rotation. No code change required.

**Owner:** operator + IAM. Tracks #67 closure.

### RC5 — Enable `anthropic_vertex` only after RC4

**What:** Keep `anthropic_vertex.enabled = false` in `config/models.yaml:29` until per-user GCP identity is provisioned, because flipping it to `true` will immediately bind Claude traffic to whatever GCP project ADC resolves to (F3).

**Why:** Prevents accidentally binding Claude traffic to the shared barobook account simply by enabling the provider.

**Cost:** None (status quo); a deliberate "do not enable yet" guardrail that should be recorded in the security-response doc (T10).

**Owner:** policy + T10 doc.

### RC6 — Document `GEULDOBI_VERTEX_AUTH_MODE` as a recommended baseline

**What:** Until RC1 lands, recommend `GEULDOBI_VERTEX_AUTH_MODE=project_credentials` as a baseline `.env` entry, with a one-line rationale referencing #67.

**Why:** Bridge measure between today's `auto` default and the eventual `project_credentials` default (F1).

**Cost:** One line in `.env.example` + one paragraph in README. T10 records it in the response doc.

**Owner:** docs change — system-track.

## Dependencies On Other Terminals

- **T01 (root secrets inventory):** Owns the path-level decision on `geuldobi-vertex-key.json` and `.env` lifecycle. T03's F4 escalation depends on T01's classification.
- **T02 (runtime config topology):** Owns the broader `.env` mutation question raised in F6 / E7 (`load_dotenv_file` mutating `os.environ`).
- **T04 (desktop config surfaces):** Owns the UI inputs that feed `VERTEX_API_KEY|VERTEX_PROJECT_ID|VERTEX_LOCATION|google_credentials_path` into `process_runner.py:886–896` (E8). Per-user identity migration cannot be code-only without T04 surfacing per-user fields.
- **T05 (windows settings paths):** Owns where `GOOGLE_APPLICATION_CREDENTIALS` should live on disk once `geuldobi-vertex-key.json` is rotated.
- **T06 (release packaging):** Owns whether `geuldobi-vertex-key.json` or `.env` could ship with a packaged build. T03 only confirmed local presence + gitignore; packaging exclusion is T06.
- **T09 (CI/release guardrails):** Should add a pre-commit / CI check that detects `*-vertex-key.json` shapes and `BEGIN PRIVATE KEY` patterns. Out of T03 scope.
- **T10 (security response doc):** Consumes F1, F4, F7, RC1–RC6 into the canonical response doc and explicitly records that #67 is **not** a docs-only closure.

## Open Questions

1. Is `geuldobi-vertex-key.json` a service-account key issued under the shared `barobook001@gmail.com`-owned GCP project, or under a separate per-user / per-machine project? (Operator/IAM check.)
2. What is the current value of `VERTEX_PROJECT_ID` in the operator's `.env`, and does it correspond to the shared barobook project? (Operator check; T03 did not read `.env` body.)
3. Has the shared `barobook001@gmail.com` Vertex API key (referenced as `.env:2` in `docs/2026-04-19/survey/T10-security-ops.md:45`, redacted) already been rotated as part of T10's earlier P0-1 response? T10's 2026-04-19 doc lists it as needing rotation; current rotation status is not tracked in this codebase.
4. Should the `"auto"` auth mode be deleted entirely (RC1), or kept behind `GEULDOBI_VERTEX_AUTH_MODE=auto` as an explicit opt-in for dev convenience? Policy call.
5. Does the migration target a single per-organisation GCP project with per-user IAM bindings, or per-user GCP projects? This decides whether `VERTEX_PROJECT_ID` becomes a shared default or a per-operator override surfaced through the desktop UI (T04).
6. Are there CI/canary scripts that explicitly require `VERTEX_API_KEY` and would break under RC1? Visible candidates: `scripts/run_stage4_canary.py` strips/sets `VERTEX_*` envs in tests, but production usage was not exhaustively traced in T03.

## Closure Recommendation

#67 cannot close as docs-only.

**Three things must happen for closure:**

1. **Code:** Apply RC1 (flip default away from `"auto"`) and RC2 (single-source the resolver). Optional: enforce RC3 (`.env.example` / README re-order) and RC6 (`GEULDOBI_VERTEX_AUTH_MODE=project_credentials` baseline) as a holding pattern until RC1 is merged.
2. **Operator/IAM:** RC4 — confirm provenance of `geuldobi-vertex-key.json`, rotate the shared-account-bound credentials, replace `barobook001@gmail.com` with per-user GCP identities for Vertex AI access, and update `.env`/UI inputs accordingly. This step does not happen inside this codebase.
3. **Policy / docs:** RC5 (gate `anthropic_vertex` enablement on operator IAM completion) and T10 records the response.

**Suggested closure ordering:**

- Step A (operator-only, no code change): set `GEULDOBI_VERTEX_AUTH_MODE=project_credentials` in `.env` immediately as a holding mitigation. The override already works (E4).
- Step B (code, system-track): RC1 → RC2 → RC3.
- Step C (operator/IAM): RC4 (rotation + per-user identity).
- Step D (policy/docs): RC5 + RC6 + T10 response doc.

Until Step C finishes, mark #67 as **mitigation-in-progress, not closed**, even if Step A and Step B are complete, because the underlying shared identity still exists in GCP IAM/billing.

T03 confidence in this report's evidence-to-recommendation chain: ~96% (one full read of every in-scope file plus cross-checked grep over `modules/`, `scripts/`, `geuldobi-desktop/`, `config/`, `tests/`, `docs/`, with redacted handling for `geuldobi-vertex-key.json` body).
