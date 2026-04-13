# Stage3 Long-Horizon Refactor and Queue Hygiene Live-Run Watchlist

- Date: 2026-04-13
- Status: draft-live-run-pending
- Scope: bounded static watchlist for Stage3 long-horizon refactor and temp-queue hygiene while the fresh live run remains in flight on current `main`
- Mode: live-merge survey support; provisional only until the current run reaches a terminal state
- Canonical Path: `docs/2026-04-13/stage3-long-horizon-refactor-and-queue-hygiene-live-run-watchlist.md`
- Baseline Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Baseline Dirty Summary: `dirty: active live-run artifacts plus current Stage3 runtime/tests/docs patches already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at draft capture; the active run is still mutating runtime evidence under 0_temp.txt and projects/000_260412_a/logs`
- Confidence: `95% for the bounded static watchlist itself; 0% for any closure claim until the active run terminates`

## Purpose

This document captures the parallel-safe work that can be completed while the current live run is still active:

1. freeze a provisional watchlist for the long-horizon Stage3 refactor direction
2. freeze a provisional watchlist for queue-closure hygiene
3. avoid premature closure claims while the run is still generating evidence

This document is not a final survey.

This document does not create or refresh a `docs/temp/` execution mirror.

This document does not authorize mid-run runtime patching.

## Evidence Anchors

- Active operator surface:
  - [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:360)
  - [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:386)
  - [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:411)
  - [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:423)
- Latest authoritative live log file:
  - `projects/000_260412_a/logs/session_20260413_140153.log`
- Governing queue and policy docs:
  - [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:64)
  - [AGENTS.md](/c:/Users/wjjo/Desktop/글도비/AGENTS.md:184)
  - [AGENTS.md](/c:/Users/wjjo/Desktop/글도비/AGENTS.md:185)
- Current Stage3 owner surfaces:
  - [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:420)
  - [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:606)
  - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1056)
  - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1724)
  - [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2260)
  - [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:158)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2030)
  - [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2578)

## Live Snapshot

- The live run is still active. `0_temp.txt` shows `제7화` inside the Stage3 patch/re-audit cycle rather than a terminal summary surface: [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:423).
- The current visible blocker family is a binding-local timeline mismatch. The first visible failure says `PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT` with `ending_state.timeline` still drifting against the arc timeline: [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:386), [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:392).
- The run then re-enters full-ensemble generation and a new local patch cycle instead of terminating: [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:395), [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:411).
- Because the run is still active, no final closure, queue cleanup, or new execution promotion should be finalized from this snapshot alone.

## Provisional Findings

### 1. Verdict authority is still split across three owners

Static code still shows three separate stages of decision mutation:

- validator converts apparently successful compare results into repair-bearing verdicts when binding prevalidation fails: [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:420), [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py:468)
- runtime applies quality-gate, retry, fallback, and pass-with-fix loop policy: [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1056), [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:1724), [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py:2260)
- orchestrator consumes the resulting flags again for persistence and dashboard semantics: [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2030), [stage3_orchestrator.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py:2578)

Provisional implication:

- even when the system is behaving better than before, closure logic remains harder to reason about because one semantic outcome can still be rewritten as it crosses validator, runtime, and orchestration surfaces

### 2. The current `inplace` repair path is still whole-blueprint regeneration with preservation merge

The patch surface called `inplace` still serializes the entire source blueprint into the prompt, asks for a corrected JSON, and then restores missing fields via merge: [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:173), [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:207), [three_phase_blueprint_generator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py:231).

Provisional implication:

- local structural drift can survive multiple patch attempts because the system is not applying a field-targeted patch contract
- binding-local fixes such as `ending_state.timeline` remain exposed to prompt drift and re-serialization loss

### 3. The current ep7 evidence suggests a locality mismatch watchpoint, not yet a final new family

Current operator evidence shows a narrow structural issue:

- the visible failure remains a bounded `ending_state.timeline` mismatch against arc truth: [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:364), [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:367), [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:392)
- after that failure, the next visible patch reason shifts to a prose-level emotional enhancement request: [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:415), [0_temp.txt](/c:/Users/wjjo/Desktop/글도비/0_temp.txt:416)

Provisional implication:

