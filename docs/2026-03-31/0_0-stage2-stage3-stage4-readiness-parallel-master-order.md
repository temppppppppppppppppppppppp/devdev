# 0_0 Stage2-Stage3 Stage4-Readiness Parallel Master Order

Date: 2026-03-31
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-master-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `dirty: recent queue-closure docs and roadmap edits, active 0_0 runtime logs/db/artifacts present, 0_temp console scratch dirty`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Track: system
Mode: bounded parallel survey, no realization
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
Context:
- `Stage4 is paused by operator for this investigation`
- `0_temp.txt`

## 1. Purpose

This is a bounded operator order for one question only:

- are `Stage 2` and `Stage 3`, as currently implemented and as currently materialized in `0_0`, structurally capable of supporting Stage 4 progression?

This order must test, not assume, these hypotheses:

- `Stage 2` arc/tactical/state output is already ambiguous, under-specified, or self-contradictory before Stage 3 starts
- `Stage 3` transforms Stage 2 authority into blueprint artifacts in a way that loses, weakens, or contaminates the authority Stage 4 needs
- the problem is not only code contract, but also `real artifact truth`
- some Stage 4 failures may be downstream symptoms of upstream `Stage 2 -> Stage 3` handoff weakness rather than Stage 4-only defects
- Stage 2 and Stage 3 may each look locally acceptable while still failing the `Stage4-readiness` contract at the boundary

This order is for:

- read-only parallel survey
- code-path and artifact-path investigation
- real-asset inspection
- later synthesis into one canonical bounded survey

This order is not for:

- code edits
- DB writes
- artifact edits
- Stage 4 rerun
- `docs/temp/` mutation
- execution SSOT authoring
- queue cleanup
- resolved claims

## 2. Scope

Minimum survey scope:

- Stage 2 authority and state packet quality
- Stage 3 transformation and validator contract quality
- real `0_0` artifacts from Stage 2 and Stage 3
- Stage 4 intake/readiness contract, but only as a consumer-readiness check because Stage 4 is paused
- vertical-slice artifact truth across at least:
  - `arc_001`
  - `arc_002`
  - `ep_0001`
  - `ep_0002`
  - one or more higher-attempt episodes inside `ep_0005` to `ep_0008`

Minimum authoritative evidence set:

- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight_runtime.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage3_context.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `modules/core/stage4_interview_round.py`
- `projects/0_0/project_data.db`
- `projects/0_0/plans/arcs/arc_001.txt`
- `projects/0_0/plans/arcs/arc_002.txt`
- `projects/0_0/plans/blueprints/blueprint_0001.txt`
- `projects/0_0/plans/blueprints/blueprint_0002.txt`
- `projects/0_0/plans/blueprints/blueprint_0005.txt`
- `projects/0_0/plans/blueprints/blueprint_0006.txt`
- `projects/0_0/plans/blueprints/blueprint_0008.txt`
- `projects/0_0/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json`
- `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/0_0/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__action_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0005/attempt_06/final_blueprint__action_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0006/attempt_09/final_blueprint__dialogue_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/0_0/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__C.txt`
- `projects/0_0/logs/artifacts/stage4/ep_0002/attempt_01/selected_candidate__A.txt`
- `projects/0_0/logs/episode_production.jsonl`
- `projects/0_0/logs/session/decisions.jsonl`
- `projects/0_0/logs/session/llm_io.jsonl`
- `projects/0_0/logs/session/ui_events.jsonl`
- `0_temp.txt`

## 3. Common Rules For All Terminals

All terminals must follow these rules:

1. Survey only.
2. Read-only only.
3. No code edits, no DB writes, no artifact edits, no `docs/temp/` edits.
4. `Stage 4 is paused`; use existing Stage 4 artifacts only as consumer-readiness evidence, not as a live-run target.
5. Use live code, DB, JSONL, and artifact truth ahead of stale survey text.
6. Use `0_temp.txt` only as navigational evidence, then confirm against authoritative sinks or artifacts.
7. Separate `artifact truth`, `metadata truth`, and `narrative truth`.
8. Explicitly distinguish:
   - Stage 2 source-authority weakness
   - Stage 3 transformation weakness
   - Stage 3 validator/contract weakness
   - Stage 2 -> Stage 3 handoff drift
   - Stage 3 -> Stage 4 intake-readiness weakness
9. Do not claim Stage 4 is the primary problem unless the Stage 2/3 handoff artifacts are shown structurally sound.
10. Do not claim Stage 2 or Stage 3 is broken from code alone; inspect the real `0_0` artifacts.
11. Saved lane drafts must be marked `Status: draft-bounded-partial-evidence`.
12. Save lane drafts only under `docs/2026-03-31/`.
13. Terminals 1-4 are for `Opus`.
14. Terminal 5 is reserved for `Codex` synthesis after 1-4 return.

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

- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane1-stage2-authority-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane2-stage3-transform-validator-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane3-artifact-truth-vertical-slice-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane4-stage4-intake-readiness-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane5-codex-synthesis-draft.md`

Final intended outputs after synthesis:

- canonical survey doc:
  - `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- raw evidence:
  - `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-evidence.json`

