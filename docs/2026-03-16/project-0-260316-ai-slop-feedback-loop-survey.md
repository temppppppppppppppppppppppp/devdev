# Project 0_260316 AI-Slop Feedback Loop Survey

Date: 2026-03-16
Status: canonical survey
Scope: `0_260316` Stage 4 `ai_slop` telemetry, Director style rejection visibility, and Chief Writer retry-loop ingress
Confidence After 3-Pass Audit: `96%`

## Executive Verdict

- **Fact:** `ai_slop_score` and `ai_slop_hits` are computed in Stage 4 post-processing after a final manuscript exists, then saved into sidecar storage and dashboard records. They are not part of the main retry-routing payload.
- **Fact:** Chief Writer retry input is assembled from `director_feedback`, `rejection_reason`, `score_breakdown`, `validation_warnings`, `open_review`, `action_items`, `runtime_advisory`, and `retry_directives`. The automatic `quality_signals` bundle does not enter that path.
- **Fact:** `0_260316` raw evidence shows final PASS manuscripts in `ep2` through `ep6` did accumulate `ai_slop_hits`, but Stage 4 REJECT rows recorded empty `quality_signals`, and retry payloads carried `NpcDrift`, `Flashback`, and continuity guidance instead.
- **Fact:** Chief Writer can still learn about style problems if Director manually writes them into `director_feedback`, `open_review`, `action_items`, or `rejection_reason`. That manual path exists.
- **Fact:** `0_260316` does not contain any literal `AI 티` or `AI Slop` wording in Director feedback logs. In this run, the style telemetry stayed monitoring-only.
- **Decision:** the current system treats AI-slop as telemetry/analytics, not as an active remediation loop. Improvement should be a bounded, Director-mediated style feedback lane, not an automatic Python reject path.

## Evidence Base

### Raw Run Evidence

- `projects/0_260316/logs/quality_metrics.jsonl:14`
- `projects/0_260316/logs/quality_metrics.jsonl:27`
- `projects/0_260316/logs/quality_metrics.jsonl:30`
- `projects/0_260316/logs/quality_metrics.jsonl:32`
- `projects/0_260316/logs/quality_metrics.jsonl:34`
- `projects/0_260316/logs/quality_metrics.jsonl:37`
- `projects/0_260316/logs/quality_metrics.jsonl:39`
- `projects/0_260316/logs/quality_metrics.jsonl:41`
- `projects/0_260316/logs/quality_metrics.jsonl:43`
- `projects/0_260316/logs/quality_metrics.jsonl:46`
- `projects/0_260316/logs/session/decisions.jsonl:15`
- `projects/0_260316/logs/session/decisions.jsonl:16`
- `projects/0_260316/logs/session/decisions.jsonl:19`
- `projects/0_260316/logs/session/decisions.jsonl:20`
- `projects/0_260316/drafts/ep_0002.txt:11`
- `projects/0_260316/drafts/ep_0003.txt:61`
- `projects/0_260316/drafts/ep_0003.txt:79`
- `projects/0_260316/drafts/ep_0004.txt:83`
- `projects/0_260316/drafts/ep_0005.txt:65`
- `projects/0_260316/drafts/ep_0005.txt:89`
- `projects/0_260316/drafts/ep_0006.txt:3`
- `projects/0_260316/drafts/ep_0006.txt:26`

### Code Revalidation

- `modules/core/stage4_post_processor.py:304-367`
- `modules/core/stage4_post_processor.py:1299-1304`
- `modules/core/quality_signal_metrics.py:129-202`
- `modules/core/db_manager.py:2910-2940`
- `modules/core/quality_dashboard.py:137-147`
- `modules/api/bridge_server.py:1021-1036`
- `modules/core/stage4_interview_round.py:401-424`
- `modules/core/stage4_interview_round.py:3534-3560`
- `modules/domain/agents/chief_writer.py:799-920`
- `modules/domain/agents/chief_writer.py:1551-1669`
- `modules/domain/agents/chief_writer.py:1705-1759`

### Test Revalidation

- `tests/test_stage4_post_processor.py:179-206`
- `tests/test_stage4_post_processor.py:480-507`
- `tests/test_stage4_interview_round.py:1870-1910`
- `tests/test_bridge_quality_summary.py:20-48`
- `tests/test_quality_signal_metrics.py:23-29`

