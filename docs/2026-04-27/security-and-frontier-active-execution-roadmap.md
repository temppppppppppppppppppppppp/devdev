# Security and Frontier Active Execution Roadmap

Date: 2026-04-27
Status: active
Canonical Path: `docs/2026-04-27/security-and-frontier-active-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were present: `docs/2026-04-27/security-parallel-investigation/`, `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`, and pre-existing `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
- Resume Commit: `9cfb9600154edcb71fabfa6bc467aef864b4025f`
- Resume Drift Summary: GitHub #58 is now closed; this refresh retires `stage4-post-select-conflict` from the active temp queue and promotes #59 as the next active queue item.
Queue Snapshot:
- `docs/temp/frontier-lag-clean-5arc-stabilization-execution-ssot.md`
- `docs/temp/security-secrets-config-execution-ssot.md`
- `docs/temp/security-runtime-settings-vertex-execution-ssot.md`
- `docs/temp/security-desktop-release-guardrails-execution-ssot.md`
- `docs/temp/stage3-stage4-genre-alignment-execution-ssot.md`
- `docs/temp/stage4-proof-digest-cove-advisory-execution-ssot.md`

## 1. Purpose

This roadmap is required because `docs/temp/` now contains more than one execution SSOT mirror. It preserves the pre-existing Frontier Lag queue item while adding three parked security execution items derived from the completed ten-terminal security survey, one parked #56 Stage3/Stage4 genre-alignment execution item derived from adversarial synthesis of the available issue/order/source evidence, and one active #59 Stage4 proof-digest/CoVe advisory execution item derived from the completed ten-terminal #59 survey. The former #58 Stage4 POST_SELECT_CONFLICT item is retained in its canonical SSOT as historical backing only because GitHub #58 is now closed.

This roadmap governs queue ordering only. It does not authorize implementation by itself. Before implementation from any listed item, re-run the 3-pass document audit against current workspace state and confirm at least 95% confidence.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `frontier-lag-clean-5arc-stabilization` | `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md` | `docs/temp/frontier-lag-clean-5arc-stabilization-execution-ssot.md` | pending | Existing terminal proof queue item; parked until #59/#56 evidence layers are cleaner. |
| `security-secrets-config` | `docs/2026-04-27/security-secrets-config-execution-ssot.md` | `docs/temp/security-secrets-config-execution-ssot.md` | pending | Security P0 substrate; parked future wave. |
| `security-runtime-settings-vertex` | `docs/2026-04-27/security-runtime-settings-vertex-execution-ssot.md` | `docs/temp/security-runtime-settings-vertex-execution-ssot.md` | pending | Depends on `security-secrets-config`; parked future wave. |
| `security-desktop-release-guardrails` | `docs/2026-04-27/security-desktop-release-guardrails-execution-ssot.md` | `docs/temp/security-desktop-release-guardrails-execution-ssot.md` | pending | Depends on both prior security SSOTs; parked future wave. |
| `stage3-stage4-genre-alignment` | `docs/2026-04-27/stage3-stage4-genre-alignment-execution-ssot.md` | `docs/temp/stage3-stage4-genre-alignment-execution-ssot.md` | pending | #56 investment/business-power action/tension semantics remediation; parked future wave pending operator promotion. |
| `stage4-proof-digest-cove-advisory` | `docs/2026-04-27/stage4-proof-digest-cove-advisory-execution-ssot.md` | `docs/temp/stage4-proof-digest-cove-advisory-execution-ssot.md` | in_progress | #59 proof-digest warn taxonomy, CoVe advisory/fail-closed split, dashboard freshness, and benchmark diagnostic packet; operator-promoted active item. |

## 3. Dependency Graph

- `security-secrets-config -> security-runtime-settings-vertex`
- `security-secrets-config -> security-desktop-release-guardrails`
- `security-runtime-settings-vertex -> security-desktop-release-guardrails`
- `frontier-lag-clean-5arc-stabilization` is independent of the security remediation chain.
- `stage3-stage4-genre-alignment` has no formal dependency edge to avoid silently reordering the existing Frontier Lag queue item, but it should be considered before any fresh terminal clean 5-arc proof claim because wrong action/tension semantics can feed downstream Stage4 rejects.
- `stage4-proof-digest-cove-advisory` has no formal dependency edge, but it should be considered before any fresh terminal clean 5-arc proof claim or Issue #62 benchmark comparison claim because it separates proof evidence, runtime advisory, semantic fail-closed retry, stale summaries, and settled attempt verdicts.

Shared substrate:
- security secret boundary must precede runtime path/auth and desktop/release guardrail implementation.
- runtime path authority must precede license/access-control persistence decisions.