These final outputs are out of scope for Opus terminals 1-4.

## 5. Required Questions

The parallel survey must answer all of these:

1. Is Stage 2 producing arc/tactical/state authority that is concrete enough for Stage 3 and later Stage 4 consumption?
2. Does Stage 3 preserve the Stage 2 authority, or does it weaken/contaminate/drift it during blueprint generation?
3. Are the actual Stage 3 blueprints structurally Stage4-consumable:
   - opening anchor
   - time/timeline
   - capital/state facts
   - scene participants
   - episode mission clarity
4. Is the Stage 3 validator currently sufficient to stop artifacts that are obviously not Stage4-ready?
5. In `0_0`, are the real Stage 2 and Stage 3 artifacts already misaligned even before Stage 4 runs?
6. Does Stage 4 intake expect stronger authority than Stage 2/3 currently provide?
7. Is the correct verdict:
   - Stage2/3 structurally ready
   - Stage2/3 structurally fragile
   - or Stage2/3 structurally blocking for Stage 4 progression?

## 6. Lane Map

Use this five-lane layout:

1. `Opus Terminal 1`: Stage 2 authority / arc-state contract lane
2. `Opus Terminal 2`: Stage 3 transformation / validator / contract lane
3. `Opus Terminal 3`: artifact-truth vertical-slice lane
4. `Opus Terminal 4`: Stage 4 intake-readiness lane
5. `Codex Terminal 5`: synthesis after 1-4 return

## 7. Opus Terminal 1 Order

Use this as-is:

```text
Terminal 1

Role:
- Stage 2 authority / arc-state contract lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- no code edits, no DB writes, no docs/temp mutation
- inspect both code contract and real Stage 2 artifacts
- do not widen into broad Stage 2 redesign

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\document-3pass-audit-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage2_orchestrator.py
- C:\Users\User\Desktop\글도비\modules\core\stage2_preflight_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage2_validation_pipeline.py
- C:\Users\User\Desktop\글도비\modules\core\stage2_context.py
- C:\Users\User\Desktop\글도비\projects\0_0\plans\arcs\arc_001.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\arcs\arc_002.txt
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage2\arc_001\attempt_01\final_arc__creative.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage2\arc_002\attempt_01\final_arc__balanced.json

Questions to answer:
- What authority does Stage 2 claim to emit?
- Are arc tactical intent, timeline, capital/state, and mission contracts concrete enough?
- Are the actual Stage 2 artifacts under-specified, contradictory, or briefing-shaped?
- Which Stage 2 fields are likely to be required downstream by Stage 3 and Stage 4 but are weak or ambiguous now?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: stage2-adequate / stage2-fragile / stage2-blocking
5. Stop

Required artifact:
- Stage 2 authority table
- Stage 2 ambiguity table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-lane1-stage2-authority-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 8. Opus Terminal 2 Order

Use this as-is:

```text
Terminal 2

Role:
- Stage 3 transformation / validator / contract lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- distinguish generation weakness from validator weakness
- inspect both code and real blueprint artifacts

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage3_orchestrator.py
- C:\Users\User\Desktop\글도비\modules\core\stage3_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\three_phase_blueprint_generator.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\three_phase_blueprint_runtime.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_constraint_compiler.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\blueprint_ensemble.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\unified_blueprint_validator.py
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0001.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0002.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0005.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0006.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0008.txt
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0001\attempt_01\final_blueprint__action_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0002\attempt_01\final_blueprint__emotion_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0005\attempt_06\final_blueprint__action_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0006\attempt_09\final_blueprint__dialogue_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0008\attempt_01\final_blueprint__dialogue_focused.json

Questions to answer:
- Does Stage 3 preserve Stage 2 authority or weaken it?
- Are Stage 3 blueprints structurally ready for Stage 4 consumption?
- Which missing or weak blueprint contracts remain:
  - scene participants
  - timeline
  - capital/state
  - opening anchor
  - mission clarity
- Is Stage 3 validator sufficient to block obviously non-ready blueprints?
- Which weakness is generation-side and which is validator-side?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: stage3-adequate / stage3-fragile / stage3-blocking
5. Stop

Required artifact:
- Stage 3 transform table
- validator blind-spot table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-lane2-stage3-transform-validator-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 9. Opus Terminal 3 Order

Use this as-is:

