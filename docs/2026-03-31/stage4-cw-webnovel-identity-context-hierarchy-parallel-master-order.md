# Stage4 CW Webnovel Identity Context Hierarchy Parallel Master Order

Date: 2026-03-31
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `170963d34d30d3076a57926c5d1ed250f13ec421`
Baseline Dirty Summary: `dirty: active 0_2 frontier-run logs/db/ui drift, 0_temp console scratch dirty, ep_0002/arc_002 runtime artifacts newly created or untracked`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Track: system
Mode: bounded parallel survey, no realization
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
Context Docs:
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-master-order.md`
- `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-postpatch-bounded-survey.md`
- `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md`
- `docs/2026-03-31/0_1-stage4-retry-efficiency-remediation-execution-ssot.md`
- `0_temp.txt`

## 1. Purpose

This is a bounded operator order for one question only:

- is `Chief Writer` failing because it is weak as a webnovel writer, or because the current Stage 4 prompt/context hierarchy makes it act like an analyst, summarizer, or briefing engine?

This order must test, not assume, these hypotheses:

- `writer identity conditioning` is too weak, so CW does not strongly internalize "you are a serialized webnovel author"
- prompt/context blocks that look like summaries, HUDs, advisories, and planning prose act like bad few-shot contamination
- `hard canon`, `episode mission`, `carryover truth`, and `soft guidance` are mixed on the same prompt plane instead of being hierarchically separated
- Stage 2 or Stage 3 upstream structure is already too vague or too briefing-like before CW starts
- some current failures are real continuity/truth conflicts, but are being perceived as "meta prose" because the family label is weak or misleading
- retry improves not because CW suddenly becomes better, but because retry task shape is narrower and structurally less contaminated than first-pass generation

Current motivating symptom:

- the active `0_2` frontier run around EP2 round 2-3 shows a sentence shaped like briefing-style recall:
  - `직전 화에서 확인했던 수치 그대로였다`
- current runtime output then surfaces:
  - `FlashbackVerifier` advisory
  - `A-3 continuity/history conflict`
- this order must decide whether that is:
  - primarily a real truth conflict
  - primarily a webnovel voice/meta-briefing failure
  - an upstream Stage 2/3 structuring failure
  - or a mixed case with misclassified downstream labeling

This order is for:

- read-only parallel survey
- evidence capture
- lane drafts
- later synthesis into one canonical bounded survey

This order is not for:

- code edits
- DB writes
- blueprint, arc, or manuscript edits
- `docs/temp/` mutation
- execution SSOT authoring
- queue cleanup
- resolved claims

## 2. Scope

Minimum survey scope:

- CW first-pass prompt topology
- writer identity conditioning
- anti-meta / anti-briefing guardrails
- first-pass vs retry prompt/context delta
- Stage 2 and Stage 3 upstream structure quality insofar as it feeds Stage 4
- current `0_2` runtime evidence around EP2
- downstream detector/gate classification only insofar as it may misclassify a style/voice defect as another family

Minimum authoritative evidence set:

- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/flashback_verifier.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight_runtime.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage3_context.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `projects/0_2/project_data.db`
- `projects/0_2/logs/episode_production.jsonl`
- `projects/0_2/logs/session/decisions.jsonl`
- `projects/0_2/logs/session/llm_io.jsonl`
- `projects/0_2/logs/session/ui_events.jsonl`
- `projects/0_2/logs/artifacts/stage2/arc_002/`
- `projects/0_2/logs/artifacts/stage4/ep_0002/`
- `projects/0_2/plans/arcs/arc_002.txt`
- `projects/0_2/drafts/ep_0002.txt`
- `0_temp.txt`

Prior survey context that must be treated as lower authority than live code/runtime evidence:

- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-parallel-master-order.md`
- `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-postpatch-bounded-survey.md`
- `docs/2026-03-31/0_1-stage4-retry-efficiency-remediation-execution-ssot.md`

## 3. Common Rules For All Terminals

All terminals must follow these rules:

1. Survey only.
2. Read-only only.
3. No code edits, no DB writes, no artifact edits, no `docs/temp/` edits.
4. Use live code, DB, JSONL, and artifact truth ahead of stale survey text.
5. Use `0_temp.txt` only as navigational evidence, then verify with authoritative runtime sinks or artifacts.
6. Separate `artifact truth`, `metadata truth`, and `stylistic/narrative truth`.
7. Separate these failure families explicitly:
   - hard truth conflict
   - continuity/history conflict
   - webnovel voice failure
   - meta/briefing prose
   - prompt hierarchy weakness
   - upstream Stage 2/3 structure weakness
   - downstream misclassification
8. Do not claim CW "does not know it is writing a webnovel" unless prompt identity conditioning is shown weak in the actual first-pass prompt.
9. Do not claim "meta prose" from a detector family label alone; inspect the underlying sentence and the actual conflict logic.
10. Do not claim Stage 2/3 upstream fault without tracing which structured fields actually feed Stage 4.
11. Do not claim retry is better unless first-pass vs retry task-shape differences are shown from live code or live prompt payloads.
12. Save lane drafts only under `docs/2026-03-31/`.
13. Saved lane drafts must be marked `Status: draft-bounded-partial-evidence`.
14. Terminals 1-4 are for `Opus`.
15. Terminal 5 is reserved for `Codex` synthesis after 1-4 return.

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

- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane1-prompt-topology-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane2-context-delta-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane3-stage2-stage3-upstream-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane4-runtime-symptom-taxonomy-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane5-codex-synthesis-draft.md`

Final intended outputs after synthesis:

- canonical survey doc:
  - `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-bounded-survey.md`
- raw evidence:
  - `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-evidence.json`

These final outputs are out of scope for Opus terminals 1-4.

## 5. Required Questions

The parallel survey must answer all of these:

1. Is CW explicitly conditioned as a serialized webnovel writer, not an analyst/summarizer, in the actual first-pass prompt?
2. Which prompt/context blocks behave like bad few-shot contamination:
   - summary prose
   - HUD prose
   - advisory prose
   - blueprint explanation prose
   - prior digest prose
3. Are these layers currently separated or mixed:
   - `Writer Identity Layer`
   - `Hard Canon Layer`
   - `Episode Mission Layer`
   - `Carryover Layer`
   - `Soft Guidance Layer`
   - `Anti-Pattern Layer`
4. What are the concrete differences between first-pass and retry prompt/context shape?
5. Is Stage 2 or Stage 3 already generating under-specified or briefing-shaped scene authority before CW starts?
6. In the current `0_2` EP2 symptom, is the bad sentence primarily:
   - truth conflict
   - meta/briefing prose
   - both
   - or downstream family misclassification?
7. What bounded remediation seams have the highest ROI:
   - writer identity hardening
   - context hierarchy separation
   - anti-meta negative examples / anti-pattern section
   - Stage 2/3 upstream tightening
   - detector-family relabeling

## 6. Lane Map

Use this five-lane layout:

1. `Opus Terminal 1`: prompt topology, writer identity, anti-meta contamination
2. `Opus Terminal 2`: context hierarchy, hard-vs-soft separation, first-pass vs retry delta
3. `Opus Terminal 3`: Stage 2/3 upstream scene-authority and blueprint leak
4. `Opus Terminal 4`: live runtime symptom taxonomy and downstream family misclassification
5. `Codex Terminal 5`: master synthesis after receiving 1-4

## 7. Opus Terminal 1 Order

Use this as-is:

```text
Terminal 1

Role:
- prompt topology / writer identity / anti-meta contamination lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- prove actual block order from live code or live prompt payloads
- do not infer writer identity from comments alone

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_prompts.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context_packets.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer.py
- C:\Users\User\Desktop\글도비\projects\0_2\logs\session\llm_io.jsonl

Questions to answer:
- What is the exact order of major first-pass CW prompt blocks?
- Where does writer identity appear?
- Does the prompt explicitly say CW is a serialized webnovel writer and not an analyst/summarizer?
- Are anti-patterns like briefing prose, summary prose, or meta recap explicitly banned?
- Which blocks look like bad few-shot contamination?
- Is the first-pass prompt teaching CW to narrate scenes, or to summarize/brief?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: identity-weak / identity-mixed / identity-adequate
5. Stop

Required artifact:
- block-order table
- authority-rank table
- bad-few-shot contamination table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-lane1-prompt-topology-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 8. Opus Terminal 2 Order

Use this as-is:

```text
Terminal 2

Role:
- context hierarchy / hard-vs-soft separation / first-pass vs retry delta lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- distinguish `stored` from `consumed`
- distinguish `hard canon` from `soft guidance`
- produce an explicit first-pass vs retry delta matrix

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_retry_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_reject_runtime.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context_packets.py
- C:\Users\User\Desktop\글도비\projects\0_2\logs\session\llm_io.jsonl
- C:\Users\User\Desktop\글도비\projects\0_2\logs\session\decisions.jsonl

Questions to answer:
- What fields reach first-pass generation?
- What fields reach retry generation but not first pass?
- Are `hard canon`, `episode mission`, `carryover`, `advisory`, and `negative examples` on different layers or flattened together?
- Is retry better because its task is narrower and less contaminated?
- Does retry inject more explicit conflict/repair framing than first pass?
- Which missing first-pass hierarchy edges are most responsible for meta/briefing prose?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: hierarchy-gap / delta-confirms-gap / mixed / adequate
5. Stop

Required artifact:
- first-pass vs retry delta matrix
- hard-canon vs soft-guidance separation table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-lane2-context-delta-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 9. Opus Terminal 3 Order

Use this as-is:

```text
Terminal 3

