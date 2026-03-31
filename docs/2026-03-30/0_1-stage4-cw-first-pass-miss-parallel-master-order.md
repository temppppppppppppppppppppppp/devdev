# 0_1 Stage4 CW First-Pass Miss Parallel Master Order

Date: 2026-03-30
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-master-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/docs-temp/log-db drift, recent EP8/EP9 survey-doc outputs untracked, operator scratch txt files present`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Track: system
Mode: bounded parallel survey, no realization
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
Context Docs:
- `docs/2026-03-28/stage4-feedback-windowing-full-survey.md`
- `docs/2026-03-29/stage4-carryover-contract-consumption-full-survey.md`
- `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`
- `docs/2026-03-29/stage4-provider-fallback-observability-gap-full-survey.md`
- `docs/2026-03-30/0_1-stage4-ep9-failure-root-cause-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep9-remediation-postpatch-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-draft-meta-leak-bounded-survey.md`

## 1. Purpose

This is a bounded operator order for one question only:

- why does `Chief Writer` often fail to produce a strong Stage 4 manuscript on the first pass?

This order must test, not assume, these hypotheses:

- prompt hierarchy is weak, so the model does not recognize the top-priority truth on first read
- prior-manuscript truth is present but semantically weak, truncated, or buried too late
- upstream structure is weak before CW starts, so CW receives under-specified scene authority
- model tier, served-model fallback, or context-budget pressure creates a real quality floor
- first-pass quality is being misread because downstream Director/advisory/gate behavior makes CW look worse than it is

This order is for:

- read-only parallel survey
- evidence capture
- bounded lane drafts
- later synthesis into one canonical bounded survey

This order is not for:

- code edits
- DB writes
- blueprint or manuscript edits
- `docs/temp/` mutation
- execution SSOT authoring
- queue cleanup
- resolved claims

## 2. Scope

Minimum survey scope:

- prompt topology and prompt-time authority ranking
- previous-manuscript ingestion and carryover consumption
- upstream blueprint and structured-context quality before first generation
- model-tier, provider, fallback, and context-budget wiring
- recent runtime evidence from `0_1` Stage 4 attempts
- downstream Director, advisory, and retry behavior only insofar as they may distort diagnosis of CW first-pass quality

Minimum authoritative evidence set:

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/llm_router.py`
- `modules/core/constants.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `config/models.yaml`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/session/llm_io.jsonl`
- `projects/0_1/logs/session/ui_events.jsonl`
- `projects/0_1/logs/artifacts/stage4/ep_0008/`
- `projects/0_1/logs/artifacts/stage4/ep_0009/`
- `projects/0_1/logs/artifacts/stage4/ep_0010/`
- `projects/0_1/plans/blueprints/blueprint_0008.txt`
- `projects/0_1/plans/blueprints/blueprint_0009.txt`
- `projects/0_1/drafts/ep_0008.txt`
- `projects/0_1/drafts/ep_0009.txt`

## 3. Common Rules For All Terminals

All terminals must follow these rules:

1. Survey only.
2. Read-only only.
3. No code edits, no DB writes, no artifact edits, no `docs/temp/` edits.
4. Use live code, DB, JSONL, and artifact truth ahead of stale survey text.
5. Use UTF-8 byte-level read-back for Korean text or manuscript evidence.
6. Do not use console mojibake or preview rendering as encoding evidence.
7. Separate `artifact truth`, `metadata truth`, and `narrative truth`.
8. Separate `CW weakness` from `upstream structure weakness`, `model/provider weakness`, and `downstream gate illusion`.
9. Do not claim `model tier problem` without checking both requested model and served/fallback evidence.
10. Do not claim `hierarchy problem` unless the prompt section order and truncation path are shown.
11. Keep lane scope bounded; do not widen into broad Stage 4 redesign.
12. Save lane drafts only under `docs/2026-03-30/`.
13. Saved lane drafts must be marked `Status: draft-bounded-partial-evidence`.
14. Terminal 5 is synthesis-only and should wait for terminals 1-4.

## 4. Output Contract

Each lane terminal must return this shape in terminal output:

1. `Coverage`
2. `Findings`
3. `Non-Issues`
4. `Verdict`
5. `Stop`

Required stop line:

- `read-only lane complete; no files mutated`

If a lane finds anything synthesis-relevant, it should also save one draft report under `docs/2026-03-30/`.

Recommended draft paths:

- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane1-prompt-topology-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane2-carryover-cognition-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane3-model-tier-budget-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane4-runtime-vs-gate-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane5-master-synthesis-draft.md`

Final intended outputs after the parallel survey returns:

- canonical survey doc:
  - `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-bounded-survey.md`
- raw evidence:
  - `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-evidence.json`

These final outputs are out of scope for the lane terminals.

## 5. Required Questions

The parallel survey must answer all of these:

1. Is `CW first-pass weakness` real, or is it being overstated by downstream advisory/gate behavior?
2. In the actual CW main prompt, are the highest-authority blocks early and salient enough?
3. Does CW receive previous-manuscript truth in a way that it can recognize as temporal authority, or is the block too truncated, too late, or too weak?
4. Is the first-pass structured input weak before generation starts:
   - opening anchor
   - immutable facts
   - scene breakdown
   - carryover ceiling
   - integrated scenario advisory
5. Is `model tier / served model / provider fallback / context budget` a real first-pass quality floor?
6. Is `candidate diversity` too shallow, so the system mistakes low search breadth for CW weakness?
7. Why do retries help when they help:
   - better information
   - narrower task
   - stronger structure
   - patch-path constraints
   - or merely different downstream scoring conditions?

## 6. Lane Map

Use this five-terminal layout:

1. Terminal 1: prompt topology and authority hierarchy
2. Terminal 2: previous-manuscript cognition and carryover consumption
3. Terminal 3: model tier, fallback, context budget, and candidate diversity
4. Terminal 4: runtime evidence and downstream gate separation
5. Terminal 5: master synthesis after receiving 1-4

## 7. Terminal 1 Order

Use this as-is:

```text
Terminal 1

Role:
- prompt topology / authority hierarchy lane for Stage4 CW first-pass diagnosis

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- prove section order and truncation path from live code
- do not infer prompt salience from comments alone

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context_packets.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_prompts.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\base_agent.py
- C:\Users\User\Desktop\글도비\modules\core\constants.py

Questions to answer:
- What is the exact order of the major CW prompt blocks on first pass?
- Which blocks are intended as highest authority, and where do they actually land?
- Are `Opening Anchor`, `Immutable Facts / prior manuscript facts / prev digest`, `Structured scene breakdown`, and `integrated scenario advisory` ordered coherently?
- Is the `previous manuscript = truth source` section late enough to be ignored or diluted?
- Where can truncation happen:
  - `smart_truncate(prev_manuscripts_text)`
  - agent-wide prompt-size gate
  - any other builder-level clipping
- Is there evidence that low-authority prose blocks can overshadow higher-authority structured blocks?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: hierarchy-weak / hierarchy-adequate / mixed
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-lane1-prompt-topology-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 8. Terminal 2 Order

Use this as-is:

```text
Terminal 2

Role:
- previous-manuscript cognition / carryover consumption lane

Common guardrails:
- survey only
- read-only only
- distinguish `stored` from `consumed`
- distinguish `prompt-visible` from `operator-visible only`
- do not claim CW ignores the past unless the actual prompt-consumed path is shown

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-29\stage4-carryover-contract-consumption-full-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-29\stage4-retry-loop-compression-full-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_retry_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_reject_runtime.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context_packets.py
- C:\Users\User\Desktop\글도비\projects\0_1\logs\episode_production.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\session\decisions.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\project_data.db

Questions to answer:
- What previous-manuscript and carryover fields reach first-pass CW generation?
- What fields reach retry generation but not first pass?
- Does CW receive:
  - previous manuscript full text
  - previous ending
  - previous digest
  - carryover ceiling
  - reuse baseline
  - conflict contract
- Which of those are merely persisted, and which are actually consumed by prompt assembly?
- Is the `previous manuscript = truth source` instruction explicit enough, and is it reinforced elsewhere or only once?
- Does retry performance improve because the retry prompt is structurally better than the first-pass prompt?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: cognition-gap / carryover-gap / adequate / mixed
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-lane2-carryover-cognition-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 9. Terminal 3 Order

Use this as-is:

```text
Terminal 3

Role:
- model tier / provider / fallback / context-budget / candidate-diversity lane

Common guardrails:
- survey only
- read-only only
- separate `requested model` from `served model`
- do not blame model tier unless the fallback and budget evidence are checked
- do not collapse provider contamination into generic CW weakness

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-29\stage4-provider-fallback-observability-gap-full-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\config\models.yaml
- C:\Users\User\Desktop\글도비\modules\core\constants.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\base_agent.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer.py
- C:\Users\User\Desktop\글도비\modules\core\llm_router.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_orchestrator.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\projects\0_1\logs\session\llm_io.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\episode_production.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\runtime_audit.jsonl