- post-run merge should explicitly check whether authoritative repair scope and patch prompt scope drifted apart on `ep7`
- this is a watchpoint, not yet a formal promoted family, because the run has not finished

### 4. Queue semantics are overloaded and make closure look worse than it is

The active roadmap still mixes together:

- active next slices: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:66)
- proof-pending realized lanes: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:68)
- deferred verifier debt: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:73)
- historical backing items still retained in working order: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:83)

This conflicts with the stronger queue rule that treats `docs/temp/` execution mirrors as active queue artifacts that should be removed after realization: [AGENTS.md](/c:/Users/wjjo/Desktop/글도비/AGENTS.md:184), [AGENTS.md](/c:/Users/wjjo/Desktop/글도비/AGENTS.md:185).

Provisional implication:

- roadmap pressure is being inflated by status overloading and historical carry-forward, not only by truly unresolved runtime debt

## Long-Horizon Refactor Direction

These are provisional design targets, not yet promoted execution items.

Companion target-state note:

- [stage3-decision-kernel-queue-semantics-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage3-decision-kernel-queue-semantics-operating-note.md:1)

### A. Introduce a single Stage3 decision object

Candidate north star:

- `Stage3DecisionReport`
- fields split into:
  - semantic verdict
  - operational disposition
  - repair authority
  - retry action
  - quality-risk flags
  - persistence/dashboard projection

Desired effect:

- validator reports facts and issue families
- one policy kernel decides `accept`, `accept_warning`, `retry_inplace`, `retry_full`, or `fail`
- runtime executes the chosen action instead of reinterpreting the verdict multiple times

### B. Replace faux-inplace with structured patch IR

Candidate north star:

- field/path-oriented repair targets such as `ending_state.timeline`
- explicit authoritative patch scope derived from validated issue families
- merge semantics that update only the targeted surfaces

Desired effect:

- better locality for binding-only repairs
- less prompt drift and less whole-blueprint reserialization churn
- easier post-run evidence attribution when a local repair misses

### C. Split queue statuses into operationally distinct states

Candidate status families:

- `active_patch`
- `proof_pending`
- `deferred_debt`
- `historical_backing`
- `blocked`
- `closed`

Desired effect:

- stop using `partially_realized` as a catch-all
- keep `docs/temp/` aligned with genuinely active queue artifacts
- make closure visually credible again

### D. Separate active queue from historical evidence backing

Candidate direction:

- keep `docs/temp/` for active or proof-pending lanes only
- move runtime-positive historical references into canonical docs plus a lighter historical index
- stop listing historical substrate lanes inside the front working order unless they materially constrain the next decision

Desired effect:

- queue length reflects current action load instead of total memory
- operator attention cost drops

## Post-Run Merge Questions

When the current run reaches a terminal state, the merged audit should answer:

1. did `ep7` close, and if so under what final verdict path
2. did `ending_state.timeline` remain the dominant failure family or disappear after a later retry
3. did authoritative repair scope and prompt repair scope remain aligned on the final `ep7` attempts
4. does the run reopen a truly new Stage3 family, or only strengthen the case for the structured patch IR refactor
5. which current temp mirrors can be downgraded from active queue semantics into historical backing after the proof wave

## Safe Next Moves While The Run Continues

- keep watching raw evidence only; do not make final queue or closure claims
- do not patch runtime control flow mid-run
- it is safe to prepare the long-horizon refactor and queue-hygiene execution proposal after the run completes
- if the run ends in a clean terminal state, the next documentation action should be a post-run merge audit that decides whether to:
  - close the Stage3 proof slice
  - open one new long-horizon parent lane for `DecisionKernel + structured patch IR`
  - open one queue-hygiene lane to normalize `docs/temp/` semantics

## 3-Pass Audit Notes

Pass 1:

- document type is a draft live-run watchlist, not a final survey or execution SSOT
- scope is bounded to parallel-safe static analysis and queue semantics

Pass 2:

- claims are limited to inspected code, roadmap text, and active operator evidence
- no final closure or execution-promotion claim is made while the run is in flight

Pass 3:

- operating consequence is explicit: wait for terminal state, then merge this watchlist into the post-run audit
- no `docs/temp/` mirror or ClickUp reflection is authorized from this draft
