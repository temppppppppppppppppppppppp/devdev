# ROL Live-Merge Stage 4 Secondary Residual Fix Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md`
Temp Mirror Path: `removed after closure`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace with current 2026-03-23 Stage 4 fixes, live-run artifacts, and closed candidate-admission SSOT`
- Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Resume Drift Summary: `revalidated against live source after candidate-admission closure`
Source Survey Docs:
- `docs/2026-03-23/rol-live-merge-0p01-generation-failure-remediation-plan.md`
- `docs/2026-03-23/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md`
- `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md`
- `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md`
- `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/0_0323/logs/artifacts/stage4/**`
- `projects/0_0323/logs/pass_rate_monitor.json`
- `projects/0_0323/project_data.db`
Side-Effect Coverage: covered

## 1. Intent

- Realize the Stage 4 residuals that were intentionally deferred while the `0p-01` candidate-admission crash was being cut first.
- Fix the remaining high-ROI `write / fix / gate` seams before the next long rerun.
- Keep scope bounded to the exact residuals previously called out:
  - opening-anchor priority
  - post-select fix-pack carryover and retry convergence
  - downstream `CONDITIONAL_PASS` handling

Why now:

- The candidate-admission wave is closed.
- Current queue is empty, so this residual cluster can be opened as a single-item execution wave.
- These issues are not the first-order `0p-01` crash, but they are the next likely quality/efficiency drains once candidate admission is alive.

## 2. Baseline Facts

- `chief_writer_prompts.py` already contains an explicit scene-header instruction at lines 127-130.
- `opening_anchor_section` still appears after `prev_digest` and `prev_ending` in the Chief Writer prompt template.
- `stage4_interview_round.py` still builds post-select downgrade `previous_attempt` without a `fix_pack` field.
- `stage4_interview_round.py` still replays `retry_directives` as an uncapped full join of prior general lines.
- `_process_verdict()` still treats only `PASS` and `PASS_WITH_FIX` as positive verdicts.
- The just-closed candidate-admission SSOT intentionally excluded these residuals to keep the crash-cut wave narrow.

Meaning:

- This is not a DB-max-retention wave.
- This is not a broad Stage 4 redesign wave.
- This is the bounded residual fix cluster that follows the candidate-admission closure.

## 3. Scope

Included:

- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_context.py` if needed to support prompt ordering or explicit override wording
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py` if needed for bounded retry-contract compatibility
- minimal targeted tests for:
  - Chief Writer opening-anchor ordering / prompt contract
  - post-select downgrade fix-pack carryover
  - retry-directive dedup/cap behavior
  - `CONDITIONAL_PASS` downstream positive handling

Excluded:

- candidate-admission parsing hardening
- broad scene-completeness fallback redesign in `blocking_validator_scene_checks.py`
- DB schema changes
- `director_selections` post-select verdict write-back redesign
- opening-anchor packet content generation redesign
- Director scoring / threshold / adaptive policy redesign
- rerun execution itself

## 4. Pass 1. Inventory Summary

Current residual clusters: 3

1. Opening-anchor priority inversion
   - prompt contains the right anchor, but it arrives after prior-state continuity signals
2. Post-select downgrade retry degradation
   - post-select `REJECT` drops `fix_pack`
   - retry directives replay stale feedback without bound
3. `CONDITIONAL_PASS` downstream handling gap
   - positive-but-conditional verdict can still miss the positive processing path

## 5. Pass 2. Semantic Classification

- Class A: contract-ordering bug
  - opening-anchor must override prior location/time when blueprint start truth differs

- Class B: retry convergence bug
  - post-select downgrade must preserve actionable `fix_pack`
  - retry directives must stop replaying the full stale backlog

- Class C: verdict routing correctness bug
  - `CONDITIONAL_PASS` must not silently fall out of the positive verdict lane

- Deferred:
  - scene-completeness fallback redesign
  - post-select DB verdict write-back parity
  - broader Stage 4 quality-wave debt

## 6. Side-Effect Map

- file writes / artifacts:
  - no new artifact family
  - Stage 4 artifact generation behavior should remain unchanged except for better retry convergence

- DB / schema / transaction boundaries:
  - no schema change
  - no new persistence table

- JSONL / log / audit sinks:
  - retry feedback text may become shorter and more current
  - do not add new truncation

- console / operator output:
  - provisional PASS / downgrade flow remains visible
  - fix-pack and retry reasons should become more actionable, not more verbose for its own sake

- retry / recovery:
  - primary impact area
  - this wave should reduce stale feedback replay and missing-patch-target loops

## 7. Execution Tranches

1. Opening-anchor priority tranche
- Targets:
  - `modules/domain/agents/chief_writer_prompts.py`
  - `modules/domain/agents/chief_writer_context.py` only if needed
- Goal:
  - when blueprint start truth conflicts with prior episode terminal state, the opening-anchor contract must arrive early and explicitly override the inherited state
- Required behavior:
  - `opening_anchor_section` is promoted ahead of `prev_digest` / `prev_ending`
  - prompt wording explicitly states blueprint start truth wins for the next opening
- Constraint:
  - do not redesign the anchor packet payload itself

2. Post-select fix-pack carryover tranche
- Target:
  - `modules/core/stage4_interview_round.py`
- Goal:
  - a provisional PASS downgraded by post-select checks must preserve normalized `fix_pack` into `previous_attempt`
- Required behavior:
  - downgrade-built `previous_attempt` carries `fix_pack`
  - the next retry lane sees actionable `patch_targets` when Director already emitted them
- Constraint:
  - do not redesign the whole retry architecture

3. Retry-directive sharpening tranche
- Targets:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_retry_runtime.py` only if needed for compatibility
- Goal:
  - retry directives stop replaying the full stale backlog
- Required behavior:
  - deduplicate repeated general lines
  - keep only a bounded latest subset
  - preserve current-round actionable instruction quality
- Constraint:
  - do not truncate operator evidence arbitrarily; sharpen structure rather than blind cut

4. `CONDITIONAL_PASS` downstream tranche
- Targets:
  - `modules/core/stage4_interview_round.py`
  - `modules/domain/agents/director_ensemble.py` only if a bounded normalization is cleaner there
- Goal:
  - `CONDITIONAL_PASS` reaches the positive handling path instead of silently behaving like reject
- Required behavior:
  - either downstream accepts `CONDITIONAL_PASS` as positive
  - or upstream fully resolves it before the interview-round branch point
- Constraint:
  - keep Director authority and adaptive policy semantics intact

## 8. Acceptance Criteria

- Chief Writer prompt order makes the opening-anchor contract operationally prior to stale previous-state continuity text.
- Post-select downgrade no longer strips `fix_pack` from `previous_attempt`.
- Retry directives are bounded and de-duplicated rather than monotonic full-history replay.
- `CONDITIONAL_PASS` no longer misses the positive verdict path.
- No DB schema change, no prompt-wave sprawl, no retry-policy redesign.

## 9. Required Verification

- `python -m py_compile modules/domain/agents/chief_writer_prompts.py modules/domain/agents/chief_writer_context.py modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py modules/domain/agents/director_ensemble.py`
- `python -m pytest tests/test_chief_writer_context.py -q`
- `python -m pytest tests/test_stage4_interview_round.py -q`
- `python -m pytest tests/test_director_modules.py -q`
- targeted low-memory shard for any new retry/fix-pack carryover tests added in touched files
- `python scripts/check_utf8_hygiene.py modules/domain/agents/chief_writer_prompts.py modules/domain/agents/chief_writer_context.py modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py modules/domain/agents/director_ensemble.py docs/2026-03-23/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md docs/temp/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 10. Closure Criteria

- all included tranches are implemented or explicitly shown already realized in live code
- targeted tests are green
- no UTF-8 hygiene failure
- temp queue reflects this as a single active item
- Codex verifies no hidden scope widening occurred
- SSOT closes only after audit; Opus must not close it

Closure Note:

- `opening_anchor_section` now precedes stale prior-state continuity text and explicitly overrides it when blueprint start truth differs.
- post-select downgrade `previous_attempt` now preserves normalized `fix_pack` and `action_items`.
- retry directives now deduplicate repeated lines and keep only the latest bounded slice.
- `_process_verdict()` now normalizes `CONDITIONAL_PASS` into the positive path even if an upstream edge case leaves it unresolved.
- Targeted regression coverage now locks:
  - prompt ordering / anchor override wording
  - post-select fix-pack carryover
  - retry-directive dedup + latest-20 cap
  - `CONDITIONAL_PASS` positive routing

## 11. Out-of-Scope Risks To Revisit After This Wave

- scene-completeness fallback redesign for headerless prose
- post-select downgrade DB write-back parity
- broader Stage 4 quality-wave redesign
- long-run Q5/Q7 stress behavior after the next rerun

## 12. Opus Order Prompt

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/temp/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md
4. docs/2026-03-23/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md
5. docs/2026-03-23/rol-live-merge-0p01-generation-failure-remediation-plan.md
6. docs/2026-03-23/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md
7. docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md
8. docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md
9. docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md
10. docs/2026-03-23/console.txt

Task:
Implement the bounded Stage 4 secondary residual fixes defined in docs/temp/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md.

Primary goal:
Finish the residual Stage 4 `write / fix / gate` seams that were intentionally deferred while the 0p-01 candidate-admission crash was fixed first.

Hard constraints:
- Follow the execution SSOT exactly.
- Do not widen scope.
- Do not reopen the closed candidate-admission wave.
- Do not reopen broad DB/console retention waves.
- Do not redesign Stage 4 architecture.
- Do not change Director scoring policy, thresholds, or authority ownership.
- Do not execute a rerun.
- If an included item is already fixed in live code, shrink scope and continue.
- Do not close the execution SSOT after implementation; Codex will audit and close it.

Execution scope:
1. Opening-anchor priority promotion
- chief_writer_prompts.py
- chief_writer_context.py only if needed

2. Post-select fix-pack carryover
- stage4_interview_round.py

3. Retry-directive sharpening
- stage4_interview_round.py
- stage4_retry_runtime.py only if needed

4. CONDITIONAL_PASS downstream handling
- stage4_interview_round.py
- director_ensemble.py only if needed

Out of scope:
- candidate payload normalization
- broad scene-completeness fallback redesign
- DB schema changes
- post-select DB write-back redesign
- rerun execution

Implementation rules:
- Use apply_patch for edits.
- Keep changes bounded and contract-oriented.
- Preserve current evidence retention and console max-display policies.
- If a design fork appears, stop and report it instead of improvising a larger wave.

Required verification:
- python -m py_compile modules/domain/agents/chief_writer_prompts.py modules/domain/agents/chief_writer_context.py modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py modules/domain/agents/director_ensemble.py
- python -m pytest tests/test_chief_writer_context.py -q
- python -m pytest tests/test_stage4_interview_round.py -q
- python -m pytest tests/test_director_modules.py -q
- python scripts/check_utf8_hygiene.py modules/domain/agents/chief_writer_prompts.py modules/domain/agents/chief_writer_context.py modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py modules/domain/agents/director_ensemble.py docs/2026-03-23/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md docs/temp/rol-live-merge-stage4-secondary-residual-fix-execution-ssot.md
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize exactly what changed by tranche
- list verification results
- list any skipped or already-resolved item
- do not close the execution SSOT; Codex will handle closure
```
