# 0_0 Stage2 Production-Consumption Global Parallel Master Order

Date: 2026-04-02
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-04-02/0_0-stage2-production-consumption-global-parallel-master-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Baseline Dirty Summary: `dirty: active Stage4 docs/code/test deltas, live canary artifacts/logs present, temp roadmap/queue active`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Track: system
Mode: bounded parallel survey, no realization
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
Related Context:
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
- `docs/2026-04-01/stage23-architecture-simplification-long-term-memo.md`

## 1. Purpose

This is a bounded operator order for one question only:

- is `Stage2`, as a global production and consumption substrate, structurally sound enough for the rest of the pipeline, or is it a major source of structure/term/contract debt?

This order must test, not assume, these hypotheses:

- `Stage2` produces enough content, but its authority packets are schema-fragile or hierarchy-weak
- `Stage2` production and downstream consumption use overlapping concepts under different names and strengths
- `Stage2 -> Stage3` and `Stage2 -> Stage4` handoffs may still be flattening or re-translating the same truth too many times
- the real issue may not be only Stage2 generation quality, but also consumer-side reinterpretation
- some current complexity may come from `Stage2` truth being represented differently in:
  - arc/tactical docs
  - constraint summaries
  - episode details
  - blueprint constraint compiler inputs
  - Stage4 context packets

This order is for:

- read-only parallel survey
- code-path and artifact-path investigation
- contract/term drift inspection
- later synthesis into one canonical bounded survey

This order is not for:

- code edits
- DB writes
- artifact edits
- fresh canary
- `docs/temp/` mutation
- execution SSOT authoring
- queue cleanup
- resolved claims

## 2. Scope

Minimum survey scope:

- `Stage2 production truth`
- `Stage2 consumption truth`
- `Stage2 -> Stage3` transform contract
- `Stage2 -> Stage4/validator/compiler` consumer contract
- real artifact vertical slices across representative episodes
- `contract drift`, `term drift`, and `authority demotion` patterns

Minimum authoritative code surfaces:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer_context.py`
- `config/prompts/ensemble.yaml`

Minimum prior docs:

- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
- `docs/2026-04-01/stage23-architecture-simplification-long-term-memo.md`

Minimum artifact slices:

- `0_0`: `ep5`, `ep6`
- `0_1`: `ep9`, `ep13`, `ep15`

Representative artifact families:

- Stage2 arc/tactical artifacts
- Stage3 blueprint artifacts
- Stage4 manuscript artifacts
- linked JSONL/DB/summary evidence where needed

## 3. Common Rules For All Terminals

All terminals must follow these rules:

1. Survey only.
2. Read-only only.
3. No code edits, no DB writes, no artifact edits, no `docs/temp/` edits.
4. Do not widen into a fresh canary or runtime closure task.
5. Use live code, DB, JSONL, and artifact truth ahead of stale survey text.
6. Separate `production truth`, `consumption truth`, `artifact truth`, and `contract drift`.
7. Distinguish:
   - Stage2 production weakness
   - Stage2 consumer-side authority demotion
   - Stage2 term/contract renaming drift
   - Stage2 redundant translation pressure
   - evidence that Stage3 is acting as a compiler/substep candidate
8. Do not claim Stage2 is broken from prompts alone; inspect real artifacts.
9. Do not claim Stage2 is fine from artifact prose alone; inspect downstream consumers.
10. Saved lane drafts must be marked `Status: draft-bounded-partial-evidence`.
11. Save lane drafts only under `docs/2026-04-02/`.
12. Terminals 1-4 are for `Opus`.
13. Terminal 5 is reserved for `Codex` synthesis after 1-4 return.

## 4. Output Contract

Each Opus lane terminal must return this shape in terminal output:

1. `Coverage`
2. `Findings`
3. `Non-Issues`
4. `Verdict`
5. `Stop`

Required stop line:

- `read-only lane complete; no files mutated`

Recommended draft paths:

- `docs/2026-04-02/0_0-stage2-production-consumption-lane1-production-authority-draft.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-lane3-stage24-consumption-draft.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-lane4-artifact-vertical-slice-draft.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-lane5-codex-synthesis-draft.md`

Final intended outputs after synthesis:

- canonical survey doc:
  - `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- raw evidence:
  - `docs/2026-04-02/0_0-stage2-production-consumption-global-evidence.json`

These final outputs are out of scope for Opus terminals 1-4.

## 5. Required Questions

The parallel survey must answer all of these:

1. What does Stage2 claim to produce authoritatively?
2. Which Stage2 outputs are truly `hard truth`, which are `mission`, which are `carryover`, and which are `advisory/history`?
3. How do Stage3, validator, compiler, and Stage4 actually consume those outputs?
4. Which Stage2 concepts are renamed, weakened, or re-packed downstream?
5. Where is the biggest `term drift` or `contract drift`?
6. Is Stage2 best described as:
   - structurally sound
   - content-sufficient but schema-fragile
   - or a major upstream debt source?
7. Does the evidence support a long-term direction of:
   - keep-as-is
   - contract normalization
   - or Stage3 compiler/substep compression?

## 6. Lane Map

Use this five-lane layout:

1. `Opus Terminal 1`: Stage2 production authority lane
2. `Opus Terminal 2`: Stage2 -> Stage3 transform / drift lane
3. `Opus Terminal 3`: Stage2 -> Stage4/validator/compiler consumption lane
4. `Opus Terminal 4`: real artifact vertical-slice lane
5. `Codex Terminal 5`: synthesis after 1-4 return

