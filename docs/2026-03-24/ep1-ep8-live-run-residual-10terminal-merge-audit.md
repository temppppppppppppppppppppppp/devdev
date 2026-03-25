# EP1-EP8 Live-Run Residual 10-Terminal Merge Audit

Date: 2026-03-24
Status: final (3-pass audited, post-run merge)
Canonical Path: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-merge-audit.md`
Primary Evidence Run: `projects/0324_00_`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: live-run logs/db plus survey docs; temp queue still held one realized Stage4 mirror`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
- `docs/2026-03-24/opus-live-run-residual/t1-run-chronology.md`
- `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth.md`
- `docs/2026-03-24/opus-live-run-residual/t2-dominant-seam-delta.md`
- `docs/2026-03-24/opus-live-run-residual/t3-stage2-validation-guardrails.md`
- `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority.md`
- `docs/2026-03-24/opus-live-run-residual/t5-inventory-gap-synthesis.md`
- `docs/2026-03-24/opus-live-run-residual/t6-stage4-carryover-consumption.md`
- `docs/2026-03-24/opus-live-run-residual/t7-retry-passwithfix-semantics.md`
- `docs/2026-03-24/opus-live-run-residual/t8-validator-signal-quality.md`
- `docs/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger.md`
- `docs/2026-03-24/opus-live-run-residual/t10-cleared-non-culprits.md`
Lower-Authority Reference Only:
- `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md`
Evidence Artifacts:
- `projects/0324_00_/logs/episode_production.jsonl`
- `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0004/attempt_01/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_01/selected_before_fix__B.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_01/rejected_best__A_tension.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0008/attempt_01/final_manuscript__A.txt`
Side-Effect Coverage:
- Stage 2 arc truth vs Stage 3 handoff
- Stage 3 blueprint prompt and prevalidation surfaces
- Stage 4 carryover consumption and retry behavior
- validator / post-select / firewall downgrade semantics
- inventory-gap advisories
- no code realization in this merge document

---

## 1. Executive Summary

10-lane merge plus live artifact re-check shows that the current residual culprit is not Stage 2, validator overreach, retry semantics, `_inventory_gaps`, or the old covert-infrastructure seam.

The dominant residual seam is now:

1. **Stage 3 blueprint state-precision / authority drift**
   - EP2 trust provenance flips at blueprint stage.
   - EP3 notebook storage drift is already in the blueprint.
   - EP7 ending-hook temporal phrase drift is already in the blueprint.
   - EP6 blueprint still hands Stage 4 a stale capital/deployment picture.
2. **Stage 4 manuscript expansion over stale or under-specified state**
   - EP5 turns a loose financial baseline into explicit arithmetic contradiction.
   - EP6 invents `4월 18일`, `20억 법인 자금`, and corporate infrastructure beyond accepted state.
   - EP8 still reproduces one uncaught `18년` future-memory phrasing residue.

The next bounded execution wave should therefore be a **Stage 3 state-precision reconciliation wave**, not another Stage 4 or Stage 2 redesign wave.

---

## 2. Included Coverage / Exclusions

Included:
- all 10 lane reports under `docs/2026-03-24/opus-live-run-residual/`
- the T2 dissent note as a non-canonical but material contradiction ledger
- completed live-run artifacts for EP1-EP8
- direct spot-check of blueprint and manuscript bodies for EP2, EP3, EP5, EP6, EP7, EP8
- `episode_production.jsonl` verdict chains and downgrade reasons
- Stage 3 code owners:
  - `modules/core/stage3_orchestrator.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/unified_blueprint_validator.py`

Excluded:
- new realization work in this document
- roadmap creation beyond the immediate next execution item
- narrative-quality judgment beyond conflict origination and authority tracing

---

## 3. Merge Findings

### 3.1 Stage 3 Blueprint Drift Is the Dominant Residual Seam

Direct artifact checks move the dominant seam upstream.

- EP2 blueprint hard-codes `조부 명의 HMC 신탁` while EP1 final manuscript establishes `어머니가 남겨준 자산` plus mixed-source seed capital. The writer followed the wrong blueprint for three rounds before recovery.
- EP3 blueprint explicitly says the notebook is stored in `서랍 깊숙한 곳`. The production log then explicitly records that the blueprint `서랍 보관` error was corrected to `금고 보관`.
- EP7 blueprint ending hook itself contains `18년 전 ... 파산의 환상통`. This is not a pure Stage 4 invention.
- EP6 blueprint still frames the episode as if a fresh `19억 3천만 원` deployment decision remains available, even though EP5 final manuscript already committed the full 19억 class capital into the WTI position.

The common pattern is not generic carryover failure. It is **already-settled facts losing authority when Stage 3 rewrites them into new blueprint obligations**.

### 3.2 Stage 4 Expansion Still Matters, but Mostly as a Secondary Multiplier

Stage 4 is not cleared. It is just no longer the best first patch target.

