# OPUS Modification-Governing 3-Pass Re-Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: docs/제안서_0318 tracked deletes/mods; untracked: bash.exe.stackdump, docs/제안서_0318/재무팀_비용회수_분석.md`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-18/OPUS/ssot/*.md`
- `docs/2026-03-18/OPUS/ssot_execution/*.md`
Evidence Basis:
- live workspace code and file inventory
- frontend/electron live files under `geuldobi-desktop/src/`
- direct code checks on Stage 0-4, validation, metrics, and vector-memory paths
Scope:
- bounded re-audit for modification governance only
- goal: decide which OPUS docs may inform code changes and which must not govern patching
- non-goal: exhaustive re-audit of every narrative/artifact claim in project-specific documents

---

## Pass 1. Structure and Scope

Audit target:
- `docs/2026-03-18/OPUS/ssot/` 7 SSOT docs
- `docs/2026-03-18/OPUS/ssot_execution/` 8 execution docs

Operating rule for this re-audit:
- treat OPUS documents as untrusted until revalidated against live code
- separate `document governance fitness` from `claim-level factual truth`
- prefer current workspace evidence over OPUS wording when they diverge

Structural findings:
- none of the OPUS SSOT or execution docs contain the current harness-required minimal commit-state metadata
- none of the OPUS execution docs declare canonical/temp mirror semantics
- `docs/temp/` has no active execution mirrors for the OPUS execution set; only `README.md` is present
- therefore the OPUS execution docs are not safe to use as-is as queue-governing execution authority under the current workspace governance

Pass 1 conclusion:
- OPUS can be used only after per-doc trust classification
- any later patching must use a fresh, current-state-governed execution document or a fresh revalidation of the chosen source doc

---

## Pass 2. Evidence and Consistency

### Bundle-level findings

1. S1 is stale at the count/header level.
- Live counts: `modules=247`, `tests=323`, `scripts=37`, `core=162`, `agents=47`, `main_a.py=4891`
- S1 still reports older counts in several places and also retains duplicate section number `## 2`

2. S2 is mostly grounded but has an internal inconsistency.
- Opener says `12 ErrorEnvelope codes`
- detailed inventory and live code support `13`
- topology claims such as `25 live IPC + 1 dead-candidate`, `8 REST + 1 WS`, and the direct renderer network surfaces are live

3. S3 factual core is grounded, but header metadata is stale.
- live frontend line counts are `index.html=8266`, `main.js=1009`, `preload.js=96`, `splash.js=89`
- S3 still carries older off-by-one counts
- key execution issue `sanitizeProjectName` path traversal is live

4. S4 has real claims, but its own confidence gate is below workspace authority threshold.
- the SSOT carries 93% confidence
- the execution doc explicitly depends on 93% / 86% upstream confidence sources
- under the workspace 95% gate, S4 may inform planning but must not govern patching directly

5. S5 mixes valid live defects with stale execution items.
- live verified: `generate_bible` empty-dict return, `ConstraintDB` degraded silent load/fallback risk, `FactLedger` degraded-load fallback, `Analyst` markerless silent return
- stale: `EX-32` claims Stage 2 Arc save non-atomicity as if unresolved, but current code already contains rollback/state-rollback handling on commit failure

6. S6 contains at least one materially false premise.
- S6 claims `quality_risk` is write-only and unused in Stage 4
- live code already consumes `quality_risk` in Stage 4 paths
- several other S6 issues remain live, but that false premise is enough to demote S6 from governing authority

7. S7 top action-bearing defects remain live.
- Stage 2/3 `record_attempt()` still omit `token_cost`
- Stage 3 timing is computed but not propagated into the monitor call path as intended
- `quality_risk` mismatch across three sites remains live

8. S8 is not allowed to govern code patching.
- the document explicitly states `코드 수정 금지`
- it mixes code issues with project-specific artifact/narrative truth
- this re-audit only spot-validated a few code claims, not the full artifact layer

### Per-document classification

