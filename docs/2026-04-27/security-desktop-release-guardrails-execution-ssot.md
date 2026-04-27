# Security Desktop Release Guardrails Execution SSOT

Date: 2026-04-27
Track: system
Status: execution-ready (parked future wave)
Canonical Path: `docs/2026-04-27/security-desktop-release-guardrails-execution-ssot.md`
Temp Mirror Path: `docs/temp/security-desktop-release-guardrails-execution-ssot.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were present: `docs/2026-04-27/security-parallel-investigation/`, `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`, and pre-existing `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
- Resume Commit: same-as-baseline
- Resume Drift Summary: no tracked source edits made while creating this SSOT
GitHub Issues:
- #69 `[SEC] Separate test/dev scripts from production source tree`
- #70 `[SEC] Add executable access control for internal distribution`
- #71 `[DOCS] Document security response and current mitigation status`
- #66 and #68 as dependencies
Source Survey Docs:
- `docs/2026-04-27/security-parallel-investigation/security-issues-parallel-investigation-dispatch.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-04-desktop-config-surfaces.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-06-release-packaging.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-07-dev-test-separation.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-08-exe-access-control.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-09-ci-release-guardrails.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-10-security-response-doc-map.md`
Evidence Artifacts:
- Thread adversarial reviews B and D returned in this Codex session
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: security-desktop-release-guardrails
  github_issue: 70
  status: pending
  queue_role: parked_future_wave
  roadmap_rank: 4
  depends_on:
    - security-secrets-config
    - security-runtime-settings-vertex
  tranches:
    - id: desktop-secret-surface-containment
      title: Desktop secret surface containment
    - id: bridge-auth-and-startup-gate
      title: Bridge auth and startup gate
    - id: release-packaging-denylist
      title: Release packaging denylist
    - id: dev-test-tree-separation
      title: Dev and test tree separation
    - id: security-response-status-doc
      title: Security response status doc
  verification_commands:
    - python scripts/check_utf8_hygiene.py <touched docs/config/code>
    - git diff --check
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Create the execution plan for desktop-facing secret exposure, release packaging guardrails, dev/test separation, and the first enforceable EXE access-control layer.

This SSOT splits #70 into two phases: bridge/startup hardening first, license/access model second. Renderer-only checks are not sufficient.

## 2. Baseline Facts

- T04 reports a P0 renderer outbound fetch that places an API key in the URL query string.
- T04 reports plaintext local settings storage for multiple API keys and a Slack webhook.
- T04 reports the backend HTTP bridge lacks an authentication header and `electron-main.log` can accumulate sensitive output.
- T06 reports release bundles shipping plaintext Python source and weak packaging exclusions.
- T06 reports no startup auth gate in `backend_entry.py`, Electron backend spawn path, or embedded Python runtime.
- T07 reports `lite_mode/` dev probes are bundled into release engine and `tools2/test_*.py` live outside `tests/`.
- T09 reports no secret-scanning guardrail and no release-bundle anti-secret/anti-test exclusion.
- T08 proposes access-control models but leaves product/ops model selection open.

## 3. Scope

Included:
- Desktop renderer/main/preload secret exposure and plaintext settings risks.
- Per-launch bridge token or equivalent backend-auth channel.
- Startup chokepoint for future license/access control.
- Release packaging denylist and manifest/hash guardrails.
- Dev/test/script tree separation plan for release inclusion.
- Canonical security response status doc after implementation facts exist.

Excluded:
- Final product decision for online login versus signed license versus hybrid provisioning unless explicitly selected.
- Deep anti-tamper beyond release manifest/signing posture.
- Runtime config path policy; see `security-runtime-settings-vertex-execution-ssot.md`.

## 4. Pass 1. Inventory Summary

| Surface | Evidence | Risk |
| --- | --- | --- |
| Renderer URL-key fetch | T04 F1 | P0 key exposure |
| Plaintext desktop settings | T04 F2/F3 | P0/P1 credential storage risk |
| Backend bridge no auth header | T04 F5 | P1 local bridge abuse risk |
| Electron log leakage | T04 F6 | P1 sensitive output persistence |
| `dist/engine` plaintext source | T06 F1 | P1/#69 release surface |
| weak root packaging exclusions | T06 F3 | P0 release leakage risk |
| weak Electron extraResources filters | T06 F4 | P1/P2 release leakage risk |
| no startup auth gate | T06 F9/T08 | P2 copied EXE runs normally |
| `lite_mode/` bundled into release | T07 F1 | P1 dev/probe release surface |
| `tools2/test_*.py` outside tests | T07 F6 | P2 dev/test separation gap |
| no CI/release guardrail | T09 F1/F2 | P0 prevention gap |