Merge opportunities:
- #66 scanner guardrails can feed #69 release denylist checks.
- #68 path authority can feed #70 license/device file placement.
- #71 status documentation should summarize all three security execution docs after implementation facts exist.
- #56 Stage3/Stage4 genre alignment can feed the Frontier Lag strict 5-arc proof path by reducing physical-action drift and unauthorized business-power scene register mismatch before fresh proof.
- #59 proof-digest/CoVe advisory remediation can feed Issue #62 benchmark reporting and any future Frontier Lag proof claim by keeping advisory warnings, semantic rejects, stale summaries, and proof evidence in separate fields.

## 4. Execution Order

Priority basis:
- `docs/implementation/queue-priority-rubric.md`
- Existing queue continuity is preserved unless the operator explicitly moves security work to the front.
- Within the security chain, dependency order is strict.

Working order:

1. `stage4-proof-digest-cove-advisory` (in progress; operator-promoted active item after #58 queue retirement)
2. `stage3-stage4-genre-alignment` (parked future wave; promote after #59 if the operator keeps bug-risk reduction ahead of security)
3. `frontier-lag-clean-5arc-stabilization` (parked future wave; existing terminal proof item after #59/#56 stabilization)
4. `security-secrets-config` (parked future wave; security P0 substrate)
5. `security-runtime-settings-vertex` (parked future wave; depends on `security-secrets-config`)
6. `security-desktop-release-guardrails` (parked future wave; depends on `security-secrets-config` and `security-runtime-settings-vertex`)

## 5. Per-Item Plan

### frontier-lag-clean-5arc-stabilization

- goal: preserve the existing active stabilization queue item and do not silently demote it during security document intake.
- prerequisites: current-state re-audit before further implementation; do not start a fresh proof claim before #59 warning taxonomy and #56 genre semantics have either landed or been explicitly deferred by the operator.
- execution notes: unrelated to security remediation except for shared queue mechanics.
- completion signal: canonical closure update and removal of temp mirror via closure harness.
- temp cleanup action: remove only `docs/temp/frontier-lag-clean-5arc-stabilization-execution-ssot.md` after realized and closed.

### security-secrets-config

- goal: contain secret exposure, define git/history/rotation posture, and establish runtime env loading chokepoint.
- prerequisites: credential owner decisions for rotation/history rewrite where needed.
- execution notes: must run before other security items.
- completion signal: #66 acceptance criteria satisfied or residual external owner tasks documented.
- temp cleanup action: remove `docs/temp/security-secrets-config-execution-ssot.md` after closure.

### security-runtime-settings-vertex

- goal: normalize Windows/user config path authority and Vertex auth resolver behavior.
- prerequisites: `security-secrets-config` boundary and approved path policy decision.
- execution notes: do not claim GCP/IAM migration complete without external owner proof.
- completion signal: #67/#68 acceptance criteria satisfied, tests pass, and docs updated.
- temp cleanup action: remove `docs/temp/security-runtime-settings-vertex-execution-ssot.md` after closure.

### security-desktop-release-guardrails

- goal: contain desktop secret surfaces, add bridge/startup gate, harden release packaging, separate dev/test artifacts, and publish mitigation status.
- prerequisites: `security-secrets-config` and `security-runtime-settings-vertex`.
- execution notes: split bridge auth from final license/access model; renderer-only checks are not enough.
- completion signal: #69/#70/#71 acceptance criteria satisfied or residual product/ops decision recorded.
- temp cleanup action: remove `docs/temp/security-desktop-release-guardrails-execution-ssot.md` after closure.

### stage3-stage4-genre-alignment

- goal: align Stage3/Stage4 action, tension, peak, and cliffhanger semantics to investment/business-power register instead of physical combat/chase defaults.
- prerequisites: current-state re-audit required before implementation; if #56 T01-T10 reports are later materialized, merge them before code edits.
- execution notes: preserve Director authority and the existing unauthorized tactical intrusion guard; treat genre semantics as prompt/route/advisory contract, not Python narrative scoring.
- completion signal: targeted regressions and fresh proof evidence show business-power action/tension prompts and Director selection context are aligned, then #56 receives a status update.
- temp cleanup action: remove `docs/temp/stage3-stage4-genre-alignment-execution-ssot.md` after closure.

### stage4-proof-digest-cove-advisory

- goal: make Stage4 proof-digest `warn`, CoVe runtime advisory, CoVe semantic fail-closed retry, Director PASS authority, settled attempt verdict, stale runtime summaries, and benchmark diagnostics visibly distinct.
- prerequisites: all ten #59 terminal reports are present; current-state re-audit is required before each remaining tranche.
- execution notes: do not make `warn` disappear by dropping evidence. Bridge/dashboard warn count forwarding and CoVe test hardening are partially realized; stale-summary detection, producer taxonomy, benchmark packet changes, and possible desktop rendering remain open.
- completion signal: targeted dashboard, CoVe, and benchmark regressions pass; proof warnings are itemized by authority role; Issue #59 receives a status update.
- temp cleanup action: remove `docs/temp/stage4-proof-digest-cove-advisory-execution-ssot.md` after closure.

## 6. Shared Risks and Side-Effects

- shared write paths: docs, `.gitignore`, `.gitattributes`, `.env.example`, config modules, provider modules, desktop files, build scripts, CI workflows.
- shared DB/schema touchpoints: not expected for security docs unless a future license/device store is implemented.
- shared logs/UI surfaces: scanner output, Electron/backend logs, auth/config errors, and security status docs must not expose secret values.
- rollback/recovery concerns: credential rotation and git-history rewrite require explicit owner approval; package denylist failures should fail closed and be easy to retry.
- queue collision or ordering risks: creating additional security or Stage4 SSOTs requires updating this roadmap before implementation.
- Stage4-specific shared side effects: `stage_attempts`, `director_selections`, `manuscripts`, `blueprints`, `episode_meta`, context cache attempts, rejected/selected artifacts, and runtime/session logs.
- Stage3/Stage4 genre-alignment side effects: prompt envelopes, candidate `_ensemble_meta`, strategy metadata, cache keys, Director prompt context, physical intrusion guard logs, and benchmark/reject-rate evidence.
- Stage4 proof-digest/CoVe advisory side effects: proof digest payloads, bridge/dashboard compact summaries, `runtime_audit_summary.json` freshness labels, CoVe advisory audit events, benchmark archive packets, and operator comparison lines.

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `frontier-lag-clean-5arc-stabilization` | pending | 2026-04-27 | parked until #59/#56 are either landed or explicitly deferred |
| `security-secrets-config` | pending | 2026-04-27 | external credential rotation/history decision may block closure |
| `security-runtime-settings-vertex` | pending | 2026-04-27 | depends on `security-secrets-config`; path policy decision required |
| `security-desktop-release-guardrails` | pending | 2026-04-27 | depends on first two security items; access-control product model may remain residual |
| `stage3-stage4-genre-alignment` | pending | 2026-04-27 | current-state re-audit required; #56 T01-T10 artifacts were not locally/GitHub-readable during synthesis |
| `stage4-proof-digest-cove-advisory` | in_progress | 2026-04-27 | partial bridge/dashboard warn count forwarding and CoVe test hardening implemented; stale-summary detection, producer taxonomy, benchmark packet, and possible desktop rendering remain open |

## 8. Queue Cleanup Rule

- remove a temp execution SSOT mirror immediately after that item is realized and closed.
- keep canonical dated docs.
- when all items are completed, remove `docs/temp/execution-roadmap.md`.
- remove `docs/temp/queue-state.json` if present and the queue is empty.
- leave `docs/temp/README.md`.

## 9. 3-Pass Document Audit

Pass 1 - structure and scope:
- PASS. Roadmap exists because temp queue now has multiple execution SSOT mirrors.
- PASS. Queue inventory, dependencies, execution order, per-item plans, and cleanup rules are present.

Pass 2 - evidence and consistency:
- PASS. Existing Frontier Lag mirror is preserved and not silently removed.
- PASS. Security dependencies match execution metadata blocks in the new SSOTs.
- PASS. Security items are marked as parked future wave, preventing accidental front-active interpretation.
- PASS. Stage4 #58 is removed from the active temp queue only after GitHub #58 closure is reflected in the canonical #58 SSOT.
- PASS. Stage3/Stage4 #56 item is marked as parked future wave and explicitly records the missing local/GitHub-readable T01-T10 artifact limitation.
- PASS. Stage4 #59 item is promoted as the active queue item and explicitly separates proof evidence, CoVe advisory, semantic retry, stale summary, and benchmark comparison surfaces.

Pass 3 - execution readiness:
- PASS. The roadmap is actionable for queue control but explicitly does not authorize implementation without fresh re-audit.
- PASS. Cleanup behavior is explicit.

Estimated operational confidence: 96%.

## 10. Operator Promotion Note - 2026-04-27

The operator promoted `stage4-post-select-conflict` ahead of the prior Frontier Lag default with the instruction to reduce bug risk first. That item is now closed on GitHub and retired from the active temp queue as historical backing only. The roadmap now treats `stage4-proof-digest-cove-advisory` (#59) as the active item because it must separate proof evidence, advisory failures, stale summaries, and benchmark diagnostics before any new clean-run or benchmark claim.

Retired item:
- `stage4-post-select-conflict` / GitHub #58: closed on GitHub, canonical SSOT retained, temp mirror removed from the active queue. This retirement does not authorize a clean 5-arc readiness claim.
