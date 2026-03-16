<!-- [완료] -->
# Auto Frontier-Lag N-Arc Test Harness SSOT

Created: 2026-03-14
Last Re-Audited: 2026-03-14
Status: `implemented-heavy-design-not-executed`
Track: system-order
Blockguide policy: do not read `docs/blockguide/*`

Related documents:
- `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`
- `docs/2026-03-14/global-remediation-postfix-3pass-closure.md`
- `docs/2026-03-13/stage4-canary-archive-locator-note.md`

Implementation surface:
- `scripts/run_auto_frontier_lag_harness.py`
- `main_a.py`
- `tests/test_auto_frontier_lag_harness.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`

## 1. Purpose

This harness defines the operator automation path for intents such as:

- `자동테스트 10아크런`
- `자동테스트 N 아크런`
- `N아크 Frontier Lag 테스트`

The harness is responsible for:

1. creating a fresh project under `projects/`
2. replaying the captured Stage 0 semantic selections
3. entering `7. Frontier Lag`
4. continuing until the requested arc count is reached
5. avoiding hard process timeouts
6. polling every 30 minutes from the same terminal-owned execution tree
7. deciding whether the run is progressing, stalled, failed, or complete
8. stopping gracefully when required
9. analyzing DB/log/artifact sinks
10. writing a canonical runtime analysis SSOT with an internal 3-pass audit

This document is an operating contract.
It does not imply that the harness is executed in this turn.

## 2. Runtime Model

The heavy-design runtime model is:

- parent process:
  - `scripts/run_auto_frontier_lag_harness.py run ...`
  - owns the 30-minute watchdog
  - writes poll history
  - performs sink analysis
  - writes the execution SSOT
- worker process:
  - `scripts/run_auto_frontier_lag_harness.py worker ...`
  - boots `SovereignApp` inside its own Python subprocess
  - replays Stage 0 selections through controlled seams
  - runs `_one_stop_pipeline_frontier_lag(...)`

Important:

- the worker is a subprocess, but it does not rely on brittle raw terminal scraping for the full flow
- instead it boots `SovereignApp` directly and uses thin runtime seams
- the watchdog still belongs to the same terminal-owned execution tree

## 3. Operator Trigger Contract

Canonical trigger family:

- `자동테스트 10아크런`
- `자동테스트 20 아크런`
- `15아크 Frontier Lag 테스트`

Normalization rule:

- parse `N` as the requested arc target
- preserve the captured Stage 0 semantic profile unless the operator overrides it
- always create a new test project
- never mutate the seed project in place

## 4. Default Input Profile

Unless overridden, the harness replays the semantic profile captured in:

- `docs/2026-03-14/main-a-manual-stage0-selection-harness-00_20260314.md`

Default semantic choices:

1. genre = `투자 (Investment Fiction)`
2. seed profile = `00_20260314`
3. Stage 0 mode = `기존 방식 - Bible/Treatment 파일 선택`
4. Bible = `01_bi_투자물_골든_카나리아 테스트.json`
5. roadmap = `01_tr_투자물_골든_카나리아 테스트.json`
6. Treatment block auto-condense = `n`
7. protagonist config:
   - `world_origin = 원시인`
   - `incarnation_type = 회귀자`
   - `pov = 혼합`
   - `external_pov_insert_policy = 적극 허용`
8. style analysis:
   - submenu `6`
   - confirm = `y`
   - cache mode = `use`

Replay rule:

- resolve by semantic value first
- only fall back to raw ordinal assumptions where the runtime seam explicitly guarantees it

## 5. Project Creation Rule

The harness must create a new target project.

Recommended naming pattern:

```text
projects/auto_test_<yyyymmdd>_<hhmmss>_<seed_profile>_<n>arc
```

Example:

```text
projects/auto_test_20260314_193000_00_20260314_10arc
```

Invariants:

- fail if the target project already exists
- do not silently reuse an old target project
- write a manifest to:

```text
projects/<target>/logs/auto_frontier_lag_harness_manifest.json
```

## 6. Frontier Lag Stop-Boundary

The heavy design uses an internal stop boundary rather than a wall-clock kill.

Current implementation seam:

- `SovereignApp._one_stop_pipeline_frontier_lag(max_arc_advances=..., batch_size_override=..., wait_for_menu_return=False)`

Required semantics:

- `max_arc_advances = N` means stop after exactly `N` advanced arcs
- `batch_size_override` is allowed for bounded test runs
- `wait_for_menu_return=False` avoids interactive menu blocking at worker end

Disallowed strategy:

- stopping only because a shell timeout elapsed

## 7. No-Timeout Rule