## 5. Pass 2. Semantic Classification

- Desktop secret exposure: renderer should not own or transmit raw provider keys; logs must redact secrets.
- Bridge/startup boundary: bridge auth protects local backend APIs before full license model exists.
- Release and dev/test hygiene: packaging must prove absence of secret/dev/test/temp/archive artifacts.
- Response documentation: #71 status doc follows verified implementation facts, not the other way around.

## 6. Side-Effect Map

- file writes / artifacts: desktop main/preload/renderer files, build scripts, Electron package config, CI workflow, docs/security status, release manifests.
- DB / schema / transaction boundaries: not applicable unless license/device state is stored in SQLite.
- JSONL / log / audit sinks: Electron and backend logs must redact secrets and access tokens.
- console / UI / operator output: unauthorized startup/config errors must be explicit but non-sensitive.
- rollback / recovery / retry: packaging denylist failures should fail closed and be retryable; license failures need support path without bypassing backend gate.
- cache / global state: per-launch bridge tokens should be memory-only unless the selected model requires persisted device/license data.
- bootstrap fallback / config-env mutation: backend startup must fail safe when expected launch auth context is missing.

## 7. Realization Architecture

This SSOT depends on the preceding security docs:
- `security-secrets-config` defines what must never ship.
- `security-runtime-settings-vertex` defines approved settings/secrets/license path authority.

## 8. Execution Tranches

1. Desktop secret surface containment.
2. Bridge auth and startup gate.
3. Release packaging denylist.
4. Dev/test tree separation.
5. Security response status doc.

## 9. Acceptance Criteria

- Renderer no longer sends provider API keys in URL query strings.
- Desktop settings do not persist raw provider keys or webhooks in the same plaintext file as non-secret preferences.
- Backend bridge requires auth context for normal operations.
- Direct copied backend/EXE launch cannot proceed into normal app usage without startup gate.
- Release packaging fails if secret/dev/test/temp/archive denylisted files are staged.
- Release artifact has manifest/hash evidence.
- Dev/test/probe trees have documented keep/move/exclude decisions.
- Security response status doc links issues #66-#71, PRs, verification, and residual risks.

## 10. Verification Plan

- Desktop smoke checks for settings save/load without secret persistence.
- Backend bridge unauthorized/authorized request tests.
- Release staging dry run proving denylist blocks known bad path classes.
- CI/pre-commit secret scan and packaging denylist checks.
- `python scripts/check_utf8_hygiene.py <touched docs/config/code>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not implement renderer-only access control and call #70 done.
- Do not store bridge tokens, license secrets, or provider keys in logs.
- Do not let packaging filters rely only on a short extension denylist.
- Do not bulk-delete dev/test artifacts without reference scans and scoped PRs.
- Do not claim code signing/tamper resistance unless explicitly implemented or recorded as residual risk.

## 12. Temp Queue Notes

- temp status: pending
- queue role: parked future wave
- cleanup condition: remove `docs/temp/security-desktop-release-guardrails-execution-ssot.md` after realization, verification, and canonical closure update.
- roadmap dependency: depends on `security-secrets-config` and `security-runtime-settings-vertex`.

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- queue state: `python scripts/sync_temp_queue_state.py`
- execution-start rule: re-run document 3-pass audit and confirm at least 95% confidence against live workspace before code edits.

## 14. 3-Pass Document Audit

Pass 1 - structure and scope:
- PASS. The document covers desktop/release/dev-test/access-control guardrails and leaves path/secret substrate to earlier SSOTs.

Pass 2 - evidence and consistency:
- PASS. Evidence is drawn from T04/T06/T07/T08/T09/T10 and adversarial reviews B/D.
- PASS. T08 bridge-auth/license-model ambiguity is resolved by separating bridge auth from final license/access model.

Pass 3 - execution readiness:
- PASS. Tranches are ordered from direct exposure to bridge gate to release proof to dev/test cleanup to status documentation.

Estimated operational confidence: 96%.

