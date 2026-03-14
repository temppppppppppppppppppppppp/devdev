# Auto Frontier-Lag N-Arc Test Harness SSOT

Created: 2026-03-14
Status: `implemented-not-executed`
Track: system-order
Blockguide policy: do not read `docs/blockguide/*`

Related documents:
- `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`
- `docs/2026-03-14/global-remediation-postfix-3pass-closure.md`

## 1. Purpose

This harness defines a future automation path for the operator intent:

- create a fresh project under `projects/`
- replay the exact Stage 0 choices already captured from the manual run
- enter menu `7. Frontier Lag`
- continue until a user-requested arc target is reached
- do not use a process timeout
- poll every 30 minutes
- run the polling watchdog inside the same terminal-owned harness session
- decide autonomously whether the run is:
  - progressing normally
  - stalled
  - failed
- terminate if needed
- analyze logs and persisted sinks
- write a canonical SSOT execution document
- re-audit that document until confidence reaches at least `95%`

This document is a specification and operating contract.
It does **not** imply that the harness is executed in this turn.

Current implementation surface:

- `scripts/run_auto_frontier_lag_harness.py`
- `tests/test_auto_frontier_lag_harness.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`

## 2. Operator Trigger Contract

The canonical operator phrase family is:

- `자동테스트 10아크런`
- `자동테스트 N아크런`
- `N아크 Frontier Lag 테스트`

Normalization rule:

- parse `N` as the requested frontier target arc count
- preserve the captured Stage 0 semantic choices unless the operator explicitly overrides them
- treat this as a new test-project run, never as an in-place mutation of an existing production project

## 3. Default Input Profile

Unless the operator overrides it, the harness replays the semantic profile captured in:

- `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`

Default semantic choices:

1. genre = `투자 (Investment Fiction)`
2. project seed profile = `00_20260314`
3. Stage 0 mode = `기존 방식 - Bible/Treatment 파일 선택`
4. Bible = `01_bi_투자물_골든_카나리아 테스트.json`
5. roadmap = `01_tr_투자물_골든_카나리아 테스트.json`
6. Treatment block auto-condense = `no`
7. protagonist config:
   - `world_origin = 원시인`
   - `incarnation_type = 회귀자`
   - `pov = 혼합`
   - `external_pov_insert_policy = 적극 허용`
8. Stage 0 style analysis:
   - run submenu `6`
   - start analysis = `yes`
   - style cache mode = `캐시 사용`

Selection resolution rule:

- replay by semantic label first
- use raw ordinals only if the displayed menu ordering still matches the captured run

## 4. Project Creation Rule

The harness must create a new project folder under `projects/`.

Recommended naming pattern:

```text
projects/auto_test_<yyyymmdd>_<hhmmss>_<base_project>_<n>arc
```

Example:

```text
projects/auto_test_20260314_193000_00_20260314_10arc
```

Creation invariants:

- never reuse an old target project silently
- never mutate the seed project in place
- persist a harness manifest inside the new project logs directory

Recommended manifest path:

```text
projects/<target>/logs/auto_frontier_lag_harness_manifest.json
```

## 5. Runtime Execution Contract

The harness owns the following sequence:

1. boot `python main_a.py`
2. replay Stage 0 semantic selections
3. return to the main menu
4. choose menu `7`
5. run `Frontier Lag`
6. stop when the requested arc target is reached

Important constraint:

- raw menu `7` behavior may auto-continue farther than the intended test scope
- therefore the automation layer must use a **thin stop boundary** so that `N아크런` actually stops at arc `N`
- this boundary must not be implemented as a shell timeout

Allowed stop-boundary strategies:

- clamp the effective frontier plan to the requested arc target
- or stop immediately after the requested designed frontier arc is completed

Disallowed strategy:

- killing the run just because a wall-clock timeout elapsed

## 6. No-Timeout Rule

The harness must not set a hard process timeout.

That means:

- no `subprocess timeout=...`
- no shell-level forced timeout
- no “2 hours and kill regardless” rule

Instead, the harness uses liveness polling plus explicit stall/failure heuristics.

## 7. Terminal-Side Watchdog Rule

The 30-minute checker is a terminal-side watchdog owned by the harness itself.

That means:

- the run process and the watchdog process live inside the same terminal-owned execution tree
- the watchdog wakes up every `30 minutes`, inspects state, then goes back to sleep
- the watchdog is **not** a timeout controller
- the watchdog may keep observing the run for many hours if progress continues

Operational interpretation:

- `30 minutes` means review cadence, not forced kill threshold
- a single quiet 30-minute window is only a liveness observation
- termination happens only after the stall/failure heuristics say it should happen

Recommended runtime split:

1. runner process
   - owns `python main_a.py` and menu replay
2. watchdog process
   - owns 30-minute polling, status judgment, and graceful stop requests
3. analyzer process
   - runs after success / stall / failure stop

## 8. 30-Minute Polling Contract

Polling interval:

- every `30 minutes`

Each poll captures:

- process alive / exited state
- current session log size delta
- latest session log tail
- blueprint count delta
- manuscript draft count delta
- `stage_attempts` Stage 3/4 row deltas
- `director_selections` row deltas
- `runtime_audit_summary.json` tag/count deltas if present

Recommended poll artifact:

```text
projects/<target>/logs/auto_frontier_lag_poll_history.jsonl
```

Polling duration rule:

- keep polling until one of `success`, `stalled`, or `failed` is reached
- do not stop polling just because the wall-clock run time became large

## 9. Progress / Stall / Failure Heuristics

### Progressing

Classify as `progressing` if at least one of the following moved since the previous poll:

