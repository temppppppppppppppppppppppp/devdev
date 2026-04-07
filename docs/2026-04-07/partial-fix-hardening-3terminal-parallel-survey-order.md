# Partial-Fix Hardening 3-Terminal Parallel Survey Order

Date: 2026-04-07
Status: final
Document Type: operator parallel order
Canonical Path: `docs/2026-04-07/partial-fix-hardening-3terminal-parallel-survey-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Track: system
Mode: read-only parallel survey; no code patching; docs-only outputs
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread docs, narrative artifacts, and runtime/output deltas are already present; this order is survey-only and must not mutate queue controllers or code`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Purpose

This order splits one bounded partial-fix survey into three non-overlapping
terminal lanes:

- `partial-fix eval harness`
- `shared patch address schema`
- `operator-facing before/after trace`

This wave is not asking for implementation.
This wave is asking a narrower set of questions:

- whether these three improvement ideas are already covered by the existing
  queued Stage2/3/4 partial-fix hardening stack
- which parts are stage-local versus truly cross-stage
- which owner files already contain the best substrate
- whether anything still deserves a new execution lane after merge

## 2. Queue Context

Active temp queue context exists already.
This order does not replace the current queue controller and must not mutate it.

Context only:

- canonical roadmap:
  - `docs/2026-04-01/active-temp-execution-roadmap.md`
- temp mirror queue controller:
  - `docs/temp/execution-roadmap.md`
- queue snapshot:
  - `docs/temp/queue-state.json`

Current queue reading relevant to this survey:

- queue ranks `9-11` already contain stage-local partial-fix hardening waves:
  - `0_0-stage4-partial-fix-hardening-remediation`
  - `0_0-stage3-partial-fix-hardening-remediation`
  - `0_0-stage2-partial-fix-hardening-remediation`
- the queue does not currently contain a dedicated `partial-fix eval harness`
  item
- the queue does not currently contain a dedicated `operator-facing before/after
  trace` item
- shared patch-address normalization exists in the queued Stage2/3/4 partial-fix
  stack, but only as stage-local future waves, not yet as one cross-stage schema
  authority

This survey therefore stays read-only and produces evidence only.
Queue mutation, if any, happens only after the three lane docs are merged and
audited centrally.

## 3. Fixed Read Before Starting

Every terminal reads these first:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/commit-state-minimal-contract.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
- `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage2-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`

Read these as stage-local context when needed:

- `docs/2026-04-07/stage4-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage3-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage2-data-shape-pwf-bounded-survey.md`

## 4. Global Guardrails

1. Stay read-only.
2. Do not patch code in this wave.
3. Do not mutate `docs/temp/`.
4. Do not rewrite or reprioritize the active queue in this wave.
5. Do not create or refresh an execution SSOT in this wave.
6. Do not claim implementation readiness from survey evidence alone.
7. Use live code and canonical docs first; temp mirrors are queue context only.
8. Findings are the primary content.
   A short `Coverage` header may precede them, but no overview may outrank the
   findings.
9. Cite exact file paths for owner claims.
10. Each lane writes exactly one output document under `docs/2026-04-07/`.
11. Each lane must classify debt into:
    - `already-covered-by-existing-queue`
    - `extend-rank9-11-stage-local-wave`
    - `candidate-new-cross-stage-lane`
12. The three lane docs are survey outputs only.
    No terminal may create queue artifacts or temp mirrors in this wave.

## 5. Global Questions

Across all three lanes, answer these without duplicating each other:

1. What is the narrowest real operator or runtime weakness?
2. Which owner files already have usable substrate?
3. Is the missing piece stage-local, shared-contract, or observability-only?
4. Is the missing piece already implicitly covered by queue ranks `9-11`, or is
   there still a cleanly missing execution home?
5. What is the minimum contract addition that would let later implementation stay
   bounded?

## 6. Terminal Ownership

### Terminal 1

- owner: `partial-fix eval harness / measurement surfaces`
- mission:
  - inspect where Stage2/3/4 already emit enough data to measure partial-fix
    quality
  - determine the narrowest additional telemetry needed for:
    - `local hit rate`
    - `fallback to partial/full`
    - `same-target retry count`
    - `do_not_regress violation rate`
  - decide whether this is a missing execution lane or can stay folded into
    existing queued items
- output:
  - `docs/2026-04-07/partial-fix-terminal1-eval-harness-survey.md`

### Terminal 2

- owner: `shared patch address schema / cross-stage target contract`
- mission:
  - inspect how Stage2/3/4 currently express patch targets:
    - `section/field`
    - `scene/path`
    - `patch_targets`
  - determine the smallest shared key set that would prevent `fix_pack-lite`
    dialect drift
  - decide whether one cross-stage schema authority is missing or whether the
    queued stage-local waves are sufficient
- output:
  - `docs/2026-04-07/partial-fix-terminal2-shared-patch-address-schema-survey.md`

### Terminal 3

