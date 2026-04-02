# 0_0 Stage4 Consumer-Finalization Global Parallel Master Order

Date: 2026-04-02
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-04-02/0_0-stage4-consumer-finalization-global-parallel-master-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Baseline Dirty Summary: `dirty: active Stage4 docs/code/test deltas, prepared canary targets, temp roadmap/queue active`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Track: system
Mode: bounded static parallel survey, no realization, no canary
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
Related Context:
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-post-implementation-audit.md`

## 1. Purpose

This is a bounded, static, read-only survey order for one question:

- where does `Stage4` still dilute, reclassify, or split authoritative truth while consuming upstream packets and finalizing manuscripts?

This order exists because:

- the current dominant blocker has repeatedly moved downstream into Stage4 finalization
- Stage2 and Stage3 surveys already isolated their main debt families
- the remaining runtime failures cluster around:
  - `fix_pack`
  - `post_select_conflict`
  - `active_pressure_vectors`
  - accepted manuscript truth vs post-pass state truth

## 2. Scope

Minimum survey scope:

- Stage4 intake and context-building truth ownership
- Stage4 advisory / fix-pack / finalization contract
- Stage4 post-select / post-pass / state-write consumption logic
- real Stage4 artifact truth on representative episodes
- consumer-side contract drift and split-truth points

Minimum code surfaces:

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer_context.py`

Representative slices:

- `0_0`: ep2, ep3, ep4, ep5
- optional contrast: latest `0_1` Stage4 slice where finalization pressure is visible

## 3. Common Rules For All Terminals

1. survey only
2. read-only only
3. no code edits, no DB writes, no docs/temp edits
4. no canary, no fresh runtime
5. separate `intake truth`, `operator truth`, `finalization truth`, `state truth`, `artifact truth`
6. do not collapse a Stage4 issue into “quality bad” without tracing the owner contract
7. inspect accepted manuscript truth separately from post-pass state and advisory logs
8. save draft lane docs only under `docs/2026-04-02/`
9. mark lane drafts `Status: draft-bounded-partial-evidence`
10. Terminals 1-4 are for Opus, Terminal 5 is reserved for Codex synthesis

## 4. Output Contract

Each Opus lane terminal must return:

1. `Coverage`
2. `Findings`
3. `Non-Issues`
4. `Verdict`
5. `Stop`

Required stop line:

- `read-only lane complete; no files mutated`

Recommended draft paths:

- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane1-intake-truth-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane2-fixpack-finalization-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane3-postpass-state-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane4-artifact-vertical-slice-draft.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-lane5-codex-synthesis-draft.md`

Final intended outputs after synthesis:

- canonical survey:
  - `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- raw evidence:
  - `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`

## 5. Required Questions

The parallel survey must answer all of these:

1. What upstream truth does Stage4 actually treat as authoritative at intake time?
2. Where does Stage4 split one source of truth into:
   - advisory truth
   - manuscript truth
   - post-pass state truth
   - operator-visible truth
3. Which Stage4 seams are really:
   - fix-pack generation problems
   - post-select contradiction contract problems
   - state-write / post-pass truth alignment problems
4. Which Stage4 fields or contracts are renamed, weakened, or flattened relative to upstream truth?
5. Is Stage4 best described as:
   - intake-clean / finalization-clean
   - intake-clean / finalization-lossy
   - or split-truth-heavy?
6. Which single consumer-side contract would reduce the most downstream confusion if normalized first?

## 6. Lane Map

1. `Opus Terminal 1`: Stage4 intake / context truth ownership
2. `Opus Terminal 2`: advisory, fix-pack, and finalization contract
3. `Opus Terminal 3`: post-pass state / active-pressure / state-write truth
4. `Opus Terminal 4`: artifact vertical slice / runtime drift taxonomy
5. `Codex Terminal 5`: synthesis

## 7. Opus Terminal 1 Order

Use this as-is:

```text
Terminal 1

Role:
- Stage4 intake / context truth ownership lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- static analysis only; no canary

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py

Questions to answer:
- What does Stage4 intake rank as authoritative?
- Which Stage2/3 truths are machine-readable at intake, and which are only prose?
- Where does Stage4 rename or weaken upstream truth before generation starts?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: intake-clean / mixed / intake-lossy
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-lane1-intake-truth-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 8. Opus Terminal 2 Order

Use this as-is:

```text
Terminal 2

Role:
- Stage4 advisory, fix-pack, and finalization contract lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- static analysis only; no canary

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_retry_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_reject_runtime.py

Questions to answer:
- Where does Stage4 lose or flatten fix-pack truth?
- Which strong advisories can localize, and which fail closed because contract fields are missing?
- How does post_select_conflict reclassify bounded repair vs full rewrite?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: finalization-clean / mixed / finalization-lossy
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-lane2-fixpack-finalization-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 9. Opus Terminal 3 Order

Use this as-is:

```text
Terminal 3

Role:
- Stage4 post-pass state / active-pressure / state-write truth lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- static analysis only; no canary

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_post_processor.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_post_pass_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_reject_runtime.py

Questions to answer:
- Where can accepted manuscript truth diverge from state truth?
- How do active_pressure_vectors, state_changes, and post-pass summaries compete?
- Which state surfaces are stale, over-persistent, or stronger than the final accepted artifact?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: state-aligned / mixed / split-truth-heavy
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-lane3-postpass-state-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 10. Opus Terminal 4 Order

Use this as-is:

```text
Terminal 4

Role:
- Stage4 artifact vertical slice / runtime drift taxonomy lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- static analysis only; no canary

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-global-parallel-master-order.md

Required surfaces:
- representative Stage4 artifacts for `0_0` ep2, ep3, ep4, ep5
- linked `decisions.jsonl`, `episode_production.jsonl`, `ui_events.jsonl`, and `project_data.db` rows when available

Questions to answer:
- In real artifacts, where does the first consumer-side drift become visible?
- Which failures are true narrative contradictions vs contract/sink flattening?
- Which one or two seams dominate the runtime cost?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: artifact-clean / mixed / artifact-lossy
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage4-consumer-finalization-lane4-artifact-vertical-slice-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 11. Codex Synthesis Order

After terminals 1-4 finish:

- verify all four draft files exist
- synthesize them into:
  - `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
  - `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`
- structure the synthesis into:
  - `hard conclusions`
  - `medium-confidence conclusions`
  - `open questions`
  - `dominant consumer-side contract drifts`
  - `next action`
- do not patch code during synthesis
- do not touch queue or `docs/temp/`

## 12. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a survey master order, not an execution SSOT
- bounded the scope to Stage4 consumer/finalization ownership only

Pass 2, evidence and consistency:

- aligned the order with the latest Stage4 surveys and remediation lineage
- kept claims bounded to already observed Stage4 finalization seams

Pass 3, execution and readability:

- split the work into intake, finalization, post-pass state, and artifact lanes
- kept synthesis separate for Codex

Confidence: `96%`
