# Security Runtime Settings and Vertex Execution SSOT

Date: 2026-04-27
Track: system
Status: execution-ready (parked future wave)
Canonical Path: `docs/2026-04-27/security-runtime-settings-vertex-execution-ssot.md`
Temp Mirror Path: `docs/temp/security-runtime-settings-vertex-execution-ssot.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were present: `docs/2026-04-27/security-parallel-investigation/`, `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`, and pre-existing `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
- Resume Commit: same-as-baseline
- Resume Drift Summary: no tracked source edits made while creating this SSOT
GitHub Issues:
- #67 `[SEC] Migrate Vertex AI authentication away from shared Barobook account`
- #68 `[SEC] Move local app settings to approved user config directory`
- #66 as dependency
Source Survey Docs:
- `docs/2026-04-27/security-parallel-investigation/security-issues-parallel-investigation-dispatch.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-02-runtime-config-topology.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-03-vertex-auth-flow.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-04-desktop-config-surfaces.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-05-windows-settings-paths.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-10-security-response-doc-map.md`
Evidence Artifacts:
- Thread adversarial reviews A, B, and D returned in this Codex session
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: security-runtime-settings-vertex
  github_issue: 68
  status: pending
  queue_role: parked_future_wave
  roadmap_rank: 3
  depends_on:
    - security-secrets-config
  tranches:
    - id: approved-windows-path-contract
      title: Approved Windows path contract
    - id: runtime-config-authority-normalization
      title: Runtime config authority normalization
    - id: vertex-auth-resolver-migration
      title: Vertex auth resolver migration
    - id: docs-and-operator-status
      title: Docs and operator status
  verification_commands:
    - python -m pytest tests/test_runtime_paths.py tests/test_config_manager.py -q
    - python -m pytest tests/test_models_config.py tests/test_vertex_provider.py -q
    - python scripts/check_utf8_hygiene.py <touched docs/config/code>
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Define and implement the approved runtime settings path policy and Vertex AI authentication migration path after the secret boundary is fixed by `security-secrets-config-execution-ssot.md`.

## 2. Baseline Facts

- T02 reports cwd-relative config loading, duplicate `settings.json` readers, and multiple env mutation paths.
- T03 reports `auth_mode: auto` makes API-key/shared-key routing remain a default risk shape.
- Adversarial review A notes Claude-on-Vertex is not API-key based, but can still bind to a shared ADC/service-account identity if ADC points there.
- T05 reports `ConfigManager.root = Path.cwd()` and unbounded cwd `load_dotenv(override=True)` as path-policy violations.
- T05 reports two settings surfaces with disjoint owners and unresolved `%APPDATA%` versus `%LOCALAPPDATA%` policy.
- T10 reports no canonical security response document exists yet.

## 3. Scope

Included:
- Windows/user settings path authority for engine runtime and desktop launcher handoff.
- Separation of non-secret settings from secret credential files.
- ConfigManager/runtime_paths normalization.
- Vertex auth default migration away from shared API-key behavior.

Excluded:
- Desktop plaintext key storage and bridge token design.
- Release packaging denylist implementation.
- External GCP/IAM account changes; this SSOT records required proof but cannot perform IAM work.

## 4. Pass 1. Inventory Summary

| Surface | Evidence | Risk |
| --- | --- | --- |
| `ConfigManager.root = Path.cwd()` | T05 F1 | P0 path-policy violation |
| cwd `load_dotenv(override=True)` | T05 F2 | P0 env mutation |
| per-project `.env` under Documents | T05 F3 | P1 secret/settings conflation |
| duplicate settings owners | T05 F4, T04 F2/F3 | P1 inconsistent authority |
| backend cwd fallback | T05 F6 | P1 packaged runtime drift |
| Vertex `auth_mode: auto` | T03 F1 | P1 shared-key/default identity risk |
| parallel Vertex auth implementations | T03 F2 | P2 duplicated bypass risk |

