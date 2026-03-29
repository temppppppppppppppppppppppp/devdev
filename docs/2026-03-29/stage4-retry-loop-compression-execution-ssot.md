# Stage4 Retry Loop Compression Execution SSOT

Date: 2026-03-29
Status: closed
Canonical Path: `docs/2026-03-29/stage4-retry-loop-compression-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-retry-loop-compression-execution-ssot.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: 23 tracked, 34 untracked; hotspots: stage4 runtime/tests, provider/runtime code, narrative assets, canary artifacts, temp queue`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; the realization landed, clean canary validation passed, and the later extreme EP3 case was traced to blueprint defect rather than a reopened runtime loop bug`
Source Survey Docs:
- `docs/2026-03-29/stage4-retry-loop-compression-full-survey-audit-order.md`
- `docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`
Evidence Artifacts:
- `projects/canary_0329_feedback_windowing_check/logs/episode_production.jsonl`
- `projects/canary_0329_feedback_windowing_check/logs/runtime_audit.jsonl`
- `projects/canary_0329_feedback_windowing_check/logs/session/decisions.jsonl`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer.py`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe correction after the retry-loop compression survey.

The confirmed structural issue is:

> high-score manuscripts downgraded by `post_select_conflict` are stored, but the rewrite path does not reuse them, adjacent rationale is stripped, and conflict evidence remains free-text, so EP3-like loops can bounce through expensive full rewrites without a typed carryover contract.

This wave is not a lane-routing redesign.
This wave is a bounded carryover-contract correction.

## 2. Baseline Facts

- `post_select_conflict` universally forces `fix_scope="full"` and empties `fix_pack`
- in EP3, `continuity_firewall` also converged to rewrite, but through replay reclassification and reject-guidance steps rather than one universal force
- `best_manuscript` is already stored during the downgraded-PASS path
- the rewrite path (`regenerate_with_feedback`) does not consume that stored manuscript as a seed or typed reference
- the reject snapshot blanks `selection_reason` and `open_review` for `post_select_conflict` while leaving `best_manuscript` intact
- conflict evidence exists only as free-text lines appended to `director_feedback`
- patch lane requires a patch-ready `fix_pack` contract and is therefore explicitly out of scope for this first wave

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer.py`
- targeted tests:
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_orchestrator.py` if loop-state or payload sinks need narrow coverage
  - one targeted Chief Writer retry-path test file or additive test block in existing Chief Writer tests
- canonical execution SSOT and temp mirror maintenance

Excluded:

- `fix_scope` / `fix_pack` lane change for `post_select_conflict`
- patch lane enablement from conflict free-text
- `continuity_firewall` threshold or contradiction policy changes
- V75-B / V75-D threshold changes
- provider-default, fallback, or observability waves
- prompt-wide feedback windowing changes
- DB schema changes
- canary runner changes

## 4. Pass 1. Inventory Summary

- one stored-but-unused manuscript seam:
  - `previous_attempt["best_manuscript"]` exists but rewrite generation ignores it
- two stripped rationale fields:
  - `selection_reason`
  - `open_review`
- one missing typed carryover payload:
  - post-select conflict evidence is free-text only
- zero intended lane-routing changes in this wave

## 5. Pass 2. Semantic Classification

- Class A: patch now
  - preserve downgraded-PASS rationale fields where they are currently blanked
  - extract a structured `conflict_contract` from post-select conflict lines
  - define and implement a rewrite-path reuse contract for stored manuscripts

- Class B: explicitly deferred
  - convert `conflict_contract` into patch-ready `fix_pack`
  - switch `post_select_conflict` from full rewrite to partial/patch lane
  - add alternation counters or other oscillation-specific loop controls
  - change contradiction-firewall policy

## 6. Side-Effect Map