```text
Terminal 3

Role:
- artifact-truth vertical-slice lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- inspect real artifacts, not only code
- separate artifact truth, metadata truth, and narrative truth

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\projects\0_0\project_data.db
- C:\Users\User\Desktop\글도비\projects\0_0\logs\episode_production.jsonl
- C:\Users\User\Desktop\글도비\projects\0_0\logs\session\decisions.jsonl
- C:\Users\User\Desktop\글도비\projects\0_0\logs\session\llm_io.jsonl
- C:\Users\User\Desktop\글도비\projects\0_0\logs\session\ui_events.jsonl
- C:\Users\User\Desktop\글도비\projects\0_0\plans\arcs\arc_001.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\arcs\arc_002.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0001.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0002.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0005.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0006.txt
- C:\Users\User\Desktop\글도비\projects\0_0\plans\blueprints\blueprint_0008.txt
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage2\arc_001\attempt_01\final_arc__creative.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage2\arc_002\attempt_01\final_arc__balanced.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0001\attempt_01\final_blueprint__action_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0002\attempt_01\final_blueprint__emotion_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0005\attempt_06\final_blueprint__action_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0006\attempt_09\final_blueprint__dialogue_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0008\attempt_01\final_blueprint__dialogue_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage4\ep_0001\attempt_01\final_manuscript__C.txt
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage4\ep_0002\attempt_01\selected_candidate__A.txt

Questions to answer:
- In real artifacts, where does the vertical slice start to drift:
  - arc source
  - Stage 2 artifact
  - Stage 3 blueprint
  - or Stage 4 intake expectation?
- Do the actual blueprints preserve enough detail for Stage 4 to proceed?
- Are there episodes where the real blueprint is already obviously under-specified before any Stage 4 decision?
- Are there episodes where metadata says acceptable but artifact truth says not Stage4-ready?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: artifact-ready / artifact-fragile / artifact-blocking
5. Stop

Required artifact:
- vertical-slice truth table
- per-episode readiness table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-lane3-artifact-truth-vertical-slice-draft.md
- mark it `Status: draft-bounded-partial-evidence`
```

## 10. Opus Terminal 4 Order

Use this as-is:

```text
Terminal 4

Role:
- Stage 4 intake-readiness lane

Model:
- Opus

Common guardrails:
- survey only
- read-only only
- Stage 4 remains paused
- inspect only what Stage 4 expects from Stage 2/3, not broad Stage 4 pathology

Read first:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-parallel-master-order.md

Required surfaces:
- C:\Users\User\Desktop\글도비\modules\core\stage4_context_builder.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_immutable_fact_contract.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context.py
- C:\Users\User\Desktop\글도비\modules\domain\agents\chief_writer_context_packets.py
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0001\attempt_01\final_blueprint__action_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0002\attempt_01\final_blueprint__emotion_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0005\attempt_06\final_blueprint__action_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0006\attempt_09\final_blueprint__dialogue_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage3\ep_0008\attempt_01\final_blueprint__dialogue_focused.json
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage4\ep_0001\attempt_01\final_manuscript__C.txt
- C:\Users\User\Desktop\글도비\projects\0_0\logs\artifacts\stage4\ep_0002\attempt_01\selected_candidate__A.txt
- C:\Users\User\Desktop\글도비\0_temp.txt

Questions to answer:
- What does Stage 4 actually expect from Stage 2/3 handoff?
- Do existing Stage 3 blueprints satisfy those intake expectations?
- Which missing or weak fields are most likely to cause Stage 4 churn even if Stage 4 code is otherwise healthy?
- Is the right diagnosis for 0_0:
  - Stage 4 is not getting enough authority
  - Stage 4 is getting authority but in the wrong shape
  - or Stage 2/3 are already structurally sufficient and the problem likely lies later?

Required output:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: intake-ready / intake-fragile / intake-blocking
5. Stop

Required artifact:
- Stage4 intake contract table
- missing-authority handoff table

Draft path:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-lane4-stage4-intake-readiness-draft.md
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
- lane1 Stage 2 authority draft
- lane2 Stage 3 transform/validator draft
- lane3 artifact-truth vertical-slice draft
- lane4 Stage 4 intake-readiness draft
- current live code and artifact evidence if any lane reports contradictions

Tasks:
- produce one answer-first canonical bounded survey
- decide whether the primary blocker is:
  - Stage 2 authority weakness
  - Stage 3 transformation weakness
  - Stage 3 validator weakness
  - artifact truth drift
  - Stage 4 intake mismatch
  - or a mixed stack with ranked causes
- include a `Stage2 -> Stage3 -> Stage4 readiness ladder`
- include an `artifact truth / metadata truth / narrative truth` matrix
- include a `per-episode readiness table`
- rank bounded remediation seams
- decide whether a new execution SSOT is justified now or whether more live evidence is required

Canonical intended outputs:
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md
- C:\Users\User\Desktop\글도비\docs\2026-03-31\0_0-stage2-stage3-stage4-readiness-parallel-evidence.json

Do not:
- patch code in this lane
- mutate docs/temp
- claim resolved
```

## 12. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a survey master order, not an execution SSOT
- fixed the task boundary to `Stage4 paused; inspect Stage2/3 first`
- bounded the question to `Stage4-readiness`, not broad subsystem redesign

Pass 2, evidence and consistency:

- aligned the order to real `0_0` paths that exist in the current workspace
- included both code truth and real artifact truth
- separated authoritative live evidence from `0_temp.txt` navigational evidence

Pass 3, execution and readability:

- each lane has a bounded responsibility
- real artifacts are explicitly included rather than implied
- synthesis duties are concrete and do not silently escalate into realization

Confidence: `97%`
