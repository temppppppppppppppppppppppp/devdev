Date: 2026-03-24
Status: final (3-pass audited)
Document Type: system-track Gemini survey order
Canonical Path: `docs/2026-03-24/ep1-ep2-handoff-residual-gemini-survey-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-24/console.txt`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
- `docs/2026-03-24/현상황요약.txt`
Evidence Artifacts:
- `projects/00_0324_2/logs/episode_production.jsonl`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_02/rejected_best__A_inplace_patch.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_03/rejected_best__A_inplace_patch.txt`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; closed Stage2->3 boundary waves plus broad system edits remain in-flight; historical project artifacts are also deleted in the worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose

This document defines a bounded Gemini survey order for the fresh-run residual seam that now blocks at `ep2`.

Goal:
- verify what changed after the closed Stage 2 -> Stage 3 boundary patches
- isolate the new `ep1 -> ep2 handoff` conflict family using live artifact truth
- keep Gemini in an evidence-collection role only

This is a survey order, not an execution SSOT.

## 2. Why This Survey Exists

The old dominant failure family was:
- `ep1 overconsumption -> ep3/ep4 continuity-firewall replay`

The fresh run now shows a different blockage:
- Stage 3 `ep1~ep4` all pass
- Stage 4 `ep1` passes
- Stage 4 `ep2` gets provisional PASS-class judgments, then is downgraded by post-select continuity/history checks three times

Representative anchors:
- `docs/2026-03-24/console.txt:453`
- `docs/2026-03-24/console.txt:470`
- `docs/2026-03-24/console.txt:488`
- `docs/2026-03-24/console.txt:495`
- `docs/2026-03-24/console.txt:588`
- `docs/2026-03-24/console.txt:681`
- `docs/2026-03-24/console.txt:683`
- `docs/2026-03-24/console.txt:795`
- `docs/2026-03-24/console.txt:919`
- `docs/2026-03-24/console.txt:923`

This means the next question is no longer "did ep1 eat ep4 again?"

It is now:
- what exact facts were established in `ep1`
- what exact facts are contradicted or repeated in `ep2`
- whether the mismatch begins in the Stage 3 blueprint or is introduced only by Stage 4 candidate generation

## 3. Gemini Role And Limits

Gemini is acceptable here because this task is:
- artifact comparison
- log-to-artifact correlation
- narrow code-path confirmation

Gemini is not the authority for:
- final root-cause verdict
- execution SSOT drafting
- closure claims
- implementation scope cutting

If the evidence is mixed, Gemini must say `not proven` instead of forcing a conclusion.

## 4. Primary Questions

1. What exact continuity facts are established in `ep1` about:
   - protagonist persona
   - current location at ending
   - note state
   - WTI planning state
   - accessible asset / broker / phone network
2. Which of those facts are already contradicted by the `ep2` Stage 3 blueprint before Stage 4 writes anything?
3. Which conflicts are introduced only inside Stage 4 manuscript generation?
4. Which post-select conflicts are clearly valid artifact-truth conflicts, and which might be validator overreach?
5. Is the dominant seam best described as:
   - `stage3 handoff mismatch`
   - `stage4 candidate expansion mismatch`
   - `mixed seam`
   - `insufficient evidence`

## 5. Scope

Included artifact surfaces:
- `docs/2026-03-24/console.txt`
- `projects/00_0324_2/logs/episode_production.jsonl`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_02/rejected_best__A_inplace_patch.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_03/rejected_best__A_inplace_patch.txt`

Included code surfaces only when needed to explain a conflict:
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_reject_runtime.py`

Excluded:
- Stage 2 density/allocation redesign
- broad semantic carryover redesign beyond evidence mention
- Director policy redesign
- DB/schema/log shape changes
- patching or execution-SSOT drafting

## 6. Working Hypothesis

Current live evidence suggests:
- the old `ep3/ep4 replay cascade` is reduced
- the new blocker is an `ep1 -> ep2 artifact-truth handoff` seam

Most likely conflict families:
- `persona-contract conflict`
- `note-state conflict`
- `location-state conflict`
- `repeated WTI planning / repeated completed-thinking conflict`

This is still a working hypothesis. Gemini should test it, not inherit it blindly.

## 7. Required Investigation Method

### Pass 1. Artifact Truth

Build a compact ledger for `ep1` and `ep2` with these columns:
- fact class
- `ep1` source path and line
- `ep2 blueprint` source path and line
- `ep2 rejected manuscript` source path and line
- conflict type
- clearly conflicting / ambiguous / not proven

Minimum fact classes:
- protagonist persona
- protagonist location
- note ownership and note content state
- WTI planning state
- money and asset-planning state
- out-of-now network access such as broker / dealer / phone

### Pass 2. Conflict Origin

For each conflict, state where it first appears:
- already present in Stage 3 blueprint
- introduced in Stage 4 manuscript expansion
- mixed / ambiguous

### Pass 3. Validator Signal Quality

For each post-select reject reason, state:
- valid conflict
- likely valid but overstated
- possibly noisy / overreaching
- not proven

Do not turn this into a redesign proposal.

## 8. Mandatory Anchors To Check

These are required anchors, not optional:
- `docs/2026-03-24/console.txt:681`
- `docs/2026-03-24/console.txt:683`
- `docs/2026-03-24/console.txt:795`
- `docs/2026-03-24/console.txt:919`
- `docs/2026-03-24/console.txt:923`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json:92`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json:110`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json:26`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt:29`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt:35`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt:59`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt:80`

