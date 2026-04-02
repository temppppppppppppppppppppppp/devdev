# 0_0 Stage234 Cross-Stage Vocabulary Source-of-Truth Matrix Parallel Master Order

Date: 2026-04-02
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md`
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
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-parallel-master-order.md`
- `docs/2026-04-01/stage23-architecture-simplification-long-term-memo.md`

## 1. Purpose

This is a bounded, static, read-only survey order for one question:

- across Stage2, Stage3, and Stage4, which fields are the real source of truth, which terms are aliases, and where do structure/term/contract debts come from?

This order exists because:

- current debt no longer looks like a single-stage bug
- the same concepts keep appearing under different names and strengths
- Stage4 consumer survey already proved a split-truth problem around `fix_pack`, `post_select_conflict`, `final_state_updates`, `actual_truth`, and `world_state`
- the next simplification step depends on a real matrix, not intuition

## 2. Scope

Minimum survey scope:

- cross-stage vocabulary mapping
- canonical owner mapping by concept
- hard truth vs mission vs carryover vs advisory classification
- proper-noun / institution / timeline / entity / pressure-vector truth paths
- `fix_pack`, `fix_scope`, `authoritative_fix_scope`, `final_state_updates`, `actual_truth`, `world_state`, `active_pressure_vectors` owner mapping
- term drift, strength inversion, and redundant translation pressure

Minimum code surfaces:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_processor.py`
- `modules/domain/agents/chief_writer_context.py`
- `config/prompts/ensemble.yaml`

Representative slices:

- `0_0`: ep2, ep3, ep4, ep5, ep6
- `0_1`: ep9, ep13, ep15

## 3. Common Rules For All Terminals

1. survey only
2. read-only only
3. no code edits, no DB writes, no docs/temp edits
4. no canary, no fresh runtime
5. separate `term`, `owner`, `strength`, `transport`, `artifact evidence`
6. do not call two different things “the same concept” unless owner/meaning actually match
7. do not collapse owner drift and naming drift into one bucket
8. treat the new Stage4 consumer-finalization survey as authoritative for already-proven Stage4 seams; do not re-spend the lanes re-proving those findings
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

- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane1-term-inventory-draft.md`
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane2-owner-strength-draft.md`
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane3-transport-drift-draft.md`
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane4-vertical-slice-draft.md`
- `docs/2026-04-02/0_0-stage234-vocab-matrix-lane5-codex-synthesis-draft.md`

Final intended outputs after synthesis:

- canonical survey:
  - `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-bounded-survey.md`
- raw evidence:
  - `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-evidence.json`

## 5. Required Questions

The parallel survey must answer all of these:

1. Which concepts should be treated as the shared canonical vocabulary across Stage2/3/4?
2. For each major concept, who is the authoritative owner?
3. At which boundary does each concept change:
   - name
   - strength
   - structure
   - or owner?
4. Which concepts are duplicated under multiple aliases?
5. Which concepts survive only as prose instead of machine-readable contract?
6. Which two or three vocab/owner mismatches generate the most downstream cost?
7. Does the evidence support:
   - contract normalization
   - owner consolidation
   - Stage3 compiler/substep compression
   as the next long-term simplification direction?
8. Which Stage4 split-truth concepts should enter the shared cross-stage matrix immediately instead of remaining stage-local terminology?

## 6. Lane Map

1. `Opus Terminal 1`: cross-stage term inventory
2. `Opus Terminal 2`: owner and strength matrix
3. `Opus Terminal 3`: transport and boundary drift
4. `Opus Terminal 4`: representative vertical slices
5. `Codex Terminal 5`: synthesis

## 7. Opus Terminal 1 Order

Use this as-is:

```text
Terminal 1

Role:
- cross-stage term inventory lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\arc_ensemble.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\config\prompts\ensemble.yaml

Questions to answer:
- What are the major repeated concepts across Stage2/3/4?
- Which terms are true equivalents, and which are only partial overlaps?
- Which concept families need a shared canonical vocabulary first?
- Ensure Stage4 consumer-seam vocabulary (`fix_pack`, `post_select_conflict`, `actual_truth`, `final_state_updates`, `active_pressure_vectors`) is included rather than treated as a separate local glossary.

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: low-drift / mixed / high-term-drift
5. Stop

Required artifact:
- cross-stage term inventory table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-vocab-matrix-lane1-term-inventory-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 8. Opus Terminal 2 Order

Use this as-is:

```text
Terminal 2

Role:
- owner and strength matrix lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_post_processor.py

Questions to answer:
- For each major concept, who owns it at each stage?
- Where does hard truth become advisory or vice versa?
- Which owner collisions create the most downstream confusion?
- Include the Stage4 state-truth split explicitly: Director state, Manager state, Python state.

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: owner-clean / mixed / owner-collision-heavy
5. Stop

Required artifact:
- owner-by-stage matrix
- strength-by-stage matrix

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-vocab-matrix-lane2-owner-strength-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 9. Opus Terminal 3 Order

Use this as-is:

```text
Terminal 3

Role:
- transport and boundary drift lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_post_pass_runtime.py

Questions to answer:
- At which boundaries does truth lose structure and become prose-only?
- Which boundary adds the most redundant translation pressure?
- Where are alias renames happening without explicit canonical mapping?
- Use the existing Stage4 consumer survey as a baseline instead of re-proving Stage4 finalization drift from scratch.

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: transport-clean / mixed / transport-lossy
5. Stop

Required artifact:
- boundary drift ledger

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-vocab-matrix-lane3-transport-drift-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 10. Opus Terminal 4 Order

Use this as-is:

```text
Terminal 4

Role:
- representative vertical slice lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md

Required slices:
- `0_0`: ep2, ep3, ep4, ep5, ep6
- `0_1`: ep9, ep13, ep15

Questions to answer:
- In real artifacts, where do terms and owners diverge first?
- Which mismatches are merely naming noise, and which actually change behavior?
- Which slice best proves the need for a shared source-of-truth matrix?
- Reuse the Stage4 consumer survey’s proven ep2+ carryover pattern and focus this lane on cross-stage mapping, not another Stage4 blocker hunt.

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: slice-clean / mixed / slice-proves-drift
5. Stop

Required artifact:
- at least two cross-stage vertical slice tables

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage234-vocab-matrix-lane4-vertical-slice-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 11. Codex Synthesis Order

After terminals 1-4 finish:

- verify all four draft files exist
- synthesize them into:
  - `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-bounded-survey.md`
  - `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-evidence.json`
- structure the synthesis into:
  - `hard conclusions`
  - `medium-confidence conclusions`
  - `open questions`
  - `top contract/term/owner drifts`
  - `candidate canonical vocabulary`
  - `candidate owner map`
  - `next action`
- do not patch code during synthesis
- do not touch queue or `docs/temp/`

## 12. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a survey master order, not an execution SSOT
- bounded the scope to cross-stage vocabulary and owner matrix work

Pass 2, evidence and consistency:

- aligned the order with the existing Stage2 and Stage3 survey conclusions
- kept the ask focused on term/owner/strength drift, not another runtime lane

Pass 3, execution and readability:

- separated term inventory, owner-strength matrix, boundary transport, and vertical slices
- left synthesis for Codex only

Confidence: `96%`
