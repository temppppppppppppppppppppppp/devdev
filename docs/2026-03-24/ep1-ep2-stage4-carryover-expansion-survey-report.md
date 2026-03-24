# EP1 -> EP2 Stage4 Carryover Expansion Survey Report

Date: 2026-03-24
Status: final
Canonical Path: `docs/2026-03-24/ep1-ep2-stage4-carryover-expansion-survey-report.md`
Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
Baseline Dirty Summary: `dirty workspace; active temp queue empty at survey start; many unrelated tracked edits/deletions already present outside this topic`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Prior Inputs:
- `docs/2026-03-24/ep1-ep2-handoff-residual-opus-survey-report.md`
- `docs/2026-03-24/console.txt`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-semantic-carryover-boundary-wave2-execution-ssot.md`
Primary Evidence Artifacts:
- `projects/00_0324_2/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_0324_2/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt`
- `projects/00_0324_2/logs/artifacts/stage4/ep_0002/attempt_04/selected_before_fix__A.txt`
- `projects/00_0324_2/logs/episode_production.jsonl`
Code Surfaces Re-audited:
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
Side-Effect Coverage:
- Stage 4 writer prompt assembly
- Stage 4 retry snapshot / retry-budget mutation
- Stage 4 JSONL and artifact logging
- console feedback / operator-visible reject guidance
- no DB schema or artifact naming change proposed in this survey

## 1. Executive Summary

Fresh run evidence shows the earlier Stage 2 -> Stage 3 leakage waves helped: ep1 no longer collapses ep3/ep4 state into the opening run. The active failure moved downstream.

The current ep2 instability is a Stage 4 dominant mixed seam:

1. The ep2 blueprint still applies pressure toward over-planning and shady-fund execution.
2. The strongest contradictions are introduced in Stage 4 manuscript expansion, not in the stored ep2 blueprint.
3. The retry loop then preserves too much of the offending expansion because post-select hard conflicts are downgraded into partial/local retry budgeting.

The prior Opus survey is useful as a warning signal, but it overclaims `Stage 3 primary`. Live artifact truth does not support that weighting.

Current confidence: 96%.

## 2. Included Coverage / Exclusions

Included:
- ep1 final blueprint and final manuscript
- ep2 final blueprint and rejected/selected Stage 4 attempts
- ep2 console trace and episode JSONL trace
- Chief Writer prompt packing and Stage 4 reject/retry code paths

Excluded:
- Stage 2 density / allocation redesign
- Stage 3 blueprint generation redesign
- Director model / scoring redesign
- global persona taxonomy cleanup
- live implementation

## 3. Artifact Truth Ledger

### 3.1 EP1 Established Facts

EP1 final artifact truth is stable and narrow:

- End position: window-side ending after writing, not bed restart
  - `final_manuscript__A.txt:82-87`
- Note state: the notebook is already half filled with future economic timeline notes
  - `final_manuscript__A.txt:78-82`
- WTI planning state: the `20억 / 3배 레버리지 / 18억 수익` computation is already completed in ep1
  - `final_manuscript__A.txt:78`
- Persona state: still a neglected rich-family rider, not an already-operational fixer with covert finance infrastructure
  - `final_manuscript__A.txt:91-101`
- Explicit equipment on page: notebook and pen
  - `final_blueprint__emotion_focused.json:29-33`

### 3.2 EP2 Blueprint: Real Pressure vs Overclaim

The saved ep2 blueprint does contain real pressure:

- It asks for `20억` cash-routing via personal luxury liquidation and a shady dealer lane.
  - `final_blueprint__emotion_focused.json:69-79`
- It repeats the WTI timeline and exit math as an active scene objective.
  - `final_blueprint__emotion_focused.json:81-97`
- Its integrated scenario expands those same plans into longer prose.
  - `final_blueprint__emotion_focused.json:26`

But the saved blueprint does not contain the strongest later inventions:

- no `암호화된 대포폰`
- no named offshore broker such as `제임스`
- no explicit `버진아일랜드 페이퍼 컴퍼니`
- no explicit `스위스 계좌`

This matters because it means the current dominant contradiction is not "the blueprint already hard-coded the whole illegal network." The blueprint is an amplifier, not the complete culprit.

### 3.3 EP2 Stage 4 Expansion: Direct Contradictions

Stage 4 attempt 1 introduces the strongest artifact-truth conflicts:

- `암호화된 대포폰`
  - `rejected_best__A_tension.txt:35`
- direct disposal call to `박 사장`
  - `rejected_best__A_tension.txt:39-45`
- offshore setup call and `버진아일랜드` / `스위스`
  - `rejected_best__A_tension.txt:61-69`
- repeated WTI math that ep1 already completed
  - `rejected_best__A_tension.txt:77-80`
- wrong body-position restart from bed
  - `rejected_best__A_tension.txt:22`
- wrong note-state reset to blank paper
  - `rejected_best__A_tension.txt:29`

Attempt 4 softens some details but still retains invented infrastructure beyond ep1 authority:

- `예전 휴대폰` replaces the burner phone
  - `selected_before_fix__A.txt:35`
- `유학 시절 ... 에이전트` replaces the named broker
  - `selected_before_fix__A.txt:61`
- but offshore `버진아일랜드` / `스위스` remains
  - `selected_before_fix__A.txt:63`

So the run improved enough to pass eventually, but the pass still required Stage 4 to improvise infrastructure that was not previously grounded on page.

## 4. Console and JSONL Assessment

The post-select lane is not hallucinating; it is catching real conflicts:

- persona / capability / infrastructure conflict
  - `console.txt:681-689`
- history replay conflict for repeated WTI plan math
  - `console.txt:683-691`
- body-position + note-state conflict
  - `console.txt:795-805`
- residual note-content conflict
  - `console.txt:919-927`

The deeper problem is what the retry system preserves:

- round 1 logging still frames broker calls and hidden-finance execution as a strength worth preserving
  - `episode_production.jsonl:2`
- the local fix pack focuses on notebook placement only
  - `episode_production.jsonl:2`
- round 2 still praises `대포폰` execution and only asks for body-position repair
  - `episode_production.jsonl:4`
- round 3 still records a perfect PASS before a post-select REJECT downgrade
  - `episode_production.jsonl:6`

This is why the run burns retries on local repairs while the more structural Stage 4 invention pressure remains alive.

## 5. Code Path Assessment

### 5.1 Chief Writer Prompt Hierarchy Is Too Flat

`chief_writer_context.py` currently merges blueprint JSON scenes and the full integrated scenario into one `scene_breakdown` blob:

- `chief_writer_context.py:273-279`

Then the main prompt presents that merged blob as the Stage 4 Step 1 blueprint authority surface:

- `chief_writer_prompts.py:127-136`

There is no explicit precedence note telling the writer that:

- `opening_anchor`
- immutable facts
- previous-episode digest
- scene-level structured fields

override long-form `integrated_scenario` prose when they conflict.

This does not prove that `integrated_scenario` alone caused the burner phone or offshore layer. It does prove that Stage 4 receives an overpowered long-form narrative draft in the same authority band as the structured blueprint.

The same bias reaches two more upstream Stage 4 paths:

- `stage4_interview_round.py:1937-1959` passes the raw blueprint into `WritingDirectiveGenerator`
- `writing_directive_generator.py:120-143` summarizes `integrated_scenario` before scene goals
- `stage4_interview_round.py:2031-2058` passes the raw blueprint again into the common writer kwargs

So the current hierarchy problem is not just one prompt string. It is a repeated raw-blueprint handoff inside Stage 4.

### 5.2 Carryover Guard Covers Items Better Than Operational Capability

`ChiefWriterContextPackets.build_common_context_packets()` produces:

- future item guard
- past death/injury guard
- previous manuscript excerpt
- episode digest

Relevant surfaces:

- `chief_writer_context_packets.py:52-183`
- `chief_writer_context_packets.py:486-517`

The problem is not absence of carryover material in general. The problem is that there is no compact Stage 4 carryover ceiling saying:

- what operational tools are explicitly on page now
- what contacts are explicitly on page now
- what has already been fully computed and should not be re-performed as a fresh scene

So Stage 4 is guarded against some `future item` errors, but not against "invent covert infrastructure to make this investment plot feel sharper."

### 5.3 Retry Guidance Still Shrinks Hard Conflicts Into Patch-Oriented Retries

`Stage4RejectRuntime` does useful work:

- it merges post-select conflict feedback into retry state
- it can widen some IFC failures
- it classifies violation families

Relevant surfaces:

- `stage4_reject_runtime.py:404-554`
- `stage4_reject_runtime.py:318-402`
- `stage4_interview_round.py:3628-3784`
- `stage4_retry_runtime.py:866-1031`

But the live retry snapshot still keeps:

- `patch_revision` repair budgeting for non-full scopes
  - `stage4_reject_runtime.py:387-398`
- explicit early `post_select_conflict` force-patch bias
  - `stage4_retry_runtime.py:866-895`
- prior positive selection rationale and do-not-regress surfaces even when later post-select hard conflicts undercut them
  - `stage4_reject_runtime.py:348-385`

This matches the live run: the system keeps preserving the action-oriented illegal-finance texture while only rotating local fixes around notebook position, body start, and note wording.

## 6. Cleared Non-Culprits

- Stage 2 density / allocation is not the active blocker in this fresh run.
- The post-select reject lane is mostly correct, not the culprit.
- The saved ep2 blueprint is not innocent, but it is not the direct source of the strongest illegal-infrastructure inventions.
- The old `ep1 eats ep3/ep4` Stage 3 leakage chain is no longer the main live problem in `00_0324_2`.
- `selected -> validation_result` letter-index resolution in reject guidance is a real code smell, but it was not proven as the active culprit in this run.

## 7. Best Current Interpretation

The current residual seam is:

- `Stage 4 candidate expansion mismatch` as the primary direct culprit
- `Stage 4 prompt hierarchy / carryover ceiling weakness` as the enabling substrate
- `Stage 4 reject-budget downscoping` as the process amplifier
- `Stage 3 blueprint over-planning` as a secondary amplifier, not the main direct culprit

That is narrower and more defensible than `Stage 3 primary`.

## 8. Recommendation

Open one bounded execution SSOT now.

That wave should stay in Stage 4 and cover only:

1. Blueprint hierarchy: structured scene contract and carryover facts outrank integrated scenario prose.
2. Carryover ceiling: explicitly surface what tools / contacts / completed planning facts are already established, and forbid one-hop invention of covert infrastructure absent authority.
3. Retry hygiene: once post-select hard conflicts fire, do not preserve the offending invented infrastructure as a protected strength and do not default to early force-patch budgeting unless the remaining issue is truly local-only.

No Stage 2 or Stage 3 redesign is needed in this wave.

## 9. Mandatory Final Lines

- Dominant seam: mixed seam (Stage 4 primary direct culprit, Stage 3 secondary amplifier)
- Are the post-select rejects mostly valid: yes
- Should Codex open an execution SSOT immediately: yes
