# 0_0 Stage3 Static Global Parallel Master Order

Date: 2026-04-02
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-04-02/0_0-stage3-static-global-parallel-master-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2 survey docs and lane drafts untracked`
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
- `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-01/stage23-architecture-simplification-long-term-memo.md`

## 1. Purpose

This is a bounded, static, read-only survey order for one question:

- is `Stage3` currently acting as a faithful compiler/substep, or is it still the main reinterpretive drift layer in the pipeline?

This order exists because:

- the latest Stage2 survey proved Stage2 has contract debt, but is not the first visible narrative drift point
- the first clear drift still appears in `Stage3`
- the next productive step is static root-cause narrowing, not another canary

## 2. Scope

Minimum survey scope:

- Stage3 generation authority and prompt hierarchy
- Stage3 validator / binding / semantic fidelity contract
- Stage3 -> Stage4 handoff contract
- real Stage3 artifact truth on representative episodes
- contract drift and redundant translation pressure

Minimum code surfaces:

- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `config/prompts/ensemble.yaml`

Representative slices:

- `0_0`: ep5, ep6, ep7, ep8, ep9
- optional contrast: any `0_1` Stage3-capable chain that is fully present and inspectable

## 3. Common Rules For All Terminals

1. survey only
2. read-only only
3. no code edits, no DB writes, no docs/temp edits
4. no canary, no fresh runtime
5. separate `generation truth`, `validator truth`, `handoff truth`, `artifact truth`, `contract drift`
6. do not assume Stage3 is bad from prompts alone; inspect artifacts
7. do not assume Stage3 is fine because some later canary improved; inspect failure and success slices together
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

- `docs/2026-04-02/0_0-stage3-static-lane1-generation-authority-draft.md`
- `docs/2026-04-02/0_0-stage3-static-lane2-validator-binding-draft.md`
- `docs/2026-04-02/0_0-stage3-static-lane3-stage34-handoff-draft.md`
- `docs/2026-04-02/0_0-stage3-static-lane4-artifact-drift-vertical-slice-draft.md`
- `docs/2026-04-02/0_0-stage3-static-lane5-codex-synthesis-draft.md`

Final intended outputs after synthesis:

- canonical survey:
  - `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- raw evidence:
  - `docs/2026-04-02/0_0-stage3-static-global-evidence.json`

## 5. Required Questions

The parallel survey must answer all of these:

1. What truth does Stage3 treat as authoritative during generation?
2. Which Stage2 truths survive into Stage3 unchanged, and which are reinterpreted?
3. Which validator/binding seams are truly blocking, and which remain advisory/deferred?
4. Does Stage3 primarily fail through:
   - off-arc invention
   - identity / institution drift
   - mission dilution
   - continuity packet loss
   - or prompt hierarchy flattening?
5. What Stage3 outputs reach Stage4 as hard handoff truth, and what gets weakened first?
6. Is Stage3 better described as:
   - compiler-like
   - mixed
   - reinterpretation-heavy
7. Does the evidence support a long-term direction of:
   - keep Stage3 as-is
   - tighten Stage3 contracts
   - or compress Stage3 toward compiler/substep status?

## 6. Lane Map

1. `Opus Terminal 1`: Stage3 generation authority / prompt hierarchy
2. `Opus Terminal 2`: Stage3 validator / binding / semantic fidelity
3. `Opus Terminal 3`: Stage3 -> Stage4 handoff / consumer contract
4. `Opus Terminal 4`: artifact vertical slice / drift taxonomy
5. `Codex Terminal 5`: synthesis

## 7. Opus Terminal 1 Order

Use this as-is:

```text
Terminal 1

Role:
- Stage3 generation authority / prompt hierarchy lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py
- C:\Users\User\Desktop\글도비\config\prompts\ensemble.yaml

Questions to answer:
- What does Stage3 actually rank first during generation?
- Which constraints are truly above arc_focus and previous-info bulk?
- Which Stage2 truths still become prose reinterpretation at Stage3?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: compiler-like / mixed / reinterpretation-heavy
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-lane1-generation-authority-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 8. Opus Terminal 2 Order

Use this as-is:

```text
Terminal 2

Role:
- Stage3 validator / binding / semantic fidelity lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py

Questions to answer:
- Which Stage3 problems are genuinely blocked by binding prevalidation?
- Which major seams are still advisory or Director-deferred?
- Where do semantic fidelity and identity/institution drift still slip through?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: binding-strong / mixed / advisory-heavy
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-lane2-validator-binding-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 9. Opus Terminal 3 Order

Use this as-is:

```text
Terminal 3

Role:
- Stage3 -> Stage4 handoff / consumer contract lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-global-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py

Questions to answer:
- What Stage3 truths survive into Stage4 as strong handoff truth?
- What gets renamed, weakened, or flattened before Stage4 sees it?
- Does Stage3 handoff look like a compiler output or another prose brief?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: handoff-clean / mixed / consumer-diluted
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-lane3-stage34-handoff-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 10. Opus Terminal 4 Order

Use this as-is:

```text
Terminal 4

Role:
- artifact vertical slice / drift taxonomy lane

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
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-global-parallel-master-order.md

Required slices:
- 0_0 ep5
- 0_0 ep6
- 0_0 ep7
- 0_0 ep8
- 0_0 ep9

Questions to answer:
- Where does first Stage3 artifact drift appear?
- Which episodes represent worst-case vs improved-case Stage3 behavior?
- What recurring drift taxonomy best describes Stage3 failure?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: first-drift-at-stage3 / stage3-improved-but-unstable / stage3-mostly-stable
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-04-02\0_0-stage3-static-lane4-artifact-drift-vertical-slice-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 11. Codex Synthesis Rule

After terminals 1-4 complete, Codex synthesizes them into:

- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage3-static-global-evidence.json`

The synthesis must answer:

- whether Stage3 is still the main reinterpretive drift layer
- whether Stage3 is converging toward compiler/substep status
- what the dominant residual Stage3 seam is
- what the next non-canary action should be

## 12. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a static parallel survey only
- excluded canary and execution realization

Pass 2, evidence and consistency:

- aligned the order with current Stage2 survey conclusions and known Stage3-first drift evidence
- did not overclaim runtime conclusions beyond existing static sources

Pass 3, execution and readability:

- lane ownership is clear
- outputs are concrete
- synthesis target is explicit

Confidence: `96%`
