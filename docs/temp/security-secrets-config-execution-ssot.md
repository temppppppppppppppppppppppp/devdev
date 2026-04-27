# Security Secrets and Config Execution SSOT

Date: 2026-04-27
Track: system
Status: execution-ready (parked future wave)
Canonical Path: `docs/2026-04-27/security-secrets-config-execution-ssot.md`
Temp Mirror Path: `docs/temp/security-secrets-config-execution-ssot.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were present: `docs/2026-04-27/security-parallel-investigation/`, `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`, and pre-existing `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
- Resume Commit: same-as-baseline
- Resume Drift Summary: no tracked source edits made while creating this SSOT
GitHub Issues:
- #66 `[SEC] Remove secrets from code/config and standardize runtime config loading`
- #67 and #68 as downstream dependency surfaces
Source Survey Docs:
- `docs/2026-04-27/security-parallel-investigation/security-issues-parallel-investigation-dispatch.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-01-secret-inventory.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-02-runtime-config-topology.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-03-vertex-auth-flow.md`
- `docs/2026-04-27/security-parallel-investigation/terminal-09-ci-release-guardrails.md`
Evidence Artifacts:
- Thread adversarial review A: T01/T02/T03 3-pass review returned in this Codex session
- Thread adversarial review D: governance/queue 3-pass review returned in this Codex session
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: security-secrets-config
  github_issue: 66
  status: pending
  queue_role: parked_future_wave
  roadmap_rank: 2
  depends_on: []
  tranches:
    - id: credential-containment-and-rotation-ledger
      title: Credential containment and rotation ledger
    - id: git-secret-history-policy
      title: Git secret history and ignore policy
    - id: runtime-env-load-chokepoint
      title: Runtime env loading chokepoint
    - id: secret-scan-guardrails
      title: Secret scan guardrails
  verification_commands:
    - python scripts/check_utf8_hygiene.py <touched docs/config/code>
    - git diff --check
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Create the first execution slice for the security-team feedback: contain secret material, stop unbounded `.env` mutation from acting as runtime authority, and add guardrails so the same leak class cannot silently return.

This SSOT is not a claim that credentials have been rotated or that git history has been remediated.

## 2. Baseline Facts

- T01 reports P0 reachable secret-bearing `.env` history and additional nested `.env` blobs in git history.
- T01 reports local working-tree secret artifacts: `geuldobi-vertex-key.json`, `github-recovery-codes.txt`, and `secrets/*.env`.
- T02 reports module-import-time and app-init env mutation, including `load_dotenv(override=True)` style behavior.
- T03 reports Vertex auth defaulting toward `auth_mode: auto`, preserving shared-key risk until the Vertex auth resolver is migrated.
- T09 reports no blocking secret scanner in pre-commit or CI and no release anti-secret guardrail.
- Adversarial review A found no raw secrets pasted into T01-T03 reports, but warned that historical `.env` evidence should remain risk-class based unless owners prove otherwise.

## 3. Scope

Included:
- Git/source-control hygiene for `.env`, service-account JSON, recovery codes, and `secrets/`.
- Runtime env-loading chokepoints in Python boot/config surfaces.
- Secret scanning and CI/pre-commit guardrails.

Excluded:
- Final Vertex auth migration; see `security-runtime-settings-vertex-execution-ssot.md`.
- Desktop plaintext settings and bridge auth; see `security-desktop-release-guardrails-execution-ssot.md`.
- External credential rotation or git-history rewrite unless explicitly approved by the credential/repo owner.

## 4. Pass 1. Inventory Summary

| Surface | Evidence | Risk |
| --- | --- | --- |
| Historical root `.env` | T01 F1 | P0 secret-history class |
| Nested historical `.env` blobs | T01 F2 | P0 leak class beyond root |
| `geuldobi-vertex-key.json` | T01 F3, T03 F4 | P1 local secret artifact |
| `github-recovery-codes.txt` | T01 F4 | P1 local recovery artifact |
| `secrets/*.env` | T01 F5 | P1 local-only secret files |
| import/cwd env mutation | T02 F1-F3 | P1 runtime authority drift |
| missing secret scanning | T09 F1 | P0 guardrail gap |
| missing release anti-secret scan | T09 F2 | P0 release leakage gap |

## 5. Pass 2. Semantic Classification

- External/account-owner decisions: credential rotation, git-history rewrite decision, service-account/recovery-code provenance.
- Repo policy and guardrails: `.gitignore`, `.gitattributes`, pre-commit, CI, and release-stage secret scans.
- Runtime authority: remove or contain global/cwd `.env` mutation and define one explicit bootstrap source order.

## 6. Side-Effect Map

- file writes / artifacts: `.gitignore`, `.gitattributes`, `.env.example`, docs, CI workflows, pre-commit config, config-loader modules.
- DB / schema / transaction boundaries: not applicable unless future code records credential rotation status.
- JSONL / log / audit sinks: scanner output and runtime errors must redact secret values.
- console / UI / operator output: identify missing/invalid config without printing values.
- rollback / recovery / retry: credential rotation and history rewrite are not trivially reversible; require explicit approval.
- cache / global state: process env mutation must be snapshot/restored or limited to explicit bootstrap.
- bootstrap fallback / config-env mutation: unbounded cwd `.env` loading is the main target.

## 7. Realization Architecture

Execute this before the path/Vertex and desktop/release SSOTs. The secret boundary must exist before later work decides where credentials, settings, and access tokens live.

## 8. Execution Tranches

1. Credential containment and rotation ledger.
2. Git secret history policy.
3. Runtime env loading chokepoint.
4. Secret scan guardrails.

## 9. Acceptance Criteria

- No tracked source/config/doc file contains real secret values.
- Local secret files are outside the repo tree or explicitly ignored and documented as local-only.
- Historical `.env` exposure has an owner-approved mitigation decision and rotation status ledger.
- Runtime env loading has one documented authority path and no unbounded cwd `load_dotenv(override=True)` behavior.
- Pre-commit, CI, and release packaging have blocking or explicitly justified secret-scan guardrails.

## 10. Verification Plan

- `python scripts/check_utf8_hygiene.py <touched docs/config/code>`
- `git diff --check`
- targeted config-loader tests once implemented
- pre-commit/CI secret scanner dry run with redacted output
- release staging scan proving denylisted secret paths are absent
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not print raw secrets in logs, reports, PRs, or GitHub comments.
- Do not claim credential rotation without owner evidence.
- Do not rewrite git history without explicit repo-owner approval.
- Do not close #66 until runtime config, source-control hygiene, and scanner guardrails all pass.

## 12. Temp Queue Notes

- temp status: pending
- queue role: parked future wave
- cleanup condition: remove `docs/temp/security-secrets-config-execution-ssot.md` after realization, verification, and canonical closure update.
- roadmap dependency: first security SSOT; `security-runtime-settings-vertex` and `security-desktop-release-guardrails` depend on this boundary.

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- queue state: `python scripts/sync_temp_queue_state.py`
- execution-start rule: re-run document 3-pass audit and confirm at least 95% confidence against live workspace before code edits.

## 14. 3-Pass Document Audit

Pass 1 - structure and scope:
- PASS. This is an execution SSOT for #66 and immediate secret/config substrate only.

Pass 2 - evidence and consistency:
- PASS. Evidence is based on T01/T02/T03/T09 plus adversarial review A and governance review D.
- PASS. No raw secret values are included.

Pass 3 - execution readiness:
- PASS. Tranches are ordered from external containment to repo guardrails to runtime chokepoint.
- PASS. Side effects and rollback limits are explicit.

Estimated operational confidence: 96%.