Questions to answer:
- What model tier is requested for Stage4 CW first pass?
- What fallback chain is available for that model?
- What served-model evidence exists in recent 0_1 first-pass attempts?
- Is `episode_production.jsonl model_tier` reliable enough for diagnosis, or is it only the requested model alias?
- Does prompt size pressure likely exceed useful model capacity on first pass?
- Is candidate generation truly diverse:
  - strategy budget
  - strategy ordering / bias reuse
  - fallback candidate behavior
- Could low first-pass quality be a model/provider floor rather than a prompt-structure floor?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: model-floor / provider-floor / budget-floor / not-model-first / mixed
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-lane3-model-tier-budget-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 10. Terminal 4 Order

Use this as-is:

```text
Terminal 4

Role:
- runtime evidence / downstream gate separation lane

Common guardrails:
- survey only
- read-only only
- compare first-pass manuscript quality claims against actual artifacts and persisted reasons
- separate CW-first failure from Director/advisory/retry illusion
- do not overfit to EP9 only; use recent 0_1 evidence but keep scope bounded

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-ep9-failure-root-cause-bounded-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-ep9-remediation-postpatch-bounded-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-draft-meta-leak-bounded-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_retry_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_outcome_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_reject_runtime.py
- C:\Users\User\Desktop\글도비\projects\0_1\project_data.db
- C:\Users\User\Desktop\글도비\projects\0_1\logs\episode_production.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\session\decisions.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\session\llm_io.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\session\ui_events.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\artifacts\stage4\ep_0008\attempt_*
- C:\Users\User\Desktop\글도비\projects\0_1\logs\artifacts\stage4\ep_0009\attempt_*
- C:\Users\User\Desktop\글도비\projects\0_1\logs\artifacts\stage4\ep_0010\attempt_*

Questions to answer:
- On recent episodes, how often is the first-pass manuscript itself weak versus the downstream reason being stale truth, false advisory, fix-pack deadlock, or provider contamination?
- What are the top persisted first-pass reject reasons by family?
- Do retries help because CW receives better task framing, or because the downstream gate changes its basis?
- Are there cases where first-pass manuscripts are structurally acceptable but are marked poor for non-CW reasons?
- Is `CW writes badly from the start` a true diagnosis, or a blended diagnosis that collapses multiple layers?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: cw-first / blended / downstream-first
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-lane4-runtime-vs-gate-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 11. Terminal 5 Order

Use this as-is:

```text
Terminal 5

Role:
- master synthesis lane

Important:
- do not start with broad discovery
- wait for terminals 1-4 to finish
- if lane reports conflict, point to missing evidence first
- do not force a single-cause answer if the evidence supports a layered answer

Inputs:
- terminal 1 final report
- terminal 2 final report
- terminal 3 final report
- terminal 4 final report

Final goal:
- classify the CW first-pass problem into one or more primary buckets:
  - hierarchy / prompt topology
  - prior-manuscript cognition
  - upstream structure weakness
  - model/provider/context-budget floor
  - shallow candidate search
  - downstream gate illusion
- rank primary blocker versus secondary blocker
- state the smallest correct next move:
  - further survey only
  - bounded execution SSOT
  - no action because diagnosis is overstated

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict
5. Stop

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-stage4-cw-first-pass-miss-lane5-master-synthesis-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 12. Post-Survey Handoff Rule

After terminals 1-5 finish:

1. collect the lane draft reports
2. run a document-side 3-pass audit on those reports
3. synthesize one canonical bounded survey
4. create execution SSOT only if the merged evidence still shows a code-side remediation target

Execution-SSOT generation is explicitly out of scope for the lane terminals.

## 13. 3-Pass Audit Record

Pass 1, structure and scope:

- document type is survey master order, not execution SSOT
- scope is explicit: CW first-pass miss diagnosis only
- canonical path is dated docs only
- `docs/temp/` exclusion is explicit
- lane outputs and later canonical outputs are separated

Pass 2, evidence and consistency:

- baseline commit and dirty summary were refreshed from the live workspace
- lane scope matches live code surfaces already known to own prompt assembly, carryover, model routing, and runtime verdict sinks
- prior surveys are support only; live code/log/db/artifact surfaces remain authoritative

Pass 3, execution and readability:

- lane scopes are non-overlapping enough for parallel use
- output contract is explicit
- required questions are concrete enough to avoid vague "CW just writes badly" conclusions
- post-survey handoff stays bounded and does not silently escalate into realization

Confidence: 96%