## Findings

### F1. `ai_slop` is generated after final-manuscript post-processing, not during retry assembly

`modules/core/stage4_post_processor.py:304-367` computes `_quality_signals = compute_quality_signal_bundle(final_manuscript, ...)` and immediately persists them via `save_episode_quality_signal`. The same post-processed bundle is only later attached to dashboard validation records at `modules/core/stage4_post_processor.py:1299-1304`.

This means the system sequence is:

1. final manuscript exists
2. quality signal bundle is computed
3. bundle is stored in sidecar DB/dashboard sinks

It does **not** mean:

1. candidate is scored for `ai_slop`
2. retry payload is enriched
3. Chief Writer is told what phrase-level style residue to remove

Supporting code:

- `modules/core/quality_signal_metrics.py:129-202` defines `compute_ai_slop()` and returns `ai_slop_score`, `ai_slop_hits`, and `signal_summary`
- `modules/core/db_manager.py:2910-2940` stores and loads `episode_quality_signals`
- `modules/core/quality_dashboard.py:137-147` persists the bundle as a validation-side record
- `modules/api/bridge_server.py:1021-1036` uses the signal row for calibration note generation such as `AI Slop 동반`

Interpretation:

- the signal is a post-hoc quality sidecar
- it is available for analytics, UI, and calibration summaries
- it is not inherently a retry-loop input

### F2. Stage 4 retry payload does not automatically carry `ai_slop_score` or `ai_slop_hits`

`modules/core/stage4_interview_round.py:401-424` builds feedback provenance from:

- `system_feedback`
- `evidence_summary`
- `director_feedback_text`
- `runtime_advisory`
- `retry_directives`

Later, `modules/core/stage4_interview_round.py:3534-3560` stores the retry packet into `previous_attempt` with keys such as:

- `score_breakdown`
- `validation_warnings`
- `open_review`
- `action_items`
- `contradiction_types`
- `director_feedback_text`
- `runtime_advisory`
- `retry_directives`

`modules/domain/agents/chief_writer.py:799-920` and `1551-1669` show what the Chief Writer actually consumes on retry:

- `rejection_reason`
- `score_breakdown`
- `validation_warnings`
- `fix_scope_reasoning`
- `open_review`
- `action_items`
- `selection_reason`
- retry history summaries

Repository search over `modules/domain/agents/chief_writer.py` and `modules/core/stage4_interview_round.py` found no `ai_slop`, `quality_signals`, or `signal_summary` references in the retry ingestion path.

Conclusion:

- automatic `ai_slop` telemetry is not wired into CW retry prompts
- if CW learns about style residue, it is because a human/LLM Director textualized it manually elsewhere

### F3. `0_260316` evidence shows the metric exists, but the retry loop never names it

`projects/0_260316/logs/quality_metrics.jsonl` shows:

- final PASS rows for `ep2`, `ep3`, `ep4`, `ep5`, `ep6` carry `ai_slop_hits`
- REJECT rows for `ep4` and `ep5` carry `quality_signals: {}`

Examples:

- `:14` `ep2 PASS` -> hits `어느새`, `입을 열었다`
- `:27` `ep3 PASS` -> hits `입을 열었다` x2
- `:34` `ep4 PASS` -> hit `순식간에`
- `:43` `ep5 PASS` -> hits `고개를 끄덕였다`, `입을 열었다`
- `:46` `ep6 PASS` -> hits `입을 열었다`, `한순간`
- `:30`, `:32`, `:37`, `:39`, `:41` -> Stage 4 REJECT rows with empty `quality_signals`

Meanwhile `projects/0_260316/logs/session/decisions.jsonl:15-20` shows the actual retry loop payloads carrying:

- `runtime_advisory` centered on `Flashback` and `NpcDrift`
- `retry_directives` centered on `V53.1 Dynamic Prompt Weighting`, continuity, character consistency, and blueprint alignment

There is no literal `AI 티`, `AI Slop`, or phrase-specific style remediation in those retry payloads.

This run therefore demonstrates a clear split:

- the metric existed
- the repeated phrase residue existed in shipped manuscripts
- the retry loop did not receive the metric as structured guidance

