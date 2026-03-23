# ROL Live-Merge 0p-01 Generation Failure Fix Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md`
Temp Mirror Path: `removed after closure`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace with current 2026-03-23 source/test/doc edits, live-run artifacts under projects/0p-01/, and no active temp execution mirror before this SSOT`
- Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Resume Drift Summary: `revalidated against current 0p-01 live evidence before save`
Source Survey Docs:
- `docs/2026-03-23/rol-live-merge-0p01-generation-failure-remediation-plan.md`
- `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md`
- `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md`
- `docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/0p-01/logs/session_20260323_205346.log`
- `projects/0p-01/logs/session/llm_io.jsonl`
- `projects/0p-01/logs/session/ui_events.jsonl`
- `projects/0p-01/logs/session/decisions.jsonl`
- `projects/0p-01/logs/episode_production.jsonl`
- `projects/0p-01/project_data.db`
Side-Effect Coverage: covered

## 1. Intent

- Realize the smallest high-ROI fix cluster that explains the current `0p-01` fresh-run failure.
- Recover Stage 4 candidate admission before reopening broader Stage 4 quality debt.
- Preserve Director sovereignty, DB max-retention, and console max-display policy.

Why now:

- Current live failure occurs before Director review and before Stage 4 artifact persistence.
- Existing ROL lane reports contain useful structural debt, but their Stage 4 quality priorities are not the first blocker for `0p-01`.
- The current rerun should not proceed farther until `ChiefWriter` candidate payload handling is hardened.

## 2. Baseline Facts

- Stage 2 and Stage 3 completed successfully in `projects/0p-01/project_data.db`.
- Current Stage 4 truth is a single `stage_attempts` row:
  - `stage=4`
  - `ep_num=1`
  - `attempt_num=1`
  - `verdict=EMPTY`
  - `score=0`
  - `reject_reason=empty_candidates`
- `director_selections` contains no Stage 4 row for this run.
- `attempt_raw_rationale` contains no row for this run.
- `logs/artifacts/stage4/` contains no Stage 4 artifact for this run.
- `session_20260323_205346.log` shows repeated:
  - `ChiefWriter _generate_single_candidate 크래시: 'list' object has no attribute 'get'`
  - `모든 후보 생성 실패`
  - `candidates 빈 배열`
- `chief_writer.py` still assumes a dict-shaped single-candidate payload in `_generate_single_candidate()`.
- `chief_writer_quality.py` still assumes a dict-shaped JSON payload in `_self_critique()` and calls `data.get("content", "")` after `json.loads(...)`.

Meaning:

- This is not primarily a Stage 4 retry/fix-pack quality problem.
- This is first a candidate-payload contract and parser-hardening problem.

## 3. Scope

Included:

- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_quality.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_interview_round.py`
- minimal targeted tests for:
  - ChiefWriter single-candidate parsing
  - ChiefWriterQuality self-critique parsing
  - Stage 4 empty-candidates classification / observability where touched

Excluded:

- broad Stage 4 quality-wave redesign
- opening-anchor ordering cleanup
- scene-locked writer contract redesign
- `CONDITIONAL_PASS` downstream handling
- post-select downgrade / fix-pack architecture
- DB schema migration
- new retention tables
- rerun execution itself

## 4. Pass 1. Inventory Summary

Inventory totals:

- current first-order blocker clusters: 3
- secondary observability cluster: 1
- deferred structural Stage 4 quality clusters: many, explicitly excluded

Current first-order blocker clusters:

1. Single-candidate payload shape drift
   - valid JSON may arrive as `list[dict]`, but the single-candidate path assumes `dict`
2. Self-critique dict-only parsing
   - list-shaped payload reaches `_self_critique()` and crashes before candidate promotion
3. Empty-candidates escalation
   - repeated candidate crashes become `candidates=[]`, then `EMPTY`

Secondary observability cluster:

4. Candidate admission failure should leave a clearer local reason surface
   - invalid JSON
   - list payload normalized
   - empty list
   - missing content
   - self-critique failure

## 5. Pass 2. Semantic Classification

- Class A: runtime correctness blocker
  - candidate payload normalization for single-candidate generation

- Class B: parser hardening blocker
  - self-critique must safely accept canonical dict payload and tolerated list payload

- Class C: bounded operator/forensic observability
  - candidate-admission failure reason should be more legible than a late `empty_candidates`