The harness must not use:

- `subprocess.run(..., timeout=...)`
- shell-level forced timeout wrappers
- fixed “kill after X hours” logic

Instead:

- the watchdog polls every 30 minutes
- the parent process checks worker liveness on a shorter internal cadence
- completion may happen much earlier than the 30-minute review window

## 8. Watchdog Contract

The watchdog is terminal-owned and runs inside the parent harness process.

Polling model:

- review cadence: every `30 minutes`
- responsive process check: every `5 seconds`
- if the worker exits early, the parent should notice promptly and must not sleep for the remaining 30-minute window

Each poll captures:

- process alive / exit code
- current session log path
- session log size delta
- session log tail
- blueprint count
- draft count
- Stage 3 attempt count
- Stage 4 attempt count
- Stage 3 / Stage 4 director selection counts
- runtime audit summary event count
- harness phase from manifest
- prompt-blocked signal

Poll history artifact:

```text
projects/<target>/logs/auto_frontier_lag_poll_history.jsonl
```

## 9. Progress / Stall / Failure Heuristics

### Progressing

Classify as `progressing` if any of these changed since the previous poll:

- session log size
- blueprint count
- draft count
- Stage 3 attempt count
- Stage 4 attempt count
- Stage 3 director-selection count
- Stage 4 director-selection count
- runtime audit total events
- manifest phase

### Waiting Prompt

Classify as `waiting_prompt` if:

- no progress moved
- but the latest session-log tail shows a known input wait marker

### Stalled

Classify as `stall-candidate` if:

- the worker is still alive
- and no progress signals moved for one full 30-minute window
- and no prompt-blocked marker is present

Classify as `stalled` if the same condition repeats for two consecutive poll windows.

### Failed

Classify as `failed` if:

- the worker exits non-zero
- traceback markers appear
- `crash_dump.log` evidence appears in the active log tail
- or sink alignment later proves structurally broken for the current session

## 10. Graceful Stop Contract

Primary stop intent:

- send `CTRL_BREAK` / `Ctrl+C` style interrupt to the worker process group first

Fallback order:

1. graceful interrupt
2. terminate
3. kill

Rationale:

- give the runtime a chance to flush logs and exit cleanly
- do not rely on hard kill first

## 11. Analysis Contract

After worker completion or forced stop, the parent analyzer must:

1. read worker result JSON
2. read harness manifest
3. read `runtime_audit_summary.json`
4. read `pass_rate_monitor.json` if present
5. inspect `stage_attempts` and `director_selections`
6. run `FailureAnalyzer.sink_alignment_summary()` for:
   - Stage 3 current session
   - Stage 4 current session
7. derive:
   - `boundary_reached`
   - `root_cause`
   - `judgment`
   - `shared_session_id`

Analysis artifacts:

- `logs/auto_frontier_lag_worker_result.json`
- `logs/auto_frontier_lag_analysis.json`
- `logs/auto_frontier_lag_failure_digest.json` when needed

## 12. SSOT Output Contract

For every analyzed run, write:

```text
docs/YYYY-MM-DD/auto-frontier-lag-<n>arc-runtime-analysis-ssot.md
```

The generated SSOT must include:

- input profile reference
- worker model
- watchdog cadence
- no-timeout statement
- graceful stop path
- poll history path
- Stage 3 current-session sink status
- Stage 4 current-session sink status
- 3-pass audit result
- confidence score

## 13. Internal 3-Pass Audit

The harness’ internal runtime-analysis doc uses a compact 3-pass audit:

1. pass 1: fact extraction
2. pass 2: contradiction check
3. pass 3: decision audit

Confidence rule:

- ordinary pass count raises confidence
- only a clean success can finalize at `95%`
- a degraded or failed run must not claim final confidence `95%`

## 14. Current Re-Audit Findings

2026-03-14 heavy-design re-audit findings:

1. fixed: Korean trigger and prompt marker literals must remain canonical UTF-8 text
2. fixed: Stage 0 protagonist replay should resolve by semantic menu value, not hard-coded raw ordinals
3. fixed: the watchdog must not block for the full 30-minute interval after a quick worker exit
4. fixed: graceful stop should attempt `CTRL_BREAK` / `Ctrl+C` semantics before terminate/kill
5. fixed: runtime analysis SSOT should describe the real worker model, not imply raw TTY replay only

Residual notes:

- execution has not been performed in this turn
- actual runtime proof still depends on a future live run

## 15. Out of Scope

This harness does not currently promise:

- packaged desktop orchestration
- full repo regression gating
- narrative pipeline automation
- productized UI controls for harness management