- file writes / artifacts:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_reject_runtime.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/domain/agents/chief_writer.py`
  - targeted tests
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - no schema change intended
  - existing `previous_attempt` payload shape may gain additive fields only

- JSONL / log / audit sinks:
  - `episode_production.jsonl`, `runtime_audit.jsonl`, and retry-pathology payloads may gain additive conflict-carryover metadata
  - no sink removal allowed

- console / UI / operator output:
  - no major console wording change intended
  - additive operator evidence for structured conflict payload is allowed

- rollback / recovery / retry:
  - retry lane selection must stay unchanged in this wave
  - rewrite still remains the next lane after `post_select_conflict`

- cache / global state:
  - no new global state intended

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### 7.1 Reuse Contract

The intended behavior is:

- when `post_select_conflict` downgrades a Director PASS or high-score near-pass manuscript, the already-stored `best_manuscript` remains the canonical carryover artifact
- the rewrite path must consume that stored manuscript through an explicit additive contract, not by silent implicit coupling
- acceptable contract shapes:
  - reference context
  - structural seed
  - diff baseline

This execution wave must pick one shape and make it explicit in code and tests.

Guardrail:

- do not claim the rewrite path is now patching in place
- do not silently mutate lane routing

### 7.2 Downstream Rationale Preservation Contract

The intended behavior is:

- for high-score `post_select_conflict` downgrades, the reject snapshot must stop blanking:
  - `selection_reason`
  - `open_review`
- these fields remain derived from the Director-approved candidate and are needed to contextualize the stored manuscript in the next rewrite round

Guardrail:

- preservation must be bounded to the downgraded-PASS / high-score path justified by survey evidence
- low-score or non-PASS reject families do not need broader preservation changes in this wave

### 7.3 Structured Conflict Payload Contract

The intended behavior is:

- post-select conflict evidence must be extracted into an additive `conflict_contract`
- minimum fields should include:
  - `conflict_type`
  - `conflict_detail`
  - `source_episode`
  - `expected_truth`
- the payload is operator and retry evidence only
- it is not yet a patch-ready `fix_pack`

Guardrail:

- do not let this wave invent `patch_targets`, `must_fix`, or `success_condition` unless already directly supported by evidence
- do not collapse authoritative Director rationale and runtime-derived conflict evidence into one field

### 7.4 Retry Path Consumption Contract

The intended behavior is:

- the rewrite path should receive:
  - stored manuscript per the chosen reuse contract
  - preserved rationale fields
  - structured conflict payload
- the Chief Writer retry prompt should consume those as clearly separated inputs
- the resulting prompt surface must not confuse:
  - Director's positive quality judgment
  - runtime conflict invalidation

Guardrail:

- do not reopen feedback snowball by blindly prepending new long text blocks
- if new prompt sections are added, they must be bounded and typed

## 8. Execution Tranches

1. Tranche 1: reject-snapshot preservation
   - stop blanking high-score downgraded-PASS rationale fields
   - keep existing `best_manuscript` semantics unchanged

2. Tranche 2: structured conflict payload
   - extract additive `conflict_contract` fields from post-select conflict evidence
   - propagate to the relevant retry payload and operator sink surfaces

3. Tranche 3: rewrite-path reuse contract
   - define one explicit reuse mode for `best_manuscript`
   - implement it in the rewrite generation path without lane change
   - keep the prompt surface bounded and typed

4. Tranche 4: regression coverage
   - prove rationale fields survive the relevant downgraded path
   - prove `conflict_contract` is emitted and preserved
   - prove rewrite retry consumes stored manuscript via the declared contract
   - prove lane selection remains unchanged

## 9. Acceptance Criteria

- `post_select_conflict` high-score downgraded-PASS snapshots preserve `selection_reason` and `open_review`
- `best_manuscript` remains stored and is explicitly consumed by the rewrite path according to one declared contract
- additive `conflict_contract` payload is present and preserved through retry evidence
- rewrite lane remains rewrite lane; no patch or partial-lane promotion occurs in this wave
- no `fix_pack` schema expansion or patch-ready conversion occurs in this wave
- no contradiction-firewall policy or escalation-threshold changes occur in this wave

## 10. Verification Plan

- targeted pytest for:
  - post-select downgrade snapshot preservation in `tests/test_stage4_interview_round.py`
  - retry-pathology / payload propagation in `tests/test_stage4_orchestrator.py` if touched
  - rewrite-path reuse contract in a targeted Chief Writer or retry-runtime test
- `python -m py_compile` on touched code/tests
- `ruff check` on touched code/tests
- `python scripts/check_utf8_hygiene.py` on touched code/tests/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Fresh Gemini canary validation should happen only after this wave lands.

## 11. Guardrails

- do not change lane routing in this wave
- do not change `fix_scope` or `fix_pack` semantics for `post_select_conflict`
- do not add patch-ready conversion from free-text conflict lines
- do not change contradiction-firewall thresholds or policy
- do not reopen provider-default, fallback, or feedback-windowing waves
- do not add DB columns
- do not let rewrite-path reuse become silent state coupling; keep it explicit and testable

## 12. Temp Queue Notes

- temp status: completed; mirror cleanup deferred to a dedicated closure sweep
- cleanup condition:
  - remove `docs/temp/stage4-retry-loop-compression-execution-ssot.md` during the next dedicated closure sweep
- roadmap dependency:
  - refresh `docs/temp/execution-roadmap.md` during closure sweep so the queue reflects this item's closed status

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- queue sync command: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least `95%` confidence against the current workspace state before patching from it

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- the wave is bounded to reuse, rationale preservation, and structured conflict payload
- lane-routing change and patch-lane enablement remain explicitly excluded
- PASS

### Pass 2. Evidence and Consistency

- the execution target matches the final audited survey, especially the correction from `preservation seam` to `reuse seam`
- no claim depends on unproven free-text to patch-ready conversion
- side-effect scope is covered across retry payloads, prompt surfaces, and operator sinks
- PASS

### Pass 3. Execution and Readability

- tranches are small and map directly to the three confirmed gaps
- acceptance criteria and guardrails make it hard to accidentally widen into a lane-routing redesign
- roadmap dependency is explicit
- PASS

Estimated confidence: `96%`

## 15. Closure Note

Date: 2026-03-29
Closure Status: closed

### 15.1 Realized Scope

- high-score downgraded-PASS rationale now survives the intended carryover path
- `conflict_contract` and `reuse_contract` became typed additive retry evidence instead of free-text-only context
- the rewrite path now explicitly reuses the stored manuscript through a declared carryover contract
- no lane-routing change, patch-lane promotion, or contradiction-threshold change was introduced

### 15.2 Verification Summary

- implementation verification:
  - targeted retry feedback / retry directives shard: `6 passed`
  - targeted orchestrator shard: `10 passed`
  - `python -m py_compile`, `ruff check`, UTF-8 hygiene, `sync_temp_queue_state.py`, and `ops_validator.py --strict` all passed
- live validation:
  - `canary_0329_retry_loop_compression_check` passed with `3/3` episode PASS and EP3-style loop compression from the earlier multi-round pattern to `2` rounds
  - later EP3-only blueprint-patch recheck passed in `1` round with score `98`, zero `continuity_firewall`, and zero `post_select_conflict`
- merged interpretation:
  - the execution wave successfully improved retry carryover behavior
  - the remaining extreme EP3 incident was input-side blueprint defect, not evidence that this runtime wave needed reopening

### 15.3 Residual Risks

- low-priority OTP advisory false-positive remains as a candidate for later bounded work
- blueprint/frontier trigger observability may still be worth an additive survey or logging pass, but threshold policy changes remain unjustified
- temp mirror cleanup is still pending

### 15.4 Follow-Up

- next queue action: dedicated closure sweep for completed Stage4 execution mirrors
- low-priority follow-up only if ROI rises: bounded survey for OTP advisory false-positive or trigger-state observability

### 15.5 Temp Cleanup

- execution SSOT mirror removed: no
- roadmap mirror removed: no
- queue-state refreshed or removed: deferred to the closure sweep