- Deferred:
  - Stage 4 contract-quality debt after candidate admission recovers

## 6. Side-Effect Map

- file writes / artifacts:
  - no new artifact family
  - Stage 4 artifact creation may begin again on next rerun if admission succeeds

- DB / schema / transaction boundaries:
  - no schema change expected
  - `stage_attempts` semantics stay the same
  - this wave should not widen into persistence redesign

- JSONL / log / audit sinks:
  - candidate-admission failure logging may become more structured or more explicit
  - do not reduce current evidence retention

- console / operator output:
  - current `empty_candidates` surface may gain more precise cause detail
  - keep max-display policy intact

- rollback / recovery / retry:
  - primary impact
  - by preventing false admission failure, later retry rounds should become meaningful again

- cache / global state:
  - not primary

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

- Normalize earliest, critique second.
  - do not let list-shaped valid JSON drift into downstream dict-only consumers
- Keep prompt tightening separate from parser hardening.
  - the parser must remain tolerant even after the prompt is stricter
- Reuse existing unwrapping helpers where possible.
  - avoid duplicating a second normalization stack in parallel
- Distinguish:
  - malformed JSON
  - valid list payload
  - valid dict payload with missing content
  - post-critique empty content

Invariant:

- Director authority stays unchanged
- Stage 4 review policy stays unchanged
- DB max-retention policy stays unchanged
- console max-display policy stays unchanged

## 8. Execution Tranches

1. Candidate payload normalization tranche
- Target:
  - `modules/domain/agents/chief_writer.py`
- Goal:
  - single-candidate generation must safely accept both canonical dict payload and tolerated list payload
- Required behavior:
  - empty list remains failure
  - `list[dict]` normalizes to a single canonical candidate object
  - malformed payload still fails cleanly
- Constraint:
  - do not widen into ensemble strategy redesign

2. Self-critique parser hardening tranche
- Target:
  - `modules/domain/agents/chief_writer_quality.py`
- Goal:
  - `_self_critique()` must not crash on list-shaped JSON payload
- Required behavior:
  - extract content safely from tolerated list/object payloads
  - preserve current critique logic once canonical content is obtained
- Constraint:
  - do not invent a new manuscript schema

3. Single-candidate output-contract tightening tranche
- Target:
  - `modules/domain/agents/chief_writer_prompts.py`
- Goal:
  - single-candidate generation path should explicitly prefer a single JSON object
- Required behavior:
  - prompt language must reduce list-shaped drift
  - runtime still stays tolerant if the model emits a list
- Constraint:
  - prompt tightening is supportive, not authoritative

4. Empty-candidates observability tranche
- Targets:
  - `modules/domain/agents/chief_writer.py`
  - `modules/core/stage4_interview_round.py`
- Goal:
  - when candidate admission fails, the local reason should be legible before the generic `empty_candidates` sink
- Required behavior:
  - keep evidence-rich logging
  - do not add truncation
- Constraint:
  - no new DB schema

## 9. Acceptance Criteria

- A valid `list[dict]` ChiefWriter single-candidate response no longer crashes the Stage 4 path.
- `_self_critique()` no longer raises `'list' object has no attribute 'get'` for tolerated list payloads.
- A malformed or empty payload still fails deterministically and clearly.
- Single-candidate prompt path now explicitly requests one object.
- The next rerun should be able to progress beyond `candidates 빈 배열` if the model returns usable content.

## 10. Required Verification