- EP5 selected manuscripts turn a loose financial baseline into explicit `480계약`, `3배 레버리지`, and `19억` arithmetic contradictions.
- EP6 rejected manuscript invents `2006년 4월 18일`, `20억 법인 자금`, `법인 통장`, and personal-to-corporate fund conflation that are not acceptable even under the stale blueprint baseline.
- EP8 final manuscript still passes with one uncaught `18년 전 파산` style residue, showing Stage 4 can still echo bad temporal phrasing when Blueprint authority leaves it available.

This is a real residual seam, but the recent run shows Stage 4 is often consuming or amplifying already-wrong Stage 3 state rather than originating the first conflict.

### 3.3 Stage 2, Validators, Retry, and Inventory Gaps Are Not the Current Primary Cause

Cross-lane consensus plus live evidence clears the following as non-primary for this run:

- Stage 2 arc structure, density, and ep-count ownership
- validator overreach
- PASS_WITH_FIX / post-select coexistence semantics
- `_inventory_gaps` as a rescue-round driver
- old burner-phone / offshore / paper-company invention seam
- broad semantic-carryover relapse

These may still contain low-priority hygiene work, but they do not explain the current rescue-round pattern.

---

## 4. Episode Attribution Ledger

| Episode | First undeniable conflict | Merge classification | Notes |
| --- | --- | --- | --- |
| EP2 | Blueprint provenance drift | Stage 3 primary | `조부 명의` blueprint authority contradicts EP1 canon |
| EP3 | Blueprint notebook storage drift | Stage 3 primary | writer first follows blueprint, later overrides to canon |
| EP5 | Arithmetic / leverage contradiction on top of loose money state | Mixed, Stage 4 primary / Stage 3 secondary | Stage 3 supplies stale/aggressive financial baseline; Stage 4 makes it explicit and contradictory |
| EP6 | Blueprint stale capital/deployment baseline plus manuscript inventions | Mixed, Stage 4 primary / Stage 3 secondary | `4월`, `20억 법인 자금`, `법인 통장` are Stage 4; stale deployment ambiguity is already upstream |
| EP7 | Blueprint ending-hook temporal phrase drift | Stage 3 primary | fixed by PASS_WITH_FIX, but origin is blueprint hook |
| EP8 | Round-1 pass with one uncaught temporal residue | Monitor only | not enough to reopen Stage 4 first |

Merged weighting:

- Stage 3 primary: EP2, EP3, EP7
- Stage 4 primary: EP5, EP6
- compound financial-state participation: EP5, EP6

This is still a mixed family, but it is **not equal-weight mixed**. The next ROI wave is upstream because Stage 3 is producing the earliest authoritative conflicts for the highest-value fixes.

---

## 5. Cleared Non-Culprits

- `T2/T3`: Stage 2 arc artifacts and guardrails do not justify a Stage 2 execution wave right now.
- `T5`: `_inventory_gaps` is noisy but not causal for the repeated rejects.
- `T7`: retry and PASS_WITH_FIX semantics are operating as designed; patch-bias is not the dominant issue anymore.
- `T8`: verdict-flipping validators are catching real contradictions, not inventing them.
- `T10`: old covert-infrastructure seam and broad semantic-carryover relapse are no longer the lead problem family.

---

## 6. Merge Decision

### 6.1 Dominant Seam

**Dominant seam: Stage 3 blueprint state-precision / authority drift primary, Stage 4 manuscript expansion secondary.**

### 6.2 Immediate Next Execution Shape

Open one bounded Stage 3 execution wave only:

- inject compact high-authority fact locks into blueprint generation
- reconcile blueprint output against previous accepted manuscript state before Director compare
- add bounded capital/deployment continuity checks for investment-fiction episodes
- catch relative-time ending-hook phrases such as `18년 전` when they contradict the run's established viewpoint

### 6.3 Queue Consequence

The older Stage 4 carryover-expansion item should be closure-audited now. Its intended seam is no longer the dominant residual family in live evidence, and its key target (covert infrastructure invention) was materially suppressed in the fresh run.

---

## 7. Confidence And Limits

### Confidence: 96%

Why above 95:
- all high-severity attribution shifts were re-checked against live artifacts, not just lane prose
- EP2, EP3, and EP7 blueprint-origin defects are directly observable on disk
- EP6 mixed attribution is directly observable on disk
- the non-culprit lanes agree strongly and are supported by run logs

Limits:
- EP5 weighting is the least certain case because Stage 2 arc truth, accepted prior manuscript truth, and Stage 4 explicit arithmetic all diverge on different axes
- the shared single-report file is lower authority because it was overwritten during parallel work and contains stale weighting
- this merge audit is for the `0324_00_` run through EP8 only

---

## 8. 3-Pass Audit Record

- Pass 1: scope and authority paths revalidated against the 10-lane master order and current temp queue
- Pass 2: contradictory lane claims were checked against live blueprint/manuscript artifacts before synthesis
- Pass 3: only one bounded next wave was kept; Stage 2, validator, retry, and inventory side quests were trimmed out

---

## Mandatory Final Lines

- Dominant seam: **Stage 3 blueprint state-precision / authority drift primary, Stage 4 manuscript expansion secondary**
- Are the repeated rejects mostly valid: **yes**
- Should Codex open the next execution SSOT immediately: **yes**
- Should the prior Stage4 carryover execution item be closure-audited now: **yes**
