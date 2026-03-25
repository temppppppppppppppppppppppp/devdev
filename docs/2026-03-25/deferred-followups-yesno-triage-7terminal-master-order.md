# Deferred Follow-Ups Yes/No Triage 7-Terminal Master Order

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md`
Scope: remaining deferred items only
Mode: compact triage survey, not deep design

## 1. Intent

Run a compact `yes / no / later after canary` triage across the remaining deferred follow-ups.

This is not a deep survey bundle.
This is not an execution SSOT bundle.
This is not permission to open multiple waves at once.

The purpose is only:
- identify which deferred lanes still deserve a future execution SSOT
- separate `yes now` from `later after canary` from `no`
- keep the blast radius low enough that stale-survey risk stays acceptable

## 2. Excluded From This Triage

Already triaged and not part of the remaining defer set:
- `Stage 2 episode_details specificity floor`
- `Stage 2 constraint_summary robustification`
- closed items from:
  - `stage3-blueprint-clarity-density-wave1`
  - `stage3-blueprint-self-audit-wave`

## 3. Common Rules For All 7 Lanes

All terminals must follow these rules:

- survey only
- code changes forbidden
- execution SSOT creation forbidden
- queue / roadmap / temp mirror edits forbidden
- shared report overwrite forbidden
- findings first
- file/line anchors required
- if confidence is below 95%, do not recommend immediate SSOT opening
- final recommendation must be one of:
  - `yes now`
  - `later after canary`
  - `no`

All lanes must save only their own lane report.

Suggested output root:
- `docs/2026-03-25/opus-deferred-triage/`

Mandatory final lines for every lane:
- `Lane verdict: yes now / later after canary / no`
- `Best bounded next wave from this lane: <short label or none>`
- `Should Codex open an execution SSOT from this lane now: yes / no`

## 4. Common Opus Survey Prompt

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-25/stage3-blueprint-clarity-density-wave1-execution-ssot.md
5. docs/2026-03-25/stage3-blueprint-self-audit-wave-execution-ssot.md
6. docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md
7. docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md
8. docs/2026-03-25/stage3-partial-canary-3terminal-merge-audit.md

Task:
Run a compact triage survey for your assigned deferred lane only.
Survey only. No code changes.

Primary goal:
Decide whether your lane should be:
- yes now
- later after canary
- no

Hard constraints:
- Do not patch code.
- Do not create execution SSOTs.
- Do not edit docs/temp or queue-state.
- Do not overwrite shared survey docs.
- Keep scope to your lane only.
- Prefer live code and prompt evidence over prior assumptions.
- If evidence is mixed, choose `later after canary` rather than forcing `yes now`.
- This is triage, not deep redesign.

Required output:
- one lane report only
- findings first
- file/line anchors
- concrete blast-radius note
- one final verdict: yes now / later after canary / no

Mandatory final lines:
- Lane verdict: yes now / later after canary / no
- Best bounded next wave from this lane: <short label or none>
- Should Codex open an execution SSOT from this lane now: yes / no
```

## 5. Lane Map

### T1. Stage 3 ConstitutionalChecker Dynamic Wiring

Save to:
- `docs/2026-03-25/opus-deferred-triage/t1-stage3-constitutionalchecker-wiring.md`

Investigate:
- `modules/core/constitutional_checker.py`
- `modules/domain/agents/blueprint_ensemble.py`
- any Stage 3 prompt assembly surfaces touched by the current self-audit wave

Question:
- Does wiring `get_architect_constitution()` into live Stage 3 prompt assembly have strong enough ROI now, or should it wait for fresh canary evidence after the static self-audit wave?

### T2. Stage 4 In-Prompt Self-Audit Restoration

Save to:
- `docs/2026-03-25/opus-deferred-triage/t2-stage4-inprompt-self-audit-restoration.md`

Investigate:
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_quality.py`
- any evidence around removed V50 writer self-diagnosis behavior

Question:
- Is restoring Stage 4 in-prompt self-audit worth opening now, or is the existing Self-Critique loop already enough?

### T3. Scene-Level Director Retry Feedback

Save to:
- `docs/2026-03-25/opus-deferred-triage/t3-director-scene-level-retry-feedback.md`

Investigate:
- Director/retry surfaces only
- whether scene-level retry guidance is the next high-ROI fix or still secondary behind additional canary evidence

Question:
- Should a bounded Director retry-feedback wave open now, or is this still a later-after-canary candidate?

### T4. Schema Tightening For Scene-Entry Object-Only Enforcement

Save to:
- `docs/2026-03-25/opus-deferred-triage/t4-scene-entry-schema-tightening.md`

Investigate:
- schema/validation surfaces tied to Stage 3 blueprint scene-entry structure
- current tolerance for weak scene objects

Question:
- Is schema tightening justified now, or is it too high-blast before more live evidence?

### T5. Stage 2 Self-Check Compliance Logging

Save to:
- `docs/2026-03-25/opus-deferred-triage/t5-stage2-selfcheck-compliance-logging.md`

Investigate:
- Stage 2 self-check surfaces only
- whether logging compliance now would materially improve operator decisions or is merely observability nice-to-have

Question:
- Is Stage 2 self-check compliance logging worth a wave now, or should it stay deferred?

### T6. Self-Audit Reasoning Field Persistence

Save to:
- `docs/2026-03-25/opus-deferred-triage/t6-self-audit-reasoning-persistence.md`

Investigate:
- persistence/logging surfaces relevant to storing self-audit reasoning
- whether persistence would materially improve triage quality or just add sink complexity

Question:
- Should reasoning persistence open now, or is it clearly later/no?

### T7. Self-Audit Compliance Rate Tracking

Save to:
- `docs/2026-03-25/opus-deferred-triage/t7-self-audit-compliance-rate-tracking.md`

Investigate:
- metric/logging surfaces for measuring self-audit compliance
- whether this is actionable enough now to justify a wave

Question:
- Is compliance-rate tracking worth opening before another canary, or is it observability-only and later/no?

## 6. Dispatch Lines

Use exactly one of the following:

- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md + 넌 1번 터미널`
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md + 넌 2번 터미널`
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md + 넌 3번 터미널`
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md + 넌 4번 터미널`
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md + 넌 5번 터미널`
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md + 넌 6번 터미널`
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md + 넌 7번 터미널`

## 7. Merge Rule

After all 7 lanes return:
- Codex will merge
- only one `yes now` lane should be promoted at a time
- if multiple lanes say `yes now`, Codex will choose the highest-ROI, lowest-blast candidate
- all `later after canary` lanes remain parked

