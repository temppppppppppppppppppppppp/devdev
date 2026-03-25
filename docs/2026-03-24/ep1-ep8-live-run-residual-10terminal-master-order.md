# EP1-EP8 Live-Run Residual 10-Terminal Master Order

Date: 2026-03-24
Status: final (3-pass audited)
Document Type: system-track parallel survey master order
Canonical Path: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
Temp Mirror Path: none
Primary Evidence Run: `projects/0324_00_`
Reference Survey Order:
- `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md`
Related Closed Waves:
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
- `docs/2026-03-24/ep1-ep2-stage4-carryover-expansion-execution-ssot.md`
Evidence Anchors:
- `docs/2026-03-24/console.txt`
- `projects/0324_00_/logs/episode_production.jsonl`
- `projects/0324_00_/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`
- `projects/0324_00_/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_balanced.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_01/rejected_best__C_tension.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_01/selected_before_fix__B.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_01/rejected_best__A_tension.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0008/attempt_01/final_manuscript__A.txt`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; one active execution SSOT mirror remains in docs/temp, but this document is survey-only and must not touch temp queue state`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `single-lane residual survey order already created; latest console and 0324_00_ live-run artifacts now extend to episode 8`

## 1. Purpose

This document upgrades the single-lane residual survey into a 10-terminal parallel master order.

Goal:

- inspect the actual Stage 2, Stage 3, and Stage 4 artifacts directly
- inspect the live code that produced and judged them
- inspect the log and JSONL trail that records when and how the failures surfaced
- rank every still-plausible residual cause without prematurely collapsing everything into one seam

This is survey-only.

- no code changes
- no execution SSOT creation unless Codex explicitly promotes one after merge
- no temp queue edits
- no closure claims

## 2. Why Expand To 10 Lanes

The latest run reached episode 8, but it did not become clean.

Observed failure distribution:

- `ep2`: three post-select history-conflict downgrades before round 4 PASS
- `ep3`: one post-select continuity/history downgrade before round 2 PASS
- `ep5`: `PASS_WITH_FIX` plus two post-select rejects before round 3 PASS
- `ep6`: primary reject plus continuity-firewall downgrade before round 3 PASS
- `ep7`: `PASS_WITH_FIX` patched to PASS
- `ep8`: round 1 PASS

This means the remaining pathology is no longer one narrow `ep1 -> ep2` handoff seam only.
It now spans:

- Stage 2 account/state payload truth
- Stage 3 blueprint and `_inventory_gaps` synthesis
- Stage 4 carryover consumption and retry semantics
- continuity/history validator signal quality
- artifact-truth mismatches across episodes

So a broad, lane-split, artifact-first re-survey is justified.

## 3. Working Hypothesis

Do not treat this as final truth. It is only the starting watchlist.

Current candidate clusters:

1. `account/provenance carryover drift`
- trust-fund source drift
- corporate-capitalization spend drift
- `15억 vs 20억` usable-capital drift

2. `item/location/time carryover drift`
- leather note storage drift
- opening continuity drift
- timestamp regression after already-established movement

3. `inventory-gap pressure`
- `_inventory_gaps` may be acting as either:
  - a useful warning channel
  - or an ambiguous authority surface that pushes later item/state invention

4. `PASS_WITH_FIX vs post-select coexistence`
- some episodes receive `PASS_WITH_FIX` and still need later post-select rejection or repair
- this may be normal separation of concerns, or it may be a residual retry-architecture smell

5. `validator/advisory noise`
- repeated `[V66.1] opening continuity` warnings may be meaningful signal
- or they may be broad advisory noise that is not causal

## 4. Hard Constraints

- survey only; no code changes
- inspect real artifact bodies, not just summaries
- do not create or modify anything in `docs/temp/`
- do not close or refresh the active execution SSOT mirror already in temp
- do not assume the old covert-infrastructure seam is still primary
- do not assume Stage 2 density/ep-count ownership is primary unless live evidence proves it
- do not overclaim from console paraphrase when artifact truth disagrees
- every lane must mark weak claims as `not proven`

## 5. Survey Model

Every lane must classify findings into one or more of:

- `confirmed primary cause`
- `confirmed secondary amplifier`
- `mixed seam`
- `validator-only signal`
- `artifact-truth mismatch`
- `cleared / not primary`
- `not proven`

Every lane must also answer:

- `Can this lane explain a real residual failure by itself: yes/no`
- `Does this lane explain repeated rescue rounds after the closed waves: yes/no`
- `Would this lane justify a bounded next execution wave: yes/no`

## 6. Terminal Plan

Use 10 terminals. Each lane owns a disjoint slice of the live-run residual problem.

Reports should be saved under:
- `docs/2026-03-24/opus-live-run-residual/`

| Terminal | Lane | Primary Scope | Final Report Path | Optional Evidence Path |
|---|---|---|---|---|
| T1 | `Run Chronology` | `console.txt`, `episode_production.jsonl`, per-episode verdict chain, rescue-round ledger | `docs/2026-03-24/opus-live-run-residual/t1-run-chronology.md` | `docs/2026-03-24/opus-live-run-residual/t1-run-chronology-evidence.md` |
| T2 | `Stage2 Arc Truth` | Arc 1 and Arc 2 final arc artifacts, episode allocation, state payload, numeric/accounting setup | `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth.md` | `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth-evidence.md` |
| T3 | `Stage2 Validation Guardrails` | `stage2_validation_pipeline.py`, `arc_draft_validator.py`, `four_phase_arc_generator.py`, current guardrails and blind spots | `docs/2026-03-24/opus-live-run-residual/t3-stage2-validation-guardrails.md` | `docs/2026-03-24/opus-live-run-residual/t3-stage2-validation-guardrails-evidence.md` |
| T4 | `Stage3 Blueprint Authority` | ep2/3/5/6/7/8 blueprints, scene goals, integrated scenario, authority ordering, current-episode scope | `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority.md` | `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority-evidence.md` |
| T5 | `Inventory Gap Synthesis` | `_inventory_gaps` generation and downstream use, item-prerequisite warnings, item acquisition authority | `docs/2026-03-24/opus-live-run-residual/t5-inventory-gap-synthesis.md` | `docs/2026-03-24/opus-live-run-residual/t5-inventory-gap-synthesis-evidence.md` |
| T6 | `Stage4 Carryover Consumption` | writer prompt inputs, carryover packets, prior-manuscript truth, state replay vs new discovery | `docs/2026-03-24/opus-live-run-residual/t6-stage4-carryover-consumption.md` | `docs/2026-03-24/opus-live-run-residual/t6-stage4-carryover-consumption-evidence.md` |
| T7 | `Retry And PASS_WITH_FIX Semantics` | `stage4_reject_runtime.py`, `stage4_retry_runtime.py`, `stage4_interview_round.py`, `PASS_WITH_FIX` coexistence with post-select | `docs/2026-03-24/opus-live-run-residual/t7-retry-passwithfix-semantics.md` | `docs/2026-03-24/opus-live-run-residual/t7-retry-passwithfix-semantics-evidence.md` |
| T8 | `Validator Signal Quality` | continuity/history/firewall warnings, `[V66.1]` and `[V67]` signal quality, false-positive risk vs real conflict | `docs/2026-03-24/opus-live-run-residual/t8-validator-signal-quality.md` | `docs/2026-03-24/opus-live-run-residual/t8-validator-signal-quality-evidence.md` |
| T9 | `Artifact Truth Diff Ledger` | episode-by-episode diff from blueprint to rejected to patched to final manuscript for ep2/3/5/6/7 | `docs/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger.md` | `docs/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger-evidence.md` |
| T10 | `Cleared Non-Culprits` | old burner-phone seam, Stage2 density, ep-count ownership, semantic-carryover relapse, what can now be demoted | `docs/2026-03-24/opus-live-run-residual/t10-cleared-non-culprits.md` | `docs/2026-03-24/opus-live-run-residual/t10-cleared-non-culprits-evidence.md` |

## 7. Lane Questions

### T1. Run Chronology

- Which episodes actually consumed multiple rescue rounds, and for what conflict family?
- Where do verdict downgrades happen relative to Director primary pass or pass-with-fix?
- Which episodes became stable without hidden residual warning debt?

### T2. Stage2 Arc Truth

- Do the Arc 1 and Arc 2 artifacts already encode the provenance, capitalization, or usable-capital states that later drift?
- Is there any direct mismatch between Stage 2 numeric truth and what Stage 3/4 later write?
- Are the problematic facts already ambiguous before Stage 3 touches them?

### T3. Stage2 Validation Guardrails

- Which guardrails already exist for episode allocation, numeric continuity, and state specificity?
- Which Stage 2 fields remain totally unvalidated?
- Can Stage 2 be downgraded as non-primary for this run, or does it still emit materially ambiguous payloads?

### T4. Stage3 Blueprint Authority

- Do the troubled blueprints already contain the later conflicts?
- Which issues are:
  - hard contradiction already in the blueprint
  - only planning pressure
  - not present until Stage 4 prose
- Does integrated scenario or scene breakdown push the provenance/time/item drift?

### T5. Inventory Gap Synthesis

- How is `_inventory_gaps` built?
- Does it correctly say "not yet on page"?
- Or does it produce ambiguous authority that later gets mistaken for already-available truth?
- Is `_inventory_gaps` a useful warning system or a residual amplifier?

### T6. Stage4 Carryover Consumption

- After the closed carryover-expansion wave, what residual carryover failures remain?
- Are prior manuscript, prev digest, and carryover ceiling packets still missing critical state?
- Does Stage 4 replay already-finished discovery/calculation or transform warnings into active facts?

### T7. Retry And PASS_WITH_FIX Semantics

- Why do some episodes still combine `PASS_WITH_FIX` and later post-select conflict?
- Is the runtime correctly separating local-fix and hard-conflict families?
- Is any retry path still too patch-biased or semantically leaky?

### T8. Validator Signal Quality

- Are repeated `[V66.1] opening continuity` warnings mostly valid?
- Are `History Conflict`, `Continuity Conflict`, and `continuity_firewall` judgments well-grounded in artifact truth?
- Is validator overreach a real cause here or mostly noise?

### T9. Artifact Truth Diff Ledger

- For ep2, ep3, ep5, ep6, and ep7:
  - what the blueprint said
  - what the rejected manuscript said
  - what the final/patch manuscript said
- Where does each conflict first become undeniable?

### T10. Cleared Non-Culprits

- What previously suspected causes are now demoted by the 8-episode run?
- Is the old covert-infrastructure seam still alive at all?
- Should Stage 2 density or ep-count ownership remain open, or are they now clearly follow-up-only?

## 8. Required Output Contract

Each lane writes:

- one final markdown report
- one optional raw evidence ledger

Common report sections:

1. Executive Summary
2. Included Coverage / Exclusions
3. Key Evidence
4. Findings Ranked
5. Cleared Non-Culprits
6. Residual Culprit Candidate
7. Next-Scope Recommendation
8. Confidence And Limits

Mandatory final lines in every lane report:

- `Can this lane explain a real residual failure by itself: yes/no`
- `Does this lane explain repeated rescue rounds after the closed waves: yes/no`
- `Would this lane justify a bounded next execution wave: yes/no`

Lane agents must not create:

- execution SSOTs
- temp queue artifacts
- merge audits
- closure notes

## 9. Read Order

Every terminal should read these first:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`
4. `docs/implementation/document-3pass-audit-harness.md`
5. `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md`
6. `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
7. `docs/2026-03-24/console.txt`
8. `projects/0324_00_/logs/episode_production.jsonl`

## 10. Common Opus Prompt

Use this common launch prompt. Only substitute the lane-specific values from section 11.

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md
6. docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md
7. docs/2026-03-24/console.txt
8. projects/0324_00_/logs/episode_production.jsonl

Task:
Run a bounded residual live-run survey for LANE_NAME on `projects/0324_00_` through episode 8.

Primary goal:
Determine whether this lane contains a real remaining cause of the rescue-round failures that survived the earlier closed waves.

Hard constraints:
- Survey only. No code changes.
- Inspect real artifact bodies, not just log summaries.
- Do not create execution SSOTs, temp queue items, merge audits, or closure notes.
- Prefer live artifact truth over console paraphrase.
- Do not overclaim. Mark weak claims as `not proven`.
- Do not default back to the old covert-infrastructure seam unless this lane proves it with current run evidence.
- Do not default back to Stage 2 density or ep-count redesign unless this lane proves it is primary again.
- Workspace is dirty. Do not revert unrelated edits.

Primary scope:
PRIMARY_SCOPE

Required outputs:
- Final report: FINAL_REPORT_PATH
- Optional evidence ledger: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. Included Coverage / Exclusions
3. Key Evidence
4. Findings Ranked
5. Cleared Non-Culprits
6. Residual Culprit Candidate
7. Next-Scope Recommendation
8. Confidence And Limits

Mandatory final lines:
- Can this lane explain a real residual failure by itself: yes/no
- Does this lane explain repeated rescue rounds after the closed waves: yes/no
- Would this lane justify a bounded next execution wave: yes/no

Document rule:
- Run a document 3-pass audit before saving.
- If confidence is 95% or higher, save status as final.
- If confidence is below 95%, save status as provisional.

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH

In your final response:
- findings first
- then residual culprit candidate
- then confidence
- then one bounded next-scope recommendation
```

