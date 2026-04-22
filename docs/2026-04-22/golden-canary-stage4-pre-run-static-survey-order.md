# Golden Canary Stage4 Pre-Run Static Survey Order

Date: 2026-04-22
Status: ready-to-dispatch
Track: system-track
Mode: pre-run static survey watchlist
Confidence: 0.97

## Purpose

- Produce a bounded `pre-run static survey` before the next real-project `Stage 4 supervised` run.
- The goal is to shorten blocker triage if the run stalls again.
- This is a `watchlist-producing order`, not a final blame or closure document.

## Target Run

- Project: `projects/골든 카나리아`
- Lane: `Stage 4 supervised`
- Planned target: `target_ep=5`
- Current known stop frontier:
  - `Stage 3` blueprints through `ep16`
  - `Stage 4` manuscripts through `ep3`
  - `Stage 4 ep4` rejected multiple times
  - `Stage 4 ep5` not started

## Operator Intent

- We are going to resume a real `Stage 4 supervised` run soon.
- Before that run, we want a static survey that identifies likely blocker surfaces, sink checkpoints, and fast triage questions.
- If the run blocks again, the post-failure investigation should merge:
  - this pre-run static watchlist
  - fresh live evidence from DB/log/artifacts
  - post-run or post-stop merge audit

Authority rule:

- `live evidence > pre-run static survey > stale survey text > assumption`

## Must-Read Inputs

Read these first:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/2026-04-22/stage4-supervised-run-interruption-context.md`

Then inspect the most relevant runtime/code surfaces:

- `scripts/run_stage4_direct_supervised.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/numeric_consistency_checker.py`
- `modules/core/failure_analyzer.py`

Inspect current project evidence surfaces as static inputs only:

- `projects/골든 카나리아/logs/runtime_audit_summary.json`
- `projects/골든 카나리아/logs/runtime_audit.jsonl`
- `projects/골든 카나리아/logs/pass_rate_monitor.json`
- `projects/골든 카나리아/logs/episode_production.jsonl`
- `projects/골든 카나리아/logs/quality_metrics.jsonl`

## Hard Constraints

- Do not modify production code.
- Do not run `Stage 4`.
- Do not start a supervised run yourself.
- Do not write execution SSOT docs or temp queue mirrors unless the user explicitly asks for that.
- Do not present hypotheses as final conclusions.
- If you find uncertainty, label it explicitly as `hypothesis` or `needs live confirmation`.

## Known Context To Respect

- A real code-side bug was already found in `numeric_consistency_checker.py` around `won/krw` unit handling.
- That patch is justified at code level, but the live `Stage 4` lane was not yet fully revalidated after the patch.
- The latest dominant persisted blocker appears to be `timeline replay / completed-event repetition` in `ep4`, not merely a tiny local wording problem.
- Your survey must not collapse everything into `regex` or `numeric parser` blame unless the evidence truly supports that.

## What To Produce

Create one human-facing document:

- `docs/2026-04-22/golden-canary-stage4-pre-run-static-watchlist.md`

The watchlist document must contain:

1. Scope
2. Current known frontier and prior interruption summary
3. Top risk watchlist
4. Code hotspot map
5. Authoritative sink map
6. Live confirmation checklist
7. Operator fast-triage checklist after the next stop/fail
8. Confidence and known unknowns

## Required Content Rules

### 1. Scope

- State clearly that this is `pre-run static watchlist`, not final conclusion.
- State the exact run target: `projects/골든 카나리아`, `Stage 4 supervised`, `target_ep=5`.

### 2. Top Risk Watchlist

Keep this bounded and prioritized. Focus on likely failure families such as:

- `ep4` timeline replay / already-completed event restaging
- frontier carryover between `ep3 -> ep4`
- `continuity_firewall` / `director_quality` rejection path
- numeric carryover warning path after the `won/krw` patch
- retry / patch / fix-scope widening paths that can hide the true blocker
- sink misalignment between persisted truth and operator-visible summaries

### 3. Code Hotspot Map

For each hotspot, say:

- why it matters
- what kind of failure it could cause
- what live evidence would confirm or falsify it

### 4. Authoritative Sink Map

Explicitly map where the next blocker should be checked first. Include at minimum:

- DB persisted attempt truth
- `pass_rate_monitor`
- `episode_production`
- `runtime_audit`
- session decision logs
- relevant artifact files under `logs/artifacts`

Make it explicit which sinks are authoritative and which are only operator summaries or companion signals.

### 5. Live Confirmation Checklist

For each top hypothesis, say exactly what to inspect when the next run stops:

- which file or DB surface
- which field or evidence shape
- what outcome would count as confirmation
- what outcome would count as disproof

### 6. Operator Fast-Triage Checklist

Give a short checklist the operator can follow within the first few minutes after a stop or failure.

This should answer:

- what to open first
- what not to over-trust
- how to separate timeline replay from numeric warning noise

## Output Style

- concise, operational, and evidence-bounded
- no fluff
- findings/watch-items first
- no nested speculation trees
- if a section is not applicable, say `not applicable`

## Non-Goals

- no code patching
- no benchmark archive work
- no queue realization
- no final execution plan unless the user later asks for one

## Dispatch Format

When you finish, return:

1. the path to the watchlist doc
2. a short summary of the top 3-5 watch items
3. any single biggest `live-confirmation-first` uncertainty

## Copy-Paste Order

Use the text below as the direct task order if needed:

```text
System-track order.

Produce a bounded pre-run static survey watchlist for the next real-project Stage 4 supervised run on `projects/골든 카나리아` toward `target_ep=5`.

This is watchlist production only, not code modification and not final conclusion.

Must read:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/live-run-merge-survey-harness.md
- docs/2026-04-22/stage4-supervised-run-interruption-context.md

Then inspect:
- scripts/run_stage4_direct_supervised.py
- modules/core/stage4_orchestrator.py
- modules/core/stage4_interview_round.py
- modules/core/stage4_director_runtime.py
- modules/core/stage4_post_processor.py
- modules/core/stage4_post_pass_runtime.py
- modules/core/numeric_consistency_checker.py
- modules/core/failure_analyzer.py
- projects/골든 카나리아/logs/runtime_audit_summary.json
- projects/골든 카나리아/logs/runtime_audit.jsonl
- projects/골든 카나리아/logs/pass_rate_monitor.json
- projects/골든 카나리아/logs/episode_production.jsonl
- projects/골든 카나리아/logs/quality_metrics.jsonl

Hard rules:
- do not modify production code
- do not run Stage 4
- do not create execution SSOT or docs/temp mirrors
- do not present hypotheses as final conclusions
- live evidence later must outrank this survey

Create:
- docs/2026-04-22/golden-canary-stage4-pre-run-static-watchlist.md

Required sections:
1. Scope
2. Current known frontier and prior interruption summary
3. Top risk watchlist
4. Code hotspot map
5. Authoritative sink map
6. Live confirmation checklist
7. Operator fast-triage checklist after the next stop/fail
8. Confidence and known unknowns

Known context to respect:
- won/krw numeric patch was a real code-side fix, but live Stage 4 revalidation is still incomplete
- the latest dominant blocker appears to be ep4 timeline replay / completed-event repetition
- do not collapse everything into regex/numeric blame unless the evidence truly supports that

Return:
1. the path to the watchlist doc
2. the top 3-5 watch items
3. the single biggest live-confirmation-first uncertainty
```