- owner: `operator-facing before/after trace / snapshot-dashboard surfaces`
- mission:
  - inspect what current operator surfaces already show before/after or repair
    trace information
  - determine the narrowest bounded trace contract for:
    - `target`
    - `old_excerpt`
    - `new_excerpt`
    - `why_changed`
    - `guard_result`
  - decide whether this is only a display-extension inside existing Stage4/Stage2
    lanes or a missing operator-observability lane
- output:
  - `docs/2026-04-07/partial-fix-terminal3-operator-before-after-trace-survey.md`

## 7. Shared Output Contract

Each terminal uses the same section shape:

1. `Coverage`
2. `Findings`
3. `Existing Coverage Check`
4. `Minimal Contract Proposal`
5. `Owner Verdict`
6. `Promotion Signal`
7. `Stop`

Section rules:

- `Coverage`:
  - what was read
  - what was intentionally excluded
- `Findings`:
  - ordered by severity
  - exact file paths required
- `Existing Coverage Check`:
  - what is already covered by ranks `9-11`
  - what is only implied, not explicit
  - what is still missing
- `Minimal Contract Proposal`:
  - the smallest bounded schema, sink, or trace addition that later execution
    should realize
- `Owner Verdict`:
  - narrowest plausible owner set
- `Promotion Signal`:
  - one of:
    - `covered-by-existing-queue`
    - `extend-rank9-11-stage-local-wave`
    - `candidate-new-cross-stage-lane`
- `Stop`:
  - no extra planning prose after the required stop line

Required stop line:

- `read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output`

## 8. Lane-Specific Questions

### Terminal 1 Questions

1. Which existing runtime or persistence surfaces already know whether a local
   fix succeeded versus escalated:
   `PASS_WITH_FIX`, repair summaries, canary snapshots, DB sinks, stage attempts,
   or dashboard/readback helpers?
2. Where can the four desired metrics be computed without violating the workspace
   rule that Python collects facts but does not make editorial judgments?
3. Which owner files already carry enough identifiers to measure
   `same-target retry count` rather than generic retry count?
4. Is the missing piece primarily:
   - instrumentation
   - sink persistence
   - post-run aggregation
   - operator presentation
5. Should this remain folded into Stage2/3/4 partial-fix waves, or is a small
   cross-stage eval harness lane still missing?

### Terminal 2 Questions

1. What is the current strongest target-address contract in each stage:
   - Stage2
   - Stage3
   - Stage4
2. Which address fields are common enough to normalize now without forcing a
   broad redesign?
3. What is the minimum shared key set:
   - `stage`
   - `target_kind`
   - `container_kind`
   - `container_id`
   - `field_path`
   - `anchor_before`
   - `anchor_after`
   - `old_text`
   - `new_text`
   or a tighter subset?
4. Which fields must stay stage-specific rather than pretending to be universal?
5. Is a cross-stage schema document or execution lane truly missing, or can the
   queued stage-local waves absorb the normalization safely?

### Terminal 3 Questions

1. Which current operator surfaces already expose repair metadata:
   logs, readback summaries, DB rows, canary helpers, bridge responses, or
   dashboard payloads?
2. Where would `target / old_excerpt / new_excerpt / why_changed / guard_result`
   fit with the smallest bounded footprint?
3. What excerpt-size or storage constraints matter under the workspace policy
   that diagnostic `TEXT` fields should not be arbitrarily truncated?
4. Which owner files would need to cooperate:
   producer/runtime, DB/persistence, server/readback, or operator display
   surfaces?
5. Is the missing trace mainly a Stage4-local quality-of-life extension, or does
   it deserve a separate operator-observability lane?

## 9. Read Lists Per Terminal

### Terminal 1 Read List

- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/db/db_manager.py`
- `bridge_server.py`
- `stage4_canary_tools.py`
- any nearby readback/snapshot helper the terminal discovers while staying within
  this lane

### Terminal 2 Read List

- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_inplace_local_ops.py`

### Terminal 3 Read List

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_inplace_local_ops.py`
- `modules/db/db_manager.py`
- `bridge_server.py`
- `stage4_canary_tools.py`
- any operator-facing serialization/helper surface that clearly feeds snapshot or
  dashboard payloads

## 10. Merge Instructions

After the three terminal docs are complete, produce one merged survey:

- `docs/2026-04-07/partial-fix-hardening-parallel-merge-survey.md`

The merge doc must:

1. deduplicate overlapping findings
2. classify each of the three themes as:
   - `already-covered`
   - `stage-local-extension-needed`
   - `new-cross-stage-lane-needed`
3. state whether queue ranks `9-11` are sufficient as written or need later
   execution-doc expansion
4. identify the narrowest owner set per theme
5. stop at survey conclusions only

The merge doc must not:

- mutate the queue
- create temp mirrors
- promote an execution SSOT directly
- claim implementation closure

## 11. Stop Condition

This operator order is complete when:

- the three lane survey docs exist
- the merged survey doc exists
- all four docs remain read-only outputs under `docs/2026-04-07/`
- no queue controller or code file was changed during the Opus survey wave