## 11. Terminal Overrides

| Terminal | LANE_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
|---|---|---|---|---|
| T1 | `Run Chronology` | `docs/2026-03-24/console.txt, projects/0324_00_/logs/episode_production.jsonl, live rescue-round chain, verdict downgrades, pathology rows` | `docs/2026-03-24/opus-live-run-residual/t1-run-chronology.md` | `docs/2026-03-24/opus-live-run-residual/t1-run-chronology-evidence.md` |
| T2 | `Stage2 Arc Truth` | `projects/0324_00_/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json, projects/0324_00_/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json, account/provenance/capital state setup` | `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth.md` | `docs/2026-03-24/opus-live-run-residual/t2-stage2-arc-truth-evidence.md` |
| T3 | `Stage2 Validation Guardrails` | `modules/core/stage2_validation_pipeline.py, modules/domain/agents/arc_draft_validator.py, modules/domain/agents/four_phase_arc_generator.py, Stage 2 blind spots vs current failures` | `docs/2026-03-24/opus-live-run-residual/t3-stage2-validation-guardrails.md` | `docs/2026-03-24/opus-live-run-residual/t3-stage2-validation-guardrails-evidence.md` |
| T4 | `Stage3 Blueprint Authority` | `projects/0324_00_/logs/artifacts/stage3/ep_0002..ep_0008 final blueprints, scene breakdown, integrated scenario, provenance/time/item pressure` | `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority.md` | `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority-evidence.md` |
| T5 | `Inventory Gap Synthesis` | `modules/core/stage3_orchestrator.py _detect_inventory_gaps, chief_writer_context_packets inventory sections, ep2/5/7 inventory-gap truth and downstream effects` | `docs/2026-03-24/opus-live-run-residual/t5-inventory-gap-synthesis.md` | `docs/2026-03-24/opus-live-run-residual/t5-inventory-gap-synthesis-evidence.md` |
| T6 | `Stage4 Carryover Consumption` | `modules/domain/agents/chief_writer_context_packets.py, chief_writer_context.py, chief_writer_prompts.py, stage4 carryover packet consumption in the troubled episodes` | `docs/2026-03-24/opus-live-run-residual/t6-stage4-carryover-consumption.md` | `docs/2026-03-24/opus-live-run-residual/t6-stage4-carryover-consumption-evidence.md` |
| T7 | `Retry And PASS_WITH_FIX Semantics` | `modules/core/stage4_reject_runtime.py, modules/core/stage4_retry_runtime.py, modules/core/stage4_interview_round.py, pass-with-fix plus post-select coexistence` | `docs/2026-03-24/opus-live-run-residual/t7-retry-passwithfix-semantics.md` | `docs/2026-03-24/opus-live-run-residual/t7-retry-passwithfix-semantics-evidence.md` |
| T8 | `Validator Signal Quality` | `modules/validation/continuity_validator.py, history/continuity/firewall messages, [V66.1]/[V67] signal quality versus artifact truth` | `docs/2026-03-24/opus-live-run-residual/t8-validator-signal-quality.md` | `docs/2026-03-24/opus-live-run-residual/t8-validator-signal-quality-evidence.md` |
| T9 | `Artifact Truth Diff Ledger` | `ep2, ep3, ep5, ep6, ep7 blueprint -> rejected -> patched/final manuscript diffs with first undeniable conflict markers` | `docs/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger.md` | `docs/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger-evidence.md` |
| T10 | `Cleared Non-Culprits` | `old covert-infrastructure seam, Stage2 density, ep-count ownership, semantic-carryover relapse, what the 8-episode run demotes` | `docs/2026-03-24/opus-live-run-residual/t10-cleared-non-culprits.md` | `docs/2026-03-24/opus-live-run-residual/t10-cleared-non-culprits-evidence.md` |