### F4. Manual Director prose is the only existing bridge, and `0_260316` did not use it for AI-slop

The system does have a valid manual bridge:

- if Director writes style criticism into `director_feedback_text`, `open_review`, `action_items`, or `rejection_reason`
- then `stage4_interview_round` preserves it
- and `chief_writer` sees it on the next retry

So the accurate statement is not:

> CW can never know style rejection reasons.

The accurate statement is:

> CW does not automatically know `ai_slop` telemetry. CW only knows style critique when Director explicitly textualizes it into the retry packet.

For `0_260316`, that explicit bridge was not used for AI-slop. The run logs show continuity- and identity-oriented retry guidance instead.

### F5. The current gap causes silent repetition across accepted episodes

The final manuscripts themselves still contain several tracked patterns:

- `ep_0002.txt:11` -> `입을 열었다`
- `ep_0003.txt:61`, `:79` -> `입을 열었다`
- `ep_0004.txt:83` -> `순식간에`
- `ep_0005.txt:65` -> `고개를 끄덕였다`
- `ep_0005.txt:89` -> `입을 열었다`
- `ep_0006.txt:3` -> `한순간`
- `ep_0006.txt:26` -> `입을 열었다`

Because the automatic signal never returns to retry prompts, the same residue can survive multiple episodes even when the system is already measuring it.

This is not a contradiction with Director sovereignty. It is simply an unclosed feedback loop.

## Improvement Direction

### Required design constraint

Any improvement must keep the workspace invariants intact:

- Python collects metrics only
- Director remains the final authority
- Chief Writer receives only Director-mediated remediation, not autonomous Python verdicts

### Recommended implementation shape

1. Add `style_signal_digest` as structured evidence, not as an automatic verdict
- Build it from `ai_slop_hits` and perhaps a bounded threshold such as `hit_count >= 2` or high density.
- Store phrase-level evidence like `입을 열었다 x2`, not only the scalar score.

2. Inject the digest into Director review first
- Director decides whether the issue is:
  - ignore
  - `PASS_WITH_FIX`
  - textual style warning only
  - hard reject for broader quality reasons

3. If Director chooses remediation, persist it into existing retry ingress
- preferred surfaces:
  - `action_items`
  - `open_review`
  - `director_feedback_text`
- do not inject raw Python judgment straight into CW without Director mediation

4. For localized phrase residue, prefer `PASS_WITH_FIX`
- example targets:
  - repeated `입을 열었다`
  - `어느새`
  - `한순간`
  - `고개를 끄덕였다`
- verification should be exact post-patch lexical confirmation, similar to the `PASS_WITH_FIX` firewall improvement already identified in `0_260316`

5. Keep analytics and retry evidence separate but linked
- DB/dashboard/API can keep full numeric telemetry
- retry loop should receive only the reduced, Director-approved style digest

## 3-Pass Audit

### Pass 1: Fact Reconciliation

- Confirmed `quality_metrics.jsonl` only exposes non-empty `quality_signals` on final PASS rows in this run.
- Confirmed Stage 4 post-processor computes and stores signals after final manuscript creation.
- Confirmed DB/dashboard/API all treat the bundle as sidecar quality telemetry.
- Confirmed the retry assembly path and CW retry consumer do not enumerate `ai_slop_*` fields.

Pass 1 result: metric generation, storage, and retry ingress are factually separated.

### Pass 2: Overclaim Guard

- Rejected overclaim: “CW can never know style feedback.”
- Accepted narrower fact: CW can know manual style criticism, but not automatic `ai_slop` telemetry.
- Rejected overclaim: “Director in `0_260316` rejected manuscripts for AI slop.”
- Accepted narrower fact: `0_260316` logs show style telemetry existed, but no literal AI-slop rejection feedback was routed to CW.

Pass 2 result: the survey distinguishes automatic telemetry absence from manual prose presence.

### Pass 3: Decision Readiness

- The document answers the operational question: no, CW does not automatically know the AI-slop metric.
- The document answers the engineering question: add a bounded Director-mediated style feedback lane, not an automatic Python reject path.
- The document is ready to merge into the project SSOT because it closes a previously open feedback-loop ambiguity without disturbing earlier recovery findings.

Pass 3 result: ready for canonical SSOT merge.