## 9. Required Output Contract

Gemini must produce:

1. one final survey report:
   - `docs/2026-03-24/ep1-ep2-handoff-residual-gemini-survey-report.md`
2. one optional raw evidence ledger:
   - `docs/2026-03-24/ep1-ep2-handoff-residual-gemini-evidence-ledger.md`

Required sections in the report:
1. Executive Summary
2. Included Coverage / Exclusions
3. Fact Ledger
4. Conflict Ledger
5. Conflict Origin Assessment
6. Cleared Non-Culprits
7. Best Current Interpretation
8. Confidence And Limits

Mandatory final lines:
- `Dominant seam: stage3 handoff mismatch / stage4 candidate expansion mismatch / mixed seam / insufficient evidence`
- `Are the post-select rejects mostly valid: yes/no/mixed`
- `Should Codex open an execution SSOT immediately: yes/no`

Gemini must not create:
- execution SSOTs
- temp queue artifacts
- closure notes
- implementation patches

## 10. Read Order

Read these files first, in this exact order:
1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/document-3pass-audit-harness.md`
4. `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
5. `docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
6. `docs/2026-03-24/console.txt`
7. `docs/2026-03-24/현상황요약.txt`
8. `docs/2026-03-24/ep1-ep2-handoff-residual-gemini-survey-order.md`

If Hangul paths render badly in terminal output, keep using the same relative paths and read files as UTF-8.

## 11. Gemini Prompt

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md
5. docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md
6. docs/2026-03-24/console.txt
7. docs/2026-03-24/현상황요약.txt
8. docs/2026-03-24/ep1-ep2-handoff-residual-gemini-survey-order.md

Task:
Run a bounded survey of the fresh-run ep1 -> ep2 handoff conflict. Survey only. No code changes.

Primary goal:
Collect evidence that shows whether the current blocker is mainly:
- a Stage 3 handoff mismatch already present in the ep2 blueprint,
- a Stage 4 candidate expansion mismatch introduced after blueprint handoff,
- a mixed seam,
- or still insufficiently proven.

Hard constraints:
- Survey only. Do not patch code.
- Do not create execution SSOTs, docs/temp artifacts, or closure notes.
- Do not claim final root cause unless the artifact evidence is direct.
- If a claim is ambiguous, mark it not proven.
- Keep the scope narrow. Do not reopen Stage 2 density/allocation redesign.
- Use UTF-8 reads.
- Prefer relative paths if absolute Hangul paths render badly in terminal output.
- Workspace is dirty. Do not revert unrelated edits.

Required evidence surfaces:
- docs/2026-03-24/console.txt
- projects/00_0324_2/logs/episode_production.jsonl
- projects/00_0324_2/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json
- projects/00_0324_2/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json
- projects/00_0324_2/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt
- projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt
- projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_02/rejected_best__A_inplace_patch.txt
- projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_03/rejected_best__A_inplace_patch.txt

Optional code-confirmation surfaces:
- modules/core/stage3_orchestrator.py
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/core/stage4_post_pass_runtime.py
- modules/core/stage4_reject_runtime.py

Required questions:
1. What exact facts are established in ep1 about persona, location, note state, WTI planning state, and available network/assets?
2. Which of those facts are contradicted in the ep2 Stage 3 blueprint?
3. Which conflicts appear only in the ep2 Stage 4 rejected manuscripts?
4. Which post-select reject reasons are clearly valid artifact-truth conflicts, and which might be overstated?
5. Is the dominant seam `stage3 handoff mismatch`, `stage4 candidate expansion mismatch`, `mixed seam`, or `insufficient evidence`?

Required outputs:
1. docs/2026-03-24/ep1-ep2-handoff-residual-gemini-survey-report.md
2. optional: docs/2026-03-24/ep1-ep2-handoff-residual-gemini-evidence-ledger.md

Required report sections:
1. Executive Summary
2. Included Coverage / Exclusions
3. Fact Ledger
4. Conflict Ledger
5. Conflict Origin Assessment
6. Cleared Non-Culprits
7. Best Current Interpretation
8. Confidence And Limits

Mandatory final lines:
- Dominant seam: stage3 handoff mismatch / stage4 candidate expansion mismatch / mixed seam / insufficient evidence
- Are the post-select rejects mostly valid: yes/no/mixed
- Should Codex open an execution SSOT immediately: yes/no

Output style:
- findings first
- concrete file and line anchors wherever possible
- no implementation claims
- no closure claims
```

## 12. Suggested Dispatch Line

Use this one-liner if a short handoff is easier:

`docs/2026-03-24/ep1-ep2-handoff-residual-gemini-survey-order.md 읽고 survey-only로 진행. 구현 금지, execution SSOT 금지, ep1->ep2 fact conflict만 artifact 기준으로 정리.`

## 13. 3-Pass Audit Record

- Pass 1
  - confirmed this is a survey order, not an execution SSOT
  - kept scope narrow to `ep1 -> ep2 handoff` instead of reopening Stage 2/3 broad waves
- Pass 2
  - checked canonical path, evidence paths, and representative anchors against the live workspace
  - bounded claims to the current fresh-run evidence only
- Pass 3
  - made Gemini role explicit as evidence collector only
  - removed patch/closure authority from the order

Estimated Confidence:
- 96%

Next Operating Consequence:
- use this document only for Gemini evidence collection
- Codex reviews the resulting report and decides whether a new execution SSOT is warranted