## 7. Opus Terminal 1 Order

Use this as-is:

```text
Terminal 1

Role:
- Stage2 production authority lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- inspect both code contract and real Stage2 artifacts
- do not widen into broad Stage2 redesign

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\arc_ensemble.py
- C:\Users\User\Desktop\글도비\config\prompts\ensemble.yaml
- representative Stage2 arc/tactical artifacts under:
  - C:\Users\User\Desktop\글도비\projects\0_0\plans\
  - C:\Users\User\Desktop\글도비\projects\0_1\plans\

Questions to answer:
- What authority does Stage2 claim to emit?
- Are hard truth / mission / carryover / advisory already separated, or still flattened?
- Which Stage2 output fields look canonical vs merely briefing-like?
- Which Stage2 outputs are likely to be too prose-heavy or ambiguous for downstream consumers?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: stage2-sound / stage2-schema-fragile / stage2-major-debt
5. Stop

Required artifact:
- Stage2 authority packet table
- Stage2 term inventory table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane1-production-authority-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 8. Opus Terminal 2 Order

Use this as-is:

```text
Terminal 2

Role:
- Stage2 -> Stage3 transform / drift lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- compare Stage2 source authority against Stage3 transform outputs

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py
- C:\Users\User\Desktop\글도비\config\prompts\ensemble.yaml
- representative `0_0` and `0_1` Stage2 vs Stage3 artifact pairs

Questions to answer:
- Which Stage2 concepts survive into Stage3 unchanged?
- Which are renamed, weakened, or re-expressed?
- Does Stage3 behave like an authority-preserving compiler, or like a second interpretation layer?
- Which Stage2 truths are most often demoted by Stage3 into soft guidance?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: compiler-like / mixed / reinterpretation-heavy
5. Stop

Required artifact:
- Stage2->Stage3 concept mapping table
- top 5 contract-drift seams

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 9. Opus Terminal 3 Order

Use this as-is:

```text
Terminal 3

Role:
- Stage2 -> Stage4 / validator / compiler consumption lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- inspect consumer-side authority usage, not just producer-side intent

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py

Questions to answer:
- How do downstream consumers read Stage2 truths?
- Which Stage2 truths are consumed as hard constraints, and which are only advisory by the time they arrive?
- Is there evidence of duplicate truth packets, repeated renaming, or authority dilution?
- Which consumer is the strongest source of Stage2 contract weakening?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: consumer-aligned / consumer-diluted / consumer-drifting
5. Stop

Required artifact:
- Stage2 consumer matrix
- authority-strength comparison table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane3-stage24-consumption-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 10. Opus Terminal 4 Order

Use this as-is:

```text
Terminal 4

Role:
- real artifact vertical-slice lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- prioritize artifact truth over stale assumptions

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-global-parallel-master-order.md

Required slices:
- `0_0`: ep5, ep6
- `0_1`: ep9, ep13, ep15

For each slice inspect:
- Stage2 artifact
- Stage3 blueprint
- Stage4 manuscript when present
- linked metadata/log truth only as support

Questions to answer:
- In real artifacts, where does the first drift happen?
- Is the drift already visible in Stage2 prose/packet, or introduced downstream?
- Which concepts survive all the way through, and which mutate by stage?
- Do the artifacts support the thesis that Stage3 is a redundant translation layer candidate?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: first-drift-at-stage2 / first-drift-at-stage3 / mixed
5. Stop

Required artifact:
- vertical slice table for each representative episode
- first-drift ledger

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane4-artifact-vertical-slice-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 11. Codex Terminal 5 Order

Use this after terminals 1-4 are complete:

```text
Terminal 5

Role:
- Codex synthesis

Model:
- Codex

Task:
- read the four lane drafts
- verify they are mutually consistent
- produce one canonical bounded survey and one raw evidence json

Inputs:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane1-production-authority-draft.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane3-stage24-consumption-draft.md
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-lane4-artifact-vertical-slice-draft.md

Required outputs:
1. canonical survey:
   - C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-global-bounded-survey.md
2. raw evidence:
   - C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage2-production-consumption-global-evidence.json

Required synthesis frame:
- answer-first
- hard conclusions / medium-confidence conclusions / open questions
- production truth / consumption truth / artifact truth / contract drift
- top 3 debt seams
- long-term structure direction:
  - keep-as-is
  - contract normalization
  - Stage3 compiler/substep candidate

Do not:
- patch code
- mutate queue
- declare closure
```

## 12. Final Deliverable Standard

The final synthesis should end with:

1. Stage2 production structure verdict
2. Stage2 consumption structure verdict
3. top 3 contract/term drift seams
4. long-term structure direction
5. next action

## 13. 3-Pass Audit Record

### Pass 1. Structure and Scope

- document type is a survey master order, not an execution SSOT
- scope is explicitly Stage2 production-consumption, not broad repo redesign
- Opus/Codex lane split is explicit

### Pass 2. Evidence and Consistency

- named representative slices align with already investigated problematic episodes
- code surfaces and downstream consumers match the current workspace topology
- path policy is canonical-only, with no temp mirror

### Pass 3. Execution and Readability

- each terminal has a bounded mission and explicit stop condition
- final synthesis expectations are concrete
- the order is ready to paste into parallel terminals without extra interpretation

Confidence: `96%`