- session log grew
- blueprint count increased
- draft count increased
- Stage 3 or Stage 4 attempt rows increased
- runtime summary advanced

### Stalled

Classify as `stall-candidate` if:

- process is still alive
- and **none** of the tracked progress indicators changed for one full 30-minute window

Classify as `stalled` if:

- `stall-candidate` repeats for two consecutive polls
- and no intentional blocking prompt requiring operator input is detected

Upon `stalled`:

- terminate the process gracefully if possible
- if graceful termination fails, perform controlled stop
- then proceed to log/sink analysis

### Failed

Classify as `failed` if any of the following is observed:

- process exits non-zero
- traceback or fatal exception is written to the active session log
- `crash_dump.log` is updated with the matching run
- the run enters a persistent error loop with no forward progress
- required Stage 3/4 sinks become structurally inconsistent for the current session

Upon `failed`:

- stop any still-alive child process if needed
- freeze artifacts
- proceed to root-cause analysis

### Success

Classify as `success` if:

- requested arc target was reached
- stop boundary triggered at the correct arc frontier
- Stage 3/4 current-session sinks are analyzable
- no fatal runtime failure occurred

Success does **not** imply quality PASS for every episode.
It only means the requested test harness run completed its intended scope.

## 10. Post-Run Analysis Contract

After stop, the harness must analyze:

- active session log
- `pass_rate_monitor.json`
- `runtime_audit_summary.json`
- Stage 3 `stage_attempts`
- Stage 4 `stage_attempts`
- `director_selections`
- `session/decisions.jsonl`
- drafts and blueprints produced in the run

Primary analysis questions:

1. Did the harness stop at the correct arc boundary?
2. Did the run actually progress through Stage 3 and Stage 4?
3. Was the final state a success, stall, or fail?
4. What is the nearest concrete root cause if the run stalled or failed?
5. Are sink mismatches current-session or legacy carryover?

Recommended analysis artifact names:

- `logs/auto_frontier_lag_analysis.json`
- `logs/auto_frontier_lag_failure_digest.json`

## 11. SSOT Documentation Contract

After analysis, the harness owner must produce a canonical execution document under:

```text
docs/YYYY-MM-DD/
```

Recommended canonical document pattern:

```text
docs/YYYY-MM-DD/auto-frontier-lag-<n>arc-runtime-analysis-ssot.md
```

The SSOT must include:

- run target and project locator
- exact semantic input profile used
- stop condition used
- watchdog poll cadence and terminal-side observation rule
- poll history summary
- success / stall / fail judgment
- concrete evidence files
- root-cause statement
- next action or no-action judgment

## 12. 3-Pass Audit Manual

The documentation rule is mandatory:

1. Pass 1 — fact extraction
   - verify logs, DB sinks, and artifacts say the same thing
2. Pass 2 — contradiction check
   - verify no claim in the doc exceeds the evidence
3. Pass 3 — decision audit
   - verify judgment, residuals, and next step are correctly bounded

Confidence rule:

- do not finalize the SSOT until confidence is at least `95%`
- if confidence is below `95%`, re-audit and revise

## 13. Manual Interpretation of `자동테스트 10아크런`

The phrase:

```text
자동테스트 10아크런
```

means:

1. create a fresh project under `projects/`
2. replay the preserved Stage 0 configuration choices
3. enter Frontier Lag via menu `7`
4. continue until `10 arcs` are completed
5. do not use a timeout
6. poll every `30 minutes` from the harness-owned terminal watchdog
7. stop autonomously on success / stall / failure
8. analyze logs and sinks
9. write a canonical SSOT
10. re-audit until confidence `>= 95%`

## 14. Non-Goals

This harness is not:

- a production launcher
- a replacement for full-repo regression
- a guarantee of commercial success
- a substitute for separate real-project validation

It is an automated runtime test-and-analysis harness.

## 15. Recommended Future Implementation Split

When implemented, split it into three layers:

1. `selection replay layer`
   - resolves semantic menu choices
2. `frontier execution layer`
   - runs menu `7` with arc stop boundary
3. `analysis + SSOT layer`
   - polls, stops, analyzes, and writes the dated document

Recommended future script pattern:

```text
scripts/run_auto_frontier_lag_harness.py
```

Recommended command pattern:

```powershell
python scripts/run_auto_frontier_lag_harness.py --arc-count 10 --seed-profile 00_20260314
```

## 16. Ten-Step Hardening Path

If the harness is upgraded aggressively, use this ten-step order:

1. semantic menu resolver
   - choose by label first, ordinal second
2. fresh-project creation guard
   - never mutate the seed project in place
3. Frontier Lag stop-boundary clamp
   - stop exactly at requested arc count
4. operator-prompt detector
   - distinguish intentional waiting from silent stall
5. terminal-side watchdog
   - 30-minute review cadence without timeout semantics
6. same-session sink triangulation
   - compare log, `stage_attempts`, `director_selections`, `decisions.jsonl`
7. automatic stall / failure digest
   - produce nearest concrete root-cause summary
8. canonical SSOT autowriter
   - write dated runtime-analysis document automatically
9. built-in 3-pass auditor
   - fact extraction, contradiction check, decision audit
10. confidence gate and preset aliases
   - finalize only at `>= 95%`
   - support triggers like `자동테스트 10아크런`

Recommended interpretation:

- the first usable harness is steps `1` through `7`
- the fully productized harness is steps `1` through `10`

## 17. Decision For This Turn

This turn freezes the harness design only.

Implemented in this turn:

- harness SSOT document creation
- harness runner / worker / watchdog script
- requested arc stop-boundary seam
- focused regression for helper / worker / stop-boundary contract

Not implemented in this turn:

- live run
- production confidence from an actual executed harness run
