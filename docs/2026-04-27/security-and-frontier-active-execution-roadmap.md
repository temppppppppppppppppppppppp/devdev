# Security and Frontier Active Execution Roadmap

Date: 2026-04-27
Status: active (#57 frontier proof reopened/front-active; #120/#121/#129/#130/#134 completed; security items parked)
Canonical Path: `docs/2026-04-27/security-and-frontier-active-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
- Baseline Dirty Summary: documentation-only untracked paths were present: `docs/2026-04-27/security-parallel-investigation/`, `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/`, and pre-existing `docs/2026-04-27/issue-56-ensemble-genre-alignment-10terminal-order.md`
- Resume Commit: `3a5cf102e383a97b7be1feee28367443e29661e3`
- Resume Drift Summary: 2026-04-30 queue refresh removes the completed #120 `stage3-genre-contract-resolver-fallback` temp mirror, reopens #57 as the active full-proof tracker, and keeps security execution SSOTs parked behind explicit operator promotion.
Queue Snapshot:
- `docs/temp/frontier-lag-clean-5arc-stabilization-execution-ssot.md`
- `docs/temp/security-secrets-config-execution-ssot.md`
- `docs/temp/security-runtime-settings-vertex-execution-ssot.md`
- `docs/temp/security-desktop-release-guardrails-execution-ssot.md`

## 1. Purpose

This roadmap is required because `docs/temp/` still contains more than one execution SSOT mirror. It preserves the pre-existing Frontier Lag proof item and keeps three security execution items parked behind explicit operator promotion. The former #58 Stage4 POST_SELECT_CONFLICT item, #59 Stage4 proof-digest/CoVe advisory item, #56 Stage3/Stage4 genre-alignment item, #120 Stage3 genre-contract resolver fallback item, and follow-up #121/#129/#130/#134 queue work are retained in canonical docs or GitHub history as historical backing only because their implementation issues are now closed and their PRs are merged.

This roadmap governs queue ordering only. It does not authorize implementation by itself. Before implementation from any listed item, re-run the 3-pass document audit against current workspace state and confirm at least 95% confidence.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `frontier-lag-clean-5arc-stabilization` | `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md` | `docs/temp/frontier-lag-clean-5arc-stabilization-execution-ssot.md` | active | Provider-wait hardening is merged; bounded reruns reached Stage 3 `replay/authority` and person fact-lock hard-binding blockers. The narrow person fact-lock advisory patch landed via PR #115, but full auto-frontier / strict 5-arc proof remains pending. |
| `security-secrets-config` | `docs/2026-04-27/security-secrets-config-execution-ssot.md` | `docs/temp/security-secrets-config-execution-ssot.md` | pending | Security P0 substrate; parked future wave. |
| `security-runtime-settings-vertex` | `docs/2026-04-27/security-runtime-settings-vertex-execution-ssot.md` | `docs/temp/security-runtime-settings-vertex-execution-ssot.md` | pending | Depends on `security-secrets-config`; parked future wave. |
| `security-desktop-release-guardrails` | `docs/2026-04-27/security-desktop-release-guardrails-execution-ssot.md` | `docs/temp/security-desktop-release-guardrails-execution-ssot.md` | pending | Depends on both prior security SSOTs; parked future wave. |

## 3. Dependency Graph

- `security-secrets-config -> security-runtime-settings-vertex`
- `security-secrets-config -> security-desktop-release-guardrails`
- `security-runtime-settings-vertex -> security-desktop-release-guardrails`
- `frontier-lag-clean-5arc-stabilization` is independent of the security remediation chain.
- #56, #59, #120, #121, #129, #130, and #134 have landed or closed as completed. They are no longer active temp queue blockers, but their canonical docs and GitHub issues remain historical evidence for Frontier Lag proof interpretation.

Shared substrate:
- security secret boundary must precede runtime path/auth and desktop/release guardrail implementation.
- runtime path authority must precede license/access-control persistence decisions.

Merge opportunities:
- #66 scanner guardrails can feed #69 release denylist checks.
- #68 path authority can feed #70 license/device file placement.
- #71 status documentation should summarize all three security execution docs after implementation facts exist.
- Completed #56/#59 work can feed the Frontier Lag strict 5-arc proof path by reducing genre-strategy drift and keeping proof/advisory evidence separated.

## 4. Execution Order

Priority basis:
- `docs/implementation/queue-priority-rubric.md`
- Existing queue continuity is preserved unless the operator explicitly moves security work to the front.
- Within the security chain, dependency order is strict.

Working order:

1. `frontier-lag-clean-5arc-stabilization` (front-active; implementation blockers removed; full auto-frontier / strict 5-arc proof pending)
2. `security-secrets-config` (parked future wave; security P0 substrate)
3. `security-runtime-settings-vertex` (parked future wave; depends on `security-secrets-config`)
4. `security-desktop-release-guardrails` (parked future wave; depends on `security-secrets-config` and `security-runtime-settings-vertex`)

## 5. Per-Item Plan

### frontier-lag-clean-5arc-stabilization

- goal: preserve the existing active stabilization queue item and do not silently demote it during security document intake.
- prerequisites: current-state re-audit completed, watchdog provider-wait classification hardening merged, bounded rerun identified Stage 3 replay-reroute plateau, and follow-up rerun identified person fact-lock hard-binding churn. Positive continuation retry feedback is implemented; person fact-lock advisory routing landed via PR #115. Next proof step is a bounded proof run only with explicit approval and runtime/cost caps.
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

## 6. Shared Risks and Side-Effects

- shared write paths: docs, `.gitignore`, `.gitattributes`, `.env.example`, config modules, provider modules, desktop files, build scripts, CI workflows.
- shared DB/schema touchpoints: not expected for security docs unless a future license/device store is implemented.
- shared logs/UI surfaces: scanner output, Electron/backend logs, auth/config errors, and security status docs must not expose secret values.
- rollback/recovery concerns: credential rotation and git-history rewrite require explicit owner approval; package denylist failures should fail closed and be easy to retry.
- queue collision or ordering risks: creating additional security, Stage3, or Stage4 SSOTs requires updating this roadmap before implementation.
- Stage4-specific shared side effects: `stage_attempts`, `director_selections`, `manuscripts`, `blueprints`, `episode_meta`, context cache attempts, rejected/selected artifacts, and runtime/session logs.
- Completed #56/#59 side effects remain relevant to Frontier Lag interpretation: prompt envelopes, candidate `_ensemble_meta`, Director prompt context, proof digest payloads, dashboard summaries, runtime-summary freshness labels, benchmark packets, and operator comparison lines.

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `frontier-lag-clean-5arc-stabilization` | active | 2026-04-30 | GitHub #57 reopened; strict full proof still pending |
| `security-secrets-config` | pending | 2026-04-27 | external credential rotation/history decision may block closure |
| `security-runtime-settings-vertex` | pending | 2026-04-27 | depends on `security-secrets-config`; path policy decision required |
| `security-desktop-release-guardrails` | pending | 2026-04-27 | depends on first two security items; access-control product model may remain residual |

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
- PASS. 2026-04-30 refresh includes all four active temp execution SSOT mirrors.

Pass 2 - evidence and consistency:
- PASS. Existing Frontier Lag mirror is preserved and not silently removed.
- PASS. Security dependencies match execution metadata blocks in the new SSOTs.
- PASS. Security items are marked as parked future wave, preventing accidental front-active interpretation.
- PASS. `stage3-genre-contract-resolver-fallback` is removed from the active temp queue only after PR #126 merged, issue #120 closed, and canonical closure evidence was added.
- PASS. Stage4 #58 is removed from the active temp queue only after GitHub #58 closure is reflected in the canonical #58 SSOT.
- PASS. Stage3/Stage4 #56 and Stage4 #59 are removed from the active temp queue only after their PRs merged, CI passed, and GitHub issues closed.

Pass 3 - execution readiness:
- PASS. The roadmap is actionable for queue control but explicitly does not authorize implementation without fresh re-audit.
- PASS. Cleanup behavior is explicit.
- PASS. The 2026-04-30 refresh is queue-control only; it does not authorize starting a fresh proof run or security realization without explicit operator approval.

Estimated operational confidence: 96%.

## 9.1 Superseded Queue Refresh - 2026-04-29

Pass 1 - inventory:
- SUPERSEDED. At that time, active temp execution mirrors were Frontier Lag, Stage3 genre-contract resolver fallback, and three parked security items.

Pass 2 - ordering:
- SUPERSEDED. The 2026-04-29 priority statement (#121 first, #120 second, #113 later) is no longer current. #120/#121/#113 are closed/completed and must not be treated as active queue targets.

Pass 3 - validator readiness:
- SUPERSEDED. Queue-state must now be regenerated from the 2026-04-30 roadmap state and should include four active execution items.

Estimated refresh confidence: 96%.

## 10. Operator Promotion Note - 2026-04-27

The operator promoted `stage4-post-select-conflict` ahead of the prior Frontier Lag default with the instruction to reduce bug risk first. That item is now closed on GitHub and retired from the active temp queue as historical backing only. The roadmap then treated `stage4-proof-digest-cove-advisory` (#59) as the active item because it had to separate proof evidence, advisory failures, stale summaries, and benchmark diagnostics before any new clean-run or benchmark claim.

Follow-up closure:
- #59 landed through PR #83, passed GitHub CI, and GitHub issue #59 is closed as completed.
- #56 landed through PR #84, passed GitHub CI, and GitHub issue #56 is closed as completed.
- Their canonical SSOTs remain historical backing; their temp mirrors are removed from the active queue.
- Frontier Lag is now the next queue item, but fresh implementation or proof execution still requires current-state 3-pass re-audit.

Retired item:
- `stage4-post-select-conflict` / GitHub #58: closed on GitHub, canonical SSOT retained, temp mirror removed from the active queue. This retirement does not authorize a clean 5-arc readiness claim.

## 11. Frontier Lag Merge Direction Note - 2026-04-28

The current merge candidate is the narrow `codex/frontier-lag-2arc-rerun-proof` branch, not a full proof closure.

3-pass queue note:

- Pass 1 - evidence: PASS. The latest bounded rerun produced enough evidence that Stage 3 person fact-lock hard binding can override Director PASS-like judgment and force repeated regeneration.
- Pass 2 - governance: PASS. The staged patch keeps Python as evidence collector and returns semantic person-lock judgment to Director review.
- Pass 3 - execution order: PASS. The narrow advisory patch landed through PR #115. GitHub `#57` was later auto-closed by PR `#115`, but that tracker closure must not be read as proof completion; the 2026-04-30 issue sync should reopen #57 and keep this roadmap item active until a later full auto-frontier proof or explicit closure wave.

Estimated roadmap confidence: 96%.

## 12. Queue Refresh - 2026-04-30

Reason: stale operator state cleanup requested after #120/#113/#134/#130/#129/#121 were found completed while the temp roadmap still named them as active or next-step targets.

Pass 1 - inventory:

- PASS. Active temp execution mirrors after cleanup are Frontier Lag plus three parked security execution items.
- PASS. `stage3-genre-contract-resolver-fallback` has canonical closure evidence and its temp mirror is removed.
- PASS. #57 is still the correct GitHub tracker for full auto-frontier / strict 5-arc proof, because existing issue comments and PR #115 explicitly say the proof is not closed.

Pass 2 - GitHub alignment:

- PASS. Closed issues should not keep `active` labels unless they are reopened as active trackers.
- PASS. #57 should be reopened and remain active.
- PASS. #113 and #41 should lose stale `active` labels.
- PASS. Open security issues #66-#71 correspond to parked security queue work, not front-active pipeline work.

Pass 3 - execution readiness:

- PASS. The roadmap now separates active proof pending work from completed historical issue lines.
- PASS. Security work remains parked and should not be promoted without explicit operator direction.
- PASS. ClickUp may be synced after repo-side queue-state regeneration and strict ops validation.

Estimated refresh confidence: 96%.