## 5. Pass 2. Semantic Classification

- Path authority decisions: canonical Windows paths for non-secret settings, secrets, logs, projects, and license/access files.
- Runtime code normalization: runtime path helpers own path decisions; cwd is not default authority.
- Vertex auth migration: default to project/service-account credentials and single-source provider auth resolution.

## 6. Side-Effect Map

- file writes / artifacts: `runtime_paths.py`, `config_manager.py`, `models_config.py`, provider modules, `config/models.yaml`, `.env.example`, docs.
- DB / schema / transaction boundaries: not applicable unless a future settings store uses SQLite.
- JSONL / log / audit sinks: path/auth failures must log redacted metadata only.
- console / UI / operator output: errors should name missing approved path/auth mode without printing credential values.
- rollback / recovery / retry: path migration needs fallback discovery; auth default flip needs documented emergency dev override if retained.
- cache / global state: environment mutation must not leak between projects/providers.
- bootstrap fallback / config-env mutation: backend launch without Electron env must fail safe or resolve approved paths.

## 7. Realization Architecture

This SSOT depends on `security-secrets-config`. Preferred architecture:
- `runtime_paths.py` defines the authoritative Windows path table.
- `ConfigManager` consumes that table instead of cwd by default.
- `.env` is dev-only and explicitly bounded if retained.
- Vertex auth resolver returns a typed mode such as `project_credentials`, `service_account_file`, `api_key_dev_only`, or `unconfigured`.

## 8. Execution Tranches

1. Approved Windows path contract.
2. Runtime config authority normalization.
3. Vertex auth resolver migration.
4. Docs and operator status.

## 9. Acceptance Criteria

- Runtime settings load from approved user/workspace paths only.
- App runtime does not write to `C:\Program Files` under normal execution.
- `.env` usage is dev-only, bounded, and not arbitrary user-PC mutation.
- Vertex auth defaults away from shared API-key/common account assumptions.
- Provider auth resolver behavior is covered by targeted tests.
- External IAM completion is recorded as a required human/security-owner proof item before #67 closure.

## 10. Verification Plan

- Targeted tests for runtime path resolution and ConfigManager root choice.
- Targeted tests for Vertex auth default and explicit override behavior.
- `python -m py_compile modules/core/runtime_paths.py modules/core/config_manager.py modules/core/models_config.py modules/core/providers/vertex_provider.py modules/core/providers/gemini_provider.py modules/core/providers/anthropic_vertex_provider.py`
- `python scripts/check_utf8_hygiene.py <touched docs/config/code>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not make secrets live in the same plaintext settings file as non-secret UI settings.
- Do not claim GCP is fixed unless IAM/account owner proof is attached or summarized.
- Do not let emergency dev override become the documented production path.
- Do not close #67 as docs-only unless code and operator evidence prove no shared account dependency remains.

## 12. Temp Queue Notes

- temp status: pending
- queue role: parked future wave
- cleanup condition: remove `docs/temp/security-runtime-settings-vertex-execution-ssot.md` after realization, verification, and canonical closure update.
- roadmap dependency: depends on `security-secrets-config`.

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- queue state: `python scripts/sync_temp_queue_state.py`
- execution-start rule: re-run document 3-pass audit and confirm at least 95% confidence against live workspace before code edits.

## 14. 3-Pass Document Audit

Pass 1 - structure and scope:
- PASS. The document covers #67/#68 and explicitly depends on #66.

Pass 2 - evidence and consistency:
- PASS. Evidence is drawn from T02/T03/T04/T05/T10 and adversarial reviews A/B/D.
- PASS. `%APPDATA%` versus `%LOCALAPPDATA%` is explicit unresolved implementation input, not hidden.

Pass 3 - execution readiness:
- PASS. Tranches are ordered from path contract to runtime normalization to provider migration to docs.

Estimated operational confidence: 96%.

