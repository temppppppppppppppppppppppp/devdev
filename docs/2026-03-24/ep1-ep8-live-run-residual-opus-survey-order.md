# EP1-EP8 Live-Run Residual Opus Survey Order

Date: 2026-03-24
Status: survey-only
Canonical Path: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md`
Primary Evidence Run: `projects/0324_00_`
Related Closed Waves:
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
- `docs/2026-03-24/ep1-ep2-stage4-carryover-expansion-execution-ssot.md`

## 1. Purpose

Run one fresh Opus survey against the latest live run through episode 8 and determine the dominant remaining residual seam after the earlier Stage 2 -> 3 boundary fixes and Stage 4 carryover-expansion fix.

This is survey only.

- no code changes
- no execution SSOT creation unless confidence reaches 95%+
- no temp queue edits
- no closure claims

## 2. Why This Survey Exists

The latest live run materially improved the earlier `ep1 overconsumption -> ep3/ep4 collapse` pattern and suppressed the earlier Stage 4 covert-infrastructure invention issue.

However, the run still needed multiple rescue rounds before stabilizing:

- `ep2`: three post-select history-conflict downgrades before round 4 PASS
- `ep3`: one post-select continuity/history downgrade before round 2 PASS
- `ep5`: `PASS_WITH_FIX` plus two post-select rejects before round 3 PASS
- `ep6`: primary reject plus continuity-firewall downgrade before round 3 PASS
- `ep7`: `PASS_WITH_FIX` patched to PASS
- `ep8`: round 1 PASS

So the question is no longer "did the old burner-phone seam survive?".
The question is:

- what residual authority/carryover seam still causes these late conflicts,
- whether it is now mainly Stage 3 under-specification, Stage 4 carryover consumption, numeric state propagation, or validator noise,
- and what the next bounded patch should be, if any.

## 3. Live Evidence Snapshot

Current evidence already points to these residual clusters:

1. `ep2` opening/state authority drift
- trust-fund provenance drifts from `mother` to `grandfather`
- secret liquidation premise drifts into chairman-consent / public unsealing logic
- opening continuity jumps from immediate handoff to a late-afternoon timeline

2. `ep3` item/time carryover drift
- leather note storage changes from safe to drawer
- timeline regresses from post-4:35 PM movement to 3:35 PM

3. `ep5` numeric/accounting carryover drift
- corporate capitalization spend (`5천만 원`) falls out of the account balance
- Director gives `PASS_WITH_FIX`, but post-select still rejects twice before stabilization

4. `ep6` capital-state / continuity firewall drift
- `15억 vs 20억` usable capital contradiction
- timeline/place/item-acquisition mismatches
- one round drops to continuity-firewall rejection

5. `ep7` phrasing-level timeline artifact
- future-memory / reincarnation wording around `18년 전` remains patch-worthy but not wave-blocking

6. recurring substrate signals
- repeated `[TF-49] inventory gaps`
- repeated `[V66.1] opening continuity` warnings
- `PASS_WITH_FIX` and post-select conflict sometimes coexist in the same area

## 4. Included Coverage

Include:

- latest live console and JSONL truth for `projects/0324_00_`
- Stage 3 blueprint outputs for the troubled episodes
- Stage 4 selected/rejected/patched/final manuscript artifacts for the troubled episodes
- the code that creates and consumes:
  - `_inventory_gaps`
  - previous-manuscript / prev-digest / carryover packets
  - post-select conflict downgrade
  - `PASS_WITH_FIX` patch loop
  - continuity/history validator messages relevant to these residuals

## 5. Excluded Coverage

Exclude unless direct evidence forces reopening:

- old `burner phone / offshore broker / paper company` seam as primary root cause
- Stage 2 episode-count ownership redesign
- Stage 2 density/allocation redesign
- broad genre-contamination work
- DB schema or persistence redesign
- global Director policy rewrite
- closure or implementation claims

## 6. Required Evidence Surfaces

Read these first:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/document-3pass-audit-harness.md`
4. `docs/2026-03-24/console.txt`
5. `projects/0324_00_/logs/episode_production.jsonl`

Required artifact surfaces:

- `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0324_00_/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__action_focused.json`

- `projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_balanced.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_04/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_01/rejected_best__C_tension.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_02/patched_after_fix__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_01/selected_before_fix__B.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_03/patched_after_fix__A_inplace_patch.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_01/rejected_best__A_tension.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__B.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt`
- `projects/0324_00_/logs/artifacts/stage4/ep_0008/attempt_01/final_manuscript__A.txt`

Required code-confirmation surfaces:

- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/validation/continuity_validator.py`

## 7. Investigation Questions

Answer these explicitly.

1. After the closed Stage 4 carryover-expansion wave, what is now the dominant remaining seam?
- `Stage 3 blueprint under-specification`
- `Stage 3 inventory-gap synthesis`
- `Stage 4 carryover consumption`
- `Stage 4 PASS_WITH_FIX / retry-lane semantics`
- `validator overreach / advisory noise`
- `mixed seam`

2. For each troubled episode (`2, 3, 5, 6, 7`), which conflict first appears in:
- blueprint authority
- writer-facing packet construction
- manuscript expansion
- post-select validator

3. Are `_inventory_gaps` helping or hurting?
- Do they correctly warn about not-yet-acquired items?
- Or do they create ambiguous pressure that later turns into state/provenance drift?

4. Why do `PASS_WITH_FIX` and post-select conflict still coexist in the same run?
- Is this an expected separation of concerns?
- Or is the current runtime letting a conflict family survive too deep into the patch loop?

5. Are the repeated `[V66.1] opening continuity` warnings mostly valid signal or mostly advisory noise in this run?

6. Is the remaining top-risk primarily:
- account/provenance state carryover
- item/location carryover
- time-anchor carryover
- or cross-surface contract drift between those three

7. Which previously suspected causes are now cleared enough to defer?
- old covert-infrastructure invention seam
- Stage 2 density
- Stage 2 ep-count ownership
- broad semantic-carryover relapse

## 8. Required Output

Produce:

1. `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md`
2. optional evidence ledger:
   - `docs/2026-03-24/ep1-ep8-live-run-residual-opus-evidence-ledger.md`

Required report sections:

1. Executive Summary
2. Run Outcome Snapshot
3. Episode-by-Episode Conflict Ledger
4. Stage Attribution Ledger
5. `_inventory_gaps` Assessment
6. `PASS_WITH_FIX` vs post-select Conflict Assessment
7. Cleared Non-Culprits
8. Best Current Interpretation
9. Recommended Next Step
10. Confidence and Limits

Mandatory final lines:

- Dominant seam: stage3 blueprint under-specification / stage3 inventory-gap synthesis / stage4 carryover consumption / stage4 retry semantics / validator overreach / mixed seam
- Are the repeated post-select rejects mostly valid: yes / no / mixed
- Should Codex open an execution SSOT immediately: yes / no

## 9. Opus Prompt

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md
5. docs/2026-03-24/console.txt
6. projects/0324_00_/logs/episode_production.jsonl

Task:
Run a residual live-run survey on `projects/0324_00_` through episode 8.
Survey only. No code changes.

Primary goal:
Determine the dominant remaining residual seam after the previously closed Stage 2->3 boundary waves and the Stage 4 carryover-expansion wave.

Hard constraints:
- Survey only. No code changes.
- Do not create an execution SSOT unless confidence reaches 95%+ and the dominant seam is isolated.
- Do not inherit older survey conclusions blindly.
- Prefer live artifact truth over console paraphrase.
- Keep scope bounded to the latest residual issues in episodes 2, 3, 5, 6, 7, and the now-stable episode 8 comparison point.
- Do not reopen Stage 2 density/ep-count redesign unless live evidence proves it is primary again.
- Do not reopen the old covert-infrastructure invention seam as primary unless live artifact evidence proves it.
- Distinguish blueprint pressure, writer-packet pressure, manuscript invention, and validator overreach.

Required evidence surfaces:
- docs/2026-03-24/console.txt
- projects/0324_00_/logs/episode_production.jsonl
- projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json
- projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json
- projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json
- projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json
- projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json
- projects/0324_00_/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__action_focused.json
- projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_balanced.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0002/attempt_04/final_manuscript__A.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_01/rejected_best__C_tension.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0003/attempt_02/patched_after_fix__A.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_01/selected_before_fix__B.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0005/attempt_03/patched_after_fix__A_inplace_patch.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_01/rejected_best__A_tension.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0006/attempt_03/final_manuscript__A.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/selected_before_fix__B.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0007/attempt_01/patched_after_fix__A_InPlace.txt
- projects/0324_00_/logs/artifacts/stage4/ep_0008/attempt_01/final_manuscript__A.txt

Required code-confirmation surfaces:
- modules/core/stage3_orchestrator.py
- modules/domain/agents/chief_writer_context_packets.py
- modules/domain/agents/chief_writer_context.py
- modules/domain/agents/chief_writer_prompts.py
- modules/core/stage4_interview_round.py
- modules/core/stage4_reject_runtime.py
- modules/core/stage4_retry_runtime.py
- modules/core/stage4_orchestrator.py
- modules/validation/continuity_validator.py

Required investigation questions:
1. What is the dominant remaining seam now?
2. For each troubled episode, where does the first hard conflict appear?
3. Are `_inventory_gaps` net-helpful or net-harmful in this run?
4. Why do `PASS_WITH_FIX` and post-select conflicts still coexist in some episodes?
5. Are repeated `[V66.1] opening continuity` warnings valid signal or mostly advisory noise?
6. Which prior suspected causes are now clearly downgraded to non-primary?

Required outputs:
1. docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md
2. optional docs/2026-03-24/ep1-ep8-live-run-residual-opus-evidence-ledger.md

Mandatory final lines:
- Dominant seam: stage3 blueprint under-specification / stage3 inventory-gap synthesis / stage4 carryover consumption / stage4 retry semantics / validator overreach / mixed seam
- Are the repeated post-select rejects mostly valid: yes / no / mixed
- Should Codex open an execution SSOT immediately: yes / no
```

## 10. Dispatch Line

```text
docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-order.md 읽고 survey-only로 진행. 0324_00_ 8화 live run 기준으로 residual seam만 재판정하고, implementation/closure/queue 건드리지 마.
```
