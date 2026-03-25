# EP5-EP7 Mid-Arc Residual 6-Terminal Merge Audit

Date: 2026-03-24
Status: final (3-pass audited, post-run merge)
Document Type: system-track merge audit
Canonical Path: `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-merge-audit.md`
Primary Evidence Run: `projects/0324_00_`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: live-run logs/db plus prior survey docs; temp queue empty before this merge`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t1-run-chronology-and-sinks.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t2-db-and-metadata-truth.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t3-stage3-blueprint-truth.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t4-stage4-manuscript-expansion.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t5-validator-retry-semantics.md`
- `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t6-capital-time-item-diff-ledger.md`
Evidence Artifacts:
- `docs/2026-03-24/console.txt`
- `projects/0324_00_/logs/episode_production.jsonl`
- `projects/0324_00_/project_data.db`
- `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_02/patched_after_fix__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0004/attempt_01/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt`
Side-Effect Coverage:
- console / JSONL / DB sink reconciliation
- Stage 3 blueprint authority
- Stage 4 manuscript expansion
- validator / retry semantics
- no realization in this merge document

---

## 1. Executive Summary

The remaining EP5-EP7 rescue rounds are no longer best explained by a broad `mid-arc continuity residual` label.

The merged culprit family is narrower:

1. **Stage 3 blueprint carry-forward drift is the dominant residual seam**
- EP5 blueprint starts from stale capital state (`19억 3천만 원`) instead of the EP4 accepted baseline (`19억 원` after the deposit deduction).
- EP6 blueprint reopens a phantom available-capital state via `19억 3천만 원이 예치된 계좌 내역` even though EP5 already committed the capital into WTI.
- EP6 and EP7 blueprints drift institutional authority from EP3 accepted canon (`HMC투자증권 VVIP PB센터`) to `한미증권 본사 VVIP 프라이빗 룸`.
- EP7 blueprint still carries the stale capital/equipment surface and `18년 전` temporal phrasing.

2. **Stage 4 remains a secondary amplifier**
- EP6 Stage 4 adds arithmetic and timeline drift on top of the already-wrong blueprint state.
- EP7 has one real Stage 4-only seam candidate: narration / POV quality drift during rescue, but it is not the dominant family.

3. **Sink reconciliation is a real observability issue, but not the next culprit wave**
- console, JSONL, and DB do not always present the same round/score story
- this impairs diagnosis, but it is not the best first execution target while the Stage 3 carry-forward seam is still producing real content defects

Operational conclusion:

- the next bounded execution wave should be **Stage 3 only**
- target: **NPC/institution fact-lock + capital carry-forward + Stage 3 prevalidation coverage**
- defer sink reconciliation and Stage 4-only hardening until after one more fresh run

---

## 2. Included Coverage / Exclusions

Included:
- all six lane reports
- direct artifact re-check of EP3 accepted truth, EP4 accepted truth, EP5/EP6/EP7 blueprints, and EP6/EP7 accepted Stage 4 outputs
- direct `episode_production.jsonl` and `project_data.db` spot checks

Excluded:
- code changes
- temp queue mutation in this document
- new Stage 4 execution wave
- sink-observability realization

---

## 3. Merge Findings

### 3.1 Stage 3 Is the Dominant Residual Seam

This is the highest-confidence merged finding.

- EP3 accepted truth establishes `HMC투자증권` / `VVIP PB센터` as the institutional authority surface.
- EP6 blueprint replaces that with `한미증권 본사 VVIP 프라이빗 룸`.
- EP7 blueprint inherits the same drift.
- EP5 blueprint still starts from stale capital (`1,930,000,000원`) instead of the EP4 accepted post-deduction state.
- EP6 and EP7 blueprints continue to expose `19억 3천만 원이 예치된 계좌 내역` after the capital should already be deployed.

This is not a pure Stage 4 hallucination family. The blueprint itself is wrong or stale before Stage 4 expands it.

### 3.2 Stage 4 Is a Secondary Amplifier, Not the Best First Fix

Stage 4 is not cleared, but it is not the dominant current owner.

- EP6 rejected manuscript adds arithmetic / timeline damage beyond the blueprint.
- EP7 likely incurred one local Stage 4 rescue seam around style/POV quality.
- However, Stage 4 is often repairing or overriding already-wrong Stage 3 authority, not originating the first contradiction.

So another Stage 4-first wave would be lower ROI than a Stage 3 carry-forward wave.

### 3.3 Sink Mismatch Is Real but Deferred

The six lanes uncovered credible sink mismatch symptoms:

- console vs JSONL round count disagreement
- score disagreement across console / JSONL / DB
- incomplete visibility of some rescue-path events

This is action-bearing, but still secondary.

Why it is deferred:

- it does not by itself create the rescue rounds
- the content errors are already visible in blueprint/manuscript truth
- fixing sink fidelity first would improve diagnosis more than content correctness

### 3.4 What Is Cleared or Demoted

The following are not the dominant residual family for this run:

- Stage 2 density / ep_count ownership
- old covert-infrastructure seam
- validator overreach as the main cause
- `_inventory_gaps` as a primary driver

They may still exist as background noise, but they are not the next culprit wave.

---

## 4. Evidence-Led Episode Attribution

### EP5

Primary:
- Stage 3 stale capital baseline (`19억 3천만 원` instead of accepted `19억 원`)

Secondary:
- Stage 4 arithmetic / formatting / local continuity cleanup

Interpretation:
- mixed, but Stage 3 starts the money-state drift

### EP6

Primary:
- Stage 3 institutional drift (`HMC투자증권` -> `한미증권`)
- Stage 3 phantom available-capital surface (`19억 3천만 원이 예치된 계좌 내역`)

Secondary:
- Stage 4 arithmetic and timeline drift on top of that stale state

Interpretation:
- strongly Stage 3 primary

### EP7

Primary:
- Stage 3 inherited institutional drift
- Stage 3 inherited phantom capital/equipment surface
- Stage 3 temporal phrasing residue (`18년 전`)

Secondary:
- one likely Stage 4 style/POV rescue seam

Interpretation:
- Stage 3 primary, Stage 4 local amplifier

---

## 5. Merge Verdict

**Dominant seam**: Stage 3 blueprint carry-forward / authority drift

**Secondary seam**: Stage 4 manuscript expansion over stale or under-specified blueprint truth

**Deferred seam**: sink reconciliation / observability fidelity

**Recommended next step**: open one bounded Stage 3 execution wave for:
- NPC / institution fact-lock anchors
- capital carry-forward fallback extraction from free-text blueprint surfaces
- Stage 3 prevalidation checks for institution drift and phantom available-capital drift

---

## 6. Next Execution Scope Decision

Execution SSOT promotion is justified.

Why confidence is above the threshold:

- all six lanes converge on a Stage 3-heavy explanation
- direct artifact re-check confirms the core Stage 3 drifts
- the proposed fix boundary is narrow and excludes Stage 4/sink redesign

The next execution wave should explicitly exclude:

- Stage 4 retry redesign
- console/JSONL/DB observability repair
- Stage 2 density or ep_count redesign

---

## 7. Residual Risks

1. Console / JSONL / DB sink disagreement still makes post-run diagnosis noisier than it should be.
2. EP7 retry-path semantics remain somewhat opaque in the sinks even though the content culprit family is clearer.
3. After the next Stage 3 wave, a fresh run will still be required before deciding whether a separate sink-observability wave is warranted.