Role:
- Stage 2 / Stage 3 upstream scene-authority and blueprint leak lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- do not widen into a whole Stage 2/3 redesign
- trace only what materially feeds Stage 4 EP2 current symptom

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage2_orchestrator.py
- C:\Users\User\Desktop\글도비\modules\core\stage2_preflight_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage2_validation_pipeline.py
- C:\Users\User\Desktop\글도비\modules\core\stage2_context.py
- C:\Users\User\Desktop\글도비\modules\core\stage3_orchestrator.py
- C:\Users\User\Desktop\글도비\modules\core\stage3_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\three_phase_blueprint_generator.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\three_phase_blueprint_runtime.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py
- C:\Users\User\Desktop\글도비\projects\0_2\plans\arcs\arc_002.txt
- C:\Users\User\Desktop\글도비\projects\0_2\logs\artifacts\stage2\arc_002\
- C:\Users\User\Desktop\글도비\projects\0_2\logs\artifacts\stage4\ep_0002\

Questions to answer:
- Before CW starts, is the scene authority already vague, briefing-like, or under-specified?
- Is the opening anchor concrete enough?
- Are financial/capital facts already packed ambiguously upstream?
- Does Stage 2 or Stage 3 emit prose that encourages recap/reporting instead of scene writing?
- Is the current EP2 symptom partly caused by upstream structure rather than CW prompt hierarchy alone?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: upstream-weak / upstream-mixed / upstream-adequate
5. Stop

Required artifact:
- Stage2/3 -> Stage4 authority handoff map
- upstream ambiguity table for current EP2 symptom

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-lane3-stage2-stage3-upstream-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 10. Opus Terminal 4 Order

Use this as-is:

```text
Terminal 4

Role:
- live runtime symptom taxonomy / downstream family misclassification lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- treat 0_temp as navigational only
- verify with DB / JSONL / attempt artifact / llm_io
- separate the underlying prose defect from the detector family label

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\0_temp.txt
- C:\Users\User\Desktop\글도비\modules\core\flashback_verifier.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\projects\0_2\project_data.db
- C:\Users\User\Desktop\글도비\projects\0_2\logs\episode_production.jsonl
- C:\Users\User\Desktop\글도비\projects\0_2\logs\session\decisions.jsonl
- C:\Users\User\Desktop\글도비\projects\0_2\logs\session\llm_io.jsonl
- C:\Users\User\Desktop\글도비\projects\0_2\logs\session\ui_events.jsonl
- C:\Users\User\Desktop\글도비\projects\0_2\logs\artifacts\stage4\ep_0002\

Questions to answer:
- In the current EP2 round-2/3 symptom, what is the actual bad sentence and what family should it belong to?
- Is `FlashbackVerifier` catching a real recall/truth conflict, or is it surfacing a style/meta problem under the wrong label?
- Is the sentence bad because the numeric truth is wrong, because the prose is briefing-like, or both?
- What existing detectors catch:
  - truth conflict
  - continuity conflict
  - style/ai-slop
  - meta/briefing prose
- What important detector gap remains for webnovel anti-meta quality?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: gate-misclassified / style-gap / mixed / true-conflict-primary
5. Stop

Required artifact:
- symptom taxonomy table
- detector coverage gap table
- current EP2 sentence-level classification note

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-lane4-runtime-symptom-taxonomy-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 11. Codex Terminal 5 Order

Reserved for `Codex`, not Opus.

Use this after terminals 1-4 return:

```text
Terminal 5

Role:
- Codex-only synthesis lane after Opus terminals 1-4 return

Inputs:
- lane1 prompt topology draft
- lane2 context delta draft
- lane3 Stage2/3 upstream draft
- lane4 runtime symptom taxonomy draft
- current live code and runtime evidence if any lane discovered contradictions

Tasks:
- produce one answer-first canonical bounded survey
- decide whether the primary problem is:
  - writer identity weakness
  - context hierarchy weakness
  - upstream Stage2/3 structure weakness
  - downstream misclassification
  - or a mixed stack with ranked causes
- include a `first-pass vs retry delta matrix`
- include a `Writer Identity Layer / Hard Canon Layer / Episode Mission Layer / Carryover Layer / Soft Guidance Layer / Anti-Pattern Layer` gap table
- include a `bad few-shot contamination` table
- include a `current EP2 symptom classification` section
- rank bounded remediation seams
- decide whether a new execution SSOT is justified now or should wait for more live evidence

Canonical intended outputs:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-parallel-bounded-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\stage4-cw-webnovel-identity-context-hierarchy-parallel-evidence.json

Do not:
- patch code in this lane
- mutate docs/temp
- claim resolved
```

## 12. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a survey master order, not an execution SSOT
- made 1-4 explicitly Opus and 5 explicitly Codex-only
- included current `0_2` frontier symptom instead of pretending this is only a historical `0_1` question

Pass 2, evidence and consistency:

- aligned the order with current workspace state:
  - current head commit
  - current dirty `0_2` frontier-run evidence
  - prior `0_1` survey and execution context
- used live file paths that exist in the current workspace
- separated prior survey context from authoritative live evidence

Pass 3, execution and readability:

- each lane has a bounded responsibility
- each lane has explicit required outputs and draft path
- the synthesis lane has concrete merge duties and closure boundaries
- no temp mirror or execution queue mutation is implied

Confidence: `96%`