| Doc | Classification | Reason |
| --- | --- | --- |
| `OPUS/ssot/s1-architecture-overview.md` | `STALE` | stale counts + duplicate section numbering |
| `OPUS/ssot_execution/s1-architecture-execution.md` | `STALE` | depends on stale S1 counts and already-completed line-ending items |
| `OPUS/ssot/s2-be-fe-connectivity.md` | `VALID` | topology mostly matches live code; opener count inconsistency is bounded |
| `OPUS/ssot_execution/s2-be-fe-execution.md` | `VALID` | execution items map to live frontend/backend surfaces |
| `OPUS/ssot/s3-frontend-electron.md` | `STALE` | header metadata drift; main claims still mostly real |
| `OPUS/ssot_execution/s3-frontend-execution.md` | `VALID` | key items, including FE-H01, still live and actionable |
| `OPUS/ssot/s4-llm-integration.md` | `ADVISORY` | factual core present, but confidence gate below 95% |
| `OPUS/ssot_execution/s4-llm-integration-execution.md` | `ADVISORY` | depends on below-threshold upstream confidence |
| `OPUS/ssot/s5-stage0-2-internals.md` | `VALID` | strong evidence map for current Stage 0-2 risks |
| `OPUS/ssot_execution/s5-stage0-2-execution.md` | `STALE` | contains at least one obsolete execution item (`EX-32`) |
| `OPUS/ssot/s6-stage3-4-crosscut.md` | `STALE` | `quality_risk write-only` premise is false |
| `OPUS/ssot_execution/s6-stage3-4-execution.md` | `STALE` | `EX-03` premise is false; other items need per-item revalidation |
| `OPUS/ssot/s7-rol-static-improvement.md` | `VALID` | top action-bearing findings still match live code |
| `OPUS/ssot_execution/s7-rol-improvement-execution.md` | `VALID` | G1/G2/OPP-05 remain live and execution-relevant |
| `OPUS/ssot_execution/s8-0_260318-project-deepdive-execution.md` | `NO-TRUST` | explicit code-modification ban + mixed artifact/code scope + incomplete bounded re-audit |

---

## Pass 3. Modification Consequence

### What may inform code changes now

Usable as planning inputs after current-state verification:
- `s2-be-fe-execution.md`
- `s3-frontend-execution.md`
- `s7-rol-improvement-execution.md`
- `s5-stage0-2-internals.md` as an evidence map, not as direct patch authority

### What must not govern patching directly

Do not patch straight from these docs:
- `s4-llm-integration.md`
- `s4-llm-integration-execution.md`
- `s5-stage0-2-execution.md`
- `s6-stage3-4-crosscut.md`
- `s6-stage3-4-execution.md`
- `s8-0_260318-project-deepdive-execution.md`

Reason:
- stale premises, stale items, or below-threshold confidence

### Verified live issues worth carrying forward

High-signal live issues that survived re-audit:
- S3 `sanitizeProjectName` path traversal
- S5 `generate_bible` empty dict return on protagonist generation failure
- S5 `ConstraintDB` degraded silent load/fallback risk
- S5 `FactLedger` degraded-load fallback without explicit degraded contract
- S5 `Analyst` markerless silent return on general exception
- S6 `director_ensemble.py` quality_risk mismatch for `PASS_WITH_WARNING`
- S6 manuscript-loss window before file write on DB failure
- S6 `WorldState.save()` / `FactLedger.save()` return values ignored
- S6 `ChainOfVerification` fail-open behavior
- S6 `degraded_checks` produced but not consumed downstream
- S7 Stage 2/3 `token_cost` omission
- S7 Stage 3 timing propagation gap

### Guardrails before any code modification

1. Do not use OPUS execution docs as queue authority in their current form.
2. For any chosen fix, create or refresh a fresh execution document anchored to the current workspace state.
3. Exclude `s8-0_260318-project-deepdive-execution.md` from code modification governance.
4. Treat S4 as advisory only until its claims are rebuilt into a 95%+ current-state document.
5. Revalidate each chosen issue against live code immediately before patching, even if its source doc is classified `VALID`.

---

## Confidence Gate

Estimated confidence for the bounded purpose of `modification governance`: **96%**

Why this clears 95%:
- bundle-level classifications are grounded in live code checks
- stale/wrong authority surfaces were identified conservatively
- scope is explicitly bounded to patch-governance safety, not to full narrative/artifact truth

Residual uncertainty:
- S8 artifact/narrative claims were not fully re-audited in this pass
- some S4 low-priority items were sampled rather than exhaustively re-verified