- `python -m py_compile modules/domain/agents/chief_writer.py modules/domain/agents/chief_writer_quality.py modules/domain/agents/chief_writer_prompts.py modules/core/stage4_interview_round.py`
- `python -m pytest tests/test_chief_writer.py -q`
- `python -m pytest tests/test_chief_writer_quality.py -q`
- `python -m pytest tests/test_chief_writer_candidate_lane_f.py -q`
- `python -m pytest tests/test_stage4_interview_round.py -q`
- `python scripts/check_utf8_hygiene.py modules/domain/agents/chief_writer.py modules/domain/agents/chief_writer_quality.py modules/domain/agents/chief_writer_prompts.py modules/core/stage4_interview_round.py docs/2026-03-23/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md docs/temp/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Closure Criteria

- code and targeted tests are green
- no UTF-8 hygiene failure
- temp queue state reflects this single active item cleanly
- Codex verifies that the list-payload crash seam is actually closed in live code
- SSOT closes only after audit; Opus must not close it

Closure Note:

- Live code now normalizes `list[dict]` payloads on both the single-candidate generation path and the self-critique/fix loop.
- Empty/non-dict candidate lists fail cleanly and leave an operator-visible warning before the generic `empty_candidates` sink.
- Targeted regression coverage now locks:
  - `_generate_single_candidate()` list payload normalization
  - `_self_critique()` list payload tolerance
  - `_fix_manuscript_issues()` list payload normalization
  - Stage 4 all-filtered candidate fallback
- Closure verification:
  - `python -m py_compile modules/domain/agents/chief_writer.py modules/domain/agents/chief_writer_quality.py modules/domain/agents/chief_writer_prompts.py modules/core/stage4_interview_round.py`
  - `python -m pytest tests/test_chief_writer.py -q`
  - `python -m pytest tests/test_chief_writer_quality.py -q`
  - `python -m pytest tests/test_chief_writer_candidate_lane_f.py -q`
  - `python -m pytest tests/test_stage4_interview_round.py -q`
  - `python scripts/check_utf8_hygiene.py ...`
  - `python scripts/ops_validator.py`

## 12. Out-of-Scope Risks To Revisit After This Wave

- Stage 4 opening-anchor priority inversion
- Stage 4 scene/write contract quality
- post-select downgrade and fix-pack convergence
- `CONDITIONAL_PASS` downstream handling
- broader long-run Q5/Q7 stress behavior

## 13. Opus Order Prompt

```text
System-track execution order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/temp/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md
4. docs/2026-03-23/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md
5. docs/2026-03-23/rol-live-merge-0p01-generation-failure-remediation-plan.md
6. docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md
7. docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md
8. docs/2026-03-23/opus/rol-live-merge-t3-contracts-context-regression.md
9. docs/2026-03-23/console.txt

Task:
Implement the bounded candidate-admission fix cluster defined in docs/temp/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md.

Primary goal:
Fix the current 0p-01 Stage 4 generation failure by hardening ChiefWriter single-candidate payload handling before the next rerun.

Hard constraints:
- Follow the execution SSOT exactly.
- Keep scope strictly bounded to candidate payload normalization, self-critique parser hardening, single-candidate prompt tightening, and empty-candidates observability.
- Do not widen into a new Stage 4 quality-wave refactor.
- Do not change Director authority or verdict policy.
- Do not touch DB schema, retention tables, or unrelated logging/model/config work.
- Do not close the execution SSOT after implementation; Codex will audit and close it.

Execution scope:
1. `modules/domain/agents/chief_writer.py`
- normalize tolerated list payloads in the single-candidate path
- keep malformed payload failure explicit

2. `modules/domain/agents/chief_writer_quality.py`
- make self-critique safe for tolerated list/object payloads
- prevent `'list' object has no attribute 'get'`

3. `modules/domain/agents/chief_writer_prompts.py`
- tighten single-candidate output contract toward one JSON object
- keep parser-tolerant runtime behavior

4. `modules/core/stage4_interview_round.py`
- improve local empty-candidates observability only if needed for bounded clarity

Implementation rules:
- Use apply_patch for edits.
- Keep comments short and boundary-oriented.
- Reuse existing helper seams where possible.
- If a field or branch cannot support richer observability cleanly, keep it bounded and report it rather than widening scope.

Required verification:
- python -m py_compile modules/domain/agents/chief_writer.py modules/domain/agents/chief_writer_quality.py modules/domain/agents/chief_writer_prompts.py modules/core/stage4_interview_round.py
- python -m pytest tests/test_chief_writer.py -q
- python -m pytest tests/test_chief_writer_quality.py -q
- python -m pytest tests/test_chief_writer_candidate_lane_f.py -q
- python -m pytest tests/test_stage4_interview_round.py -q
- python scripts/check_utf8_hygiene.py modules/domain/agents/chief_writer.py modules/domain/agents/chief_writer_quality.py modules/domain/agents/chief_writer_prompts.py modules/core/stage4_interview_round.py docs/2026-03-23/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md docs/temp/rol-live-merge-0p01-generation-failure-fix-execution-ssot.md
- python scripts/sync_temp_queue_state.py
- python scripts/ops_validator.py

Output requirements:
- summarize exactly what changed by tranche
- explain how list payloads are now handled
- list verification results
- do not close or supersede the execution SSOT; Codex will handle closure
```