## 12. Dispatch One-Liners

Use the user-preferred format: `path + 넌 n번 터미널`.

- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 1번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 2번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 3번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 4번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 5번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 6번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 7번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 8번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 9번 터미널`
- `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md + 넌 10번 터미널`

## 13. Codex Merge Rule

Lane agents stop at their own reports.

Codex owns:

- stale-claim cleanup
- duplicate-finding merge
- true primary-cause ranking
- deciding whether the next step is:
  - no action
  - another compact survey
  - one bounded execution SSOT
  - or one small paired-wave execution split

Lane agents must not create the merge audit or the next execution SSOT.

## 14. 3-Pass Audit Record

- Pass 1
  - confirmed this is a survey master order, not an execution SSOT
  - confirmed the broadened scope matches the user's request for exhaustive residual-cause inspection
- Pass 2
  - confirmed the lane split is grounded in current `0324_00_` live-run evidence rather than stale pre-run assumptions
  - confirmed canonical/temp semantics are correct for a survey-only artifact
- Pass 3
  - confirmed the lanes cover both code and real artifact bodies
  - confirmed the output contract blocks premature implementation and preserves Codex as merge owner

## 15. Confidence

- Confidence: 97%
- Basis:
  - the 8-episode live run exposes multiple residual failure families, not one single narrow seam
  - 10-way lane decomposition is justified and bounded
  - actual artifact bodies, code paths, and runtime logs are all explicitly included
